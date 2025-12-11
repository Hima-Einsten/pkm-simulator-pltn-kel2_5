#!/usr/bin/env python3
"""
Raspberry Pi GPIO Button Handler for PLTN Control Panel
Handles 15 physical push buttons with debouncing
"""

import RPi.GPIO as GPIO
import time
import logging
from enum import IntEnum

logger = logging.getLogger(__name__)

# ============================================
# GPIO Pin Mapping (BCM Mode)
# ============================================

class ButtonPin(IntEnum):
    """GPIO pin assignments for buttons"""
    # Pump Control (6 buttons)
    PUMP_PRIMARY_ON = 5
    PUMP_PRIMARY_OFF = 6
    PUMP_SECONDARY_ON = 13
    PUMP_SECONDARY_OFF = 19
    PUMP_TERTIARY_ON = 26
    PUMP_TERTIARY_OFF = 21
    
    # Rod Control (6 buttons)
    SAFETY_ROD_UP = 20
    SAFETY_ROD_DOWN = 16
    SHIM_ROD_UP = 12
    SHIM_ROD_DOWN = 7
    REGULATING_ROD_UP = 8
    REGULATING_ROD_DOWN = 25
    
    # Pressurizer Control (2 buttons)
    PRESSURE_UP = 24
    PRESSURE_DOWN = 23
    
    # System Control (2 buttons)
    REACTOR_START = 17  # GREEN button - Start reactor system
    REACTOR_STOP = 27   # YELLOW button - Stop reactor system
    
    # Emergency (1 button)
    EMERGENCY = 18  # RED button - Emergency shutdown!

# Button names for logging
BUTTON_NAMES = {
    ButtonPin.PUMP_PRIMARY_ON: "Pump Primary ON",
    ButtonPin.PUMP_PRIMARY_OFF: "Pump Primary OFF",
    ButtonPin.PUMP_SECONDARY_ON: "Pump Secondary ON",
    ButtonPin.PUMP_SECONDARY_OFF: "Pump Secondary OFF",
    ButtonPin.PUMP_TERTIARY_ON: "Pump Tertiary ON",
    ButtonPin.PUMP_TERTIARY_OFF: "Pump Tertiary OFF",
    ButtonPin.SAFETY_ROD_UP: "Safety Rod UP",
    ButtonPin.SAFETY_ROD_DOWN: "Safety Rod DOWN",
    ButtonPin.SHIM_ROD_UP: "Shim Rod UP",
    ButtonPin.SHIM_ROD_DOWN: "Shim Rod DOWN",
    ButtonPin.REGULATING_ROD_UP: "Regulating Rod UP",
    ButtonPin.REGULATING_ROD_DOWN: "Regulating Rod DOWN",
    ButtonPin.PRESSURE_UP: "Pressure UP",
    ButtonPin.PRESSURE_DOWN: "Pressure DOWN",
    ButtonPin.REACTOR_START: "REACTOR START",
    ButtonPin.REACTOR_STOP: "REACTOR STOP",
    ButtonPin.EMERGENCY: "EMERGENCY SHUTDOWN",
}

# ============================================
# Button Handler Class
# ============================================

class ButtonHandler:
    """Handles all physical push buttons with debouncing"""
    
    def __init__(self, debounce_time=0.2):
        """
        Initialize GPIO buttons
        
        Args:
            debounce_time: Debounce delay in seconds (default: 200ms)
        """
        self.debounce_time = debounce_time
        self.last_press_time = {}
        self.last_state = {}
        self.callbacks = {}
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all button pins as INPUT with PULL_UP
        # (Buttons connect pin to GND when pressed)
        for pin in ButtonPin:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_press_time[pin] = 0
            self.last_state[pin] = GPIO.HIGH
            
        logger.info("GPIO Button Handler initialized with 15 buttons")
    
    def register_callback(self, button_pin, callback):
        """
        Register callback function for button press
        
        Args:
            button_pin: ButtonPin enum value
            callback: Function to call when button pressed (no arguments)
        """
        self.callbacks[button_pin] = callback
        logger.info(f"Callback registered: {BUTTON_NAMES[button_pin]}")
    
    def check_all_buttons(self):
        """
        Check all buttons and trigger callbacks if pressed
        Should be called frequently (e.g., every 10ms) in main loop
        """
        current_time = time.time()
        
        for pin in ButtonPin:
            current_state = GPIO.input(pin)
            
            # Detect HIGH to LOW transition (button press)
            if current_state == GPIO.LOW and self.last_state[pin] == GPIO.HIGH:
                # Check debounce
                time_since_last = current_time - self.last_press_time[pin]
                
                if time_since_last > self.debounce_time:
                    self.last_press_time[pin] = current_time
                    
                    logger.info(f"✓ Button pressed: {BUTTON_NAMES[pin]}")
                    
                    # Trigger callback if registered
                    if pin in self.callbacks:
                        try:
                            self.callbacks[pin]()
                        except Exception as e:
                            logger.error(f"Error in callback for {BUTTON_NAMES[pin]}: {e}")
                    else:
                        logger.warning(f"⚠ No callback registered for {BUTTON_NAMES[pin]}")
            
            # Update last state AFTER checking
            self.last_state[pin] = current_state
    
    def is_button_pressed(self, button_pin):
        """
        Check if specific button is currently pressed (without callback)
        
        Args:
            button_pin: ButtonPin enum value
            
        Returns:
            bool: True if button pressed, False otherwise
        """
        return GPIO.input(button_pin) == GPIO.LOW
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup()
        logger.info("GPIO Button Handler cleaned up")

# ============================================
# Test Function
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("  PLTN Control Panel Button Test")
    print("="*60)
    print("Press any button to test. Ctrl+C to exit.")
    print()
    
    handler = ButtonHandler()
    
    try:
        while True:
            handler.check_all_buttons()
            time.sleep(0.01)  # 10ms polling
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        handler.cleanup()
