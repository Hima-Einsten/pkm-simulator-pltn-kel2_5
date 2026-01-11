#!/bin/bash
# Quick Fix - Update Service File on Raspberry Pi
# Run this on Raspberry Pi to update the service file

echo "=========================================="
echo "QUICK FIX: Update pltn_video_display.service"
echo "=========================================="
echo ""

# Stop the service first
echo "Step 1: Stopping service..."
sudo systemctl stop pltn_video_display

# Backup old service file
echo "Step 2: Backing up old service file..."
sudo cp /etc/systemd/system/pltn_video_display.service /etc/systemd/system/pltn_video_display.service.backup

# Copy updated service file
echo "Step 3: Copying updated service file..."
sudo cp ~/pkm-simulator-PLTN/pltn_video_display/pltn_video_display.service /etc/systemd/system/

# Reload systemd
echo "Step 4: Reloading systemd..."
sudo systemctl daemon-reload

# Start the service
echo "Step 5: Starting service..."
sudo systemctl start pltn_video_display

# Check status
echo ""
echo "Step 6: Checking service status..."
sudo systemctl status pltn_video_display --no-pager

echo ""
echo "=========================================="
echo "If service is running, you're good to go!"
echo "If not, check logs:"
echo "  sudo journalctl -u pltn_video_display -n 50"
echo "=========================================="
