//run this in terminal: node server.js
//npm install express body-parser ws



//in terminal to run backend server :node server.js

const WebSocket = require('ws');
const express = require('express');
const bodyParser = require('body-parser');

const PORT = 3000;
const HTTP_PORT = 3001;

const wss = new WebSocket.Server({ port: PORT });
const app = express();
app.use(bodyParser.json());

console.log(` WebSocket server running on ws://localhost:${PORT}`);


wss.on('connection', (ws) => {
  console.log(" A browser connected");

  // Sends a simulated gesture (for testing so ignore if i ll remove after)
  const gestureList = ['Fist', 'Peace', 'Open Palm', 'Thumbs Up'];
 
  const interval = setInterval(() => {
    const randomGesture = gestureList[Math.floor(Math.random() * gestureList.length)];
   
    const message = JSON.stringify({
      source: "server",
      gesture: randomGesture,
      angles: [30, 45, 50, 60, 20]
    });

    ws.send(message);
    console.log(" Sent to browser:", message);
  }, 3000);

  ws.on('close', () => {
    console.log(" Browser disconnected");
    clearInterval(interval);
  });


  ws.on('error', (err) => {
    console.error("WebSocket error:", err);
  });
});

// Handle incoming ESP32 data via HTTP POST
app.post('/send-data', (req, res) => {
  const data = req.body;
  console.log(" Received from esp32:", data);

  // Forward the data to all connected browser clients
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });

  res.sendStatus(200);
});


app.listen(HTTP_PORT, () => {
  console.log(` HTTP server running on http://localhost:${HTTP_PORT}`);
});

