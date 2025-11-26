"""
Video Player Module for PLTN Simulator
Displays educational video content based on simulation state
Connected to monitor via HDMI
"""

import os
import time
import logging
import threading
from enum import Enum
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SimulationPhase(Enum):
    """Simulation phases for video selection"""
    IDLE = "idle"
    STARTUP_PRESSURE = "startup_pressure"
    STARTUP_PUMPS = "startup_pumps"
    CONTROL_RODS = "control_rods"
    POWER_GENERATION = "power_generation"
    NORMAL_OPERATION = "normal_operation"
    SHUTDOWN = "shutdown"
    EMERGENCY = "emergency"


class VideoPlayerBackend(Enum):
    """Supported video player backends"""
    VLC = "vlc"
    OMXPLAYER = "omxplayer"  # Hardware accelerated for Raspberry Pi
    OPENCV = "opencv"


class VideoPlayer:
    """
    Video player for educational content display
    Automatically selects video based on simulation state
    """
    
    def __init__(self, 
                 video_directory: str = "/home/pi/pltn_videos",
                 backend: VideoPlayerBackend = VideoPlayerBackend.OMXPLAYER,
                 fullscreen: bool = True,
                 loop_videos: bool = True):
        """
        Initialize video player
        
        Args:
            video_directory: Path to directory containing video files
            backend: Video player backend to use
            fullscreen: Display video in fullscreen mode
            loop_videos: Loop current video until phase changes
        """
        self.video_dir = Path(video_directory)
        self.backend = backend
        self.fullscreen = fullscreen
        self.loop_videos = loop_videos
        
        self.current_phase = SimulationPhase.IDLE
        self.current_video = None
        self.player_process = None
        self.is_playing = False
        self.stop_flag = threading.Event()
        
        # Video file mapping for each phase
        self.video_map: Dict[SimulationPhase, str] = {
            SimulationPhase.IDLE: "01_intro_pltn.mp4",
            SimulationPhase.STARTUP_PRESSURE: "02_pressurizer_system.mp4",
            SimulationPhase.STARTUP_PUMPS: "03_coolant_circulation.mp4",
            SimulationPhase.CONTROL_RODS: "04_control_rods_operation.mp4",
            SimulationPhase.POWER_GENERATION: "05_turbine_generator.mp4",
            SimulationPhase.NORMAL_OPERATION: "06_normal_operation.mp4",
            SimulationPhase.SHUTDOWN: "07_shutdown_procedure.mp4",
            SimulationPhase.EMERGENCY: "08_emergency_shutdown.mp4",
        }
        
        logger.info(f"Video Player initialized with backend: {backend.value}")
        self._check_video_files()
        self._check_backend_availability()
    
    def _check_video_files(self):
        """Check if video directory and files exist"""
        if not self.video_dir.exists():
            logger.warning(f"Video directory not found: {self.video_dir}")
            logger.info("Creating video directory structure...")
            self.video_dir.mkdir(parents=True, exist_ok=True)
        
        # Check which videos are available
        for phase, filename in self.video_map.items():
            video_path = self.video_dir / filename
            if video_path.exists():
                logger.info(f"✓ Found: {filename}")
            else:
                logger.warning(f"✗ Missing: {filename}")
    
    def _check_backend_availability(self):
        """Check if selected backend is available"""
        if self.backend == VideoPlayerBackend.OMXPLAYER:
            # Check if omxplayer is installed
            ret = os.system("which omxplayer > /dev/null 2>&1")
            if ret != 0:
                logger.warning("omxplayer not found. Install with: sudo apt install omxplayer")
                logger.info("Falling back to VLC backend")
                self.backend = VideoPlayerBackend.VLC
        
        elif self.backend == VideoPlayerBackend.VLC:
            # Check if VLC is installed
            ret = os.system("which vlc > /dev/null 2>&1")
            if ret != 0:
                logger.warning("VLC not found. Install with: sudo apt install vlc")
        
        elif self.backend == VideoPlayerBackend.OPENCV:
            try:
                import cv2
                logger.info(f"OpenCV version: {cv2.__version__}")
            except ImportError:
                logger.error("OpenCV not available. Install with: pip3 install opencv-python")
    
    def update_simulation_state(self, 
                                pressure: float,
                                pump_primary: int,
                                pump_secondary: int,
                                pump_tertiary: int,
                                rod_positions: list,
                                power_output: float,
                                emergency_active: bool = False):
        """
        Update current simulation phase based on system state
        
        Args:
            pressure: Current pressure (bar)
            pump_primary: Primary pump status (0=OFF, 1=STARTING, 2=ON)
            pump_secondary: Secondary pump status
            pump_tertiary: Tertiary pump status
            rod_positions: List of control rod positions [0-100]
            power_output: Generated power (MW)
            emergency_active: Emergency shutdown flag
        """
        # Determine current simulation phase
        new_phase = self._determine_phase(
            pressure, 
            pump_primary, 
            pump_secondary, 
            pump_tertiary,
            rod_positions,
            power_output,
            emergency_active
        )
        
        # Change video if phase changed
        if new_phase != self.current_phase:
            logger.info(f"Phase transition: {self.current_phase.value} → {new_phase.value}")
            self.current_phase = new_phase
            self.play_video_for_phase(new_phase)
    
    def _determine_phase(self, pressure, pump1, pump2, pump3, rods, power, emergency):
        """Determine current simulation phase from system state"""
        
        # Emergency takes highest priority
        if emergency:
            return SimulationPhase.EMERGENCY
        
        # Shutdown: all systems going down
        avg_rods = sum(rods) / len(rods) if rods else 0
        if avg_rods < 10 and power < 10 and pump1 == 0:
            return SimulationPhase.SHUTDOWN
        
        # Normal operation: everything running steadily
        if (pressure >= 140 and pump1 == 2 and pump2 == 2 and pump3 == 2 
            and avg_rods > 30 and power > 50):
            return SimulationPhase.NORMAL_OPERATION
        
        # Power generation: turbine active but not full power
        if power > 10 and avg_rods > 20:
            return SimulationPhase.POWER_GENERATION
        
        # Control rods: rods being withdrawn
        if avg_rods > 10 and pump1 == 2:
            return SimulationPhase.CONTROL_RODS
        
        # Pumps starting: pumps activating
        if pump1 >= 1 or pump2 >= 1 or pump3 >= 1:
            return SimulationPhase.STARTUP_PUMPS
        
        # Pressure buildup: pressure increasing
        if pressure > 10 and pump1 == 0:
            return SimulationPhase.STARTUP_PRESSURE
        
        # Default: idle state
        return SimulationPhase.IDLE
    
    def play_video_for_phase(self, phase: SimulationPhase):
        """
        Play video corresponding to simulation phase
        
        Args:
            phase: Current simulation phase
        """
        video_filename = self.video_map.get(phase)
        if not video_filename:
            logger.warning(f"No video mapped for phase: {phase.value}")
            return
        
        video_path = self.video_dir / video_filename
        if not video_path.exists():
            logger.warning(f"Video file not found: {video_path}")
            return
        
        self.play_video(str(video_path))
    
    def play_video(self, video_path: str):
        """
        Play specific video file
        
        Args:
            video_path: Full path to video file
        """
        # Stop current video if playing
        if self.is_playing:
            self.stop_video()
        
        self.current_video = video_path
        logger.info(f"Playing video: {os.path.basename(video_path)}")
        
        # Start video in background thread
        video_thread = threading.Thread(
            target=self._play_video_thread,
            args=(video_path,),
            daemon=True
        )
        video_thread.start()
    
    def _play_video_thread(self, video_path: str):
        """Thread function to play video"""
        self.is_playing = True
        
        while not self.stop_flag.is_set():
            if self.backend == VideoPlayerBackend.OMXPLAYER:
                self._play_with_omxplayer(video_path)
            elif self.backend == VideoPlayerBackend.VLC:
                self._play_with_vlc(video_path)
            elif self.backend == VideoPlayerBackend.OPENCV:
                self._play_with_opencv(video_path)
            
            if not self.loop_videos:
                break
        
        self.is_playing = False
    
    def _play_with_omxplayer(self, video_path: str):
        """Play video using omxplayer (hardware accelerated for RPi)"""
        import subprocess
        
        cmd = ["omxplayer"]
        
        if self.fullscreen:
            cmd.append("--no-osd")
        
        if self.loop_videos:
            cmd.append("--loop")
        
        # Audio to HDMI
        cmd.extend(["--adev", "hdmi"])
        
        cmd.append(video_path)
        
        try:
            self.player_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.player_process.wait()
        except Exception as e:
            logger.error(f"Error playing video with omxplayer: {e}")
    
    def _play_with_vlc(self, video_path: str):
        """Play video using VLC"""
        import subprocess
        
        cmd = ["vlc"]
        
        if self.fullscreen:
            cmd.extend(["--fullscreen", "--no-video-title-show"])
        
        if self.loop_videos:
            cmd.append("--repeat")
        else:
            cmd.append("--play-and-exit")
        
        # Quiet mode
        cmd.extend(["--quiet", "--no-osd"])
        
        cmd.append(video_path)
        
        try:
            self.player_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.player_process.wait()
        except Exception as e:
            logger.error(f"Error playing video with VLC: {e}")
    
    def _play_with_opencv(self, video_path: str):
        """Play video using OpenCV (for testing)"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            
            if self.fullscreen:
                cv2.namedWindow('PLTN Video', cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty('PLTN Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.namedWindow('PLTN Video', cv2.WINDOW_NORMAL)
            
            while cap.isOpened() and not self.stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    if self.loop_videos:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break
                
                cv2.imshow('PLTN Video', frame)
                
                # Wait for frame delay (30 fps)
                if cv2.waitKey(33) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            logger.error(f"Error playing video with OpenCV: {e}")
    
    def stop_video(self):
        """Stop currently playing video"""
        self.stop_flag.set()
        
        if self.player_process:
            try:
                self.player_process.terminate()
                self.player_process.wait(timeout=2)
            except:
                self.player_process.kill()
            
            self.player_process = None
        
        self.is_playing = False
        self.stop_flag.clear()
        logger.info("Video stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_video()
        logger.info("Video player cleaned up")


# Example integration with main controller
class VideoEnabledPLTNController:
    """
    Extended PLTN Controller with video player integration
    This is an example of how to integrate the video player
    """
    
    def __init__(self):
        # Initialize video player
        self.video_player = VideoPlayer(
            video_directory="/home/pi/pltn_videos",
            backend=VideoPlayerBackend.OMXPLAYER,
            fullscreen=True,
            loop_videos=True
        )
        
        # Video update thread
        self.video_update_thread = None
        self.video_running = True
    
    def start_video_system(self):
        """Start video update thread"""
        self.video_update_thread = threading.Thread(
            target=self._video_update_loop,
            daemon=True
        )
        self.video_update_thread.start()
        logger.info("Video system started")
    
    def _video_update_loop(self):
        """Update video based on simulation state (called periodically)"""
        while self.video_running:
            try:
                # Get current system state (example values)
                # In real implementation, get from actual system state
                pressure = 150.0  # From pressurizer
                pump1 = 2  # From pump controller
                pump2 = 2
                pump3 = 2
                rods = [50, 50, 50]  # From ESP-B
                power = 75.0  # From ESP-C
                emergency = False
                
                # Update video player with current state
                self.video_player.update_simulation_state(
                    pressure=pressure,
                    pump_primary=pump1,
                    pump_secondary=pump2,
                    pump_tertiary=pump3,
                    rod_positions=rods,
                    power_output=power,
                    emergency_active=emergency
                )
                
            except Exception as e:
                logger.error(f"Error in video update loop: {e}")
            
            # Update every 5 seconds
            time.sleep(5)
    
    def stop_video_system(self):
        """Stop video system"""
        self.video_running = False
        self.video_player.cleanup()
        logger.info("Video system stopped")


if __name__ == "__main__":
    """Test video player standalone"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("PLTN Video Player - Test Mode")
    print("="*60)
    
    # Create video player
    player = VideoPlayer(
        video_directory="/home/pi/pltn_videos",
        backend=VideoPlayerBackend.OMXPLAYER,
        fullscreen=True,
        loop_videos=False
    )
    
    try:
        # Test phase transitions
        print("\n[1] Testing IDLE phase...")
        player.update_simulation_state(0, 0, 0, 0, [0, 0, 0], 0, False)
        time.sleep(10)
        
        print("\n[2] Testing PRESSURE phase...")
        player.update_simulation_state(50, 0, 0, 0, [0, 0, 0], 0, False)
        time.sleep(10)
        
        print("\n[3] Testing PUMPS phase...")
        player.update_simulation_state(100, 1, 1, 1, [0, 0, 0], 0, False)
        time.sleep(10)
        
        print("\n[4] Testing CONTROL RODS phase...")
        player.update_simulation_state(150, 2, 2, 2, [30, 30, 30], 0, False)
        time.sleep(10)
        
        print("\n[5] Testing POWER GENERATION phase...")
        player.update_simulation_state(150, 2, 2, 2, [50, 50, 50], 40, False)
        time.sleep(10)
        
        print("\n[6] Testing NORMAL OPERATION phase...")
        player.update_simulation_state(150, 2, 2, 2, [60, 60, 60], 80, False)
        time.sleep(10)
        
        print("\n[7] Testing EMERGENCY phase...")
        player.update_simulation_state(150, 2, 2, 2, [60, 60, 60], 80, True)
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        player.cleanup()
        print("\nVideo player test completed")
