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
 * - LATCH Pins: 4, 16, 17 (safe pins, no SPI conflict)
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
// PUMP STRUCT
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
#define DEBUG_SHIFT_REGISTER false  // Set to false untuk mengurangi Serial output
#define DEBUG_UART false            // Debug UART communication
#define DEBUG_TIMING false          // Debug timing performance

// ============================================
// HARDWARE PIN ASSIGNMENT (NO CONFLICT)
// ============================================

// LED POWER - GPIO yang AMAN (tidak konflik dengan SPI/ADC)
const int NUM_LEDS = 4;
const int POWER_LEDS[NUM_LEDS] = {25, 26, 27, 32};  // GPIO aman, tidak konflik

// SHIFT REGISTER - Menggunakan HARDWARE SPI (HSPI)
#define SPI_CLOCK_PIN 14       // SCK - HSPI default
#define SPI_MOSI_PIN 13        // MOSI - HSPI default
// MISO (12) dan SS (15) tidak digunakan

// LATCH Pins (separate per IC) - GPIO yang AMAN
#define LATCH_PIN_PRIMARY 4    // IC #1 - Primary pump flow
#define LATCH_PIN_SECONDARY 5 // IC #2 - Secondary pump flow
#define LATCH_PIN_TERTIARY 12  // IC #3 - Tertiary pump flow

// SPI Configuration
SPIClass * hspi = NULL;
#define SPI_FREQUENCY 8000000  // 8 MHz

// ============================================
// TIMING CONFIGURATION (CRITICAL FOR SMOOTH ANIMATION)
// ============================================
#define ANIMATION_INTERVAL 150    // Update animasi setiap 150ms (konsisten!)
#define LED_UPDATE_INTERVAL 100   // Update LED power setiap 100ms
#define UART_PROCESS_INTERVAL 10  // Proses UART setiap 10ms
#define DEBUG_INTERVAL 2000       // Debug output setiap 2 detik

// Animation speeds (milliseconds per step)
#define ANIM_SPEED_ON 500         // 500ms per step saat ON
#define ANIM_SPEED_SHUTDOWN 1000  // 1000ms per step saat SHUTTING_DOWN

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

// Pump instances
Pump pump_primary = {0, LATCH_PIN_PRIMARY, 0, 0, 255};
Pump pump_secondary = {0, LATCH_PIN_SECONDARY, 0, 0, 255};
Pump pump_tertiary = {0, LATCH_PIN_TERTIARY, 0, 0, 255};

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
// SHIFT REGISTER FUNCTIONS (OPTIMIZED)
// ============================================

void writeShiftRegisterIC(byte data, int latchPin) {
  // OPTIMIZED: Minimal delays for stability
  digitalWrite(latchPin, LOW);
  // No delay needed - SPI is hardware synchronized
  hspi->transfer(data);
  digitalWrite(latchPin, HIGH);
  // No delay needed - latch is edge triggered
  
  #if DEBUG_SHIFT_REGISTER
    Serial.print("[SPI] Latch=");
    Serial.print(latchPin);
    Serial.print(" Data=0x");
    Serial.println(data, HEX);
  #endif
}

void clearAllShiftRegisters() {
  writeShiftRegisterIC(0x00, LATCH_PIN_PRIMARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_SECONDARY);
  writeShiftRegisterIC(0x00, LATCH_PIN_TERTIARY);
}

// ============================================
// ANIMATION FUNCTIONS (OPTIMIZED)
// ============================================

void updatePumpFlow(Pump *p, unsigned long now) {
  // Deteksi perubahan status
  if (p->status != p->lastStatus) {
    #if DEBUG_TIMING
      Serial.printf("[PUMP] Latch=%d Status: %d->%d\n", 
                    p->latchPin, p->lastStatus, p->status);
    #endif
    p->lastStatus = p->status;
    p->pos = 0;
    p->lastUpdate = now;  // Reset timing
    
    // Jika status OFF, matikan LED segera
    if (p->status == 0) {
      writeShiftRegisterIC(0x00, p->latchPin);
    }
  }
  
  // Handle berdasarkan status
  switch (p->status) {
    case 0:  // OFF
      // Sudah dimatikan di atas, tidak perlu update berulang
      return;
      
    case 1:  // STARTING
      // Tidak ada animasi, LED mati
      if (p->pos != 0) {
        writeShiftRegisterIC(0x00, p->latchPin);
        p->pos = 0;
      }
      return;
      
    case 2:  // ON - normal flow
      if (now - p->lastUpdate >= ANIM_SPEED_ON) {
        p->lastUpdate = now;
        writeShiftRegisterIC(FLOW_PATTERN[p->pos], p->latchPin);
        p->pos = (p->pos + 1) % 8;
      }
      break;
      
    case 3:  // SHUTTING_DOWN - slow flow
      if (now - p->lastUpdate >= ANIM_SPEED_SHUTDOWN) {
        p->lastUpdate = now;
        writeShiftRegisterIC(FLOW_PATTERN[p->pos], p->latchPin);
        p->pos = (p->pos + 1) % 8;
      }
      break;
  }
}

void updateFlowAnimation() {
  unsigned long currentTime = millis();
  
  // Update semua pump dengan interval yang konsisten
  updatePumpFlow(&pump_primary, currentTime);
  updatePumpFlow(&pump_secondary, currentTime);
  updatePumpFlow(&pump_tertiary, currentTime);
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
  // Batasi jumlah byte yang diproses per panggilan
  uint8_t bytes_processed = 0;
  
  while (UartComm.available() && bytes_processed < 10) {
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
// HARDWARE TEST
// ============================================

void testShiftRegisterHardware() {
  Serial.println("\n=== SHIFT REGISTER HARDWARE TEST ===");
  
  // Test pattern untuk verifikasi hardware
  byte testPatterns[] = {0x81, 0x42, 0x24, 0x18, 0xFF, 0x00};
  
  for (int test = 0; test < 6; test++) {
    Serial.printf("\nPattern %d: 0x%02X\n", test+1, testPatterns[test]);
    
    // Test semua IC dengan pattern yang sama
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_PRIMARY);
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_SECONDARY);
    writeShiftRegisterIC(testPatterns[test], LATCH_PIN_TERTIARY);
    
    delay(1000);
  }
  
  // Clear all
  clearAllShiftRegisters();
  Serial.println("\n✅ Hardware test complete\n");
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
  Serial.println("Pin Configuration (No Conflict):");
  Serial.println("  Power LEDs: GPIO 25, 26, 27, 32");
  Serial.println("  SPI HSPI: SCK=14, MOSI=13");
  Serial.println("  LATCH Pins: 4, 16, 17");
  Serial.println("===========================================");
  
  // Initialize UART
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  
  // Initialize HARDWARE SPI
  Serial.println("Initializing HARDWARE SPI (HSPI)...");
  hspi = new SPIClass(HSPI);
  hspi->begin(SPI_CLOCK_PIN, -1, SPI_MOSI_PIN, -1);
  hspi->beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE0));
  
  // Initialize LATCH pins
  pinMode(LATCH_PIN_PRIMARY, OUTPUT);
  pinMode(LATCH_PIN_SECONDARY, OUTPUT);
  pinMode(LATCH_PIN_TERTIARY, OUTPUT);
  digitalWrite(LATCH_PIN_PRIMARY, LOW);
  digitalWrite(LATCH_PIN_SECONDARY, LOW);
  digitalWrite(LATCH_PIN_TERTIARY, LOW);
  
  delay(10);
  
  // Clear all shift registers
  clearAllShiftRegisters();
  Serial.println("✓ SPI initialized - shift registers cleared");
  
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
  Serial.printf("  Animation: %d ms interval\n", ANIMATION_INTERVAL);
  Serial.printf("  LED Update: %d ms interval\n", LED_UPDATE_INTERVAL);
  Serial.println("===========================================");
  Serial.println("ESP32 Power Indicator READY");
  Serial.println("===========================================\n");
  
  // Uncomment untuk test hardware saat startup
  // testShiftRegisterHardware();
  
  // Test LED flash
  Serial.println("Testing LEDs...");
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
  static unsigned long last_anim_time = 0;
  static unsigned long last_led_time = 0;
  static unsigned long last_uart_time = 0;
  
  unsigned long current_time = millis();
  
  // 1. Update animasi dengan interval KONSISTEN
  if (current_time - last_anim_time >= ANIMATION_INTERVAL) {
    updateFlowAnimation();
    last_anim_time = current_time;
  }
  
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
  
  // Yield untuk menjaga stabilitas sistem
  yield();
}