#!/usr/bin/env python3
"""
OLED Display Test - Test all display conditions during simulation
Tests all 9 OLED displays with various simulation states
"""

import sys
import time
import logging
from PIL import Image, ImageDraw, ImageFont

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_text_width():
    """Test if text fits in 128px OLED display"""
    print("="*70)
    print("OLED TEXT WIDTH TEST (128x64 display)")
    print("="*70)
    print()
    
    # Create test image
    img = Image.new('1', (128, 64))
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
        print("✓ Using TrueType fonts")
    except:
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
        print("✓ Using default fonts")
    
    print()
    
    # Test texts that appear in displays
    test_cases = [
        ("PRESSURIZER", font),
        ("PUMP PRIMARY", font),
        ("PUMP SECONDARY", font),
        ("PUMP TERTIARY", font),
        ("SAFETY ROD", font),
        ("SHIM ROD", font),
        ("REGULATING ROD", font),
        ("ELECTRICAL POWER", font),
        ("SYSTEM STATUS", font),
        ("200.0 bar", font_large),
        ("SHUTTING DOWN", font_large),
        ("!! CRITICAL !!", font),
        ("! WARNING !", font),
        ("Interlock: NOT OK", font),
        ("Turbine: SHUTDOWN", font),
    ]
    
    print("Text Width Analysis:")
    print("-" * 70)
    issues = []
    
    for text, test_font in test_cases:
        bbox = draw.textbbox((0, 0), text, font=test_font)
        width = bbox[2] - bbox[0]
        status = "✓ OK" if width <= 128 else "✗ TOO WIDE"
        font_type = "LARGE" if test_font == font_large else "NORMAL"
        
        print(f"{text:25s} [{font_type:6s}]: {width:3d}px {status}")
        
        if width > 128:
            issues.append((text, width, font_type))
    
    print("-" * 70)
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} text(s) that may be cut off:")
        for text, width, font_type in issues:
            excess = width - 128
            print(f"  • '{text}' is {excess}px too wide ({font_type})")
    else:
        print("\n✓ All texts fit within 128px display width")
    
    print()
    return len(issues) == 0


def test_display_scenarios():
    """Test various simulation scenarios"""
    print("="*70)
    print("OLED DISPLAY SCENARIO TEST")
    print("="*70)
    print()
    
    try:
        from raspi_oled_manager import OLEDDisplay
        print("✓ OLED Manager module loaded")
    except Exception as e:
        print(f"✗ Failed to load OLED module: {e}")
        return
    
    print()
    
    # Create test display
    display = OLEDDisplay(128, 64)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Normal Operation',
            'pressure': 155.0,
            'warning': False,
            'critical': False,
            'pump_status': 2,  # ON
            'rod_position': 50,
            'power_kw': 100000,  # 100 MWe
        },
        {
            'name': 'High Pressure Warning',
            'pressure': 185.0,
            'warning': True,
            'critical': False,
            'pump_status': 2,
            'rod_position': 75,
            'power_kw': 200000,
        },
        {
            'name': 'Critical Pressure',
            'pressure': 198.0,
            'warning': False,
            'critical': True,
            'pump_status': 3,  # SHUTTING DOWN
            'rod_position': 0,
            'power_kw': 50000,
        },
        {
            'name': 'Maximum Pressure (200 bar)',
            'pressure': 200.0,
            'warning': False,
            'critical': True,
            'pump_status': 3,
            'rod_position': 0,
            'power_kw': 0,
        },
        {
            'name': 'Startup Sequence',
            'pressure': 20.0,
            'warning': False,
            'critical': False,
            'pump_status': 1,  # STARTING
            'rod_position': 25,
            'power_kw': 10000,
        },
        {
            'name': 'Shutdown Sequence',
            'pressure': 80.0,
            'warning': False,
            'critical': False,
            'pump_status': 3,  # SHUTTING DOWN
            'rod_position': 10,
            'power_kw': 30000,
        },
    ]
    
    print("Testing Display Scenarios:")
    print("-" * 70)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Pressure: {scenario['pressure']:.1f} bar")
        print(f"   Pump Status: {['OFF', 'STARTING', 'ON', 'SHUTTING DOWN'][scenario['pump_status']]}")
        print(f"   Rod Position: {scenario['rod_position']}%")
        print(f"   Power: {scenario['power_kw']/1000:.1f} MWe")
        
        # Test Pressurizer Display
        display.clear()
        display.draw_text_centered("PRESSURIZER", 0, display.font)
        pressure_text = f"{scenario['pressure']:.1f} bar"
        display.draw_text_centered(pressure_text, 15, display.font_large)
        
        if scenario['critical']:
            display.draw_text_centered("!! CRITICAL !!", 35, display.font)
        elif scenario['warning']:
            display.draw_text_centered("! WARNING !", 35, display.font)
        else:
            display.draw_text_centered("NORMAL", 35, display.font)
        
        # Check if content fits
        bbox = display.draw.textbbox((0, 0), pressure_text, font=display.font_large)
        width = bbox[2] - bbox[0]
        fits = "✓" if width <= 128 else "✗"
        print(f"   Pressure text width: {width}px {fits}")
        
        # Test Pump Display
        display.clear()
        status_texts = ["OFF", "STARTING", "ON", "SHUTTING DOWN"]
        status_text = status_texts[scenario['pump_status']]
        display.draw_text_centered("PUMP PRIMARY", 0, display.font)
        display.draw_text_centered(status_text, 15, display.font_large)
        
        bbox = display.draw.textbbox((0, 0), status_text, font=display.font_large)
        width = bbox[2] - bbox[0]
        fits = "✓" if width <= 128 else "✗"
        print(f"   Pump status text width: {width}px {fits}")
        
        # Test Power Display
        display.clear()
        display.draw_text_centered("ELECTRICAL POWER", 0, display.font)
        power_mwe = scenario['power_kw'] / 1000.0
        power_text = f"{power_mwe:.1f} MWe"
        display.draw_text_centered(power_text, 20, display.font_large)
        
        bbox = display.draw.textbbox((0, 0), power_text, font=display.font_large)
        width = bbox[2] - bbox[0]
        fits = "✓" if width <= 128 else "✗"
        print(f"   Power text width: {width}px {fits}")
    
    print()
    print("-" * 70)
    print("✓ All scenarios tested successfully")
    print()


def test_live_simulation():
    """Test OLED displays with live simulation"""
    print("="*70)
    print("LIVE OLED SIMULATION TEST")
    print("="*70)
    print()
    
    try:
        from raspi_oled_manager import OLEDDisplay
        print("✓ OLED Manager module loaded")
    except Exception as e:
        print(f"✗ Failed to load OLED module: {e}")
        return
    
    print()
    print("Running 30-second simulation with various states...")
    print("This simulates a complete reactor cycle:")
    print("  1. Startup (0-10s)")
    print("  2. Normal operation (10-20s)")
    print("  3. Overload warning (20-25s)")
    print("  4. Shutdown (25-30s)")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    display = OLEDDisplay(128, 64)
    start_time = time.time()
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            # Simulate different phases
            if elapsed < 10:
                # Startup phase
                phase = "STARTUP"
                pressure = 20 + (elapsed / 10) * 135  # 20 -> 155 bar
                pump_status = 1  # STARTING
                rod_position = int((elapsed / 10) * 50)  # 0 -> 50%
                power_kw = (elapsed / 10) * 100000  # 0 -> 100 MWe
                warning = False
                critical = False
                
            elif elapsed < 20:
                # Normal operation
                phase = "NORMAL"
                pressure = 155.0
                pump_status = 2  # ON
                rod_position = 50
                power_kw = 100000
                warning = False
                critical = False
                
            elif elapsed < 25:
                # Overload warning
                phase = "WARNING"
                t = (elapsed - 20) / 5
                pressure = 155 + t * 30  # 155 -> 185 bar
                pump_status = 2
                rod_position = 50 + int(t * 30)  # 50 -> 80%
                power_kw = 100000 + t * 100000  # 100 -> 200 MWe
                warning = True
                critical = False
                
            elif elapsed < 30:
                # Shutdown
                phase = "SHUTDOWN"
                t = (elapsed - 25) / 5
                pressure = 185 - t * 165  # 185 -> 20 bar
                pump_status = 3  # SHUTTING DOWN
                rod_position = int(80 - t * 80)  # 80 -> 0%
                power_kw = 200000 - t * 200000  # 200 -> 0 MWe
                warning = False
                critical = False
                
            else:
                print("\n✓ Simulation complete (30 seconds)")
                break
            
            # Update display simulation
            display.clear()
            display.draw_text_centered("PRESSURIZER", 0, display.font)
            pressure_text = f"{pressure:.1f} bar"
            display.draw_text_centered(pressure_text, 15, display.font_large)
            
            if critical:
                display.draw_text_centered("!! CRITICAL !!", 35, display.font)
            elif warning:
                display.draw_text_centered("! WARNING !", 35, display.font)
            else:
                display.draw_text_centered("NORMAL", 35, display.font)
            
            # Progress bar
            display.draw_progress_bar(10, 50, 108, 8, pressure, 200)
            
            # Print status
            power_mwe = power_kw / 1000
            status_line = f"[{phase:8s}] P:{pressure:6.1f}bar  Rod:{rod_position:3d}%  Pwr:{power_mwe:6.1f}MWe"
            print(f"\r{status_line}", end='', flush=True)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user")
    
    print()


def main():
    """Main test function"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "PLTN OLED DISPLAY TEST SUITE" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    # Test 1: Text width
    test_text_width()
    time.sleep(1)
    
    # Test 2: Display scenarios
    test_display_scenarios()
    time.sleep(1)
    
    # Test 3: Live simulation
    test_live_simulation()
    
    print()
    print("="*70)
    print("All OLED tests completed!")
    print("="*70)
    print()


if __name__ == "__main__":
    main()
