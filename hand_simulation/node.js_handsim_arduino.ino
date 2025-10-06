#include <Wire.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <MPU6050.h>
#include <Adafruit_BNO055.h>
#include <MadgwickAHRS.h>

//connecting to wifi 
const char* ssid = "BT-2NAJRR";
const char* password = "evaxHphvyT3qHE";

//node js server connection
const char* NODE_SERVER_IP = "192.168.1.168"; // change with your own pc's ip
const uint16_t NODE_PORT = 3000;
WebSocketsClient webSocket;

#define RATE_HZ 50                  
#define SEND_PERIOD_MS (1000 / RATE_HZ)
#define DEG_TO_RAD 0.01745329251f
unsigned long lastSend = 0;

#define NUM_MPU1 6 //mux1
#define NUM_MPU2 4 //mux2
MPU6050 mpus1[NUM_MPU1];
MPU6050 mpus2[NUM_MPU2];
Madgwick filter1[NUM_MPU1];
Madgwick filter2[NUM_MPU2];
Adafruit_BNO055 bno = Adafruit_BNO055(55);

//multiplexers
#define TCA1 0x70
#define TCA2 0x71
uint8_t mux1_channels[] = {0,2,3,4,5,6};
uint8_t mux2_channels[] = {0,1,6,7};

//function to select a channel in the mux
void tcaSelect(uint8_t addr, uint8_t channel) {
  if(channel > 7) return;
  Wire.beginTransmission(addr);
  Wire.write(1 << channel);
  Wire.endTransmission();
}


void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("Connected to Node.js server");
      break;

    case WStype_DISCONNECTED:
      Serial.println("Disconnected from Node.js server");
      break;
    }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  WiFi.setSleep(false);

  // connecting to wifi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while(WiFi.status() != WL_CONNECTED){
    delay(100);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // starting WebSocket client
  webSocket.begin(NODE_SERVER_IP, NODE_PORT, "/esp");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(2000);
  webSocket.enableHeartbeat(10000, 2000, 1);

  // Initialise IMUs on mux1
  for(int i = 0; i < NUM_MPU1; i++){
    tcaSelect(TCA1, mux1_channels[i]);
    mpus1[i].initialize();
    filter1[i].begin(RATE_HZ);

    if(!mpus1[i].testConnection()){
      Serial.print("imu ");
      Serial.print(i);
      Serial.println(" on mux1 not responding");
    }
  }

  // Initialise IMUs on mux2
  for(int i = 0; i < NUM_MPU2; i++){
    tcaSelect(TCA2, mux2_channels[i]);
    mpus2[i].initialize();
    filter2[i].begin(RATE_HZ);

    if(!mpus2[i].testConnection()){
      Serial.print("imu ");
      Serial.print(i);
      Serial.println("on mux2 not responding");
    }
  }

  // Initialize BNO055 , wrist
  if(!bno.begin()) Serial.println(" BNO055 not found");
  else bno.setExtCrystalUse(true);
}


void loop() {
  webSocket.loop();

  unsigned long now = millis();
  if(now - lastSend < SEND_PERIOD_MS){ return; }
  lastSend = now;

  //creating json
  StaticJsonDocument<3072> doc; 
  static char outBuf[3072];
  static uint32_t seq = 0;

  doc["seq"] = seq++;
  doc["esp_ts"] = millis();

  // Wrist
  imu::Quaternion q = bno.getQuat();
  doc["wrist"]["x"] = q.x();
  doc["wrist"]["y"] = q.y();
  doc["wrist"]["z"] = q.z();
  doc["wrist"]["w"] = q.w();

  // Fingers
  JsonArray fingers = doc.createNestedArray("fingers");
  int16_t ax, ay, az, gx, gy, gz;

  // Mux1
  for(int i = 0; i < NUM_MPU1; i++){
    tcaSelect(TCA1, mux1_channels[i]);
    mpus1[i].getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    filter1[i].updateIMU(
      gx*DEG_TO_RAD/131.0f, gy*DEG_TO_RAD/131.0f, gz*DEG_TO_RAD/131.0f,
      ax/16384.0f, ay/16384.0f, az/16384.0f
    );
    JsonObject f = fingers.createNestedObject();
    f["x"] = filter1[i].q1;
    f["y"] = filter1[i].q2;
    f["z"] = filter1[i].q3;
    f["w"] = filter1[i].q0;
  }

  // Mux2
  for(int i = 0; i < NUM_MPU2; i++){
    tcaSelect(TCA2, mux2_channels[i]);
    mpus2[i].getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    filter2[i].updateIMU(
      gx*DEG_TO_RAD/131.0f, gy*DEG_TO_RAD/131.0f, gz*DEG_TO_RAD/131.0f,
      ax/16384.0f, ay/16384.0f, az/16384.0f
    );
    JsonObject f = fingers.createNestedObject();
    f["x"] = filter2[i].q1;
    f["y"] = filter2[i].q2;
    f["z"] = filter2[i].q3;
    f["w"] = filter2[i].q0;
  }

  // Sending the json
  size_t n = serializeJson(doc, outBuf, sizeof(outBuf));
  if(webSocket.isConnected()){
    webSocket.sendTXT(outBuf, n);
    Serial.println("IMU packet sent"); // message to debug in arduino
  }
}
