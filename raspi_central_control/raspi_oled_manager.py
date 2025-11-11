"""
OLED Display Manager
Manages 4 OLED displays through TCA9548A multiplexer
"""

import logging
from PIL import Image, ImageDraw, ImageFont
import time

logger = logging.getLogger(__name__)

# Try to import Adafruit library
try:
    import board
    import adafruit_ssd1306
    ADAFRUIT_AVAILABLE = True
except ImportError:
    logger.warning("Adafruit libraries not available. Running in simulation mode.")
    ADAFRUIT_AVAILABLE = False


class OLEDDisplay:
    """
    Single OLED display wrapper
    """
    
    def __init__(self, width: int = 128, height: int = 32):
        """
        Initialize OLED display
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.device = None
        self.image = Image.new('1', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Try to load a font
        try:
            self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
        except:
            self.font = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
        
        self.initialized = False
    
    def init_hardware(self, i2c, address: int = 0x3C):
        """
        Initialize hardware OLED display
        
        Args:
            i2c: I2C bus object
            address: I2C address of OLED
        """
        if not ADAFRUIT_AVAILABLE:
            logger.warning("Hardware display not available")
            return False
        
        try:
            self.device = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, i2c, addr=address)
            self.device.fill(0)
            self.device.show()
            self.initialized = True
            logger.info(f"OLED display initialized at 0x{address:02X}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OLED at 0x{address:02X}: {e}")
            return False
    
    def clear(self):
        """Clear display"""
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
    
    def draw_text(self, text: str, x: int = 0, y: int = 0, font=None):
        """Draw text on display"""
        if font is None:
            font = self.font
        self.draw.text((x, y), text, font=font, fill=255)
    
    def draw_text_centered(self, text: str, y: int = 0, font=None):
        """Draw centered text"""
        if font is None:
            font = self.font
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        self.draw.text((x, y), text, font=font, fill=255)
    
    def draw_progress_bar(self, x: int, y: int, width: int, height: int, 
                         value: float, max_value: float = 100.0):
        """
        Draw a progress bar
        
        Args:
            x, y: Top-left corner
            width, height: Bar dimensions
            value: Current value
            max_value: Maximum value
        """
        # Draw outline
        self.draw.rectangle((x, y, x + width, y + height), outline=255, fill=0)
        
        # Draw filled portion
        if value > 0 and max_value > 0:
            fill_width = int((value / max_value) * (width - 2))
            if fill_width > 0:
                self.draw.rectangle((x + 1, y + 1, x + 1 + fill_width, y + height - 1), 
                                  outline=255, fill=255)
    
    def show(self):
        """Update display"""
        if self.initialized and self.device:
            try:
                self.device.image(self.image)
                self.device.show()
            except Exception as e:
                logger.error(f"Failed to update display: {e}")


class OLEDManager:
    """
    Manages 4 OLED displays through TCA9548A multiplexer
    """
    
    def __init__(self, mux_manager, width: int = 128, height: int = 32):
        """
        Initialize OLED manager
        
        Args:
            mux_manager: TCA9548A multiplexer manager
            width: Display width
            height: Display height
        """
        self.mux = mux_manager
        self.width = width
        self.height = height
        
        # Create 4 display objects
        self.oled_pressurizer = OLEDDisplay(width, height)
        self.oled_pump_primary = OLEDDisplay(width, height)
        self.oled_pump_secondary = OLEDDisplay(width, height)
        self.oled_pump_tertiary = OLEDDisplay(width, height)
        
        self.blink_state = False
        self.last_blink_time = time.time()
        
        logger.info("OLED Manager initialized")
    
    def init_all_displays(self):
        """Initialize all OLED displays"""
        displays = [
            (0, self.oled_pressurizer, "Pressurizer"),
            (1, self.oled_pump_primary, "Pump Primary"),
            (2, self.oled_pump_secondary, "Pump Secondary"),
            (3, self.oled_pump_tertiary, "Pump Tertiary")
        ]
        
        if not ADAFRUIT_AVAILABLE:
            logger.warning("Running without hardware displays (simulation mode)")
            return
        
        try:
            i2c = board.I2C()
            
            for channel, display, name in displays:
                self.mux.select_display_channel(channel)
                time.sleep(0.1)
                display.init_hardware(i2c, 0x3C)
                
                # Show startup message
                display.clear()
                display.draw_text_centered(name, 8, display.font)
                display.draw_text_centered("Initializing...", 20, display.font)
                display.show()
                time.sleep(0.5)
            
            logger.info("All OLED displays initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize displays: {e}")
    
    def update_blink_state(self, interval: float = 0.25):
        """Update blink state for warning indicators"""
        current_time = time.time()
        if current_time - self.last_blink_time > interval:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time
    
    def update_pressurizer_display(self, pressure: float, warning: bool = False, 
                                   critical: bool = False):
        """
        Update pressurizer display
        
        Args:
            pressure: Current pressure in bar
            warning: Warning flag (pressure high)
            critical: Critical flag (pressure critical)
        """
        self.mux.select_display_channel(0)
        
        display = self.oled_pressurizer
        display.clear()
        
        # Title
        display.draw_text_centered("PRESSURIZER", 0, display.font)
        
        # Pressure value (large)
        pressure_text = f"{pressure:.1f} bar"
        display.draw_text_centered(pressure_text, 12, display.font_large)
        
        # Status indicator
        if critical:
            if self.blink_state:
                display.draw_text_centered("!! CRITICAL !!", 28, display.font)
        elif warning:
            if self.blink_state:
                display.draw_text_centered("! WARNING !", 28, display.font)
        else:
            display.draw_text_centered("NORMAL", 28, display.font)
        
        display.show()
    
    def update_pump_display(self, pump_name: str, channel: int, display_obj: OLEDDisplay,
                           status: int, pwm: int):
        """
        Update pump display
        
        Args:
            pump_name: Name of pump (e.g., "PRIMARY")
            channel: TCA9548A channel
            display_obj: OLED display object
            status: Pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
            pwm: PWM percentage (0-100)
        """
        self.mux.select_display_channel(channel)
        
        display_obj.clear()
        
        # Title
        display_obj.draw_text_centered(f"PUMP {pump_name}", 0, display_obj.font)
        
        # Status text
        status_text = ["OFF", "STARTING", "ON", "SHUTTING DOWN"][status]
        display_obj.draw_text_centered(status_text, 12, display_obj.font_large)
        
        # PWM bar
        display_obj.draw_text("PWM:", 2, 25, display_obj.font)
        display_obj.draw_progress_bar(30, 25, 95, 6, pwm, 100)
        
        display_obj.show()
    
    def update_pump_primary(self, status: int, pwm: int):
        """Update primary pump display"""
        self.update_pump_display("PRIMARY", 1, self.oled_pump_primary, status, pwm)
    
    def update_pump_secondary(self, status: int, pwm: int):
        """Update secondary pump display"""
        self.update_pump_display("SECONDARY", 2, self.oled_pump_secondary, status, pwm)
    
    def update_pump_tertiary(self, status: int, pwm: int):
        """Update tertiary pump display"""
        self.update_pump_display("TERTIARY", 3, self.oled_pump_tertiary, status, pwm)
    
    def show_startup_screen(self):
        """Show startup screen on all displays"""
        screens = [
            (0, self.oled_pressurizer),
            (1, self.oled_pump_primary),
            (2, self.oled_pump_secondary),
            (3, self.oled_pump_tertiary)
        ]
        
        for channel, display in screens:
            self.mux.select_display_channel(channel)
            display.clear()
            display.draw_text_centered("PLTN Simulator", 8, display.font)
            display.draw_text_centered("v2.0 - I2C", 20, display.font)
            display.show()
        
        time.sleep(2)
    
    def show_error_screen(self, message: str):
        """Show error message on all displays"""
        screens = [
            (0, self.oled_pressurizer),
            (1, self.oled_pump_primary),
            (2, self.oled_pump_secondary),
            (3, self.oled_pump_tertiary)
        ]
        
        for channel, display in screens:
            self.mux.select_display_channel(channel)
            display.clear()
            display.draw_text_centered("ERROR", 8, display.font_large)
            display.draw_text_centered(message, 24, display.font)
            display.show()


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("OLED Manager Test")
    print("Note: This is a simulation. Real display requires Raspberry Pi hardware.")
    
    # Create dummy display
    display = OLEDDisplay()
    
    # Test drawing
    display.clear()
    display.draw_text_centered("PRESSURIZER", 0)
    display.draw_text_centered("150.5 bar", 12)
    display.draw_progress_bar(10, 25, 108, 6, 75, 100)
    
    print("Display test completed (image not shown in simulation)")
