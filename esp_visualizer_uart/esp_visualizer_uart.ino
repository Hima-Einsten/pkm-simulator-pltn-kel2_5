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
#include <SPI.h>

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
// PUMP STRUCT - Must be declared before use
// ============================================
struct Pump {
  uint8_t status;           // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
  int latchPin;             // LATCH pin for this IC
  unsigned long lastUpdate; // Last animation update time
  int pos;                  // Current animation position (0-7)
  uint8_t lastStatus;       // For detecting status changes
};

// ============================================
// DEBUG Configuration
// ============================================
#define DEBUG_SHIFT_REGISTER true  // Set to false to disable debug output

// Helper function to print binary representation
void printBinary(byte value) {
  for (int i = 7; i >= 0; i--) {
    Serial.print((value >> i) & 1);
  }
}

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
// Using HARDWARE SPI for faster communication (vs software shiftOut)
// ESP32 VSPI pins: MOSI=23, MISO=19, SCK=18, SS=5
// We use HSPI instead: MOSI=13, MISO=12, SCK=14, SS=15

#define SPI_CLOCK_PIN 14       // SCK - Shared clock for all 3 ICs (SRCLK)
#define SPI_MOSI_PIN 13        // MOSI - Shared data line for all 3 ICs

// Separate LATCH pins (one per IC/pump) - act as chip select
#define LATCH_PIN_PRIMARY 18   // IC #1 - Primary pump flow (RCLK)
#define LATCH_PIN_SECONDARY 19 // IC #2 - Secondary pump flow (RCLK)
#define LATCH_PIN_TERTIARY 21  // IC #3 - Tertiary pump flow (RCLK)

// SPI Configuration
SPIClass * hspi = NULL;  // Hardware SPI instance
#define SPI_FREQUENCY 8000000  // 8 MHz (74HC595 max ~25 MHz, safe value)

// Flow animation configuration
// Pattern: 2 LEDs (main + tail) shifting for smooth flow effect
// Animation only active when pump status = 2 (ON) or 3 (SHUTTING_DOWN)

// ============================================
// DATA
// ============================================
float thermal_kw = 0.0;      // Thermal power dalam kW (0-300000)
float power_mwe = 0.0;       // Electrical power dalam MWe (0-300)
int current_pwm = 0;         // Current PWM value (0-255)

// Pump instances - consolidated state
Pump pump_primary = {0, LATCH_PIN_PRIMARY, 0, 0, 255};
Pump pump_secondary = {0, LATCH_PIN_SECONDARY, 0, 0, 255};
Pump pump_tertiary = {0, LATCH_PIN_TERTIARY, 0, 0, 255};

// LED Mode Control (PWM vs HIGH mode)
#define PWM_THRESHOLD_HIGH 250    // Switch to HIGH mode when PWM >= 250
#define PWM_THRESHOLD_LOW 240     // Switch back to PWM mode when PWM < 240 (hysteresis)
bool led_mode_high = false;       // true = HIGH mode (full 3.3V), false = PWM mode

// ============================================
// Shift Register Control Functions
// ============================================

/**
 * Write data to a single shift register IC using HARDWARE SPI
 * @param data - 8-bit pattern to write
 * @param latchPin - LATCH pin for this IC
 * 
 * 74HC595 Protocol with SPI:
 * 1. LATCH (RCLK) LOW - prepare to receive data
 * 2. SPI.transfer() - shifts 8 bits via MOSI + SCK (much faster than shiftOut)
 * 3. LATCH (RCLK) HIGH - transfer shift register to output register
 * 4. Data appears on Q0-Q7, UDN2981 sources current to LEDs
 * 
 * PERFORMANCE: SPI hardware is ~3x faster than software shiftOut()
 * CRITICAL: Uses MSBFIRST to match physical LED wiring
 * Bit 7 (MSB) = Q7 (LED 8), Bit 0 (LSB) = Q0 (LED 1)
 * 
 * TIMING FIX: Added delays to prevent glitches and ensure stable operation
 */
void writeShiftRegisterIC(byte data, int latchPin) {
  // Step 1: LATCH LOW - disable output update
  digitalWrite(latchPin, LOW);
  delayMicroseconds(1);  // Setup time - ensure LATCH is stable LOW
  
  // Step 2: Shift 8 bits via hardware SPI (FAST!)
  hspi->transfer(data);  // SPI handles MSBFIRST by default
  
  // CRITICAL: Wait for SPI transfer to complete
  delayMicroseconds(2);  // Hold time - ensure all 8 bits are fully shifted
  
  // Step 3: LATCH HIGH - transfer shift register to output register
  digitalWrite(latchPin, HIGH);
  delayMicroseconds(2);  // Pulse width - ensure latch captures data
  
  // Keep LATCH HIGH - 74HC595 output register is level-triggered
  // Data will remain stable on outputs as long as LATCH is HIGH;
  
  // DEBUG: Print what was sent
  if (DEBUG_SHIFT_REGISTER) {
    Serial.print("[SPI TX] Latch=");
    Serial.print(latchPin);
    Serial.print(" | Data=0x");
    Serial.print(data, HEX);
    Serial.print(" | Binary=");
    printBinary(data);
    Serial.print(" | LEDs: ");
    // Show which LEDs should be ON (bit 7=LED8, bit 0=LED1)
    for (int i = 7; i >= 0; i--) {
      if ((data >> i) & 1) {
        Serial.print(8-i);
        Serial.print(" ");
      }
    }
    Serial.println();
  }
}

/**
 * Clear all shift registers - turn off all LEDs
 * Call this during initialization and when all pumps are OFF
 */
void clearAllShiftRegisters() {
  writeShiftRegisterIC(0x00, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_TERTIARY);
}

// ============================================
// FLOW ANIMATION PATTERNS
// ============================================
/**
 * Flow animation pattern array - 8 steps showing water flow
 * Each byte represents LED states on 74HC595 outputs Q0-Q7
 * 
 * Pattern: 2 adjacent LEDs moving through the pipe
 * Bit 7 (MSB) = Q7 (LED 8), Bit 0 (LSB) = Q0 (LED 1)
 * 
 * Customize this array to change animation style:
 * - Current: 2 LEDs (main + tail) for smooth flow effect
 * - Alternative: Single LED, 3 LEDs, or custom patterns
 */
const byte FLOW_PATTERN[8] = {
  0b11000000,  // Step 0: LEDs 8-7
  0b01100000,  // Step 1: LEDs 7-6
  0b00110000,  // Step 2: LEDs 6-5
  0b00011000,  // Step 3: LEDs 5-4
  0b00001100,  // Step 4: LEDs 4-3
  0b00000110,  // Step 5: LEDs 3-2
  0b00000011,  // Step 6: LEDs 2-1
  0b10000001   // Step 7: LEDs 8-1 (wrap around)
};

/**
 * Update single pump flow animation
 * @param p - Reference to Pump struct
 * @param now - Current time from millis()
 * 
 * REFACTORED: Uses predefined pattern array for clearer animation control
 * Uses struct-based approach for cleaner, more maintainable code
 */
void updatePumpFlow(Pump *p, unsigned long now) {
  // Detect status change
  if (p->status != p->lastStatus) {
    Serial.printf("\n=== PUMP STATUS CHANGE (Latch=%d) ===\n", p->latchPin);
    Serial.printf("Status: %d -> %d | ", p->lastStatus, p->status);
    
    // Print status name
    const char* statusNames[] = {"OFF", "STARTING", "ON", "SHUTTING_DOWN"};
    if (p->status <= 3) {
      Serial.printf("(%s)\n", statusNames[p->status]);
    } else {
      Serial.println("(UNKNOWN)");
    }
    
    p->lastStatus = p->status;
    p->pos = 0;  // Reset position on status change
    Serial.println("Position reset to 0\n");
  }
  
  // Determine animation delay based on status
  unsigned long delay_ms = 0;
  
  switch (p->status) {
    case 0:  // OFF - FORCE clear LEDs (ensure all outputs are LOW)
      if (p->pos != 0 || p->lastUpdate == 0) {
        writeShiftRegisterIC(0x00, p->latchPin);
        p->pos = 0;
        p->lastUpdate = now;
      }
      return;
      
    case 1:  // STARTING - no flow yet, keep LEDs clear
      writeShiftRegisterIC(0x00, p->latchPin);
      p->pos = 0;
      return;
      
    case 2:  // ON - normal flow
      delay_ms = 500;  // 500ms per step (4 seconds per full cycle)
      break;
      
    case 3:  // SHUTTING_DOWN - slow flow
      delay_ms = 1000;  // 1 second per step (8 seconds per full cycle)
      break;
      
    default:
      return;
  }
  
  // Animate if enough time has passed
  if (now - p->lastUpdate >= delay_ms) {
    p->lastUpdate = now;
    
    // Get pattern from array (much clearer than bit shifting!)
    byte pattern = FLOW_PATTERN[p->pos];
    
    // DEBUG: Print animation step
    if (DEBUG_SHIFT_REGISTER && p->status >= 2) {
      Serial.printf("[ANIM] Latch=%d | Pos=%d/7 | Pattern=0x%02X | ", 
                    p->latchPin, p->pos, pattern);
      printBinary(pattern);
      Serial.printf(" | Delay=%lums\n", delay_ms);
    }
    
    // Write pattern to shift register
    writeShiftRegisterIC(pattern, p->latchPin);
    
    // Advance to next position (0-7, then wrap to 0)
    p->pos++;
    if (p->pos >= 8) {
      p->pos = 0;
      if (DEBUG_SHIFT_REGISTER && p->status >= 2) {
        Serial.println("[ANIM] Cycle complete - wrapping to position 0\n");
      }
    }
  }
}

/**
 * Update water flow animations for all 3 pumps
 * 
 * REFACTORED: Uses struct-based approach to eliminate code duplication
 * Each pump is now updated with a single reusable function
 */
void updateFlowAnimation() {
  unsigned long currentTime = millis();
  
  // Update all 3 pumps with single function
  updatePumpFlow(&pump_primary, currentTime);
  updatePumpFlow(&pump_secondary, currentTime);
  updatePumpFlow(&pump_tertiary, currentTime);
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
    
    // Apply same pattern to all 3 ICs (updated for SPI)
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_PRIMARY);
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_SECONDARY);
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_TERTIARY);
    
    Serial.println("✓ Pattern applied - verify LEDs visually");
    delay(2000);  // 2 seconds to observe
  }
  
  // Clear all at end
  writeShiftRegisterIC(0x00, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_TERTIARY);
  
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
  data[5] = pump_primary.status;
  data[6] = pump_secondary.status;
  data[7] = pump_tertiary.status;
  
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
    pump_primary.status = msg[7];
    pump_secondary.status = msg[8];
    pump_tertiary.status = msg[9];
    
    // Convert kW to MWe
    power_mwe = thermal_kw / 1000.0;
    
    Serial.printf("RX: Update - Thermal=%.1f kW → Power=%.1f MWe | Pumps: P=%d S=%d T=%d\n", 
                  thermal_kw, power_mwe, pump_primary.status, pump_secondary.status, pump_tertiary.status);
    
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

  // Initialize HARDWARE SPI for shift registers
  Serial.println("Initializing HARDWARE SPI for shift registers...");
  
  // Create HSPI instance (MOSI=13, MISO=12, SCK=14, SS=15)
  hspi = new SPIClass(HSPI);
  hspi->begin(SPI_CLOCK_PIN, -1, SPI_MOSI_PIN, -1);  // SCK, MISO (unused), MOSI, SS (unused)
  
  // Configure SPI settings: 8 MHz, MSB first, SPI Mode 0
  hspi->beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE0));
  
  // Initialize LATCH pins (act as chip select for each IC)
  pinMode(LATCH_PIN_PRIMARY, OUTPUT);
  pinMode(LATCH_PIN_SECONDARY, OUTPUT);
  pinMode(LATCH_PIN_TERTIARY, OUTPUT);
  digitalWrite(LATCH_PIN_PRIMARY, LOW);
  digitalWrite(LATCH_PIN_SECONDARY, LOW);
  digitalWrite(LATCH_PIN_TERTIARY, LOW);
  
  delay(10);  // Let pins stabilize
  
  // Clear all shift registers - ensure all LEDs are OFF
  clearAllShiftRegisters();
  Serial.println("✓ SPI initialized at 8 MHz - shift registers cleared");
  
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
  
  yield();  // Feed watchdog - no blocking delay needed
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
  // Direct conversion: 0-300 MWe → 0-255 PWM (simplified)
  int target_pwm = 0;
  
  if (power_mwe > 0) {
    target_pwm = map(power_mwe, 0, 300, 0, 255);
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