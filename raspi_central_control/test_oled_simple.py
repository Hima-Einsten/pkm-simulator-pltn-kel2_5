#!/usr/bin/env python3
"""
Simple OLED Test - Minimal Dependencies
Test OLED dengan raw I2C commands tanpa library kompleks

Usage:
    python3 test_oled_simple.py

Requirements:
    pip3 install smbus2
"""

import sys
import os
import time

# Fix import path
user_site = os.path.expanduser('~/.local/lib/python3.7/site-packages')
if user_site not in sys.path:
    sys.path.insert(0, user_site)

try:
    import smbus2
    print("✓ smbus2 imported successfully")
except ImportError as e:
    print(f"✗ Failed to import smbus2: {e}")
    print("Install with: pip3 install smbus2")
    sys.exit(1)

# Try to import luma.oled
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    LUMA_AVAILABLE = True
    print("✓ luma.oled imported successfully")
except ImportError as e:
    LUMA_AVAILABLE = False
    print(f"⚠️  luma.oled not available: {e}")
    print("Will use basic I2C test only")

# Configuration
I2C_BUS = 1
MUX_1_ADDR = 0x70
MUX_2_ADDR = 0x71
OLED_ADDR = 0x3C

print("\n" + "="*60)
print("SIMPLE OLED TEST")
print("="*60)

# Initialize I2C bus
try:
    bus = smbus2.SMBus(I2C_BUS)
    print(f"✓ I2C Bus {I2C_BUS} opened")
except Exception as e:
    print(f"✗ Failed to open I2C bus: {e}")
    sys.exit(1)

# Test multiplexers
print("\n1. Testing TCA9548A Multiplexers...")
for mux_addr in [MUX_1_ADDR, MUX_2_ADDR]:
    try:
        bus.read_byte(mux_addr)
        print(f"   ✓ TCA9548A found at 0x{mux_addr:02X}")
    except:
        print(f"   ✗ TCA9548A NOT found at 0x{mux_addr:02X}")

# Test OLEDs on each channel
print("\n2. Testing OLEDs on each channel...")

test_configs = [
    (MUX_1_ADDR, 1, "PRESSURIZER"),
    (MUX_1_ADDR, 2, "PUMP PRIMARY"),
    (MUX_1_ADDR, 3, "PUMP SECONDARY"),
    (MUX_1_ADDR, 4, "PUMP TERTIARY"),
    (MUX_1_ADDR, 5, "SAFETY ROD"),
    (MUX_1_ADDR, 6, "SHIM ROD"),
    (MUX_1_ADDR, 7, "REGULATING ROD"),
    (MUX_2_ADDR, 1, "THERMAL POWER"),
    (MUX_2_ADDR, 2, "SYSTEM STATUS"),
]

results = []

for mux_addr, channel, name in test_configs:
    print(f"\n   Testing: {name} (MUX 0x{mux_addr:02X}, Ch{channel})")
    
    # Select channel
    try:
        channel_mask = 1 << channel
        bus.write_byte(mux_addr, channel_mask)
        time.sleep(0.002)
        print(f"      ✓ Channel selected")
    except Exception as e:
        print(f"      ✗ Failed to select channel: {e}")
        results.append((name, False))
        continue
    
    # Check if OLED responds
    try:
        bus.read_byte(OLED_ADDR)
        print(f"      ✓ OLED responds at 0x{OLED_ADDR:02X}")
        oled_found = True
    except:
        print(f"      ✗ OLED not found at 0x{OLED_ADDR:02X}")
        results.append((name, False))
        continue
    
    # Try to initialize and display if luma is available
    if LUMA_AVAILABLE:
        try:
            print(f"      → Initializing display...")
            serial = i2c(port=I2C_BUS, address=OLED_ADDR)
            device = ssd1306(serial, width=128, height=64)
            
            print(f"      → Clearing display...")
            device.clear()
            time.sleep(0.1)
            
            print(f"      → Drawing test pattern...")
            with canvas(device) as draw:
                # Border
                draw.rectangle(device.bounding_box, outline="white", fill="black")
                
                # Title
                draw.text((10, 10), "PLTN TEST", fill="white")
                draw.text((10, 30), name, fill="white")
                draw.text((10, 50), "ACTIVE", fill="white")
            
            print(f"      ✓ Display ACTIVE - Check OLED screen!")
            results.append((name, True))
            time.sleep(1)
            
        except Exception as e:
            print(f"      ✗ Display failed: {e}")
            results.append((name, False))
    else:
        # Basic test - just check communication
        try:
            # Send display ON command
            bus.write_i2c_block_data(OLED_ADDR, 0x00, [0xAF])
            print(f"      ✓ Command sent (basic test)")
            results.append((name, True))
        except Exception as e:
            print(f"      ✗ Command failed: {e}")
            results.append((name, False))

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = 0
failed = 0

for name, success in results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{name:.<35} {status}")
    if success:
        passed += 1
    else:
        failed += 1

print(f"\nTotal: {passed} PASS, {failed} FAIL")

if LUMA_AVAILABLE and passed > 0:
    print("\n✓ OLEDs should be ACTIVE and showing test pattern!")
    print("  Check each OLED display physically.")
elif not LUMA_AVAILABLE:
    print("\n⚠️  Basic I2C test only (luma.oled not available)")
    print("   Install luma.oled for full display test:")
    print("   pip3 install luma.oled pillow")

if failed > 0:
    print("\n⚠️  Some OLEDs failed. Check:")
    print("   1. Wiring (VCC=3.3V, GND, SDA, SCL)")
    print("   2. TCA9548A channel connections")
    print("   3. OLED power supply")

bus.close()
print("\n✓ Test complete")
