#!/bin/bash
# PLTN Simulator - Raspberry Pi Installation Script
# Installs dependencies, configures system, and sets up auto-start services

set -e  # Exit on error

echo "=============================================="
echo "PLTN Simulator - Raspberry Pi Installation"
echo "=============================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: Not running on Raspberry Pi"
    echo "   Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "⚠️  Warning: Not running as 'pi' user (current: $USER)"
    echo "   Services are configured for user 'pi'"
    echo "   Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y python3-rpi.gpio python3-smbus python3-serial

echo ""
echo "Step 3: Installing video display dependencies..."
# Pygame
pip3 install --user pygame==2.5.2

# Video player (mpv - lightweight & hardware accelerated)
sudo apt install -y mpv

# Optional: VLC as backup
# sudo apt install -y vlc

echo ""
echo "Step 4: Installing simulator dependencies..."
cd ~/pkm-simulator-PLTN/raspi_central_control
pip3 install --user -r requirements.txt 2>/dev/null || echo "No requirements.txt found, skipping"

echo ""
echo "Step 5: Configuring Raspberry Pi display settings..."

# Disable screen blanking
echo "   - Disabling screen blanking..."
sudo raspi-config nonint do_blanking 1

# Force HDMI output (prevent no signal on boot)
echo "   - Forcing HDMI output..."
if ! grep -q "hdmi_force_hotplug=1" /boot/config.txt; then
    echo "hdmi_force_hotplug=1" | sudo tee -a /boot/config.txt
fi

if ! grep -q "hdmi_drive=2" /boot/config.txt; then
    echo "hdmi_drive=2" | sudo tee -a /boot/config.txt
fi

# Set display resolution (optional - uncomment if needed)
# echo "hdmi_group=2" | sudo tee -a /boot/config.txt
# echo "hdmi_mode=82" | sudo tee -a /boot/config.txt  # 1920x1080 60Hz

echo ""
echo "Step 6: Configuring X11 for auto-login and display..."

# Enable auto-login to desktop (required for video display)
sudo raspi-config nonint do_boot_behaviour B4

# Disable screensaver in LXDE
mkdir -p ~/.config/lxsession/LXDE-pi
if [ ! -f ~/.config/lxsession/LXDE-pi/autostart ]; then
    touch ~/.config/lxsession/LXDE-pi/autostart
fi

# Add screensaver disable commands
if ! grep -q "xset s off" ~/.config/lxsession/LXDE-pi/autostart; then
    echo "@xset s off" >> ~/.config/lxsession/LXDE-pi/autostart
    echo "@xset -dpms" >> ~/.config/lxsession/LXDE-pi/autostart
    echo "@xset s noblank" >> ~/.config/lxsession/LXDE-pi/autostart
fi

echo ""
echo "Step 7: Creating /tmp directory for state file..."
sudo mkdir -p /tmp
sudo chmod 1777 /tmp

echo ""
echo "Step 8: Installing systemd services..."



# Install video display service
echo "   - Installing pltn_video_display.service..."
sudo cp ~/pkm-simulator-PLTN/pltn_video_display/pltn_video_display.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/pltn_video_display.service

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "Step 9: Enabling services for auto-start..."
sudo systemctl enable pltn_video_display.service

echo ""
echo "=============================================="
echo "✅ Installation Complete!"
echo "=============================================="
echo ""
echo "Configuration Summary:"
echo "  - Python 3 & dependencies: ✅ Installed"
echo "  - Pygame & mpv: ✅ Installed"
echo "  - Screen blanking: ✅ Disabled"
echo "  - HDMI hotplug: ✅ Forced"
echo "  - Auto-login desktop: ✅ Enabled"
echo "  - Systemd services: ✅ Installed & enabled"
echo ""
echo "Next Steps:"
echo ""
echo "1. REBOOT the Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "2. After reboot, check services status:"
echo "   sudo systemctl status pkm-simulator"
echo "   sudo systemctl status pltn_video_display"
echo ""
echo "3. View logs if needed:"
echo "   sudo journalctl -u pkm-simulator -f"
echo "   sudo journalctl -u pltn_video_display -f"
echo ""
echo "4. Manual control (if needed):"
echo "   sudo systemctl start pkm-simulator"
echo "   sudo systemctl start pltn_video_display"
echo "   sudo systemctl stop pkm-simulator"
echo "   sudo systemctl stop pltn_video_display"
echo ""
echo "=============================================="
echo "Press ENTER to continue (will NOT reboot yet)..."
read -r
