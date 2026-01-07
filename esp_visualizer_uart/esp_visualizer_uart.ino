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
// Animation delays are now dynamic per pump (see updateFlowAnimation)
// Each pump has independent timer - no global timer needed
// Pattern: 2 LEDs (main + tail) shifting for smooth flow effect
// Animation only active when pump status = 2 (ON) or 3 (SHUTTING_DOWN)

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
 * 
 * 74HC595 Protocol:
 * 1. LATCH (RCLK) LOW - prepare to receive data
 * 2. Shift 8 bits via DATA + CLOCK (SRCLK) - shiftOut() handles this
 * 3. LATCH (RCLK) HIGH - transfer shift register to output register
 * 4. Data appears on Q0-Q7, UDN2981 sources current to LEDs
 * 
 * CRITICAL: Uses MSBFIRST to match physical LED wiring
 * Bit 7 (MSB) = Q7 (LED 8), Bit 0 (LSB) = Q0 (LED 1)
 */
void writeShiftRegisterIC(byte data, int dataPin, int latchPin) {
  // Step 1: LATCH LOW - disable output update
  digitalWrite(latchPin, LOW);
  delayMicroseconds(1);  // Setup time
  
  // Step 2: Shift 8 bits (shiftOut generates clock pulses automatically)
  shiftOut(dataPin, CLOCK_PIN, MSBFIRST, data);
  
  // Step 3: LATCH HIGH - transfer to output register
  delayMicroseconds(1);  // Hold time
  digitalWrite(latchPin, HIGH);
  delayMicroseconds(1);  // Propagation delay
}

/**
 * Update water flow animations for all 3 pumps
 * 
 * CRITICAL IMPROVEMENTS:
 * 1. Independent timer per pump (no global timer blocking)
 * 2. Continuous LED refresh (not just on status change)
 * 3. Non-blocking design (animation runs on millis(), not UART events)
 * 4. Explicit LED clear when pump is OFF
 * 
 * Based on reference implementation adapted for shift register
 */
void updateFlowAnimation() {
  unsigned long currentTime = millis();
  
  // ========================================
  // PRIMARY PUMP - Independent timer and position
  // ========================================
  static unsigned long lastUpdate_Primary = 0;
  static int pos_Primary = 0;
  static unsigned long delay_Primary = 200;
  static uint8_t lastStatus_Primary = 255;
  
  // Detect status change for primary pump
  if (pump_primary_status != lastStatus_Primary) {
    Serial.printf("Primary pump status changed: %d → %d\n", lastStatus_Primary, pump_primary_status);
    lastStatus_Primary = pump_primary_status;
    pos_Primary = 0;  // Reset position on status change
  }
  
  // Update delay based on current status
  switch (pump_primary_status) {
    case 0:  // OFF
      // Explicitly clear LEDs when OFF
      writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
      break;
      
    case 1:  // STARTING - no flow animation yet
      writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
      break;
      
    case 2:  // ON - show flow animation
      delay_Primary = 1000;  // 1 second per step for clear visibility
      
      // Animate if enough time has passed
      if (currentTime - lastUpdate_Primary >= delay_Primary) {
        lastUpdate_Primary = currentTime;
        
        // Generate 2 ADJACENT LEDs pattern that shifts right
        // Pattern: 11000000 → 01100000 → 00110000 → ... → 10000001 → 11000000
        byte pattern = 0;
        
        // Set 2 adjacent bits based on position
        pattern |= (1 << (7 - pos_Primary));      // First LED (MSB side)
        pattern |= (1 << (7 - pos_Primary - 1));  // Second LED (adjacent)
        
        // Special case: when pos=7, wrap around (10000001)
        if (pos_Primary == 7) {
          pattern = 0b10000001;  // bit 7 and bit 0
        }
        
        // Write complete pattern (only 2 bits set)
        writeShiftRegisterIC(pattern, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
        
        // Advance position
        pos_Primary++;
        if (pos_Primary >= 8) pos_Primary = 0;
      }
      break;
      
    case 3:  // SHUTTING_DOWN - slow flow
      delay_Primary = 2000;  // Very slow (2 seconds)
      
      if (currentTime - lastUpdate_Primary >= delay_Primary) {
        lastUpdate_Primary = currentTime;
        
        // Same 2 adjacent LEDs pattern
        byte pattern = 0;
        pattern |= (1 << (7 - pos_Primary));
        pattern |= (1 << (7 - pos_Primary - 1));
        
        if (pos_Primary == 7) {
          pattern = 0b10000001;
        }
        
        writeShiftRegisterIC(pattern, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
        
        // Advance position
        pos_Primary++;
        if (pos_Primary >= 8) pos_Primary = 0;
      }
      break;
  }
  
  // ========================================
  // SECONDARY PUMP - Independent timer and position
  // ========================================
  static unsigned long lastUpdate_Secondary = 0;
  static int pos_Secondary = 0;
  static unsigned long delay_Secondary = 250;
  static uint8_t lastStatus_Secondary = 255;
  
  // Detect status change for secondary pump
  if (pump_secondary_status != lastStatus_Secondary) {
    Serial.printf("Secondary pump status changed: %d → %d\n", lastStatus_Secondary, pump_secondary_status);
    lastStatus_Secondary = pump_secondary_status;
    pos_Secondary = 0;
  }
  
  // Update delay and animate
  switch (pump_secondary_status) {
    case 0:  // OFF
      writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
      break;
      
    case 1:  // STARTING - no flow
      writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
      break;
      
    case 2:  // ON - show flow
      delay_Secondary = 1000;  // 1 second
      
      if (currentTime - lastUpdate_Secondary >= delay_Secondary) {
        lastUpdate_Secondary = currentTime;
        
        // 2 adjacent LEDs pattern
        byte pattern = 0;
        pattern |= (1 << (7 - pos_Secondary));
        pattern |= (1 << (7 - pos_Secondary - 1));
        
        if (pos_Secondary == 7) {
          pattern = 0b10000001;
        }
        
        writeShiftRegisterIC(pattern, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
        
        pos_Secondary++;
        if (pos_Secondary >= 8) pos_Secondary = 0;
      }
      break;
      
    case 3:  // SHUTTING_DOWN
      delay_Secondary = 2000;
      
      if (currentTime - lastUpdate_Secondary >= delay_Secondary) {
        lastUpdate_Secondary = currentTime;
        
        byte pattern = 0;
        pattern |= (1 << (7 - pos_Secondary));
        pattern |= (1 << (7 - pos_Secondary - 1));
        
        if (pos_Secondary == 7) {
          pattern = 0b10000001;
        }
        
        writeShiftRegisterIC(pattern, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
        
        pos_Secondary++;
        if (pos_Secondary >= 8) pos_Secondary = 0;
      }
      break;
  }
  
  // ========================================
  // TERTIARY PUMP - Independent timer and position
  // ========================================
  static unsigned long lastUpdate_Tertiary = 0;
  static int pos_Tertiary = 0;
  static unsigned long delay_Tertiary = 250;
  static uint8_t lastStatus_Tertiary = 255;
  
  // Detect status change for tertiary pump
  if (pump_tertiary_status != lastStatus_Tertiary) {
    Serial.printf("Tertiary pump status changed: %d → %d\n", lastStatus_Tertiary, pump_tertiary_status);
    lastStatus_Tertiary = pump_tertiary_status;
    pos_Tertiary = 0;
  }
  
  // Update delay and animate
  switch (pump_tertiary_status) {
    case 0:  // OFF
      writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
      break;
      
    case 1:  // STARTING - no flow
      writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
      break;
      
    case 2:  // ON - show flow
      delay_Tertiary = 1000;  // 1 second
      
      if (currentTime - lastUpdate_Tertiary >= delay_Tertiary) {
        lastUpdate_Tertiary = currentTime;
        
        // 2 adjacent LEDs pattern
        byte pattern = 0;
        pattern |= (1 << (7 - pos_Tertiary));
        pattern |= (1 << (7 - pos_Tertiary - 1));
        
        if (pos_Tertiary == 7) {
          pattern = 0b10000001;
        }
        
        writeShiftRegisterIC(pattern, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
        
        pos_Tertiary++;
        if (pos_Tertiary >= 8) pos_Tertiary = 0;
      }
      break;
      
    case 3:  // SHUTTING_DOWN
      delay_Tertiary = 2000;
      
      if (currentTime - lastUpdate_Tertiary >= delay_Tertiary) {
        lastUpdate_Tertiary = currentTime;
        
        byte pattern = 0;
        pattern |= (1 << (7 - pos_Tertiary));
        pattern |= (1 << (7 - pos_Tertiary - 1));
        
        if (pos_Tertiary == 7) {
          pattern = 0b10000001;
        }
        
        writeShiftRegisterIC(pattern, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
        
        pos_Tertiary++;
        if (pos_Tertiary >= 8) pos_Tertiary = 0;
      }
      break;
  }
}

// ============================================
// Hardware Test Patterns
// ============================================

/**
 * Test all shift register outputs with alternating patterns
 * Call this from setup() to verify hardware before normal operation
 * 
 * Tests:
 * - 0xAA (10101010) - Alternating bits
 * - 0x55 (01010101) - Inverted alternating bits
 * - 0xFF (11111111) - All LEDs on
 * - 0x00 (00000000) - All LEDs off
 */
void testShiftRegisterHardware() {
  Serial.println("\n========================================");
  Serial.println("HARDWARE TEST: Shift Register Validation");
  Serial.println("========================================");
  
  byte testPatterns[] = {0xAA, 0x55, 0xFF, 0x00};
  const char* patternNames[] = {"0xAA (10101010)", "0x55 (01010101)", "0xFF (all ON)", "0x00 (all OFF)"};
  
  for (int test = 0; test < 4; test++) {
    Serial.printf("\nTest %d: Pattern %s\n", test + 1, patternNames[test]);
    Serial.println("Applying to all 3 shift registers...");
    
    // Apply same pattern to all 3 ICs
    writeShiftRegisterIC(testPatterns[test], DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
    writeShiftRegisterIC(testPatterns[test], DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
    writeShiftRegisterIC(testPatterns[test], DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
    
    Serial.println("✓ Pattern applied - verify LEDs visually");
    delay(2000);  // 2 seconds to observe
  }
  
  // Clear all at end
  writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  
  Serial.println("\n✅ Hardware test complete - all ICs cleared");
  Serial.println("If all patterns displayed correctly, hardware is OK");
  Serial.println("========================================\n");
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
  
  // CLOCK - shared by all 3 ICs
  pinMode(CLOCK_PIN, OUTPUT);
  digitalWrite(CLOCK_PIN, LOW);
  
  // PRIMARY circuit
  pinMode(DATA_PIN_PRIMARY, OUTPUT);
  pinMode(LATCH_PIN_PRIMARY, OUTPUT);
  digitalWrite(DATA_PIN_PRIMARY, LOW);
  digitalWrite(LATCH_PIN_PRIMARY, LOW);
  
  // SECONDARY circuit
  pinMode(DATA_PIN_SECONDARY, OUTPUT);
  pinMode(LATCH_PIN_SECONDARY, OUTPUT);
  digitalWrite(DATA_PIN_SECONDARY, LOW);
  digitalWrite(LATCH_PIN_SECONDARY, LOW);
  
  // TERTIARY circuit
  pinMode(DATA_PIN_TERTIARY, OUTPUT);
  pinMode(LATCH_PIN_TERTIARY, OUTPUT);
  digitalWrite(DATA_PIN_TERTIARY, LOW);
  digitalWrite(LATCH_PIN_TERTIARY, LOW);
  
  delay(10);  // Let pins stabilize
  
  // Clear all shift registers
  writeShiftRegisterIC(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  Serial.println("Shift registers initialized and cleared");
  
  // OPTIONAL: Hardware test mode - uncomment to test all Q0-Q7 pins
  // Recommended for first-time setup or troubleshooting
  // testShiftRegisterHardware();  // Uncomment this line to run hardware test


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