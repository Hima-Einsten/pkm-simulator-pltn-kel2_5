#!/bin/bash
# Check System User Configuration
# Run this on Raspberry Pi to diagnose user issue

echo "=========================================="
echo "DIAGNOSTIC: Check User Configuration"
echo "=========================================="
echo ""

echo "1. Current user:"
whoami
echo ""

echo "2. User ID:"
id
echo ""

echo "3. Check if 'pi' user exists:"
id pi 2>/dev/null && echo "✅ User 'pi' exists" || echo "❌ User 'pi' NOT found!"
echo ""

echo "4. List all users:"
cat /etc/passwd | grep -E "/(home|root)" | cut -d: -f1
echo ""

echo "5. Current Python path:"
which python
which python3
echo ""

echo "6. Python version:"
python --version 2>&1 || echo "python not found"
python3 --version 2>&1 || echo "python3 not found"
echo ""

echo "7. Check pygame installation:"
python -c "import pygame; print('pygame OK for python')" 2>&1 || echo "pygame NOT installed for python"
python3 -c "import pygame; print('pygame OK for python3')" 2>&1 || echo "pygame NOT installed for python3"
echo ""

echo "=========================================="
echo "RECOMMENDATION:"
echo ""
echo "If user is NOT 'pi', update service file with:"
echo "  User=$(whoami)"
echo "  Group=$(id -gn)"
echo "=========================================="
