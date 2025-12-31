# 🎛️ Dual Mode Simulation - PLTN Simulator

## 📋 Overview

PLTN Simulator kini mendukung **2 mode operasi** yang berbeda untuk memenuhi kebutuhan pembelajaran dan demonstrasi:

1. **Mode Manual** - Operator mengontrol setiap proses secara individual
2. **Mode Auto** - Simulasi berjalan otomatis dari awal hingga akhir dengan kecepatan lambat

---

## 🎮 Mode 1: Manual Mode (Mode Inputan User)

### Deskripsi
Pada mode manual, operator memiliki **kontrol penuh** terhadap setiap proses simulasi. Setiap langkah harus dilakukan secara manual dengan menekan tombol yang sesuai.

### Cara Menggunakan

#### 1️⃣ Start Reactor (Manual Mode)
```
Tekan: REACTOR START button (GPIO 17 - GREEN button)
```
- Sistem reaktor aktif
- Semua kontrol menjadi available
- Operator dapat mulai input manual

#### 2️⃣ Kontrol Manual

**Pressure Control:**
```
PRESSURE UP button   → Naikkan tekanan (+1 bar per press)
PRESSURE DOWN button → Turunkan tekanan (-1 bar per press)
```

**Pump Control:** (Harus urut: Tertiary → Secondary → Primary)
```
PUMP TERTIARY ON  → Start pompa pendingin
PUMP SECONDARY ON → Start pompa secondary loop
PUMP PRIMARY ON   → Start pompa primary loop
```

**Control Rods:** (Memerlukan interlock: pressure ≥40 bar, all pumps ON)
```
SHIM ROD UP         → Naikkan shim rod (+1% per press)
REGULATING ROD UP   → Naikkan regulating rod (+1% per press)
SAFETY ROD DOWN     → Turunkan safety rod (untuk shutdown)
```

**Emergency:**
```
EMERGENCY button → Immediate SCRAM (all rods drop, pumps shutdown)
```

**Reset:**
```
REACTOR RESET button → Reset simulasi ke kondisi awal
```

### Keunggulan Mode Manual
✅ **Full Control** - Operator mengontrol setiap detail  
✅ **Hands-on Learning** - Belajar dengan praktik langsung  
✅ **Understanding Sequence** - Memahami urutan startup yang benar  
✅ **Experimentation** - Dapat mencoba skenario berbeda  
✅ **Safety Training** - Belajar interlock dan safety system  

### Cocok Untuk
- 🎓 Pelatihan operator PLTN
- 🔬 Eksperimen dengan parameter berbeda
- 👨‍🏫 Demonstrasi interaktif di kelas
- 📚 Pemahaman mendalam tentang sistem kontrol

---

## 🤖 Mode 2: Auto Simulation (Mode Otomatis)

### Deskripsi
Pada mode auto, **cukup tekan 1 tombol** dan seluruh simulasi berjalan otomatis dari startup hingga operasi normal. Kecepatan simulasi **diperlambat** agar ada waktu untuk memahami setiap fase.

### Cara Menggunakan

#### 1️⃣ Start Auto Simulation
```
Tekan: START AUTO SIMULATION button (GPIO 2 - BLUE button)
```
- Sistem langsung start (tidak perlu tekan START manual)
- Simulasi berjalan otomatis
- Kecepatan lambat untuk pembelajaran

#### 2️⃣ Simulasi Berjalan Otomatis

**Phase 1: System Initialization (0-3s)**
```
✓ Reactor system started
✓ All controls initialized
```

**Phase 2: Pressurizer Activation (3-12s)**
```
→ Pressure: 0 → 45 bar (gradual, 0.2s per bar)
→ Visual feedback: Pressure nilai naik perlahan
```

**Phase 3: Coolant Pumps Startup (12-21s)**
```
→ Tertiary Pump: Starting → ON (3s delay)
→ Secondary Pump: Starting → ON (3s delay)
→ Primary Pump: Starting → ON (3s delay)
→ Visual: LED flow animation aktif
```

**Phase 4: Control Rod Withdrawal (21-46s)**
```
→ Shim Rod: 0% → 50% (gradual, 0.5s per 1%)
→ Regulating Rod: 0% → 50% (gradual, 0.5s per 1%)
→ Safety Rod: Tetap 0% (untuk SCRAM only)
→ Visual: Servo motors bergerak bertahap
```

**Phase 5: Steam Generator Activation (46-51s)**
```
→ Humidifier SG1 & SG2: Automatically ON
→ Visual: Uap keluar dari steam generator 💨
```

**Phase 6: Turbine-Generator Startup (51-59s)**
```
→ Turbine: IDLE → STARTING → RUNNING
→ Speed: 0% → 100% (gradual)
→ Visual: Motor turbine spinning up
```

**Phase 7: Power Generation (59-64s)**
```
→ Thermal Power: ~900 MWth
→ Electrical Output: ~200-250 MWe
→ Visual: 10 Power LEDs brightness increasing 💡
```

**Phase 8: Cooling Tower Activation (64-69s)**
```
→ CT Humidifiers 1-4: Activate in stages
→ Visual: Uap keluar dari 4 cooling towers 💨
```

**Phase 9: Normal Operation (69s+)**
```
✅ REACTOR AT STABLE OPERATION
   - Pressure: 45 bar
   - Control Rods: 50% (Shim & Reg)
   - All Pumps: ON
   - Turbine: Running
   - Power: ~200-250 MWe
   - Humidifiers: All active
```

#### 3️⃣ Setelah Auto Simulation Selesai

Sistem otomatis beralih ke **MANUAL mode**:
```
✓ Simulasi tetap berjalan di kondisi stabil
✓ Operator dapat adjust parameter secara manual
✓ Dapat fine-tune control rods
✓ Dapat adjust pressure
```

#### 4️⃣ Stop/Reset Auto Simulation
```
Tekan: REACTOR RESET button
→ Auto simulation berhenti
→ Semua parameter reset ke 0
→ Siap untuk mode baru (manual atau auto lagi)
```

### Keunggulan Mode Auto
✅ **One-Button Start** - Cukup 1 tombol untuk full simulation  
✅ **Educational Pacing** - Kecepatan lambat untuk pembelajaran  
✅ **Complete Sequence** - Menampilkan seluruh startup procedure  
✅ **Hands-free Demo** - Ideal untuk presentasi  
✅ **Understanding Flow** - Melihat alur lengkap tanpa interupsi  
✅ **Consistent Results** - Hasil yang konsisten setiap run  

### Cocok Untuk
- 📊 Presentasi ke audiens (PKM, seminar)
- 🎓 Demonstrasi di kelas yang besar
- 📹 Video edukasi / recording
- 👥 Tour fasilitas dengan pengunjung
- 🏆 Kompetisi / pameran
- 📚 Pengenalan sistem PLTN untuk pemula

---

## 🎯 Perbandingan Mode

| Aspek | Manual Mode | Auto Mode |
|-------|-------------|-----------|
| **Start** | REACTOR START button | START AUTO SIMULATION button |
| **Kontrol** | Operator manual | Fully automatic |
| **Kecepatan** | Sesuai operator | Slow paced (~70s total) |
| **Learning** | Hands-on practice | Observational learning |
| **Repeatability** | Bervariasi | Konsisten |
| **Intervensi** | Kapan saja | Tidak bisa (sampai selesai) |
| **Ideal Untuk** | Training, eksperimen | Demo, presentasi, edukasi |
| **Tombol Dipakai** | 18 tombol available | 1 tombol (start) + reset |
| **Interlock** | Manual compliance | Auto compliance |
| **Duration** | Fleksibel | ~70 detik (fixed) |

---

## 🔄 Switching Between Modes

### Manual → Auto
```
1. REACTOR RESET button (reset kondisi saat ini)
2. START AUTO SIMULATION button
   → Auto simulation dimulai
```

### Auto → Manual (setelah selesai)
```
Otomatis beralih ke manual setelah Phase 9
→ Operator dapat langsung kontrol manual
```

### Stop Any Mode
```
REACTOR RESET button
→ Reset ke kondisi initial
→ Pilih mode baru
```

---

## 📝 Button Summary (18 Total)

### Mode Selection (3 buttons)
```
GPIO 17 - REACTOR START         (GREEN)  → Start manual mode
GPIO 2  - START AUTO SIMULATION (BLUE)   → Start auto mode  
GPIO 27 - REACTOR RESET         (YELLOW) → Reset simulation
```

### Manual Control (14 buttons)
```
Pumps (6):
  GPIO 11 - Pump Primary ON
  GPIO 6  - Pump Primary OFF
  GPIO 13 - Pump Secondary ON
  GPIO 19 - Pump Secondary OFF
  GPIO 26 - Pump Tertiary ON
  GPIO 21 - Pump Tertiary OFF

Rods (6):
  GPIO 20 - Safety Rod UP
  GPIO 16 - Safety Rod DOWN
  GPIO 12 - Shim Rod UP
  GPIO 7  - Shim Rod DOWN
  GPIO 8  - Regulating Rod UP
  GPIO 25 - Regulating Rod DOWN

Pressure (2):
  GPIO 24 - Pressure UP
  GPIO 23 - Pressure DOWN
```

### Emergency (1 button)
```
GPIO 18 - EMERGENCY SHUTDOWN (RED) → SCRAM (works in both modes)
```

---

## 🎓 Educational Benefits

### For Students
- **Mode Manual:** Learn by doing, understand each component
- **Mode Auto:** See the big picture, understand overall flow

### For Instructors
- **Mode Manual:** Interactive teaching, Q&A during operation
- **Mode Auto:** Consistent demo, focus on explanation

### For Visitors
- **Mode Auto:** Quick overview, impressive demonstration
- **Mode Manual:** (Optional) Try it yourself after auto demo

---

## 🛠️ Implementation Details

### Technical Specifications

**Auto Simulation Thread:**
- Dedicated thread for auto sequence
- Non-blocking (other threads continue)
- Cancellable via REACTOR RESET
- Automatic transition to manual after completion

**Timing Breakdown:**
```
Phase 1: 3s    (initialization)
Phase 2: 9s    (pressurizer: 45 bars × 0.2s)
Phase 3: 9s    (pumps: 3 × 3s)
Phase 4: 25s   (rods: 50% × 0.5s)
Phase 5: 5s    (steam generator)
Phase 6: 8s    (turbine startup)
Phase 7: 5s    (power generation)
Phase 8: 5s    (cooling towers)
Phase 9: ∞     (stable operation)
------------------------
Total:   ~70s  (to stable operation)
```

**Safety Features:**
- Emergency button works in both modes
- Auto mode respects all interlock conditions
- Reset cancels auto simulation immediately
- No manual interference during auto run

---

## 🎯 Use Case Examples

### Example 1: Classroom Demonstration
```
1. Instructor: "First, let me show you auto mode"
2. Press START AUTO SIMULATION
3. Explain each phase as it progresses (slow pace helps!)
4. After completion: "Now let's try manual mode"
5. Press REACTOR RESET
6. Press REACTOR START
7. Let students control manually
```

### Example 2: PKM Competition Presentation
```
1. Start with AUTO MODE for judges
   → Shows complete system in 70 seconds
   → Professional, consistent demo
2. Q&A while system runs in stable mode
3. If time permits, demo MANUAL mode
   → Show individual control capability
```

### Example 3: Training New Operators
```
Week 1: AUTO MODE only
  → Understand the sequence
  → See what "normal" looks like
  
Week 2: MANUAL MODE practice
  → Hands-on with guidance
  → Learn proper sequence
  
Week 3: MANUAL MODE independent
  → Operate without help
  → Handle abnormal conditions
```

---

## 🚀 Getting Started

### Quick Start - Auto Mode
```bash
# 1. Run program
cd raspi_central_control
python3 raspi_main_panel.py

# 2. Press BLUE button (GPIO 2)
#    → START AUTO SIMULATION

# 3. Watch the simulation (70s)

# 4. After completion, you're in manual mode
#    → Adjust parameters as needed

# 5. To restart:
#    Press RESET → Choose mode again
```

### Quick Start - Manual Mode
```bash
# 1. Run program
cd raspi_central_control
python3 raspi_main_panel.py

# 2. Press GREEN button (GPIO 17)
#    → REACTOR START (Manual)

# 3. Follow standard startup sequence:
#    a. Raise pressure to 45 bar
#    b. Start pumps (Tertiary → Secondary → Primary)
#    c. Raise control rods gradually
#    d. Monitor system response

# 4. Adjust parameters as needed

# 5. To stop:
#    Press RESET or EMERGENCY
```

---

## 📊 Status Monitoring

### Console Output
Both modes provide detailed logging:

```
Manual Mode:
  [INFO] ✓ Pressure UP: 45.0 bar
  [INFO] ✓ Tertiary pump: STARTING
  [INFO] ✓ Shim rod UP: 25%

Auto Mode:
  [INFO] 📍 Phase 2: Pressurizer Activation
  [INFO]    Pressure: 25.0 bar
  [INFO] 📍 Phase 3: Coolant Pumps Startup
  [INFO]    Starting Tertiary Pump...
```

### OLED Displays (9 screens)
Real-time status for both modes:
- Pressure, pump status, rod positions
- Thermal power, turbine state
- Humidifier status

### Visual Feedback
- 48 LEDs: Flow animation (3 loops)
- 10 LEDs: Power output indicator
- 6 Humidifiers: Steam visual effects
- 3 Servos: Rod position

---

## 🎉 Conclusion

Dengan **Dual Mode Simulation**, PLTN Simulator menjadi lebih fleksibel:

- ✅ **Mode Manual** untuk pembelajaran mendalam dan training praktis
- ✅ **Mode Auto** untuk demonstrasi cepat dan presentasi
- ✅ **Seamless switching** antara kedua mode
- ✅ **Educational focus** dengan pacing yang tepat

**Perfect for PKM Competition! 🏆**

---

## 📞 Support

Jika ada pertanyaan tentang dual mode simulation:
1. Lihat log output untuk detail phase
2. Periksa button wiring (18 buttons)
3. Test individual mode dulu sebelum switch
4. Review timing jika perlu adjust

---

**Version:** 3.4 with Dual Mode Support  
**Last Updated:** December 2024  
**Status:** ✅ Ready for Production & PKM Competition

---

🎓 **Educational Excellence + Professional Demo = PKM Winner! 🏆**
