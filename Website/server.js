const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const os = require("os");

const app = express();
app.use(express.static(__dirname));
const server = http.createServer(app);

const espWSS = new WebSocket.Server({ noServer: true });
const browserWSS = new WebSocket.Server({ noServer: true });
const browserClients = [];

//upgrading http request to create persistent connection
server.on("upgrade", (req, socket, head) => {
  if (req.url === "/esp") {
    espWSS.handleUpgrade(req, socket, head, (ws) => {
      espWSS.emit("connection", ws, req);
    });
  } else if (req.url === "/browser") {
    browserWSS.handleUpgrade(req, socket, head, (ws) => {
      browserWSS.emit("connection", ws, req);
    });
  } else {
    socket.destroy();
  }
});

// connecting to esp32
espWSS.on("connection", (ws) => {
  console.log("[Server] ESP32 connected");

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());
      data.server_ts = Date.now();
      const out = JSON.stringify(data);

      // Forward only if ESP is alive
      browserClients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(out);
        }
      });
    } catch (e) {
      console.error("Invalid JSON from ESP:", e.message);
    }
  });

  ws.on("close", () => {
    console.log("[Server] ESP32 disconnected");

    // debug notice of disconnection
    const notice = JSON.stringify({ type: "esp_status", status: "disconnected" });
    browserClients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(notice);
      }
    });
  });
});


//connecting to browser
browserWSS.on("connection", (ws) => {
  console.log("[Server] Browser connected");
  browserClients.push(ws);

  ws.on("close", () => {
    const idx = browserClients.indexOf(ws);
    if (idx !== -1) browserClients.splice(idx, 1);
    console.log("[Server] Browser disconnected");
  });
});

// starting the server
const PORT = 3000;
server.listen(PORT, () => {
  console.log(`[Server] Running at http://localhost:${PORT}/index.html`);
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === "IPv4" && !iface.internal) {
        console.log(`  LAN: http://${iface.address}:${PORT}/index.html`);
      }
    }
  }
});
