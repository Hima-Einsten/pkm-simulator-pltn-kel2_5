#!/usr/bin/env python3
"""
Interactive Test untuk ESP Visualizer dengan Multiplexer
Test berbagai status pompa dan lihat animasi LED secara real-time
"""

import smbus2
import time
import struct
import sys

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70

# ESP Visualizer Configuration
VISUALIZERS = {
    'ESP-E': {
        'name': 'ESP-E (Primary Flow)',
        'channel': 2,
        'address': 0x0A,
        'pump_name': 'Primary Pump'
    },
    'ESP-F': {
        'name': 'ESP-F (Secondary Flow)',
        'channel': 3,
        'address': 0x0B,
        'pump_name': 'Secondary Pump'
    },
    'ESP-G': {
        'name': 'ESP-G (Tertiary Flow)',
        'channel': 4,
        'address': 0x0C,
        'pump_name': 'Tertiary Pump'
    }
}

# Pump Status
PUMP_STATUS = {
    0: {'name': 'OFF', 'desc': 'Pompa mati, LED semua mati'},
    1: {'name': 'STARTING', 'desc': 'Pompa mulai, animasi lambat (300ms)'},
    2: {'name': 'ON', 'desc': 'Pompa jalan penuh, animasi cepat (100ms)'},
    3: {'name': 'SHUTTING_DOWN', 'desc': 'Pompa mati perlahan, animasi sangat lambat (500ms)'}
}

def select_channel(bus, pca_addr, channel):
    """Select PCA9548A channel"""
    try:
        channel_mask = 1 << channel
        bus.write_byte(pca_addr, channel_mask)
        return True
    except Exception as e:
        print(f"❌ Failed to select channel: {e}")
        return False

def send_pump_data(bus, esp_addr, pressure, pump_status):
    """
    Kirim data pressure & pump status ke ESP Visualizer
    Protocol: pressure (float, 4 bytes) + pumpStatus (uint8, 1 byte)
    """
    try:
        data = struct.pack('fB', pressure, pump_status)
        bus.write_i2c_block_data(esp_addr, 0x00, list(data))
        return True
    except Exception as e:
        print(f"❌ Failed to send data: {e}")
        return False

def read_visualizer_data(bus, esp_addr):
    """
    Baca data dari ESP Visualizer
    Returns: (animationSpeed, ledCount)
    """
    try:
        data = bus.read_i2c_block_data(esp_addr, 0x00, 2)
        animation_speed = data[0]
        led_count = data[1]
        return (animation_speed, led_count)
    except Exception as e:
        print(f"❌ Failed to read data: {e}")
        return (None, None)

def test_visualizer_cycle(bus, pca_addr, visualizer_id, config, duration=10):
    """
    Test visualizer dengan cycle status pompa
    """
    name = config['name']
    channel = config['channel']
    esp_addr = config['address']
    pump_name = config['pump_name']
    
    print(f"\n{'='*70}")
    print(f"  Testing {name} - {pump_name}")
    print(f"{'='*70}")
    
    # Select channel
    if not select_channel(bus, pca_addr, channel):
        return False
    
    time.sleep(0.1)
    
    # Test setiap status pompa
    pressure = 150.0  # bar (konstan)
    
    for status, info in PUMP_STATUS.items():
        print(f"\n--- Test Status: {info['name']} ({info['desc']}) ---")
        print(f"⚙️  Sending: pressure={pressure:.1f} bar, pump_status={status}")
        
        # Kirim data
        if not send_pump_data(bus, esp_addr, pressure, status):
            print("❌ Failed to send data")
            continue
        
        time.sleep(0.2)
        
        # Baca response
        anim_speed, led_count = read_visualizer_data(bus, esp_addr)
        
        if anim_speed is not None:
            print(f"✅ Response: animation_speed={anim_speed}, led_count={led_count}")
            print(f"💡 Watch the LEDs! They should show: {info['desc']}")
        else:
            print("❌ No response from ESP")
        
        # Tunggu untuk melihat animasi
        print(f"⏳ Observing animation for {duration} seconds...")
        
        for i in range(duration):
            sys.stdout.write(f"\r   {i+1}/{duration}s ")
            sys.stdout.flush()
            time.sleep(1)
        
        print("\n")
    
    return True

def test_all_visualizers_simultaneously(bus, pca_addr, duration=30):
    """
    Test semua visualizer bersamaan dengan status berbeda
    """
    print(f"\n{'='*70}")
    print(f"  SIMULTANEOUS TEST - All Visualizers Different Status")
    print(f"{'='*70}")
    
    pressure = 150.0
    
    # Set ESP-E: STARTING (lambat)
    print("\n🔵 ESP-E (Primary): Setting to STARTING (slow animation)")
    select_channel(bus, pca_addr, VISUALIZERS['ESP-E']['channel'])
    time.sleep(0.05)
    send_pump_data(bus, VISUALIZERS['ESP-E']['address'], pressure, 1)
    
    # Set ESP-F: ON (cepat)
    print("🟢 ESP-F (Secondary): Setting to ON (fast animation)")
    select_channel(bus, pca_addr, VISUALIZERS['ESP-F']['channel'])
    time.sleep(0.05)
    send_pump_data(bus, VISUALIZERS['ESP-F']['address'], pressure, 2)
    
    # Set ESP-G: SHUTTING_DOWN (sangat lambat)
    print("🟡 ESP-G (Tertiary): Setting to SHUTTING_DOWN (very slow)")
    select_channel(bus, pca_addr, VISUALIZERS['ESP-G']['channel'])
    time.sleep(0.05)
    send_pump_data(bus, VISUALIZERS['ESP-G']['address'], pressure, 3)
    
    print(f"\n💡 All visualizers running with different speeds!")
    print(f"   - ESP-E (Primary): Slow animation (300ms)")
    print(f"   - ESP-F (Secondary): Fast animation (100ms)")
    print(f"   - ESP-G (Tertiary): Very slow animation (500ms)")
    print(f"\n⏳ Observing for {duration} seconds...")
    
    for i in range(duration):
        sys.stdout.write(f"\r   {i+1}/{duration}s ")
        sys.stdout.flush()
        time.sleep(1)
    
    print("\n")

def interactive_control(bus, pca_addr):
    """
    Mode interaktif untuk kontrol manual visualizer
    """
    print(f"\n{'='*70}")
    print(f"  INTERACTIVE CONTROL MODE")
    print(f"{'='*70}")
    print("\nCommands:")
    print("  e <status> - Control ESP-E (Primary), status: 0-3")
    print("  f <status> - Control ESP-F (Secondary), status: 0-3")
    print("  g <status> - Control ESP-G (Tertiary), status: 0-3")
    print("  all <status> - Control all visualizers")
    print("  status - Show all visualizer status")
    print("  quit - Exit")
    print("\nPump Status: 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN")
    print("="*70)
    
    pressure = 150.0
    current_status = {'ESP-E': 0, 'ESP-F': 0, 'ESP-G': 0}
    
    while True:
        try:
            cmd = input("\n> ").strip().lower().split()
            
            if not cmd:
                continue
            
            if cmd[0] == 'quit':
                break
            
            elif cmd[0] == 'status':
                print("\nCurrent Status:")
                for vis_id, status in current_status.items():
                    print(f"  {vis_id}: {PUMP_STATUS[status]['name']}")
            
            elif cmd[0] in ['e', 'f', 'g']:
                if len(cmd) < 2:
                    print("❌ Usage: e/f/g <status>")
                    continue
                
                try:
                    status = int(cmd[1])
                    if status < 0 or status > 3:
                        print("❌ Status must be 0-3")
                        continue
                    
                    vis_map = {'e': 'ESP-E', 'f': 'ESP-F', 'g': 'ESP-G'}
                    vis_id = vis_map[cmd[0]]
                    config = VISUALIZERS[vis_id]
                    
                    select_channel(bus, pca_addr, config['channel'])
                    time.sleep(0.05)
                    
                    if send_pump_data(bus, config['address'], pressure, status):
                        current_status[vis_id] = status
                        print(f"✅ {vis_id} set to {PUMP_STATUS[status]['name']}")
                    
                except ValueError:
                    print("❌ Invalid status number")
            
            elif cmd[0] == 'all':
                if len(cmd) < 2:
                    print("❌ Usage: all <status>")
                    continue
                
                try:
                    status = int(cmd[1])
                    if status < 0 or status > 3:
                        print("❌ Status must be 0-3")
                        continue
                    
                    for vis_id, config in VISUALIZERS.items():
                        select_channel(bus, pca_addr, config['channel'])
                        time.sleep(0.05)
                        send_pump_data(bus, config['address'], pressure, status)
                        current_status[vis_id] = status
                    
                    print(f"✅ All visualizers set to {PUMP_STATUS[status]['name']}")
                
                except ValueError:
                    print("❌ Invalid status number")
            
            else:
                print("❌ Unknown command")
        
        except KeyboardInterrupt:
            print("\n")
            break

def main():
    print("=" * 70)
    print("  ESP Visualizer Interactive Test (with Multiplexer)")
    print("  Test LED flow animation for ESP-E, ESP-F, ESP-G")
    print("=" * 70)
    
    try:
        # Init I2C
        bus = smbus2.SMBus(I2C_BUS)
        print(f"✅ I2C Bus {I2C_BUS} initialized")
        
        # Check PCA9548A
        try:
            bus.read_byte(PCA9548A_ADDR)
            print(f"✅ PCA9548A found at 0x{PCA9548A_ADDR:02X}")
        except:
            print(f"❌ PCA9548A not found at 0x{PCA9548A_ADDR:02X}")
            return
        
        # Menu
        while True:
            print("\n" + "="*70)
            print("  SELECT TEST MODE")
            print("="*70)
            print("  1. Test ESP-E (Primary Flow) - Complete cycle")
            print("  2. Test ESP-F (Secondary Flow) - Complete cycle")
            print("  3. Test ESP-G (Tertiary Flow) - Complete cycle")
            print("  4. Test All Visualizers (different speeds simultaneously)")
            print("  5. Interactive Control Mode")
            print("  6. Exit")
            print("="*70)
            
            choice = input("Select option (1-6): ").strip()
            
            if choice == '1':
                test_visualizer_cycle(bus, PCA9548A_ADDR, 'ESP-E', VISUALIZERS['ESP-E'])
            
            elif choice == '2':
                test_visualizer_cycle(bus, PCA9548A_ADDR, 'ESP-F', VISUALIZERS['ESP-F'])
            
            elif choice == '3':
                test_visualizer_cycle(bus, PCA9548A_ADDR, 'ESP-G', VISUALIZERS['ESP-G'])
            
            elif choice == '4':
                test_all_visualizers_simultaneously(bus, PCA9548A_ADDR)
            
            elif choice == '5':
                interactive_control(bus, PCA9548A_ADDR)
            
            elif choice == '6':
                break
            
            else:
                print("❌ Invalid option")
        
        # Cleanup - matikan semua
        print("\n🔌 Turning off all visualizers...")
        for vis_id, config in VISUALIZERS.items():
            select_channel(bus, PCA9548A_ADDR, config['channel'])
            time.sleep(0.05)
            send_pump_data(bus, config['address'], 0.0, 0)  # Status OFF
        
        bus.write_byte(PCA9548A_ADDR, 0x00)  # Disable all channels
        bus.close()
        
        print("✅ Test completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
