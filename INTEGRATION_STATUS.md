# 📊 STATUS INTEGRASI SISTEM - Analisis Lengkap

**Tanggal:** 4 Desember 2024  
**Status:** 🟡 **PARTIAL INTEGRATION** (60% integrated)

---

## 🎯 KESIMPULAN UTAMA

### ❌ **SISTEM BELUM TERINTEGRASI PENUH!**

Ada **MISMATCH** besar antara:
1. **Panel kontrol fisik** (15 buttons + 9 OLEDs) dengan **program yang ada**
2. **ESP-C** ada **2 versi** (lama & baru dengan humidifier)
3. **Raspberry Pi** program belum support GPIO buttons & 9 OLEDs

---

## 📁 ANALISIS PER FILE

### **A. ESP32 FIRMWARE**

#### 1. ESP-B (Control Rods)

**File:** `ESP_B/ESP_B_I2C/ESP_B_I2C.ino`

**Status:** 🟡 **PARTIALLY COMPATIBLE**

**I2C Protocol:**
```cpp
Receive: 10 bytes (pressure + pump status)
Send: 16 bytes (rod positions + thermal kW)
```

**Issues:**
```diff
❌ MASALAH UTAMA:
- Kode masih expect RECEIVE dari RasPi (pressure + pump status)
- SEHARUSNYA: Receive target rod positions dari RasPi
- Button handling masih ada di ESP-B (SEHARUSNYA di RasPi)
- OLED display logic masih ada di ESP-B (SEHARUSNYA di RasPi)

✅ YANG BENAR:
- Servo motor control: OK
- Thermal kW calculation: OK
- I2C communication: OK (tapi protocol salah)
```

**Perlu Diubah:**
```cpp
// SEKARANG (SALAH):
void onReceiveData(int numBytes) {
    // Terima: pressure + pump status
    // Parse: pressure, pump1Status, pump2Status
}

// SEHARUSNYA (BENAR):
void onReceiveData(int numBytes) {
    // Terima: target rod positions
    // Byte 0: safety_rod_target (0-100%)
    // Byte 1: shim_rod_target (0-100%)
    // Byte 2: regulating_rod_target (0-100%)
    
    // Gerakkan servo sesuai target
    servo1.write(map(safety_target, 0, 100, 0, 180));
    servo2.write(map(shim_target, 0, 100, 0, 180));
    servo3.write(map(regulating_target, 0, 100, 0, 180));
}
```

---

#### 2. ESP-C (Turbine & Humidifier)

**⚠️ ADA 2 VERSI!**

##### **Versi 1 (LAMA): ESP_C/ESP_C_I2C/ESP_C_I2C.ino**

**Status:** ❌ **DEPRECATED - JANGAN GUNAKAN!**

```cpp
#define RECEIVE_SIZE 3   // Only rod positions
#define SEND_SIZE 10     // No humidifier status

// Protocol LAMA:
Receive: 3 bytes (rod1, rod2, rod3)
Send: 10 bytes (power, state, gen_status, turb_status)

❌ TIDAK SUPPORT HUMIDIFIER!
❌ GPIO 32/33 tidak digunakan
❌ Tidak ada humidifier control logic
```

##### **Versi 2 (BARU): ESP_C/ESP_C_HUMIDIFIER.ino**

**Status:** ✅ **USE THIS VERSION!**

```cpp
#define RECEIVE_SIZE 12  // Rod + thermal + humidifier commands
#define SEND_SIZE 12     // Power + state + humidifier status

// Protocol BARU:
Receive: 12 bytes
  - Byte 0: Register (0x00)
  - Byte 1-3: Rod positions
  - Byte 4-7: Thermal kW (float)
  - Byte 8: Humidifier SG command (0/1)
  - Byte 9: Humidifier CT command (0/1)

Send: 12 bytes
  - Byte 0-3: Power level (float)
  - Byte 4-7: State (uint32)
  - Byte 8: Generator status
  - Byte 9: Turbine status
  - Byte 10: Humidifier SG status ⭐
  - Byte 11: Humidifier CT status ⭐

✅ SUPPORT HUMIDIFIER!
✅ GPIO 32: Steam Gen Humidifier
✅ GPIO 33: Cooling Tower Humidifier
✅ Logic untuk ON/OFF berdasarkan RasPi command
```

**💡 KESIMPULAN ESP-C:**
```
❌ HAPUS: ESP_C_I2C.ino (versi lama)
✅ GUNAKAN: ESP_C_HUMIDIFIER.ino (versi baru)

ATAU rename untuk clarity:
mv ESP_C_HUMIDIFIER.ino ESP_C_I2C/ESP_C_I2C.ino
rm -rf ESP_C_I2C.old  # backup old version
```

---

#### 3. ESP-E (3-Flow Visualizer)

**File:** `ESP_E_Aliran_Primer/ESP_E_I2C/ESP_E_I2C.ino`

**Status:** ✅ **FULLY COMPATIBLE**

```cpp
#define RECEIVE_SIZE 16  // 1 register + 15 data (3 flows)
#define SEND_SIZE 2      // Animation speed + LED count

Protocol:
Receive: 16 bytes
  - Byte 0: Register (0x00)
  - Byte 1-5: Primary (pressure float + pump status)
  - Byte 6-10: Secondary (pressure float + pump status)
  - Byte 11-15: Tertiary (pressure float + pump status)

✅ CODE SUDAH BENAR!
✅ Support 3 aliran independent
✅ LED animation based on pump status
✅ Multiplexer control: OK
```

**Tidak perlu perubahan!** ✅

---

### **B. RASPBERRY PI SOFTWARE**

#### 1. Main Program

**File:** `raspi_central_control/raspi_main.py`

**Status:** ❌ **NOT COMPATIBLE WITH PANEL**

**Yang Ada Sekarang:**
```python
# 8 buttons (di GPIO atau serial?)
# 4 OLED displays via TCA9548A
# Logic untuk control
```

**Yang Dibutuhkan:**
```python
# 15 buttons via GPIO 5-25
# 9 OLED displays via 2x PCA9548A (0x70, 0x71)
# Support humidifier control
# Multi-threaded architecture
# Safety interlock
```

**Issues:**
```diff
❌ Tidak ada GPIO button handling (15 buttons)
❌ Hanya support 4 OLED, bukan 9 OLED
❌ Tidak ada humidifier logic integration
❌ Tidak ada safety interlock implementation
❌ Button logic di ESP-B, seharusnya di RasPi
```

---

#### 2. Button Handler

**File:** `raspi_central_control/raspi_gpio_buttons.py`

**Status:** ✅ **READY TO USE**

```python
class ButtonHandler:
    def __init__(self, debounce_time=0.2):
        # Setup 15 GPIO pins as INPUT with PULL_UP
        
    def check_all_buttons(self):
        # Polling semua 15 buttons
        # Trigger callbacks if pressed
        
✅ Support 15 buttons
✅ Debouncing 200ms
✅ Callback system
✅ Ready untuk integration
```

**Tidak perlu perubahan!** ✅

---

#### 3. Humidifier Control

**File:** `raspi_central_control/raspi_humidifier_control.py`

**Status:** ✅ **READY TO USE**

```python
class HumidifierController:
    def update_all(self, safety_rod, shim_rod, regulating_rod, thermal_kw):
        # Calculate commands
        sg_cmd = (shim_rod >= 40%) AND (reg_rod >= 40%)
        ct_cmd = (thermal_kw >= 800)
        return (sg_cmd, ct_cmd)

✅ Logic sudah benar
✅ Hysteresis implemented
✅ Configurable thresholds
✅ Ready untuk integration
```

**Tidak perlu perubahan!** ✅

---

#### 4. I2C Master

**File:** `raspi_central_control/raspi_i2c_master.py`

**Status:** 🟡 **NEEDS UPDATE**

**Yang Perlu Ditambah:**
```python
def send_to_esp_b_new(self, safety_target, shim_target, reg_target):
    """
    NEW: Send target rod positions (NOT pressure!)
    Protocol: 3 bytes (safety, shim, reg)
    """
    data = struct.pack('<BBB', safety_target, shim_target, reg_target)
    # Send via I2C

def send_to_esp_c_with_humidifier(self, rods, thermal_kw, humid_sg, humid_ct):
    """
    NEW: Send with humidifier commands
    Protocol: 12 bytes (rods + thermal + 2x humid commands)
    """
    data = struct.pack('<BBBfBB', 
        rods[0], rods[1], rods[2],  # 3 rod positions
        thermal_kw,                  # thermal kW (float)
        humid_sg,                    # Steam Gen command (0/1)
        humid_ct                     # Cooling Tower command (0/1)
    )
    # Send via I2C
```

---

#### 5. OLED Manager

**File:** `raspi_central_control/raspi_oled_manager.py`

**Status:** ❌ **NOT COMPATIBLE**

**Issues:**
```diff
❌ Only support 4 OLED displays
❌ Uses TCA9548A, seharusnya PCA9548A
❌ Tidak ada layout untuk 9 OLED

SEHARUSNYA:
✅ Support 9 OLED displays
✅ Use 2x PCA9548A (0x70, 0x71)
✅ Layout untuk: pressure, 3 pumps, 3 rods, thermal, status
```

---

#### 6. Test Scripts

**File:** `raspi_central_control/test_esp_e_quick.py`

**Status:** ✅ **WORKING**

```python
# Test ESP-E dengan data 3 aliran
# Protocol: 16 bytes (1 register + 15 data)

✅ Sudah menggunakan struct.pack('<fBfBfB', ...)
✅ Sudah menggunakan i2c_msg.write()
✅ Compatible dengan ESP-E code
```

---

## 📊 COMPATIBILITY MATRIX

### **Hardware Level**

| Component | Physical Panel | Software Support | Status |
|-----------|----------------|------------------|--------|
| 15 Buttons | ✅ Installed | ❌ Not in main program | 🔴 MISMATCH |
| 9 OLEDs | ✅ Installed | ❌ Only 4 supported | 🔴 MISMATCH |
| 3 ESP32 | ✅ Installed | ✅ Supported | 🟢 MATCH |
| 2 Humidifier | ✅ Installed | ⚠️ ESP-C ready, RasPi needs work | 🟡 PARTIAL |
| 48 LEDs | ✅ Installed | ✅ ESP-E ready | 🟢 MATCH |

### **Software Level**

| Module | File | Status | Integration |
|--------|------|--------|-------------|
| ESP-B | ESP_B_I2C.ino | 🟡 Works but wrong protocol | 40% |
| ESP-C (old) | ESP_C_I2C.ino | ❌ No humidifier | 0% |
| ESP-C (new) | ESP_C_HUMIDIFIER.ino | ✅ Ready | 100% |
| ESP-E | ESP_E_I2C.ino | ✅ Ready | 100% |
| RasPi Buttons | raspi_gpio_buttons.py | ✅ Ready | 100% |
| RasPi Humid | raspi_humidifier_control.py | ✅ Ready | 100% |
| RasPi Main | raspi_main.py | ❌ Not compatible | 20% |
| RasPi OLED | raspi_oled_manager.py | ❌ Only 4 OLEDs | 30% |
| RasPi I2C | raspi_i2c_master.py | 🟡 Needs update | 50% |

---

## 🔧 PERUBAHAN YANG DIPERLUKAN

### **Priority 1: CRITICAL (Sistem Tidak Jalan Tanpa Ini)**

#### **A. ESP-C: Gunakan Versi Baru**

```bash
# Option 1: Rename dan cleanup
cd ESP_C
mv ESP_C_I2C ESP_C_I2C_OLD_BACKUP
mkdir ESP_C_I2C
mv ESP_C_HUMIDIFIER.ino ESP_C_I2C/ESP_C_I2C.ino

# Option 2: Hapus yang lama (jika sudah backup)
cd ESP_C
rm -rf ESP_C_I2C
mkdir ESP_C_I2C
mv ESP_C_HUMIDIFIER.ino ESP_C_I2C/ESP_C_I2C.ino
```

**💡 KESIMPULAN:** HARUS gunakan `ESP_C_HUMIDIFIER.ino` karena:
- ✅ Support humidifier (GPIO 32, 33)
- ✅ Protocol 12 bytes (rod + thermal + humid commands)
- ✅ Send 12 bytes back (status + humid status)

---

#### **B. ESP-B: Update Protocol**

**File yang perlu diubah:** `ESP_B/ESP_B_I2C/ESP_B_I2C.ino`

**Changes:**
```cpp
// ====================================
// OLD PROTOCOL (SALAH):
// ====================================
// Receive: pressure + pump status (10 bytes)
// Send: rod positions + thermal (16 bytes)

void onReceiveData(int numBytes) {
    // Parse pressure, pump1, pump2
    // Implement interlock di ESP-B (SALAH!)
}

// ====================================
// NEW PROTOCOL (BENAR):
// ====================================
// Receive: target rod positions (3 bytes)
// Send: actual rod positions + thermal (16 bytes)

void onReceiveData(int numBytes) {
    if (numBytes != 3) return;
    
    // Parse target positions
    uint8_t safety_target = receiveBuffer[0];
    uint8_t shim_target = receiveBuffer[1];
    uint8_t reg_target = receiveBuffer[2];
    
    // Move servos (no interlock check here!)
    // Interlock sekarang di Raspberry Pi
    servo1.write(map(safety_target, 0, 100, 0, 180));
    servo2.write(map(shim_target, 0, 100, 0, 180));
    servo3.write(map(reg_target, 0, 100, 0, 180));
    
    // Read actual positions
    rod1_actual = map(servo1.read(), 0, 180, 0, 100);
    rod2_actual = map(servo2.read(), 0, 180, 0, 100);
    rod3_actual = map(servo3.read(), 0, 180, 0, 100);
    
    // Calculate thermal power
    float avgRod = (rod1_actual + rod2_actual + rod3_actual) / 3.0;
    thermalKW = avgRod * 20.0;  // Example: 100% = 2000 kW
}

void prepareSendData() {
    sendBuffer[0] = rod1_actual;      // Safety rod
    sendBuffer[1] = rod2_actual;      // Shim rod
    sendBuffer[2] = rod3_actual;      // Regulating rod
    sendBuffer[3] = 0;                // Reserved
    memcpy(&sendBuffer[4], &thermalKW, 4);  // Thermal kW (float)
    // Byte 8-15: Reserved for future
}
```

**Remove from ESP-B:**
```cpp
// ❌ HAPUS: Button handling code
// ❌ HAPUS: OLED display code
// ❌ HAPUS: Interlock logic
// ❌ HAPUS: Emergency button handling

// ✅ KEEP: Servo control
// ✅ KEEP: Thermal calculation
// ✅ KEEP: I2C communication
```

---

#### **C. Raspberry Pi Main Program**

**File:** `raspi_central_control/raspi_main_panel.py` (BUAT BARU!)

**Structure:**
```python
import threading
from raspi_gpio_buttons import ButtonHandler, ButtonPin
from raspi_humidifier_control import HumidifierController, HUMIDIFIER_CONFIG_DEFAULT
# Import lainnya...

class PLTNController:
    def __init__(self):
        # Initialize components
        self.button_handler = ButtonHandler()
        self.humidifier = HumidifierController(HUMIDIFIER_CONFIG_DEFAULT)
        
        # System state
        self.safety_rod = 0
        self.shim_rod = 0
        self.regulating_rod = 0
        self.pressure = 0.0
        self.thermal_kw = 0.0
        
        self.pump_primary_status = 0
        self.pump_secondary_status = 0
        self.pump_tertiary_status = 0
        
        self.emergency_flag = False
        
        # Register button callbacks
        self.setup_button_callbacks()
    
    def setup_button_callbacks(self):
        # Pump control
        self.button_handler.register_callback(
            ButtonPin.PUMP_PRIMARY_ON,
            self.on_pump_primary_on
        )
        # ... register 14 more buttons
        
        # Rod control
        self.button_handler.register_callback(
            ButtonPin.SAFETY_ROD_UP,
            self.on_safety_rod_up
        )
        # ... etc
    
    def on_safety_rod_up(self):
        if self.check_interlock():
            self.safety_rod = min(100, self.safety_rod + 1)
    
    def check_interlock(self):
        """Check if rod movement allowed"""
        return (
            self.pressure >= 40.0 and
            self.pump_primary_status == 2 and  # ON
            self.pump_secondary_status == 2 and  # ON
            not self.emergency_flag
        )
    
    def thread_button_polling(self):
        """Thread 1: Button polling (10ms)"""
        while self.running:
            self.button_handler.check_all_buttons()
            time.sleep(0.01)
    
    def thread_control_logic(self):
        """Thread 2: Control logic (50ms)"""
        while self.running:
            # Update humidifier commands
            sg_cmd, ct_cmd = self.humidifier.update_all(
                self.safety_rod,
                self.shim_rod,
                self.regulating_rod,
                self.thermal_kw
            )
            
            self.humid_sg_cmd = sg_cmd
            self.humid_ct_cmd = ct_cmd
            
            time.sleep(0.05)
    
    def thread_oled_update(self):
        """Thread 3: OLED update (200ms)"""
        while self.running:
            # Update 9 OLEDs
            for i in range(9):
                self.update_oled(i)
            time.sleep(0.2)
    
    def thread_esp_communication(self):
        """Thread 4: ESP communication (100ms)"""
        while self.running:
            # Send to ESP-B
            self.send_rod_targets()
            rod_data = self.receive_from_esp_b()
            self.thermal_kw = rod_data['thermal']
            
            # Send to ESP-C (with humidifier)
            self.send_to_esp_c(rod_data, self.humid_sg_cmd, self.humid_ct_cmd)
            
            # Send to ESP-E
            self.send_to_esp_e()
            
            time.sleep(0.1)
    
    def run(self):
        # Start all threads
        threads = [
            threading.Thread(target=self.thread_button_polling),
            threading.Thread(target=self.thread_control_logic),
            threading.Thread(target=self.thread_oled_update),
            threading.Thread(target=self.thread_esp_communication),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()

if __name__ == "__main__":
    controller = PLTNController()
    controller.run()
```

---

#### **D. Update raspi_i2c_master.py**

**Add methods:**
```python
def send_rod_targets_to_esp_b(self, safety, shim, regulating):
    """Send target positions to ESP-B"""
    try:
        self.select_channel(self.pca_esp, 0)  # ESP-B channel
        data = struct.pack('<BBB', safety, shim, regulating)
        write_msg = i2c_msg.write(0x08, data)
        self.bus.i2c_rdwr(write_msg)
    except Exception as e:
        logger.error(f"Error sending to ESP-B: {e}")

def receive_from_esp_b(self):
    """Receive actual positions + thermal from ESP-B"""
    try:
        self.select_channel(self.pca_esp, 0)
        read_msg = i2c_msg.read(0x08, 16)
        self.bus.i2c_rdwr(read_msg)
        data = list(read_msg)
        
        return {
            'safety_actual': data[0],
            'shim_actual': data[1],
            'reg_actual': data[2],
            'thermal': struct.unpack('<f', bytes(data[4:8]))[0]
        }
    except Exception as e:
        logger.error(f"Error receiving from ESP-B: {e}")
        return None

def send_to_esp_c_with_humidifier(self, rods, thermal_kw, sg_cmd, ct_cmd):
    """Send to ESP-C with humidifier commands"""
    try:
        self.select_channel(self.pca_esp, 1)  # ESP-C channel
        
        data = struct.pack('<BBBfBB',
            rods['safety'],
            rods['shim'],
            rods['regulating'],
            thermal_kw,
            sg_cmd,  # 0 or 1
            ct_cmd   # 0 or 1
        )
        
        # Add register byte
        full_data = [0x00] + list(data)
        write_msg = i2c_msg.write(0x09, full_data)
        self.bus.i2c_rdwr(write_msg)
        
    except Exception as e:
        logger.error(f"Error sending to ESP-C: {e}")
```

---

#### **E. Create 9-OLED Manager**

**File:** `raspi_central_control/raspi_panel_oled_9.py` (BUAT BARU!)

```python
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

class NineOLEDManager:
    """Manage 9 OLED displays via 2x PCA9548A"""
    
    def __init__(self, bus, pca1_addr=0x70, pca2_addr=0x71):
        self.bus = bus
        self.pca1 = pca1_addr
        self.pca2 = pca2_addr
        
        # Init I2C
        i2c = busio.I2C(SCL, SDA)
        
        # Create 9 OLED objects (will be selected via multiplexer)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
        
        # Font
        self.font = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12
        )
    
    def select_oled(self, oled_num):
        """Select OLED 1-9"""
        if oled_num <= 8:
            # OLED 1-8 on PCA9548A #1 (0x70)
            channel = oled_num - 1
            self.bus.write_byte(self.pca1, 1 << channel)
        else:
            # OLED 9 on PCA9548A #2 (0x71)
            self.bus.write_byte(self.pca2, 1)
    
    def update_oled1_pressure(self, pressure):
        """OLED 1: Presurizer Pressure"""
        self.select_oled(1)
        
        image = Image.new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        
        draw.text((0, 0), "PRESURIZER", font=self.font, fill=255)
        draw.text((0, 20), f"{pressure:.1f} bar", font=self.font, fill=255)
        
        # Bar graph
        bar_width = int((pressure / 160.0) * 120)
        draw.rectangle((0, 40, bar_width, 50), outline=255, fill=255)
        
        self.oled.image(image)
        self.oled.show()
    
    def update_oled2_pump_primary(self, status):
        """OLED 2: Pump Primary Status"""
        self.select_oled(2)
        
        status_text = ["OFF", "STARTING", "ON", "SHUTDOWN"][status]
        
        image = Image.new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        
        draw.text((0, 0), "PUMP PRIMARY", font=self.font, fill=255)
        draw.text((0, 25), status_text, font=self.font, fill=255)
        
        self.oled.image(image)
        self.oled.show()
    
    # ... update_oled3 through update_oled9
```

---

## 🎯 ROADMAP INTEGRASI

### **Phase 1: Cleanup (1 hari)**
- [x] Hapus file .md yang tidak perlu ✅
- [ ] Pilih ESP-C version (gunakan HUMIDIFIER.ino)
- [ ] Backup ESP-B current version
- [ ] Create integration branch di Git

### **Phase 2: ESP Firmware Update (2-3 hari)**
- [ ] Update ESP-B protocol (3 bytes in, 16 bytes out)
- [ ] Remove button/OLED code dari ESP-B
- [ ] Test ESP-C HUMIDIFIER version
- [ ] Verify ESP-E (already OK)

### **Phase 3: Raspberry Pi Software (3-4 hari)**
- [ ] Create raspi_main_panel.py
- [ ] Create raspi_panel_oled_9.py
- [ ] Update raspi_i2c_master.py
- [ ] Create raspi_interlock.py
- [ ] Integrate all modules

### **Phase 4: Testing (2-3 hari)**
- [ ] Test button handler
- [ ] Test OLED displays (all 9)
- [ ] Test ESP communication
- [ ] Test humidifier control
- [ ] Test interlock logic
- [ ] Test emergency shutdown

### **Phase 5: Integration & Tuning (2-3 hari)**
- [ ] Full system test
- [ ] Performance tuning
- [ ] Bug fixes
- [ ] Documentation updates

**Total Estimated Time: 10-15 hari**

---

## 📊 SUMMARY

### **Yang Sudah Benar (60%):**
✅ ESP-E: 100% ready  
✅ ESP-C HUMIDIFIER version: 100% ready  
✅ raspi_gpio_buttons.py: 100% ready  
✅ raspi_humidifier_control.py: 100% ready  
✅ Test scripts: Working  

### **Yang Perlu Diperbaiki (40%):**
❌ ESP-B: Wrong protocol (receive pressure, should receive rod targets)  
❌ ESP-C: 2 versions! Use HUMIDIFIER.ino, delete old version  
❌ raspi_main.py: Not compatible with 15 buttons + 9 OLEDs  
❌ raspi_oled_manager.py: Only 4 OLEDs, need 9  
⚠️ raspi_i2c_master.py: Need new methods for updated protocols  

### **Prioritas Tertinggi:**
1. **Pilih ESP-C version** → Gunakan `ESP_C_HUMIDIFIER.ino`
2. **Update ESP-B protocol** → Receive rod targets, not pressure
3. **Create new main program** → Support 15 buttons + 9 OLEDs
4. **Test integration** → One component at a time

---

**Status:** 🟡 **60% INTEGRATED**  
**Next Action:** Pilih ESP-C version & update ESP-B protocol  
**ETA Full Integration:** 10-15 hari kerja

