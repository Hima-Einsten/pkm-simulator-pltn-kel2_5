#!/usr/bin/env python3
"""
UART Monitor - Real-time UART Communication Monitor
Monitors ESP-BC and ESP-E communication in real-time

Usage:
    python3 uart_monitor.py
"""

import serial
import json
import time
import sys
import threading
from datetime import datetime

class UARTMonitor:
    def __init__(self, port, name, baudrate=115200):
        self.port = port
        self.name = name
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.rx_count = 0
        self.tx_count = 0
        self.error_count = 0
        self.last_rx_time = None
        self.last_tx_time = None
        
    def connect(self):
        """Connect to serial port"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )
            print(f"[{self.name}] ✅ Connected to {self.port}")
            return True
        except Exception as e:
            print(f"[{self.name}] ❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[{self.name}] Disconnected")
    
    def send_ping(self):
        """Send ping command"""
        try:
            command = {"cmd": "ping"}
            command_str = json.dumps(command) + '\n'
            self.ser.write(command_str.encode('utf-8'))
            self.ser.flush()
            self.tx_count += 1
            self.last_tx_time = time.time()
            return True
        except Exception as e:
            print(f"[{self.name}] ❌ Send error: {e}")
            self.error_count += 1
            return False
    
    def read_response(self):
        """Read response from ESP"""
        try:
            if self.ser.in_waiting > 0:
                response = self.ser.readline()
                response_str = response.decode('utf-8').strip()
                self.rx_count += 1
                self.last_rx_time = time.time()
                
                try:
                    data = json.loads(response_str)
                    return True, data
                except json.JSONDecodeError:
                    return False, response_str
            return None, None
        except Exception as e:
            self.error_count += 1
            return False, str(e)
    
    def get_stats(self):
        """Get communication statistics"""
        now = time.time()
        rx_age = (now - self.last_rx_time) if self.last_rx_time else None
        tx_age = (now - self.last_tx_time) if self.last_tx_time else None
        
        return {
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'error_count': self.error_count,
            'rx_age': rx_age,
            'tx_age': tx_age
        }


def print_header():
    """Print monitoring header"""
    print("\n" + "="*80)
    print("UART COMMUNICATION MONITOR")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"{'Time':<12} {'Device':<10} {'Type':<6} {'Status':<8} {'Data':<40}")
    print("-"*80)


def monitor_continuous(esp_bc_port, esp_e_port):
    """Continuous monitoring mode"""
    print_header()
    
    # Initialize monitors
    esp_bc = UARTMonitor(esp_bc_port, "ESP-BC")
    esp_e = UARTMonitor(esp_e_port, "ESP-E")
    
    # Connect
    if not esp_bc.connect():
        print("❌ Cannot connect to ESP-BC")
        return False
    
    if not esp_e.connect():
        print("❌ Cannot connect to ESP-E")
        esp_bc.disconnect()
        return False
    
    print("\n📡 Monitoring started (Press Ctrl+C to stop)...\n")
    
    try:
        counter = 0
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Ping ESP-BC every 2 seconds
            if counter % 20 == 0:
                esp_bc.send_ping()
                print(f"{timestamp:<12} {'ESP-BC':<10} {'TX':<6} {'PING':<8} {{'cmd': 'ping'}}")
            
            # Ping ESP-E every 2 seconds (offset)
            if counter % 20 == 10:
                esp_e.send_ping()
                print(f"{timestamp:<12} {'ESP-E':<10} {'TX':<6} {'PING':<8} {{'cmd': 'ping'}}")
            
            # Check ESP-BC response
            status, data = esp_bc.read_response()
            if status is not None:
                if status:
                    data_str = json.dumps(data)[:40]
                    print(f"{timestamp:<12} {'ESP-BC':<10} {'RX':<6} {'OK':<8} {data_str}")
                else:
                    print(f"{timestamp:<12} {'ESP-BC':<10} {'RX':<6} {'ERROR':<8} {str(data)[:40]}")
            
            # Check ESP-E response
            status, data = esp_e.read_response()
            if status is not None:
                if status:
                    data_str = json.dumps(data)[:40]
                    print(f"{timestamp:<12} {'ESP-E':<10} {'RX':<6} {'OK':<8} {data_str}")
                else:
                    print(f"{timestamp:<12} {'ESP-E':<10} {'RX':<6} {'ERROR':<8} {str(data)[:40]}")
            
            # Print stats every 10 seconds
            if counter % 100 == 0 and counter > 0:
                print("\n" + "-"*80)
                print("STATISTICS:")
                
                bc_stats = esp_bc.get_stats()
                print(f"  ESP-BC: TX={bc_stats['tx_count']}, RX={bc_stats['rx_count']}, "
                      f"Errors={bc_stats['error_count']}, "
                      f"Last RX: {bc_stats['rx_age']:.1f}s ago" if bc_stats['rx_age'] else "Never")
                
                e_stats = esp_e.get_stats()
                print(f"  ESP-E:  TX={e_stats['tx_count']}, RX={e_stats['rx_count']}, "
                      f"Errors={e_stats['error_count']}, "
                      f"Last RX: {e_stats['rx_age']:.1f}s ago" if e_stats['rx_age'] else "Never")
                
                print("-"*80 + "\n")
            
            counter += 1
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")
    finally:
        esp_bc.disconnect()
        esp_e.disconnect()
        
        # Final stats
        print("\n" + "="*80)
        print("FINAL STATISTICS")
        print("="*80)
        
        bc_stats = esp_bc.get_stats()
        print(f"ESP-BC:")
        print(f"  Messages sent: {bc_stats['tx_count']}")
        print(f"  Messages received: {bc_stats['rx_count']}")
        print(f"  Errors: {bc_stats['error_count']}")
        print(f"  Success rate: {(bc_stats['rx_count']/bc_stats['tx_count']*100):.1f}%" if bc_stats['tx_count'] > 0 else "N/A")
        
        e_stats = esp_e.get_stats()
        print(f"\nESP-E:")
        print(f"  Messages sent: {e_stats['tx_count']}")
        print(f"  Messages received: {e_stats['rx_count']}")
        print(f"  Errors: {e_stats['error_count']}")
        print(f"  Success rate: {(e_stats['rx_count']/e_stats['tx_count']*100):.1f}%" if e_stats['tx_count'] > 0 else "N/A")
        
        print("="*80)
    
    return True


def test_stress(esp_bc_port, esp_e_port, duration=60):
    """Stress test mode - rapid fire commands"""
    print("\n" + "="*80)
    print(f"STRESS TEST - {duration} seconds")
    print("="*80)
    
    esp_bc = UARTMonitor(esp_bc_port, "ESP-BC")
    esp_e = UARTMonitor(esp_e_port, "ESP-E")
    
    if not esp_bc.connect() or not esp_e.connect():
        print("❌ Connection failed")
        return False
    
    print(f"\n🔥 Sending rapid commands for {duration} seconds...")
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            # Send to ESP-BC
            esp_bc.send_ping()
            time.sleep(0.01)
            esp_bc.read_response()
            
            # Send to ESP-E
            esp_e.send_ping()
            time.sleep(0.01)
            esp_e.read_response()
            
            # Progress
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"  {elapsed}s: ESP-BC TX={esp_bc.tx_count} RX={esp_bc.rx_count}, "
                      f"ESP-E TX={esp_e.tx_count} RX={esp_e.rx_count}")
                time.sleep(0.1)  # Avoid duplicate prints
    
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
    
    finally:
        esp_bc.disconnect()
        esp_e.disconnect()
        
        # Results
        print("\n" + "="*80)
        print("STRESS TEST RESULTS")
        print("="*80)
        
        bc_stats = esp_bc.get_stats()
        e_stats = esp_e.get_stats()
        
        bc_rate = (bc_stats['rx_count']/bc_stats['tx_count']*100) if bc_stats['tx_count'] > 0 else 0
        e_rate = (e_stats['rx_count']/e_stats['tx_count']*100) if e_stats['tx_count'] > 0 else 0
        
        print(f"ESP-BC: {bc_stats['tx_count']} sent, {bc_stats['rx_count']} received, "
              f"{bc_stats['error_count']} errors")
        print(f"        Success rate: {bc_rate:.1f}%")
        
        print(f"ESP-E:  {e_stats['tx_count']} sent, {e_stats['rx_count']} received, "
              f"{e_stats['error_count']} errors")
        print(f"        Success rate: {e_rate:.1f}%")
        
        if bc_rate > 95 and e_rate > 95:
            print("\n✅ PASS: Both ESPs have >95% success rate")
        else:
            print("\n⚠️  WARNING: Success rate below 95%")
        
        print("="*80)


def main():
    """Main function"""
    print("\n" + "="*80)
    print("UART MONITOR & TEST TOOL")
    print("="*80)
    
    # Configuration
    esp_bc_port = '/dev/ttyAMA0'
    esp_e_port = '/dev/ttyUSB0'
    
    print(f"\nConfiguration:")
    print(f"  ESP-BC: {esp_bc_port} (GPIO 14/15)")
    print(f"  ESP-E:  {esp_e_port} (USB Serial Adapter)")
    print(f"  Baudrate: 115200")
    
    print("\nSelect test mode:")
    print("  1. Continuous monitoring (real-time)")
    print("  2. Stress test (60 seconds)")
    print("  3. Quick ping test")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        monitor_continuous(esp_bc_port, esp_e_port)
    elif choice == '2':
        test_stress(esp_bc_port, esp_e_port, duration=60)
    elif choice == '3':
        # Quick test
        print("\n📍 Quick ping test...")
        esp_bc = UARTMonitor(esp_bc_port, "ESP-BC")
        esp_e = UARTMonitor(esp_e_port, "ESP-E")
        
        bc_ok = False
        e_ok = False
        
        if esp_bc.connect():
            esp_bc.send_ping()
            time.sleep(0.2)
            status, data = esp_bc.read_response()
            bc_ok = (status is True)
            print(f"  ESP-BC: {'✅ OK' if bc_ok else '❌ FAIL'}")
            if bc_ok:
                print(f"    Response: {data}")
            esp_bc.disconnect()
        
        if esp_e.connect():
            esp_e.send_ping()
            time.sleep(0.2)
            status, data = esp_e.read_response()
            e_ok = (status is True)
            print(f"  ESP-E:  {'✅ OK' if e_ok else '❌ FAIL'}")
            if e_ok:
                print(f"    Response: {data}")
            esp_e.disconnect()
        
        if bc_ok and e_ok:
            print("\n✅ Both ESPs responding")
        else:
            print("\n❌ One or more ESPs not responding")
    else:
        print("Invalid choice")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
