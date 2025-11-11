# ESP-B I2C Slave - Batang Kendali & Reaktor

## 📋 Spesifikasi

- **I2C Slave Address:** `0x08`
- **Role:** Control Rod Controller & Reactor Core Simulation
- **Communication:** I2C dengan Raspberry Pi (Master)

## 🔌 Hardware yang Dibutuhkan

### Input:
- 6x Push buttons (Rod UP/DOWN untuk 3 batang)
- 1x Emergency button
- 1x Buzzer

### Output:
- 3x Servo motor (untuk 3 batang kendali)
- 4x OLED display 128x32 (via PCA9548A multiplexer)

### Connections:
```
Servo Pins:
- Rod 1: GPIO 13
- Rod 2: GPIO 14
- Rod 3: GPIO 15

Button Pins:
- Rod 1 UP: GPIO 0
- Rod 1 DOWN: GPIO 5
- Rod 2 UP: GPIO 4
- Rod 2 DOWN: GPIO 2
- Rod 3 UP: GPIO 12
- Rod 3 DOWN: GPIO 23
- Emergency: GPIO 19

Buzzer: GPIO 18

I2C (untuk OLED via PCA9548A):
- SDA: GPIO 21
- SCL: GPIO 22
```

## 📊 Data Protocol

### Receives from Master (Raspberry Pi):
```cpp
Byte 0-3: float pressure      // Tekanan pressurizer (bar)
Byte 4-7: float reserved      // Reserved untuk future use
Byte 8:   uint8 pump1_status  // Status pompa primer (0-3)
Byte 9:   uint8 pump2_status  // Status pompa sekunder (0-3)
Total: 10 bytes
```

### Sends to Master:
```cpp
Byte 0:   uint8 rod1_pos      // Posisi batang 1 (0-100%)
Byte 1:   uint8 rod2_pos      // Posisi batang 2 (0-100%)
Byte 2:   uint8 rod3_pos      // Posisi batang 3 (0-100%)
Byte 3:   uint8 reserved      // Reserved
Byte 4-7: float kwThermal     // Daya termal (kW)
Byte 8-11: float reserved     // Reserved
Byte 12-15: float reserved    // Reserved
Total: 16 bytes
```

## 🔐 Interlock Logic

Batang kendali **hanya bisa digerakkan** jika memenuhi kondisi:
1. Tekanan ≥ 40 bar
2. Pompa primer ON (status = 2)
3. Pompa sekunder ON (status = 2)

## 🚨 Emergency Function

- Tekan tombol Emergency → semua batang turun ke 0%
- Buzzer bunyi 1 detik
- Flag emergency tetap aktif sampai reset

## 📦 Upload ke ESP32

### Arduino IDE:
1. Buka file `ESP_B_I2C.ino`
2. Install library yang diperlukan:
   - ESP32Servo
   - Adafruit_SSD1306
   - Adafruit_GFX
3. Select board: ESP32 Dev Module
4. Upload

### PlatformIO:
```bash
pio lib install "ESP32Servo"
pio lib install "Adafruit SSD1306"
pio lib install "Adafruit GFX Library"
pio run --target upload
```

## 🧪 Testing

### Test I2C Communication:
```cpp
// Di Serial Monitor, akan muncul:
// "I2C Slave initialized at address 0x08"
// "Received: P=150.0, Pump1=2, Pump2=2"
```

### Test Buttons:
- Tekan tombol UP/DOWN → servo bergerak
- Lihat OLED display untuk konfirmasi posisi

### Test Interlock:
- Jika tekanan < 40 atau pompa tidak ON → batang tidak bisa gerak

## ⚙️ Configuration

Edit di file `.ino` jika perlu ubah pin:
```cpp
#define ROD1_SERVO_PIN 13  // Ubah sesuai wiring
#define I2C_SLAVE_ADDRESS 0x08  // Ubah jika conflict
```

## 🐛 Troubleshooting

**I2C not detected:**
- Check wiring SDA/SCL
- Pastikan address tidak conflict
- Test dengan i2cdetect di Raspberry Pi

**Servo tidak bergerak:**
- Check interlock conditions
- Pastikan tombol wiring correct
- Test servo dengan contoh code ESP32Servo

**OLED tidak muncul:**
- Check PCA9548A wiring
- Test OLED address (0x3C atau 0x3D)
- Check channel selection

---

✅ **Ready to use!** Upload ke ESP32 dan test dengan Raspberry Pi I2C Master.
