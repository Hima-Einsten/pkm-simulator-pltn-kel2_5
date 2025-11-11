# Rencana Migrasi: ESP-A ke Raspberry Pi dengan Full I2C Architecture

## Gambaran Umum Perubahan

Mengubah arsitektur sistem dari ESP-A sebagai kontrol master menjadi **Raspberry Pi sebagai I2C Master** dengan 2 TCA9548A I2C multiplexer, sambil mempertahankan:
- ✅ Alur simulasi yang sudah ada
- ✅ ESP-B, ESP-C, ESP-E, ESP-F, ESP-G tetap berfungsi sebagai kontrol aktuator
- ✅ **Semua komunikasi menggunakan I2C** (mengganti UART → I2C)
- ✅ Logika interlock dan keamanan tetap sama
- ✅ Raspberry Pi sebagai **I2C Master**, semua ESP sebagai **I2C Slave**

---

## Arsitektur Baru (Full I2C)

```
                    [Raspberry Pi - I2C Master]
                              |
                    +---------+---------+
                    |                   |
              [TCA9548A #1]       [TCA9548A #2]
           (0x70 - Display)      (0x71 - ESP Slaves)
                    |                   |
        +-----------+-----------+       +---------------+---------------+
        |           |           |       |               |               |
    [OLED 0]    [OLED 1]    [OLED 2]  [ESP-B]       [ESP-C]         [ESP-E]
   (Pressu.)   (Pump1)     (Pump2)  (0x08)        (0x09)          (0x0A)
                    |                   |               |               |
                [OLED 3]            [ESP-F]         [ESP-G]
               (Pump3)              (0x0B)          (0x0C)

Legend:
- TCA9548A #1: Untuk 4x OLED display (sama seperti rencana awal)
- TCA9548A #2: Untuk 5x ESP32 sebagai I2C Slave devices
- Semua ESP menjadi I2C Slave dengan alamat unik
- Raspberry Pi polling/broadcast data via I2C
```

---

## Komponen Hardware yang Dibutuhkan

### 1. Raspberry Pi (Pi 3/4/Zero 2W)
- **Fungsi:** I2C Master untuk seluruh sistem
- **Interface:**
  - **I2C0** (GPIO 0/1) → TCA9548A #1 (Display) 
  - **I2C1** (GPIO 2/3) → TCA9548A #2 (ESP Slaves)
  - GPIO untuk tombol input (8 tombol)
  - GPIO untuk buzzer alarm
  - GPIO PWM untuk 3 motor pompa

### 2. TCA9548A I2C Multiplexer x2
- **TCA9548A #1 (Address 0x70)** - Untuk Display
  - Channel 0 → OLED Pressurizer
  - Channel 1 → OLED Pompa Primer
  - Channel 2 → OLED Pompa Sekunder
  - Channel 3 → OLED Pompa Tersier
  - Channel 4-7 → Reserved untuk ekspansi
  
- **TCA9548A #2 (Address 0x71)** - Untuk ESP Slaves
  - Channel 0 → ESP-B (I2C Slave 0x08)
  - Channel 1 → ESP-C (I2C Slave 0x09)
  - Channel 2 → ESP-E (I2C Slave 0x0A)
  - Channel 3 → ESP-F (I2C Slave 0x0B)
  - Channel 4 → ESP-G (I2C Slave 0x0C)
  - Channel 5-7 → Reserved untuk ekspansi

### 3. Perubahan Hardware dari ESP-A
- **Pindahkan ke Raspberry Pi:**
  - ✅ 8 tombol kontrol
  - ✅ 1 buzzer alarm
  - ✅ 4 OLED 128x32 (melalui TCA9548A #1)
  - ✅ 3 motor driver L298N untuk pompa

### 4. Perubahan pada Semua ESP
- **Tambahkan I2C Slave Interface:**
  - ✅ ESP-B: Implementasi I2C Slave (address 0x08)
  - ✅ ESP-C: Implementasi I2C Slave (address 0x09)
  - ✅ ESP-E: Implementasi I2C Slave (address 0x0A)
  - ✅ ESP-F: Implementasi I2C Slave (address 0x0B)
  - ✅ ESP-G: Implementasi I2C Slave (address 0x0C)
  - ⚠️ **Hapus/disable semua komunikasi UART lama**

---

## Perubahan Software

### A. Raspberry Pi (Python) - I2C Master

**File Baru:** `RasPi_Central_Control/main.py`

**Fitur:**
1. **Dual I2C Bus Management**
   - I2C Bus 0: TCA9548A #1 untuk OLED
   - I2C Bus 1: TCA9548A #2 untuk ESP Slaves
   - Fungsi untuk memilih channel pada setiap multiplexer
   - Thread-safe I2C communication

2. **OLED Display Management**
   - Inisialisasi 4 OLED di channel berbeda (TCA9548A #1)
   - Update display untuk tekanan dan status pompa
   - Non-blocking display update

3. **I2C Master Communication dengan ESP Slaves**
   - Write data ke ESP: `i2c.write(address, data)`
   - Read data dari ESP: `i2c.read(address, length)`
   - Polling semua ESP secara berkala
   - Error handling untuk slave yang tidak merespon

4. **GPIO Handling**
   - 8 tombol dengan debouncing
   - Buzzer control dengan PWM
   - 3 PWM output untuk motor pompa

5. **Logika Kontrol (sama dengan ESP-A)**
   - Pressurizer pressure control
   - Pump startup/shutdown sequence
   - Alarm logic (warning & critical)
   - Interlock untuk keamanan

**Library yang Dibutuhkan:**
```python
import smbus2          # I2C communication (dual bus support)
import board           # GPIO access
import digitalio       # GPIO digital
import pwmio           # PWM output
import threading       # Multi-threading untuk I2C
from PIL import Image, ImageDraw, ImageFont  # OLED display
import adafruit_ssd1306  # OLED driver
import struct          # Binary data packing
```

### B. ESP-B, C, E, F, G - I2C Slave Implementation

**⚠️ PERLU MODIFIKASI PADA SEMUA ESP**

**Perubahan yang Diperlukan:**

1. **Hapus Komunikasi UART**
   - Comment/hapus semua kode `Serial2.begin()`, `Serial2.print()`, `Serial2.read()`
   - Hapus UART RX/TX pin definitions

2. **Implementasi I2C Slave**
   ```cpp
   #include <Wire.h>
   
   #define I2C_SLAVE_ADDRESS 0x08  // Beda untuk setiap ESP
   
   // Buffer untuk receive data dari Master
   volatile uint8_t receiveBuffer[32];
   volatile uint8_t receiveLength = 0;
   volatile bool newDataAvailable = false;
   
   // Buffer untuk send data ke Master
   uint8_t sendBuffer[32];
   uint8_t sendLength = 0;
   
   void onReceive(int numBytes);  // Callback saat Master write
   void onRequest();               // Callback saat Master read
   ```

3. **Data Structure untuk I2C Communication**
   - **Struct untuk ESP-B (Slave 0x08):**
     - Receive: {pressure, pump1_status, pump2_status, pump3_status}
     - Send: {rod1_pos, rod2_pos, rod3_pos, kwThermal}
   
   - **Struct untuk ESP-C (Slave 0x09):**
     - Receive: {rod1_pos, rod2_pos, rod3_pos}
     - Send: {powerLevel, state, generator_status, turbine_status}
   
   - **Struct untuk ESP-E/F/G (Slave 0x0A/0x0B/0x0C):**
     - Receive: {pressure, pump_status}
     - Send: {animation_speed, led_status}

4. **Threading/Non-blocking**
   - I2C callbacks berjalan di interrupt context
   - Hanya update flag dan buffer, processing di loop()
   - Hindari delay() di dalam callback

---

## Pin Mapping Raspberry Pi

### I2C Buses (Dual I2C)
```
I2C Bus 0 (GPIO 0/1) - Jarang digunakan, untuk TCA9548A #1
  GPIO0  (SDA0) → TCA9548A #1 SDA (Display)
  GPIO1  (SCL0) → TCA9548A #1 SCL (Display)

I2C Bus 1 (GPIO 2/3) - Default, untuk TCA9548A #2
  GPIO2  (SDA1) → TCA9548A #2 SDA (ESP Slaves)
  GPIO3  (SCL1) → TCA9548A #2 SCL (ESP Slaves)

TCA9548A #1 Address: 0x70 (Display Multiplexer)
TCA9548A #2 Address: 0x71 (ESP Slaves Multiplexer)
OLED Address: 0x3C (pada setiap channel TCA9548A #1)
```

### GPIO untuk Tombol (Input)
```
GPIO5  → BTN_PRES_UP        (Naik tekanan)
GPIO6  → BTN_PRES_DOWN      (Turun tekanan)
GPIO4  → BTN_PUMP_PRIM_ON   (Pompa Primer ON)
GPIO17 → BTN_PUMP_PRIM_OFF  (Pompa Primer OFF)
GPIO27 → BTN_PUMP_SEC_ON    (Pompa Sekunder ON)
GPIO22 → BTN_PUMP_SEC_OFF   (Pompa Sekunder OFF)
GPIO10 → BTN_PUMP_TER_ON    (Pompa Tersier ON)
GPIO9  → BTN_PUMP_TER_OFF   (Pompa Tersier OFF)
```

### GPIO untuk Output
```
GPIO18 → BUZZER_PIN         (Hardware PWM untuk alarm)
GPIO12 → MOTOR_PRIM_PWM     (Hardware PWM Pompa Primer)
GPIO13 → MOTOR_SEC_PWM      (Hardware PWM Pompa Sekunder)
GPIO19 → MOTOR_TER_PWM      (Hardware PWM Pompa Tersier)
```

### I2C Slave Addresses (ESP32)
```
ESP-B: 0x08  (Batang Kendali & Reaktor)
ESP-C: 0x09  (Turbin & Generator)
ESP-E: 0x0A  (Visualizer Aliran Primer)
ESP-F: 0x0B  (Visualizer Aliran Sekunder)
ESP-G: 0x0C  (Visualizer Aliran Tersier)
```

---

## Protokol Komunikasi I2C

### 1. Raspberry Pi → ESP-B (Address 0x08)
**Master Write (RasPi → ESP-B):**
```python
# Data Structure (8 bytes)
data = struct.pack('ffBB', 
    pressure,           # float, 4 bytes - Tekanan pressurizer
    0.0,                # float, 4 bytes - Reserved
    pump1_status,       # uint8, 1 byte - Status pompa primer (0-3)
    pump2_status        # uint8, 1 byte - Status pompa sekunder (0-3)
)
i2c.write_i2c_block_data(0x08, 0x00, list(data))
```

**Master Read (RasPi ← ESP-B):**
```python
# Read 16 bytes dari ESP-B
data = i2c.read_i2c_block_data(0x08, 0x00, 16)
rod1, rod2, rod3, kwThermal = struct.unpack('BBBB', data)
# rod1-3: 0-100%, kwThermal: float
```

### 2. Raspberry Pi → ESP-C (Address 0x09)
**Master Write (RasPi → ESP-C):**
```python
# Data dari ESP-B diteruskan ke ESP-C
data = struct.pack('BBB', 
    rod1_position,      # uint8, 0-100%
    rod2_position,      # uint8, 0-100%
    rod3_position       # uint8, 0-100%
)
i2c.write_i2c_block_data(0x09, 0x00, list(data))
```

**Master Read (RasPi ← ESP-C):**
```python
# Read status turbin dan generator
data = i2c.read_i2c_block_data(0x09, 0x00, 8)
powerLevel, state = struct.unpack('fI', data)
```

### 3. Raspberry Pi → ESP-E/F/G (Address 0x0A/0x0B/0x0C)
**Master Write (RasPi → Visualizer):**
```python
# Data untuk animasi LED
data = struct.pack('fB', 
    pressure,           # float, 4 bytes
    pump_status         # uint8, 1 byte - Status pompa yang relevan
)
# ESP-E: pump1_status (Primer)
# ESP-F: pump2_status (Sekunder)  
# ESP-G: pump3_status (Tersier)
i2c.write_i2c_block_data(esp_address, 0x00, list(data))
```

**Master Read (RasPi ← Visualizer):**
```python
# Read status LED (optional untuk debugging)
data = i2c.read_i2c_block_data(esp_address, 0x00, 2)
animation_speed, led_count = struct.unpack('BB', data)
```

### Timing dan Polling Strategy
```python
# Polling Interval
POLL_INTERVAL_FAST = 0.05   # 50ms untuk ESP-B (critical data)
POLL_INTERVAL_NORMAL = 0.1  # 100ms untuk ESP-C
POLL_INTERVAL_SLOW = 0.2    # 200ms untuk ESP-E/F/G (visualizer)

# Sequence per cycle:
# 1. Write to ESP-B (pressure + pump status)
# 2. Read from ESP-B (rod positions)
# 3. Write to ESP-C (rod positions from ESP-B)
# 4. Read from ESP-C (power level)
# 5. Write to ESP-E/F/G (pressure + pump status)
```

### Error Handling
```python
try:
    i2c.write_i2c_block_data(address, reg, data)
except OSError as e:
    if e.errno == 121:  # Remote I/O error (slave tidak merespon)
        log_error(f"ESP at {hex(address)} not responding")
        retry_count += 1
    elif e.errno == 110:  # Timeout
        log_error(f"I2C timeout for {hex(address)}")
```

---

## Struktur Folder Baru

```
simulator_PLTN_v1.0/
├── RasPi_Central_Control/          # ← FOLDER BARU
│   ├── main.py                     # Program utama Raspberry Pi
│   ├── config.py                   # Konfigurasi pin dan konstanta
│   ├── tca9548a.py                 # Library TCA9548A I2C multiplexer
│   ├── oled_manager.py             # Manajemen 4 OLED
│   ├── pump_controller.py          # Kontrol pompa dan PWM
│   ├── pressure_controller.py      # Kontrol tekanan pressurizer
│   ├── uart_broadcaster.py         # UART communication
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Dokumentasi instalasi
│
├── ESP_B_Rev_1/                    # ← TIDAK BERUBAH
├── esp_c/                          # ← TIDAK BERUBAH
├── ESP_E_Aliran_Primer/            # ← TIDAK BERUBAH
├── ESP_F_Aliran_Sekunder/          # ← TIDAK BERUBAH
├── ESP_G_Aliran_Tersier/           # ← TIDAK BERUBAH
└── README.md                       # ← UPDATE dengan info migrasi
```

---

## Langkah Implementasi

### Phase 1: Persiapan Hardware
- [ ] Siapkan Raspberry Pi dan install Raspbian OS
- [ ] Hubungkan TCA9548A ke Raspberry Pi (I2C)
- [ ] Hubungkan 4 OLED ke TCA9548A (channel 0-3)
- [ ] Hubungkan 8 tombol ke GPIO Raspberry Pi
- [ ] Hubungkan buzzer dan 3 motor driver ke GPIO
- [ ] Hubungkan UART TX Raspberry Pi ke semua ESP RX (parallel)

### Phase 2: Software Development - Raspberry Pi
- [ ] Install Python dependencies di Raspberry Pi
- [ ] Enable I2C0 dan I2C1 di raspi-config
- [ ] Test TCA9548A #1 dan #2 dengan i2cdetect
- [ ] Implementasi `tca9548a.py` untuk dual multiplexer
- [ ] Implementasi `oled_manager.py` untuk display management
- [ ] Implementasi `i2c_master.py` untuk komunikasi dengan ESP
- [ ] Port logika kontrol dari ESP-A ke `main.py`
- [ ] Testing individual components

### Phase 3: Software Development - ESP Slaves
- [ ] **ESP-B:** Implementasi I2C Slave (0x08)
  - Hapus UART code
  - Add Wire.onReceive() dan Wire.onRequest()
  - Define data structure (receive: 8 bytes, send: 16 bytes)
  - Test dengan Raspberry Pi

- [ ] **ESP-C:** Implementasi I2C Slave (0x09)
  - Hapus UART code
  - Add I2C slave interface
  - Modify state machine untuk receive dari I2C
  - Test dengan Raspberry Pi

- [ ] **ESP-E/F/G:** Implementasi I2C Slave (0x0A/0x0B/0x0C)
  - Hapus UART code
  - Add I2C slave interface untuk receive pump status
  - LED animation tetap sama
  - Test dengan Raspberry Pi

### Phase 4: Integration Testing
- [ ] Test individual ESP dengan Raspberry Pi (one by one)
- [ ] Test broadcast dari Raspberry Pi ke ESP-E/F/G (visualizer)
- [ ] Test komunikasi Raspberry Pi → ESP-B (interlock)
- [ ] Test komunikasi Raspberry Pi → ESP-C (turbin control)
- [ ] Test keseluruhan alur simulasi
- [ ] Verify semua logika keamanan bekerja
- [ ] Stress test: Run 24 jam non-stop

### Phase 5: Optimization
- [ ] Fine-tune I2C polling timing
- [ ] Optimize data structure untuk minimal latency
- [ ] Add comprehensive error handling
- [ ] Implement data logging (CSV/database)
- [ ] Create web dashboard dengan Flask (optional)
- [ ] Add MQTT telemetry (optional)

---

## Keuntungan Migrasi ke Full I2C Architecture

### 1. **Komunikasi Terstruktur & Reliable**
   - ✅ Protocol standard dengan ACK/NACK
   - ✅ Error detection built-in
   - ✅ No data corruption seperti di UART
   - ✅ Bi-directional communication (read/write)

### 2. **Sentralisasi Kontrol**
   - ✅ Raspberry Pi sebagai **single point of control**
   - ✅ Semua data flow melalui master
   - ✅ Mudah untuk monitoring dan debugging
   - ✅ Data logging terpusat di Raspberry Pi

### 3. **Skalabilitas**
   - ✅ Mudah menambah ESP baru (tinggal tambah slave address)
   - ✅ Bisa tambah TCA9548A ketiga jika perlu
   - ✅ Maksimal 8 channel × 8 TCA9548A = 64 devices

### 4. **Synchronization**
   - ✅ Master mengontrol timing komunikasi
   - ✅ No race condition antar ESP
   - ✅ Deterministic behavior

### 5. **Processing Power**
   - ✅ Complex logic di Raspberry Pi (Python)
   - ✅ ESP fokus ke kontrol aktuator saja
   - ✅ Bisa tambah AI/ML untuk prediksi

### 6. **Network Integration**
   - ✅ Web dashboard via Flask/FastAPI
   - ✅ MQTT integration untuk IoT
   - ✅ Remote monitoring via WiFi/Ethernet
   - ✅ Data logging ke database (InfluxDB/MySQL)

---

## Risiko & Mitigasi (Updated untuk I2C)

### Risiko 1: I2C Bus Capacitance
- **Masalah:** I2C limited to ~400pF capacitance, kabel panjang bisa error
- **Mitigasi:** 
  - Gunakan kabel pendek (<20cm antar device)
  - Tambahkan pull-up resistor 2.2kΩ - 4.7kΩ
  - Gunakan I2C repeater jika jarak jauh (PCA9515)

### Risiko 2: I2C Clock Stretching
- **Masalah:** ESP32 slave mungkin perlu waktu processing, stretch clock
- **Mitigasi:**
  - Implement non-blocking I2C slave di ESP
  - Gunakan buffer untuk data receive/transmit
  - Set timeout di Raspberry Pi (1 second)

### Risiko 3: Multiple Bus Timing
- **Masalah:** Dual I2C bus bisa conflict jika tidak synchronized
- **Mitigasi:**
  - Gunakan threading dengan mutex lock
  - Separate thread untuk I2C0 (OLED) dan I2C1 (ESP)
  - Priority: ESP communication > Display update

### Risiko 4: Slave Address Conflict
- **Masalah:** Jika 2 ESP punya address sama, collision
- **Mitigasi:**
  - Hard-code unique address untuk setiap ESP
  - Document address map dengan jelas
  - Test dengan i2cdetect sebelum assembly

### Risiko 5: Data Latency
- **Masalah:** I2C polling bisa lebih lambat dari UART interrupt-based
- **Mitigasi:**
  - Optimize polling interval (50ms untuk critical data)
  - Gunakan multi-threading untuk parallel polling
  - Implement timeout dan skip untuk non-responsive slave

### Risiko 6: ESP32 I2C Slave Limitation
- **Masalah:** ESP32 I2C slave kadang unstable di Arduino framework
- **Mitigasi:**
  - Gunakan ESP-IDF native I2C slave driver (lebih stable)
  - Test thoroughly dengan stress test
  - Implement watchdog timer untuk auto-recovery
  - Fallback: Gunakan ESP32-S2/S3/C3 dengan better I2C slave support

---

## Testing Checklist

### Unit Testing
- [ ] TCA9548A channel switching berfungsi
- [ ] Semua 4 OLED dapat tampil bersamaan
- [ ] 8 tombol terdeteksi dengan benar
- [ ] Buzzer bunyi dengan pattern yang benar
- [ ] PWM motor smooth dari 0-255
- [ ] UART broadcast data valid

### Integration Testing
- [ ] ESP-E LED animasi sesuai status pompa primer
- [ ] ESP-F LED animasi sesuai status pompa sekunder
- [ ] ESP-G LED animasi sesuai status pompa tersier
- [ ] ESP-B interlock bekerja (batang hanya gerak jika pompa ON)
- [ ] ESP-C turbin start sesuai posisi batang kendali
- [ ] Emergency shutdown berfungsi di semua sistem

### System Testing
- [ ] Startup sequence lengkap (tekanan → pompa → batang → turbin)
- [ ] Normal operation berjalan stabil
- [ ] Shutdown sequence berfungsi dengan benar
- [ ] Emergency shutdown berfungsi
- [ ] Alarm warning dan critical berfungsi
- [ ] Sistem berjalan continuous minimal 1 jam tanpa error

---

## Estimasi Waktu (Updated untuk Full I2C)

- **Phase 1 (Hardware):** 2-3 hari
- **Phase 2 (Software - Raspberry Pi):** 5-7 hari
- **Phase 3 (Software - ESP Slaves):** 7-10 hari ⚠️ (Major changes)
- **Phase 4 (Integration Testing):** 4-5 hari
- **Phase 5 (Optimization):** 3-4 hari

**Total:** ~3-4 minggu untuk development dan testing lengkap

⚠️ **Note:** Phase 3 lebih lama karena perlu modifikasi semua 5 ESP untuk I2C slave

---

## Next Steps

1. **Review rencana ini** dengan tim
2. **Procurement hardware** yang dibutuhkan
3. **Setup development environment** di Raspberry Pi
4. **Mulai implementasi Phase 1**
5. **Dokumentasi setiap progress**

