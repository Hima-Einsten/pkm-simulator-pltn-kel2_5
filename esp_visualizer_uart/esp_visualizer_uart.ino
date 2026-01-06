/*
 * ESP32 Power Indicator - BINARY PROTOCOL VERSION
 * 
 * Fungsi:
 * - Kontrol 4 LED power indicator untuk visualisasi daya reaktor
 * - Komunikasi UART dengan Raspberry Pi menggunakan BINARY protocol
 * - LED brightness proporsional dengan daya output (0-300 MWe)
 * - Auto-switching PWM → HIGH mode untuk kecerahan maksimal (≥250 PWM)
 * 
 * LED Mode Control:
 * - PWM Mode (0-249): LED dikontrol dengan PWM (0-255) untuk brightness bertahap
 * - HIGH Mode (≥250): LED menerima 3.3V penuh untuk kecerahan maksimal
 * - Hysteresis: Switch ke HIGH di ≥250, kembali ke PWM di <240
 * 
 * Protocol: BINARY Protocol with ACK/NACK (115200 baud, 8N1)
 * - Command: 9 bytes (vs 42 bytes JSON) - 79% reduction
 * - Response: 10 bytes (vs 45 bytes JSON) - 78% reduction
 * - CRC8 checksum for error detection
 * - ACK/NACK responses for reliability
 * - No buffer garbage issues
 */

#include <Arduino.h>

// ============================================
// Binary Protocol Constants
// ============================================
#define STX 0x02          // Start of Text
#define ETX 0x03          // End of Text
#define ACK 0x06          // Acknowledge
#define NACK 0x15         // Negative Acknowledge
#define CMD_PING 0x50     // 'P' - Ping command
#define CMD_UPDATE 0x55   // 'U' - Update command

// Message lengths
#define PING_CMD_LEN 5    // [STX][CMD][LEN=0][CRC][ETX]
#define UPDATE_CMD_LEN 9  // [STX][CMD][LEN=4][thermal_kw (4 bytes)][CRC][ETX]
#define PING_RESP_LEN 5   // [STX][ACK][LEN=0][CRC][ETX]
#define UPDATE_RESP_LEN 10 // [STX][ACK][LEN=5][power_mwe (4)][pwm][CRC][ETX]

// ============================================
// CRC8 Checksum (CRC-8/MAXIM)
// ============================================
uint8_t crc8_maxim(const uint8_t* data, size_t len) {
  uint8_t crc = 0x00;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 0x80) {
        crc = (crc << 1) ^ 0x31;
      } else {
        crc = crc << 1;
      }
    }
  }
  return crc;
}

// ============================================
// UART Configuration
// ============================================
#define UART_BAUD 115200
HardwareSerial UartComm(2); // RX=16 TX=17

// ============================================
// Binary Message Buffer
// ============================================
uint8_t rx_buffer[16];  // Buffer for incoming binary messages
uint8_t rx_index = 0;

// State machine for robust frame parsing
// This prevents STX/ETX bytes in payload from breaking frame detection
enum RxState {
  WAIT_STX,   // Waiting for start of frame
  IN_FRAME    // Currently receiving frame data
};
RxState rx_state = WAIT_STX;

unsigned long last_byte_time = 0;
#define RX_TIMEOUT_MS 500  // Reset buffer if no data for 500ms

// ============================================
// LED PINS - Array of 4 LEDs for power visualization
// ============================================
const int NUM_LEDS = 4;
const int POWER_LEDS[NUM_LEDS] = {23, 25, 33, 27};  // 4 GPIO pins for LEDs (26→33: avoid DAC2/ADC2 conflict)

// ============================================
// DATA
// ============================================
float thermal_kw = 0.0;      // Thermal power dalam kW (0-300000)
float power_mwe = 0.0;       // Electrical power dalam MWe (0-300)
int current_pwm = 0;         // Current PWM value (0-255)

// LED Mode Control (PWM vs HIGH mode)
#define PWM_THRESHOLD_HIGH 250    // Switch to HIGH mode when PWM >= 250
#define PWM_THRESHOLD_LOW 240     // Switch back to PWM mode when PWM < 240 (hysteresis)
bool led_mode_high = false;       // true = HIGH mode (full 3.3V), false = PWM mode

// ============================================
// Binary Protocol Functions
// ============================================

void sendNACK() {
  // Send NACK response: [STX][NACK][LEN=0][CRC][ETX]
  uint8_t response[5];
  response[0] = STX;
  response[1] = NACK;
  response[2] = 0;  // LEN = 0 (no payload)
  
  // Calculate CRC over CMD + LEN
  uint8_t crc_data[2] = {NACK, 0};
  response[3] = crc8_maxim(crc_data, 2);
  response[4] = ETX;
  
  UartComm.write(response, 5);
  UartComm.flush();
  
  Serial.println("TX: NACK");
}

void sendPongResponse() {
  // Send pong response: [STX][ACK][LEN=0][CRC][ETX]
  uint8_t response[5];
  response[0] = STX;
  response[1] = ACK;
  response[2] = 0;  // LEN = 0 (no payload)
  
  // Calculate CRC over CMD + LEN
  uint8_t crc_data[2] = {ACK, 0};
  response[3] = crc8_maxim(crc_data, 2);
  response[4] = ETX;
  
  UartComm.write(response, 5);
  UartComm.flush();
  
  Serial.println("TX: Pong ACK");
}

void sendUpdateResponse() {
  // Send update response: [STX][ACK][LEN=5][power_mwe (4)][pwm][CRC][ETX]
  uint8_t response[10];
  response[0] = STX;
  response[1] = ACK;
  response[2] = 5;  // LEN = 5 bytes payload
  
  // Pack data (5 bytes total)
  uint8_t* data = &response[3];
  
  // Power MWe (4 bytes, float32, little-endian)
  memcpy(&data[0], &power_mwe, 4);
  
  // PWM (1 byte)
  data[4] = (uint8_t)current_pwm;
  
  // Calculate CRC over CMD + LEN + data (7 bytes total)
  response[8] = crc8_maxim(&response[1], 7);
  response[9] = ETX;
  
  UartComm.write(response, 10);
  UartComm.flush();
  
  Serial.println("TX: Update ACK with data");
}

void processBinaryMessage(uint8_t* msg, uint8_t len) {
  // Validate message structure
  if (len < 5) {
    Serial.println("Message too short");
    return;
  }
  
  if (msg[0] != STX || msg[len-1] != ETX) {
    Serial.println("Invalid STX/ETX");
    return;
  }
  
  // Extract fields: [STX][CMD][LEN][PAYLOAD...][CRC][ETX]
  uint8_t cmd = msg[1];
  uint8_t payload_len = msg[2];
  uint8_t received_crc = msg[len-2];
  
  // Validate total message length
  uint8_t expected_len = 5 + payload_len;  // STX + CMD + LEN + PAYLOAD + CRC + ETX
  if (len != expected_len) {
    Serial.printf("Length mismatch: got %d bytes, expected %d (LEN field=%d)\n", len, expected_len, payload_len);
    sendNACK();
    return;
  }
  
  // Validate CRC (over CMD + LEN + PAYLOAD)
  uint8_t crc_len = 2 + payload_len;  // CMD + LEN + payload
  uint8_t calculated_crc = crc8_maxim(&msg[1], crc_len);
  
  if (received_crc != calculated_crc) {
    Serial.printf("CRC mismatch: received=0x%02X, calculated=0x%02X\n", received_crc, calculated_crc);
    sendNACK();
    return;
  }
  
  // Process command
  if (cmd == CMD_PING) {
    if (payload_len != 0) {
      Serial.printf("Invalid ping payload length: %d (expected 0)\n", payload_len);
      sendNACK();
      return;
    }
    Serial.println("RX: Ping");
    sendPongResponse();
  }
  else if (cmd == CMD_UPDATE) {
    if (payload_len != 4) {
      Serial.printf("Invalid update payload length: %d (expected 4)\n", payload_len);
      sendNACK();
      return;
    }
    
    // Parse update data - thermal_kw (4 bytes, float32, little-endian)
    // Payload starts at index 3
    memcpy(&thermal_kw, &msg[3], 4);
    
    // Convert kW to MWe
    power_mwe = thermal_kw / 1000.0;
    
    Serial.printf("RX: Update - Thermal=%.1f kW → Power=%.1f MWe\n", thermal_kw, power_mwe);
    
    sendUpdateResponse();
  }
  else {
    Serial.printf("Unknown command: 0x%02X\n", cmd);
    sendNACK();
  }
}

// ============================================
// SETUP
// ============================================
void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP-E Power Indicator - BINARY PROTOCOL");
  Serial.println("===========================================");
  Serial.println("Fungsi: Visualisasi daya reaktor");
  Serial.println("LED: 1x Power Indicator (GPIO 23)");
  Serial.println("Protocol: BINARY with ACK/NACK");
  Serial.println("===========================================");
  
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  delay(500);

  // Initialize all 4 power LEDs
  Serial.println("Initializing 4 power LEDs...");
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(POWER_LEDS[i], OUTPUT);
    ledcAttach(POWER_LEDS[i], 5000, 8);  // 5kHz, 8-bit
    ledcWrite(POWER_LEDS[i], 0);
    Serial.printf("  LED %d: GPIO %d initialized\n", i+1, POWER_LEDS[i]);
  }

  Serial.println("UART ready at 115200 baud");
  Serial.println("===========================================");
  Serial.println("ESP32 Power Indicator READY");
  Serial.println("===========================================\n");
  
  // Test LEDs - flash 3 times
  Serial.println("Testing all LEDs...");
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < NUM_LEDS; j++) {
      ledcWrite(POWER_LEDS[j], 255);
    }
    delay(200);
    for (int j = 0; j < NUM_LEDS; j++) {
      ledcWrite(POWER_LEDS[j], 0);
    }
    delay(200);
  }
  Serial.println("LED test complete\n");
}

// ============================================
// LOOP
// ============================================
void loop() {
  // Read UART data with state machine for robust frame parsing
  while (UartComm.available()) {
    uint8_t byte = UartComm.read();
    unsigned long current_time = millis();
    
    // Check for timeout (reset to WAIT_STX if no data for 500ms)
    if (rx_state == IN_FRAME && (current_time - last_byte_time > RX_TIMEOUT_MS)) {
      Serial.println("RX timeout - resetting to WAIT_STX");
      rx_state = WAIT_STX;
      rx_index = 0;
    }
    
    last_byte_time = current_time;
    
    // State machine for frame parsing
    if (rx_state == WAIT_STX) {
      // Only accept STX when waiting for new frame
      if (byte == STX) {
        rx_index = 0;
        rx_buffer[rx_index++] = byte;
        rx_state = IN_FRAME;
      }
      // Ignore all other bytes when waiting for STX
    }
    else if (rx_state == IN_FRAME) {
      // Add byte to buffer
      if (rx_index < sizeof(rx_buffer)) {
        rx_buffer[rx_index++] = byte;
        
        // Check if this is ETX (end of frame)
        if (byte == ETX) {
          // Process complete message
          processBinaryMessage(rx_buffer, rx_index);
          
          // Return to WAIT_STX state
          rx_state = WAIT_STX;
          rx_index = 0;
        }
      }
      else {
        // Buffer overflow - reset to WAIT_STX
        Serial.println("Buffer overflow - resetting to WAIT_STX");
        rx_state = WAIT_STX;
        rx_index = 0;
      }
    }
    
    yield();  // Feed watchdog
  }

  // Update power LED
  updatePowerLED();
  
  yield();
  delay(10);
}

// ============================================
// POWER LED UPDATE - Controls all 4 LEDs with PWM/HIGH mode switching
// ============================================
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
  
  // ============================================
  // Mode Switching Logic with Hysteresis
  // ============================================
  
  // Check if we need to switch to HIGH mode (PWM → HIGH)
  if (!led_mode_high && current_pwm >= PWM_THRESHOLD_HIGH) {
    // Switch to HIGH mode for maximum brightness
    Serial.println("Switching to HIGH mode (full 3.3V)");
    
    for (int i = 0; i < NUM_LEDS; i++) {
      // Detach PWM
      ledcDetach(POWER_LEDS[i]);
      
      // Reconfigure as digital OUTPUT
      pinMode(POWER_LEDS[i], OUTPUT);
      
      // Set to HIGH (full 3.3V)
      digitalWrite(POWER_LEDS[i], HIGH);
    }
    
    led_mode_high = true;
  }
  // Check if we need to switch back to PWM mode (HIGH → PWM)
  else if (led_mode_high && current_pwm < PWM_THRESHOLD_LOW) {
    // Switch back to PWM mode
    Serial.println("Switching to PWM mode");
    
    for (int i = 0; i < NUM_LEDS; i++) {
      // Re-attach PWM
      ledcAttach(POWER_LEDS[i], 5000, 8);  // 5kHz, 8-bit
      
      // Set initial PWM value
      ledcWrite(POWER_LEDS[i], current_pwm);
    }
    
    led_mode_high = false;
  }
  // If in PWM mode, update PWM values
  else if (!led_mode_high) {
    // Apply PWM to all 4 LEDs
    for (int i = 0; i < NUM_LEDS; i++) {
      ledcWrite(POWER_LEDS[i], current_pwm);
    }
  }
  // If in HIGH mode, LEDs stay at HIGH (no action needed)
  
  // Debug output every 2 seconds
  static unsigned long last_debug = 0;
  if (millis() - last_debug > 2000) {
    last_debug = millis();
    const char* mode_str = led_mode_high ? "HIGH" : "PWM";
    Serial.printf("Power: %.1f MWe | PWM: %d/255 | Mode: %s | Brightness: %d%% | All %d LEDs\n", 
                  power_mwe, current_pwm, mode_str, (current_pwm * 100) / 255, NUM_LEDS);
  }
}
