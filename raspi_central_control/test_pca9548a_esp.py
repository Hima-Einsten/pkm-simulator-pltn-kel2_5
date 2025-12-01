#!/usr/bin/env python3
"""
Test script untuk PCA9548A + ESP32 multiple modules
Tes komunikasi I2C dengan ESP-B dan ESP-C melalui multiplexer
"""

import smbus2
import time
import struct

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70

# ESP-B Configuration
ESP_B_CHANNEL = 0
ESP_B_ADDR = 0x08

# ESP-C Configuration
ESP_C_CHANNEL = 1
ESP_C_ADDR = 0x09

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

def test_esp_b_communication(bus, esp_addr):
    """
    Test komunikasi dengan ESP-B (Batang Kendali & Reaktor)
    """
    print(f"\n📡 Testing ESP-B communication at 0x{esp_addr:02X}...")
    
    try:
        # Baca 16 bytes dari ESP-B
        # Protokol: rod1, rod2, rod3, reserved, kwThermal, etc.
        data = bus.read_i2c_block_data(esp_addr, 0x00, 16)
        
        print(f"✅ Received {len(data)} bytes from ESP-B:")
        print(f"   Raw data: {' '.join([f'{b:02X}' for b in data])}")
        
        # Parse data ESP-B
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
        print(f"❌ Failed to read from ESP-B: {e}")
        return False

def test_esp_c_communication(bus, esp_addr):
    """
    Test komunikasi dengan ESP-C (Turbin & Generator)
    """
    print(f"\n📡 Testing ESP-C communication at 0x{esp_addr:02X}...")
    
    try:
        # Baca 10 bytes dari ESP-C
        # Protokol: turbineRPM (float), kwElectric (float), generatorTemp (uint16)
        data = bus.read_i2c_block_data(esp_addr, 0x00, 10)
        
        print(f"✅ Received {len(data)} bytes from ESP-C:")
        print(f"   Raw data: {' '.join([f'{b:02X}' for b in data])}")
        
        # Parse data ESP-C
        if len(data) >= 10:
            # turbineRPM float di byte 0-3
            turbine_rpm_bytes = bytes(data[0:4])
            turbine_rpm = struct.unpack('f', turbine_rpm_bytes)[0]
            
            # kwElectric float di byte 4-7
            kw_electric_bytes = bytes(data[4:8])
            kw_electric = struct.unpack('f', kw_electric_bytes)[0]
            
            # generatorTemp uint16 di byte 8-9
            gen_temp = (data[9] << 8) | data[8]
            
            print(f"   Turbine RPM: {turbine_rpm:.2f} RPM")
            print(f"   kW Electric: {kw_electric:.2f} kW")
            print(f"   Generator Temp: {gen_temp}°C")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read from ESP-C: {e}")
        return False

def test_write_to_esp_b(bus, esp_addr):
    """
    Test menulis data ke ESP-B
    Kirim dummy pressure & pump status
    """
    print(f"\n📤 Testing write to ESP-B at 0x{esp_addr:02X}...")
    
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
        
        print(f"✅ Data sent to ESP-B successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write to ESP-B: {e}")
        return False

def test_write_to_esp_c(bus, esp_addr):
    """
    Test menulis data ke ESP-C
    Kirim dummy turbine control & pump status
    """
    print(f"\n📤 Testing write to ESP-C at 0x{esp_addr:02X}...")
    
    try:
        # Protokol ESP-C: steamPressure (float) + pump2Status (byte) + pump3Status (byte)
        steam_pressure = 75.0  # bar
        pump2_status = 1  # ON
        pump3_status = 1  # ON
        
        # Pack data (6 bytes total)
        data = struct.pack('fBB', steam_pressure, pump2_status, pump3_status)
        
        print(f"   Sending: steam_pressure={steam_pressure} bar, pump2={pump2_status}, pump3={pump3_status}")
        print(f"   Raw bytes: {' '.join([f'{b:02X}' for b in data])}")
        
        # Write data
        bus.write_i2c_block_data(esp_addr, 0x00, list(data))
        
        print(f"✅ Data sent to ESP-C successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write to ESP-C: {e}")
        return False

def test_esp_module(bus, pca_addr, esp_name, channel, esp_addr, write_func, read_func):
    """
    Test single ESP module
    """
    print(f"\n{'='*60}")
    print(f"  Testing {esp_name}")
    print(f"{'='*60}")
    
    # Select channel
    print(f"\n--- Select Channel {channel} for {esp_name} ---")
    if not select_pca9548a_channel(bus, pca_addr, channel):
        return False
    
    time.sleep(0.1)  # Wait for channel switch
    
    # Scan devices di channel
    print(f"\n--- Scan Channel {channel} ---")
    channel_devices = scan_i2c_devices(bus)
    
    if esp_addr not in channel_devices:
        print(f"❌ {esp_name} not found at 0x{esp_addr:02X}")
        print(f"   Make sure {esp_name} is connected to Channel {channel}")
        return False
    
    print(f"✅ {esp_name} found at 0x{esp_addr:02X}")
    
    # Test communication
    print(f"\n--- Test {esp_name} Communication ---")
    
    # Test write
    write_success = write_func(bus, esp_addr)
    time.sleep(0.2)
    
    # Test read
    read_success = read_func(bus, esp_addr)
    
    return write_success and read_success

def main():
    print("=" * 60)
    print("  PCA9548A + ESP32 Multi-Module I2C Test")
    print("  Testing ESP-B and ESP-C")
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
        
        # Test ESP-B
        esp_b_success = test_esp_module(
            bus, PCA9548A_ADDR, 
            "ESP-B (Reactor Control)", 
            ESP_B_CHANNEL, ESP_B_ADDR,
            test_write_to_esp_b, test_esp_b_communication
        )
        
        time.sleep(0.5)
        
        # Test ESP-C
        esp_c_success = test_esp_module(
            bus, PCA9548A_ADDR,
            "ESP-C (Turbine & Generator)",
            ESP_C_CHANNEL, ESP_C_ADDR,
            test_write_to_esp_c, test_esp_c_communication
        )
        
        # Summary
        print("\n" + "=" * 60)
        print("  TEST SUMMARY")
        print("=" * 60)
        print(f"  ESP-B (Channel {ESP_B_CHANNEL}, 0x{ESP_B_ADDR:02X}): {'✅ PASS' if esp_b_success else '❌ FAIL'}")
        print(f"  ESP-C (Channel {ESP_C_CHANNEL}, 0x{ESP_C_ADDR:02X}): {'✅ PASS' if esp_c_success else '❌ FAIL'}")
        print("=" * 60)
        
        if esp_b_success and esp_c_success:
            print("  ✅ ALL TESTS PASSED!")
            print("  Both ESP modules are communicating correctly!")
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
