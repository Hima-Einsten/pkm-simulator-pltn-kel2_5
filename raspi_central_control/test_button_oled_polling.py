#!/usr/bin/env python3
"""
Interactive Button + OLED Test (Polling Version)
Menggunakan polling untuk button, lebih reliable daripada interrupt

Usage:
    python test_button_oled_polling.py

Press Ctrl+C to exit
"""

import time
import sys
import signal

try:
    import smbus2
    print("✓ smbus2 loaded")
except ImportError:
    print("✗ smbus2 not found")
    sys.exit(1)

try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO loaded")
except ImportError:
    print("✗ RPi.GPIO not found")
    sys.exit(1)

# GPIO Pins
BTN_PRES_UP = 5
BTN_PRES_DOWN = 6
BTN_PUMP_PRIM_ON = 4
BTN_PUMP_PRIM_OFF = 17
BTN_PUMP_SEC_ON = 27
BTN_PUMP_SEC_OFF = 22
BTN_PUMP_TER_ON = 10
BTN_PUMP_TER_OFF = 9

# I2C
I2C_BUS = 1
MUX_1_ADDR = 0x70
OLED_ADDR = 0x3C

# OLED Channels
OLED_PRESSURIZER = (MUX_1_ADDR, 1)
OLED_PUMP_PRIMARY = (MUX_1_ADDR, 2)
OLED_PUMP_SECONDARY = (MUX_1_ADDR, 3)
OLED_PUMP_TERTIARY = (MUX_1_ADDR, 4)

# State
pressurizer_value = 155.0
pump_primary_status = "OFF"
pump_primary_pwm = 0
pump_secondary_status = "OFF"
pump_secondary_pwm = 0
pump_tertiary_status = "OFF"
pump_tertiary_pwm = 0

# Button state tracking
button_last_state = {}
button_press_count = {}

# Init commands
SSD1306_INIT = [
    0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14,
    0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xFF, 0xD9, 0xF1,
    0xDB, 0x40, 0xA4, 0xA6, 0xAF
]

# Font
FONT_5x8 = {
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E], '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46], '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10], '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30], '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36], '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06], 'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41], 'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F], 'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43], 'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F], 'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F], ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00], '.': [0x00, 0x60, 0x60, 0x00, 0x00],
}


class BasicOLED:
    def __init__(self, bus_num=1):
        self.bus = smbus2.SMBus(bus_num)
        self.initialized = {}
    
    def select_channel(self, mux_addr, channel):
        try:
            self.bus.write_byte(mux_addr, 1 << channel)
            time.sleep(0.001)
            return True
        except:
            return False
    
    def send_command(self, cmd):
        if isinstance(cmd, list):
            self.bus.write_i2c_block_data(OLED_ADDR, 0x00, cmd)
        else:
            self.bus.write_byte_data(OLED_ADDR, 0x00, cmd)
    
    def send_data(self, data):
        if isinstance(data, list):
            for i in range(0, len(data), 32):
                self.bus.write_i2c_block_data(OLED_ADDR, 0x40, data[i:i+32])
        else:
            self.bus.write_byte_data(OLED_ADDR, 0x40, data)
    
    def init_display(self, mux_addr, channel):
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
        
        self.initialized[key] = True
        return True
    
    def clear_display(self):
        for page in range(8):
            self.send_command([0xB0 + page, 0x00, 0x10])
            for col in range(0, 128, 32):
                self.send_data([0x00] * 32)
    
    def draw_text(self, text, x=0, page=0):
        self.send_command([0xB0 + page, x & 0x0F, 0x10 | (x >> 4)])
        for char in text:
            if char.upper() in FONT_5x8:
                self.send_data(FONT_5x8[char.upper()])
                self.send_data([0x00])
    
    def update_pressurizer(self, mux_addr, channel, pressure):
        if not self.select_channel(mux_addr, channel):
            return False
        self.init_display(mux_addr, channel)
        self.clear_display()
        self.draw_text("PRESSURIZER", x=20, page=0)
        self.draw_text(f"{pressure:.1f}", x=30, page=3)
        self.draw_text("BAR", x=70, page=3)
        return True
    
    def update_pump(self, mux_addr, channel, name, status, pwm):
        if not self.select_channel(mux_addr, channel):
            return False
        self.init_display(mux_addr, channel)
        self.clear_display()
        self.draw_text(name, x=10, page=0)
        self.draw_text(f"STATUS: {status}", x=5, page=3)
        if status == "ON":
            self.draw_text(f"PWM: {pwm}", x=10, page=5)
        return True
    
    def close(self):
        self.bus.close()


oled = None
running = True


def signal_handler(sig, frame):
    global running
    print("\n\nShutting down...")
    running = False


def handle_buttons():
    """Poll buttons and handle state changes"""
    global pressurizer_value, pump_primary_status, pump_primary_pwm
    global pump_secondary_status, pump_secondary_pwm
    global pump_tertiary_status, pump_tertiary_pwm
    
    buttons = {
        BTN_PRES_UP: ("Pressurizer UP", lambda: update_pressurizer(+5)),
        BTN_PRES_DOWN: ("Pressurizer DOWN", lambda: update_pressurizer(-5)),
        BTN_PUMP_PRIM_ON: ("Pump Primary ON", lambda: update_pump_primary(True)),
        BTN_PUMP_PRIM_OFF: ("Pump Primary OFF", lambda: update_pump_primary(False)),
        BTN_PUMP_SEC_ON: ("Pump Secondary ON", lambda: update_pump_secondary(True)),
        BTN_PUMP_SEC_OFF: ("Pump Secondary OFF", lambda: update_pump_secondary(False)),
        BTN_PUMP_TER_ON: ("Pump Tertiary ON", lambda: update_pump_tertiary(True)),
        BTN_PUMP_TER_OFF: ("Pump Tertiary OFF", lambda: update_pump_tertiary(False)),
    }
    
    for pin, (name, action) in buttons.items():
        current_state = GPIO.input(pin)
        
        # Detect falling edge (button press)
        if pin in button_last_state:
            if button_last_state[pin] == 1 and current_state == 0:
                print(f"\n[Button] {name}")
                button_press_count[pin] = button_press_count.get(pin, 0) + 1
                action()
                time.sleep(0.1)  # Debounce
        
        button_last_state[pin] = current_state


def update_pressurizer(delta):
    global pressurizer_value
    pressurizer_value = max(0.0, min(200.0, pressurizer_value + delta))
    print(f"  → Pressurizer: {pressurizer_value:.1f} bar")
    oled.update_pressurizer(*OLED_PRESSURIZER, pressurizer_value)


def update_pump_primary(on):
    global pump_primary_status, pump_primary_pwm
    pump_primary_status = "ON" if on else "OFF"
    pump_primary_pwm = 80 if on else 0
    print(f"  → Pump Primary: {pump_primary_status} (PWM: {pump_primary_pwm}%)")
    oled.update_pump(*OLED_PUMP_PRIMARY, "PUMP PRIM", 
                    pump_primary_status, pump_primary_pwm)


def update_pump_secondary(on):
    global pump_secondary_status, pump_secondary_pwm
    pump_secondary_status = "ON" if on else "OFF"
    pump_secondary_pwm = 75 if on else 0
    print(f"  → Pump Secondary: {pump_secondary_status} (PWM: {pump_secondary_pwm}%)")
    oled.update_pump(*OLED_PUMP_SECONDARY, "PUMP SEC", 
                    pump_secondary_status, pump_secondary_pwm)


def update_pump_tertiary(on):
    global pump_tertiary_status, pump_tertiary_pwm
    pump_tertiary_status = "ON" if on else "OFF"
    pump_tertiary_pwm = 70 if on else 0
    print(f"  → Pump Tertiary: {pump_tertiary_status} (PWM: {pump_tertiary_pwm}%)")
    oled.update_pump(*OLED_PUMP_TERTIARY, "PUMP TER", 
                    pump_tertiary_status, pump_tertiary_pwm)


def main():
    global oled, running
    
    print("\n" + "="*60)
    print("BUTTON + OLED TEST (Polling Mode)")
    print("="*60)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize OLED
    print("\n1. Initializing OLEDs...")
    oled = BasicOLED(I2C_BUS)
    
    oled.update_pressurizer(*OLED_PRESSURIZER, pressurizer_value)
    oled.update_pump(*OLED_PUMP_PRIMARY, "PUMP PRIM", pump_primary_status, pump_primary_pwm)
    oled.update_pump(*OLED_PUMP_SECONDARY, "PUMP SEC", pump_secondary_status, pump_secondary_pwm)
    oled.update_pump(*OLED_PUMP_TERTIARY, "PUMP TER", pump_tertiary_status, pump_tertiary_pwm)
    
    print("   ✓ All OLEDs initialized")
    
    # Setup GPIO
    print("\n2. Setting up GPIO...")
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    buttons = [BTN_PRES_UP, BTN_PRES_DOWN, BTN_PUMP_PRIM_ON, BTN_PUMP_PRIM_OFF,
               BTN_PUMP_SEC_ON, BTN_PUMP_SEC_OFF, BTN_PUMP_TER_ON, BTN_PUMP_TER_OFF]
    
    for pin in buttons:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        button_last_state[pin] = GPIO.input(pin)
    
    print("   ✓ GPIO configured")
    
    print("\n" + "="*60)
    print("System Ready! Press buttons...")
    print("Press Ctrl+C to exit")
    print("="*60)
    
    # Main loop
    try:
        while running:
            handle_buttons()
            time.sleep(0.01)  # 100Hz polling
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    print("\n\nButton Press Statistics:")
    for pin, count in button_press_count.items():
        print(f"  GPIO {pin:2d}: {count:3d} presses")
    
    GPIO.cleanup()
    oled.close()
    print("\n✓ Cleanup complete!")


if __name__ == "__main__":
    main()
