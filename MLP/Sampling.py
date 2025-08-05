import numpy as np

N = 1000
input_dim = 23   # 10 encoders + 4 flex + 9 IMU
output_dim = 15  # joint values

X = np.random.rand(N, input_dim)

y = np.random.uniform(-1, 1, size=(N, output_dim))

np.save("sensor_inputs.npy", X)
np.save("joint_outputs.npy", y)

print("dataset saved.")
