#!/bin/bash
# Alternative Fix - Run Service Without User Specification
# This fixes the "Failed at step USER" error

echo "=========================================="
echo "ALTERNATIVE FIX: Service without User spec"
echo "=========================================="
echo ""

# Check current user
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"

if [ "$CURRENT_USER" != "pi" ]; then
    echo "⚠️  Warning: You are not 'pi' user"
    echo "   Service file will be updated for no user spec"
fi

echo ""
echo "Step 1: Stopping service..."
sudo systemctl stop pltn_video_display

echo ""
echo "Step 2: Backing up old service file..."
sudo cp /etc/systemd/system/pltn_video_display.service /etc/systemd/system/pltn_video_display.service.backup

echo ""
echo "Step 3: Using service file without User specification..."
sudo cp ~/pkm-simulator-PLTN/pltn_video_display/pltn_video_display.service /etc/systemd/system/

echo ""
echo "Step 4: Reloading systemd..."
sudo systemctl daemon-reload

echo ""
echo "Step 5: Starting service..."
sudo systemctl start pltn_video_display

echo ""
echo "Step 6: Checking status..."
sleep 2
sudo systemctl status pltn_video_display --no-pager -n 20

echo ""
echo "=========================================="
echo "Checking logs for errors..."
sudo journalctl -u pltn_video_display -n 10 --no-pager

echo ""
echo "=========================================="
echo "If still failing, try alternative service:"
echo "  sudo cp ~/pkm-simulator-PLTN/pltn_video_display/pltn_video_display_nouser.service /etc/systemd/system/pltn_video_display.service"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart pltn_video_display"
echo "=========================================="
