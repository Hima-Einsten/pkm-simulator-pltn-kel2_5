# Deprecated Files & Folders - V2.0

## 🗑️ Removed in Version 2.0.0

### Folders Removed:

#### 1. `ESP_F_Aliran_Sekunder/`
**Reason:** Merged into ESP-E  
**Date Removed:** 2024-12-02  
**Replacement:** ESP-E now handles secondary flow via multiplexer #2

**What it contained:**
- Single flow visualizer for secondary cooling loop
- Direct LED control (16 pins)
- I2C slave at address 0x0B
- Channel 3 on PCA9548A

**Migration:**
- Hardware → Wire to ESP-E multiplexer #2 (EN=GPIO15, SIG=GPIO4)
- Software → Use `update_all_visualizers()` method

---

#### 2. `ESP_G_Aliran_Tersier/`
**Reason:** Merged into ESP-E  
**Date Removed:** 2024-12-02  
**Replacement:** ESP-E now handles tertiary flow via multiplexer #3

**What it contained:**
- Single flow visualizer for tertiary cooling loop
- Direct LED control (16 pins)
- I2C slave at address 0x0C
- Channel 4 on PCA9548A

**Migration:**
- Hardware → Wire to ESP-E multiplexer #3 (EN=GPIO2, SIG=GPIO16)
- Software → Use `update_all_visualizers()` method

---

### Files Deprecated (but kept for reference):

#### In `raspi_i2c_master.py`:
```python
# DEPRECATED - Show warnings when called
def update_esp_f()  # Line ~345
def update_esp_g()  # Line ~349
```

**Replacement:**
```python
update_all_visualizers(
    pressure_primary, pump_status_primary,
    pressure_secondary, pump_status_secondary,
    pressure_tertiary, pump_status_tertiary
)
```

---

## 📦 Archive Information

If you need the old code for reference:

### ESP-F Archive:
- **Last working version:** Git commit before V2.0
- **Backup location:** None (can restore from git history)
- **Key features:** Direct 16-LED control, simple animation

### ESP-G Archive:
- **Last working version:** Git commit before V2.0
- **Backup location:** None (can restore from git history)
- **Key features:** Direct 16-LED control, simple animation

---

## 🔄 How to Restore (if needed)

If you need the old 5-ESP system:

```bash
# Check git history
git log --oneline

# Find commit before V2.0
git checkout <commit-hash>

# Or restore specific folders
git checkout <commit-hash> -- ESP_F_Aliran_Sekunder/
git checkout <commit-hash> -- ESP_G_Aliran_Tersier/
```

---

## ✅ Current System (V2.0)

**Active ESP Modules:**
1. ESP-B (0x08) - Batang Kendali & Reaktor
2. ESP-C (0x09) - Turbin & Generator
3. ESP-E (0x0A) - 3-Flow Visualizer (Primer, Sekunder, Tersier)

**Total:** 3 ESP (was 5)

---

## 📊 Impact of Removal

| Aspect | Impact |
|--------|--------|
| Hardware Cost | -40% (2 fewer ESP32) |
| Complexity | Reduced (3 vs 5 modules) |
| Functionality | **Increased** (better animations) |
| Maintenance | Easier (less code) |
| Pin Usage | -50% (multiplexing) |

---

## 📝 Notes

- Old code is still in git history
- No functionality lost - actually improved!
- Migration path documented
- Test scripts updated

**Date:** 2024-12-02  
**Version:** 2.0.0  
**Status:** Archived
