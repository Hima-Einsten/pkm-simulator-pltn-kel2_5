#include <Arduino.h>

// Pre-compiler check to ensure ESP32 platform
#if !defined(ESP32)
#error This code is for ESP32 only! Please select ESP32 board from Tools > Board menu.
#endif

/**
 * STANDALONE TEST: Water Flow Visualization
 * 
 * File ini untuk test visualisasi aliran air tanpa dependency UART
 * Upload ke ESP32 untuk test hardware shift register + LED
 * 
 * Platform: ESP32 (Arduino framework)
 * Board: ESP32 Dev Module atau sejenisnya
 * 
 * Hardware:
 * - 3x 74HC595 shift register
 * - 3x UDN2981 source driver
 * - 24 LEDs total (8 per circuit)
 * 
 * Wiring:
 * - CLOCK (shared): GPIO 14
 * - DATA Primary: GPIO 12
 * - DATA Secondary: GPIO 13
 * - DATA Tertiary: GPIO 15
 * - LATCH Primary: GPIO 18
 * - LATCH Secondary: GPIO 19
 * - LATCH Tertiary: GPIO 21
 */

// ============================================
// PIN DEFINITIONS
// ============================================
#define CLOCK_PIN 14

#define DATA_PIN_PRIMARY 12
#define DATA_PIN_SECONDARY 13
#define DATA_PIN_TERTIARY 15

#define LATCH_PIN_PRIMARY 18
#define LATCH_PIN_SECONDARY 19
#define LATCH_PIN_TERTIARY 21

// ============================================
// ANIMATION SETTINGS
// ============================================
#define ANIMATION_DELAY 200  // ms per frame

// ============================================
// FUNCTIONS
// ============================================

/**
 * Write data to 74HC595 shift register
 * 
 * 74HC595 Protocol:
 * 1. LATCH (RCLK) LOW - prepare to receive data
 * 2. Shift 8 bits via DATA + CLOCK (SRCLK)
 *    - shiftOut() handles this automatically
 * 3. LATCH (RCLK) HIGH - transfer shift register to output register
 * 4. Data appears on Q0-Q7 outputs
 * 
 * UDN2981 then sources current to LEDs based on Q0-Q7 state
 */
void writeShiftRegister(byte data, int dataPin, int latchPin) {
  // Step 1: LATCH LOW - disable output update, prepare to receive
  digitalWrite(latchPin, LOW);
  delayMicroseconds(1);  // tsu (setup time) ~20ns minimum
  
  // Step 2: Shift 8 bits (MSB first)
  // shiftOut() automatically generates clock pulses on CLOCK_PIN
  // Each bit: DATA set → CLOCK HIGH → CLOCK LOW
  shiftOut(dataPin, CLOCK_PIN, MSBFIRST, data);
  
  // Step 3: LATCH HIGH - transfer shift register to output register
  delayMicroseconds(1);  // th (hold time) ~20ns minimum
  digitalWrite(latchPin, HIGH);
  delayMicroseconds(1);  // Output propagation delay
  
  // Now Q0-Q7 outputs reflect the 8 bits we sent
  // UDN2981 sources current to LEDs based on Q0-Q7 HIGH/LOW
}

void testAllPins() {
  Serial.println("\n=== TEST 1: All Pins Validation ===");
  Serial.println("Testing each pin individually...\n");
  
  for (int ic = 0; ic < 3; ic++) {
    int dataPin, latchPin;
    const char* name;
    
    if (ic == 0) {
      dataPin = DATA_PIN_PRIMARY;
      latchPin = LATCH_PIN_PRIMARY;
      name = "PRIMARY";
    } else if (ic == 1) {
      dataPin = DATA_PIN_SECONDARY;
      latchPin = LATCH_PIN_SECONDARY;
      name = "SECONDARY";
    } else {
      dataPin = DATA_PIN_TERTIARY;
      latchPin = LATCH_PIN_TERTIARY;
      name = "TERTIARY";
    }
    
    Serial.printf("Testing %s circuit:\n", name);
    
    // Test each bit individually
    for (int bit = 0; bit < 8; bit++) {
      byte pattern = (1 << bit);  // Single bit
      writeShiftRegister(pattern, dataPin, latchPin);
      Serial.printf("  Bit %d (Q%d): 0x%02X - LED should light\n", bit, bit, pattern);
      delay(500);
    }
    
    // Clear
    writeShiftRegister(0x00, dataPin, latchPin);
    Serial.println();
    delay(1000);
  }
  
  Serial.println("✓ Individual pin test complete\n");
}

void testPatterns() {
  Serial.println("\n=== TEST 2: Pattern Validation ===");
  
  byte patterns[] = {0xAA, 0x55, 0xFF, 0x0F, 0xF0};
  const char* names[] = {"0xAA (10101010)", "0x55 (01010101)", "0xFF (all ON)", "0x0F (lower 4)", "0xF0 (upper 4)"};
  
  for (int p = 0; p < 5; p++) {
    Serial.printf("\nPattern: %s\n", names[p]);
    Serial.println("Applying to all 3 circuits simultaneously...");
    
    writeShiftRegister(patterns[p], DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
    writeShiftRegister(patterns[p], DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
    writeShiftRegister(patterns[p], DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
    
    delay(2000);
  }
  
  // Clear all
  writeShiftRegister(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegister(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegister(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  
  Serial.println("\n✓ Pattern test complete\n");
}

void testFlowAnimation() {
  Serial.println("\n=== TEST 3: Flow Animation (Simultaneous) ===");
  Serial.println("All 3 circuits should animate together\n");
  
  int pos = 0;
  unsigned long lastUpdate = 0;
  
  for (int frame = 0; frame < 50; frame++) {  // 50 frames
    unsigned long currentTime = millis();
    
    if (currentTime - lastUpdate >= ANIMATION_DELAY) {
      lastUpdate = currentTime;
      
      // Generate 4-LED block pattern for all 3 circuits
      // All circuits use SAME position for synchronized animation
      byte pattern = 0;
      for (int i = 0; i < 4; i++) {
        int ledPos = (pos + i) % 8;
        pattern |= (1 << ledPos);  // Simple bit shift
      }
      
      // Write to ALL 3 circuits SIMULTANEOUSLY
      writeShiftRegister(pattern, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
      writeShiftRegister(pattern, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
      writeShiftRegister(pattern, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
      
      Serial.printf("Frame %d: Position %d, Pattern 0x%02X\n", frame, pos, pattern);
      
      // Advance position
      pos++;
      if (pos >= 8) pos = 0;
    }
  }
  
  // Clear all
  writeShiftRegister(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegister(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegister(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  
  Serial.println("\n✓ Flow animation test complete\n");
}

void testIndependentSpeeds() {
  Serial.println("\n=== TEST 4: Independent Speed Animation ===");
  Serial.println("Each circuit animates at different speed\n");
  
  int pos_primary = 0;
  int pos_secondary = 0;
  int pos_tertiary = 0;
  
  unsigned long lastUpdate_primary = 0;
  unsigned long lastUpdate_secondary = 0;
  unsigned long lastUpdate_tertiary = 0;
  
  unsigned long startTime = millis();
  
  while (millis() - startTime < 10000) {  // 10 seconds
    unsigned long currentTime = millis();
    
    // Primary - Fast (150ms)
    if (currentTime - lastUpdate_primary >= 150) {
      lastUpdate_primary = currentTime;
      
      byte pattern = 0;
      for (int i = 0; i < 4; i++) {
        int ledPos = (pos_primary + i) % 8;
        pattern |= (1 << ledPos);
      }
      writeShiftRegister(pattern, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
      
      pos_primary++;
      if (pos_primary >= 8) pos_primary = 0;
    }
    
    // Secondary - Medium (250ms)
    if (currentTime - lastUpdate_secondary >= 250) {
      lastUpdate_secondary = currentTime;
      
      byte pattern = 0;
      for (int i = 0; i < 4; i++) {
        int ledPos = (pos_secondary + i) % 8;
        pattern |= (1 << ledPos);
      }
      writeShiftRegister(pattern, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
      
      pos_secondary++;
      if (pos_secondary >= 8) pos_secondary = 0;
    }
    
    // Tertiary - Slow (400ms)
    if (currentTime - lastUpdate_tertiary >= 400) {
      lastUpdate_tertiary = currentTime;
      
      byte pattern = 0;
      for (int i = 0; i < 4; i++) {
        int ledPos = (pos_tertiary + i) % 8;
        pattern |= (1 << ledPos);
      }
      writeShiftRegister(pattern, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
      
      pos_tertiary++;
      if (pos_tertiary >= 8) pos_tertiary = 0;
    }
  }
  
  // Clear all
  writeShiftRegister(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegister(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegister(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  
  Serial.println("\n✓ Independent speed test complete\n");
}

// ============================================
// SETUP & LOOP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n========================================");
  Serial.println("WATER FLOW VISUALIZATION - STANDALONE TEST");
  Serial.println("========================================");
  Serial.println("Hardware: 3x 74HC595 + UDN2981");
  Serial.println("LEDs: 24 total (8 per circuit)");
  Serial.println("========================================\n");
  
  // Initialize pins with explicit states
  Serial.println("Initializing pins...");
  
  // CLOCK pin - shared by all 3 ICs
  pinMode(CLOCK_PIN, OUTPUT);
  digitalWrite(CLOCK_PIN, LOW);  // Ensure CLOCK starts LOW
  Serial.printf("  CLOCK (GPIO %d): OUTPUT, LOW\n", CLOCK_PIN);
  
  // PRIMARY circuit
  pinMode(DATA_PIN_PRIMARY, OUTPUT);
  pinMode(LATCH_PIN_PRIMARY, OUTPUT);
  digitalWrite(DATA_PIN_PRIMARY, LOW);
  digitalWrite(LATCH_PIN_PRIMARY, LOW);  // LATCH starts LOW
  Serial.printf("  PRIMARY - DATA (GPIO %d), LATCH (GPIO %d): OUTPUT, LOW\n", 
                DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  
  // SECONDARY circuit
  pinMode(DATA_PIN_SECONDARY, OUTPUT);
  pinMode(LATCH_PIN_SECONDARY, OUTPUT);
  digitalWrite(DATA_PIN_SECONDARY, LOW);
  digitalWrite(LATCH_PIN_SECONDARY, LOW);
  Serial.printf("  SECONDARY - DATA (GPIO %d), LATCH (GPIO %d): OUTPUT, LOW\n", 
                DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  
  // TERTIARY circuit
  pinMode(DATA_PIN_TERTIARY, OUTPUT);
  pinMode(LATCH_PIN_TERTIARY, OUTPUT);
  digitalWrite(DATA_PIN_TERTIARY, LOW);
  digitalWrite(LATCH_PIN_TERTIARY, LOW);
  Serial.printf("  TERTIARY - DATA (GPIO %d), LATCH (GPIO %d): OUTPUT, LOW\n", 
                DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  
  Serial.println("\n✓ All pins initialized to LOW state");
  delay(100);  // Let pins stabilize
  
  // Clear all shift registers - ensure all LEDs are OFF
  Serial.println("\nClearing all shift registers...");
  writeShiftRegister(0x00, DATA_PIN_PRIMARY, LATCH_PIN_PRIMARY);
  writeShiftRegister(0x00, DATA_PIN_SECONDARY, LATCH_PIN_SECONDARY);
  writeShiftRegister(0x00, DATA_PIN_TERTIARY, LATCH_PIN_TERTIARY);
  Serial.println("✓ All shift registers cleared (0x00)");
  Serial.println("  All LEDs should be OFF now\n");
  
  delay(2000);  // 2 seconds to verify all LEDs are OFF
  
  // Run tests
  testAllPins();
  delay(2000);
  
  testPatterns();
  delay(2000);
  
  testFlowAnimation();
  delay(2000);
  
  testIndependentSpeeds();
  
  Serial.println("\n========================================");
  Serial.println("ALL TESTS COMPLETE");
  Serial.println("========================================");
  Serial.println("\nObservations:");
  Serial.println("1. Did all individual pins light up? (Test 1)");
  Serial.println("2. Did patterns display correctly? (Test 2)");
  Serial.println("3. Did all 3 circuits animate together? (Test 3)");
  Serial.println("4. Did circuits animate at different speeds? (Test 4)");
  Serial.println("\nIf YES to all → Hardware OK, check main firmware");
  Serial.println("If NO → Check wiring, IC, or LED connections");
  Serial.println("========================================\n");
}

void loop() {
  // Tests run once in setup()
  // Loop does nothing
  delay(1000);
}
