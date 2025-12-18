#!/bin/bash
# PKM Simulator - Systemd Service Installation Script
# This script installs and enables the PKM simulator as a systemd service

set -e  # Exit on error

echo "=========================================="
echo "PKM Simulator Service Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do NOT run this script as root (sudo)"
    echo "   The script will ask for sudo password when needed"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo "📁 Script directory: $SCRIPT_DIR"
echo ""

# Check if service file exists
SERVICE_FILE="$SCRIPT_DIR/pkm-simulator.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

echo "✅ Service file found: $SERVICE_FILE"
echo ""

# Update service file with correct paths
echo "📝 Updating service file with current paths..."
TEMP_SERVICE="/tmp/pkm-simulator.service"
sed "s|/home/pi/Downloads/pkm-simulator-PLTN|$PROJECT_DIR|g" "$SERVICE_FILE" > "$TEMP_SERVICE"

# Update user if not 'pi'
CURRENT_USER=$(whoami)
sed -i "s|User=pi|User=$CURRENT_USER|g" "$TEMP_SERVICE"
sed -i "s|Group=pi|Group=$CURRENT_USER|g" "$TEMP_SERVICE"

echo "   User: $CURRENT_USER"
echo "   WorkingDirectory: $SCRIPT_DIR"
echo "   ExecStart: /usr/bin/python3 $SCRIPT_DIR/raspi_main_panel.py"
echo ""

# Check if Python3 exists
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3 first."
    exit 1
fi

echo "✅ Python3 found: $(which python3)"
echo ""

# Check if main script exists
MAIN_SCRIPT="$SCRIPT_DIR/raspi_main_panel.py"
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Main script not found: $MAIN_SCRIPT"
    exit 1
fi

echo "✅ Main script found: $MAIN_SCRIPT"
echo ""

# Install service file
echo "📦 Installing service file..."
sudo cp "$TEMP_SERVICE" /etc/systemd/system/pkm-simulator.service
sudo chmod 644 /etc/systemd/system/pkm-simulator.service
echo "✅ Service file installed to /etc/systemd/system/pkm-simulator.service"
echo ""

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "✅ Systemd daemon reloaded"
echo ""

# Enable service
echo "🔧 Enabling service (auto-start on boot)..."
sudo systemctl enable pkm-simulator.service
echo "✅ Service enabled"
echo ""

# Ask if user wants to start service now
read -p "Do you want to start the service now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting service..."
    sudo systemctl start pkm-simulator.service
    sleep 2
    echo ""
    echo "📊 Service status:"
    sudo systemctl status pkm-simulator.service --no-pager
else
    echo "⏭️  Service not started. You can start it manually with:"
    echo "   sudo systemctl start pkm-simulator.service"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Service Management Commands:"
echo "  Start:   sudo systemctl start pkm-simulator.service"
echo "  Stop:    sudo systemctl stop pkm-simulator.service"
echo "  Restart: sudo systemctl restart pkm-simulator.service"
echo "  Status:  sudo systemctl status pkm-simulator.service"
echo "  Logs:    sudo journalctl -u pkm-simulator.service -f"
echo ""
echo "The service will automatically start on next boot!"
echo ""
