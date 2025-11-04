#This file is an extra file that was helpful in computing the average stride and gait metrics of 
#the project 0 green robot.

#this can be run by writing: python green_step.py <green_.log>

#!/usr/bin/env python3
import json
import numpy as np
import sys
from typing import List, Dict, Tuple, Optional

# -------------------------
# Helper parsing functions
# -------------------------
def parse_log_line(line: str) -> Tuple[Optional[float], Optional[List[Dict]]]:
    """Parse a single log line into timestamp and tag data."""
    parts = line.strip().split(',', 1)
    if len(parts) != 2:
        return None, None

    # timestamp may come with leading '[' or trailing ']'
    ts_str = parts[0].strip().lstrip('[').rstrip(']')
    try:
        timestamp = float(ts_str)
    except ValueError:
        return None, None

    tag_data_str = parts[1].strip()
    # ensure it looks like a JSON array
    if not tag_data_str.startswith('['):
        tag_data_str = '[' + tag_data_str

    try:
        tag_data = json.loads(tag_data_str)
    except json.JSONDecodeError:
        # last resort: try replacing single quotes with double quotes (only if necessary)
        try:
            tag_data = json.loads(tag_data_str.replace("'", '"'))
        except Exception:
            return None, None

    return timestamp, tag_data

def extract_tag_center(tag_dict: Dict) -> Tuple[Optional[float], Optional[float]]:
    """Calculate the center point of a tag from its corner coordinates."""
    points = tag_dict.get('p', []) or tag_dict.get('points', [])
    if not points:
        return None, None

    x_coords = [float(p[0]) for p in points]
    y_coords = [float(p[1]) for p in points]

    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)

    return center_x, center_y

# -------------------------
# Movement / step detection
# -------------------------
def calculate_movement(data: List[Tuple[float, List[Dict]]]) -> np.ndarray:
    """Calculate movement (timestamp, center_x, center_y) for tag i==16."""
    rows = []
    for timestamp, tags in data:
        if not tags:
            continue
        # tags expected as list of dicts
        for tag in tags:
            # tag id key 'i' (per your logs)
            if tag.get('i') == 16:
                cx, cy = extract_tag_center(tag)
                if cx is None or cy is None:
                    continue
                rows.append((float(timestamp), float(cx), float(cy)))
                break
    if not rows:
        return np.empty((0, 3), dtype=float)
    return np.array(rows, dtype=float)

def find_steps(movements: np.ndarray,
               velocity_threshold: float = 0.5,
               min_stride_time: float = 0.3,
               min_stride_length: float = 1.0,
               smoothing_window: int = 3) -> List[Dict]:
    """
    Identify steps where velocity magnitude has a local minimum below threshold,
    with smoothing and minimum stride filters.

    movements: array of shape (N, 3) columns [timestamp, x, y]
    velocity_threshold: ignore local minima above this
    min_stride_time: minimum time between consecutive steps (s)
    min_stride_length: minimum distance between consecutive steps (px)
    smoothing_window: number of points for moving average smoothing
    """
    steps = []
    if movements.size == 0 or movements.shape[0] < 3:
        return steps

    timestamps = movements[:, 0]
    x_pos = movements[:, 1]
    y_pos = movements[:, 2]

    dt = np.diff(timestamps)
    dx = np.diff(x_pos)
    dy = np.diff(y_pos)

    dt[dt == 0] = 1e-10  # avoid divide-by-zero

    vx = dx / dt
    vy = dy / dt
    velocity_mag = np.sqrt(vx**2 + vy**2)

    # Smooth velocity to reduce noise from small jitters
    if smoothing_window > 1:
        smoothed_v = np.convolve(velocity_mag,
                                 np.ones(smoothing_window)/smoothing_window,
                                 mode='same')
    else:
        smoothed_v = velocity_mag

    # Detect local minima
    for i in range(1, len(smoothed_v)-1):
        if (smoothed_v[i] < smoothed_v[i-1] and
            smoothed_v[i] < smoothed_v[i+1] and
            smoothed_v[i] < velocity_threshold):

            step_time = float(timestamps[i+1])
            step_x = float(x_pos[i+1])
            step_y = float(y_pos[i+1])
            candidate_step = {
                'timestamp': step_time,
                'position': (step_x, step_y),
                'velocity': float(smoothed_v[i])
            }

            # Apply minimum stride time and distance filters
            if steps:
                dt_step = candidate_step['timestamp'] - steps[-1]['timestamp']
                dx_step = np.linalg.norm(np.array(candidate_step['position']) - 
                                         np.array(steps[-1]['position']))
                if dt_step < min_stride_time or dx_step < min_stride_length:
                    continue  # skip this step

            steps.append(candidate_step)

    return steps


# -------------------------
# Gait metrics
# -------------------------
def calculate_gait_metrics(steps: List[Dict], movements: np.ndarray, drop_low_percent: float = 5.0) -> Dict:
    """
    Calculate gait metrics from identified steps, including stride lengths/times
    and angular drift (heading changes).
    """
    if len(steps) < 2:
        print("[INFO] Not enough steps detected to calculate metrics.")
        return {
            'stride_times': [],
            'stride_lengths': [],
            'average_stride_time': 0,
            'average_stride_length': 0,
            'cadence': 0,
            'average_velocity': 0,
            'total_distance': 0,
            'per_stride_angle_changes': [],
            'average_heading_drift': 0,
            'total_heading_drift': 0
        }

    stride_times = []
    stride_lengths = []
    headings = []  # heading angles between steps (degrees)

    for i in range(1, len(steps)):
        tdiff = steps[i]['timestamp'] - steps[i-1]['timestamp']
        stride_times.append(float(tdiff))

        x1, y1 = steps[i-1]['position']
        x2, y2 = steps[i]['position']
        dx, dy = (x2 - x1), (y2 - y1)
        distance = float(np.sqrt(dx**2 + dy**2))
        stride_lengths.append(distance)

        # heading angle in degrees
        heading = np.degrees(np.arctan2(dy, dx))
        headings.append(heading)

    # filter smallest bottom X percent
    if drop_low_percent > 0 and len(stride_lengths) > 5:
        cutoff = float(np.percentile(stride_lengths, drop_low_percent))
        keep_idx = [i for i, d in enumerate(stride_lengths) if d >= cutoff]
        dropped = len(stride_lengths) - len(keep_idx)
        if dropped > 0:
            print(f"[INFO] Dropped {dropped} strides below {cutoff:.2f} px (bottom {drop_low_percent}%)")
        stride_lengths = [stride_lengths[i] for i in keep_idx]
        stride_times = [stride_times[i] for i in keep_idx]
        headings = [headings[i] for i in keep_idx if i < len(headings)]

    avg_stride_time = float(np.mean(stride_times)) if stride_times else 0.0
    avg_stride_length = float(np.mean(stride_lengths)) if stride_lengths else 0.0
    cadence = (60.0 / avg_stride_time) if avg_stride_time > 0 else 0.0

    total_distance = float(sum(stride_lengths))
    total_time = float(steps[-1]['timestamp'] - steps[0]['timestamp'])
    avg_velocity = (total_distance / total_time) if total_time > 0 else 0.0

    # --- Angular drift analysis ---
    angle_changes = []
    for i in range(1, len(headings)):
        diff = headings[i] - headings[i-1]
        # wrap to [-180, 180]
        diff = (diff + 180) % 360 - 180
        angle_changes.append(diff)

    total_heading_drift = float(np.sum(np.abs(angle_changes)))
    avg_heading_drift = float(np.mean(np.abs(angle_changes))) if angle_changes else 0.0

    # Debug prints
    print("\n[DEBUG] Gait metric data:")
    print(f"  Stride count: {len(stride_lengths)}")
    print(f"  Average stride time: {avg_stride_time:.3f}s")
    print(f"  Average stride length: {avg_stride_length:.2f}px")
    print(f"  Cadence: {cadence:.1f} steps/min")
    print(f"  Average velocity: {avg_velocity:.2f}px/s")
    print(f"  Total distance: {total_distance:.2f}px")
    print(f"  Total heading drift: {total_heading_drift:.2f}°")
    print(f"  Average heading drift per stride: {avg_heading_drift:.2f}°")
    print(f"  Stride times: {np.round(stride_times, 3)}")
    print(f"  Stride lengths: {np.round(stride_lengths, 2)}")
    print(f"  Per-stride angle changes: {np.round(angle_changes, 2)}\n")

    return {
        'stride_times': stride_times,
        'stride_lengths': stride_lengths,
        'average_stride_time': avg_stride_time,
        'average_stride_length': avg_stride_length,
        'cadence': cadence,
        'average_velocity': avg_velocity,
        'total_distance': total_distance,
        'per_stride_angle_changes': angle_changes,
        'average_heading_drift': avg_heading_drift,
        'total_heading_drift': total_heading_drift
    }


# -------------------------
# Main parse/analyze
# -------------------------
def parse_robot_log(log_data: str, velocity_threshold: float = 0.5) -> Dict:
    lines = log_data.strip().split('\n')
    data = []
    for line in lines:
        if not line.strip():
            continue
        ts, tags = parse_log_line(line)
        if ts is not None and tags is not None:
            data.append((float(ts), tags))
        else:
            # optional: print malformed line debug
            # print("[WARN] Skipping malformed line:", line)
            pass

    if not data:
        return {'error': 'No valid data found'}

    movements = calculate_movement(data)
    if movements.size == 0:
        print("[WARN] No movements recorded for tag 16.")
    steps = find_steps(movements, velocity_threshold)
    gait_metrics = calculate_gait_metrics(steps, movements, drop_low_percent=1.0)

    return {
        'total_frames': len(data),
        'duration': float(data[-1][0] - data[0][0]),
        'steps_detected': len(steps),
        'steps': steps,
        'gait_metrics': gait_metrics,
        'movements': movements.tolist()
    }

# -------------------------
# CLI entrypoint
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python green2.py <log_file.log>")
        sys.exit(1)

    log_file = sys.argv[1]
    try:
        with open(log_file, 'r') as f:
            log_data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{log_file}' not found")
        sys.exit(1)

    results = parse_robot_log(log_data, velocity_threshold=2.0)

    # sanity check / debug: confirm helpers are loaded
    print("[INFO] Helper availability:",
          "parse_log_line" if callable(parse_log_line) else "MISSING",
          "calculate_movement" if callable(calculate_movement) else "MISSING",
          "find_steps" if callable(find_steps) else "MISSING")

    if 'error' in results:
        print("Error:", results['error'])
        sys.exit(1)

    print("=" * 70)
    print("ROBOT GAIT ANALYSIS")
    print("=" * 70)
    print(f"\nLog File: {log_file}")
    print(f"Total frames: {results['total_frames']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Steps detected: {results['steps_detected']}")

    if results['steps_detected'] > 0:
        gait = results['gait_metrics']
        print("\n" + "=" * 70)
        print("GAIT METRICS")
        print("=" * 70)
        print(f"Average stride time: {gait['average_stride_time']:.3f} seconds")
        print(f"Average stride length: {gait['average_stride_length']:.2f} pixels")
        print(f"Cadence: {gait['cadence']:.1f} steps/minute")
        print(f"Average velocity: {gait['average_velocity']:.2f} pixels/second")
        print(f"Total distance: {gait['total_distance']:.2f} pixels")
        print(f"Average heading drift per stride: {gait['average_heading_drift']:.2f}°")
        print(f"Total heading drift: {gait['total_heading_drift']:.2f}°")

        print("\n" + "=" * 70)
        print("INDIVIDUAL STEPS")
        print("=" * 70)
        print(f"{'Step':<6} {'Time (s)':<12} {'Position (x, y)':<25} {'Stride Time':<15} {'Stride Length'}")
        print("-" * 70)
        for i, step in enumerate(results['steps'], 1):
            time_str = f"{step['timestamp']:.3f}"
            pos_str = f"({step['position'][0]:.1f}, {step['position'][1]:.1f})"
            if i == 1:
                stride_time_str = "---"
                stride_length_str = "---"
            else:
                stride_time = gait['stride_times'][i-2] if i-2 < len(gait['stride_times']) else 0
                stride_length = gait['stride_lengths'][i-2] if i-2 < len(gait['stride_lengths']) else 0
                stride_time_str = f"{stride_time:.3f} s"
                stride_length_str = f"{stride_length:.2f} px"
            print(f"{i:<6} {time_str:<12} {pos_str:<25} {stride_time_str:<15} {stride_length_str}")

    # save JSON
    output_file = log_file.replace('.log', '_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Analysis saved to: {output_file}")
    print("=" * 70)
