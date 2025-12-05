/*
 * ESP-BC MERGED - Control Rods + Turbine + Humidifier
 * I2C Address: 0x08
 * 
 * Menggabungkan fungsi ESP-B dan ESP-C:
 * - 3x Servo motors (control rods)
 * - 6x Relay (4 main components + 2 humidifiers)
 * - 4x PWM motors (steam gen, turbine, condenser, cooling)
 * - Thermal power calculation
 * - Turbine state machine
 * 
 * Pin Configuration (ESP32 38-pin):
 * - Servos: GPIO 25, 26, 27
 * - Main Relays: GPIO 32, 33, 14, 12
 * - Humidifier Relays: GPIO 13, 15
 * - Motors PWM: GPIO 4, 16, 17, 5
 * - I2C: GPIO 21 (SDA), 22 (SCL)
 * - Status LED: GPIO 2
 * 
 * IMPORTANT: Uses ESP32 Arduino Core v3.x API
 * - ledcAttach(pin, freq, resolution) instead of ledcSetup() + ledcAttachPin()
 * - ledcWrite(pin, duty) uses pin number directly (no channel needed)
 */

#include <Wire.h>
#include <ESP32Servo.h>

// ================================
// I2C Slave Configuration
// ================================
#define I2C_SLAVE_ADDRESS 0x08
#define RECEIVE_SIZE 12    // 12 bytes from Raspberry
#define SEND_SIZE    20    // 20 bytes to Raspberry

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ================================
// PIN DEFINITIONS
// ================================

// === CONTROL RODS (3 servo) ===
#define SERVO_SAFETY      25
#define SERVO_SHIM        26
#define SERVO_REGULATING  27

// === MAIN RELAYS (4 relay) ===
#define RELAY_STEAM_GEN       32
#define RELAY_TURBINE         33
#define RELAY_CONDENSER       14
#define RELAY_COOLING_TOWER   12

// === HUMIDIFIER RELAYS (2 relay) ===
#define RELAY_HUMID_SG    13    // Steam Generator humidifier
#define RELAY_HUMID_CT    15    // Cooling Tower humidifier

// === PWM MOTORS (4 motors) ===
#define MOTOR_STEAM_GEN_PIN   4
#define MOTOR_TURBINE_PIN     16
#define MOTOR_CONDENSER_PIN   17
#define MOTOR_COOLING_PIN     5

// === PWM Configuration (ESP32 Core v3.x) ===
#define PWM_FREQ       5000  // 5 kHz
#define PWM_RESOLUTION 8     // 8-bit (0-255)

// === OPTIONAL: Status LED ===
#define STATUS_LED 2

// ================================
// GLOBAL VARIABLES - Control Rods
// ================================
Servo servoSafety;
Servo servoShim;
Servo servoRegulating;

uint8_t safety_target = 0;
uint8_t shim_target = 0;
uint8_t regulating_target = 0;

uint8_t safety_actual = 0;
uint8_t shim_actual = 0;
uint8_t regulating_actual = 0;

float thermal_kw_calculated = 0.0;

// ================================
// GLOBAL VARIABLES - Turbine
// ================================
enum TurbineState {
  STATE_IDLE = 0,
  STATE_STARTING = 1,
  STATE_RUNNING = 2,
  STATE_SHUTDOWN = 3
};

TurbineState current_state = STATE_IDLE;
float power_level = 0.0;  // 0-100%

// ================================
// GLOBAL VARIABLES - Humidifier
// ================================
uint8_t humid_sg_cmd = 0;  // Command from RasPi
uint8_t humid_ct_cmd = 0;
uint8_t humid_sg_status = 0;  // Actual relay status
uint8_t humid_ct_status = 0;

// ================================
// I2C ISR HANDLERS
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

  Serial.println("\n=== ESP-BC MERGED: Control Rods + Turbine + Humidifier ===");
  Serial.println("I2C Address: 0x08");
  
  // Initialize servos
  servoSafety.attach(SERVO_SAFETY);
  servoShim.attach(SERVO_SHIM);
  servoRegulating.attach(SERVO_REGULATING);
  
  // Set initial position (0%)
  servoSafety.write(0);
  servoShim.write(0);
  servoRegulating.write(0);
  Serial.println("✓ Servos initialized at 0%");

  // Initialize relay pins
  pinMode(RELAY_STEAM_GEN, OUTPUT);
  pinMode(RELAY_TURBINE, OUTPUT);
  pinMode(RELAY_CONDENSER, OUTPUT);
  pinMode(RELAY_COOLING_TOWER, OUTPUT);
  pinMode(RELAY_HUMID_SG, OUTPUT);
  pinMode(RELAY_HUMID_CT, OUTPUT);
  
  // All relays OFF initially
  digitalWrite(RELAY_STEAM_GEN, LOW);
  digitalWrite(RELAY_TURBINE, LOW);
  digitalWrite(RELAY_CONDENSER, LOW);
  digitalWrite(RELAY_COOLING_TOWER, LOW);
  digitalWrite(RELAY_HUMID_SG, LOW);
  digitalWrite(RELAY_HUMID_CT, LOW);
  Serial.println("✓ Relays initialized (all OFF)");

  // Initialize PWM channels (ESP32 Core v3.x API)
  ledcAttach(MOTOR_STEAM_GEN_PIN, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_TURBINE_PIN, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_CONDENSER_PIN, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_COOLING_PIN, PWM_FREQ, PWM_RESOLUTION);
  
  // All motors OFF initially
  ledcWrite(MOTOR_STEAM_GEN_PIN, 0);
  ledcWrite(MOTOR_TURBINE_PIN, 0);
  ledcWrite(MOTOR_CONDENSER_PIN, 0);
  ledcWrite(MOTOR_COOLING_PIN, 0);
  Serial.println("✓ PWM motors initialized (speed 0)");

  // Initialize status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  // Initialize I2C
  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onReceive(onReceiveHandler);
  Wire.onRequest(onRequestHandler);

  Serial.println("✓ I2C Ready at address 0x08");
  Serial.println("=== System Ready ===\n");
}

// ================================
// SERVO CONTROL
// ================================
void updateServos() {
  // Map 0-100% to servo angle (0-180 degrees)
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
// THERMAL POWER CALCULATION
// ================================
void calculateThermalPower() {
  float avgRodPosition = (safety_actual + shim_actual + regulating_actual) / 3.0;
  
  // Base power curve
  thermal_kw_calculated = 50.0 + (avgRodPosition * avgRodPosition * 0.195);
  
  // Add individual rod contributions
  thermal_kw_calculated += safety_actual * 2.0;
  thermal_kw_calculated += shim_actual * 3.5;
  thermal_kw_calculated += regulating_actual * 4.0;
}

// ================================
// TURBINE STATE MACHINE
// ================================
void updateTurbineState() {
  float thermal_kw = thermal_kw_calculated;
  
  switch (current_state) {
    case STATE_IDLE:
      if (thermal_kw > 500.0) {
        current_state = STATE_STARTING;
        Serial.println("Turbine: IDLE → STARTING");
      }
      power_level = 0.0;
      break;
      
    case STATE_STARTING:
      power_level += 0.5;
      if (power_level >= 100.0) {
        power_level = 100.0;
        current_state = STATE_RUNNING;
        Serial.println("Turbine: STARTING → RUNNING");
      }
      break;
      
    case STATE_RUNNING:
      if (thermal_kw < 200.0) {
        current_state = STATE_SHUTDOWN;
        Serial.println("Turbine: RUNNING → SHUTDOWN");
      }
      power_level = 100.0;
      break;
      
    case STATE_SHUTDOWN:
      power_level -= 1.0;
      if (power_level <= 0.0) {
        power_level = 0.0;
        current_state = STATE_IDLE;
        Serial.println("Turbine: SHUTDOWN → IDLE");
      }
      break;
  }
  
  // Update relays
  digitalWrite(RELAY_STEAM_GEN, (current_state != STATE_IDLE) ? HIGH : LOW);
  digitalWrite(RELAY_TURBINE, (current_state == STATE_RUNNING) ? HIGH : LOW);
  digitalWrite(RELAY_CONDENSER, (current_state != STATE_IDLE) ? HIGH : LOW);
  digitalWrite(RELAY_COOLING_TOWER, (current_state != STATE_IDLE) ? HIGH : LOW);
}

// ================================
// HUMIDIFIER CONTROL
// ================================
void updateHumidifiers() {
  digitalWrite(RELAY_HUMID_SG, humid_sg_cmd ? HIGH : LOW);
  digitalWrite(RELAY_HUMID_CT, humid_ct_cmd ? HIGH : LOW);
  
  humid_sg_status = digitalRead(RELAY_HUMID_SG);
  humid_ct_status = digitalRead(RELAY_HUMID_CT);
}

// ================================
// PWM MOTOR SPEED CONTROL
// ================================
void updateMotorSpeeds() {
  int speed = map((int)power_level, 0, 100, 0, 255);
  
  // ESP32 Core v3.x: ledcWrite() uses pin number directly
  ledcWrite(MOTOR_STEAM_GEN_PIN, speed);
  ledcWrite(MOTOR_TURBINE_PIN, speed);
  ledcWrite(MOTOR_CONDENSER_PIN, speed);
  ledcWrite(MOTOR_COOLING_PIN, speed);
}

// ================================
// PREPARE SEND DATA
// ================================
void prepareSendData() {
  sendBuffer[0] = safety_actual;
  sendBuffer[1] = shim_actual;
  sendBuffer[2] = regulating_actual;
  sendBuffer[3] = 0;
  
  memcpy(&sendBuffer[4], &thermal_kw_calculated, 4);
  memcpy(&sendBuffer[8], &power_level, 4);
  
  uint32_t state_value = (uint32_t)current_state;
  memcpy(&sendBuffer[12], &state_value, 4);
  
  sendBuffer[16] = (current_state != STATE_IDLE) ? 1 : 0;
  sendBuffer[17] = (current_state == STATE_RUNNING) ? 1 : 0;
  sendBuffer[18] = humid_sg_status;
  sendBuffer[19] = humid_ct_status;
}

// ================================
// PROCESS RECEIVED DATA
// ================================
void processReceivedData() {
  uint8_t buf[RECEIVE_SIZE];
  memcpy(buf, (const void*)receiveBuffer, RECEIVE_SIZE);

  safety_target = buf[0];
  shim_target = buf[1];
  regulating_target = buf[2];
  
  humid_sg_cmd = buf[8];
  humid_ct_cmd = buf[9];

  Serial.println("\n=== COMMAND RECEIVED ===");
  Serial.printf("Rod Targets: Safety=%d%%, Shim=%d%%, Reg=%d%%\n", 
                safety_target, shim_target, regulating_target);
  Serial.printf("Humidifier: SG=%d, CT=%d\n", humid_sg_cmd, humid_ct_cmd);
}

// ================================
// Main Loop
// ================================
void loop() {
  if (newDataFlag) {
    newDataFlag = false;
    processReceivedData();
    updateServos();
    
    Serial.println("=== STATUS ===");
    Serial.printf("Rods: %d%%, %d%%, %d%%\n", safety_actual, shim_actual, regulating_actual);
    Serial.printf("Thermal: %.2f kW, State: %d, Power: %.1f%%\n", 
                  thermal_kw_calculated, current_state, power_level);
  }
  
  calculateThermalPower();
  updateTurbineState();
  updateHumidifiers();
  updateMotorSpeeds();
  prepareSendData();
  
  delay(10);
}
