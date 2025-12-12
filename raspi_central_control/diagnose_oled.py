#!/usr/bin/env python3
"""
OLED Display Diagnostic Tool
Cek kenapa perubahan tidak terlihat di display
"""

import sys
import os

print("\n")
print("╔" + "="*68 + "╗")
print("║" + " "*18 + "OLED DISPLAY DIAGNOSTIC" + " "*27 + "║")
print("╚" + "="*68 + "╝")
print()

# === TEST 1: File Check ===
print("="*70)
print("TEST 1: Checking Source File")
print("="*70)
print()

file_path = 'raspi_oled_manager.py'
if not os.path.exists(file_path):
    print(f"✗ File not found: {file_path}")
    print("  Are you in raspi_central_control directory?")
    sys.exit(1)

print(f"✓ File exists: {file_path}")

# Read file content
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for old text (should NOT exist)
old_texts = [
    'PUMP PRIMARY"',
    'PUMP SECONDARY"', 
    'PUMP TERTIARY"',
    'SHUTTING DOWN"',
    'REGULATING ROD"',
    'ELECTRICAL POWER"'
]

found_old = []
for old_text in old_texts:
    if old_text in content:
        found_old.append(old_text)

if found_old:
    print()
    print("✗ PROBLEM: File contains OLD text that should be changed!")
    print("  Found:")
    for text in found_old:
        print(f"    - {text}")
    print()
    print("  The file was NOT properly edited!")
    print("  Please check if you're editing the correct file.")
    sys.exit(1)
else:
    print("✓ No old text found (good!)")

# Check for new text (should exist)
new_texts = [
    '"PUMP 1"',
    '"PUMP 2"',
    '"PUMP 3"',
    '"SHUTDOWN"',
    '"REG. ROD"',
    '"POWER OUTPUT"'
]

found_new = []
for new_text in new_texts:
    if new_text in content:
        found_new.append(new_text)

print(f"✓ Found {len(found_new)}/{len(new_texts)} new optimizations")

if len(found_new) < len(new_texts):
    print("  Missing:")
    for text in new_texts:
        if text not in content:
            print(f"    ✗ {text}")
else:
    print("  All optimizations present!")

print()

# === TEST 2: Module Import ===
print("="*70)
print("TEST 2: Testing Module Import")
print("="*70)
print()

# Clear cache first
if 'raspi_oled_manager' in sys.modules:
    print("⚠️  Module already loaded, removing from cache...")
    del sys.modules['raspi_oled_manager']

try:
    from raspi_oled_manager import OLEDManager, OLEDDisplay
    print("✓ Module imported successfully")
    
    # Check what's actually in the loaded module
    import inspect
    
    # Get the source of update_pump_display
    source = inspect.getsource(OLEDManager.update_pump_display)
    
    if '"PUMP 1"' in source:
        print("✓ Loaded module contains 'PUMP 1' (CORRECT)")
    else:
        print("✗ Loaded module does NOT contain 'PUMP 1' (WRONG!)")
        print("  This means Python is loading from cache!")
        
    if '"SHUTDOWN"' in source:
        print("✓ Loaded module contains 'SHUTDOWN' (CORRECT)")
    else:
        print("✗ Loaded module does NOT contain 'SHUTDOWN' (WRONG!)")
        
except Exception as e:
    print(f"✗ Failed to import: {e}")
    print()
    sys.exit(1)

print()

# === TEST 3: Runtime Test ===
print("="*70)
print("TEST 3: Runtime Simulation")
print("="*70)
print()

try:
    # Create a mock display
    display = OLEDDisplay(128, 64)
    print("✓ Created OLEDDisplay instance")
    
    # Simulate what would be displayed
    pump_names = ["PRIMARY", "SECONDARY", "TERTIARY"]
    title_map = {
        "PRIMARY": "PUMP 1",
        "SECONDARY": "PUMP 2",
        "TERTIARY": "PUMP 3"
    }
    
    print()
    print("Testing pump name mapping:")
    for pump in pump_names:
        result = title_map.get(pump, f"PUMP {pump}")
        print(f"  {pump} → {result}")
    
    print()
    print("Testing status text:")
    status_texts = ["OFF", "STARTING", "ON", "SHUTDOWN"]
    for i, status in enumerate(status_texts):
        print(f"  Status {i}: {status}")
    
    print()
    print("✓ All runtime mappings correct!")
    
except Exception as e:
    print(f"✗ Runtime test failed: {e}")

print()

# === TEST 4: Cache Check ===
print("="*70)
print("TEST 4: Checking for Cache Files")
print("="*70)
print()

import glob

pyc_files = glob.glob('*.pyc') + glob.glob('**/*.pyc', recursive=True)
pycache_dirs = glob.glob('**/__pycache__', recursive=True)

if pyc_files:
    print(f"⚠️  Found {len(pyc_files)} .pyc files:")
    for pyc in pyc_files[:5]:  # Show first 5
        print(f"    {pyc}")
    if len(pyc_files) > 5:
        print(f"    ... and {len(pyc_files) - 5} more")
else:
    print("✓ No .pyc files found")

if pycache_dirs:
    print(f"⚠️  Found {len(pycache_dirs)} __pycache__ directories:")
    for pycdir in pycache_dirs[:3]:
        print(f"    {pycdir}")
else:
    print("✓ No __pycache__ directories found")

print()

# === SUMMARY ===
print("="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)
print()

if len(found_new) == len(new_texts) and not found_old:
    print("✅ SOURCE FILE: CORRECT")
    print("   All optimizations are in the file.")
    print()
    
    if pyc_files or pycache_dirs:
        print("⚠️  CACHE DETECTED")
        print("   Python cache files exist. These may cause old code to run.")
        print()
        print("   SOLUTION:")
        print("   1. Delete cache:")
        print("      rm -rf __pycache__")
        print("      find . -name '*.pyc' -delete")
        print()
        print("   2. Stop your program (Ctrl+C)")
        print()
        print("   3. Restart:")
        print("      python3 raspi_main_panel.py")
        print()
    else:
        print("✅ NO CACHE: Clean")
        print()
        print("   If display still shows old text, the issue is:")
        print()
        print("   A. Program not restarted")
        print("      → Stop program (Ctrl+C) and restart")
        print()
        print("   B. Wrong file being used")
        print("      → Check working directory")
        print("      → Run: pwd")
        print("      → Should be: .../pkm-simulator-PLTN/raspi_central_control")
        print()
        print("   C. Display hardware lag")
        print("      → Wait 5-10 seconds after restart")
        print("      → Display updates every 200ms")
        print()
        print("   D. Running in simulation mode")
        print("      → Check log for 'OLED displays initialized'")
        print("      → If not found, hardware not connected")
        print()
else:
    print("✗ SOURCE FILE: PROBLEM")
    print("   File does NOT have all optimizations!")
    print()
    print("   This should not happen. The edits were not saved properly.")
    print()

print("="*70)
print()

print("NEXT STEPS:")
print()
print("1. Run this to clear cache:")
print("   rm -rf __pycache__ && find . -name '*.pyc' -delete")
print()
print("2. Stop the running program:")
print("   pkill -f raspi_main_panel.py")
print()
print("3. Restart:")
print("   cd /path/to/pkm-simulator-PLTN/raspi_central_control")
print("   python3 raspi_main_panel.py")
print()
print("4. Watch the OLED displays for 10 seconds")
print()
print("5. If STILL showing old text:")
print("   - Take a photo of the display")
print("   - Check the log file: tail -f pltn_simulator.log")
print("   - Look for 'OLED' related messages")
print()

print("="*70)
print()
