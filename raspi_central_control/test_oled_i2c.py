"""
Test I2C Communication and OLED Display Update
PLTN Simulator - TCA9548A + 9 OLED Test Script

Usage:
    python test_oled_i2c.py

Features:
- Scan TCA9548A multiplexers
- Test each OLED channel
- Display test patterns and text
- Verify I2C communication

Author: System Architect
Date: 2024-12-10
"""

import time
import smbus2
import logging
from typing import List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# Configuration
# ============================================
I2C_BUS = 1
TCA9548A_1_ADDRESS = 0x70  # Main multiplexer
TCA9548A_2_ADDRESS = 0x71  # Secondary multiplexer
OLED_ADDRESS = 0x3C

# Channel mapping for 9 OLEDs
OLED_CHANNELS = [
    # TCA9548A #1 (0x70)
    (0x70, 0, "ESP-BC"),           # Not OLED, but ESP32
    (0x70, 1, "Pressurizer"),
    (0x70, 2, "Pump Primary"),
    (0x70, 3, "Pump Secondary"),
    (0x70, 4, "Pump Tertiary"),
    (0x70, 5, "Safety Rod"),
    (0x70, 6, "Shim Rod"),
    (0x70, 7, "Regulating Rod"),
    
    # TCA9548A #2 (0x71)
    (0x71, 0, "ESP-E"),            # Not OLED, but ESP32
    (0x71, 1, "Thermal Power"),
    (0x71, 2, "System Status"),
]


# ============================================
# TCA9548A Control Functions
# ============================================
class TCA9548AController:
    """Simple TCA9548A multiplexer controller"""
    
    def __init__(self, bus_number: int = 1):
        self.bus = smbus2.SMBus(bus_number)
        logger.info(f"I2C Bus {bus_number} initialized")
    
    def select_channel(self, mux_addr: int, channel: int) -> bool:
        """
        Select a channel on TCA9548A
        
        Args:
            mux_addr: 0x70 or 0x71
            channel: 0-7
            
        Returns:
            True if success, False otherwise
        """
        if channel < 0 or channel > 7:
            logger.error(f"Invalid channel {channel}. Must be 0-7")
            return False
        
        try:
            channel_mask = 1 << channel
            self.bus.write_byte(mux_addr, channel_mask)
            logger.debug(f"Selected MUX 0x{mux_addr:02X} Channel {channel}")
            time.sleep(0.001)  # 1ms settle time
            return True
        except Exception as e:
            logger.error(f"Failed to select channel: {e}")
            return False
    
    def disable_all_channels(self, mux_addr: int) -> bool:
        """Disable all channels on a multiplexer"""
        try:
            self.bus.write_byte(mux_addr, 0x00)
            logger.debug(f"All channels disabled on MUX 0x{mux_addr:02X}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable channels: {e}")
            return False
    
    def scan_channel(self, mux_addr: int, channel: int) -> List[int]:
        """
        Scan for I2C devices on a specific channel
        
        Returns:
            List of device addresses found
        """
        devices = []
        
        if not self.select_channel(mux_addr, channel):
            return devices
        
        # Scan I2C addresses 0x03 to 0x77
        for addr in range(0x03, 0x78):
            try:
                self.bus.read_byte(addr)
                devices.append(addr)
            except:
                pass
        
        return devices
    
    def scan_all_channels(self, mux_addr: int) -> dict:
        """
        Scan all 8 channels on a multiplexer
        
        Returns:
            Dictionary mapping channel -> list of addresses
        """
        results = {}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scanning TCA9548A at 0x{mux_addr:02X}")
        logger.info(f"{'='*60}")
        
        for channel in range(8):
            devices = self.scan_channel(mux_addr, channel)
            if devices:
                results[channel] = devices
                device_list = ", ".join([f"0x{d:02X}" for d in devices])
                logger.info(f"  Channel {channel}: {device_list}")
            else:
                logger.info(f"  Channel {channel}: No devices found")
        
        self.disable_all_channels(mux_addr)
        return results
    
    def close(self):
        """Close I2C bus"""
        try:
            self.bus.close()
            logger.info("I2C bus closed")
        except Exception as e:
            logger.error(f"Error closing I2C bus: {e}")


# ============================================
# OLED Display Functions (using luma.oled)
# ============================================
def test_oled_display(mux_controller: TCA9548AController, 
                      mux_addr: int, 
                      channel: int, 
                      display_name: str) -> bool:
    """
    Test OLED display on a specific channel
    
    Args:
        mux_controller: TCA9548A controller
        mux_addr: Multiplexer address
        channel: Channel number
        display_name: Name to display on OLED
        
    Returns:
        True if test successful
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing OLED: {display_name}")
    logger.info(f"MUX: 0x{mux_addr:02X}, Channel: {channel}")
    logger.info(f"{'='*60}")
    
    # Select channel
    if not mux_controller.select_channel(mux_addr, channel):
        logger.error("Failed to select channel")
        return False
    
    # Check if OLED is present
    devices = mux_controller.scan_channel(mux_addr, channel)
    if OLED_ADDRESS not in devices:
        logger.warning(f"OLED not found at 0x{OLED_ADDRESS:02X}")
        return False
    
    logger.info(f"✓ OLED found at 0x{OLED_ADDRESS:02X}")
    
    # Try to initialize OLED with luma.oled
    try:
        from luma.core.interface.serial import i2c
        from luma.core.render import canvas
        from luma.oled.device import ssd1306
        from PIL import ImageFont
        
        # Create I2C interface (direct, no multiplexer control needed)
        # luma will use the currently selected channel
        serial = i2c(port=I2C_BUS, address=OLED_ADDRESS)
        device = ssd1306(serial, width=128, height=64)
        
        # Clear display
        device.clear()
        time.sleep(0.1)
        
        # Test 1: Display text
        logger.info("Test 1: Displaying text...")
        with canvas(device) as draw:
            # Title
            draw.text((0, 0), "PLTN SIMULATOR", fill="white")
            draw.text((0, 16), display_name, fill="white")
            draw.text((0, 32), "I2C: OK", fill="white")
            draw.text((0, 48), f"Ch: {channel}", fill="white")
        
        time.sleep(2)
        
        # Test 2: Draw rectangle border
        logger.info("Test 2: Drawing shapes...")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 20), "Test Pattern", fill="white")
            draw.text((10, 35), "SUCCESS", fill="white")
        
        time.sleep(2)
        
        # Test 3: Simulated data display
        logger.info("Test 3: Displaying simulated data...")
        for i in range(3):
            with canvas(device) as draw:
                draw.text((0, 0), display_name, fill="white")
                draw.text((0, 16), f"Value: {50 + i*10}", fill="white")
                draw.text((0, 32), f"Status: ON", fill="white")
                draw.text((0, 48), f"Count: {i+1}/3", fill="white")
            time.sleep(1)
        
        logger.info(f"✓ OLED '{display_name}' test PASSED")
        device.cleanup()
        return True
        
    except ImportError:
        logger.error("luma.oled not installed!")
        logger.error("Install with: pip install luma.oled")
        return False
    except Exception as e:
        logger.error(f"OLED test failed: {e}")
        return False


# ============================================
# Simple OLED Test (without luma.oled)
# ============================================
def simple_oled_test(mux_controller: TCA9548AController,
                     mux_addr: int,
                     channel: int,
                     display_name: str) -> bool:
    """
    Simple OLED test using raw I2C commands
    (Works without luma.oled library)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Simple Test: {display_name}")
    logger.info(f"MUX: 0x{mux_addr:02X}, Channel: {channel}")
    logger.info(f"{'='*60}")
    
    # Select channel
    if not mux_controller.select_channel(mux_addr, channel):
        return False
    
    # Check if device responds
    try:
        mux_controller.bus.read_byte(OLED_ADDRESS)
        logger.info(f"✓ Device responds at 0x{OLED_ADDRESS:02X}")
        
        # Try to send initialization command
        # This is SSD1306 display ON command
        mux_controller.bus.write_byte_data(OLED_ADDRESS, 0x00, 0xAF)
        logger.info("✓ Sent display ON command")
        
        return True
    except Exception as e:
        logger.error(f"Device not responding: {e}")
        return False


# ============================================
# Main Test Functions
# ============================================
def test_multiplexer_detection():
    """Test 1: Detect TCA9548A multiplexers"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: TCA9548A Detection")
    logger.info("="*60)
    
    try:
        bus = smbus2.SMBus(I2C_BUS)
        
        # Test TCA9548A #1 (0x70)
        try:
            bus.read_byte(TCA9548A_1_ADDRESS)
            logger.info(f"✓ TCA9548A #1 found at 0x{TCA9548A_1_ADDRESS:02X}")
            mux1_ok = True
        except:
            logger.error(f"✗ TCA9548A #1 NOT found at 0x{TCA9548A_1_ADDRESS:02X}")
            mux1_ok = False
        
        # Test TCA9548A #2 (0x71)
        try:
            bus.read_byte(TCA9548A_2_ADDRESS)
            logger.info(f"✓ TCA9548A #2 found at 0x{TCA9548A_2_ADDRESS:02X}")
            mux2_ok = True
        except:
            logger.error(f"✗ TCA9548A #2 NOT found at 0x{TCA9548A_2_ADDRESS:02X}")
            mux2_ok = False
        
        bus.close()
        return mux1_ok and mux2_ok
        
    except Exception as e:
        logger.error(f"I2C bus error: {e}")
        return False


def test_channel_scanning():
    """Test 2: Scan all channels on both multiplexers"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Channel Scanning")
    logger.info("="*60)
    
    try:
        mux = TCA9548AController(I2C_BUS)
        
        # Scan TCA9548A #1
        results1 = mux.scan_all_channels(TCA9548A_1_ADDRESS)
        
        # Scan TCA9548A #2
        results2 = mux.scan_all_channels(TCA9548A_2_ADDRESS)
        
        mux.close()
        
        return len(results1) > 0 or len(results2) > 0
        
    except Exception as e:
        logger.error(f"Scanning error: {e}")
        return False


def test_all_oleds(use_luma: bool = True):
    """Test 3: Test all OLED displays"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: OLED Display Tests")
    logger.info("="*60)
    
    try:
        mux = TCA9548AController(I2C_BUS)
        
        results = []
        oled_count = 0
        
        for mux_addr, channel, name in OLED_CHANNELS:
            # Skip ESP32 channels (0)
            if channel == 0:
                logger.info(f"\nSkipping {name} (ESP32, not OLED)")
                continue
            
            oled_count += 1
            
            if use_luma:
                success = test_oled_display(mux, mux_addr, channel, name)
            else:
                success = simple_oled_test(mux, mux_addr, channel, name)
            
            results.append((name, success))
            
            if success:
                logger.info(f"✓ {name}: PASS")
            else:
                logger.warning(f"✗ {name}: FAIL")
            
            time.sleep(0.5)
        
        mux.close()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        logger.info(f"Total OLEDs tested: {total}")
        logger.info(f"Passed: {passed}/{total}")
        logger.info(f"Failed: {total - passed}/{total}")
        logger.info(f"Success rate: {passed/total*100:.1f}%")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"OLED test error: {e}")
        return False


def run_all_tests():
    """Run all tests sequentially"""
    logger.info("\n" + "#"*60)
    logger.info("# PLTN SIMULATOR - I2C & OLED Test Suite")
    logger.info("# TCA9548A + 9 OLED Configuration Test")
    logger.info("#"*60)
    
    results = []
    
    # Test 1: Multiplexer Detection
    test1 = test_multiplexer_detection()
    results.append(("Multiplexer Detection", test1))
    
    if not test1:
        logger.error("\n⚠️  Multiplexers not detected! Check wiring:")
        logger.error("   - VCC → 3.3V")
        logger.error("   - GND → GND")
        logger.error("   - SDA → GPIO 2")
        logger.error("   - SCL → GPIO 3")
        logger.error("   - A0/A1/A2 → GND (for 0x70) or A0→VCC (for 0x71)")
        return
    
    # Test 2: Channel Scanning
    test2 = test_channel_scanning()
    results.append(("Channel Scanning", test2))
    
    # Test 3: OLED Tests
    # Check if luma.oled is available
    try:
        import luma.oled
        logger.info("\n✓ luma.oled library detected")
        use_luma = True
    except ImportError:
        logger.warning("\n⚠️  luma.oled not installed - using simple test")
        logger.info("Install with: pip install luma.oled")
        use_luma = False
    
    test3 = test_all_oleds(use_luma=use_luma)
    results.append(("OLED Display Tests", test3))
    
    # Final Summary
    logger.info("\n" + "#"*60)
    logger.info("# FINAL TEST SUMMARY")
    logger.info("#"*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:.<40} {status}")
    
    total_passed = sum(1 for _, result in results if result)
    logger.info(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        logger.info("\n🎉 ALL TESTS PASSED! System ready for operation.")
    else:
        logger.warning("\n⚠️  Some tests failed. Check hardware connections.")


# ============================================
# Interactive Menu
# ============================================
def interactive_menu():
    """Interactive test menu"""
    while True:
        print("\n" + "="*60)
        print("PLTN SIMULATOR - I2C Test Menu")
        print("="*60)
        print("1. Test TCA9548A Detection")
        print("2. Scan All Channels")
        print("3. Test All OLEDs (Full)")
        print("4. Test Specific OLED")
        print("5. Run All Tests")
        print("0. Exit")
        print("="*60)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            test_multiplexer_detection()
        elif choice == "2":
            test_channel_scanning()
        elif choice == "3":
            test_all_oleds()
        elif choice == "4":
            print("\nAvailable OLEDs:")
            for i, (mux, ch, name) in enumerate(OLED_CHANNELS):
                if ch != 0:  # Skip ESP32
                    print(f"  {i}. {name} (MUX 0x{mux:02X}, Ch {ch})")
            
            try:
                idx = int(input("\nSelect OLED number: "))
                mux_addr, channel, name = OLED_CHANNELS[idx]
                if channel == 0:
                    print("That's an ESP32, not an OLED!")
                else:
                    mux = TCA9548AController(I2C_BUS)
                    test_oled_display(mux, mux_addr, channel, name)
                    mux.close()
            except (ValueError, IndexError):
                print("Invalid selection!")
        elif choice == "5":
            run_all_tests()
        elif choice == "0":
            print("\nExiting...")
            break
        else:
            print("Invalid option!")


# ============================================
# Main Entry Point
# ============================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--menu":
        interactive_menu()
    else:
        run_all_tests()
