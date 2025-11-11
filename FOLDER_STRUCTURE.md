# 📁 Struktur Folder Project - PLTN Simulator v2.0

## 📊 Current Structure

```
pkm-simulator-PLTN/
│
├── .git/                                    # Git repository
├── .gitignore                               # Git ignore rules
├── .vscode/                                 # VS Code settings
│
├── 📁 ESP_A_Rev_1/                          # ⚠️ LEGACY - Will be replaced by RasPi
│   └── ESP_A_Rev_1.ino                      # Original ESP-A code (UART-based)
│
├── 📁 ESP_B_Rev_1/                          # ⚠️ NEEDS MODIFICATION for I2C Slave
│   └── ESP_B_Rev_1.ino                      # Control rod & reactor core
│
├── 📁 esp_c/                                # ⚠️ NEEDS MODIFICATION for I2C Slave
│   ├── platformio.ini
│   ├── src/
│   │   └── main.cpp                         # Turbine & generator
│   └── ...
│
├── 📁 ESP_E_Aliran_Primer/                  # ⚠️ NEEDS MODIFICATION for I2C Slave
│   └── ESP_E_Aliran_Primer.ino              # Primary flow visualizer
│
├── 📁 ESP_F_Aliran_Sekunder/                # ⚠️ NEEDS MODIFICATION for I2C Slave
│   └── ESP_F_Aliran_Sekunder.ino            # Secondary flow visualizer
│
├── 📁 ESP_G_Aliran_Tersier/                 # ⚠️ NEEDS MODIFICATION for I2C Slave
│   └── ESP_G_Aliran_Tersier.ino             # Tertiary flow visualizer
│
├── 📁 raspi_central_control/                # ✅ NEW - Raspberry Pi Control
│   ├── raspi_main.py                        # Main control program
│   ├── raspi_config.py                      # Configuration
│   ├── raspi_tca9548a.py                    # TCA9548A driver
│   ├── raspi_i2c_master.py                  # I2C Master communication
│   ├── raspi_oled_manager.py                # OLED display manager
│   ├── raspi_requirements.txt               # Python dependencies
│   └── raspi_README.md                      # Installation guide
│
├── 📄 ESP_B_I2C_Slave_Template.ino          # ✅ Template for ESP-B I2C migration
├── 📄 I2C_MIGRATION_QUICKGUIDE.md           # ✅ Quick migration guide
├── 📄 MIGRATION_PLAN.md                     # ✅ Detailed migration plan
├── 📄 RASPI_PACKAGE_SUMMARY.md              # ✅ RasPi package summary
└── 📄 README.md                             # Project overview
```

---

## 🎯 Recommended Structure (Clean & Organized)

### Option 1: Rename Files (Keep All in One Folder)

```
raspi_central_control/
├── main.py                  # (rename from raspi_main.py)
├── config.py                # (rename from raspi_config.py)
├── tca9548a.py              # (rename from raspi_tca9548a.py)
├── i2c_master.py            # (rename from raspi_i2c_master.py)
├── oled_manager.py          # (rename from raspi_oled_manager.py)
├── requirements.txt         # (rename from raspi_requirements.txt)
└── README.md                # (rename from raspi_README.md)
```

### Option 2: Organize by Module Type

```
raspi_central_control/
│
├── 📄 main.py               # Main entry point
├── 📄 config.py             # Global configuration
├── 📄 requirements.txt      # Dependencies
├── 📄 README.md             # Documentation
│
├── 📁 hardware/             # Hardware interface modules
│   ├── tca9548a.py          # I2C multiplexer
│   ├── i2c_master.py        # I2C communication
│   ├── oled_manager.py      # Display management
│   └── gpio_control.py      # GPIO & PWM (if separated)
│
├── 📁 controllers/          # Control logic
│   ├── pump_controller.py
│   ├── pressure_controller.py
│   └── alarm_controller.py
│
├── 📁 utils/                # Utilities
│   ├── logger.py
│   ├── data_logger.py
│   └── health_monitor.py
│
└── 📁 tests/                # Test files
    ├── test_i2c.py
    ├── test_oled.py
    └── test_gpio.py
```

---

## 🔄 Migration Status per Module

### ✅ COMPLETE (Ready to Use)
- **Raspberry Pi Control** - Full Python implementation
- **Documentation** - Migration guides & README
- **ESP-B Template** - I2C Slave template provided

### ⚠️ NEEDS WORK (ESP I2C Slave Migration)
- **ESP-B** - Modify to I2C Slave (use template)
- **ESP-C** - Modify to I2C Slave
- **ESP-E** - Modify to I2C Slave
- **ESP-F** - Modify to I2C Slave
- **ESP-G** - Modify to I2C Slave

### ⏸️ DEPRECATED
- **ESP-A** - Replaced by Raspberry Pi (keep for reference)

---

## 📝 Recommended Actions

### Immediate (Clean Up Current Structure):

1. **Rename files in `raspi_central_control/` untuk consistency:**
   ```bash
   cd raspi_central_control/
   mv raspi_main.py main.py
   mv raspi_config.py config.py
   mv raspi_tca9548a.py tca9548a.py
   mv raspi_i2c_master.py i2c_master.py
   mv raspi_oled_manager.py oled_manager.py
   mv raspi_requirements.txt requirements.txt
   mv raspi_README.md README.md
   ```

2. **Update import statements in Python files:**
   ```python
   # Old:
   import raspi_config as config
   from raspi_tca9548a import TCA9548A
   
   # New:
   import config
   from tca9548a import TCA9548A
   ```

3. **Move documentation to root or docs folder:**
   ```bash
   # Keep these at project root:
   # - README.md (main)
   # - MIGRATION_PLAN.md
   # - I2C_MIGRATION_QUICKGUIDE.md
   # - RASPI_PACKAGE_SUMMARY.md
   
   # Or create docs/ folder:
   mkdir docs/
   mv *MIGRATION*.md docs/
   mv RASPI_PACKAGE_SUMMARY.md docs/
   ```

### Next Phase (ESP Migration):

1. **Create ESP I2C templates for each module:**
   ```
   ├── ESP_B_I2C/
   │   └── ESP_B_I2C.ino
   ├── ESP_C_I2C/
   │   └── ESP_C_I2C.ino
   ├── ESP_E_I2C/
   │   └── ESP_E_I2C.ino
   ├── ESP_F_I2C/
   │   └── ESP_F_I2C.ino
   └── ESP_G_I2C/
       └── ESP_G_I2C.ino
   ```

2. **Keep old folders as backup:**
   ```bash
   # Rename old folders
   mv ESP_B_Rev_1/ ESP_B_Rev_1_UART_BACKUP/
   mv esp_c/ esp_c_UART_BACKUP/
   # etc...
   ```

---

## 🎨 Final Recommended Structure

```
pkm-simulator-PLTN/
│
├── 📁 raspi_central_control/        # ✅ Raspberry Pi (I2C Master)
│   ├── main.py
│   ├── config.py
│   ├── tca9548a.py
│   ├── i2c_master.py
│   ├── oled_manager.py
│   ├── requirements.txt
│   └── README.md
│
├── 📁 ESP_B_I2C/                    # ⏳ ESP-B (I2C Slave)
│   └── ESP_B_I2C.ino
│
├── 📁 ESP_C_I2C/                    # ⏳ ESP-C (I2C Slave)
│   └── ESP_C_I2C.ino
│
├── 📁 ESP_E_I2C/                    # ⏳ ESP-E (I2C Slave)
│   └── ESP_E_I2C.ino
│
├── 📁 ESP_F_I2C/                    # ⏳ ESP-F (I2C Slave)
│   └── ESP_F_I2C.ino
│
├── 📁 ESP_G_I2C/                    # ⏳ ESP-G (I2C Slave)
│   └── ESP_G_I2C.ino
│
├── 📁 docs/                         # Documentation
│   ├── MIGRATION_PLAN.md
│   ├── I2C_MIGRATION_QUICKGUIDE.md
│   └── RASPI_PACKAGE_SUMMARY.md
│
├── 📁 backups/                      # Old UART-based code
│   ├── ESP_A_Rev_1/
│   ├── ESP_B_Rev_1/
│   ├── esp_c/
│   ├── ESP_E_Aliran_Primer/
│   ├── ESP_F_Aliran_Sekunder/
│   └── ESP_G_Aliran_Tersier/
│
├── 📄 README.md                     # Main project README
├── 📄 .gitignore
└── 📄 LICENSE
```

---

## 🚀 Quick Command to Organize

Save this as `organize_structure.sh`:

```bash
#!/bin/bash

echo "🔄 Organizing project structure..."

# 1. Rename Python files in raspi_central_control
cd raspi_central_control/
mv raspi_main.py main.py 2>/dev/null
mv raspi_config.py config.py 2>/dev/null
mv raspi_tca9548a.py tca9548a.py 2>/dev/null
mv raspi_i2c_master.py i2c_master.py 2>/dev/null
mv raspi_oled_manager.py oled_manager.py 2>/dev/null
mv raspi_requirements.txt requirements.txt 2>/dev/null
mv raspi_README.md README.md 2>/dev/null
cd ..

# 2. Create docs folder and move documentation
mkdir -p docs
mv MIGRATION_PLAN.md docs/ 2>/dev/null
mv I2C_MIGRATION_QUICKGUIDE.md docs/ 2>/dev/null
mv RASPI_PACKAGE_SUMMARY.md docs/ 2>/dev/null

# 3. Create backups folder
mkdir -p backups

# 4. Move old ESP folders to backups (optional)
# Uncomment if you want to move:
# mv ESP_A_Rev_1 backups/
# mv ESP_B_Rev_1 backups/
# mv esp_c backups/
# mv ESP_E_Aliran_Primer backups/
# mv ESP_F_Aliran_Sekunder backups/
# mv ESP_G_Aliran_Tersier backups/

echo "✅ Project structure organized!"
echo ""
echo "📁 Structure:"
tree -L 2 -I '.git|.vscode|backups'
```

Run with:
```bash
chmod +x organize_structure.sh
./organize_structure.sh
```

---

## 📋 File Count Summary

| Category | Files | Status |
|----------|-------|--------|
| Raspberry Pi (Python) | 7 files | ✅ Complete |
| ESP I2C Slaves | 0 files | ⏳ To be created |
| Documentation | 4 files | ✅ Complete |
| Legacy ESP (UART) | 6 folders | 📦 Keep as backup |
| **Total** | **11+ files** | **~60% Complete** |

---

## 🎯 Current Status

**Raspberry Pi Side:** ✅ **100% Complete**
- All Python modules ready
- Documentation complete
- Ready to deploy

**ESP32 Side:** ⏳ **0% Complete**
- Need to convert 5 ESP modules to I2C Slave
- Template provided (ESP_B_I2C_Slave_Template.ino)
- Estimated: 1-2 weeks work

**Overall Project:** 🔄 **~60% Complete**

---

**Recommended Next Step:** 
1. Rename files in `raspi_central_control/` (remove "raspi_" prefix)
2. Test Raspberry Pi code on actual hardware
3. Start migrating ESP modules one by one

Need help with organizing? Let me know! 🚀
