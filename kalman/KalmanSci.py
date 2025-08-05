import numpy as np
from scipy.spatial.transform import Rotation as R

class IMU_EKF:
    def __init__(self, dt = 0.01):
        self.dt = dt
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.p = np.eye(4) * 0.01
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
        dq = Omega @ self.q #updates quaternion basd on rotation rate
        self.q += dq * self.dt
        self.q = self.normalise_quaternion(self.q)

        #linearise and update P
        F = np.eye(4) + Omega * self.dt
        self.P = F @ self.P @ F.T + self.Q

    def update(self, accel):
        q = self.q
        g = np.array([
            2*(q[1]*q[3] - q[0]*q[2]),
            2*(q[0]*q[1] + q[2]*q[3]),
            q[0]**2 - q[1]**2 - q[2]**2 + q[3]**2
        ])

        z = accel / np.linalg.norm(accel) #normalise
        y = z - g #innovation

        H = self.jacobian_gravity(q) 
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S) #kalman gain

        dq = K @ y
        self.q += dq
        self.q = self.normalise_quaternion(self.q)
        self.P = (np.eye(4) - K @ H) @ self.P #kalman update

    def jacobian_gravity(self, q):
        q0, q1, q2, q3 = q
        return np.array([
            [-2*q2,  2*q3, -2*q0, 2*q1],
            [2*q1,   2*q0,  2*q3, 2*q2],
            [2*q0,  -2*q1, -2*q2, 2*q3]
        ])
    
    def get_orientation(self):
        return self.q 
        