# 🔧 Dual Mode Simplification - v4.0

**Tanggal:** 3 Januari 2026  
**Status:** ✅ In Progress

---

## 📋 Perubahan Utama

### **Konsep Baru:**

#### Mode Manual (Default - Always Active):
- User langsung bisa kontrol **tanpa tekan START dulu**
- Semua tombol kontrol langsung berfungsi
- Tidak ada flag `reactor_started` lagi

#### Mode Auto:
- Tekan tombol **START (GPIO 17)** → Trigger auto simulation
- Simulasi berjalan smooth ~70 detik
- Setelah selesai auto, kembali ke manual control

### **Jumlah Tombol: 17** (sesuai permintaan)
- **Dihapus:** Tombol REACTOR_START untuk manual mode
- **Dihapus:** Tombol START_AUTO_SIMULATION (GPIO 2)
- **Diubah:** Tombol START (GPIO 17) → fungsi baru: trigger auto simulation

---

## 📁 File yang Dimodifikasi

### 1. `raspi_gpio_buttons.py`

**Before:**
```python
# 18 buttons total
REACTOR_START = 17         # Manual mode start
START_AUTO_SIMULATION = 2  # Auto mode start
REACTOR_RESET = 27
```

**After:**
```python
# 17 buttons total
START_AUTO_SIMULATION = 17 # Trigger auto simulation (was REACTOR_START)
REACTOR_RESET = 27         # Reset simulation
```

---

### 2. `raspi_main_panel.py`

#### Changes in `PanelState`:
```python
# REMOVED:
reactor_started: bool = False

# Manual mode is now ALWAYS active by default
# No flag needed
```

#### Changes in Button Registration:
```python
# REMOVED:
self.button_manager.register_callback(ButtonPin.REACTOR_START, self.on_reactor_start)

# KEPT:
self.button_manager.register_callback(ButtonPin.START_AUTO_SIMULATION, self.on_start_auto_simulation)
self.button_manager.register_callback(ButtonPin.REACTOR_RESET, self.on_reactor_reset)

# Expected callbacks: 17 (was 18)
```

#### Changes in Event Handlers:
```python
# REMOVED all checks like this:
if not self.state.reactor_started:
    logger.warning("⚠️ Reactor not started! Press START button first")
    return

# NOW: All commands work immediately (manual mode always active)
```

#### Changes in Auto Simulation:
```python
# BEFORE:
if self.state.reactor_started:
    logger.warning("⚠️ Reactor already started! Reset first for auto mode")
    return

# Auto simulation still checks:
# - If auto_sim_running (prevent double start)
# BUT no longer checks reactor_started
```

---

## 🎮 User Experience

### **Sebelum (v3.x):**
```
1. Program start
2. Press START button (GPIO 17) → activate manual mode
3. Now can control pumps, rods, pressure
4. OR: Press AUTO_SIM button (GPIO 2) → auto mode
```

### **Sesudah (v4.0):**
```
1. Program start → MANUAL MODE SUDAH AKTIF
2. Langsung bisa control pumps, rods, pressure
3. OR: Press START button (GPIO 17) → auto simulation mode
```

---

## 🔄 Auto Simulation Flow (v4.0)

### Trigger:
```
Press: START AUTO SIMULATION button (GPIO 17 - GREEN)
```

### Sequence (70 seconds total):
```
Phase 1: System Init (3s)
Phase 2: Pressurizer (9s)     → 0-45 bar gradual
Phase 3: Pumps (9s)            → Tertiary → Secondary → Primary
Phase 4: Control Rods (25s)    → 0-50% gradual (Shim & Reg)
Phase 5: Steam Gen (5s)        → Humidifier SG1 & SG2 ON
Phase 6: Turbine (8s)          → Startup to 100% speed
Phase 7: Power Gen (5s)        → 0-250 MWe output
Phase 8: Cooling Tower (5s)    → CT1-4 humidifiers ON
Phase 9: Stable Operation      → Ready for manual control
```

### After Auto Complete:
```
simulation_mode = 'manual'
auto_sim_running = False
→ User can continue with manual control
```

---

## ⚠️ Breaking Changes

### Code yang Perlu Disesuaikan:

1. **Remove all `reactor_started` checks:**
```python
# OLD:
if not self.state.reactor_started:
    return

# NEW:
# Just remove this check - manual mode always active
```

2. **Update button count validation:**
```python
# OLD:
if callback_count != 18:

# NEW:
if callback_count != 17:
```

3. **Remove REACTOR_START event:**
```python
# OLD:
elif event == ButtonEvent.REACTOR_START:
    self.state.reactor_started = True

# NEW:
# Remove this entire block
```

---

## ✅ Implementation Checklist

### raspi_gpio_buttons.py:
- [x] Change REACTOR_START → START_AUTO_SIMULATION (GPIO 17)
- [x] Remove AUTO_SIM (GPIO 2)
- [x] Update button count: 18 → 17
- [x] Update BUTTON_NAMES dictionary

### raspi_main_panel.py:
- [x] Remove `reactor_started` from PanelState
- [x] Remove `on_reactor_start()` method
- [x] Remove REACTOR_START from ButtonEvent enum
- [x] Update button registration (17 callbacks)
- [ ] Remove all `reactor_started` checks in event handlers (IN PROGRESS)
- [ ] Update REACTOR_RESET logic
- [ ] Update START_AUTO_SIMULATION logic
- [ ] Update safety interlock (no reactor_started check)

### Testing:
- [ ] Test manual control without START
- [ ] Test auto simulation trigger
- [ ] Test RESET button
- [ ] Test emergency shutdown
- [ ] Verify 17 buttons registered

---

## 🐛 Known Issues to Fix

### Issue 1: Pressure/Pump/Rod checks
**Location:** Lines 435-553
**Problem:** All have `if not self.state.reactor_started` check
**Solution:** Remove this check

### Issue 2: REACTOR_START event handler
**Location:** Lines 570-576
**Problem:** Still processes REACTOR_START event
**Solution:** Remove entire block

### Issue 3: RESET logic
**Location:** Lines 578-604
**Problem:** Sets `reactor_started = False`
**Solution:** Remove this line

### Issue 4: AUTO_SIM logic
**Location:** Lines 606-622
**Problem:** Checks `reactor_started`
**Solution:** Remove check, only check `auto_sim_running`

---

## 📝 Next Steps

1. Remove all `reactor_started` checks from event handlers
2. Update RESET logic
3. Update AUTO_SIM logic
4. Update safety interlock check
5. Test with hardware
6. Update documentation

---

**Created:** 3 Januari 2026  
**Version:** 4.0 (In Progress)  
**Status:** ⏳ Implementation ongoing
