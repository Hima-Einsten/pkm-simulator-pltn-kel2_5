/*
 * ESP32 LED Flow Visualizer - SIMPLIFIED VERSION
 * 
 * Changes:
 * - Ultra-simplified code structure
 * - Changed problematic pins (12,13,15,2 → 18,19,21,22)
 * - Minimal JSON parsing
 * - No complex state management
 */

#include <ArduinoJson.h>

// ================= UART =================
#define UART_BAUD 115200
HardwareSerial UartComm(2); // RX=16 TX=17

// ================= FLOW PINS =================
#define NUM_FLOWS 3

// Flow 0 (Primary) - UNCHANGED
#define F0_A 32
#define F0_B 33
#define F0_C 25
#define F0_D 26

// Flow 1 (Secondary) - CHANGED: 14,12,13 → 14,18,19
#define F1_A 27
#define F1_B 14
#define F1_C 18  // Was 12 (boot strapping pin - problematic!)
#define F1_D 19  // Was 13 (boot strapping pin - problematic!)

// Flow 2 (Tertiary) - CHANGED: 15,2,4,5 → 21,22,4,5
#define F2_A 21  // Was 15 (boot strapping pin - problematic!)
#define F2_B 22  // Was 2 (boot mode pin - problematic!)
#define F2_C 4
#define F2_D 5

// Power LED
#define POWER_LED 23

// ================= DATA =================
struct FlowData {
  float pressure;
  int pump;  // 0=OFF, 1=STARTING, 2=ON, 3=STOPPING
};

FlowData flows[NUM_FLOWS];
float thermal_kw = 0.0;

// ================= ANIMATION =================
int anim_step = 0;
unsigned long last_anim = 0;

const bool PATTERN[4][4] = {
  {1, 1, 1, 0},  // Step 0
  {0, 1, 1, 1},  // Step 1
  {1, 0, 1, 1},  // Step 2
  {1, 1, 0, 1}   // Step 3
};

// ================= JSON =================
StaticJsonDocument<768> rx;  // Static allocation - more stable!
StaticJsonDocument<256> tx;
String rx_buf = "";

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP-E LED Flow Visualizer (SIMPLIFIED)");
  Serial.println("===========================================");
  
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  delay(1000);

  // Initialize all LED pins
  int pins[] = {
    F0_A, F0_B, F0_C, F0_D,
    F1_A, F1_B, F1_C, F1_D,
    F2_A, F2_B, F2_C, F2_D
  };

  for (int p : pins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }

  // Initialize power LED
  ledcAttach(POWER_LED, 5000, 8);
  ledcWrite(POWER_LED, 0);

  Serial.println("✅ All pins initialized");
  Serial.println("✅ UART ready at 115200 baud");
  Serial.println("===========================================");
  Serial.println("✅ ESP32 LED Flow READY - Waiting for data...");
  Serial.println("===========================================\n");
}

// ================= LOOP =================
void loop() {
  // Read UART data - LIMIT reads per loop to prevent watchdog timeout!
  int read_count = 0;
  const int MAX_READS_PER_LOOP = 64;  // Prevent infinite loop
  
  while (UartComm.available() && read_count < MAX_READS_PER_LOOP) {
    char c = UartComm.read();
    read_count++;
    
    if (c == '\n') {
      handleCommand(rx_buf);
      rx_buf = "";
    } else if (c != '\r') {  // Ignore carriage return
      rx_buf += c;
      
      // Safety: prevent buffer overflow
      if (rx_buf.length() > 600) {
        Serial.println("Buffer overflow - clearing");
        rx_buf = "";
      }
    }
    
    // Feed watchdog every few reads
    if (read_count % 16 == 0) {
      yield();  // Let other tasks run
    }
  }

  // Update animations
  animateFlows();
  
  // Update power LED
  updatePower();
  
  // Feed watchdog
  yield();
  delay(10);
}

// ================= JSON HANDLER =================
void handleCommand(String cmd) {
  if (cmd.length() == 0) return;
  
  // Safety check - reject oversized commands
  if (cmd.length() > 500) {
    Serial.println("Command too long - rejected");
    return;
  }
  
  Serial.print("RX: ");
  Serial.println(cmd);
  
  // Clear document before parsing (CRITICAL!)
  rx.clear();
  
  DeserializationError error = deserializeJson(rx, cmd);
  
  if (error) {
    Serial.print("JSON error: ");
    Serial.println(error.c_str());
    // Don't crash - just skip this command
    return;
  }

  const char* command = rx["cmd"];
  if (command == nullptr) {
    Serial.println("No cmd field");
    return;
  }
  
  if (strcmp(command, "ping") == 0) {
    sendPong();
    return;
  }
  
  if (strcmp(command, "update") != 0) {
    Serial.println("Unknown cmd");
    return;
  }

  // Parse flows array
  JsonArray arr = rx["flows"];
  if (arr.isNull()) {
    Serial.println("No flows array!");
    return;
  }
  
  // Safely parse each flow
  for (int i = 0; i < NUM_FLOWS && i < arr.size(); i++) {
    JsonObject flow_obj = arr[i];
    if (!flow_obj.isNull()) {
      flows[i].pump = flow_obj["pump"] | 0;
      flows[i].pressure = flow_obj["pressure"] | 0.0;
    }
  }

  // Parse thermal power
  thermal_kw = rx["thermal_kw"] | 0.0;

  Serial.printf("Update: P1=%d P2=%d P3=%d Thermal=%.0fkW\n",
                flows[0].pump, flows[1].pump, flows[2].pump, thermal_kw);

  sendAck();
}

// ================= FLOW ANIMATION =================
void animateFlows() {
  if (millis() - last_anim < 500) return;
  last_anim = millis();

  anim_step = (anim_step + 1) % 4;

  for (int i = 0; i < NUM_FLOWS; i++) {
    if (flows[i].pump == 2) {  // ON
      setFlow(i, anim_step);
    } else {
      setFlow(i, -1);  // OFF
    }
  }
}

void setFlow(int flow_idx, int step) {
  int pins[4];
  
  if (flow_idx == 0) {
    pins[0] = F0_A; pins[1] = F0_B; pins[2] = F0_C; pins[3] = F0_D;
  } else if (flow_idx == 1) {
    pins[0] = F1_A; pins[1] = F1_B; pins[2] = F1_C; pins[3] = F1_D;
  } else {
    pins[0] = F2_A; pins[1] = F2_B; pins[2] = F2_C; pins[3] = F2_D;
  }

  for (int i = 0; i < 4; i++) {
    if (step >= 0) {
      digitalWrite(pins[i], PATTERN[step][i] ? HIGH : LOW);
    } else {
      digitalWrite(pins[i], LOW);
    }
  }
}

// ================= POWER LED =================
void updatePower() {
  static unsigned long last_update = 0;
  
  if (millis() - last_update < 2000) return;
  last_update = millis();
  
  // Map thermal power to PWM (0-300MW → 0-255)
  int pwm = map(thermal_kw, 0, 300000, 0, 255);
  pwm = constrain(pwm, 0, 255);
  
  // Minimum brightness when reactor running
  if (thermal_kw > 0 && pwm < 20) pwm = 20;
  
  ledcWrite(POWER_LED, pwm);
  
  Serial.printf("Power: %.0fkW PWM=%d\n", thermal_kw, pwm);
}

// ================= RESPONSES =================
void sendAck() {
  tx.clear();
  tx["status"] = "ok";
  tx["anim_step"] = anim_step;
  tx["led_count"] = 16;
  
  serializeJson(tx, UartComm);
  UartComm.println();
  UartComm.flush();
}

void sendPong() {
  tx.clear();
  tx["status"] = "ok";
  tx["message"] = "pong";
  tx["device"] = "ESP-E";
  
  serializeJson(tx, UartComm);
  UartComm.println();
  UartComm.flush();
  
  Serial.println("TX: pong");
}
