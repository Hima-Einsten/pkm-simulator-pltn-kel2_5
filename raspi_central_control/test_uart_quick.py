#!/usr/bin/env python3
"""
UART Connection Test - Quick Diagnostic Tool
Tests connection to ESP-BC and ESP-E via UART

Usage:
    python3 test_uart_quick.py
"""

import serial
import json
import time
import sys

def test_uart_device(port_name, device_name):
    """Quick test for a single UART device"""
    print(f"\n{'='*60}")
    print(f"Testing {device_name}")
    print(f"Port: {port_name}")
    print(f"{'='*60}")
    
    # Step 1: Check if port exists
    print(f"[1/4] Checking if {port_name} exists...")
    try:
        import os
        if not os.path.exists(port_name):
            print(f"  ❌ FAIL: {port_name} not found")
            print(f"  💡 Tip: Run 'ls -l /dev/ttyAMA*' to see available ports")
            return False
        print(f"  ✅ OK: Port exists")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False
    
    # Step 2: Try to open serial port
    print(f"\n[2/4] Opening serial port...")
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0
        )
        print(f"  ✅ OK: Port opened successfully")
    except serial.SerialException as e:
        print(f"  ❌ FAIL: Cannot open port")
        print(f"  Error: {e}")
        print(f"  💡 Tip: Check permissions with 'groups | grep dialout'")
        print(f"         If not in group: sudo usermod -a -G dialout $USER")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False
    
    # Step 3: Clear buffers and send ping
    print(f"\n[3/4] Sending ping command...")
    try:
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send ping
        command = {"cmd": "ping"}
        command_str = json.dumps(command) + '\n'
        ser.write(command_str.encode('utf-8'))
        ser.flush()
        print(f"  TX: {command}")
        
        # Wait for response
        time.sleep(0.2)
        
        if ser.in_waiting > 0:
            response = ser.readline()
            response_str = response.decode('utf-8').strip()
            print(f"  RX: {response_str}")
            
            try:
                data = json.loads(response_str)
                if data.get("status") == "ok":
                    print(f"  ✅ OK: ESP responded with 'pong'")
                    device = data.get("device", "Unknown")
                    print(f"  Device: {device}")
                else:
                    print(f"  ⚠️  WARNING: Unexpected response")
                    print(f"  Response: {data}")
            except json.JSONDecodeError:
                print(f"  ❌ FAIL: Invalid JSON response")
                print(f"  Raw: {response_str}")
                ser.close()
                return False
        else:
            print(f"  ❌ FAIL: No response from ESP (timeout)")
            print(f"  💡 Tip: Check wiring:")
            print(f"         - RX ↔ TX must be crossed")
            print(f"         - Common GND required")
            print(f"         - ESP firmware uploaded?")
            ser.close()
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        ser.close()
        return False
    
    # Step 4: Send update command
    print(f"\n[4/4] Sending update command...")
    try:
        if "ESP-BC" in device_name:
            command = {
                "cmd": "update",
                "rods": [25, 30, 35],
                "humid_sg": [1, 0],
                "humid_ct": [1, 0, 1, 0]
            }
        else:
            command = {
                "cmd": "update",
                "flows": [
                    {"pressure": 100.0, "pump": 2},
                    {"pressure": 35.0, "pump": 2},
                    {"pressure": 10.0, "pump": 2}
                ],
                "thermal_kw": 25000.0
            }
        
        command_str = json.dumps(command) + '\n'
        ser.write(command_str.encode('utf-8'))
        ser.flush()
        print(f"  TX: {json.dumps(command, indent=2)}")
        
        time.sleep(0.2)
        
        if ser.in_waiting > 0:
            response = ser.readline()
            response_str = response.decode('utf-8').strip()
            print(f"  RX: {response_str}")
            
            data = json.loads(response_str)
            if data.get("status") == "ok":
                print(f"  ✅ OK: Update command accepted")
            else:
                print(f"  ⚠️  WARNING: Update may have failed")
        else:
            print(f"  ⚠️  WARNING: No response to update (might be OK)")
            
    except Exception as e:
        print(f"  ⚠️  ERROR: {e}")
    
    # Close
    ser.close()
    print(f"\n{'='*60}")
    print(f"✅ {device_name} TEST PASSED")
    print(f"{'='*60}")
    return True


def check_system():
    """Check system configuration"""
    print("\n" + "="*60)
    print("SYSTEM CHECK")
    print("="*60)
    
    # Check if running on Raspberry Pi
    try:
        import platform
        if 'linux' not in platform.system().lower():
            print("⚠️  WARNING: Not running on Linux")
            print("   This tool is designed for Raspberry Pi")
    except:
        pass
    
    # Check available UART devices
    print("\n[1] Checking available UART devices...")
    import os
    uart_devices = []
    for device in ['/dev/ttyAMA0', '/dev/ttyAMA1', '/dev/ttyAMA2']:
        if os.path.exists(device):
            uart_devices.append(device)
            print(f"  ✅ Found: {device}")
        else:
            print(f"  ❌ Not found: {device}")
    
    if not uart_devices:
        print("\n  ❌ CRITICAL: No UART devices found!")
        print("  💡 Tip: Enable UART in /boot/config.txt:")
        print("          enable_uart=1")
        print("          dtoverlay=uart2")
        return False
    
    # Check permissions
    print("\n[2] Checking permissions...")
    import subprocess
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout
        if 'dialout' in groups:
            print("  ✅ User in 'dialout' group")
        else:
            print("  ❌ User NOT in 'dialout' group")
            print("  💡 Tip: sudo usermod -a -G dialout $USER")
            print("          Then logout and login again")
    except:
        print("  ⚠️  Cannot check groups")
    
    # Check pyserial
    print("\n[3] Checking pyserial module...")
    try:
        import serial
        print(f"  ✅ pyserial installed (version {serial.__version__})")
    except ImportError:
        print("  ❌ pyserial NOT installed")
        print("  💡 Tip: pip3 install pyserial")
        return False
    
    print("\n" + "="*60)
    return True


def detect_uart_pins():
    """Try to detect which GPIO pins are used for UART"""
    print("\n" + "="*60)
    print("UART PIN DETECTION")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(['dmesg', '|', 'grep', 'ttyAMA'], 
                              shell=True, capture_output=True, text=True)
        output = result.stdout
        
        if 'ttyAMA0' in output:
            print("\n/dev/ttyAMA0 detected:")
            if 'fe201000' in output:
                print("  📍 GPIO 14/15 (Pin 8/10)")
            print(f"  {output}")
        
        if 'ttyAMA2' in output:
            print("\n/dev/ttyAMA2 detected:")
            if 'fe201400' in output:
                print("  📍 GPIO 0/1 (Pin 27/28) - UART2")
            elif 'fe201600' in output:
                print("  📍 GPIO 4/5 (Pin 7/29) - UART3")
            elif 'fe201800' in output:
                print("  📍 GPIO 8/9 (Pin 24/21) - UART4")
            print(f"  {output}")
    except:
        print("  ⚠️  Cannot detect pin mapping")
    
    print("="*60)


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("UART CONNECTION TEST")
    print("PKM PLTN Simulator - ESP Communication Test")
    print("="*60)
    print("\nThis will test UART communication with ESP32 devices.")
    print("Make sure:")
    print("  1. ESP firmware uploaded (esp_utama_uart.ino, esp_visualizer_uart.ino)")
    print("  2. UART wiring correct (RX↔TX crossed, common GND)")
    print("  3. /boot/config.txt has: enable_uart=1, dtoverlay=uart2")
    print("  4. User in dialout group")
    
    # System check
    if not check_system():
        print("\n❌ System check failed. Please fix issues above.")
        return 1
    
    # Detect pins
    detect_uart_pins()
    
    input("\nPress ENTER to start testing...")
    
    # Test configuration
    configs = [
        {
            'port': '/dev/ttyAMA0',
            'name': 'ESP-BC (Control Rods + Turbine + Humidifier)',
            'expected_pins': 'GPIO 14/15 (Pin 8/10)'
        },
        {
            'port': '/dev/ttyUSB0',
            'name': 'ESP-E (LED Visualizer)',
            'expected_pins': 'USB Serial Adapter'
        }
    ]
    
    results = {}
    
    # Test each device
    for config in configs:
        port = config['port']
        name = config['name']
        pins = config['expected_pins']
        
        print(f"\n\n📍 Expected wiring: {pins}")
        result = test_uart_device(port, name)
        results[name] = result
        
        if not result:
            print(f"\n⚠️  Skipping remaining tests for {name}")
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour UART connections are working correctly.")
        print("You can now run the main program:")
        print("  python3 raspi_main_panel.py")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nTroubleshooting steps:")
        print("1. Check wiring (RX↔TX must be crossed)")
        print("2. Check ESP Serial Monitor shows 'UART Ready'")
        print("3. Check /boot/config.txt has correct dtoverlay")
        print("4. Verify pins with: dmesg | grep ttyAMA")
        print("5. Check permissions: groups | grep dialout")
        print("\nFor detailed wiring guide, see:")
        print("  UART_WIRING_GUIDE.md")
        print("  GPIO_UART_CONFLICT_ANALYSIS.md")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
