#include <Wire.h>
#include <ESP32Servo.h>

// ================================
// I2C Slave Configuration
// ================================
#define I2C_SLAVE_ADDRESS 0x08

#define RECEIVE_SIZE 3     // 3 bytes: target rod positions (Safety, Shim, Regulating)
#define SEND_SIZE    16    // 16 bytes: actual positions + thermal kW

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ================================
// Servo Configuration
// ================================
#define SERVO_SAFETY_PIN      25
#define SERVO_SHIM_PIN        26
#define SERVO_REGULATING_PIN  27

Servo servoSafety;
Servo servoShim;
Servo servoRegulating;

// ================================
// Rod Control Variables
// ================================
uint8_t safety_target = 0;      // Target position from RasPi (0-100%)
uint8_t shim_target = 0;
uint8_t regulating_target = 0;

uint8_t safety_actual = 0;      // Actual position (0-100%)
uint8_t shim_actual = 0;
uint8_t regulating_actual = 0;

float thermalKW = 0.0;          // Calculated thermal power
float resFloat1 = 0.0;          // Reserved for future use
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

  Serial.println("\n=== ESP-B: Control Rod Controller ===");
  
  // Initialize servos
  servoSafety.attach(SERVO_SAFETY_PIN);
  servoShim.attach(SERVO_SHIM_PIN);
  servoRegulating.attach(SERVO_REGULATING_PIN);
  
  // Set initial position (0%)
  servoSafety.write(0);
  servoShim.write(0);
  servoRegulating.write(0);
  Serial.println("Servos initialized at 0%");

  // Initialize I2C
  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onReceive(onReceiveHandler);
  Wire.onRequest(onRequestHandler);

  Serial.println("I2C Ready at address 0x08");
  Serial.println("Waiting for Raspberry Pi commands...");
}

// ================================
// Servo Control Function
// ================================
void moveServosToTarget() {
  // Move servos smoothly to target positions
  // Map 0-100% to servo angle (typically 0-180 degrees)
  int angleSafety = map(safety_target, 0, 100, 0, 180);
  int angleShim = map(shim_target, 0, 100, 0, 180);
  int angleReg = map(regulating_target, 0, 100, 0, 180);
  
  servoSafety.write(angleSafety);
  servoShim.write(angleShim);
  servoRegulating.write(angleReg);
  
  // Update actual positions
  safety_actual = safety_target;
  shim_actual = shim_target;
  regulating_actual = regulating_target;
}

// ================================
// Calculate Thermal Power
// ================================
void calculateThermalPower() {
  // Simple thermal power calculation based on rod positions
  // Formula: More rods inserted (higher %) = more power
  // This is simplified - real reactors use complex neutronics
  
  float avgRodPosition = (safety_actual + shim_actual + regulating_actual) / 3.0;
  
  // Base power curve: quadratic relationship
  // 0% rods = ~50 kW (decay heat)
  // 50% rods = ~500 kW
  // 100% rods = ~2000 kW (max power)
  thermalKW = 50.0 + (avgRodPosition * avgRodPosition * 0.195);
  
  // Add individual rod contributions (different worth)
  thermalKW += safety_actual * 2.0;      // Safety rod worth: 2 kW per %
  thermalKW += shim_actual * 3.5;        // Shim rod worth: 3.5 kW per %
  thermalKW += regulating_actual * 4.0;  // Regulating rod worth: 4 kW per %
}

// ================================
// Prepare Send Data
// ================================
void prepareSendData() {
  // Byte 0-2: Actual rod positions (0-100%)
  sendBuffer[0] = safety_actual;
  sendBuffer[1] = shim_actual;
  sendBuffer[2] = regulating_actual;
  sendBuffer[3] = 0;  // Reserved byte
  
  // Byte 4-7: Thermal power (float)
  memcpy(&sendBuffer[4], &thermalKW, 4);
  
  // Byte 8-15: Reserved for future use
  memcpy(&sendBuffer[8], &resFloat1, 4);
  memcpy(&sendBuffer[12], &resFloat2, 4);
}

// ================================
// Main Loop
// ================================
void loop() {
  // Process new data from Raspberry Pi
  if (newDataFlag) {
    newDataFlag = false;

    // Copy volatile buffer to local
    uint8_t buf[RECEIVE_SIZE];
    memcpy(buf, (const void*)receiveBuffer, RECEIVE_SIZE);

    // Parse 3 bytes: target rod positions
    safety_target = buf[0];
    shim_target = buf[1];
    regulating_target = buf[2];

    Serial.println("\n=== COMMAND RECEIVED ===");
    Serial.printf("Safety Rod Target:     %d%%\n", safety_target);
    Serial.printf("Shim Rod Target:       %d%%\n", shim_target);
    Serial.printf("Regulating Rod Target: %d%%\n", regulating_target);

    // Move servos to target positions
    moveServosToTarget();

    // Calculate thermal power based on rod positions
    calculateThermalPower();

    // Update send buffer for next request
    prepareSendData();

    Serial.println("=== STATUS UPDATE ===");
    Serial.printf("Safety Rod Actual:     %d%%\n", safety_actual);
    Serial.printf("Shim Rod Actual:       %d%%\n", shim_actual);
    Serial.printf("Regulating Rod Actual: %d%%\n", regulating_actual);
    Serial.printf("Thermal Power:         %.2f kW\n", thermalKW);
  }

  delay(2);
}
