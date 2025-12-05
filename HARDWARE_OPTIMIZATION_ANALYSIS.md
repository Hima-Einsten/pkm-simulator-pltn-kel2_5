# 🔧 Analisis Optimasi Hardware: 1 RasPi + 2 ESP32

## 📊 Konfigurasi Saat Ini (3 ESP32)

### Current System:
```
1x Raspberry Pi 4
├─ 15 GPIO buttons (GPIO 5-26)
├─ I2C bus → 2x PCA9548A (9 OLED)
└─ I2C bus → 1x PCA9548A (3 ESP32)

3x ESP32:
├─ ESP-B: 3 servo + I2C
├─ ESP-C: 6 relay + 4 PWM motor + I2C
└─ ESP-E: 48 LED (via 3x multiplexer) + I2C
```

**Total GPIO Usage:**
- **Raspberry Pi:** 15 GPIO (buttons) + 2 I2C = 17 pins
- **ESP-B:** 3 servo + 2 I2C = 5 pins
- **ESP-C:** 6 relay + 4 PWM + 2 I2C = 12 pins
- **ESP-E:** 4 selector + 6 enable/signal + 2 I2C = 12 pins

---

## 🎯 Proposal: 1 RasPi + 2 ESP32

### Strategi Optimasi:

#### **Option 1: Merge ESP-B + ESP-C (Recommended)**
Gabungkan control rods, relay, dan motor dalam 1 ESP32

#### **Option 2: Merge ESP-C + ESP-E**
Gabungkan relay, motor, dan LED visualizer dalam 1 ESP32

Mari analisis kedua opsi:

---

## ✅ Option 1: ESP-B+C Merged (Recommended)

### New System Architecture:

```
1x Raspberry Pi 4
├─ 15 GPIO buttons (GPIO 5-26)
├─ I2C bus → 2x PCA9548A (9 OLED)
└─ I2C bus → 1x PCA9548A (2 ESP32)

2x ESP32:
├─ ESP-BC (Merged): Control rods + Turbine + Humidifier
└─ ESP-E: 48 LED visualization
```

---

### 📌 ESP-BC (Merged B+C) - GPIO Analysis

**Required Functions:**
1. ✅ 3x Servo motors (control rods)
2. ✅ 6x Relay (4 main + 2 humidifier)
3. ✅ 4x PWM motors (steam gen, turbine, condenser, cooling)
4. ✅ I2C communication

**ESP32 GPIO Available:** 34 total pins
- GPIO 0-39 (beberapa tidak useable)
- **Useable pins:** ~28 pins
- **Reserved:** I2C (GPIO 21, 22), Boot (GPIO 0), etc

**Pin Assignment:**

```cpp
// ===== CONTROL RODS (3 servo) =====
#define SERVO_SAFETY      25
#define SERVO_SHIM        26
#define SERVO_REGULATING  27

// ===== MAIN RELAYS (4 relay) =====
#define RELAY_STEAM_GEN   32
#define RELAY_TURBINE     33
#define RELAY_CONDENSER   14
#define RELAY_COOLING_TOWER 12

// ===== HUMIDIFIER RELAYS (2 relay) =====
#define RELAY_HUMID_SG    13    // Steam Generator humidifier
#define RELAY_HUMID_CT    15    // Cooling Tower humidifier

// ===== PWM MOTORS (4 motors) =====
#define MOTOR_STEAM_GEN_PIN   4
#define MOTOR_TURBINE_PIN     16
#define MOTOR_CONDENSER_PIN   17
#define MOTOR_COOLING_PIN     5

// ===== I2C =====
#define SDA 21
#define SCL 22

// ===== OPTIONAL: Status LED =====
#define STATUS_LED 2
```

**Total Pins Used:** 
- 3 servo + 6 relay + 4 PWM + 2 I2C + 1 status = **16 pins**
- **Remaining:** 28 - 16 = **12 pins available**

✅ **FEASIBLE! Masih ada 12 pins cadangan**

---

### 📌 ESP-E (LED Visualizer) - No Change

**Pin Assignment (sama seperti sekarang):**

```cpp
// Shared selector (all 3 multiplexers)
#define S0 14
#define S1 27
#define S2 26
#define S3 25

// Flow 1: Primary
#define EN_PRIMARY 33
#define SIG_PRIMARY 32

// Flow 2: Secondary
#define EN_SECONDARY 15
#define SIG_SECONDARY 4

// Flow 3: Tertiary
#define EN_TERTIARY 2
#define SIG_TERTIARY 16

// I2C
#define SDA 21
#define SCL 22
```

**Total Pins Used:** 4 + 6 + 2 = **12 pins**
✅ **No problem, still within limits**

---

### 📌 Raspberry Pi 4 - No Change

**Pin Assignment:**
```
GPIO 2/3:  I2C (SDA/SCL)
GPIO 5-26: 15 Push Buttons (exact pins flexible)
```

**Total Used:** 2 + 15 = **17 GPIO**
**Available:** 40 GPIO total
✅ **Still plenty of room (23 pins free)**

---

## 📡 New I2C Protocol for ESP-BC

### ESP-BC I2C Address: 0x08

#### **RECEIVE (from RasPi):** 12 bytes

```cpp
struct ReceiveData {
    uint8_t safety_target;      // Byte 0: Safety rod target (0-100%)
    uint8_t shim_target;        // Byte 1: Shim rod target
    uint8_t regulating_target;  // Byte 2: Regulating rod target
    uint8_t reserved1;          // Byte 3: Reserved
    float thermal_kw;           // Byte 4-7: Thermal power (for PWM control)
    uint8_t humid_sg_cmd;       // Byte 8: Humidifier SG command (0/1)
    uint8_t humid_ct_cmd;       // Byte 9: Humidifier CT command (0/1)
    uint8_t reserved2;          // Byte 10: Reserved
    uint8_t reserved3;          // Byte 11: Reserved
};
```

#### **SEND (to RasPi):** 20 bytes

```cpp
struct SendData {
    uint8_t safety_actual;      // Byte 0: Safety rod actual
    uint8_t shim_actual;        // Byte 1: Shim rod actual
    uint8_t regulating_actual;  // Byte 2: Regulating rod actual
    uint8_t reserved1;          // Byte 3: Reserved
    float thermal_kw;           // Byte 4-7: Calculated thermal power
    float power_level;          // Byte 8-11: Turbine power level (%)
    uint32_t state;             // Byte 12-15: State machine
    uint8_t gen_status;         // Byte 16: Generator status
    uint8_t turb_status;        // Byte 17: Turbine status
    uint8_t humid_sg_status;    // Byte 18: Humidifier SG actual
    uint8_t humid_ct_status;    // Byte 19: Humidifier CT actual
};
```

---

## 💾 ESP-BC Firmware Structure

```cpp
#include <Wire.h>
#include <ESP32Servo.h>

// ===== PIN DEFINITIONS =====
// (as defined above)

// ===== GLOBAL VARIABLES =====
Servo servoSafety, servoShim, servoRegulating;

uint8_t safety_target = 0, shim_target = 0, reg_target = 0;
uint8_t safety_actual = 0, shim_actual = 0, reg_actual = 0;
float thermal_kw = 0.0;
uint8_t humid_sg_cmd = 0, humid_ct_cmd = 0;

// Turbine state machine
enum State { IDLE, STARTING, RUNNING, SHUTDOWN };
State current_state = IDLE;
float power_level = 0.0;

// ===== SETUP =====
void setup() {
    // Initialize servos
    servoSafety.attach(SERVO_SAFETY);
    servoShim.attach(SERVO_SHIM);
    servoRegulating.attach(SERVO_REGULATING);
    
    // Initialize relays
    pinMode(RELAY_STEAM_GEN, OUTPUT);
    pinMode(RELAY_TURBINE, OUTPUT);
    pinMode(RELAY_CONDENSER, OUTPUT);
    pinMode(RELAY_COOLING_TOWER, OUTPUT);
    pinMode(RELAY_HUMID_SG, OUTPUT);
    pinMode(RELAY_HUMID_CT, OUTPUT);
    
    // Initialize PWM motors
    ledcSetup(0, 5000, 8); // Channel 0, 5kHz, 8-bit
    ledcSetup(1, 5000, 8);
    ledcSetup(2, 5000, 8);
    ledcSetup(3, 5000, 8);
    
    ledcAttachPin(MOTOR_STEAM_GEN_PIN, 0);
    ledcAttachPin(MOTOR_TURBINE_PIN, 1);
    ledcAttachPin(MOTOR_CONDENSER_PIN, 2);
    ledcAttachPin(MOTOR_COOLING_PIN, 3);
    
    // Initialize I2C
    Wire.begin(0x08);
    Wire.onReceive(onReceive);
    Wire.onRequest(onRequest);
}

// ===== MAIN LOOP =====
void loop() {
    // Update servos
    updateServos();
    
    // Calculate thermal power
    calculateThermalPower();
    
    // Update turbine state machine
    updateTurbineState();
    
    // Update humidifiers
    updateHumidifiers();
    
    // Update PWM motors
    updateMotorSpeeds();
    
    delay(10);
}

// ===== FUNCTIONS =====
void updateServos() {
    int angleSafety = map(safety_target, 0, 100, 0, 180);
    int angleShim = map(shim_target, 0, 100, 0, 180);
    int angleReg = map(reg_target, 0, 100, 0, 180);
    
    servoSafety.write(angleSafety);
    servoShim.write(angleShim);
    servoRegulating.write(angleReg);
    
    safety_actual = safety_target;
    shim_actual = shim_target;
    reg_actual = reg_target;
}

void calculateThermalPower() {
    float avgRodPos = (safety_actual + shim_actual + reg_actual) / 3.0;
    thermal_kw = 50.0 + (avgRodPos * avgRodPos * 0.195);
    thermal_kw += safety_actual * 2.0 + shim_actual * 3.5 + reg_actual * 4.0;
}

void updateTurbineState() {
    // State machine logic based on thermal_kw
    // IDLE → STARTING → RUNNING → SHUTDOWN
    
    if (thermal_kw > 500 && current_state == IDLE) {
        current_state = STARTING;
    }
    
    if (current_state == STARTING) {
        power_level += 0.5; // Gradual startup
        if (power_level >= 100.0) {
            current_state = RUNNING;
            power_level = 100.0;
        }
    }
    
    if (thermal_kw < 200 && current_state == RUNNING) {
        current_state = SHUTDOWN;
    }
    
    if (current_state == SHUTDOWN) {
        power_level -= 1.0;
        if (power_level <= 0) {
            current_state = IDLE;
            power_level = 0;
        }
    }
    
    // Update relays based on state
    digitalWrite(RELAY_STEAM_GEN, (current_state != IDLE) ? HIGH : LOW);
    digitalWrite(RELAY_TURBINE, (current_state == RUNNING) ? HIGH : LOW);
    digitalWrite(RELAY_CONDENSER, (current_state != IDLE) ? HIGH : LOW);
    digitalWrite(RELAY_COOLING_TOWER, (current_state != IDLE) ? HIGH : LOW);
}

void updateHumidifiers() {
    digitalWrite(RELAY_HUMID_SG, humid_sg_cmd ? HIGH : LOW);
    digitalWrite(RELAY_HUMID_CT, humid_ct_cmd ? HIGH : LOW);
}

void updateMotorSpeeds() {
    int speed = map(power_level, 0, 100, 0, 255);
    
    ledcWrite(0, speed); // Steam gen motor
    ledcWrite(1, speed); // Turbine motor
    ledcWrite(2, speed); // Condenser motor
    ledcWrite(3, speed); // Cooling motor
}

void onReceive(int len) {
    if (len == 12) {
        uint8_t buf[12];
        for (int i = 0; i < 12; i++) {
            buf[i] = Wire.read();
        }
        
        safety_target = buf[0];
        shim_target = buf[1];
        reg_target = buf[2];
        // buf[3] reserved
        memcpy(&thermal_kw, &buf[4], 4);
        humid_sg_cmd = buf[8];
        humid_ct_cmd = buf[9];
    }
}

void onRequest() {
    uint8_t sendBuf[20];
    
    sendBuf[0] = safety_actual;
    sendBuf[1] = shim_actual;
    sendBuf[2] = reg_actual;
    sendBuf[3] = 0; // reserved
    memcpy(&sendBuf[4], &thermal_kw, 4);
    memcpy(&sendBuf[8], &power_level, 4);
    memcpy(&sendBuf[12], &current_state, 4);
    sendBuf[16] = (current_state != IDLE) ? 1 : 0; // gen status
    sendBuf[17] = (current_state == RUNNING) ? 1 : 0; // turb status
    sendBuf[18] = digitalRead(RELAY_HUMID_SG);
    sendBuf[19] = digitalRead(RELAY_HUMID_CT);
    
    Wire.write(sendBuf, 20);
}
```

---

## 📊 Comparison Table

| Aspect | 3 ESP (Current) | 2 ESP (Optimized) |
|--------|-----------------|-------------------|
| **Hardware Cost** | 3x ESP32 (~$15-30) | 2x ESP32 (~$10-20) |
| **Wiring Complexity** | Higher (3 I2C slaves) | Lower (2 I2C slaves) |
| **Pin Usage ESP-BC** | Separate (5 + 12) | Merged (16 pins) |
| **Pin Usage ESP-E** | 12 pins | 12 pins (same) |
| **RasPi GPIO** | 17 pins | 17 pins (same) |
| **I2C Multiplexer** | 1x PCA9548A (3 ch) | 1x PCA9548A (2 ch) |
| **Firmware Files** | 3 files | 2 files |
| **Code Complexity** | Simpler (separate) | Slightly complex |
| **Maintainability** | Easier debug | Moderate |
| **Scalability** | Better | Limited |

---

## ⚖️ Pros & Cons

### ✅ Advantages (2 ESP):
1. 💰 **Cost savings:** ~$5-10 per ESP32
2. 🔌 **Less wiring:** Only 2 I2C slaves
3. ⚡ **Lower power consumption**
4. 📦 **Smaller physical footprint**
5. 🧹 **Cleaner panel layout**

### ❌ Disadvantages (2 ESP):
1. 🔧 **More complex firmware:** One ESP handles multiple tasks
2. 🐛 **Harder debugging:** If ESP-BC fails, everything fails
3. ⏱️ **Potential timing issues:** More tasks = more processing
4. 📈 **Less scalable:** Adding features harder
5. 🔥 **Higher load per ESP:** May need better heat management

---

## 🎯 Recommendation

### **For Development/Testing: Use 3 ESP (Current)**
✅ Easier to debug  
✅ Modular design  
✅ Separate failures don't cascade  
✅ Better for learning/iteration

### **For Production/Final: Use 2 ESP (Optimized)**
✅ Lower cost  
✅ Simpler wiring  
✅ More professional  
✅ Once code is stable, merging is safe

---

## 🚀 Migration Path

### Phase 1: Test Current 3-ESP System
1. Verify ESP-B works (servos + thermal)
2. Verify ESP-C works (relay + PWM + humidifier)
3. Verify ESP-E works (48 LED animation)
4. Full integration test

### Phase 2: Develop ESP-BC Merged Firmware
1. Start with ESP-B code as base
2. Add relay control from ESP-C
3. Add PWM motor control from ESP-C
4. Add state machine logic
5. Test on breadboard

### Phase 3: Hardware Transition
1. Build ESP-BC on new ESP32
2. Test in parallel with old system
3. Validate all functions work
4. Remove old ESP-B and ESP-C
5. Update wiring

### Phase 4: Production
1. Create PCB (optional) for ESP-BC
2. Professional enclosure
3. Final documentation

---

## 📝 Conclusion

### **Answer: YES, it's feasible!** ✅

**ESP32 has enough pins:**
- ESP-BC needs: **16 pins** (out of 28 useable)
- ESP-E needs: **12 pins** (out of 28 useable)
- RasPi needs: **17 GPIO** (out of 40)

**Recommendation:**
1. **Start with 3 ESP** for development (current design)
2. **Migrate to 2 ESP** once system is stable
3. Keep ESP-E separate (LED visualization is independent task)
4. Merge ESP-B + ESP-C for cost/space savings

**Best of both worlds:**
- Develop with 3 ESP (easier debugging)
- Deploy with 2 ESP (cost effective)

---

## 🔍 Additional Optimization Ideas

### Option A: Use ESP32-S3 (More Pins)
- ESP32-S3 has 45 GPIO pins
- Could handle even more sensors/actuators
- Future-proof design

### Option B: Add I2C Expanders
- PCF8574 (8-bit I/O expander)
- Could add more relays without using GPIO
- ~$1 per chip

### Option C: Use Shift Registers
- 74HC595 for outputs (relay control)
- Save GPIO pins for critical functions
- Good for production boards

---

**Would you like me to:**
1. Create the merged ESP-BC firmware?
2. Update RasPi code for 2-ESP system?
3. Design a PCB layout for the optimized system?
