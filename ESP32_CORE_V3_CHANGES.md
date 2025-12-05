# 🔧 ESP32 Arduino Core v3.x Changes

## ⚠️ Breaking Changes

Starting from **ESP32 Arduino Core v3.0.0**, the PWM (LEDC) API has been simplified.

---

## 🔄 PWM API Changes

### ❌ Old API (v2.x):
```cpp
// Step 1: Setup channel
ledcSetup(channel, freq, resolution);

// Step 2: Attach pin to channel
ledcAttachPin(pin, channel);

// Step 3: Write PWM value using channel
ledcWrite(channel, dutyCycle);
```

### ✅ New API (v3.x):
```cpp
// Step 1: Attach pin directly (combines setup + attach)
ledcAttach(pin, freq, resolution);

// Step 2: Write PWM value using pin directly
ledcWrite(pin, dutyCycle);
```

---

## 📝 Changes Made to ESP-BC Code

### Before (v2.x):
```cpp
// PWM Channel definitions
#define PWM_CHANNEL_STEAM_GEN  0
#define PWM_CHANNEL_TURBINE    1
#define PWM_CHANNEL_CONDENSER  2
#define PWM_CHANNEL_COOLING    3

// Setup
ledcSetup(PWM_CHANNEL_STEAM_GEN, 5000, 8);
ledcSetup(PWM_CHANNEL_TURBINE, 5000, 8);
ledcSetup(PWM_CHANNEL_CONDENSER, 5000, 8);
ledcSetup(PWM_CHANNEL_COOLING, 5000, 8);

ledcAttachPin(MOTOR_STEAM_GEN_PIN, PWM_CHANNEL_STEAM_GEN);
ledcAttachPin(MOTOR_TURBINE_PIN, PWM_CHANNEL_TURBINE);
ledcAttachPin(MOTOR_CONDENSER_PIN, PWM_CHANNEL_CONDENSER);
ledcAttachPin(MOTOR_COOLING_PIN, PWM_CHANNEL_COOLING);

// Usage
ledcWrite(PWM_CHANNEL_STEAM_GEN, speed);
```

### After (v3.x):
```cpp
// No channel definitions needed!

// Setup (simplified)
ledcAttach(MOTOR_STEAM_GEN_PIN, 5000, 8);
ledcAttach(MOTOR_TURBINE_PIN, 5000, 8);
ledcAttach(MOTOR_CONDENSER_PIN, 5000, 8);
ledcAttach(MOTOR_COOLING_PIN, 5000, 8);

// Usage (use pin directly)
ledcWrite(MOTOR_STEAM_GEN_PIN, speed);
```

---

## ✅ Benefits of v3.x API

1. **Simpler:** No need to manage channel numbers
2. **Less code:** Combines 2 steps into 1
3. **Clearer:** Pin-centric instead of channel-centric
4. **Same performance:** No overhead

---

## 🔍 How to Check Your Version

```bash
# In Arduino IDE
Tools → Board → Boards Manager → Search "esp32"
# Check version number
```

Or check programmatically:
```cpp
Serial.println(ESP_ARDUINO_VERSION_MAJOR);
Serial.println(ESP_ARDUINO_VERSION_MINOR);
Serial.println(ESP_ARDUINO_VERSION_PATCH);
```

---

## 🚀 Migration Guide

If you have **old v2.x code**, do this:

### Step 1: Find all `ledcSetup()` calls
```cpp
ledcSetup(channel, freq, res);
```

### Step 2: Find corresponding `ledcAttachPin()` calls
```cpp
ledcAttachPin(pin, channel);
```

### Step 3: Replace with single `ledcAttach()`
```cpp
ledcAttach(pin, freq, res);
```

### Step 4: Update all `ledcWrite()` calls
```cpp
// Old: ledcWrite(channel, duty);
// New: ledcWrite(pin, duty);
```

### Step 5: Remove channel definitions
```cpp
// Delete these:
#define PWM_CHANNEL_XXX  0
```

---

## 📚 References

- [ESP32 Arduino Core v3.0.0 Release Notes](https://github.com/espressif/arduino-esp32/releases/tag/3.0.0)
- [LEDC API Documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html)

---

## ✅ Compatibility Status

| Component | v2.x | v3.x |
|-----------|------|------|
| **ESP-BC (esp_utama.ino)** | ❌ | ✅ Fixed |
| **ESP-E (ESP_E_I2C.ino)** | ✅ | ✅ No PWM used |

---

**Last Updated:** 2024-12-05  
**ESP32 Core Version:** 3.3.1  
**Status:** ✅ Compatible
