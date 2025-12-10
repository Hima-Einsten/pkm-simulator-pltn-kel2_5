#!/bin/bash
# Run scripts with Python 3.7 environment
# This ensures we use the correct Python version for the project

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/py37env"

echo "============================================================"
echo "Running with Python 3.7 Environment"
echo "============================================================"

# Check if py37env exists
if [ ! -d "$ENV_DIR" ]; then
    echo "❌ Virtual environment 'py37env' not found!"
    echo ""
    echo "Creating Python 3.7 virtual environment..."
    
    # Check if python3.7 is available
    if command -v python3.7 &> /dev/null; then
        python3.7 -m venv "$ENV_DIR"
        echo "✓ Virtual environment created"
    else
        echo "❌ Python 3.7 not found on system!"
        echo ""
        echo "Install Python 3.7:"
        echo "  sudo apt update"
        echo "  sudo apt install python3.7 python3.7-venv python3.7-dev"
        exit 1
    fi
fi

# Activate virtual environment
echo ""
echo "Activating Python 3.7 environment..."
source "$ENV_DIR/bin/activate"

# Show Python version
echo "✓ Python version: $(python --version)"
echo ""

# Check if luma.oled is installed
if python -c "import luma.oled" 2>/dev/null; then
    echo "✓ luma.oled is installed"
else
    echo "⚠️  luma.oled not found in virtual environment"
    echo ""
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install luma.oled pillow smbus2
    echo ""
fi

# Run the script passed as argument
if [ -z "$1" ]; then
    echo "Usage: ./run_with_python37.sh <script_name>"
    echo ""
    echo "Examples:"
    echo "  ./run_with_python37.sh test_oled_simple.py"
    echo "  ./run_with_python37.sh test_oled_display_active.py"
    echo "  ./run_with_python37.sh check_python_env.py"
else
    echo "============================================================"
    echo "Running: $1"
    echo "============================================================"
    echo ""
    python "$1" "${@:2}"
fi

# Deactivate is automatic when script exits
