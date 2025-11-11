"""
ESP-B I2C Slave Implementation Template
Menggantikan komunikasi UART dengan I2C Slave

Address: 0x08
Role: Batang Kendali & Reaktor Core

Data Structure:
- Receive (8 bytes): pressure(float), reserved(float), pump1(uint8), pump2(uint8)
- Send (16 bytes): rod1(uint8), rod2(uint8), rod3(uint8), reserved(uint8), kwThermal(float), reserved(float×2)
"""

#include <Wire.h>
#include <ESP32Servo.h>
#include <Adafruit_SSD1306.h>

// ============================================
// I2C Slave Configuration
// ============================================
#define I2C_SLAVE_ADDRESS 0x08
#define I2C_SDA_PIN 21  // Default SDA untuk Wire (I2C0)
#define I2C_SCL_PIN 22  // Default SCL untuk Wire (I2C0)

// Data buffers
#define RECEIVE_BUFFER_SIZE 32
#define SEND_BUFFER_SIZE 32

volatile uint8_t receiveBuffer[RECEIVE_BUFFER_SIZE];
volatile uint8_t receiveLength = 0;
volatile bool newDataFromMaster = false;

uint8_t sendBuffer[SEND_BUFFER_SIZE];
uint8_t sendLength = 0;

// Parsed data dari Master (Raspberry Pi)
struct MasterData {
    float pressure;
    float reserved1;
    uint8_t pump1Status;
    uint8_t pump2Status;
} masterData;

// Data yang akan dikirim ke Master
struct SlaveData {
    uint8_t rod1Pos;
    uint8_t rod2Pos;
    uint8_t rod3Pos;
    uint8_t reserved1;
    float kwThermal;
    float reserved2;
    float reserved3;
} slaveData;

// ============================================
// Hardware Definitions (sama seperti sebelumnya)
// ============================================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_ADDRESS 0x3C
#define PCA9548A_ADDRESS 0x70

#define ROD1_SERVO_PIN 13
#define ROD2_SERVO_PIN 14
#define ROD3_SERVO_PIN 15

const int btnUp1 = 0;
const int btnDown1 = 5;
const int btnUp2 = 4;
const int btnDown2 = 2;
const int btnUp3 = 12;
const int btnDown3 = 23;
const int btnEmergency = 19;
const int buzzerPin = 18;

Servo servo1, servo2, servo3;
Adafruit_SSD1306 oled1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled3(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oledKwThermal(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Global variables
int pos1 = 0, pos2 = 0, pos3 = 0;
float kwThermal = 0.0;
bool emergencyTriggered = false;

// ============================================
// I2C Callback Functions
// ============================================

// Callback ketika Master menulis data ke Slave
void onReceiveData(int numBytes) {
    // IMPORTANT: Fungsi ini berjalan di interrupt context
    // Jangan gunakan delay(), Serial.print(), atau operasi berat lainnya
    
    receiveLength = 0;
    while (Wire.available() && receiveLength < RECEIVE_BUFFER_SIZE) {
        receiveBuffer[receiveLength++] = Wire.read();
    }
    
    newDataFromMaster = true;
}

// Callback ketika Master membaca data dari Slave
void onRequestData() {
    // IMPORTANT: Fungsi ini berjalan di interrupt context
    
    // Kirim data yang sudah disiapkan di loop()
    Wire.write(sendBuffer, sendLength);
}

// ============================================
// Data Processing Functions
// ============================================

void parseReceivedData() {
    if (receiveLength >= 8) {
        // Parse data structure: float, float, uint8, uint8
        memcpy(&masterData.pressure, &receiveBuffer[0], 4);
        memcpy(&masterData.reserved1, &receiveBuffer[4], 4);
        masterData.pump1Status = receiveBuffer[8];
        masterData.pump2Status = receiveBuffer[9];
        
        // Debug (optional, comment out untuk production)
        // Serial.printf("Received: P=%.1f, Pump1=%d, Pump2=%d\n", 
        //               masterData.pressure, masterData.pump1Status, masterData.pump2Status);
    }
}

void prepareSendData() {
    // Update slave data structure
    slaveData.rod1Pos = pos1;
    slaveData.rod2Pos = pos2;
    slaveData.rod3Pos = pos3;
    slaveData.reserved1 = 0;
    slaveData.kwThermal = kwThermal;
    slaveData.reserved2 = 0.0;
    slaveData.reserved3 = 0.0;
    
    // Pack ke buffer
    sendLength = 0;
    sendBuffer[sendLength++] = slaveData.rod1Pos;
    sendBuffer[sendLength++] = slaveData.rod2Pos;
    sendBuffer[sendLength++] = slaveData.rod3Pos;
    sendBuffer[sendLength++] = slaveData.reserved1;
    memcpy(&sendBuffer[sendLength], &slaveData.kwThermal, 4);
    sendLength += 4;
    memcpy(&sendBuffer[sendLength], &slaveData.reserved2, 4);
    sendLength += 4;
    memcpy(&sendBuffer[sendLength], &slaveData.reserved3, 4);
    sendLength += 4;
}

// ============================================
// Interlock Logic (sama seperti sebelumnya)
// ============================================

bool isInterlockSatisfied() {
    // Batang kendali hanya bisa digerakkan jika:
    // 1. Tekanan >= 40 bar
    // 2. Pompa primer ON (status = 2)
    // 3. Pompa sekunder ON (status = 2)
    
    if (masterData.pressure < 40.0) {
        return false;
    }
    
    if (masterData.pump1Status != 2 || masterData.pump2Status != 2) {
        return false;
    }
    
    return true;
}

// ============================================
// Setup Function
// ============================================

void setup() {
    Serial.begin(115200);
    Serial.println("ESP-B I2C Slave Starting...");
    
    // Initialize I2C Slave
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
    
    // Initialize OLED (PCA9548A multiplexer)
    // ... (copy dari code lama)
    
    Serial.println("ESP-B Ready!");
}

// ============================================
// Loop Function
// ============================================

void loop() {
    static unsigned long lastUpdate = 0;
    unsigned long currentTime = millis();
    
    // Process received data dari Master
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
    }
    
    // Check interlock before allowing rod movement
    bool interlockOK = isInterlockSatisfied();
    
    if (interlockOK && !emergencyTriggered) {
        // Rod control logic (sama seperti sebelumnya)
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
        // ... (sama untuk rod2 dan rod3)
    }
    
    // Calculate kwThermal
    kwThermal = (pos1 + pos2 + pos3) / 3.0 * 10.0;  // Simplified formula
    
    // Prepare data untuk dikirim ke Master
    if (currentTime - lastUpdate > 100) {  // Update setiap 100ms
        prepareSendData();
        lastUpdate = currentTime;
    }
    
    // Update OLED display
    // ... (sama seperti sebelumnya)
}

// ============================================
// OLED Functions (sama seperti sebelumnya)
// ============================================
// ... copy dari code lama
