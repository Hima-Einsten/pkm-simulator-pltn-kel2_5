# TODO: Penyesuaian Simulasi PLTN v1.0 → v3.x

## Perbandingan Arsitektur

### **Sistem Lama (v1.0)**
```
ESP-A (Master Panel) ──broadcast──→ ESP-E, F, G (Visualizers)
                     │
                     ├──────────→ ESP-B (Reactor + Rods)
                     │                    │
                     │                    └──→ ESP-C (Turbine + Generator)
                     
7 ESP Total:
- 1x ESP-A: Panel Kontrol (8 buttons, 4 OLED, PWM motor pompa)
- 1x ESP-B: Reactor Core (6 buttons + Emergency, 4 OLED, 3 servo)
- 1x ESP-C: Turbine & Generator (relay + motor control, state machine)
- 3x ESP-E/F/G: LED Visualizer (16 LED each)
```

### **Sistem Baru (v3.x)**
```
Raspberry Pi ──UART0──→ ESP-BC (Rods + Turbine + Humid + Motor)
             │
             └──UART3──→ ESP-E (48 LED Visualizer)

3 Devices Total:
- 1x RasPi: Panel Kontrol (17 buttons, 9 OLED, humidifier logic)
- 1x ESP-BC: Reactor + Turbine + Humid (3 servo, 4 motor, 6 relay)
- 1x ESP-E: LED Visualizer (48 LED for 3 flows)
```

---

## Feature Comparison Matrix

| Feature | v1.0 (OLD) | v3.x (NEW) | Status | Priority |
|---------|------------|------------|--------|----------|
| **Control Logic** |
| Button Step Size | 1% per press | 5% → 1% ✅ | Fixed | - |
| Button Hold | ❌ Single press only | ✅ Hold continuous | Implemented | - |
| Interlock Check | ✅ All pumps ON + P≥130 bar | ⚠️ P≥40 bar only | **Need Fix** | 🔴 HIGH |
| Emergency SCRAM | ✅ Dedicated button | ✅ Dedicated button | OK | - |
| Emergency Behavior | All rods → 0% + buzzer 1s | All rods → 0% + alarm | **Need Test** | 🟡 MED |
| Rod Lowering Rule | Rod1 only if Rod2&3=0% | ❌ No rule | **Need Add** | 🔴 HIGH |
| **Display & Feedback** |
| Pump Status Display | Status only (OFF/START/ON/STOP) | Status + PWM% | ✅ Fixed (no %) | - |
| System Status Display | Static status | ✅ Instructions + Status | Improved | - |
| Interlock Feedback | Buzzer beep if violated | ⚠️ Log warning only | **Need Add Buzzer** | 🟡 MED |
| **Actuator Control** |
| Servo Movement | ✅ Gradual (1% per 150ms) | ✅ Gradual (1% per 10ms) | OK | - |
| Motor PWM | ✅ Direct from RasPi | ✅ Via ESP-BC | OK | - |
| Pump Startup Sequence | Manual one-by-one | Manual one-by-one | OK | - |
| **Safety Features** |
| Interlock Bypass | ❌ Cannot bypass | ❌ Cannot bypass | OK | - |
| Emergency Reset | Auto after 1s | ❌ Need manual | **Need Fix** | 🟡 MED |
| Pressure Warning | Buzzer if >160 bar | ✅ Buzzer + blink | OK | - |
| **State Machine** |
| Turbine States | ✅ IDLE/START/RUN/STOP | ✅ IDLE/START/RUN/STOP | OK | - |
| Pump States | ✅ OFF/START/ON/STOP | ✅ OFF/START/ON/STOP | OK | - |
| Generator State | ✅ Linked to turbine | ❌ Not implemented | **Need Add** | 🟢 LOW |

---

## 🔴 HIGH PRIORITY FIXES

### **1. Interlock Logic - TIDAK SESUAI!**

#### ❌ **Current (v3.x):**
```python
# raspi_main_panel.py
def _check_interlock_internal(self):
    return self.state.pressure >= 40.0  # SALAH!
```

**Masalah:** 
- Hanya cek pressure ≥ 40 bar
- Tidak cek status pompa
- Rod bisa dioperasikan meskipun pompa OFF!

#### ✅ **Should Be (dari v1.0):**
```cpp
// ESP_B_Rev_1.ino line 399-405
bool rodsCanBeOperated = false;
if (receivedPumpPrimaryStatus == PUMP_ON &&      // Pompa 1 harus ON
    receivedPumpSecondaryStatus == PUMP_ON &&    // Pompa 2 harus ON
    receivedPumpTertiaryStatus == PUMP_ON &&     // Pompa 3 harus ON
    receivedPressure >= MIN_PRESSURE) {          // Pressure >= threshold
  rodsCanBeOperated = true;
}
```

**ACTION REQUIRED:**
```python
# File: raspi_main_panel.py
# Location: _check_interlock_internal()

def _check_interlock_internal(self):
    """
    Interlock: Batang kendali HANYA bisa dioperasikan jika:
    1. Reactor sudah START
    2. Pressure >= 40 bar (original: 130 bar)
    3. ALL pumps dalam status ON (2)
    """
    return (self.state.reactor_started and
            self.state.pressure >= 40.0 and
            self.state.pump_primary_status == 2 and      # ← ADD THIS
            self.state.pump_secondary_status == 2 and    # ← ADD THIS
            self.state.pump_tertiary_status == 2)        # ← ADD THIS
```

---

### **2. Rod Lowering Safety Rule - MISSING!**

#### ❌ **Current (v3.x):**
```python
# Semua rod bisa diturunkan kapan saja
elif event == ButtonEvent.SAFETY_ROD_DOWN:
    self.state.safety_rod = max(self.state.safety_rod - 1, 0)  # Langsung turun
```

#### ✅ **Should Be (dari v1.0):**
```cpp
// ESP_B_Rev_1.ino line 462-465
if (pos1 > 0) {
  if (pos2 == 0 && pos3 == 0) {  // Rod1 hanya bisa turun jika Rod2&3 sudah 0%
    pos1 -= stepSize;
  } else {
    // Buzzer warning - Rod2 dan Rod3 harus turun dulu!
    digitalWrite(buzzerPin, HIGH); 
    delay(200); 
    digitalWrite(buzzerPin, LOW);
  }
}
```

**Explanation:** 
- **Safety Rod (Rod1)** adalah rod paling kritis
- Harus diturunkan **TERAKHIR**
- Jika user coba turunkan Safety Rod saat Shim/Regulating masih naik → **BUZZER WARNING**

**ACTION REQUIRED:**
```python
# File: raspi_main_panel.py
# Location: SAFETY_ROD_DOWN event handler

elif event == ButtonEvent.SAFETY_ROD_DOWN:
    if not self.state.reactor_started:
        logger.warning("⚠️  Reactor not started!")
        return
    
    # NEW: Safety rod hanya bisa turun jika shim dan regulating sudah 0%
    if self.state.shim_rod > 0 or self.state.regulating_rod > 0:
        logger.warning("⚠️  Cannot lower Safety Rod! Lower Shim & Regulating first!")
        # Trigger buzzer warning
        if self.buzzer:
            self.buzzer.beep(duration=0.2)
        return
    
    self.state.safety_rod = max(self.state.safety_rod - 1, 0)
    logger.info(f"✓ Safety rod DOWN: {self.state.safety_rod}%")
```

---

### **3. Servo Not Moving - CRITICAL BUG!**

**Symptoms:**
- RasPi OLED shows rod=100% but physical servo at 0%
- ESP reset → servo jumps to max then drops to 0%

**Root Cause Analysis:**
```
v1.0: Button → ESP reads GPIO → servo.write() → INSTANT (< 10ms)
v3.x: Button → RasPi → UART → ESP → updateServos() → DELAYED (115-250ms)

Total latency v3.x: 10-25x SLOWER than v1.0!
```

**ACTION REQUIRED:**

#### Step 1: Add Debug Logging to ESP32
```cpp
// File: esp_utama_uart/esp_utama_uart.ino
// Location: updateServos() function

void updateServos() {
  // Track if any servo is moving
  bool servo_moving = false;
  
  // Add periodic debug output
  static unsigned long lastDebug = 0;
  if (millis() - lastDebug > 1000) {  // Every 1 second
    Serial.printf("🔧 SERVO STATUS:\n");
    Serial.printf("   Targets: S=%d, Sh=%d, R=%d\n", 
                  safety_target, shim_target, regulating_target);
    Serial.printf("   Actual:  S=%d, Sh=%d, R=%d\n", 
                  safety_actual, shim_actual, regulating_actual);
    lastDebug = millis();
  }
  
  // Smoothly move to target (1% per cycle)
  if (safety_actual < safety_target) {
    safety_actual++;
    servo_moving = true;
  }
  // ... rest of code
  
  if (servo_moving) {
    Serial.printf("⚡ Servos moving: [%d→%d, %d→%d, %d→%d]\n",
                  safety_actual, safety_target,
                  shim_actual, shim_target,
                  regulating_actual, regulating_target);
  }
}
```

#### Step 2: Verify Power Supply
- Servo needs **5V external power**, NOT 3.3V from ESP32
- Check connections:
  - Servo VCC → 5V supply
  - Servo GND → Common GND with ESP32
  - Servo Signal → ESP32 GPIO (13, 12, 14)

#### Step 3: Test Servo Manually
```cpp
// Temporary test code in setup()
void setup() {
  // ... existing setup
  
  // TEST: Move servo to 90° for 2 seconds
  Serial.println("🧪 SERVO TEST: Moving to 90°...");
  servo_safety.write(90);
  servo_shim.write(90);
  servo_regulating.write(90);
  delay(2000);
  
  Serial.println("🧪 SERVO TEST: Moving to 0°...");
  servo_safety.write(0);
  servo_shim.write(0);
  servo_regulating.write(0);
  delay(2000);
  
  Serial.println("✅ SERVO TEST: Complete!");
}
```

---

### **4. Pump PWM Startup Too Fast - MOTOR OVERLOAD RISK!**

**Problem:**
- v1.0: 0→255 PWM in 2.5 seconds (safe soft start)
- v3.x: 0→100% in 1 second (2.5x faster, risky!)

**ACTION REQUIRED:**
```cpp
// File: esp_utama_uart/esp_utama_uart.ino
// Location: updatePumpSpeeds() function

void updatePumpSpeeds() {
  // Update every 10ms
  
  // PRIMARY PUMP
  if (pump_primary_cmd == 1 && pump_primary_target < 100.0) {
    // BEFORE (TOO FAST):
    // pump_primary_target += 2.0;  // 0→100% in 0.5s
    
    // AFTER (MATCH v1.0 TIMING):
    pump_primary_target += 0.4;  // 0→100% in 2.5s (100 ÷ 0.4 × 10ms)
    
    if (pump_primary_target >= 100.0) {
      pump_primary_target = 100.0;
      pump_primary_cmd = 2;  // Status: ON
    }
  }
  
  // Apply same fix to SECONDARY and TERTIARY pumps
  if (pump_secondary_cmd == 1 && pump_secondary_target < 100.0) {
    pump_secondary_target += 0.4;  // ← CHANGE FROM 2.0
    if (pump_secondary_target >= 100.0) {
      pump_secondary_target = 100.0;
      pump_secondary_cmd = 2;
    }
  }
  
  if (pump_tertiary_cmd == 1 && pump_tertiary_target < 100.0) {
    pump_tertiary_target += 0.4;  // ← CHANGE FROM 2.0
    if (pump_tertiary_target >= 100.0) {
      pump_tertiary_target = 100.0;
      pump_tertiary_cmd = 2;
    }
  }
  
  // Rest of function remains same...
}
```

**Verification:**
- Startup time: 100% ÷ 0.4% × 10ms = 2500ms = 2.5 seconds ✅
- Matches v1.0 behavior

---

## 🟡 MEDIUM PRIORITY IMPROVEMENTS

### **3. Emergency SCRAM Behavior**

#### Current:
```python
elif event == ButtonEvent.EMERGENCY:
    logger.critical("🚨 EMERGENCY SHUTDOWN!")
    self.state.safety_rod = 0
    self.state.shim_rod = 0
    self.state.regulating_rod = 0
    self.state.emergency_active = True
```

#### Should Add:
```python
elif event == ButtonEvent.EMERGENCY:
    logger.critical("🚨 EMERGENCY SHUTDOWN (SCRAM)!")
    
    # 1. Lower all rods immediately
    self.state.safety_rod = 0
    self.state.shim_rod = 0
    self.state.regulating_rod = 0
    
    # 2. Mark emergency state
    self.state.emergency_active = True
    
    # 3. Trigger buzzer alarm for 1 second
    if self.buzzer:
        self.buzzer.emergency_alarm(duration=1.0)  # ← ADD THIS
    
    # 4. Auto-reset emergency flag after alarm
    threading.Timer(1.0, self._reset_emergency).start()  # ← ADD THIS

def _reset_emergency(self):
    """Reset emergency flag after alarm duration"""
    with self.state_lock:
        self.state.emergency_active = False
        logger.info("Emergency reset - system ready for operation")
```

---

### **4. Interlock Violation Feedback**

#### Current:
```python
if not self._check_interlock_internal():
    logger.warning("⚠️  Interlock not satisfied!")
    return  # Silent fail
```

#### Should Add:
```python
if not self._check_interlock_internal():
    logger.warning("⚠️  Interlock not satisfied!")
    
    # Give user feedback WHY interlock failed
    if self.state.pressure < 40.0:
        logger.warning(f"   → Pressure too low: {self.state.pressure:.1f} bar (need ≥40)")
    
    if self.state.pump_primary_status != 2:
        logger.warning("   → Primary pump not ON")
    if self.state.pump_secondary_status != 2:
        logger.warning("   → Secondary pump not ON")
    if self.state.pump_tertiary_status != 2:
        logger.warning("   → Tertiary pump not ON")
    
    # Buzzer beep for violation attempt
    if self.buzzer:
        self.buzzer.beep(duration=0.2)  # Short beep
    
    return
```

---

### **5. Adaptive Pressure Control - Missing Fast Mode**

**Problem:**
- v1.0: Hold button >500ms → Fast mode (5 bar/increment)
- v3.x: Always 1 bar/50ms (no acceleration)

**ACTION REQUIRED:**
```python
# File: raspi_main_panel.py

# Add to PanelState class
@dataclass
class PanelState:
    # ... existing fields
    
    # NEW: Track button hold duration for adaptive speed
    pressure_hold_start_time: float = 0.0
    pressure_up_hold_active: bool = False
    pressure_down_hold_active: bool = False

# Modify button_hold_thread()
def button_hold_thread(self):
    """Thread for detecting held buttons (rod and pressure control)"""
    logger.info("Button hold detection thread started")
    
    HOLD_BUTTONS = {
        ButtonPin.SAFETY_ROD_UP,
        ButtonPin.SAFETY_ROD_DOWN,
        ButtonPin.SHIM_ROD_UP,
        ButtonPin.SHIM_ROD_DOWN,
        ButtonPin.REGULATING_ROD_UP,
        ButtonPin.REGULATING_ROD_DOWN,
        ButtonPin.PRESSURE_UP,
        ButtonPin.PRESSURE_DOWN
    }
    
    while self.state.running:
        try:
            pressed = self.button_manager.check_hold_buttons(hold_interval=0.05)
            current_time = time.time()
            
            # PRESSURE UP - Adaptive speed
            if ButtonPin.PRESSURE_UP in pressed:
                with self.state_lock:
                    # Start tracking hold duration
                    if not self.state.pressure_up_hold_active:
                        self.state.pressure_up_hold_active = True
                        self.state.pressure_hold_start_time = current_time
                    
                    # Calculate hold duration
                    hold_duration = current_time - self.state.pressure_hold_start_time
                    
                    # Adaptive increment: slow first 500ms, then fast
                    if hold_duration > 0.5:
                        increment = 5.0  # FAST: 5 bar per event
                    else:
                        increment = 1.0  # SLOW: 1 bar per event
                    
                    # Queue event with increment value
                    self.button_event_queue.put(('PRESSURE_UP', increment))
            else:
                with self.state_lock:
                    self.state.pressure_up_hold_active = False
            
            # PRESSURE DOWN - Adaptive speed
            if ButtonPin.PRESSURE_DOWN in pressed:
                with self.state_lock:
                    if not self.state.pressure_down_hold_active:
                        self.state.pressure_down_hold_active = True
                        self.state.pressure_hold_start_time = current_time
                    
                    hold_duration = current_time - self.state.pressure_hold_start_time
                    
                    if hold_duration > 0.5:
                        increment = 5.0  # FAST
                    else:
                        increment = 1.0  # SLOW
                    
                    self.button_event_queue.put(('PRESSURE_DOWN', increment))
            else:
                with self.state_lock:
                    self.state.pressure_down_hold_active = False
            
            # Process other buttons (rods) with fixed 1% increment
            for pin in pressed & HOLD_BUTTONS:
                if pin not in [ButtonPin.PRESSURE_UP, ButtonPin.PRESSURE_DOWN]:
                    # Map pin to event (existing code)
                    if pin == ButtonPin.SAFETY_ROD_UP:
                        self.button_event_queue.put(ButtonEvent.SAFETY_ROD_UP)
                    # ... etc
            
            time.sleep(0.01)
            
        except Exception as e:
            logger.error(f"Error in button hold thread: {e}")
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(0.05)
    
    logger.info("Button hold detection thread stopped")

# Modify button_event_processor_thread() to handle tuple events
def button_event_processor_thread(self):
    # ... existing code
    
    # Handle pressure events with increment value
    if isinstance(event, tuple) and event[0] == 'PRESSURE_UP':
        increment = event[1]
        self.state.pressure = min(self.state.pressure + increment, 200.0)
        logger.info(f"✓ Pressure UP: {self.state.pressure:.1f} bar (+{increment})")
    
    elif isinstance(event, tuple) and event[0] == 'PRESSURE_DOWN':
        increment = event[1]
        self.state.pressure = max(self.state.pressure - increment, 0.0)
        logger.info(f"✓ Pressure DOWN: {self.state.pressure:.1f} bar (-{increment})")
```

**Verification:**
- Hold <500ms: 1 bar per 50ms = 20 bar/sec
- Hold >500ms: 5 bar per 50ms = 100 bar/sec (5x faster!)
- Matches v1.0 behavior ✅

---

### **6. Display Actual Servo Position (Not Just Target)**

**Problem:**
- OLED shows: "SHIM ROD 50%" (target from RasPi)
- Servo actual: 45% (still moving)
- User confusion!

**ACTION REQUIRED:**
```python
# File: raspi_oled_manager.py

def update_rod_display(self, rod_name: str, channel: int, display_obj: OLEDDisplay, 
                       target_position: int, actual_position: int = None):
    """
    Update control rod display with target and actual position
    
    Args:
        rod_name: Name of rod (e.g., "SAFETY", "SHIM", "REGULATING")
        channel: TCA9548A channel
        display_obj: OLED display object
        target_position: Target rod position (0-100%) - from RasPi state
        actual_position: Actual servo position (0-100%) - from ESP feedback
    """
    self.mux.select_display_channel(channel)
    
    data_key = f'{rod_name.lower()}_rod'
    current_data = (target_position, actual_position)
    
    if self.last_data.get(data_key) == current_data:
        return
    
    self.last_data[data_key] = current_data
    
    display_obj.clear()
    
    # Title
    display_obj.draw_text_centered(f"{rod_name} ROD", 1, display_obj.font_small)
    
    # Show target position (large font)
    display_obj.draw_text_centered(f"{target_position}%", 12, display_obj.font_large)
    
    # If actual position available, show difference
    if actual_position is not None and actual_position != target_position:
        # Show "moving" indicator
        diff = target_position - actual_position
        if diff > 0:
            indicator = f"↑{diff}%"  # Moving up
        else:
            indicator = f"↓{abs(diff)}%"  # Moving down
        
        display_obj.draw_text_centered(indicator, 24, display_obj.font_small)
    
    display_obj.show()

# Update raspi_main_panel.py to pass actual position
def esp_communication_thread(self):
    while self.state.running:
        # ... send command to ESP
        
        if success:
            # Get feedback from ESP
            esp_bc_data = self.uart_master.get_esp_bc_data()
            self.state.thermal_kw = esp_bc_data.kw_thermal
            self.state.turbine_speed = esp_bc_data.turbine_speed
            
            # NEW: Store actual servo positions from ESP
            self.state.safety_rod_actual = esp_bc_data.safety_actual
            self.state.shim_rod_actual = esp_bc_data.shim_actual
            self.state.regulating_rod_actual = esp_bc_data.regulating_actual
```

**Display Example:**
```
┌────────────┐
│ SHIM ROD   │  ← Title
│    50%     │  ← Target (large)
│   ↑5%      │  ← Moving indicator (small)
└────────────┘
```

---

## 🟢 LOW PRIORITY ENHANCEMENTS

### **5. Generator State Display**

v1.0 memiliki ESP-C yang menampilkan status generator terpisah. Bisa ditambahkan di OLED Thermal Power display:

```python
# raspi_oled_manager.py - update_thermal_power()

def update_thermal_power(self, thermal_kw: float, generator_online: bool):
    # ... existing code
    
    # Line 2: Generator status
    if generator_online:
        gen_text = "Gen: ONLINE"
    else:
        gen_text = "Gen: OFFLINE"
    
    display.draw_text(gen_text, 0, 21, display.font_small)
```

---

### **6. Startup Sequence Guidance**

Bisa ditambahkan di System Status OLED untuk memandu user:

```
Phase 1:
INSTRUKSI
Press START

Phase 2:
INSTRUKSI
Raise P to 40

Phase 3:
INSTRUKSI
Start Pump 1

Phase 4:
INSTRUKSI
Start Pump 2

Phase 5:
INSTRUKSI
Start Pump 3

Phase 6:
STATUS
All Pumps ON
P=150bar READY

Phase 7:
STATUS
Uap: Ya
Turbin&Gen:ON
```

---

## Implementation Checklist

### **Phase 1: Critical Safety & Actuator Control (HIGH Priority)**

#### ✅ Completed:
- [x] Button step size changed from 5% → 1%
- [x] Button hold functionality implemented
- [x] Pump display fixed (removed PWM %)
- [x] System status display with instructions added
- [x] ESP busy flag removed

#### ⚠️ In Progress / To Fix:
- [ ] **Fix interlock logic** - add pump status check (CRITICAL!)
- [ ] **Add rod lowering safety rule** - Safety rod last (CRITICAL!)
- [ ] **Debug servo not moving** - add logging, verify power supply (CRITICAL!)
- [ ] **Slow down pump PWM startup** - 2.0% → 0.4% increment (CRITICAL!)
- [ ] Test all critical fixes together

**Estimated Time:** 2-3 hours  
**Risk Level:** 🔴 HIGH - Safety-critical issues

---

### **Phase 2: User Feedback & Control Improvements (MEDIUM Priority)**

- [ ] Add emergency auto-reset after 1 second
- [ ] Add buzzer feedback for interlock violation
- [ ] Add detailed logging for interlock failure reasons
- [ ] Implement adaptive pressure control (slow/fast mode)
- [ ] Display actual servo position (not just target)
- [ ] Add "moving" indicator on rod displays
- [ ] Test emergency SCRAM behavior

**Estimated Time:** 3-4 hours  
**Risk Level:** 🟡 MEDIUM - User experience improvements

---

### **Phase 3: Display & Visual Enhancement (LOW Priority)**

- [ ] Add generator status to Thermal Power OLED
- [ ] Enhance system status display with operational phases
- [ ] Add visual feedback for emergency state (blinking?)
- [ ] Add startup sequence phase indicators
- [ ] Test all OLED displays for consistency
- [ ] Optimize OLED update timing (reduce lag)

**Estimated Time:** 2-3 hours  
**Risk Level:** 🟢 LOW - Polish and refinement

---

### **Phase 4: Testing & Validation**

#### Test Sequence 1: Interlock Enforcement
```
1. ❌ Press START
2. ❌ Press PRESSURE UP (to 50 bar)
3. ❌ Try SHIM ROD UP → Should FAIL (pumps not ON) + buzzer beep
4. ❌ Start PUMP 1
5. ❌ Try SHIM ROD UP → Should FAIL (Pump 2,3 not ON) + buzzer beep
6. ❌ Start PUMP 2 and 3
7. ✅ Try SHIM ROD UP → Should SUCCESS (all conditions met)
8. ❌ Lower PRESSURE to 30 bar
9. ❌ Try SHIM ROD UP → Should FAIL (pressure too low) + buzzer beep
```

#### Test Sequence 2: Rod Lowering Safety
```
1. ✅ Complete startup (all pumps ON, P≥40)
2. ✅ Raise SHIM ROD to 50%
3. ✅ Raise REGULATING ROD to 30%
4. ✅ Raise SAFETY ROD to 20%
5. ❌ Try to lower SAFETY ROD → Should FAIL + BUZZER (Shim&Reg still up)
6. ✅ Lower REGULATING ROD to 0%
7. ❌ Try to lower SAFETY ROD → Should FAIL + BUZZER (Shim still up)
8. ✅ Lower SHIM ROD to 0%
9. ✅ Try to lower SAFETY ROD → Should SUCCESS (both Shim&Reg at 0%)
```

#### Test Sequence 3: Emergency SCRAM
```
1. ✅ Complete startup and raise all rods to 50%
2. ✅ Press EMERGENCY button
3. ✅ Verify:
   - All rods go to 0% immediately
   - Buzzer sounds for 1 second
   - Emergency flag set during buzzer
   - After 1 second, emergency flag auto-reset
   - System ready for operation again
```

#### Test Sequence 4: Servo Movement
```
1. ✅ Upload ESP32 code with debug logging
2. ✅ Open Serial Monitor (115200 baud)
3. ✅ Start RasPi program
4. ✅ Press SHIM ROD UP
5. ✅ Watch Serial Monitor:
   - Should see "✓ Received Rod Targets: Shim=1"
   - Should see "Servos Moving: Shim=0/1"
   - Should see servo angle change
6. ✅ Watch physical servo - should rotate smoothly
7. ✅ Watch OLED - should show position increasing 1% at a time
```

#### Test Sequence 5: Pump PWM Timing
```
1. ✅ Start all three pumps one by one
2. ✅ Time startup for each pump
3. ✅ Expected: 0→100% in approximately 2.5 seconds
4. ✅ Watch motor - should ramp up smoothly (not jerky)
5. ✅ Measure current draw - should be gradual increase
```

#### Test Sequence 6: Adaptive Pressure Control
```
1. ✅ Press PRESSURE UP once (quick tap)
   - Should increase by 1 bar
2. ✅ Hold PRESSURE UP for <500ms
   - Should increase by ~1 bar (slow mode)
3. ✅ Hold PRESSURE UP for >500ms
   - Should increase by 5 bar per increment (fast mode)
4. ✅ Release and press again
   - Should reset to slow mode
```

**Total Testing Time:** 4-6 hours  
**Success Criteria:** All tests pass without manual intervention

---

## Files to Modify (Priority Ordered)

### 🔴 **HIGH PRIORITY**

| File | Changes | Lines | Complexity |
|------|---------|-------|------------|
| `raspi_main_panel.py` | Interlock logic (add pump check) | ~10 | Low |
| `raspi_main_panel.py` | Safety rod lowering rule | ~15 | Low |
| `esp_utama_uart.ino` | Add servo debug logging | ~20 | Low |
| `esp_utama_uart.ino` | Slow down pump PWM (0.4%) | ~6 | Low |

**Total:** ~50 lines, 1-2 hours work

---

### 🟡 **MEDIUM PRIORITY**

| File | Changes | Lines | Complexity |
|------|---------|-------|------------|
| `raspi_main_panel.py` | Emergency auto-reset | ~15 | Medium |
| `raspi_main_panel.py` | Interlock violation feedback | ~20 | Low |
| `raspi_main_panel.py` | Adaptive pressure control | ~80 | High |
| `raspi_oled_manager.py` | Display actual position | ~40 | Medium |

**Total:** ~155 lines, 3-4 hours work

---

### 🟢 **LOW PRIORITY**

| File | Changes | Lines | Complexity |
|------|---------|-------|------------|
| `raspi_oled_manager.py` | Generator status display | ~20 | Low |
| `raspi_oled_manager.py` | Startup phase indicators | ~40 | Medium |
| `raspi_oled_manager.py` | Emergency visual feedback | ~15 | Low |

**Total:** ~75 lines, 2-3 hours work

---

## Risk Assessment

### **Critical Risks (Must Fix Before Use)**

1. ⚠️ **Servo Not Moving**
   - **Impact:** Reactor control rods tidak berfungsi → simulasi tidak realistis
   - **Likelihood:** High (currently broken)
   - **Mitigation:** Debug logging + power supply check + manual test

2. ⚠️ **Interlock Bypass**
   - **Impact:** Rods bisa dioperasikan tanpa pompa → tidak aman secara simulasi
   - **Likelihood:** High (currently possible)
   - **Mitigation:** Add pump status check to interlock logic

3. ⚠️ **Pump PWM Too Fast**
   - **Impact:** Motor bisa overload atau burn out
   - **Likelihood:** Medium (depends on motor rating)
   - **Mitigation:** Reduce ramp-up speed to 2.5 seconds

### **Medium Risks (Should Fix Soon)**

4. ⚠️ **No Safety Rod Lowering Rule**
   - **Impact:** Shutdown sequence tidak sesuai prosedur reaktor nyata
   - **Likelihood:** Medium (user bisa bypass)
   - **Mitigation:** Add rule: Safety rod only if Shim&Reg at 0%

5. ⚠️ **No Adaptive Pressure Control**
   - **Impact:** User experience kurang baik (lambat naik pressure)
   - **Likelihood:** Low (annoying but not critical)
   - **Mitigation:** Add hold duration detection

### **Low Risks (Nice to Have)**

6. ℹ️ **Display Shows Target Not Actual**
   - **Impact:** User confusion tentang posisi actual
   - **Likelihood:** Medium
   - **Mitigation:** Show both target and actual with indicator

---

## Performance Optimization Notes

### **Current Bottlenecks:**

1. **UART Communication Latency:** ~50-100ms per cycle
   - Unavoidable with current architecture
   - RasPi → ESP communication inherently slower than ESP-to-ESP

2. **Multi-threaded Overhead:** 7 threads running
   - Button polling: 10ms
   - Button hold: 10ms  
   - Event processor: blocking queue
   - Control logic: 200ms
   - ESP comm: 50ms
   - OLED update: 100ms
   - Health monitor: 1000ms

3. **OLED Update Lag:** 100ms cycle
   - Can be improved to update immediately after state change
   - Trade-off: More I2C traffic vs faster visual feedback

### **Optimization Recommendations:**

1. ✅ **Already Optimized:**
   - Event queue pattern prevents blocking
   - OLED only updates when data changes
   - UART communication batched (not per-actuator)

2. ⚠️ **Can Be Improved:**
   - Merge button_polling and button_hold threads → reduce context switching
   - Update OLED immediately for critical displays (pressure, rods)
   - Add priority queue for emergency events

3. ❌ **Cannot Be Improved Without Architecture Change:**
   - UART latency (hardware limitation)
   - Multi-device communication overhead
   - Python GIL (Global Interpreter Lock) overhead

---

## Comparison Summary: v1.0 vs v3.x

### **What v3.x Does Better:**

✅ **Better Organization:**
- Clear separation: RasPi (control logic) vs ESP32 (actuators)
- Easier to maintain and debug
- Modular code structure

✅ **More Features:**
- 17 buttons vs 14 buttons (more control options)
- 9 OLED displays vs 8 displays (more feedback)
- Humidifier control integrated
- System status with instructions (better UX)

✅ **Better Display:**
- Instructional system status
- Centralized OLED management
- Consistent display logic

### **What v1.0 Does Better:**

✅ **Faster Response:**
- Direct GPIO → Servo (< 10ms)
- Direct GPIO → Motor PWM (< 10ms)
- No UART communication overhead

✅ **Simpler Logic:**
- Single-threaded per ESP
- No event queues
- Immediate feedback

✅ **More Realistic Control:**
- Proper interlock with pump status check
- Safety rod lowering rule enforced
- Adaptive pressure control (fast/slow mode)

### **Final Score:**

| Category | v1.0 | v3.x (Current) | v3.x (After Fixes) |
|----------|------|----------------|-------------------|
| Safety Logic | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Response Time | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| User Feedback | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Maintainability | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Features | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **TOTAL** | **20/25** | **16/25** | **23/25** ✅ |

---

**Status**: 📋 TODO List Updated with Actuator Control Fixes  
**Date**: 2025-12-17  
**Version**: v3.5 → v3.6 (After all fixes implemented)  
**Critical Issues**: 4 HIGH priority items must be fixed before production use

---

## Files to Modify

| Priority | File | Changes Needed |
|----------|------|----------------|
| 🔴 HIGH | `raspi_main_panel.py` | Interlock logic, rod safety rule |
| 🔴 HIGH | `raspi_buzzer_alarm.py` | Emergency alarm method |
| 🟡 MED | `raspi_main_panel.py` | Emergency auto-reset |
| 🟡 MED | `raspi_main_panel.py` | Interlock violation feedback |
| 🟢 LOW | `raspi_oled_manager.py` | Generator status display |
| 🟢 LOW | `raspi_oled_manager.py` | Enhanced system status |

---

## Testing Protocol

### **Test 1: Interlock Enforcement**
```
1. Press START
2. Press PRESSURE UP (to 50 bar)
3. Try to raise SHIM ROD → Should FAIL (pumps not ON)
4. Start PUMP 1
5. Try to raise SHIM ROD → Should FAIL (Pump 2,3 not ON)
6. Start PUMP 2 and 3
7. Try to raise SHIM ROD → Should SUCCESS
8. Lower PRESSURE to 30 bar
9. Try to raise SHIM ROD → Should FAIL (pressure too low)
```

### **Test 2: Rod Lowering Safety**
```
1. Complete startup (all pumps ON, P≥40)
2. Raise SHIM ROD to 50%
3. Raise REGULATING ROD to 30%
4. Raise SAFETY ROD to 20%
5. Try to lower SAFETY ROD → Should FAIL + BUZZER (Shim&Reg still up)
6. Lower REGULATING ROD to 0%
7. Try to lower SAFETY ROD → Should FAIL + BUZZER (Shim still up)
8. Lower SHIM ROD to 0%
9. Try to lower SAFETY ROD → Should SUCCESS
```

### **Test 3: Emergency SCRAM**
```
1. Complete startup and raise all rods to 50%
2. Press EMERGENCY button
3. Verify:
   - All rods go to 0% immediately
   - Buzzer sounds for 1 second
   - Emergency flag set for 1 second
   - After 1 second, system ready for operation
```

---

**Status**: 📋 TODO List Created  
**Date**: 2025-12-17  
**Version**: v3.5 → v3.6 (After fixes)
