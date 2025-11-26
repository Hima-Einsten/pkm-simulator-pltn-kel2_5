# 📺 PLTN Simulator - Video System Guide

## Overview

Sistem video player terintegrasi untuk menampilkan konten edukasi PLTN secara otomatis berdasarkan fase simulasi yang sedang berjalan.

## 🎯 Features

- ✅ **Automatic Phase Detection** - Video berganti otomatis sesuai fase simulasi
- ✅ **Hardware Acceleration** - Menggunakan omxplayer untuk performa optimal di Raspberry Pi
- ✅ **HDMI Output** - Output langsung ke monitor via HDMI
- ✅ **Fullscreen Display** - Tampilan fullscreen otomatis
- ✅ **Loop Playback** - Video loop sampai fase berubah
- ✅ **Multiple Backends** - Support omxplayer, VLC, dan OpenCV

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           PLTN Main Controller                  │
│                                                 │
│  ┌──────────────┐    ┌──────────────┐          │
│  │ System State │───▶│Video Player  │          │
│  │  - Pressure  │    │  - Phase Det.│          │
│  │  - Pumps     │    │  - Video Sel.│          │
│  │  - Rods      │    │  - Playback  │          │
│  │  - Power     │    └──────┬───────┘          │
│  └──────────────┘           │                   │
└─────────────────────────────┼───────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   omxplayer/VLC    │
                    │  (Video Backend)   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   HDMI Output      │
                    │   (Monitor)        │
                    └────────────────────┘
```

## 📦 Installation

### 1. Run Setup Script

```bash
cd ~/pltn_control
chmod +x setup_video_system.sh
./setup_video_system.sh
```

This will:
- Install omxplayer and VLC
- Create video directory structure
- Check HDMI configuration
- Test video playback capability

### 2. Manual Installation (Alternative)

```bash
# Install video players
sudo apt update
sudo apt install -y omxplayer vlc

# Create video directory
mkdir -p /home/pi/pltn_videos

# Install Python dependencies (optional)
pip3 install opencv-python
```

## 🎬 Video Files Setup

### Required Video Files

Place these files in `/home/pi/pltn_videos/`:

| Filename | Phase | Duration | Description |
|----------|-------|----------|-------------|
| `01_intro_pltn.mp4` | IDLE | 2-3 min | Introduction to PWR |
| `02_pressurizer_system.mp4` | STARTUP_PRESSURE | 1-2 min | Pressurizer operation |
| `03_coolant_circulation.mp4` | STARTUP_PUMPS | 1-2 min | Pump systems |
| `04_control_rods_operation.mp4` | CONTROL_RODS | 1-2 min | Control rod mechanism |
| `05_turbine_generator.mp4` | POWER_GENERATION | 1-2 min | Power generation |
| `06_normal_operation.mp4` | NORMAL_OPERATION | 2-3 min | Normal operation |
| `07_shutdown_procedure.mp4` | SHUTDOWN | 1-2 min | Shutdown sequence |
| `08_emergency_shutdown.mp4` | EMERGENCY | 30-60 sec | Emergency SCRAM |

### Video Specifications

**Recommended:**
- Format: MP4 (H.264)
- Resolution: 1920x1080 (Full HD) or 1280x720 (HD)
- Framerate: 30 fps
- Audio: AAC, stereo
- Bitrate: 2-5 Mbps

**Creating/Converting Videos:**

```bash
# Using ffmpeg to convert video
ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 23 \
       -c:a aac -b:a 128k -vf scale=1920:1080 \
       01_intro_pltn.mp4

# Reduce file size if needed
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac \
       -b:a 96k output.mp4
```

## 🚀 Usage

### Standalone Testing

Test video player without full simulator:

```bash
cd ~/pltn_control
python3 raspi_video_player.py
```

This will cycle through all phases for testing.

### Integration with Main Controller

**Method 1: Using Integration Helper (Recommended)**

Edit `raspi_main.py` and add at the top:

```python
from raspi_video_integration import integrate_video_player, add_video_cleanup
```

In the `main()` function, after creating controller:

```python
def main():
    controller = PLTNController()
    
    # Integrate video player
    integrate_video_player(controller)
    add_video_cleanup(controller)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda s, f: controller.shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: controller.shutdown())
    
    # Run controller
    controller.run()
```

**Method 2: Manual Integration**

```python
from raspi_video_player import VideoPlayer, VideoPlayerBackend

class PLTNController:
    def __init__(self):
        # ... existing initialization ...
        
        # Add video player
        self.video_player = VideoPlayer(
            video_directory="/home/pi/pltn_videos",
            backend=VideoPlayerBackend.OMXPLAYER,
            fullscreen=True,
            loop_videos=True
        )
    
    def update_displays(self):
        # ... existing display update code ...
        
        # Update video player
        self.video_player.update_simulation_state(
            pressure=self.state.pressure,
            pump_primary=self.state.pump_primary_status,
            pump_secondary=self.state.pump_secondary_status,
            pump_tertiary=self.state.pump_tertiary_status,
            rod_positions=[rod1, rod2, rod3],  # Get from ESP-B data
            power_output=power,  # Get from ESP-C data
            emergency_active=self.state.critical_active
        )
```

## 🎮 Phase Detection Logic

Video player automatically detects simulation phase:

| Condition | Phase |
|-----------|-------|
| Emergency active | **EMERGENCY** |
| Rods < 10%, Power < 10%, Pump OFF | **SHUTDOWN** |
| Pressure ≥ 140, All pumps ON, Rods > 30%, Power > 50% | **NORMAL_OPERATION** |
| Power > 10%, Rods > 20% | **POWER_GENERATION** |
| Rods > 10%, Primary pump ON | **CONTROL_RODS** |
| Any pump starting or ON | **STARTUP_PUMPS** |
| Pressure > 10, Pump OFF | **STARTUP_PRESSURE** |
| Default | **IDLE** |

## 🔧 Configuration

Edit `raspi_video_player.py` to customize:

```python
# Change video directory
video_player = VideoPlayer(
    video_directory="/custom/path/to/videos",
    ...
)

# Change video backend
video_player = VideoPlayer(
    backend=VideoPlayerBackend.VLC,  # or OMXPLAYER, OPENCV
    ...
)

# Disable looping
video_player = VideoPlayer(
    loop_videos=False,
    ...
)

# Windowed mode (not fullscreen)
video_player = VideoPlayer(
    fullscreen=False,
    ...
)
```

### Custom Video Mapping

Edit `video_map` in `VideoPlayer.__init__()`:

```python
self.video_map = {
    SimulationPhase.IDLE: "custom_intro.mp4",
    SimulationPhase.STARTUP_PRESSURE: "my_pressure_video.mp4",
    # ... etc
}
```

## 🎥 Testing Videos

### Test Single Video

```bash
# Test with omxplayer
omxplayer --loop /home/pi/pltn_videos/01_intro_pltn.mp4

# Test with VLC
vlc --fullscreen --loop /home/pi/pltn_videos/01_intro_pltn.mp4

# Test with OpenCV (if installed)
python3 -c "import cv2; cap = cv2.VideoCapture('video.mp4'); ..."
```

### Test All Videos

```bash
cd /home/pi/pltn_videos
for video in *.mp4; do
    echo "Playing: $video"
    omxplayer "$video"
done
```

### Check Video Info

```bash
# Using ffprobe
ffprobe -hide_banner video.mp4

# Get duration
ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 video.mp4
```

## 🔊 Audio Configuration

### Route Audio to HDMI

```bash
# Set HDMI as audio output
amixer cset numid=3 2

# Or edit /boot/config.txt
sudo nano /boot/config.txt
# Add: hdmi_drive=2
```

### Test Audio

```bash
# Play test sound to HDMI
speaker-test -t wav -c 2

# Test video with audio
omxplayer --adev hdmi test_video.mp4
```

## 🖥️ Display Configuration

### Set HDMI Resolution

Edit `/boot/config.txt`:

```bash
# For 1080p
hdmi_group=1
hdmi_mode=16

# For 720p
hdmi_group=1
hdmi_mode=4
```

### Force HDMI Output

```bash
# Edit /boot/config.txt
hdmi_force_hotplug=1
```

### Check Current Display

```bash
tvservice -s
fbset -s
```

## 📊 Performance

### Resource Usage

| Component | CPU | RAM | Notes |
|-----------|-----|-----|-------|
| omxplayer (H.264) | 5-10% | 50 MB | Hardware accelerated |
| VLC (H.264) | 30-40% | 80 MB | Software decode |
| OpenCV | 40-60% | 100 MB | For testing only |

### Optimization Tips

1. **Use omxplayer** for best performance (hardware accelerated)
2. **Keep videos under 5 minutes** to reduce memory usage
3. **Use 720p instead of 1080p** if performance issues
4. **Reduce video bitrate** to 2-3 Mbps max
5. **Close other applications** when running simulator

## 🐛 Troubleshooting

### Video Not Playing

```bash
# Check if video file exists
ls -lh /home/pi/pltn_videos/*.mp4

# Test video manually
omxplayer /home/pi/pltn_videos/01_intro_pltn.mp4

# Check video codec
ffprobe video.mp4 2>&1 | grep -i codec
```

### No Video on HDMI

```bash
# Check HDMI status
tvservice -s

# Force HDMI hotplug
sudo tvservice -o
sudo tvservice -p
```

### Audio Not Working

```bash
# Check audio routing
amixer cget numid=3

# Force HDMI audio
amixer cset numid=3 2

# Test with omxplayer
omxplayer --adev hdmi video.mp4
```

### Performance Issues

```bash
# Check CPU usage
top -d 1

# Check memory
free -h

# Kill other processes
sudo killall vlc omxplayer

# Reduce video quality
# Re-encode at lower bitrate/resolution
```

### Video Player Won't Stop

```bash
# Kill all video players
killall omxplayer
killall vlc

# Force kill
killall -9 omxplayer vlc
```

## 📚 Advanced Usage

### Multiple Monitors

For dual monitor setup:

```python
# Player for main monitor
player1 = VideoPlayer(
    video_directory="/home/pi/videos1",
    backend=VideoPlayerBackend.OMXPLAYER
)

# Player for secondary monitor
player2 = VideoPlayer(
    video_directory="/home/pi/videos2",
    backend=VideoPlayerBackend.VLC
)
```

### Custom Phase Logic

Modify `_determine_phase()` for custom logic:

```python
def _determine_phase(self, pressure, pump1, pump2, pump3, rods, power, emergency):
    # Custom logic
    if pressure > 180:
        return SimulationPhase.EMERGENCY
    
    if power > 90:
        return SimulationPhase.HIGH_POWER  # Add new phase
    
    # ... etc
```

### Add New Video Phase

```python
# In SimulationPhase enum
class SimulationPhase(Enum):
    # ... existing phases ...
    MAINTENANCE = "maintenance"
    REFUELING = "refueling"

# In video_map
self.video_map[SimulationPhase.MAINTENANCE] = "09_maintenance.mp4"
```

## 📝 Content Creation Tips

### Educational Video Structure

1. **Introduction** (5-10 sec)
   - Title card with phase name
   - Brief overview

2. **Main Content** (60-90 sec)
   - Animated diagrams
   - Key concepts
   - Safety points

3. **Summary** (5-10 sec)
   - Key takeaways
   - Transition to next phase

### Recommended Tools

- **Video Editing**: DaVinci Resolve, OpenShot
- **Animation**: Blender, Manim
- **Screen Recording**: OBS Studio
- **Conversion**: ffmpeg, HandBrake

### Sample Animation Script

```python
# Using manim for technical animations
from manim import *

class PressureSystem(Scene):
    def construct(self):
        title = Text("Pressurizer System")
        self.play(Write(title))
        self.wait(1)
        # Add animation...
```

## 🔒 Security Notes

- Videos are stored locally (no network required)
- No internet connection needed for playback
- Files are read-only (no write access needed)
- Can run in kiosk mode for public display

## 📦 Backup and Maintenance

### Backup Videos

```bash
# Backup all videos
tar -czf pltn_videos_backup.tar.gz /home/pi/pltn_videos/

# Restore
tar -xzf pltn_videos_backup.tar.gz -C /
```

### Update Videos

```bash
# Replace video file
cp new_video.mp4 /home/pi/pltn_videos/01_intro_pltn.mp4

# Restart simulator to apply changes
```

## 📞 Support

For issues:
1. Check log files: `pltn_control.log`
2. Test video files manually with omxplayer
3. Verify HDMI connection and settings
4. Check video format and codec

---

**Status:** ✅ **Ready to Use**  
**Last Updated:** 2024-11-20

🎬 **Ready to educate!** 📺🏭
