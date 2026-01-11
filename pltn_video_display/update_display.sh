#!/bin/bash
# Quick Update - Video Display untuk 4K dan Fix State Detection

echo "=========================================="
echo "UPDATE: Video Display (4K + State Fix)"
echo "=========================================="
echo ""

echo "Step 1: Backup current file..."
cp ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py.backup

echo "Step 2: Copying updated file..."
# Assumes you've transferred the new video_display_app.py
# If not, you need to transfer it first

echo "Step 3: Restarting service..."
sudo systemctl restart pltn_video_display

echo ""
echo "Step 4: Checking service status..."
sleep 2
sudo systemctl status pltn_video_display --no-pager -n 15

echo ""
echo "Step 5: Checking logs (last 20 lines)..."
sudo journalctl -u pltn_video_display -n 20 --no-pager

echo ""
echo "=========================================="
echo "Check display now:"
echo "  - Should show proper 4K scaled UI"
echo "  - Mode detection with debug output"
echo ""
echo "Watch logs live:"
echo "  sudo journalctl -u pltn_video_display -f"
echo "=========================================="
