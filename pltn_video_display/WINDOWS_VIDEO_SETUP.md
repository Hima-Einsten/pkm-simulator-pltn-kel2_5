# 🎬 Video Setup untuk Windows

## ✅ Video sudah ada: `assets/penjelasan.mp4`

Path sudah di-update ke: `assets/penjelasan.mp4`

---

## 🎥 MPV di Windows - Apakah Wajib?

### **Jawaban Singkat: OPSIONAL (Recommended tapi tidak wajib)**

| Skenario | MPV Needed? | Alternative |
|----------|-------------|-------------|
| **Test Mode** | ❌ NO | Pakai overlay saja |
| **AUTO mode + Real video** | ✅ YES | Or use VLC |
| **MANUAL mode** | ❌ NO | Pure Pygame UI |

---

## 📊 Options untuk Windows:

### **Option 1: Install MPV (Recommended)**

**Pros:**
- ✅ Lightweight (5MB)
- ✅ Hardware accelerated
- ✅ Low CPU usage
- ✅ Best performance

**Install:**
1. Download: https://mpv.io/installation/
2. Extract to folder (e.g., `C:\mpv\`)
3. Add to PATH:
   - Windows Search → "Environment Variables"
   - Edit "Path"
   - Add: `C:\mpv\`
4. Test: `mpv --version` di cmd

**Quick Install (via Chocolatey):**
```cmd
choco install mpv
```

---

### **Option 2: Use VLC (Alternative)**

Jika sudah ada VLC installed, bisa pakai itu.

**Modify code** di `video_display_app.py`:

```python
# Line ~210-245 (play_video method)
def play_video(self, video_path: str, loop: bool = False):
    """Play video using VLC (Windows alternative)"""
    if self.video_process:
        self.stop_video()
    
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return
    
    # VLC command (if installed)
    vlc_path = "C:/Program Files/VideoLAN/VLC/vlc.exe"  # Adjust path
    cmd = [
        vlc_path,
        '--fullscreen',
        '--no-video-title-show',
        '--no-osd',
        video_path
    ]
    
    if loop:
        cmd.insert(1, '--loop')
    
    try:
        self.video_process = subprocess.Popen(cmd)
        self.current_video = video_path
        print(f"▶️  Playing: {Path(video_path).name}")
    except FileNotFoundError:
        print("❌ VLC not found!")
```

---

### **Option 3: No Video Player (Test Mode Only)**

Jika tidak install mpv/VLC:
- Test mode tetap jalan ✅
- AUTO mode show overlay "VIDEO PLAYING" saja
- MANUAL mode tetap jalan penuh ✅

**Ini cukup untuk development UI!**

---

## 🚀 Rekomendasi Saya:

### **Untuk Development (Sekarang):**

**Opsi A: Tanpa mpv (Simplest)**
```cmd
# Just run test mode
python video_display_app.py --test --windowed

# Press 2 for AUTO mode
# → Show "VIDEO PLAYING" overlay (no real video)
# → This is fine for UI testing!
```

**Opsi B: Install mpv (Best Experience)**
```cmd
# 1. Download mpv: https://mpv.io/installation/
# 2. Extract & add to PATH
# 3. Test video playback:
python video_display_app.py --test

# Press 2 for AUTO mode
# → Will play assets/penjelasan.mp4
```

---

## 🧪 Test Video Playback (Manual)

### **Test 1: Verify video file**

```cmd
cd C:\Users\Lenovo\Downloads\pkm-simulator-PLTN\pltn_video_display

# Check file exists
dir assets\penjelasan.mp4
```

### **Test 2: Play with Windows Media Player (Quick check)**

```cmd
# Just double-click video
explorer assets\penjelasan.mp4
```

### **Test 3: Play with mpv (if installed)**

```cmd
mpv assets\penjelasan.mp4
```

### **Test 4: Run app in AUTO mode**

```cmd
python video_display_app.py --test

# Window opens
# Press 2 (AUTO mode)
# If mpv installed: Video plays
# If mpv NOT installed: Shows overlay
```

---

## 📋 Quick Decision Guide:

**Jika Anda ingin:**

| Goal | Need mpv? | Command |
|------|-----------|---------|
| Test UI only | ❌ NO | `python video_display_app.py --test --windowed` |
| Test MANUAL mode | ❌ NO | Press 3 in test mode |
| Test AUTO with video | ✅ YES | Install mpv first |
| Full production | ✅ YES | mpv recommended |

---

## 🎯 Langkah Sekarang:

### **Minimal (No mpv):**

```cmd
cd C:\Users\Lenovo\Downloads\pkm-simulator-PLTN\pltn_video_display

# Install pygame
pip install pygame

# Run test (no video playback)
python video_display_app.py --test --windowed

# Test controls:
# Press 1 - IDLE screen ✅
# Press 3 - MANUAL guide ✅
# Press 2 - AUTO (overlay only, no video) ⚠️
```

### **Full Experience (With mpv):**

```cmd
# 1. Install mpv
# Download: https://mpv.io/installation/
# Or: choco install mpv

# 2. Run test
python video_display_app.py --test --windowed

# 3. Test AUTO mode with real video
# Press 2 → plays assets/penjelasan.mp4 ✅
```

---

## ✅ Summary:

**Status:** ✅ Video path updated ke `assets/penjelasan.mp4`

**MPV di Windows:**
- **Required?** ❌ Optional (for video playback)
- **Without mpv:** UI testing works, no video playback
- **With mpv:** Full experience, video plays

**Recommended:**
- Development: Test mode without mpv is fine
- Production: Install mpv for best experience

**Next step:**
```cmd
pip install pygame
python video_display_app.py --test --windowed
```

Try it dan beritahu hasilnya! 🚀
