# 🔧 Compilation Fix - ESP32 Core v3.x

## ❌ Problem

**Error message:**
```
error: 'ledcSetup' was not declared in this scope
error: 'ledcAttachPin' was not declared in this scope; did you mean 'ledcAttach'?
```

**Root cause:** Code written for ESP32 Arduino Core **v2.x**, but you're using **v3.x**

---

## ✅ Solution Applied

### Changes Made to `esp_utama.ino`:

#### 1. PWM Initialization (Lines 166-176)

**Before:**
```cpp
// Initialize PWM channels
ledcSetup(PWM_CHANNEL_STEAM_GEN, PWM_FREQ, PWM_RESOLUTION);
ledcSetup(PWM_CHANNEL_TURBINE, PWM_FREQ, PWM_RESOLUTION);
ledcSetup(PWM_CHANNEL_CONDENSER, PWM_FREQ, PWM_RESOLUTION);
ledcSetup(PWM_CHANNEL_COOLING, PWM_FREQ, PWM_RESOLUTION);

ledcAttachPin(MOTOR_STEAM_GEN_PIN, PWM_CHANNEL_STEAM_GEN);
ledcAttachPin(MOTOR_TURBINE_PIN, PWM_CHANNEL_TURBINE);
ledcAttachPin(MOTOR_CONDENSER_PIN, PWM_CHANNEL_CONDENSER);
ledcAttachPin(MOTOR_COOLING_PIN, PWM_CHANNEL_COOLING);

// All motors OFF initially
ledcWrite(PWM_CHANNEL_STEAM_GEN, 0);
ledcWrite(PWM_CHANNEL_TURBINE, 0);
ledcWrite(PWM_CHANNEL_CONDENSER, 0);
ledcWrite(PWM_CHANNEL_COOLING, 0);
```

**After:**
```cpp
// Initialize PWM channels (ESP32 Core v3.x API)
ledcAttach(MOTOR_STEAM_GEN_PIN, PWM_FREQ, PWM_RESOLUTION);
ledcAttach(MOTOR_TURBINE_PIN, PWM_FREQ, PWM_RESOLUTION);
ledcAttach(MOTOR_CONDENSER_PIN, PWM_FREQ, PWM_RESOLUTION);
ledcAttach(MOTOR_COOLING_PIN, PWM_FREQ, PWM_RESOLUTION);

// All motors OFF initially
ledcWrite(MOTOR_STEAM_GEN_PIN, 0);
ledcWrite(MOTOR_TURBINE_PIN, 0);
ledcWrite(MOTOR_CONDENSER_PIN, 0);
ledcWrite(MOTOR_COOLING_PIN, 0);
```

#### 2. PWM Speed Update (Lines 289-296)

**Before:**
```cpp
void updateMotorSpeeds() {
  int speed = map((int)power_level, 0, 100, 0, 255);
  
  ledcWrite(PWM_CHANNEL_STEAM_GEN, speed);
  ledcWrite(PWM_CHANNEL_TURBINE, speed);
  ledcWrite(PWM_CHANNEL_CONDENSER, speed);
  ledcWrite(PWM_CHANNEL_COOLING, speed);
}
```

**After:**
```cpp
void updateMotorSpeeds() {
  int speed = map((int)power_level, 0, 100, 0, 255);
  
  // ESP32 Core v3.x: ledcWrite() uses pin number directly
  ledcWrite(MOTOR_STEAM_GEN_PIN, speed);
  ledcWrite(MOTOR_TURBINE_PIN, speed);
  ledcWrite(MOTOR_CONDENSER_PIN, speed);
  ledcWrite(MOTOR_COOLING_PIN, speed);
}
```

#### 3. Removed Unused Channel Definitions (Lines 62-68)

**Before:**
```cpp
// === PWM CHANNELS ===
#define PWM_FREQ      5000
#define PWM_RESOLUTION 8
#define PWM_CHANNEL_STEAM_GEN  0
#define PWM_CHANNEL_TURBINE    1
#define PWM_CHANNEL_CONDENSER  2
#define PWM_CHANNEL_COOLING    3
```

**After:**
```cpp
// === PWM Configuration (ESP32 Core v3.x) ===
#define PWM_FREQ       5000  // 5 kHz
#define PWM_RESOLUTION 8     // 8-bit (0-255)
```

#### 4. Updated Header Comment

Added note about ESP32 Core v3.x compatibility:
```cpp
/*
 * ...
 * IMPORTANT: Uses ESP32 Arduino Core v3.x API
 * - ledcAttach(pin, freq, resolution) instead of ledcSetup() + ledcAttachPin()
 * - ledcWrite(pin, duty) uses pin number directly (no channel needed)
 */
```

---

## 🔍 Verification

### Check for old API calls:
```bash
# Should return NO results:
grep -r "ledcSetup\|ledcAttachPin\|PWM_CHANNEL_[A-Z]" esp_utama.ino
```

### Expected compile result:
```
Sketch uses XXXX bytes (X%) of program storage space.
Global variables use XXXX bytes (X%) of dynamic memory.
```

---

## 📊 API Comparison

| Feature | v2.x API | v3.x API |
|---------|----------|----------|
| **Setup** | `ledcSetup(ch, f, r)` + `ledcAttachPin(p, ch)` | `ledcAttach(p, f, r)` |
| **Write** | `ledcWrite(channel, duty)` | `ledcWrite(pin, duty)` |
| **Channel Management** | Manual | Automatic |
| **Lines of Code** | More | Less |

---

## ✅ Status

- [x] PWM initialization updated
- [x] PWM write calls updated
- [x] Channel definitions removed
- [x] Header comment updated
- [x] Code documented
- [x] Ready to compile

---

## 🚀 Next Steps

### 1. Compile in Arduino IDE:
```
File → Open → esp_utama.ino
Tools → Board → ESP32 Dev Module
Sketch → Verify/Compile
```

### 2. Expected Output:
```
Compiling sketch...
✓ Compiled successfully
```

### 3. Upload to ESP32:
```
Tools → Port → (select your ESP32)
Sketch → Upload
```

### 4. Verify Serial Output:
```
=== ESP-BC MERGED: Control Rods + Turbine + Humidifier ===
I2C Address: 0x08
✓ Servos initialized at 0%
✓ Relays initialized (all OFF)
✓ PWM motors initialized (speed 0)
✓ I2C Ready at address 0x08
=== System Ready ===
```

---

## 📚 Additional Resources

- **ESP32_CORE_V3_CHANGES.md** - Detailed migration guide
- **ARCHITECTURE_2ESP.md** - System architecture
- **INTEGRATION_CHECKLIST_2ESP.md** - Testing checklist

---

**Fixed by:** AI Assistant  
**Date:** 2024-12-05  
**ESP32 Core Version:** 3.3.1  
**Status:** ✅ Fixed and Ready
