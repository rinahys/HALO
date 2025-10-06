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
scene.background = color.gray(0.9)
scene.forward = vector(-1, -1, -1)
scene.range = 5

# ---------- REFERENCE AXES ----------
xaxis = arrow(length=2, shaftwidth=0.05, color=color.red, axis=vector(1, 0, 0))
yaxis = arrow(length=2, shaftwidth=0.05, color=color.green, axis=vector(0, 1, 0))
zaxis = arrow(length=2, shaftwidth=0.05, color=color.blue, axis=vector(0, 0, 1))

# ---------- HAND MODEL ----------
# Simple 3D block hand with a palm and fingers
palm = box(length=1.5, height=0.2, width=1, color=color.orange)

fingers = []
for i in range(5):
    x_offset = -0.6 + i * 0.3
    finger = cylinder(pos=vector(x_offset, 0.1, 0.5), axis=vector(0, 0.5, 0), radius=0.05, color=color.yellow)
    fingers.append(finger)

# Combine palm and fingers
hand = compound([palm] + fingers)

# ---------- ORIENTATION ARROWS (hand's local axes) ----------
frontArrow = arrow(length=2, shaftwidth=0.07, color=color.purple)
upArrow = arrow(length=1, shaftwidth=0.07, color=color.magenta)
sideArrow = arrow(length=1.5, shaftwidth=0.07, color=color.orange)

scene.forward = vector(-1, -0.8, -0.6)  # tweak direction
scene.up = vector(0, 1, 0)

# ---------- MAIN LOOP ----------
while True:
    try:
        while ad.in_waiting == 0:
            pass

        # Read and parse the serial data
        dataPacket = ad.readline().decode('utf-8').strip()
        splitPacket = dataPacket.split(',')

        if len(splitPacket) < 4:
            continue

        q0 = float(splitPacket[0])
        q1 = float(splitPacket[1])
        q2 = float(splitPacket[2])
        q3 = float(splitPacket[3])

        # ---------- Convert quaternion to Euler angles ----------
        roll = -math.atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 ** 2 + q2 ** 2))
        pitch = math.asin(2 * (q0 * q2 - q3 * q1))
        yaw = -math.atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 ** 2 + q3 ** 2)) - np.pi / 2

        # ---------- Update 3D hand orientation ----------
        rate(50)

        # Forward direction
        k = vector(math.cos(yaw) * math.cos(pitch), math.sin(pitch), math.sin(yaw) * math.cos(pitch))
        y = vector(0, 1, 0)
        s = cross(k, y)
        v = cross(s, k)
        vrot = v * math.cos(roll) + cross(k, v) * math.sin(roll)

        # Update arrows
        frontArrow.axis = k * 2
        upArrow.axis = vrot
        sideArrow.axis = cross(k, vrot)

        # Update hand orientation
        hand.axis = k
        hand.up = vrot

        # Keep arrows attached to hand
        frontArrow.pos = hand.pos
        upArrow.pos = hand.pos
        sideArrow.pos = hand.pos

    except Exception as e:
        print(" Error:", e)
        pass

