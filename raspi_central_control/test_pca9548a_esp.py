#!/usr/bin/env python3
"""
Test script untuk PCA9548A + ESP32 multiple modules
Auto-detect dan test semua ESP modules yang terhubung
"""

import smbus2
import time
import struct

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70

# ESP Modules Configuration
ESP_MODULES = {
    'ESP-B': {
        'name': 'ESP-B (Reactor Control)',
        'channel': 0,
        'address': 0x08,
        'write_size': 10,
        'read_size': 16,
        'protocol': 'reactor'
    },
    'ESP-C': {
        'name': 'ESP-C (Turbine & Generator)',
        'channel': 1,
        'address': 0x09,
        'write_size': 3,
        'read_size': 10,
        'protocol': 'turbine'
    },
    'ESP-E': {
        'name': 'ESP-E (3-Flow Visualizer: Primary, Secondary, Tertiary)',
        'channel': 2,
        'address': 0x0A,
        'write_size': 15,  # 3 flows x (4 bytes float + 1 byte status)
        'read_size': 2,
        'protocol': 'three_flow_visualizer'
    }
}

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
        
        # Verify channel selection
        time.sleep(0.05)
        current_channel = bus.read_byte(pca_addr)
        print(f"   Channel verification: 0x{current_channel:02X} (expected: 0x{channel_mask:02X})")
        
        return True
    except Exception as e:
        print(f"❌ Failed to select channel: {e}")
        return False

def scan_i2c_devices(bus, silent=False):
    """Scan semua device di I2C bus"""
    if not silent:
        print("\n🔍 Scanning I2C bus...")
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
            if not silent:
                print(f"  Found device: 0x{addr:02X}")
        except:
            pass
    return devices

def detect_connected_modules(bus, pca_addr, modules):
    """
    Auto-detect which ESP modules are connected
    Returns list of connected module IDs
    """
    print("\n" + "="*60)
    print("  AUTO-DETECTING CONNECTED ESP MODULES")
    print("="*60)
    
    connected = []
    
    for module_id, config in modules.items():
        channel = config['channel']
        esp_addr = config['address']
        name = config['name']
        
        # Select channel
        try:
            if not select_pca9548a_channel(bus, pca_addr, channel):
                continue
            
            time.sleep(0.05)
            
            # Scan for device on this channel
            devices = scan_i2c_devices(bus, silent=True)
            
            if esp_addr in devices:
                connected.append(module_id)
                print(f"✅ {name} DETECTED on Channel {channel} @ 0x{esp_addr:02X}")
            else:
                print(f"❌ {name} NOT FOUND on Channel {channel} @ 0x{esp_addr:02X}")
                
        except Exception as e:
            print(f"⚠️  Error detecting {name}: {e}")
    
    print("="*60)
    print(f"  Total modules detected: {len(connected)}/{len(modules)}")
    print("="*60)
    
    return connected

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
        # Protokol: powerLevel (float, 4 bytes), state (uint32, 4 bytes), 
        #           generatorStatus (byte), turbineStatus (byte)
        data = bus.read_i2c_block_data(esp_addr, 0x00, 10)
        
        print(f"✅ Received {len(data)} bytes from ESP-C:")
        print(f"   Raw data: {' '.join([f'{b:02X}' for b in data])}")
        
        # Parse data ESP-C
        if len(data) >= 10:
            # powerLevel float di byte 0-3
            power_level_bytes = bytes(data[0:4])
            power_level = struct.unpack('f', power_level_bytes)[0]
            
            # state uint32 di byte 4-7
            state_bytes = bytes(data[4:8])
            state = struct.unpack('I', state_bytes)[0]
            
            # generatorStatus byte 8, turbineStatus byte 9
            generator_status = data[8]
            turbine_status = data[9]
            
            state_names = {0: "IDLE", 1: "STARTING_UP", 2: "RUNNING", 3: "SHUTTING_DOWN"}
            state_name = state_names.get(state, "UNKNOWN")
            
            print(f"   Power Level: {power_level:.2f}%")
            print(f"   State: {state} ({state_name})")
            print(f"   Generator Status: {generator_status}")
            print(f"   Turbine Status: {turbine_status}")
        
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
    Kirim dummy rod positions (protocol: 3 bytes)
    """
    print(f"\n📤 Testing write to ESP-C at 0x{esp_addr:02X}...")
    
    try:
        # Protokol ESP-C: rod1 (byte) + rod2 (byte) + rod3 (byte)
        rod1 = 50  # 50%
        rod2 = 50  # 50%
        rod3 = 50  # 50%
        
        # Pack data (3 bytes total)
        data = struct.pack('BBB', rod1, rod2, rod3)
        
        print(f"   Sending: rod1={rod1}%, rod2={rod2}%, rod3={rod3}%")
        print(f"   Raw bytes: {' '.join([f'{b:02X}' for b in data])}")
        
        # Write data
        bus.write_i2c_block_data(esp_addr, 0x00, list(data))
        
        print(f"✅ Data sent to ESP-C successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write to ESP-C: {e}")
        return False

def test_write_to_esp_three_flow_visualizer(bus, esp_addr):
    """
    Test menulis data ke ESP-E (3-Flow Visualizer)
    Kirim data untuk ketiga aliran (Primary, Secondary, Tertiary)
    """
    print(f"\n📤 Testing write to 3-Flow Visualizer at 0x{esp_addr:02X}...")
    
    # Test scenarios untuk ketiga aliran
    test_scenarios = [
        {
            'name': 'All Flows OFF',
            'primary': (150.0, 0),
            'secondary': (100.0, 0),
            'tertiary': (50.0, 0),
            'duration': 3
        },
        {
            'name': 'Primary ON, Others OFF',
            'primary': (155.0, 2),
            'secondary': (0.0, 0),
            'tertiary': (0.0, 0),
            'duration': 8
        },
        {
            'name': 'Primary + Secondary ON',
            'primary': (155.0, 2),
            'secondary': (105.0, 2),
            'tertiary': (0.0, 0),
            'duration': 8
        },
        {
            'name': 'All Flows ON (Full Operation)',
            'primary': (155.0, 2),
            'secondary': (105.0, 2),
            'tertiary': (55.0, 2),
            'duration': 10
        },
        {
            'name': 'All STARTING (Slow Animation)',
            'primary': (150.0, 1),
            'secondary': (100.0, 1),
            'tertiary': (50.0, 1),
            'duration': 8
        },
        {
            'name': 'All SHUTTING DOWN',
            'primary': (140.0, 3),
            'secondary': (90.0, 3),
            'tertiary': (40.0, 3),
            'duration': 8
        },
    ]
    
    for scenario in test_scenarios:
        try:
            print(f"\n{'='*60}")
            print(f"   Scenario: {scenario['name']}")
            print(f"{'='*60}")
            
            # Pack data untuk 3 aliran (15 bytes total)
            # Primary: 4 bytes float + 1 byte status
            # Secondary: 4 bytes float + 1 byte status  
            # Tertiary: 4 bytes float + 1 byte status
            data = struct.pack('fBfBfB',
                scenario['primary'][0], scenario['primary'][1],
                scenario['secondary'][0], scenario['secondary'][1],
                scenario['tertiary'][0], scenario['tertiary'][1]
            )
            
            print(f"   Primary: {scenario['primary'][0]:.1f} bar, Status: {scenario['primary'][1]}")
            print(f"   Secondary: {scenario['secondary'][0]:.1f} bar, Status: {scenario['secondary'][1]}")
            print(f"   Tertiary: {scenario['tertiary'][0]:.1f} bar, Status: {scenario['tertiary'][1]}")
            print(f"   Raw bytes ({len(data)}): {' '.join([f'{b:02X}' for b in data])}")
            
            # Write data
            bus.write_i2c_block_data(esp_addr, 0x00, list(data))
            
            print(f"   ✅ Data sent successfully!")
            print(f"   💡 Watch ALL THREE flow LEDs for {scenario['duration']} seconds...")
            
            for i in range(scenario['duration']):
                print(f"      {i+1}/{scenario['duration']}s", end='\r')
                time.sleep(1)
            print()
            
        except Exception as e:
            print(f"   ❌ Failed to write: {e}")
            return False
    
    return True

def test_read_from_esp_visualizer(bus, esp_addr):
    """
    Test membaca data dari ESP Visualizer (E/F/G)
    """
    print(f"\n📡 Testing read from Visualizer at 0x{esp_addr:02X}...")
    
    try:
        # Baca 2 bytes: animationSpeed + LED_COUNT
        data = bus.read_i2c_block_data(esp_addr, 0x00, 2)
        
        print(f"   ✅ Received {len(data)} bytes:")
        print(f"   Raw data: {' '.join([f'{b:02X}' for b in data])}")
        
        if len(data) >= 2:
            animation_speed = data[0]
            led_count = data[1]
            
            print(f"   Animation Speed: {animation_speed}")
            print(f"   LED Count: {led_count}")
            
            # Interpretasi status
            if animation_speed == 0:
                print(f"   Status: OFF (no animation)")
            elif animation_speed == 33:
                print(f"   Status: STARTING (slow)")
            elif animation_speed == 100:
                print(f"   Status: ON (fast)")
            elif animation_speed == 20:
                print(f"   Status: SHUTTING_DOWN (very slow)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to read: {e}")
        return False

def test_esp_module(bus, pca_addr, module_id, config):
    """
    Test single ESP module with auto protocol selection
    """
    name = config['name']
    channel = config['channel']
    esp_addr = config['address']
    protocol = config['protocol']
    
    print(f"\n{'='*60}")
    print(f"  Testing {name}")
    print(f"{'='*60}")
    
    # Select channel
    print(f"\n--- Select Channel {channel} ---")
    if not select_pca9548a_channel(bus, pca_addr, channel):
        return False
    
    time.sleep(0.1)  # Wait for channel switch
    
    # Test communication based on protocol
    print(f"\n--- Test {name} Communication ---")
    
    write_success = False
    read_success = False
    
    try:
        if protocol == 'reactor':
            # ESP-B protocol
            write_success = test_write_to_esp_b(bus, esp_addr)
            time.sleep(0.2)
            read_success = test_esp_b_communication(bus, esp_addr)
            
        elif protocol == 'turbine':
            # ESP-C protocol
            write_success = test_write_to_esp_c(bus, esp_addr)
            time.sleep(0.2)
            read_success = test_esp_c_communication(bus, esp_addr)
            
        elif protocol == 'three_flow_visualizer':
            # ESP-E protocol (3 flows in one ESP)
            write_success = test_write_to_esp_three_flow_visualizer(bus, esp_addr)
            time.sleep(0.2)
            read_success = test_read_from_esp_visualizer(bus, esp_addr)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return write_success and read_success

def test_esp_e_detailed(bus, pca_addr):
    """
    Detailed test khusus untuk ESP-E dengan debugging lengkap
    ESP-E mengontrol 3 aliran sekaligus (Primary, Secondary, Tertiary)
    """
    print("\n" + "="*70)
    print("  DETAILED TEST: ESP-E (3-Flow Visualizer)")
    print("  Controls: Primary + Secondary + Tertiary Flows")
    print("="*70)
    
    esp_addr = 0x0A
    channel = 2
    
    # Step 1: Select channel
    print("\n--- Step 1: Select PCA9548A Channel 2 ---")
    if not select_pca9548a_channel(bus, pca_addr, channel):
        return False
    time.sleep(0.1)
    
    # Step 2: Scan for ESP-E
    print("\n--- Step 2: Scan for ESP-E at 0x0A ---")
    devices = scan_i2c_devices(bus, silent=False)
    
    if esp_addr not in devices:
        print(f"\n❌ ESP-E not found at 0x{esp_addr:02X}")
        print("   Possible issues:")
        print("   1. ESP-E not powered or not running")
        print("   2. I2C address in code != 0x0A")
        print("   3. SDA/SCL not connected to ESP32 GPIO 21/22")
        print("   4. PCA9548A channel 2 wiring issue")
        return False
    
    print(f"\n✅ ESP-E found at 0x{esp_addr:02X}")
    
    # Step 3: Test 3-Flow control with various scenarios
    print("\n--- Step 3: Test 3-Flow LED Animation ---")
    
    flow_tests = [
        {
            'name': 'All Flows OFF',
            'primary': (150.0, 0), 'secondary': (100.0, 0), 'tertiary': (50.0, 0),
            'desc': 'All LEDs should be OFF', 'duration': 3
        },
        {
            'name': 'Primary Flow ONLY (ON)',
            'primary': (155.0, 2), 'secondary': (0.0, 0), 'tertiary': (0.0, 0),
            'desc': 'Only Primary LEDs flowing (fast)', 'duration': 8
        },
        {
            'name': 'Primary + Secondary Flows (ON)',
            'primary': (155.0, 2), 'secondary': (105.0, 2), 'tertiary': (0.0, 0),
            'desc': 'Primary & Secondary LEDs flowing', 'duration': 8
        },
        {
            'name': 'All 3 Flows ON (Full Operation)',
            'primary': (155.0, 2), 'secondary': (105.0, 2), 'tertiary': (55.0, 2),
            'desc': 'All LEDs flowing (fast animation)', 'duration': 10
        },
        {
            'name': 'All Flows STARTING (Slow)',
            'primary': (150.0, 1), 'secondary': (100.0, 1), 'tertiary': (50.0, 1),
            'desc': 'All LEDs slow animation (starting)', 'duration': 8
        },
        {
            'name': 'All Flows SHUTTING DOWN',
            'primary': (140.0, 3), 'secondary': (90.0, 3), 'tertiary': (40.0, 3),
            'desc': 'All LEDs very slow animation', 'duration': 8
        }
    ]
    
    for test in flow_tests:
        print(f"\n{'='*70}")
        print(f">>> Test: {test['name']}")
        print(f"    Expected: {test['desc']}")
        print(f"{'='*70}")
        
        try:
            # Pack 15 bytes: 3 x (float pressure + byte status)
            data = struct.pack('fBfBfB',
                test['primary'][0], test['primary'][1],
                test['secondary'][0], test['secondary'][1],
                test['tertiary'][0], test['tertiary'][1]
            )
            
            print(f"    Primary: {test['primary'][0]:.1f} bar, Status: {test['primary'][1]}")
            print(f"    Secondary: {test['secondary'][0]:.1f} bar, Status: {test['secondary'][1]}")
            print(f"    Tertiary: {test['tertiary'][0]:.1f} bar, Status: {test['tertiary'][1]}")
            print(f"    Raw bytes ({len(data)}): {' '.join([f'{b:02X}' for b in data])}")
            
            bus.write_i2c_block_data(esp_addr, 0x00, list(data))
            print(f"    ✅ Data sent successfully!")
            
            time.sleep(0.2)
            
            # Read response
            response = bus.read_i2c_block_data(esp_addr, 0x00, 2)
            anim_speed = response[0]
            led_count = response[1]
            
            print(f"    Response: animation_speed={anim_speed}, led_count={led_count}")
            
            # Observe animation
            print(f"    💡 WATCH ALL 3 FLOW LEDs for {test['duration']} seconds...")
            for i in range(test['duration']):
                print(f"       {i+1}/{test['duration']}s", end='\r')
                time.sleep(1)
            print()
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return False
    
    print("\n" + "="*70)
    print("  ESP-E 3-FLOW TEST COMPLETED")
    print("="*70)
    return True

def main():
    print("=" * 60)
    print("  PCA9548A + ESP32 Auto-Detection & Test")
    print("  Supports: ESP-B, ESP-C, ESP-E (3-Flow Visualizer)")
    print("=" * 60)
    
    try:
        # Init I2C bus
        bus = smbus2.SMBus(I2C_BUS)
        print(f"✅ I2C Bus {I2C_BUS} initialized")
        
        # Step 1: Check PCA9548A
        print("\n--- Step 1: Check PCA9548A Multiplexer ---")
        devices = scan_i2c_devices(bus)
        
        if PCA9548A_ADDR not in devices:
            print(f"❌ PCA9548A not found at 0x{PCA9548A_ADDR:02X}")
            print("   Check wiring: VCC, GND, SDA, SCL")
            return
        
        print(f"✅ PCA9548A found at 0x{PCA9548A_ADDR:02X}")
        
        # Step 2: Auto-detect connected ESP modules
        print("\n--- Step 2: Auto-Detect ESP Modules ---")
        connected_modules = detect_connected_modules(bus, PCA9548A_ADDR, ESP_MODULES)
        
        if not connected_modules:
            print("\n❌ No ESP modules detected!")
            print("   Check ESP module connections and I2C addresses")
            return
        
        print(f"\n✅ Found {len(connected_modules)} module(s): {', '.join(connected_modules)}")
        
        # Step 3: Special detailed test for ESP-E if detected
        if 'ESP-E' in connected_modules:
            print("\n" + "="*60)
            print("  ESP-E DETECTED - Run detailed test? (y/n)")
            print("="*60)
            choice = input("Run detailed ESP-E test? [y/n]: ").strip().lower()
            
            if choice == 'y':
                test_esp_e_detailed(bus, PCA9548A_ADDR)
                
                # Ask to continue with other modules
                print("\n" + "="*60)
                choice = input("Continue testing other modules? [y/n]: ").strip().lower()
                if choice != 'y':
                    print("\nTest completed. Exiting...")
                    bus.write_byte(PCA9548A_ADDR, 0x00)
                    bus.close()
                    return
        
        # Step 4: Test each connected module
        print("\n--- Step 4: Test Each Module ---")
        test_results = {}
        
        for module_id in connected_modules:
            config = ESP_MODULES[module_id]
            
            print(f"\n{'='*60}")
            print(f"  Testing {config['name']}")
            print(f"{'='*60}")
            
            success = test_esp_module(bus, PCA9548A_ADDR, module_id, config)
            test_results[module_id] = success
            
            time.sleep(0.5)
        
        # Step 5: Summary
        print("\n" + "=" * 60)
        print("  FINAL TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for module_id in connected_modules:
            config = ESP_MODULES[module_id]
            status = "✅ PASS" if test_results[module_id] else "❌ FAIL"
            print(f"  {config['name']:<40} {status}")
            
            if test_results[module_id]:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"  Total: {passed} PASSED, {failed} FAILED")
        print("=" * 60)
        
        if failed == 0:
            print("  ✅ ALL TESTS PASSED!")
            print("  All connected ESP modules are communicating correctly!")
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
