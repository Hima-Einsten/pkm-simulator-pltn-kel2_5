#!/bin/bash
# Test Video Playback - Manual Test

echo "=========================================="
echo "TEST: Video Playback"
echo "=========================================="
echo ""

VIDEO_FILE="$HOME/pkm-simulator-PLTN/pltn_video_display/assets/penjelasan.mp4"

echo "1. Check video file exists:"
ls -lh "$VIDEO_FILE"
echo ""

echo "2. Check mpv installed:"
which mpv
mpv --version | head -5
echo ""

echo "3. Test video playback (X11 mode):"
echo "   Playing 5 seconds..."
timeout 5 mpv --fs --really-quiet "$VIDEO_FILE" 2>&1 &
MPV_PID=$!
sleep 6
kill $MPV_PID 2>/dev/null
echo "   ✅ X11 test done"
echo ""

echo "4. Test video playback (Wayland mode):"
echo "   Playing 5 seconds..."
timeout 5 mpv --fs --really-quiet --vo=gpu --hwdec=auto --gpu-context=wayland "$VIDEO_FILE" 2>&1 &
MPV_PID=$!
sleep 6
kill $MPV_PID 2>/dev/null
echo "   ✅ Wayland test done"
echo ""

echo "5. Test video info:"
mpv --no-video --length=0 "$VIDEO_FILE" 2>&1 | grep -E "Video|Audio|Duration"
echo ""

echo "=========================================="
echo "Manual test:"
echo "  mpv --fs $VIDEO_FILE"
echo ""
echo "If video freezes, try:"
echo "  mpv --fs --vo=gpu --hwdec=auto --gpu-context=wayland $VIDEO_FILE"
echo "=========================================="
