from vpython import *
import serial, time, math

# ---- Serial ----
arduino = serial.Serial('COM3', 115200)  # <-- change if needed
time.sleep(1)

# ---- Scene ----
scene.range = 6
scene.background = color.white
scene.width = 1200
scene.height = 800
scene.forward = vector(-1, -1, -1)

# ---- Boxes ----
# Length is along .axis; choose sizes that look "hand-like"
wrist_len = 4.0
bone1_len = 3.0
bone2_len = 3.0

wrist = box(length=wrist_len, width=2.0, height=0.6, opacity=0.7, color=color.orange, pos=vector(0,0,0))
bone1 = box(length=bone1_len, width=0.8, height=0.6, opacity=0.8, color=color.cyan)
bone2 = box(length=bone2_len, width=0.7, height=0.5, opacity=0.8, color=color.green)

# ---- Helpers ----
y_up = vector(0,1,0)

def rpy_to_axis_up(roll, pitch, yaw):
    """
    Convert roll/pitch/yaw (radians) to VPython axis & up vectors.
    This matches the earlier math: k is forward/axis, up is rotated by roll around k.
    """
    k = vector(math.cos(yaw)*math.cos(pitch),
               math.sin(pitch),
               math.sin(yaw)*math.cos(pitch))
    s = cross(k, y_up)
    v = cross(s, k)
    up = v*math.cos(roll) + cross(k, v)*math.sin(roll)
    return k, up

# Neutral offsets + smoothing memories
pitch1_zero = None
pitch2_zero = None
pitch1_prev = 0.0
pitch2_prev = 0.0

# Optional sign flips if your board orientation needs it
SIGN_P1 =  1.0   # flip to -1.0 if bend direction is inverted
SIGN_P2 =  1.0

# Clamp limits (deg) to keep visuals sane
PITCH_MIN_DEG = -5
PITCH_MAX_DEG = 110

def clamp(v, vmin, vmax):
    return max(vmin, min(v, vmax))

# ---- Main loop ----
while True:
    try:
        if arduino.in_waiting == 0:
            rate(200)
            continue

        line = arduino.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 14:
            # print("Short frame:", line)
            continue

        # --- Parse frame ---
        q0, q1, q2, q3 = [float(parts[i]) for i in range(4)]

        # MPU1 (proximal) RPY in degrees
        roll1_deg  = float(parts[4])
        pitch1_deg = float(parts[5])
        yaw1_deg   = float(parts[6])  # ignored

        # MPU2 (distal) RPY in degrees
        roll2_deg  = float(parts[7])
        pitch2_deg = float(parts[8])
        yaw2_deg   = float(parts[9])  # ignored

        # Calibration (integers)
        system = int(parts[10]); gyro = int(parts[11]); accel = int(parts[12]); mag = int(parts[13])

        # --- BNO quaternion -> rollB/pitchB/yawB (radians) ---
        # Using same convention as earlier
        rollB  = -math.atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2))
        pitchB =  math.asin( 2*(q0*q2 - q3*q1))
        yawB   = -math.atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3))

        # --- Finger bends: only pitch from each MPU, in radians ---
        pitch1 = math.radians(pitch1_deg) * SIGN_P1
        pitch2 = math.radians(pitch2_deg) * SIGN_P2

        # Initialize neutrals on first valid frame
        if pitch1_zero is None: pitch1_zero = pitch1
        if pitch2_zero is None: pitch2_zero = pitch2

        pitch1 -= pitch1_zero
        pitch2 -= pitch2_zero

        # Light smoothing (1st order low-pass)
        pitch1 = 0.9*pitch1_prev + 0.1*pitch1
        pitch2 = 0.9*pitch2_prev + 0.1*pitch2
        pitch1_prev = pitch1
        pitch2_prev = pitch2

        # Clamp bends
        pitch1 = math.radians(clamp(math.degrees(pitch1), PITCH_MIN_DEG, PITCH_MAX_DEG))
        pitch2 = math.radians(clamp(math.degrees(pitch2), PITCH_MIN_DEG, PITCH_MAX_DEG))

        # --- Yaw & Roll for fingers come from BNO ---
        yawF  = yawB
        rollF = rollB

        # --- Update wrist (BNO) orientation ---
        kB, upB = rpy_to_axis_up(rollB, pitchB, yawB)
        wrist.axis = kB
        wrist.up   = upB
        wrist.pos  = vector(0,0,0)

        # --- Finger bone 1 (uses yawB/rollB + pitch1) ---
        k1, up1 = rpy_to_axis_up(rollF, pitch1, yawF)
        bone1.axis = k1
        bone1.up   = up1
        # position bone1 at end of wrist, along wrist's forward direction
        bone1.pos  = wrist.pos + kB * (wrist_len/2.0 + bone1_len/2.0)

        # --- Finger bone 2 (uses yawB/rollB + pitch2), chained after bone1 ---
        k2, up2 = rpy_to_axis_up(rollF, pitch2, yawF)
        bone2.axis = k2
        bone2.up   = up2
        # position bone2 at end of bone1 along bone1's forward direction
        bone2.pos  = bone1.pos + k1 * (bone1_len/2.0 + bone2_len/2.0)

        # (Optional) uncomment to see calibration in console
        # print(f"Calib Sys:{system} G:{gyro} A:{accel} M:{mag}")

        rate(60)

    except Exception as e:
        print("Error:", e)
        # If you want to debug malformed lines, uncomment:
        # print("Line was:", line)
        pass
