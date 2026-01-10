# 🎨 Pygame Animation Capabilities untuk PLTN Simulator

## ✅ JAWABAN: Ya, Pygame SANGAT BISA untuk Animasi!

Pygame adalah game engine, jadi **animation adalah kekuatan utamanya**.

---

## 🎬 Apa yang Bisa Dibuat dengan Pygame?

### **1. Basic Animations (Easy)**

| Animation Type | Complexity | Use Case |
|----------------|------------|----------|
| **Moving Objects** | ⭐ Easy | Partikel air bergerak |
| **Sprite Animation** | ⭐ Easy | Rotating turbine |
| **Color Transitions** | ⭐ Easy | Temperature heatmap |
| **Progress Bars** | ⭐ Easy | Already implemented! |
| **Text Animation** | ⭐ Easy | Fading text, scrolling |

### **2. Intermediate Animations**

| Animation Type | Complexity | Use Case |
|----------------|------------|----------|
| **Particle Systems** | ⭐⭐ Medium | Steam effect, bubbles |
| **Path Following** | ⭐⭐ Medium | Coolant flow animation |
| **Sprite Sheets** | ⭐⭐ Medium | Complex animations |
| **Scaling/Rotation** | ⭐⭐ Medium | Pump rotation, valves |
| **Easing Functions** | ⭐⭐ Medium | Smooth transitions |

### **3. Advanced Animations**

| Animation Type | Complexity | Use Case |
|----------------|------------|----------|
| **Physics Simulation** | ⭐⭐⭐ Hard | Realistic fluid flow |
| **Skeletal Animation** | ⭐⭐⭐ Hard | Complex machinery |
| **Shader Effects** | ⭐⭐⭐ Hard | Glow, blur effects |
| **Real-time Graphs** | ⭐⭐⭐ Hard | Live data plotting |

---

## 🎯 Rekomendasi Animasi untuk PLTN Simulator

### **Konsep Visual:**

```
┌──────────────────────────────────────────────────┐
│                  STEP 3                          │
│         Start Primary Pump                       │
│                                                  │
│    ╔════════════════════════╗                   │
│    ║   REACTOR CORE         ║                   │
│    ║                        ║                   │
│    ║    ⚛️  [Animated]     ║  ← Rotating atom   │
│    ║                        ║     or glow        │
│    ╚════════════════════════╝                   │
│              │ ↓ ↓ ↓  Animated flow             │
│    ╔════════════════════════╗                   │
│    ║   PRIMARY PUMP         ║                   │
│    ║   [⟳ Rotating]    ON  ║  ← Spinning blade  │
│    ╚════════════════════════╝                   │
│              │ ↓ ↓ ↓  Animated flow             │
│    ╔════════════════════════╗                   │
│    ║   STEAM GENERATOR      ║                   │
│    ║   [≈≈≈ Steam]     ON  ║  ← Rising steam    │
│    ╚════════════════════════╝                   │
│                                                  │
│  Progress: [▓▓▓▓▓░░░░░] 50%                    │
└──────────────────────────────────────────────────┘
```

---

## 💡 Contoh Animasi Simple (Copy-Paste Ready)

### **1. Flow Particles (Coolant Flow)**

```python
import random

class FlowParticle:
    """Animated particle untuk simulasi aliran coolant"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, 3)
        self.color = (0, 150, 255)  # Blue coolant
        self.size = random.randint(2, 4)
    
    def update(self):
        self.y += self.speed  # Move downward
        if self.y > 600:  # Reset at bottom
            self.y = 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, 
                         (int(self.x), int(self.y)), self.size)

# Usage:
# particles = [FlowParticle(640, random.randint(0, 600)) for _ in range(30)]
# 
# In main loop:
# for particle in particles:
#     particle.update()
#     particle.draw(screen)
```

### **2. Rotating Pump/Turbine**

```python
import math

class RotatingPump:
    """Animated rotating pump blade"""
    def __init__(self, x, y, radius=30):
        self.x = x
        self.y = y
        self.radius = radius
        self.angle = 0
        self.speed = 0  # RPM (set > 0 to rotate)
        self.blades = 4
    
    def update(self):
        if self.speed > 0:
            self.angle += self.speed * 0.1
            if self.angle >= 360:
                self.angle = 0
    
    def draw(self, screen):
        # Draw center circle
        pygame.draw.circle(screen, (100, 100, 100), 
                         (self.x, self.y), 10)
        
        # Draw rotating blades
        for i in range(self.blades):
            angle_rad = math.radians(self.angle + i * (360/self.blades))
            end_x = self.x + self.radius * math.cos(angle_rad)
            end_y = self.y + self.radius * math.sin(angle_rad)
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.x, self.y), (end_x, end_y), 4)

# Usage:
# pump = RotatingPump(400, 300)
# pump.speed = 5  # Set RPM
#
# In main loop:
# pump.update()
# pump.draw(screen)
```

### **3. Steam/Smoke Particles**

```python
class SteamParticle:
    """Rising steam/smoke effect"""
    def __init__(self, x, y):
        self.x = x + random.randint(-10, 10)
        self.y = y
        self.speed = random.uniform(1, 3)
        self.alpha = 255  # Transparency
        self.size = random.randint(3, 8)
        self.lifetime = 0
    
    def update(self):
        self.y -= self.speed  # Rise upward
        self.alpha -= 3  # Fade out
        self.size += 0.2  # Expand
        self.lifetime += 1
    
    def is_alive(self):
        return self.alpha > 0 and self.lifetime < 100
    
    def draw(self, screen):
        if self.alpha > 0:
            color = (220, 220, 220)  # Light gray
            # Note: Pygame doesn't support alpha per-draw easily
            # For simple version, just draw circle
            pygame.draw.circle(screen, color, 
                             (int(self.x), int(self.y)), 
                             int(self.size), 1)

# Usage:
# steam_particles = []
#
# In main loop (spawn new):
# if thermal_power > 50000:
#     if random.random() < 0.3:  # 30% chance
#         steam_particles.append(SteamParticle(640, 300))
#
# Update all:
# for steam in steam_particles[:]:
#     steam.update()
#     if steam.is_alive():
#         steam.draw(screen)
#     else:
#         steam_particles.remove(steam)
```

### **4. Pulsing Glow Effect**

```python
class GlowingReactor:
    """Pulsing glow untuk reactor core"""
    def __init__(self, x, y, base_radius=50):
        self.x = x
        self.y = y
        self.base_radius = base_radius
        self.glow = 0
        self.glow_direction = 1
        self.power_level = 0
    
    def update(self, power_percent):
        self.power_level = power_percent
        
        if power_percent > 0:
            # Pulse effect
            self.glow += self.glow_direction * 0.5
            if self.glow > 10:
                self.glow_direction = -1
            elif self.glow < 0:
                self.glow_direction = 1
    
    def draw(self, screen):
        if self.power_level > 0:
            # Draw glow layers (simulated)
            intensity = int(100 + self.power_level * 1.5)
            
            # Outer glow
            pygame.draw.circle(screen, 
                             (intensity, intensity//2, 0), 
                             (self.x, self.y), 
                             int(self.base_radius + self.glow + 10), 1)
            
            # Middle glow
            pygame.draw.circle(screen, 
                             (255, intensity, 0), 
                             (self.x, self.y), 
                             int(self.base_radius + self.glow), 2)
            
            # Core
            pygame.draw.circle(screen, 
                             (255, 200, 0), 
                             (self.x, self.y), 
                             self.base_radius)

# Usage:
# reactor = GlowingReactor(640, 200)
#
# In main loop:
# power = (shim_rod + reg_rod) / 2  # 0-100%
# reactor.update(power)
# reactor.draw(screen)
```

### **5. Temperature Heatmap Color**

```python
def get_temp_color(temperature, min_temp=0, max_temp=350):
    """
    Get color based on temperature
    Blue (cold) → Green → Yellow → Red (hot)
    """
    ratio = (temperature - min_temp) / (max_temp - min_temp)
    ratio = max(0, min(1, ratio))
    
    if ratio < 0.33:  # Blue to green
        r = 0
        g = int(255 * (ratio / 0.33))
        b = int(255 * (1 - ratio / 0.33))
    elif ratio < 0.66:  # Green to yellow
        r = int(255 * ((ratio - 0.33) / 0.33))
        g = 255
        b = 0
    else:  # Yellow to red
        r = 255
        g = int(255 * (1 - (ratio - 0.66) / 0.34))
        b = 0
    
    return (r, g, b)

# Usage:
# temp = 280  # Celsius
# color = get_temp_color(temp, 0, 350)
# pygame.draw.circle(screen, color, (x, y), 20)
```

### **6. Animated Flow Arrows**

```python
class FlowArrow:
    """Animated dashed arrow showing flow direction"""
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.offset = 0
        self.dash_length = 10
    
    def update(self):
        self.offset += 2
        if self.offset > self.dash_length * 2:
            self.offset = 0
    
    def draw(self, screen):
        color = (0, 200, 255)
        length = math.sqrt((self.x2-self.x1)**2 + (self.y2-self.y1)**2)
        steps = int(length / self.dash_length)
        
        for i in range(steps):
            # Draw dashes that move
            if (i * self.dash_length + self.offset) % (self.dash_length * 2) < self.dash_length:
                t1 = i / steps
                t2 = min((i + 1) / steps, 1)
                
                x1 = self.x1 + (self.x2 - self.x1) * t1
                y1 = self.y1 + (self.y2 - self.y1) * t1
                x2 = self.x1 + (self.x2 - self.x1) * t2
                y2 = self.y1 + (self.y2 - self.y1) * t2
                
                pygame.draw.line(screen, color, (int(x1), int(y1)), 
                               (int(x2), int(y2)), 3)

# Usage:
# arrow = FlowArrow(640, 200, 640, 400)  # Vertical down
#
# In main loop:
# arrow.update()
# arrow.draw(screen)
```

---

## 🎨 Complete Example: Animated PLTN Diagram

```python
class AnimatedPLTNDiagram:
    """Complete animated PLTN diagram untuk MANUAL mode"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Components
        self.reactor = GlowingReactor(self.width//2, 150)
        self.primary_pump = RotatingPump(self.width//2, 300)
        self.steam_gen = (self.width//2 + 150, 150)  # Position
        self.turbine = RotatingPump(self.width//2 + 300, 150, radius=40)
        
        # Animations
        self.flow_particles = []
        self.steam_particles = []
        self.flow_arrow = FlowArrow(self.width//2, 200, self.width//2, 280)
    
    def update(self, state):
        """Update all animations based on simulation state"""
        # Reactor glow
        power = (state.get("shim_rod", 0) + state.get("regulating_rod", 0)) / 2
        self.reactor.update(power)
        
        # Primary pump
        if state.get("pump_primary", 0) > 0:
            self.primary_pump.speed = 5
            
            # Spawn flow particles
            if random.random() < 0.1:
                self.flow_particles.append(
                    FlowParticle(self.width//2, 200)
                )
        else:
            self.primary_pump.speed = 0
        
        self.primary_pump.update()
        
        # Turbine
        if state.get("thermal_kw", 0) > 50000:
            self.turbine.speed = 10
        else:
            self.turbine.speed = 0
        self.turbine.update()
        
        # Flow particles
        for particle in self.flow_particles[:]:
            particle.update()
            if particle.y > 600:
                self.flow_particles.remove(particle)
        
        # Steam particles
        if state.get("thermal_kw", 0) > 50000:
            if random.random() < 0.2:
                self.steam_particles.append(
                    SteamParticle(self.steam_gen[0], self.steam_gen[1])
                )
        
        for steam in self.steam_particles[:]:
            steam.update()
            if not steam.is_alive():
                self.steam_particles.remove(steam)
        
        # Flow arrow
        self.flow_arrow.update()
    
    def draw(self):
        """Draw all components"""
        # Draw components
        self.reactor.draw(self.screen)
        self.primary_pump.draw(self.screen)
        self.turbine.draw(self.screen)
        
        # Draw steam generator box
        pygame.draw.rect(self.screen, (150, 150, 150),
                        (self.steam_gen[0]-40, self.steam_gen[1]-40, 80, 80), 2)
        
        # Draw animations
        self.flow_arrow.draw(self.screen)
        
        for particle in self.flow_particles:
            particle.draw(self.screen)
        
        for steam in self.steam_particles:
            steam.draw(self.screen)

# Usage in video_display_app.py:
# 
# In __init__:
# self.pltn_diagram = AnimatedPLTNDiagram(self.screen)
#
# In draw_manual_guide:
# self.pltn_diagram.update(state)
# self.pltn_diagram.draw()
```

---

## 🚀 Roadmap Implementation

### **Phase 1: Foundation (1-2 hours)**
- [ ] Add basic classes (FlowParticle, RotatingPump)
- [ ] Test each animation individually
- [ ] Adjust colors and speeds

### **Phase 2: Integration (2-3 hours)**
- [ ] Create AnimatedPLTNDiagram class
- [ ] Integrate with manual mode
- [ ] Test dengan mock data

### **Phase 3: Polish (1-2 hours)**
- [ ] Tune animation speeds
- [ ] Add more visual feedback
- [ ] Optimize performance (if needed)

---

## ✅ Summary

**Pygame Animation Capabilities:**
- ✅ Particles (flow, steam) - EASY
- ✅ Rotation (pumps, turbine) - EASY
- ✅ Color effects (temperature) - EASY
- ✅ Glow/pulse effects - MEDIUM
- ✅ Complex diagrams - MEDIUM

**Recommendations:**
1. Start simple: Flow arrows + rotating pumps
2. Add one animation at a time
3. Test performance (should be 60 FPS)
4. Make it educational, not just pretty!

**Next Step:**
Want me to create a full working example file? Or discuss the visual flow/layout first?
