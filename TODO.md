# 📋 TODO LIST - PKM PLTN Simulator Integration

**Last Updated:** 2024-12-04  
**Overall Progress:** 🟡 **60%** Complete  
**Status:** In Development  
**Target Completion:** January 2025

---

## 🎯 CRITICAL ISSUES (Must Fix First!)

### 🔴 **ISSUE #1: ESP-C - 2 Versions Exist**

**Problem:**
- `ESP_C/ESP_C_I2C/ESP_C_I2C.ino` (OLD - No humidifier support)
- `ESP_C/ESP_C_HUMIDIFIER.ino` (NEW - With humidifier support)

**Action Required:**
- [ ] **Decision:** Use `ESP_C_HUMIDIFIER.ino` (has GPIO 32, 33 for humidifiers)
- [ ] Backup old version: `mv ESP_C_I2C ESP_C_I2C_OLD_BACKUP`
- [ ] Replace with new: `cp ESP_C_HUMIDIFIER.ino ESP_C_I2C/ESP_C_I2C.ino`
- [ ] Test on hardware
- [ ] Delete `ESP_C_HUMIDIFIER.ino` after confirmation

**Why:** Only the new version supports humidifier control that the physical panel needs.

**Priority:** 🔴 **URGENT**  
**Estimated Time:** 30 minutes  
**Dependencies:** None

---

### 🔴 **ISSUE #2: ESP-B - Wrong I2C Protocol**

**Problem:**
```cpp
// CURRENT (WRONG):
Receive: 10 bytes (pressure + pump status)
  - Expects data from RasPi about pressure & pumps
  - Has button handling code (should be in RasPi)
  - Has OLED display code (should be in RasPi)
  - Has interlock logic (should be in RasPi)

// SHOULD BE (CORRECT):
Receive: 3 bytes (target rod positions)
  - Byte 0: Safety rod target (0-100%)
  - Byte 1: Shim rod target (0-100%)
  - Byte 2: Regulating rod target (0-100%)
```

**Action Required:**
- [ ] Open `ESP_B/ESP_B_I2C/ESP_B_I2C.ino`
- [ ] **Remove:**
  - [ ] Button handling code (lines with `digitalRead(BUTTON_*)`)
  - [ ] OLED display code (lines with `display.` or `oled.`)
  - [ ] Interlock logic (pressure checks, pump checks)
  - [ ] Emergency button handling
- [ ] **Update `onReceiveData()`:**
  - [ ] Change `RECEIVE_SIZE` from 10 to 3
  - [ ] Parse 3 bytes: `safety_target`, `shim_target`, `reg_target`
  - [ ] Move servos to target positions
  - [ ] Remove interlock checks (now in RasPi)
- [ ] **Keep:**
  - [ ] Servo motor control
  - [ ] Thermal kW calculation
  - [ ] `prepareSendData()` (16 bytes: positions + thermal)
- [ ] Test with serial monitor
- [ ] Test I2C communication

**Priority:** 🔴 **URGENT**  
**Estimated Time:** 2-3 hours  
**Dependencies:** None  
**Reference:** See `INTEGRATION_STATUS.md` Section B

---

### 🟡 **ISSUE #3: Raspberry Pi Main Program - Not Compatible**

**Problem:**
- Current `raspi_main.py` only supports:
  - 8 buttons (not 15)
  - 4 OLEDs (not 9)
  - No GPIO button handling
  - No humidifier integration

**Action Required:**
- [ ] Create NEW file: `raspi_main_panel.py`
- [ ] **Structure:**
  - [ ] Import `raspi_gpio_buttons.py`
  - [ ] Import `raspi_humidifier_control.py`
  - [ ] Import `raspi_i2c_master.py`
  - [ ] Create `PLTNController` class
  - [ ] Implement 5 threads:
    - [ ] Thread 1: Button polling (10ms)
    - [ ] Thread 2: Control logic (50ms)
    - [ ] Thread 3: OLED update (200ms)
    - [ ] Thread 4: ESP communication (100ms)
    - [ ] Thread 5: Data logging (1s)
- [ ] **Implement state variables:**
  - [ ] Rod positions (3x)
  - [ ] Pump status (3x)
  - [ ] Pressure
  - [ ] Thermal kW
  - [ ] Emergency flag
  - [ ] Humidifier commands (2x)
- [ ] **Implement button callbacks:**
  - [ ] 6 pump buttons (ON/OFF for 3 pumps)
  - [ ] 6 rod buttons (UP/DOWN for 3 rods)
  - [ ] 2 pressure buttons
  - [ ] 1 emergency button
- [ ] **Implement interlock logic:**
  - [ ] Check pressure >= 40 bar
  - [ ] Check primary pump ON
  - [ ] Check secondary pump ON
  - [ ] Check no emergency
- [ ] Test individually
- [ ] Integration test

**Priority:** 🟡 **HIGH**  
**Estimated Time:** 1 day  
**Dependencies:** Issue #2 (ESP-B protocol)  
**Reference:** See `INTEGRATION_STATUS.md` Section C

---

### 🟡 **ISSUE #4: raspi_i2c_master.py - Missing Methods**

**Problem:**
- No method to send 3 bytes to ESP-B (rod targets)
- No method to send 12 bytes to ESP-C (with humidifier)
- Current methods use old protocol

**Action Required:**
- [ ] Open `raspi_i2c_master.py`
- [ ] **Add new method:**
  ```python
  def send_rod_targets_to_esp_b(self, safety, shim, regulating):
      """Send 3 bytes: target rod positions"""
  ```
- [ ] **Add new method:**
  ```python
  def receive_from_esp_b(self):
      """Receive 16 bytes: actual positions + thermal kW"""
  ```
- [ ] **Add new method:**
  ```python
  def send_to_esp_c_with_humidifier(self, rods, thermal_kw, sg_cmd, ct_cmd):
      """Send 12 bytes: rods + thermal + 2x humidifier commands"""
  ```
- [ ] **Add new method:**
  ```python
  def receive_from_esp_c(self):
      """Receive 12 bytes: power + state + humidifier status"""
  ```
- [ ] Test each method individually
- [ ] Test with actual ESP hardware

**Priority:** 🟡 **HIGH**  
**Estimated Time:** 2-3 hours  
**Dependencies:** Issue #2 (ESP-B update)  
**Reference:** See `INTEGRATION_STATUS.md` Section D

---

### 🟢 **ISSUE #5: 9-OLED Display Manager**

**Problem:**
- Current `raspi_oled_manager.py` only supports 4 OLEDs
- Uses TCA9548A (should use PCA9548A)
- No layout for 9 different displays

**Action Required:**
- [ ] Create NEW file: `raspi_panel_oled_9.py`
- [ ] **Implement `NineOLEDManager` class:**
  - [ ] Init with 2x PCA9548A addresses (0x70, 0x71)
  - [ ] Method: `select_oled(1-9)`
  - [ ] Method: `update_oled1_pressure(pressure)`
  - [ ] Method: `update_oled2_pump_primary(status)`
  - [ ] Method: `update_oled3_pump_secondary(status)`
  - [ ] Method: `update_oled4_pump_tertiary(status)`
  - [ ] Method: `update_oled5_safety_rod(position)`
  - [ ] Method: `update_oled6_shim_rod(position)`
  - [ ] Method: `update_oled7_regulating_rod(position)`
  - [ ] Method: `update_oled8_thermal_power(kw)`
  - [ ] Method: `update_oled9_system_status(data)`
- [ ] **Design layouts:**
  - [ ] Bar graphs for pressure & rods
  - [ ] Status text for pumps
  - [ ] Large font for thermal kW
- [ ] Test each OLED individually
- [ ] Test rapid switching (200ms cycle)

**Priority:** 🟢 **MEDIUM**  
**Estimated Time:** 1 day  
**Dependencies:** None (can work in parallel)  
**Reference:** See `INTEGRATION_STATUS.md` Section E

---

## 📅 WEEKLY PLAN

### **Week 1: Foundation (Days 1-5)**

**Day 1: Cleanup & Decision**
- [x] Remove unnecessary .md files ✅
- [ ] Choose ESP-C version (HUMIDIFIER.ino)
- [ ] Backup all current code
- [ ] Create Git branch: `integration-panel-control`
- [ ] Read through TODO.md

**Day 2: ESP-C Migration**
- [ ] Issue #1: Replace ESP-C with HUMIDIFIER version
- [ ] Upload to ESP32
- [ ] Test serial output
- [ ] Test humidifier relay (GPIO 32, 33)

**Day 3: ESP-B Protocol Update**
- [ ] Issue #2: Update ESP-B receive protocol
- [ ] Remove button/OLED code
- [ ] Test servo movement
- [ ] Test I2C communication

**Day 4: RasPi I2C Update**
- [ ] Issue #4: Add new methods to raspi_i2c_master.py
- [ ] Test send to ESP-B (3 bytes)
- [ ] Test receive from ESP-B (16 bytes)
- [ ] Test send to ESP-C (12 bytes)

**Day 5: Testing & Validation**
- [ ] Test ESP-B: Send rod targets, receive positions
- [ ] Test ESP-C: Send with humidifier, receive status
- [ ] Test ESP-E: Verify still works (no changes)
- [ ] Document any issues found

---

### **Week 2: Main Program (Days 6-10)**

**Day 6: Main Program Structure**
- [ ] Issue #3: Create raspi_main_panel.py
- [ ] Implement class structure
- [ ] Setup state variables
- [ ] Implement thread skeleton

**Day 7: Button Callbacks**
- [ ] Register 15 button callbacks
- [ ] Implement pump ON/OFF logic
- [ ] Implement rod UP/DOWN logic
- [ ] Implement pressure UP/DOWN
- [ ] Implement emergency button

**Day 8: Control Logic**
- [ ] Implement interlock checking
- [ ] Implement pump startup sequence
- [ ] Integrate humidifier controller
- [ ] Test logic with print statements

**Day 9: ESP Communication Thread**
- [ ] Thread 4: ESP communication implementation
- [ ] Send targets to ESP-B
- [ ] Receive from ESP-B
- [ ] Send to ESP-C with humidifier
- [ ] Send to ESP-E
- [ ] Test communication cycle

**Day 10: Testing Week 2**
- [ ] Test button → logic → ESP flow
- [ ] Test humidifier triggers (Shim+Reg >= 40%, Thermal >= 800kW)
- [ ] Test interlock prevents rod movement
- [ ] Fix bugs found

---

### **Week 3: Display & Integration (Days 11-15)**

**Day 11: OLED Manager**
- [ ] Issue #5: Create raspi_panel_oled_9.py
- [ ] Implement display selection
- [ ] Implement 9 update methods

**Day 12: OLED Layouts**
- [ ] Design pressure display with bar
- [ ] Design pump status displays
- [ ] Design rod position displays
- [ ] Design thermal power display
- [ ] Design system status display

**Day 13: Full Integration**
- [ ] Add OLED thread to main program
- [ ] Connect all 5 threads
- [ ] Test full system loop
- [ ] Monitor performance (CPU, timing)

**Day 14: Hardware Testing**
- [ ] Test with actual 15 buttons
- [ ] Test with actual 9 OLEDs
- [ ] Test with actual 2 humidifiers
- [ ] Test with actual 48 LEDs
- [ ] Test emergency shutdown

**Day 15: Bug Fixes & Tuning**
- [ ] Fix any issues found
- [ ] Tune thread timing if needed
- [ ] Optimize OLED update speed
- [ ] Add error handling
- [ ] Update documentation

---

## 🧪 TESTING CHECKLIST

### **Unit Tests (Individual Components)**

**ESP-B:**
- [ ] Upload updated firmware
- [ ] Serial monitor: Check receive 3 bytes
- [ ] Serial monitor: Check send 16 bytes
- [ ] Servo motors move to target positions
- [ ] Thermal kW calculation correct

**ESP-C:**
- [ ] Upload HUMIDIFIER version
- [ ] Serial monitor: Check receive 12 bytes
- [ ] Serial monitor: Check send 12 bytes
- [ ] GPIO 32: Humidifier SG relay clicks
- [ ] GPIO 33: Humidifier CT relay clicks
- [ ] Main relays work (turbine, generator, etc)

**ESP-E:**
- [ ] Verify no changes needed
- [ ] Test 3-flow LED animation
- [ ] Test animation speed changes

**RasPi GPIO Buttons:**
- [ ] Run `python3 raspi_gpio_buttons.py`
- [ ] Press each of 15 buttons
- [ ] Verify debouncing works
- [ ] Check callback triggering

**RasPi Humidifier Logic:**
- [ ] Run `python3 raspi_humidifier_control.py`
- [ ] Verify SG: ON when Shim>=40 AND Reg>=40
- [ ] Verify CT: ON when Thermal>=800kW
- [ ] Verify hysteresis works (no oscillation)

**RasPi 9-OLED:**
- [ ] Test select_oled(1) through select_oled(9)
- [ ] Verify correct PCA9548A channel
- [ ] Test update each display
- [ ] Verify no flickering

---

### **Integration Tests (System Level)**

**Scenario 1: Normal Startup**
- [ ] All pumps OFF initially
- [ ] Press "Tertiary Pump ON" → LED animate
- [ ] Press "Secondary Pump ON" → LED animate
- [ ] Press "Primary Pump ON" → LED animate
- [ ] Press "Safety Rod UP" → Servo moves, OLED updates
- [ ] Press "Shim Rod UP" → When >= 40%, SG humidifier ON
- [ ] Press "Regulating Rod UP" → When >= 40%, SG humidifier ON
- [ ] When thermal >= 800kW → CT humidifier ON
- [ ] All OLEDs show correct values

**Scenario 2: Interlock Test**
- [ ] Primary pump OFF → Rod buttons locked
- [ ] OLED shows "INTERLOCK NOT SATISFIED"
- [ ] Turn on all pumps → Rod buttons unlocked

**Scenario 3: Emergency Shutdown**
- [ ] Press EMERGENCY button
- [ ] All rods immediately → 0%
- [ ] All pumps → SHUTDOWN state
- [ ] Both humidifiers → OFF
- [ ] OLEDs show "EMERGENCY SHUTDOWN"

**Scenario 4: Humidifier Logic**
- [ ] Start with rods at 0%
- [ ] Move Shim to 50%, Reg at 30% → SG humid OFF
- [ ] Move Reg to 50% → SG humid ON
- [ ] Move Shim to 30% → SG humid OFF (hysteresis)
- [ ] Thermal 700kW → CT humid OFF
- [ ] Thermal 850kW → CT humid ON
- [ ] Thermal 720kW → CT humid still ON (hysteresis)
- [ ] Thermal 650kW → CT humid OFF

---

## 📊 PROGRESS TRACKING

### **Phase 1: Cleanup & Foundation (Days 1-5)**
**Status:** 🟡 20% Complete

- [x] Documentation cleanup ✅
- [ ] ESP-C version selection (0%)
- [ ] ESP-B protocol update (0%)
- [ ] RasPi I2C update (0%)
- [ ] Foundation testing (0%)

### **Phase 2: Main Program (Days 6-10)**
**Status:** ⚪ 0% Complete

- [ ] Main program structure (0%)
- [ ] Button callbacks (0%)
- [ ] Control logic (0%)
- [ ] ESP communication (0%)
- [ ] Integration testing (0%)

### **Phase 3: Display & Full Integration (Days 11-15)**
**Status:** ⚪ 0% Complete

- [ ] 9-OLED manager (0%)
- [ ] OLED layouts (0%)
- [ ] Full integration (0%)
- [ ] Hardware testing (0%)
- [ ] Bug fixes (0%)

---

## 🐛 KNOWN ISSUES

### **Issue #1: ESP-C Two Versions**
- **Status:** 🔴 Open
- **Severity:** Critical
- **Assigned:** Pending
- **Blocker:** Yes (blocks humidifier testing)

### **Issue #2: ESP-B Wrong Protocol**
- **Status:** 🔴 Open
- **Severity:** Critical
- **Assigned:** Pending
- **Blocker:** Yes (blocks RasPi integration)

### **Issue #3: RasPi Main Not Compatible**
- **Status:** 🔴 Open
- **Severity:** High
- **Assigned:** Pending
- **Blocker:** Partial (can work on other parts)

### **Issue #4: I2C Master Missing Methods**
- **Status:** 🟡 Open
- **Severity:** High
- **Assigned:** Pending
- **Blocker:** Partial

### **Issue #5: 9-OLED Manager Needed**
- **Status:** 🟢 Open
- **Severity:** Medium
- **Assigned:** Pending
- **Blocker:** No (can work in parallel)

---

## 📚 REFERENCE DOCUMENTS

**Read These First:**
1. `README.md` - Complete system documentation
2. `INTEGRATION_STATUS.md` - Detailed integration analysis
3. This file - `TODO.md` - What to do next

**For Specific Topics:**
- Hardware: See README.md → Hardware Components
- ESP-B Update: See INTEGRATION_STATUS.md → Section B
- ESP-C Choice: See INTEGRATION_STATUS.md → Section 2
- RasPi Main: See INTEGRATION_STATUS.md → Section C
- Humidifier: See README.md → Humidifier Control

**Code Examples:**
- Button handling: `raspi_gpio_buttons.py` (already done)
- Humidifier logic: `raspi_humidifier_control.py` (already done)
- ESP-E test: `test_esp_e_quick.py` (working example)

---

## 💾 BACKUP STRATEGY

**Before Starting Each Phase:**
```bash
# Create backup
git add .
git commit -m "Backup before Phase X"
git tag backup-phase-X

# Create branch for new work
git checkout -b phase-X-development
```

**Files to Backup Manually:**
- `ESP_C/ESP_C_I2C/ESP_C_I2C.ino` → `ESP_C_I2C_BACKUP_20241204.ino`
- `ESP_B/ESP_B_I2C/ESP_B_I2C.ino` → `ESP_B_I2C_BACKUP_20241204.ino`

---

## 🎯 SUCCESS CRITERIA

**System is considered "Complete" when:**

- [x] Single README.md with all documentation ✅
- [ ] ESP-C: Only 1 version exists (HUMIDIFIER)
- [ ] ESP-B: Protocol updated (3 bytes in, 16 bytes out)
- [ ] ESP-B: No button/OLED code
- [ ] RasPi: raspi_main_panel.py works with 15 buttons
- [ ] RasPi: 9 OLEDs display correctly
- [ ] RasPi: Interlock logic prevents illegal moves
- [ ] Humidifier SG: ON when Shim+Reg >= 40%
- [ ] Humidifier CT: ON when Thermal >= 800kW
- [ ] All 48 LEDs animate correctly
- [ ] Emergency button immediately shuts down
- [ ] System stable for 10+ minutes continuous operation
- [ ] All threads perform within timing requirements
- [ ] No I2C timeouts or communication errors
- [ ] Documentation updated with actual behavior

---

## 📞 HELP & SUPPORT

**If Stuck:**
1. Read relevant section in README.md
2. Check INTEGRATION_STATUS.md for details
3. Review code examples in working files
4. Test individual components before integration
5. Ask AI assistant by referencing this TODO.md

**AI Assistant Instructions:**
```
When you see this TODO.md file, you should:
1. Check the current phase and status
2. Focus on unchecked [ ] items in current phase
3. Reference INTEGRATION_STATUS.md for technical details
4. Update progress when tasks completed
5. Add new issues if found
6. Keep this file as single source of truth
```

---

## 📝 NOTES

**2024-12-04:**
- Created TODO.md as master tracking document
- Consolidated all tasks from INTEGRATION_STATUS.md
- Organized into weekly phases (15 days total)
- Added testing checklists
- Status: 60% complete overall, starting Week 1

**Next Session Should:**
1. Choose ESP-C version (Issue #1)
2. Start ESP-B protocol update (Issue #2)
3. Update progress in this file

---

**Last Updated By:** AI Assistant  
**Date:** 2024-12-04  
**Next Review:** When starting each new phase  
**Version:** 1.0

🎯 **Focus on Issue #1 and #2 this week!**
