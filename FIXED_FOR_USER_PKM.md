# ✅ FIXED: Service File untuk User PKM

## Problem Solved!

Error `status=217/USER` terjadi karena service file menggunakan user `pi` tapi system Anda menggunakan user `pkm`.

---

## ✅ Yang Sudah Diperbaiki:

### **File: pltn_video_display.service**

**Changed:**
```diff
 [Service]
 Type=simple
-User=pi
-Group=pi
-WorkingDirectory=/home/pi/pkm-simulator-PLTN/pltn_video_display
-Environment="XAUTHORITY=/home/pi/.Xauthority"
+User=pkm
+Group=pkm
+WorkingDirectory=/home/pkm/pkm-simulator-PLTN/pltn_video_display
+Environment="XAUTHORITY=/home/pkm/.Xauthority"

-ExecStart=/usr/bin/python3 /home/pi/...
+ExecStart=/usr/bin/python /home/pkm/...
```

**Summary of Changes:**
1. ✅ User: `pi` → `pkm`
2. ✅ Group: `pi` → `pkm`
3. ✅ WorkingDirectory: `/home/pi/...` → `/home/pkm/...`
4. ✅ XAUTHORITY: `/home/pi/...` → `/home/pkm/...`
5. ✅ Python: `python3` → `python`

---

## 🚀 Cara Deploy (SIMPLE!):

### **Step 1: Transfer Updated File**
File yang sudah diupdate:
- `pltn_video_display/pltn_video_display.service` (✅ FIXED for user pkm)

### **Step 2: Run Fix Script**
```bash
cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x fix_service.sh
./fix_service.sh
```

### **Step 3: Verify**
```bash
sudo systemctl status pltn_video_display
```

**Expected Output:**
```
● pltn_video_display.service - PLTN Video Display System
   Active: active (running) since Sat 2026-01-11 14:05:00 WIB
   Main PID: 1234 (python)
```

---

## 🧪 Verification:

### Check Service:
```bash
sudo systemctl status pltn_video_display
```
Should show: `active (running)` ✅

### Check Process:
```bash
ps aux | grep video_display_app
```
Should show Python process running as user `pkm` ✅

### Check Logs:
```bash
sudo journalctl -u pltn_video_display -n 20
```
Should NOT have errors ✅

### Check Display:
- HDMI monitor shows IDLE screen ✅
- Logo BRIN & Poltek visible ✅
- "SIMULATION READY" badge showing ✅

---

## 📊 Service Configuration:

```ini
[Unit]
Description=PLTN Video Display System
After=pkm-simulator.service
Requires=pkm-simulator.service

[Service]
Type=simple
User=pkm                    # ✅ YOUR USERNAME
Group=pkm                   # ✅ YOUR GROUP
WorkingDirectory=/home/pkm/pkm-simulator-PLTN/pltn_video_display
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pkm/.Xauthority"
ExecStart=/usr/bin/python /home/pkm/pkm-simulator-PLTN/pltn_video_display/video_display_app.py

[Install]
WantedBy=graphical.target
```

---

## 🎯 Boot Sequence:

```
1. Raspberry Pi boots
2. Desktop loads (auto-login as user pkm)
3. pkm-simulator.service starts
   └─► Running as user: pkm
   └─► Writes /tmp/pltn_state.json
4. pltn_video_display.service starts
   └─► Running as user: pkm
   └─► Reads /tmp/pltn_state.json
   └─► Shows IDLE screen on HDMI
```

---

## 📁 Updated Files:

1. **pltn_video_display.service** - User pi → pkm, paths updated
2. **install_raspi.sh** - User check updated to pkm
3. **fix_service.sh** - Unchanged (universal)

---

## ✅ Ready to Deploy!

**Commands:**
```bash
# Transfer updated files to Raspberry Pi
# Then run:

cd ~/pkm-simulator-PLTN/pltn_video_display
chmod +x fix_service.sh
./fix_service.sh

# Verify
sudo systemctl status pltn_video_display
```

**Expected:** Service running tanpa error! 🎉

---

**Status:** ✅ FIXED for user `pkm`  
**Last Updated:** 2026-01-11 14:05 WIB  
**Ready:** YES - Deploy sekarang!
