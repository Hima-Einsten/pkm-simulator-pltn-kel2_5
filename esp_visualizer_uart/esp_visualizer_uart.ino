/*
 * ESP32 Power Indicator - BINARY PROTOCOL VERSION (OPTIMIZED)
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
 * Pin Configuration (NO CONFLICT):
 * - LED Power: GPIO 25, 26, 27, 32 (safe pins, no SPI conflict)
 * - SPI HSPI: SCK=14, MOSI=13 (default, no conflict with LEDs)
 * 
 * Protocol: BINARY Protocol with ACK/NACK (115200 baud, 8N1)
 * - Command: 9 bytes (vs 42 bytes JSON) - 79% reduction
 * - Response: 10 bytes (vs 45 bytes JSON) - 78% reduction
 * - CRC8 checksum for error detection
 * - ACK/NACK responses for reliability
 * - No buffer garbage issues
 * 
 * OPTIMIZATION:
 * - Fixed SPI pin conflicts
 * - Non-blocking UART processing
 * - Consistent animation timing
 * - Reduced microsecond delays
 * - Task separation with proper intervals
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
// PUMP STRUCT
// ============================================// Pump structure - simplified for OE-based control
struct Pump {
  uint8_t status;           // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
  int oePin;                // Output Enable pin (LOW=enabled, HIGH=disabled)
  uint8_t lastStatus;       // For detecting status changes
};

// ============================================
// DEBUG Configuration
// ============================================
#define DEBUG_SHIFT_REGISTER false   // Set to true untuk debug LED animation
#define DEBUG_UART false            // Debug UART communication
#define DEBUG_TIMING false           // Debug timing performance
#define HARDWARE_TEST_MODE false    // Set TRUE untuk test kontinyu (bypass pump status)

// ============================================
// HARDWARE PIN ASSIGNMENT (NO CONFLICT)
// ============================================

// LED POWER - GPIO yang AMAN (tidak konflik dengan SPI/ADC)
const int NUM_LEDS = 4;
const int POWER_LEDS[NUM_LEDS] = {25, 26, 27, 32};  // GPIO aman, tidak konflik

#define SPI_CLOCK_PIN 14       // SCK - LEDC PWM (continuous 10kHz)
#define SPI_MOSI_PIN 13        // MOSI - Manual bit-banging

// LATCH Pin (RCLK) - GLOBAL untuk semua IC (shared)
#define LATCH_PIN_GLOBAL 4     // Shared RCLK for all 74HC595 ICs

// OUTPUT ENABLE Pins - Separate per IC untuk kontrol ON/OFF
#define OE_PIN_PRIMARY 18      // OE IC#1 - Primary pump (LOW=enabled, HIGH=disabled)
#define OE_PIN_SECONDARY 19    // OE IC#2 - Secondary pump
#define OE_PIN_TERTIARY 21     // OE IC#3 - Tertiary pump

// ============================================
// BIT-BANGING MODE - LEDC PWM Clock Only
// ============================================
#define BIT_DELAY_US 10      // 10us = half period of 10kHz

// Animation state
byte currentPattern = 0x00;
int animationPos = 0;
// Independent animation phase for each pump (WATER FLOW MODEL)
int animPosPrimary = 0;
int animPosSecondary = 0;
int animPosTertiary = 0;

// ============================================
// TIMING CONFIGURATION (CRITICAL FOR SMOOTH ANIMATION)
// ============================================
#define ANIM_STEP_DELAY 1000      // 1 detik per step animasi (realistic water flow)
#define LED_UPDATE_INTERVAL 100   // Update LED power setiap 100ms
#define UART_PROCESS_INTERVAL 10  // Proses UART setiap 10ms
#define DEBUG_INTERVAL 2000       // Debug output setiap 2 detik

// Independent animation timers per pump
unsigned long lastAnimPrimary = 0;
unsigned long lastAnimSecondary = 0;
unsigned long lastAnimTertiary = 0;

// ============================================
// CONTINUOUS SPI MODE (NEW APPROACH)
// ============================================
// SPI selalu aktif mengirim pattern ke semua IC
// LATCH pin mengontrol apakah output IC aktif atau tidak


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

// Binary Message Buffer
uint8_t rx_buffer[16];
uint8_t rx_index = 0;

// State machine untuk robust frame parsing
enum RxState {
  WAIT_STX,
  IN_FRAME
};
RxState rx_state = WAIT_STX;

unsigned long last_byte_time = 0;
#define RX_TIMEOUT_MS 500

// ============================================
// DATA VARIABLES
// ============================================
float thermal_kw = 0.0;
float power_mwe = 0.0;
int current_pwm = 0;

// Pump instances with OE pins
Pump pump_primary = {0, OE_PIN_PRIMARY, 0};
Pump pump_secondary = {0, OE_PIN_SECONDARY, 0};
Pump pump_tertiary = {0, OE_PIN_TERTIARY, 0};



// LED Mode Control
#define PWM_THRESHOLD_HIGH 250
#define PWM_THRESHOLD_LOW 240
bool led_mode_high = false;

// ============================================
// Flow Animation Pattern
// ============================================
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

// ============================================
// BIT-BANGING SHIFT REGISTER FUNCTIONS
// ============================================
void shiftOutManual(byte data) {
  for (int i = 7; i >= 0; i--) {
    digitalWrite(SPI_MOSI_PIN, (data >> i) & 1);
    digitalWrite(SPI_CLOCK_PIN, HIGH);
    delayMicroseconds(BIT_DELAY_US);
    digitalWrite(SPI_CLOCK_PIN, LOW);
    delayMicroseconds(BIT_DELAY_US);
  }
}

/**
 * Send pattern to ALL shift registers using global LATCH
 * All ICs share one RCLK line, receive same pattern
 */
void sendPattern(byte pattern) {
  // Global LATCH LOW - prepare all ICs to receive data
  digitalWrite(LATCH_PIN_GLOBAL, LOW);
  delayMicroseconds(1);
  
  // Send 8 bits to all 3 ICs sequentially (they share MOSI)
  shiftOutManual(pattern);  // IC #1
  shiftOutManual(pattern);  // IC #2
  shiftOutManual(pattern);  // IC #3
  
  delayMicroseconds(1);
  
  // Global LATCH HIGH - transfer to output registers
  digitalWrite(LATCH_PIN_GLOBAL, HIGH);
  delayMicroseconds(1);
  
  #if DEBUG_SHIFT_REGISTER
    Serial.printf("[SEND] Pattern=0x%02X to all ICs\n", pattern);
  #endif
}

/**
 * Update OE pins based on pump status
 * OE LOW = output enabled (LEDs visible)
 * OE HIGH = output disabled (LEDs off)
 */
void updatePumpOutputs() {
  // Primary pump
  if (pump_primary.status == 2 || pump_primary.status == 3) {
    digitalWrite(pump_primary.oePin, LOW);  // Enable output
  } else {
    digitalWrite(pump_primary.oePin, HIGH); // Disable output
  }
  
  // Secondary pump
  if (pump_secondary.status == 2 || pump_secondary.status == 3) {
    digitalWrite(pump_secondary.oePin, LOW);
  } else {
    digitalWrite(pump_secondary.oePin, HIGH);
  }
  
  // Tertiary pump
  if (pump_tertiary.status == 2 || pump_tertiary.status == 3) {
    digitalWrite(pump_tertiary.oePin, LOW);
  } else {
    digitalWrite(pump_tertiary.oePin, HIGH);
  }
  
  #if DEBUG_TIMING
    Serial.printf("[OE] P1=%s P2=%s P3=%s\n",
                  pump_primary.status >= 2 ? "ON" : "OFF",
                  pump_secondary.status >= 2 ? "ON" : "OFF",
                  pump_tertiary.status >= 2 ? "ON" : "OFF");
  #endif
}

void clearAllShiftRegisters() {
  // Send 0x00 using global LATCH
  sendPattern(0x00);
}



// ============================================
// BINARY PROTOCOL FUNCTIONS
// ============================================

void sendNACK() {
  uint8_t response[5];
  response[0] = STX;
  response[1] = NACK;
  response[2] = 0;
  
  uint8_t crc_data[2] = {NACK, 0};
  response[3] = crc8_maxim(crc_data, 2);
  response[4] = ETX;
  
  UartComm.write(response, 5);
  UartComm.flush();  // CRITICAL: Ensure data is sent before continuing
  
  #if DEBUG_UART
    Serial.println("TX: NACK");
  #endif
}

void sendPongResponse() {
  uint8_t response[5];
  response[0] = STX;
  response[1] = ACK;
  response[2] = 0;
  
  uint8_t crc_data[2] = {ACK, 0};
  response[3] = crc8_maxim(crc_data, 2);
  response[4] = ETX;
  
  UartComm.write(response, 5);
  UartComm.flush();  // CRITICAL: Ensure data is sent before continuing
  
  #if DEBUG_UART
    Serial.println("TX: Pong ACK");
  #endif
}

void sendUpdateResponse() {
  uint8_t response[13];
  response[0] = STX;
  response[1] = ACK;
  response[2] = 8;
  
  uint8_t* data = &response[3];
  memcpy(&data[0], &power_mwe, 4);
  data[4] = (uint8_t)current_pwm;
  data[5] = pump_primary.status;
  data[6] = pump_secondary.status;
  data[7] = pump_tertiary.status;
  
  response[11] = crc8_maxim(&response[1], 10);
  response[12] = ETX;
  
  UartComm.write(response, 13);
  UartComm.flush();  // CRITICAL: Ensure data is sent before continuing
  
  #if DEBUG_UART
    Serial.println("TX: Update ACK with data");
  #endif
}

void processBinaryMessage(uint8_t* msg, uint8_t len) {
  // Validasi struktur pesan
  if (len < 5 || msg[0] != STX || msg[len-1] != ETX) {
    sendNACK();
    return;
  }
  
  uint8_t cmd = msg[1];
  uint8_t payload_len = msg[2];
  uint8_t received_crc = msg[len-2];
  
  // Validasi panjang
  uint8_t expected_len = 5 + payload_len;
  if (len != expected_len) {
    sendNACK();
    return;
  }
  
  // Validasi CRC
  uint8_t crc_len = 2 + payload_len;
  uint8_t calculated_crc = crc8_maxim(&msg[1], crc_len);
  
  if (received_crc != calculated_crc) {
    sendNACK();
    return;
  }
  
  // Process command
  if (cmd == CMD_PING) {
    if (payload_len != 0) {
      sendNACK();
      return;
    }
    
    #if DEBUG_UART
      Serial.println("RX: Ping");
    #endif
    
    sendPongResponse();
  }
  else if (cmd == CMD_UPDATE) {
    if (payload_len != 7) {
      sendNACK();
      return;
    }
    
    pump_primary.lastStatus = pump_primary.status;
    pump_secondary.lastStatus = pump_secondary.status;
    pump_tertiary.lastStatus = pump_tertiary.status;
    // Parse data
    memcpy(&thermal_kw, &msg[3], 4);
    pump_primary.status = msg[7];
    pump_secondary.status = msg[8];
    pump_tertiary.status = msg[9];
    
    // Convert kW to MWe
    power_mwe = thermal_kw / 1000.0;
    
    #if DEBUG_UART
      Serial.printf("RX: Update - Thermal=%.1f kW → Power=%.1f MWe\n", 
                    thermal_kw, power_mwe);
    #endif
    
    sendUpdateResponse();
  }
  else {
    sendNACK();
  }
}

// ============================================
// UART PROCESSING (NON-BLOCKING)
// ============================================

void processUART() {
  // Batasi jumlah byte yang diproses per panggilan untuk non-blocking
  // INCREASED: 10 -> 20 bytes untuk handle UPDATE command (12 bytes)
  uint8_t bytes_processed = 0;
  const uint8_t MAX_BYTES_PER_CALL = 20;  // Cukup untuk 1 pesan lengkap
  
  while (UartComm.available() && bytes_processed < MAX_BYTES_PER_CALL) {
    uint8_t byte = UartComm.read();
    bytes_processed++;
    
    unsigned long current_time = millis();
    
    // Timeout check
    if (rx_state == IN_FRAME && (current_time - last_byte_time > RX_TIMEOUT_MS)) {
      rx_state = WAIT_STX;
      rx_index = 0;
    }
    
    last_byte_time = current_time;
    
    // State machine
    if (rx_state == WAIT_STX) {
      if (byte == STX) {
        rx_index = 0;
        rx_buffer[rx_index++] = byte;
        rx_state = IN_FRAME;
      }
    }
    else if (rx_state == IN_FRAME) {
      if (rx_index < sizeof(rx_buffer)) {
        rx_buffer[rx_index++] = byte;
        
        if (byte == ETX) {
          processBinaryMessage(rx_buffer, rx_index);
          rx_state = WAIT_STX;
          rx_index = 0;
        }
      }
      else {
        // Buffer overflow
        rx_state = WAIT_STX;
        rx_index = 0;
      }
    }
    
    yield();  // Feed watchdog during UART processing
  }
}

// ============================================
// POWER LED FUNCTIONS
// ============================================

void updatePowerLED() {
  // Calculate PWM based on power output
  int target_pwm = 0;
  
  if (power_mwe > 0) {
    target_pwm = map(power_mwe, 0, 300, 0, 255);
    target_pwm = constrain(target_pwm, 0, 255);
    
    if (target_pwm < 20) {
      target_pwm = 20;
    }
  }
  
  // Smooth transition
  if (target_pwm > current_pwm) {
    current_pwm += min(5, target_pwm - current_pwm);
  } else if (target_pwm < current_pwm) {
    current_pwm -= min(5, current_pwm - target_pwm);
  }
  
  // Mode switching dengan hysteresis
  if (!led_mode_high && current_pwm >= PWM_THRESHOLD_HIGH) {
    // Switch ke HIGH mode
    for (int i = 0; i < NUM_LEDS; i++) {
      ledcDetach(POWER_LEDS[i]);
      pinMode(POWER_LEDS[i], OUTPUT);
      digitalWrite(POWER_LEDS[i], HIGH);
    }
    led_mode_high = true;
    
    #if DEBUG_TIMING
      Serial.println("LED Mode: HIGH (full brightness)");
    #endif
  }
  else if (led_mode_high && current_pwm < PWM_THRESHOLD_LOW) {
    // Switch kembali ke PWM mode
    for (int i = 0; i < NUM_LEDS; i++) {
      ledcAttach(POWER_LEDS[i], 5000, 8);
      ledcWrite(POWER_LEDS[i], current_pwm);
    }
    led_mode_high = false;
    
    #if DEBUG_TIMING
      Serial.println("LED Mode: PWM");
    #endif
  }
  // Update PWM jika dalam mode PWM
  else if (!led_mode_high) {
    for (int i = 0; i < NUM_LEDS; i++) {
      ledcWrite(POWER_LEDS[i], current_pwm);
    }
  }
  // HIGH mode: LEDs tetap HIGH, tidak perlu update
  
  // Debug output
  static unsigned long last_debug = 0;
  #if DEBUG_TIMING
    if (millis() - last_debug > DEBUG_INTERVAL) {
      last_debug = millis();
      const char* mode_str = led_mode_high ? "HIGH" : "PWM";
      Serial.printf("Power: %.1f MWe | PWM: %d | Mode: %s\n", 
                    power_mwe, current_pwm, mode_str);
    }
  #endif
}



// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP32 Power Indicator - OPTIMIZED VERSION");
  Serial.println("===========================================");
  Serial.println("Pin Configuration (No Conflict - FIXED):");
  Serial.println("  Power LEDs: GPIO 25, 26, 27, 32");
  Serial.println("  SPI HSPI: SCK=14, MOSI=13");
  Serial.println("  UART: RX=16, TX=17");
  Serial.println("===========================================");
  
  // Initialize UART
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  
  // Initialize GPIO pins for continuous mode
  Serial.println("Initializing GPIO pins for PWM CONTINUOUS MODE...");
  
  // IMPORTANT: Do NOT set pinMode for SPI_CLOCK_PIN
  // LEDC PWM will handle it automatically
  
  // Only initialize data pin
  pinMode(SPI_MOSI_PIN, OUTPUT);
  digitalWrite(SPI_MOSI_PIN, LOW);
  Serial.println("✓ GPIO 13 (data) initialized");
  Serial.println("✓ GPIO 14 (clock) will be controlled by LEDC PWM only");
  
  delay(10);
  
  // Initialize GLOBAL LATCH pin
  pinMode(LATCH_PIN_GLOBAL, OUTPUT);
  digitalWrite(LATCH_PIN_GLOBAL, LOW);
  Serial.println("✓ Global LATCH pin initialized (GPIO 4)");
  
  // Initialize OE pins (FAIL-SAFE: HIGH = disabled)
  pinMode(OE_PIN_PRIMARY, OUTPUT);
  pinMode(OE_PIN_SECONDARY, OUTPUT);
  pinMode(OE_PIN_TERTIARY, OUTPUT);
  digitalWrite(OE_PIN_PRIMARY, HIGH);    // Disabled at boot
  digitalWrite(OE_PIN_SECONDARY, HIGH);  // Disabled at boot
  digitalWrite(OE_PIN_TERTIARY, HIGH);   // Disabled at boot

  pinMode(SPI_CLOCK_PIN, OUTPUT);
  digitalWrite(SPI_CLOCK_PIN, LOW);

  
  delay(10);
  
  // Continuous mode will start automatically - no test needed
  Serial.println("\nSkipping SPI test - continuous mode will verify signals");
  
  // Clear all shift registers
  Serial.println("Clearing all shift registers...");
  clearAllShiftRegisters();
  Serial.println("✓ SPI test complete - shift registers cleared");
  
  // Initialize all power LEDs
  Serial.println("Initializing 4 power LEDs...");
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(POWER_LEDS[i], OUTPUT);
    ledcAttach(POWER_LEDS[i], 5000, 8);
    ledcWrite(POWER_LEDS[i], 0);
    Serial.printf("  LED %d: GPIO %d\n", i+1, POWER_LEDS[i]);
  }
  
  Serial.println("UART ready at 115200 baud");
  Serial.println("Timing Configuration:");
  Serial.printf("  Animation Step: %d ms\n", ANIM_STEP_DELAY);
  Serial.printf("  LED Update: %d ms interval\n", LED_UPDATE_INTERVAL);
  Serial.println("===========================================");
  Serial.println("ESP32 Power Indicator READY");
  Serial.println("===========================================\n");
  

  
  // Quick LED test
  Serial.println("Testing power LEDs (quick flash)...");
  for (int i = 0; i < 2; i++) {
    for (int j = 0; j < NUM_LEDS; j++) {
      ledcWrite(POWER_LEDS[j], 255);
    }
    delay(100);
    for (int j = 0; j < NUM_LEDS; j++) {
      ledcWrite(POWER_LEDS[j], 0);
    }
    delay(100);
  }
  Serial.println("LED test complete\n");
}

// ============================================
// MAIN LOOP (OPTIMIZED)
// ============================================

void loop() {
  static unsigned long last_led_time = 0;
  static unsigned long last_uart_time = 0;
  
  unsigned long current_time = millis();
  
  // NORMAL OPERATION - Independent animation per pump
  
  // Reset animation phase when pump transitions OFF -> ON
  if (pump_primary.lastStatus < 2 && pump_primary.status >= 2) {
    animPosPrimary = 0;
    lastAnimPrimary = current_time;  // Reset timer
  }

  if (pump_secondary.lastStatus < 2 && pump_secondary.status >= 2) {
    animPosSecondary = 0;
    lastAnimSecondary = current_time;  // Reset timer
  }

  if (pump_tertiary.lastStatus < 2 && pump_tertiary.status >= 2) {
    animPosTertiary = 0;
    lastAnimTertiary = current_time;  // Reset timer
  }

  byte combinedPattern = 0x00;

  /* ================= PRIMARY ================= */
  if (pump_primary.status >= 2) {
    if (current_time - lastAnimPrimary >= ANIM_STEP_DELAY) {
      animPosPrimary = (animPosPrimary + 1) % 8;
      lastAnimPrimary = current_time;
    }
    combinedPattern |= FLOW_PATTERN[animPosPrimary];
  }

  /* ================= SECONDARY ================= */
  if (pump_secondary.status >= 2) {
    if (current_time - lastAnimSecondary >= ANIM_STEP_DELAY) {
      animPosSecondary = (animPosSecondary + 1) % 8;
      lastAnimSecondary = current_time;
    }
    combinedPattern |= FLOW_PATTERN[animPosSecondary];
  }

  /* ================= TERTIARY ================= */
  if (pump_tertiary.status >= 2) {
    if (current_time - lastAnimTertiary >= ANIM_STEP_DELAY) {
      animPosTertiary = (animPosTertiary + 1) % 8;
      lastAnimTertiary = current_time;
    }
    combinedPattern |= FLOW_PATTERN[animPosTertiary];
  }

  // Kirim ke shift register & update OE
  sendPattern(combinedPattern);
  updatePumpOutputs();
  
  yield();  // Prevent watchdog timeout

  
  // 2. Update LED power dengan interval terpisah
  if (current_time - last_led_time >= LED_UPDATE_INTERVAL) {
    updatePowerLED();
    last_led_time = current_time;
  }
  
  // 3. Proses UART dengan interval terpisah
  if (current_time - last_uart_time >= UART_PROCESS_INTERVAL) {
    processUART();
    last_uart_time = current_time;
  }

  pump_primary.lastStatus   = pump_primary.status;
  pump_secondary.lastStatus = pump_secondary.status;
  pump_tertiary.lastStatus  = pump_tertiary.status;

  // Yield untuk menjaga stabilitas sistem
  yield();
}