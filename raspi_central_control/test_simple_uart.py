#!/usr/bin/env python3
"""
Simple UART Test - Test komunikasi UART paling basic
Untuk debugging koneksi ESP32
"""

import serial
import time

def test_simple(port):
    print(f"\n{'='*60}")
    print(f"SIMPLE UART TEST - {port}")
    print(f"{'='*60}\n")
    
    print("Upload firmware: esp_uart_test_simple.ino ke ESP32")
    print("Lalu jalankan test ini\n")
    
    input("Press ENTER to start...")
    
    try:
        print(f"\n[1] Opening {port}...")
        ser = serial.Serial(port, 115200, timeout=2)
        print("✅ Port opened\n")
        
        # Clear buffers
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        print("[2] Listening for ESP heartbeat (5 seconds)...")
        print("    ESP should send heartbeat every 5 seconds")
        print("    Press Ctrl+C to skip\n")
        
        # Listen for heartbeat
        timeout = time.time() + 10
        got_heartbeat = False
        
        try:
            while time.time() < timeout:
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8', errors='replace').strip()
                    print(f"    RX: {data}")
                    if 'alive' in data or 'ready' in data:
                        got_heartbeat = True
                        print("    ✅ ESP is transmitting!")
                        break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n    Skipped")
        
        if not got_heartbeat:
            print("\n    ❌ No data from ESP!")
            print("    Possible issues:")
            print("    1. ESP not powered")
            print("    2. Wrong wiring (check TX wire)")
            print("    3. ESP crashed (check USB Serial Monitor)")
            print("\n    Check ESP Serial Monitor (USB) for error messages\n")
        
        print("\n[3] Sending test command...")
        
        # Send test
        ser.reset_input_buffer()
        test_cmd = '{"cmd":"ping"}\n'
        print(f"    TX: {test_cmd.strip()}")
        ser.write(test_cmd.encode('utf-8'))
        ser.flush()
        
        # Wait for response
        print("    Waiting for response...")
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"    RX: {response}")
            
            if 'pong' in response or 'ok' in response:
                print("\n✅ SUCCESS! ESP responded correctly!")
                print("   Communication is working!")
            else:
                print(f"\n⚠️  Got response but unexpected: {response}")
        else:
            print("    ❌ No response!")
            print("\n    ESP can TX but not RX (or RX wire issue)")
            print("    Check:")
            print("    1. RX wire connected? (RasPi TX → ESP RX)")
            print("    2. Wiring crossed? (TX↔RX must be swapped)")
            print("    3. ESP Serial Monitor shows RX data?")
        
        print("\n[4] Testing echo...")
        ser.reset_input_buffer()
        echo_cmd = 'test echo message\n'
        print(f"    TX: {echo_cmd.strip()}")
        ser.write(echo_cmd.encode('utf-8'))
        ser.flush()
        
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"    RX: {response}")
        else:
            print("    ❌ No echo")
        
        ser.close()
        print("\n" + "="*60)
        
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SIMPLE UART TEST")
    print("="*60)
    print("\nTest basic UART communication")
    print("\nOptions:")
    print("  1. Test /dev/ttyAMA0 (ESP-BC)")
    print("  2. Test /dev/ttyUSB0 (ESP-E)")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == '1':
        test_simple('/dev/ttyAMA0')
    elif choice == '2':
        test_simple('/dev/ttyUSB0')
    else:
        print("Invalid choice")
