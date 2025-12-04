#!/usr/bin/env python3
"""
Quick test untuk ESP-E (3-Flow Visualizer)
Test mengirim data 15 bytes untuk ketiga aliran
"""

import smbus2
from smbus2 import i2c_msg
import time
import struct

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70
ESP_E_CHANNEL = 2
ESP_E_ADDR = 0x0A

def select_pca_channel(bus, channel):
    """Select PCA9548A channel"""
    try:
        channel_mask = 1 << channel
        bus.write_byte(PCA9548A_ADDR, channel_mask)
        print(f"✅ Selected PCA9548A Channel {channel}")
        return True
    except Exception as e:
        print(f"❌ Failed to select channel: {e}")
        return False

def test_esp_e_three_flows():
    """Test ESP-E dengan 3 aliran"""
    print("="*60)
    print("  ESP-E Quick Test (3-Flow Visualizer)")
    print("="*60)
    
    try:
        bus = smbus2.SMBus(I2C_BUS)
        print(f"✅ I2C Bus {I2C_BUS} opened")
        
        # Select channel
        if not select_pca_channel(bus, ESP_E_CHANNEL):
            return
        
        time.sleep(0.1)
        
        # Test scenarios
        scenarios = [
            ("All OFF", 0.0, 0, 0.0, 0, 0.0, 0, 3),
            ("Primary ON", 155.0, 2, 0.0, 0, 0.0, 0, 8),
            ("Primary + Secondary ON", 155.0, 2, 105.0, 2, 0.0, 0, 8),
            ("All ON", 155.0, 2, 105.0, 2, 55.0, 2, 10),
            ("All STARTING", 150.0, 1, 100.0, 1, 50.0, 1, 8),
        ]
        
        for name, p1, s1, p2, s2, p3, s3, duration in scenarios:
            print(f"\n{'='*60}")
            print(f"Test: {name}")
            print(f"{'='*60}")
            
            # Pack 15 bytes: 3 x (float + byte)
            data = struct.pack('fBfBfB', p1, s1, p2, s2, p3, s3)
            
            print(f"Primary: {p1:.1f} bar, Status: {s1}")
            print(f"Secondary: {p2:.1f} bar, Status: {s2}")
            print(f"Tertiary: {p3:.1f} bar, Status: {s3}")
            print(f"Data ({len(data)} bytes): {' '.join([f'{b:02X}' for b in data])}")
            
            # Send using i2c_msg (register 0x00 + 15 bytes data)
            write_msg = i2c_msg.write(ESP_E_ADDR, [0x00] + list(data))
            bus.i2c_rdwr(write_msg)
            
            print(f"✅ Sent! Watch LEDs for {duration}s...")
            
            # Wait and show countdown
            for i in range(duration):
                print(f"  {i+1}/{duration}s", end='\r')
                time.sleep(1)
            print()
        
        # Turn off all
        print("\n" + "="*60)
        print("Turning off all flows...")
        data = struct.pack('fBfBfB', 0.0, 0, 0.0, 0, 0.0, 0)
        write_msg = i2c_msg.write(ESP_E_ADDR, [0x00] + list(data))
        bus.i2c_rdwr(write_msg)
        print("✅ All flows OFF")
        
        # Cleanup
        bus.write_byte(PCA9548A_ADDR, 0x00)
        bus.close()
        
        print("\n" + "="*60)
        print("Test completed!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_esp_e_three_flows()
