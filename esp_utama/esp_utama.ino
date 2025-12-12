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
// PWM Speed Control
#define MOTOR_PUMP_PRIMARY    4    // Pompa Primer (ENA)
#define MOTOR_PUMP_SECONDARY  16   // Pompa Sekunder (ENB)
#define MOTOR_PUMP_TERTIARY   17   // Pompa Tersier (ENA)
#define MOTOR_TURBINE         5    // Motor Turbin (ENB)

// Direction Control (untuk L298N IN1, IN2, IN3, IN4)
// L298N #1 - Pompa Primer & Sekunder
#define MOTOR_PUMP_PRIMARY_IN1    18   // Pompa Primer direction 1
#define MOTOR_PUMP_PRIMARY_IN2    19   // Pompa Primer direction 2
#define MOTOR_PUMP_SECONDARY_IN1  23   // Pompa Sekunder direction 1
#define MOTOR_PUMP_SECONDARY_IN2  22   // Pompa Sekunder direction 2

// L298N #2 - Pompa Tersier & Turbin
#define MOTOR_PUMP_TERTIARY_IN1   21   // Pompa Tersier direction 1
#define MOTOR_PUMP_TERTIARY_IN2   3    // Pompa Tersier direction 2
#define MOTOR_TURBINE_IN1         1    // Motor Turbin direction 1
#define MOTOR_TURBINE_IN2         0    // Motor Turbin direction 2

// Motor Direction Enum
#define MOTOR_FORWARD  1
#define MOTOR_REVERSE  2
#define MOTOR_STOP     0

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
  /*
   * Electrical Power Calculation - PWR Nuclear Reactor Model
   * 
   * Reactor Rating: 300 MWe (300,000 kW electrical)
   * 
   * Power dihasilkan ketika:
   * 1. Control rods ditarik (reactivity meningkat)
   * 2. Turbin bergerak (konversi thermal → electrical)
   * 
   * Realistic Physics:
   * - Reactor menghasilkan panas thermal (dari fisi nuklir)
   * - Turbine efficiency ~33% (typical PWR)
   * - Electrical output = Thermal × Turbine Efficiency × Load
   * 
   * Formula:
   * - Reactivity dari shim + regulating rods (safety untuk shutdown)
   * - Thermal capacity ~900 MWth (untuk 300 MWe)
   * - Scaling berdasarkan turbine power_level (0-100%)
   */
  
  // Calculate reactivity from control rods
  float avgRodPosition = (shim_actual + regulating_actual) / 2.0;
  // Safety rod hanya untuk shutdown/SCRAM, tidak berkontribusi ke power
  
  // Reactor thermal power capacity (0 - 900 MWth = 900,000 kW thermal)
  float reactor_thermal_kw = 0.0;
  
  if (avgRodPosition > 10.0) {
    // Non-linear power curve (quadratic untuk simulasi reaktivitas)
    // Max thermal: 900 MWth ketika rods full (100%)
    reactor_thermal_kw = avgRodPosition * avgRodPosition * 90.0;  // 100^2 × 90 = 900,000 kW
    
    // Individual rod contributions untuk fine control
    reactor_thermal_kw += shim_actual * 150.0;       // Coarse control
    reactor_thermal_kw += regulating_actual * 200.0; // Fine control
  }
  
  // Clamp reactor thermal output (0 - 900 MWth)
  if (reactor_thermal_kw > 900000.0) reactor_thermal_kw = 900000.0;
  
  // **Turbine Conversion: Thermal → Electrical**
  // Turbine efficiency ~33% (typical PWR)
  // power_level = turbine load (0-100%)
  
  float turbine_load = power_level / 100.0;  // 0.0 to 1.0
  const float TURBINE_EFFICIENCY = 0.33;     // 33% thermal to electrical
  
  // Final electrical power output (MWe)
  // 900 MWth × 33% × 100% load = 300 MWe (max)
  thermal_kw_calculated = reactor_thermal_kw * TURBINE_EFFICIENCY * turbine_load;
  
  // Clamp electrical output (0 - 300 MWe = 300,000 kW)
  if (thermal_kw_calculated < 0.0) thermal_kw_calculated = 0.0;
  if (thermal_kw_calculated > 300000.0) thermal_kw_calculated = 300000.0;
}

// ================================
// TURBINE STATE MACHINE
// ================================
void updateTurbineState() {
  // Check reactor thermal capacity (not electrical output)
  // Calculate reactor thermal for state machine decision
  float avgRodPosition = (shim_actual + regulating_actual) / 2.0;
  float reactor_thermal_capacity = 0.0;
  
  if (avgRodPosition > 10.0) {
    reactor_thermal_capacity = avgRodPosition * avgRodPosition * 90.0;
    reactor_thermal_capacity += shim_actual * 150.0;
    reactor_thermal_capacity += regulating_actual * 200.0;
  }
  
  switch (current_state) {
    case STATE_IDLE:
      // Start turbine ketika reactor panas cukup (>50 MWth = 50,000 kW)
      if (reactor_thermal_capacity > 50000.0) {
        current_state = STATE_STARTING;
        Serial.println("Turbine: IDLE → STARTING");
      }
      power_level = 0.0;
      break;
      
    case STATE_STARTING:
      // Gradual turbine spin-up (0→100% dalam ~3 menit)
      power_level += 0.5;  // Increment per cycle
      if (power_level >= 100.0) {
        power_level = 100.0;
        current_state = STATE_RUNNING;
        Serial.println("Turbine: STARTING → RUNNING");
      }
      break;
      
    case STATE_RUNNING:
      // Shutdown jika reactor thermal terlalu rendah (<20 MWth)
      if (reactor_thermal_capacity < 20000.0) {
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
// MOTOR DIRECTION CONTROL
// ================================
void setMotorDirection(uint8_t motor_id, uint8_t direction) {
  /*
   * Set motor direction for L298N H-Bridge
   * 
   * Parameters:
   *   motor_id: 1=Primer, 2=Sekunder, 3=Tersier, 4=Turbin
   *   direction: MOTOR_FORWARD, MOTOR_REVERSE, MOTOR_STOP
   *   
   * L298N Truth Table:
   *   IN1=LOW,  IN2=LOW  → STOP (brake)
   *   IN1=HIGH, IN2=LOW  → FORWARD
   *   IN1=LOW,  IN2=HIGH → REVERSE
   *   IN1=HIGH, IN2=HIGH → STOP (brake)
   */
  
  switch(motor_id) {
    case 1: // Pompa Primer
      if (direction == MOTOR_FORWARD) {
        digitalWrite(MOTOR_PUMP_PRIMARY_IN1, HIGH);
        digitalWrite(MOTOR_PUMP_PRIMARY_IN2, LOW);
      } else if (direction == MOTOR_REVERSE) {
        digitalWrite(MOTOR_PUMP_PRIMARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_PRIMARY_IN2, HIGH);
      } else { // MOTOR_STOP
        digitalWrite(MOTOR_PUMP_PRIMARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_PRIMARY_IN2, LOW);
      }
      break;
      
    case 2: // Pompa Sekunder
      if (direction == MOTOR_FORWARD) {
        digitalWrite(MOTOR_PUMP_SECONDARY_IN1, HIGH);
        digitalWrite(MOTOR_PUMP_SECONDARY_IN2, LOW);
      } else if (direction == MOTOR_REVERSE) {
        digitalWrite(MOTOR_PUMP_SECONDARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_SECONDARY_IN2, HIGH);
      } else {
        digitalWrite(MOTOR_PUMP_SECONDARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_SECONDARY_IN2, LOW);
      }
      break;
      
    case 3: // Pompa Tersier
      if (direction == MOTOR_FORWARD) {
        digitalWrite(MOTOR_PUMP_TERTIARY_IN1, HIGH);
        digitalWrite(MOTOR_PUMP_TERTIARY_IN2, LOW);
      } else if (direction == MOTOR_REVERSE) {
        digitalWrite(MOTOR_PUMP_TERTIARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_TERTIARY_IN2, HIGH);
      } else {
        digitalWrite(MOTOR_PUMP_TERTIARY_IN1, LOW);
        digitalWrite(MOTOR_PUMP_TERTIARY_IN2, LOW);
      }
      break;
      
    case 4: // Motor Turbin
      if (direction == MOTOR_FORWARD) {
        digitalWrite(MOTOR_TURBINE_IN1, HIGH);
        digitalWrite(MOTOR_TURBINE_IN2, LOW);
      } else if (direction == MOTOR_REVERSE) {
        digitalWrite(MOTOR_TURBINE_IN1, LOW);
        digitalWrite(MOTOR_TURBINE_IN2, HIGH);
      } else {
        digitalWrite(MOTOR_TURBINE_IN1, LOW);
        digitalWrite(MOTOR_TURBINE_IN2, LOW);
      }
      break;
  }
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
  
  // Set direction to FORWARD when speed > 0, STOP when speed = 0
  if (pump_primary_actual > 0) {
    setMotorDirection(1, MOTOR_FORWARD);
  } else {
    setMotorDirection(1, MOTOR_STOP);
  }
  
  if (pump_secondary_actual > 0) {
    setMotorDirection(2, MOTOR_FORWARD);
  } else {
    setMotorDirection(2, MOTOR_STOP);
  }
  
  if (pump_tertiary_actual > 0) {
    setMotorDirection(3, MOTOR_FORWARD);
  } else {
    setMotorDirection(3, MOTOR_STOP);
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
