"""
Create placeholder videos for PLTN Simulator
This creates simple test videos with text overlay
Requires: opencv-python, numpy
"""

import cv2
import numpy as np
import os

def create_placeholder_video(filename, title, duration=10, fps=30):
    """
    Create a simple placeholder video with text
    
    Args:
        filename: Output filename
        title: Text to display
        duration: Duration in seconds
        fps: Frames per second
    """
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # Create blank frame (dark blue background)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (80, 40, 0)  # Dark blue in BGR
        
        # Add title text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(title, font, 2, 3)[0]
        text_x = (width - text_size[0]) // 2
        text_y = height // 2
        
        cv2.putText(frame, title, (text_x, text_y), font, 2, (255, 255, 255), 3)
        
        # Add subtitle
        subtitle = f"PLTN Simulator - Video Edukasi"
        sub_size = cv2.getTextSize(subtitle, font, 1, 2)[0]
        sub_x = (width - sub_size[0]) // 2
        sub_y = text_y + 80
        
        cv2.putText(frame, subtitle, (sub_x, sub_y), font, 1, (200, 200, 200), 2)
        
        # Add frame counter
        counter = f"Frame: {frame_num}/{total_frames}"
        cv2.putText(frame, counter, (50, height - 50), font, 0.7, (150, 150, 150), 2)
        
        out.write(frame)
    
    out.release()
    print(f"✓ Created: {filename}")

def main():
    """Create all placeholder videos"""
    
    print("="*60)
    print("Creating Placeholder Videos for PLTN Simulator")
    print("="*60)
    print()
    
    # Create output directory
    output_dir = "/home/pi/pltn_videos"
    
    # Check if running on Windows (for testing)
    if os.name == 'nt':
        output_dir = os.path.join(os.path.dirname(__file__), "test_videos")
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}\n")
    
    # Video definitions
    videos = [
        ("01_intro_pltn.mp4", "Pengenalan PLTN", 15),
        ("02_pressurizer_system.mp4", "Sistem Pressurizer", 12),
        ("03_coolant_circulation.mp4", "Sirkulasi Pendingin", 12),
        ("04_control_rods_operation.mp4", "Operasi Control Rod", 12),
        ("05_turbine_generator.mp4", "Turbin & Generator", 12),
        ("06_normal_operation.mp4", "Operasi Normal", 15),
        ("07_shutdown_procedure.mp4", "Prosedur Shutdown", 12),
        ("08_emergency_shutdown.mp4", "Emergency Shutdown", 10),
    ]
    
    # Create each video
    for filename, title, duration in videos:
        filepath = os.path.join(output_dir, filename)
        create_placeholder_video(filepath, title, duration)
    
    print()
    print("="*60)
    print("✓ All placeholder videos created!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Replace these placeholder videos with real educational content")
    print("2. Use tools like PowerPoint, Canva, or DaVinci Resolve")
    print("3. Keep format: MP4 (H.264), 1280x720 or 1920x1080")
    print("4. Test with: omxplayer video.mp4")
    print()

if __name__ == "__main__":
    try:
        import cv2
        import numpy as np
        main()
    except ImportError as e:
        print("Error: Required libraries not installed")
        print("Install with: pip3 install opencv-python numpy")
        print(f"Details: {e}")
