/*
 * ESP-BC MERGED - Control Rods + Turbine + Humidifier + Pumps
 * I2C Address: 0x08
 * 
 * Menggabungkan fungsi ESP-B dan ESP-C:
 * - 3x Servo motors (control rods)
 * - 6x Relay untuk humidifier (4 untuk cooling tower, 2 untuk steam generator)
 * - 4x Motor DC dengan motor driver (3 pompa aliran + 1 turbin)
 * - Thermal power calculation
 * - Turbine state machine
 * 
 * Pin Configuration (ESP32 38-pin):
 * - Servos: GPIO 25, 26, 27 (control rods)
 * - Humidifier Relays Cooling Tower (4): GPIO 32, 33, 14, 12
 * - Humidifier Relays Steam Generator (2): GPIO 13, 15
 * - Motor Driver PWM:
 *   - GPIO 4:  Pompa Primer (Primary Loop)
 *   - GPIO 16: Pompa Sekunder (Secondary Loop)
 *   - GPIO 17: Pompa Tersier (Tertiary/Cooling Loop)
 *   - GPIO 5:  Motor Turbin (berdasarkan shim + regulating rod)
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

// === HUMIDIFIER RELAYS - Cooling Tower (4 relay) ===
#define RELAY_HUMID_CT1       32
#define RELAY_HUMID_CT2       33
#define RELAY_HUMID_CT3       14
#define RELAY_HUMID_CT4       12

// === HUMIDIFIER RELAYS - Steam Generator (2 relay) ===
#define RELAY_HUMID_SG1       13
#define RELAY_HUMID_SG2       15

// === MOTOR DRIVER PWM (4 motor DC) ===
#define MOTOR_PUMP_PRIMARY    4    // Pompa Primer
#define MOTOR_PUMP_SECONDARY  16   // Pompa Sekunder
#define MOTOR_PUMP_TERTIARY   17   // Pompa Tersier
#define MOTOR_TURBINE         5    // Motor Turbin

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
// GLOBAL VARIABLES - Pumps
// ================================
float pump_primary_actual = 0.0;    // Current PWM (0-100%)
float pump_secondary_actual = 0.0;
float pump_tertiary_actual = 0.0;

float pump_primary_target = 0.0;    // Target PWM from state machine
float pump_secondary_target = 0.0;
float pump_tertiary_target = 0.0;

// ================================
// GLOBAL VARIABLES - Humidifier
// ================================
uint8_t humid_sg1_cmd = 0;  // Command from RasPi
uint8_t humid_sg2_cmd = 0;
uint8_t humid_ct1_cmd = 0;
uint8_t humid_ct2_cmd = 0;
uint8_t humid_ct3_cmd = 0;
uint8_t humid_ct4_cmd = 0;

uint8_t humid_sg1_status = 0;  // Actual relay status
uint8_t humid_sg2_status = 0;
uint8_t humid_ct1_status = 0;
uint8_t humid_ct2_status = 0;
uint8_t humid_ct3_status = 0;
uint8_t humid_ct4_status = 0;

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

  // Initialize humidifier relay pins
  pinMode(RELAY_HUMID_CT1, OUTPUT);
  pinMode(RELAY_HUMID_CT2, OUTPUT);
  pinMode(RELAY_HUMID_CT3, OUTPUT);
  pinMode(RELAY_HUMID_CT4, OUTPUT);
  pinMode(RELAY_HUMID_SG1, OUTPUT);
  pinMode(RELAY_HUMID_SG2, OUTPUT);
  
  // All humidifier relays OFF initially
  digitalWrite(RELAY_HUMID_CT1, LOW);
  digitalWrite(RELAY_HUMID_CT2, LOW);
  digitalWrite(RELAY_HUMID_CT3, LOW);
  digitalWrite(RELAY_HUMID_CT4, LOW);
  digitalWrite(RELAY_HUMID_SG1, LOW);
  digitalWrite(RELAY_HUMID_SG2, LOW);
  Serial.println("✓ Humidifier relays initialized (all OFF)");

  // Initialize motor driver PWM channels (ESP32 Core v3.x API)
  ledcAttach(MOTOR_PUMP_PRIMARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_PUMP_SECONDARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_PUMP_TERTIARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_TURBINE, PWM_FREQ, PWM_RESOLUTION);
  
  // All motor drivers OFF initially
  ledcWrite(MOTOR_PUMP_PRIMARY, 0);
  ledcWrite(MOTOR_PUMP_SECONDARY, 0);
  ledcWrite(MOTOR_PUMP_TERTIARY, 0);
  ledcWrite(MOTOR_TURBINE, 0);
  Serial.println("✓ Motor drivers initialized (3 pumps + turbine = 0%)");

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
  
  // Update pump targets based on turbine state
  if (current_state == STATE_IDLE) {
    pump_primary_target = 0.0;
    pump_secondary_target = 0.0;
    pump_tertiary_target = 0.0;
  } else if (current_state == STATE_STARTING) {
    pump_primary_target = 50.0;
    pump_secondary_target = 50.0;
    pump_tertiary_target = 50.0;
  } else if (current_state == STATE_RUNNING) {
    pump_primary_target = 100.0;
    pump_secondary_target = 100.0;
    pump_tertiary_target = 100.0;
  } else if (current_state == STATE_SHUTDOWN) {
    pump_primary_target = 20.0;
    pump_secondary_target = 20.0;
    pump_tertiary_target = 20.0;
  }
}

// ================================
// HUMIDIFIER CONTROL
// ================================
void updateHumidifiers() {
  // Steam Generator humidifiers (2)
  digitalWrite(RELAY_HUMID_SG1, humid_sg1_cmd ? HIGH : LOW);
  digitalWrite(RELAY_HUMID_SG2, humid_sg2_cmd ? HIGH : LOW);
  
  // Cooling Tower humidifiers (4)
  digitalWrite(RELAY_HUMID_CT1, humid_ct1_cmd ? HIGH : LOW);
  digitalWrite(RELAY_HUMID_CT2, humid_ct2_cmd ? HIGH : LOW);
  digitalWrite(RELAY_HUMID_CT3, humid_ct3_cmd ? HIGH : LOW);
  digitalWrite(RELAY_HUMID_CT4, humid_ct4_cmd ? HIGH : LOW);
  
  // Update status
  humid_sg1_status = digitalRead(RELAY_HUMID_SG1);
  humid_sg2_status = digitalRead(RELAY_HUMID_SG2);
  humid_ct1_status = digitalRead(RELAY_HUMID_CT1);
  humid_ct2_status = digitalRead(RELAY_HUMID_CT2);
  humid_ct3_status = digitalRead(RELAY_HUMID_CT3);
  humid_ct4_status = digitalRead(RELAY_HUMID_CT4);
}

// ================================
// PUMP GRADUAL SPEED CONTROL
// ================================
void updatePumpSpeeds() {
  // Gradual acceleration/deceleration untuk pompa
  // Jika dimatikan/dinyalakan, tidak langsung tapi perlahan
  
  // Primary pump
  if (pump_primary_actual < pump_primary_target) {
    pump_primary_actual += 2.0;  // Naik 2% per cycle
    if (pump_primary_actual > pump_primary_target) {
      pump_primary_actual = pump_primary_target;
    }
  } else if (pump_primary_actual > pump_primary_target) {
    pump_primary_actual -= 1.0;  // Turun 1% per cycle (lebih pelan)
    if (pump_primary_actual < pump_primary_target) {
      pump_primary_actual = pump_primary_target;
    }
  }
  
  // Secondary pump
  if (pump_secondary_actual < pump_secondary_target) {
    pump_secondary_actual += 2.0;
    if (pump_secondary_actual > pump_secondary_target) {
      pump_secondary_actual = pump_secondary_target;
    }
  } else if (pump_secondary_actual > pump_secondary_target) {
    pump_secondary_actual -= 1.0;
    if (pump_secondary_actual < pump_secondary_target) {
      pump_secondary_actual = pump_secondary_target;
    }
  }
  
  // Tertiary pump
  if (pump_tertiary_actual < pump_tertiary_target) {
    pump_tertiary_actual += 2.0;
    if (pump_tertiary_actual > pump_tertiary_target) {
      pump_tertiary_actual = pump_tertiary_target;
    }
  } else if (pump_tertiary_actual > pump_tertiary_target) {
    pump_tertiary_actual -= 1.0;
    if (pump_tertiary_actual < pump_tertiary_target) {
      pump_tertiary_actual = pump_tertiary_target;
    }
  }
  
  // Apply PWM to motor drivers
  int pwm_primary = map((int)pump_primary_actual, 0, 100, 0, 255);
  int pwm_secondary = map((int)pump_secondary_actual, 0, 100, 0, 255);
  int pwm_tertiary = map((int)pump_tertiary_actual, 0, 100, 0, 255);
  
  ledcWrite(MOTOR_PUMP_PRIMARY, pwm_primary);
  ledcWrite(MOTOR_PUMP_SECONDARY, pwm_secondary);
  ledcWrite(MOTOR_PUMP_TERTIARY, pwm_tertiary);
}

// ================================
// TURBINE MOTOR SPEED CONTROL
// ================================
void updateTurbineSpeed() {
  // Putaran turbin berdasarkan posisi shim dan regulating rod
  // Semakin ditarik ke atas (nilai besar), semakin cepat putaran
  
  float avg_control_rods = (shim_actual + regulating_actual) / 2.0;
  
  // Map 0-100% rod position to 0-100% turbine speed
  // Safety rod tidak mempengaruhi turbine speed
  float turbine_speed = avg_control_rods;
  
  // Apply minimum threshold
  if (turbine_speed < 10.0) {
    turbine_speed = 0.0;  // Stop turbine if rods too low
  }
  
  // Convert to PWM (0-255)
  int pwm_turbine = map((int)turbine_speed, 0, 100, 0, 255);
  
  ledcWrite(MOTOR_TURBINE, pwm_turbine);
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
  
  // Kirim status semua humidifier (6 relays dalam 2 bytes)
  sendBuffer[18] = (humid_sg1_status) | (humid_sg2_status << 1) | 
                   (humid_ct1_status << 2) | (humid_ct2_status << 3);
  sendBuffer[19] = (humid_ct3_status) | (humid_ct4_status << 1);
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
  
  // Unpack humidifier commands (6 relays dari 2 bytes)
  humid_sg1_cmd = buf[8] & 0x01;
  humid_sg2_cmd = (buf[8] >> 1) & 0x01;
  humid_ct1_cmd = (buf[8] >> 2) & 0x01;
  humid_ct2_cmd = (buf[8] >> 3) & 0x01;
  humid_ct3_cmd = (buf[8] >> 4) & 0x01;
  humid_ct4_cmd = (buf[8] >> 5) & 0x01;

  Serial.println("\n=== COMMAND RECEIVED ===");
  Serial.printf("Rod Targets: Safety=%d%%, Shim=%d%%, Reg=%d%%\n", 
                safety_target, shim_target, regulating_target);
  Serial.printf("Humidifier SG: %d,%d | CT: %d,%d,%d,%d\n", 
                humid_sg1_cmd, humid_sg2_cmd, 
                humid_ct1_cmd, humid_ct2_cmd, humid_ct3_cmd, humid_ct4_cmd);
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
  updatePumpSpeeds();
  updateTurbineSpeed();
  prepareSendData();
  
  delay(10);
}
