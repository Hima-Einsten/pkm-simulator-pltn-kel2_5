# ESP-C I2C Slave - Turbin & Generator

## 📋 Spesifikasi

- **I2C Slave Address:** `0x09`
- **Role:** Turbine & Generator Control System
- **Communication:** I2C dengan Raspberry Pi (Master)

## 🔌 Hardware yang Dibutuhkan

### Output:
- 4x Relay (Steam Generator, Turbine, Condenser, Cooling Tower)
- 4x Motor/Fan (untuk simulasi komponen)

### Connections:
```
Relay Pins:
- Steam Generator: GPIO 25
- Turbine: GPIO 26
- Condenser: GPIO 27
- Cooling Tower: GPIO 14

Motor/Fan PWM Pins:
- Steam Generator Motor: GPIO 12
- Turbine Motor: GPIO 13
- Condenser Motor: GPIO 32
- Cooling Tower Motor: GPIO 33

I2C:
- SDA: GPIO 21
- SCL: GPIO 22
```

## 📊 Data Protocol

### Receives from Master (Raspberry Pi):
```cpp
Byte 0: uint8 rod1_pos  // Posisi batang 1 (0-100%)
Byte 1: uint8 rod2_pos  // Posisi batang 2 (0-100%)
Byte 2: uint8 rod3_pos  // Posisi batang 3 (0-100%)
Total: 3 bytes
```

### Sends to Master:
```cpp
Byte 0-3: float powerLevel      // Level daya output (0-100%)
Byte 4-7: uint32 state          // State machine (0-3)
Byte 8:   uint8 generator_status  // Status generator (0/1)
Byte 9:   uint8 turbine_status    // Status turbine (0/1)
Total: 10 bytes
```

## 🔄 State Machine

```
IDLE (0)
  ↓ (rod avg > 10%)
STARTING_UP (1)
  ↓ (power reaches target)
RUNNING (2)
  ↓ (rod avg < 5%)
SHUTTING_DOWN (3)
  ↓ (power reaches 0)
IDLE (0)
```

## ⚡ Power Calculation

```cpp
Average Rod Position = (rod1 + rod2 + rod3) / 3
Target Power = Average Rod Position (%)

State STARTING_UP:
  - Power increases by 2% per cycle
  
State RUNNING:
  - Power = Target Power

State SHUTTING_DOWN:
  - Power decreases by 2% per cycle
```

## 🎛️ Component Control

### Activation Thresholds:
- **Steam Generator:** Power > 20%
- **Turbine:** Power > 30%
- **Condenser:** Power > 20%
- **Cooling Tower:** Power > 15%

### PWM Output:
```cpp
PWM = map(powerLevel, 0, 100, 0, 255)
```

## 📦 Upload ke ESP32

### Arduino IDE:
1. Buka file `ESP_C_I2C.ino`
2. Install library: Wire (built-in)
3. Select board: ESP32 Dev Module
4. Upload

### PlatformIO:
```bash
pio run --target upload
```

## 🧪 Testing

### Serial Monitor Output:
```
ESP-C I2C Slave Starting...
I2C Slave initialized at address 0x09
ESP-C Ready!
Rods: 50,50,50 | Power: 50.0% | State: 2
```

### Test Sequence:
1. Master mengirim rod positions (contoh: 50,50,50)
2. ESP-C calculate average = 50%
3. State machine: IDLE → STARTING_UP → RUNNING
4. Power level increases gradually to 50%
5. Relays dan motors activated sesuai threshold

## ⚙️ Configuration

Edit jika perlu ubah pin:
```cpp
#define I2C_SLAVE_ADDRESS 0x09
#define RELAY_STEAM_GEN 25
#define MOTOR_STEAM_GEN_PIN 12
// dst...
```

## 🐛 Troubleshooting

**Relay tidak aktif:**
- Check power supply relay
- Test relay dengan digitalWrite manual
- Check threshold power level

**Motor tidak berputar:**
- Check PWM pin connection
- Test dengan analogWrite manual
- Pastikan power supply cukup

**I2C communication error:**
- Check SDA/SCL wiring
- Verify slave address dengan i2cdetect
- Check pull-up resistors (4.7kΩ)

---

✅ **Ready to use!** Upload dan test dengan Raspberry Pi Master.
