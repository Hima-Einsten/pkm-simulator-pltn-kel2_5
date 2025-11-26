#!/usr/bin/env python3
"""
Test script untuk PCA9548A + ESP32 single module
Tes komunikasi I2C dengan 1 ESP melalui multiplexer
"""

import smbus2
import time
import struct

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70
ESP_CHANNEL = 0  # Channel 0 pada PCA9548A
ESP_ADDR = 0x08  # ESP-B address (ganti sesuai modul yang ditest)

def select_pca9548a_channel(bus, pca_addr, channel):
    """
    Pilih channel pada PCA9548A
    channel: 0-7
    """
    if channel < 0 or channel > 7:
        print(f"❌ Invalid channel: {channel}")
        return False
    
    try:
        channel_mask = 1 << channel
        bus.write_byte(pca_addr, channel_mask)
        print(f"✅ PCA9548A Channel {channel} selected (mask: 0x{channel_mask:02X})")
        return True
    except Exception as e:
        print(f"❌ Failed to select channel: {e}")
        return False

def scan_i2c_devices(bus):
    """Scan semua device di I2C bus"""
    print("\n🔍 Scanning I2C bus...")
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
            print(f"  Found device: 0x{addr:02X}")
        except:
            pass
    return devices

def test_esp_communication(bus, esp_addr):
    """
    Test komunikasi dengan ESP32
    Coba baca data dari ESP
    """
    print(f"\n📡 Testing communication with ESP at 0x{esp_addr:02X}...")
    
    try:
        # Coba baca 16 bytes dari ESP-B
        # (sesuai protokol: rod1, rod2, rod3, reserved, kwThermal, etc.)
        data = bus.read_i2c_block_data(esp_addr, 0x00, 16)
        
        print(f"✅ Received {len(data)} bytes from ESP:")
        print(f"   Raw data: {' '.join([f'{b:02X}' for b in data])}")
        
        # Parse data (contoh untuk ESP-B)
        if len(data) >= 16:
            rod1 = data[0]
            rod2 = data[1]
            rod3 = data[2]
            # kwThermal adalah float di byte 4-7
            kw_thermal_bytes = bytes(data[4:8])
            kw_thermal = struct.unpack('f', kw_thermal_bytes)[0]
            
            print(f"   Rod 1: {rod1}%")
            print(f"   Rod 2: {rod2}%")
            print(f"   Rod 3: {rod3}%")
            print(f"   kW Thermal: {kw_thermal:.2f} kW")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read from ESP: {e}")
        return False

def test_write_to_esp(bus, esp_addr):
    """
    Test menulis data ke ESP
    Kirim dummy pressure & pump status
    """
    print(f"\n📤 Testing write to ESP at 0x{esp_addr:02X}...")
    
    try:
        # Protokol ESP-B: pressure (float) + reserved (float) + pump1 (byte) + pump2 (byte)
        pressure = 155.5  # bar
        reserved = 0.0
        pump1_status = 1  # ON
        pump2_status = 1  # ON
        
        # Pack data
        data = struct.pack('ffBB', pressure, reserved, pump1_status, pump2_status)
        
        print(f"   Sending: pressure={pressure} bar, pump1={pump1_status}, pump2={pump2_status}")
        print(f"   Raw bytes: {' '.join([f'{b:02X}' for b in data])}")
        
        # Write data
        bus.write_i2c_block_data(esp_addr, 0x00, list(data))
        
        print(f"✅ Data sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write to ESP: {e}")
        return False

def main():
    print("=" * 60)
    print("  PCA9548A + ESP32 I2C Test Script")
    print("=" * 60)
    
    try:
        # Init I2C bus
        bus = smbus2.SMBus(I2C_BUS)
        print(f"✅ I2C Bus {I2C_BUS} initialized")
        
        # Step 1: Scan I2C bus untuk cek PCA9548A
        print("\n--- Step 1: Check PCA9548A ---")
        devices = scan_i2c_devices(bus)
        
        if PCA9548A_ADDR not in devices:
            print(f"❌ PCA9548A not found at 0x{PCA9548A_ADDR:02X}")
            print("   Check wiring: VCC, GND, SDA, SCL")
            return
        
        print(f"✅ PCA9548A found at 0x{PCA9548A_ADDR:02X}")
        
        # Step 2: Select channel untuk ESP
        print(f"\n--- Step 2: Select Channel {ESP_CHANNEL} ---")
        if not select_pca9548a_channel(bus, PCA9548A_ADDR, ESP_CHANNEL):
            return
        
        time.sleep(0.1)  # Wait for channel switch
        
        # Step 3: Scan devices di channel yang dipilih
        print(f"\n--- Step 3: Scan Channel {ESP_CHANNEL} ---")
        channel_devices = scan_i2c_devices(bus)
        
        if ESP_ADDR not in channel_devices:
            print(f"❌ ESP not found at 0x{ESP_ADDR:02X}")
            print(f"   Make sure ESP is connected to PCA9548A Channel {ESP_CHANNEL}")
            print("   Check ESP I2C address in code matches 0x{ESP_ADDR:02X}")
            return
        
        print(f"✅ ESP found at 0x{ESP_ADDR:02X}")
        
        # Step 4: Test komunikasi
        print("\n--- Step 4: Test Communication ---")
        
        # Test write
        test_write_to_esp(bus, ESP_ADDR)
        time.sleep(0.2)
        
        # Test read
        test_read_success = test_esp_communication(bus, ESP_ADDR)
        
        # Summary
        print("\n" + "=" * 60)
        if test_read_success:
            print("  ✅ ALL TESTS PASSED!")
            print("  PCA9548A + ESP32 communication is working!")
        else:
            print("  ⚠️  Some tests failed. Check ESP code and wiring.")
        print("=" * 60)
        
        # Cleanup
        bus.write_byte(PCA9548A_ADDR, 0x00)  # Disable all channels
        bus.close()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
