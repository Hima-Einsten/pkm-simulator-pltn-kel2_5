# 🎬 PLTN Video Display System - 3 Mode Design Specification

## 📋 System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           PLTN DISPLAY SYSTEM - 3 MODES                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  MODE 1: IDLE      → Branding & Information            │
│  MODE 2: MANUAL    → Interactive Animated Guide        │
│  MODE 3: AUTO      → Educational Video Playback        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 MODE 1: IDLE - Branding Screen

### **Purpose:**
- Display ketika tidak ada interaksi
- Professional branding untuk exhibition
- Informasi institusi & project

### **Layout Design:**

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ┌────────┐                           ┌────────┐        ║
║   │  BRIN  │                           │ POLTEK │        ║
║   │  LOGO  │                           │  LOGO  │        ║
║   └────────┘                           └────────┘        ║
║                                                           ║
║                                                           ║
║                                                           ║
║              ALAT PERAGA PLTN TIPE PWR                   ║
║           BERBASIS MIKROKONTROLER                        ║
║                                                           ║
║                                                           ║
║        Politeknik Teknologi Nuklir Indonesia             ║
║                                                           ║
║                                                           ║
║                                                           ║
║         [Tekan tombol untuk memulai simulasi]            ║
║                                                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### **Technical Specs:**

**Components:**
1. **Logos (Top)**
   - Position: Top corners (20px from edge)
   - Size: 120x120px each
   - Format: PNG with transparency
   - Files: `logo_brin.png`, `logo_poltek.png`

2. **Main Title (Center)**
   - Font: Bold, 60px
   - Color: Cyan (#00C8FF)
   - Text: "ALAT PERAGA PLTN TIPE PWR"
   - Position: Center, Y = 35%

3. **Subtitle**
   - Font: Bold, 48px
   - Color: White (#FFFFFF)
   - Text: "BERBASIS MIKROKONTROLER"
   - Position: Center, Y = 45%

4. **Institution Name**
   - Font: Medium, 40px
   - Color: Light Gray (#CCCCCC)
   - Text: "Politeknik Teknologi Nuklir Indonesia"
   - Position: Center, Y = 60%

5. **Instruction Text (Bottom)**
   - Font: Regular, 32px
   - Color: Yellow (#FFD700)
   - Text: "Tekan START AUTO SIMULATION atau gunakan MANUAL MODE"
   - Position: Bottom, Y = 80%
   - Animation: Subtle fade in/out (1s cycle)

### **Animations (Subtle):**
- Fading instruction text (alpha: 200 ↔ 255)
- Optional: Slow rotating atom icon di center
- Optional: Particle background effect (very subtle)

---

## 🎮 MODE 2: MANUAL - Interactive Animated Guide

### **Purpose:**
- Step-by-step interactive training
- Real-time visual feedback
- Educational dengan animasi PLTN
- Sync dengan state simulasi backend

### **Layout Design:**

```
╔═══════════════════════════════════════════════════════════╗
║ [Logo] PLTN Simulator - Manual Mode            [Logo]    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ┌─────────────────────────────────────────────────┐    ║
║  │        ANIMATED PLTN DIAGRAM                    │    ║
║  │                                                  │    ║
║  │   ╔══════╗       ╔══════╗                      │    ║
║  │   ║ ⚛️   ║  ↓↓↓  ║ ≈≈≈  ║   ⟳                 │    ║
║  │   ║REACT ║ FLOW  ║STEAM ║  TURB    [POWER]    │    ║
║  │   ║[Glow]║ ━━→   ║ GEN  ║ ━━━→     250 MWe    │    ║
║  │   ╚══════╝       ╚══════╝                      │    ║
║  │      ↓              │                           │    ║
║  │   [⟳ PUMP]     RETURN FLOW                     │    ║
║  │    PRIMARY         ↓                           │    ║
║  │                                                  │    ║
║  └─────────────────────────────────────────────────┘    ║
║                                                           ║
║  ╔═══════════════════════════════════════════════════╗  ║
║  ║  STEP 4: Withdraw Control Rods                   ║  ║
║  ║  Target: Raise Shim Rod to 50%                   ║  ║
║  ╚═══════════════════════════════════════════════════╝  ║
║                                                           ║
║  Pressure:   140 bar  [▓▓▓▓▓▓▓▓▓░] 90%                 ║
║  Safety Rod: 100%     [▓▓▓▓▓▓▓▓▓▓] FULL                ║
║  Shim Rod:   30%      [▓▓▓░░░░░░░] → Target: 50%       ║
║  Reg Rod:    30%      [▓▓▓░░░░░░░]                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### **Technical Specs:**

**1. Header Bar (Top 60px)**
- Logo BRIN (left): 40x40px
- Title: "PLTN Simulator - Manual Mode"
- Logo Poltek (right): 40x40px
- Background: Dark blue (#1A1A2E)

**2. Animated PLTN Diagram (Center, 500px height)**
- Full animated components:
  - ⚛️ Reactor: Pulsing glow (based on power)
  - ↓↓↓ Flow: Animated particles
  - ⟳ Pumps: Rotating blades
  - ≈≈≈ Steam: Rising particles
  - ⟳ Turbine: Spinning
  - Temperature colors (blue → red)

**3. Step Instruction Box (150px height)**
- Current step number & description
- Clear, large text
- Highlighted background

**4. Progress Bars (Bottom 200px)**
- 4 parameters dengan visual bars
- Real-time update
- Color-coded (green = good, yellow = warning, red = danger)

### **Animations:**
- Reactor glow: Pulse intensity based on power
- Flow particles: Move along pipes
- Pump rotation: Speed based on status
- Steam: Rise from steam generator
- Turbine: Spin speed based on power
- Temperature: Heatmap colors

### **Educational Features:**
- Component labels appear on hover (optional)
- Flow direction arrows
- Real-time parameter display
- Step-by-step guidance

---

## 📹 MODE 3: AUTO - Video Playback

### **Purpose:**
- Play complete educational video
- Automated demonstration
- Loop until simulation complete
- Synchronized dengan auto simulation timing

### **Layout Design:**

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                                                           ║
║                                                           ║
║                                                           ║
║                                                           ║
║                  [VIDEO FULLSCREEN]                      ║
║                                                           ║
║              Video: penjelasan.mp4                       ║
║              Duration: ~70 seconds                       ║
║              Loop: Yes (until auto sim done)             ║
║                                                           ║
║                                                           ║
║                                                           ║
║                                                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### **Technical Specs:**

**Video Player:**
- Backend: mpv (fullscreen, hardware accelerated)
- File: `assets/penjelasan.mp4`
- Loop: Yes (--loop=inf)
- Controls: Hidden (no OSD)
- Audio: Enabled

**Video Content (Recommendations):**
- Duration: 60-90 seconds
- Format: MP4 (H.264)
- Resolution: 1920x1080 or 1280x720
- Content: Complete PWR process explanation
- Narration: Indonesian language
- Background music: Subtle (low volume)

**Sync dengan Simulasi:**
- Video loops continuously
- Stops when auto simulation completes
- Transitions to MANUAL mode
- Smooth fade transition

---

## 🔄 Mode Transition Logic

### **State Machine:**

```
         ┌──────────────┐
    ┌───→│     IDLE     │←────┐
    │    └──────────────┘     │
    │           │              │
    │           │ user action  │
    │           ▼              │
    │    ┌──────────────┐     │
    │    │   Detect     │     │
    │    │   Button     │     │
    │    └──────────────┘     │
    │      │          │        │
    │      │ MANUAL   │ AUTO   │
    │      │          │        │
    │      ▼          ▼        │
    │  ┌────────┐  ┌────────┐ │
    └──│ MANUAL │  │  AUTO  │─┘
       └────────┘  └────────┘
          │            │
          │ RESET      │ RESET
          └────────────┘
```

### **Transition Triggers:**

**To IDLE:**
- System startup
- RESET button pressed
- No activity for 5 minutes (optional)
- Emergency stop

**To MANUAL:**
- From IDLE: Any manual button pressed
- From AUTO: Auto simulation complete
- Mode: `simulation_mode = 'manual'`

**To AUTO:**
- From IDLE: START AUTO SIMULATION button
- From MANUAL: START AUTO SIMULATION button
- Mode: `simulation_mode = 'auto'` AND `auto_running = True`

---

## 🎨 Visual Style Guide

### **Color Palette:**

```python
COLORS = {
    # Background
    'bg_dark': (20, 20, 40),
    'bg_light': (40, 40, 60),
    
    # Branding
    'primary_cyan': (0, 200, 255),
    'accent_yellow': (255, 215, 0),
    
    # Status
    'success': (0, 255, 100),
    'warning': (255, 200, 0),
    'danger': (255, 50, 50),
    'info': (100, 150, 255),
    
    # Text
    'text_white': (255, 255, 255),
    'text_gray': (200, 200, 200),
    'text_dark': (100, 100, 100),
    
    # Components
    'reactor_glow': (255, 150, 0),
    'coolant': (0, 150, 255),
    'steam': (220, 220, 220),
    'hot': (255, 100, 0),
    'cold': (0, 100, 255)
}
```

### **Typography:**

```python
FONTS = {
    'title': ('Arial', 60, 'bold'),
    'subtitle': ('Arial', 48, 'bold'),
    'heading': ('Arial', 40, 'bold'),
    'body': ('Arial', 32, 'normal'),
    'small': ('Arial', 24, 'normal'),
    'tiny': ('Arial', 18, 'normal')
}
```

### **Layout Grid:**

```python
LAYOUT = {
    'margin': 20,           # Screen margin
    'padding': 15,          # Component padding
    'spacing': 10,          # Element spacing
    'header_height': 60,    # Top header bar
    'footer_height': 200,   # Progress bars area
    'logo_size': (120, 120) # Logo dimensions (idle)
}
```

---

## 📁 Asset Requirements

### **Images:**

```
assets/
├── penjelasan.mp4           ✅ Video for AUTO mode
├── logo_brin.png            ⚠️  NEEDED (transparent PNG, 512x512)
├── logo_poltek.png          ⚠️  NEEDED (transparent PNG, 512x512)
└── (optional sprites)
    ├── reactor_icon.png
    ├── pump_icon.png
    └── turbine_icon.png
```

### **Logo Specifications:**

**Format:**
- PNG with transparency
- High resolution: 512x512px minimum
- Will be scaled to:
  - IDLE mode: 120x120px
  - MANUAL mode: 40x40px

**Design Guidelines:**
- Clean, simple design
- Good contrast on dark background
- Professional appearance

---

## 🚀 Implementation Priority

### **Phase 1: Core Structure (2-3 hours)**

**Files to create:**
1. `video_display_app_v2.py` (enhanced version)
2. `animations.py` (animation classes)
3. `layouts.py` (layout constants)

**Tasks:**
- [ ] Update IDLE screen with logos & text
- [ ] Add logo loading & rendering
- [ ] Implement fade animation for instruction text
- [ ] Test IDLE screen looks good

### **Phase 2: MANUAL Mode Animations (1-2 days)**

**Tasks:**
- [ ] Design PLTN diagram layout (positions)
- [ ] Implement FlowParticle system
- [ ] Implement RotatingPump/Turbine
- [ ] Implement SteamParticle system
- [ ] Implement GlowingReactor
- [ ] Add temperature color coding
- [ ] Integrate animations with state data
- [ ] Test all animations smooth (60 FPS)

### **Phase 3: Polish & Integration (1 day)**

**Tasks:**
- [ ] Fine-tune animation speeds
- [ ] Add smooth transitions between modes
- [ ] Test mode switching
- [ ] Optimize performance
- [ ] User testing & feedback
- [ ] Final adjustments

---

## 🎯 Success Criteria

### **IDLE Mode:**
- ✅ Logos displayed clearly
- ✅ Text readable from 2-3 meters
- ✅ Professional appearance
- ✅ Subtle animations not distracting
- ✅ Clear call-to-action

### **MANUAL Mode:**
- ✅ Diagram clear and educational
- ✅ Animations smooth (60 FPS)
- ✅ Real-time sync with simulation
- ✅ Step instructions easy to follow
- ✅ Progress bars intuitive
- ✅ Logos visible but not distracting

### **AUTO Mode:**
- ✅ Video plays smoothly
- ✅ Loop works correctly
- ✅ Audio clear
- ✅ Transitions smooth
- ✅ Synchronized with simulation timing

---

## 💡 Recommendations

### **Logo Placement:**

**IDLE Mode:**
```
Best: Top corners, large (120x120)
- Professional
- Balanced layout
- Clear branding
```

**MANUAL Mode:**
```
Best: Top corners, small (40x40)
- Present but not distracting
- Maintains branding
- Doesn't obscure content
```

### **Animation Balance:**

**Key Principle:** Educational > Flashy

- Use animations to **explain**, not just decorate
- Flow arrows show **direction** clearly
- Colors indicate **temperature/status**
- Speed reflects **actual operation**
- Keep it **simple and clear**

### **Text Guidelines:**

- **IDLE:** Large, centered, inspiring
- **MANUAL:** Clear, instructional, concise
- **Font size:** Readable from 2m distance
- **Contrast:** High contrast on dark bg
- **Hierarchy:** Clear visual hierarchy

---

## 📋 Next Steps

### **Immediate (Today):**

1. **Prepare logos:**
   - Find/create logo BRIN (PNG, transparent)
   - Find/create logo Poltek (PNG, transparent)
   - Save to `assets/` folder
   - Test loading in pygame

2. **Update IDLE screen:**
   - Load & display logos
   - Add institution text
   - Add fade animation
   - Test appearance

### **This Week:**

3. **Design PLTN diagram:**
   - Sketch layout on paper/digital
   - Decide component positions
   - List all animations needed
   - Plan step-by-step flow

4. **Implement basic animations:**
   - Start with FlowParticle
   - Add RotatingPump
   - Test performance

### **Next Week:**

5. **Complete MANUAL mode:**
   - Full animated diagram
   - All components working
   - State synchronization
   - Polish & optimize

6. **Testing:**
   - Test all 3 modes
   - User feedback
   - Final adjustments

---

## ✅ Summary

**Your Concept:** ⭐⭐⭐⭐⭐ **EXCELLENT!**

**Why it's good:**
- ✅ Clear separation of modes
- ✅ Professional branding (IDLE)
- ✅ Educational focus (MANUAL)
- ✅ Video for AUTO (easy)
- ✅ Logos maintain branding
- ✅ Scalable design

**Implementation:**
- IDLE: 2-3 hours (after logos ready)
- MANUAL: 1-2 days (animations)
- AUTO: Already working ✅

**Priority:**
1. Get logos (PNG files)
2. Update IDLE screen
3. Design PLTN diagram layout
4. Implement animations incrementally

**Status:** Ready to implement!

Mau saya mulai update code untuk IDLE screen dulu? Atau mau diskusi PLTN diagram layout untuk MANUAL mode? 🎨
