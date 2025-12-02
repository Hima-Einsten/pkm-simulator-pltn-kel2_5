/*
 * ESP-E I2C Slave - Visualizer Aliran Primer
 * 
 * I2C Slave Address: 0x0A
 * 
 * Receives from Raspberry Pi:
 * - Pressure (float, 4 bytes)
 * - Pump Status (uint8, 1 byte) - Primary pump status
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
#define I2C_SLAVE_ADDRESS 0x0A

// I2C Data Buffers
#define RECEIVE_SIZE 5
#define SEND_SIZE 2

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ============================================
// LED Multiplexer Configuration
// ============================================
#define NUM_LEDS 16

// Multiplexer control pins
const int S0 = 14;
const int S1 = 27;
const int S2 = 26;
const int S3 = 25;
const int EN = 33;  // Enable multiplexer
const int SIG = 32; // SIG/COM multiplexer (output to LED)

// Function to select multiplexer channel
void setMux(int channel) {
    digitalWrite(S0, channel & 1);
    digitalWrite(S1, (channel >> 1) & 1);
    digitalWrite(S2, (channel >> 2) & 1);
    digitalWrite(S3, (channel >> 3) & 1);
}

// Function to turn on specific LED
void turnOnLED(int index) {
    if (index >= 0 && index < NUM_LEDS) {
        setMux(index);
    }
}

// Function to turn off all LEDs
void turnOffAllLEDs() {
    setMux(15); // Set to unused channel to turn off all
}

// ============================================
// Animation Variables
// ============================================
struct {
    float pressure;
    uint8_t pumpStatus;
} masterData;

int animationPosition = 0;
unsigned long lastAnimationUpdate = 0;
unsigned long animationInterval = 200; // Default 200ms

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
    // Determine animation speed based on pump status
    // 0 = OFF, 1 = STARTING, 2 = ON, 3 = SHUTTING_DOWN
    
    switch (masterData.pumpStatus) {
        case 0: // OFF
            animationInterval = 0; // No animation
            animationSpeed = 0;
            // Turn off all LEDs
            turnOffAllLEDs();
            return;
            
        case 1: // STARTING
            animationInterval = 300; // Slow
            animationSpeed = 33;
            break;
            
        case 2: // ON
            animationInterval = 100; // Fast
            animationSpeed = 100;
            break;
            
        case 3: // SHUTTING_DOWN
            animationInterval = 500; // Very slow
            animationSpeed = 20;
            break;
    }
    
    // Perform animation
    if (millis() - lastAnimationUpdate >= animationInterval) {
        // Turn on current position LED (multiplexer stays on selected channel)
        turnOnLED(animationPosition);
        
        // Move to next position
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
    
    Serial.println("\nESP-E (Primary Flow Visualizer) I2C Slave Starting...");
    
    // Initialize I2C as Slave
    Wire.begin(I2C_SLAVE_ADDRESS);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C Slave initialized at address 0x%02X\n", I2C_SLAVE_ADDRESS);
    
    // Initialize multiplexer pins
    pinMode(S0, OUTPUT);
    pinMode(S1, OUTPUT);
    pinMode(S2, OUTPUT);
    pinMode(S3, OUTPUT);
    pinMode(EN, OUTPUT);
    pinMode(SIG, OUTPUT);
    
    digitalWrite(EN, LOW);   // Enable multiplexer (EN = LOW to enable)
    digitalWrite(SIG, HIGH); // Set signal HIGH to LED
    turnOffAllLEDs();        // Turn off all LEDs initially
    
    // Startup animation
    for (int i = 0; i < NUM_LEDS; i++) {
        turnOnLED(i);
        delay(50);
    }
    turnOffAllLEDs();
    
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
        
        // Debug output
        Serial.printf("Pressure: %.1f bar | Pump Status: %d\n",
                      masterData.pressure, masterData.pumpStatus);
    }
    
    // Update animation
    updateAnimation();
    
    // Prepare data to send
    prepareSendData();
    
    // Prevent watchdog reset
    delay(2);
}
