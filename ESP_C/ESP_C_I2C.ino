/*
 * ESP-C I2C Slave - Turbin & Generator
 * 
 * I2C Slave Address: 0x09
 * 
 * Receives from Raspberry Pi:
 * - Rod 1 Position (uint8, 1 byte) 0-100%
 * - Rod 2 Position (uint8, 1 byte) 0-100%
 * - Rod 3 Position (uint8, 1 byte) 0-100%
 * Total: 3 bytes
 * 
 * Sends to Raspberry Pi:
 * - Power Level (float, 4 bytes) 0-100%
 * - State (uint32, 4 bytes) State machine state
 * - Generator Status (uint8, 1 byte)
 * - Turbine Status (uint8, 1 byte)
 * Total: 10 bytes
 */

#include <Wire.h>

// ============================================
// I2C Slave Configuration
// ============================================
#define I2C_SLAVE_ADDRESS 0x09
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// I2C Data Buffers
#define RECEIVE_BUFFER_SIZE 32
#define SEND_BUFFER_SIZE 32

volatile uint8_t receiveBuffer[RECEIVE_BUFFER_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFromMaster = false;

uint8_t sendBuffer[SEND_BUFFER_SIZE];
uint8_t sendLength = 0;

// ============================================
// Hardware Configuration
// ============================================
// Relay & Motor Pins
#define RELAY_STEAM_GEN 25
#define RELAY_TURBINE 26
#define RELAY_CONDENSER 27
#define RELAY_COOLING_TOWER 14

#define MOTOR_STEAM_GEN_PIN 12
#define MOTOR_TURBINE_PIN 13
#define MOTOR_CONDENSER_PIN 32
#define MOTOR_COOLING_PIN 33

// ============================================
// State Machine
// ============================================
enum SystemState {
    STATE_IDLE = 0,
    STATE_STARTING_UP = 1,
    STATE_RUNNING = 2,
    STATE_SHUTTING_DOWN = 3
};

SystemState currentState = STATE_IDLE;

// ============================================
// System Variables
// ============================================
struct {
    uint8_t rod1Pos;
    uint8_t rod2Pos;
    uint8_t rod3Pos;
} masterData;

float powerLevel = 0.0;
uint8_t generatorStatus = 0;
uint8_t turbineStatus = 0;

unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 100;

// ============================================
// I2C Callback Functions
// ============================================

void onReceiveData(int numBytes) {
    receiveLength = 0;
    while (Wire.available() && receiveLength < RECEIVE_BUFFER_SIZE) {
        receiveBuffer[receiveLength++] = Wire.read();
    }
    newDataFromMaster = true;
}

void onRequestData() {
    Wire.write(sendBuffer, sendLength);
}

// ============================================
// Data Processing
// ============================================

void parseReceivedData() {
    if (receiveLength >= 3) {
        masterData.rod1Pos = receiveBuffer[0];
        masterData.rod2Pos = receiveBuffer[1];
        masterData.rod3Pos = receiveBuffer[2];
    }
}

void prepareSendData() {
    sendLength = 0;
    
    // Power Level (float, 4 bytes)
    memcpy(&sendBuffer[sendLength], &powerLevel, 4);
    sendLength += 4;
    
    // State (uint32, 4 bytes)
    uint32_t state = (uint32_t)currentState;
    memcpy(&sendBuffer[sendLength], &state, 4);
    sendLength += 4;
    
    // Generator & Turbine Status (2 bytes)
    sendBuffer[sendLength++] = generatorStatus;
    sendBuffer[sendLength++] = turbineStatus;
}

// ============================================
// Control Functions
// ============================================

void updateStateMachine() {
    // Calculate average rod position
    float avgRodPos = (masterData.rod1Pos + masterData.rod2Pos + masterData.rod3Pos) / 3.0;
    
    // Target power level from rod positions
    float targetPower = avgRodPos;
    
    switch (currentState) {
        case STATE_IDLE:
            if (targetPower > 10.0) {
                currentState = STATE_STARTING_UP;
                Serial.println("Starting up...");
            }
            powerLevel = 0.0;
            break;
            
        case STATE_STARTING_UP:
            // Gradual power increase
            if (powerLevel < targetPower) {
                powerLevel += 2.0;
                if (powerLevel >= targetPower) {
                    currentState = STATE_RUNNING;
                    Serial.println("Running");
                }
            }
            break;
            
        case STATE_RUNNING:
            // Track target power
            if (targetPower < 5.0) {
                currentState = STATE_SHUTTING_DOWN;
                Serial.println("Shutting down...");
            } else {
                powerLevel = targetPower;
            }
            break;
            
        case STATE_SHUTTING_DOWN:
            // Gradual power decrease
            if (powerLevel > 0.0) {
                powerLevel -= 2.0;
                if (powerLevel <= 0.0) {
                    powerLevel = 0.0;
                    currentState = STATE_IDLE;
                    Serial.println("Idle");
                }
            }
            break;
    }
    
    // Clamp power level
    if (powerLevel < 0.0) powerLevel = 0.0;
    if (powerLevel > 100.0) powerLevel = 100.0;
}

void updateOutputs() {
    // Control relays and motors based on power level
    
    if (powerLevel > 20.0) {
        // Steam Generator
        digitalWrite(RELAY_STEAM_GEN, HIGH);
        analogWrite(MOTOR_STEAM_GEN_PIN, map(powerLevel, 0, 100, 0, 255));
        generatorStatus = 1;
    } else {
        digitalWrite(RELAY_STEAM_GEN, LOW);
        analogWrite(MOTOR_STEAM_GEN_PIN, 0);
        generatorStatus = 0;
    }
    
    if (powerLevel > 30.0) {
        // Turbine
        digitalWrite(RELAY_TURBINE, HIGH);
        analogWrite(MOTOR_TURBINE_PIN, map(powerLevel, 0, 100, 0, 255));
        turbineStatus = 1;
    } else {
        digitalWrite(RELAY_TURBINE, LOW);
        analogWrite(MOTOR_TURBINE_PIN, 0);
        turbineStatus = 0;
    }
    
    if (powerLevel > 20.0) {
        // Condenser
        digitalWrite(RELAY_CONDENSER, HIGH);
        analogWrite(MOTOR_CONDENSER_PIN, map(powerLevel, 0, 100, 0, 255));
    } else {
        digitalWrite(RELAY_CONDENSER, LOW);
        analogWrite(MOTOR_CONDENSER_PIN, 0);
    }
    
    if (powerLevel > 15.0) {
        // Cooling Tower
        digitalWrite(RELAY_COOLING_TOWER, HIGH);
        analogWrite(MOTOR_COOLING_PIN, map(powerLevel, 0, 100, 0, 255));
    } else {
        digitalWrite(RELAY_COOLING_TOWER, LOW);
        analogWrite(MOTOR_COOLING_PIN, 0);
    }
}

// ============================================
// Setup
// ============================================

void setup() {
    Serial.begin(115200);
    Serial.println("ESP-C I2C Slave Starting...");
    
    // Initialize I2C as Slave
    Wire.begin(I2C_SLAVE_ADDRESS, I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C Slave initialized at address 0x%02X\n", I2C_SLAVE_ADDRESS);
    
    // Initialize relay pins
    pinMode(RELAY_STEAM_GEN, OUTPUT);
    pinMode(RELAY_TURBINE, OUTPUT);
    pinMode(RELAY_CONDENSER, OUTPUT);
    pinMode(RELAY_COOLING_TOWER, OUTPUT);
    
    // Initialize motor pins
    pinMode(MOTOR_STEAM_GEN_PIN, OUTPUT);
    pinMode(MOTOR_TURBINE_PIN, OUTPUT);
    pinMode(MOTOR_CONDENSER_PIN, OUTPUT);
    pinMode(MOTOR_COOLING_PIN, OUTPUT);
    
    // Turn everything off initially
    digitalWrite(RELAY_STEAM_GEN, LOW);
    digitalWrite(RELAY_TURBINE, LOW);
    digitalWrite(RELAY_CONDENSER, LOW);
    digitalWrite(RELAY_COOLING_TOWER, LOW);
    
    Serial.println("ESP-C Ready!");
}

// ============================================
// Loop
// ============================================

void loop() {
    // Process received data
    if (newDataFromMaster) {
        noInterrupts();
        parseReceivedData();
        newDataFromMaster = false;
        interrupts();
    }
    
    // Update state machine
    if (millis() - lastUpdate >= UPDATE_INTERVAL) {
        updateStateMachine();
        updateOutputs();
        prepareSendData();
        lastUpdate = millis();
        
        // Debug output
        Serial.printf("Rods: %d,%d,%d | Power: %.1f%% | State: %d\n",
                      masterData.rod1Pos, masterData.rod2Pos, masterData.rod3Pos,
                      powerLevel, currentState);
    }
}
