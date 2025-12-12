#!/usr/bin/env python3
"""
Force Reload OLED Manager - Memastikan perubahan diterapkan
"""

import sys
import os

print("="*70)
print("FORCE RELOAD OLED MANAGER MODULE")
print("="*70)
print()

# Step 1: Remove any cached modules
print("Step 1: Clearing module cache...")
modules_to_clear = [
    'raspi_oled_manager',
    'raspi_tca9548a',
    'raspi_main_panel'
]

for module in modules_to_clear:
    if module in sys.modules:
        print(f"  Removing {module} from cache...")
        del sys.modules[module]
        
print("  ✓ Module cache cleared")
print()

# Step 2: Remove .pyc files
print("Step 2: Removing bytecode files...")
import glob
pyc_files = glob.glob('*.pyc') + glob.glob('__pycache__/*.pyc')
for pyc in pyc_files:
    try:
        os.remove(pyc)
        print(f"  Removed: {pyc}")
    except:
        pass

if os.path.exists('__pycache__'):
    import shutil
    try:
        shutil.rmtree('__pycache__')
        print("  ✓ __pycache__ directory removed")
    except:
        print("  ⚠️  Could not remove __pycache__")

print()

# Step 3: Import and verify
print("Step 3: Importing fresh module...")
try:
    from raspi_oled_manager import OLEDManager, OLEDDisplay
    print("  ✓ Module imported successfully")
    print()
    
    # Step 4: Verify changes
    print("Step 4: Verifying optimizations...")
    
    # Create a test display
    display = OLEDDisplay(128, 64)
    
    # Check if the code has the changes
    import inspect
    source = inspect.getsource(OLEDManager.update_pump_display)
    
    checks = [
        ('"PUMP 1"' in source, 'Pump 1 mapping'),
        ('"PUMP 2"' in source, 'Pump 2 mapping'),
        ('"PUMP 3"' in source, 'Pump 3 mapping'),
        ('"SHUTDOWN"' in source, 'Shutdown text'),
    ]
    
    all_ok = True
    for check, desc in checks:
        if check:
            print(f"  ✓ {desc}: FOUND")
        else:
            print(f"  ✗ {desc}: NOT FOUND")
            all_ok = False
    
    print()
    
    if all_ok:
        print("="*70)
        print("✅ SUCCESS - All optimizations are in the loaded module!")
        print("="*70)
        print()
        print("Next steps:")
        print("1. Make sure your Raspberry Pi program is STOPPED")
        print("2. Run this command to restart:")
        print()
        print("   sudo python3 raspi_main_panel.py")
        print()
        print("3. Watch for log messages:")
        print("   - '9 OLED displays initialized'")
        print("   - 'OLED update thread started'")
        print()
        print("4. Check the actual OLED displays")
        print()
    else:
        print("="*70)
        print("⚠️  PROBLEM - Changes not found in module!")
        print("="*70)
        print()
        print("This means the file may not be saved correctly.")
        print("Try:")
        print("1. Open raspi_oled_manager.py in editor")
        print("2. Search for 'PUMP PRIMARY' - should NOT be found")
        print("3. Search for 'PUMP 1' - should be found")
        print("4. If not found, file was not saved properly")
        print()
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    print()
    print("  This might mean:")
    print("  - You're not in the raspi_central_control directory")
    print("  - File permissions issue")
    print("  - Missing dependencies")
    print()

print()
print("="*70)
print()
