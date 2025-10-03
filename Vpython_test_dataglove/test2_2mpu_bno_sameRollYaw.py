from vpython import *
import serial, time, math
from serial.tools import list_ports

# ---------- PORT ----------
def pick_port():
    ports = list(list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ("cp210","silicon","ch340","usb-serial","esp32","wch","ftdi")):
            return p.device
    return ports[0].device if ports else None

PORT = pick_port() or "COM4"   # fallback, change if needed
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2.0)
ser.reset_input_buffer()

# ---------- Scene ----------
scene.title = "BNO wrist + two MPU finger bones (bend axis selectable)"
scene.range = 6
scene.background = color.white
scene.width = 1200
scene.height = 800
scene.forward = vector(-1, -1, -1)

# ---------- Geometry ----------
wrist_len = 4.0
bone1_len = 3.0
bone2_len = 3.0

wrist = box(length=wrist_len, width=2.0, height=0.6, opacity=0.7, color=color.orange, pos=vector(0,0,0))
bone1 = box(length=bone1_len, width=0.8, height=0.6, opacity=0.85, color=color.cyan)
bone2 = box(length=bone2_len, width=0.7, height=0.5, opacity=0.85, color=color.green)

hud = wtext(text="")

# ---------- Config (tweak live if needed) ----------
BEND_AXIS_1 = "pitch"   # "pitch" or "roll"
BEND_AXIS_2 = "pitch"
SMOOTH = 0.15           # 0 = no smoothing, 0.15 is light smoothing
GAIN_1 = 1.0            # scale the bend if it's too small
GAIN_2 = 1.0
SIGN_P1 = 1.0           # flip to -1.0 if direction is inverted
SIGN_P2 = 1.0
USE_CLAMP = False       # set True to clamp to realistic finger range
CLAMP_MIN_DEG = -5
CLAMP_MAX_DEG = 110

# ---------- Helpers ----------
y_up = vector(0,1,0)

def rpy_to_axis_up(roll, pitch, yaw):
    k = vector(math.cos(yaw)*math.cos(pitch),
               math.sin(pitch),
               math.sin(yaw)*math.cos(pitch))
    s = cross(k, y_up)
    v = cross(s, k)
    up = v*math.cos(roll) + cross(k, v)*math.sin(roll)
    return k, up

def clamp(v, vmin, vmax):
    return max(vmin, min(v, vmax))

# Zero & smoothing state
bend1_zero = None
bend2_zero = None
bend1_prev = 0.0
bend2_prev = 0.0

def on_key(evt):
    global BEND_AXIS_1, BEND_AXIS_2, bend1_zero, bend2_zero
    k = evt.key
    if k == '1':
        BEND_AXIS_1 = "roll" if BEND_AXIS_1 == "pitch" else "pitch"
    elif k == '2':
        BEND_AXIS_2 = "roll" if BEND_AXIS_2 == "pitch" else "pitch"
    elif k == 'z':
        bend1_zero = None
        bend2_zero = None

scene.bind('keydown', on_key)

# ---------- Main loop ----------
while True:
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            rate(200); continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 14:
            rate(200); continue

        # BNO quaternion -> rollB/pitchB/yawB (radians)
        q0,q1,q2,q3 = [float(parts[i]) for i in range(4)]
        rollB  = -math.atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2))
        pitchB =  math.asin( 2*(q0*q2 - q3*q1))
        yawB   = -math.atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3))

        # Raw MPU degrees
        roll1_deg  = float(parts[4]);  pitch1_deg = float(parts[5])
        roll2_deg  = float(parts[7]);  pitch2_deg = float(parts[8])

        # Choose which axis drives the bend (per bone), convert to radians
        bend1_raw = math.radians(pitch1_deg if BEND_AXIS_1=="pitch" else roll1_deg) * SIGN_P1 * GAIN_1
        bend2_raw = math.radians(pitch2_deg if BEND_AXIS_2=="pitch" else roll2_deg) * SIGN_P2 * GAIN_2

        # Auto-zero on first frame or after pressing 'z'
        if bend1_zero is None: bend1_zero = bend1_raw
        if bend2_zero is None: bend2_zero = bend2_raw
        bend1 = bend1_raw - bend1_zero
        bend2 = bend2_raw - bend2_zero

        # Smoothing
        if SMOOTH > 0:
            bend1 = (1.0-SMOOTH)*bend1_prev + SMOOTH*bend1
            bend2 = (1.0-SMOOTH)*bend2_prev + SMOOTH*bend2
        bend1_prev, bend2_prev = bend1, bend2

        # Optional clamp
        if USE_CLAMP:
            bend1 = math.radians(clamp(math.degrees(bend1), CLAMP_MIN_DEG, CLAMP_MAX_DEG))
            bend2 = math.radians(clamp(math.degrees(bend2), CLAMP_MIN_DEG, CLAMP_MAX_DEG))

        # HUD: see which axis is actually moving
        system = int(parts[10]); gyro = int(parts[11]); accel = int(parts[12]); mag = int(parts[13])
        hud.text = (f"Calib Sys:{system} G:{gyro} A:{accel} M:{mag} | Port:{PORT}\n"
                    f"MPU1 r={roll1_deg:.1f}° p={pitch1_deg:.1f}°  [bend axis={BEND_AXIS_1}]\n"
                    f"MPU2 r={roll2_deg:.1f}° p={pitch2_deg:.1f}°  [bend axis={BEND_AXIS_2}]\n"
                    "Keys: '1' toggle bone1 axis, '2' toggle bone2 axis, 'z' re-zero\n")

        # Wrist from BNO
        kB, upB = rpy_to_axis_up(rollB, pitchB, yawB)
        wrist.axis = kB; wrist.up = upB; wrist.pos = vector(0,0,0)

        # Fingers: yaw/roll from BNO, bend from chosen axis
        yawF = yawB; rollF = rollB

        k1, up1 = rpy_to_axis_up(rollF, bend1, yawF)
        bone1.axis = k1; bone1.up = up1
        bone1.pos  = wrist.pos + kB * (wrist_len/2.0 + bone1_len/2.0)

        k2, up2 = rpy_to_axis_up(rollF, bend2, yawF)
        bone2.axis = k2; bone2.up = up2
        bone2.pos  = bone1.pos + k1 * (bone1_len/2.0 + bone2_len/2.0)

        rate(60)

    except Exception as e:
        print("Error:", e)
        rate(60)
