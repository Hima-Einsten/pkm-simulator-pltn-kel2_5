#!/usr/bin/env python3
"""
OLED Channel Mapping Diagnostic Tool

This script will display unique identifiers on each OLED to verify
the actual hardware channel mapping vs what the code expects.

Expected Mapping:
MUX #1 (0x70):
  Ch 1: Pressurizer
  Ch 2: Pump Primary
  Ch 3: Pump Secondary
  Ch 4: Pump Tertiary
  Ch 5: Safety Rod
  Ch 6: Shim Rod
  Ch 7: Regulating Rod

MUX #2 (0x71):
  Ch 1: Thermal Power
  Ch 2: System Status
"""

import sys
import time
import logging
from raspi_tca9548a import DualMultiplexerManager
from raspi_oled_manager import OLEDDisplay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_channel_mapping():
    """Test and display channel mapping for all OLEDs"""
    
    print("=" * 60)
    print("OLED Channel Mapping Diagnostic")
    print("=" * 60)
    print("\nThis will display unique labels on each OLED.")
    print("Please verify which physical display shows which label.\n")
    
    try:
        # Initialize multiplexer manager
        mux = DualMultiplexerManager(display_bus=1, esp_bus=1)
        
        # Test MUX #1 (0x70) - Channels 1-7
        print("\n--- Testing MUX #1 (0x70) ---")
        mux1_channels = [
            (1, "OLED #1", "PRESSURIZER"),
            (2, "OLED #2", "PUMP 1"),
            (3, "OLED #3", "PUMP 2"),
            (4, "OLED #4", "PUMP 3"),
            (5, "OLED #5", "SAFETY ROD"),
            (6, "OLED #6", "SHIM ROD"),
            (7, "OLED #7", "REG ROD"),
        ]
        
        import board
        i2c = board.I2C()
        
        for channel, label, name in mux1_channels:
            print(f"\nTesting Channel {channel}: {label} ({name})")
            
            # Select channel
            mux.select_display_channel(channel)
            time.sleep(0.05)
            
            # Create and initialize display
            display = OLEDDisplay(128, 32)
            if display.init_hardware(i2c, 0x3C, timeout=1.0):
                display.clear()
                display.draw_text_centered(label, 1, display.font_small)
                display.draw_text_centered(name, 12, display.font_large)
                display.draw_text_centered(f"MUX1 Ch{channel}", 22, display.font_small)
                display.show()
                print(f"  ✓ Display updated: {label}")
            else:
                print(f"  ✗ Failed to initialize")
            
            time.sleep(0.5)  # Pause between displays
        
        # Test MUX #2 (0x71) - Channels 1-2
        print("\n--- Testing MUX #2 (0x71) ---")
        mux2_channels = [
            (1, "OLED #8", "THERMAL PWR"),
            (2, "OLED #9", "SYS STATUS"),
        ]
        
        for channel, label, name in mux2_channels:
            print(f"\nTesting Channel {channel}: {label} ({name})")
            
            # Select channel on MUX #2
            mux.select_esp_channel(channel)
            time.sleep(0.05)
            
            # Create and initialize display
            display = OLEDDisplay(128, 32)
            if display.init_hardware(i2c, 0x3C, timeout=1.0):
                display.clear()
                display.draw_text_centered(label, 1, display.font_small)
                display.draw_text_centered(name, 12, display.font_large)
                display.draw_text_centered(f"MUX2 Ch{channel}", 22, display.font_small)
                display.show()
                print(f"  ✓ Display updated: {label}")
            else:
                print(f"  ✗ Failed to initialize")
            
            time.sleep(0.5)  # Pause between displays
        
        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print("\nPlease verify:")
        print("1. Which physical display shows 'OLED #7 REG ROD'?")
        print("2. Which physical display shows 'OLED #9 SYS STATUS'?")
        print("3. Are they showing the correct labels?")
        print("\nIf labels are swapped or incorrect, we have a channel mapping issue.")
        
        # Keep displays on for 30 seconds
        print("\nDisplays will stay on for 30 seconds...")
        time.sleep(30)
        
        # Cleanup
        mux.close()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_channel_mapping()
