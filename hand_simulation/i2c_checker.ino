#include <Wire.h>

#define TCAADDR1 0x70   // First TCA9548A
#define TCAADDR2 0x71   // Second TCA9548A

// Select channel on TCA
void tcaSelect(uint8_t tcaAddr, uint8_t channel) {
  if (channel > 7) return;
  Wire.beginTransmission(tcaAddr);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// I2C scan function
void i2cScan() {
  byte error, address;
  int nDevices = 0;

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("  - Device found at 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      nDevices++;
    }
  }

  if (nDevices == 0) {
    Serial.println("  - No I2C devices found");
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }   // Wait for Serial on some boards

  // Important: ESP32 needs explicit SDA/SCL pins!
  Wire.begin(21, 22);   // SDA=GPIO21, SCL=GPIO22

  delay(2000);
  Serial.println("========== I2C SCANNER ==========");

  // Scan the main bus
  Serial.println("Main I2C bus scan:");
  i2cScan();

  // Scan all channels of TCA #1
  Serial.println("\n--- Scanning TCA9548A #1 (0x70) ---");
  for (uint8_t ch = 0; ch < 8; ch++) {
    Serial.print("Channel "); Serial.println(ch);
    tcaSelect(TCAADDR1, ch);
    delay(5);
    i2cScan();
  }

  // Scan all channels of TCA #2
  Serial.println("\n--- Scanning TCA9548A #2 (0x71) ---");
  for (uint8_t ch = 0; ch < 8; ch++) {
    Serial.print("Channel "); Serial.println(ch);
    tcaSelect(TCAADDR2, ch);
    delay(5);
    i2cScan();
  }

  Serial.println("========== DONE ==========");
}

void loop() {
  // nothing
}