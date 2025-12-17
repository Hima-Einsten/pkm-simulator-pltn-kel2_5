/*
 * ESP32 UART Communication - ESP-E (LED Visualizer)
 * Replaces I2C slave with UART communication
 * 
 * Hardware:
 * - UART2 (GPIO 16=RX, GPIO 17=TX) for communication with Raspberry Pi
 * - Serial (USB) for debugging
 * - 48 LEDs via multiplexers for 3 flow visualizations
 * 
 * Protocol: JSON over UART (115200 baud, 8N1)
 */

#include <ArduinoJson.h>

// ============================================
// UART Configuration
// ============================================
#define UART_BAUD 115200
HardwareSerial UartComm(2);  // UART2 (GPIO 16=RX, 17=TX)

// ============================================
// LED Multiplexer Configuration
// ============================================
#define NUM_LEDS 16
#define NUM_FLOWS 3

// Multiplexer selector pins (shared)
const int S0 = 14;
const int S1 = 27;
const int S2 = 26;
const int S3 = 25;

// Multiplexer enable pins (1 per flow)
const int EN_PRIMARY = 33;
const int EN_SECONDARY = 15;
const int EN_TERTIARY = 2;

// PWM signal pins (1 per flow)
const int SIG_PRIMARY = 32;
const int SIG_SECONDARY = 4;
const int SIG_TERTIARY = 21;

// ============================================
// Power Indicator LEDs (3 groups)
// ============================================
const int POWER_LED_DIRECT_PINS[3] = { 23, 19, 18 };

// ============================================
// Flow Data
// ============================================
struct FlowData {
  float pressure;
  int pump_status;  // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
  int animation_speed;
};

FlowData flows[NUM_FLOWS];
float thermal_power_kw = 0.0;

// ============================================
// Animation Variables
// ============================================
unsigned long last_animation_update = 0;
int animation_phase = 0;

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
  Serial.println("LED Flow Visualizer (3 Flows)");
  Serial.println("===========================================");

  // Initialize UART2
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  Serial.println("✅ UART2 initialized at 115200 baud");
  Serial.println("   RX: GPIO 16");
  Serial.println("   TX: GPIO 17");

  // Initialize multiplexer selector pins
  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(S3, OUTPUT);

  // Initialize enable pins
  pinMode(EN_PRIMARY, OUTPUT);
  pinMode(EN_SECONDARY, OUTPUT);
  pinMode(EN_TERTIARY, OUTPUT);

  // Initialize PWM pins
  ledcAttach(SIG_PRIMARY, 5000, 8);
  ledcAttach(SIG_SECONDARY, 5000, 8);
  ledcAttach(SIG_TERTIARY, 5000, 8);

  // All disabled initially
  digitalWrite(EN_PRIMARY, HIGH);  // Active LOW
  digitalWrite(EN_SECONDARY, HIGH);
  digitalWrite(EN_TERTIARY, HIGH);

  Serial.println("✅ LED multiplexers initialized");

  // Initialize power indicator LEDs
  for (int i = 0; i < 3; i++) {
    ledcAttach(POWER_LED_DIRECT_PINS[i], 5000, 8);
    ledcWrite(POWER_LED_DIRECT_PINS[i], 0);
  }
  Serial.println("✅ Power indicator LEDs initialized");

  // Initialize flow data
  for (int i = 0; i < NUM_FLOWS; i++) {
    flows[i].pressure = 0.0;
    flows[i].pump_status = 0;
    flows[i].animation_speed = 0;
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

  // Safety timeout
  if (millis() - last_command_time > COMMAND_TIMEOUT) {
    if (thermal_power_kw > 0.0) {
      Serial.println("⚠️  Communication timeout - Clearing display");
      thermal_power_kw = 0.0;
      for (int i = 0; i < NUM_FLOWS; i++) {
        flows[i].pressure = 0.0;
        flows[i].pump_status = 0;
      }
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
    sendError("JSON parse error");
    return;
  }

  const char* cmd = json_rx["cmd"];

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
  // Parse flow data
  if (json_rx.containsKey("flows")) {
    JsonArray flows_array = json_rx["flows"];

    for (int i = 0; i < NUM_FLOWS && i < flows_array.size(); i++) {
      JsonObject flow = flows_array[i];
      flows[i].pressure = flow["pressure"];
      flows[i].pump_status = flow["pump"];

      // Calculate animation speed based on pressure and pump status
      if (flows[i].pump_status == 2) {  // ON
        flows[i].animation_speed = map(flows[i].pressure, 0, 200, 0, 255);
      } else {
        flows[i].animation_speed = 0;
      }
    }
  }

  // Parse thermal power
  if (json_rx.containsKey("thermal_kw")) {
    thermal_power_kw = json_rx["thermal_kw"];
  }

  Serial.printf("Flows: P1=%.1f/%d, P2=%.1f/%d, P3=%.1f/%d, Thermal=%.1fkW\n",
                flows[0].pressure, flows[0].pump_status,
                flows[1].pressure, flows[1].pump_status,
                flows[2].pressure, flows[2].pump_status,
                thermal_power_kw);

  sendStatus();
}

// ============================================
// Send Status Response
// ============================================
void sendStatus() {
  json_tx.clear();

  json_tx["status"] = "ok";
  json_tx["anim_speed"] = flows[0].animation_speed;  // Primary flow
  json_tx["led_count"] = NUM_LEDS;

  serializeJson(json_tx, UartComm);
  UartComm.println();

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
// Set Multiplexer Channel
// ============================================
void setMux(int channel) {
  digitalWrite(S0, channel & 1);
  digitalWrite(S1, (channel >> 1) & 1);
  digitalWrite(S2, (channel >> 2) & 1);
  digitalWrite(S3, (channel >> 3) & 1);
}

// ============================================
// Update Animations
// ============================================
void updateAnimations() {
  unsigned long current_time = millis();

  // Update animation every 50ms
  if (current_time - last_animation_update < 50) {
    return;
  }
  last_animation_update = current_time;

  animation_phase++;
  if (animation_phase >= NUM_LEDS) {
    animation_phase = 0;
  }

  // Update each flow
  for (int flow_idx = 0; flow_idx < NUM_FLOWS; flow_idx++) {
    if (flows[flow_idx].pump_status == 2) {  // ON
      // Enable this flow's multiplexer
      enableFlow(flow_idx, true);

      // Animate LEDs
      for (int led = 0; led < NUM_LEDS; led++) {
        setMux(led);

        // Wave effect
        int brightness = 0;
        int distance = abs(led - animation_phase);
        if (distance < 3) {
          brightness = map(3 - distance, 0, 3, 0, flows[flow_idx].animation_speed);
        }

        setFlowBrightness(flow_idx, brightness);
        delayMicroseconds(100);
      }
    } else {
      // Turn off this flow
      enableFlow(flow_idx, false);
    }
  }
}

// ============================================
// Enable/Disable Flow
// ============================================
void enableFlow(int flow_idx, bool enable) {
  int pin = (flow_idx == 0) ? EN_PRIMARY : (flow_idx == 1) ? EN_SECONDARY
                                                           : EN_TERTIARY;
  digitalWrite(pin, enable ? LOW : HIGH);  // Active LOW
}

// ============================================
// Set Flow Brightness
// ============================================
void setFlowBrightness(int flow_idx, int brightness) {
  int pin = (flow_idx == 0) ? SIG_PRIMARY : (flow_idx == 1) ? SIG_SECONDARY
                                                            : SIG_TERTIARY;
  ledcWrite(pin, brightness);
}

// ============================================
// Update Power Indicator
// ============================================
void updatePowerIndicator() {
  // Calculate power ratio (0.0 to 1.0)
  const float MAX_THERMAL_MWE = 300.0;  // 300 MW max
  float power_mwe = thermal_power_kw / 1000.0;
  float ratio = power_mwe / MAX_THERMAL_MWE;

  if (ratio > 1.0) ratio = 1.0;
  if (ratio < 0.0) ratio = 0.0;

  int brightness = (int)(ratio * 255);
  if (brightness > 0 && brightness < 20) brightness = 20;

  // LED group 1 (always on when power > 0%)
  if (ratio > 0.0) {
    ledcWrite(POWER_LED_DIRECT_PINS[0], brightness);
  } else {
    ledcWrite(POWER_LED_DIRECT_PINS[0], 0);
  }

  // LED group 2 (on when power > 30%)
  if (ratio > 0.3) {
    ledcWrite(POWER_LED_DIRECT_PINS[1], brightness);
  } else {
    ledcWrite(POWER_LED_DIRECT_PINS[1], 0);
  }

  // LED group 3 (on when power > 70%)
  if (ratio > 0.7) {
    ledcWrite(POWER_LED_DIRECT_PINS[2], brightness);
  } else {
    ledcWrite(POWER_LED_DIRECT_PINS[2], 0);
  }
}
