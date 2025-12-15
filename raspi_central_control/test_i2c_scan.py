#!/usr/bin/env python3
"""
I2C Hardware Diagnostic Tool
Tests multiplexer routing and ESP device detection
"""

import smbus2
import time
import sys

def scan_i2c_bus(bus_num=1):
    """Scan main I2C bus for devices"""
    print(f"\n{'='*60}")
    print(f"Scanning I2C Bus {bus_num} (Main Bus)")
    print(f"{'='*60}")
    
    try:
        bus = smbus2.SMBus(bus_num)
    except Exception as e:
        print(f"❌ Failed to open I2C bus {bus_num}: {e}")
        return None, []
    
    devices = []
    print("\nScanning addresses 0x03 to 0x77...")
    
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
            device_name = get_device_name(addr)
            print(f"  ✅ 0x{addr:02X} - {device_name}")
        except:
            pass
    
    if not devices:
        print("  ❌ No devices found!")
    
    return bus, devices


def get_device_name(addr):
    """Get friendly name for I2C address"""
    names = {
        0x08: "ESP-BC (should be behind MUX)",
        0x0A: "ESP-E (should be behind MUX)",
        0x3C: "OLED (should be behind MUX)",
        0x70: "TCA9548A #1 (Multiplexer)",
        0x71: "TCA9548A #2 (Multiplexer)",
    }
    return names.get(addr, "Unknown")


def test_multiplexer(bus, mux_addr, mux_name):
    """Test TCA9548A multiplexer channels"""
    print(f"\n{'='*60}")
    print(f"Testing {mux_name} (0x{mux_addr:02X})")
    print(f"{'='*60}")
    
    try:
        # Test if multiplexer responds
        bus.read_byte(mux_addr)
        print(f"✅ Multiplexer 0x{mux_addr:02X} responding")
    except Exception as e:
        print(f"❌ Multiplexer 0x{mux_addr:02X} NOT responding: {e}")
        return False
    
    print("\nScanning all 8 channels...")
    
    for channel in range(8):
        try:
            # Select channel
            channel_mask = 1 << channel
            bus.write_byte(mux_addr, channel_mask)
            time.sleep(0.05)
            
            # Scan for devices on this channel
            devices = []
            for addr in range(0x03, 0x78):
                if addr == mux_addr:  # Skip multiplexer itself
                    continue
                try:
                    bus.read_byte(addr)
                    devices.append(addr)
                except:
                    pass
            
            if devices:
                device_list = ", ".join([f"0x{a:02X}" for a in devices])
                print(f"  Channel {channel}: {device_list}")
                
                # Show what should be on this channel
                if mux_addr == 0x70:
                    expected = {
                        0: "ESP-BC (0x08)",
                        1: "OLED #1 (0x3C)",
                        2: "OLED #2 (0x3C)",
                        3: "OLED #3 (0x3C)",
                        4: "OLED #4 (0x3C)",
                        5: "OLED #5 (0x3C)",
                        6: "OLED #6 (0x3C)",
                        7: "OLED #7 (0x3C)",
                    }
                else:  # 0x71
                    expected = {
                        0: "ESP-E (0x0A)",
                        1: "OLED #8 (0x3C)",
                        2: "OLED #9 (0x3C)",
                    }
                
                exp = expected.get(channel, "Nothing expected")
                print(f"             Expected: {exp}")
            else:
                print(f"  Channel {channel}: No devices")
        
        except Exception as e:
            print(f"  Channel {channel}: Error - {e}")
    
    # Disable all channels
    try:
        bus.write_byte(mux_addr, 0x00)
    except:
        pass
    
    return True


def test_esp_direct(bus, esp_addr, esp_name, mux_addr, mux_channel):
    """Test ESP communication through multiplexer"""
    print(f"\n{'='*60}")
    print(f"Testing {esp_name} (0x{esp_addr:02X})")
    print(f"Via MUX 0x{mux_addr:02X}, Channel {mux_channel}")
    print(f"{'='*60}")
    
    try:
        # Select multiplexer channel
        channel_mask = 1 << mux_channel
        bus.write_byte(mux_addr, channel_mask)
        time.sleep(0.05)
        
        print(f"✅ Multiplexer channel {mux_channel} selected")
        
        # Try to communicate with ESP
        try:
            # Send dummy data
            test_data = [0] * 12
            bus.write_i2c_block_data(esp_addr, 0x00, test_data)
            print(f"✅ Write successful to {esp_name}")
            
            time.sleep(0.02)
            
            # Try to read
            response = bus.read_i2c_block_data(esp_addr, 0x00, 20)
            print(f"✅ Read successful from {esp_name}")
            print(f"   Response (first 10 bytes): {response[:10]}")
            return True
            
        except Exception as e:
            print(f"❌ ESP {esp_name} NOT responding: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if device is visible at all
            print(f"\n   Checking if device visible on bus...")
            try:
                bus.read_byte(esp_addr)
                print(f"   ✅ Device 0x{esp_addr:02X} is visible (might be ESP not initialized)")
            except Exception as e2:
                print(f"   ❌ Device 0x{esp_addr:02X} NOT visible: {e2}")
            
            return False
    
    except Exception as e:
        print(f"❌ Failed to select multiplexer channel: {e}")
        return False
    
    finally:
        # Disable multiplexer channels
        try:
            bus.write_byte(mux_addr, 0x00)
        except:
            pass


def main():
    print("\n" + "="*60)
    print("I2C Hardware Diagnostic Tool")
    print("PLTN Simulator - 2 ESP Architecture")
    print("="*60)
    
    # Step 1: Scan main bus
    bus, main_devices = scan_i2c_bus(1)
    if bus is None:
        print("\n❌ Cannot proceed without I2C bus access")
        return 1
    
    # Check for multiplexers
    has_mux1 = 0x70 in main_devices
    has_mux2 = 0x71 in main_devices
    
    print(f"\n{'='*60}")
    print("Multiplexer Detection")
    print(f"{'='*60}")
    print(f"  TCA9548A #1 (0x70): {'✅ Found' if has_mux1 else '❌ NOT FOUND'}")
    print(f"  TCA9548A #2 (0x71): {'✅ Found' if has_mux2 else '❌ NOT FOUND'}")
    
    if not has_mux1 or not has_mux2:
        print("\n❌ CRITICAL: One or both multiplexers not found!")
        print("   Check:")
        print("   1. TCA9548A wiring (VCC, GND, SDA, SCL)")
        print("   2. Pull-up resistors on SDA/SCL (4.7kΩ)")
        print("   3. Address jumpers (A0, A1, A2)")
        print("      - MUX #1: A0=GND, A1=GND, A2=GND (0x70)")
        print("      - MUX #2: A0=VCC, A1=GND, A2=GND (0x71)")
        return 1
    
    # Step 2: Test multiplexer channels
    if has_mux1:
        test_multiplexer(bus, 0x70, "TCA9548A #1")
    
    if has_mux2:
        test_multiplexer(bus, 0x71, "TCA9548A #2")
    
    # Step 3: Test ESP communication
    print(f"\n{'='*60}")
    print("ESP Communication Tests")
    print(f"{'='*60}")
    
    esp_bc_ok = test_esp_direct(bus, 0x08, "ESP-BC", 0x70, 0)
    esp_e_ok = test_esp_direct(bus, 0x0A, "ESP-E", 0x71, 0)
    
    # Summary
    print(f"\n{'='*60}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    print(f"  Main I2C Bus:        {'✅ OK' if main_devices else '❌ FAIL'}")
    print(f"  TCA9548A #1 (0x70):  {'✅ OK' if has_mux1 else '❌ FAIL'}")
    print(f"  TCA9548A #2 (0x71):  {'✅ OK' if has_mux2 else '❌ FAIL'}")
    print(f"  ESP-BC (0x08):       {'✅ OK' if esp_bc_ok else '❌ FAIL'}")
    print(f"  ESP-E (0x0A):        {'✅ OK' if esp_e_ok else '❌ FAIL'}")
    
    if not esp_bc_ok or not esp_e_ok:
        print(f"\n{'='*60}")
        print("TROUBLESHOOTING TIPS")
        print(f"{'='*60}")
        
        if not esp_bc_ok:
            print("\n❌ ESP-BC (0x08) not responding:")
            print("   1. Check ESP32 is powered on")
            print("   2. Upload esp_utama.ino to ESP32")
            print("   3. Check Serial Monitor for 'I2C Ready at address 0x08'")
            print("   4. Verify wiring:")
            print("      - ESP32 Pin 21 (SDA) → TCA9548A #1, SD0")
            print("      - ESP32 Pin 22 (SCL) → TCA9548A #1, SC0")
            print("      - ESP32 GND → Common GND")
            print("   5. Check I2C slave address in code: Wire.begin(0x08)")
        
        if not esp_e_ok:
            print("\n❌ ESP-E (0x0A) not responding:")
            print("   1. Check ESP32 is powered on")
            print("   2. Upload esp_visualizer.ino to ESP32")
            print("   3. Check Serial Monitor for 'I2C Ready at address 0x0A'")
            print("   4. Verify wiring:")
            print("      - ESP32 Pin 21 (SDA) → TCA9548A #2, SD0")
            print("      - ESP32 Pin 22 (SCL) → TCA9548A #2, SC0")
            print("      - ESP32 GND → Common GND")
            print("   5. Check I2C slave address in code: Wire.begin(0x0A)")
    
    bus.close()
    return 0 if (esp_bc_ok and esp_e_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
