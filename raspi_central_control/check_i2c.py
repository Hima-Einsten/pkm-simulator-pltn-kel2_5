#!/usr/bin/env python3
"""
I2C Bus Checker and Troubleshooter
Checks available I2C buses and provides fix suggestions
"""

import os
import sys
import subprocess

def check_i2c_devices():
    """Check which I2C devices are available"""
    print("=" * 60)
    print("  I2C Bus Checker")
    print("=" * 60)
    print()
    
    # Check for /dev/i2c-* devices
    i2c_devices = []
    for i in range(10):  # Check i2c-0 through i2c-9
        dev_path = f"/dev/i2c-{i}"
        if os.path.exists(dev_path):
            i2c_devices.append(i)
            print(f"✅ Found: {dev_path}")
        else:
            print(f"❌ Not found: {dev_path}")
    
    print()
    
    if not i2c_devices:
        print("⚠️  NO I2C DEVICES FOUND!")
        print()
        print_enable_instructions()
        return False
    
    print(f"✅ Available I2C buses: {i2c_devices}")
    print()
    
    # Try to scan the available buses
    for bus_num in i2c_devices:
        print(f"📡 Scanning I2C bus {bus_num}...")
        try:
            result = subprocess.run(
                ['i2cdetect', '-y', str(bus_num)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"   ⚠️  Error scanning bus {bus_num}")
        except FileNotFoundError:
            print("   ⚠️  i2cdetect not found. Install with: sudo apt-get install i2c-tools")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    
    return True

def print_enable_instructions():
    """Print instructions to enable I2C"""
    print("=" * 60)
    print("  How to Enable I2C on Raspberry Pi")
    print("=" * 60)
    print()
    print("Option 1: Using raspi-config (Recommended)")
    print("-" * 60)
    print("1. Run: sudo raspi-config")
    print("2. Select: 3 Interface Options")
    print("3. Select: I5 I2C")
    print("4. Select: Yes")
    print("5. Select: Ok")
    print("6. Select: Finish")
    print("7. Reboot: sudo reboot")
    print()
    
    print("Option 2: Manual Enable")
    print("-" * 60)
    print("1. Edit config file:")
    print("   sudo nano /boot/config.txt")
    print()
    print("2. Add or uncomment these lines:")
    print("   dtparam=i2c_arm=on")
    print("   dtparam=i2c1=on")
    print()
    print("3. Save and reboot:")
    print("   sudo reboot")
    print()
    
    print("Option 3: Load I2C modules")
    print("-" * 60)
    print("sudo modprobe i2c-dev")
    print("sudo modprobe i2c-bcm2835")
    print()
    
    print("After enabling, check with:")
    print("  ls -l /dev/i2c-*")
    print()

def check_i2c_permissions():
    """Check if current user has I2C permissions"""
    print("=" * 60)
    print("  Checking I2C Permissions")
    print("=" * 60)
    print()
    
    # Check if user is in i2c group
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout
        
        if 'i2c' in groups:
            print("✅ User is in 'i2c' group")
        else:
            print("❌ User is NOT in 'i2c' group")
            print()
            print("To fix, run:")
            print("  sudo usermod -a -G i2c $USER")
            print("  sudo reboot")
    except Exception as e:
        print(f"⚠️  Could not check groups: {e}")
    
    print()

def check_python_packages():
    """Check if required Python packages are installed"""
    print("=" * 60)
    print("  Checking Python Packages")
    print("=" * 60)
    print()
    
    packages = ['smbus2', 'RPi.GPIO']
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} NOT installed")
            print(f"   Install with: pip3 install {package}")
    
    print()

def test_i2c_communication(bus_num=1):
    """Test basic I2C communication"""
    print("=" * 60)
    print(f"  Testing I2C Communication on bus {bus_num}")
    print("=" * 60)
    print()
    
    try:
        import smbus2
        
        bus = smbus2.SMBus(bus_num)
        print(f"✅ Successfully opened I2C bus {bus_num}")
        
        # Try to scan for common addresses
        print()
        print("Scanning common I2C addresses...")
        found_devices = []
        
        common_addresses = [
            (0x70, "TCA9548A Multiplexer"),
            (0x71, "TCA9548A Multiplexer"),
            (0x3C, "OLED Display"),
            (0x08, "ESP-B"),
            (0x09, "ESP-C"),
            (0x0A, "ESP-E")
        ]
        
        for addr, name in common_addresses:
            try:
                bus.read_byte(addr)
                print(f"  ✅ 0x{addr:02X} - {name}")
                found_devices.append((addr, name))
            except:
                print(f"  ❌ 0x{addr:02X} - {name} (not found)")
        
        bus.close()
        
        print()
        if found_devices:
            print(f"✅ Found {len(found_devices)} device(s)")
        else:
            print("⚠️  No devices found. Check wiring!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to open I2C bus {bus_num}")
        print(f"   Error: {e}")
        return False

def print_config_fix():
    """Print configuration fix for raspi_config.py"""
    print("=" * 60)
    print("  Configuration Fix")
    print("=" * 60)
    print()
    print("Update your raspi_config.py:")
    print()
    print("# OLD (incorrect for most Raspberry Pi):")
    print("I2C_BUS_DISPLAY = 0")
    print("I2C_BUS_ESP = 1")
    print()
    print("# NEW (correct):")
    print("I2C_BUS = 1")
    print("I2C_BUS_DISPLAY = 1")
    print("I2C_BUS_ESP = 1")
    print()
    print("Both multiplexers should be on the same bus (bus 1).")
    print("They are differentiated by their I2C addresses:")
    print("  - 0x70 for display multiplexer")
    print("  - 0x71 for ESP multiplexer")
    print()

def main():
    """Main check function"""
    print()
    print("🔍 PLTN Simulator I2C Checker")
    print()
    
    # Check 1: I2C devices
    devices_ok = check_i2c_devices()
    
    if not devices_ok:
        print()
        print("❌ I2C is not enabled!")
        print("   Follow the instructions above to enable it.")
        return
    
    # Check 2: Permissions
    check_i2c_permissions()
    
    # Check 3: Python packages
    check_python_packages()
    
    # Check 4: Test communication
    test_i2c_communication(1)
    
    # Show config fix
    print()
    print_config_fix()
    
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print()
    print("If you see errors above:")
    print("1. Enable I2C (see instructions)")
    print("2. Add user to i2c group")
    print("3. Install required packages")
    print("4. Update raspi_config.py")
    print("5. Reboot and try again")
    print()
    print("After fixing, run:")
    print("  python3 raspi_main.py")
    print()

if __name__ == "__main__":
    main()
