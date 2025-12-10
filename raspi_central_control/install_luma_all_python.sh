#!/bin/bash
# Install luma.oled for ALL Python versions
# This ensures the library works with both Python 3.7 and 3.13

echo "============================================================"
echo "Installing luma.oled for ALL Python Versions"
echo "============================================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

# Function to install for a specific Python version
install_for_python() {
    local PYTHON_CMD=$1
    local VERSION_NAME=$2
    
    echo "----------------------------------------"
    echo "Installing for $VERSION_NAME"
    echo "----------------------------------------"
    
    # Check if Python version exists
    if command -v "$PYTHON_CMD" &> /dev/null; then
        echo "✓ $PYTHON_CMD found: $($PYTHON_CMD --version)"
        
        # Install using pip
        echo "  Installing luma.oled, pillow, smbus2..."
        
        if $PYTHON_CMD -m pip install --user luma.oled pillow smbus2 --upgrade; then
            echo "  ✓ Installation successful for $VERSION_NAME"
            
            # Verify installation
            if $PYTHON_CMD -c "import luma.oled" 2>/dev/null; then
                echo "  ✓ Import test: SUCCESS"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "  ✗ Import test: FAILED"
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi
        else
            echo "  ✗ Installation failed for $VERSION_NAME"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        echo "✗ $PYTHON_CMD not found - skipping"
    fi
    echo ""
}

# Install for Python 3.7
install_for_python "python3.7" "Python 3.7"

# Install for Python 3 (default, could be 3.13 or others)
install_for_python "python3" "Python 3 (default)"

# Install for Python 3.13 explicitly if available
install_for_python "python3.13" "Python 3.13"

# Install in virtual environment if it exists
echo "----------------------------------------"
echo "Checking Virtual Environment (py37env)"
echo "----------------------------------------"

if [ -d "py37env" ]; then
    echo "✓ py37env found"
    
    # Activate and install
    source py37env/bin/activate
    
    echo "  Installing in virtual environment..."
    if pip install luma.oled pillow smbus2 --upgrade; then
        echo "  ✓ Installation successful in py37env"
        
        # Verify
        if python -c "import luma.oled" 2>/dev/null; then
            echo "  ✓ Import test: SUCCESS"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "  ✗ Import test: FAILED"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        echo "  ✗ Installation failed in py37env"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    
    deactivate
else
    echo "✗ py37env not found"
    echo ""
    echo "Creating Python 3.7 virtual environment..."
    
    if command -v python3.7 &> /dev/null; then
        python3.7 -m venv py37env
        source py37env/bin/activate
        
        echo "  Installing in new virtual environment..."
        pip install --upgrade pip
        pip install luma.oled pillow smbus2
        
        if python -c "import luma.oled" 2>/dev/null; then
            echo "  ✓ py37env created and configured successfully"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "  ✗ Installation failed"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        
        deactivate
    else
        echo "  ✗ Python 3.7 not available - cannot create py37env"
    fi
fi

echo ""
echo "============================================================"
echo "Installation Summary"
echo "============================================================"
echo "Successful installations: $SUCCESS_COUNT"
echo "Failed installations: $FAIL_COUNT"
echo ""

# Final verification
echo "============================================================"
echo "Verification Tests"
echo "============================================================"
echo ""

# Test Python 3.7
if command -v python3.7 &> /dev/null; then
    echo "Python 3.7:"
    if python3.7 -c "import luma.oled; print('  ✓ luma.oled works!')" 2>/dev/null; then
        :
    else
        echo "  ✗ luma.oled NOT working"
    fi
fi

# Test Python 3 (default)
echo ""
echo "Python 3 (default):"
if python3 -c "import luma.oled; print('  ✓ luma.oled works!')" 2>/dev/null; then
    :
else
    echo "  ✗ luma.oled NOT working"
fi

# Test in virtual environment
echo ""
echo "Virtual Environment (py37env):"
if [ -d "py37env" ]; then
    source py37env/bin/activate
    if python -c "import luma.oled; print('  ✓ luma.oled works!')" 2>/dev/null; then
        :
    else
        echo "  ✗ luma.oled NOT working"
    fi
    deactivate
else
    echo "  ✗ py37env not found"
fi

echo ""
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "You can now run tests with any of these commands:"
echo ""
echo "  # Using Python 3.7 directly:"
echo "  python3.7 test_oled_simple.py"
echo ""
echo "  # Using default Python 3:"
echo "  python3 test_oled_simple.py"
echo ""
echo "  # Using virtual environment:"
echo "  source py37env/bin/activate"
echo "  python test_oled_simple.py"
echo "  deactivate"
echo ""
