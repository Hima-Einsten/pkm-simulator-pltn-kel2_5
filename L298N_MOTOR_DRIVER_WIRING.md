# 🔌 L298N Motor Driver Wiring Guide - ESP32 Utama

## 📊 Hardware Configuration

**ESP32 Utama mengontrol 4 motor DC:**
- 3x Pompa (Primary, Secondary, Tertiary) 
- 1x Motor Turbin

**Motor Driver yang digunakan:**
- 2x L298N Dual H-Bridge Motor Driver
- Setiap L298N bisa control 2 motor DC
- Total kapasitas: 4 motor DC ✅

---

## 🎯 PIN ASSIGNMENT - ESP32 Utama

```cpp
// === MOTOR DRIVER PWM (4 motor DC) ===
#define MOTOR_PUMP_PRIMARY    4    // Pompa Primer
#define MOTOR_PUMP_SECONDARY  16   // Pompa Sekunder
#define MOTOR_PUMP_TERTIARY   17   // Pompa Tersier
#define MOTOR_TURBINE         5    // Motor Turbin

// PWM Configuration
#define PWM_FREQ       5000  // 5 kHz
#define PWM_RESOLUTION 8     // 8-bit (0-255)
```

---

## 🔧 L298N Motor Driver Pinout

```
┌─────────────────────────────────────┐
│        L298N H-Bridge Driver        │
├─────────────────────────────────────┤
│ Power Input:                        │
│   +12V  - Motor power (6-12V DC)   │
│   GND   - Common ground             │
│   +5V   - Logic power (from regulator) │
│                                     │
│ Motor A (Channel 1):                │
│   OUT1  - Motor A wire 1            │
│   OUT2  - Motor A wire 2            │
│                                     │
│ Motor B (Channel 2):                │
│   OUT3  - Motor B wire 1            │
│   OUT4  - Motor B wire 2            │
│                                     │
│ Control Pins:                       │
│   IN1   - Motor A direction 1       │
│   IN2   - Motor A direction 2       │
│   IN3   - Motor B direction 1       │
│   IN4   - Motor B direction 2       │
│   ENA   - Motor A speed (PWM)       │
│   ENB   - Motor B speed (PWM)       │
│                                     │
│ Jumpers:                            │
│   ENA   - Remove jumper for PWM     │
│   ENB   - Remove jumper for PWM     │
└─────────────────────────────────────┘
```

---

## 📡 WIRING DIAGRAM

### **L298N #1 - Pompa Primer & Pompa Sekunder**

```
ESP32 Utama                L298N #1                 Motors
━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━          ━━━━━━━━━━━━
                           
GPIO 4 (PWM) ────────────> ENA (PWM)               
GND ──────────────────────> IN1 (Direction)        
3.3V ─────────────────────> IN2 (Direction)        
                              │                     
                           OUT1 ──────────────────> Motor Pompa Primer (+)
                           OUT2 ──────────────────> Motor Pompa Primer (-)
                           
GPIO 16 (PWM) ───────────> ENB (PWM)               
GND ──────────────────────> IN3 (Direction)        
3.3V ─────────────────────> IN4 (Direction)        
                              │                     
                           OUT3 ──────────────────> Motor Pompa Sekunder (+)
                           OUT4 ──────────────────> Motor Pompa Sekunder (-)
                           
GND ──────────────────────> GND (Common)           
                           +12V <─────────────────── Power Supply 12V
                           +5V ────────────────────> NOT USED (internal regulator)
```

### **L298N #2 - Pompa Tersier & Motor Turbin**

```
ESP32 Utama                L298N #2                 Motors
━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━          ━━━━━━━━━━━━
                           
GPIO 17 (PWM) ───────────> ENA (PWM)               
GND ──────────────────────> IN1 (Direction)        
3.3V ─────────────────────> IN2 (Direction)        
                              │                     
                           OUT1 ──────────────────> Motor Pompa Tersier (+)
                           OUT2 ──────────────────> Motor Pompa Tersier (-)
                           
GPIO 5 (PWM) ────────────> ENB (PWM)               
GND ──────────────────────> IN3 (Direction)        
3.3V ─────────────────────> IN4 (Direction)        
                              │                     
                           OUT3 ──────────────────> Motor Turbin (+)
                           OUT4 ──────────────────> Motor Turbin (-)
                           
GND ──────────────────────> GND (Common)           
                           +12V <─────────────────── Power Supply 12V
                           +5V ────────────────────> NOT USED
```

---

## 🔌 CONNECTION TABLE

### **L298N #1 - Pompa Primer & Sekunder**

| L298N #1 Pin | Connect To | Description |
|--------------|------------|-------------|
| **+12V** | Power Supply +12V | Motor power input |
| **GND** | ESP32 GND + Power Supply GND | Common ground |
| **+5V** | NOT USED | Internal 5V regulator output |
| | | |
| **ENA** | ESP32 GPIO 4 | Pompa Primer speed (PWM) |
| **IN1** | ESP32 GND | Pompa Primer direction (always forward) |
| **IN2** | ESP32 3.3V | Pompa Primer direction (always forward) |
| **OUT1** | Motor Pompa Primer (+) | Motor wire 1 |
| **OUT2** | Motor Pompa Primer (-) | Motor wire 2 |
| | | |
| **ENB** | ESP32 GPIO 16 | Pompa Sekunder speed (PWM) |
| **IN3** | ESP32 GND | Pompa Sekunder direction (always forward) |
| **IN4** | ESP32 3.3V | Pompa Sekunder direction (always forward) |
| **OUT3** | Motor Pompa Sekunder (+) | Motor wire 1 |
| **OUT4** | Motor Pompa Sekunder (-) | Motor wire 2 |

### **L298N #2 - Pompa Tersier & Motor Turbin**

| L298N #2 Pin | Connect To | Description |
|--------------|------------|-------------|
| **+12V** | Power Supply +12V | Motor power input |
| **GND** | ESP32 GND + Power Supply GND | Common ground |
| **+5V** | NOT USED | Internal 5V regulator output |
| | | |
| **ENA** | ESP32 GPIO 17 | Pompa Tersier speed (PWM) |
| **IN1** | ESP32 GND | Pompa Tersier direction (always forward) |
| **IN2** | ESP32 3.3V | Pompa Tersier direction (always forward) |
| **OUT1** | Motor Pompa Tersier (+) | Motor wire 1 |
| **OUT2** | Motor Pompa Tersier (-) | Motor wire 2 |
| | | |
| **ENB** | ESP32 GPIO 5 | Motor Turbin speed (PWM) |
| **IN3** | ESP32 GND | Motor Turbin direction (always forward) |
| **IN4** | ESP32 3.3V | Motor Turbin direction (always forward) |
| **OUT3** | Motor Turbin (+) | Motor wire 1 |
| **OUT4** | Motor Turbin (-) | Motor wire 2 |

---

## ⚙️ L298N CONFIGURATION

### **Important Settings:**

1. **Remove ENA/ENB Jumpers:**
   - L298N biasanya datang dengan jumper di ENA dan ENB
   - **HARUS DILEPAS** agar bisa control speed via PWM
   - Jika jumper dipasang, motor always full speed

2. **IN1/IN2 dan IN3/IN4 Configuration:**
   - Untuk pompa dan turbin, kita hanya perlu 1 arah (forward)
   - IN1=LOW, IN2=HIGH → Motor berputar forward
   - Speed diatur via PWM di pin ENA/ENB

3. **Power Supply:**
   - +12V untuk motor power (bisa 6-12V tergantung motor)
   - GND harus common dengan ESP32
   - +5V output dari L298N: JANGAN DIGUNAKAN (terlalu lemah untuk ESP32)

---

## 🔌 COMPLETE WIRING DIAGRAM

```
                    ╔════════════════════════════════════╗
                    ║      Power Supply 12V DC          ║
                    ╚═══════╦════════════════════╦══════╝
                            ║                    ║
                         +12V                   GND
                            ║                    ║
            ┌───────────────╫────────────────────╫───────────────┐
            │               ║                    ║               │
            │         ┌─────╨─────┐        ┌─────╨─────┐       │
            │         │  L298N #1 │        │  L298N #2 │       │
            │         │           │        │           │       │
            │         │  +12V GND │        │  +12V GND │       │
            │         └─────┬─────┘        └─────┬─────┘       │
            │               │                    │              │
            │         ┌─────┴─────┐        ┌─────┴─────┐       │
            │         │           │        │           │       │
            │      ┌──┤ ENA   IN1 ├──┐  ┌──┤ ENA   IN1 ├──┐   │
            │      │  │ IN2   OUT1├──┼──┼──┤ IN2   OUT1├──┼───┼──> Motor Primer
            │      │  │ OUT2  ENB │  │  │  │ OUT2  ENB │  │   │
            │      │  │ IN3   IN4 ├──┼──┼──┤ IN3   IN4 ├──┼───┼──> Motor Sekunder
            │      │  │ OUT3  OUT4│  │  │  │ OUT3  OUT4│  │   │
            │      │  └───────────┘  │  │  └───────────┘  │   │
            │      │                 │  │                 │   │
            │   ┌──┴─────────────────┴──┴─────────────────┴───┴──> Motor Tersier
            │   │                                                   
            │   │                                                   Motor Turbin
            │   │
            │   │         ╔════════════════════════════╗
            │   └─────────║      ESP32 UTAMA          ║
            │             ║    (Address 0x08)          ║
            └─────────────║                            ║
                          ║  GPIO 4  ──> L298N#1 ENA   ║
                          ║  GPIO 16 ──> L298N#1 ENB   ║
                          ║  GPIO 17 ──> L298N#2 ENA   ║
                          ║  GPIO 5  ──> L298N#2 ENB   ║
                          ║                            ║
                          ║  3.3V ────> IN2, IN4 (x4)  ║
                          ║  GND ─────> IN1, IN3 (x4)  ║
                          ║  GND ─────> L298N GND      ║
                          ╚════════════════════════════╝
```

---

## 💻 SOFTWARE IMPLEMENTATION

### **Program ESP32 sudah benar!** ✅

```cpp
// Initialize PWM channels (ESP32 Core v3.x)
void setup() {
  // Attach PWM to motor driver pins
  ledcAttach(MOTOR_PUMP_PRIMARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_PUMP_SECONDARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_PUMP_TERTIARY, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_TURBINE, PWM_FREQ, PWM_RESOLUTION);
  
  // Initialize to 0% speed
  ledcWrite(MOTOR_PUMP_PRIMARY, 0);
  ledcWrite(MOTOR_PUMP_SECONDARY, 0);
  ledcWrite(MOTOR_PUMP_TERTIARY, 0);
  ledcWrite(MOTOR_TURBINE, 0);
}

// Update pump speeds (gradual control)
void updatePumpSpeeds() {
  // Gradual acceleration/deceleration
  // Primary pump
  if (pump_primary_actual < pump_primary_target) {
    pump_primary_actual += 2.0;  // +2% per cycle
  } else if (pump_primary_actual > pump_primary_target) {
    pump_primary_actual -= 1.0;  // -1% per cycle
  }
  
  // Apply PWM (0-100% mapped to 0-255 PWM)
  int pwm_primary = map((int)pump_primary_actual, 0, 100, 0, 255);
  ledcWrite(MOTOR_PUMP_PRIMARY, pwm_primary);
  
  // Same for secondary & tertiary...
}

// Update turbine speed
void updateTurbineSpeed() {
  // Turbine speed = average of shim + regulating rods
  turbine_speed = (shim_actual + regulating_actual) / 2.0;
  
  // Apply PWM
  int pwm_turbine = map((int)turbine_speed, 0, 100, 0, 255);
  ledcWrite(MOTOR_TURBINE, pwm_turbine);
}
```

---

## 🎛️ CONTROL LOGIC

### **Pompa Control (Automatic dari ESP32):**

```
Turbine State: IDLE
├─ pump_primary_target = 0%
├─ pump_secondary_target = 0%
└─ pump_tertiary_target = 0%

Turbine State: STARTING
├─ pump_primary_target = 50%
├─ pump_secondary_target = 50%
└─ pump_tertiary_target = 50%

Turbine State: RUNNING
├─ pump_primary_target = 100%
├─ pump_secondary_target = 100%
└─ pump_tertiary_target = 100%

Turbine State: SHUTDOWN
├─ pump_primary_target = 20%
├─ pump_secondary_target = 20%
└─ pump_tertiary_target = 20%
```

### **Turbine Control (Automatic dari ESP32):**

```
turbine_speed = (shim_rod + regulating_rod) / 2

Example:
- Shim = 60%, Regulating = 80%
- Turbine speed = (60 + 80) / 2 = 70%
- PWM = map(70, 0, 100, 0, 255) = 178
```

---

## ⚡ POWER REQUIREMENTS

### **Motor Specifications (typical):**

| Motor | Voltage | Current (max) | Power |
|-------|---------|---------------|-------|
| Pompa Primer | 12V | 1A | 12W |
| Pompa Sekunder | 12V | 1A | 12W |
| Pompa Tersier | 12V | 1A | 12W |
| Motor Turbin | 12V | 1.5A | 18W |
| **Total** | **12V** | **~4.5A** | **~54W** |

### **Power Supply Requirements:**

```
Recommended: 12V 5A DC Power Supply

Why:
- 4 motors total draw ~4.5A maximum
- Add 10% safety margin = 5A
- L298N internal regulator loses ~2V
- Stable voltage important for PWM control
```

### **Connections:**

```
Power Supply 12V 5A
    ├─ (+) ──> L298N #1 +12V
    ├─ (+) ──> L298N #2 +12V
    └─ (-) ──> Common GND (L298N #1, #2, ESP32)
```

---

## 🧪 TESTING PROCEDURE

### **Step 1: Hardware Check (Power OFF)**
```
□ Verify all PWM connections (GPIO 4, 5, 16, 17)
□ Verify all direction pins (IN1-IN4 on both L298N)
□ Verify GND connections (common ground)
□ Remove ENA/ENB jumpers on both L298N
□ Check motor polarity (+ and -)
```

### **Step 2: Power ON Test (No Motors)**
```
□ Connect 12V power supply
□ Check L298N power LEDs (should be ON)
□ Measure voltage at motor outputs (should be 0V)
```

### **Step 3: Individual Motor Test**
```
1. Test Pompa Primer:
   - Set pump_primary_target = 50%
   - Motor should spin smoothly
   - Check direction (should be forward)

2. Test Pompa Sekunder:
   - Set pump_secondary_target = 50%
   - Motor should spin smoothly

3. Test Pompa Tersier:
   - Set pump_tertiary_target = 50%
   - Motor should spin smoothly

4. Test Motor Turbin:
   - Set shim_rod = 50%, regulating_rod = 50%
   - Turbine speed should be 50%
   - Motor should spin smoothly
```

### **Step 4: Speed Control Test**
```
□ Test gradual acceleration (0% → 100%)
□ Test gradual deceleration (100% → 0%)
□ Test intermediate speeds (25%, 50%, 75%)
□ Verify PWM frequency (5kHz with oscilloscope)
```

### **Step 5: Full System Test**
```
□ Start simulator (press START button on RasPi)
□ Raise control rods (shim & regulating)
□ Verify turbine auto-starts when thermal > 50 MWth
□ Verify pompa speeds ramp up gradually
□ Test emergency shutdown (all motors stop)
```

---

## ⚠️ SAFETY WARNINGS

### **Electrical Safety:**
```
⚠️  12V power supply - ensure proper polarity
⚠️  Common ground essential (ESP32 + L298N + Power Supply)
⚠️  L298N can get HOT - add heatsinks if needed
⚠️  Check motor current - L298N max 2A per channel
⚠️  Separate 12V motor power from 3.3V ESP32 logic
```

### **Motor Safety:**
```
⚠️  Direction pins (IN1-IN4) should NEVER be floating
⚠️  Always set direction before enabling PWM
⚠️  Motor wires can reverse - check polarity
⚠️  Add flyback diodes if motors create electrical noise
```

---

## 🔧 TROUBLESHOOTING

### **Problem: Motor tidak berputar**
```
Check:
1. Power supply connected? (12V ON?)
2. GND common? (ESP32 and L298N share GND?)
3. PWM signal present? (measure with multimeter/oscilloscope)
4. Motor polarity correct? (swap wires if backward)
5. ENA/ENB jumper removed?
```

### **Problem: Motor berputar tapi tidak smooth**
```
Check:
1. PWM frequency correct? (5kHz)
2. Power supply voltage stable? (should be 12V ±0.5V)
3. Motor current within L298N spec? (<2A per channel)
4. Gradual control working? (increment 2% per cycle)
```

### **Problem: L298N sangat panas**
```
Solutions:
1. Add heatsink to L298N chip
2. Reduce motor load
3. Check motor current (may exceed 2A)
4. Use external cooling fan
5. Consider using separate motor driver for each motor
```

### **Problem: ESP32 resets when motors start**
```
Cause: Voltage drop from motor startup current

Solutions:
1. Use separate power supply for motors (12V) and ESP32 (5V USB)
2. Add large capacitor (1000μF) near L298N +12V input
3. Use thicker wires for power connections
4. Implement gradual motor startup (already done in code)
```

---

## 📐 PHYSICAL LAYOUT RECOMMENDATION

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   ┌──────────────┐        ┌──────────────┐    │
│   │   L298N #1   │        │   L298N #2   │    │
│   │  Pompa 1&2   │        │  Pompa 3+Turb│    │
│   └──────────────┘        └──────────────┘    │
│          │                        │             │
│          │    ┌──────────────┐   │             │
│          └────┤  ESP32 Utama ├───┘             │
│               └──────────────┘                  │
│                      │                          │
│                 ┌────┴─────┐                    │
│                 │ 12V PSU  │                    │
│                 │   5A     │                    │
│                 └──────────┘                    │
│                                                 │
└─────────────────────────────────────────────────┘

Tips:
- Keep PWM wires short (<20cm)
- Twist PWM wire with GND wire (reduce noise)
- Keep motor wires away from I2C wires
- Add capacitors near L298N power input (100μF + 0.1μF)
```

---

## ✅ CHECKLIST SEBELUM TESTING

### **Hardware:**
- [ ] 2x L298N motor driver ready
- [ ] ENA/ENB jumpers removed on both L298N
- [ ] 4x DC motors connected
- [ ] 12V 5A power supply ready
- [ ] Common ground verified
- [ ] PWM wires connected (GPIO 4, 5, 16, 17)
- [ ] Direction pins wired (IN1-IN4 to GND/3.3V)

### **Software:**
- [ ] ESP32 firmware uploaded (`esp_utama.ino`)
- [ ] Serial monitor working (115200 baud)
- [ ] PWM frequency 5kHz verified
- [ ] Gradual control logic tested

### **Safety:**
- [ ] Power supply fused
- [ ] No loose wires
- [ ] Heatsinks on L298N if needed
- [ ] Fire extinguisher nearby (just in case!)

---

## 📞 SUPPORT

**If you encounter problems:**
1. Check this wiring guide again
2. Verify with multimeter (voltage, continuity)
3. Test each motor individually
4. Check Serial Monitor for ESP32 debug messages

**Common Issues Database:**
- Motor not spinning → Check power & PWM signal
- Motor spinning backward → Reverse motor wires (OUT1 ↔ OUT2)
- Erratic speed → Check PWM frequency & power supply
- L298N hot → Add heatsink, check motor current

---

**Last Updated:** 2024-12-12  
**Version:** 1.0  
**Status:** ✅ Ready for Implementation

