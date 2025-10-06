#only bno test 1-> python side  

from vpython import *
import serial
import time
import math
import numpy as np

# ---------- SERIAL SETUP ----------
ad = serial.Serial('COM4', 115200)
time.sleep(1)

# ---------- SCENE SETUP ----------
scene.title = "BNO055 Hand Simulation"
scene.width = 1200
scene.height = 900
scene.background = color.black      
scene.range = 5
scene.forward = vector(-1, -0.8, -0.6)
scene.up = vector(0, 1, 0)

# ---------- REFERENCE AXES ----------
xaxis = arrow(length=2, shaftwidth=0.05, color=color.red, axis=vector(1, 0, 0))
yaxis = arrow(length=2, shaftwidth=0.05, color=color.green, axis=vector(0, 1, 0))
zaxis = arrow(length=2, shaftwidth=0.05, color=color.blue, axis=vector(0, 0, 1))

# ---------- HAND MODEL ----------
palm = box(length=1.5, height=0.2, width=1, color=color.orange)
hand = compound([palm])

# ---------- ORIENTATION ARROWS (hand's local axes) ----------
frontArrow = arrow(length=1.2, shaftwidth=0.07, color=color.orange)  #
upArrow = arrow(length=1, shaftwidth=0.07, color=color.magenta)
sideArrow = box(length=4, shaftwidth=0.07, color=color.orange)     # 

# ---------- MANUAL ALIGNMENT OFFSETS ----------
yaw_offset = math.radians(180)      # rotate around vertical axis (Y)
pitch_offset = math.radians(0)      # tilt up/down
roll_offset = math.radians(0)       # rotate around forward axis

# ---------- MAIN LOOP ----------
while True:
    try:
        while ad.in_waiting == 0:
            pass

        dataPacket = ad.readline().decode('utf-8').strip()
        splitPacket = dataPacket.split(',')

        if len(splitPacket) < 4:
            continue

        q0 = float(splitPacket[0])
        q1 = float(splitPacket[1])
        q2 = float(splitPacket[2])
        q3 = float(splitPacket[3])

        # ---------- Convert quaternion to Euler ----------
        roll = -math.atan2(2 * (q0*q1 + q2*q3), 1 - 2 * (q1**2 + q2**2))
        pitch = math.asin(2 * (q0*q2 - q3*q1))
        yaw = -math.atan2(2 * (q0*q3 + q1*q2), 1 - 2 * (q2**2 + q3**2)) - np.pi / 2

        # ---------- Apply manual offsets ----------
        yaw += yaw_offset
        pitch += pitch_offset
        roll += roll_offset

        # ---------- Update 3D orientation ----------
        rate(50)
        k = vector(math.cos(yaw)*math.cos(pitch),
                   math.sin(pitch),
                   math.sin(yaw)*math.cos(pitch))
        y = vector(0, 1, 0)
        s = cross(k, y)
        v = cross(s, k)
        vrot = v*math.cos(roll) + cross(k, v)*math.sin(roll)

        # Update arrows
        frontArrow.axis = k * 1.2
        sideArrow.axis = cross(k, vrot) * 4  
        upArrow.axis = vrot

        # Update hand
        hand.axis = k
        hand.up = vrot

        # Keep arrows at hand position
        frontArrow.pos = hand.pos
        sideArrow.pos = hand.pos
        upArrow.pos = hand.pos

    except Exception as e:
        print(" Error:", e)
        pass

