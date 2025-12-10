#!/bin/bash
# Fix Pillow (PIL) Installation Issue
# Error: cannot import name '_imaging' from 'PIL'

echo "============================================================"
echo "Fixing Pillow Installation"
echo "============================================================"
echo ""

# Check if we're in virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "⚠️  Not in virtual environment"
    echo "Using system Python"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

echo ""
echo "Python version: $($PYTHON_CMD --version)"
echo ""

# Step 1: Uninstall old Pillow
echo "Step 1: Removing old Pillow installation..."
$PIP_CMD uninstall -y pillow PIL 2>/dev/null || true
$PIP_CMD uninstall -y pillow 2>/dev/null || true

echo ""

# Step 2: Install system dependencies for Pillow
echo "Step 2: Installing system dependencies..."
echo "This may require sudo password..."
sudo apt update
sudo apt install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5 \
    libwebp-dev \
    python3-dev \
    python3-setuptools

echo ""

# Step 3: Upgrade pip
echo "Step 3: Upgrading pip..."
$PIP_CMD install --upgrade pip

echo ""

# Step 4: Install Pillow from source
echo "Step 4: Installing Pillow (this may take a while)..."
$PIP_CMD install --no-cache-dir pillow

echo ""

# Step 5: Verify Pillow installation
echo "Step 5: Verifying Pillow installation..."
if $PYTHON_CMD -c "from PIL import Image; print('✓ PIL.Image works!')" 2>/dev/null; then
    echo "✓ Pillow installed successfully!"
else
    echo "❌ Pillow still has issues"
    echo ""
    echo "Trying alternative: Install from wheel..."
    $PIP_CMD install --no-cache-dir --force-reinstall pillow
fi

echo ""

# Step 6: Reinstall luma.oled
echo "Step 6: Reinstalling luma.oled..."
$PIP_CMD install --upgrade luma.oled smbus2

echo ""

# Step 7: Final verification
echo "============================================================"
echo "Final Verification"
echo "============================================================"
echo ""

echo "Testing imports..."

if $PYTHON_CMD -c "from PIL import Image; print('✓ PIL.Image: OK')" 2>&1; then
    :
else
    echo "❌ PIL.Image: FAILED"
fi

if $PYTHON_CMD -c "import luma.core; print('✓ luma.core: OK')" 2>&1; then
    :
else
    echo "❌ luma.core: FAILED"
fi

if $PYTHON_CMD -c "import luma.oled; print('✓ luma.oled: OK')" 2>&1; then
    :
else
    echo "❌ luma.oled: FAILED"
fi

if $PYTHON_CMD -c "import smbus2; print('✓ smbus2: OK')" 2>&1; then
    :
else
    echo "❌ smbus2: FAILED"
fi

echo ""
echo "============================================================"
echo "Fix Complete!"
echo "============================================================"
echo ""
echo "Now try running:"
echo "  $PYTHON_CMD test_oled_simple.py"
echo ""
