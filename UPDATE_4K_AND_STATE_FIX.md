# ✅ UPDATE: 4K Display Support + State Detection Fix

## What's Fixed

### 1. 4K Display Support (3840x2160)
- ✅ Auto-scale all UI elements based on screen resolution
- ✅ Fonts scaled dynamically (base 1920x1080 → 3840x2160 = 2x)
- ✅ Logos scaled: 120px → 240px (large), 60px → 120px (small)
- ✅ All margins, paddings, line widths scaled
- ✅ Progress bars and badges scaled

### 2. State Detection Fixed
- ✅ Added debug output untuk tracking mode changes
- ✅ Fixed mode logic: `mode="manual"` should show MANUAL guide
- ✅ Fixed AUTO detection: `mode="auto" AND auto_running=true`
- ✅ Video plays only in AUTO mode (mpv fullscreen)

---

## Changes Made

### **video_display_app.py**

**1. Added Scale Factor Calculation:**
```python
# Line ~55
self.scale_x = self.width / 1920.0
self.scale_y = self.height / 1080.0
self.scale = min(self.scale_x, self.scale_y)

# For 3840x2160: scale = 2.0
# For 1920x1080: scale = 1.0
```

**2. Scaled All Fonts:**
```python
# Line ~85
base_scale = int(self.scale * 56)  # 56 → 112 for 4K
self.font_display = pygame.font.Font(None, base_scale)
self.font_title = pygame.font.Font(None, int(base_scale * 0.86))
...
```

**3. Scaled All UI Elements:**
- Logo sizes: `int(120 * self.scale)`
- Margins: `int(80 * self.scale)`
- Line widths: `int(400 * self.scale)`
- Badge sizes: `int(280 * self.scale)` x `int(40 * self.scale)`
- Progress bars: `int(300 * self.scale)` x `int(30 * self.scale)`

**4. Added Debug Output:**
```python
# Line ~652
if state:
    mode = state.get("mode", "unknown")
    auto_running = state.get("auto_running", False)
    print(f"📊 State: mode={mode}, auto_running={auto_running}, display_mode={self.display_mode.value}")
```

**5. Fixed Mode Detection:**
```python
# Line ~707 - AUTO mode
if mode == "auto" and auto_running:
    # Play video via mpv
    return  # Don't draw anything (mpv handles fullscreen)

# Line ~719 - MANUAL mode (simplified)
elif mode == "manual":
    # Show step-by-step guide
    self.draw_manual_guide(state)
```

---

## Deploy to Raspberry Pi

### **Step 1: Transfer Updated File**
```bash
# From your PC, copy to Raspberry Pi:
scp video_display_app.py pkm@raspberrypi:/home/pkm/pkm-simulator-PLTN/pltn_video_display/
```

### **Step 2: Restart Service**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x update_display.sh
./update_display.sh
```

### **Step 3: Watch Logs**
```bash
sudo journalctl -u pltn_video_display -f
```

**Look for:**
```
🖥️  Display: 3840x2160
📏 Scale factor: 2.00x
📊 State: mode=manual, auto_running=False, display_mode=manual_guide
```

---

## Testing

### Test 1: Check Scale Factor
```bash
sudo journalctl -u pltn_video_display | grep "Display:"
# Expected: Display: 3840x2160
#          Scale factor: 2.00x
```

### Test 2: Check State Reading
```bash
# Check state file
cat /tmp/pltn_state.json

# Expected format:
# {
#   "mode": "manual",
#   "auto_running": false,
#   "pressure": 0.0,
#   ...
# }
```

### Test 3: Mode Switching
```bash
# Watch logs in real-time
sudo journalctl -u pltn_video_display -f

# Press buttons on control panel:
# - START AUTO SIMULATION → Should show "Switching to AUTO VIDEO mode"
# - Any other button → Should show "Switching to MANUAL GUIDE mode"
```

### Test 4: Visual Check
- ✅ **IDLE Screen:** Text readable, logos clear, proper spacing
- ✅ **MANUAL Mode:** Step guide visible, progress bars scaled, fonts readable
- ✅ **AUTO Mode:** Video plays fullscreen via mpv

---

## Troubleshooting

### Issue: Text too small or too large

**Check scale factor:**
```bash
sudo journalctl -u pltn_video_display | grep "Scale factor"
```

**If wrong, check display resolution:**
```bash
xrandr
# Should show: 3840x2160
```

**Force resolution in service:**
Edit `/etc/systemd/system/pltn_video_display.service`:
```ini
Environment="SDL_VIDEO_ALLOW_SCREENSAVER=1"
Environment="SDL_VIDEODRIVER=x11"
```

### Issue: Mode not switching

**Check state file:**
```bash
watch -n 0.5 cat /tmp/pltn_state.json
```

**Check debug output:**
```bash
sudo journalctl -u pltn_video_display -f
```

Should show:
```
📊 State: mode=auto, auto_running=true, display_mode=auto_video
```

**If not updating:**
- Check pkm-simulator.service running
- Check state file permissions: `ls -la /tmp/pltn_state.json`
- Restart both services

### Issue: Video not playing

**Check mpv:**
```bash
mpv --version
which mpv
```

**Check video file:**
```bash
ls -la ~/pkm-simulator-PLTN/pltn_video_display/assets/penjelasan.mp4
```

**Test manually:**
```bash
mpv ~/pkm-simulator-PLTN/pltn_video_display/assets/penjelasan.mp4
```

---

## Summary

**Changes:**
1. ✅ 4K display support (auto-scale UI elements)
2. ✅ Fixed mode detection logic
3. ✅ Added debug output for troubleshooting
4. ✅ Improved font scaling for readability

**Expected Resolution:** 3840x2160 @ 30Hz  
**Scale Factor:** 2.0x  
**All UI elements:** Scaled proportionally

**Status:** Ready to deploy! 🚀

---

**Last Updated:** 2026-01-11  
**Version:** 1.2 (4K support)  
**Tested:** Pending on actual 4K display
