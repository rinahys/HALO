import torch
import torch.nn.functional as F
import math

class IMU_EKF_Torch:
    def __init__(self, dt=0.01, device='cpu'):
        self.device = device
        self.dt = dt
        self.q = torch.tensor([1., 0., 0., 0.], device=device)  # w, x, y, z
        self.P = torch.eye(4, device=device) * 0.01
        self.Q = torch.eye(4, device=device) * 0.001
        self.R = torch.eye(3, device=device) * 0.1

    def normalize_quaternion(self, q):
        return q / torch.norm(q)

    def predict(self, gyro):
        wx, wy, wz = gyro
        Omega = 0.5 * torch.tensor([
            [0., -wx, -wy, -wz],
            [wx, 0., wz, -wy],
            [wy, -wz, 0., wx],
            [wz, wy, -wx, 0.]
        ], device=self.device)

        dq = Omega @ self.q
        self.q = self.q + dq * self.dt
        self.q = self.normalize_quaternion(self.q)

        F = torch.eye(4, device=self.device) + Omega * self.dt
        self.P = F @ self.P @ F.T + self.Q

    def update(self, accel):
        q = self.q
        g = torch.tensor([
            2*(q[1]*q[3] - q[0]*q[2]),
            2*(q[0]*q[1] + q[2]*q[3]),
            q[0]**2 - q[1]**2 - q[2]**2 + q[3]**2
        ], device=self.device)

        z = accel / torch.norm(accel)
        y = z - g

        H = self.jacobian_gravity(q)
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ torch.linalg.inv(S)

        dq = K @ y
        self.q = self.q + dq
        self.q = self.normalize_quaternion(self.q)
        self.P = (torch.eye(4, device=self.device) - K @ H) @ self.P

    def jacobian_gravity(self, q):
        q0, q1, q2, q3 = q
        return torch.tensor([
            [-2*q2,  2*q3, -2*q0, 2*q1],
            [2*q1,   2*q0,  2*q3, 2*q2],
            [2*q0,  -2*q1, -2*q2, 2*q3]
        ], device=self.device)

    def get_orientation(self):
        return self.q  # Returns [w, x, y, z]
    
    def torch_quat_conjugate(q):
        # Input q: [w, x, y, z]
        return torch.tensor([q[0], -q[1], -q[2], -q[3]], device=q.device)

    def torch_quat_multiply(q1, q2):
        # Hamilton product
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return torch.tensor([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ], device=q1.device)
    
    def relative_orientation(base_q, tip_q):
        base_conj = torch_quat_conjugate(base_q)
        return torch_quat_multiply(base_conj, tip_q)

    def quat_to_euler(q):
    # Input: [w, x, y, z]
        w, x, y, z = q
        t0 = 2.0 * (w * x + y * z)
        t1 = 1.0 - 2.0 * (x * x + y * y)
        roll = torch.atan2(t0, t1)

        t2 = 2.0 * (w * y - z * x)
        t2 = torch.clamp(t2, -1.0, 1.0)
        pitch = torch.asin(t2)

        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        yaw = torch.atan2(t3, t4)

        return torch.rad2deg(torch.stack([roll, pitch, yaw]))  # in degree

