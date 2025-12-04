/*
 * ESP-C I2C Slave - Turbine, Generator & Humidifier Control
 * 
 * I2C Slave Address: 0x09
 * 
 * UPDATED PROTOCOL FOR HUMIDIFIER CONTROL:
 * 
 * Receives from Raspberry Pi (11 bytes):
 * - Rod 1 Position (uint8, 1 byte) - Safety Rod 0-100%
 * - Rod 2 Position (uint8, 1 byte) - Shim Rod 0-100%
 * - Rod 3 Position (uint8, 1 byte) - Regulating Rod 0-100%
 * - Thermal Power kW (float, 4 bytes) - From ESP-B
 * - Humidifier Steam Gen Command (uint8, 1 byte) - 0=OFF, 1=ON
 * - Humidifier Cooling Tower Command (uint8, 1 byte) - 0=OFF, 1=ON
 * Total: 11 bytes
 * 
 * Sends to Raspberry Pi (12 bytes):
 * - Power Level (float, 4 bytes) 0-100%
 * - State (uint32, 4 bytes) State machine state
 * - Generator Status (uint8, 1 byte)
 * - Turbine Status (uint8, 1 byte)
 * - Humidifier Steam Gen Status (uint8, 1 byte)
 * - Humidifier Cooling Tower Status (uint8, 1 byte)
 * Total: 12 bytes
 */

#include <Wire.h>

// ============================================
// I2C Slave Configuration
// ============================================
#define I2C_SLAVE_ADDRESS 0x09

// I2C Data Buffers - UPDATED SIZE
#define RECEIVE_SIZE 12  // Was 3, now 12 (11 data + 1 register)
#define SEND_SIZE 12     // Was 10, now 12

volatile uint8_t receiveBuffer[RECEIVE_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFlag = false;

uint8_t sendBuffer[SEND_SIZE];

// ============================================
// Hardware Configuration
// ============================================
// Relay Pins
#define RELAY_STEAM_GEN 25              // Main steam generator (turbine steam)
#define RELAY_TURBINE 26                // Turbine
#define RELAY_CONDENSER 27              // Condenser
#define RELAY_COOLING_TOWER 14          // Cooling tower (was used for tower, now free)

// NEW: Humidifier Relay Pins
#define RELAY_HUMIDIFIER_STEAM_GEN 32   // Humidifier di Steam Generator
#define RELAY_HUMIDIFIER_COOLING_TOWER 33  // Humidifier di Cooling Tower

// Motor PWM Pins
#define MOTOR_STEAM_GEN_PIN 12
#define MOTOR_TURBINE_PIN 13
#define MOTOR_CONDENSER_PIN 15
#define MOTOR_COOLING_PIN 4

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
    uint8_t rod1Pos;      // Safety Rod
    uint8_t rod2Pos;      // Shim Rod
    uint8_t rod3Pos;      // Regulating Rod
    float thermalPowerKW; // Thermal power from ESP-B
    uint8_t humidifierSteamGenCmd;     // Command from RasPi
    uint8_t humidifierCoolingTowerCmd; // Command from RasPi
} masterData;

float powerLevel = 0.0;
uint8_t generatorStatus = 0;
uint8_t turbineStatus = 0;
uint8_t humidifierSteamGenStatus = 0;      // NEW
uint8_t humidifierCoolingTowerStatus = 0;  // NEW

unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 100;

// ============================================
// I2C Callback Functions
// ============================================

void onReceiveData(int numBytes) {
    if (numBytes <= 0 || numBytes > RECEIVE_SIZE) {
        Serial.printf("Invalid numBytes: %d\n", numBytes);
        return;
    }
    
    for (int i = 0; i < numBytes; i++) {
        receiveBuffer[i] = Wire.read();
    }
    receiveLength = numBytes;
    newDataFlag = true;
    
    // Debug
    Serial.print("Received: ");
    for (int i = 0; i < numBytes; i++) {
        Serial.printf("%02X ", receiveBuffer[i]);
    }
    Serial.println();
}

void onRequestData() {
    Wire.write(sendBuffer, SEND_SIZE);
}

// ============================================
// Data Processing
// ============================================

void prepareSendData() {
    // Power Level (float, 4 bytes)
    memcpy(&sendBuffer[0], &powerLevel, 4);
    
    // State (uint32, 4 bytes)
    uint32_t state = (uint32_t)currentState;
    memcpy(&sendBuffer[4], &state, 4);
    
    // Status bytes
    sendBuffer[8] = generatorStatus;
    sendBuffer[9] = turbineStatus;
    sendBuffer[10] = humidifierSteamGenStatus;         // NEW
    sendBuffer[11] = humidifierCoolingTowerStatus;     // NEW
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
                Serial.println("State: STARTING_UP");
            }
            powerLevel = 0.0;
            break;
            
        case STATE_STARTING_UP:
            // Gradual power increase
            if (powerLevel < targetPower) {
                powerLevel += 2.0;
                if (powerLevel >= targetPower) {
                    currentState = STATE_RUNNING;
                    Serial.println("State: RUNNING");
                }
            }
            break;
            
        case STATE_RUNNING:
            // Track target power
            if (targetPower < 5.0) {
                currentState = STATE_SHUTTING_DOWN;
                Serial.println("State: SHUTTING_DOWN");
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
                    Serial.println("State: IDLE");
                }
            }
            break;
    }
    
    // Clamp power level
    if (powerLevel < 0.0) powerLevel = 0.0;
    if (powerLevel > 100.0) powerLevel = 100.0;
}

void updateOutputs() {
    // ========================================
    // Main Power Generation Components
    // ========================================
    
    // Steam Generator (main turbine steam)
    if (powerLevel > 20.0) {
        digitalWrite(RELAY_STEAM_GEN, HIGH);
        analogWrite(MOTOR_STEAM_GEN_PIN, map(powerLevel, 0, 100, 0, 255));
        generatorStatus = 1;
    } else {
        digitalWrite(RELAY_STEAM_GEN, LOW);
        analogWrite(MOTOR_STEAM_GEN_PIN, 0);
        generatorStatus = 0;
    }
    
    // Turbine
    if (powerLevel > 30.0) {
        digitalWrite(RELAY_TURBINE, HIGH);
        analogWrite(MOTOR_TURBINE_PIN, map(powerLevel, 0, 100, 0, 255));
        turbineStatus = 1;
    } else {
        digitalWrite(RELAY_TURBINE, LOW);
        analogWrite(MOTOR_TURBINE_PIN, 0);
        turbineStatus = 0;
    }
    
    // Condenser
    if (powerLevel > 20.0) {
        digitalWrite(RELAY_CONDENSER, HIGH);
        analogWrite(MOTOR_CONDENSER_PIN, map(powerLevel, 0, 100, 0, 255));
    } else {
        digitalWrite(RELAY_CONDENSER, LOW);
        analogWrite(MOTOR_CONDENSER_PIN, 0);
    }
    
    // Cooling Tower (main cooling)
    if (powerLevel > 15.0) {
        digitalWrite(RELAY_COOLING_TOWER, HIGH);
        analogWrite(MOTOR_COOLING_PIN, map(powerLevel, 0, 100, 0, 255));
    } else {
        digitalWrite(RELAY_COOLING_TOWER, LOW);
        analogWrite(MOTOR_COOLING_PIN, 0);
    }
    
    // ========================================
    // HUMIDIFIER CONTROL (NEW!)
    // ========================================
    
    // Humidifier di Steam Generator
    // Command dari Raspberry Pi berdasarkan Shim + Regulating Rod
    if (masterData.humidifierSteamGenCmd == 1) {
        digitalWrite(RELAY_HUMIDIFIER_STEAM_GEN, HIGH);
        humidifierSteamGenStatus = 1;
        Serial.println("Humidifier Steam Gen: ON");
    } else {
        digitalWrite(RELAY_HUMIDIFIER_STEAM_GEN, LOW);
        humidifierSteamGenStatus = 0;
    }
    
    // Humidifier di Cooling Tower
    // Command dari Raspberry Pi berdasarkan Thermal Power (kW)
    if (masterData.humidifierCoolingTowerCmd == 1) {
        digitalWrite(RELAY_HUMIDIFIER_COOLING_TOWER, HIGH);
        humidifierCoolingTowerStatus = 1;
        Serial.println("Humidifier Cooling Tower: ON");
    } else {
        digitalWrite(RELAY_HUMIDIFIER_COOLING_TOWER, LOW);
        humidifierCoolingTowerStatus = 0;
    }
}

// ============================================
// Setup
// ============================================

void setup() {
    Serial.begin(115200);
    delay(300);
    
    Serial.println("\n================================");
    Serial.println("ESP-C I2C Slave + Humidifier Control");
    Serial.println("================================");
    
    // Initialize I2C as Slave
    Wire.begin(I2C_SLAVE_ADDRESS);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C: Address 0x%02X\n", I2C_SLAVE_ADDRESS);
    Serial.printf("Receive: %d bytes\n", RECEIVE_SIZE);
    Serial.printf("Send: %d bytes\n", SEND_SIZE);
    
    // Initialize main relay pins
    pinMode(RELAY_STEAM_GEN, OUTPUT);
    pinMode(RELAY_TURBINE, OUTPUT);
    pinMode(RELAY_CONDENSER, OUTPUT);
    pinMode(RELAY_COOLING_TOWER, OUTPUT);
    
    // Initialize humidifier relay pins (NEW)
    pinMode(RELAY_HUMIDIFIER_STEAM_GEN, OUTPUT);
    pinMode(RELAY_HUMIDIFIER_COOLING_TOWER, OUTPUT);
    
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
    digitalWrite(RELAY_HUMIDIFIER_STEAM_GEN, LOW);
    digitalWrite(RELAY_HUMIDIFIER_COOLING_TOWER, LOW);
    
    analogWrite(MOTOR_STEAM_GEN_PIN, 0);
    analogWrite(MOTOR_TURBINE_PIN, 0);
    analogWrite(MOTOR_CONDENSER_PIN, 0);
    analogWrite(MOTOR_COOLING_PIN, 0);
    
    Serial.println("Hardware initialized");
    Serial.println("Waiting for Raspberry Pi...\n");
}

// ============================================
// Loop
// ============================================

void loop() {
    // Process received data
    if (newDataFlag) {
        newDataFlag = false;
        
        // Copy to local buffer
        uint8_t buf[RECEIVE_SIZE];
        memcpy(buf, (const void*)receiveBuffer, RECEIVE_SIZE);
        
        // Parse data (skip first byte if it's register address)
        int offset = (receiveLength == 12) ? 1 : 0;
        
        // Parse 11 bytes of data
        masterData.rod1Pos = buf[offset + 0];
        masterData.rod2Pos = buf[offset + 1];
        masterData.rod3Pos = buf[offset + 2];
        memcpy(&masterData.thermalPowerKW, &buf[offset + 3], 4);
        masterData.humidifierSteamGenCmd = buf[offset + 7];
        masterData.humidifierCoolingTowerCmd = buf[offset + 8];
        
        // Debug
        Serial.printf("Rods: S=%d%% H=%d%% R=%d%% | Thermal: %.1f kW | Humid: SG=%d CT=%d\n",
            masterData.rod1Pos, masterData.rod2Pos, masterData.rod3Pos,
            masterData.thermalPowerKW,
            masterData.humidifierSteamGenCmd,
            masterData.humidifierCoolingTowerCmd
        );
    }
    
    // Update system periodically
    if (millis() - lastUpdate >= UPDATE_INTERVAL) {
        lastUpdate = millis();
        
        updateStateMachine();
        updateOutputs();
        prepareSendData();
    }
    
    delay(10);
}
