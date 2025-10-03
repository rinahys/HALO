from vpython import *
import serial, time, math

arduino = serial.Serial('COM3', 115200)  # adjust port!
time.sleep(1)

scene.range = 6
scene.background = color.white
scene.width = 1200
scene.height = 800
scene.forward = vector(-1, -1, -1)

# Two IMU boxes
bno_box = box(length=4, width=2, height=0.2, opacity=0.7, color=color.orange, pos=vector(-2,0,0))
mpu_box = box(length=4, width=2, height=0.2, opacity=0.7, color=color.cyan, pos=vector(2,0,0))

while True:
    try:
        while arduino.in_waiting == 0:
            pass
        line = arduino.readline().decode('utf-8').strip()
        vals = line.split(",")

        if len(vals) < 11:
            continue

        # --- BNO055 quaternion ---
        q0, q1, q2, q3 = [float(v) for v in vals[0:4]]

        rollB = -math.atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2))
        pitchB = math.asin(2*(q0*q2 - q3*q1))
        yawB = -math.atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3))

        #mpu roll pitch yaw 
        rollM = float(vals[4]) * math.pi/180
        pitchM = float(vals[5]) * math.pi/180
        yawM = float(vals[6]) * math.pi/180

        #####test fixing drift and roll!!!!!!!!!!!!!!
        yawM = yawB
        rollM = rollB

        # --- Calibration status ---
        system = int(vals[7])
        gyro   = int(vals[8])
        accel  = int(vals[9])
        mag    = int(vals[10])

        print(f"Calibration -> Sys:{system} G:{gyro} A:{accel} M:{mag}")

        # --- Update BNO box orientation ---
        kB = vector(math.cos(yawB)*math.cos(pitchB),
                    math.sin(pitchB),
                    math.sin(yawB)*math.cos(pitchB))
        y = vector(0,1,0)
        s = cross(kB,y); v = cross(s,kB)
        vrotB = v*math.cos(rollB) + cross(kB,v)*math.sin(rollB)

        bno_box.axis = kB
        bno_box.up = vrotB

        # --- Update MPU box orientation ---
        kM = vector(math.cos(yawM)*math.cos(pitchM),
                    math.sin(pitchM),
                    math.sin(yawM)*math.cos(pitchM))
        s = cross(kM,y); v = cross(s,kM)
        vrotM = v*math.cos(rollM) + cross(kM,v)*math.sin(rollM)

        mpu_box.axis = kM
        mpu_box.up = vrotM

        rate(50)

    except Exception as e:
        print("Error:", e)
        pass
