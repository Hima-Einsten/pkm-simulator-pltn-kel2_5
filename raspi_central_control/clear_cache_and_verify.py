#!/usr/bin/env python3
"""
Clear Python Cache and Verify OLED Manager Changes
This script removes all Python cache files to ensure changes take effect
"""

import os
import sys
import shutil

def remove_pycache():
    """Remove all __pycache__ directories"""
    print("="*70)
    print("CLEARING PYTHON CACHE")
    print("="*70)
    print()
    
    removed_count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing: {pycache_path}")
            shutil.rmtree(pycache_path)
            removed_count += 1
    
    # Also remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                print(f"Removing: {pyc_path}")
                os.remove(pyc_path)
                removed_count += 1
    
    print()
    if removed_count > 0:
        print(f"✓ Removed {removed_count} cache items")
    else:
        print("✓ No cache files found")
    print()

def verify_oled_changes():
    """Verify OLED manager has the optimizations"""
    print("="*70)
    print("VERIFYING OLED MANAGER CHANGES")
    print("="*70)
    print()
    
    try:
        with open('raspi_oled_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for optimizations
        checks = [
            ('"PUMP 1"', 'Pump name optimization'),
            ('"SHUTDOWN"', 'Status text shortening'),
            ('"REG. ROD"', 'Rod name shortening'),
            ('"POWER OUTPUT"', 'Power display shortening'),
            ('"Intlk: FAIL"', 'Interlock text shortening'),
        ]
        
        all_found = True
        for check_text, description in checks:
            if check_text in content:
                print(f"✓ {description}: Found")
            else:
                print(f"✗ {description}: NOT FOUND")
                all_found = False
        
        print()
        if all_found:
            print("✓ All OLED optimizations are present in the file")
        else:
            print("⚠️  Some optimizations are missing!")
        print()
        
        return all_found
        
    except FileNotFoundError:
        print("✗ raspi_oled_manager.py not found!")
        print("   Make sure you run this from raspi_central_control directory")
        return False

def check_imports():
    """Check if main program imports the manager correctly"""
    print("="*70)
    print("CHECKING MAIN PROGRAM IMPORTS")
    print("="*70)
    print()
    
    try:
        with open('raspi_main_panel.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'from raspi_oled_manager import' in content or 'import raspi_oled_manager' in content:
            print("✓ Main program imports raspi_oled_manager")
            
            # Check if OLEDManager is used
            if 'OLEDManager' in content:
                print("✓ OLEDManager class is used")
            else:
                print("⚠️  OLEDManager class may not be instantiated")
        else:
            print("✗ Main program does NOT import raspi_oled_manager!")
            print("   This might be the issue!")
        
        print()
        
    except FileNotFoundError:
        print("✗ raspi_main_panel.py not found!")
        print()

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "OLED CACHE CLEANUP & VERIFICATION" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    # Step 1: Remove cache
    remove_pycache()
    
    # Step 2: Verify changes
    changes_ok = verify_oled_changes()
    
    # Step 3: Check imports
    check_imports()
    
    # Summary
    print("="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print()
    
    if changes_ok:
        print("1. Python cache has been cleared")
        print("2. OLED optimizations are in place")
        print("3. Restart your PLTN simulator program:")
        print()
        print("   # Stop current program (Ctrl+C)")
        print("   # Then restart:")
        print("   python3 raspi_main_panel.py")
        print()
        print("4. If still no effect, check:")
        print("   - Are you running from the correct directory?")
        print("   - Is raspi_oled_manager.py being imported?")
        print("   - Check for any error messages in the log")
    else:
        print("⚠️  OLED optimizations not properly applied!")
        print("   Please check the file manually")
    
    print()
    print("="*70)
    print()

if __name__ == "__main__":
    main()
