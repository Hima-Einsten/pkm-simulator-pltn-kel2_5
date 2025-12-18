/*
 * ESP32 UART Communication - ESP-E (LED Visualizer)
 * INTERLEAVED 4-PIN DESIGN: Continuous water flow with direction
 * 
 * Hardware:
 * - UART2 (GPIO 16=RX, GPIO 17=TX) for communication with Raspberry Pi
 * - 12 GPIO pins for LED control (4 pins × 3 flows)
 * - 1 PWM pin for power indicator
 * 
 * LED Pattern: Interleaved for continuous flow visualization
 * Each flow has 4 pins controlling LEDs in interleaved pattern:
 *   - Pin A: LED 0, 4, 8, 12
 *   - Pin B: LED 1, 5, 9, 13
 *   - Pin C: LED 2, 6, 10, 14
 *   - Pin D: LED 3, 7, 11, 15
 * 
 * Animation: 3 of 4 pins ON at any time (75% fill)
 * Pattern shifts to show water flow direction (left to right)
 */

#include <ArduinoJson.h>

// ============================================
// UART Configuration
// ============================================
#define UART_BAUD 115200
HardwareSerial UartComm(2);  // UART2 (GPIO 16=RX, 17=TX)

// ============================================
// LED Control Pins (4 pins per flow)
// ============================================
#define NUM_FLOWS 3

// Primary Flow (Flow 0) - Interleaved pattern
const int PRIMARY_A = 32;   // LED 0, 4, 8, 12
const int PRIMARY_B = 33;   // LED 1, 5, 9, 13
const int PRIMARY_C = 25;   // LED 2, 6, 10, 14
const int PRIMARY_D = 26;   // LED 3, 7, 11, 15

// Secondary Flow (Flow 1) - Interleaved pattern
const int SECONDARY_A = 27; // LED 0, 4, 8, 12
const int SECONDARY_B = 14; // LED 1, 5, 9, 13
const int SECONDARY_C = 12; // LED 2, 6, 10, 14
const int SECONDARY_D = 13; // LED 3, 7, 11, 15

// Tertiary Flow (Flow 2) - Interleaved pattern
const int TERTIARY_A = 15;  // LED 0, 4, 8, 12
const int TERTIARY_B = 2;   // LED 1, 5, 9, 13
const int TERTIARY_C = 4;   // LED 2, 6, 10, 14
const int TERTIARY_D = 5;   // LED 3, 7, 11, 15

// Power Indicator (PWM)
const int POWER_LED_PIN = 23;  // PWM output for power visualization

// ============================================
// Flow Data
// ============================================
struct FlowData {
  float pressure;
  int pump_status;  // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
};

FlowData flows[NUM_FLOWS];
float thermal_power_kw = 0.0;

// ============================================
// Animation Variables
// ============================================
unsigned long last_animation_update = 0;
int animation_step = 0;  // 0-3 for 4-step pattern

// ============================================
// Power LED Smoothing
// ============================================
int current_brightness = 0;  // Current PWM value
int target_brightness = 0;   // Target PWM value
const int BRIGHTNESS_STEP = 3;  // Change per update (smaller = smoother)

// ============================================
// Data Persistence (keep last valid data)
// ============================================
bool data_valid = false;  // Track if we have valid data

// Interleaved pattern table
// Each row = one animation step
// Each column = pin state (A, B, C, D)
// Pattern creates "gap" that moves right-to-left (= water flows left-to-right)
const bool FLOW_PATTERN[4][4] = {
  {1, 1, 1, 0},  // Step 0: A,B,C ON, D OFF  → ●●●○●●●○●●●○●●●○
  {0, 1, 1, 1},  // Step 1: B,C,D ON, A OFF  → ○●●●○●●●○●●●○●●●
  {1, 0, 1, 1},  // Step 2: A,C,D ON, B OFF  → ●○●●●○●●●○●●●○●●
  {1, 1, 0, 1}   // Step 3: A,B,D ON, C OFF  → ●●○●●●○●●●○●●●○●
};

// ============================================
// JSON Communication
// ============================================
DynamicJsonDocument json_rx(512);
DynamicJsonDocument json_tx(256);

String rx_buffer = "";
unsigned long last_command_time = 0;
const unsigned long COMMAND_TIMEOUT = 5000;

// ============================================
// Setup
// ============================================
void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(500);

  Serial.println("\n\n===========================================");
  Serial.println("ESP-E UART Communication");
  Serial.println("LED Flow Visualizer (INTERLEAVED 4-PIN)");
  Serial.println("===========================================");

  // Initialize UART2
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  delay(2000);
  
  while (UartComm.available()) {
    UartComm.read();
  }
  
  Serial.println("✅ UART2 initialized at 115200 baud");

  // Initialize LED control pins - Primary Flow
  pinMode(PRIMARY_A, OUTPUT);
  pinMode(PRIMARY_B, OUTPUT);
  pinMode(PRIMARY_C, OUTPUT);
  pinMode(PRIMARY_D, OUTPUT);

  // Initialize LED control pins - Secondary Flow
  pinMode(SECONDARY_A, OUTPUT);
  pinMode(SECONDARY_B, OUTPUT);
  pinMode(SECONDARY_C, OUTPUT);
  pinMode(SECONDARY_D, OUTPUT);

  // Initialize LED control pins - Tertiary Flow
  pinMode(TERTIARY_A, OUTPUT);
  pinMode(TERTIARY_B, OUTPUT);
  pinMode(TERTIARY_C, OUTPUT);
  pinMode(TERTIARY_D, OUTPUT);

  // All OFF initially
  setFlowPattern(0, -1);  // Primary OFF
  setFlowPattern(1, -1);  // Secondary OFF
  setFlowPattern(2, -1);  // Tertiary OFF

  Serial.println("✅ LED pins initialized (4 pins per flow, interleaved)");

  // Initialize power indicator PWM
  ledcAttach(POWER_LED_PIN, 5000, 8);  // 5kHz, 8-bit resolution
  ledcWrite(POWER_LED_PIN, 0);  // Start OFF

  Serial.println("✅ Power indicator PWM initialized");
  
  // TEST: Blink power LED to verify PWM works
  Serial.println("Testing power LED...");
  ledcWrite(POWER_LED_PIN, 255);  // Full brightness
  delay(500);
  ledcWrite(POWER_LED_PIN, 0);    // OFF
  delay(500);
  ledcWrite(POWER_LED_PIN, 128);  // Half brightness
  delay(500);
  ledcWrite(POWER_LED_PIN, 0);    // OFF
  Serial.println("✅ Power LED test complete");

  // Initialize flow data
  for (int i = 0; i < NUM_FLOWS; i++) {
    flows[i].pressure = 0.0;
    flows[i].pump_status = 0;
  }

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
      processCommand(rx_buffer);
      rx_buffer = "";
    } else {
      rx_buffer += c;

      if (rx_buffer.length() > 256) {
        Serial.println("⚠️  RX buffer overflow");
        rx_buffer = "";
      }
    }
  }

  // Safety timeout - but DON'T clear thermal_power immediately
  // Only clear if timeout is very long (no data for 10+ seconds)
  if (millis() - last_command_time > 10000) {  // 10 seconds (was 5)
    if (thermal_power_kw > 0.0) {
      Serial.println("⚠️  Long communication timeout - Clearing display");
      thermal_power_kw = 0.0;
      for (int i = 0; i < NUM_FLOWS; i++) {
        flows[i].pressure = 0.0;
        flows[i].pump_status = 0;
      }
      data_valid = false;
    }
    last_command_time = millis();
  }

  // Update animations
  updateAnimations();
  updatePowerIndicator();

  delay(10);
}

// ============================================
// Process JSON Command
// ============================================
void processCommand(String command) {
  if (command.length() == 0) return;

  Serial.print("RX: ");
  Serial.println(command);

  DeserializationError error = deserializeJson(json_rx, command);

  if (error) {
    Serial.print("❌ JSON parse error: ");
    Serial.println(error.c_str());
    Serial.print("   Raw data: ");
    Serial.println(command);
    
    // DON'T reset data - keep last valid values!
    // This prevents LED from turning off on temporary communication errors
    Serial.println("⚠️  Keeping last valid data");
    
    // Only send error if it's not a ping (to avoid breaking handshake)
    if (command.indexOf("ping") == -1) {
      sendError("JSON parse error");
    }
    
    // Clear RX buffer to prevent corruption
    while (UartComm.available()) {
      UartComm.read();
    }
    
    return;
  }

  const char* cmd = json_rx["cmd"];
  
  // Safety check for null cmd
  if (cmd == nullptr) {
    Serial.println("⚠️  Command field missing");
    return;
  }

  if (strcmp(cmd, "update") == 0) {
    handleUpdateCommand();
    last_command_time = millis();
  } else if (strcmp(cmd, "ping") == 0) {
    sendPong();
  } else {
    sendError("Unknown command");
  }
}

// ============================================
// Handle Update Command
// ============================================
void handleUpdateCommand() {
  if (json_rx.containsKey("flows")) {
    JsonArray flows_array = json_rx["flows"];

    for (int i = 0; i < NUM_FLOWS && i < flows_array.size(); i++) {
      JsonObject flow = flows_array[i];
      flows[i].pressure = flow["pressure"];
      flows[i].pump_status = flow["pump"];
    }
  } else if (json_rx.containsKey("pumps")) {
    JsonArray pumps_array = json_rx["pumps"];
    for (int i = 0; i < NUM_FLOWS && i < pumps_array.size(); i++) {
      flows[i].pump_status = pumps_array[i];
    }
  }

  if (json_rx.containsKey("thermal_kw")) {
    thermal_power_kw = json_rx["thermal_kw"];
    data_valid = true;  // Mark data as valid
  }

  Serial.printf("Flows: P1=%d, P2=%d, P3=%d, Thermal=%.1fkW\n",
                flows[0].pump_status, flows[1].pump_status,
                flows[2].pump_status, thermal_power_kw);

  sendStatus();
}

// ============================================
// Send Status Response
// ============================================
void sendStatus() {
  json_tx.clear();
  json_tx["status"] = "ok";
  json_tx["anim_step"] = animation_step;
  json_tx["led_count"] = 16;

  serializeJson(json_tx, UartComm);
  UartComm.println();
  UartComm.flush();

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
  json_tx["device"] = "ESP-E";

  serializeJson(json_tx, UartComm);
  UartComm.println();
  UartComm.flush();

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
  UartComm.flush();
}

// ============================================
// Update Animations
// ============================================
void updateAnimations() {
  unsigned long current_time = millis();

  // Update animation every 500ms for smooth water flow
  if (current_time - last_animation_update < 500) {
    return;
  }
  last_animation_update = current_time;

  // Advance to next step (0 → 1 → 2 → 3 → 0)
  animation_step++;
  if (animation_step >= 4) {
    animation_step = 0;
  }

  // Update each flow based on pump status
  for (int flow_idx = 0; flow_idx < NUM_FLOWS; flow_idx++) {
    if (flows[flow_idx].pump_status == 2) {  // ON
      setFlowPattern(flow_idx, animation_step);
    } else {
      // Turn off this flow
      setFlowPattern(flow_idx, -1);  // -1 = all OFF
    }
  }
}

// ============================================
// Set Flow Pattern (Interleaved)
// ============================================
void setFlowPattern(int flow_idx, int step) {
  int pin_a, pin_b, pin_c, pin_d;

  // Select pins based on flow index
  if (flow_idx == 0) {
    pin_a = PRIMARY_A;
    pin_b = PRIMARY_B;
    pin_c = PRIMARY_C;
    pin_d = PRIMARY_D;
  } else if (flow_idx == 1) {
    pin_a = SECONDARY_A;
    pin_b = SECONDARY_B;
    pin_c = SECONDARY_C;
    pin_d = SECONDARY_D;
  } else {
    pin_a = TERTIARY_A;
    pin_b = TERTIARY_B;
    pin_c = TERTIARY_C;
    pin_d = TERTIARY_D;
  }

  if (step == -1) {
    // All OFF (pump not running)
    digitalWrite(pin_a, LOW);
    digitalWrite(pin_b, LOW);
    digitalWrite(pin_c, LOW);
    digitalWrite(pin_d, LOW);
  } else {
    // Apply interleaved pattern from table
    digitalWrite(pin_a, FLOW_PATTERN[step][0] ? HIGH : LOW);
    digitalWrite(pin_b, FLOW_PATTERN[step][1] ? HIGH : LOW);
    digitalWrite(pin_c, FLOW_PATTERN[step][2] ? HIGH : LOW);
    digitalWrite(pin_d, FLOW_PATTERN[step][3] ? HIGH : LOW);
  }
}

// ============================================
// Update Power Indicator (PWM with Smoothing)
// ============================================
void updatePowerIndicator() {
  // Calculate power ratio (0.0 to 1.0)
  const float MAX_THERMAL_KW = 300000.0;  // 300 MW = 300,000 kW
  float ratio = thermal_power_kw / MAX_THERMAL_KW;

  // Clamp to valid range
  if (ratio > 1.0) ratio = 1.0;
  if (ratio < 0.0) ratio = 0.0;

  // Convert to target PWM brightness (0-255)
  target_brightness = (int)(ratio * 255);
  
  // Minimum brightness when reactor is running (for visibility)
  if (thermal_power_kw > 0.0 && target_brightness < 20) {
    target_brightness = 20;
  }

  // SMOOTH TRANSITION: Gradually move current to target
  if (current_brightness < target_brightness) {
    current_brightness += BRIGHTNESS_STEP;
    if (current_brightness > target_brightness) {
      current_brightness = target_brightness;
    }
  } else if (current_brightness > target_brightness) {
    current_brightness -= BRIGHTNESS_STEP;
    if (current_brightness < target_brightness) {
      current_brightness = target_brightness;
    }
  }

  // OPTION 1: Normal PWM (active-HIGH)
  ledcWrite(POWER_LED_PIN, current_brightness);
  
  // OPTION 2: Inverted PWM (active-LOW) - uncomment if LED is inverted
  // ledcWrite(POWER_LED_PIN, 255 - current_brightness);
  
  // Debug output (every 2 seconds)
  static unsigned long last_debug = 0;
  if (millis() - last_debug > 2000) {
    Serial.printf("Power: %.1f kW, Ratio: %.2f, Current: %d, Target: %d, Valid: %s\n", 
                  thermal_power_kw, ratio, current_brightness, target_brightness,
                  data_valid ? "YES" : "NO");
    last_debug = millis();
  }
}
