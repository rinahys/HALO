from vpython import *
import serial
import time
import math

# --- Setup Serial ---
arduino = serial.Serial('COM3', 115200)  # change COM port as needed
time.sleep(1)

# --- VPython scene setup ---
scene.range = 5
scene.background = color.white
scene.width = 1200
scene.height = 800
scene.forward = vector(-1, -1, -1)

# Reference arrows
xarrow = arrow(length=2, shaftwidth=0.1, color=color.red, axis=vector(1,0,0))
yarrow = arrow(length=2, shaftwidth=0.1, color=color.green, axis=vector(0,1,0))
zarrow = arrow(length=2, shaftwidth=0.1, color=color.blue, axis=vector(0,0,1))

# Object (board)
board = box(length=4, width=2, height=0.2, opacity=0.7, color=color.cyan)
imu = compound([board])

# --- Loop ---
while True:
    try:
        while arduino.in_waiting == 0:
            pass
        data = arduino.readline().decode('utf-8').strip()
        split_data = data.split()

        if len(split_data) < 3:
            continue

        roll = float(split_data[0]) * math.pi/180.0
        pitch = float(split_data[1]) * math.pi/180.0
        yaw = float(split_data[2]) * math.pi/180.0

        # Rotation math
        k = vector(math.cos(yaw)*math.cos(pitch),
                   math.sin(pitch),
                   math.sin(yaw)*math.cos(pitch))
        y = vector(0,1,0)
        s = cross(k,y)
        v = cross(s,k)
        vrot = v*math.cos(roll) + cross(k,v)*math.sin(roll)

        rate(50)
        imu.axis = k
        imu.up = vrot

    except Exception as e:
        print("Error:", e)
        pass
