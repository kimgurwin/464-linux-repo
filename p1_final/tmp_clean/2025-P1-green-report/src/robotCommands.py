"""
robotCommands.py

Implements physical robot control for a 2-leg CKBot without backup or continuous rotation motors.
Provides a thread-safe, non-blocking "tap" API usable from the JoyApp/pygame control loop.

Each "tap" corresponds to a short, predefined movement of one or both robot legs.
This module can run in either:
  - **Hardware mode:** if CKBot hardware is connected
  - **Simulation mode:** if hardware is unavailable

Public API:
  - forward_tap(): both legs move for forward gait
  - turn_left_tap(): right leg only
  - turn_right_tap(): left leg only
  - stop(): immediately stop and reset leg positions to 0
  
ChatGPT used to generate some docstrings & comments.
"""

import time
import threading

# Try to import CKBot library
try:
    import ckbot.logical as L
    _CKBOT_AVAILABLE = True
except Exception:
    _CKBOT_AVAILABLE = False


class RobotDriver:
    """
    Thread-safe driver for a 2-leg CKBot system using tap-based motion.
    Designed for integration with event-driven loops (e.g., JoyApp).

    Parameters:
      left_id (str): CKBot module ID for the left leg.
      right_id (str): CKBot module ID for the right leg.
      count (int): Expected number of modules.
      verbose (bool): Print status messages.

    The driver operates in either real or simulated mode based on hardware availability.
    """

    def __init__(self, left_id="Nx24", right_id="Nx32", count=2, verbose=True):
        self.verbose = verbose
        self.sim = not _CKBOT_AVAILABLE
        self._busy = False
        self._lock = threading.Lock()
        self._t = None
        self._stop_flag = False

        if not self.sim:
            try:
                self.c = L.Cluster(count=count)
                self.left = getattr(self.c.at, left_id)
                self.right = getattr(self.c.at, right_id)
                if self.verbose:
                    print(f"[RobotDriver] CKBot connected: left={left_id}, right={right_id}")
            except Exception as e:
                print(f"[RobotDriver] CKBot initialization failed ({e}); running in SIM mode")
                self.sim = True

        if self.sim:
            # Create dummy actuator objects for simulation
            class _Dummy:
                def set_pos(self, x): pass
            self.c = None
            self.left = _Dummy()
            self.right = _Dummy()
            if self.verbose:
                print("[RobotDriver] Simulation mode (no hardware detected)")

        # Tap motion parameters
        self.amplitude = 5000      # Maximum forward sweep angle
        self.return_pos = -11500   # Return sweep back to "neutral" position
        self.step = 50             # Increment per step during sweep
        self.delay = 0.020         # Delay between each step (~tap duration)

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    @property
    def busy(self):
        """Return True if a movement tap is currently running."""
        return self._busy

    def forward_tap(self):
        """Perform a forward gait tap (both legs move)."""
        self._start_thread(self._tap_forward)

    def turn_left_tap(self):
        """Perform a left turn tap (right leg moves)."""
        self._start_thread(self._tap_turn_right_leg)

    def turn_right_tap(self):
        """Perform a right turn tap (left leg moves)."""
        self._start_thread(self._tap_turn_left_leg)

    def stop(self):
        """Immediately stop all motion and reset leg positions to 0."""
        with self._lock:
            self._stop_flag = True
        if self._t and self._t.is_alive():
            self._t.join(timeout=0.1)
        self.left.set_pos(0)
        self.right.set_pos(0)
        with self._lock:
            self._busy = False
            self._stop_flag = False
        if self.verbose:
            print("[RobotDriver] STOP")

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------

    def _start_thread(self, fn):
        """Launch a new thread for the given movement function."""
        with self._lock:
            if self._busy:
                return  # Ignore command if another tap is already running
            self._busy = True
            self._stop_flag = False
        self._t = threading.Thread(target=self._run_guard, args=(fn,), daemon=True)
        self._t.start()

    def _run_guard(self, fn):
        """Run a motion function safely, ensuring busy flag resets on completion."""
        try:
            fn()
        finally:
            with self._lock:
                self._busy = False
                self._stop_flag = False

    def _sweep(self, setpos_fn_list):
        """
        Sweep actuator(s) through a tap motion.

        Args:
            setpos_fn_list (list): Functions to control actuator positions (e.g., self.left.set_pos).

        Behavior:
            - Increment position from 0 up to amplitude in steps.
            - Then reset to the defined return position.
            - Stops early if stop() is called.
        """
        rng = range(0, self.amplitude + 1, self.step)
        for i in rng:
            with self._lock:
                if self._stop_flag:
                    return
            for sp in setpos_fn_list:
                sp(i)
            # Small busy-wait loop to emulate mechanical delay
            count = 0
            while count < 250000:
                count += 1
            count = 0
        for sp in setpos_fn_list:
            sp(self.return_pos)

    # ----------------------------------------------------------------------
    # Concrete motion patterns
    # ----------------------------------------------------------------------

    def _tap_forward(self):
        if self.verbose:
            print("[RobotDriver] forward_tap")
        self._sweep([self.left.set_pos, self.right.set_pos])

    def _tap_turn_right_leg(self):
        if self.verbose:
            print("[RobotDriver] turn_left_tap (RIGHT leg active)")
        self._sweep([self.right.set_pos])

    def _tap_turn_left_leg(self):
        if self.verbose:
            print("[RobotDriver] turn_right_tap (LEFT leg active)")
        self._sweep([self.left.set_pos])