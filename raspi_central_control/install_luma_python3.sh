#!/bin/bash
# Install luma.oled for current Python 3 version
# This fixes the Python version mismatch issue

echo "============================================================"
echo "Installing luma.oled for Python 3.13"
echo "============================================================"

# Get current Python version
PYTHON_VERSION=$(python3 --version)
echo ""
echo "Current Python: $PYTHON_VERSION"
echo ""

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found!"
    echo "Installing pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

echo "Installing luma.oled and dependencies..."
echo ""

# Install for system Python 3
pip3 install --user luma.oled pillow smbus2

echo ""
echo "============================================================"
echo "Installation complete!"
echo "============================================================"
echo ""
echo "Verifying installation..."
python3 -c "import luma.oled; print('✓ luma.oled successfully imported!')" && \
python3 -c "import luma.core; print('✓ luma.core successfully imported!')" && \
python3 -c "import PIL; print('✓ PIL successfully imported!')" && \
python3 -c "import smbus2; print('✓ smbus2 successfully imported!')"

echo ""
echo "✅ Ready to test OLED displays!"
echo ""
echo "Run test with:"
echo "  python3 test_oled_simple.py"
