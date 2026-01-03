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
        
        # Try to load a font - smaller sizes for 128x32 display
        try:
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
            self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12)
        except:
            self.font_small = ImageFont.load_default()
            self.font = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
        
        self.initialized = False
    
    def init_hardware(self, i2c, address: int = 0x3C, timeout: float = 1.0):
        """
        Initialize hardware OLED display with timeout
        
        Args:
            i2c: I2C bus object
            address: I2C address of OLED
            timeout: Timeout in seconds (default 1.0s)
        """
        if not ADAFRUIT_AVAILABLE:
            logger.warning("Hardware display not available")
            return False
        
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def try_init():
            try:
                self.device = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, i2c, addr=address)
                self.device.fill(0)
                self.device.show()
                self.initialized = True
                result_queue.put(True)
                logger.debug(f"OLED display initialized at 0x{address:02X}")
            except Exception as e:
                logger.debug(f"Failed to initialize OLED at 0x{address:02X}: {e}")
                result_queue.put(False)
        
        # Try init with timeout
        init_thread = threading.Thread(target=try_init, daemon=True)
        init_thread.start()
        init_thread.join(timeout=timeout)
        
        # Check result
        try:
            return result_queue.get_nowait()
        except:
            logger.debug(f"OLED at 0x{address:02X} timeout after {timeout}s")
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
    
    def __init__(self, mux_manager, width: int = 128, height: int = 32):
        """
        Initialize OLED manager for 9 displays
        
        Args:
            mux_manager: TCA9548A multiplexer manager
            width: Display width (128 for 0.91 inch)
            height: Display height (32 for 0.91 inch)
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
        
        logger.info("OLED Manager initialized for 9 displays (128x32)")
    
    def init_all_displays(self):
        """Initialize all 9 OLED displays through 2x TCA9548A with graceful degradation"""
        # TCA9548A #1 (0x70) - 7 displays
        displays_mux1 = [
            (1, self.oled_pressurizer, "Pressurizer"),
            (2, self.oled_pump_primary, "Pump Primer"),
            (3, self.oled_pump_secondary, "Pump Sekunder"),
            (4, self.oled_pump_tertiary, "Pump Tersier"),
            (5, self.oled_safety_rod, "Safety Rod"),
            (6, self.oled_shim_rod, "Shim Rod"),
            (7, self.oled_regulating_rod, "Reg Rod")
        ]
        
        # TCA9548A #2 (0x71) - 2 displays
        displays_mux2 = [
            (1, self.oled_thermal_power, "Thermal Power"),
            (2, self.oled_system_status, "System Status")
        ]
        
        if not ADAFRUIT_AVAILABLE:
            logger.warning("Running without hardware displays (simulation mode)")
            return
        
        success_count = 0
        
        try:
            i2c = board.I2C()
            
            # Initialize displays on TCA9548A #1 (0x70)
            logger.info("Initializing OLEDs on TCA9548A #1 (0x70)...")
            for channel, display, name in displays_mux1:
                try:
                    self.mux.select_display_channel(channel)
                    time.sleep(0.05)  # Minimal delay
                    
                    # Try to initialize with 0.5s timeout per display
                    if display.init_hardware(i2c, 0x3C, timeout=0.5):
                        # Show startup message (3 lines, max y=24)
                        display.clear()
                        display.draw_text_centered(name, 1, display.font_small)
                        display.draw_text_centered("PLTN v2", 12, display.font)
                        display.draw_text_centered("Ready", 22, display.font_small)
                        display.show()
                        logger.info(f"  ✓ OLED #{channel}: {name}")
                        success_count += 1
                    else:
                        logger.warning(f"  ✗ OLED #{channel}: {name} - skipped")
                    
                except Exception as e:
                    logger.warning(f"  ✗ OLED #{channel}: {name} - error: {e}")
                    continue  # Skip to next display
            
            # Initialize displays on TCA9548A #2 (0x71)
            logger.info("Initializing OLEDs on TCA9548A #2 (0x71)...")
            for channel, display, name in displays_mux2:
                try:
                    # Use esp_channel to access second multiplexer (0x71)
                    self.mux.select_esp_channel(channel)
                    time.sleep(0.05)  # Minimal delay
                    
                    # Try to initialize with 0.5s timeout per display
                    if display.init_hardware(i2c, 0x3C, timeout=0.5):
                        # Show startup message (3 lines, max y=24)
                        display.clear()
                        display.draw_text_centered(name, 1, display.font_small)
                        display.draw_text_centered("PLTN v2", 12, display.font)
                        display.draw_text_centered("Ready", 22, display.font_small)
                        display.show()
                        logger.info(f"  ✓ OLED #{channel + 7}: {name}")
                        success_count += 1
                    else:
                        logger.warning(f"  ✗ OLED #{channel + 7}: {name} - skipped")
                    
                except Exception as e:
                    logger.warning(f"  ✗ OLED #{channel + 7}: {name} - error: {e}")
                    continue  # Skip to next display
            
            logger.info(f"OLED initialization complete: {success_count}/9 displays ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize displays: {e}")
            logger.warning("Continuing without OLED displays...")
    
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
        # Select channel
        self.mux.select_display_channel(1)  # Pressurizer on channel 1
        
        # Round to 1 decimal
        pressure_rounded = round(pressure, 1)
        
        display = self.oled_pressurizer
        display.clear()
        
        # Title (small font)
        display.draw_text_centered("PRESSURIZER", 1, display.font_small)
        
        # Pressure value (medium font, centered)
        pressure_text = f"{pressure_rounded:.1f} bar"
        display.draw_text_centered(pressure_text, 12, display.font_large)
        
        display.show()
        time.sleep(0.005)  # 5ms delay after show() to ensure OLED processing completes
    
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
        # Select channel
        self.mux.select_display_channel(channel)
        
        display_obj.clear()
        
        # Title - use shorter names (small font)
        title_map = {
            "PRIMARY": "PUMP 1",
            "SECONDARY": "PUMP 2",
            "TERTIARY": "PUMP 3"
        }
        title = title_map.get(pump_name, f"PUMP {pump_name}")
        display_obj.draw_text_centered(title, 1, display_obj.font_small)
        
        # Status on line 2
        status_text = ["OFF", "START", "ON", "STOP"][status]
        display_obj.draw_text_centered(status_text, 14, display_obj.font_large)
        
        display_obj.show()
        time.sleep(0.005)  # 5ms delay after show() to ensure OLED processing completes
    
    def update_pump_primary(self, status: int, pwm: int):
        """Update primary pump display"""
        self.update_pump_display("PRIMARY", 2, self.oled_pump_primary, status, pwm)  # Channel 2
    
    def update_pump_secondary(self, status: int, pwm: int):
        """Update secondary pump display"""
        self.update_pump_display("SECONDARY", 3, self.oled_pump_secondary, status, pwm)  # Channel 3
    
    def update_pump_tertiary(self, status: int, pwm: int):
        """Update tertiary pump display"""
        self.update_pump_display("TERTIARY", 4, self.oled_pump_tertiary, status, pwm)  # Channel 4
    
    def update_rod_display(self, rod_name: str, channel: int, display_obj: OLEDDisplay, position: int):
        """
        Update control rod display
        
        Args:
            rod_name: Name of rod (e.g., "SAFETY", "SHIM", "REGULATING")
            channel: TCA9548A channel
            display_obj: OLED display object
            position: Rod position (0-100%)
        """
        # Select channel
        self.mux.select_display_channel(channel)
        
        display_obj.clear()
        
        # Title - use shorter names (small font)
        title_map = {
            "SAFETY": "SAFETY",
            "SHIM": "SHIM",
            "REGULATING": "REG"
        }
        title = title_map.get(rod_name, rod_name)
        display_obj.draw_text_centered(title, 1, display_obj.font_small)
        
        # Position value (medium font, centered)
        position_text = f"{position}%"
        display_obj.draw_text_centered(position_text, 12, display_obj.font_large)
        
        display_obj.show()
        time.sleep(0.005)  # 5ms delay after show() to ensure OLED processing completes
    
    def update_safety_rod(self, position: int):
        """Update safety rod display"""
        self.update_rod_display("SAFETY", 5, self.oled_safety_rod, position)
    
    def update_shim_rod(self, position: int):
        """Update shim rod display"""
        self.update_rod_display("SHIM", 6, self.oled_shim_rod, position)
    
    def update_regulating_rod(self, position: int):
        """Update regulating rod display"""
        self.update_rod_display("REGULATING", 7, self.oled_regulating_rod, position)
        # Extra delay: This is the LAST channel on MUX #1 (channel 7)
        # Give OLED time to fully process before switching to MUX #2
        time.sleep(0.010)  # 10ms post-update delay
    
    def update_thermal_power(self, power_kw: float):
        """
        Update thermal power display
        
        Args:
            power_kw: Electrical power in kW (0-300,000 kW = 0-300 MWe)
        """
        # Select channel
        self.mux.select_esp_channel(1)  # Use ESP channel for TCA9548A #2, Channel 1
        
        # Round to 1 decimal
        power_kw_rounded = round(power_kw, 1)
        
        display = self.oled_thermal_power
        display.clear()
        
        # Title (small font)
        display.draw_text_centered("POWER", 1, display.font_small)
        
        # Power in MWe (medium font, centered)
        power_mwe = power_kw_rounded / 1000.0
        power_text = f"{power_mwe:.1f} MWe"
        display.draw_text_centered(power_text, 12, display.font_large)
        
        display.show()
        time.sleep(0.005)  # 5ms delay after show() to ensure OLED processing completes
    
    def update_system_status(self, pressure: float, 
                            pump_primary: int, pump_secondary: int, pump_tertiary: int,
                            interlock: bool, thermal_kw: float, turbine_speed: float):
        """
        Update system status display with user instructions AND system status
        
        Args:
            pressure: Current pressure
            pump_primary: Primary pump status
            pump_secondary: Secondary pump status  
            pump_tertiary: Tertiary pump status
            interlock: Interlock satisfied flag
            thermal_kw: Thermal power in kW
            turbine_speed: Turbine speed percentage
        """
        # Select channel
        self.mux.select_esp_channel(2)  # Use ESP channel for TCA9548A #2, Channel 2
        
        display = self.oled_system_status
        display.clear()
        
        # Determine if showing instruction or status
        # Show instruction if system not ready
        if pressure < 40.0:
            instruction = f"Raise P to 40"
            display.draw_text_centered("INSTRUKSI", 1, display.font_small)
            display.draw_text_centered(instruction, 11, display.font_small)
            display.draw_text(f"Now: {pressure:.0f}bar", 0, 21, display.font_small)
        elif pump_primary != 2:  # Not ON
            instruction = "Start Pump 1"
            display.draw_text_centered("INSTRUKSI", 1, display.font_small)
            display.draw_text_centered(instruction, 14, display.font_large)
        elif pump_secondary != 2:
            instruction = "Start Pump 2"
            display.draw_text_centered("INSTRUKSI", 1, display.font_small)
            display.draw_text_centered(instruction, 14, display.font_large)
        elif pump_tertiary != 2:
            instruction = "Start Pump 3"
            display.draw_text_centered("INSTRUKSI", 1, display.font_small)
            display.draw_text_centered(instruction, 14, display.font_large)
        elif not interlock:
            instruction = "Wait P>=40bar"
            display.draw_text_centered("INSTRUKSI", 1, display.font_small)
            display.draw_text_centered(instruction, 14, display.font)
        else:
            # System ready - show STATUS instead of instruction
            display.draw_text_centered("STATUS", 1, display.font_small)
            
            # Line 1: Steam generation (thermal power)
            if thermal_kw >= 50000:  # 50 MWth = steam production
                steam_text = "Uap: Ya"
            else:
                steam_text = "Uap: Blm"
            display.draw_text(steam_text, 0, 11, display.font_small)
            
            # Line 2: Turbine & Generator
            if turbine_speed >= 80:
                turb_gen = "Turbin&Gen:ON"
            elif turbine_speed >= 10:
                turb_gen = "Turbin:START"
            else:
                turb_gen = "Raise Rods!"
            display.draw_text(turb_gen, 0, 21, display.font_small)
        
        display.show()
        
        # Extra delay: This is the LAST channel on MUX #2 (channel 2)
        # Give OLED time to fully process before next update cycle
        time.sleep(0.010)  # 10ms post-update delay
    
    def update_all(self, state):
        """
        Update all displays from panel state
        
        Args:
            state: PanelState object with all current values
        """
        self.update_blink_state()
        
        # ============================================
        # MUX #1 (0x70) - Channels 1-7
        # ============================================
        
        # Update all displays on MUX #1
        self.update_pressurizer_display(state.pressure, 
                                       warning=(state.pressure > 180),
                                       critical=(state.pressure > 195))
        
        self.update_pump_primary(state.pump_primary_status, 50)  # PWM placeholder
        self.update_pump_secondary(state.pump_secondary_status, 50)
        self.update_pump_tertiary(state.pump_tertiary_status, 50)
        
        self.update_safety_rod(state.safety_rod)
        self.update_shim_rod(state.shim_rod)
        self.update_regulating_rod(state.regulating_rod)
        
        # ============================================
        # MUX #2 (0x71) - Channels 1-2
        # ============================================
        # Auto-delay handled by TCA9548AManager when switching between MUX
        
        self.update_thermal_power(state.thermal_kw)
        
        self.update_system_status(
            pressure=state.pressure,
            pump_primary=state.pump_primary_status,
            pump_secondary=state.pump_secondary_status,
            pump_tertiary=state.pump_tertiary_status,
            interlock=state.interlock_satisfied,
            thermal_kw=state.thermal_kw,
            turbine_speed=state.turbine_speed
        )
    
    def show_startup_screen(self):
        """Show startup screen on all 9 displays (128x32 layout)"""
        screens_mux1 = [
            (1, self.oled_pressurizer, "PRESSURIZER"),
            (2, self.oled_pump_primary, "PUMP 1"),
            (3, self.oled_pump_secondary, "PUMP 2"),
            (4, self.oled_pump_tertiary, "PUMP 3"),
            (5, self.oled_safety_rod, "SAFETY ROD"),
            (6, self.oled_shim_rod, "SHIM ROD"),
            (7, self.oled_regulating_rod, "REG ROD")
        ]
        
        screens_mux2 = [
            (1, self.oled_thermal_power, "POWER"),
            (2, self.oled_system_status, "STATUS")
        ]
        
        # Show on TCA9548A #1
        for channel, display, name in screens_mux1:
            self.mux.select_display_channel(channel)
            display.clear()
            # 3 lines layout: y=1, y=12, y=22 (max y=24)
            display.draw_text_centered(name, 1, display.font_small)
            display.draw_text_centered("PLTN v2.0", 12, display.font)
            display.draw_text_centered("Ready", 22, display.font_small)
            display.show()
        
        # Show on TCA9548A #2
        for channel, display, name in screens_mux2:
            self.mux.select_esp_channel(channel)
            display.clear()
            # 3 lines layout: y=1, y=12, y=22 (max y=24)
            display.draw_text_centered(name, 1, display.font_small)
            display.draw_text_centered("PLTN v2.0", 12, display.font)
            display.draw_text_centered("Ready", 22, display.font_small)
            display.show()
        
        time.sleep(2)
    
    def show_error_screen(self, message: str):
        """Show error message on all 9 displays (128x32 layout)"""
        screens_mux1 = [
            (1, self.oled_pressurizer),
            (2, self.oled_pump_primary),
            (3, self.oled_pump_secondary),
            (4, self.oled_pump_tertiary),
            (5, self.oled_safety_rod),
            (6, self.oled_shim_rod),
            (7, self.oled_regulating_rod)
        ]
        
        screens_mux2 = [
            (1, self.oled_thermal_power),
            (2, self.oled_system_status)
        ]
        
        # Show on TCA9548A #1
        for channel, display in screens_mux1:
            self.mux.select_display_channel(channel)
            display.clear()
            # 3 lines layout: y=1, y=12, y=22 (max y=24)
            display.draw_text_centered("ERROR", 1, display.font_small)
            display.draw_text_centered("System", 12, display.font)
            display.draw_text_centered(message[:12], 22, display.font_small)  # Max 12 chars
            display.show()
        
        # Show on TCA9548A #2
        for channel, display in screens_mux2:
            self.mux.select_esp_channel(channel)
            display.clear()
            # 3 lines layout: y=1, y=12, y=22 (max y=24)
            display.draw_text_centered("ERROR", 1, display.font_small)
            display.draw_text_centered("System", 12, display.font)
            display.draw_text_centered(message[:12], 22, display.font_small)  # Max 12 chars
            display.show()


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("OLED Manager Test")
    print("Note: This is a simulation. Real display requires Raspberry Pi hardware.")
    
    # Create dummy display
    display = OLEDDisplay()
    
    # Test drawing (128x32 layout)
    display.clear()
    display.draw_text_centered("PRESSURIZER", 1, display.font_small)
    display.draw_text_centered("150.5 bar", 12, display.font)
    display.draw_text_centered("Normal", 22, display.font_small)
    
    print("Display test completed (image not shown in simulation)")
