# ESP-E Wiring - 3 Flow Visualizers (Primer, Sekunder, Tersier)

## 📊 System Overview

**1 ESP32 mengontrol 3 Multiplexer CD74HC4067 = 48 LED Total**

- **Flow 1 (Primer):** 16 LED - Multiplexer #1
- **Flow 2 (Sekunder):** 16 LED - Multiplexer #2
- **Flow 3 (Tersier):** 16 LED - Multiplexer #3

## 🔌 Wiring Diagram

### A. Shared Selector Pins (1 set untuk 3 multiplexer)

| ESP32 Pin | Connect To | Function |
|-----------|------------|----------|
| GPIO 14   | S0 (All 3 MUX) | Selector bit 0 |
| GPIO 27   | S1 (All 3 MUX) | Selector bit 1 |
| GPIO 26   | S2 (All 3 MUX) | Selector bit 2 |
| GPIO 25   | S3 (All 3 MUX) | Selector bit 3 |

**Catatan:** Pin S0-S3 di-PARALLEL ke 3 multiplexer!

### B. Individual Control Pins (1 per multiplexer)

#### Multiplexer #1 (Primer):
| ESP32 Pin | MUX #1 Pin | Function |
|-----------|------------|----------|
| GPIO 33   | EN         | Enable (LOW = active) |
| GPIO 32   | SIG/COM    | PWM Signal output |

#### Multiplexer #2 (Sekunder):
| ESP32 Pin | MUX #2 Pin | Function |
|-----------|------------|----------|
| GPIO 15   | EN         | Enable (LOW = active) |
| GPIO 4    | SIG/COM    | PWM Signal output |

#### Multiplexer #3 (Tersier):
| ESP32 Pin | MUX #3 Pin | Function |
|-----------|------------|----------|
| GPIO 2    | EN         | Enable (LOW = active) |
| GPIO 16   | SIG/COM    | PWM Signal output |

### C. Power Supply (Shared)

| ESP32 Pin | Connect To | Function |
|-----------|------------|----------|
| 3.3V      | VCC (All 3 MUX) | Power |
| GND       | GND (All 3 MUX) | Ground |

### D. I2C Communication

| ESP32 Pin | PCA9548A Pin | Function |
|-----------|--------------|----------|
| GPIO 21   | SDA (Ch 2)   | I2C Data |
| GPIO 22   | SCL (Ch 2)   | I2C Clock |

### E. LED Connections (Per Multiplexer)

**Each Multiplexer:**
```
C0-C15 → Resistor 220Ω → LED Anode (+) → LED Cathode (-) → GND
```

**Total LEDs:** 3 x 16 = 48 LED

## 🎨 Visual Diagram

```
                         ESP32
         ┌───────────────────────────────────┐
         │                                   │
         │  S0 (14) ──┬────┬────┬────────┐  │
         │  S1 (27) ──┼────┼────┼───┐    │  │
         │  S2 (26) ──┼────┼────┼┐  │    │  │
         │  S3 (25) ──┼────┼────┼┼┐ │    │  │
         │            │    │    │││ │    │  │
         │  EN (33) ──┤    │    │││ │    │  │
         │  SIG(32) ──┤    │    │││ │    │  │
         │            │    │    │││ │    │  │
         │  EN (15) ───────┤    │││ │    │  │
         │  SIG (4) ───────┤    │││ │    │  │
         │                 │    │││ │    │  │
         │  EN  (2) ────────────┤││ │    │  │
         │  SIG(16) ────────────┤││ │    │  │
         │                      │││ │    │  │
         │  GPIO 21 (SDA) ──────┼┼┼─┼────┼──┤
         │  GPIO 22 (SCL) ──────┼┼┼─┼────┼──┤
         │                      │││ │    │  │
         └──────────────────────┼┼┼─┼────┼──┘
                                │││ │    │
              ┌─────────────────┘││ │    │
              │  ┌────────────────┘│ │    │
              │  │  ┌──────────────┘ │    │
              │  │  │  ┌─────────────┘    │
              ▼  ▼  ▼  ▼                  ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │   MUX #1     │  │   MUX #2     │  │   MUX #3     │
         │  (Primer)    │  │ (Sekunder)   │  │  (Tersier)   │
         │              │  │              │  │              │
         │ S0 S1 S2 S3  │  │ S0 S1 S2 S3  │  │ S0 S1 S2 S3  │
         │ EN  SIG      │  │ EN  SIG      │  │ EN  SIG      │
         │              │  │              │  │              │
         │ C0-C15       │  │ C0-C15       │  │ C0-C15       │
         └──┬───────────┘  └──┬───────────┘  └──┬───────────┘
            │                 │                 │
            ▼                 ▼                 ▼
      16 LEDs (Primer)   16 LEDs (Sekunder) 16 LEDs (Tersier)
```

## ⚡ Power Requirements

### Current Draw:
- **Per LED:** ~20mA (max)
- **48 LEDs:** 48 x 20mA = 960mA max
- **ESP32:** ~200mA
- **Total:** ~1.2A max

### Power Options:

#### Option 1: ESP32 Power Only (Testing)
- **Pros:** Simple, no external supply
- **Cons:** May brownout with 48 LEDs at full brightness
- **Use for:** Testing with low brightness or few LEDs active

#### Option 2: External 5V Supply (Recommended)
```
5V Power Supply (2A+)
  ├─→ ESP32 VIN (5V)
  └─→ LED Common GND
```
- **Pros:** Stable, no brownout
- **Recommended:** 5V 2A USB power adapter

## 🎯 Pin Usage Summary

| Function | GPIO Pins | Count |
|----------|-----------|-------|
| Shared Selectors | 14, 27, 26, 25 | 4 |
| Enable Pins | 33, 15, 2 | 3 |
| Signal PWM | 32, 4, 16 | 3 |
| I2C | 21, 22 | 2 |
| **Total Used** | | **12 pins** |
| **Available** | | **18+ pins** |

## 🔍 Testing Checklist

### Before Power On:
- [ ] S0-S3 connected in PARALLEL to all 3 multiplexers
- [ ] Each MUX has unique EN pin (33, 15, 2)
- [ ] Each MUX has unique SIG pin (32, 4, 16)
- [ ] All VCC connected to 3.3V
- [ ] All GND connected to common ground
- [ ] 48 LED dengan resistor terpasang correct polarity
- [ ] I2C SDA/SCL connected to PCA9548A channel 2

### After Power On:
1. **Serial Monitor:** Should show startup animation testing all 3 flows
2. **Visual:** Each flow lights up sequentially
3. **Test Python script:** Send different status to each flow

## 🐛 Troubleshooting

### Only 1 flow works:
- Check EN pins - each must have unique GPIO
- Verify EN = LOW (0V) untuk enable

### LEDs flicker:
- Power supply insufficient
- Use external 5V 2A supply

### Random LED patterns:
- Check S0-S3 wiring - must be parallel to all MUX
- Verify no loose connections

### I2C not receiving:
- Check GPIO 21/22 connections
- Verify ESP32 at address 0x0A

---

✅ **Ready for 48-LED flowing animation system!**
