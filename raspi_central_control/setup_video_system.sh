#!/bin/bash
# Setup script for PLTN Video Player System
# Run on Raspberry Pi to install dependencies and configure system

echo "=================================================="
echo "PLTN Video Player System Setup"
echo "=================================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1/6] Updating system packages..."
sudo apt update

echo ""
echo "[2/6] Installing omxplayer (hardware accelerated video player)..."
sudo apt install -y omxplayer

echo ""
echo "[3/6] Installing VLC (backup video player)..."
sudo apt install -y vlc

echo ""
echo "[4/6] Installing Python dependencies..."
pip3 install opencv-python 2>/dev/null || echo "OpenCV installation skipped (optional)"

echo ""
echo "[5/6] Creating video directory structure..."
VIDEO_DIR="/home/pi/pltn_videos"
mkdir -p "$VIDEO_DIR"

echo "Creating placeholder text files for required videos..."
cat > "$VIDEO_DIR/README.txt" << EOF
PLTN Simulator - Video Files Directory
========================================

Required video files:
1. 01_intro_pltn.mp4              - Introduction to PWR Nuclear Plant
2. 02_pressurizer_system.mp4      - Pressurizer System Operation
3. 03_coolant_circulation.mp4     - Coolant Circulation Pumps
4. 04_control_rods_operation.mp4  - Control Rods Operation
5. 05_turbine_generator.mp4       - Turbine and Generator System
6. 06_normal_operation.mp4        - Normal Operation Overview
7. 07_shutdown_procedure.mp4      - Normal Shutdown Procedure
8. 08_emergency_shutdown.mp4      - Emergency Shutdown (SCRAM)

Video Requirements:
- Format: MP4 (H.264 codec recommended)
- Resolution: 1920x1080 (Full HD) or 1280x720 (HD)
- Duration: 30 seconds to 5 minutes per video
- Audio: AAC codec, stereo

Place your video files in this directory with exact filenames.
EOF

# Create sample video list file
cat > "$VIDEO_DIR/video_checklist.txt" << EOF
Video Checklist for PLTN Simulator
====================================

Phase: IDLE
[ ] 01_intro_pltn.mp4
    Topics: PWR basics, safety features, system overview

Phase: STARTUP - PRESSURE
[ ] 02_pressurizer_system.mp4
    Topics: Pressurizer function, pressure control, safety limits

Phase: STARTUP - PUMPS
[ ] 03_coolant_circulation.mp4
    Topics: Primary/secondary/tertiary loops, pump operation

Phase: CONTROL RODS
[ ] 04_control_rods_operation.mp4
    Topics: Neutron control, reactivity, rod insertion/withdrawal

Phase: POWER GENERATION
[ ] 05_turbine_generator.mp4
    Topics: Steam cycle, turbine operation, power conversion

Phase: NORMAL OPERATION
[ ] 06_normal_operation.mp4
    Topics: Steady-state operation, monitoring, control

Phase: SHUTDOWN
[ ] 07_shutdown_procedure.mp4
    Topics: Normal shutdown sequence, cooldown, safety

Phase: EMERGENCY
[ ] 08_emergency_shutdown.mp4
    Topics: SCRAM procedure, safety systems, emergency response

Notes:
- Mark [X] when video file is added
- Check video plays correctly: omxplayer <filename>
- Test on actual HDMI monitor
EOF

echo "Video directory created at: $VIDEO_DIR"
ls -la "$VIDEO_DIR"

echo ""
echo "[6/6] Testing video playback capability..."

# Test omxplayer
if command -v omxplayer &> /dev/null; then
    echo "✓ omxplayer is installed"
    omxplayer --version 2>&1 | head -n 1
else
    echo "✗ omxplayer not found"
fi

# Test VLC
if command -v vlc &> /dev/null; then
    echo "✓ VLC is installed"
    vlc --version 2>&1 | head -n 1
else
    echo "✗ VLC not found"
fi

# Check HDMI output
echo ""
echo "Checking HDMI configuration..."
if tvservice -s &> /dev/null; then
    tvservice -s
else
    echo "tvservice not available"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Add your video files to: $VIDEO_DIR"
echo "2. Test video player: python3 raspi_video_player.py"
echo "3. Integrate with main controller (see raspi_video_integration.py)"
echo ""
echo "Video file requirements:"
echo "- Use exact filenames from README.txt"
echo "- MP4 format recommended"
echo "- 720p or 1080p resolution"
echo "- Test with: omxplayer /path/to/video.mp4"
echo ""
echo "For more information, see: VIDEO_SYSTEM_GUIDE.md"
echo ""
