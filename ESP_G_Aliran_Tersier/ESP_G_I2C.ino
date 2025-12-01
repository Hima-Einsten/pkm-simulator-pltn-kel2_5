/*
 * ESP-G I2C Slave - Visualizer Aliran Tersier
 * 
 * I2C Slave Address: 0x0C
 * 
 * Receives from Raspberry Pi:
 * - Pressure (float, 4 bytes)
 * - Pump Status (uint8, 1 byte) - Tertiary pump status
 * Total: 5 bytes
 * 
 * Sends to Raspberry Pi:
 * - Animation Speed (uint8, 1 byte)
 * - LED Count (uint8, 1 byte)
 * Total: 2 bytes
 */

#include <Wire.h>

// ============================================
// I2C Slave Configuration
// ============================================
#define I2C_SLAVE_ADDRESS 0x0C

// I2C Data Buffers
#define RECEIVE_SIZE 5
#define SEND_SIZE 2

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ============================================
// LED Configuration
// ============================================
#define NUM_LEDS 16
const int ledPins[NUM_LEDS] = {
    13, 12, 14, 27, 26, 25, 33, 32,
    15, 2, 0, 4, 16, 17, 5, 18
};

// ============================================
// Animation Variables
// ============================================
struct {
    float pressure;
    uint8_t pumpStatus;
} masterData;

int animationPosition = 0;
unsigned long lastAnimationUpdate = 0;
unsigned long animationInterval = 200;

uint8_t animationSpeed = 0;
const uint8_t LED_COUNT = NUM_LEDS;

// ============================================
// I2C Callback Functions (ISR - Keep Simple!)
// ============================================

void onReceiveData(int numBytes) {
    if (numBytes <= 0 || numBytes > RECEIVE_SIZE) return;
    
    for (int i = 0; i < numBytes; i++) {
        receiveBuffer[i] = Wire.read();
    }
    receiveLength = numBytes;
    newDataFlag = true;
}

void onRequestData() {
    Wire.write(sendBuffer, SEND_SIZE);
}

// ============================================
// Data Processing
// ============================================

void prepareSendData() {
    sendBuffer[0] = animationSpeed;
    sendBuffer[1] = LED_COUNT;
}

// ============================================
// LED Animation
// ============================================

void updateAnimation() {
    switch (masterData.pumpStatus) {
        case 0: // OFF
            animationInterval = 0;
            animationSpeed = 0;
            for (int i = 0; i < NUM_LEDS; i++) {
                digitalWrite(ledPins[i], LOW);
            }
            return;
            
        case 1: // STARTING
            animationInterval = 300;
            animationSpeed = 33;
            break;
            
        case 2: // ON
            animationInterval = 100;
            animationSpeed = 100;
            break;
            
        case 3: // SHUTTING_DOWN
            animationInterval = 500;
            animationSpeed = 20;
            break;
    }
    
    if (millis() - lastAnimationUpdate >= animationInterval) {
        for (int i = 0; i < NUM_LEDS; i++) {
            digitalWrite(ledPins[i], LOW);
        }
        
        digitalWrite(ledPins[animationPosition], HIGH);
        
        animationPosition++;
        if (animationPosition >= NUM_LEDS) {
            animationPosition = 0;
        }
        
        lastAnimationUpdate = millis();
    }
}

// ============================================
// Setup
// ============================================

void setup() {
    Serial.begin(115200);
    delay(300);
    
    Serial.println("\nESP-G (Tertiary Flow Visualizer) I2C Slave Starting...");
    
    Wire.begin(I2C_SLAVE_ADDRESS);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C Slave initialized at address 0x%02X\n", I2C_SLAVE_ADDRESS);
    
    for (int i = 0; i < NUM_LEDS; i++) {
        pinMode(ledPins[i], OUTPUT);
        digitalWrite(ledPins[i], LOW);
    }
    
    // Startup animation
    for (int i = 0; i < NUM_LEDS; i++) {
        digitalWrite(ledPins[i], HIGH);
        delay(50);
        digitalWrite(ledPins[i], LOW);
    }
    
    // Prepare initial send buffer
    prepareSendData();
    
    Serial.println("I2C Ready. Waiting for Raspberry Pi...");
}

// ============================================
// Loop
// ============================================

void loop() {
    // Process received data from Raspberry Pi
    if (newDataFlag) {
        newDataFlag = false;
        
        // Copy to local buffer to avoid volatile issues
        uint8_t buf[RECEIVE_SIZE];
        memcpy(buf, (const void*)receiveBuffer, RECEIVE_SIZE);
        
        // Parse received data
        memcpy(&masterData.pressure, &buf[0], 4);
        masterData.pumpStatus = buf[4];
        
        Serial.printf("Pressure: %.1f bar | Pump Status: %d\n",
                      masterData.pressure, masterData.pumpStatus);
    }
    
    updateAnimation();
    prepareSendData();
    
    // Prevent watchdog reset
    delay(2);
}
