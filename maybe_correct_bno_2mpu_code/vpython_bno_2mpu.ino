//this code is when ur testing with 1 bno, and 2 mpus, ardunio side for the vpython test

#include <Wire.h>
#include <MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// ---------- I2C & MUX ----------
#define I2C_SDA   21
#define I2C_SCL   22
#define TCA_ADDR  0x70
// Channels: 1 = distal, 2 = proximal (per your wiring)
#define CH_DISTAL   0
#define CH_PROXIMAL 2


// ---------- Sensors ----------
Adafruit_BNO055 bno(55);         // default address 0x28
MPU6050 mpu(0x68);               // same address on both channels; mux isolates

// ---------- State ----------
unsigned long lastTime;
float dt = 0.01f;
const float alpha = 0.98f;       // complementary filter

// Proximal (CH_PROXIMAL)
float roll1 = 0, pitch1 = 0, yaw1 = 0;
// Distal (CH_DISTAL)
float roll2 = 0, pitch2 = 0, yaw2 = 0;

// ---------- Helpers ----------
static inline void tcaSelect(uint8_t ch) {
  if (ch > 7) return;
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << ch);           // enable only this channel
  Wire.endTransmission();
  delayMicroseconds(300);
}

bool initMPUOnChannel(uint8_t ch) {
  tcaSelect(ch);
  mpu.initialize();
  return mpu.testConnection();
}

void updateMPUOnChannel(uint8_t ch, float &roll, float &pitch, float &yaw, float dt) {
  tcaSelect(ch);

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Scale: ±2g (16384 LSB/g), ±250 dps (131 LSB/°/s) — adjust if you changed ranges
  float accX = ax / 16384.0f;
  float accY = ay / 16384.0f;
  float accZ = az / 16384.0f;
  float gyroX = gx / 131.0f;     // deg/s
  float gyroY = gy / 131.0f;     // deg/s
  float gyroZ = gz / 131.0f;     // deg/s

  float rollAcc  = atan2f(accY, accZ) * 180.0f / PI;
  float pitchAcc = atan2f(-accX, sqrtf(accY*accY + accZ*accZ)) * 180.0f / PI;

  // Complementary filter on roll & pitch (deg)
  roll  = alpha * (roll  + gyroX * dt) + (1.0f - alpha) * rollAcc;
  pitch = alpha * (pitch + gyroY * dt) + (1.0f - alpha) * pitchAcc;

  // Yaw from integrating gyro Z (deg) 
  yaw   += gyroZ * dt;
}

void setup() {
  Serial.begin(115200);
  delay(400);

  // ESP32 I2C
  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(400000);

  // Deselect all mux channels
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(2);

  // BNO055 on main bus (not behind mux)
  bool bno_ok = bno.begin();     
  if (!bno_ok) {
    Serial.println("ERR: BNO055 not detected (check wiring/addr ADR pin).");
  } else {
    bno.setExtCrystalUse(true);
  }

  // Init both MPUs via TCA channels
  bool mpu_prox_ok = initMPUOnChannel(CH_PROXIMAL);
  bool mpu_dist_ok = initMPUOnChannel(CH_DISTAL);

  if (mpu_prox_ok) { tcaSelect(CH_PROXIMAL); /* mpu.setDLPFMode(3); mpu.setRate(4); */ }
  if (mpu_dist_ok) { tcaSelect(CH_DISTAL);   /* mpu.setDLPFMode(3); mpu.setRate(4); */ }

  Serial.print("INIT  BNO:"); Serial.print(bno_ok ? "OK" : "FAIL");
  Serial.print("  MPU@CH");   Serial.print(CH_PROXIMAL); Serial.print(":"); Serial.print(mpu_prox_ok ? "OK" : "FAIL");
  Serial.print("  MPU@CH");   Serial.print(CH_DISTAL);   Serial.print(":"); Serial.println(mpu_dist_ok ? "OK" : "FAIL");

  lastTime = millis();
}

void loop() {
  // Time step
  unsigned long now = millis();
  dt = (now - lastTime) / 1000.0f;
  lastTime = now;
  if (dt <= 0.0f || dt > 0.1f) dt = 0.01f; // clamp for stability

  // Read BNO055 quaternion + calibration
  imu::Quaternion q = bno.getQuat();
  uint8_t system=0, gyro=0, accel=0, mag=0;
  bno.getCalibration(&system, &gyro, &accel, &mag);

  // Update each MPU via its TCA channel
  updateMPUOnChannel(CH_PROXIMAL, roll1, pitch1, yaw1, dt);
  updateMPUOnChannel(CH_DISTAL,   roll2, pitch2, yaw2, dt);

  // CSV: q0,q1,q2,q3, r1,p1, r2,p2, sys,gyro,accel,mag
  Serial.print("<");
  Serial.print(q.w(), 6);  Serial.print(',');
  Serial.print(q.x(), 6);  Serial.print(',');
  Serial.print(q.y(), 6);  Serial.print(',');
  Serial.print(q.z(), 6);  Serial.print(',');

  Serial.print(roll1, 6);  Serial.print(',');
  Serial.print(pitch1, 6); Serial.print(',');


  Serial.print(roll2, 6);  Serial.print(',');
  Serial.print(pitch2, 6); Serial.print(',');


  Serial.print(system);    Serial.print(',');
  Serial.print(gyro);      Serial.print(',');
  Serial.print(accel);     Serial.print(',');
  Serial.print(mag);
  Serial.println(">");

  delay(10); // ~200 Hz output target
}
