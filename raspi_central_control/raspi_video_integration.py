"""
Integration module to add video player to existing PLTN controller
This file shows how to integrate video player with raspi_main.py
"""

import logging
from raspi_video_player import VideoPlayer, VideoPlayerBackend, SimulationPhase

logger = logging.getLogger(__name__)


def integrate_video_player(controller_instance):
    """
    Integrate video player into existing PLTNController instance
    
    Usage:
        controller = PLTNController()
        integrate_video_player(controller)
    
    Args:
        controller_instance: Instance of PLTNController from raspi_main.py
    """
    
    # Add video player to controller
    controller_instance.video_player = VideoPlayer(
        video_directory="/home/pi/pltn_videos",
        backend=VideoPlayerBackend.OMXPLAYER,
        fullscreen=True,
        loop_videos=True
    )
    
    logger.info("Video player integrated into PLTN Controller")
    
    # Store original update method
    original_update_displays = controller_instance.update_displays
    
    # Create new update method that includes video updates
    def update_displays_with_video(self):
        """Enhanced update_displays that also updates video"""
        # Call original display update
        original_update_displays()
        
        # Update video based on current state
        try:
            # Get ESP-B data for control rods
            with self.state_lock:
                esp_b_data = self.i2c_master.esp_b_data if hasattr(self.i2c_master, 'esp_b_data') else None
                esp_c_data = self.i2c_master.esp_c_data if hasattr(self.i2c_master, 'esp_c_data') else None
            
            # Extract rod positions
            if esp_b_data:
                rods = [
                    esp_b_data.get('rod1_position', 0),
                    esp_b_data.get('rod2_position', 0),
                    esp_b_data.get('rod3_position', 0)
                ]
            else:
                rods = [0, 0, 0]
            
            # Extract power output
            power = esp_c_data.get('power_output', 0) if esp_c_data else 0
            
            # Update video player
            self.video_player.update_simulation_state(
                pressure=self.state.pressure,
                pump_primary=self.state.pump_primary_status,
                pump_secondary=self.state.pump_secondary_status,
                pump_tertiary=self.state.pump_tertiary_status,
                rod_positions=rods,
                power_output=power,
                emergency_active=self.state.critical_active
            )
            
        except Exception as e:
            logger.error(f"Error updating video player: {e}")
    
    # Replace update_displays method
    import types
    controller_instance.update_displays = types.MethodType(update_displays_with_video, controller_instance)
    
    logger.info("Video updates integrated into display update loop")


def add_video_cleanup(controller_instance):
    """
    Add video cleanup to controller shutdown
    
    Args:
        controller_instance: Instance of PLTNController from raspi_main.py
    """
    
    # Store original shutdown method
    original_shutdown = controller_instance.shutdown
    
    def shutdown_with_video_cleanup(self):
        """Enhanced shutdown that also stops video player"""
        logger.info("Stopping video player...")
        if hasattr(self, 'video_player'):
            self.video_player.cleanup()
        
        # Call original shutdown
        original_shutdown()
    
    # Replace shutdown method
    import types
    controller_instance.shutdown = types.MethodType(shutdown_with_video_cleanup, controller_instance)
    
    logger.info("Video cleanup integrated into shutdown procedure")


# Example usage in raspi_main.py:
"""
To integrate video player into your existing raspi_main.py:

1. Import this module at the top of raspi_main.py:
   from raspi_video_integration import integrate_video_player, add_video_cleanup

2. In the main() function, after creating controller:
   
   controller = PLTNController()
   
   # Add video player integration
   integrate_video_player(controller)
   add_video_cleanup(controller)
   
   # Start video system
   controller.video_player.video_running = True
   
   # Continue with normal operation
   controller.run()

3. That's it! Video will automatically update based on simulation state.
"""
