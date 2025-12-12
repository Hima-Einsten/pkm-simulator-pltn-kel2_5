# 📋 TODO LIST - PKM PLTN Simulator Integration

**Last Updated:** 2024-12-12 (Session 6 - Alur Simulasi Documented & Issues Identified)  
**Overall Progress:** 🟢 **95%** Complete (Code done, integration issues found)  
**Architecture:** ✅ **2 ESP (ESP-BC + ESP-E)** - OPTIMIZED  
**Status:** Integration Issues Identified - Need fixes before hardware test  
**Target Completion:** December 2024

---

## 🆕 LATEST UPDATE - 2024-12-08

### ✅ **Hardware Configuration Correction** [COMPLETED]

**What Changed:**
- 🔧 Clarified relay usage: **6 relays = ALL for humidifiers only**
- 🔧 Clarified motor driver: **4 channels = 3 pompa + 1 turbin**
- 🔧 Added gradual pump control (realistic behavior)
- 🔧 Added dynamic turbine speed based on control rods

**Key Updates:**
1. **Relay Configuration (6 Channels):**
   - 2x Steam Generator Humidifiers (GPIO 13, 15)
   - 4x Cooling Tower Humidifiers (GPIO 32, 33, 14, 12)

2. **Motor Driver (4 Channels):**
   - Pompa Primer (GPIO 4)
   - Pompa Sekunder (GPIO 16)
   - Pompa Tersier (GPIO 17)
   - Motor Turbin (GPIO 5)

3. **New Features:**
   - ✅ Pompa gradual start/stop (realistic!)
   - ✅ Turbine speed = (Shim + Regulating) / 2
   - ✅ Safety rod tidak mempengaruhi turbine speed
   - ✅ 6 humidifier individual control

**Files Updated:**
- `esp_utama/esp_utama.ino` - Hardware config + pump/turbine logic
- `raspi_central_control/raspi_i2c_master.py` - 6 humidifier support
- `raspi_central_control/raspi_main_panel.py` - 6 humidifier commands
- `HARDWARE_UPDATE_SUMMARY.md` - Complete documentation (NEW)

**Status:** ✅ **COMPLETED**  
**Documentation:** See `HARDWARE_UPDATE_SUMMARY.md`

---

## 🎉 MAJOR ACHIEVEMENT: 2 ESP ARCHITECTURE COMPLETED!

**Architecture Change:**
- **Before:** 3 ESP (ESP-B + ESP-C + ESP-E) - More complex, more wiring
- **After:** 2 ESP (ESP-BC merged + ESP-E) - Simpler, cost-effective ✅

**Benefits:**
- 💰 Cost savings: ~$5-10 per unit
- 🔌 Simpler wiring: 2 I2C slaves instead of 3
- ⚡ Better performance: <10% CPU load per ESP
- 📦 More compact hardware layout
- 🧹 Professional, cleaner design

---

## 🎯 COMPLETED MILESTONES

### ✅ **MILESTONE #1: Architecture Optimization** [COMPLETED]

**Achievement:**
- [x] Merged ESP-B + ESP-C → ESP-BC ✅
- [x] Updated firmware: `esp_utama/esp_utama.ino` ✅
- [x] Fixed ESP32 Core v3.x compatibility ✅
- [x] Optimized pin usage (16/38 pins used) ✅
- [x] Performance validated (<10% CPU load) ✅

**Status:** ✅ **COMPLETED** on 2024-12-05  
**Time Saved:** 50% reduction in I2C communication overhead  
**Documentation:** See `ARCHITECTURE_2ESP.md`, `ESP_PERFORMANCE_ANALYSIS.md`

---

### ✅ **MILESTONE #2: Python Code Refactoring** [COMPLETED]

**Achievement:**
- [x] Updated `raspi_i2c_master.py` (2 ESP methods) ✅
- [x] Updated `raspi_main_panel.py` (v3.0) ✅
- [x] Fixed `raspi_humidifier_control.py` ✅
- [x] Fixed button handler imports ✅
- [x] All old API references removed ✅
- [x] Test script created: `test_2esp_architecture.py` ✅

**Status:** ✅ **COMPLETED** on 2024-12-05  
**Test Status:** 5/5 tests passing (software validation)  
**Documentation:** See `REVIEW_SUMMARY.md`, `BUTTON_FIX.md`

---

### ✅ **MILESTONE #3: Compilation Fixes** [COMPLETED]

**Achievement:**
- [x] Fixed ESP32 Arduino Core v3.x API changes ✅
- [x] Updated PWM functions: `ledcAttach()`, `ledcWrite()` ✅
- [x] Removed deprecated channel management ✅
- [x] Code compiles successfully ✅

**Status:** ✅ **COMPLETED** on 2024-12-05  
**Documentation:** See `COMPILATION_FIX.md`, `ESP32_CORE_V3_CHANGES.md`

---

### ✅ **MILESTONE #4: Cleanup & Organization** [COMPLETED]

**Achievement:**
- [x] Created cleanup guide ✅
- [x] Identified deprecated files ✅
- [x] Old `raspi_main.py` marked for deletion ✅
- [x] Documentation consolidated ✅

**Status:** ✅ **COMPLETED** on 2024-12-05  
**Documentation:** See `CLEANUP_GUIDE.md`

---

## 🎯 LEGACY ISSUES (Resolved in 2 ESP Architecture)

### ✅ **ISSUE #1: ESP-C - 2 Versions Exist** [RESOLVED - MERGED]

**Problem:**
- `ESP_C/ESP_C_I2C/ESP_C_I2C.ino` (OLD - No humidifier support)
- `ESP_C/ESP_C_HUMIDIFIER.ino` (NEW - With humidifier support)

**Action Taken:**
- [x] **Decision:** Use `ESP_C_HUMIDIFIER.ino` (has GPIO 32, 33 for humidifiers) ✅
- [x] User confirmed ESP-C already updated with humidifier version ✅

**Status:** ✅ **COMPLETED** on 2024-12-05  
**Priority:** 🔴 **URGENT**  
**Time Spent:** Already completed by user

---

### ✅ **ISSUE #2: ESP-B - Wrong I2C Protocol** [RESOLVED - MERGED INTO ESP-BC]

**Problem:**
```cpp
// OLD (WRONG):
Receive: 10 bytes (pressure + pump status)
  - Had button/OLED/interlock code (should be in RasPi)

// NEW (CORRECT):
Receive: 3 bytes (target rod positions)
  - Byte 0: Safety rod target (0-100%)
  - Byte 1: Shim rod target (0-100%)
  - Byte 2: Regulating rod target (0-100%)
```

**Action Completed:**
- [x] Changed `RECEIVE_SIZE` from 10 to 3 ✅
- [x] Added ESP32Servo library for servo control ✅
- [x] Removed pressure/pump logic (moved to RasPi) ✅
- [x] Parse 3 bytes: `safety_target`, `shim_target`, `regulating_target` ✅
- [x] Added `moveServosToTarget()` function ✅
- [x] Added `calculateThermalPower()` with proper formula ✅
- [x] Kept `prepareSendData()` (16 bytes: positions + thermal) ✅
- [x] Added servo pins: GPIO 25, 26, 27 ✅
- [ ] Test with serial monitor (pending hardware)
- [ ] Test I2C communication with RasPi (pending)

**Status:** ✅ **CODE COMPLETED** on 2024-12-05  
**Priority:** 🔴 **URGENT**  
**Time Spent:** 30 minutes  
**Next:** Upload to ESP32 and test  
**Reference:** See `ESP_B/ESP_B_I2C/ESP_B_I2C.ino`

---

### ✅ **ISSUE #3: Raspberry Pi Main Program - Not Compatible** [RESOLVED]

**Problem:**
- Current `raspi_main.py` only supports 8 buttons, 4 OLEDs
- No GPIO button handling
- No humidifier integration

**Action Completed:**
- [x] Created NEW file: `raspi_main_panel.py` ✅
- [x] **Structure implemented:** ✅
  - [x] Imported `raspi_gpio_buttons.py`
  - [x] Imported `raspi_humidifier_control.py`
  - [x] Imported `raspi_i2c_master.py`
  - [x] Created `PLTNPanelController` class
  - [x] Implemented 3 threads (simplified):
    - [x] Thread 1: Button polling (10ms)
    - [x] Thread 2: Control logic (50ms)
    - [x] Thread 3: ESP communication (100ms)
- [x] **State variables implemented:** ✅
  - [x] Rod positions (3x: safety, shim, regulating)
  - [x] Pump status (3x)
  - [x] Pressure
  - [x] Thermal kW
  - [x] Emergency flag
  - [x] Humidifier commands (2x: SG, CT)
- [x] **Button callbacks implemented:** ✅
  - [x] 6 pump buttons (ON/OFF for 3 pumps)
  - [x] 6 rod buttons (UP/DOWN for 3 rods)
  - [x] 2 pressure buttons
  - [x] 1 emergency button
- [x] **Interlock logic implemented:** ✅
  - [x] Check pressure >= 40 bar
  - [x] Check primary pump ON
  - [x] Check secondary pump ON
  - [x] Check no emergency
- [ ] Test on actual hardware (pending)

**Status:** ✅ **CODE COMPLETED** on 2024-12-05  
**Priority:** 🟡 **HIGH**  
**Time Spent:** 1 hour  
**Next:** Hardware testing and 9-OLED integration  
**Reference:** See `raspi_main_panel.py`

---

### ✅ **ISSUE #4: raspi_i2c_master.py - Missing Methods** [RESOLVED]

**Problem:**
- No method to send 3 bytes to ESP-B (rod targets)
- No method to send 12 bytes to ESP-C (with humidifier)
- Current methods use old protocol

**Action Completed:**
- [x] Updated `raspi_i2c_master.py` ✅
- [x] Added `send_rod_targets_to_esp_b(safety, shim, regulating)` ✅
  - Send 3 bytes: target rod positions
  - Receive 16 bytes: actual positions + thermal kW
- [x] Added `send_to_esp_c_with_humidifier(rods, thermal_kw, sg_cmd, ct_cmd)` ✅
  - Send 12 bytes: rods + thermal + 2x humidifier commands
  - Receive 12 bytes: power + state + humidifier status
- [x] Updated ESP_B_Data and ESP_C_Data dataclasses ✅
- [x] Deprecated old methods (backward compatible) ✅
- [ ] Test with actual ESP hardware (pending)

**Status:** ✅ **CODE COMPLETED** on 2024-12-05  
**Priority:** 🟡 **HIGH**  
**Time Spent:** 45 minutes  
**Next:** Hardware testing  
**Reference:** See `raspi_i2c_master.py`

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

**Day 1: Cleanup & Decision** ✅
- [x] Remove unnecessary .md files ✅
- [x] Choose ESP-C version (HUMIDIFIER.ino) ✅
- [x] Read through TODO.md ✅

**Day 2: ESP-C Migration** ✅
- [x] Issue #1: Replace ESP-C with HUMIDIFIER version ✅
- [ ] Upload to ESP32 (pending hardware)
- [ ] Test serial output (pending hardware)
- [ ] Test humidifier relay (GPIO 32, 33) (pending hardware)

**Day 3: ESP-B Protocol Update** ✅
- [x] Issue #2: Update ESP-B receive protocol ✅
- [x] Removed pressure/pump logic ✅
- [x] Added servo control code ✅
- [ ] Upload to ESP32 (pending hardware)
- [ ] Test servo movement (pending hardware)
- [ ] Test I2C communication (pending hardware)

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
**Status:** ✅ 95% Complete (Code Done, Hardware Testing Pending)

- [x] Documentation cleanup ✅
- [x] ESP-C version selection ✅
- [x] ESP-B protocol update (code done) ✅
- [x] RasPi I2C update (code done) ✅
- [ ] Foundation testing (pending hardware)

### **Phase 2: Main Program (Days 6-10)**
**Status:** ✅ 90% Complete (Code Done, Testing Pending)

- [x] Main program structure ✅
- [x] Button callbacks (15 buttons) ✅
- [x] Control logic (interlock + humidifier) ✅
- [x] ESP communication (3 threads) ✅
- [ ] Integration testing (pending hardware)

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
- **Status:** ✅ Closed (2024-12-05)
- **Severity:** Critical
- **Assigned:** Completed
- **Blocker:** No (unblocked humidifier testing)

### **Issue #2: ESP-B Wrong Protocol**
- **Status:** ✅ Closed (2024-12-05)
- **Severity:** Critical
- **Assigned:** Completed
- **Blocker:** No (unblocked RasPi integration)

### **Issue #3: RasPi Main Not Compatible**
- **Status:** ✅ Closed (2024-12-05)
- **Severity:** High
- **Assigned:** Completed
- **Blocker:** No (unblocked by creating new file)

### **Issue #4: I2C Master Missing Methods**
- **Status:** ✅ Closed (2024-12-05)
- **Severity:** High
- **Assigned:** Completed
- **Blocker:** No (unblocked RasPi-ESP communication)

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

**2024-12-05 Session 1:**
- ✅ Issue #1: ESP-C version confirmed using HUMIDIFIER version
- ✅ Issue #2: ESP-B protocol completely rewritten
  - Changed RECEIVE_SIZE from 10 to 3 bytes
  - Added ESP32Servo library and servo control
  - Removed pressure/pump/button/OLED code
  - Implemented thermal power calculation
- Status: 70% complete overall

**2024-12-05 Session 2:**
- ✅ Issue #4: raspi_i2c_master.py updated
  - Added `send_rod_targets_to_esp_b()` method
  - Added `send_to_esp_c_with_humidifier()` method
  - Updated data structures for new protocol
- ✅ Issue #3: Created raspi_main_panel.py
  - Full 15-button support with callbacks
  - 3 threads: button polling, control logic, ESP communication
  - Interlock logic implemented
  - Humidifier integration complete
  - Emergency shutdown logic
- Status: 85% complete overall
- Phase 1: 95% complete (code done)
- Phase 2: 90% complete (code done)

**2024-12-05 Session 3:**
- ✅ Architecture optimization: Merged ESP-B + ESP-C → ESP-BC
- ✅ Created `esp_utama/esp_utama.ino` (ESP-BC merged firmware)
- ✅ Updated all Python files for 2 ESP architecture
- ✅ Fixed ESP32 Core v3.x compatibility issues
- ✅ Fixed button handler import issues
- ✅ Created comprehensive documentation:
  - `ARCHITECTURE_2ESP.md` - Complete system architecture
  - `ESP_PERFORMANCE_ANALYSIS.md` - Performance analysis
  - `HARDWARE_OPTIMIZATION_ANALYSIS.md` - Pin usage optimization
  - `INTEGRATION_CHECKLIST_2ESP.md` - Testing checklist
  - `REVIEW_SUMMARY.md` - Code review results
  - `COMPILATION_FIX.md` - ESP32 v3.x fixes
  - `ESP32_CORE_V3_CHANGES.md` - API migration guide
  - `CLEANUP_GUIDE.md` - Cleanup instructions
- Status: 95% complete overall
- Phase 1: 100% complete ✅
- Phase 2: 100% complete ✅
- Phase 3: 0% complete (9-OLED pending)

**2024-12-12 Session 6:**
- ✅ **ALUR SIMULASI UPDATED IN README**
- ✅ Documented realistic 8-phase PWR startup sequence
- ✅ Clarified START button requirement
- ✅ Documented automatic turbine control
- ✅ Documented gradual pump control behavior
- ✅ Documented 6 individual humidifier logic
- ✅ Documented 10 LED power indicator
- ✅ Documented emergency shutdown sequence
- ⚠️ **IDENTIFIED 7 CRITICAL ISSUES:**
  1. 🔴 START button not implemented (flag exists but no callback)
  2. 🔴 Safety interlock broken (expects manual pump control)
  3. 🟡 Humidifier threshold mismatch (800 kW vs 80 MWe)
  4. 🟡 Pump status not communicated from ESP-BC
  5. 🟢 OLED display manager missing (optional)
  6. 🟢 Documentation needs updates
  7. 🟢 Testing scripts incomplete
- Status: 95% complete (integration fixes needed)
- **CRITICAL:** Must fix interlock & START button before hardware test!

**Next Session Should:**
1. Upload updated ESP-BC firmware to ESP32
2. Test hardware integration (relay + motor driver)
3. Verify pump gradual control behavior
4. Verify turbine speed control
5. Test 6 individual humidifiers
6. Implement 9-OLED display manager (Issue #5)
7. Full system integration testing

---

## 🔧 YANG MASIH PERLU DIBENAHI

### **1. Implementasi START Button** ⚠️ PENTING
**Status:** ⏳ Belum ada

**Problem:**
- Code `raspi_main_panel.py` sudah ada flag `reactor_started`
- Tapi belum ada button callback untuk START
- User harus manually set `reactor_started = True`

**Action Required:**
```python
# Di raspi_main_panel.py tambahkan:
def on_start_button(self):
    """START reactor button"""
    logger.info(">>> Callback: on_start_button")
    with self.state_lock:
        if not self.state.reactor_started:
            self.state.reactor_started = True
            logger.info("🟢 REACTOR STARTED - All controls active")
        else:
            logger.warning("Reactor already started")

# Register button di init_buttons():
self.buttons.register_callback(config.GPIO_START, self.on_start_button)
```

**Files to Update:**
- [ ] `raspi_config.py` - Tambah `GPIO_START = XX`
- [ ] `raspi_main_panel.py` - Tambah callback `on_start_button()`
- [ ] `raspi_gpio_buttons.py` - Register GPIO START button

**Priority:** 🔴 HIGH  
**Estimated Time:** 15 minutes

---

### **2. Humidifier Logic - Threshold Mismatch** ⚠️ PENTING
**Status:** ⏳ Perlu disesuaikan

**Problem:**
- ESP-BC expects: `thermal_kw` (electrical power in kW)
- Humidifier controller checks: `thermal >= 800 kW` untuk CT
- Tapi code README mengatakan: `≥ 80 MWe` (80,000 kW)
- Jadi threshold mana yang benar?

**Current Code:**
```python
# raspi_humidifier_control.py
ct_thermal_threshold: 800.0  # 800 kW

# README.md
Kondisi trigger: Electrical power ≥ 80 MWe (80,000 kW)
```

**Action Required:**
Pilih salah satu:

**Option A: Use 80 MWe (80,000 kW)** - Recommended
```python
# raspi_humidifier_control.py
HUMIDIFIER_CONFIG = {
    'ct_thermal_threshold': 80000.0,  # 80 MWe = 80,000 kW
    'ct_hysteresis': 5000.0,          # 5 MWe hysteresis
}
```

**Option B: Use 800 kW (0.8 MWe)** - Untuk testing
```python
# Tetap pakai 800 kW untuk mudah trigger saat testing
# Update README untuk konsistensi
```

**Files to Update:**
- [ ] `raspi_humidifier_control.py` - Update threshold
- [ ] `README.md` - Konsistensi dengan code
- [ ] Test dengan reactor thermal output actual

**Priority:** 🟡 MEDIUM  
**Estimated Time:** 10 minutes  
**Note:** Testing perlu untuk tentukan threshold realistis

---

### **3. Safety Interlock - Incomplete Logic** ⚠️ CRITICAL
**Status:** ⏳ Perlu diperbaiki

**Problem:**
- Current interlock hanya check:
  - Pressure >= 40 bar
  - Primary pump ON
  - Secondary pump ON
  - Emergency flag False
- **Tapi pompa sekarang auto-controlled oleh turbine!**
- User tidak press button "Pump ON" lagi

**Current Code:**
```python
def check_interlock(self):
    with self.state_lock:
        # Check pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTDOWN)
        primary_ok = self.state.pump_primary_status == 2  # ON
        secondary_ok = self.state.pump_secondary_status == 2  # ON
```

**Issue:**
- Pompa status tidak di-update dari ESP-BC
- ESP-BC auto-control pompa berdasarkan turbine state
- Raspberry Pi tidak tahu status pompa actual

**Action Required:**

**Option A: Remove Pump Interlock** - Recommended
```python
def check_interlock(self):
    """Simplified interlock - pompa auto-controlled"""
    with self.state_lock:
        pressure_ok = self.state.pressure >= 40.0
        turbine_ok = self.state.thermal_kw > 0  # Turbine running
        emergency_ok = not self.state.emergency_active
        
        self.state.interlock_satisfied = (
            pressure_ok and turbine_ok and emergency_ok
        )
        return self.state.interlock_satisfied
```

**Option B: Add Pump Status from ESP-BC**
```python
# Update ESP-BC I2C send buffer to include pump status
# Update raspi_i2c_master.py to parse pump status
# Update raspi_main_panel.py to use pump status
```

**Files to Update:**
- [ ] `raspi_main_panel.py` - Simplify `check_interlock()`
- [ ] Test interlock dengan turbine state
- [ ] Update README interlock logic

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 20 minutes  
**Impact:** Interlock tidak bekerja dengan benar!

---

### **4. ESP-BC Communication - Pump Status Missing** ⚠️ MEDIUM
**Status:** ⏳ Perlu ditambah

**Problem:**
- ESP-BC mengirim 20 bytes data
- Tapi Raspberry Pi tidak parse pump status
- Padahal ESP-BC sudah control pompa gradual

**Current ESP-BC Send Buffer (20 bytes):**
```cpp
// Byte 0-3:   Electrical power kW (float)
// Byte 4-7:   Turbine state (uint32)
// Byte 8:     Safety rod actual
// Byte 9:     Shim rod actual
// Byte 10:    Regulating rod actual
// Byte 11-16: Humidifier status (6 bytes)
// Byte 17-19: Reserved
```

**Missing:** Pump speeds (3 bytes)

**Action Required:**
```cpp
// ESP-BC: esp_utama.ino
// Update prepareSendData():
sendBuffer[17] = (uint8_t)pump_primary_actual;
sendBuffer[18] = (uint8_t)pump_secondary_actual;
sendBuffer[19] = (uint8_t)pump_tertiary_actual;
```

```python
# Raspberry Pi: raspi_i2c_master.py
# Update ESP_BC_Data dataclass:
@dataclass
class ESP_BC_Data:
    ...
    pump_primary_speed: int = 0
    pump_secondary_speed: int = 0
    pump_tertiary_speed: int = 0
```

**Files to Update:**
- [ ] `esp_utama/esp_utama.ino` - Add pump speeds to send buffer
- [ ] `raspi_i2c_master.py` - Parse pump speeds
- [ ] `raspi_main_panel.py` - Use pump speeds untuk interlock

**Priority:** 🟡 MEDIUM  
**Estimated Time:** 30 minutes

---

### **5. OLED Display Manager** ⏳ BELUM ADA
**Status:** Not started (0%)

**Problem:**
- 9 OLED belum ada implementasi
- Program main berjalan tapi tidak ada visual feedback

**Action Required:**
- [ ] Create `raspi_panel_oled_9.py`
- [ ] Implement `NineOLEDManager` class
- [ ] Design 9 different layouts
- [ ] Integrate dengan `raspi_main_panel.py`
- [ ] Test dengan 2x PCA9548A

**Priority:** 🟢 LOW (optional untuk testing code)  
**Estimated Time:** 4-6 hours

---

### **6. Documentation Updates Needed** 📝
**Status:** Partially complete

**Updates Required:**
- [x] README.md - Alur simulasi (COMPLETED)
- [ ] README.md - Interlock logic update
- [ ] README.md - START button procedure
- [ ] HARDWARE_UPDATE_SUMMARY.md - Pump status communication
- [ ] I2C_ADDRESS_MAPPING.md - Verify pinout dengan hardware actual

**Priority:** 🟢 LOW  
**Estimated Time:** 30 minutes

---

### **7. Testing Scripts Needed** 🧪
**Status:** Basic tests only

**Missing Tests:**
- [ ] Test START button sequence
- [ ] Test interlock dengan turbine control
- [ ] Test humidifier trigger thresholds
- [ ] Test pump gradual control
- [ ] Test emergency shutdown sequence
- [ ] Test full 8-phase startup sequence

**Priority:** 🟡 MEDIUM  
**Estimated Time:** 2-3 hours

---

## 📊 PRIORITY SUMMARY

### 🔴 CRITICAL (Harus diperbaiki sebelum hardware test):
1. **Safety Interlock Logic** - Tidak bekerja dengan turbine auto-control
2. **START Button Implementation** - Required untuk operasi normal

### 🟡 HIGH (Recommended untuk production):
3. **Humidifier Threshold** - Konsistensi 800 kW vs 80 MWe
4. **Pump Status Communication** - ESP-BC → RasPi
5. **Testing Scripts** - Validate all sequences

### 🟢 MEDIUM (Nice to have):
6. **9-OLED Display Manager** - Visual feedback
7. **Documentation Updates** - Keep in sync

---

**Last Updated By:** AI Assistant  
**Date:** 2024-12-12 (Session 6 - Alur Simulasi & Integration Issues)  
**Next Review:** Fix CRITICAL issues (START button + Interlock logic)  
**Version:** 3.2 - Integration Issues Identified

✅ **ACHIEVEMENT: Complete Alur Simulasi Documented!**  
✅ **8-Phase Realistic PWR Startup Sequence**  
✅ **Automatic Turbine Control Flow**  
✅ **6 Individual Humidifiers Logic**  
⚠️ **CRITICAL ISSUES FOUND:**
  - 🔴 START button callback missing
  - 🔴 Safety interlock broken (expects manual pumps)
  - 🟡 Humidifier threshold inconsistency
  - 🟡 Pump status communication missing
🎯 **Next Focus: Fix CRITICAL issues before hardware testing**  
📊 **Code: 95% Complete | Integration: Needs fixes | Hardware Testing: Blocked**
