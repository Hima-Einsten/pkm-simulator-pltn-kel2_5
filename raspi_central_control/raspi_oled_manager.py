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
    Manages 9 OLED displays (0.91 inch 128x64) through 2x TCA9548A multiplexers
    
    TCA9548A #1 (0x70):
      - Channel 1: OLED #1 (Pressurizer)
      - Channel 2: OLED #2 (Pump Primary)
      - Channel 3: OLED #3 (Pump Secondary)
      - Channel 4: OLED #4 (Pump Tertiary)
      - Channel 5: OLED #5 (Safety Rod)
      - Channel 6: OLED #6 (Shim Rod)
      - Channel 7: OLED #7 (Regulating Rod)
    
    TCA9548A #2 (0x71):
      - Channel 1: OLED #8 (Thermal Power)
      - Channel 2: OLED #9 (System Status)
    """
    
    def __init__(self, mux_manager, width: int = 128, height: int = 64):
        """
        Initialize OLED manager for 9 displays
        
        Args:
            mux_manager: TCA9548A multiplexer manager
            width: Display width (128 for 0.91 inch)
            height: Display height (64 for 0.91 inch)
        """
        self.mux = mux_manager
        self.width = width
        self.height = height
        
        # Create 9 display objects
        self.oled_pressurizer = OLEDDisplay(width, height)
        self.oled_pump_primary = OLEDDisplay(width, height)
        self.oled_pump_secondary = OLEDDisplay(width, height)
        self.oled_pump_tertiary = OLEDDisplay(width, height)
        self.oled_safety_rod = OLEDDisplay(width, height)
        self.oled_shim_rod = OLEDDisplay(width, height)
        self.oled_regulating_rod = OLEDDisplay(width, height)
        self.oled_thermal_power = OLEDDisplay(width, height)
        self.oled_system_status = OLEDDisplay(width, height)
        
        self.blink_state = False
        self.last_blink_time = time.time()
        
        # Data tracking for optimization (only update if changed)
        self.last_data = {
            'pressurizer': None,
            'pump_primary': None,
            'pump_secondary': None,
            'pump_tertiary': None,
            'safety_rod': None,
            'shim_rod': None,
            'regulating_rod': None,
            'thermal_power': None,
            'system_status': None
        }
        
        logger.info("OLED Manager initialized for 9 displays (128x64)")
    
    def init_all_displays(self):
        """Initialize all 9 OLED displays through 2x TCA9548A"""
        # TCA9548A #1 (0x70) - 7 displays
        displays_mux1 = [
            (1, self.oled_pressurizer, "Pressurizer"),
            (2, self.oled_pump_primary, "Pump Primary"),
            (3, self.oled_pump_secondary, "Pump Secondary"),
            (4, self.oled_pump_tertiary, "Pump Tertiary"),
            (5, self.oled_safety_rod, "Safety Rod"),
            (6, self.oled_shim_rod, "Shim Rod"),
            (7, self.oled_regulating_rod, "Regulating Rod")
        ]
        
        # TCA9548A #2 (0x71) - 2 displays
        displays_mux2 = [
            (1, self.oled_thermal_power, "Thermal Power"),
            (2, self.oled_system_status, "System Status")
        ]
        
        if not ADAFRUIT_AVAILABLE:
            logger.warning("Running without hardware displays (simulation mode)")
            return
        
        try:
            i2c = board.I2C()
            
            # Initialize displays on TCA9548A #1
            logger.info("Initializing OLEDs on TCA9548A #1 (0x70)...")
            for channel, display, name in displays_mux1:
                self.mux.select_display_channel(channel)
                time.sleep(0.1)
                display.init_hardware(i2c, 0x3C)
                
                # Show startup message
                display.clear()
                display.draw_text_centered(name, 20, display.font_large)
                display.draw_text_centered("Ready", 40, display.font)
                display.show()
                logger.info(f"  ✓ OLED #{channel}: {name}")
                time.sleep(0.3)
            
            # Initialize displays on TCA9548A #2
            logger.info("Initializing OLEDs on TCA9548A #2 (0x71)...")
            # Note: This requires dual multiplexer support
            # For now, we'll use the same method but with different base
            for channel, display, name in displays_mux2:
                # Select second multiplexer (implementation depends on mux_manager)
                # This may need adjustment based on DualMultiplexerManager implementation
                self.mux.select_display_channel(channel + 10)  # Offset for second mux
                time.sleep(0.1)
                display.init_hardware(i2c, 0x3C)
                
                # Show startup message
                display.clear()
                display.draw_text_centered(name, 20, display.font_large)
                display.draw_text_centered("Ready", 40, display.font)
                display.show()
                logger.info(f"  ✓ OLED #{channel + 7}: {name}")
                time.sleep(0.3)
            
            logger.info("All 9 OLED displays initialized successfully")
            
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
        self.update_pump_display("TERTIARY", 4, self.oled_pump_tertiary, status, pwm)
    
    def update_rod_display(self, rod_name: str, channel: int, display_obj: OLEDDisplay, position: int):
        """
        Update control rod display
        
        Args:
            rod_name: Name of rod (e.g., "SAFETY", "SHIM", "REGULATING")
            channel: TCA9548A channel
            display_obj: OLED display object
            position: Rod position (0-100%)
        """
        self.mux.select_display_channel(channel)
        
        display_obj.clear()
        
        # Title
        display_obj.draw_text_centered(f"{rod_name} ROD", 0, display_obj.font)
        
        # Position value (large)
        position_text = f"{position}%"
        display_obj.draw_text_centered(position_text, 20, display_obj.font_large)
        
        # Progress bar
        display_obj.draw_text("Position:", 2, 45, display_obj.font)
        display_obj.draw_progress_bar(10, 55, 108, 8, position, 100)
        
        display_obj.show()
    
    def update_safety_rod(self, position: int):
        """Update safety rod display"""
        self.update_rod_display("SAFETY", 5, self.oled_safety_rod, position)
    
    def update_shim_rod(self, position: int):
        """Update shim rod display"""
        self.update_rod_display("SHIM", 6, self.oled_shim_rod, position)
    
    def update_regulating_rod(self, position: int):
        """Update regulating rod display"""
        self.update_rod_display("REGULATING", 7, self.oled_regulating_rod, position)
    
    def update_thermal_power(self, power_kw: float):
        """
        Update thermal power display
        
        Args:
            power_kw: Electrical power in kW (0-300,000 kW = 0-300 MWe)
        """
        # Channel offset for second multiplexer
        self.mux.select_display_channel(11)  # TCA9548A #2, Channel 1
        
        display = self.oled_thermal_power
        display.clear()
        
        # Title
        display.draw_text_centered("ELECTRICAL POWER", 0, display.font)
        
        # Power in MWe (large)
        power_mwe = power_kw / 1000.0
        power_text = f"{power_mwe:.1f} MWe"
        display.draw_text_centered(power_text, 20, display.font_large)
        
        # Reactor thermal (smaller)
        thermal_mwth = power_kw / 0.33  # Reverse calculate thermal from electrical
        thermal_text = f"({thermal_mwth:.0f} MWth)"
        display.draw_text_centered(thermal_text, 45, display.font)
        
        display.show()
    
    def update_system_status(self, turbine_state: int, humid_sg1: int, humid_sg2: int,
                            humid_ct1: int, humid_ct2: int, humid_ct3: int, humid_ct4: int,
                            interlock: bool = True):
        """
        Update system status display
        
        Args:
            turbine_state: Turbine state (0=IDLE, 1=STARTING, 2=RUNNING, 3=SHUTDOWN)
            humid_sg1-sg2: Steam generator humidifier status (0/1)
            humid_ct1-ct4: Cooling tower humidifier status (0/1)
            interlock: Interlock satisfied flag
        """
        # Channel offset for second multiplexer
        self.mux.select_display_channel(12)  # TCA9548A #2, Channel 2
        
        display = self.oled_system_status
        display.clear()
        
        # Title
        display.draw_text_centered("SYSTEM STATUS", 0, display.font)
        
        # Turbine state
        turbine_text = ["IDLE", "STARTING", "RUNNING", "SHUTDOWN"][turbine_state]
        display.draw_text(f"Turbine: {turbine_text}", 2, 15, display.font)
        
        # Humidifier status
        sg_status = f"SG: {'✓' if humid_sg1 else '✗'}{'✓' if humid_sg2 else '✗'}"
        ct_status = f"CT: {'✓' if humid_ct1 else '✗'}{'✓' if humid_ct2 else '✗'}{'✓' if humid_ct3 else '✗'}{'✓' if humid_ct4 else '✗'}"
        display.draw_text(sg_status, 2, 30, display.font)
        display.draw_text(ct_status, 2, 42, display.font)
        
        # Interlock status
        interlock_text = "Interlock: OK" if interlock else "Interlock: NOT OK"
        display.draw_text(interlock_text, 2, 54, display.font)
        
        display.show()
    
    def update_all(self, state):
        """
        Update all displays from panel state
        
        Args:
            state: PanelState object with all current values
        """
        self.update_blink_state()
        
        # Update all displays
        self.update_pressurizer_display(state.pressure, 
                                       warning=(state.pressure > 180),
                                       critical=(state.pressure > 195))
        
        self.update_pump_primary(state.pump_primary_status, 50)  # PWM placeholder
        self.update_pump_secondary(state.pump_secondary_status, 50)
        self.update_pump_tertiary(state.pump_tertiary_status, 50)
        
        self.update_safety_rod(state.safety_rod)
        self.update_shim_rod(state.shim_rod)
        self.update_regulating_rod(state.regulating_rod)
        
        self.update_thermal_power(state.thermal_kw)
        
        self.update_system_status(
            turbine_state=0,  # Placeholder
            humid_sg1=state.humid_sg1_cmd,
            humid_sg2=state.humid_sg2_cmd,
            humid_ct1=state.humid_ct1_cmd,
            humid_ct2=state.humid_ct2_cmd,
            humid_ct3=state.humid_ct3_cmd,
            humid_ct4=state.humid_ct4_cmd,
            interlock=state.interlock_satisfied
        )
    
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
