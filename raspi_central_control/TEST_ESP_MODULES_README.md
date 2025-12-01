# ESP Modules Auto-Detection Test Script

## 📋 Overview

Script `test_pca9548a_esp.py` sekarang sudah diupdate dengan fitur **auto-detection** untuk mendeteksi dan menguji semua ESP modules yang terhubung ke Raspberry Pi melalui PCA9548A multiplexer.

## 🎯 Features

### ✅ Auto-Detection
- Otomatis mendeteksi ESP modules mana yang terhubung
- Scan semua 5 channels PCA9548A
- Identifikasi ESP-B, ESP-C, ESP-E, ESP-F, ESP-G

### ✅ Protocol-Aware Testing
- ESP-B: Reactor control protocol (10 bytes write, 16 bytes read)
- ESP-C: Turbine protocol (3 bytes write, 10 bytes read)
- ESP-E/F/G: Visualizer protocol (5 bytes write, 2 bytes read)

### ✅ Comprehensive Summary
- Tampilkan status setiap module
- Statistik PASS/FAIL
- Detail komunikasi untuk debugging

## 🚀 Usage

### Run Test Script:
```bash
cd /home/pi/raspi_central_control
python3 test_pca9548a_esp.py
```

## 📊 Expected Output

```
============================================================
  PCA9548A + ESP32 Auto-Detection & Test
  Supports: ESP-B, ESP-C, ESP-E, ESP-F, ESP-G
============================================================
✅ I2C Bus 1 initialized

--- Step 1: Check PCA9548A Multiplexer ---

🔍 Scanning I2C bus...
  Found device: 0x70
✅ PCA9548A found at 0x70

--- Step 2: Auto-Detect ESP Modules ---

============================================================
  AUTO-DETECTING CONNECTED ESP MODULES
============================================================
✅ PCA9548A Channel 0 selected (mask: 0x01)
✅ ESP-B (Reactor Control) DETECTED on Channel 0 @ 0x08
✅ PCA9548A Channel 1 selected (mask: 0x02)
✅ ESP-C (Turbine & Generator) DETECTED on Channel 1 @ 0x09
✅ PCA9548A Channel 2 selected (mask: 0x04)
✅ ESP-E (Primary Flow Visualizer) DETECTED on Channel 2 @ 0x0A
✅ PCA9548A Channel 3 selected (mask: 0x08)
❌ ESP-F (Secondary Flow Visualizer) NOT FOUND on Channel 3 @ 0x0B
✅ PCA9548A Channel 4 selected (mask: 0x10)
❌ ESP-G (Tertiary Flow Visualizer) NOT FOUND on Channel 4 @ 0x0C
============================================================
  Total modules detected: 3/5
============================================================

✅ Found 3 module(s): ESP-B, ESP-C, ESP-E

--- Step 3: Test Each Module ---

============================================================
  Testing ESP-B (Reactor Control)
============================================================

--- Select Channel 0 ---
✅ PCA9548A Channel 0 selected (mask: 0x01)

--- Test ESP-B (Reactor Control) Communication ---

📤 Testing write to ESP-B at 0x08...
   Sending: pressure=155.5 bar, pump1=1, pump2=1
   Raw bytes: 00 00 1B 43 00 00 00 00 01 01
✅ Data sent to ESP-B successfully!

📡 Testing ESP-B communication at 0x08...
✅ Received 16 bytes from ESP-B:
   Raw data: 3C 41 46 00 CD CC CC 41 00 00 00 00 00 00 00 00
   Rod 1: 60%
   Rod 2: 65%
   Rod 3: 70%
   kW Thermal: 1943.75 kW

============================================================
  Testing ESP-C (Turbine & Generator)
============================================================

--- Select Channel 1 ---
✅ PCA9548A Channel 1 selected (mask: 0x02)

--- Test ESP-C (Turbine & Generator) Communication ---

📤 Testing write to ESP-C at 0x09...
   Sending: rod1=50%, rod2=50%, rod3=50%
   Raw bytes: 32 32 32
✅ Data sent to ESP-C successfully!

📡 Testing ESP-C communication at 0x09...
✅ Received 10 bytes from ESP-C:
   Raw data: 00 00 48 42 01 00 00 00 01 01
   Power Level: 50.00%
   State: 1 (STARTING_UP)
   Generator Status: 1
   Turbine Status: 1

============================================================
  Testing ESP-E (Primary Flow Visualizer)
============================================================

--- Select Channel 2 ---
✅ PCA9548A Channel 2 selected (mask: 0x04)

--- Test ESP-E (Primary Flow Visualizer) Communication ---

📤 Testing write to Visualizer at 0x0A...
   Sending: pressure=150.0 bar, pump1_status=2
   Raw bytes: 00 00 16 43 02
✅ Data sent successfully!

📡 Testing read from Visualizer at 0x0A...
✅ Received 2 bytes:
   Raw data: 05 10
   Animation Speed: 5
   LED Count: 16

============================================================
  FINAL TEST SUMMARY
============================================================
  ESP-B (Reactor Control)                 ✅ PASS
  ESP-C (Turbine & Generator)              ✅ PASS
  ESP-E (Primary Flow Visualizer)          ✅ PASS
============================================================
  Total: 3 PASSED, 0 FAILED
============================================================
  ✅ ALL TESTS PASSED!
  All connected ESP modules are communicating correctly!
============================================================
```

## 🔧 Configuration

### ESP Modules Configuration (in script):

```python
ESP_MODULES = {
    'ESP-B': {
        'name': 'ESP-B (Reactor Control)',
        'channel': 0,
        'address': 0x08,
        'write_size': 10,
        'read_size': 16,
        'protocol': 'reactor'
    },
    'ESP-C': {
        'name': 'ESP-C (Turbine & Generator)',
        'channel': 1,
        'address': 0x09,
        'write_size': 3,
        'read_size': 10,
        'protocol': 'turbine'
    },
    'ESP-E': {
        'name': 'ESP-E (Primary Flow Visualizer)',
        'channel': 2,
        'address': 0x0A,
        'write_size': 5,
        'read_size': 2,
        'protocol': 'visualizer'
    },
    'ESP-F': {
        'name': 'ESP-F (Secondary Flow Visualizer)',
        'channel': 3,
        'address': 0x0B,
        'write_size': 5,
        'read_size': 2,
        'protocol': 'visualizer'
    },
    'ESP-G': {
        'name': 'ESP-G (Tertiary Flow Visualizer)',
        'channel': 4,
        'address': 0x0C,
        'write_size': 5,
        'read_size': 2,
        'protocol': 'visualizer'
    }
}
```

## 🐛 Troubleshooting

### Module Not Detected:
1. **Check Physical Connection**
   - Pastikan ESP terhubung ke channel yang benar di PCA9548A
   - Cek kabel SDA, SCL, VCC, GND

2. **Check I2C Address**
   - ESP-B: 0x08
   - ESP-C: 0x09
   - ESP-E: 0x0A
   - ESP-F: 0x0B
   - ESP-G: 0x0C

3. **Check ESP Code**
   - Pastikan ESP sudah di-upload dengan code terbaru
   - Check serial monitor ESP untuk error

4. **Check PCA9548A Channel**
   - ESP-B: Channel 0
   - ESP-C: Channel 1
   - ESP-E: Channel 2
   - ESP-F: Channel 3
   - ESP-G: Channel 4

### Test Failed:
1. **Communication Error**
   - Check baud rate I2C (default: 100kHz)
   - Check pull-up resistors on SDA/SCL
   - Check cable length (< 1 meter recommended)

2. **Protocol Mismatch**
   - Pastikan ESP code sesuai dengan protocol di test script
   - Check write_size dan read_size di config

3. **Watchdog Reset**
   - Pastikan ESP code sudah include `delay(2)` di loop()
   - Check serial monitor ESP untuk "Watchdog reset" message

## 📝 Protocol Details

### ESP-B (Reactor Control)
**Write (10 bytes):**
- pressure (float, 4 bytes)
- reserved (float, 4 bytes)
- pump1_status (byte, 1 byte)
- pump2_status (byte, 1 byte)

**Read (16 bytes):**
- rod1_pos (byte, 1 byte)
- rod2_pos (byte, 1 byte)
- rod3_pos (byte, 1 byte)
- reserved (byte, 1 byte)
- kwThermal (float, 4 bytes)
- reserved (float, 4 bytes)
- reserved (float, 4 bytes)

### ESP-C (Turbine & Generator)
**Write (3 bytes):**
- rod1_pos (byte, 1 byte)
- rod2_pos (byte, 1 byte)
- rod3_pos (byte, 1 byte)

**Read (10 bytes):**
- powerLevel (float, 4 bytes)
- state (uint32, 4 bytes)
- generatorStatus (byte, 1 byte)
- turbineStatus (byte, 1 byte)

### ESP-E/F/G (Visualizers)
**Write (5 bytes):**
- pressure (float, 4 bytes)
- pumpStatus (byte, 1 byte)

**Read (2 bytes):**
- animationSpeed (byte, 1 byte)
- LED_COUNT (byte, 1 byte)

## 🎯 Next Steps

1. **Test Individual Module**
   - Comment out modules di ESP_MODULES dict untuk test satu per satu

2. **Integration Test**
   - Jalankan test dengan semua 5 modules terhubung

3. **Production Use**
   - Gunakan script ini untuk debugging di production
   - Monitor komunikasi I2C secara berkala

## ✅ Success Criteria

- ✅ PCA9548A detected
- ✅ All connected modules detected
- ✅ Write to each module successful
- ✅ Read from each module successful
- ✅ Data parsed correctly
- ✅ No communication errors

---

**Last Updated:** December 1, 2024
**Version:** 2.0 (Auto-Detection)
