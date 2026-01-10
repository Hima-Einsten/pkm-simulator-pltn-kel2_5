# 🎬 PLTN Video Display System

## 📋 Overview

Sistem visualisasi video **terpisah** untuk PLTN Simulator yang menampilkan:
- **Auto Mode**: Video edukasi lengkap proses PLTN
- **Manual Mode**: Interactive step-by-step guide dengan animasi

**Key Features:**
- ✅ **Standalone testing** (tidak perlu simulasi utama)
- ✅ **Pygame-based UI** (lightweight & cross-platform)
- ✅ **mpv video player** backend (hardware accelerated)
- ✅ **Fullscreen HDMI** output untuk Raspberry Pi
- ✅ **Real-time sync** dengan simulasi via JSON file

---

## 🏗️ Architecture

### **Separation of Concerns:**

```
┌─────────────────────────────────┐
│   raspi_central_control/        │
│   (Simulasi Utama - Backend)    │
│   - Button handling             │
│   - ESP communication           │
│   - Control logic               │
│   - Export state to JSON ✨     │
└─────────────────────────────────┘
            │
            │ IPC via JSON file
            │ (C:/temp/pltn_state.json on Windows)
            │ (/tmp/pltn_state.json on Linux)
            ▼
┌─────────────────────────────────┐
│   pltn_video_display/           │
│   (Video Display - Frontend)    │
│   - Pygame window               │
│   - Read state from JSON        │
│   - Display video/guide         │
│   - No dependency ke simulasi   │
└─────────────────────────────────┘
```

---

## 📁 File Structure

```
pltn_video_display/
├── video_display_app.py        # ✅ Main application
├── README.md                   # ✅ This file
├── requirements.txt            # ✅ Python dependencies
├── test_video_display.bat      # ✅ Quick test script (Windows)
├── WINDOWS_VIDEO_SETUP.md      # ✅ Windows setup guide
├── assets/                     # ✅ Development videos
│   └── penjelasan.mp4          # ✅ Current development video
└── videos/                     # (Optional) Production videos
    └── full_process.mp4        # (Future) Final educational video
```

---

## 🚀 Quick Start

### **Step 1: Install Dependencies**

```bash
# Install pygame
pip install pygame

# (Optional) Install mpv for video playback
# Windows: Download from https://mpv.io/installation/
# Linux: sudo apt install mpv
```

### **Step 2: Test Standalone (No Simulation Needed)**

**Windows:**
```cmd
test_video_display.bat
```

**Manual:**
```cmd
python video_display_app.py --test --windowed
```

### **Step 3: Try Different Modes**

**Test mode controls:**
- Press **1** = IDLE screen
- Press **2** = AUTO mode (video)
- Press **3** = MANUAL mode (step guide)
- Press **UP/DOWN** = Adjust pressure
- Press **R** = Toggle rods
- Press **P** = Toggle pumps
- Press **ESC** = Exit

---

## 🎯 Usage Modes

### **Mode 1: Test Mode (Standalone)**

```bash
# Windowed mode (recommended for testing)
python video_display_app.py --test --windowed

# Fullscreen mode
python video_display_app.py --test
```

**Features:**
- ✅ Mock data (no simulation needed)
- ✅ Keyboard controls to simulate state changes
- ✅ Test all 3 screens: IDLE, AUTO, MANUAL
- ✅ Perfect for development & debugging

### **Mode 2: Production Mode (with Simulation)**

```bash
# Read from simulation backend
python video_display_app.py
```

**Requirements:**
- Simulasi backend harus running
- State file harus ada di:
  - Windows: `C:/temp/pltn_state.json`
  - Linux: `/tmp/pltn_state.json`

---

## 📺 Display Screens

### **1. IDLE Screen**

Ditampilkan saat:
- Simulasi idle (no activity)
- Backend tidak running (production mode)
- Test mode dengan key "1"

**Content:**
```
┌────────────────────────────────┐
│      PLTN SIMULATOR            │
│  Pressurized Water Reactor     │
│                                │
│  Press START AUTO SIMULATION   │
│  for guided demo               │
│                                │
│  Or use MANUAL MODE for        │
│  hands-on training             │
└────────────────────────────────┘
```

### **2. AUTO Mode - Video Playing**

Ditampilkan saat:
- Simulasi set `mode='auto'` dan `auto_running=True`
- Test mode dengan key "2"

**Content:**
- Fullscreen video: `videos/full_process.mp4`
- Loop video sampai simulasi selesai
- In test mode: Show "VIDEO PLAYING" overlay

### **3. MANUAL Mode - Interactive Guide**

Ditampilkan saat:
- Simulasi set `mode='manual'`
- Test mode dengan key "3"

**Content:**
```
┌────────────────────────────────┐
│         STEP 1                 │
│                                │
│  Raise Pressure to 45 bar      │
│  Press PRESSURE UP button      │
│                                │
│  Pressure: 23.0 [▓▓▓░░░░░░]   │
│  Safety: 0      [░░░░░░░░░]   │
│  Shim: 0        [░░░░░░░░░]   │
│  Reg: 0         [░░░░░░░░░]   │
└────────────────────────────────┘
```

**9 Steps Total:**
1. Raise Pressure to 45 bar
2. Start Tertiary Pump
3. Start Secondary Pump
4. Start Primary Pump
5. Raise Pressure to 140 bar
6. Withdraw Safety Rod to 100%
7. Withdraw Shim Rod to 50%
8. Withdraw Regulating Rod to 50%
9. Normal Operation Achieved

---

## 🎨 Framework Details

### **Why Pygame?**

| Aspect | Pygame | PyQt5 | Tkinter |
|--------|--------|-------|---------|
| Size | ~5MB | ~100MB | Built-in |
| Learning | Easy | Steep | Medium |
| Video | ✅ (mpv) | ✅ Built-in | ❌ None |
| Fullscreen | ✅ Easy | ✅ Complex | ⚠️ Limited |
| Testing | ✅ Windowed | ✅ Yes | ✅ Yes |
| HW Accel | ✅ (mpv) | ✅ | ❌ |

**Decision:** Pygame = perfect balance untuk project ini!

### **Why mpv?**

| Backend | Size | CPU | HW Accel | Status |
|---------|------|-----|----------|--------|
| **mpv** | 5MB | 5-10% | ✅ Yes | ⭐ Best |
| VLC | 50MB | 10-15% | ✅ Yes | ✅ Backup |
| omxplayer | 3MB | 3-5% | ✅ RPi | ❌ Deprecated |
| OpenCV | 10MB | 40-60% | ❌ No | ❌ Too heavy |

---

## 📊 State JSON Format

**File Location:**
- Windows: `C:/temp/pltn_state.json`
- Linux/RPi: `/tmp/pltn_state.json`

**Example:**
```json
{
  "timestamp": 1736520312.123,
  "mode": "manual",
  "auto_running": false,
  "auto_phase": "",
  "pressure": 45.0,
  "safety_rod": 100,
  "shim_rod": 50,
  "regulating_rod": 50,
  "pump_primary": 2,
  "pump_secondary": 2,
  "pump_tertiary": 2,
  "thermal_kw": 25000.0,
  "turbine_speed": 85.0,
  "emergency": false
}
```

**Update Frequency:** 100ms (10 Hz) - sufficient for UI updates

---

## 🔧 Configuration

### **Change Video Path:**

Edit line ~285 in `video_display_app.py`:

```python
# Change from:
video_path = str(Path(__file__).parent / "videos" / "full_process.mp4")

# To custom path:
video_path = "D:/my_videos/pltn_intro.mp4"
```

### **Change Colors:**

Edit lines ~67-72:

```python
self.COLOR_BG = (20, 20, 40)        # Dark blue background
self.COLOR_TEXT = (255, 255, 255)   # White text
self.COLOR_ACCENT = (0, 200, 255)   # Cyan accent
self.COLOR_SUCCESS = (0, 255, 100)  # Green success
self.COLOR_WARNING = (255, 200, 0)  # Yellow warning
self.COLOR_ERROR = (255, 50, 50)    # Red error
```

### **Change Resolution (Windowed):**

Edit line ~45:

```python
# Change from:
self.screen = pygame.display.set_mode((1280, 720))

# To:
self.screen = pygame.display.set_mode((1920, 1080))
```

---

## 🐛 Troubleshooting

### **Problem: pygame not installed**

```bash
pip install pygame
```

### **Problem: mpv not found**

**Windows:**
1. Download from https://mpv.io/installation/
2. Extract and add to PATH
3. Or: Use VLC as alternative

**Linux:**
```bash
sudo apt install mpv
```

### **Problem: Video not playing**

- Check video file exists: `videos/full_process.mp4`
- In test mode: This is expected (no video file)
- Check mpv installed: `mpv --version`

### **Problem: State file not found**

- In test mode: Normal, uses mock data
- In production: Simulasi backend belum running
- Check file exists: `C:/temp/pltn_state.json` (Windows)

### **Problem: Window too small**

Use `--windowed` flag untuk testing:
```bash
python video_display_app.py --test --windowed
```

---

## 🚀 Next Steps

### **Phase 1: Testing (Current - Complete ✅)**

- [x] Standalone app dengan mock data
- [x] Test mode dengan keyboard controls
- [x] 3 display screens (IDLE, AUTO, MANUAL)
- [x] Progress bars dan step guide

### **Phase 2: Video Content (TODO)**

- [ ] Create/obtain video: `full_process.mp4`
- [ ] Video duration: ~60-90 seconds
- [ ] Content: Complete PLTN power generation process
- [ ] Format: MP4 (H.264), 1920x1080 recommended

### **Phase 3: Backend Integration (TODO)**

- [ ] Add state export di `raspi_main_panel.py`
- [ ] Write JSON setiap 100ms
- [ ] Test production mode dengan simulasi
- [ ] Verify sync: video ↔ simulasi

### **Phase 4: Deployment (TODO)**

- [ ] Create systemd service (`pltn_video.service`)
- [ ] Auto-start after boot
- [ ] Setup HDMI output ke monitor
- [ ] Test pada Raspberry Pi

---

## 📖 Examples

### **Example 1: Test IDLE Screen**

```bash
python video_display_app.py --test --windowed
# Press 1 (IDLE mode)
```

### **Example 2: Test MANUAL Guide**

```bash
python video_display_app.py --test --windowed
# Press 3 (MANUAL mode)
# Press UP to increase pressure
# Press R to toggle rods
# Watch step advance automatically
```

### **Example 3: Test AUTO Video**

```bash
python video_display_app.py --test --windowed
# Press 2 (AUTO mode)
# See "VIDEO PLAYING" overlay (no real video in test)
```

### **Example 4: Production Mode**

```bash
# Terminal 1: Run simulation
cd raspi_central_control
python raspi_main_panel.py

# Terminal 2: Run video display
cd pltn_video_display
python video_display_app.py
```

---

## ✅ Summary

**Status:** ✅ **Ready for Testing!**

**What's Complete:**
- ✅ Main application code (500+ lines)
- ✅ Test mode dengan mock data
- ✅ 3 display screens
- ✅ Interactive step guide
- ✅ Progress visualization
- ✅ Cross-platform (Windows/Linux)

**What's Needed:**
- 📹 Video file: `videos/full_process.mp4`
- 🔧 Backend integration (state export)
- 🧪 Testing with actual simulation

**Test Now:**
```bash
python video_display_app.py --test --windowed
```

---

## 📞 Support

**Getting Started:**
1. Install pygame: `pip install pygame`
2. Run test: `python video_display_app.py --test --windowed`
3. Press 1/2/3 to test different modes
4. Press UP/DOWN/R/P to simulate changes

**Issues:**
- Read code comments in `video_display_app.py`
- Check troubleshooting section above
- Test in windowed mode first

---

**Created:** 2026-01-10  
**Version:** 1.0  
**Framework:** Pygame 2.5.2 + mpv  
**Python:** 3.7+  
**Status:** ✅ Ready for Testing
