# Perbandingan Detail: Kontrol Aktuator v1.0 vs v3.x

## 1. SERVO CONTROL (Control Rods)

### **v1.0 - ESP-B (Lama)**

#### Input Processing:
```cpp
// ESP_B_Rev_1.ino line 437-525
// IMMEDIATE CONTROL - Servo bergerak langsung saat button pressed

while (true) {
  // Cek button SETIAP LOOP (no delay)
  if (digitalRead(btnUp1) == LOW && prevBtnUp1State == HIGH) {
    // Button baru ditekan
    pos1 += stepSize;  // stepSize = 1%
    setServoPosition(servo1, pos1);
  } else if (digitalRead(btnUp1) == LOW && (currentTime - lastMoveTime > 150ms)) {
    // Button ditahan (hold) - interval 150ms
    pos1 += stepSize;
    setServoPosition(servo1, pos1);
  }
}

void setServoPosition(Servo& servo, int positionPercent) {
  int angle = map(positionPercent, 0, 100, 0, 180);
  servo.write(angle);  // LANGSUNG KIRIM KE SERVO
}
```

**Karakteristik:**
- ✅ **Direct control** - Button press → servo bergerak INSTANTLY
- ✅ **Hold button** - Continuous movement dengan interval 150ms
- ✅ **No communication delay** - Servo di ESP yang sama dengan button
- ✅ **Immediate feedback** - User langsung lihat servo bergerak

---

### **v3.x - RasPi + ESP-BC (Baru)**

#### Input Processing:
```python
# raspi_main_panel.py

# Thread 1: Button polling (10ms cycle)
def button_polling_thread(self):
    while self.state.running:
        self.button_manager.check_all_buttons()  # Edge detection
        time.sleep(0.01)

# Thread 2: Button hold detection (50ms interval)
def button_hold_thread(self):
    while self.state.running:
        pressed = self.button_manager.check_hold_buttons(hold_interval=0.05)
        for pin in pressed:
            self.button_event_queue.put(ButtonEvent.SHIM_ROD_UP)
        time.sleep(0.01)

# Thread 3: Event processor
def button_event_processor_thread(self):
    while self.state.running:
        event = self.button_event_queue.get()
        
        # Update STATE di RasPi
        self.state.shim_rod = min(self.state.shim_rod + 1, 100)
        # State hanya ada di memory RasPi!

# Thread 4: ESP communication (50ms cycle)
def esp_communication_thread(self):
    while self.state.running:
        time.sleep(0.05)  # 50ms cycle
        
        # Kirim TARGET ke ESP-BC via UART
        self.uart_master.update_esp_bc(
            safety=self.state.safety_rod,    # Target position
            shim=self.state.shim_rod,
            regulating=self.state.regulating_rod
        )
```

#### ESP32 Processing:
```cpp
// esp_utama_uart.ino

void handleUpdateCommand() {
  // Terima command dari RasPi
  safety_target = rods[0];  // Set target, bukan langsung gerakkan!
  shim_target = rods[1];
  regulating_target = rods[2];
}

void loop() {
  updateServos();  // Dipanggil setiap 10ms
  delay(10);
}

void updateServos() {
  // GRADUAL MOVEMENT - 1% per 10ms cycle
  if (safety_actual < safety_target) safety_actual++;
  if (safety_actual > safety_target) safety_actual--;
  
  int angle = map(safety_actual, 0, 100, 0, 180);
  servo_safety.write(angle);
}
```

**Karakteristik:**
- ⚠️ **Multi-layer delay:**
  1. Button hold interval: 50ms
  2. Event queue processing: variable
  3. ESP comm cycle: 50ms
  4. UART transmission: ~5ms
  5. ESP servo update: 10ms
  
  **Total latency: ~115ms minimum**

- ⚠️ **State vs Actual mismatch:**
  - RasPi OLED shows: `shim_rod = 50%` (STATE)
  - Physical servo actual: `shim_actual = 45%` (5% behind)
  
- ❌ **No immediate feedback** - User sees OLED update but servo masih bergerak

---

## 2. MOTOR PUMP CONTROL (PWM)

### **v1.0 - ESP-A (Lama)**

#### Direct PWM Control:
```cpp
// ESP_A_Rev_1.ino line 403-468

// Loop interval: 100ms
if (currentTime - lastPWMUpdateTime >= 100) {
  
  // STARTUP: PWM naik 10 per cycle (100ms)
  if (pumpPrimaryStatus == PUMP_STARTING) {
    pumpPrimaryPWM += 10;  // 0 → 10 → 20 → ... → 255
    if (pumpPrimaryPWM >= 255) {
      pumpPrimaryPWM = 255;
      pumpPrimaryStatus = PUMP_ON;
    }
  }
  
  // SHUTDOWN: PWM turun 1 per cycle (100ms)
  else if (pumpPrimaryStatus == PUMP_SHUTTING_DOWN) {
    pumpPrimaryPWM -= 1;  // 255 → 254 → 253 → ... → 0
    if (pumpPrimaryPWM <= 0) {
      pumpPrimaryPWM = 0;
      pumpPrimaryStatus = PUMP_OFF;
    }
  }
  
  // DIRECT PWM OUTPUT - No delay
  analogWrite(MOTOR_PRIM_PWM_PIN, pumpPrimaryPWM);
}
```

**Timing:**
- **Startup**: 0 → 255 dalam 2.5 detik (255/10 steps × 100ms)
- **Shutdown**: 255 → 0 dalam 25.5 detik (255/1 steps × 100ms)

**Karakteristik:**
- ✅ **Soft start** - PWM naik bertahap
- ✅ **Soft stop** - PWM turun perlahan (simula coast down)
- ✅ **Direct control** - ESP-A langsung output PWM ke motor
- ✅ **No communication overhead**

---

### **v3.x - RasPi + ESP-BC (Baru)**

#### RasPi → ESP-BC Command:
```python
# raspi_main_panel.py

# Button event (edge trigger only, no hold)
elif event == ButtonEvent.PUMP_PRIMARY_ON:
    self.state.pump_primary_status = 1  # STARTING
    
# ESP communication
self.uart_master.update_esp_bc(
    pump_primary=self.state.pump_primary_status,  # Send status, not PWM!
    # ...
)
```

#### ESP32 PWM Control:
```cpp
// esp_utama_uart.ino

void handleUpdateCommand() {
  pump_primary_cmd = pumps[0];  // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
}

void updatePumpSpeeds() {
  // Dipanggil setiap 10ms (bukan 100ms!)
  
  if (pump_primary_cmd == 1 && pump_primary_target < 100.0) {
    // STARTING: naik 1-2% per cycle (10ms)
    pump_primary_target += 2.0;  // Lebih cepat dari v1.0!
  }
  
  // Gradual movement
  if (pump_primary_actual < pump_primary_target) {
    pump_primary_actual += 1.0;  // 1% per 10ms
  }
  
  // PWM output (0-255)
  int pwm_value = map(pump_primary_actual, 0, 100, 0, 255);
  ledcWrite(MOTOR_PRIMARY_CHANNEL, pwm_value);
}
```

**Timing:**
- **Startup**: 0 → 100% dalam 1 detik (100 steps × 10ms)
  - v1.0: 2.5 detik
  - v3.x: **1 detik** (2.5x lebih cepat!) ⚠️

**Masalah:**
- ⚠️ **Terlalu cepat startup** - Motor bisa overload
- ❌ **Status vs PWM confusion** - RasPi kirim status (0-3), ESP konversi ke PWM
- ⚠️ **Communication latency** - Delay 50-100ms sebelum ESP mulai naik PWM

---

## 3. PRESSURIZER CONTROL

### **v1.0 - ESP-A (Lama)**

#### Direct Variable Update:
```cpp
// ESP_A_Rev_1.ino line 320-364

void loop() {
  // Cek button SETIAP LOOP (no delay, immediate response)
  
  if (digitalRead(BTN_PRES_UP_PIN) == LOW) {
    // Debounce: 100ms
    if (currentTime - lastButtonPressTime > 100) {
      
      // HOLD detection: if held > 500ms → FAST increment
      if (currentTime - lastButtonPressTime > 500) {
        pressurizerPressure += 5.0;  // FAST: 5 bar per press
      } else {
        pressurizerPressure += 1.0;  // SLOW: 1 bar per press
      }
      
      // UPDATE OLED IMMEDIATELY
      updateOLED(2, &display2, "Pressurizer", String(pressurizerPressure, 1) + " bar");
      
      lastButtonPressTime = currentTime;
    }
  } else {
    // Reset timer saat button release
    lastButtonPressTime = 0;
  }
}
```

**Karakteristik:**
- ✅ **Immediate response** - Button → variable update INSTANTLY
- ✅ **Smart hold detection** - First 500ms: 1 bar/press, After: 5 bar/press
- ✅ **Direct OLED update** - Display langsung update saat button pressed
- ✅ **No communication** - Semua lokal di ESP-A

---

### **v3.x - RasPi (Baru)**

#### Event Queue Processing:
```python
# raspi_main_panel.py

# Thread 1: Button hold (50ms interval - FIXED interval, no adaptive)
def button_hold_thread(self):
    pressed = self.button_manager.check_hold_buttons(hold_interval=0.05)
    if ButtonPin.PRESSURE_UP in pressed:
        self.button_event_queue.put(ButtonEvent.PRESSURE_UP)

# Thread 2: Event processor
def button_event_processor_thread(self):
    event = self.button_event_queue.get()
    
    if event == ButtonEvent.PRESSURE_UP:
        # FIXED increment - 1 bar per event
        self.state.pressure = min(self.state.pressure + 1.0, 200.0)
        logger.info(f"✓ Pressure UP: {self.state.pressure:.1f} bar")

# Thread 3: OLED update (100ms cycle)
def oled_update_thread(self):
    time.sleep(0.1)
    self.oled_manager.update_all(self.state)
```

**Timing:**
- **Button hold** → event queue @ 50ms
- **Event process** → state update @ variable delay
- **OLED update** → display refresh @ 100ms
- **Total latency:** ~150ms

**Masalah:**
- ❌ **No adaptive speed** - Selalu 1 bar/50ms, tidak ada "fast mode"
- ⚠️ **Display lag** - OLED update 100ms after button press
- ⚠️ **Thread overhead** - 3 threads untuk 1 button!

---

## 4. USER INPUT PROCESSING COMPARISON

### **v1.0 Architecture**
```
Button Press
     ↓
ESP reads GPIO (immediate)
     ↓
Update local variable
     ↓
Update actuator (servo/PWM)
     ↓
Update OLED (immediate)

Total latency: < 10ms
```

### **v3.x Architecture**
```
Button Press
     ↓
RasPi GPIO read (10ms polling)
     ↓
Button hold detection (50ms interval)
     ↓
Event queue (variable delay)
     ↓
Event processor updates STATE
     ↓
OLED update (100ms cycle)
     ↓
ESP communication (50ms cycle)
     ↓
UART transmission (~5ms)
     ↓
ESP receives command
     ↓
ESP updates target
     ↓
ESP gradual movement (10ms per 1%)
     ↓
Actuator moves

Total latency: 115-250ms (10-25x slower!)
```

---

## CRITICAL ISSUES IN v3.x

### **Issue 1: Servo Not Moving**

**Root Cause:**
```
RasPi OLED shows rod=100% (STATE)
BUT ESP-BC servo actual=0% (PHYSICAL)

WHY?
1. RasPi sends target=100 via UART
2. ESP-BC receives command OK
3. ESP-BC sets safety_target=100 ✓
4. BUT updateServos() not being called! ✗
5. OR servo power supply problem
```

**Debug Steps:**
```cpp
// Add to esp_utama_uart.ino
void updateServos() {
  static unsigned long lastDebug = 0;
  if (millis() - lastDebug > 1000) {
    Serial.printf("SERVO DEBUG: target=[%d,%d,%d], actual=[%d,%d,%d]\n",
                  safety_target, shim_target, regulating_target,
                  safety_actual, shim_actual, regulating_actual);
    lastDebug = millis();
  }
  
  // ... existing code
}
```

---

### **Issue 2: Pump PWM Too Fast**

**v1.0:** 0 → 255 dalam 2.5 detik (safe startup)
**v3.x:** 0 → 100% dalam 1 detik (too fast!)

**Fix:**
```cpp
// esp_utama_uart.ino - updatePumpSpeeds()

// BEFORE
pump_primary_target += 2.0;  // 2% per 10ms = 100% in 0.5s (TOO FAST!)

// AFTER  
pump_primary_target += 0.5;  // 0.5% per 10ms = 100% in 2s (SAFER)
```

---

### **Issue 3: No Adaptive Pressure Control**

**v1.0:** Hold > 500ms → 5 bar/press (fast mode)
**v3.x:** Always 1 bar/50ms (fixed speed)

**Fix:** Add time-based acceleration
```python
# raspi_main_panel.py

class PanelState:
    pressure_hold_start_time: float = 0.0  # NEW

def button_hold_thread(self):
    pressed = self.button_manager.check_hold_buttons(hold_interval=0.05)
    
    if ButtonPin.PRESSURE_UP in pressed:
        # Track hold duration
        if self.state.pressure_hold_start_time == 0:
            self.state.pressure_hold_start_time = time.time()
        
        # Adaptive increment
        hold_duration = time.time() - self.state.pressure_hold_start_time
        if hold_duration > 0.5:  # Hold > 500ms
            increment = 5.0  # FAST: 5 bar
        else:
            increment = 1.0  # SLOW: 1 bar
        
        self.button_event_queue.put((ButtonEvent.PRESSURE_UP, increment))
    else:
        self.state.pressure_hold_start_time = 0  # Reset
```

---

## RECOMMENDATIONS

### **HIGH PRIORITY:**

1. **Fix Servo Control**
   - Add debug logging to ESP-BC
   - Verify updateServos() is being called
   - Check servo power supply (needs 5V, not 3.3V)

2. **Slow Down Pump Startup**
   - Change increment from 2% → 0.5% per cycle
   - Match v1.0 timing (2.5 seconds startup)

3. **Add Adaptive Pressure Control**
   - Implement hold duration detection
   - 0-500ms: 1 bar increment
   - >500ms: 5 bar increment

### **MEDIUM PRIORITY:**

4. **Reduce Display Latency**
   - Update OLED immediately after state change
   - Don't wait for 100ms cycle

5. **Add Direct Feedback**
   - Show "actual" position from ESP, not just "target"
   - Add "(moving...)" indicator when servo in motion

### **LOW PRIORITY:**

6. **Optimize Thread Architecture**
   - Consider merging button_hold and button_polling
   - Reduce number of threads for simpler logic

---

**Status**: 📊 Detailed comparison completed  
**Date**: 2025-12-17  
**Critical Issues Found**: 3 (Servo, Pump PWM, Pressure Control)
