# 🚀 Quick Deployment Guide - PLTN Video Display

## ⚡ 5-Minute Setup (Raspberry Pi)

### **Step 1: Transfer Files**
```bash
# Copy project folder to Raspberry Pi
# Location: /home/pi/pkm-simulator-PLTN/
```

### **Step 2: Run Installation**
```bash
cd ~/pkm-simulator-PLTN
chmod +x install_raspi.sh
./install_raspi.sh
```
**Wait:** ~10-15 minutes (automatic)

### **Step 3: Reboot**
```bash
sudo reboot
```
**Wait:** ~30 seconds for boot

### **Step 4: Verify**
```bash
# Check services running
sudo systemctl status raspi_simulator
sudo systemctl status pltn_video_display

# Both should show: "active (running)"
```

**✅ Done! Video display will show automatically.**

---

## 📺 Display Behavior

**After Boot:**
1. IDLE screen shows automatically (branding + "SIMULATION READY")
2. Press **START AUTO SIMULATION** → Video plays
3. Press **REACTOR START** → Manual mode (step guide)

---

## 🔧 Quick Commands

### **View Logs:**
```bash
# Simulator
sudo journalctl -u raspi_simulator -f

# Video display
sudo journalctl -u pltn_video_display -f

# Both
sudo journalctl -u raspi_simulator -u pltn_video_display -f
```

### **Control Services:**
```bash
# Restart
sudo systemctl restart raspi_simulator
sudo systemctl restart pltn_video_display

# Stop
sudo systemctl stop raspi_simulator
sudo systemctl stop pltn_video_display

# Start
sudo systemctl start raspi_simulator
sudo systemctl start pltn_video_display
```

### **Check State File:**
```bash
cat /tmp/pltn_state.json
```

---

## 🐛 Quick Troubleshooting

### **Video display tidak muncul:**
```bash
# Restart video service
sudo systemctl restart pltn_video_display

# Check logs
sudo journalctl -u pltn_video_display -n 50
```

### **State file tidak ada:**
```bash
# Check simulator running
sudo systemctl status raspi_simulator

# Restart simulator
sudo systemctl restart raspi_simulator

# Wait 5 seconds
sleep 5
cat /tmp/pltn_state.json
```

### **Screen blanking:**
```bash
# Disable blanking
nano ~/.config/lxsession/LXDE-pi/autostart

# Add:
@xset s off
@xset -dpms
@xset s noblank

# Reboot
sudo reboot
```

---

## 📋 Files Changed

**Modified (2 files):**
1. `raspi_central_control/raspi_main_panel.py` (+60 lines - state export)
2. `pltn_video_display/video_display_app.py` (1 comment - video path)

**Created (5 files):**
1. `raspi_central_control/raspi_simulator.service` - Simulator auto-start
2. `pltn_video_display/pltn_video_display.service` - Video auto-start
3. `install_raspi.sh` - Installation script
4. `RASPI_DEPLOYMENT.md` - Full deployment guide
5. `VIDEO_DISPLAY_INTEGRATION_SUMMARY.md` - Implementation details

---

## ✅ Production Checklist

Before demo:
- [ ] Run `install_raspi.sh` successfully
- [ ] Reboot completed
- [ ] Both services show "active (running)"
- [ ] State JSON file exists: `/tmp/pltn_state.json`
- [ ] IDLE screen shows on HDMI monitor
- [ ] Video file exists: `assets/penjelasan.mp4`
- [ ] Buttons responsive (test REACTOR START)
- [ ] AUTO mode plays video correctly
- [ ] MANUAL mode shows step guide
- [ ] No errors in logs

---

## 🎯 What's New

### **Program Utama (raspi_main_panel.py):**
- ✅ Now exports state to `/tmp/pltn_state.json` (10 Hz)
- ✅ Video display can read simulation status

### **Video Display (video_display_app.py):**
- ✅ Uses video: `assets/penjelasan.mp4`
- ✅ 3 modes: IDLE, MANUAL, AUTO

### **System (Raspberry Pi):**
- ✅ Auto-start on boot (both services)
- ✅ HDMI output forced on
- ✅ Screen blanking disabled
- ✅ Auto-login to desktop

---

## 📚 Full Documentation

**For detailed info, read:**
- `RASPI_DEPLOYMENT.md` - Complete deployment guide (500+ lines)
- `VIDEO_DISPLAY_INTEGRATION_SUMMARY.md` - Implementation details

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-01-11  
**Installation Time:** ~15 minutes  
**Boot Time:** ~30 seconds
