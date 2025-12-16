#!/usr/bin/env python3
"""
Test UART timing untuk ESP-BC
Mencoba berbagai timeout dan delay untuk menemukan setting optimal
"""

import serial
import json
import time

def test_uart_timing():
    port = '/dev/ttyAMA0'
    baudrate = 115200
    
    print("="*70)
    print("Testing UART Timing - ESP-BC")
    print("="*70)
    
    try:
        # Open serial port
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0,  # 2 second timeout
            write_timeout=1.0
        )
        
        print(f"✅ Opened {port} at {baudrate} baud")
        
        # Wait for ESP to be ready
        print("\n⏳ Waiting 2 seconds for ESP32 to initialize...")
        time.sleep(2.0)
        
        # Flush buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✅ Buffers flushed")
        
        # Test 1: Ping command
        print("\n" + "="*70)
        print("TEST 1: Ping Command")
        print("="*70)
        
        cmd = {"cmd": "ping"}
        json_str = json.dumps(cmd) + '\n'
        
        print(f"Sending: {json_str.strip()}")
        ser.write(json_str.encode('utf-8'))
        ser.flush()
        
        print("⏳ Waiting for response (timeout: 2s)...")
        line = ser.readline()
        
        if line:
            response = line.decode('utf-8').strip()
            print(f"✅ Response: {response}")
            data = json.loads(response)
            print(f"   Parsed: {data}")
        else:
            print("❌ No response (timeout)")
        
        # Test 2: Update command dengan delay lebih lama
        print("\n" + "="*70)
        print("TEST 2: Update Command (with longer delay)")
        print("="*70)
        
        time.sleep(0.5)  # Delay before next command
        
        cmd = {
            "cmd": "update",
            "rods": [0, 50, 50],
            "humid_sg": [0, 0],
            "humid_ct": [0, 0, 0, 0]
        }
        json_str = json.dumps(cmd) + '\n'
        
        print(f"Sending: {json_str.strip()}")
        ser.write(json_str.encode('utf-8'))
        ser.flush()
        
        print("⏳ Waiting for response (timeout: 2s)...")
        line = ser.readline()
        
        if line:
            response = line.decode('utf-8').strip()
            print(f"✅ Response: {response}")
            data = json.loads(response)
            
            # Parse important fields
            print("\n📊 Parsed Data:")
            print(f"   Status: {data.get('status')}")
            print(f"   Rods: {data.get('rods')}")
            print(f"   Thermal: {data.get('thermal_kw')} kW")
            print(f"   Turbine Speed: {data.get('turbine_speed')}%")
            print(f"   Pump Speeds: {data.get('pump_speeds')}")
            print(f"   State: {data.get('state')} (0=IDLE, 1=STARTING, 2=RUNNING, 3=SHUTDOWN)")
        else:
            print("❌ No response (timeout)")
        
        # Test 3: Multiple rapid commands
        print("\n" + "="*70)
        print("TEST 3: Multiple Rapid Commands")
        print("="*70)
        
        for i in range(3):
            time.sleep(0.3)  # Small delay between commands
            
            cmd = {
                "cmd": "update",
                "rods": [0, 30 + i*10, 30 + i*10],
                "humid_sg": [0, 0],
                "humid_ct": [0, 0, 0, 0]
            }
            json_str = json.dumps(cmd) + '\n'
            
            print(f"\nCommand {i+1}: Rods=[0, {30+i*10}, {30+i*10}]")
            ser.write(json_str.encode('utf-8'))
            ser.flush()
            
            line = ser.readline()
            if line:
                data = json.loads(line.decode('utf-8').strip())
                print(f"   ✅ Rods: {data.get('rods')}, Thermal: {data.get('thermal_kw'):.1f} kW")
            else:
                print(f"   ❌ No response")
        
        # Test 4: Buffer timing
        print("\n" + "="*70)
        print("TEST 4: Check for buffered data")
        print("="*70)
        
        print("⏳ Waiting 1 second to see if more data arrives...")
        time.sleep(1.0)
        
        if ser.in_waiting > 0:
            print(f"⚠️  Found {ser.in_waiting} bytes in buffer!")
            leftover = ser.read(ser.in_waiting)
            print(f"   Data: {leftover.decode('utf-8', errors='ignore')}")
        else:
            print("✅ No buffered data (good!)")
        
        # Close
        ser.close()
        print("\n" + "="*70)
        print("✅ Test Complete")
        print("="*70)
        
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_uart_timing()
