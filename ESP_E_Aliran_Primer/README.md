# ESP-E/F/G I2C Slave - Flow Visualizers

## 📋 Spesifikasi

| ESP | Address | Role |
|-----|---------|------|
| ESP-E | 0x0A | Visualizer Aliran Primer |
| ESP-F | 0x0B | Visualizer Aliran Sekunder |
| ESP-G | 0x0C | Visualizer Aliran Tersier |

## 🔌 Hardware yang Dibutuhkan

### Output:
- 16x LED (untuk animasi aliran)

### Connections:
```
LED Pins (GPIO):
13, 12, 14, 27, 26, 25, 33, 32,
15, 2, 0, 4, 16, 17, 5, 18

I2C:
- SDA: GPIO 21
- SCL: GPIO 22
```

## 📊 Data Protocol

### Receives from Master (Raspberry Pi):
```cpp
Byte 0-3: float pressure    // Tekanan system (bar)
Byte 4:   uint8 pump_status // Status pompa yang relevan
Total: 5 bytes

ESP-E menerima: Primary Pump Status
ESP-F menerima: Secondary Pump Status
ESP-G menerima: Tertiary Pump Status
```

### Sends to Master:
```cpp
Byte 0: uint8 animation_speed  // Kecepatan animasi
Byte 1: uint8 led_count        // Jumlah LED (16)
Total: 2 bytes
```

## 🎨 Animation Logic

### Pump Status → Animation Speed:

| Status | Name | Interval | Speed Value |
|--------|------|----------|-------------|
| 0 | OFF | No animation | 0 |
| 1 | STARTING | 300ms | 33 |
| 2 | ON | 100ms | 100 |
| 3 | SHUTTING_DOWN | 500ms | 20 |

### Animation Pattern:
```
LED sequence: 0 → 1 → 2 → ... → 15 → 0 (loop)
Only one LED active at a time
```

## 📦 Upload ke ESP32

### Arduino IDE:
1. Buka file yang sesuai:
   - `ESP_E_I2C.ino` untuk ESP-E
   - `ESP_F_I2C.ino` untuk ESP-F
   - `ESP_G_I2C.ino` untuk ESP-G
2. **PENTING:** Pastikan I2C address sudah benar!
3. Select board: ESP32 Dev Module
4. Upload

### PlatformIO:
```bash
pio run --target upload
```

## 🎯 Perbedaan Antar ESP

**ESP-E (0x0A):**
- Visualizer untuk aliran primer
- Menerima status Pompa Primer dari Raspberry Pi

**ESP-F (0x0B):**
- Visualizer untuk aliran sekunder
- Menerima status Pompa Sekunder dari Raspberry Pi

**ESP-G (0x0C):**
- Visualizer untuk aliran tersier
- Menerima status Pompa Tersier dari Raspberry Pi

## 🧪 Testing

### Serial Monitor Output:
```
ESP-E (Primary Flow Visualizer) I2C Slave Starting...
I2C Slave initialized at address 0x0A
ESP-E Ready!
Pressure: 150.0 bar | Pump Status: 2
```

### Test Animation:
1. Power ON ESP → LED startup sequence
2. Receive pump status = 2 (ON) → fast animation
3. Receive pump status = 0 (OFF) → all LEDs off

## ⚙️ Configuration

### Ubah I2C Address (jika conflict):
```cpp
// ESP-E
#define I2C_SLAVE_ADDRESS 0x0A

// ESP-F
#define I2C_SLAVE_ADDRESS 0x0B

// ESP-G
#define I2C_SLAVE_ADDRESS 0x0C
```

### Ubah LED Pins (sesuai wiring):
```cpp
const int ledPins[NUM_LEDS] = {
    13, 12, 14, 27, 26, 25, 33, 32,
    15, 2, 0, 4, 16, 17, 5, 18
};
```

### Ubah Animation Speed:
```cpp
case 2: // ON
    animationInterval = 100; // Fast (ubah nilai ini)
    animationSpeed = 100;
    break;
```

## 🐛 Troubleshooting

**LED tidak menyala:**
- Check LED orientation (anoda/katoda)
- Check GPIO pin output dengan multimeter
- Test LED dengan digitalWrite manual

**Animation tidak smooth:**
- Periksa power supply
- Reduce LED count jika perlu
- Check timing di Serial Monitor

**I2C tidak terdeteksi:**
- Verify address dengan i2cdetect
- Check SDA/SCL connection
- Pastikan tidak ada address conflict

**Semua LED menyala bersamaan:**
- Check logic di updateAnimation()
- Pastikan clear LED sebelum set new position

## 💡 Tips

1. **Power Supply:** Gunakan power supply terpisah untuk LED jika >50mA
2. **Resistor:** Tambahkan resistor 220Ω-330Ω untuk setiap LED
3. **Testing:** Test satu LED dulu sebelum connect semua
4. **Wiring:** Gunakan color code untuk memudahkan troubleshoot

---

✅ **Ready to use!** Upload ke masing-masing ESP dengan address yang benar.
