#!/usr/bin/env python3
"""
LED Visualizer Debugging Script
Helps diagnose why LEDs are not lighting up
"""

import serial
import json
import time
import sys

def test_esp_e_uart(port='/dev/ttyAMA3', baudrate=115200):
    """Test ESP-E UART communication"""
    print("="*70)
    print("ESP-E UART Debugging Tool")
    print("="*70)
    
    try:
        # Open serial connection
        print(f"\n[1] Opening {port} at {baudrate} baud...")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0
        )
        
        print("✅ Serial port opened successfully")
        
        # Wait for ESP32 to stabilize
        print("\n[2] Waiting 2 seconds for ESP32 to stabilize...")
        time.sleep(2.0)
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Test 1: Ping
        print("\n[3] Sending PING to ESP-E...")
        ping_cmd = {"cmd": "ping"}
        ser.write((json.dumps(ping_cmd) + '\n').encode('utf-8'))
        ser.flush()
        print(f"TX: {json.dumps(ping_cmd)}")
        
        # Wait for response
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"RX: {response}")
            
            try:
                resp_data = json.loads(response)
                if resp_data.get("status") == "ok" and resp_data.get("message") == "pong":
                    print("✅ ESP-E responded to PING - Communication OK!")
                else:
                    print("⚠️  ESP-E responded but not with expected pong")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response from ESP-E")
        else:
            print("❌ No response from ESP-E - Check UART connection!")
            print("   - Verify GPIO 4 (Raspi TX) → GPIO 5 (ESP-E RX)")
            print("   - Verify GPIO 5 (Raspi RX) → GPIO 4 (ESP-E TX)")
            print("   - Verify GND connection")
            return False
        
        # Test 2: Send test data to light up LEDs
        print("\n[4] Sending test data to ESP-E...")
        print("   This should light up all 3 flow LEDs and power LED")
        
        test_cmd = {
            "cmd": "update",
            "flows": [
                {"pressure": 150.0, "pump": 2},  # Primary ON
                {"pressure": 52.5, "pump": 2},   # Secondary ON
                {"pressure": 15.0, "pump": 2}    # Tertiary ON
            ],
            "thermal_kw": 150000.0  # 150 MW (50% of max)
        }
        
        ser.write((json.dumps(test_cmd) + '\n').encode('utf-8'))
        ser.flush()
        print(f"TX: {json.dumps(test_cmd)}")
        
        # Wait for response
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"RX: {response}")
            
            try:
                resp_data = json.loads(response)
                if resp_data.get("status") == "ok":
                    print("✅ ESP-E accepted update command")
                    print("\n🔍 CHECK NOW:")
                    print("   - Flow 1 LEDs (GPIO 32,33,25,26) should be animating")
                    print("   - Flow 2 LEDs (GPIO 27,14,12,13) should be animating")
                    print("   - Flow 3 LEDs (GPIO 15,2,4,5) should be animating")
                    print("   - Power LED (GPIO 23) should be at ~50% brightness")
                    print("\n   If LEDs are NOT lighting up:")
                    print("   → Check LED connections to ESP32 pins")
                    print("   → Check ESP32 power supply (needs 5V, sufficient current)")
                    print("   → Use multimeter to check pin voltage (should be ~3.3V when HIGH)")
                else:
                    print("⚠️  ESP-E responded with error")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response from ESP-E")
        else:
            print("⚠️  No response from ESP-E after update command")
        
        # Test 3: Turn off all LEDs
        print("\n[5] Sending OFF command to ESP-E...")
        off_cmd = {
            "cmd": "update",
            "flows": [
                {"pressure": 0.0, "pump": 0},  # Primary OFF
                {"pressure": 0.0, "pump": 0},  # Secondary OFF
                {"pressure": 0.0, "pump": 0}   # Tertiary OFF
            ],
            "thermal_kw": 0.0
        }
        
        ser.write((json.dumps(off_cmd) + '\n').encode('utf-8'))
        ser.flush()
        print(f"TX: {json.dumps(off_cmd)}")
        
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"RX: {response}")
            print("✅ All LEDs should now be OFF")
        
        # Close
        ser.close()
        print("\n" + "="*70)
        print("✅ Test complete")
        print("="*70)
        return True
        
    except serial.SerialException as e:
        print(f"❌ Serial port error: {e}")
        print("\nPossible causes:")
        print("  - Port not available (check with 'ls /dev/ttyAMA*')")
        print("  - Permission denied (run with sudo)")
        print("  - Port already in use (stop pkm-simulator service)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_raspi_logs():
    """Check Raspberry Pi logs for ESP communication"""
    print("\n" + "="*70)
    print("Checking Raspberry Pi Logs")
    print("="*70)
    print("\nRun this command to see live logs:")
    print("  sudo journalctl -u pkm-simulator -f")
    print("\nLook for these indicators:")
    print("  ✅ '✅ ESP-E handshake successful (pong)' - ESP-E connected")
    print("  ✅ 'TX /dev/ttyAMA3: {\"cmd\":\"update\",...}' - Data being sent")
    print("  ✅ 'RX /dev/ttyAMA3: {\"status\":\"ok\",...}' - ESP-E responding")
    print("  ✅ 'Thermal=XXX.XkW' - Thermal power data available")
    print("  ⚠️  'ESP-E: No response' - Communication problem")
    print("  ⚠️  'Thermal=0.0kW' - No thermal power (rods not raised)")

def main():
    print("\nLED Visualizer Debugging Tool")
    print("Choose test mode:")
    print("  1. Test ESP-E UART communication (requires sudo)")
    print("  2. Show how to check Raspberry Pi logs")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n⚠️  Make sure to stop pkm-simulator service first:")
        print("  sudo systemctl stop pkm-simulator")
        input("\nPress Enter when ready...")
        test_esp_e_uart()
    elif choice == "2":
        check_raspi_logs()
    else:
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
