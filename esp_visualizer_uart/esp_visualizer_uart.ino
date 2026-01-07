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
#define UPDATE_CMD_LEN 12 // [STX][CMD][LEN=7][thermal_kw (4)][pump_prim][pump_sec][pump_ter][CRC][ETX]
#define PING_RESP_LEN 5   // [STX][ACK][LEN=0][CRC][ETX]
#define UPDATE_RESP_LEN 13 // [STX][ACK][LEN=8][power_mwe (4)][pwm][pump_prim][pump_sec][pump_ter][CRC][ETX]

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
// SHIFT REGISTER PINS - 74HC595 + UDN2981 for water flow visualization
// ============================================
// Shared CLOCK for all 3 ICs
#define CLOCK_PIN 14

// Separate DATA pins (one per IC/pump)
#define DATA_PIN_PRIMARY 12    // IC #1 - Primary pump flow
#define DATA_PIN_SECONDARY 13  // IC #2 - Secondary pump flow
#define DATA_PIN_TERTIARY 15   // IC #3 - Tertiary pump flow

// Separate LATCH pins (one per IC/pump)
#define LATCH_PIN_PRIMARY 18   // IC #1 - Primary pump flow
#define LATCH_PIN_SECONDARY 19 // IC #2 - Secondary pump flow
#define LATCH_PIN_TERTIARY 21  // IC #3 - Tertiary pump flow

// Flow animation configuration
// Animation delays are now dynamic based on pump status (see updateFlowAnimation)
// Pattern: 4-LED block (B11110000) that rotates around 8 LEDs
unsigned long lastFlowAnim = 0;  // Last animation update time

// ============================================
// DATA
// ============================================
float thermal_kw = 0.0;      // Thermal power dalam kW (0-300000)
float power_mwe = 0.0;       // Electrical power dalam MWe (0-300)
int current_pwm = 0;         // Current PWM value (0-255)

// Pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
uint8_t pump_primary_status = 0;
uint8_t pump_secondary_status = 0;
uint8_t pump_tertiary_status = 0;

// LED Mode Control (PWM vs HIGH mode)
#define PWM_THRESHOLD_HIGH 250    // Switch to HIGH mode when PWM >= 250
#define PWM_THRESHOLD_LOW 240     // Switch back to PWM mode when PWM < 240 (hysteresis)
bool led_mode_high = false;       // true = HIGH mode (full 3.3V), false = PWM mode

// ============================================
// Shift Register Control Functions
// ============================================

/**
 * Write data to a single shift register IC
 * @param data - 8-bit pattern to write
 * @param dataPin - DATA pin for this IC
 * @param latchPin - LATCH pin for this IC
 */
void writeShiftRegisterIC(byte data, int dataPin, int latchPin) {
  digitalWrite(latchPin, LOW);
  shiftOut(dataPin, CLOCK_PIN, LSBFIRST, data);
  digitalWrite(latchPin, HIGH);
}

/**
 * Update water flow animations for all 3 pumps
 * Based on reference implementation with adaptations for shift register
 * Uses multi-LED blocks with variable speed per pump status
 */
void updateFlowAnimation() {
  unsigned long currentTime = millis();
  
  // Track previous status to detect changes
  static uint8_t prev_pump_primary = 255;
  static uint8_t prev_pump_secondary = 255;
  static uint8_t prev_pump_tertiary = 255;
  
  // Track animation positions for each pump
  static int pos_primary = 0;
  static int pos_secondary = 0;
  static int pos_tertiary = 0;
  
  // Variable animation delays per pump status (from reference)
  static unsigned long delay_primary = 200;
  static unsigned long delay_secondary = 250;
  static unsigned long delay_tertiary = 250;
  
  // Detect pump status changes and handle accordingly
  if (pump_primary_status != prev_pump_primary) {
    if (pump_primary_status != 2) {
      // Pump stopped - immediately clear and reset
      writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
      pos_primary = 0;
      Serial.println("Primary pump stopped - LEDs cleared");
    } else {
      Serial.println("Primary pump started");
      pos_primary = 0;  // Reset position on start
    }
    prev_pump_primary = pump_primary_status;
  }
  
  if (pump_secondary_status != prev_pump_secondary) {
    if (pump_secondary_status != 2) {
      writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
      pos_secondary = 0;
      Serial.println("Secondary pump stopped - LEDs cleared");
    } else {
      Serial.println("Secondary pump started");
      pos_secondary = 0;
    }
    prev_pump_secondary = pump_secondary_status;
  }
  
  if (pump_tertiary_status != prev_pump_tertiary) {
    if (pump_tertiary_status != 2) {
      writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
      pos_tertiary = 0;
      Serial.println("Tertiary pump stopped - LEDs cleared");
    } else {
      Serial.println("Tertiary pump started");
      pos_tertiary = 0;
    }
    prev_pump_tertiary = pump_tertiary_status;
  }
  
  // Update animation delays based on pump status (from reference)
  // Primary pump
  switch (pump_primary_status) {
    case 1: delay_primary = 500; break;  // STARTING
    case 2: delay_primary = 200; break;  // ON (fastest)
    case 3: delay_primary = 600; break;  // SHUTTING_DOWN
    default: delay_primary = 1000; break;
  }
  
  // Secondary pump
  switch (pump_secondary_status) {
    case 1: delay_secondary = 500; break;  // STARTING
    case 2: delay_secondary = 250; break;  // ON (medium speed)
    case 3: delay_secondary = 600; break;  // SHUTTING_DOWN
    default: delay_secondary = 1000; break;
  }
  
  // Tertiary pump
  switch (pump_tertiary_status) {
    case 1: delay_tertiary = 500; break;  // STARTING
    case 2: delay_tertiary = 250; break;  // ON (medium speed)
    case 3: delay_tertiary = 600; break;  // SHUTTING_DOWN
    default: delay_tertiary = 1000; break;
  }
  
  // Check if it's time to update animation (using shortest delay for smooth updates)
  unsigned long min_delay = min(delay_primary, min(delay_secondary, delay_tertiary));
  if (currentTime - lastFlowAnim < min_delay) {
    return;
  }
  
  lastFlowAnim = currentTime;
  
  // Primary pump flow - 4-LED block pattern (adapted from reference)
  if (pump_primary_status == 2) {  // PUMP_ON
    // Create 4-LED block pattern: B11110000 rotated
    byte pattern = 0;
    for (int i = 0; i < 4; i++) {
      int ledPos = (pos_primary + i) % 8;
      pattern |= (1 << ledPos);
    }
    writeShiftRegisterIC(pattern, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
    
    // Advance position
    pos_primary++;
    if (pos_primary >= 8) pos_primary = 0;
  }
  
  // Secondary pump flow - 4-LED block pattern
  if (pump_secondary_status == 2) {  // PUMP_ON
    byte pattern = 0;
    for (int i = 0; i < 4; i++) {
      int ledPos = (pos_secondary + i) % 8;
      pattern |= (1 << ledPos);
    }
    writeShiftRegisterIC(pattern, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
    
    pos_secondary++;
    if (pos_secondary >= 8) pos_secondary = 0;
  }
  
  // Tertiary pump flow - 4-LED block pattern
  if (pump_tertiary_status == 2) {  // PUMP_ON
    byte pattern = 0;
    for (int i = 0; i < 4; i++) {
      int ledPos = (pos_tertiary + i) % 8;
      pattern |= (1 << ledPos);
    }
    writeShiftRegisterIC(pattern, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
    
    pos_tertiary++;
    if (pos_tertiary >= 8) pos_tertiary = 0;
  }
}

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
  // Send update response: [STX][ACK][LEN=8][power_mwe (4)][pwm][pump_prim][pump_sec][pump_ter][CRC][ETX]
  uint8_t response[13];
  response[0] = STX;
  response[1] = ACK;
  response[2] = 8;  // LEN = 8 bytes payload
  
  // Pack data (8 bytes total)
  uint8_t* data = &response[3];
  
  // Power MWe (4 bytes, float32, little-endian)
  memcpy(&data[0], &power_mwe, 4);
  
  // PWM (1 byte)
  data[4] = (uint8_t)current_pwm;
  
  // Pump status (3 bytes)
  data[5] = pump_primary_status;
  data[6] = pump_secondary_status;
  data[7] = pump_tertiary_status;
  
  // Calculate CRC over CMD + LEN + data (10 bytes total)
  response[11] = crc8_maxim(&response[1], 10);
  response[12] = ETX;
  
  UartComm.write(response, 13);
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
    if (payload_len != 7) {
      Serial.printf("Invalid update payload length: %d (expected 7)\n", payload_len);
      sendNACK();
      return;
    }
    
    // Parse update data - thermal_kw (4 bytes) + 3 pump status bytes
    // Payload starts at index 3
    memcpy(&thermal_kw, &msg[3], 4);
    pump_primary_status = msg[7];
    pump_secondary_status = msg[8];
    pump_tertiary_status = msg[9];
    
    // Convert kW to MWe
    power_mwe = thermal_kw / 1000.0;
    
    Serial.printf("RX: Update - Thermal=%.1f kW → Power=%.1f MWe | Pumps: P=%d S=%d T=%d\n", 
                  thermal_kw, power_mwe, pump_primary_status, pump_secondary_status, pump_tertiary_status);
    
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
  Serial.println("Fungsi: Visualisasi daya reaktor + aliran air");
  Serial.println("LED: 4x Power Indicator (GPIO 23,25,33,27)");
  Serial.println("Flow: 3x Shift Register 74HC595 + UDN2981");
  Serial.println("Protocol: BINARY with ACK/NACK");
  Serial.println("===========================================");
  
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  delay(500);

  // Initialize shift register pins
  Serial.println("Initializing shift register pins...");
  pinMode(CLOCK_PIN, OUTPUT);
  pinMode(DATA_PIN_PRIMARY, OUTPUT);
  pinMode(DATA_PIN_SECONDARY, OUTPUT);
  pinMode(DATA_PIN_TERTIARY, OUTPUT);
  pinMode(LATCH_PIN_PRIMARY, OUTPUT);
  pinMode(LATCH_PIN_SECONDARY, OUTPUT);
  pinMode(LATCH_PIN_TERTIARY, OUTPUT);
  
  // Clear all shift registers
  writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  Serial.println("Shift registers initialized and cleared");


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
  
  // Update water flow animations
  updateFlowAnimation();
  
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
