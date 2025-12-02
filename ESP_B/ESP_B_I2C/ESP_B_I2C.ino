#include <Wire.h>

// ================================
// I2C Slave Configuration
// ================================
#define I2C_SLAVE_ADDRESS 0x08

#define RECEIVE_SIZE 10    // 10 byte from Raspberry
#define SEND_SIZE    16    // 16 byte to Raspberry

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ================================
// Sensor / Control Data Variables
// ================================
float pressure = 0.0;
float reservedIn = 0.0;
uint8_t pump1Status = 0;
uint8_t pump2Status = 0;

uint8_t rod1_pos = 0;
uint8_t rod2_pos = 0;
uint8_t rod3_pos = 0;
float thermalKW = 0.0;
float resFloat1 = 0.0;
float resFloat2 = 0.0;

// ================================
// I2C ISR HANDLERS (No Serial here!)
// ================================
void onReceiveHandler(int len) {
  if (len <= 0 || len > RECEIVE_SIZE) return;

  for (int i = 0; i < len; i++) {
    receiveBuffer[i] = Wire.read();
  }
  receiveLength = len;
  newDataFlag = true;
}

void onRequestHandler() {
  Wire.write(sendBuffer, SEND_SIZE);
}

// ================================
// Setup
// ================================
void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("\nESP32 I2C Slave Starting...");
  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onReceive(onReceiveHandler);
  Wire.onRequest(onRequestHandler);

  Serial.println("I2C Ready. Waiting for Raspberry Pi...");
}

// ================================
// Main Loop
// ================================
void loop() {
  // When new data received from Raspberry
    if (newDataFlag) {
    newDataFlag = false;

    // Buat buffer lokal agar volatile hilang
    uint8_t buf[RECEIVE_SIZE];
    memcpy(buf, (const void*)receiveBuffer, RECEIVE_SIZE);

    memcpy(&pressure,   &buf[0], 4);
    memcpy(&reservedIn, &buf[4], 4);
    pump1Status = buf[8];
    pump2Status = buf[9];


    Serial.println("\n--- DATA RECEIVED FROM RASPBERRY ---");
    Serial.printf("Pressure: %.2f bar\n", pressure);
    Serial.printf("Reserved : %.2f\n", reservedIn);
    Serial.printf("Pump1    : %d\n", pump1Status);
    Serial.printf("Pump2    : %d\n", pump2Status);

    // Simulasikan hasil reaktor (boleh diganti sesuai logika Anda)
    rod1_pos = (pressure > 100) ? 30 : 60;
    rod2_pos = (pressure > 100) ? 35 : 65;
    rod3_pos = (pressure > 100) ? 40 : 70;
    thermalKW = pressure * 12.5;   // contoh rumus output

    // Pack 16 bytes balasan
    sendBuffer[0] = rod1_pos;
    sendBuffer[1] = rod2_pos;
    sendBuffer[2] = rod3_pos;
    sendBuffer[3] = 0;   // reserved byte

    memcpy(&sendBuffer[4],  &thermalKW, 4);
    memcpy(&sendBuffer[8],  &resFloat1, 4);
    memcpy(&sendBuffer[12], &resFloat2, 4);

    Serial.println("--- RESPONSE UPDATED ---");
    Serial.printf("Rod1=%d  Rod2=%d  Rod3=%d\n", rod1_pos, rod2_pos, rod3_pos);
    Serial.printf("Thermal = %.2f kW\n", thermalKW);
  }

  // Hindari watchdog reset
  delay(2);
}
