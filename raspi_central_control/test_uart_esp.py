#!/usr/bin/env python3
"""
UART ESP Communication Test
Test UART communication with ESP-BC and ESP-E

Usage:
    python3 test_uart_esp.py
"""

import serial
import json
import time
import sys

def test_esp_device(port, device_name):
    """Test communication with a single ESP device"""
    print(f"\n{'='*70}")
    print(f"Testing {device_name} on {port}")
    print(f"{'='*70}")
    
    try:
        # Open serial port
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0
        )
        
        print(f"✅ Serial port opened: {port}")
        
        # Wait for ESP to be ready
        time.sleep(0.5)
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Test 1: Ping
        print("\n[Test 1] Ping...")
        command = {"cmd": "ping"}
        ser.write((json.dumps(command) + '\n').encode('utf-8'))
        ser.flush()
        print(f"  TX: {json.dumps(command)}")
        
        response = ser.readline()
        if response:
            response_str = response.decode('utf-8').strip()
            print(f"  RX: {response_str}")
            data = json.loads(response_str)
            if data.get("status") == "ok":
                print(f"  ✅ Ping successful: {data.get('message')}")
            else:
                print(f"  ❌ Unexpected response: {data}")
        else:
            print(f"  ❌ No response (timeout)")
            ser.close()
            return False
        
        # Test 2: Update command
        print("\n[Test 2] Update command...")
        
        if "ESP-BC" in device_name:
            # ESP-BC update
            command = {
                "cmd": "update",
                "rods": [50, 60, 70],
                "humid_sg": [1, 1],
                "humid_ct": [1, 0, 1, 0]
            }
        else:
            # ESP-E update
            command = {
                "cmd": "update",
                "flows": [
                    {"pressure": 155.0, "pump": 2},
                    {"pressure": 50.0, "pump": 2},
                    {"pressure": 15.0, "pump": 2}
                ],
                "thermal_kw": 50000.0
            }
        
        ser.write((json.dumps(command) + '\n').encode('utf-8'))
        ser.flush()
        print(f"  TX: {json.dumps(command)}")
        
        response = ser.readline()
        if response:
            response_str = response.decode('utf-8').strip()
            print(f"  RX: {response_str}")
            data = json.loads(response_str)
            if data.get("status") == "ok":
                print(f"  ✅ Update successful")
                if "rods" in data:
                    print(f"     Rod positions: {data['rods']}")
                    print(f"     Thermal power: {data.get('thermal_kw', 0)} kW")
                if "anim_speed" in data:
                    print(f"     Animation speed: {data['anim_speed']}")
                    print(f"     LED count: {data.get('led_count', 0)}")
            else:
                print(f"  ❌ Update failed: {data}")
        else:
            print(f"  ❌ No response (timeout)")
            ser.close()
            return False
        
        # Test 3: Rapid updates (10 times)
        print("\n[Test 3] Rapid updates (10x)...")
        success_count = 0
        for i in range(10):
            if "ESP-BC" in device_name:
                command = {
                    "cmd": "update",
                    "rods": [i*10, i*10, i*10],
                    "humid_sg": [1, 1],
                    "humid_ct": [1, 0, 1, 0]
                }
            else:
                command = {
                    "cmd": "update",
                    "flows": [
                        {"pressure": i*15.0, "pump": 2},
                        {"pressure": i*5.0, "pump": 2},
                        {"pressure": i*1.5, "pump": 2}
                    ],
                    "thermal_kw": i*5000.0
                }
            
            ser.write((json.dumps(command) + '\n').encode('utf-8'))
            ser.flush()
            
            response = ser.readline()
            if response:
                data = json.loads(response.decode('utf-8').strip())
                if data.get("status") == "ok":
                    success_count += 1
            
            time.sleep(0.05)  # 50ms between commands
        
        print(f"  ✅ Success rate: {success_count}/10")
        
        # Close
        ser.close()
        print(f"\n✅ {device_name} test PASSED")
        return True
        
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("UART ESP Communication Test")
    print("="*70)
    print("\nThis script will test UART communication with:")
    print("  1. ESP-BC on /dev/ttyAMA0 (GPIO 14/15)")
    print("  2. ESP-E on /dev/ttyAMA1 (GPIO 0/1)")
    print("\nMake sure:")
    print("  - ESPs are powered on")
    print("  - UART firmware uploaded (esp_utama_uart.ino, esp_visualizer_uart.ino)")
    print("  - UART wiring correct")
    print("  - /boot/config.txt has: dtoverlay=uart2")
    print("="*70)
    
    input("\nPress ENTER to start testing...")
    
    # Test ESP-BC
    esp_bc_ok = test_esp_device('/dev/ttyAMA0', 'ESP-BC')
    
    # Test ESP-E
    esp_e_ok = test_esp_device('/dev/ttyAMA1', 'ESP-E')
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"  ESP-BC: {'✅ PASS' if esp_bc_ok else '❌ FAIL'}")
    print(f"  ESP-E:  {'✅ PASS' if esp_e_ok else '❌ FAIL'}")
    print("="*70)
    
    if esp_bc_ok and esp_e_ok:
        print("\n✅ ALL TESTS PASSED")
        print("   You can now run: python3 raspi_main_panel.py")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("   Check:")
        print("   1. ESP32 firmware uploaded correctly")
        print("   2. UART wiring (RX/TX crossed)")
        print("   3. ESP Serial Monitor shows 'UART Ready'")
        print("   4. /dev/ttyAMA0 and /dev/ttyAMA1 exist")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled")
        sys.exit(1)
