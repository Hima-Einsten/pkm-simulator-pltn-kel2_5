"""
Main Control Program for PLTN Simulator
Raspberry Pi Central Control with Full I2C Architecture
"""

import time
import logging
import signal
import sys
import threading
from dataclasses import dataclass
from typing import Optional

# Import our modules
import raspi_config as config
from raspi_tca9548a import DualMultiplexerManager
from raspi_i2c_master import I2CMaster
from raspi_oled_manager import OLEDManager

# Try to import GPIO library
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    logging.warning("RPi.GPIO not available. Running in simulation mode.")
    GPIO_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SystemState:
    """System state variables"""
    # Pressurizer
    pressure: float = 0.0
    
    # Pump status and PWM
    pump_primary_status: int = config.PUMP_OFF
    pump_secondary_status: int = config.PUMP_OFF
    pump_tertiary_status: int = config.PUMP_OFF
    
    pump_primary_pwm: int = 0
    pump_secondary_pwm: int = 0
    pump_tertiary_pwm: int = 0
    
    # Alarm state
    warning_active: bool = False
    critical_active: bool = False
    buzzer_active: bool = False
    
    # Button states (for debouncing)
    button_states: dict = None
    button_last_time: dict = None
    
    # System running flag
    running: bool = True
    
    def __post_init__(self):
        self.button_states = {}
        self.button_last_time = {}


class PLTNController:
    """
    Main PLTN Controller Class
    Manages entire simulation system
    """
    
    def __init__(self):
        """Initialize PLTN Controller"""
        logger.info("="*60)
        logger.info("PLTN Simulator v2.0 - Raspberry Pi Central Control")
        logger.info("Full I2C Architecture with TCA9548A Multiplexers")
        logger.info("="*60)
        
        self.state = SystemState()
        
        # Initialize hardware components
        self.init_multiplexers()
        self.init_i2c_master()
        self.init_oled_displays()
        self.init_gpio()
        
        # Threading locks
        self.i2c_lock = threading.Lock()
        self.state_lock = threading.Lock()
        
        # CSV data logging
        if config.ENABLE_CSV_LOGGING:
            self.init_csv_logging()
        
        logger.info("PLTN Controller initialized successfully")
    
    def init_multiplexers(self):
        """Initialize TCA9548A multiplexers"""
        try:
            self.mux_manager = DualMultiplexerManager(
                display_bus=config.I2C_BUS_DISPLAY,
                esp_bus=config.I2C_BUS_ESP,
                display_addr=config.TCA9548A_DISPLAY_ADDRESS,
                esp_addr=config.TCA9548A_ESP_ADDRESS
            )
            
            # Scan for devices
            logger.info("Scanning I2C devices...")
            devices = self.mux_manager.scan_all()
            
            logger.info("Display multiplexer devices:")
            for ch, addrs in devices['display'].items():
                logger.info(f"  Channel {ch}: {[hex(a) for a in addrs]}")
            
            logger.info("ESP multiplexer devices:")
            for ch, addrs in devices['esp'].items():
                logger.info(f"  Channel {ch}: {[hex(a) for a in addrs]}")
            
        except Exception as e:
            logger.error(f"Failed to initialize multiplexers: {e}")
            raise
    
    def init_i2c_master(self):
        """Initialize I2C Master for ESP communication"""
        try:
            self.i2c_master = I2CMaster(
                bus_number=config.I2C_BUS_ESP,
                mux_select_callback=self.mux_manager.select_esp_channel
            )
            logger.info("I2C Master initialized")
        except Exception as e:
            logger.error(f"Failed to initialize I2C Master: {e}")
            raise
    
    def init_oled_displays(self):
        """Initialize OLED displays"""
        try:
            self.oled_manager = OLEDManager(
                mux_manager=self.mux_manager,
                width=config.SCREEN_WIDTH,
                height=config.SCREEN_HEIGHT
            )
            
            self.oled_manager.init_all_displays()
            self.oled_manager.show_startup_screen()
            
            logger.info("OLED displays initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OLED displays: {e}")
            # Continue without displays
    
    def init_gpio(self):
        """Initialize GPIO pins"""
        if not GPIO_AVAILABLE:
            logger.warning("GPIO not available - running in simulation mode")
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup button pins (input with pull-up)
            button_pins = [
                config.BTN_PRES_UP, config.BTN_PRES_DOWN,
                config.BTN_PUMP_PRIM_ON, config.BTN_PUMP_PRIM_OFF,
                config.BTN_PUMP_SEC_ON, config.BTN_PUMP_SEC_OFF,
                config.BTN_PUMP_TER_ON, config.BTN_PUMP_TER_OFF
            ]
            
            for pin in button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.state.button_states[pin] = GPIO.HIGH
                self.state.button_last_time[pin] = 0
            
            # Setup output pins (PWM for motors and buzzer)
            GPIO.setup(config.BUZZER_PIN, GPIO.OUT)
            GPIO.setup(config.MOTOR_PRIM_PWM, GPIO.OUT)
            GPIO.setup(config.MOTOR_SEC_PWM, GPIO.OUT)
            GPIO.setup(config.MOTOR_TER_PWM, GPIO.OUT)
            
            # Initialize PWM
            self.pwm_buzzer = GPIO.PWM(config.BUZZER_PIN, config.PWM_FREQUENCY)
            self.pwm_motor_prim = GPIO.PWM(config.MOTOR_PRIM_PWM, config.PWM_FREQUENCY)
            self.pwm_motor_sec = GPIO.PWM(config.MOTOR_SEC_PWM, config.PWM_FREQUENCY)
            self.pwm_motor_ter = GPIO.PWM(config.MOTOR_TER_PWM, config.PWM_FREQUENCY)
            
            self.pwm_motor_prim.start(0)
            self.pwm_motor_sec.start(0)
            self.pwm_motor_ter.start(0)
            
            logger.info("GPIO initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
    
    def init_csv_logging(self):
        """Initialize CSV data logging"""
        try:
            import csv
            self.csv_file = open(config.CSV_LOG_FILE, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header
            self.csv_writer.writerow([
                'timestamp', 'pressure', 
                'pump1_status', 'pump1_pwm',
                'pump2_status', 'pump2_pwm',
                'pump3_status', 'pump3_pwm',
                'rod1', 'rod2', 'rod3', 'kw_thermal',
                'power_level', 'esp_c_state'
            ])
            
            self.last_csv_log_time = time.time()
            logger.info("CSV logging initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize CSV logging: {e}")
            config.ENABLE_CSV_LOGGING = False
    
    # ============================================
    # Button Handling
    # ============================================
    
    def read_button(self, pin: int) -> bool:
        """
        Read button with debouncing
        
        Returns:
            True if button pressed (with debounce), False otherwise
        """
        if not GPIO_AVAILABLE:
            return False
        
        current_time = time.time()
        current_state = GPIO.input(pin)
        
        # Button pressed (LOW) and debounce time passed
        if (current_state == GPIO.LOW and 
            self.state.button_states[pin] == GPIO.HIGH and
            current_time - self.state.button_last_time[pin] > config.DEBOUNCE_DELAY):
            
            self.state.button_states[pin] = current_state
            self.state.button_last_time[pin] = current_time
            return True
        
        self.state.button_states[pin] = current_state
        return False
    
    def handle_buttons(self):
        """Handle all button inputs"""
        # Pressure control
        if self.read_button(config.BTN_PRES_UP):
            with self.state_lock:
                self.state.pressure = min(
                    self.state.pressure + config.PRESS_INCREMENT_FAST,
                    config.PRESS_MAX
                )
                logger.info(f"Pressure increased to {self.state.pressure:.1f} bar")
        
        if self.read_button(config.BTN_PRES_DOWN):
            with self.state_lock:
                self.state.pressure = max(
                    self.state.pressure - config.PRESS_INCREMENT_FAST,
                    config.PRESS_MIN
                )
                logger.info(f"Pressure decreased to {self.state.pressure:.1f} bar")
        
        # Pump Primary control
        if self.read_button(config.BTN_PUMP_PRIM_ON):
            self.start_pump(1)
        
        if self.read_button(config.BTN_PUMP_PRIM_OFF):
            self.stop_pump(1)
        
        # Pump Secondary control
        if self.read_button(config.BTN_PUMP_SEC_ON):
            self.start_pump(2)
        
        if self.read_button(config.BTN_PUMP_SEC_OFF):
            self.stop_pump(2)
        
        # Pump Tertiary control
        if self.read_button(config.BTN_PUMP_TER_ON):
            self.start_pump(3)
        
        if self.read_button(config.BTN_PUMP_TER_OFF):
            self.stop_pump(3)
    
    # ============================================
    # Pump Control
    # ============================================
    
    def start_pump(self, pump_num: int):
        """Start pump (1=Primary, 2=Secondary, 3=Tertiary)"""
        with self.state_lock:
            # Check interlock for primary pump
            if pump_num == 1 and self.state.pressure < config.PRESS_MIN_ACTIVATE_PUMP1:
                logger.warning(f"Cannot start pump {pump_num}: Pressure too low")
                return
            
            if pump_num == 1:
                if self.state.pump_primary_status == config.PUMP_OFF:
                    self.state.pump_primary_status = config.PUMP_STARTING
                    logger.info("Primary pump starting")
            elif pump_num == 2:
                if self.state.pump_secondary_status == config.PUMP_OFF:
                    self.state.pump_secondary_status = config.PUMP_STARTING
                    logger.info("Secondary pump starting")
            elif pump_num == 3:
                if self.state.pump_tertiary_status == config.PUMP_OFF:
                    self.state.pump_tertiary_status = config.PUMP_STARTING
                    logger.info("Tertiary pump starting")
    
    def stop_pump(self, pump_num: int):
        """Stop pump"""
        with self.state_lock:
            if pump_num == 1:
                if self.state.pump_primary_status == config.PUMP_ON:
                    self.state.pump_primary_status = config.PUMP_SHUTTING_DOWN
                    logger.info("Primary pump shutting down")
            elif pump_num == 2:
                if self.state.pump_secondary_status == config.PUMP_ON:
                    self.state.pump_secondary_status = config.PUMP_SHUTTING_DOWN
                    logger.info("Secondary pump shutting down")
            elif pump_num == 3:
                if self.state.pump_tertiary_status == config.PUMP_ON:
                    self.state.pump_tertiary_status = config.PUMP_SHUTTING_DOWN
                    logger.info("Tertiary pump shutting down")
    
    def update_pump_pwm(self):
        """Update PWM values based on pump status"""
        with self.state_lock:
            # Primary pump
            if self.state.pump_primary_status == config.PUMP_STARTING:
                self.state.pump_primary_pwm = min(
                    self.state.pump_primary_pwm + config.PWM_STARTUP_STEP,
                    config.PWM_MAX
                )
                if self.state.pump_primary_pwm >= config.PWM_MAX:
                    self.state.pump_primary_status = config.PUMP_ON
                    logger.info("Primary pump fully started")
            
            elif self.state.pump_primary_status == config.PUMP_SHUTTING_DOWN:
                self.state.pump_primary_pwm = max(
                    self.state.pump_primary_pwm - config.PWM_SHUTDOWN_STEP,
                    0
                )
                if self.state.pump_primary_pwm <= 0:
                    self.state.pump_primary_status = config.PUMP_OFF
                    logger.info("Primary pump fully stopped")
            
            # Secondary pump
            if self.state.pump_secondary_status == config.PUMP_STARTING:
                self.state.pump_secondary_pwm = min(
                    self.state.pump_secondary_pwm + config.PWM_STARTUP_STEP,
                    config.PWM_MAX
                )
                if self.state.pump_secondary_pwm >= config.PWM_MAX:
                    self.state.pump_secondary_status = config.PUMP_ON
                    logger.info("Secondary pump fully started")
            
            elif self.state.pump_secondary_status == config.PUMP_SHUTTING_DOWN:
                self.state.pump_secondary_pwm = max(
                    self.state.pump_secondary_pwm - config.PWM_SHUTDOWN_STEP,
                    0
                )
                if self.state.pump_secondary_pwm <= 0:
                    self.state.pump_secondary_status = config.PUMP_OFF
                    logger.info("Secondary pump fully stopped")
            
            # Tertiary pump
            if self.state.pump_tertiary_status == config.PUMP_STARTING:
                self.state.pump_tertiary_pwm = min(
                    self.state.pump_tertiary_pwm + config.PWM_STARTUP_STEP,
                    config.PWM_MAX
                )
                if self.state.pump_tertiary_pwm >= config.PWM_MAX:
                    self.state.pump_tertiary_status = config.PUMP_ON
                    logger.info("Tertiary pump fully started")
            
            elif self.state.pump_tertiary_status == config.PUMP_SHUTTING_DOWN:
                self.state.pump_tertiary_pwm = max(
                    self.state.pump_tertiary_pwm - config.PWM_SHUTDOWN_STEP,
                    0
                )
                if self.state.pump_tertiary_pwm <= 0:
                    self.state.pump_tertiary_status = config.PUMP_OFF
                    logger.info("Tertiary pump fully stopped")
        
        # Apply PWM to motors
        if GPIO_AVAILABLE:
            self.pwm_motor_prim.ChangeDutyCycle(self.state.pump_primary_pwm)
            self.pwm_motor_sec.ChangeDutyCycle(self.state.pump_secondary_pwm)
            self.pwm_motor_ter.ChangeDutyCycle(self.state.pump_tertiary_pwm)
    
    # ============================================
    # Alarm Control
    # ============================================
    
    def update_alarms(self):
        """Update alarm status based on pressure"""
        with self.state_lock:
            # Check pressure levels
            if self.state.pressure >= config.PRESS_CRITICAL_HIGH:
                self.state.critical_active = True
                self.state.warning_active = False
                
                if GPIO_AVAILABLE and not self.state.buzzer_active:
                    self.pwm_buzzer.ChangeFrequency(2000)
                    self.pwm_buzzer.start(50)
                    self.state.buzzer_active = True
                    
            elif self.state.pressure >= config.PRESS_WARNING_ABOVE:
                self.state.warning_active = True
                self.state.critical_active = False
                
                # Intermittent buzzer
                if GPIO_AVAILABLE:
                    current_time = time.time()
                    if int(current_time * 2) % 2 == 0:  # Beep every 0.5 sec
                        if not self.state.buzzer_active:
                            self.pwm_buzzer.ChangeFrequency(1000)
                            self.pwm_buzzer.start(30)
                            self.state.buzzer_active = True
                    else:
                        if self.state.buzzer_active:
                            self.pwm_buzzer.stop()
                            self.state.buzzer_active = False
            else:
                self.state.warning_active = False
                self.state.critical_active = False
                
                if GPIO_AVAILABLE and self.state.buzzer_active:
                    self.pwm_buzzer.stop()
                    self.state.buzzer_active = False
    
    # ============================================
    # I2C Communication (runs in separate thread)
    # ============================================
    
    def i2c_communication_thread(self):
        """Thread for I2C communication with ESP slaves"""
        logger.info("I2C communication thread started")
        
        last_esp_b_time = 0
        last_esp_c_time = 0
        last_esp_viz_time = 0
        
        while self.state.running:
            try:
                current_time = time.time()
                
                with self.i2c_lock:
                    # Update ESP-B (fast - 50ms)
                    if current_time - last_esp_b_time > config.I2C_UPDATE_INTERVAL_FAST:
                        success = self.i2c_master.update_esp_b(
                            self.state.pressure,
                            self.state.pump_primary_status,
                            self.state.pump_secondary_status
                        )
                        last_esp_b_time = current_time
                        
                        # Get rod positions and forward to ESP-C
                        if success:
                            esp_b_data = self.i2c_master.get_esp_b_data()
                            
                            # Update ESP-C with rod positions
                            if current_time - last_esp_c_time > config.I2C_UPDATE_INTERVAL_NORMAL:
                                self.i2c_master.update_esp_c(
                                    esp_b_data.rod1_pos,
                                    esp_b_data.rod2_pos,
                                    esp_b_data.rod3_pos
                                )
                                last_esp_c_time = current_time
                    
                    # Update visualizers (slow - 200ms)
                    if current_time - last_esp_viz_time > config.I2C_UPDATE_INTERVAL_SLOW:
                        self.i2c_master.update_esp_e(
                            self.state.pressure, 
                            self.state.pump_primary_status
                        )
                        self.i2c_master.update_esp_f(
                            self.state.pressure, 
                            self.state.pump_secondary_status
                        )
                        self.i2c_master.update_esp_g(
                            self.state.pressure, 
                            self.state.pump_tertiary_status
                        )
                        last_esp_viz_time = current_time
                
                time.sleep(0.01)  # Small sleep to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error in I2C communication thread: {e}")
                time.sleep(0.1)
        
        logger.info("I2C communication thread stopped")
    
    # ============================================
    # Display Update
    # ============================================
    
    def update_displays(self):
        """Update all OLED displays"""
        try:
            self.oled_manager.update_blink_state(config.BLINK_INTERVAL)
            
            with self.state_lock:
                self.oled_manager.update_pressurizer_display(
                    self.state.pressure,
                    self.state.warning_active,
                    self.state.critical_active
                )
                
                self.oled_manager.update_pump_primary(
                    self.state.pump_primary_status,
                    self.state.pump_primary_pwm
                )
                
                self.oled_manager.update_pump_secondary(
                    self.state.pump_secondary_status,
                    self.state.pump_secondary_pwm
                )
                
                self.oled_manager.update_pump_tertiary(
                    self.state.pump_tertiary_status,
                    self.state.pump_tertiary_pwm
                )
        except Exception as e:
            logger.error(f"Error updating displays: {e}")
    
    # ============================================
    # Data Logging
    # ============================================
    
    def log_data_csv(self):
        """Log data to CSV file"""
        if not config.ENABLE_CSV_LOGGING:
            return
        
        current_time = time.time()
        if current_time - self.last_csv_log_time < config.CSV_LOG_INTERVAL:
            return
        
        try:
            esp_b_data = self.i2c_master.get_esp_b_data()
            esp_c_data = self.i2c_master.get_esp_c_data()
            
            self.csv_writer.writerow([
                time.strftime('%Y-%m-%d %H:%M:%S'),
                f"{self.state.pressure:.1f}",
                self.state.pump_primary_status,
                self.state.pump_primary_pwm,
                self.state.pump_secondary_status,
                self.state.pump_secondary_pwm,
                self.state.pump_tertiary_status,
                self.state.pump_tertiary_pwm,
                esp_b_data.rod1_pos,
                esp_b_data.rod2_pos,
                esp_b_data.rod3_pos,
                f"{esp_b_data.kw_thermal:.1f}",
                f"{esp_c_data.power_level:.1f}",
                esp_c_data.state
            ])
            
            self.csv_file.flush()
            self.last_csv_log_time = current_time
            
        except Exception as e:
            logger.error(f"Error logging to CSV: {e}")
    
    # ============================================
    # Main Loop
    # ============================================
    
    def run(self):
        """Main control loop"""
        logger.info("Starting main control loop...")
        
        # Start I2C communication thread
        i2c_thread = threading.Thread(target=self.i2c_communication_thread, daemon=True)
        i2c_thread.start()
        
        last_pwm_update = 0
        last_display_update = 0
        
        try:
            while self.state.running:
                current_time = time.time()
                
                # Handle button inputs
                self.handle_buttons()
                
                # Update pump PWM
                if current_time - last_pwm_update > config.PWM_UPDATE_INTERVAL:
                    self.update_pump_pwm()
                    last_pwm_update = current_time
                
                # Update alarms
                self.update_alarms()
                
                # Update displays
                if current_time - last_display_update > config.OLED_UPDATE_INTERVAL:
                    self.update_displays()
                    last_display_update = current_time
                
                # Log data
                self.log_data_csv()
                
                # Small sleep
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown system gracefully"""
        logger.info("Shutting down PLTN Controller...")
        
        self.state.running = False
        time.sleep(0.5)  # Wait for threads to stop
        
        # Stop all pumps
        if GPIO_AVAILABLE:
            self.pwm_motor_prim.stop()
            self.pwm_motor_sec.stop()
            self.pwm_motor_ter.stop()
            if self.state.buzzer_active:
                self.pwm_buzzer.stop()
            GPIO.cleanup()
        
        # Close I2C
        self.i2c_master.close()
        self.mux_manager.close()
        
        # Close CSV file
        if config.ENABLE_CSV_LOGGING:
            self.csv_file.close()
        
        logger.info("PLTN Controller shutdown complete")


# ============================================
# Main Entry Point
# ============================================

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Signal received, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        controller = PLTNController()
        controller.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
