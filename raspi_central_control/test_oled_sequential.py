#!/usr/bin/env python3
"""
Simple OLED Channel Test - Sequential Display Test
Tests one channel at a time with clear visual feedback
"""

import sys
import time
import logging
from raspi_tca9548a import DualMultiplexerManager
from raspi_oled_manager import OLEDDisplay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_channel(mux, i2c, mux_num, channel, label, name):
    """Test a single channel and display unique label"""
    print(f"\n{'='*60}")
    print(f"Testing: {label} - {name}")
    print(f"MUX #{mux_num}, Channel {channel}")
    print(f"{'='*60}")
    
    try:
        # Select channel
        if mux_num == 1:
            success = mux.select_display_channel(channel)
        else:
            success = mux.select_esp_channel(channel)
        
        if not success:
            print(f"❌ Failed to select channel")
            return False
        
        time.sleep(0.1)  # Wait for channel switch
        
        # Create and initialize display
        display = OLEDDisplay(128, 32)
        if display.init_hardware(i2c, 0x3C, timeout=2.0):
            # Clear and draw
            display.clear()
            display.draw_text_centered(label, 1, display.font_small)
            display.draw_text_centered(name, 12, display.font_large)
            display.draw_text_centered(f"M{mux_num}C{channel}", 22, display.font_small)
            display.show()
            
            print(f"✅ Display updated successfully")
            print(f"   Line 1: {label}")
            print(f"   Line 2: {name}")
            print(f"   Line 3: M{mux_num}C{channel}")
            return True
        else:
            print(f"❌ Failed to initialize display")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("OLED SEQUENTIAL CHANNEL TEST")
    print("="*60)
    print("\nThis will test each OLED one by one.")
    print("Please observe which PHYSICAL display shows each label.\n")
    
    input("Press ENTER to start test...")
    
    try:
        import board
        i2c = board.I2C()
        
        # Initialize multiplexer
        mux = DualMultiplexerManager(display_bus=1, esp_bus=1)
        
        # Test sequence
        tests = [
            # MUX #1 tests
            (1, 1, "OLED-1", "PRESSURIZER"),
            (1, 2, "OLED-2", "PUMP-1"),
            (1, 3, "OLED-3", "PUMP-2"),
            (1, 4, "OLED-4", "PUMP-3"),
            (1, 5, "OLED-5", "SAFETY"),
            (1, 6, "OLED-6", "SHIM"),
            (1, 7, "OLED-7", "REGULATING"),  # ← PROBLEM DISPLAY
            
            # MUX #2 tests
            (2, 1, "OLED-8", "THERMAL"),
            (2, 2, "OLED-9", "STATUS"),      # ← PROBLEM DISPLAY
        ]
        
        for mux_num, channel, label, name in tests:
            test_single_channel(mux, i2c, mux_num, channel, label, name)
            
            # Pause between tests
            print("\nDisplay will stay on for 5 seconds...")
            print("Please note which PHYSICAL display is showing this label.")
            time.sleep(5)
            
            if mux_num == 1 and channel == 7:
                print("\n" + "!"*60)
                print("⚠️  CRITICAL: This should be REGULATING ROD display")
                print("⚠️  If you see 'OLED-7 REGULATING M1C7', note which physical display it is!")
                print("!"*60)
                input("\nPress ENTER to continue to MUX #2 tests...")
            
            if mux_num == 2 and channel == 2:
                print("\n" + "!"*60)
                print("⚠️  CRITICAL: This should be SYSTEM STATUS display")
                print("⚠️  If you see 'OLED-9 STATUS M2C2', note which physical display it is!")
                print("!"*60)
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\nPlease report:")
        print("1. Did OLED-7 (REGULATING) appear on the correct physical display?")
        print("2. Did OLED-9 (STATUS) appear on the correct physical display?")
        print("3. Were any displays showing wrong labels?")
        
        # Cleanup
        mux.close()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
