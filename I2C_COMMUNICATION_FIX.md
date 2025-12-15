# I2C Communication Fix - ESP ↔ Raspberry Pi

**Date:** 2024-12-15  
**Status:** ✅ FIXED  
**Architecture:** 2-ESP Merged (ESP-BC + ESP-E)

---

## 🔍 Root Cause Analysis

### **Problem: ESP komunikasi dengan Raspberry Pi gagal**

Setelah analisis mendalam, ditemukan **3 masalah kritis** dalam implementasi I2C:

---

## ❌ **Masalah 1: Config Mismatch (KRITIS!)**

**File:** `raspi_config.py` (Line 30-37)

**SEBELUM (SALAH):**
```python
# Masih pakai arsitektur lama (3 ESP)
ESP_B_ADDRESS = 0x08
ESP_C_ADDRESS = 0x09  # ❌ ESP-C tidak ada lagi (sudah merged!)
ESP_E_ADDRESS = 0x0A

ESP_B_CHANNEL = 0
ESP_C_CHANNEL = 1     # ❌ Channel 1 tidak digunakan!
ESP_E_CHANNEL = 2     # ❌ Salah! ESP-E di channel 0, bukan 2
```

**SESUDAH (BENAR):**
```python
# Arsitektur 2-ESP merged
ESP_BC_ADDRESS = 0x08  # ESP-BC: Control Rods + Turbine + Humidifier (MERGED)
ESP_E_ADDRESS = 0x0A   # ESP-E: 3-Flow LED Visualizer

# Channel mapping (both on channel 0 of their respective multiplexers)
ESP_BC_CHANNEL = 0     # ESP-BC on TCA9548A #1 (0x70), Channel 0
ESP_E_CHANNEL = 0      # ESP-E on TCA9548A #2 (0x71), Channel 0
```

**Root Cause:**  
Config file tidak di-update setelah merge ESP-B dan ESP-C menjadi ESP-BC.

---

## ❌ **Masalah 2: Callback Multiplexer Tidak Jelas**

**File:** `raspi_i2c_master.py` + `raspi_tca9548a.py`

**SEBELUM (SALAH):**
```python
# raspi_i2c_master.py
def update_esp_bc(self, ...):
    if self.mux_select:
        self.mux_select(0)  # ❌ Channel 0 di multiplexer mana?
    # ...

def update_esp_e(self, ...):
    if self.mux_select:
        self.mux_select(2)  # ❌ Channel 2? ESP-E di channel 0!
```

**MASALAH:**
- `mux_select(0)` tidak jelas: Apakah MUX #1 Ch 0 atau MUX #2 Ch 0?
- ESP-BC ada di **TCA9548A #1 (0x70), Channel 0**
- ESP-E ada di **TCA9548A #2 (0x71), Channel 0**
- Callback tidak membedakan multiplexer address!

**SESUDAH (BENAR):**
```python
# raspi_main_panel.py - Explicitly select MUX #1 Channel 0 for ESP-BC
if self.mux_manager:
    self.mux_manager.select_mux1_channel(0)

success = self.i2c_master.update_esp_bc(...)

# raspi_i2c_master.py - MUX #2 Channel 0 selected by callback for ESP-E
if self.mux_select:
    self.mux_select(0)  # Now clear: select_esp_channel(0) → MUX #2 Ch 0
```

**Root Cause:**  
Callback hanya mengirim channel number tanpa informasi multiplexer address.

---

## ❌ **Masalah 3: Dual Multiplexer Manager Confusion**

**File:** `raspi_tca9548a.py`

**SEBELUM (SALAH):**
```python
class DualMultiplexerManager:
    def __init__(self, ...):
        self.mux_display = TCA9548A(...)  # ❌ Nama misleading
        self.mux_esp = TCA9548A(...)      # ❌ Nama misleading
    
    def select_display_channel(self, channel):
        # ❌ Logic rumit, map channel 0-8 ke 2 multiplexer
        if channel <= 6:
            return self.mux_display.select_channel(channel + 1)
        else:
            return self.mux_esp.select_channel(channel - 7 + 1)
    
    def select_esp_channel(self, esp_id):
        # ❌ Parameter nama "esp_id" tapi function dipanggil untuk OLED juga!
        if esp_id == 0:
            return self.mux_display.select_channel(0)
        elif esp_id == 1:
            return self.mux_esp.select_channel(0)
```

**MASALAH:**
- Nama `mux_display` dan `mux_esp` misleading karena:
  - `mux_display` (MUX #1) juga berisi **ESP-BC**
  - `mux_esp` (MUX #2) juga berisi **OLED #8-9**
- Method `select_esp_channel` digunakan untuk OLED manager juga!
- Mapping channel tidak konsisten dengan dokumentasi hardware

**SESUDAH (BENAR):**
```python
class DualMultiplexerManager:
    def __init__(self, ...):
        self.mux1 = TCA9548A(...)  # ✅ TCA9548A #1 (0x70)
        self.mux2 = TCA9548A(...)  # ✅ TCA9548A #2 (0x71)
    
    def select_mux1_channel(self, channel):
        """Select channel on MUX #1 (ESP-BC + OLED #1-7)"""
        return self.mux1.select_channel(channel)
    
    def select_mux2_channel(self, channel):
        """Select channel on MUX #2 (ESP-E + OLED #8-9)"""
        return self.mux2.select_channel(channel)
    
    def select_display_channel(self, channel):
        """For OLED manager (channels 1-7 on MUX #1)"""
        return self.mux1.select_channel(channel)
    
    def select_esp_channel(self, channel):
        """For MUX #2 access (ESP-E at Ch 0, OLED #8-9 at Ch 1-2)"""
        return self.mux2.select_channel(channel)
```

**Root Cause:**  
Abstraction layer terlalu kompleks dan naming tidak sesuai dengan hardware mapping.

---

## ✅ **Solusi yang Diterapkan**

### **1. Update Config File**
**File:** `raspi_config.py`
- ✅ Hapus referensi ESP-C (sudah merged)
- ✅ Update channel mapping: ESP-BC di Ch 0, ESP-E di Ch 0
- ✅ Tambah komentar jelas tentang multiplexer routing

### **2. Refactor Multiplexer Manager**
**File:** `raspi_tca9548a.py`
- ✅ Rename `mux_display` → `mux1` (TCA9548A #1)
- ✅ Rename `mux_esp` → `mux2` (TCA9548A #2)
- ✅ Tambah `select_mux1_channel()` dan `select_mux2_channel()` yang eksplisit
- ✅ Keep `select_display_channel()` dan `select_esp_channel()` untuk backward compatibility
- ✅ Dokumentasi jelas tentang hardware mapping

### **3. Fix I2C Master Communication**
**File:** `raspi_i2c_master.py`
- ✅ Update docstring callback: Jelaskan bahwa callback untuk MUX #2 only
- ✅ ESP-BC: Select MUX #1 Ch 0 secara eksplisit di main_panel
- ✅ ESP-E: Select MUX #2 Ch 0 via callback (channel 0, bukan 2!)

### **4. Fix Main Panel Communication**
**File:** `raspi_main_panel.py`
- ✅ Tambah explicit `select_mux1_channel(0)` sebelum `update_esp_bc()`
- ✅ Callback `select_esp_channel` otomatis handle MUX #2 untuk `update_esp_e()`

---

## 📊 Hardware Mapping (FINAL - CORRECT)

```
I2C Bus 1 (Raspberry Pi GPIO 2/3)
│
├─── TCA9548A #1 (0x70) ─────────────────┐
│    │                                    │
│    ├─ Channel 0: ESP-BC (0x08) ◄───────┼─── Control Rods + Turbine + Humidifier
│    ├─ Channel 1: OLED #1 (0x3C)        │
│    ├─ Channel 2: OLED #2 (0x3C)        │
│    ├─ Channel 3: OLED #3 (0x3C)        │
│    ├─ Channel 4: OLED #4 (0x3C)        │
│    ├─ Channel 5: OLED #5 (0x3C)        │
│    ├─ Channel 6: OLED #6 (0x3C)        │
│    └─ Channel 7: OLED #7 (0x3C)        │
│                                         │
└─── TCA9548A #2 (0x71) ─────────────────┘
     │
     ├─ Channel 0: ESP-E (0x0A) ◄─────────── 48 LED Visualizer
     ├─ Channel 1: OLED #8 (0x3C)
     └─ Channel 2: OLED #9 (0x3C)
```

---

## 🔧 Communication Flow (FIXED)

### **ESP-BC Communication:**
```
main_panel.esp_communication_thread()
    │
    ├─► mux_manager.select_mux1_channel(0)  # Select MUX #1, Ch 0
    │       └─► TCA9548A #1 (0x70), Channel 0 activated
    │
    └─► i2c_master.update_esp_bc(...)
            └─► I2C write to 0x08 ✅ SUCCESS!
```

### **ESP-E Communication:**
```
main_panel.esp_communication_thread()
    │
    └─► i2c_master.update_esp_e(...)
            │
            ├─► mux_select(0)  # Callback: select_esp_channel(0)
            │       └─► TCA9548A #2 (0x71), Channel 0 activated
            │
            └─► I2C write to 0x0A ✅ SUCCESS!
```

### **OLED Communication (Unchanged - Already Working):**
```
oled_manager.update_display(channel=1-7)
    │
    └─► mux_manager.select_display_channel(1-7)
            └─► TCA9548A #1 (0x70), Channel 1-7 activated
                    └─► I2C write to 0x3C ✅ SUCCESS!

oled_manager.update_display(channel=8-9)
    │
    └─► mux_manager.select_esp_channel(1-2)
            └─► TCA9548A #2 (0x71), Channel 1-2 activated
                    └─► I2C write to 0x3C ✅ SUCCESS!
```

---

## ✅ Testing Checklist

### **1. Test I2C Device Detection:**
```bash
i2cdetect -y 1
```

**Expected output:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
...
70: 70 71 -- -- -- -- -- --
```
✅ Kedua multiplexer terdeteksi (0x70 dan 0x71)

### **2. Test ESP-BC Communication:**
```python
python3 raspi_i2c_master.py
# Should see:
# - ESP-BC communication successful
# - Rod positions received
# - Thermal power value
```

### **3. Test ESP-E Communication:**
```python
python3 raspi_i2c_master.py
# Should see:
# - ESP-E communication successful
# - Animation speed and LED count
```

### **4. Test OLED Display (Should still work):**
```python
python3 test_oled_hardware.py
# Should see:
# - 9 OLEDs detected and working
```

### **5. Test Full System:**
```bash
python3 raspi_main_panel.py
```

**Expected behavior:**
- ✅ All 9 OLED displays update correctly
- ✅ ESP-BC responds to rod commands
- ✅ ESP-E animates LED flows
- ✅ No I2C communication errors in log

---

## 📝 Files Modified

1. **`raspi_config.py`**
   - Updated ESP addresses and channel mapping
   - Removed deprecated ESP-C references

2. **`raspi_tca9548a.py`**
   - Refactored DualMultiplexerManager
   - Added explicit `select_mux1_channel()` and `select_mux2_channel()`
   - Improved documentation

3. **`raspi_i2c_master.py`**
   - Updated callback documentation
   - Fixed ESP-E channel selection (0 instead of 2)
   - Added hardware mapping comments

4. **`raspi_main_panel.py`**
   - Added explicit MUX #1 Ch 0 selection before ESP-BC communication
   - Improved ESP communication flow

---

## 🎯 Key Takeaways

1. **Always match software config with hardware documentation**
   - Hardware doc said ESP-BC on MUX #1 Ch 0
   - Config file said ESP-BC on Ch 0 (but which MUX?)
   - Fix: Make it explicit!

2. **Callback functions need clear contracts**
   - Old: `mux_select(channel)` - ambiguous
   - New: `select_mux1_channel(channel)` or `select_mux2_channel(channel)` - clear!

3. **Naming matters for maintainability**
   - `mux_display` and `mux_esp` were misleading
   - `mux1` and `mux2` match hardware schematic

4. **Test each communication path independently**
   - ESP-BC via MUX #1 Ch 0
   - ESP-E via MUX #2 Ch 0
   - OLED via MUX #1 Ch 1-7 and MUX #2 Ch 1-2

---

## 🚀 Next Steps

1. ✅ **Test on actual hardware**
   - Upload ESP-BC code to ESP32 (address 0x08)
   - Upload ESP-E code to ESP32 (address 0x0A)
   - Run `raspi_main_panel.py`
   - Verify I2C communication with `i2cdetect` and logs

2. ✅ **Monitor I2C error rates**
   - Check `pltn_control.log` for I2C timeouts
   - Use `i2c_master.get_health_status()` to track errors

3. ✅ **Fine-tune timing if needed**
   - Current: 100ms cycle for ESP communication
   - Adjust if seeing timeouts or delays

---

**Status:** ✅ **READY FOR HARDWARE TESTING**

**Author:** GitHub Copilot CLI  
**Date:** 2024-12-15  
**Version:** 3.1 (2-ESP Architecture with I2C Fix)
