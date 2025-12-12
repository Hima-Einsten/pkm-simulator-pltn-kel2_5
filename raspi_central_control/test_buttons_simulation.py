#!/usr/bin/env python3
"""
Test Button Functionality - Without ESP32
Test apakah button callbacks berfungsi dengan benar
"""

import sys
import time
import logging

# Setup logging untuk test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_button_simulation():
    """Test button functionality in simulation mode"""
    
    print("="*70)
    print("PLTN BUTTON TEST - Simulation Mode")
    print("="*70)
    print()
    
    # Import modules
    try:
        from raspi_gpio_buttons import ButtonPin, ButtonHandler
        print("✓ GPIO Button module loaded")
    except Exception as e:
        print(f"✗ Failed to load button module: {e}")
        return
    
    # Simulate state
    class SimulatorState:
        def __init__(self):
            self.reactor_started = False
            self.pressure = 0.0
            self.pump_primary_status = 0
            self.safety_rod = 0
            self.shim_rod = 0
            
    state = SimulatorState()
    
    # Create button handler
    button_handler = ButtonHandler()
    
    # Register test callbacks
    def on_start():
        state.reactor_started = True
        print(f"  → State: reactor_started = {state.reactor_started}")
    
    def on_pressure_up():
        if not state.reactor_started:
            print("  → Blocked: Reactor not started!")
            return
        state.pressure = min(state.pressure + 5.0, 200.0)
        print(f"  → State: pressure = {state.pressure:.1f} bar")
    
    def on_pump_on():
        if not state.reactor_started:
            print("  → Blocked: Reactor not started!")
            return
        state.pump_primary_status = 1
        print(f"  → State: pump_primary_status = {state.pump_primary_status}")
    
    def on_rod_up():
        if not state.reactor_started:
            print("  → Blocked: Reactor not started!")
            return
        state.shim_rod = min(state.shim_rod + 5, 100)
        print(f"  → State: shim_rod = {state.shim_rod}%")
    
    button_handler.register_callback(ButtonPin.REACTOR_START, on_start)
    button_handler.register_callback(ButtonPin.PRESSURE_UP, on_pressure_up)
    button_handler.register_callback(ButtonPin.PUMP_PRIMARY_ON, on_pump_on)
    button_handler.register_callback(ButtonPin.SHIM_ROD_UP, on_rod_up)
    
    print(f"✓ {len(button_handler.callbacks)} callbacks registered")
    print()
    
    # Test instructions
    print("TEST SEQUENCE:")
    print("-" * 70)
    print("1. Try pressing PRESSURE UP button (should be blocked)")
    print("2. Press REACTOR START button (GPIO 17)")
    print("3. Try pressing PRESSURE UP button again (should work)")
    print("4. Press PUMP PRIMARY ON button (GPIO 5)")
    print("5. Press SHIM ROD UP button (GPIO 12)")
    print()
    print("Press Ctrl+C to exit")
    print("=" * 70)
    print()
    
    # Monitor loop
    try:
        while True:
            button_handler.check_all_buttons()
            time.sleep(0.01)  # 10ms polling
            
    except KeyboardInterrupt:
        print("\n\nTest terminated by user")
        print("\nFinal State:")
        print(f"  reactor_started: {state.reactor_started}")
        print(f"  pressure: {state.pressure:.1f} bar")
        print(f"  pump_primary_status: {state.pump_primary_status}")
        print(f"  shim_rod: {state.shim_rod}%")
        button_handler.cleanup()

if __name__ == "__main__":
    test_button_simulation()
