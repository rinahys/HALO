import numpy as np
import time
import serial
from scipy.spatial.transform import Rotation as R

class IMU_EKF:
    def __init__(self, dt=0.01):
        self.dt = dt
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.P = np.eye(4) * 0.01
        self.Q = np.eye(4) * 0.001
        self.R = np.eye(3) * 0.1

    def normalise_quaternion(self, q):
        return q / np.linalg.norm(q)

    def predict(self, gyro):
        wx, wy, wz = gyro
        Omega = 0.5 * np.array([
            [0, -wx, -wy, -wz],
            [wx, 0, wz, -wy],
            [wy, -wz, 0, wx],
            [wz, wy, -wx, 0]
        ])
        dq = Omega @ self.q
        self.q += dq * self.dt
        self.q = self.normalise_quaternion(self.q)

        F = np.eye(4) + Omega * self.dt
        self.P = F @ self.P @ F.T + self.Q

    def update(self, accel):
        q = self.q
        g = np.array([
            2*(q[1]*q[3] - q[0]*q[2]),
            2*(q[0]*q[1] + q[2]*q[3]),
            q[0]**2 - q[1]**2 - q[2]**2 + q[3]**2
        ])
        z = accel / np.linalg.norm(accel)
        y = z - g

        H = self.jacobian_gravity(q)
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)

        dq = K @ y
        self.q += dq
        self.q = self.normalise_quaternion(self.q)
        self.P = (np.eye(4) - K @ H) @ self.P

    def jacobian_gravity(self, q):
        q0, q1, q2, q3 = q
        return np.array([
            [-2*q2,  2*q3, -2*q0, 2*q1],
            [2*q1,   2*q0,  2*q3, 2*q2],
            [2*q0,  -2*q1, -2*q2, 2*q3]
        ])

    def get_quaternion(self):
        return self.q

    def get_euler(self):
        r = R.from_quat([self.q[1], self.q[2], self.q[3], self.q[0]])
        return r.as_euler('xyz', degrees=True)


class MultiIMUManager:
    def __init__(self, num_imus, dt=0.01):
        self.filters = [IMU_EKF(dt) for _ in range(num_imus)]

    def step(self, imu_data):
        
        for ekf, (gyro, accel) in zip(self.filters, imu_data):
            ekf.predict(gyro)
            ekf.update(accel)

    def get_all_euler(self):
        angles = []
        for ekf in self.filters:
            angles.extend(ekf.get_euler())
        return np.array(angles)

    def get_all_quaternions(self):
        quats = []
        for ekf in self.filters:
            quats.extend(ekf.get_quaternion())
        return np.array(quats)



def imu_reader(num_imus, dt, port="COM3", baud=115200):
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2)

    while True:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        try:
            values = list(map(float, line.split(',')))
            if len(values) != num_imus * 6:
                continue

            imu_data = []
            for i in range(num_imus):
                gx, gy, gz, ax, ay, az = values[i*6:(i+1)*6]

                gx, gy, gz = np.deg2rad([gx, gy, gz]) 
                ax, ay, az = np.array([ax, ay, az]) * 9.81

                imu_data.append((np.array([gx, gy, gz]), np.array([ax, ay, az])))

            yield imu_data
        except ValueError:
            continue


if __name__ == "__main__":
    num_imus = 3   
    dt = 0.01
    port = "COM3"  
    baud = 115200  
    manager = MultiIMUManager(num_imus, dt)

    for imu_data in imu_reader(num_imus, dt, port=port, baud=baud):
        manager.step(imu_data)
        euler_angles = manager.get_all_euler()
        print("Euler angles:", euler_angles)