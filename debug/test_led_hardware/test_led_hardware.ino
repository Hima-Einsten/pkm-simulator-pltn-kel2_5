/*
 * ESP32 LED Test - Standalone Test untuk ESP-E
 * Test semua pin LED tanpa komunikasi UART
 * 
 * Tujuan: Memverifikasi bahwa hardware LED dan ESP32 berfungsi dengan baik
 * 
 * Upload program ini ke ESP-E untuk test hardware
 */

// Pin definitions (sama seperti esp_visualizer_uart.ino)
// Primary Flow
const int PRIMARY_A = 32;
const int PRIMARY_B = 33;
const int PRIMARY_C = 25;
const int PRIMARY_D = 26;

// Secondary Flow
const int SECONDARY_A = 27;
const int SECONDARY_B = 14;
const int SECONDARY_C = 12;
const int SECONDARY_D = 13;

// Tertiary Flow
const int TERTIARY_A = 15;
const int TERTIARY_B = 2;
const int TERTIARY_C = 4;
const int TERTIARY_D = 5;

// Power LED
const int POWER_LED_PIN = 23;

void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("\n\n===========================================");
  Serial.println("ESP-E LED Hardware Test");
  Serial.println("===========================================");
  
  // Initialize all LED pins
  pinMode(PRIMARY_A, OUTPUT);
  pinMode(PRIMARY_B, OUTPUT);
  pinMode(PRIMARY_C, OUTPUT);
  pinMode(PRIMARY_D, OUTPUT);
  
  pinMode(SECONDARY_A, OUTPUT);
  pinMode(SECONDARY_B, OUTPUT);
  pinMode(SECONDARY_C, OUTPUT);
  pinMode(SECONDARY_D, OUTPUT);
  
  pinMode(TERTIARY_A, OUTPUT);
  pinMode(TERTIARY_B, OUTPUT);
  pinMode(TERTIARY_C, OUTPUT);
  pinMode(TERTIARY_D, OUTPUT);
  
  // Initialize power LED PWM
  ledcAttach(POWER_LED_PIN, 5000, 8);
  
  Serial.println("✅ All pins initialized");
  Serial.println("===========================================\n");
}

void loop() {
  // Test 1: All LEDs ON
  Serial.println("[TEST 1] All LEDs ON (2 seconds)");
  digitalWrite(PRIMARY_A, HIGH);
  digitalWrite(PRIMARY_B, HIGH);
  digitalWrite(PRIMARY_C, HIGH);
  digitalWrite(PRIMARY_D, HIGH);
  
  digitalWrite(SECONDARY_A, HIGH);
  digitalWrite(SECONDARY_B, HIGH);
  digitalWrite(SECONDARY_C, HIGH);
  digitalWrite(SECONDARY_D, HIGH);
  
  digitalWrite(TERTIARY_A, HIGH);
  digitalWrite(TERTIARY_B, HIGH);
  digitalWrite(TERTIARY_C, HIGH);
  digitalWrite(TERTIARY_D, HIGH);
  
  ledcWrite(POWER_LED_PIN, 255);  // Full brightness
  
  Serial.println("  → Check: All 48 LEDs should be ON");
  Serial.println("  → Check: Power LED should be at full brightness");
  delay(2000);
  
  // Test 2: All LEDs OFF
  Serial.println("[TEST 2] All LEDs OFF (1 second)");
  digitalWrite(PRIMARY_A, LOW);
  digitalWrite(PRIMARY_B, LOW);
  digitalWrite(PRIMARY_C, LOW);
  digitalWrite(PRIMARY_D, LOW);
  
  digitalWrite(SECONDARY_A, LOW);
  digitalWrite(SECONDARY_B, LOW);
  digitalWrite(SECONDARY_C, LOW);
  digitalWrite(SECONDARY_D, LOW);
  
  digitalWrite(TERTIARY_A, LOW);
  digitalWrite(TERTIARY_B, LOW);
  digitalWrite(TERTIARY_C, LOW);
  digitalWrite(TERTIARY_D, LOW);
  
  ledcWrite(POWER_LED_PIN, 0);  // OFF
  
  Serial.println("  → Check: All LEDs should be OFF");
  delay(1000);
  
  // Test 3: Test each flow individually
  Serial.println("[TEST 3] Primary Flow Only (1 second)");
  digitalWrite(PRIMARY_A, HIGH);
  digitalWrite(PRIMARY_B, HIGH);
  digitalWrite(PRIMARY_C, HIGH);
  digitalWrite(PRIMARY_D, HIGH);
  Serial.println("  → Check: Only Primary Flow LEDs (GPIO 32,33,25,26) should be ON");
  delay(1000);
  
  digitalWrite(PRIMARY_A, LOW);
  digitalWrite(PRIMARY_B, LOW);
  digitalWrite(PRIMARY_C, LOW);
  digitalWrite(PRIMARY_D, LOW);
  
  Serial.println("[TEST 4] Secondary Flow Only (1 second)");
  digitalWrite(SECONDARY_A, HIGH);
  digitalWrite(SECONDARY_B, HIGH);
  digitalWrite(SECONDARY_C, HIGH);
  digitalWrite(SECONDARY_D, HIGH);
  Serial.println("  → Check: Only Secondary Flow LEDs (GPIO 27,14,12,13) should be ON");
  delay(1000);
  
  digitalWrite(SECONDARY_A, LOW);
  digitalWrite(SECONDARY_B, LOW);
  digitalWrite(SECONDARY_C, LOW);
  digitalWrite(SECONDARY_D, LOW);
  
  Serial.println("[TEST 5] Tertiary Flow Only (1 second)");
  digitalWrite(TERTIARY_A, HIGH);
  digitalWrite(TERTIARY_B, HIGH);
  digitalWrite(TERTIARY_C, HIGH);
  digitalWrite(TERTIARY_D, HIGH);
  Serial.println("  → Check: Only Tertiary Flow LEDs (GPIO 15,2,4,5) should be ON");
  delay(1000);
  
  digitalWrite(TERTIARY_A, LOW);
  digitalWrite(TERTIARY_B, LOW);
  digitalWrite(TERTIARY_C, LOW);
  digitalWrite(TERTIARY_D, LOW);
  
  // Test 4: Power LED PWM levels
  Serial.println("[TEST 6] Power LED PWM Test");
  Serial.println("  → 25% brightness");
  ledcWrite(POWER_LED_PIN, 64);
  delay(1000);
  
  Serial.println("  → 50% brightness");
  ledcWrite(POWER_LED_PIN, 128);
  delay(1000);
  
  Serial.println("  → 75% brightness");
  ledcWrite(POWER_LED_PIN, 192);
  delay(1000);
  
  Serial.println("  → 100% brightness");
  ledcWrite(POWER_LED_PIN, 255);
  delay(1000);
  
  ledcWrite(POWER_LED_PIN, 0);
  
  Serial.println("\n===========================================");
  Serial.println("Test cycle complete. Repeating...\n");
  delay(2000);
}
