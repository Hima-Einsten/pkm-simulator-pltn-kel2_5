# GPIO Pin Assignment Summary - PLTN Simulator

**Date:** 2024-12-11  
**System:** PKM PLTN Simulator v3.1  
**Total Buttons:** 17 push buttons

---

## 📍 Complete GPIO Pin Mapping (BCM Mode)

### **Pump Control (6 buttons)**

| Button | GPIO Pin | Function | Notes |
|--------|----------|----------|-------|
| Pump Primary ON | **GPIO 5** | Start primary pump | Must press START first |
| Pump Primary OFF | **GPIO 6** | Stop primary pump | Must press START first |
| Pump Secondary ON | **GPIO 13** | Start secondary pump | Must press START first |
| Pump Secondary OFF | **GPIO 19** | Stop secondary pump | Must press START first |
| Pump Tertiary ON | **GPIO 26** | Start tertiary pump | Must press START first |
| Pump Tertiary OFF | **GPIO 21** | Stop tertiary pump | Must press START first |

---

### **Control Rod Control (6 buttons)**

| Button | GPIO Pin | Function | Notes |
|--------|----------|----------|-------|
| Safety Rod UP | **GPIO 20** | Raise safety rod +5% | Requires START + interlock |
| Safety Rod DOWN | **GPIO 16** | Lower safety rod -5% | Requires START |
| Shim Rod UP | **GPIO 12** | Raise shim rod +5% | Requires START + interlock |
| Shim Rod DOWN | **GPIO 7** | Lower shim rod -5% | Requires START |
| Regulating Rod UP | **GPIO 8** | Raise regulating rod +5% | Requires START + interlock |
| Regulating Rod DOWN | **GPIO 25** | Lower regulating rod -5% | Requires START |

---

### **Pressurizer Control (2 buttons)**

| Button | GPIO Pin | Function | Notes |
|--------|----------|----------|-------|
| Pressure UP | **GPIO 24** | Increase pressure +5 bar | Requires START |
| Pressure DOWN | **GPIO 23** | Decrease pressure -5 bar | Requires START |

---

### **System Control (2 buttons)** ⭐ NEW

| Button | GPIO Pin | Function | Notes |
|--------|----------|----------|-------|
| REACTOR START | **GPIO 17** | Start reactor system | GREEN button - Enables all controls |
| REACTOR STOP | **GPIO 27** | Stop reactor system | YELLOW button - Only works if system at initial state |

---

### **Emergency Control (1 button)**

| Button | GPIO Pin | Function | Notes |
|--------|----------|----------|-------|
| EMERGENCY | **GPIO 18** | Emergency shutdown | RED button - Works anytime (no START required) |

---

## 📊 GPIO Usage Summary

### **Total GPIO Pins Used: 17**

```
GPIO 5  ✅ Pump Primary ON
GPIO 6  ✅ Pump Primary OFF
GPIO 7  ✅ Shim Rod DOWN
GPIO 8  ✅ Regulating Rod UP
GPIO 12 ✅ Shim Rod UP
GPIO 13 ✅ Pump Secondary ON
GPIO 16 ✅ Safety Rod DOWN
GPIO 17 ✅ REACTOR START (NEW - was reserved)
GPIO 18 ✅ EMERGENCY
GPIO 19 ✅ Pump Secondary OFF
GPIO 20 ✅ Safety Rod UP
GPIO 21 ✅ Pump Tertiary OFF
GPIO 23 ✅ Pressure DOWN
GPIO 24 ✅ Pressure UP
GPIO 25 ✅ Regulating Rod DOWN
GPIO 26 ✅ Pump Tertiary ON
GPIO 27 ✅ REACTOR STOP (NEW - was reserved)
```

### **Reserved/Unused GPIO:**

```
GPIO 2  ⚠️  I2C SDA (untuk OLED dan ESP32)
GPIO 3  ⚠️  I2C SCL (untuk OLED dan ESP32)
GPIO 4  🆓 Available
GPIO 9  🆓 Available
GPIO 10 🆓 Available
GPIO 11 🆓 Available
GPIO 14 🆓 Available (previously reserved)
GPIO 15 🆓 Available (previously reserved)
GPIO 22 🆓 Available
```

---

## 🔌 Wiring Diagram (Push Buttons)

### **Button Wiring (Standard Pull-up Configuration):**

```
For each button:

Button Terminal 1 ──────── GPIO Pin (5, 6, 7, 8, etc.)
                            │
                            │ (Internal pull-up resistor enabled)
                            │
Button Terminal 2 ──────── GND

When pressed: GPIO = LOW (0)
When released: GPIO = HIGH (1)
```

### **Code Configuration:**

```python
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Button pressed when:
if GPIO.input(pin) == GPIO.LOW:
    # Button is pressed
```

---

## 🎨 Physical Panel Layout Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│              PLTN REACTOR CONTROL PANEL v3.1                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SYSTEM CONTROL                                     │   │
│  │                                                      │   │
│  │  🟢 START (GPIO 17)     🔴 EMERGENCY (GPIO 18)     │   │
│  │  🟡 STOP  (GPIO 27)                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  PRESSURIZER                                                │
│  [▲ UP]   GPIO 24      [▼ DOWN]  GPIO 23                  │
├─────────────────────────────────────────────────────────────┤
│  PUMP CONTROL                                               │
│  Primary:    [ON] GPIO 5      [OFF] GPIO 6                 │
│  Secondary:  [ON] GPIO 13     [OFF] GPIO 19                │
│  Tertiary:   [ON] GPIO 26     [OFF] GPIO 21                │
├─────────────────────────────────────────────────────────────┤
│  CONTROL RODS                                               │
│  Safety Rod:      [↑] GPIO 20    [↓] GPIO 16              │
│  Shim Rod:        [↑] GPIO 12    [↓] GPIO 7               │
│  Regulating Rod:  [↑] GPIO 8     [↓] GPIO 25              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Button Priority & Behavior

### **Priority Order (Highest to Lowest):**

1. **EMERGENCY (GPIO 18)** - Always active, no prerequisites
2. **REACTOR START (GPIO 17)** - Must press first to enable other buttons
3. **REACTOR STOP (GPIO 27)** - Only works if system at initial state
4. **All other buttons** - Only work if `reactor_started = True`

### **Interlock Logic:**

```python
# Level 1: System Started Check (ALL buttons except EMERGENCY and START)
if not reactor_started:
    return "⚠️  Reactor not started! Press START button first."

# Level 2: Interlock Check (Only ROD UP buttons)
if not (pressure >= 40 and pump_primary == ON and pump_secondary == ON):
    return "⚠️  Interlock not satisfied!"

# Level 3: State Check (REACTOR STOP only)
if not (all_pumps_off and all_rods_zero and pressure_low):
    return "⚠️  Cannot stop reactor! Return to initial state first."
```

---

## 🔄 Operation Flow

### **Startup:**

```
1. Press START (GPIO 17)
   └─> reactor_started = True
   └─> All controls enabled

2. Operate reactor...
   └─> Press buttons as needed
   └─> System responds normally
```

### **Shutdown:**

```
1. Return to initial state:
   └─> Lower all rods to 0%
   └─> Stop all pumps
   └─> Lower pressure to 0 bar

2. Press STOP (GPIO 27)
   └─> Check if safe to stop
   └─> If yes: reactor_started = False
   └─> System reset
```

### **Emergency:**

```
Press EMERGENCY (GPIO 18)
   └─> Force all rods to 0%
   └─> Force all pumps to shutdown
   └─> emergency_active = True
   └─> reactor_started remains True
   
After emergency resolved:
   └─> Return to safe state
   └─> Press STOP (GPIO 27) to reset
```

---

## 📝 Code Reference

### **Button Pin Enum (raspi_gpio_buttons.py):**

```python
class ButtonPin(IntEnum):
    # Pump Control (6 buttons)
    PUMP_PRIMARY_ON = 5
    PUMP_PRIMARY_OFF = 6
    PUMP_SECONDARY_ON = 13
    PUMP_SECONDARY_OFF = 19
    PUMP_TERTIARY_ON = 26
    PUMP_TERTIARY_OFF = 21
    
    # Rod Control (6 buttons)
    SAFETY_ROD_UP = 20
    SAFETY_ROD_DOWN = 16
    SHIM_ROD_UP = 12
    SHIM_ROD_DOWN = 7
    REGULATING_ROD_UP = 8
    REGULATING_ROD_DOWN = 25
    
    # Pressurizer Control (2 buttons)
    PRESSURE_UP = 24
    PRESSURE_DOWN = 23
    
    # System Control (2 buttons)
    REACTOR_START = 17  # GREEN button
    REACTOR_STOP = 27   # YELLOW button
    
    # Emergency (1 button)
    EMERGENCY = 18      # RED button
```

---

## ✅ Testing Checklist

### **Hardware Wiring Check:**
- [ ] All 17 buttons wired to correct GPIO
- [ ] All buttons connected to GND
- [ ] No shorts between GPIO pins
- [ ] Pull-up resistors enabled in code

### **Software Check:**
- [ ] START button registered (GPIO 17)
- [ ] STOP button registered (GPIO 27)
- [ ] All callbacks check `reactor_started`
- [ ] EMERGENCY works without START

### **Functional Test:**
- [ ] Press START → System enabled
- [ ] Press control buttons → Work normally
- [ ] Restart program → Press control buttons → Blocked
- [ ] Press START → Control buttons work again
- [ ] Return to initial state → Press STOP → Success
- [ ] Try STOP with active systems → Blocked

---

## 🔧 Troubleshooting

### **Problem: Button tidak merespon**

```bash
# Check GPIO wiring
gpio readall

# Check button state
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO 17 state:', GPIO.input(17))
# Should be: 1 (not pressed), 0 (pressed)
"
```

### **Problem: START button tidak enable kontrol**

```bash
# Check log
tail -f pltn_simulator.log | grep "reactor_start"

# Should see:
# [INFO] >>> Callback: on_reactor_start
# [INFO] 🟢 REACTOR SYSTEM STARTED
```

### **Problem: STOP button tidak work**

```bash
# Check system state
# Must be:
# - All pumps OFF (status = 0)
# - All rods 0%
# - Pressure < 5 bar

# Check log for specific reason
tail -f pltn_simulator.log | grep "Cannot stop"
```

---

## 📊 GPIO Comparison (Before vs After)

| Function | OLD GPIO | NEW GPIO | Status |
|----------|----------|----------|--------|
| REACTOR START | GPIO 15 (reserved) | **GPIO 17** | ✅ Changed |
| REACTOR STOP | GPIO 14 (reserved) | **GPIO 27** | ✅ Changed |

**Reason for change:** GPIO 14 and 15 are typically reserved for UART/SPI on some Raspberry Pi configurations.

**New GPIO 17 and 27:** Safe to use, no conflicts with I2C or other peripherals.

---

## 🎉 Summary

✅ **Total Buttons:** 17  
✅ **System Control:** START (GPIO 17), STOP (GPIO 27)  
✅ **Emergency:** GPIO 18 (always active)  
✅ **All controls:** Protected by reactor_started flag  
✅ **GPIO 14, 15:** Now available for future use

---

**Status:** ✅ Implemented  
**Version:** 3.1  
**Date:** 2024-12-11  
**Hardware Ready:** YES (awaiting physical wiring)
