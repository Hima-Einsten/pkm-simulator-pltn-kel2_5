#!/usr/bin/env python3
"""
Test script untuk simulasi startup sequence reaktor PWR
Mensimulasikan urutan startup yang benar:
1. Secondary & Tertiary flow ON dulu (pendingin siap)
2. Setelah stabil, Primary flow ON (reaktor mulai)
"""

import smbus2
import time
import struct
import sys

# Konfigurasi
I2C_BUS = 1
PCA9548A_ADDR = 0x70
ESP_E_ADDR = 0x0A  # ESP-E now handles all 3 flows
CHANNEL = 2

# Pump Status Constants
PUMP_OFF = 0
PUMP_STARTING = 1
PUMP_ON = 2
PUMP_SHUTTING_DOWN = 3

def select_channel(bus, channel):
    """Select PCA9548A channel"""
    channel_mask = 1 << channel
    bus.write_byte(PCA9548A_ADDR, channel_mask)
    time.sleep(0.05)

def send_all_flows(bus, pressure_p, status_p, pressure_s, status_s, pressure_t, status_t):
    """
    Send data untuk 3 aliran sekaligus ke ESP-E
    
    Args:
        pressure_p: Primary pressure (bar)
        status_p: Primary pump status (0-3)
        pressure_s: Secondary pressure (bar)
        status_s: Secondary pump status (0-3)
        pressure_t: Tertiary pressure (bar)
        status_t: Tertiary pump status (0-3)
    """
    try:
        # Pack data: 3 x (float + uint8) = 15 bytes
        data = struct.pack('fBfBfB', 
                          pressure_p, status_p,
                          pressure_s, status_s,
                          pressure_t, status_t)
        
        print(f"\n📤 Sending to ESP-E (0x{ESP_E_ADDR:02X}):")
        print(f"   Primary:   P={pressure_p:6.1f} bar, Status={status_p} ({get_status_name(status_p)})")
        print(f"   Secondary: P={pressure_s:6.1f} bar, Status={status_s} ({get_status_name(status_s)})")
        print(f"   Tertiary:  P={pressure_t:6.1f} bar, Status={status_t} ({get_status_name(status_t)})")
        
        # Write to ESP-E
        bus.write_i2c_block_data(ESP_E_ADDR, 0x00, list(data))
        
        time.sleep(0.2)
        
        # Read response
        response = bus.read_i2c_block_data(ESP_E_ADDR, 0x00, 2)
        anim_speed = response[0]
        led_count = response[1]
        
        print(f"   ✅ Response: animation_speed={anim_speed}, led_count={led_count}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def get_status_name(status):
    """Get pump status name"""
    names = {0: "OFF", 1: "STARTING", 2: "ON", 3: "SHUTTING_DOWN"}
    return names.get(status, "UNKNOWN")

def reactor_startup_sequence(bus):
    """
    Simulasi startup reaktor PWR yang benar
    """
    print("\n" + "="*70)
    print("  PWR REACTOR STARTUP SEQUENCE SIMULATION")
    print("="*70)
    print("\n🔵 Phase 1: Initial State - All Systems OFF")
    print("="*70)
    
    # Phase 1: All OFF
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    time.sleep(3)
    
    # Phase 2: Start Secondary & Tertiary first (cooling loops)
    print("\n🟢 Phase 2: Start Cooling Loops (Secondary & Tertiary)")
    print("="*70)
    print("⚠️  PRIMARY MUST STAY OFF until cooling is ready!")
    
    print("\n>>> Starting Tertiary Pump (Condenser Cooling)...")
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 10.0, PUMP_STARTING)
    time.sleep(5)
    
    print("\n>>> Tertiary Pump RUNNING")
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 15.0, PUMP_ON)
    time.sleep(3)
    
    print("\n>>> Starting Secondary Pump (Steam Generator Cooling)...")
    send_all_flows(bus, 0.0, PUMP_OFF, 20.0, PUMP_STARTING, 15.0, PUMP_ON)
    time.sleep(5)
    
    print("\n>>> Secondary Pump RUNNING")
    send_all_flows(bus, 0.0, PUMP_OFF, 50.0, PUMP_ON, 15.0, PUMP_ON)
    time.sleep(3)
    
    # Phase 3: Cooling stable, ready for primary
    print("\n🔴 Phase 3: Cooling Stable - Ready for Primary Loop")
    print("="*70)
    print("✅ Secondary & Tertiary running stable")
    print("✅ Heat removal path established")
    print("✅ Safe to start Primary loop")
    
    time.sleep(2)
    
    print("\n>>> Starting Primary Pump (Reactor Coolant)...")
    send_all_flows(bus, 50.0, PUMP_STARTING, 50.0, PUMP_ON, 15.0, PUMP_ON)
    time.sleep(5)
    
    print("\n>>> Primary Pump RUNNING")
    send_all_flows(bus, 155.0, PUMP_ON, 50.0, PUMP_ON, 15.0, PUMP_ON)
    time.sleep(3)
    
    # Phase 4: Normal operation
    print("\n⚡ Phase 4: NORMAL OPERATION")
    print("="*70)
    print("✅ All cooling loops operational")
    print("✅ Reactor can now be brought to power")
    
    for i in range(10):
        send_all_flows(bus, 155.0, PUMP_ON, 50.0, PUMP_ON, 15.0, PUMP_ON)
        time.sleep(2)
    
    # Phase 5: Shutdown sequence (reverse order)
    print("\n🟡 Phase 5: SHUTDOWN SEQUENCE")
    print("="*70)
    print("⚠️  Must shutdown in REVERSE order!")
    
    print("\n>>> Shutting down Primary Pump first...")
    send_all_flows(bus, 155.0, PUMP_SHUTTING_DOWN, 50.0, PUMP_ON, 15.0, PUMP_ON)
    time.sleep(5)
    
    print("\n>>> Primary Pump OFF (decay heat still needs removal!)")
    send_all_flows(bus, 0.0, PUMP_OFF, 50.0, PUMP_ON, 15.0, PUMP_ON)
    time.sleep(3)
    
    print("\n>>> Waiting for decay heat to dissipate (5 seconds)...")
    time.sleep(5)
    
    print("\n>>> Shutting down Secondary Pump...")
    send_all_flows(bus, 0.0, PUMP_OFF, 50.0, PUMP_SHUTTING_DOWN, 15.0, PUMP_ON)
    time.sleep(5)
    
    print("\n>>> Secondary Pump OFF")
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 15.0, PUMP_ON)
    time.sleep(3)
    
    print("\n>>> Shutting down Tertiary Pump...")
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 15.0, PUMP_SHUTTING_DOWN)
    time.sleep(5)
    
    print("\n>>> Tertiary Pump OFF")
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    time.sleep(3)
    
    print("\n" + "="*70)
    print("  ✅ SHUTDOWN COMPLETE - All systems secured")
    print("="*70)

def wrong_startup_demo(bus):
    """
    Demo WRONG startup (untuk edukasi)
    """
    print("\n" + "="*70)
    print("  ⚠️  WRONG STARTUP SEQUENCE (DEMONSTRATION)")
    print("="*70)
    print("\n❌ What happens if we start Primary FIRST? (DON'T DO THIS!)")
    
    input("\nPress Enter to see what goes wrong...")
    
    print("\n>>> Starting Primary Pump WITHOUT cooling ready...")
    send_all_flows(bus, 50.0, PUMP_STARTING, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    time.sleep(3)
    
    print("\n>>> Primary running but NO HEAT REMOVAL PATH!")
    send_all_flows(bus, 155.0, PUMP_ON, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    time.sleep(3)
    
    print("\n" + "="*70)
    print("  🚨 DANGER: Reactor overheating!")
    print("  🚨 No secondary cooling!")
    print("  🚨 No condenser cooling!")
    print("  🚨 Temperature rising uncontrollably!")
    print("="*70)
    
    print("\n>>> EMERGENCY SHUTDOWN!")
    send_all_flows(bus, 155.0, PUMP_SHUTTING_DOWN, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    time.sleep(2)
    
    send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
    
    print("\n⚠️  This is why startup sequence matters!")
    print("✅ Always start cooling BEFORE reactor heating!")

def manual_control(bus):
    """
    Mode kontrol manual untuk eksperimen
    """
    print("\n" + "="*70)
    print("  MANUAL CONTROL MODE")
    print("="*70)
    print("\nControl format: <P_press> <P_stat> <S_press> <S_stat> <T_press> <T_stat>")
    print("Pump status: 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN")
    print("Example: 155 2 50 2 15 2  (all ON)")
    print("Type 'quit' to exit")
    print("="*70)
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if cmd.lower() == 'quit':
                break
            
            parts = cmd.split()
            if len(parts) != 6:
                print("❌ Need 6 values: P_press P_stat S_press S_stat T_press T_stat")
                continue
            
            pp = float(parts[0])
            ps = int(parts[1])
            sp = float(parts[2])
            ss = int(parts[3])
            tp = float(parts[4])
            ts = int(parts[5])
            
            if not all(0 <= s <= 3 for s in [ps, ss, ts]):
                print("❌ Status must be 0-3")
                continue
            
            send_all_flows(bus, pp, ps, sp, ss, tp, ts)
            
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    print("="*70)
    print("  PWR Reactor Flow Sequence Test")
    print("  ESP-E with 3-Flow Unified Control")
    print("="*70)
    
    try:
        # Init I2C
        bus = smbus2.SMBus(I2C_BUS)
        print(f"✅ I2C Bus {I2C_BUS} initialized")
        
        # Check PCA9548A
        try:
            bus.read_byte(PCA9548A_ADDR)
            print(f"✅ PCA9548A found at 0x{PCA9548A_ADDR:02X}")
        except:
            print(f"❌ PCA9548A not found!")
            return
        
        # Select channel
        select_channel(bus, CHANNEL)
        print(f"✅ Channel {CHANNEL} selected")
        
        # Check ESP-E
        try:
            bus.read_byte(ESP_E_ADDR)
            print(f"✅ ESP-E found at 0x{ESP_E_ADDR:02X}")
        except:
            print(f"❌ ESP-E not found!")
            return
        
        # Menu
        while True:
            print("\n" + "="*70)
            print("  SELECT TEST MODE")
            print("="*70)
            print("  1. Correct Startup Sequence (Educational)")
            print("  2. Wrong Startup Demo (What NOT to do)")
            print("  3. Manual Control Mode")
            print("  4. Exit")
            print("="*70)
            
            choice = input("Select (1-4): ").strip()
            
            if choice == '1':
                reactor_startup_sequence(bus)
            
            elif choice == '2':
                wrong_startup_demo(bus)
            
            elif choice == '3':
                manual_control(bus)
            
            elif choice == '4':
                break
            
            else:
                print("❌ Invalid choice")
        
        # Cleanup
        print("\n🔌 Turning off all flows...")
        send_all_flows(bus, 0.0, PUMP_OFF, 0.0, PUMP_OFF, 0.0, PUMP_OFF)
        
        bus.write_byte(PCA9548A_ADDR, 0x00)
        bus.close()
        print("✅ Test completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        bus.write_byte(PCA9548A_ADDR, 0x00)
        bus.close()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
