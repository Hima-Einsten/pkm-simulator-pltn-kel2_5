# 🔧 Fix: USER Credentials Error (status=217/USER)

## Problem

Service gagal dengan error:
```
Failed to determine user credentials: No such process
Failed at step USER spawning /usr/bin/python: No such process
Main process exited, code=exited, status=217/USER
```

## Root Cause

Ada 3 kemungkinan:
1. User `pi` tidak ada di system
2. User credentials tidak bisa di-resolve oleh systemd
3. Permission issue dengan user specification

---

## 🔍 Diagnosis

**Run diagnostic script:**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x check_user.sh
./check_user.sh
```

**Check output:**
- Jika user `pi` NOT found → User Anda beda
- Jika user `pi` exists → Permission/systemd issue

---

## ✅ Solution 1: Remove User Specification (RECOMMENDED)

Service akan run tanpa user specification, systemd akan handle otomatis.

**Updated service file:** `pltn_video_display.service`

**Changes:**
```diff
 [Service]
 Type=simple
-User=pi
-Group=pi
+# User and Group removed - run as current user
 WorkingDirectory=/home/pi/pkm-simulator-PLTN/pltn_video_display
```

**Deploy:**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x fix_user_issue.sh
./fix_user_issue.sh
```

---

## ✅ Solution 2: Use Correct Username

**If user is NOT 'pi':**

**1. Check your username:**
```bash
whoami
```

**2. Edit service file:**
```bash
sudo nano /etc/systemd/system/pltn_video_display.service
```

**3. Update User and Group:**
```ini
[Service]
Type=simple
User=YOUR_USERNAME_HERE    # Change to your username
Group=YOUR_USERNAME_HERE   # Change to your username
...
```

**4. Also update WorkingDirectory and XAUTHORITY:**
```ini
WorkingDirectory=/home/YOUR_USERNAME_HERE/pkm-simulator-PLTN/pltn_video_display
Environment="XAUTHORITY=/home/YOUR_USERNAME_HERE/.Xauthority"
```

**5. Reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart pltn_video_display
```

---

## ✅ Solution 3: Run as Root (LAST RESORT)

**Use alternative service file:**
```bash
sudo cp ~/pkm-simulator-PLTN/pltn_video_display/pltn_video_display_nouser.service /etc/systemd/system/pltn_video_display.service
sudo systemctl daemon-reload
sudo systemctl restart pltn_video_display
```

---

## 🧪 Verification

**Check service status:**
```bash
sudo systemctl status pltn_video_display
```

**Expected (SUCCESS):**
```
● pltn_video_display.service - PLTN Video Display System
   Active: active (running) since Sat 2026-01-11 14:05:00 WIB
```

**Check logs (NO errors):**
```bash
sudo journalctl -u pltn_video_display -n 20
```

Should NOT see:
- ❌ "Failed to determine user credentials"
- ❌ "Failed at step USER"
- ❌ "status=217/USER"

**Check process running:**
```bash
ps aux | grep video_display_app
```

Should show Python process running.

**Check display:**
- HDMI monitor shows IDLE screen
- No black screen
- No errors

---

## 🐛 Additional Troubleshooting

### Test Python script manually:

```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
python video_display_app.py --test --windowed
```

**Expected:** Window opens with IDLE screen

**If fails:**
- Check pygame installed: `python -c "import pygame"`
- Check display: `echo $DISPLAY` (should be `:0`)
- Check X11 running: `ps aux | grep X`

### Check file permissions:

```bash
ls -la ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
```

**Expected:** File readable by all users

**If not:**
```bash
chmod 755 ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
```

### Check working directory:

```bash
ls -la ~/pkm-simulator-PLTN/pltn_video_display/
```

**Expected:** Directory exists and accessible

---

## 📋 Files Updated

1. **pltn_video_display.service** - Removed User/Group specification
2. **pltn_video_display_nouser.service** - Alternative without user spec
3. **fix_user_issue.sh** - Auto-fix script
4. **check_user.sh** - Diagnostic script
5. **FIX_USER_CREDENTIALS.md** - This documentation

---

## 🎯 Summary

**Problem:** systemd tidak bisa resolve user `pi`  
**Solution:** Remove User/Group dari service file  
**Alternative:** Specify correct username atau run as root  
**Status:** Ready untuk deploy ulang

---

## 📞 Next Steps

**1. Run diagnostic:**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x check_user.sh
./check_user.sh
```

**2. Apply fix:**
```bash
chmod +x fix_user_issue.sh
./fix_user_issue.sh
```

**3. Verify:**
```bash
sudo systemctl status pltn_video_display
```

**4. If still fails, check logs:**
```bash
sudo journalctl -u pltn_video_display -n 50
```

---

**Last Updated:** 2026-01-11  
**Issue:** status=217/USER error  
**Solution:** Remove User specification from service file  
**Status:** ✅ Fixed - Ready to deploy
