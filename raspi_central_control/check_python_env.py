"""
Check Python Environment and Module Installation
Quick diagnostic for luma.oled import issues
"""

import sys
import subprocess

print("="*60)
print("Python Environment Diagnostic")
print("="*60)

# 1. Python version
print(f"\n1. Python Version:")
print(f"   {sys.version}")
print(f"   Executable: {sys.executable}")

# 2. Python path
print(f"\n2. Python Path (sys.path):")
for i, path in enumerate(sys.path):
    print(f"   [{i}] {path}")

# 3. Check luma.oled
print(f"\n3. Checking luma.oled installation:")
try:
    import luma.oled
    print(f"   ✓ luma.oled found!")
    print(f"   Version: {luma.oled.__version__ if hasattr(luma.oled, '__version__') else 'Unknown'}")
    print(f"   Location: {luma.oled.__file__}")
except ImportError as e:
    print(f"   ✗ luma.oled NOT found!")
    print(f"   Error: {e}")

# 4. Check luma.core
print(f"\n4. Checking luma.core:")
try:
    import luma.core
    print(f"   ✓ luma.core found!")
    print(f"   Version: {luma.core.__version__ if hasattr(luma.core, '__version__') else 'Unknown'}")
    print(f"   Location: {luma.core.__file__}")
except ImportError as e:
    print(f"   ✗ luma.core NOT found!")
    print(f"   Error: {e}")

# 5. Check PIL/Pillow
print(f"\n5. Checking PIL/Pillow:")
try:
    import PIL
    print(f"   ✓ PIL found!")
    print(f"   Version: {PIL.__version__ if hasattr(PIL, '__version__') else 'Unknown'}")
    print(f"   Location: {PIL.__file__}")
except ImportError as e:
    print(f"   ✗ PIL NOT found!")
    print(f"   Error: {e}")

# 6. Check smbus2
print(f"\n6. Checking smbus2:")
try:
    import smbus2
    print(f"   ✓ smbus2 found!")
    print(f"   Version: {smbus2.__version__ if hasattr(smbus2, '__version__') else 'Unknown'}")
    print(f"   Location: {smbus2.__file__}")
except ImportError as e:
    print(f"   ✗ smbus2 NOT found!")
    print(f"   Error: {e}")

# 7. List installed packages
print(f"\n7. Checking pip list for luma packages:")
try:
    result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    print("   Installed luma packages:")
    for line in lines:
        if 'luma' in line.lower() or 'pillow' in line.lower() or 'smbus' in line.lower():
            print(f"   - {line}")
except Exception as e:
    print(f"   Error running pip list: {e}")

print("\n" + "="*60)
print("Diagnostic Complete")
print("="*60)
print("\nIf luma.oled shows 'NOT found' but pip shows 'already satisfied',")
print("the issue is likely:")
print("1. Wrong Python interpreter being used")
print("2. Module installed in different Python environment")
print("3. Need to use 'python3' instead of 'python'")
print("\nSolution: Run script with the SAME python that has luma.oled:")
print("  python3 test_oled_display_active.py")
