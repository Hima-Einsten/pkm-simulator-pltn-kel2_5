# GPIO Pin Conflict Analysis - UART Migration

**Date:** 2024-12-15  
**Issue:** Checking pin conflicts untuk UART communication  
**Status:** ⚠️ **CRITICAL CONFLICTS FOUND!**

---

## 🔴 **CRITICAL CONFLICTS DETECTED!**

### **Conflict 1: GPIO 16 - SAFETY ROD DOWN Button**

```
❌ EXISTING USE: Safety Rod DOWN button
❌ NEW USE: UART0 RX for ESP-BC (ttyAMA0)

PIN: GPIO 16
Function in current project: Button input (Safety Rod DOWN)
Proposed UART use: RX pin for ttyAMA0
```

**Impact:** 
- Safety rod button TIDAK AKAN BEKERJA jika pin ini digunakan untuk UART
- UART akan menerima noise dari button presses

### **Conflict 2: GPIO 17 - REACTOR START Button**

```
❌ EXISTING USE: Reactor START button (GREEN button - CRITICAL!)
❌ NEW USE: UART0 TX for ESP-BC (ttyAMA0)

PIN: GPIO 17
Function in current project: Button input (REACTOR START)
Proposed UART use: TX pin for ttyAMA0
```

**Impact:**
- START button (GREEN) TIDAK AKAN BEKERJA
- Tanpa START button, SELURUH SISTEM TIDAK BISA DIOPERASIKAN!
- UART akan terinterupsi oleh button presses

---

## ⚠️ **POTENTIAL CONFLICTS**

### **GPIO 4 dan GPIO 5 (ttyAMA2):**

```
⚠️  GPIO 4: Available (no conflict)
❌ GPIO 5: PUMP PRIMARY ON button

PIN: GPIO 5
Current use: Pump Primary ON button
Proposed UART use (if ttyAMA2 is UART3): TX pin
```

---

## 📊 **Pin Usage Summary**

### **UART Pins vs Button Pins:**

| GPIO | Current Function | UART Function | Conflict? |
|------|------------------|---------------|-----------|
| **GPIO 16** | Safety Rod DOWN | UART0 RX (ttyAMA0) | ❌ **YES** |
| **GPIO 17** | REACTOR START | UART0 TX (ttyAMA0) | ❌ **YES** |
| GPIO 14 | (Available) | UART0 TX (alt) | ✅ No |
| GPIO 15 | (Available) | UART0 RX (alt) | ✅ No |
| **GPIO 4** | (Available) | UART3 TX (ttyAMA2) | ✅ No |
| **GPIO 5** | Pump Primary ON | UART3 RX (ttyAMA2) | ❌ **YES** |
| GPIO 0 | (Available) | UART2 TX | ✅ No |
| GPIO 1 | (Available) | UART2 RX | ✅ No |
| GPIO 8 | Regulating Rod UP | UART4 TX | ❌ **YES** |
| GPIO 9 | (Available) | UART4 RX | ✅ No |

---

## ✅ **SOLUTION - Use Safe GPIO Pins**

### **Recommended Pin Mapping:**

Gunakan **GPIO 14/15** untuk ttyAMA0 dan **GPIO 0/1** atau **GPIO 4/9** untuk ttyAMA2:

#### **Option 1: GPIO 14/15 + GPIO 0/1 (Recommended)**

```
┌──────────────────────────────────────────────────┐
│ ESP-BC (ttyAMA0) - Safe Pins                     │
├──────────────────────────────────────────────────┤
│ ESP-BC GPIO 16 (RX2) ← RasPi GPIO 14 (TX, Pin 8) │
│ ESP-BC GPIO 17 (TX2) → RasPi GPIO 15 (RX, Pin 10)│
│ ESP-BC GND           ← RasPi GND (Pin 6)         │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ ESP-E (ttyAMA2 as UART2) - Safe Pins            │
├──────────────────────────────────────────────────┤
│ ESP-E GPIO 16 (RX2) ← RasPi GPIO 0 (TX, Pin 27)  │
│ ESP-E GPIO 17 (TX2) → RasPi GPIO 1 (RX, Pin 28)  │
│ ESP-E GND           ← RasPi GND (Pin 14)         │
└──────────────────────────────────────────────────┘
```

**Requires:** `dtoverlay=uart2` in `/boot/config.txt`

#### **Option 2: GPIO 14/15 + GPIO 4/9 (Alternative)**

```
┌──────────────────────────────────────────────────┐
│ ESP-BC (ttyAMA0) - Safe Pins                     │
├──────────────────────────────────────────────────┤
│ ESP-BC GPIO 16 (RX2) ← RasPi GPIO 14 (TX, Pin 8) │
│ ESP-BC GPIO 17 (TX2) → RasPi GPIO 15 (RX, Pin 10)│
│ ESP-BC GND           ← RasPi GND (Pin 6)         │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ ESP-E (ttyAMA2 as UART4) - Safe Pins            │
├──────────────────────────────────────────────────┤
│ ESP-E GPIO 16 (RX2) ← RasPi GPIO 9 (RX, Pin 21)  │
│ ESP-E GPIO 17 (TX2) → RasPi GPIO 4 (TX, Pin 7)   │
│ ESP-E GND           ← RasPi GND (Pin 20)         │
└──────────────────────────────────────────────────┘
```

**Requires:** `dtoverlay=uart4` in `/boot/config.txt`

---

## 🔧 **Configuration Updates Needed**

### **/boot/config.txt:**

**For Option 1 (GPIO 0/1):**
```bash
enable_uart=1
dtoverlay=uart2
```

**For Option 2 (GPIO 4/9):**
```bash
enable_uart=1
dtoverlay=uart4
```

### **raspi_config.py:**

```python
# UART Configuration (UPDATED - Safe pins)
UART_ESP_BC_PORT = '/dev/ttyAMA0'    # GPIO 14/15 (Pin 8/10) ✅ SAFE
UART_ESP_E_PORT = '/dev/ttyAMA2'     # GPIO 0/1 or 4/9 ✅ SAFE
UART_BAUDRATE = 115200
UART_TIMEOUT = 0.5
UART_UPDATE_INTERVAL = 0.1
```

---

## 📋 **Complete Safe Pin Mapping**

### **I2C (OLEDs):**
```
GPIO 2  (Pin 3)  → I2C SDA (TCA9548A)
GPIO 3  (Pin 5)  → I2C SCL (TCA9548A)
```

### **UART (ESP Communication):**
```
GPIO 14 (Pin 8)  → UART0 TX (ESP-BC) ✅ SAFE
GPIO 15 (Pin 10) → UART0 RX (ESP-BC) ✅ SAFE
GPIO 0  (Pin 27) → UART2 TX (ESP-E)  ✅ SAFE
GPIO 1  (Pin 28) → UART2 RX (ESP-E)  ✅ SAFE
```

### **Buttons (17 buttons):**
```
GPIO 5  → Pump Primary ON
GPIO 6  → Pump Primary OFF
GPIO 7  → Shim Rod DOWN
GPIO 8  → Regulating Rod UP
GPIO 12 → Shim Rod UP
GPIO 13 → Pump Secondary ON
GPIO 16 → Safety Rod DOWN         ✅ NO CONFLICT (not using this for UART)
GPIO 17 → REACTOR START           ✅ NO CONFLICT (not using this for UART)
GPIO 18 → EMERGENCY
GPIO 19 → Pump Secondary OFF
GPIO 20 → Safety Rod UP
GPIO 21 → Pump Tertiary OFF
GPIO 23 → Pressure DOWN
GPIO 24 → Pressure UP
GPIO 25 → Regulating Rod DOWN
GPIO 26 → Pump Tertiary ON
GPIO 27 → REACTOR STOP
```

---

## ⚡ **Action Required**

### **DO NOT USE GPIO 16/17 for UART!**

❌ **Wrong wiring (will break buttons):**
```
GPIO 16 → ESP UART RX  ← CONFLICT dengan Safety Rod DOWN
GPIO 17 → ESP UART TX  ← CONFLICT dengan REACTOR START
```

✅ **Correct wiring (safe):**
```
GPIO 14 → ESP-BC UART TX  ← No conflict
GPIO 15 → ESP-BC UART RX  ← No conflict
GPIO 0  → ESP-E UART TX   ← No conflict
GPIO 1  → ESP-E UART RX   ← No conflict
```

---

## 📝 **Updated Wiring Documentation**

### **UART_WIRING_GUIDE.md needs update:**

```markdown
❌ OLD (WRONG - Has conflicts):
ESP-BC: GPIO 16/17 → Conflicts with buttons!

✅ NEW (CORRECT - No conflicts):
ESP-BC: GPIO 14/15 (Pin 8/10)
ESP-E:  GPIO 0/1 (Pin 27/28)
```

---

## 🧪 **Testing After Fix**

### **Test 1: Verify no button conflicts**
```bash
# Test all 17 buttons work
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# Test critical buttons
buttons = {
    16: 'Safety Rod DOWN',
    17: 'REACTOR START',
    5: 'Pump Primary ON'
}

for pin, name in buttons.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    state = GPIO.input(pin)
    print(f'{name} (GPIO {pin}): {state}')

GPIO.cleanup()
"
```

### **Test 2: Verify UART on correct pins**
```bash
# Check which GPIO is mapped to ttyAMA0 and ttyAMA2
dmesg | grep ttyAMA

# Should see:
# fe201000.serial: ttyAMA0 at MMIO 0xfe201000 (GPIO 14/15)
# fe201400.serial: ttyAMA2 at MMIO 0xfe201400 (GPIO 0/1)
```

### **Test 3: UART communication**
```bash
python3 test_uart_esp.py
# All tests should pass without affecting buttons
```

### **Test 4: Full system test**
```bash
python3 raspi_main_panel.py

# Test sequence:
# 1. Press START button (GPIO 17) → Should work ✅
# 2. Press Safety Rod DOWN (GPIO 16) → Should work ✅
# 3. Check UART communication → Should work ✅
# 4. All should work simultaneously ✅
```

---

## 📊 **Pin Availability After UART**

### **Used Pins:**
- GPIO 2, 3: I2C (OLEDs)
- GPIO 14, 15: UART0 (ESP-BC)
- GPIO 0, 1: UART2 (ESP-E)
- GPIO 5-8, 12-13, 16-21, 23-27: Buttons (17)

### **Still Available:**
```
GPIO 4  🆓 Free
GPIO 9  🆓 Free
GPIO 10 🆓 Free
GPIO 11 🆓 Free
GPIO 22 🆓 Free
```

**Total used:** 24 / 27 usable GPIO
**Total free:** 5 GPIO (for future expansion)

---

## ✅ **FINAL RECOMMENDATION**

### **Use these pins for UART:**

```
ESP-BC (ttyAMA0):
- RasPi GPIO 14 (Pin 8)  → ESP-BC GPIO 16 (RX2)
- RasPi GPIO 15 (Pin 10) → ESP-BC GPIO 17 (TX2)
- RasPi GND (Pin 6)      → ESP-BC GND

ESP-E (ttyAMA2):
- RasPi GPIO 0 (Pin 27)  → ESP-E GPIO 16 (RX2)
- RasPi GPIO 1 (Pin 28)  → ESP-E GPIO 17 (TX2)
- RasPi GND (Pin 14)     → ESP-E GND
```

**Config:**
```bash
# /boot/config.txt
enable_uart=1
dtoverlay=uart2
```

**Result:**
- ✅ No button conflicts
- ✅ I2C still works (OLEDs)
- ✅ All 17 buttons functional
- ✅ UART communication stable
- ✅ 5 GPIO still available

---

**Status:** ⚠️ **WIRING GUIDE NEEDS UPDATE**

**Action:** Update all UART wiring documentation to use **GPIO 14/15 + GPIO 0/1** instead of GPIO 16/17!

**Priority:** 🔴 **CRITICAL** - Wrong pins will break button functionality!

