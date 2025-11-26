# 📹 Panduan Membuat Video Edukasi PLTN

## 🎯 Overview

Anda perlu membuat **8 video edukasi** untuk menjelaskan setiap fase operasi PLTN. Video akan ditampilkan otomatis di monitor saat simulasi berjalan.

## 📋 Daftar Video yang Dibutuhkan

### Video 1: Intro PLTN (2-3 menit)
**Filename:** `01_intro_pltn.mp4`  
**Tampil saat:** Sistem idle/startup

**Konten yang disarankan:**
- Apa itu PLTN (Pembangkit Listrik Tenaga Nuklir)
- Jenis PWR (Pressurized Water Reactor)
- Keunggulan energi nuklir
- Komponen utama: reaktor, steam generator, turbine, condenser
- Diagram sistem secara keseluruhan
- Safety features

---

### Video 2: Sistem Pressurizer (1-2 menit)
**Filename:** `02_pressurizer_system.mp4`  
**Tampil saat:** Pressure naik (10-140 bar)

**Konten yang disarankan:**
- Fungsi pressurizer: menjaga tekanan primary loop
- Target pressure: 155 bar (2250 psi)
- Cara kerja: heater & spray
- Safety limits: warning (160 bar), critical (180 bar)
- Animasi tekanan naik secara bertahap

---

### Video 3: Sirkulasi Pendingin (1-2 menit)
**Filename:** `03_coolant_circulation.mp4`  
**Tampil saat:** Pompa mulai nyala

**Konten yang disarankan:**
- 3 loop pendingin:
  - **Primary**: Air bertekanan tinggi dari reaktor
  - **Secondary**: Steam untuk turbine
  - **Tertiary**: Cooling water untuk condenser
- Fungsi masing-masing pompa
- Flow rate dan timing
- Interlock safety: pompa butuh pressure minimal

---

### Video 4: Control Rod Operation (1-2 menit)
**Filename:** `04_control_rods_operation.mp4`  
**Tampil saat:** Control rod mulai ditarik (>10%)

**Konten yang disarankan:**
- Fungsi control rod: mengontrol reaksi fisi
- Material: Boron, Cadmium (neutron absorber)
- Cara kerja: insert (turunkan daya), withdraw (naikkan daya)
- Posisi: 0% (fully inserted) → 100% (fully withdrawn)
- Safety: SCRAM (drop semua rod dalam 1 detik)
- Thermal power calculation

---

### Video 5: Turbine & Generator (1-2 menit)
**Filename:** `05_turbine_generator.mp4`  
**Tampil saat:** Power generation mulai (>10 MW)

**Konten yang disarankan:**
- Steam cycle: primary → secondary
- Steam generator: heat exchanger
- Turbine: convert steam kinetic energy → mechanical
- Generator: convert mechanical → electrical
- Typical output: 1000 MW electrical
- Condenser: convert steam back to water

---

### Video 6: Normal Operation (2-3 menit)
**Filename:** `06_normal_operation.mp4`  
**Tampil saat:** Sistem stabil (>50 MW, semua optimal)

**Konten yang disarankan:**
- Parameter operasi normal:
  - Pressure: 155 bar
  - Temperature: 325°C (primary outlet)
  - Power: 100% (1000 MWe)
  - All pumps: ON
- Monitoring yang perlu diperhatikan
- Load following capability
- Operator responsibilities
- Safety systems always active

---

### Video 7: Shutdown Procedure (1-2 menit)
**Filename:** `07_shutdown_procedure.mp4`  
**Tampil saat:** Shutdown normal (rod <10%, power turun)

**Konten yang disarankan:**
- Langkah shutdown normal:
  1. Reduce power gradually (insert control rods)
  2. Trip turbine generator
  3. Continue cooling (pumps still running)
  4. Monitor temperature decay
  5. Stop pumps when safe
  6. Reduce pressure
- Cooling time: beberapa jam sampai hari
- Decay heat: 7% initial power setelah shutdown

---

### Video 8: Emergency Shutdown (30-60 detik)
**Filename:** `08_emergency_shutdown.mp4`  
**Tampil saat:** Emergency button ditekan / SCRAM

**Konten yang disarankan:**
- SCRAM / Emergency shutdown
- Trigger conditions:
  - Earthquake
  - Loss of coolant
  - Overpressure
  - Manual emergency button
- Automatic response:
  - All control rods drop (gravity)
  - Emergency cooling activated
  - Containment isolation
  - Alarm activated
- Post-SCRAM monitoring
- Recovery procedure

---

## 🛠️ Tools untuk Membuat Video

### 1. PowerPoint / Google Slides (Paling Mudah)
```
1. Buat slides dengan konten di atas
2. Tambahkan animasi transisi
3. Record narasi (optional)
4. Export as Video:
   - PowerPoint: File → Export → Create Video
   - Google Slides: File → Download → MPEG-4 (.mp4)
```

### 2. Canva (Online, User-Friendly)
- Website: canva.com
- Gratis dengan banyak template
- Drag & drop interface
- Export langsung ke MP4

### 3. DaVinci Resolve (Professional, Gratis)
- Download: blackmagicdesign.com
- Full video editor
- Color grading, effects
- Free version sudah sangat powerful

### 4. Manim (Python Animation, untuk Teknis)
```python
# Contoh animasi dengan Manim
from manim import *

class PWRDiagram(Scene):
    def construct(self):
        title = Text("PWR System Diagram")
        self.play(Write(title))
        self.wait(1)
        # Add reactor, steam generator, turbine...
```

### 5. OBS Studio (Screen Recording)
- Download: obsproject.com
- Record presentasi/demo
- Add webcam overlay
- Screen + audio recording

---

## 📐 Spesifikasi Video

### Format:
- **Container:** MP4
- **Video Codec:** H.264 (AVC)
- **Audio Codec:** AAC
- **Resolution:** 1280x720 (HD) atau 1920x1080 (Full HD)
- **Frame Rate:** 30 fps
- **Bitrate:** 2-5 Mbps (balance quality & size)
- **Duration:** 30 detik - 3 menit (1-2 menit ideal)

### Convert dengan ffmpeg:
```bash
# Install ffmpeg terlebih dahulu

# Convert video ke format optimal
ffmpeg -i input.avi \
       -c:v libx264 -preset medium -crf 23 \
       -c:a aac -b:a 128k \
       -vf scale=1280:720 \
       -r 30 \
       output.mp4

# Compress file besar
ffmpeg -i input.mp4 \
       -c:v libx264 -crf 28 \
       -c:a aac -b:a 96k \
       output_compressed.mp4
```

---

## 🎨 Tips Desain Video

### Visual:
- **Background gelap** (easier on eyes untuk monitor besar)
- **Font besar** dan jelas (minimum 24pt)
- **High contrast** (white text on dark background)
- **Animasi sederhana** (jangan terlalu ramai)
- **Diagram clear** dengan label jelas

### Konten:
- **Fokus pada 1 topik** per video
- **Bullet points** lebih baik dari paragraph
- **Visual > text** (show, don't just tell)
- **Narasi optional** (video bisa tanpa suara)
- **Consistency** (style sama untuk semua video)

### Audio (Optional):
- **Narasi bahasa Indonesia**
- **Background music** (volume rendah, non-distracting)
- **Sound effects** minimal
- **Clear pronunciation** kalau ada narasi

---

## 📦 Workflow Recommended

### **Langkah 1: Riset & Script** (2-3 jam)
- Baca dokumentasi PLTN
- Tulis script untuk masing-masing video
- Tentukan visual yang dibutuhkan

### **Langkah 2: Buat Assets** (3-4 jam)
- Diagram/ilustrasi sistem PLTN
- Icons untuk komponen
- Animasi transisi
- Background images

### **Langkah 3: Production** (1 jam per video)
- Buat video di PowerPoint/Canva
- Tambahkan animasi
- Record narasi (optional)
- Export ke MP4

### **Langkah 4: Post-Production** (30 menit per video)
- Convert ke format optimal (ffmpeg)
- Check audio levels
- Verify playback di Raspberry Pi
- Test dengan simulator

### **Langkah 5: Deploy** (15 menit)
```bash
# Upload ke Raspberry Pi
scp *.mp4 pi@raspberrypi.local:/home/pi/pltn_videos/

# Test
omxplayer /home/pi/pltn_videos/01_intro_pltn.mp4
```

**Total estimated time: 1-2 hari** (tergantung detail)

---

## 🎓 Referensi Konten

### Sumber Belajar PLTN:
1. **World Nuclear Association** - world-nuclear.org
2. **IAEA (International Atomic Energy Agency)** - iaea.org
3. **NRC (Nuclear Regulatory Commission)** - nrc.gov
4. **YouTube channels:**
   - Illinois EnergyProf
   - Real Engineering
   - Practical Engineering

### Diagram PWR yang bagus:
- Wikipedia: Pressurized Water Reactor
- Google Images: "PWR diagram"
- Nuclear power plant schematics

---

## 🚀 Quick Start (Minimal Viable Videos)

Kalau mau **cepat untuk testing**, buat video sederhana:

### Opsi A: Text-only slides
```
Slide 1: "01 - Pengenalan PLTN"
Slide 2: "PWR menggunakan air bertekanan tinggi"
Slide 3: "3 komponen utama: Reaktor, SG, Turbine"
Slide 4: "Safety adalah prioritas utama"

Export duration: 10 detik (auto-advance)
```

### Opsi B: Use placeholder videos
Jalankan script `create_placeholder_videos.py` untuk buat video dummy dengan text overlay.

---

## ✅ Checklist

Sebelum deploy ke Raspberry Pi:

- [ ] 8 video sudah dibuat
- [ ] Format MP4 H.264
- [ ] Resolution 720p atau 1080p
- [ ] Duration 30s - 3 menit
- [ ] Filename **exact match** dengan yang di tabel
- [ ] Test playback di PC: `ffplay video.mp4`
- [ ] File size reasonable (<50MB per video)
- [ ] Audio level normal (jika ada audio)
- [ ] No corruption (play sampai habis)

---

## 💡 Alternative: Hire/Collaborate

Kalau tidak punya waktu membuat video:
- **Hire freelancer** di Fiverr/Upwork (animator/video editor)
- **Kolaborasi** dengan mahasiswa desain grafis/multimedia
- **Gunakan template** dari Envato Elements (berbayar)
- **AI tools** seperti Synthesia (text-to-video)

---

## 📞 Need Help?

File yang sudah saya buat:
1. ✅ `raspi_video_player.py` - Video player engine
2. ✅ `raspi_video_integration.py` - Integration helper
3. ✅ `setup_video_system.sh` - Setup script
4. ✅ `VIDEO_SYSTEM_GUIDE.md` - Technical guide
5. ✅ `create_placeholder_videos.py` - Generate test videos

Yang perlu Anda lakukan:
1. ❌ Buat/siapkan 8 video edukasi (konten)
2. ❌ Upload ke `/home/pi/pltn_videos/`
3. ❌ Test dan verify

---

**Good luck creating the educational content!** 🎬📚

Kalau ada pertanyaan tentang konten atau teknis pembuatan video, feel free to ask!
