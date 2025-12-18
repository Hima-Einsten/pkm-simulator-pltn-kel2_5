/*
 * ESP32 UART Communication - ESP-BC (Control Rods + Turbine + Humidifier + Motor Driver)
 * Replaces I2C slave with UART communication
 * 
 * Hardware:
 * - UART2 (GPIO 16=RX, GPIO 17=TX) for communication with Raspberry Pi
 * - Serial (USB) for debugging
 * - 4x Motor DC dengan L298N motor driver (3 pompa + 1 turbin)
 * - 3x Servo motors (control rods)
 * - 6x Relay untuk humidifier
 * 
 * Protocol: JSON over UART (115200 baud, 8N1)
 * 
 * Pin Configuration:
 * - UART: GPIO 16 (RX), 17 (TX) - Communication with RasPi
 * - Servos: GPIO 13, 12, 14 (control rods)
 * - Humidifier Relays: GPIO 25, 26, 27, 32, 33, 34
 * - Motor Driver PWM: GPIO 4, 5, 18, 19 (3 pompa + turbin)
 * - Motor Direction: GPIO 23, 15 (turbine only, pumps hard-wired)
 */

#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ============================================
// UART Configuration
// ============================================
#define UART_BAUD 115200
HardwareSerial UartComm(2);  // UART2 (GPIO 16=RX, 17=TX)

// ============================================
// Control Rod Servos
// ============================================
Servo servo_safety;
Servo servo_shim;
Servo servo_regulating;

const int SERVO_PIN_SAFETY = 13;
const int SERVO_PIN_SHIM = 12;
const int SERVO_PIN_REGULATING = 14;

// Rod positions (0-100%)
int safety_target = 0;
int shim_target = 0;
int regulating_target = 0;

// Final desired targets (for smooth motion)
float safety_final_target = 0.0;
float shim_final_target = 0.0;
float regulating_final_target = 0.0;


// Actual positions as floats for smooth interpolation
float safety_actual_f = 0.0;
float shim_actual_f = 0.0;
float regulating_actual_f = 0.0;

int safety_actual = 0;
int shim_actual = 0;
int regulating_actual = 0;

// ============================================
// Motor Driver PWM Configuration
// ============================================
// NOTE: GPIO 16, 17 digunakan untuk UART, tidak boleh digunakan untuk motor
// Motor Driver PWM pins (speed control)
#define MOTOR_PUMP_PRIMARY    4    // Pompa Primer (Primary Loop)
#define MOTOR_PUMP_SECONDARY  5    // Pompa Sekunder (Secondary Loop)
#define MOTOR_PUMP_TERTIARY   18   // Pompa Tersier (Tertiary/Cooling Loop)
#define MOTOR_TURBINE         19   // Motor Turbin

// Motor Direction Control - ONLY for Turbine
// Pumps always FORWARD (IN1=GND, IN2=+3.3V hard-wired on L298N)
#define MOTOR_TURBINE_IN1     23   // Turbine direction 1
#define MOTOR_TURBINE_IN2     15   // Turbine direction 2

// Motor Direction Enum
#define MOTOR_FORWARD  1
#define MOTOR_REVERSE  2
#define MOTOR_STOP     0

// PWM Configuration
#define PWM_FREQ       5000  // 5 kHz
#define PWM_RESOLUTION 8     // 8-bit (0-255)

// ============================================
// Humidifier Relays
// ============================================
const int RELAY_SG1 = 32;  // Steam Generator 1
const int RELAY_SG2 = 33;  // Steam Generator 2
const int RELAY_CT1 = 27;  // Cooling Tower 1
const int RELAY_CT2 = 26;  // Cooling Tower 2
const int RELAY_CT3 = 25;  // Cooling Tower 3
const int RELAY_CT4 = 34;  // Cooling Tower 4

uint8_t humid_sg1_cmd = 0;
uint8_t humid_sg2_cmd = 0;
uint8_t humid_ct1_cmd = 0;
uint8_t humid_ct2_cmd = 0;
uint8_t humid_ct3_cmd = 0;
uint8_t humid_ct4_cmd = 0;

uint8_t humid_sg1_status = 0;
uint8_t humid_sg2_status = 0;
uint8_t humid_ct1_status = 0;
uint8_t humid_ct2_status = 0;
uint8_t humid_ct3_status = 0;
uint8_t humid_ct4_status = 0;

// ============================================
// Turbine & Generator Simulation
// ============================================
enum TurbineState {
  STATE_IDLE = 0,
  STATE_STARTING = 1,
  STATE_RUNNING = 2,
  STATE_SHUTDOWN = 3
};

TurbineState current_state = STATE_IDLE;
float power_level = 0.0;    // Turbine power (0-100%)
float thermal_kw_calculated = 0.0;
float turbine_speed = 0.0;  // Current turbine speed (0-100%)

// ============================================
// Pump Variables
// ============================================
float pump_primary_actual = 0.0;    // Current PWM (0-100%)
float pump_secondary_actual = 0.0;
float pump_tertiary_actual = 0.0;

float pump_primary_target = 0.0;    // Target PWM from RasPi button command
float pump_secondary_target = 0.0;
float pump_tertiary_target = 0.0;

// Pump commands from RasPi (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
int pump_primary_cmd = 0;
int pump_secondary_cmd = 0;
int pump_tertiary_cmd = 0;

// ============================================
// JSON Communication
// ============================================
DynamicJsonDocument json_rx(512);   // Receive buffer
DynamicJsonDocument json_tx(512);   // Transmit buffer

String rx_buffer = "";
unsigned long last_command_time = 0;
const unsigned long COMMAND_TIMEOUT = 5000;  // 5 seconds

// ============================================
// Setup
// ============================================
void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP-BC UART Communication");
  Serial.println("Control Rods + Turbine + Humidifier + Motor Driver");
  Serial.println("===========================================");
  
  // Initialize UART2 for Raspberry Pi communication
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);  // RX=16, TX=17
  Serial.println("✅ UART2 initialized at 115200 baud");
  Serial.println("   RX: GPIO 16");
  Serial.println("   TX: GPIO 17");
  
  // Initialize servos
  servo_safety.attach(SERVO_PIN_SAFETY);
  servo_shim.attach(SERVO_PIN_SHIM);
  servo_regulating.attach(SERVO_PIN_REGULATING);
  
  // Set initial positions (0%)
  updateServos();
  Serial.println("✅ Servos initialized");
  
  // Initialize relay pins
  pinMode(RELAY_SG1, OUTPUT);
  pinMode(RELAY_SG2, OUTPUT);
  pinMode(RELAY_CT1, OUTPUT);
  pinMode(RELAY_CT2, OUTPUT);
  pinMode(RELAY_CT3, OUTPUT);
  pinMode(RELAY_CT4, OUTPUT);
  
  // All relays OFF initially (HIGH for low-level trigger)
  digitalWrite(RELAY_SG1, HIGH);
  digitalWrite(RELAY_SG2, HIGH);
  digitalWrite(RELAY_CT1, HIGH);
  digitalWrite(RELAY_CT2, HIGH);
  digitalWrite(RELAY_CT3, HIGH);
  digitalWrite(RELAY_CT4, HIGH);
  Serial.println("✅ Humidifier relays initialized");
  
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
  Serial.println("✅ Motor drivers initialized (3 pumps + turbine)");
  Serial.println("   PWM Pins: GPIO 4, 5, 18, 19");
  
  // Initialize turbine direction control pins
  pinMode(MOTOR_TURBINE_IN1, OUTPUT);
  pinMode(MOTOR_TURBINE_IN2, OUTPUT);
  digitalWrite(MOTOR_TURBINE_IN1, HIGH);  // Default: FORWARD
  digitalWrite(MOTOR_TURBINE_IN2, LOW);
  Serial.println("✅ Turbine direction control initialized");
  Serial.println("   Direction Pins: GPIO 23, 15");
  Serial.println("   Pumps: Hard-wired FORWARD (no GPIO needed)");
  
  Serial.println("===========================================");
  Serial.println("✅ System Ready - Waiting for commands...");
  Serial.println("===========================================\n");
  
  last_command_time = millis();
}

// ============================================
// Main Loop
// ============================================
void loop() {
  // Check for incoming UART data
  if (UartComm.available()) {
    char c = UartComm.read();
    
    if (c == '\n') {
      // Process complete message
      processCommand(rx_buffer);
      rx_buffer = "";
    } else {
      rx_buffer += c;
      
      // Prevent buffer overflow
      if (rx_buffer.length() > 256) {
        Serial.println("⚠️  RX buffer overflow, clearing");
        rx_buffer = "";
      }
    }
  }
  
  // Safety: If no command received for 5 seconds, go to safe state
  if (millis() - last_command_time > COMMAND_TIMEOUT) {
    if (safety_target != 0 || shim_target != 0 || regulating_target != 0) {
      Serial.println("⚠️  Communication timeout - Going to safe state");
      safety_target = 0;
      shim_target = 0;
      regulating_target = 0;
      humid_sg1_cmd = 0;
      humid_sg2_cmd = 0;
      humid_ct1_cmd = 0;
      humid_ct2_cmd = 0;
      humid_ct3_cmd = 0;
      humid_ct4_cmd = 0;
    }
    last_command_time = millis();  // Reset timer
  }
  
  // Update system state
  updateServos();
  calculateThermalPower();
  updateTurbineState();
  updateHumidifiers();
  updatePumpSpeeds();     // Pompa controlled by button commands from RasPi
  updateTurbineSpeed();   // Turbin controlled by rod position
  
  // Flush UART TX buffer to prevent overflow
  UartComm.flush();
  
  delay(10);
}

// ============================================
// Process JSON Command
// ============================================
void processCommand(String command) {
  if (command.length() == 0) return;
  
  Serial.print("RX: ");
  Serial.println(command);

  // Clean input: trim and extract JSON object between first '{' and last '}'
  command.trim();
  int startIdx = command.indexOf('{');
  int endIdx = command.lastIndexOf('}');
  if (startIdx != -1 && endIdx > startIdx) {
    command = command.substring(startIdx, endIdx + 1);
  } else if (startIdx != -1) {
    command = command.substring(startIdx);
  }
  // Remove non-printable characters except common whitespace
  String cleaned = "";
  for (size_t i = 0; i < command.length(); i++) {
    char c = command[i];
    if (c == '\n' || c == '\r' || c == '\t' || c >= 32) cleaned += c;
  }
  command = cleaned;

  // Parse JSON
  DeserializationError error = deserializeJson(json_rx, command);

  if (error) {
    Serial.print("❌ JSON parse error: ");
    Serial.println(error.c_str());
    sendError("JSON parse error");
    return;
  }
  
  // Get command type
  const char* cmd = json_rx["cmd"];
  
  if (strcmp(cmd, "update") == 0) {
    // Update command
    handleUpdateCommand();
    last_command_time = millis();
  } else if (strcmp(cmd, "ping") == 0) {
    // Ping command
    sendPong();
  } else {
    Serial.println("⚠️  Unknown command");
    sendError("Unknown command");
  }
}

// ============================================
// Handle Update Command
// ============================================
void handleUpdateCommand() {
  // Parse rod positions
  if (json_rx.containsKey("rods")) {
    JsonArray rods = json_rx["rods"];
    safety_target = rods[0];
    shim_target = rods[1];
    regulating_target = rods[2];
    
    safety_final_target     = constrain(safety_target, 0, 100);
    shim_final_target       = constrain(shim_target, 0, 100);
    regulating_final_target = constrain(regulating_target, 0, 100);

    Serial.printf("✓ Received Rod Targets: Safety=%d, Shim=%d, Reg=%d\n",
                  safety_target, shim_target, regulating_target);
  } else {
    Serial.println("⚠️  No 'rods' field in command!");
  }
  
  // Parse pump commands from RasPi button status
  if (json_rx.containsKey("pumps")) {
    JsonArray pumps = json_rx["pumps"];
    pump_primary_cmd = pumps[0];
    pump_secondary_cmd = pumps[1];
    pump_tertiary_cmd = pumps[2];

      // Setelah parsing rods[]


  }
  
  // Parse humidifier commands
  if (json_rx.containsKey("humid_sg")) {
    JsonArray humid_sg = json_rx["humid_sg"];
    humid_sg1_cmd = humid_sg[0];
    humid_sg2_cmd = humid_sg[1];
  }
  
  if (json_rx.containsKey("humid_ct")) {
    JsonArray humid_ct = json_rx["humid_ct"];
    humid_ct1_cmd = humid_ct[0];
    humid_ct2_cmd = humid_ct[1];
    humid_ct3_cmd = humid_ct[2];
    humid_ct4_cmd = humid_ct[3];
  }
  
  Serial.printf("Targets: Rods=[%d,%d,%d], Pumps=[%d,%d,%d], Humid_SG=[%d,%d], Humid_CT=[%d,%d,%d,%d]\n",
                safety_target, shim_target, regulating_target,
                pump_primary_cmd, pump_secondary_cmd, pump_tertiary_cmd,
                humid_sg1_cmd, humid_sg2_cmd,
                humid_ct1_cmd, humid_ct2_cmd, humid_ct3_cmd, humid_ct4_cmd);
  
  // Send response
  sendStatus();
}

// ============================================
// Send Status Response
// ============================================
void sendStatus() {
  json_tx.clear();
  
  json_tx["status"] = "ok";
  
  // Rod positions
  JsonArray rods = json_tx.createNestedArray("rods");
  rods.add(safety_actual);
  rods.add(shim_actual);
  rods.add(regulating_actual);
  
  // Thermal power and turbine
  json_tx["thermal_kw"] = thermal_kw_calculated;
  json_tx["power_level"] = power_level;
  json_tx["state"] = current_state;
  json_tx["turbine_speed"] = turbine_speed;
  
  // Pump speeds (automatic control by ESP)
  JsonArray pump_speeds = json_tx.createNestedArray("pump_speeds");
  pump_speeds.add(pump_primary_actual);
  pump_speeds.add(pump_secondary_actual);
  pump_speeds.add(pump_tertiary_actual);
  
  // Humidifier status
  JsonArray humid_status = json_tx.createNestedArray("humid_status");
  JsonArray humid_sg = humid_status.createNestedArray();
  humid_sg.add(humid_sg1_status);
  humid_sg.add(humid_sg2_status);
  JsonArray humid_ct = humid_status.createNestedArray();
  humid_ct.add(humid_ct1_status);
  humid_ct.add(humid_ct2_status);
  humid_ct.add(humid_ct3_status);
  humid_ct.add(humid_ct4_status);
  
  // Send via UART
  serializeJson(json_tx, UartComm);
  UartComm.println();
  
  // Debug to USB Serial
  Serial.print("TX: ");
  serializeJson(json_tx, Serial);
  Serial.println();
}

// ============================================
// Send Pong Response
// ============================================
void sendPong() {
  json_tx.clear();
  json_tx["status"] = "ok";
  json_tx["message"] = "pong";
  json_tx["device"] = "ESP-BC";
  
  serializeJson(json_tx, UartComm);
  UartComm.println();
  
  Serial.println("TX: pong");
}

// ============================================
// Send Error Response
// ============================================
void sendError(const char* message) {
  json_tx.clear();
  json_tx["status"] = "error";
  json_tx["message"] = message;
  
  serializeJson(json_tx, UartComm);
  UartComm.println();
}

// ============================================
// Update Servos
// ============================================
// Smooth servo update: interpolate towards final targets
// Config: maximum percent change per second
#define SERVO_MAX_DELTA_PER_SEC 50.0  // percent per second (adjust for smoothness)

void updateServos() {
  // Calculate max delta per loop (loop ~10ms)
  const float loop_dt = 0.01; // 10 ms (matches main loop delay)
  const float max_delta = SERVO_MAX_DELTA_PER_SEC * loop_dt;
  bool servo_moving = false;

  // Move safety_actual_f toward safety_final_target
  if (fabs(safety_actual_f - safety_final_target) > 0.001) {
    float diff = safety_final_target - safety_actual_f;
    if (fabs(diff) <= max_delta) safety_actual_f = safety_final_target;
    else safety_actual_f += (diff > 0 ? max_delta : -max_delta);
    servo_moving = true;
  }

  // Move shim_actual_f toward shim_final_target
  if (fabs(shim_actual_f - shim_final_target) > 0.001) {
    float diff = shim_final_target - shim_actual_f;
    if (fabs(diff) <= max_delta) shim_actual_f = shim_final_target;
    else shim_actual_f += (diff > 0 ? max_delta : -max_delta);
    servo_moving = true;
  }

  // Move regulating_actual_f toward regulating_final_target
  if (fabs(regulating_actual_f - regulating_final_target) > 0.001) {
    float diff = regulating_final_target - regulating_actual_f;
    if (fabs(diff) <= max_delta) regulating_actual_f = regulating_final_target;
    else regulating_actual_f += (diff > 0 ? max_delta : -max_delta);
    servo_moving = true;
  }

  // Update integer snapshots used elsewhere
  safety_actual = (int)round(safety_actual_f);
  shim_actual = (int)round(shim_actual_f);
  regulating_actual = (int)round(regulating_actual_f);

  // Debug if moving
  if (servo_moving) {
    Serial.printf("Servos Moving: Safety=%.2f->%d, Shim=%.2f->%d, Reg=%.2f->%d\n",
                  safety_actual_f, (int)round(safety_final_target),
                  shim_actual_f, (int)round(shim_final_target),
                  regulating_actual_f, (int)round(regulating_final_target));
  }

  // Map 0-100% to servo angle (0-180 degrees)
  int angle_safety = (int)map(safety_actual, 0, 100, 0, 180);
  int angle_shim = (int)map(shim_actual, 0, 100, 0, 180);
  int angle_regulating = (int)map(regulating_actual, 0, 100, 0, 180);

  servo_safety.write(angle_safety);
  servo_shim.write(angle_shim);
  servo_regulating.write(angle_regulating);
}

// ============================================
// Calculate Thermal Power
// ============================================
void calculateThermalPower() {
  /*
   * Electrical Power Calculation - PWR Nuclear Reactor Model
   * Reactor Rating: 300 MWe (300,000 kW electrical)
   * 
   * Realistic Physics:
   * - Reactor menghasilkan panas thermal (dari fisi nuklir)
   * - Turbine efficiency ~33% (typical PWR)
   * - Electrical output = Thermal × Turbine Efficiency × Load
   */
  
  // Calculate reactivity from control rods
  float avgRodPosition = (shim_actual + regulating_actual) / 2.0;
  
  // Reactor thermal power capacity (0 - 900 MWth = 900,000 kW thermal)
  float reactor_thermal_kw = 0.0;
  
  if (avgRodPosition > 10.0) {
    // Non-linear power curve (quadratic untuk simulasi reaktivitas)
    reactor_thermal_kw = avgRodPosition * avgRodPosition * 90.0;
    
    // Individual rod contributions
    reactor_thermal_kw += shim_actual * 150.0;       // Coarse control
    reactor_thermal_kw += regulating_actual * 200.0; // Fine control
  }
  
  // Clamp reactor thermal output (0 - 900 MWth)
  if (reactor_thermal_kw > 900000.0) reactor_thermal_kw = 900000.0;
  
  // Turbine Conversion: Thermal → Electrical
  float turbine_load = power_level / 100.0;  // 0.0 to 1.0
  const float TURBINE_EFFICIENCY = 0.33;     // 33% thermal to electrical
  
  // Final electrical power output (MWe)
  thermal_kw_calculated = reactor_thermal_kw * TURBINE_EFFICIENCY * turbine_load;
  
  // Clamp electrical output (0 - 300 MWe)
  if (thermal_kw_calculated < 0.0) thermal_kw_calculated = 0.0;
  if (thermal_kw_calculated > 300000.0) thermal_kw_calculated = 300000.0;
}

// ============================================
// Update Turbine State
// ============================================
void updateTurbineState() {
  // TURBINE bergantung pada posisi batang kendali (rod position)
  // Calculate reactor thermal capacity for state machine
  float avgRodPosition = (shim_actual + regulating_actual) / 2.0;
  float reactor_thermal_capacity = 0.0;
  
  if (avgRodPosition > 10.0) {
    reactor_thermal_capacity = avgRodPosition * avgRodPosition * 90.0;
    reactor_thermal_capacity += shim_actual * 150.0;
    reactor_thermal_capacity += regulating_actual * 200.0;
  }
  
  switch (current_state) {
    case STATE_IDLE:
      // Start turbine when reactor thermal > 50 MWth
      if (reactor_thermal_capacity > 50000.0) {
        current_state = STATE_STARTING;
        Serial.println("Turbine: IDLE → STARTING");
      }
      power_level = 0.0;
      break;
      
    case STATE_STARTING:
      // Gradual turbine spin-up
      power_level += 0.5;
      if (power_level >= 100.0) {
        power_level = 100.0;
        current_state = STATE_RUNNING;
        Serial.println("Turbine: STARTING → RUNNING");
      }
      break;
      
    case STATE_RUNNING:
      // Shutdown if reactor thermal too low
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
  
  // POMPA TIDAK LAGI di-update di sini!
  // Pompa sekarang dikendalikan langsung oleh button command dari RasPi
}

// ============================================
// Update Humidifiers
// ============================================
void updateHumidifiers() {
  // Update relay states based on commands (inverted for low-level trigger)
  digitalWrite(RELAY_SG1, humid_sg1_cmd ? LOW : HIGH);
  digitalWrite(RELAY_SG2, humid_sg2_cmd ? LOW : HIGH);
  digitalWrite(RELAY_CT1, humid_ct1_cmd ? LOW : HIGH);
  digitalWrite(RELAY_CT2, humid_ct2_cmd ? LOW : HIGH);
  digitalWrite(RELAY_CT3, humid_ct3_cmd ? LOW : HIGH);
  digitalWrite(RELAY_CT4, humid_ct4_cmd ? LOW : HIGH);
  
  // Update status (in real system, read actual relay state)
  humid_sg1_status = humid_sg1_cmd;
  humid_sg2_status = humid_sg2_cmd;
  humid_ct1_status = humid_ct1_cmd;
  humid_ct2_status = humid_ct2_cmd;
  humid_ct3_status = humid_ct3_cmd;
  humid_ct4_status = humid_ct4_cmd;
}

// ============================================
// Motor Direction Control
// ============================================
void setMotorDirection(uint8_t motor_id, uint8_t direction) {
  /*
   * Set motor direction for L298N H-Bridge
   * Only turbine has GPIO direction control
   * 
   * Parameters:
   *   motor_id: 1=Primer, 2=Sekunder, 3=Tersier, 4=Turbin
   *   direction: MOTOR_FORWARD, MOTOR_REVERSE, MOTOR_STOP
   */
  
  // Only turbine (motor_id = 4) has GPIO control
  if (motor_id == 4) {
    if (direction == MOTOR_FORWARD) {
      digitalWrite(MOTOR_TURBINE_IN1, HIGH);
      digitalWrite(MOTOR_TURBINE_IN2, LOW);
    } else if (direction == MOTOR_REVERSE) {
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, HIGH);
    } else { // MOTOR_STOP
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, LOW);
    }
  }
  // Pumps 1-3: Direction hard-wired on L298N (always FORWARD)
}

// ============================================
// Pump Gradual Speed Control (PWM Ramp-up/down)
// ============================================
void updatePumpSpeeds() {
  /*
   * POMPA dikontrol oleh PUSH BUTTON dari Raspberry Pi
   * dengan PWM gradual (smooth ramp-up dan ramp-down)
   * 
   * Button Status dari RasPi:
   * 0 = OFF
   * 1 = STARTING (ramp-up)
   * 2 = ON (full speed)
   * 3 = SHUTTING_DOWN (ramp-down)
   */
  
  // === PRIMARY PUMP ===
  if (pump_primary_cmd == 0) {
    // OFF
    pump_primary_target = 0.0;
  } else if (pump_primary_cmd == 1) {
    // STARTING - gradual ramp-up to 50%
    pump_primary_target = 50.0;
  } else if (pump_primary_cmd == 2) {
    // ON - full speed
    pump_primary_target = 100.0;
  } else if (pump_primary_cmd == 3) {
    // SHUTTING_DOWN - ramp to 20%
    pump_primary_target = 20.0;
  }
  
  // Gradual PWM change
  if (pump_primary_actual < pump_primary_target) {
    pump_primary_actual += 1.0;  // +1% per cycle (smooth ramp-up)
    if (pump_primary_actual > pump_primary_target) {
      pump_primary_actual = pump_primary_target;
    }
  } else if (pump_primary_actual > pump_primary_target) {
    pump_primary_actual -= 2.0;  // -2% per cycle (faster ramp-down)
    if (pump_primary_actual < pump_primary_target) {
      pump_primary_actual = pump_primary_target;
    }
  }
  
  // === SECONDARY PUMP ===
  if (pump_secondary_cmd == 0) {
    pump_secondary_target = 0.0;
  } else if (pump_secondary_cmd == 1) {
    pump_secondary_target = 50.0;
  } else if (pump_secondary_cmd == 2) {
    pump_secondary_target = 100.0;
  } else if (pump_secondary_cmd == 3) {
    pump_secondary_target = 20.0;
  }
  
  if (pump_secondary_actual < pump_secondary_target) {
    pump_secondary_actual += 1.0;
    if (pump_secondary_actual > pump_secondary_target) {
      pump_secondary_actual = pump_secondary_target;
    }
  } else if (pump_secondary_actual > pump_secondary_target) {
    pump_secondary_actual -= 2.0;
    if (pump_secondary_actual < pump_secondary_target) {
      pump_secondary_actual = pump_secondary_target;
    }
  }
  
  // === TERTIARY PUMP ===
  if (pump_tertiary_cmd == 0) {
    pump_tertiary_target = 0.0;
  } else if (pump_tertiary_cmd == 1) {
    pump_tertiary_target = 50.0;
  } else if (pump_tertiary_cmd == 2) {
    pump_tertiary_target = 100.0;
  } else if (pump_tertiary_cmd == 3) {
    pump_tertiary_target = 20.0;
  }
  
  if (pump_tertiary_actual < pump_tertiary_target) {
    pump_tertiary_actual += 1.0;
    if (pump_tertiary_actual > pump_tertiary_target) {
      pump_tertiary_actual = pump_tertiary_target;
    }
  } else if (pump_tertiary_actual > pump_tertiary_target) {
    pump_tertiary_actual -= 2.0;
    if (pump_tertiary_actual < pump_tertiary_target) {
      pump_tertiary_actual = pump_tertiary_target;
    }
  }
  
  // Apply PWM to motor drivers (0-255)
  int pwm_primary = map((int)pump_primary_actual, 0, 100, 0, 255);
  int pwm_secondary = map((int)pump_secondary_actual, 0, 100, 0, 255);
  int pwm_tertiary = map((int)pump_tertiary_actual, 0, 100, 0, 255);
  
  ledcWrite(MOTOR_PUMP_PRIMARY, pwm_primary);
  ledcWrite(MOTOR_PUMP_SECONDARY, pwm_secondary);
  ledcWrite(MOTOR_PUMP_TERTIARY, pwm_tertiary);
}

// ============================================
// Turbine Motor Speed Control
// ============================================
void updateTurbineSpeed() {
  // TURBIN bergantung pada posisi batang kendali (shim & regulating rod)
  // Turbine speed based on shim and regulating rod position
  float avg_control_rods = (shim_actual + regulating_actual) / 2.0;
  
  turbine_speed = avg_control_rods;
  
  // Minimum threshold
  if (turbine_speed < 10.0) {
    turbine_speed = 0.0;
    setMotorDirection(4, MOTOR_STOP);
  } else {
    setMotorDirection(4, MOTOR_FORWARD);
  }
  
  // Convert to PWM (0-255)
  int pwm_turbine = map((int)turbine_speed, 0, 100, 0, 255);
  
  ledcWrite(MOTOR_TURBINE, pwm_turbine);
}
