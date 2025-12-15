#!/usr/bin/env python3
"""
Debug UART - Troubleshooting tool for ESP UART communication
"""

import serial
import time
import sys

def test_loopback(port):
    """Test port dengan loopback (hubungkan TX ke RX)"""
    print(f"\n{'='*60}")
    print(f"LOOPBACK TEST - {port}")
    print(f"{'='*60}")
    print("Instruksi: Hubungkan TX ke RX dengan jumper wire")
    print("  GPIO 14 (Pin 8) → GPIO 15 (Pin 10)")
    input("Press ENTER setelah jumper terpasang...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"✅ Port opened")
        
        # Send test
        test_msg = "TEST123\n"
        print(f"Sending: {test_msg.strip()}")
        ser.write(test_msg.encode())
        time.sleep(0.1)
        
        # Read
        if ser.in_waiting > 0:
            received = ser.readline().decode().strip()
            print(f"Received: {received}")
            if received == "TEST123":
                print("✅ LOOPBACK OK - Port is working!")
            else:
                print(f"⚠️  Received different: {received}")
        else:
            print("❌ No data received")
            print("   Check: Jumper wire connected?")
        
        ser.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def check_esp_serial_monitor(port):
    """Monitor raw data dari ESP"""
    print(f"\n{'='*60}")
    print(f"RAW SERIAL MONITOR - {port}")
    print(f"{'='*60}")
    print("Monitoring raw data from ESP...")
    print("Press Ctrl+C to stop\n")
    
    try:
        ser = serial.Serial(port, 115200, timeout=0.5)
        print(f"✅ Listening on {port}")
        print("="*60)
        
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                try:
                    text = data.decode('utf-8', errors='replace')
                    print(text, end='')
                except:
                    print(f"[Binary: {data.hex()}]")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopped")
        ser.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def send_manual_command(port):
    """Send manual command and see raw response"""
    print(f"\n{'='*60}")
    print(f"MANUAL COMMAND TEST - {port}")
    print(f"{'='*60}")
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        print(f"✅ Connected to {port}")
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.5)
        
        # Send ping
        command = '{"cmd":"ping"}\n'
        print(f"\nSending: {command.strip()}")
        ser.write(command.encode('utf-8'))
        ser.flush()
        print("✅ Sent")
        
        # Wait and read
        print("\nWaiting for response...")
        time.sleep(0.5)
        
        print(f"Bytes available: {ser.in_waiting}")
        
        if ser.in_waiting > 0:
            # Read all available
            data = ser.read(ser.in_waiting)
            print(f"\nRaw bytes: {data}")
            print(f"Hex: {data.hex()}")
            try:
                text = data.decode('utf-8')
                print(f"Text: {text}")
            except:
                print("Cannot decode as UTF-8")
        else:
            print("❌ No response received")
            print("\nPossible issues:")
            print("  1. ESP not running/crashed")
            print("  2. Wrong baudrate (check ESP: Serial2.begin(115200))")
            print("  3. Wrong wiring (RX/TX swapped)")
            print("  4. ESP firmware not uploaded")
            print("  5. ESP not connected to GPIO 16/17")
            print("\nCheck ESP Serial Monitor (USB):")
            print("  Should show: 'UART2 initialized'")
        
        ser.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def check_usb_device():
    """Check USB serial devices"""
    print(f"\n{'='*60}")
    print("USB SERIAL DEVICE CHECK")
    print(f"{'='*60}")
    
    import os
    import glob
    
    # Check ttyUSB*
    usb_devices = glob.glob('/dev/ttyUSB*')
    if usb_devices:
        print(f"✅ Found USB devices:")
        for dev in usb_devices:
            print(f"   {dev}")
            try:
                # Try to get info
                result = os.popen(f'udevadm info -q all -n {dev} | grep ID_MODEL').read()
                if result:
                    print(f"     {result.strip()}")
            except:
                pass
    else:
        print("❌ No /dev/ttyUSB* devices found")
        print("\nCheck:")
        print("  1. USB adapter connected?")
        print("  2. Run: lsusb")
        print("  3. Check dmesg: dmesg | grep ttyUSB")
    
    # Check ttyAMA*
    print(f"\nBuilt-in UART devices:")
    ama_devices = glob.glob('/dev/ttyAMA*')
    if ama_devices:
        for dev in ama_devices:
            print(f"   ✅ {dev}")
    else:
        print("   ❌ No /dev/ttyAMA* found")

def main():
    print("\n" + "="*60)
    print("UART DEBUG TOOL")
    print("="*60)
    
    print("\nSelect test:")
    print("  1. Check devices (ttyUSB/ttyAMA)")
    print("  2. Loopback test (ttyAMA0)")
    print("  3. Raw monitor ESP-BC (ttyAMA0)")
    print("  4. Raw monitor ESP-E (ttyUSB0)")
    print("  5. Manual command test (ttyAMA0)")
    print("  6. Manual command test (ttyUSB0)")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == '1':
        check_usb_device()
    elif choice == '2':
        test_loopback('/dev/ttyAMA0')
    elif choice == '3':
        check_esp_serial_monitor('/dev/ttyAMA0')
    elif choice == '4':
        check_usb_device()
        check_esp_serial_monitor('/dev/ttyUSB0')
    elif choice == '5':
        send_manual_command('/dev/ttyAMA0')
    elif choice == '6':
        check_usb_device()
        send_manual_command('/dev/ttyUSB0')
    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
