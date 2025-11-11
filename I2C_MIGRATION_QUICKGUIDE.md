# Migrasi ke Full I2C Architecture - Quick Guide

## 🎯 Konsep Utama

**Mengubah sistem dari UART-based menjadi I2C Master-Slave architecture:**
- ✅ Raspberry Pi sebagai **I2C Master**
- ✅ Semua ESP32 sebagai **I2C Slave**
- ✅ 2x TCA9548A multiplexer untuk ekspansi I2C
- ✅ Komunikasi terstruktur dengan binary protocol

---

## 🏗️ Arsitektur Hardware

```
Raspberry Pi (I2C Master)
├─ I2C Bus 0 → TCA9548A #1 (0x70) - Display
│   ├─ CH0: OLED Pressurizer (0x3C)
│   ├─ CH1: OLED Pump Primary (0x3C)
│   ├─ CH2: OLED Pump Secondary (0x3C)
│   └─ CH3: OLED Pump Tertiary (0x3C)
│
└─ I2C Bus 1 → TCA9548A #2 (0x71) - ESP Slaves
    ├─ CH0: ESP-B (0x08) - Batang Kendali
    ├─ CH1: ESP-C (0x09) - Turbin & Generator
    ├─ CH2: ESP-E (0x0A) - Visualizer Primer
    ├─ CH3: ESP-F (0x0B) - Visualizer Sekunder
    └─ CH4: ESP-G (0x0C) - Visualizer Tersier
```

---

## 📊 Data Flow

```
┌──────────────────────────────────────────────────────────┐
│  Raspberry Pi (Python)                                    │
│  - Baca input tombol                                      │
│  - Update pressure & pump status                          │
│  - Display ke OLED via TCA9548A #1                        │
└───────────┬──────────────────────────────────────────────┘
            │ I2C Write/Read
            ↓
┌───────────┴──────────────────────────────────────────────┐
│  ESP-B (I2C Slave 0x08)                                   │
│  Receive: {pressure, pump1, pump2}                        │
│  Send: {rod1, rod2, rod3, kwThermal}                      │
└───────────┬──────────────────────────────────────────────┘
            │ (RasPi forward data rod positions)
            ↓
┌───────────┴──────────────────────────────────────────────┐
│  ESP-C (I2C Slave 0x09)                                   │
│  Receive: {rod1, rod2, rod3}                              │
│  Send: {powerLevel, state, status}                        │
└──────────────────────────────────────────────────────────┘

            (Parallel communication)
            ↓
┌──────────────────────────────────────────────────────────┐
│  ESP-E/F/G (I2C Slave 0x0A/0x0B/0x0C)                    │
│  Receive: {pressure, pump_status}                         │
│  Send: {animation_speed, led_count}                       │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Perubahan yang Diperlukan

### Hardware
1. ✅ Raspberry Pi 3/4 atau Zero 2W
2. ✅ 2x TCA9548A I2C Multiplexer
3. ✅ Jumper wire untuk koneksi I2C (pendek <20cm)
4. ✅ Pull-up resistor 4.7kΩ untuk SDA/SCL (jika perlu)
5. ✅ Relokasi 8 tombol, buzzer, motor dari ESP-A ke RasPi

### Software - Raspberry Pi (Python)
```
RasPi_Central_Control/
├── main.py                 # Program utama
├── config.py               # Konfigurasi pin & parameter
├── tca9548a.py            # Library multiplexer
├── i2c_master.py          # I2C Master communication
├── oled_manager.py        # Display management
├── pump_controller.py     # PWM motor control
└── requirements.txt       # Dependencies
```

### Software - ESP32 (Arduino/C++)
**Perubahan pada ESP-B, C, E, F, G:**
1. ❌ **Hapus** semua code UART (Serial2.begin, read, write)
2. ✅ **Tambah** I2C Slave implementation
   ```cpp
   Wire.begin(SLAVE_ADDRESS, SDA_PIN, SCL_PIN);
   Wire.onReceive(onReceiveCallback);
   Wire.onRequest(onRequestCallback);
   ```
3. ✅ **Update** data structure untuk binary protocol
4. ✅ **Test** dengan i2cdetect di Raspberry Pi

---

## 📋 Protokol I2C

### Master → ESP-B (0x08)
```python
# Write 10 bytes
data = struct.pack('ffBB', 
    pressure,        # float 4B
    0.0,             # reserved 4B  
    pump1_status,    # uint8 1B
    pump2_status     # uint8 1B
)
```

### Master ← ESP-B (0x08)
```python
# Read 16 bytes
rod1, rod2, rod3, _, kwThermal, _, _ = struct.unpack('BBBBfff', data)
```

### Master → ESP-C (0x09)
```python
# Write 3 bytes
data = struct.pack('BBB', rod1, rod2, rod3)
```

### Master → ESP-E/F/G (0x0A/0x0B/0x0C)
```python
# Write 5 bytes
data = struct.pack('fB', pressure, pump_status)
```

---

## ⚠️ Hal Penting

### ESP32 I2C Slave Limitation
- ESP32 I2C slave di Arduino framework **kadang unstable**
- **Solusi 1:** Gunakan ESP-IDF native (lebih kompleks tapi stable)
- **Solusi 2:** Test thoroughly, implement watchdog
- **Solusi 3:** Fallback ke ESP32-S3/C3 (better I2C slave)

### I2C Bus Reliability
- Kabel maksimal 20cm antar device
- Gunakan twisted pair untuk SDA/SCL
- Tambahkan pull-up resistor 4.7kΩ
- Avoid long cable runs (use I2C repeater jika perlu)

### Timing & Performance
- Polling interval: 50ms (ESP-B), 100ms (ESP-C), 200ms (ESP-E/F/G)
- I2C clock: 100kHz (standard) atau 400kHz (fast mode)
- Timeout: 1 second untuk setiap transaksi
- Threading untuk parallel I2C communication

---

## 📈 Keuntungan vs UART

| Aspek | UART | I2C (New) |
|-------|------|-----------|
| Topology | Point-to-point | Multi-drop (1 master, banyak slave) |
| Wiring | 1 TX + 1 RX per connection | 2 wire (SDA+SCL) untuk semua |
| Error Detection | ❌ None | ✅ ACK/NACK |
| Bi-directional | ✅ Full-duplex | ✅ Half-duplex |
| Sentralisasi | ❌ Distributed | ✅ Centralized di RasPi |
| Debugging | Sulit | ✅ Mudah (i2cdetect, i2cdump) |
| Scalability | ❌ Butuh banyak pin | ✅ Unlimited (via multiplexer) |

---

## 🚀 Langkah Implementasi

### Week 1: Hardware Setup
- [ ] Install Raspbian OS di Raspberry Pi
- [ ] Enable I2C di raspi-config
- [ ] Hubungkan 2x TCA9548A
- [ ] Hubungkan 4 OLED ke TCA9548A #1
- [ ] Test dengan `i2cdetect -y 0` dan `i2cdetect -y 1`

### Week 2: Raspberry Pi Software
- [ ] Install Python dependencies
- [ ] Implement I2C master communication
- [ ] Implement OLED display manager
- [ ] Port control logic dari ESP-A
- [ ] Test dengan dummy I2C slave (Arduino)

### Week 3: ESP32 Software Migration
- [ ] Modify ESP-B untuk I2C slave
- [ ] Modify ESP-C untuk I2C slave
- [ ] Modify ESP-E/F/G untuk I2C slave
- [ ] Individual testing dengan Raspberry Pi

### Week 4: Integration & Testing
- [ ] Full system integration test
- [ ] Verify interlock logic
- [ ] Stress test (24 jam continuous)
- [ ] Fine-tuning & optimization

---

## 📞 Troubleshooting

### ESP tidak terdeteksi di i2cdetect
- Cek wiring SDA/SCL
- Cek alamat I2C di code ESP
- Cek pull-up resistor
- Test ESP dengan Arduino sebagai master

### I2C communication timeout/error
- Reduce I2C clock speed (100kHz)
- Shorten cable length
- Implement retry logic di Python
- Check ESP I2C slave implementation

### Data corruption
- Verify data structure packing (struct.pack)
- Check byte order (little/big endian)
- Implement CRC checksum (optional)

---

## 📚 File Template Tersedia

1. ✅ `MIGRATION_PLAN.md` - Dokumentasi lengkap
2. ✅ `ESP_B_I2C_Slave_Template.ino` - Template ESP-B
3. ⏳ `RasPi_Central_Control/` - Python code (WIP)
4. ⏳ Template untuk ESP-C, E, F, G (coming soon)

---

**Status:** ✅ Planning Complete | 🔄 Ready for Implementation
**Estimasi:** 3-4 minggu development + testing
**Author:** System Migration Team
**Date:** 2025-11-11
