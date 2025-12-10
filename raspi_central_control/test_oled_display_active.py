"""
Test OLED Display with ACTIVE Visual Output
PLTN Simulator - TCA9548A + 9 OLED Test Script

This script will ACTUALLY LIGHT UP the OLEDs and display text!

Usage:
    python test_oled_display_active.py

Requirements:
    pip install smbus2 luma.oled pillow

Author: System Architect
Date: 2024-12-10
"""

import time
import smbus2
import logging
from typing import Optional

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
TCA9548A_1_ADDRESS = 0x70
TCA9548A_2_ADDRESS = 0x71
OLED_ADDRESS = 0x3C

# OLED Configuration (9 units)
OLED_LIST = [
    # TCA9548A #1 (0x70)
    (0x70, 1, "PRESSURIZER", "Tekanan: 155 bar"),
    (0x70, 2, "PUMP PRIMARY", "Status: ON"),
    (0x70, 3, "PUMP SECONDARY", "Status: ON"),
    (0x70, 4, "PUMP TERTIARY", "Status: ON"),
    (0x70, 5, "SAFETY ROD", "Position: 45%"),
    (0x70, 6, "SHIM ROD", "Position: 60%"),
    (0x70, 7, "REGULATING ROD", "Position: 75%"),
    
    # TCA9548A #2 (0x71)
    (0x71, 1, "THERMAL POWER", "Power: 3500 kW"),
    (0x71, 2, "SYSTEM STATUS", "State: RUNNING"),
]


# ============================================
# TCA9548A Controller
# ============================================
class TCA9548AController:
    """TCA9548A Multiplexer Controller"""
    
    def __init__(self, bus_number: int = 1):
        self.bus = smbus2.SMBus(bus_number)
        logger.info(f"I2C Bus {bus_number} initialized")
    
    def select_channel(self, mux_addr: int, channel: int) -> bool:
        """Select a channel on TCA9548A"""
        if channel < 0 or channel > 7:
            logger.error(f"Invalid channel {channel}")
            return False
        
        try:
            channel_mask = 1 << channel
            self.bus.write_byte(mux_addr, channel_mask)
            time.sleep(0.002)  # 2ms settle time
            logger.debug(f"Selected MUX 0x{mux_addr:02X} Ch{channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to select channel: {e}")
            return False
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()


# ============================================
# OLED Display Manager
# ============================================
class OLEDDisplayManager:
    """Manage OLED displays with luma.oled library"""
    
    def __init__(self, mux_controller: TCA9548AController):
        self.mux = mux_controller
        logger.info("OLED Display Manager initialized")
    
    def test_single_oled(self, mux_addr: int, channel: int, 
                        title: str, content: str) -> bool:
        """
        Test and display content on a single OLED
        
        Args:
            mux_addr: Multiplexer address (0x70 or 0x71)
            channel: Channel number (0-7)
            title: Title text to display
            content: Content text to display
            
        Returns:
            True if successful
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing OLED: {title}")
        logger.info(f"MUX: 0x{mux_addr:02X}, Channel: {channel}")
        logger.info(f"{'='*60}")
        
        # Select channel
        if not self.mux.select_channel(mux_addr, channel):
            logger.error("❌ Failed to select channel")
            return False
        
        try:
            from luma.core.interface.serial import i2c
            from luma.core.render import canvas
            from luma.oled.device import ssd1306
            from PIL import ImageFont
            
            # Create I2C serial interface
            serial = i2c(port=I2C_BUS, address=OLED_ADDRESS)
            
            # Create SSD1306 device (128x64)
            device = ssd1306(serial, width=128, height=64)
            
            logger.info("✓ OLED device initialized")
            
            # Clear display first
            device.clear()
            time.sleep(0.1)
            
            # Test Pattern 1: Text Display
            logger.info("Drawing test pattern 1: Text...")
            with canvas(device) as draw:
                # Border
                draw.rectangle(device.bounding_box, outline="white", fill="black")
                
                # Title
                draw.text((4, 4), "PLTN SIMULATOR", fill="white")
                draw.line((4, 14, 124, 14), fill="white")
                
                # Main content
                draw.text((4, 20), title, fill="white")
                draw.text((4, 36), content, fill="white")
                
                # Footer
                draw.text((4, 52), f"Ch{channel} 0x{mux_addr:02X}", fill="white")
            
            logger.info("✓ Test pattern 1 displayed")
            time.sleep(2)
            
            # Test Pattern 2: Animated Counter
            logger.info("Drawing test pattern 2: Animation...")
            for i in range(5):
                with canvas(device) as draw:
                    # Border
                    draw.rectangle(device.bounding_box, outline="white", fill="black")
                    
                    # Title
                    draw.text((20, 10), title, fill="white")
                    
                    # Animated counter
                    draw.text((30, 30), f"Count: {i+1}/5", fill="white")
                    
                    # Progress bar
                    progress = int((i + 1) / 5 * 100)
                    bar_width = int(100 * progress / 100)
                    draw.rectangle((14, 50, 114, 58), outline="white", fill="black")
                    draw.rectangle((14, 50, 14 + bar_width, 58), outline="white", fill="white")
                
                time.sleep(0.5)
            
            logger.info("✓ Test pattern 2 displayed")
            
            # Final display: Keep content on screen
            with canvas(device) as draw:
                # Border
                draw.rectangle(device.bounding_box, outline="white", fill="black")
                
                # Title
                draw.text((4, 4), "PLTN SIMULATOR", fill="white")
                draw.line((4, 14, 124, 14), fill="white")
                
                # Main content
                draw.text((4, 20), title, fill="white")
                draw.text((4, 36), content, fill="white")
                
                # Status
                draw.text((4, 52), "STATUS: ACTIVE", fill="white")
            
            logger.info(f"✓ OLED '{title}' TEST PASSED")
            logger.info("✓ Display will stay ON")
            
            # DON'T call device.cleanup() - keep display on!
            # device.cleanup()  # <-- Commented out to keep display active
            
            return True
            
        except ImportError as e:
            logger.error("❌ luma.oled library not installed!")
            logger.error("Install with: pip install luma.oled pillow")
            return False
        except Exception as e:
            logger.error(f"❌ OLED test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============================================
# Main Test Functions
# ============================================
def test_all_oleds_with_display():
    """Test all 9 OLEDs with ACTIVE display"""
    
    logger.info("\n" + "#"*60)
    logger.info("# PLTN SIMULATOR - OLED ACTIVE DISPLAY TEST")
    logger.info("# This will LIGHT UP all OLEDs!")
    logger.info("#"*60)
    
    # Check luma.oled installation
    try:
        import luma.oled
        logger.info("✓ luma.oled library found")
    except ImportError:
        logger.error("❌ luma.oled NOT installed!")
        logger.error("\nPlease install:")
        logger.error("  pip install luma.oled pillow")
        return False
    
    # Initialize controllers
    try:
        mux_controller = TCA9548AController(I2C_BUS)
        oled_manager = OLEDDisplayManager(mux_controller)
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        return False
    
    # Test each OLED
    results = []
    
    for mux_addr, channel, title, content in OLED_LIST:
        success = oled_manager.test_single_oled(mux_addr, channel, title, content)
        results.append((title, success))
        
        if success:
            logger.info(f"✅ {title}: PASS (Display ON)")
        else:
            logger.warning(f"❌ {title}: FAIL")
        
        time.sleep(1)  # Delay between tests
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for title, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{title:.<35} {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    logger.info(f"\nTotal: {passed}/{total} OLEDs working")
    logger.info(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("\n🎉 ALL OLEDS ARE NOW ACTIVE AND DISPLAYING!")
        logger.info("✓ Displays will stay ON")
        logger.info("✓ Check each OLED - they should show content")
    else:
        logger.warning("\n⚠️  Some OLEDs failed. Check:")
        logger.warning("  - Wiring (VCC, GND, SDA, SCL)")
        logger.warning("  - TCA9548A channel connections")
        logger.warning("  - OLED power (must be 3.3V, NOT 5V!)")
    
    # DON'T close bus - keep displays active
    # mux_controller.close()
    
    logger.info("\n✓ Test complete. OLEDs should remain active.")
    logger.info("  Press Ctrl+C to exit and turn off displays.")
    
    return passed == total


def test_single_oled_interactive():
    """Test a single OLED interactively"""
    
    print("\n" + "="*60)
    print("SINGLE OLED TEST")
    print("="*60)
    print("\nAvailable OLEDs:")
    
    for i, (mux, ch, title, content) in enumerate(OLED_LIST):
        print(f"  {i+1}. {title} (MUX 0x{mux:02X}, Ch{ch})")
    
    try:
        choice = int(input("\nSelect OLED number (1-9): "))
        
        if choice < 1 or choice > len(OLED_LIST):
            print("Invalid choice!")
            return
        
        mux_addr, channel, title, content = OLED_LIST[choice - 1]
        
        print(f"\nTesting: {title}")
        print("="*60)
        
        mux_controller = TCA9548AController(I2C_BUS)
        oled_manager = OLEDDisplayManager(mux_controller)
        
        success = oled_manager.test_single_oled(mux_addr, channel, title, content)
        
        if success:
            print(f"\n✅ {title} is now ACTIVE!")
            print("✓ Check the display - it should be showing content")
            print("✓ Press Ctrl+C to exit")
            
            # Keep running to maintain display
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nExiting...")
        else:
            print(f"\n❌ {title} test FAILED")
            print("Check wiring and power connections")
        
    except ValueError:
        print("Invalid input!")
    except KeyboardInterrupt:
        print("\n\nExiting...")


def continuous_update_test():
    """Continuously update all OLEDs with live data"""
    
    logger.info("\n" + "#"*60)
    logger.info("# CONTINUOUS UPDATE TEST")
    logger.info("# OLEDs will update with changing values")
    logger.info("# Press Ctrl+C to stop")
    logger.info("#"*60)
    
    try:
        import luma.oled
        from luma.core.interface.serial import i2c
        from luma.core.render import canvas
        from luma.oled.device import ssd1306
    except ImportError:
        logger.error("❌ luma.oled not installed!")
        return
    
    mux_controller = TCA9548AController(I2C_BUS)
    
    # Create device objects for each OLED
    devices = []
    
    for mux_addr, channel, title, content in OLED_LIST:
        try:
            mux_controller.select_channel(mux_addr, channel)
            serial = i2c(port=I2C_BUS, address=OLED_ADDRESS)
            device = ssd1306(serial, width=128, height=64)
            device.clear()
            devices.append((mux_addr, channel, title, device))
            logger.info(f"✓ Initialized: {title}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize {title}: {e}")
    
    if not devices:
        logger.error("No OLEDs initialized!")
        return
    
    logger.info(f"\n✓ {len(devices)} OLEDs ready for continuous update")
    logger.info("Starting update loop...\n")
    
    counter = 0
    
    try:
        while True:
            for mux_addr, channel, title, device in devices:
                # Select channel
                mux_controller.select_channel(mux_addr, channel)
                
                # Update display
                with canvas(device) as draw:
                    # Border
                    draw.rectangle(device.bounding_box, outline="white", fill="black")
                    
                    # Title
                    draw.text((4, 4), title, fill="white")
                    draw.line((4, 14, 124, 14), fill="white")
                    
                    # Live counter
                    draw.text((4, 24), f"Count: {counter}", fill="white")
                    draw.text((4, 40), f"Time: {time.strftime('%H:%M:%S')}", fill="white")
                    
                    # Status
                    draw.text((4, 54), "LIVE UPDATE", fill="white")
            
            counter += 1
            logger.info(f"Update cycle {counter} completed")
            time.sleep(1)  # Update every 1 second
            
    except KeyboardInterrupt:
        logger.info("\n\nStopping continuous update...")
        
        # Clear all displays
        for mux_addr, channel, title, device in devices:
            mux_controller.select_channel(mux_addr, channel)
            device.clear()
            device.cleanup()
        
        mux_controller.close()
        logger.info("✓ All displays cleared and closed")


# ============================================
# Main Menu
# ============================================
def main_menu():
    """Main interactive menu"""
    
    while True:
        print("\n" + "="*60)
        print("PLTN SIMULATOR - OLED ACTIVE DISPLAY TEST")
        print("="*60)
        print("1. Test All OLEDs (Display ON)")
        print("2. Test Single OLED")
        print("3. Continuous Update Test (Live)")
        print("0. Exit")
        print("="*60)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            test_all_oleds_with_display()
        elif choice == "2":
            test_single_oled_interactive()
        elif choice == "3":
            continuous_update_test()
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
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--menu":
            main_menu()
        elif sys.argv[1] == "--single":
            test_single_oled_interactive()
        elif sys.argv[1] == "--continuous":
            continuous_update_test()
        else:
            print("Usage:")
            print("  python test_oled_display_active.py           # Test all OLEDs")
            print("  python test_oled_display_active.py --menu    # Interactive menu")
            print("  python test_oled_display_active.py --single  # Test single OLED")
            print("  python test_oled_display_active.py --continuous  # Continuous update")
    else:
        # Default: Test all OLEDs
        test_all_oleds_with_display()
