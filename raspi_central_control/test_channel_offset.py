#!/usr/bin/env python3
"""
Quick OLED Channel Fix Test
Test if the issue is channel offset (0-based vs 1-based indexing)
"""

import sys
import time
import logging
from raspi_tca9548a import DualMultiplexerManager
from raspi_oled_manager import OLEDDisplay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*60)
    print("QUICK CHANNEL OFFSET TEST")
    print("="*60)
    print("\nTesting hypothesis: Channel offset issue")
    print("Will test Regulating Rod and System Status with different offsets\n")
    
    try:
        import board
        i2c = board.I2C()
        mux = DualMultiplexerManager(display_bus=1, esp_bus=1)
        
        # Test 1: Current mapping (what code thinks)
        print("\n--- Test 1: Current Code Mapping ---")
        print("Regulating Rod: MUX #1, Channel 7")
        print("System Status: MUX #2, Channel 2")
        input("Press ENTER to test...")
        
        # Regulating Rod - Channel 7
        mux.select_display_channel(7)
        time.sleep(0.1)
        display = OLEDDisplay(128, 32)
        if display.init_hardware(i2c, 0x3C, timeout=1.0):
            display.clear()
            display.draw_text_centered("TEST 1", 1, display.font_small)
            display.draw_text_centered("REG ROD", 12, display.font_large)
            display.draw_text_centered("M1 Ch7", 22, display.font_small)
            display.show()
        
        time.sleep(2)
        
        # System Status - Channel 2
        mux.select_esp_channel(2)
        time.sleep(0.1)
        display2 = OLEDDisplay(128, 32)
        if display2.init_hardware(i2c, 0x3C, timeout=1.0):
            display2.clear()
            display2.draw_text_centered("TEST 1", 1, display2.font_small)
            display2.draw_text_centered("STATUS", 12, display2.font_large)
            display2.draw_text_centered("M2 Ch2", 22, display2.font_small)
            display2.show()
        
        print("\nCheck displays:")
        print("  - Does 'REG ROD M1 Ch7' appear on Regulating Rod physical display?")
        print("  - Does 'STATUS M2 Ch2' appear on System Status physical display?")
        input("\nPress ENTER to try alternative mapping...")
        
        # Test 2: Try 0-based indexing
        print("\n--- Test 2: Zero-Based Indexing ---")
        print("Regulating Rod: MUX #1, Channel 6 (7-1)")
        print("System Status: MUX #2, Channel 1 (2-1)")
        input("Press ENTER to test...")
        
        # Regulating Rod - Channel 6
        mux.select_display_channel(6)
        time.sleep(0.1)
        display3 = OLEDDisplay(128, 32)
        if display3.init_hardware(i2c, 0x3C, timeout=1.0):
            display3.clear()
            display3.draw_text_centered("TEST 2", 1, display3.font_small)
            display3.draw_text_centered("REG ROD", 12, display3.font_large)
            display3.draw_text_centered("M1 Ch6", 22, display3.font_small)
            display3.show()
        
        time.sleep(2)
        
        # System Status - Channel 1
        mux.select_esp_channel(1)
        time.sleep(0.1)
        display4 = OLEDDisplay(128, 32)
        if display4.init_hardware(i2c, 0x3C, timeout=1.0):
            display4.clear()
            display4.draw_text_centered("TEST 2", 1, display4.font_small)
            display4.draw_text_centered("STATUS", 12, display4.font_large)
            display4.draw_text_centered("M2 Ch1", 22, display4.font_small)
            display4.show()
        
        print("\nCheck displays:")
        print("  - Does 'REG ROD M1 Ch6' appear on Regulating Rod physical display?")
        print("  - Does 'STATUS M2 Ch1' appear on System Status physical display?")
        input("\nPress ENTER to try swapped MUX...")
        
        # Test 3: Try swapped MUX assignment
        print("\n--- Test 3: Swapped MUX Assignment ---")
        print("Regulating Rod: MUX #2, Channel 2")
        print("System Status: MUX #1, Channel 7")
        input("Press ENTER to test...")
        
        # Regulating Rod - MUX #2 Channel 2
        mux.select_esp_channel(2)
        time.sleep(0.1)
        display5 = OLEDDisplay(128, 32)
        if display5.init_hardware(i2c, 0x3C, timeout=1.0):
            display5.clear()
            display5.draw_text_centered("TEST 3", 1, display5.font_small)
            display5.draw_text_centered("REG ROD", 12, display5.font_large)
            display5.draw_text_centered("M2 Ch2", 22, display5.font_small)
            display5.show()
        
        time.sleep(2)
        
        # System Status - MUX #1 Channel 7
        mux.select_display_channel(7)
        time.sleep(0.1)
        display6 = OLEDDisplay(128, 32)
        if display6.init_hardware(i2c, 0x3C, timeout=1.0):
            display6.clear()
            display6.draw_text_centered("TEST 3", 1, display6.font_small)
            display6.draw_text_centered("STATUS", 12, display6.font_large)
            display6.draw_text_centered("M1 Ch7", 22, display6.font_small)
            display6.show()
        
        print("\nCheck displays:")
        print("  - Does 'REG ROD M2 Ch2' appear on Regulating Rod physical display?")
        print("  - Does 'STATUS M1 Ch7' appear on System Status physical display?")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\nWhich test showed correct mapping?")
        print("  Test 1: Current code (M1Ch7 / M2Ch2)")
        print("  Test 2: Zero-based (M1Ch6 / M2Ch1)")
        print("  Test 3: Swapped MUX (M2Ch2 / M1Ch7)")
        
        mux.close()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
