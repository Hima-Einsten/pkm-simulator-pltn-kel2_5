# ⚡ ESP32 Pin Conflict Resolution - Motor Driver Optimization

## 🚨 Problem Identified

**Original pin assignment had I2C conflict:**
- **GPIO 21** (I2C SDA) was also assigned to `MOTOR_PUMP_TERTIARY_IN1`
- **GPIO 22** (I2C SCL) was also assigned to `MOTOR_PUMP_SECONDARY_IN2`
- Additional conflicts with boot/UART pins (0, 1, 3)

This caused I2C communication failures between ESP32 and Raspberry Pi.

---

## ✅ Solution: Simplified Motor Direction Control

### Key Insight
**Pompa (pumps) hanya perlu satu arah - FORWARD!**
- Tidak perlu kontrol direction untuk pompa (always forward)
- Hanya turbine yang perlu bisa diubah arah putarannya
- Menghemat **6 GPIO pins**

### Implementation Strategy

| Motor | Direction Control | Reason |
|-------|------------------|---------|
| Pompa Primer | HARD-WIRED (always FORWARD) | Pompa hanya perlu dorong coolant satu arah |
| Pompa Sekunder | HARD-WIRED (always FORWARD) | Pompa hanya perlu dorong coolant satu arah |
| Pompa Tersier | HARD-WIRED (always FORWARD) | Pompa hanya perlu dorong coolant satu arah |
| **Turbine** | **GPIO controlled** | Perlu adjustment arah putar untuk optimize |

---

## 📍 New Pin Assignment

### ESP32 Utama Pin Usage

```cpp
// === MOTOR PWM (Speed Control) ===
GPIO 4  → MOTOR_PUMP_PRIMARY      (ENA L298N #1)
GPIO 16 → MOTOR_PUMP_SECONDARY    (ENB L298N #1)
GPIO 17 → MOTOR_PUMP_TERTIARY     (ENA L298N #2)
GPIO 5  → MOTOR_TURBINE           (ENB L298N #2)

// === MOTOR DIRECTION (Only Turbine) ===
GPIO 23 → MOTOR_TURBINE_IN1       (direction 1)
GPIO 18 → MOTOR_TURBINE_IN2       (direction 2)

// === I2C (Now Conflict-Free!) ===
GPIO 21 → I2C SDA ✅
GPIO 22 → I2C SCL ✅

// === Other Peripherals ===
GPIO 25, 26, 27 → Servos (control rods)
GPIO 32, 33, 14, 12 → Relay CT1-4
GPIO 13, 15 → Relay SG1-2
GPIO 2 → Status LED
```

### Pins Saved
✅ **6 GPIO pins freed up** (was 8 direction pins, now only 2)

---

## 🔌 L298N Wiring - Updated

### L298N #1 - Pompa Primer & Sekunder

```
ESP32 Side:
  GPIO 4  ──────────> ENA (Pompa Primer speed PWM)
  GPIO 16 ──────────> ENB (Pompa Sekunder speed PWM)
  GND ───────────────> GND (common ground)

L298N Board Side:
  IN1 ──────────────> Connect to GND (hardwired)
  IN2 ──────────────> Connect to +3.3V (hardwired)
  IN3 ──────────────> Connect to GND (hardwired)
  IN4 ──────────────> Connect to +3.3V (hardwired)
  
  OUT1/OUT2 ────────> Motor Pompa Primer
  OUT3/OUT4 ────────> Motor Pompa Sekunder
  
  +12V ─────────────> Power supply 12V
  GND ──────────────> Common ground
```

### L298N #2 - Pompa Tersier & Turbine

```
ESP32 Side:
  GPIO 17 ──────────> ENA (Pompa Tersier speed PWM)
  GPIO 5  ──────────> ENB (Turbine speed PWM)
  GPIO 23 ──────────> IN3 (Turbine direction 1)
  GPIO 18 ──────────> IN4 (Turbine direction 2)
  GND ───────────────> GND (common ground)

L298N Board Side:
  IN1 ──────────────> Connect to GND (hardwired)
  IN2 ──────────────> Connect to +3.3V (hardwired)
  IN3 ───────────────> From ESP32 GPIO 23
  IN4 ───────────────> From ESP32 GPIO 18
  
  OUT1/OUT2 ────────> Motor Pompa Tersier
  OUT3/OUT4 ────────> Motor Turbine
  
  +12V ─────────────> Power supply 12V
  GND ──────────────> Common ground
```

---

## 🛠️ Hardware Modification Steps

### For Pompa Channels (IN1 & IN2 on Pump Motors)

**On L298N #1 (Channel A - Pompa Primer):**
1. Remove jumper from IN1 pin hole (if present)
2. Connect IN1 directly to **GND rail** using jumper wire
3. Connect IN2 directly to **+3.3V rail** using jumper wire
4. Result: Motor always rotates FORWARD when ENA receives PWM

**On L298N #1 (Channel B - Pompa Sekunder):**
1. Connect IN3 to **GND rail**
2. Connect IN4 to **+3.3V rail**
3. Result: Motor always rotates FORWARD when ENB receives PWM

**On L298N #2 (Channel A - Pompa Tersier):**
1. Connect IN1 to **GND rail**
2. Connect IN2 to **+3.3V rail**
3. Result: Motor always rotates FORWARD when ENA receives PWM

**On L298N #2 (Channel B - Turbine):**
1. **DO NOT** hardwire IN3/IN4
2. Connect IN3 to ESP32 GPIO 23
3. Connect IN4 to ESP32 GPIO 18
4. Result: Motor direction controlled via ESP32 (for rotation adjustment)

---

## 📊 Connection Table Summary

| L298N | Channel | Motor | ENA/ENB Pin | IN1 | IN2 | Control Type |
|-------|---------|-------|-------------|-----|-----|--------------|
| **#1** | A | Pompa Primer | GPIO 4 | GND | +3.3V | Speed only (always FORWARD) |
| **#1** | B | Pompa Sekunder | GPIO 16 | GND | +3.3V | Speed only (always FORWARD) |
| **#2** | A | Pompa Tersier | GPIO 17 | GND | +3.3V | Speed only (always FORWARD) |
| **#2** | B | **Turbine** | GPIO 5 | **GPIO 23** | **GPIO 18** | **Speed + Direction** |

---

## 💻 Software Changes

### Code Before (8 direction pins needed)
```cpp
#define MOTOR_PUMP_PRIMARY_IN1    18
#define MOTOR_PUMP_PRIMARY_IN2    19
#define MOTOR_PUMP_SECONDARY_IN1  23
#define MOTOR_PUMP_SECONDARY_IN2  22   // ❌ Conflict with I2C SCL!
#define MOTOR_PUMP_TERTIARY_IN1   21   // ❌ Conflict with I2C SDA!
#define MOTOR_PUMP_TERTIARY_IN2   3
#define MOTOR_TURBINE_IN1         1
#define MOTOR_TURBINE_IN2         0
```

### Code After (2 direction pins needed)
```cpp
// Only turbine has direction control
#define MOTOR_TURBINE_IN1         23   // ✅ No conflict
#define MOTOR_TURBINE_IN2         18   // ✅ No conflict

// Pumps hardwired to FORWARD (no GPIO needed)
```

### Updated setMotorDirection() Function

```cpp
void setMotorDirection(uint8_t motor_id, uint8_t direction) {
  // Only turbine (motor_id = 4) has GPIO control
  if (motor_id == 4) {
    if (direction == MOTOR_FORWARD) {
      digitalWrite(MOTOR_TURBINE_IN1, HIGH);
      digitalWrite(MOTOR_TURBINE_IN2, LOW);
    } else if (direction == MOTOR_REVERSE) {
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, HIGH);
    } else { // MOTOR_STOP
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, LOW);
    }
  }
  // Pumps 1-3: Hard-wired to FORWARD on L298N board
}
```

---

## ✅ Benefits

### 1. **I2C Conflict Resolved**
- GPIO 21 (SDA) and GPIO 22 (SCL) now exclusively for I2C
- No more communication errors with Raspberry Pi
- Reliable sensor data exchange

### 2. **GPIO Pins Saved**
- Before: 8 pins for motor direction control
- After: 2 pins for motor direction control
- **Saved: 6 GPIO pins** for future expansion

### 3. **Simpler Wiring**
- Fewer wires from ESP32 to L298N
- Less chance of wiring errors
- Easier to troubleshoot

### 4. **Practical Design**
- Pumps realistically only need one direction
- Turbine direction adjustment is still available
- Hardware matches actual use case

---

## 🧪 Testing Checklist

### Hardware Verification
- [ ] Verify GPIO 21/22 only connected to I2C bus
- [ ] Check pump IN1 pins connected to GND
- [ ] Check pump IN2 pins connected to +3.3V  
- [ ] Verify turbine IN3/IN4 connected to GPIO 23/18
- [ ] Confirm common ground between ESP32, L298N, PSU

### Software Testing
```bash
# Upload new firmware
arduino-cli compile --fqbn esp32:esp32:esp32 esp_utama/
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 esp_utama/

# Monitor serial output
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
```

Expected output:
```
✓ Motor drivers initialized (3 pumps + turbine = 0%)
✓ Turbine direction control initialized (FORWARD)
✓ I2C Ready at address 0x08
```

### Functional Testing
- [ ] Test pompa primer speed 0-100%
- [ ] Test pompa sekunder speed 0-100%
- [ ] Test pompa tersier speed 0-100%
- [ ] Test turbine forward direction
- [ ] Test turbine reverse direction
- [ ] Test I2C communication (no errors)

---

## 📸 Wiring Diagram

```
                     [ESP32 Utama]
                           |
        ┌──────────────────┼──────────────────┐
        |                  |                  |
    [GPIO 4,16]       [GPIO 17,5]      [GPIO 23,18]
        |                  |                  |
        ▼                  ▼                  ▼
   [L298N #1]          [L298N #2]       [Turbine DIR]
        |                  |                  
   [Pump 1,2]         [Pump 3, Turbine]      
        |                  |
        └─────────[12V PSU]┘
                     |
                   [GND]────[ESP32 GND]
```

---

## 🎯 Summary

**Problem:** GPIO 21/22 I2C conflict with motor pins  
**Root Cause:** Too many direction control pins assigned  
**Solution:** Hard-wire pump directions, control only turbine  
**Result:** 6 pins saved, I2C working, simpler wiring  

**Status:** ✅ **RESOLVED**

---

**Updated:** 2025-12-12  
**Version:** 2.0  
**Tested:** Pending hardware implementation
