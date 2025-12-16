#!/usr/bin/env python3
"""
Quick UART Test - ESP-BC Communication
Simple test to verify UART is working properly
"""

import serial
import json
import time
import sys

def test_esp_bc():
    port = '/dev/ttyAMA0'
    baudrate = 115200
    
    print("="*70)
    print("Quick UART Test - ESP-BC")
    print("="*70)
    print(f"Port: {port}")
    print(f"Baudrate: {baudrate}")
    print()
    
    try:
        # Open serial
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2.0,
            write_timeout=1.0
        )
        
        print("✅ Serial port opened")
        
        # Wait and flush
        print("⏳ Waiting 1 second for ESP32...")
        time.sleep(1.0)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✅ Buffers flushed\n")
        
        # Test 1: Ping
        print("TEST 1: Ping Command")
        print("-" * 70)
        cmd = {"cmd": "ping"}
        json_str = json.dumps(cmd) + '\n'
        
        print(f"Sending: {json_str.strip()}")
        ser.write(json_str.encode('utf-8'))
        ser.flush()
        
        line = ser.readline()
        if line:
            response = line.decode('utf-8').strip()
            print(f"✅ Response: {response}\n")
        else:
            print("❌ No response (timeout)\n")
            return False
        
        # Small delay
        time.sleep(0.3)
        
        # Test 2: Update command
        print("TEST 2: Update Command (Raise control rods)")
        print("-" * 70)
        cmd = {
            "cmd": "update",
            "rods": [0, 60, 60],
            "humid_sg": [0, 0],
            "humid_ct": [0, 0, 0, 0]
        }
        json_str = json.dumps(cmd) + '\n'
        
        print(f"Sending: {json_str.strip()}")
        ser.write(json_str.encode('utf-8'))
        ser.flush()
        
        line = ser.readline()
        if line:
            response = line.decode('utf-8').strip()
            print(f"✅ Response received")
            
            try:
                data = json.loads(response)
                print("\n📊 Parsed Data:")
                print(f"   Status: {data.get('status')}")
                print(f"   Rods: {data.get('rods')}")
                print(f"   Thermal Power: {data.get('thermal_kw')} kW")
                print(f"   Turbine Speed: {data.get('turbine_speed')}%")
                print(f"   Turbine State: {data.get('state')} (0=IDLE, 1=STARTING, 2=RUNNING, 3=SHUTDOWN)")
                print(f"   Power Level: {data.get('power_level')}%")
                print(f"   Pump Speeds: {data.get('pump_speeds')}")
                print(f"   Humidifier Status: {data.get('humid_status')}")
                print()
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"   Raw response: {response}\n")
                return False
        else:
            print("❌ No response (timeout)\n")
            return False
        
        # Test 3: Another update
        time.sleep(0.5)
        
        print("TEST 3: Update Command (Higher rods + Humidifiers ON)")
        print("-" * 70)
        cmd = {
            "cmd": "update",
            "rods": [0, 80, 80],
            "humid_sg": [1, 1],
            "humid_ct": [1, 1, 1, 1]
        }
        json_str = json.dumps(cmd) + '\n'
        
        print(f"Sending: {json_str.strip()}")
        ser.write(json_str.encode('utf-8'))
        ser.flush()
        
        line = ser.readline()
        if line:
            response = line.decode('utf-8').strip()
            data = json.loads(response)
            
            print(f"✅ Response received")
            print("\n📊 Parsed Data:")
            print(f"   Rods: {data.get('rods')}")
            print(f"   Thermal Power: {data.get('thermal_kw')} kW")
            print(f"   Turbine Speed: {data.get('turbine_speed')}%")
            print(f"   Turbine State: {data.get('state')}")
            print(f"   Pump Speeds: {data.get('pump_speeds')}")
            print()
            
            # Check if turbine started
            state = data.get('state', 0)
            if state >= 1:
                print("🎉 Turbine is active! (State = STARTING or RUNNING)")
            else:
                print("ℹ️  Turbine still in IDLE state (need higher thermal power)")
            print()
        else:
            print("❌ No response (timeout)\n")
            return False
        
        # Close
        ser.close()
        print("="*70)
        print("✅ All tests passed!")
        print("="*70)
        return True
        
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if ESP32 is connected and powered")
        print("2. Check if UART is enabled: sudo raspi-config")
        print("3. Check permissions: ls -l /dev/ttyAMA0")
        print("4. Add to dialout group: sudo usermod -a -G dialout $USER")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_esp_bc()
    sys.exit(0 if success else 1)
