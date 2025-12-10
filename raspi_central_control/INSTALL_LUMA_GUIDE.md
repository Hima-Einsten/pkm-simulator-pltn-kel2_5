# Install luma.oled for All Python Versions

## 🎯 Goal
Install luma.oled library for **BOTH** Python 3.7 and Python 3.13 so it works everywhere.

---

## ✅ Solution: Install Everywhere

### **Method 1: Automatic Installation Script (Recommended)**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Make executable
chmod +x install_luma_all_python.sh

# Run installation
./install_luma_all_python.sh
```

This script will:
- ✅ Install for Python 3.7 (if available)
- ✅ Install for Python 3.13 (if available)
- ✅ Install in py37env virtual environment
- ✅ Verify all installations
- ✅ Show test commands

---

### **Method 2: Manual Installation (Step by Step)**

#### **Step 1: Install for Python 3.7**

```bash
# Check if python3.7 is available
which python3.7

# Install for Python 3.7
python3.7 -m pip install --user luma.oled pillow smbus2

# Verify
python3.7 -c "import luma.oled; print('✓ Python 3.7: OK')"
```

#### **Step 2: Install for Python 3.13 (default python3)**

```bash
# Check Python 3 version
python3 --version

# Install for Python 3 (3.13)
python3 -m pip install --user luma.oled pillow smbus2

# Verify
python3 -c "import luma.oled; print('✓ Python 3.13: OK')"
```

#### **Step 3: Install in Virtual Environment (py37env)**

```bash
# Navigate to project directory
cd ~/pkm-simulator-PLTN/raspi_central_control

# If py37env doesn't exist, create it
if [ ! -d "py37env" ]; then
    python3.7 -m venv py37env
fi

# Activate virtual environment
source py37env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install luma.oled
pip install luma.oled pillow smbus2

# Verify
python -c "import luma.oled; print('✓ Virtual env: OK')"

# Deactivate
deactivate
```

---

## 🔍 Troubleshooting

### **Problem 1: pip not found for python3.7**

```bash
# Install pip for Python 3.7
sudo apt update
sudo apt install python3.7 python3-pip

# Try again
python3.7 -m pip install --user luma.oled pillow smbus2
```

### **Problem 2: Permission denied**

```bash
# Use --user flag to install in user directory
python3.7 -m pip install --user luma.oled pillow smbus2
python3 -m pip install --user luma.oled pillow smbus2

# OR use sudo (not recommended, but works)
sudo python3.7 -m pip install luma.oled pillow smbus2
sudo python3 -m pip install luma.oled pillow smbus2
```

### **Problem 3: Module still not found after installation**

```bash
# Check where modules are installed
python3.7 -m pip show luma.oled
python3 -m pip show luma.oled

# Check Python path
python3.7 -c "import sys; print('\n'.join(sys.path))"
python3 -c "import sys; print('\n'.join(sys.path))"

# Force reinstall
python3.7 -m pip install --user --force-reinstall luma.oled
python3 -m pip install --user --force-reinstall luma.oled
```

### **Problem 4: Python 3.7 not installed**

```bash
# Install Python 3.7
sudo apt update
sudo apt install python3.7 python3.7-venv python3.7-dev

# Verify installation
python3.7 --version
```

---

## 📊 Installation Verification Matrix

After installation, verify all versions:

```bash
echo "Testing Python 3.7:"
python3.7 -c "import luma.oled; print('✓ OK')" 2>&1

echo ""
echo "Testing Python 3.13:"
python3 -c "import luma.oled; print('✓ OK')" 2>&1

echo ""
echo "Testing py37env:"
cd ~/pkm-simulator-PLTN/raspi_central_control
source py37env/bin/activate
python -c "import luma.oled; print('✓ OK')" 2>&1
deactivate
```

**Expected Output:**
```
Testing Python 3.7:
✓ OK

Testing Python 3.13:
✓ OK

Testing py37env:
✓ OK
```

---

## 🚀 Test OLED After Installation

### **Test with Python 3.7:**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Direct Python 3.7
python3.7 test_oled_simple.py

# Or with virtual environment
source py37env/bin/activate
python test_oled_simple.py
deactivate
```

### **Test with Python 3.13:**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Direct Python 3
python3 test_oled_simple.py
```

---

## 📋 Complete Installation Commands (Copy-Paste)

### **Quick Install - All Versions:**

```bash
# Navigate to project
cd ~/pkm-simulator-PLTN/raspi_central_control

# Install for Python 3.7
echo "Installing for Python 3.7..."
python3.7 -m pip install --user luma.oled pillow smbus2

# Install for Python 3.13 (default python3)
echo "Installing for Python 3.13..."
python3 -m pip install --user luma.oled pillow smbus2

# Install in virtual environment
echo "Installing in virtual environment..."
if [ -d "py37env" ]; then
    source py37env/bin/activate
    pip install luma.oled pillow smbus2
    deactivate
else
    python3.7 -m venv py37env
    source py37env/bin/activate
    pip install --upgrade pip
    pip install luma.oled pillow smbus2
    deactivate
fi

# Verify all installations
echo ""
echo "Verification:"
echo "Python 3.7:"
python3.7 -c "import luma.oled; print('  ✓ OK')"
echo "Python 3.13:"
python3 -c "import luma.oled; print('  ✓ OK')"
echo "Virtual env:"
source py37env/bin/activate
python -c "import luma.oled; print('  ✓ OK')"
deactivate

echo ""
echo "✅ Installation complete!"
```

---

## 🎯 Why Install for Both Versions?

| Scenario | Python Version | Why Needed |
|----------|---------------|------------|
| **Project scripts** | Python 3.7 | Original project environment |
| **System commands** | Python 3.13 | Default `python3` command |
| **Virtual env** | Python 3.7 | Isolated project environment |
| **Compatibility** | Both | Works regardless of which you use |

---

## ✅ Expected Final State

After successful installation:

```
~/.local/lib/python3.7/site-packages/
├── luma/
│   ├── core/
│   └── oled/
├── PIL/
└── smbus2/

~/.local/lib/python3.13/site-packages/
├── luma/
│   ├── core/
│   └── oled/
├── PIL/
└── smbus2/

~/pkm-simulator-PLTN/raspi_central_control/py37env/lib/python3.7/site-packages/
├── luma/
│   ├── core/
│   └── oled/
├── PIL/
└── smbus2/
```

All locations have luma.oled installed! ✅

---

## 📞 If Still Having Issues

Run diagnostic:

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Run full diagnostic
python3 check_python_env.py

# Check specific Python versions
echo "=== Python 3.7 ==="
python3.7 --version
python3.7 -m pip list | grep -i luma
python3.7 -c "import sys; print(sys.path)" 

echo ""
echo "=== Python 3.13 ==="
python3 --version
python3 -m pip list | grep -i luma
python3 -c "import sys; print(sys.path)"
```

---

## 🎉 Summary

**Problem:** luma.oled not available in Python 3.7 or 3.13

**Solution:** Install for ALL Python versions

**Quick Command:**
```bash
cd ~/pkm-simulator-PLTN/raspi_central_control
chmod +x install_luma_all_python.sh
./install_luma_all_python.sh
```

**Verify:**
```bash
python3.7 -c "import luma.oled; print('✓')"
python3 -c "import luma.oled; print('✓')"
```

**Test:**
```bash
python3.7 test_oled_simple.py
# atau
python3 test_oled_simple.py
```

---

**Status:** 🔧 Ready to install  
**Date:** 2024-12-10
