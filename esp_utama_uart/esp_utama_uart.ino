/*
 * ESP32 UART Communication - ESP-BC (Control Rods + Turbine + Humidifier)
 * Replaces I2C slave with UART communication
 * 
 * Hardware:
 * - UART2 (GPIO 16=RX, GPIO 17=TX) for communication with Raspberry Pi
 * - Serial (USB) for debugging
 * 
 * Protocol: JSON over UART (115200 baud, 8N1)
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

int safety_actual = 0;
int shim_actual = 0;
int regulating_actual = 0;

// ============================================
// Humidifier Relays
// ============================================
const int RELAY_SG1 = 25;  // Steam Generator 1
const int RELAY_SG2 = 26;  // Steam Generator 2
const int RELAY_CT1 = 27;  // Cooling Tower 1
const int RELAY_CT2 = 32;  // Cooling Tower 2
const int RELAY_CT3 = 33;  // Cooling Tower 3
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
int current_state = 0;      // 0=OFF, 1=STARTUP, 2=RUNNING, 3=SHUTDOWN
float power_level = 0.0;    // Turbine power (0-100%)
float thermal_kw_calculated = 0.0;

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
  Serial.println("Control Rods + Turbine + Humidifier");
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
  
  // All relays OFF initially
  digitalWrite(RELAY_SG1, LOW);
  digitalWrite(RELAY_SG2, LOW);
  digitalWrite(RELAY_CT1, LOW);
  digitalWrite(RELAY_CT2, LOW);
  digitalWrite(RELAY_CT3, LOW);
  digitalWrite(RELAY_CT4, LOW);
  Serial.println("✅ Humidifier relays initialized");
  
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
  
  delay(10);
}

// ============================================
// Process JSON Command
// ============================================
void processCommand(String command) {
  if (command.length() == 0) return;
  
  Serial.print("RX: ");
  Serial.println(command);
  
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
  
  Serial.printf("Targets: Rods=[%d,%d,%d], Humid_SG=[%d,%d], Humid_CT=[%d,%d,%d,%d]\n",
                safety_target, shim_target, regulating_target,
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
  
  // Thermal power
  json_tx["thermal_kw"] = thermal_kw_calculated;
  json_tx["power_level"] = power_level;
  json_tx["state"] = current_state;
  
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
void updateServos() {
  // Smoothly move to target (1% per cycle)
  if (safety_actual < safety_target) safety_actual++;
  if (safety_actual > safety_target) safety_actual--;
  
  if (shim_actual < shim_target) shim_actual++;
  if (shim_actual > shim_target) shim_actual--;
  
  if (regulating_actual < regulating_target) regulating_actual++;
  if (regulating_actual > regulating_target) regulating_actual--;
  
  // Map 0-100% to servo angle (0-180 degrees)
  int angle_safety = map(safety_actual, 0, 100, 0, 180);
  int angle_shim = map(shim_actual, 0, 100, 0, 180);
  int angle_regulating = map(regulating_actual, 0, 100, 0, 180);
  
  servo_safety.write(angle_safety);
  servo_shim.write(angle_shim);
  servo_regulating.write(angle_regulating);
}

// ============================================
// Calculate Thermal Power
// ============================================
void calculateThermalPower() {
  // Average rod insertion
  float avg_insertion = (safety_actual + shim_actual + regulating_actual) / 3.0;
  
  // Thermal power calculation (simplified)
  // Max thermal: 300 MW = 300,000 kW
  // Power increases with rod insertion
  const float MAX_THERMAL_KW = 300000.0;
  thermal_kw_calculated = (avg_insertion / 100.0) * MAX_THERMAL_KW;
}

// ============================================
// Update Turbine State
// ============================================
void updateTurbineState() {
  // Simplified turbine state machine
  if (thermal_kw_calculated > 50000.0) {
    current_state = 2;  // RUNNING
    power_level = (thermal_kw_calculated / 300000.0) * 100.0;
  } else if (thermal_kw_calculated > 10000.0) {
    current_state = 1;  // STARTUP
    power_level = 10.0;
  } else {
    current_state = 0;  // OFF
    power_level = 0.0;
  }
  
  // Clamp power level
  if (power_level > 100.0) power_level = 100.0;
  if (power_level < 0.0) power_level = 0.0;
}

// ============================================
// Update Humidifiers
// ============================================
void updateHumidifiers() {
  // Update relay states based on commands
  digitalWrite(RELAY_SG1, humid_sg1_cmd ? HIGH : LOW);
  digitalWrite(RELAY_SG2, humid_sg2_cmd ? HIGH : LOW);
  digitalWrite(RELAY_CT1, humid_ct1_cmd ? HIGH : LOW);
  digitalWrite(RELAY_CT2, humid_ct2_cmd ? HIGH : LOW);
  digitalWrite(RELAY_CT3, humid_ct3_cmd ? HIGH : LOW);
  digitalWrite(RELAY_CT4, humid_ct4_cmd ? HIGH : LOW);
  
  // Update status (in real system, read actual relay state)
  humid_sg1_status = humid_sg1_cmd;
  humid_sg2_status = humid_sg2_cmd;
  humid_ct1_status = humid_ct1_cmd;
  humid_ct2_status = humid_ct2_cmd;
  humid_ct3_status = humid_ct3_cmd;
  humid_ct4_status = humid_ct4_cmd;
}
