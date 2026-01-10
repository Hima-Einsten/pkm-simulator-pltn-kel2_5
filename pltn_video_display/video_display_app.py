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
        
        # Fonts - Enhanced for professional display
        self.font_title = pygame.font.Font(None, 60)      # Main title
        self.font_subtitle = pygame.font.Font(None, 48)   # Subtitle
        self.font_heading = pygame.font.Font(None, 40)    # Institution
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_instruction = pygame.font.Font(None, 32) # Instruction text
        
        # Colors - Enhanced palette
        self.COLOR_BG = (20, 20, 40)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_ACCENT = (0, 200, 255)           # Cyan for titles
        self.COLOR_YELLOW = (255, 215, 0)           # Gold for instructions
        self.COLOR_GRAY = (200, 200, 200)           # Light gray
        self.COLOR_SUCCESS = (0, 255, 100)
        self.COLOR_WARNING = (255, 200, 0)
        self.COLOR_ERROR = (255, 50, 50)
        
        # Load logos
        self.logo_brin = None
        self.logo_poltek = None
        self.logo_size_large = (120, 120)  # IDLE mode
        self.logo_size_small = (60, 60)    # MANUAL mode - Updated from 40x40
        self.load_logos()
        
        # IDLE screen animation
        self.idle_fade_alpha = 255
        self.idle_fade_direction = -1
        self.idle_fade_speed = 2
        
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
                return json.load(f)
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
        """Play video using mpv (lightweight & HW accelerated)"""
        if self.video_process:
            self.stop_video()
        
        # Check if video file exists
        if not Path(video_path).exists():
            print(f"❌ Video not found: {video_path}")
            if self.test_mode:
                print("   💡 In test mode, this is expected")
                print("   💡 Create video file or use placeholder")
            return
        
        # Build mpv command
        cmd = [
            'mpv',
            '--fs',                  # Fullscreen
            '--no-osd-bar',         # No on-screen display
            '--no-input-default-bindings',  # Disable keyboard
            '--really-quiet',       # Minimal output
            video_path
        ]
        
        if loop:
            cmd.insert(1, '--loop=inf')
        
        try:
            self.video_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_video = video_path
            print(f"▶️  Playing: {Path(video_path).name}")
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
        """Display idle/intro screen - Professional branding"""
        self.screen.fill(self.COLOR_BG)
        
        # Update fade animation
        self.idle_fade_alpha += self.idle_fade_direction * self.idle_fade_speed
        if self.idle_fade_alpha >= 255:
            self.idle_fade_alpha = 255
            self.idle_fade_direction = -1
        elif self.idle_fade_alpha <= 180:
            self.idle_fade_alpha = 180
            self.idle_fade_direction = 1
        
        # === TOP SECTION: LOGOS ===
        logo_y = 40
        logo_margin = 60
        
        # BRIN Logo (Top Left)
        if self.logo_brin:
            logo_x = logo_margin
            self.screen.blit(self.logo_brin, (logo_x, logo_y))
        
        # Poltek Logo (Top Right)
        if self.logo_poltek:
            logo_x = self.width - self.logo_size_large[0] - logo_margin
            self.screen.blit(self.logo_poltek, (logo_x, logo_y))
        
        # === CENTER SECTION: MAIN TITLE ===
        center_y_start = self.height // 2 - 100
        
        # Main Title Line 1
        title1 = self.font_title.render("ALAT PERAGA PLTN TIPE PWR", True, self.COLOR_ACCENT)
        title1_rect = title1.get_rect(center=(self.width//2, center_y_start))
        self.screen.blit(title1, title1_rect)
        
        # Main Title Line 2 (Subtitle)
        title2 = self.font_subtitle.render("BERBASIS MIKROKONTROLER", True, self.COLOR_TEXT)
        title2_rect = title2.get_rect(center=(self.width//2, center_y_start + 70))
        self.screen.blit(title2, title2_rect)
        
        # Institution Name
        institution = self.font_heading.render("Politeknik Teknologi Nuklir Indonesia", True, self.COLOR_GRAY)
        inst_rect = institution.get_rect(center=(self.width//2, center_y_start + 140))
        self.screen.blit(institution, inst_rect)
        
        # === BOTTOM SECTION: INSTRUCTIONS ===
        instruction_y = self.height - 120
        
        # Instruction text with fade animation
        instruction_color = (self.COLOR_YELLOW[0], 
                           self.COLOR_YELLOW[1], 
                           self.COLOR_YELLOW[2], 
                           int(self.idle_fade_alpha))
        
        # Create surface with alpha for fade effect
        inst_text = "Tekan START AUTO SIMULATION atau gunakan MANUAL MODE"
        inst_surface = self.font_instruction.render(inst_text, True, self.COLOR_YELLOW)
        
        # Apply fade by adjusting alpha
        inst_surface.set_alpha(int(self.idle_fade_alpha))
        inst_rect = inst_surface.get_rect(center=(self.width//2, instruction_y))
        self.screen.blit(inst_surface, inst_rect)
        
        # === TEST MODE INDICATOR ===
        if self.test_mode:
            test_y = self.height - 50
            test_text = self.font_small.render("TEST MODE - Press I/M/A to change mode | ESC to exit", True, self.COLOR_ERROR)
            test_rect = test_text.get_rect(center=(self.width//2, test_y))
            self.screen.blit(test_text, test_rect)
        
        pygame.display.flip()
    
    def draw_manual_guide(self, state: Dict):
        """Display interactive step-by-step guide"""
        self.screen.fill(self.COLOR_BG)
        
        # === HEADER BAR === (Updated: larger size)
        header_height = 80  # Increased from 60
        header_bg_color = (26, 26, 46)
        left_margin = 30    # Increased from 15
        right_margin = 30   # Increased from 15
        
        # Draw header background
        pygame.draw.rect(self.screen, header_bg_color, (0, 0, self.width, header_height))
        pygame.draw.line(self.screen, self.COLOR_ACCENT, (0, header_height), (self.width, header_height), 2)
        
        # Logo BRIN (left) - larger version (60x60)
        if self.logo_brin:
            logo_small_brin = pygame.transform.smoothscale(self.logo_brin, self.logo_size_small)
            logo_y = (header_height - self.logo_size_small[1]) // 2
            self.screen.blit(logo_small_brin, (left_margin, logo_y))
        
        # Title text (center)
        header_title = self.font_heading.render("PLTN Simulator - Manual Mode", True, self.COLOR_TEXT)
        header_title_rect = header_title.get_rect(center=(self.width//2, header_height//2))
        self.screen.blit(header_title, header_title_rect)
        
        # Logo Poltek (right) - larger version (60x60)
        if self.logo_poltek:
            logo_small_poltek = pygame.transform.smoothscale(self.logo_poltek, self.logo_size_small)
            logo_y = (header_height - self.logo_size_small[1]) // 2
            logo_x = self.width - self.logo_size_small[0] - right_margin
            self.screen.blit(logo_small_poltek, (logo_x, logo_y))
        
        # === MAIN CONTENT AREA ===
        content_y_start = header_height + 20
        
        # Current step instruction
        step_text = self.get_current_step_instruction(state)
        
        # Draw step title
        title = self.font_large.render(f"STEP {self.current_step + 1}", True, self.COLOR_ACCENT)
        title_rect = title.get_rect(center=(self.width//2, content_y_start + 30))
        self.screen.blit(title, title_rect)
        
        # Draw instruction
        y_offset = content_y_start + 80
        for line in step_text:
            text = self.font_medium.render(line, True, self.COLOR_TEXT)
            text_rect = text.get_rect(center=(self.width//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 60
        
        # Draw progress bar
        self.draw_progress_bar(state)
        
        # Test mode hint
        if self.test_mode:
            hint1 = self.font_small.render("TEST: I=IDLE | M=MANUAL | A=AUTO", True, self.COLOR_ERROR)
            hint1_rect = hint1.get_rect(center=(self.width//2, self.height - 80))
            self.screen.blit(hint1, hint1_rect)
            
            hint2 = self.font_small.render("UP/DOWN=Pressure | R=Rods | P=Pumps", True, self.COLOR_WARNING)
            hint2_rect = hint2.get_rect(center=(self.width//2, self.height - 40))
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
        """Draw parameter progress bars"""
        y_start = self.height - 300
        bar_width = self.width - 400
        bar_height = 40
        
        params = [
            ("Pressure", state.get("pressure", 0), 155),
            ("Safety Rod", state.get("safety_rod", 0), 100),
            ("Shim Rod", state.get("shim_rod", 0), 100),
            ("Reg Rod", state.get("regulating_rod", 0), 100)
        ]
        
        for i, (label, value, max_val) in enumerate(params):
            y = y_start + i * 60
            
            # Label
            text = self.font_small.render(f"{label}: {value:.1f}", True, self.COLOR_TEXT)
            self.screen.blit(text, (200, y))
            
            # Bar background
            pygame.draw.rect(self.screen, (50, 50, 50), 
                           (200, y + 30, bar_width, bar_height))
            
            # Bar fill
            fill_width = int((value / max_val) * bar_width)
            color = self.COLOR_SUCCESS if value > 0 else (100, 100, 100)
            pygame.draw.rect(self.screen, color, 
                           (200, y + 30, fill_width, bar_height))
    
    def draw_video_playing_overlay(self):
        """Draw overlay when video is playing (for debug)"""
        if self.test_mode and self.display_mode == DisplayMode.AUTO_VIDEO:
            self.screen.fill((0, 0, 0))
            text = self.font_large.render("VIDEO PLAYING", True, self.COLOR_ACCENT)
            text_rect = text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(text, text_rect)
            
            hint = self.font_small.render("(Simulated - no actual video)", True, self.COLOR_WARNING)
            hint_rect = hint.get_rect(center=(self.width//2, self.height//2 + 80))
            self.screen.blit(hint, hint_rect)
            
            pygame.display.flip()
    
    def update(self):
        """Main update loop"""
        state = self.read_simulation_state()
        
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
        
        # Production mode logic
        if not state:
            # No state yet - show idle
            if self.display_mode != DisplayMode.IDLE:
                self.stop_video()
                self.display_mode = DisplayMode.IDLE
            self.draw_idle_screen()
            return
        
        mode = state.get("mode", "manual")
        auto_running = state.get("auto_running", False)
        
        # MODE 1: AUTO SIMULATION - Play video
        if mode == "auto" and auto_running:
            if self.display_mode != DisplayMode.AUTO_VIDEO:
                print("🎬 Switching to AUTO VIDEO mode")
                # Update: Use video from assets folder (development)
                video_path = str(Path(__file__).parent / "assets" / "penjelasan.mp4")
                self.play_video(video_path, loop=True)
                self.display_mode = DisplayMode.AUTO_VIDEO
            
            # In test mode, show overlay instead
            if self.test_mode:
                self.draw_video_playing_overlay()
        
        # MODE 2: MANUAL - Show guide
        elif mode == "manual" and not auto_running:
            if self.display_mode != DisplayMode.MANUAL_GUIDE:
                print("📋 Switching to MANUAL GUIDE mode")
                self.stop_video()
                self.display_mode = DisplayMode.MANUAL_GUIDE
                self.current_step = 0
            
            self.draw_manual_guide(state)
        
        # IDLE
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
