/*
 * ESP-B I2C Slave - Batang Kendali & Reaktor Core
 * 
 * I2C Slave Address: 0x08
 * 
 * Receives from Raspberry Pi:
 * - Pressure (float, 4 bytes)
 * - Reserved (float, 4 bytes)
 * - Pump Primary Status (uint8, 1 byte)
 * - Pump Secondary Status (uint8, 1 byte)
 * Total: 10 bytes
 * 
 * Sends to Raspberry Pi:
 * - Rod 1 Position (uint8, 1 byte) 0-100%
 * - Rod 2 Position (uint8, 1 byte) 0-100%
 * - Rod 3 Position (uint8, 1 byte) 0-100%
 * - Reserved (uint8, 1 byte)
 * - kwThermal (float, 4 bytes)
 * - Reserved (float, 4 bytes)
 * - Reserved (float, 4 bytes)
 * Total: 16 bytes
 */

#include <Wire.h>
#include <ESP32Servo.h>
#include <Adafruit_SSD1306.h>

// ============================================
// I2C Slave Configuration
// ============================================
#define I2C_SLAVE_ADDRESS 0x08
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
#define PCA9548A_ADDRESS 0x70
#define OLED_ADDRESS 0x3C
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32

// Servo Pins
#define ROD1_SERVO_PIN 13
#define ROD2_SERVO_PIN 14
#define ROD3_SERVO_PIN 15

// Button Pins
const int btnUp1 = 0;
const int btnDown1 = 5;
const int btnUp2 = 4;
const int btnDown2 = 2;
const int btnUp3 = 12;
const int btnDown3 = 23;
const int btnEmergency = 19;
const int buzzerPin = 18;

// ============================================
// Global Objects
// ============================================
Servo servo1, servo2, servo3;
Adafruit_SSD1306 oled1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled3(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oledKwThermal(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

bool oledInitialized[4] = {false, false, false, false};

// ============================================
// System State Variables
// ============================================
// Rod positions (0-100%)
int pos1 = 0, pos2 = 0, pos3 = 0;
float kwThermal = 0.0;

// Emergency state
bool emergencyTriggered = false;

// Received data from Master (Raspberry Pi)
struct {
    float pressure;
    float reserved1;
    uint8_t pumpPrimaryStatus;
    uint8_t pumpSecondaryStatus;
} masterData;

// Timing
unsigned long lastOLEDUpdate = 0;
const unsigned long OLEDRate = 200;

// ============================================
// I2C Callback Functions
// ============================================

void onReceiveData(int numBytes) {
    // Called when Master writes data to this slave
    // IMPORTANT: Keep this function SHORT and FAST (interrupt context)
    
    receiveLength = 0;
    while (Wire.available() && receiveLength < RECEIVE_BUFFER_SIZE) {
        receiveBuffer[receiveLength++] = Wire.read();
    }
    newDataFromMaster = true;
}

void onRequestData() {
    // Called when Master requests data from this slave
    // IMPORTANT: Keep this function SHORT and FAST (interrupt context)
    
    Wire.write(sendBuffer, sendLength);
}

// ============================================
// Data Processing Functions
// ============================================

void parseReceivedData() {
    if (receiveLength >= 10) {
        // Parse: float + float + uint8 + uint8
        memcpy(&masterData.pressure, &receiveBuffer[0], 4);
        memcpy(&masterData.reserved1, &receiveBuffer[4], 4);
        masterData.pumpPrimaryStatus = receiveBuffer[8];
        masterData.pumpSecondaryStatus = receiveBuffer[9];
    }
}

void prepareSendData() {
    // Pack data to send to Master
    sendLength = 0;
    
    // Rod positions (3 bytes)
    sendBuffer[sendLength++] = (uint8_t)pos1;
    sendBuffer[sendLength++] = (uint8_t)pos2;
    sendBuffer[sendLength++] = (uint8_t)pos3;
    sendBuffer[sendLength++] = 0; // Reserved
    
    // kwThermal (4 bytes)
    memcpy(&sendBuffer[sendLength], &kwThermal, 4);
    sendLength += 4;
    
    // Reserved (8 bytes)
    float reserved = 0.0f;
    memcpy(&sendBuffer[sendLength], &reserved, 4);
    sendLength += 4;
    memcpy(&sendBuffer[sendLength], &reserved, 4);
    sendLength += 4;
}

// ============================================
// Interlock Logic
// ============================================

bool isInterlockSatisfied() {
    // Rods can only move if:
    // 1. Pressure >= 40 bar
    // 2. Primary pump ON (status = 2)
    // 3. Secondary pump ON (status = 2)
    
    if (masterData.pressure < 40.0) return false;
    if (masterData.pumpPrimaryStatus != 2) return false;
    if (masterData.pumpSecondaryStatus != 2) return false;
    
    return true;
}

// ============================================
// PCA9548A Functions
// ============================================

void selectPCA9548AChannel(uint8_t channel) {
    if (channel > 7) return;
    Wire.beginTransmission(PCA9548A_ADDRESS);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

// ============================================
// OLED Functions
// ============================================

void initializeOLEDs() {
    for (int i = 0; i < 4; i++) {
        selectPCA9548AChannel(i);
        delay(10);
        
        Adafruit_SSD1306* oled = nullptr;
        if (i == 0) oled = &oled1;
        else if (i == 1) oled = &oled2;
        else if (i == 2) oled = &oled3;
        else if (i == 3) oled = &oledKwThermal;
        
        if (oled && oled->begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
            oled->clearDisplay();
            oled->setTextSize(1);
            oled->setTextColor(SSD1306_WHITE);
            oled->display();
            oledInitialized[i] = true;
        }
    }
}

void updateOLEDs() {
    if (millis() - lastOLEDUpdate < OLEDRate) return;
    lastOLEDUpdate = millis();
    
    // OLED 1: Rod 1
    if (oledInitialized[0]) {
        selectPCA9548AChannel(0);
        oled1.clearDisplay();
        oled1.setCursor(0, 0);
        oled1.println("ROD 1");
        oled1.setTextSize(2);
        oled1.print(pos1);
        oled1.println("%");
        oled1.display();
        oled1.setTextSize(1);
    }
    
    // OLED 2: Rod 2
    if (oledInitialized[1]) {
        selectPCA9548AChannel(1);
        oled2.clearDisplay();
        oled2.setCursor(0, 0);
        oled2.println("ROD 2");
        oled2.setTextSize(2);
        oled2.print(pos2);
        oled2.println("%");
        oled2.display();
        oled2.setTextSize(1);
    }
    
    // OLED 3: Rod 3
    if (oledInitialized[2]) {
        selectPCA9548AChannel(2);
        oled3.clearDisplay();
        oled3.setCursor(0, 0);
        oled3.println("ROD 3");
        oled3.setTextSize(2);
        oled3.print(pos3);
        oled3.println("%");
        oled3.display();
        oled3.setTextSize(1);
    }
    
    // OLED 4: kwThermal
    if (oledInitialized[3]) {
        selectPCA9548AChannel(3);
        oledKwThermal.clearDisplay();
        oledKwThermal.setCursor(0, 0);
        oledKwThermal.println("THERMAL");
        oledKwThermal.setTextSize(2);
        oledKwThermal.print(kwThermal, 1);
        oledKwThermal.println("kW");
        oledKwThermal.display();
        oledKwThermal.setTextSize(1);
    }
}

// ============================================
// Setup
// ============================================

void setup() {
    Serial.begin(115200);
    Serial.println("ESP-B I2C Slave Starting...");
    
    // Initialize I2C as Slave
    Wire.begin(I2C_SLAVE_ADDRESS, I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.onReceive(onReceiveData);
    Wire.onRequest(onRequestData);
    Serial.printf("I2C Slave initialized at address 0x%02X\n", I2C_SLAVE_ADDRESS);
    
    // Initialize buttons
    pinMode(btnUp1, INPUT_PULLUP);
    pinMode(btnDown1, INPUT_PULLUP);
    pinMode(btnUp2, INPUT_PULLUP);
    pinMode(btnDown2, INPUT_PULLUP);
    pinMode(btnUp3, INPUT_PULLUP);
    pinMode(btnDown3, INPUT_PULLUP);
    pinMode(btnEmergency, INPUT_PULLUP);
    pinMode(buzzerPin, OUTPUT);
    
    // Initialize servos
    servo1.attach(ROD1_SERVO_PIN);
    servo2.attach(ROD2_SERVO_PIN);
    servo3.attach(ROD3_SERVO_PIN);
    
    servo1.write(0);
    servo2.write(0);
    servo3.write(0);
    
    // Initialize OLEDs
    delay(100);
    initializeOLEDs();
    
    Serial.println("ESP-B Ready!");
}

// ============================================
// Loop
// ============================================

void loop() {
    // Process received data from Master
    if (newDataFromMaster) {
        noInterrupts();
        parseReceivedData();
        newDataFromMaster = false;
        interrupts();
    }
    
    // Check emergency button
    if (digitalRead(btnEmergency) == LOW) {
        emergencyTriggered = true;
        pos1 = pos2 = pos3 = 0;
        servo1.write(0);
        servo2.write(0);
        servo3.write(0);
        digitalWrite(buzzerPin, HIGH);
        delay(1000);
        digitalWrite(buzzerPin, LOW);
        Serial.println("EMERGENCY TRIGGERED!");
    }
    
    // Check interlock
    bool interlockOK = isInterlockSatisfied();
    
    // Rod control (only if interlock satisfied)
    if (interlockOK && !emergencyTriggered) {
        // Rod 1
        if (digitalRead(btnUp1) == LOW && pos1 < 100) {
            pos1++;
            servo1.write(map(pos1, 0, 100, 0, 180));
            delay(50);
        }
        if (digitalRead(btnDown1) == LOW && pos1 > 0) {
            pos1--;
            servo1.write(map(pos1, 0, 100, 0, 180));
            delay(50);
        }
        
        // Rod 2
        if (digitalRead(btnUp2) == LOW && pos2 < 100) {
            pos2++;
            servo2.write(map(pos2, 0, 100, 0, 180));
            delay(50);
        }
        if (digitalRead(btnDown2) == LOW && pos2 > 0) {
            pos2--;
            servo2.write(map(pos2, 0, 100, 0, 180));
            delay(50);
        }
        
        // Rod 3
        if (digitalRead(btnUp3) == LOW && pos3 < 100) {
            pos3++;
            servo3.write(map(pos3, 0, 100, 0, 180));
            delay(50);
        }
        if (digitalRead(btnDown3) == LOW && pos3 > 0) {
            pos3--;
            servo3.write(map(pos3, 0, 100, 0, 180));
            delay(50);
        }
    }
    
    // Calculate kwThermal (simplified formula)
    kwThermal = (pos1 + pos2 + pos3) / 3.0 * 10.0;
    
    // Prepare data to send to Master
    prepareSendData();
    
    // Update OLED displays
    updateOLEDs();
}
