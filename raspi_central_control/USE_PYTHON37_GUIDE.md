# Using Python 3.7 for PLTN Simulator Project

## ✅ Correct Approach: Use Python 3.7

Your project is designed for **Python 3.7**, and luma.oled is already installed there.

---

## 🎯 Solution: Use Python 3.7 Virtual Environment

### **Method 1: Using Wrapper Script (Easiest)**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Make executable
chmod +x run_with_python37.sh

# Run any test with Python 3.7
./run_with_python37.sh test_oled_simple.py
./run_with_python37.sh test_oled_display_active.py
./run_with_python37.sh check_python_env.py
```

### **Method 2: Activate Virtual Environment Manually**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Activate Python 3.7 environment
source py37env/bin/activate

# You should see (py37env) in your prompt
# Now run scripts with python (not python3)
python test_oled_simple.py
python test_oled_display_active.py

# When done, deactivate
deactivate
```

### **Method 3: Use python3.7 Directly (If Available)**

```bash
# Check if python3.7 is available
which python3.7

# Run scripts directly with python3.7
python3.7 test_oled_simple.py
python3.7 test_oled_display_active.py
```

---

## 🔍 Why Python 3.7?

From your diagnostic output:

```
pip list shows:
- luma.oled installed in: ~/.local/lib/python3.7/site-packages
- Libraries work with Python 3.7

python3 command:
- Points to Python 3.13
- Cannot see Python 3.7 packages
```

**Project uses Python 3.7:**
- Virtual environment: `py37env/`
- All dependencies installed for Python 3.7
- Compatibility tested with Python 3.7

---

## 📋 Complete Test Procedure

### **Step 1: Activate Python 3.7 Environment**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control
source py37env/bin/activate
```

### **Step 2: Verify Installation**

```bash
# Check Python version (should be 3.7.x)
python --version

# Check if luma.oled is available
python -c "import luma.oled; print('✓ luma.oled OK')"
python -c "import smbus2; print('✓ smbus2 OK')"
python -c "import PIL; print('✓ PIL OK')"
```

### **Step 3: Run OLED Tests**

```bash
# Simple test
python test_oled_simple.py

# Full test with display
python test_oled_display_active.py

# Interactive menu
python test_oled_display_active.py --menu
```

### **Step 4: Deactivate When Done**

```bash
deactivate
```

---

## 🛠️ If py37env is Missing or Broken

### **Recreate Virtual Environment:**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Remove old environment
rm -rf py37env

# Create new Python 3.7 environment
python3.7 -m venv py37env

# Activate it
source py37env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install luma.oled pillow smbus2

# Test
python -c "import luma.oled; print('Success!')"
```

---

## 🔧 Troubleshooting

### **Problem: python3.7 not found**

```bash
# Check if Python 3.7 is installed
dpkg -l | grep python3.7

# If not installed, install it
sudo apt update
sudo apt install python3.7 python3.7-venv python3.7-dev
```

### **Problem: Virtual environment won't activate**

```bash
# Check if activation script exists
ls -la py37env/bin/activate

# If missing, recreate environment
rm -rf py37env
python3.7 -m venv py37env
source py37env/bin/activate
```

### **Problem: luma.oled not found in virtual environment**

```bash
# Activate environment first
source py37env/bin/activate

# Install luma.oled
pip install luma.oled pillow smbus2

# Verify
python -c "import luma.oled; print('OK')"
```

---

## 📊 Python Version Comparison

| Aspect | Python 3.7 | Python 3.13 |
|--------|-----------|-------------|
| **Project compatibility** | ✅ Designed for this | ❌ Not tested |
| **Libraries installed** | ✅ All ready | ❌ Need reinstall |
| **Virtual environment** | ✅ py37env exists | ❌ Not set up |
| **Recommended** | ✅ **Use this** | ❌ Avoid |

---

## ✅ Quick Start Commands

```bash
# ONE-LINER: Test OLED with Python 3.7
cd ~/pkm-simulator-PLTN/raspi_central_control && source py37env/bin/activate && python test_oled_simple.py

# Or use wrapper script
cd ~/pkm-simulator-PLTN/raspi_central_control
chmod +x run_with_python37.sh
./run_with_python37.sh test_oled_simple.py
```

---

## 🎯 Expected Output (with Python 3.7)

```bash
(py37env) pkm@raspberrypi4:~/pkm-simulator-PLTN/raspi_central_control$ python test_oled_simple.py

✓ smbus2 imported successfully
✓ luma.oled imported successfully
============================================================
SIMPLE OLED TEST
============================================================
✓ I2C Bus 1 opened

1. Testing TCA9548A Multiplexers...
   ✓ TCA9548A found at 0x70
   ✓ TCA9548A found at 0x71

2. Testing OLEDs on each channel...

   Testing: PRESSURIZER (MUX 0x70, Ch1)
      ✓ Channel selected
      ✓ OLED responds at 0x3C
      → Initializing display...
      → Clearing display...
      → Drawing test pattern...
      ✓ Display ACTIVE - Check OLED screen!  ← LAYAR HIDUP! ✨

   Testing: PUMP PRIMARY (MUX 0x70, Ch2)
      ✓ Channel selected
      ✓ OLED responds at 0x3C
      → Initializing display...
      → Clearing display...
      → Drawing test pattern...
      ✓ Display ACTIVE - Check OLED screen!  ← LAYAR HIDUP! ✨

...
```

---

## 📚 Main Project Files

All main project scripts should be run with Python 3.7:

```bash
# Activate environment
source py37env/bin/activate

# Run main system
python raspi_main_panel.py

# Run specific tests
python test_2esp_architecture.py
python test_all_gpio.py

# When done
deactivate
```

---

## ✅ Summary

**Problem:** Used Python 3.13 instead of Python 3.7

**Solution:** Use Python 3.7 virtual environment

**Commands:**
```bash
cd ~/pkm-simulator-PLTN/raspi_central_control
source py37env/bin/activate
python test_oled_simple.py
```

**Or use wrapper:**
```bash
./run_with_python37.sh test_oled_simple.py
```

---

**Status:** ✅ Ready to use  
**Python Version:** 3.7 (from py37env)  
**Date:** 2024-12-10
