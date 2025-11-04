"""
robotSimulator.py

Simulates or drives a robot using a bang-bang control strategy.

Simulation logic was broken.

Keyboard commands:
  ↑  Move forward (tap)
  ←  Turn left (tap)
  →  Turn right (tap)
  ↓  Stop
  p  Toggle autonomy (bang-bang mode ON/OFF)

ChatGPT used to generate some docstrings & comments.
"""

from numpy import mean, abs, asarray, pi, angle
from sensorPlanTCP import SensorPlanTCP
from robotSimIX import SimpleRobotSim, RobotSimInterface
from joy import JoyApp, progress
from joy.decl import *
from joy.plans import Plan
from plotIX import JoyAppWptSensorMixin
from waypointShared import WAYPOINT_HOST, WAYPOINT_MSG_PORT
from pylab import randn
import time

# Toggle this to use the real robot instead of the simulator
REAL = True

if REAL:
  try:
    from robotCommands import RobotDriver
  except Exception as e:
    RobotDriver = None
    progress(f"(warn) Could not import RobotDriver: {e}")

# Constants derived from motion calibration
STEP_CM = 3.7653083102525993
TURN_DEG = 9.272544430948525
STEP_SIGMA_CM = 0.22097875920252896
TURN_SIGMA_DEG = 3.611843507114224


class MoveForward(Plan):
  """Simulates a short forward movement ('tap') in the simulator."""
  def __init__(self, app, simIX):
    super().__init__(app)
    self.simIX = simIX
    self.dur = 0.1

  def behavior(self):
    s = self.simIX
    tp = s.tagPos
    px_per_cm = sorted([((tp[i] - tp[(i + 1) % 4]) ** 2).sum() ** 0.5 for i in range(4)])[2] / 10.0
    step_cm = STEP_CM + randn() * STEP_SIGMA_CM
    if step_cm < 0:
      step_cm = 0.0
    self.app.captureStateBeforeMove()
    s.move(step_cm * px_per_cm)
    yield self.forDuration(self.dur)


class Turn(Plan):
  """Simulates a short in-place turn ('tap') in the simulator."""
  def __init__(self, app, simIX):
    super().__init__(app)
    self.simIX = simIX
    self.ang = 0.1
    self.dur = 0.1

  def behavior(self):
    s = self.simIX
    sign = 1.0 if self.ang >= 0 else -1.0
    turn_magnitude_deg = TURN_DEG + randn() * TURN_SIGMA_DEG
    if turn_magnitude_deg < 0:
      turn_magnitude_deg = 0
    final_ang_rad = sign * turn_magnitude_deg * pi / 180.0
    self.app.captureStateBeforeMove()
    s.turn(final_ang_rad)
    yield self.forDuration(self.dur)


class RobotSimulatorApp(JoyApp, JoyAppWptSensorMixin):
  """Main robot control and visualization application using bang-bang control."""
  def __init__(self, wphAddr=WAYPOINT_HOST, wphPort=WAYPOINT_MSG_PORT, *arg, **kw):
    JoyApp.__init__(self, confPath="$/cfg/JoyApp.yml", *arg, **kw)
    JoyAppWptSensorMixin.__init__(self, host=wphAddr, wptPort=wphPort)

  def onStart(self):
    """Initial setup for sensors, visualization, and robot interface."""
    JoyAppWptSensorMixin.onStart(self)
    self.timeForStatus = self.onceEvery(1)        # print sensor data @ 1 Hz
    self.timeForFrame  = self.onceEvery(1 / 10.0) # refresh visualization @ 10 Hz
    self.T0 = self.now

    self._must_force_forward = False
    self._turn_cooldown_until = 0.0

    # Setup for real robot or simulator
    if REAL:
      self.robSim = None
      self.moveP = None
      self.turnP = None
    else:
      self.robSim = SimpleRobotSim()
      self.moveP = MoveForward(self, self.robSim)
      self.turnP = Turn(self, self.robSim)

    # Initialize robot driver if REAL=True
    self.driver = None
    if REAL and 'RobotDriver' in globals() and RobotDriver is not None:
      try:
        self.driver = RobotDriver()
        progress("(say) RobotDriver initialized")
      except Exception as e:
        progress(f"(warn) RobotDriver failed to init: {e}")
    elif REAL:
      progress("(warn) REAL=True but RobotDriver not available")

    # State variables
    self.key_is_down = False
    self.position_history = []
    self.max_history = 100
    self.auto_mode = False

    # Sensor and control state
    self.prev_move_state = {'right': 0, 'left': 0, 'action': None}
    self.current_sensors = {'right': 0, 'left': 0}
    self.last_command = None

    # Non-blocking control timing
    self._repeat = None
    self._auto_next_tap_t = 0.0
    self._auto_tap_dt = 1.5

  # ---------------------------------------------------------------------
  # Helper methods
  # ---------------------------------------------------------------------

  def _sim_busy(self):
    """Check if simulator movement plans are active."""
    return (self.moveP and self.moveP.isRunning()) or (self.turnP and self.turnP.isRunning())

  def _actuator_free(self):
    """Check whether robot (real or sim) is ready for a new tap command."""
    if REAL:
      return (self.driver is not None) and (not getattr(self.driver, "busy", False))
    else:
      return (self.robSim is not None) and (not self._sim_busy())

  def _issue_tap(self, kind):
    """Send a single movement tap to either the real robot or simulator."""
    if REAL and self.driver and not getattr(self.driver, "busy", False):
      if kind == 'forward':
        self.driver.forward_tap()
      elif kind == 'left':
        self.driver.turn_left_tap()
      elif kind == 'right':
        self.driver.turn_right_tap()
      return True

    if (not REAL) and self.robSim and not self._sim_busy():
      if kind == 'forward':
        self.moveP = MoveForward(self, self.robSim)
        self.moveP.start()
      else:
        self.turnP = Turn(self, self.robSim)
        self.turnP.ang = 0.5 if kind == 'left' else -0.5
        self.turnP.start()
      return True

    return False

  def _enforce_turn_then_forward(self):
    """After a turn, wait briefly before forcing a forward tap."""
    if not self._must_force_forward:
      return False
    if self.now >= self._turn_cooldown_until and self._actuator_free():
      if self._issue_tap('forward'):
        self.last_command = "FORWARD"
        self._must_force_forward = False
        progress("AUTO: forced FORWARD after turn", sameLine=False)
        self._auto_next_tap_t = self.now + self._auto_tap_dt
        return True
    return False

  def captureStateBeforeMove(self):
    """Record previous sensor values before issuing a new movement."""
    ts, f, b = self.sensor.lastSensor
    if ts:
      self.prev_move_state = {'right': f, 'left': b, 'action': self.last_command}

  # ---------------------------------------------------------------------
  # Bang-Bang Controller
  # ---------------------------------------------------------------------

  def bangBangControl(self):
    """Compute robot action (FORWARD, LEFT, RIGHT, RECOVER, WAIT) based on sensors."""
    ts, f, b = self.sensor.lastSensor
    if not ts:
      return "WAIT", "No sensor data"

    self.current_sensors['right'] = f
    self.current_sensors['left'] = b

    right_curr, left_curr = f, b
    right_prev, left_prev = self.prev_move_state['right'], self.prev_move_state['left']
    last_action = self.prev_move_state['action']

    BALANCE_THRESHOLD = 30
    ON_LINE_THRESHOLD = 50
    DEGRADATION_THRESHOLD = 20

    # Recover from degradation after a turn
    if last_action == "TURN_LEFT" and right_prev > 0:
      if (right_prev - right_curr) > DEGRADATION_THRESHOLD:
        return "TURN_RIGHT", f"Bang-bang: R degraded after L turn ({right_prev}->{right_curr})"
    if last_action == "TURN_RIGHT" and left_prev > 0:
      if (left_prev - left_curr) > DEGRADATION_THRESHOLD:
        return "TURN_LEFT", f"Bang-bang: L degraded after R turn ({left_prev}->{left_curr})"

    # Resume forward when back on line
    if last_action in ["TURN_LEFT", "TURN_RIGHT"]:
      if right_curr > ON_LINE_THRESHOLD or left_curr > ON_LINE_THRESHOLD:
        return "FORWARD", f"Testing turn: R={right_curr} L={left_curr}"

    # Lost both sensors
    if right_curr < ON_LINE_THRESHOLD and left_curr < ON_LINE_THRESHOLD:
      return "RECOVER", f"Both sensors low: R={right_curr} L={left_curr}"

    # Balance logic
    imbalance = right_curr - left_curr
    if abs(imbalance) < BALANCE_THRESHOLD and right_curr > ON_LINE_THRESHOLD and left_curr > ON_LINE_THRESHOLD:
      return "FORWARD", f"Balanced R={right_curr} L={left_curr}"
    if imbalance > BALANCE_THRESHOLD:
      return "TURN_LEFT", f"R>L by {imbalance:.0f}"
    if imbalance < -BALANCE_THRESHOLD:
      return "TURN_RIGHT", f"L>R by {-imbalance:.0f}"

    # Default case
    if right_curr > ON_LINE_THRESHOLD or left_curr > ON_LINE_THRESHOLD:
      return "FORWARD", f"Default forward: R={right_curr} L={left_curr}"

    return "RECOVER", ""

  # ---------------------------------------------------------------------
  # Visualization
  # ---------------------------------------------------------------------

  def showSensors(self):
    """Return formatted sensor and waypoint info."""
    msg = []
    ts, f, b = self.sensor.lastSensor
    if ts:
      msg.append("Sensor: %4d f(R)=%d b(L)=%d" % (ts - self.T0, f, b))
    ts, w = self.sensor.lastWaypoints
    if ts:
      msg.append("Waypoints: %4d " % (ts - self.T0) + str(w))
    return msg

  def doVis(self):
    """Update visualization with sensor readings and bang-bang action."""
    if REAL or (self.robSim is None):
      self.visArenaClear()
      ts_wp, wps = self.sensor.lastWaypoints
      if ts_wp and wps:
        idx = 1 if len(wps) > 1 else 0
        wx, wy = wps[idx]
        self.visArena('plot', [wx], [wy],
                      marker='o', markersize=7, color="#ef871f",
                      mec='k', mew=1, alpha=1, linestyle='None', zorder=12)
      self.visArena('grid', 1)

      self.visRobotClear()
      action, reasoning = self.bangBangControl()
      action_colors = {
          'FORWARD': 'green',
          'TURN_RIGHT': 'blue',
          'TURN_LEFT': 'orange',
          'RECOVER': 'red',
          'WAIT': 'gray'
      }
      color = action_colors.get(action, 'black')
      lines = [
          f"NEXT: {action}",
          f"Right: {self.current_sensors['right']}",
          f"Left: {self.current_sensors['left']}",
          reasoning,
      ]
      if self.prev_move_state['action']:
        lines.insert(1, f"Last: {self.prev_move_state['action']} -> "
                        f"R:{self.prev_move_state['right']} L:{self.prev_move_state['left']}")
      self.visRobot('text', 0, -5000, s="\n".join(lines),
                    ha='center', va='top', fontsize=7,
                    color=color, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
      return

  # ---------------------------------------------------------------------
  # Keyboard controls and event loop
  # ---------------------------------------------------------------------

  def on_K_UP(self, evt):
    self.key_is_down = True
    self.last_command = "FORWARD"
    self._repeat = {'kind': 'forward', 'next_t': 0.0, 'dt': 0.15}
    return progress("Move forward")

  def on_K_LEFT(self, evt):
    self.key_is_down = True
    self.last_command = "TURN_LEFT"
    self._repeat = {'kind': 'left', 'next_t': 0.0, 'dt': 0.15}
    return progress("Turn left")

  def on_K_RIGHT(self, evt):
    self.key_is_down = True
    self.last_command = "TURN_RIGHT"
    self._repeat = {'kind': 'right', 'next_t': 0.0, 'dt': 0.15}
    return progress("Turn right")

  def on_K_DOWN(self, evt):
    if REAL and self.driver:
      try:
        self.driver.stop()
      except Exception:
        pass
    self.key_is_down = False
    self._repeat = None
    return progress("Stop")

  def on_K_p(self, evt):
    """Toggle autonomous bang-bang mode."""
    self.auto_mode = not self.auto_mode
    return progress(f"AUTONOMY {'ON' if self.auto_mode else 'OFF'}")

  def onEvent(self, evt):
    """Main control loop: handles visualization, keypresses, and autonomy."""
    if evt.type == KEYUP:
      if evt.key in (K_UP, K_LEFT, K_RIGHT):
        self.key_is_down = False
        self._repeat = None
      return

    if self.timeForStatus():
      msg = self.showSensors()
      progress(" ".join(msg), sameLine=True)

    if self.timeForFrame():
      if (self.robSim is not None) and (not REAL):
        self.robSim.refreshState()
      self.doVis()

      # Handle manual control
      if self._repeat and self.now >= self._repeat['next_t'] and self._actuator_free():
        if self._issue_tap(self._repeat['kind']):
          self._repeat['next_t'] = self.now + self._repeat['dt']

      # Handle autonomous bang-bang control
      elif self.auto_mode:
        if not self._enforce_turn_then_forward() and self.now >= self._auto_next_tap_t and self._actuator_free():
          act, reason = self.bangBangControl()
          issued = False
          if act == "TURN_LEFT":
            issued = self._issue_tap('left'); self.last_command = "TURN_LEFT"
            self._must_force_forward = True; self._turn_cooldown_until = self.now + 4.0
          elif act == "TURN_RIGHT":
            issued = self._issue_tap('right'); self.last_command = "TURN_RIGHT"
            self._must_force_forward = True; self._turn_cooldown_until = self.now + 4.0
          elif act == "FORWARD":
            issued = self._issue_tap('forward'); self.last_command = "FORWARD"

          if issued:
            self._auto_next_tap_t = self.now + self._auto_tap_dt
          progress(reason, sameLine=False)

    if evt.type == KEYDOWN:
      return JoyApp.onEvent(self, evt)


if __name__ == "__main__":
  from sys import argv
  print("""
  Running the robot simulator

  Listens on local port 0xBAA (2986) for incoming waypointServer
  information, and transmits simulated tagStreamer messages to
  the waypointServer at the specified host and port.

  Usage:
    python robotSimulator.py
        Connect to default host and port
    python robotSimulator.py <host>
        Connect to specified host on default port
    python robotSimulator.py <host> <port>
        Connect to specified host and port
  """)
  cfg = {'windowSize': [160, 120]}
  if len(argv) > 2:
    app = RobotSimulatorApp(wphAddr=argv[1], wphPort=int(argv[2]), cfg=cfg)
  elif len(argv) == 2:
    app = RobotSimulatorApp(wphAddr=argv[1], cfg=cfg)
  else:
    app = RobotSimulatorApp(cfg=cfg)
  app.run()