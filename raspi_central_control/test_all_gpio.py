#!/usr/bin/env python3
"""
Simple GPIO test - Monitor ALL button pins continuously
Shows which GPIO pins are actually changing state
"""

import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not available!")
    exit(1)

# All button GPIO pins from raspi_gpio_buttons.py
BUTTON_PINS = {
    5: "PUMP_PRIMARY_ON",
    6: "PUMP_PRIMARY_OFF",
    13: "PUMP_SECONDARY_ON",
    19: "PUMP_SECONDARY_OFF",
    26: "PUMP_TERTIARY_ON",
    21: "PUMP_TERTIARY_OFF",
    20: "SAFETY_ROD_UP",
    16: "SAFETY_ROD_DOWN",
    12: "SHIM_ROD_UP",
    7: "SHIM_ROD_DOWN",
    8: "REGULATING_ROD_UP",
    25: "REGULATING_ROD_DOWN",
    24: "PRESSURE_UP",
    23: "PRESSURE_DOWN",
    18: "EMERGENCY",
    15: "SPARE_1",
    14: "SPARE_2"
}

print("="*70)
print("  GPIO BUTTON TEST - Real-time State Monitor")
print("="*70)
print("Monitoring all 17 button pins...")
print("Press buttons to see which GPIO changes state")
print("Press Ctrl+C to exit")
print()

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup all pins as input with pull-up
for pin in BUTTON_PINS.keys():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"  GPIO {pin:2d} = {BUTTON_PINS[pin]}")

print()
print("-"*70)
print("Monitoring... (Waiting for button presses)")
print("-"*70)

# Store last state
last_state = {}
for pin in BUTTON_PINS.keys():
    last_state[pin] = GPIO.HIGH

try:
    count = 0
    while True:
        for pin in BUTTON_PINS.keys():
            current = GPIO.input(pin)
            
            # Detect state change
            if current != last_state[pin]:
                state_text = "PRESSED " if current == GPIO.LOW else "RELEASED"
                print(f"[{time.strftime('%H:%M:%S.%f')[:-3]}] GPIO {pin:2d} ({BUTTON_PINS[pin]:20s}) -> {state_text}")
                last_state[pin] = current
        
        # Heartbeat every 100 loops (1 second)
        count += 1
        if count % 100 == 0:
            # Show current state of all pins
            pressed = [pin for pin in BUTTON_PINS.keys() if GPIO.input(pin) == GPIO.LOW]
            if pressed:
                print(f"[{time.strftime('%H:%M:%S')}] Currently pressed: {pressed}")
        
        time.sleep(0.01)  # 10ms

except KeyboardInterrupt:
    print("\n\nTest stopped by user")
finally:
    GPIO.cleanup()
    print("GPIO cleaned up")
