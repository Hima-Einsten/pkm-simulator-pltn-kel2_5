#!/usr/bin/env python3
"""
I2C Bus Reset Utility
Force reset I2C bus when it's locked

Usage:
    python3 reset_i2c_bus.py
"""

import smbus2
import time
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_i2c_multiplexers():
    """Reset both TCA9548A multiplexers"""
    logger.info("="*60)
    logger.info("I2C Bus Reset Utility")
    logger.info("="*60)
    
    try:
        bus = smbus2.SMBus(1)
        logger.info("✅ I2C bus 1 opened")
    except Exception as e:
        logger.error(f"❌ Failed to open I2C bus: {e}")
        return False
    
    success_count = 0
    
    # Reset TCA9548A #1 (0x70)
    try:
        logger.info("\nResetting TCA9548A #1 (0x70)...")
        bus.write_byte(0x70, 0x00)  # Disable all channels
        time.sleep(0.1)
        
        # Verify
        result = bus.read_byte(0x70)
        if result == 0x00:
            logger.info("  ✅ TCA9548A #1 reset successful (all channels disabled)")
            success_count += 1
        else:
            logger.warning(f"  ⚠️  TCA9548A #1 responded but value unexpected: 0x{result:02X}")
    except Exception as e:
        logger.error(f"  ❌ Failed to reset TCA9548A #1: {e}")
    
    # Reset TCA9548A #2 (0x71)
    try:
        logger.info("\nResetting TCA9548A #2 (0x71)...")
        bus.write_byte(0x71, 0x00)  # Disable all channels
        time.sleep(0.1)
        
        # Verify
        result = bus.read_byte(0x71)
        if result == 0x00:
            logger.info("  ✅ TCA9548A #2 reset successful (all channels disabled)")
            success_count += 1
        else:
            logger.warning(f"  ⚠️  TCA9548A #2 responded but value unexpected: 0x{result:02X}")
    except Exception as e:
        logger.error(f"  ❌ Failed to reset TCA9548A #2: {e}")
    
    # Close bus
    try:
        bus.close()
        logger.info("\n✅ I2C bus closed cleanly")
    except Exception as e:
        logger.error(f"❌ Error closing bus: {e}")
    
    # Summary
    logger.info("\n" + "="*60)
    if success_count == 2:
        logger.info("✅ SUCCESS - Both multiplexers reset")
        logger.info("   You can now run raspi_main_panel.py")
        return True
    elif success_count == 1:
        logger.warning("⚠️  PARTIAL SUCCESS - Only one multiplexer reset")
        logger.warning("   Check wiring and power for the other multiplexer")
        return False
    else:
        logger.error("❌ FAILED - No multiplexers reset")
        logger.error("   Check:")
        logger.error("   1. I2C bus enabled (sudo raspi-config)")
        logger.error("   2. Multiplexers powered (3.3V)")
        logger.error("   3. SDA/SCL connections")
        logger.error("   4. Pull-up resistors (4.7kΩ)")
        return False


def scan_i2c_bus():
    """Quick I2C bus scan"""
    logger.info("\nScanning I2C bus for devices...")
    
    try:
        bus = smbus2.SMBus(1)
    except Exception as e:
        logger.error(f"❌ Cannot open I2C bus: {e}")
        return []
    
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
        except:
            pass
    
    bus.close()
    
    if devices:
        logger.info(f"✅ Found {len(devices)} devices:")
        for addr in devices:
            name = get_device_name(addr)
            logger.info(f"  - 0x{addr:02X}: {name}")
    else:
        logger.error("❌ No I2C devices found!")
    
    return devices


def get_device_name(addr):
    """Get friendly name for I2C address"""
    names = {
        0x08: "ESP-BC",
        0x0A: "ESP-E",
        0x3C: "OLED",
        0x70: "TCA9548A #1",
        0x71: "TCA9548A #2",
    }
    return names.get(addr, "Unknown")


def force_esp_reset():
    """Try to wake up ESP slaves"""
    logger.info("\n" + "="*60)
    logger.info("Attempting to wake up ESP slaves...")
    logger.info("="*60)
    
    try:
        bus = smbus2.SMBus(1)
    except Exception as e:
        logger.error(f"❌ Cannot open I2C bus: {e}")
        return False
    
    # Try ESP-BC (via MUX #1, Channel 0)
    try:
        logger.info("\nWaking ESP-BC (0x08)...")
        
        # Select MUX #1 Channel 0
        bus.write_byte(0x70, 0x01)
        time.sleep(0.05)
        
        # Send dummy write to ESP-BC
        dummy_data = [0] * 12
        bus.write_i2c_block_data(0x08, 0x00, dummy_data)
        time.sleep(0.02)
        
        # Try to read
        response = bus.read_i2c_block_data(0x08, 0x00, 20)
        logger.info(f"  ✅ ESP-BC responding (received {len(response)} bytes)")
        
    except Exception as e:
        logger.warning(f"  ⚠️  ESP-BC not responding: {e}")
    
    # Try ESP-E (via MUX #2, Channel 0)
    try:
        logger.info("\nWaking ESP-E (0x0A)...")
        
        # Disable MUX #1 first
        bus.write_byte(0x70, 0x00)
        time.sleep(0.02)
        
        # Select MUX #2 Channel 0
        bus.write_byte(0x71, 0x01)
        time.sleep(0.05)
        
        # Send dummy write to ESP-E
        dummy_data = [0] * 20
        bus.write_i2c_block_data(0x0A, 0x00, dummy_data)
        time.sleep(0.02)
        
        # Try to read
        response = bus.read_i2c_block_data(0x0A, 0x00, 2)
        logger.info(f"  ✅ ESP-E responding (received {len(response)} bytes)")
        
    except Exception as e:
        logger.warning(f"  ⚠️  ESP-E not responding: {e}")
    
    # Disable all channels
    try:
        bus.write_byte(0x70, 0x00)
        bus.write_byte(0x71, 0x00)
    except:
        pass
    
    bus.close()
    return True


def main():
    """Main function"""
    print("\n" + "="*60)
    print("I2C Bus Reset Utility - PLTN Simulator")
    print("="*60)
    print("\nThis script will:")
    print("  1. Scan I2C bus for devices")
    print("  2. Reset both TCA9548A multiplexers")
    print("  3. Attempt to wake up ESP slaves")
    print("  4. Prepare system for fresh start")
    print("\n" + "="*60)
    
    input("\nPress ENTER to continue or Ctrl+C to cancel...")
    
    # Step 1: Scan bus
    devices = scan_i2c_bus()
    
    # Step 2: Reset multiplexers
    success = reset_i2c_multiplexers()
    
    # Step 3: Wake up ESPs
    if 0x70 in devices and 0x71 in devices:
        force_esp_reset()
    
    # Final message
    logger.info("\n" + "="*60)
    logger.info("RESET COMPLETE")
    logger.info("="*60)
    
    if success:
        logger.info("\n✅ I2C bus is now ready")
        logger.info("   You can run: python3 raspi_main_panel.py")
    else:
        logger.error("\n❌ Reset incomplete")
        logger.error("   Check hardware connections and try again")
        logger.error("   Or run: python3 test_i2c_scan.py for detailed diagnostics")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
