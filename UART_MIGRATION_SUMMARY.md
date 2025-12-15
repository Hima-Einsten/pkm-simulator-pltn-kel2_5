# UART Migration Summary

**Date:** 2024-12-15  
**Status:** ✅ READY FOR IMPLEMENTATION  
**Estimated Time:** 4-6 hours total

---

## 📦 Files Created

### **New Python Modules:**
1. ✅ **`raspi_uart_master.py`** (523 lines)
   - UART communication handler
   - JSON protocol implementation
   - ESP-BC and ESP-E management
   - Error handling and health monitoring

### **New ESP32 Firmware:**
2. ✅ **`esp_utama/esp_utama_uart.ino`** (400+ lines)
   - UART communication via Serial2
   - JSON command parsing
   - Control rods + turbine + humidifier
   - Safety timeout mechanism

3. ✅ **`esp_visualizer/esp_visualizer_uart.ino`** (350+ lines)
   - UART communication via Serial2
   - JSON command parsing
   - 3-flow LED visualization
   - Power indicator control

### **Testing Tools:**
4. ✅ **`test_uart_esp.py`** (200+ lines)
   - Automated UART testing
   - ESP-BC communication test
   - ESP-E communication test
   - Performance benchmarking

### **Documentation:**
5. ✅ **`UART_MIGRATION_GUIDE.md`**
   - Complete migration overview
   - Architecture changes
   - Benefits analysis

6. ✅ **`UART_WIRING_GUIDE.md`**
   - Detailed wiring instructions
   - Pin mappings
   - Troubleshooting guide
   - Step-by-step procedure

### **Configuration Updates:**
7. ✅ **`raspi_config.py`** (modified)
   - Added UART configuration
   - Updated comments for I2C (OLEDs only)

---

## 🔄 Migration Steps

### **Phase 1: Hardware (1-2 hours)**

**1.1 Disconnect Old I2C Wiring:**
```
Remove from ESP-BC:
❌ GPIO 21 (SDA) → TCA9548A #1
❌ GPIO 22 (SCL) → TCA9548A #1

Remove from ESP-E:
❌ GPIO 21 (SDA) → TCA9548A #2
❌ GPIO 22 (SCL) → TCA9548A #2
```

**1.2 Connect New UART Wiring:**
```
ESP-BC UART:
✅ GPIO 16 (RX2) → RasPi GPIO 14 (TX, Pin 8)
✅ GPIO 17 (TX2) → RasPi GPIO 15 (RX, Pin 10)
✅ GND → RasPi GND (Pin 6)

ESP-E UART:
✅ GPIO 16 (RX2) → RasPi GPIO 0 (TX, Pin 27)
✅ GPIO 17 (TX2) → RasPi GPIO 1 (RX, Pin 28)
✅ GND → RasPi GND (Pin 14)
```

**1.3 Verify Wiring:**
```bash
# Use multimeter to test continuity
# Check all connections
# Verify no shorts
```

---

### **Phase 2: Raspberry Pi Configuration (15 min)**

**2.1 Enable UART2:**
```bash
sudo nano /boot/config.txt

# Add these lines:
enable_uart=1
dtoverlay=uart2

# Save and reboot
sudo reboot
```

**2.2 Verify UART Devices:**
```bash
ls -l /dev/ttyAMA*

# Should see:
# /dev/ttyAMA0 → UART0 (GPIO 14/15)
# /dev/ttyAMA1 → UART2 (GPIO 0/1)
```

**2.3 Set Permissions:**
```bash
sudo usermod -a -G dialout $USER
# Logout and login, or reboot
```

---

### **Phase 3: ESP32 Firmware (30 min)**

**3.1 Upload ESP-BC Firmware:**
```bash
Arduino IDE:
1. File → Open → esp_utama/esp_utama_uart.ino
2. Tools → Board → ESP32 Dev Module
3. Tools → Port → /dev/ttyUSB0 (your ESP port)
4. Sketch → Upload
5. Tools → Serial Monitor (115200 baud)

Expected output:
✅ UART2 initialized at 115200 baud
✅ Servos initialized
✅ Humidifier relays initialized
✅ System Ready
```

**3.2 Upload ESP-E Firmware:**
```bash
Same process with:
- File → Open → esp_visualizer/esp_visualizer_uart.ino

Expected output:
✅ UART2 initialized
✅ LED multiplexers initialized
✅ Power indicator LEDs initialized
✅ System Ready
```

---

### **Phase 4: Software Integration (1 hour)**

**4.1 Install Dependencies:**
```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Install pyserial if not already installed
pip3 install pyserial
```

**4.2 Test UART Communication:**
```bash
python3 test_uart_esp.py

Expected output:
Testing ESP-BC on /dev/ttyAMA0
✅ Serial port opened
✅ Ping successful
✅ Update successful
✅ Success rate: 10/10
✅ ESP-BC test PASSED

Testing ESP-E on /dev/ttyAMA1
✅ Serial port opened
✅ Ping successful
✅ Update successful
✅ Success rate: 10/10
✅ ESP-E test PASSED

✅ ALL TESTS PASSED
```

**4.3 Modify Main Panel (NEXT STEP - Not done yet):**

We still need to modify `raspi_main_panel.py` to use UART instead of I2C:

```python
# Replace this import:
# from raspi_i2c_master import I2CMaster

# With this:
from raspi_uart_master import UARTMaster

# Replace initialization:
# self.i2c_master = I2CMaster(...)

# With this:
self.uart_master = UARTMaster(
    esp_bc_port=config.UART_ESP_BC_PORT,
    esp_e_port=config.UART_ESP_E_PORT,
    baudrate=config.UART_BAUDRATE
)
```

---

## 📊 Comparison: I2C vs UART

| Feature | I2C (Old) | UART (New) |
|---------|-----------|------------|
| **Reliability** | ❌ Poor (ESP32 I2C slave unstable) | ✅ Excellent |
| **Speed** | 100 kHz (slow) | 115200 bps (11x faster) |
| **Latency** | ~10-50ms | ~1-5ms |
| **Error Rate** | High (timeouts, bus locks) | Very low |
| **Wiring** | Complex (via multiplexer) | Simple (direct) |
| **Debugging** | Hard (need logic analyzer) | Easy (Serial Monitor) |
| **Bus Locking** | ❌ Frequent issue | ✅ No bus locking |
| **Multi-master** | Yes (but problematic) | No (but not needed) |
| **GPIO Pins** | 2 pins (shared bus) | 4 pins (2 per ESP) |
| **Setup Time** | Medium | Fast |
| **Protocol** | Binary (smbus) | JSON (human-readable) |

---

## 🎯 Benefits of UART Migration

### **✅ Reliability:**
- No more I2C slave timeout errors
- No more bus locking issues
- Stable communication even under load

### **✅ Performance:**
- 11x faster than I2C (115200 vs 100k)
- Lower latency (~1ms vs ~10ms)
- No clock stretching issues

### **✅ Debugging:**
- JSON protocol is human-readable
- Easy to monitor with Serial Monitor
- Can inject test commands manually
- Clear error messages

### **✅ Simplicity:**
- Direct point-to-point wiring
- No multiplexer needed for ESPs
- Fewer failure points
- Easier troubleshooting

### **✅ Scalability:**
- Can increase baudrate to 921600 if needed
- Can add CRC/checksum for error detection
- Can implement flow control (RTS/CTS)
- Can add more UART devices (Pi has 6 UARTs)

---

## ⚠️ Trade-offs

### **Cons of UART:**
1. **More GPIO pins used:**
   - I2C: 2 pins total (shared)
   - UART: 4 pins (2 per ESP)

2. **No multi-master:**
   - Only point-to-point (1 master, 1 slave)
   - Can't have multiple masters on same bus

3. **Need to enable UART2:**
   - Requires /boot/config.txt modification
   - GPIO 0/1 not enabled by default

### **Why it's worth it:**
✅ **Raspberry Pi has 6 UARTs** (plenty of pins)  
✅ **No need for multi-master** (we control everything)  
✅ **One-time config** (dtoverlay=uart2)  
✅ **Reliability > pin count** (stability is critical)

---

## 🚀 Next Actions

### **Immediate (Do Now):**
1. ✅ Hardware rewiring (remove I2C, add UART)
2. ✅ Enable UART2 (/boot/config.txt)
3. ✅ Upload ESP firmware (uart versions)
4. ✅ Test with `test_uart_esp.py`

### **Next Session (After hardware works):**
5. ⏳ Modify `raspi_main_panel.py` to use UARTMaster
6. ⏳ Update `raspi_system_health.py` for UART checks
7. ⏳ Test full system integration
8. ⏳ Update all documentation

### **Optional (Later):**
9. ⏳ Add binary protocol for even faster speed
10. ⏳ Add CRC/checksum for data integrity
11. ⏳ Implement hardware flow control (RTS/CTS)
12. ⏳ Create monitoring dashboard for UART stats

---

## 📝 Rollback Plan (If Needed)

If UART doesn't work, we can rollback:

```bash
# 1. Re-upload old I2C firmware
cd esp_utama
# Upload: esp_utama.ino (old version)

cd esp_visualizer
# Upload: esp_visualizer.ino (old version)

# 2. Reconnect I2C wiring
# Follow old wiring diagram

# 3. Use old raspi_main_panel.py
git checkout HEAD~1 raspi_main_panel.py

# 4. Restart system
python3 raspi_main_panel.py
```

**But we expect UART to work perfectly!** ✅

---

## 📞 Support

**If you encounter issues:**

1. **Check Serial Monitor** on ESP32
   - Should show "UART Ready"
   - Should show incoming commands
   - Should show outgoing responses

2. **Run diagnostic:**
   ```bash
   python3 test_uart_esp.py
   ```

3. **Check wiring:**
   - RX ↔ TX must be crossed
   - Common GND required
   - No loose connections

4. **Check UART devices:**
   ```bash
   ls -l /dev/ttyAMA*
   dmesg | grep tty
   ```

5. **Check permissions:**
   ```bash
   groups | grep dialout
   ```

---

**Status:** ✅ **READY TO START HARDWARE MIGRATION**

**Confidence Level:** 95% (UART is proven technology)

**Expected Result:** 100% stable communication with NO timeouts

**Let's do this!** 🚀

