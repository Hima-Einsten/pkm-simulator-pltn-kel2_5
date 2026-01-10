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
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        
        # Colors
        self.COLOR_BG = (20, 20, 40)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_ACCENT = (0, 200, 255)
        self.COLOR_SUCCESS = (0, 255, 100)
        self.COLOR_WARNING = (255, 200, 0)
        self.COLOR_ERROR = (255, 50, 50)
        
        # Manual guide - step tracker
        self.current_step = 0
        self.steps_completed = []
        
        # Test mode variables
        if self.test_mode:
            print("🧪 TESTING MODE ACTIVE")
            print("   Using mock simulation data")
            print("   Press keys to simulate states:")
            print("   - 1: IDLE mode")
            print("   - 2: AUTO mode (play video)")
            print("   - 3: MANUAL mode (step guide)")
            print("   - UP/DOWN: Adjust mock values")
            print("   - R: Toggle rods")
            print("   - P: Toggle pumps")
            self.mock_state = self.create_mock_state()
            self.mock_mode = "idle"
        else:
            print("🚀 PRODUCTION MODE")
            print(f"   Reading state from: {self.state_file}")
        
        print(f"🎬 Video Display App initialized")
        print(f"   Screen: {self.width}x{self.height}")
        print(f"   Fullscreen: {fullscreen}")
    
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
            if self.mock_mode == "auto":
                self.mock_state["mode"] = "auto"
                self.mock_state["auto_running"] = True
                self.mock_state["auto_phase"] = "Running"
            elif self.mock_mode == "manual":
                self.mock_state["mode"] = "manual"
                self.mock_state["auto_running"] = False
            else:  # idle
                self.mock_state["mode"] = "manual"
                self.mock_state["auto_running"] = False
                self.mock_state["pressure"] = 0
            
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
            # Mode switches
            if event.key == pygame.K_1:
                print("🔄 Test: Switching to IDLE mode")
                self.mock_mode = "idle"
            
            elif event.key == pygame.K_2:
                print("🔄 Test: Switching to AUTO mode")
                self.mock_mode = "auto"
            
            elif event.key == pygame.K_3:
                print("🔄 Test: Switching to MANUAL mode")
                self.mock_mode = "manual"
            
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
        """Display idle/intro screen"""
        self.screen.fill(self.COLOR_BG)
        
        # Title
        title = self.font_large.render("PLTN SIMULATOR", True, self.COLOR_ACCENT)
        title_rect = title.get_rect(center=(self.width//2, self.height//3))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_medium.render("Pressurized Water Reactor", True, self.COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(center=(self.width//2, self.height//2))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        inst1 = self.font_small.render("Press START AUTO SIMULATION for guided demo", True, self.COLOR_SUCCESS)
        inst1_rect = inst1.get_rect(center=(self.width//2, self.height*2//3))
        self.screen.blit(inst1, inst1_rect)
        
        inst2 = self.font_small.render("Or use MANUAL MODE for hands-on training", True, self.COLOR_WARNING)
        inst2_rect = inst2.get_rect(center=(self.width//2, self.height*2//3 + 50))
        self.screen.blit(inst2, inst2_rect)
        
        # Test mode indicator
        if self.test_mode:
            test_text = self.font_small.render("TEST MODE - Press 1/2/3 to change mode", True, self.COLOR_ERROR)
            test_rect = test_text.get_rect(center=(self.width//2, self.height - 50))
            self.screen.blit(test_text, test_rect)
        
        pygame.display.flip()
    
    def draw_manual_guide(self, state: Dict):
        """Display interactive step-by-step guide"""
        self.screen.fill(self.COLOR_BG)
        
        # Current step instruction
        step_text = self.get_current_step_instruction(state)
        
        # Draw step title
        title = self.font_large.render(f"STEP {self.current_step + 1}", True, self.COLOR_ACCENT)
        title_rect = title.get_rect(center=(self.width//2, 100))
        self.screen.blit(title, title_rect)
        
        # Draw instruction
        y_offset = 200
        for line in step_text:
            text = self.font_medium.render(line, True, self.COLOR_TEXT)
            text_rect = text.get_rect(center=(self.width//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 60
        
        # Draw progress bar
        self.draw_progress_bar(state)
        
        # Test mode hint
        if self.test_mode:
            hint = self.font_small.render("TEST: Use UP/DOWN/R/P keys to simulate", True, self.COLOR_WARNING)
            hint_rect = hint.get_rect(center=(self.width//2, self.height - 50))
            self.screen.blit(hint, hint_rect)
        
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
        
        if not state and not self.test_mode:
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
            
            # 10 FPS sufficient for UI updates
            clock.tick(10)
        
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
