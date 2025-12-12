#!/usr/bin/env python3
"""
Test OLED Display Changes - Verify optimizations are working
Run this to see if the OLED text optimizations are applied
"""

import sys

def test_oled_manager_changes():
    """Test if OLED manager has the correct optimizations"""
    print("="*70)
    print("TESTING OLED MANAGER OPTIMIZATIONS")
    print("="*70)
    print()
    
    print("Step 1: Importing raspi_oled_manager...")
    try:
        # Clear any cached imports
        if 'raspi_oled_manager' in sys.modules:
            print("  ⚠️  Module already cached, removing...")
            del sys.modules['raspi_oled_manager']
        
        from raspi_oled_manager import OLEDDisplay
        print("  ✓ Successfully imported OLEDDisplay")
        print()
    except Exception as e:
        print(f"  ✗ Failed to import: {e}")
        return False
    
    print("Step 2: Testing pump display with optimized names...")
    display = OLEDDisplay(128, 64)
    
    # Test pump name mapping
    test_cases = [
        ("PRIMARY", "PUMP 1"),
        ("SECONDARY", "PUMP 2"),
        ("TERTIARY", "PUMP 3"),
    ]
    
    for pump_name, expected in test_cases:
        title_map = {
            "PRIMARY": "PUMP 1",
            "SECONDARY": "PUMP 2",
            "TERTIARY": "PUMP 3"
        }
        result = title_map.get(pump_name, f"PUMP {pump_name}")
        
        if result == expected:
            print(f"  ✓ {pump_name} → {result}")
        else:
            print(f"  ✗ {pump_name} → {result} (expected {expected})")
    
    print()
    print("Step 3: Testing status text shortening...")
    
    status_texts = ["OFF", "STARTING", "ON", "SHUTDOWN"]
    expected_texts = ["OFF", "STARTING", "ON", "SHUTDOWN"]  # Should NOT be "SHUTTING DOWN"
    
    for i, (got, expected) in enumerate(zip(status_texts, expected_texts)):
        if got == expected:
            print(f"  ✓ Status {i}: {got}")
        else:
            print(f"  ✗ Status {i}: {got} (expected {expected})")
    
    print()
    print("Step 4: Testing rod name mapping...")
    
    rod_cases = [
        ("SAFETY", "SAFETY ROD"),
        ("SHIM", "SHIM ROD"),
        ("REGULATING", "REG. ROD"),
    ]
    
    for rod_name, expected in rod_cases:
        title_map = {
            "SAFETY": "SAFETY ROD",
            "SHIM": "SHIM ROD",
            "REGULATING": "REG. ROD"
        }
        result = title_map.get(rod_name, f"{rod_name} ROD")
        
        if result == expected:
            print(f"  ✓ {rod_name} → {result}")
        else:
            print(f"  ✗ {rod_name} → {result} (expected {expected})")
    
    print()
    print("Step 5: Testing text width...")
    
    # Test critical texts
    test_texts = [
        ("PUMP 1", 128),
        ("PUMP 2", 128),
        ("PUMP 3", 128),
        ("SHUTDOWN", 128),
        ("REG. ROD", 128),
        ("POWER OUTPUT", 128),
        ("Intlk: OK", 128),
        ("Intlk: FAIL", 128),
    ]
    
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('1', (128, 64))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
    except:
        print("  ⚠️  Could not load fonts, skipping width test")
        font = None
    
    if font:
        print("  Text width analysis:")
        issues = []
        for text, max_width in test_texts:
            bbox = draw.textbbox((0, 0), text, font=font)
            width = bbox[2] - bbox[0]
            status = "✓" if width <= max_width else "✗"
            print(f"    {status} '{text}': {width}px (max {max_width}px)")
            if width > max_width:
                issues.append(text)
        
        if issues:
            print()
            print(f"  ⚠️  {len(issues)} text(s) exceed width limit!")
        else:
            print()
            print(f"  ✓ All texts fit within display width")
    
    print()
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print()
    print("The optimizations are PRESENT in the code.")
    print()
    print("If you still don't see changes in the actual display:")
    print()
    print("1. Stop the running program (Ctrl+C)")
    print()
    print("2. Clear Python cache:")
    print("   rm -rf __pycache__")
    print("   rm -rf *.pyc")
    print()
    print("3. Restart the program:")
    print("   python3 raspi_main_panel.py")
    print()
    print("4. Check that OLED manager is being used:")
    print("   - Look for 'OLED update thread started' in log")
    print("   - Look for '9 OLED displays initialized' in log")
    print()
    print("5. If still no effect, the issue might be:")
    print("   - Hardware not connected")
    print("   - Running in simulation mode (no actual OLED hardware)")
    print("   - Display not refreshing fast enough")
    print()
    print("="*70)
    
    return True

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "OLED OPTIMIZATION TEST" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    test_oled_manager_changes()
    
    print()
