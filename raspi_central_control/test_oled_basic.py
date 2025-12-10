#!/usr/bin/env python3
"""
Basic OLED Test - NO External Libraries Required
Only uses smbus2 (already installed)

This script sends raw I2C commands to SSD1306 OLED displays
to initialize and display a simple pattern.

Usage:
    python test_oled_basic.py

Requirements:
    - smbus2 (already installed)
    - No luma.oled needed!
    - No PIL/Pillow needed!
"""

import time
import sys

try:
    import smbus2
    print("✓ smbus2 loaded")
except ImportError:
    print("✗ smbus2 not found. Install with: pip install smbus2")
    sys.exit(1)

# Configuration
I2C_BUS = 1
MUX_1_ADDR = 0x70
MUX_2_ADDR = 0x71
OLED_ADDR = 0x3C

# OLED list
OLED_LIST = [
    (MUX_1_ADDR, 1, "PRESSURIZER"),
    (MUX_1_ADDR, 2, "PUMP PRIMARY"),
    (MUX_1_ADDR, 3, "PUMP SECONDARY"),
    (MUX_1_ADDR, 4, "PUMP TERTIARY"),
    (MUX_1_ADDR, 5, "SAFETY ROD"),
    (MUX_1_ADDR, 6, "SHIM ROD"),
    (MUX_1_ADDR, 7, "REGULATING ROD"),
    (MUX_2_ADDR, 1, "THERMAL POWER"),
    (MUX_2_ADDR, 2, "SYSTEM STATUS"),
]

# SSD1306 initialization sequence
SSD1306_INIT = [
    0xAE,        # Display OFF
    0xD5, 0x80,  # Set display clock divide ratio
    0xA8, 0x3F,  # Set multiplex ratio (1 to 64)
    0xD3, 0x00,  # Set display offset (no offset)
    0x40,        # Set start line address
    0x8D, 0x14,  # Charge pump setting (enable)
    0x20, 0x00,  # Memory addressing mode (horizontal)
    0xA1,        # Set segment re-map (column 127 mapped to SEG0)
    0xC8,        # Set COM output scan direction (remapped)
    0xDA, 0x12,  # Set COM pins hardware configuration
    0x81, 0xFF,  # Set contrast control (max brightness)
    0xD9, 0xF1,  # Set pre-charge period
    0xDB, 0x40,  # Set VCOMH deselect level
    0xA4,        # Entire display ON (resume to RAM content)
    0xA6,        # Set normal display (not inverted)
    0xAF,        # Display ON
]

# Simple 5x8 font (numbers 0-9 and letters)
FONT_5x8 = {
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
}


class BasicOLED:
    """Basic OLED controller using raw I2C commands"""
    
    def __init__(self, bus_num=1):
        self.bus = smbus2.SMBus(bus_num)
    
    def select_mux_channel(self, mux_addr, channel):
        """Select TCA9548A channel"""
        try:
            self.bus.write_byte(mux_addr, 1 << channel)
            time.sleep(0.002)
            return True
        except:
            return False
    
    def send_command(self, cmd):
        """Send command to OLED"""
        if isinstance(cmd, list):
            self.bus.write_i2c_block_data(OLED_ADDR, 0x00, cmd)
        else:
            self.bus.write_byte_data(OLED_ADDR, 0x00, cmd)
    
    def send_data(self, data):
        """Send data to OLED"""
        if isinstance(data, list):
            # Split into chunks of 32 bytes
            for i in range(0, len(data), 32):
                chunk = data[i:i+32]
                self.bus.write_i2c_block_data(OLED_ADDR, 0x40, chunk)
        else:
            self.bus.write_byte_data(OLED_ADDR, 0x40, data)
    
    def init_display(self):
        """Initialize SSD1306 OLED"""
        for i in range(0, len(SSD1306_INIT), 2):
            if i + 1 < len(SSD1306_INIT):
                self.send_command([SSD1306_INIT[i], SSD1306_INIT[i+1]])
            else:
                self.send_command(SSD1306_INIT[i])
            time.sleep(0.001)
    
    def clear_display(self):
        """Clear entire display"""
        for page in range(8):  # 8 pages (64 pixels / 8)
            self.send_command([0xB0 + page])  # Set page
            self.send_command([0x00, 0x10])   # Set column to 0
            
            # Send 128 bytes of 0x00 (black)
            for col in range(0, 128, 32):
                self.send_data([0x00] * 32)
    
    def fill_display(self):
        """Fill entire display (test pattern)"""
        for page in range(8):
            self.send_command([0xB0 + page])  # Set page
            self.send_command([0x00, 0x10])   # Set column to 0
            
            # Send 128 bytes of 0xFF (white)
            for col in range(0, 128, 32):
                self.send_data([0xFF] * 32)
    
    def draw_border(self):
        """Draw border around display"""
        # Top border (page 0, all pixels)
        self.send_command([0xB0])           # Page 0
        self.send_command([0x00, 0x10])     # Column 0
        self.send_data([0xFF] * 128)
        
        # Bottom border (page 7, all pixels)
        self.send_command([0xB7])           # Page 7
        self.send_command([0x00, 0x10])     # Column 0
        self.send_data([0xFF] * 128)
        
        # Left and right borders
        for page in range(1, 7):
            self.send_command([0xB0 + page])
            
            # Left border (column 0)
            self.send_command([0x00, 0x10])
            self.send_data(0xFF)
            
            # Right border (column 127)
            self.send_command([0x7F, 0x10])
            self.send_data(0xFF)
    
    def draw_text(self, text, x=10, page=2):
        """Draw text at position (simple, centered)"""
        self.send_command([0xB0 + page])    # Set page
        self.send_command([x & 0x0F, 0x10 | (x >> 4)])  # Set column
        
        for char in text:
            if char.upper() in FONT_5x8:
                font_data = FONT_5x8[char.upper()]
                self.send_data(font_data)
                self.send_data([0x00])  # Space between chars
    
    def test_pattern(self, name):
        """Display test pattern with name"""
        # Clear display
        self.clear_display()
        time.sleep(0.1)
        
        # Draw border
        self.draw_border()
        time.sleep(0.5)
        
        # Draw text (simplified - just show "OK" + first char of name)
        self.draw_text("OK", x=50, page=3)
        
        # Blink test
        for i in range(2):
            self.send_command(0xA7)  # Invert display
            time.sleep(0.2)
            self.send_command(0xA6)  # Normal display
            time.sleep(0.2)
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()


def test_all_oleds():
    """Test all OLEDs with basic pattern"""
    print("\n" + "="*60)
    print("BASIC OLED TEST (No luma.oled required)")
    print("="*60)
    print("")
    
    oled = BasicOLED(I2C_BUS)
    results = []
    
    # Test multiplexers
    print("1. Testing TCA9548A multiplexers...")
    for mux_addr in [MUX_1_ADDR, MUX_2_ADDR]:
        try:
            oled.bus.read_byte(mux_addr)
            print(f"   ✓ MUX 0x{mux_addr:02X} found")
        except:
            print(f"   ✗ MUX 0x{mux_addr:02X} NOT found")
    
    print("")
    print("2. Testing OLEDs...")
    print("")
    
    for mux_addr, channel, name in OLED_LIST:
        print(f"   Testing: {name} (MUX 0x{mux_addr:02X}, Ch{channel})")
        
        # Select channel
        if not oled.select_mux_channel(mux_addr, channel):
            print(f"      ✗ Failed to select channel")
            results.append((name, False))
            continue
        
        # Check if OLED responds
        try:
            oled.bus.read_byte(OLED_ADDR)
            print(f"      ✓ OLED found at 0x{OLED_ADDR:02X}")
        except:
            print(f"      ✗ OLED not found")
            results.append((name, False))
            continue
        
        # Initialize and test
        try:
            print(f"      → Initializing display...")
            oled.init_display()
            time.sleep(0.1)
            
            print(f"      → Drawing test pattern...")
            oled.test_pattern(name)
            
            print(f"      ✓ Display ACTIVE - Check OLED screen!")
            print(f"         (Should show border + 'OK' + blink)")
            results.append((name, True))
            
        except Exception as e:
            print(f"      ✗ Test failed: {e}")
            results.append((name, False))
        
        time.sleep(1)
        print("")
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:.<35} {status}")
    
    print(f"\nTotal: {passed} PASS, {failed} FAIL")
    
    if passed > 0:
        print("\n✓ OLEDs should be ACTIVE!")
        print("  Check each display - should show:")
        print("  - White border")
        print("  - 'OK' text in center")
        print("  - Display should have blinked")
    
    oled.close()
    
    return passed == len(results)


def test_single_oled(index):
    """Test a single OLED by index"""
    if index < 0 or index >= len(OLED_LIST):
        print(f"Invalid index {index}. Must be 0-{len(OLED_LIST)-1}")
        return
    
    mux_addr, channel, name = OLED_LIST[index]
    
    print(f"\nTesting: {name}")
    print(f"MUX: 0x{mux_addr:02X}, Channel: {channel}")
    print("="*60)
    
    oled = BasicOLED(I2C_BUS)
    
    # Select channel
    if not oled.select_mux_channel(mux_addr, channel):
        print("✗ Failed to select channel")
        return
    
    # Check OLED
    try:
        oled.bus.read_byte(OLED_ADDR)
        print(f"✓ OLED found at 0x{OLED_ADDR:02X}")
    except:
        print(f"✗ OLED not found at 0x{OLED_ADDR:02X}")
        return
    
    # Initialize
    print("Initializing...")
    oled.init_display()
    
    # Test pattern
    print("Drawing test pattern...")
    oled.test_pattern(name)
    
    print("\n✓ Test complete!")
    print("Check OLED - should show border + 'OK'")
    
    oled.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            print("\nAvailable OLEDs:")
            for i, (mux, ch, name) in enumerate(OLED_LIST):
                print(f"  {i}: {name} (MUX 0x{mux:02X}, Ch{ch})")
        elif sys.argv[1] == "--single":
            if len(sys.argv) > 2:
                try:
                    idx = int(sys.argv[2])
                    test_single_oled(idx)
                except ValueError:
                    print("Invalid index. Use: --single <index>")
            else:
                print("Usage: python test_oled_basic.py --single <index>")
                print("       python test_oled_basic.py --list")
        else:
            print("Usage:")
            print("  python test_oled_basic.py           # Test all OLEDs")
            print("  python test_oled_basic.py --list    # List OLEDs")
            print("  python test_oled_basic.py --single <index>  # Test one OLED")
    else:
        test_all_oleds()
