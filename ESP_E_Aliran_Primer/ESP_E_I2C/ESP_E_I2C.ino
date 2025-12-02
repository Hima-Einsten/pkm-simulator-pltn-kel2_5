/*
 * ESP-E I2C Slave - Visualizer 3 Aliran (Primer, Sekunder, Tersier)
 * 
 * I2C Slave Address: 0x0A
 * 
 * Receives from Raspberry Pi:
 * - Pressure 1 (float, 4 bytes) - Primary
 * - Pump Status 1 (uint8, 1 byte) - Primary
 * - Pressure 2 (float, 4 bytes) - Secondary
 * - Pump Status 2 (uint8, 1 byte) - Secondary
 * - Pressure 3 (float, 4 bytes) - Tertiary
 * - Pump Status 3 (uint8, 1 byte) - Tertiary
 * Total: 15 bytes
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
#define RECEIVE_SIZE 16  // Python sends: 1 byte register + 15 bytes data (3 flows x 5 bytes)
#define DATA_SIZE 15     // Actual data: 3 x (4 bytes float + 1 byte status)
#define SEND_SIZE 2

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ============================================
// LED Multiplexer Configuration - 3 Flow Visualizers
// ============================================
#define NUM_LEDS 16
#define NUM_FLOWS 3      // Aliran Primer, Sekunder, Tersier
#define NUM_WAVES 4      // Jumlah gelombang per aliran
#define WAVE_LENGTH 3    // Panjang setiap gelombang (LED)
#define WAVE_SPACING 4   // Jarak antar gelombang

// Multiplexer selector pins (SHARED untuk 3 multiplexer)
const int S0 = 14;
const int S1 = 27;
const int S2 = 26;
const int S3 = 25;

// Multiplexer enable pins (1 per flow)
const int EN_PRIMARY = 33;    // Enable untuk Aliran Primer
const int EN_SECONDARY = 15;  // Enable untuk Aliran Sekunder
const int EN_TERTIARY = 2;    // Enable untuk Aliran Tersier

// Multiplexer signal pins (1 per flow)
const int SIG_PRIMARY = 32;   // PWM output untuk Aliran Primer
const int SIG_SECONDARY = 4;  // PWM output untuk Aliran Sekunder
const int SIG_TERTIARY = 16;  // PWM output untuk Aliran Tersier

// PWM settings for brightness control
const int PWM_FREQ = 5000;
const int PWM_RESOLUTION = 8;

// Function to select multiplexer channel
void setMux(int channel) {
    digitalWrite(S0, channel & 1);
    digitalWrite(S1, (channel >> 1) & 1);
    digitalWrite(S2, (channel >> 2) & 1);
    digitalWrite(S3, (channel >> 3) & 1);
}

// Function to set LED brightness for specific flow (0-255)
void setLEDBrightness(int flowIndex, int ledIndex, int brightness) {
    if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
        // Select LED channel (shared selector for all multiplexers)
        setMux(ledIndex);
        
        // Set brightness on specific flow's PWM output
        if (flowIndex == 0) {
            analogWrite(SIG_PRIMARY, brightness);
        } else if (flowIndex == 1) {
            analogWrite(SIG_SECONDARY, brightness);
        } else if (flowIndex == 2) {
            analogWrite(SIG_TERTIARY, brightness);
        }
    }
}

// Function to turn off all LEDs for specific flow
void turnOffAllLEDs(int flowIndex) {
    if (flowIndex == 0) {
        analogWrite(SIG_PRIMARY, 0);
    } else if (flowIndex == 1) {
        analogWrite(SIG_SECONDARY, 0);
    } else if (flowIndex == 2) {
        analogWrite(SIG_TERTIARY, 0);
    }
    setMux(15); // Set to unused channel
}

// Function to turn off all flows
void turnOffAllFlows() {
    for (int i = 0; i < NUM_FLOWS; i++) {
        turnOffAllLEDs(i);
    }
}

// ============================================
// Animation Variables - 3 Independent Flows
// ============================================
struct FlowData {
    float pressure;
    uint8_t pumpStatus;
    int animationPosition;
    unsigned long lastAnimationUpdate;
    unsigned long animationInterval;
    uint8_t animationSpeed;
};

FlowData flows[NUM_FLOWS] = {
    {0.0, 0, 0, 0, 200, 0},  // Primary
    {0.0, 0, 0, 0, 200, 0},  // Secondary
    {0.0, 0, 0, 0, 200, 0}   // Tertiary
};

const uint8_t LED_COUNT = NUM_LEDS;

// ============================================
// I2C Callback Functions (ISR - Keep Simple!)
// ============================================

void onReceiveData(int numBytes) {
    Serial.printf("[ISR] onReceive called: %d bytes\n", numBytes);
    
    if (numBytes <= 0 || numBytes > RECEIVE_SIZE) {
        Serial.printf("[ISR] Invalid numBytes: %d\n", numBytes);
        return;
    }
    
    for (int i = 0; i < numBytes; i++) {
        receiveBuffer[i] = Wire.read();
    }
    receiveLength = numBytes;
    newDataFlag = true;
    
    // Debug raw bytes
    Serial.print("[ISR] Raw bytes: ");
    for (int i = 0; i < numBytes; i++) {
        Serial.printf("%02X ", receiveBuffer[i]);
    }
    Serial.println();
}

void onRequestData() {
    Serial.printf("[ISR] onRequest called - Sending: %02X %02X\n", 
                  sendBuffer[0], sendBuffer[1]);
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
// LED Animation - Multiple Flowing Waves Effect
// ============================================

// Calculate brightness for a single LED based on multiple wave positions
int calculateBrightness(int ledIndex, int basePosition) {
    int maxBrightness = 0;
    
    // Check each wave
    for (int wave = 0; wave < NUM_WAVES; wave++) {
        // Calculate wave center position
        int waveCenter = (basePosition + wave * WAVE_SPACING) % NUM_LEDS;
        
        // Calculate distance from this LED to wave center
        int distance = abs(ledIndex - waveCenter);
        
        // Handle wrap-around for circular effect
        if (distance > NUM_LEDS / 2) {
            distance = NUM_LEDS - distance;
        }
        
        // Calculate brightness based on distance from wave center
        int brightness = 0;
        
        if (distance == 0) {
            brightness = 255;  // Brightest at center
        } else if (distance == 1) {
            brightness = 160;  // Medium-bright
        } else if (distance == 2) {
            brightness = 60;   // Dim (tail effect)
        } else {
            brightness = 0;    // Off
        }
        
        // Keep the maximum brightness if multiple waves overlap
        if (brightness > maxBrightness) {
            maxBrightness = brightness;
        }
    }
    
    return maxBrightness;
}

void updateAnimation() {
    // Update each flow independently
    for (int flowIndex = 0; flowIndex < NUM_FLOWS; flowIndex++) {
        FlowData &flow = flows[flowIndex];
        
        // Determine animation speed based on pump status
        switch (flow.pumpStatus) {
            case 0: // OFF
                flow.animationInterval = 0;
                flow.animationSpeed = 0;
                turnOffAllLEDs(flowIndex);
                continue; // Skip to next flow
                
            case 1: // STARTING
                flow.animationInterval = 80;
                flow.animationSpeed = 33;
                break;
                
            case 2: // ON
                flow.animationInterval = 40;
                flow.animationSpeed = 100;
                break;
                
            case 3: // SHUTTING_DOWN
                flow.animationInterval = 120;
                flow.animationSpeed = 20;
                break;
        }
        
        // Update animation position
        if (millis() - flow.lastAnimationUpdate >= flow.animationInterval) {
            flow.animationPosition++;
            if (flow.animationPosition >= NUM_LEDS) {
                flow.animationPosition = 0;
            }
            flow.lastAnimationUpdate = millis();
        }
        
        // Refresh LEDs for this flow
        for (int i = 0; i < NUM_LEDS; i++) {
            int brightness = calculateBrightness(i, flow.animationPosition);
            
            if (brightness > 0) {
                setLEDBrightness(flowIndex, i, brightness);
                delayMicroseconds(50); // Small delay for multiplexer
            }
        }
    }
}

// ============================================
// Setup
// ============================================

void setup() {
    Serial.begin(115200);
    delay(300);
    
    Serial.println("\nESP-E (Primary Flow Visualizer) I2C Slave Starting...");
    Serial.printf("I2C Address: 0x%02X\n", I2C_SLAVE_ADDRESS);
    Serial.printf("Expected data: 5 bytes (4 float + 1 uint8)\n");
    
    // Initialize all flows to zero
    for (int i = 0; i < NUM_FLOWS; i++) {
        flows[i].pressure = 0.0;
        flows[i].pumpStatus = 0;
        flows[i].animationPosition = 0;
        flows[i].lastAnimationUpdate = 0;
        flows[i].animationInterval = 200;
        flows[i].animationSpeed = 0;
    }
    
    // Initialize I2C as Slave
    Wire.begin(I2C_SLAVE_ADDRESS);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C Slave initialized at address 0x%02X\n", I2C_SLAVE_ADDRESS);
    Serial.println("Callbacks registered: onReceive & onRequest");
    
    // Initialize multiplexer selector pins (shared)
    pinMode(S0, OUTPUT);
    pinMode(S1, OUTPUT);
    pinMode(S2, OUTPUT);
    pinMode(S3, OUTPUT);
    
    // Initialize enable pins (1 per flow)
    pinMode(EN_PRIMARY, OUTPUT);
    pinMode(EN_SECONDARY, OUTPUT);
    pinMode(EN_TERTIARY, OUTPUT);
    
    // Initialize signal pins (1 per flow)
    pinMode(SIG_PRIMARY, OUTPUT);
    pinMode(SIG_SECONDARY, OUTPUT);
    pinMode(SIG_TERTIARY, OUTPUT);
    
    // Setup PWM for brightness control (ESP32 Core 3.x)
    analogWriteResolution(SIG_PRIMARY, PWM_RESOLUTION);
    analogWriteFrequency(SIG_PRIMARY, PWM_FREQ);
    analogWriteResolution(SIG_SECONDARY, PWM_RESOLUTION);
    analogWriteFrequency(SIG_SECONDARY, PWM_FREQ);
    analogWriteResolution(SIG_TERTIARY, PWM_RESOLUTION);
    analogWriteFrequency(SIG_TERTIARY, PWM_FREQ);
    
    // Enable all multiplexers (EN = LOW to enable)
    digitalWrite(EN_PRIMARY, LOW);
    digitalWrite(EN_SECONDARY, LOW);
    digitalWrite(EN_TERTIARY, LOW);
    
    turnOffAllFlows();  // Turn off all LEDs initially
    
    Serial.println("3-Flow Multiplexer System initialized with PWM control");
    
    // Startup animation - test all 3 flows sequentially
    Serial.println("Running startup animation...");
    for (int flowIndex = 0; flowIndex < NUM_FLOWS; flowIndex++) {
        Serial.printf("Testing Flow %d...\n", flowIndex + 1);
        for (int pos = 0; pos < NUM_LEDS; pos++) {
            for (int i = 0; i < NUM_LEDS; i++) {
                int brightness = calculateBrightness(i, pos);
                if (brightness > 0) {
                    setLEDBrightness(flowIndex, i, brightness);
                    delayMicroseconds(80);
                }
            }
            delay(30);
        }
        turnOffAllLEDs(flowIndex);
        delay(200);
    }
    
    Serial.println("Startup animation complete!");
    
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
        
        Serial.printf("[LOOP] Processing %d bytes\n", receiveLength);
        Serial.print("[LOOP] Buffer: ");
        for (int i = 0; i < receiveLength; i++) {
            Serial.printf("%02X ", buf[i]);
        }
        Serial.println();
        
        // Parse received data for 3 flows
        // Skip first byte (register address from Python), data starts at buf[1]
        int dataStart = (receiveLength == 16) ? 1 : 0;  // Auto-detect format
        
        // Parse Primary flow (bytes 0-4)
        memcpy(&flows[0].pressure, &buf[dataStart], 4);
        flows[0].pumpStatus = buf[dataStart + 4];
        
        // Parse Secondary flow (bytes 5-9)
        memcpy(&flows[1].pressure, &buf[dataStart + 5], 4);
        flows[1].pumpStatus = buf[dataStart + 9];
        
        // Parse Tertiary flow (bytes 10-14)
        memcpy(&flows[2].pressure, &buf[dataStart + 10], 4);
        flows[2].pumpStatus = buf[dataStart + 14];
        
        // Debug output
        Serial.printf("[LOOP] Primary: %.1f bar | Status: %d\n", 
                      flows[0].pressure, flows[0].pumpStatus);
        Serial.printf("[LOOP] Secondary: %.1f bar | Status: %d\n", 
                      flows[1].pressure, flows[1].pumpStatus);
        Serial.printf("[LOOP] Tertiary: %.1f bar | Status: %d\n", 
                      flows[2].pressure, flows[2].pumpStatus);
    }
    
    // Update animation
    updateAnimation();
    
    // Prepare data to send
    prepareSendData();
    
    // Prevent watchdog reset
    delay(2);
    
    // Heartbeat every 5 seconds
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat >= 5000) {
        Serial.printf("[HEARTBEAT] P:%d S:%d T:%d\n", 
                      flows[0].pumpStatus, flows[1].pumpStatus, flows[2].pumpStatus);
        lastHeartbeat = millis();
    }
}
