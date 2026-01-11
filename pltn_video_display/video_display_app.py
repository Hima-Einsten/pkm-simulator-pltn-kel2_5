"""
PLTN Video Display Application
Menampilkan video edukasi atau interactive guide
Fullscreen ke HDMI monitor

TESTING MODE: Run standalone tanpa simulasi backend
PRODUCTION MODE: Read state dari /tmp/pltn_state.json
"""

import pygame
import json
import time
import sys
import subprocess
from pathlib import Path
from enum import Enum
from typing import Optional, Dict
import argparse

# Initialize Pygame
pygame.init()

class DisplayMode(Enum):
    AUTO_VIDEO = "auto_video"           # Play full video (auto sim)
    MANUAL_GUIDE = "manual_guide"       # Show step guide (manual)
    IDLE = "idle"                       # Standby/intro screen


class VideoDisplayApp:
    """
    Video Display Application for PLTN Simulator
    
    Supports 2 modes:
    1. TESTING MODE: Standalone dengan mock data
    2. PRODUCTION MODE: Read dari simulasi backend
    """
    
    def __init__(self, test_mode: bool = False, fullscreen: bool = True):
        """
        Initialize video display app
        
        Args:
            test_mode: If True, gunakan mock data tanpa simulasi
            fullscreen: If True, fullscreen window
        """
        self.test_mode = test_mode
        
        # Fullscreen window atau windowed (untuk testing)
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1280, 720))
        
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("PLTN Simulator - Educational Display")
        
        # Calculate scale factor for 4K displays
        # Base design: 1920x1080, actual: could be 3840x2160
        self.scale_x = self.width / 1920.0
        self.scale_y = self.height / 1080.0
        self.scale = min(self.scale_x, self.scale_y)  # Use minimum to maintain aspect ratio
        
        print(f"🖥️  Display: {self.width}x{self.height}")
        print(f"📏 Scale factor: {self.scale:.2f}x")
        
        # State file path (cross-platform)
        if sys.platform == 'win32':
            # Windows: use temp folder
            self.state_file = Path("C:/temp/pltn_state.json")
            self.state_file.parent.mkdir(exist_ok=True)
        else:
            # Linux/RPi: use /tmp
            self.state_file = Path("/tmp/pltn_state.json")
        
        self.last_state = {}
        
        # Video player (mpv subprocess)
        self.video_process = None
        self.current_video = None
        
        # Display mode
        self.display_mode = DisplayMode.IDLE
        
        # Fonts - Enhanced for professional display with better hierarchy
        # Scale fonts based on display resolution (4K support)
        base_scale = int(self.scale * 56)
        self.font_display = pygame.font.Font(None, base_scale)                    # Main title (IDLE)
        self.font_title = pygame.font.Font(None, int(base_scale * 0.86))          # Title (48)
        self.font_subtitle = pygame.font.Font(None, int(base_scale * 0.75))       # Subtitle (42)
        self.font_heading = pygame.font.Font(None, int(base_scale * 0.71))        # Institution (40)
        self.font_large = pygame.font.Font(None, int(base_scale * 0.64))          # Large text (36)
        self.font_medium = pygame.font.Font(None, int(base_scale * 0.54))         # Medium text (30)
        self.font_body = pygame.font.Font(None, int(base_scale * 0.50))           # Body text (28)
        self.font_small = pygame.font.Font(None, int(base_scale * 0.43))          # Small text (24)
        self.font_caption = pygame.font.Font(None, int(base_scale * 0.36))        # Caption/tiny (20)
        
        # Professional Nuclear Blue Color Palette
        # === BACKGROUNDS ===
        self.COLOR_BG = (10, 25, 41)              # #0A1929 - Deep Navy
        self.COLOR_BG_SECONDARY = (19, 47, 76)    # #132F4C - Medium Navy
        self.COLOR_BG_TERTIARY = (30, 73, 118)    # #1E4976 - Bright Navy
        self.COLOR_BG_PANEL = (26, 35, 46)        # #1A232E - Panel background
        
        # === BRAND COLORS ===
        self.COLOR_PRIMARY = (0, 180, 216)        # #00B4D8 - Cyan Blue
        self.COLOR_PRIMARY_BRIGHT = (0, 229, 255) # #00E5FF - Bright Cyan
        self.COLOR_PRIMARY_LIGHT = (72, 202, 228) # #48CAE4 - Sky Blue
        
        # === TEXT ===
        self.COLOR_TEXT = (255, 255, 255)         # #FFFFFF - Pure White
        self.COLOR_TEXT_SECONDARY = (224, 231, 255) # #E0E7FF - Light Blue Tint
        self.COLOR_TEXT_TERTIARY = (144, 202, 249)  # #90CAF9 - Pale Blue
        self.COLOR_TEXT_MUTED = (84, 110, 122)    # #546E7A - Blue Gray
        
        # === STATUS ===
        self.COLOR_SUCCESS = (76, 175, 80)        # #4CAF50 - Green
        self.COLOR_WARNING = (255, 167, 38)       # #FFA726 - Orange
        self.COLOR_ERROR = (239, 83, 80)          # #EF5350 - Red
        self.COLOR_INFO = (41, 182, 246)          # #29B6F6 - Light Blue
        
        # === ACCENTS ===
        self.COLOR_GOLD = (255, 179, 0)           # #FFB300 - Amber Gold
        self.COLOR_ENERGY = (0, 229, 255)         # #00E5FF - Energy Cyan
        self.COLOR_SAFETY = (118, 255, 3)         # #76FF03 - Safety Green
        
        # === UI ELEMENTS ===
        self.COLOR_BORDER = (72, 202, 228)        # #48CAE4 - Sky Blue
        self.COLOR_SEPARATOR = (30, 73, 118)      # #1E4976 - Bright Navy
        self.COLOR_HOVER = (19, 47, 76)           # #132F4C - Medium Navy
        
        # Legacy compatibility (deprecated, will be removed)
        self.COLOR_ACCENT = self.COLOR_PRIMARY_BRIGHT
        
        # Logo sizes - scaled for 4K
        self.logo_size_large = (int(120 * self.scale), int(120 * self.scale))  # IDLE mode
        self.logo_size_small = (int(60 * self.scale), int(60 * self.scale))    # MANUAL mode
        self.load_logos()
        
        # IDLE screen animation
        self.idle_fade_alpha = 255
        self.idle_fade_direction = -1
        self.idle_fade_speed = 2
        
        # Mode transition tracking
        self.last_state_hash = None  # Track state changes
        self.auto_complete_time = None  # Track when auto simulation completes
        self.user_has_interacted = False  # Track if user pressed any button
        self.last_pressure = 0
        self.last_rods_sum = 0
        self.last_pumps_sum = 0
        
        # Manual guide - step tracker
        self.current_step = 0
        self.steps_completed = []
        
        # Test mode variables
        if self.test_mode:
            print("🧪 TESTING MODE ACTIVE")
            print("   Using mock simulation data")
            print("   Press keys to simulate states:")
            print("   - I: IDLE mode (branding screen)")
            print("   - M: MANUAL mode (interactive guide)")
            print("   - A: AUTO mode (play video)")
            print("   - UP/DOWN: Adjust pressure values")
            print("   - R: Toggle control rods")
            print("   - P: Toggle pumps")
            print("   - ESC: Exit")
            self.mock_state = self.create_mock_state()
            self.mock_mode = "idle"  # Start with IDLE
        else:
            print("🚀 PRODUCTION MODE")
            print(f"   Reading state from: {self.state_file}")
        
        print(f"🎬 Video Display App initialized")
        print(f"   Screen: {self.width}x{self.height}")
        print(f"   Fullscreen: {fullscreen}")
        if self.logo_brin and self.logo_poltek:
            print(f"   ✅ Logos loaded successfully")
        else:
            print(f"   ⚠️  Logos not found (will skip)")
    
    def load_logos(self):
        """Load BRIN and Poltek logos from assets folder"""
        try:
            logo_path_brin = Path(__file__).parent / "assets" / "logo-brin.png"
            logo_path_poltek = Path(__file__).parent / "assets" / "logo-poltek.png"
            
            if logo_path_brin.exists():
                logo_img = pygame.image.load(str(logo_path_brin))
                # Scale for IDLE mode (large)
                self.logo_brin = pygame.transform.smoothscale(logo_img, self.logo_size_large)
                print(f"   ✅ Loaded BRIN logo")
            else:
                print(f"   ⚠️  BRIN logo not found: {logo_path_brin}")
            
            if logo_path_poltek.exists():
                logo_img = pygame.image.load(str(logo_path_poltek))
                # Scale for IDLE mode (large)
                self.logo_poltek = pygame.transform.smoothscale(logo_img, self.logo_size_large)
                print(f"   ✅ Loaded Poltek logo")
            else:
                print(f"   ⚠️  Poltek logo not found: {logo_path_poltek}")
        
        except Exception as e:
            print(f"   ❌ Error loading logos: {e}")
            self.logo_brin = None
            self.logo_poltek = None
    
    def create_mock_state(self) -> Dict:
        """Create mock state for testing"""
        return {
            "timestamp": time.time(),
            "mode": "manual",
            "auto_running": False,
            "auto_phase": "",
            "pressure": 0.0,
            "safety_rod": 0,
            "shim_rod": 0,
            "regulating_rod": 0,
            "pump_primary": 0,
            "pump_secondary": 0,
            "pump_tertiary": 0,
            "thermal_kw": 0.0,
            "turbine_speed": 0.0,
            "emergency": False
        }
    
    def read_simulation_state(self) -> Dict:
        """
        Read state from backend simulation
        In test mode: return mock state
        In production: read from JSON file
        """
        if self.test_mode:
            # Update mock state based on current mode
            if self.mock_mode == "idle":
                # Return empty state for IDLE mode
                return {}
            elif self.mock_mode == "auto":
                self.mock_state["mode"] = "auto"
                self.mock_state["auto_running"] = True
                self.mock_state["auto_phase"] = "Running"
            elif self.mock_mode == "manual":
                self.mock_state["mode"] = "manual"
                self.mock_state["auto_running"] = False
            
            return self.mock_state
        
        # Production mode: read from file
        try:
            if not self.state_file.exists():
                return {}
            
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Check if state has changed significantly (user interaction)
            if not self.user_has_interacted:
                current_pressure = state.get("pressure", 0)
                current_rods = (state.get("safety_rod", 0) + 
                              state.get("shim_rod", 0) + 
                              state.get("regulating_rod", 0))
                current_pumps = (state.get("pump_primary", 0) + 
                               state.get("pump_secondary", 0) + 
                               state.get("pump_tertiary", 0))
                
                # Detect user interaction (significant state change)
                if (abs(current_pressure - self.last_pressure) > 5 or
                    abs(current_rods - self.last_rods_sum) > 10 or
                    abs(current_pumps - self.last_pumps_sum) > 0):
                    
                    # Only consider as interaction if not during auto simulation
                    auto_running = state.get("auto_running", False)
                    if not auto_running:
                        self.user_has_interacted = True
                        print("👤 User interaction detected - enabling MANUAL mode")
                
                # Update last known values
                self.last_pressure = current_pressure
                self.last_rods_sum = current_rods
                self.last_pumps_sum = current_pumps
            
            return state
        except Exception as e:
            print(f"⚠️  Failed to read state: {e}")
            return {}
    
    def handle_test_mode_keys(self, event):
        """Handle keyboard input for test mode"""
        if not self.test_mode:
            return
        
        if event.type == pygame.KEYDOWN:
            # Mode switches - Updated keys: I, M, A
            if event.key == pygame.K_i:
                print("🔄 Test: Switching to IDLE mode")
                self.mock_mode = "idle"
                self.current_step = 0  # Reset manual step
            
            elif event.key == pygame.K_m:
                print("🔄 Test: Switching to MANUAL mode")
                self.mock_mode = "manual"
                self.current_step = 0  # Reset to step 1
            
            elif event.key == pygame.K_a:
                print("🔄 Test: Switching to AUTO mode")
                self.mock_mode = "auto"
            
            # Adjust mock values (for manual mode testing)
            elif event.key == pygame.K_UP:
                if self.mock_mode == "manual":
                    self.mock_state["pressure"] = min(155, self.mock_state["pressure"] + 10)
                    print(f"📈 Pressure: {self.mock_state['pressure']}")
            
            elif event.key == pygame.K_DOWN:
                if self.mock_mode == "manual":
                    self.mock_state["pressure"] = max(0, self.mock_state["pressure"] - 10)
                    print(f"📉 Pressure: {self.mock_state['pressure']}")
            
            elif event.key == pygame.K_r:
                # Toggle rods
                self.mock_state["safety_rod"] = 100 if self.mock_state["safety_rod"] == 0 else 0
                self.mock_state["shim_rod"] = 50 if self.mock_state["shim_rod"] == 0 else 0
                self.mock_state["regulating_rod"] = 50 if self.mock_state["regulating_rod"] == 0 else 0
                print(f"🔄 Rods toggled: Safety={self.mock_state['safety_rod']}, Shim={self.mock_state['shim_rod']}")
            
            elif event.key == pygame.K_p:
                # Toggle pumps
                val = 2 if self.mock_state["pump_primary"] == 0 else 0
                self.mock_state["pump_primary"] = val
                self.mock_state["pump_secondary"] = val
                self.mock_state["pump_tertiary"] = val
                print(f"🔄 Pumps toggled: {val}")
    
    def play_video(self, video_path: str, loop: bool = False):
        """
        Play video using mpv (Wayland compatible)
        
        Args:
            video_path: Path to video file
            loop: Loop video infinitely
        """
        # Stop any current video
        if self.video_process:
            self.stop_video()
        
        # Check if video file exists
        if not Path(video_path).exists():
            print(f"❌ Video not found: {video_path}")
            if self.test_mode:
                print("   💡 In test mode, this is expected")
                print("   💡 Create video file or use placeholder")
            return
        
        # Build mpv command for Wayland
        cmd = [
            'mpv',
            '--fs',                      # Fullscreen
            '--no-osd-bar',             # No on-screen display
            '--no-input-default-bindings',  # Disable keyboard
            '--really-quiet',           # Minimal output
            '--vo=gpu',                 # Video output: GPU (Wayland compatible)
            '--hwdec=auto',             # Hardware decode (4K support)
            '--gpu-context=wayland',    # Use Wayland context
            video_path
        ]
        
        if loop:
            cmd.insert(1, '--loop=inf')
        
        try:
            # Set Wayland environment for mpv
            env = {
                'DISPLAY': ':0',
                'WAYLAND_DISPLAY': 'wayland-0',
                'XDG_RUNTIME_DIR': '/run/user/1000'
            }
            
            self.video_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_video = video_path
            print(f"▶️  Playing: {Path(video_path).name}")
            print(f"   Using Wayland GPU context with hardware decode")
        except FileNotFoundError:
            print("❌ mpv not installed!")
            print("   Install: sudo apt install mpv")
            if self.test_mode:
                print("   💡 Test mode: Simulating video playback")
        except Exception as e:
            print(f"❌ Failed to play video: {e}")
    
    def stop_video(self):
        """Stop current video"""
        if self.video_process:
            self.video_process.terminate()
            try:
                self.video_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.video_process.kill()
            self.video_process = None
            self.current_video = None
            print("⏹️  Video stopped")
    
    def draw_idle_screen(self):
        """Display idle/intro screen - Professional branding with Nuclear Blue theme (4K scaled)"""
        self.screen.fill(self.COLOR_BG)
        
        # Update fade animation for instruction text
        self.idle_fade_alpha += self.idle_fade_direction * self.idle_fade_speed
        if self.idle_fade_alpha >= 255:
            self.idle_fade_alpha = 255
            self.idle_fade_direction = -1
        elif self.idle_fade_alpha <= 180:
            self.idle_fade_alpha = 180
            self.idle_fade_direction = 1
        
        # === TOP SECTION: LOGOS === (scaled)
        logo_y = int(50 * self.scale)
        logo_margin = int(80 * self.scale)
        
        # BRIN Logo (Top Left)
        if self.logo_brin:
            logo_x = logo_margin
            self.screen.blit(self.logo_brin, (logo_x, logo_y))
        
        # Poltek Logo (Top Right)
        if self.logo_poltek:
            logo_x = self.width - self.logo_size_large[0] - logo_margin
            self.screen.blit(self.logo_poltek, (logo_x, logo_y))
        
        # === CENTER SECTION: MAIN TITLE WITH DECORATIVE LINES === (scaled)
        center_y_start = self.height // 2 - int(120 * self.scale)
        
        # Decorative line (top) - scaled
        line_width = int(400 * self.scale)
        line_x = (self.width - line_width) // 2
        line_thickness = max(int(3 * self.scale), 2)
        pygame.draw.line(self.screen, self.COLOR_BORDER, 
                        (line_x, center_y_start - int(20 * self.scale)), 
                        (line_x + line_width, center_y_start - int(20 * self.scale)), 
                        line_thickness)
        
        # Main Title Line 1 (Bright Cyan with shadow for depth)
        title1_text = "ALAT PERAGA PLTN TIPE PWR"
        # Shadow
        title1_shadow = self.font_display.render(title1_text, True, (0, 0, 0))
        shadow_offset = int(2 * self.scale)
        title1_shadow_rect = title1_shadow.get_rect(center=(self.width//2 + shadow_offset, center_y_start + int(22 * self.scale)))
        self.screen.blit(title1_shadow, title1_shadow_rect)
        # Main text
        title1 = self.font_display.render(title1_text, True, self.COLOR_PRIMARY_BRIGHT)
        title1_rect = title1.get_rect(center=(self.width//2, center_y_start + int(20 * self.scale)))
        self.screen.blit(title1, title1_rect)
        
        # Main Title Line 2 (Pure White)
        title2_text = "BERBASIS MIKROKONTROLER"
        # Shadow
        title2_shadow = self.font_subtitle.render(title2_text, True, (0, 0, 0))
        title2_shadow_rect = title2_shadow.get_rect(center=(self.width//2 + shadow_offset, center_y_start + int(82 * self.scale)))
        self.screen.blit(title2_shadow, title2_shadow_rect)
        # Main text
        title2 = self.font_subtitle.render(title2_text, True, self.COLOR_TEXT)
        title2_rect = title2.get_rect(center=(self.width//2, center_y_start + int(80 * self.scale)))
        self.screen.blit(title2, title2_rect)
        
        # Decorative line (bottom) - scaled
        pygame.draw.line(self.screen, self.COLOR_BORDER, 
                        (line_x, center_y_start + int(130 * self.scale)), 
                        (line_x + line_width, center_y_start + int(130 * self.scale)), 
                        line_thickness)
        
        # Institution Name (Light Blue)
        institution = self.font_heading.render("Politeknik Teknologi Nuklir Indonesia", 
                                               True, self.COLOR_TEXT_TERTIARY)
        inst_rect = institution.get_rect(center=(self.width//2, center_y_start + int(170 * self.scale)))
        self.screen.blit(institution, inst_rect)
        
        # === STATUS BADGE === (scaled)
        status_y = center_y_start + int(230 * self.scale)
        
        # Status badge background - scaled
        badge_width = int(280 * self.scale)
        badge_height = int(40 * self.scale)
        badge_x = (self.width - badge_width) // 2
        badge_radius = int(20 * self.scale)
        badge_rect = pygame.Rect(badge_x, status_y - int(10 * self.scale), badge_width, badge_height)
        pygame.draw.rect(self.screen, self.COLOR_BG_TERTIARY, badge_rect, border_radius=badge_radius)
        pygame.draw.rect(self.screen, self.COLOR_GOLD, badge_rect, max(int(2 * self.scale), 1), border_radius=badge_radius)
        
        # Status text with icon
        status_text = "⚡ SIMULATION READY ⚡"
        status_surface = self.font_body.render(status_text, True, self.COLOR_GOLD)
        status_rect = status_surface.get_rect(center=(self.width//2, status_y + int(10 * self.scale)))
        self.screen.blit(status_surface, status_rect)
        
        # === BOTTOM SECTION: INSTRUCTIONS === (scaled)
        instruction_y = self.height - int(120 * self.scale)
        
        # Instruction text with fade animation (Bright Cyan)
        inst_text = "Tekan tombol untuk memulai simulasi"
        inst_surface = self.font_body.render(inst_text, True, self.COLOR_ENERGY)
        
        # Apply fade by adjusting alpha
        inst_surface.set_alpha(int(self.idle_fade_alpha))
        inst_rect = inst_surface.get_rect(center=(self.width//2, instruction_y))
        self.screen.blit(inst_surface, inst_rect)
        
        # === TEST MODE INDICATOR ===
        if self.test_mode:
            test_y = self.height - int(50 * self.scale)
            test_text = self.font_small.render("TEST MODE - Press I/M/A to change mode | ESC to exit", 
                                               True, self.COLOR_ERROR)
            test_rect = test_text.get_rect(center=(self.width//2, test_y))
            self.screen.blit(test_text, test_rect)
        
        pygame.display.flip()
    
    def draw_manual_guide(self, state: Dict):
        """Display interactive step-by-step guide with Nuclear Blue theme (4K scaled)"""
        self.screen.fill(self.COLOR_BG)
        
        # === HEADER BAR === (Updated: Full title centered) - scaled
        header_height = int(80 * self.scale)
        left_margin = int(30 * self.scale)
        right_margin = int(30 * self.scale)
        
        # Draw header background (Medium Navy)
        pygame.draw.rect(self.screen, self.COLOR_BG_SECONDARY, (0, 0, self.width, header_height))
        line_thickness = max(int(3 * self.scale), 2)
        pygame.draw.line(self.screen, self.COLOR_BORDER, (0, header_height), (self.width, header_height), line_thickness)
        
        # Logo BRIN (left)
        if self.logo_brin:
            logo_small_brin = pygame.transform.smoothscale(self.logo_brin, self.logo_size_small)
            logo_y = (header_height - self.logo_size_small[1]) // 2
            self.screen.blit(logo_small_brin, (left_margin, logo_y))
        
        # Title text (center) - Full title, Pure White
        header_title = self.font_heading.render("SIMULATOR PLTN TIPE PWR BERBASIS MIKROKONTROLER", 
                                                 True, self.COLOR_TEXT)
        header_title_rect = header_title.get_rect(center=(self.width//2, header_height//2))
        self.screen.blit(header_title, header_title_rect)
        
        # Logo Poltek (right)
        if self.logo_poltek:
            logo_small_poltek = pygame.transform.smoothscale(self.logo_poltek, self.logo_size_small)
            logo_y = (header_height - self.logo_size_small[1]) // 2
            logo_x = self.width - self.logo_size_small[0] - right_margin
            self.screen.blit(logo_small_poltek, (logo_x, logo_y))
        
        # === MAIN CONTENT AREA === (scaled)
        content_y_start = header_height + int(30 * self.scale)
        
        # Current step instruction
        step_text = self.get_current_step_instruction(state)
        
        # Draw step title (Bright Cyan)
        title = self.font_title.render(f"STEP {self.current_step + 1}", True, self.COLOR_PRIMARY_BRIGHT)
        title_rect = title.get_rect(center=(self.width//2, content_y_start + int(20 * self.scale)))
        self.screen.blit(title, title_rect)
        
        # Draw instruction (Pure White) - scaled line spacing
        y_offset = content_y_start + int(70 * self.scale)
        line_spacing = int(50 * self.scale)
        for line in step_text:
            text = self.font_body.render(line, True, self.COLOR_TEXT)
            text_rect = text.get_rect(center=(self.width//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += line_spacing
        
        # Draw progress bar (moved up significantly) - scaled
        self.draw_progress_bar(state)
        
        # Test mode hint - scaled
        if self.test_mode:
            hint1 = self.font_small.render("TEST: I=IDLE | M=MANUAL | A=AUTO", True, self.COLOR_ERROR)
            hint1_rect = hint1.get_rect(center=(self.width//2, self.height - int(80 * self.scale)))
            self.screen.blit(hint1, hint1_rect)
            
            hint2 = self.font_small.render("UP/DOWN=Pressure | R=Rods | P=Pumps", True, self.COLOR_WARNING)
            hint2_rect = hint2.get_rect(center=(self.width//2, self.height - int(50 * self.scale)))
            self.screen.blit(hint2, hint2_rect)
        
        pygame.display.flip()
    
    def get_current_step_instruction(self, state: Dict) -> list:
        """Get instruction text for current step"""
        steps = [
            {
                "text": ["Raise Pressure to 45 bar", "Press PRESSURE UP button"],
                "check": lambda s: s.get("pressure", 0) >= 45
            },
            {
                "text": ["Start Tertiary Pump", "Press PUMP TERTIARY ON"],
                "check": lambda s: s.get("pump_tertiary", 0) >= 1
            },
            {
                "text": ["Start Secondary Pump", "Press PUMP SECONDARY ON"],
                "check": lambda s: s.get("pump_secondary", 0) >= 1
            },
            {
                "text": ["Start Primary Pump", "Press PUMP PRIMARY ON"],
                "check": lambda s: s.get("pump_primary", 0) >= 1
            },
            {
                "text": ["Raise Pressure to 140 bar", "Continue pressing PRESSURE UP"],
                "check": lambda s: s.get("pressure", 0) >= 140
            },
            {
                "text": ["Withdraw Safety Rod to 100%", "Press SAFETY ROD UP"],
                "check": lambda s: s.get("safety_rod", 0) >= 100
            },
            {
                "text": ["Withdraw Shim Rod to 50%", "Press SHIM ROD UP"],
                "check": lambda s: s.get("shim_rod", 0) >= 50
            },
            {
                "text": ["Withdraw Regulating Rod to 50%", "Press REGULATING ROD UP"],
                "check": lambda s: s.get("regulating_rod", 0) >= 50
            },
            {
                "text": ["Normal Operation Achieved!", "System is generating power"],
                "check": lambda s: True
            }
        ]
        
        # Check if current step completed
        if self.current_step < len(steps):
            step = steps[self.current_step]
            if step["check"](state):
                self.current_step += 1
                if self.test_mode:
                    print(f"✅ Step {self.current_step} completed!")
        
        if self.current_step < len(steps):
            return steps[self.current_step]["text"]
        else:
            return ["Simulation Complete!", "Press RESET to restart"]
    
    def draw_progress_bar(self, state: Dict):
        """Draw parameter progress bars with Nuclear Blue theme (4K scaled)"""
        y_start = self.height - int(300 * self.scale)  # Moved up significantly - scaled
        bar_width = int(300 * self.scale)
        bar_height = int(30 * self.scale)
        bar_spacing = int(45 * self.scale)  # Reduced spacing - scaled
        
        params = [
            ("Pressure", state.get("pressure", 0), 155, "bar"),
            ("Safety Rod", state.get("safety_rod", 0), 100, "%"),
            ("Shim Rod", state.get("shim_rod", 0), 100, "%"),
            ("Reg Rod", state.get("regulating_rod", 0), 100, "%")
        ]
        
        for i, (label, value, max_val, unit) in enumerate(params):
            y = y_start + i * bar_spacing
            x_label = int(200 * self.scale)
            x_bar = int(380 * self.scale)
            
            # Label (Light Blue)
            text = self.font_small.render(f"{label}:", True, self.COLOR_TEXT_TERTIARY)
            self.screen.blit(text, (x_label, y))
            
            # Value text (Pure White)
            value_text = self.font_small.render(f"{value:.0f}{unit}", True, self.COLOR_TEXT)
            self.screen.blit(value_text, (x_bar + bar_width + int(15 * self.scale), y))
            
            # Bar background (Panel BG)
            border_radius = int(5 * self.scale)
            bg_rect = pygame.Rect(x_bar, y + int(5 * self.scale), bar_width, bar_height)
            pygame.draw.rect(self.screen, self.COLOR_BG_PANEL, bg_rect, border_radius=border_radius)
            
            # Bar fill (Color based on value)
            fill_width = int((value / max_val) * bar_width) if max_val > 0 else 0
            if fill_width > 0:
                fill_rect = pygame.Rect(x_bar, y + int(5 * self.scale), fill_width, bar_height)
                # Choose color based on value
                if value > max_val * 0.7:
                    color = self.COLOR_SUCCESS
                elif value > max_val * 0.3:
                    color = self.COLOR_PRIMARY
                else:
                    color = self.COLOR_INFO
                pygame.draw.rect(self.screen, color, fill_rect, border_radius=border_radius)
            
            # Bar border (Border color)
            border_thickness = max(int(2 * self.scale), 1)
            pygame.draw.rect(self.screen, self.COLOR_BORDER, bg_rect, border_thickness, border_radius=border_radius)
    
    def draw_video_playing_overlay(self):
        """Draw overlay when video is playing (for debug) with Nuclear Blue theme"""
        if self.test_mode and self.display_mode == DisplayMode.AUTO_VIDEO:
            self.screen.fill(self.COLOR_BG)
            
            # Title
            text = self.font_title.render("VIDEO PLAYING", True, self.COLOR_PRIMARY_BRIGHT)
            text_rect = text.get_rect(center=(self.width//2, self.height//2 - 30))
            self.screen.blit(text, text_rect)
            
            # Subtitle
            hint = self.font_body.render("(Simulated - no actual video)", True, self.COLOR_TEXT_TERTIARY)
            hint_rect = hint.get_rect(center=(self.width//2, self.height//2 + 20))
            self.screen.blit(hint, hint_rect)
            
            # Instructions
            inst = self.font_small.render("Press I to return to IDLE", True, self.COLOR_INFO)
            inst_rect = inst.get_rect(center=(self.width//2, self.height//2 + 60))
            self.screen.blit(inst, inst_rect)
            
            pygame.display.flip()
    
    def update(self):
        """Main update loop with improved mode transition logic"""
        state = self.read_simulation_state()
        
        # DEBUG: Print state info (less frequent)
        if state and hasattr(self, '_debug_counter'):
            self._debug_counter = (self._debug_counter + 1) % 30  # Print every 30 frames (~1 sec)
            if self._debug_counter == 0:
                mode = state.get("mode", "unknown")
                auto_running = state.get("auto_running", False)
                print(f"📊 mode={mode}, auto={auto_running}, display={self.display_mode.value}, user_interacted={self.user_has_interacted}")
        elif not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        
        # In test mode, check mock_mode first
        if self.test_mode:
            if self.mock_mode == "idle":
                # Force IDLE mode
                if self.display_mode != DisplayMode.IDLE:
                    self.stop_video()
                    self.display_mode = DisplayMode.IDLE
                self.draw_idle_screen()
                return
            elif self.mock_mode == "auto":
                # Force AUTO mode
                if self.display_mode != DisplayMode.AUTO_VIDEO:
                    print("🎬 Switching to AUTO VIDEO mode")
                    video_path = str(Path(__file__).parent / "assets" / "penjelasan.mp4")
                    self.play_video(video_path, loop=True)
                    self.display_mode = DisplayMode.AUTO_VIDEO
                
                # Show overlay in test mode
                self.draw_video_playing_overlay()
                return
            elif self.mock_mode == "manual":
                # Force MANUAL mode
                if self.display_mode != DisplayMode.MANUAL_GUIDE:
                    print("📋 Switching to MANUAL GUIDE mode")
                    self.stop_video()
                    self.display_mode = DisplayMode.MANUAL_GUIDE
                    self.current_step = 0
                
                self.draw_manual_guide(state)
                return
        
        # Production mode logic with improved transitions
        if not state:
            # No state yet - show idle
            if self._debug_counter == 0:
                print("⚠️  No state file - showing IDLE")
            if self.display_mode != DisplayMode.IDLE:
                self.stop_video()
                self.display_mode = DisplayMode.IDLE
                self.user_has_interacted = False  # Reset on no state
            self.draw_idle_screen()
            return
        
        mode = state.get("mode", "manual")
        auto_running = state.get("auto_running", False)
        emergency = state.get("emergency", False)
        
        # Check if auto simulation just completed
        if not auto_running and self.display_mode == DisplayMode.AUTO_VIDEO:
            # Auto simulation just finished
            print("🏁 Auto simulation completed")
            self.stop_video()
            self.auto_complete_time = time.time()  # Mark completion time
            self.display_mode = DisplayMode.IDLE
            self.user_has_interacted = False  # Reset - wait for new input
            print("   Waiting 60 seconds before allowing MANUAL...")
        
        # MODE 1: EMERGENCY - Always return to IDLE
        if emergency:
            if self.display_mode != DisplayMode.IDLE:
                print("🚨 Emergency detected - returning to IDLE")
                self.stop_video()
                self.display_mode = DisplayMode.IDLE
                self.user_has_interacted = False
                self.auto_complete_time = None
            self.draw_idle_screen()
            return
        
        # MODE 2: AUTO SIMULATION - Play video
        if mode == "auto" and auto_running:
            if self.display_mode != DisplayMode.AUTO_VIDEO:
                print(f"🎬 Switching to AUTO VIDEO mode")
                # Use video from assets folder (production ready)
                video_path = str(Path(__file__).parent / "assets" / "penjelasan.mp4")
                self.play_video(video_path, loop=True)
                self.display_mode = DisplayMode.AUTO_VIDEO
                self.auto_complete_time = None  # Reset completion timer
                self.user_has_interacted = False  # Reset interaction flag
            
            # Video is playing via mpv - don't draw anything
            # (mpv handles fullscreen itself)
            return
        
        # MODE 3: After AUTO complete - Wait 60 seconds in IDLE
        if self.auto_complete_time is not None:
            elapsed = time.time() - self.auto_complete_time
            if elapsed < 60:
                # Still in waiting period
                if self.display_mode != DisplayMode.IDLE:
                    self.display_mode = DisplayMode.IDLE
                self.draw_idle_screen()
                return
            else:
                # 60 seconds passed, allow transition to MANUAL
                print("⏰ 60 seconds elapsed after AUTO - allowing MANUAL mode")
                self.auto_complete_time = None
                # Don't auto-enable MANUAL - wait for user interaction
        
        # MODE 4: MANUAL - Only if user has interacted
        if mode == "manual" and self.user_has_interacted:
            if self.display_mode != DisplayMode.MANUAL_GUIDE:
                print(f"📋 Switching to MANUAL GUIDE mode (user pressed button)")
                self.stop_video()
                self.display_mode = DisplayMode.MANUAL_GUIDE
                self.current_step = 0
            
            self.draw_manual_guide(state)
        
        # MODE 5: IDLE - Default (no user interaction yet)
        else:
            if self.display_mode != DisplayMode.IDLE:
                self.stop_video()
                self.display_mode = DisplayMode.IDLE
            self.draw_idle_screen()
    
    def run(self):
        """Main application loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("🚀 Video Display App running...")
        print("   Press ESC to exit")
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                # Test mode keyboard handling
                self.handle_test_mode_keys(event)
            
            # Update display
            self.update()
            
            # 30 FPS sufficient for UI updates
            clock.tick(30)
        
        # Cleanup
        self.stop_video()
        pygame.quit()
        print("👋 Video Display App stopped")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description='PLTN Video Display Application')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode (no simulation required)')
    parser.add_argument('--windowed', action='store_true',
                       help='Run in windowed mode (not fullscreen)')
    
    args = parser.parse_args()
    
    # Run application
    app = VideoDisplayApp(
        test_mode=args.test,
        fullscreen=not args.windowed
    )
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
