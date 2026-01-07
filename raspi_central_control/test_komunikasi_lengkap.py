#!/usr/bin/env python3
"""
Test Komunikasi Keseluruhan - PKM PLTN Simulator

Test lengkap untuk semua komunikasi:
- ESP-BC (Control Rods + Turbine + Pumps + Humidifiers)
- ESP-E (Power Indicator)
- UART protocol validation
- Performance test
- Error handling

Usage:
    python3 test_komunikasi_lengkap.py
"""

import serial
import json
import time
import sys
from datetime import datetime

# ============================================
# Configuration
# ============================================
ESP_BC_PORT = '/dev/ttyAMA0'  # GPIO 14/15 (UART0)
ESP_E_PORT = '/dev/ttyAMA3'   # GPIO 4/5 (UART3)
BAUDRATE = 115200
TIMEOUT = 2.0

# ============================================
# Colors for terminal output
# ============================================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER} {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

# ============================================
# Test Results Storage
# ============================================
class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_test(self, name, passed, message=""):
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def add_warning(self, name, message):
        self.tests.append({
            'name': name,
            'passed': None,
            'message': message,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        self.warnings += 1
    
    def print_summary(self):
        print_header("TEST SUMMARY")
        print(f"\nTotal tests: {self.passed + self.failed}")
        print_success(f"Passed: {self.passed}")
        if self.failed > 0:
            print_error(f"Failed: {self.failed}")
        if self.warnings > 0:
            print_warning(f"Warnings: {self.warnings}")
        
        print("\nDetailed Results:")
        for test in self.tests:
            time_str = test['time']
            if test['passed'] is True:
                print(f"  [{time_str}] {Colors.OKGREEN}✓{Colors.ENDC} {test['name']}")
            elif test['passed'] is False:
                print(f"  [{time_str}] {Colors.FAIL}✗{Colors.ENDC} {test['name']}")
                if test['message']:
                    print(f"            {Colors.FAIL}{test['message']}{Colors.ENDC}")
            else:
                print(f"  [{time_str}] {Colors.WARNING}⚠{Colors.ENDC} {test['name']}")
                if test['message']:
                    print(f"            {Colors.WARNING}{test['message']}{Colors.ENDC}")

results = TestResults()

# ============================================
# ESP-BC Tests
# ============================================
def test_esp_bc():
    print_header("ESP-BC Tests (Control Rods + Turbine + Humidifiers)")
    
    try:
        # Open port
        print("\n1. Opening serial port...")
        ser_bc = serial.Serial(
            port=ESP_BC_PORT,
            baudrate=BAUDRATE,
            timeout=TIMEOUT
        )
        print_success(f"Port {ESP_BC_PORT} opened")
        results.add_test("ESP-BC: Port Open", True)
        
        # Wait for ESP to stabilize
        print("\n2. Waiting for ESP32 to stabilize (1s)...")
        time.sleep(1.0)  # Reduced from 3s to 1s
        ser_bc.reset_input_buffer()
        ser_bc.reset_output_buffer()
        print_success("Buffers cleared")
        
        # Test 1: Ping
        print("\n3. Testing ping command...")
        ping_cmd = {'cmd': 'ping'}
        ser_bc.write((json.dumps(ping_cmd) + '\n').encode())
        ser_bc.flush()
        
        response = ser_bc.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok' and data.get('message') == 'pong':
                device = data.get('device', 'unknown')
                print_success(f"Ping successful! Device: {device}")
                results.add_test("ESP-BC: Ping", True)
            else:
                print_error(f"Unexpected ping response: {data}")
                results.add_test("ESP-BC: Ping", False, "Unexpected response")
                ser_bc.close()
                return None
        else:
            print_error("No ping response (timeout)")
            results.add_test("ESP-BC: Ping", False, "Timeout")
            ser_bc.close()
            return None
        
        time.sleep(0.5)
        
        # Test 2: Update rods
        print("\n4. Testing rod control...")
        update_cmd = {
            'cmd': 'update',
            'rods': [30, 40, 50],
            'pumps': [0, 0, 0],
            'humid_ct': [0, 0, 0, 0]
        }
        ser_bc.write((json.dumps(update_cmd) + '\n').encode())
        ser_bc.flush()
        
        response = ser_bc.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok':
                rods = data.get('rods', [0, 0, 0])
                thermal = data.get('thermal_kw', 0.0)
                print_success(f"Rod update successful!")
                print(f"   Rods: Safety={rods[0]}%, Shim={rods[1]}%, Reg={rods[2]}%")
                print(f"   Thermal: {thermal:.1f} kW")
                results.add_test("ESP-BC: Rod Control", True)
            else:
                print_error(f"Rod update failed: {data}")
                results.add_test("ESP-BC: Rod Control", False)
        else:
            print_error("No rod update response")
            results.add_test("ESP-BC: Rod Control", False, "Timeout")
        
        time.sleep(0.5)
        
        # Test 3: Pump control
        print("\n5. Testing pump control...")
        update_cmd = {
            'cmd': 'update',
            'rods': [50, 60, 70],
            'pumps': [2, 2, 2],  # All pumps ON
            'humid_ct': [0, 0, 0, 0]
        }
        ser_bc.write((json.dumps(update_cmd) + '\n').encode())
        ser_bc.flush()
        
        response = ser_bc.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok':
                pump_speeds = data.get('pump_speeds', [0, 0, 0])
                print_success(f"Pump control successful!")
                print(f"   Pump speeds: P1={pump_speeds[0]:.1f}%, P2={pump_speeds[1]:.1f}%, P3={pump_speeds[2]:.1f}%")
                results.add_test("ESP-BC: Pump Control", True)
            else:
                print_error(f"Pump control failed: {data}")
                results.add_test("ESP-BC: Pump Control", False)
        else:
            print_error("No pump response")
            results.add_test("ESP-BC: Pump Control", False, "Timeout")
        
        time.sleep(0.5)
        
        # Test 4: Humidifier control
        print("\n6. Testing humidifier control...")
        update_cmd = {
            'cmd': 'update',
            'rods': [60, 70, 80],
            'pumps': [2, 2, 2],
            'humid_ct': [1, 1, 1, 1]  # All humidifiers ON
        }
        ser_bc.write((json.dumps(update_cmd) + '\n').encode())
        ser_bc.flush()
        
        response = ser_bc.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok':
                humid_status = data.get('humid_status', [0, 0, 0, 0])
                print_success(f"Humidifier control successful!")
                print(f"   Humid status: CT1={humid_status[0]}, CT2={humid_status[1]}, CT3={humid_status[2]}, CT4={humid_status[3]}")
                results.add_test("ESP-BC: Humidifier Control", True)
            else:
                print_error(f"Humidifier control failed: {data}")
                results.add_test("ESP-BC: Humidifier Control", False)
        else:
            print_error("No humidifier response")
            results.add_test("ESP-BC: Humidifier Control", False, "Timeout")
        
        time.sleep(0.5)
        
        # Test 5: Turbine state
        print("\n7. Testing turbine state...")
        # High power should trigger turbine
        update_cmd = {
            'cmd': 'update',
            'rods': [80, 90, 90],
            'pumps': [2, 2, 2],
            'humid_ct': [1, 1, 1, 1]
        }
        ser_bc.write((json.dumps(update_cmd) + '\n').encode())
        ser_bc.flush()
        
        response = ser_bc.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok':
                state = data.get('state', 0)
                turbine_speed = data.get('turbine_speed', 0.0)
                state_names = {0: 'IDLE', 1: 'STARTING', 2: 'RUNNING', 3: 'SHUTDOWN'}
                print_success(f"Turbine state check successful!")
                print(f"   State: {state_names.get(state, 'UNKNOWN')}")
                print(f"   Speed: {turbine_speed:.1f}%")
                results.add_test("ESP-BC: Turbine State", True)
            else:
                print_error(f"Turbine state check failed: {data}")
                results.add_test("ESP-BC: Turbine State", False)
        else:
            print_error("No turbine response")
            results.add_test("ESP-BC: Turbine State", False, "Timeout")
        
        time.sleep(0.5)
        
        # Test 6: Response timing
        print("\n8. Testing response timing (10 rapid commands)...")
        times = []
        success_count = 0
        
        for i in range(10):
            start = time.time()
            
            cmd = {
                'cmd': 'update',
                'rods': [i*10, i*10, i*10],
                'pumps': [0, 0, 0],
                'humid_ct': [0, 0, 0, 0]
            }
            ser_bc.write((json.dumps(cmd) + '\n').encode())
            ser_bc.flush()
            
            response = ser_bc.readline()
            elapsed = (time.time() - start) * 1000
            
            if response:
                try:
                    data = json.loads(response.decode().strip())
                    if data.get('status') == 'ok':
                        times.append(elapsed)
                        success_count += 1
                except:
                    pass
            
            time.sleep(0.1)
        
        if times:
            avg = sum(times) / len(times)
            print_success(f"Rapid test: {success_count}/10 successful")
            print(f"   Average response time: {avg:.1f} ms")
            
            if avg < 50:
                print_info("Performance: EXCELLENT")
                results.add_test("ESP-BC: Response Timing", True, f"{avg:.1f}ms avg")
            elif avg < 100:
                print_info("Performance: GOOD")
                results.add_test("ESP-BC: Response Timing", True, f"{avg:.1f}ms avg")
            elif avg < 200:
                print_warning("Performance: ACCEPTABLE")
                results.add_warning("ESP-BC: Response Timing", f"{avg:.1f}ms (slow)")
            else:
                print_error("Performance: SLOW")
                results.add_test("ESP-BC: Response Timing", False, f"{avg:.1f}ms (too slow)")
        else:
            print_error("No successful rapid responses")
            results.add_test("ESP-BC: Response Timing", False, "All failed")
        
        return ser_bc
        
    except serial.SerialException as e:
        print_error(f"Serial port error: {e}")
        results.add_test("ESP-BC: Port Open", False, str(e))
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        results.add_test("ESP-BC: General", False, str(e))
        return None

# ============================================
# ESP-E Tests
# ============================================
def test_esp_e():
    print_header("ESP-E Tests (Power Indicator)")
    
    try:
        # Open port
        print("\n1. Opening serial port...")
        ser_e = serial.Serial(
            port=ESP_E_PORT,
            baudrate=BAUDRATE,
            timeout=TIMEOUT
        )
        print_success(f"Port {ESP_E_PORT} opened")
        results.add_test("ESP-E: Port Open", True)
        
        # Wait for ESP to stabilize
        print("\n2. Waiting for ESP32 to stabilize (1s)...")
        time.sleep(1.0)  # Reduced from 2s to 1s
        ser_e.reset_input_buffer()
        ser_e.reset_output_buffer()
        print_success("Buffers cleared")
        
        # Test 1: Ping
        print("\n3. Testing ping command...")
        ping_cmd = {'cmd': 'ping'}
        ser_e.write((json.dumps(ping_cmd) + '\n').encode())
        ser_e.flush()
        
        response = ser_e.readline()
        if response:
            data = json.loads(response.decode().strip())
            if data.get('status') == 'ok' and data.get('message') == 'pong':
                device = data.get('device', 'unknown')
                version = data.get('version', 'unknown')
                print_success(f"Ping successful! Device: {device}, Version: {version}")
                results.add_test("ESP-E: Ping", True)
            else:
                print_error(f"Unexpected ping response: {data}")
                results.add_test("ESP-E: Ping", False, "Unexpected response")
                ser_e.close()
                return None
        else:
            print_error("No ping response (timeout)")
            results.add_test("ESP-E: Ping", False, "Timeout")
            ser_e.close()
            return None
        
        time.sleep(0.5)
        
        # Test 2: Power levels
        print("\n4. Testing power indicator (various levels)...")
        test_powers = [
            (0, "OFF"),
            (75000, "25%"),
            (150000, "50%"),
            (225000, "75%"),
            (300000, "100%")
        ]
        
        all_passed = True
        for thermal_kw, label in test_powers:
            cmd = {'cmd': 'update', 'thermal_kw': thermal_kw}
            ser_e.write((json.dumps(cmd) + '\n').encode())
            ser_e.flush()
            
            response = ser_e.readline()
            if response:
                data = json.loads(response.decode().strip())
                if data.get('status') == 'ok':
                    power_mwe = data.get('power_mwe', 0.0)
                    pwm = data.get('pwm', 0)
                    print(f"   [{label}] Power: {power_mwe:.1f} MWe, PWM: {pwm}/255")
                else:
                    print_error(f"   [{label}] Failed")
                    all_passed = False
            else:
                print_error(f"   [{label}] No response")
                all_passed = False
            
            time.sleep(0.3)
        
        if all_passed:
            print_success("Power indicator test passed!")
            results.add_test("ESP-E: Power Levels", True)
        else:
            print_error("Some power tests failed")
            results.add_test("ESP-E: Power Levels", False)
        
        return ser_e
        
    except serial.SerialException as e:
        print_error(f"Serial port error: {e}")
        print_warning("ESP-E is optional (power indicator only)")
        results.add_warning("ESP-E: Port Open", f"Not connected: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        results.add_test("ESP-E: General", False, str(e))
        return None

# ============================================
# Integration Tests
# ============================================
def test_integration(ser_bc, ser_e):
    print_header("Integration Tests (ESP-BC + ESP-E)")
    
    if not ser_bc:
        print_error("ESP-BC not available, skipping integration tests")
        results.add_test("Integration", False, "ESP-BC not connected")
        return
    
    print("\n1. Simulating reactor startup sequence...")
    
    # Step 1: Raise rods
    print("\n   Step 1: Raising control rods to 60%...")
    cmd_bc = {
        'cmd': 'update',
        'rods': [60, 60, 60],
        'pumps': [2, 2, 2],
        'humid_ct': [0, 0, 0, 0]
    }
    ser_bc.write((json.dumps(cmd_bc) + '\n').encode())
    ser_bc.flush()
    response_bc = ser_bc.readline()
    
    if response_bc:
        data_bc = json.loads(response_bc.decode().strip())
        thermal_kw = data_bc.get('thermal_kw', 0.0)
        print_success(f"Thermal power: {thermal_kw:.1f} kW")
        
        # Update ESP-E if available
        if ser_e:
            cmd_e = {'cmd': 'update', 'thermal_kw': thermal_kw}
            ser_e.write((json.dumps(cmd_e) + '\n').encode())
            ser_e.flush()
            response_e = ser_e.readline()
            
            if response_e:
                data_e = json.loads(response_e.decode().strip())
                power_mwe = data_e.get('power_mwe', 0.0)
                pwm = data_e.get('pwm', 0)
                print_success(f"Power indicator: {power_mwe:.1f} MWe (PWM: {pwm})")
        
        results.add_test("Integration: Startup Step 1", True)
    else:
        print_error("No response from ESP-BC")
        results.add_test("Integration: Startup Step 1", False)
    
    time.sleep(1.0)
    
    # Step 2: Full power
    print("\n   Step 2: Raising to full power (90%)...")
    cmd_bc = {
        'cmd': 'update',
        'rods': [90, 90, 90],
        'pumps': [2, 2, 2],
        'humid_ct': [1, 1, 1, 1]
    }
    ser_bc.write((json.dumps(cmd_bc) + '\n').encode())
    ser_bc.flush()
    response_bc = ser_bc.readline()
    
    if response_bc:
        data_bc = json.loads(response_bc.decode().strip())
        thermal_kw = data_bc.get('thermal_kw', 0.0)
        state = data_bc.get('state', 0)
        turbine_speed = data_bc.get('turbine_speed', 0.0)
        
        print_success(f"Thermal power: {thermal_kw:.1f} kW")
        print_success(f"Turbine speed: {turbine_speed:.1f}%")
        
        # Update ESP-E
        if ser_e:
            cmd_e = {'cmd': 'update', 'thermal_kw': thermal_kw}
            ser_e.write((json.dumps(cmd_e) + '\n').encode())
            ser_e.flush()
            response_e = ser_e.readline()
            
            if response_e:
                data_e = json.loads(response_e.decode().strip())
                power_mwe = data_e.get('power_mwe', 0.0)
                print_success(f"Power output: {power_mwe:.1f} MWe")
        
        results.add_test("Integration: Full Power", True)
    else:
        print_error("No response from ESP-BC")
        results.add_test("Integration: Full Power", False)
    
    time.sleep(1.0)
    
    # Step 3: Shutdown
    print("\n   Step 3: Emergency shutdown...")
    cmd_bc = {
        'cmd': 'update',
        'rods': [0, 0, 0],
        'pumps': [0, 0, 0],
        'humid_ct': [0, 0, 0, 0]
    }
    ser_bc.write((json.dumps(cmd_bc) + '\n').encode())
    ser_bc.flush()
    response_bc = ser_bc.readline()
    
    if response_bc:
        data_bc = json.loads(response_bc.decode().strip())
        thermal_kw = data_bc.get('thermal_kw', 0.0)
        
        print_success(f"Thermal power: {thermal_kw:.1f} kW (shutdown)")
        
        # Update ESP-E
        if ser_e:
            cmd_e = {'cmd': 'update', 'thermal_kw': 0.0}
            ser_e.write((json.dumps(cmd_e) + '\n').encode())
            ser_e.flush()
            ser_e.readline()
            print_success("Power indicator: OFF")
        
        results.add_test("Integration: Shutdown", True)
    else:
        print_error("No response from ESP-BC")
        results.add_test("Integration: Shutdown", False)
    
    print_success("\nIntegration test completed!")

# ============================================
# Main Test Function
# ============================================
def main():
    print("\n" + "="*70)
    print(" 🧪 Test Komunikasi Lengkap - PKM PLTN Simulator")
    print("="*70)
    print("\nTest ini akan memeriksa:")
    print("  1. ESP-BC (Control Rods + Turbine + Pumps + Humidifiers)")
    print("  2. ESP-E (Power Indicator)")
    print("  3. Integration (kedua ESP bekerja bersama)")
    print("\nPastikan:")
    print("  - Kedua ESP32 terhubung dan firmware sudah diupload")
    print("  - UART ports tersedia (/dev/ttyAMA0 dan /dev/ttyAMA3)")
    print("  - Power supply mencukupi untuk semua hardware")
    
    input("\nPress Enter to start testing...")
    
    start_time = time.time()
    
    # Test ESP-BC
    ser_bc = test_esp_bc()
    
    time.sleep(1.0)
    
    # Test ESP-E
    ser_e = test_esp_e()
    
    time.sleep(1.0)
    
    # Integration tests
    test_integration(ser_bc, ser_e)
    
    # Close ports
    print_header("Cleanup")
    if ser_bc:
        ser_bc.close()
        print_success("ESP-BC port closed")
    if ser_e:
        ser_e.close()
        print_success("ESP-E port closed")
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    results.print_summary()
    
    print(f"\nTotal test time: {elapsed_time:.1f} seconds")
    
    # Exit code
    if results.failed == 0:
        print_success("\n🎉 All tests passed! Communication is working properly.")
        sys.exit(0)
    else:
        print_error(f"\n⚠️  {results.failed} test(s) failed. Check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
