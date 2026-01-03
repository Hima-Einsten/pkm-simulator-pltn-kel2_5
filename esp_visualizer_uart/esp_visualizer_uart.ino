/*
 * ESP32 Power Indicator - SIMPLIFIED VERSION
 * 
 * Fungsi:
 * - Hanya kontrol 1 LED power indicator untuk visualisasi daya reaktor
 * - Komunikasi UART dengan Raspberry Pi
 * - LED brightness proporsional dengan daya output (0-300 MWe)
 * 
 * Perubahan:
 * - ❌ REMOVED: 48 LED flow visualization (akan dikembangkan nanti)
 * - ❌ REMOVED: Flow animation logic
 * - ✅ KEPT: Power LED indicator (GPIO 23)
 * - ✅ SIMPLIFIED: Protocol hanya terima thermal_kw
 */

#include <ArduinoJson.h>

// ================= UART =================
#define UART_BAUD 115200
HardwareSerial UartComm(2); // RX=16 TX=17

// ================= LED PIN =================
#define POWER_LED 23  // LED visualisasi daya reaktor

// ================= DATA =================
float thermal_kw = 0.0;      // Thermal power dalam kW (0-300000)
float power_mwe = 0.0;       // Electrical power dalam MWe (0-300)
int current_pwm = 0;         // Current PWM value (0-255)

// ================= JSON =================
StaticJsonDocument<256> rx;
StaticJsonDocument<256> tx;
String rx_buf = "";

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP-E Power Indicator (SIMPLIFIED)");
  Serial.println("===========================================");
  Serial.println("Fungsi: Visualisasi daya reaktor");
  Serial.println("LED: 1x Power Indicator (GPIO 23)");
  Serial.println("===========================================");
  
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  delay(500);

  // Initialize power LED
  pinMode(POWER_LED, OUTPUT);
  ledcAttach(POWER_LED, 5000, 8);  // 5kHz, 8-bit
  ledcWrite(POWER_LED, 0);

  Serial.println("Power LED initialized (GPIO 23)");
  Serial.println("UART ready at 115200 baud");
  Serial.println("===========================================");
  Serial.println("ESP32 Power Indicator READY");
  Serial.println("===========================================\n");
  
  // Test LED - flash 3 times
  Serial.println("Testing LED...");
  for (int i = 0; i < 3; i++) {
    ledcWrite(POWER_LED, 255);
    delay(200);
    ledcWrite(POWER_LED, 0);
    delay(200);
  }
  Serial.println("LED test complete\n");
}

// ================= LOOP =================
void loop() {
  // Read UART data
  int read_count = 0;
  const int MAX_READS_PER_LOOP = 64;
  
  while (UartComm.available() && read_count < MAX_READS_PER_LOOP) {
    char c = UartComm.read();
    read_count++;
    
    if (c == '\n') {
      handleCommand(rx_buf);
      rx_buf = "";
    } else if (c != '\r') {
      rx_buf += c;
      
      // Safety: prevent buffer overflow
      if (rx_buf.length() > 300) {
        Serial.println("Buffer overflow - clearing");
        rx_buf = "";
      }
    }
    
    // Feed watchdog
    if (read_count % 16 == 0) {
      yield();
    }
  }

  // Update power LED
  updatePowerLED();
  
  yield();
  delay(10);
}

// ================= COMMAND HANDLER =================
void handleCommand(String cmd) {
  if (cmd.length() == 0) return;
  
  // Safety check
  if (cmd.length() > 250) {
    Serial.println("Command too long - rejected");
    return;
  }
  
  Serial.print("RX: ");
  Serial.println(cmd);
  
  // Clear document before parsing
  rx.clear();
  
  DeserializationError error = deserializeJson(rx, cmd);
  
  if (error) {
    Serial.print("JSON error: ");
    Serial.println(error.c_str());
    return;
  }

  const char* command = rx["cmd"];
  if (command == nullptr) {
    Serial.println("No cmd field");
    return;
  }
  
  // Handle ping command
  if (strcmp(command, "ping") == 0) {
    sendPong();
    return;
  }
  
  // Handle update command
  if (strcmp(command, "update") == 0) {
    // Parse thermal power
    thermal_kw = rx["thermal_kw"] | 0.0;
    
    // Convert kW to MWe
    power_mwe = thermal_kw / 1000.0;
    
    Serial.printf("Update: Thermal=%.1f kW → Power=%.1f MWe\n", 
                  thermal_kw, power_mwe);
    
    sendAck();
    return;
  }
  
  Serial.println("Unknown command");
}

// ================= POWER LED UPDATE =================
void updatePowerLED() {
  static unsigned long last_update = 0;
  
  // Update every 100ms
  if (millis() - last_update < 100) return;
  last_update = millis();
  
  // Calculate PWM based on power output
  // 0-300 MWe → 0-255 PWM
  int target_pwm = 0;
  
  if (power_mwe > 0) {
    target_pwm = map(power_mwe * 1000, 0, 300000, 0, 255);
    target_pwm = constrain(target_pwm, 0, 255);
    
    // Minimum brightness when reactor running
    if (target_pwm < 20) {
      target_pwm = 20;
    }
  }
  
  // Smooth transition (avoid sudden jumps)
  if (target_pwm > current_pwm) {
    current_pwm += min(5, target_pwm - current_pwm);
  } else if (target_pwm < current_pwm) {
    current_pwm -= min(5, current_pwm - target_pwm);
  }
  
  // Apply PWM
  ledcWrite(POWER_LED, current_pwm);
  
  // Debug output every 2 seconds
  static unsigned long last_debug = 0;
  if (millis() - last_debug > 2000) {
    last_debug = millis();
    Serial.printf("Power: %.1f MWe | PWM: %d/255 | Brightness: %d%%\n", 
                  power_mwe, current_pwm, (current_pwm * 100) / 255);
  }
}

// ================= RESPONSES =================
void sendAck() {
  tx.clear();
  tx["status"] = "ok";
  tx["power_mwe"] = power_mwe;
  tx["pwm"] = current_pwm;
  
  serializeJson(tx, UartComm);
  UartComm.println();
  UartComm.flush();
  
  Serial.print("TX: ");
  serializeJson(tx, Serial);
  Serial.println();
}

void sendPong() {
  tx.clear();
  tx["status"] = "ok";
  tx["message"] = "pong";
  tx["device"] = "ESP-E-PowerOnly";
  tx["version"] = "1.0";
  
  serializeJson(tx, UartComm);
  UartComm.println();
  UartComm.flush();
  
  Serial.println("TX: pong");
}
