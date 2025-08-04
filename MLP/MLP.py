import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.preprocessing import StandardScaler

class SimpleKalman:
    def __init__(self, q=0.01, r=0.1):
        self.q = q
        self.r = r
        self.p = 1.0
        self.x = 0.0

    def update(self, measurement):
        self.p += self.q
        k = self.p / (self.p + self.r)
        self.x += k * (measurement - self.x)
        self.p *= (1 - k)
        return self.x

X = np.load("sensor_inputs.npy")
y = np.load("joint_outputs.npy")

x_scaler = StandardScaler()
y_scaler = StandardScaler()

X_scaled = x_scaler.fit_transform(X)
y_scaled = y_scaler.fit_transform(y)

X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
y_tensor = torch.tensor(y_scaled, dtype=torch.float32)

class GloveMLP(nn.Module):
    def __init__(self, input_dim=23, output_dim=15):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
            # nn.ReLU(),
            # nn.Linear(128, 64),
            # nn.ReLU(),
            # nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.net(x)

# Training
model = GloveMLP()
loss_fn = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Split train
train_size = int(0.8 * len(X_tensor)) 
X_train, y_train = X_tensor[:train_size], y_tensor[:train_size]
X_val, y_val = X_tensor[train_size:], y_tensor[train_size:]

# Training
for epoch in range(300):
    model.train()
    preds = model(X_train)
    loss = loss_fn(preds, y_train)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 10 == 0:
        val_loss = loss_fn(model(X_val), y_val)
        print(f"Epoch {epoch}: Train Loss = {loss.item():.4f} | Val Loss = {val_loss.item():.4f}")

# Prediction
def predict_live(sensor_input):

    kalman_filters = [SimpleKalman() for _ in range(23)]
    
    filtered = np.array([kf.update(val) for kf, val in zip(kalman_filters, sensor_input)])

    scaled = x_scaler.transform([filtered])
    tensor = torch.tensor(scaled, dtype=torch.float32)
    with torch.no_grad():
        output = model(tensor).numpy()
    return y_scaler.inverse_transform(output)[0]  
