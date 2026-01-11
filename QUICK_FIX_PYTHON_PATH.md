# 🔧 Quick Fix - Python Path Issue

## Problem
Service gagal start dengan error:
```
Failed to determine user credentials: No such process
Failed at step USER spawning /usr/bin/python3
```

## Root Cause
Service file menggunakan `/usr/bin/python3` tapi system Anda menggunakan `/usr/bin/python`

---

## ✅ Solution

### Option 1: Update Service File (RECOMMENDED)

**1. Transfer updated files ke Raspberry Pi**
   - File: `pltn_video_display/pltn_video_display.service` (already fixed)
   - File: `pltn_video_display/fix_service.sh` (new helper script)

**2. Run quick fix script:**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x fix_service.sh
./fix_service.sh
```

**3. Verify:**
```bash
sudo systemctl status pltn_video_display
```

Should show: `active (running)`

---

### Option 2: Manual Fix (if needed)

**1. Edit service file directly:**
```bash
sudo nano /etc/systemd/system/pltn_video_display.service
```

**2. Find line 16:**
```ini
ExecStart=/usr/bin/python3 /home/pi/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
```

**3. Change to:**
```ini
ExecStart=/usr/bin/python /home/pi/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
```

**4. Save and exit** (Ctrl+O, Enter, Ctrl+X)

**5. Reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart pltn_video_display
sudo systemctl status pltn_video_display
```

---

## 🧪 Test

**Check service running:**
```bash
sudo systemctl status pltn_video_display
```

**Expected output:**
```
● pltn_video_display.service - PLTN Video Display System
   Loaded: loaded (/etc/systemd/system/pltn_video_display.service; enabled)
   Active: active (running) since Sat 2026-01-11 13:55:00 WIB; 5s ago
```

**Check logs:**
```bash
sudo journalctl -u pltn_video_display -n 20
```

Should NOT see errors about "USER" or "python3"

**Check display:**
- HDMI monitor should show IDLE screen
- Logo BRIN & Poltek visible
- "SIMULATION READY" badge showing

---

## 🎯 What Was Changed

**File:** `pltn_video_display.service`

**Line 16:**
```diff
- ExecStart=/usr/bin/python3 /home/pi/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
+ ExecStart=/usr/bin/python /home/pi/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
```

**Reason:** Your Raspberry Pi uses `python` command, not `python3`

---

## 📋 Verification Checklist

After fix:
- [ ] Service file updated
- [ ] systemd reloaded: `sudo systemctl daemon-reload`
- [ ] Service restarted: `sudo systemctl restart pltn_video_display`
- [ ] Service status: `active (running)`
- [ ] No errors in logs
- [ ] IDLE screen shows on HDMI
- [ ] Both services running:
  ```bash
  sudo systemctl status pkm-simulator        # active (running)
  sudo systemctl status pltn_video_display   # active (running)
  ```

---

## 🚀 Next Steps

Once service is running:

**Test MANUAL mode:**
```bash
# Press any button on control panel
# Display should switch to step-by-step guide
```

**Test AUTO mode:**
```bash
# Press START AUTO SIMULATION button
# Video should play fullscreen
```

**Check state sync:**
```bash
# Check state file exists and updating
cat /tmp/pltn_state.json

# Should show current state with timestamp
```

---

## 🐛 If Still Fails

**Check Python path:**
```bash
which python
which python3
```

**Use the one that exists:**
- If only `python`: Use `/usr/bin/python`
- If only `python3`: Use `/usr/bin/python3`
- If both exist: Use `/usr/bin/python`

**Check Python version:**
```bash
python --version
# Should be Python 2.7+ or 3.7+
```

**Test pygame:**
```bash
python -c "import pygame; print('Pygame OK')"
```

Should print: `Pygame OK`

**If pygame not found:**
```bash
pip install pygame==2.5.2
# or
pip3 install pygame==2.5.2
```

---

## 📞 Support

**View live logs:**
```bash
sudo journalctl -u pltn_video_display -f
```

**Restart service:**
```bash
sudo systemctl restart pltn_video_display
```

**Check both services:**
```bash
sudo systemctl status pkm-simulator pltn_video_display
```

---

**Status:** ✅ Fixed - Ready to deploy  
**Last Updated:** 2026-01-11  
**Issue:** Python path mismatch  
**Solution:** Changed `python3` → `python`
