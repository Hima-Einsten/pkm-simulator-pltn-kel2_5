#!/usr/bin/env python3
"""
Interactive Button + OLED Test
Test integrasi antara GPIO button dengan OLED display

Setiap tombol yang ditekan akan update OLED yang sesuai:
- BTN_PRES_UP/DOWN → Update OLED Pressurizer
- BTN_PUMP_PRIM_ON/OFF → Update OLED Pump Primary
- BTN_PUMP_SEC_ON/OFF → Update OLED Pump Secondary
- BTN_PUMP_TER_ON/OFF → Update OLED Pump Tertiary

Usage:
    python test_button_oled_interactive.py

Requirements:
    - smbus2 (for I2C)
    - RPi.GPIO (for buttons)

Press Ctrl+C to exit
"""

import time
import sys
import signal

try:
    import smbus2
    print("✓ smbus2 loaded")
except ImportError:
    print("✗ smbus2 not found. Install with: pip install smbus2")
    sys.exit(1)

try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO loaded")
except ImportError:
    print("✗ RPi.GPIO not found. Install with: pip install RPi.GPIO")
    sys.exit(1)

# Configuration - GPIO Pins
BTN_PRES_UP = 5
BTN_PRES_DOWN = 6
BTN_PUMP_PRIM_ON = 4
BTN_PUMP_PRIM_OFF = 17
BTN_PUMP_SEC_ON = 27
BTN_PUMP_SEC_OFF = 22
BTN_PUMP_TER_ON = 10
BTN_PUMP_TER_OFF = 9

# I2C Configuration
I2C_BUS = 1
MUX_1_ADDR = 0x70
MUX_2_ADDR = 0x71
OLED_ADDR = 0x3C

# OLED Channels
OLED_PRESSURIZER = (MUX_1_ADDR, 1)
OLED_PUMP_PRIMARY = (MUX_1_ADDR, 2)
OLED_PUMP_SECONDARY = (MUX_1_ADDR, 3)
OLED_PUMP_TERTIARY = (MUX_1_ADDR, 4)

# State variables
pressurizer_value = 155.0  # bar
pump_primary_status = "OFF"
pump_primary_pwm = 0
pump_secondary_status = "OFF"
pump_secondary_pwm = 0
pump_tertiary_status = "OFF"
pump_tertiary_pwm = 0

# Button press counters
button_press_count = {
    BTN_PRES_UP: 0,
    BTN_PRES_DOWN: 0,
    BTN_PUMP_PRIM_ON: 0,
    BTN_PUMP_PRIM_OFF: 0,
    BTN_PUMP_SEC_ON: 0,
    BTN_PUMP_SEC_OFF: 0,
    BTN_PUMP_TER_ON: 0,
    BTN_PUMP_TER_OFF: 0,
}

# SSD1306 initialization commands
SSD1306_INIT = [
    0xAE,        # Display OFF
    0xD5, 0x80,  # Clock divide ratio
    0xA8, 0x3F,  # Multiplex ratio
    0xD3, 0x00,  # Display offset
    0x40,        # Start line
    0x8D, 0x14,  # Charge pump ON
    0x20, 0x00,  # Horizontal addressing mode
    0xA1,        # Segment remap
    0xC8,        # COM scan direction
    0xDA, 0x12,  # COM pins
    0x81, 0xFF,  # Contrast (max)
    0xD9, 0xF1,  # Pre-charge
    0xDB, 0x40,  # VCOMH
    0xA4,        # Display ON resume
    0xA6,        # Normal display
    0xAF,        # Display ON
]

# Simple font (5x8)
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
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
}


class BasicOLED:
    """Basic OLED controller"""
    
    def __init__(self, bus_num=1):
        self.bus = smbus2.SMBus(bus_num)
        self.initialized = {}
    
    def select_channel(self, mux_addr, channel):
        """Select TCA9548A channel"""
        try:
            self.bus.write_byte(mux_addr, 1 << channel)
            time.sleep(0.001)
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
            for i in range(0, len(data), 32):
                chunk = data[i:i+32]
                self.bus.write_i2c_block_data(OLED_ADDR, 0x40, chunk)
        else:
            self.bus.write_byte_data(OLED_ADDR, 0x40, data)
    
    def init_display(self, mux_addr, channel):
        """Initialize OLED"""
        key = (mux_addr, channel)
        if key in self.initialized:
            return True
        
        if not self.select_channel(mux_addr, channel):
            return False
        
        for i in range(0, len(SSD1306_INIT), 2):
            if i + 1 < len(SSD1306_INIT):
                self.send_command([SSD1306_INIT[i], SSD1306_INIT[i+1]])
            else:
                self.send_command(SSD1306_INIT[i])
            time.sleep(0.001)
        
        self.initialized[key] = True
        return True
    
    def clear_display(self):
        """Clear display"""
        for page in range(8):
            self.send_command([0xB0 + page, 0x00, 0x10])
            for col in range(0, 128, 32):
                self.send_data([0x00] * 32)
    
    def draw_text(self, text, x=0, page=0):
        """Draw text at position"""
        self.send_command([0xB0 + page])
        self.send_command([x & 0x0F, 0x10 | (x >> 4)])
        
        for char in text:
            if char.upper() in FONT_5x8:
                font_data = FONT_5x8[char.upper()]
                self.send_data(font_data)
                self.send_data([0x00])
    
    def update_pressurizer(self, mux_addr, channel, pressure):
        """Update pressurizer OLED"""
        if not self.select_channel(mux_addr, channel):
            return False
        
        self.init_display(mux_addr, channel)
        self.clear_display()
        
        # Title
        self.draw_text("PRESSURIZER", x=20, page=0)
        
        # Value
        pressure_str = f"{pressure:.1f}"
        self.draw_text(pressure_str, x=30, page=3)
        self.draw_text("BAR", x=70, page=3)
        
        # Bar indicator (simple)
        bar_level = int(pressure / 200.0 * 100)
        self.draw_text(f"{bar_level}", x=50, page=5)
        
        return True
    
    def update_pump(self, mux_addr, channel, name, status, pwm):
        """Update pump OLED"""
        if not self.select_channel(mux_addr, channel):
            return False
        
        self.init_display(mux_addr, channel)
        self.clear_display()
        
        # Name
        self.draw_text(name, x=10, page=0)
        
        # Status
        self.draw_text(f"STATUS: {status}", x=5, page=3)
        
        # PWM
        if status == "ON":
            self.draw_text(f"PWM: {pwm}", x=10, page=5)
        
        return True
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()


# Global OLED controller
oled = None


def button_callback(channel):
    """Handle button press"""
    global pressurizer_value, pump_primary_status, pump_primary_pwm
    global pump_secondary_status, pump_secondary_pwm
    global pump_tertiary_status, pump_tertiary_pwm
    global button_press_count
    
    # Increment counter
    button_press_count[channel] += 1
    
    # Debounce
    time.sleep(0.05)
    
    print(f"\n[Button Press] GPIO {channel}")
    
    # Handle Pressurizer buttons
    if channel == BTN_PRES_UP:
        pressurizer_value = min(200.0, pressurizer_value + 5.0)
        print(f"  → Pressurizer UP: {pressurizer_value:.1f} bar")
        oled.update_pressurizer(*OLED_PRESSURIZER, pressurizer_value)
    
    elif channel == BTN_PRES_DOWN:
        pressurizer_value = max(0.0, pressurizer_value - 5.0)
        print(f"  → Pressurizer DOWN: {pressurizer_value:.1f} bar")
        oled.update_pressurizer(*OLED_PRESSURIZER, pressurizer_value)
    
    # Handle Pump Primary buttons
    elif channel == BTN_PUMP_PRIM_ON:
        pump_primary_status = "ON"
        pump_primary_pwm = 80
        print(f"  → Pump Primary ON (PWM: {pump_primary_pwm}%)")
        oled.update_pump(*OLED_PUMP_PRIMARY, "PUMP PRIM", 
                        pump_primary_status, pump_primary_pwm)
    
    elif channel == BTN_PUMP_PRIM_OFF:
        pump_primary_status = "OFF"
        pump_primary_pwm = 0
        print(f"  → Pump Primary OFF")
        oled.update_pump(*OLED_PUMP_PRIMARY, "PUMP PRIM", 
                        pump_primary_status, pump_primary_pwm)
    
    # Handle Pump Secondary buttons
    elif channel == BTN_PUMP_SEC_ON:
        pump_secondary_status = "ON"
        pump_secondary_pwm = 75
        print(f"  → Pump Secondary ON (PWM: {pump_secondary_pwm}%)")
        oled.update_pump(*OLED_PUMP_SECONDARY, "PUMP SEC", 
                        pump_secondary_status, pump_secondary_pwm)
    
    elif channel == BTN_PUMP_SEC_OFF:
        pump_secondary_status = "OFF"
        pump_secondary_pwm = 0
        print(f"  → Pump Secondary OFF")
        oled.update_pump(*OLED_PUMP_SECONDARY, "PUMP SEC", 
                        pump_secondary_status, pump_secondary_pwm)
    
    # Handle Pump Tertiary buttons
    elif channel == BTN_PUMP_TER_ON:
        pump_tertiary_status = "ON"
        pump_tertiary_pwm = 70
        print(f"  → Pump Tertiary ON (PWM: {pump_tertiary_pwm}%)")
        oled.update_pump(*OLED_PUMP_TERTIARY, "PUMP TER", 
                        pump_tertiary_status, pump_tertiary_pwm)
    
    elif channel == BTN_PUMP_TER_OFF:
        pump_tertiary_status = "OFF"
        pump_tertiary_pwm = 0
        print(f"  → Pump Tertiary OFF")
        oled.update_pump(*OLED_PUMP_TERTIARY, "PUMP TER", 
                        pump_tertiary_status, pump_tertiary_pwm)


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\n\n" + "="*60)
    print("Shutting down...")
    print("="*60)
    
    # Print statistics
    print("\nButton Press Statistics:")
    total = 0
    for pin, count in button_press_count.items():
        if count > 0:
            print(f"  GPIO {pin:2d}: {count:3d} presses")
            total += count
    print(f"  Total:    {total:3d} presses")
    
    # Cleanup
    GPIO.cleanup()
    if oled:
        oled.close()
    
    print("\n✓ Cleanup complete. Goodbye!")
    sys.exit(0)


def main():
    """Main function"""
    global oled
    
    print("\n" + "="*60)
    print("INTERACTIVE BUTTON + OLED TEST")
    print("="*60)
    print("\nInitializing...")
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize OLED
    print("\n1. Initializing I2C and OLEDs...")
    oled = BasicOLED(I2C_BUS)
    
    # Initialize all displays with default values
    print("   → Initializing Pressurizer OLED...")
    oled.update_pressurizer(*OLED_PRESSURIZER, pressurizer_value)
    
    print("   → Initializing Pump Primary OLED...")
    oled.update_pump(*OLED_PUMP_PRIMARY, "PUMP PRIM", 
                    pump_primary_status, pump_primary_pwm)
    
    print("   → Initializing Pump Secondary OLED...")
    oled.update_pump(*OLED_PUMP_SECONDARY, "PUMP SEC", 
                    pump_secondary_status, pump_secondary_pwm)
    
    print("   → Initializing Pump Tertiary OLED...")
    oled.update_pump(*OLED_PUMP_TERTIARY, "PUMP TER", 
                    pump_tertiary_status, pump_tertiary_pwm)
    
    print("   ✓ All OLEDs initialized")
    
    # Setup GPIO
    print("\n2. Setting up GPIO buttons...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    buttons = [
        (BTN_PRES_UP, "Pressurizer UP"),
        (BTN_PRES_DOWN, "Pressurizer DOWN"),
        (BTN_PUMP_PRIM_ON, "Pump Primary ON"),
        (BTN_PUMP_PRIM_OFF, "Pump Primary OFF"),
        (BTN_PUMP_SEC_ON, "Pump Secondary ON"),
        (BTN_PUMP_SEC_OFF, "Pump Secondary OFF"),
        (BTN_PUMP_TER_ON, "Pump Tertiary ON"),
        (BTN_PUMP_TER_OFF, "Pump Tertiary OFF"),
    ]
    
    for pin, name in buttons:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, 
                            callback=button_callback, 
                            bouncetime=200)
        print(f"   ✓ GPIO {pin:2d}: {name}")
    
    print("\n" + "="*60)
    print("System Ready!")
    print("="*60)
    print("\nButton Mapping:")
    print("  GPIO  5 (↑)  : Pressurizer UP (+5 bar)")
    print("  GPIO  6 (↓)  : Pressurizer DOWN (-5 bar)")
    print("  GPIO  4 (ON) : Pump Primary ON")
    print("  GPIO 17 (OFF): Pump Primary OFF")
    print("  GPIO 27 (ON) : Pump Secondary ON")
    print("  GPIO 22 (OFF): Pump Secondary OFF")
    print("  GPIO 10 (ON) : Pump Tertiary ON")
    print("  GPIO  9 (OFF): Pump Tertiary OFF")
    print("\nPress buttons to update OLEDs!")
    print("Press Ctrl+C to exit")
    print("="*60)
    
    # Keep program running
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
