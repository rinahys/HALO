#include <Wire.h>
#include <MPU6050.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_Sensor.h>

#define TCA_ADDR 0x70
#define NUM_MPU 8   // 8 MPU6050 

MPU6050 mpus[NUM_MPU]; 
Adafruit_BNO055 bno = Adafruit_BNO055(55);

// Filter state for each MPU6050
float roll[NUM_MPU]  = {0};
float pitch[NUM_MPU] = {0};
float yaw[NUM_MPU]   = {0};

unsigned long lastUs = 0;
float alpha = 0.98; // Complementary filter

void tcaSelect(uint8_t channel) {
    if (channel > 7) return;
    Wire.beginTransmission(TCA_ADDR);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

void setup() {
    Serial.begin(1000000);
    Wire.begin();
    Wire.setClock(400000);

    // Init MPU6050s on TCA channels 1–8 (fingers)
    for (int i = 0; i < NUM_MPU; i++) {
        tcaSelect(i + 1); // use channels 1-8 for MPU6050s
        mpus[i].initialize();
        if (!mpus[i].testConnection()) {
            Serial.print("MPU6050 ");
            Serial.print(i);
            Serial.println(" not found");
        }
    }

    // Init BNO055 on channel 0
    tcaSelect(0);
    if (!bno.begin()) {
        Serial.println("BNO055 not detected!");
    } else {
        bno.setExtCrystalUse(true);
    }

    lastUs = micros();
}

void loop() {
    static unsigned long lastPrint = 0;
    unsigned long now = micros();
    float dt = (now - lastUs) / 1e6;
    lastUs = now;

    int16_t ax, ay, az, gx, gy, gz;

    // Run at ~100 Hz
    if (now - lastPrint >= 10000) {
        lastPrint = now;

        Serial.print("imu:"); // start line

        // ---------- BNO055 (wrist) ----------
        tcaSelect(0);
        sensors_event_t orientationData, angVelData, accelData, magData;
        bno.getEvent(&orientationData, Adafruit_BNO055::VECTOR_EULER);
        Serial.print(orientationData.orientation.x); Serial.print(","); // Roll
        Serial.print(orientationData.orientation.y); Serial.print(","); // Pitch
        Serial.print(orientationData.orientation.z); Serial.print(","); // Yaw

        // ---------- MPU6050 (fingers) ----------
        for (int i = 0; i < NUM_MPU; i++) {
            tcaSelect(i + 1);

            mpus[i].getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

            // Accelerometer angles
            float accRoll  = atan2(ay, az) * 180 / PI;
            float accPitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180 / PI;

            // Gyroscope rates
            float gyroRollRate  = gx / 131.0;
            float gyroPitchRate = gy / 131.0;
            float gyroYawRate   = gz / 131.0;

            // Complementary filter
            roll[i]  = alpha * (roll[i]  + gyroRollRate * dt) + (1 - alpha) * accRoll;
            pitch[i] = alpha * (pitch[i] + gyroPitchRate * dt) + (1 - alpha) * accPitch;
            yaw[i]  += gyroYawRate * dt; // Yaw uses gyro only

            // Send values
            Serial.print(roll[i]); Serial.print(",");
            Serial.print(pitch[i]); Serial.print(",");
            Serial.print(yaw[i]);

            if (i < NUM_MPU - 1) Serial.print(",");
        }

        Serial.println(); // end of line
    }
}
