"""
Main Control Program for PLTN Simulator - Panel Control Version
Supports 15 buttons, 9 OLEDs, humidifier control, and new ESP protocols
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
from raspi_gpio_buttons import ButtonManager
from raspi_humidifier_control import HumidifierController

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
class PanelState:
    """Panel control system state"""
    # Pressure control
    pressure: float = 0.0
    
    # Pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
    pump_primary_status: int = 0
    pump_secondary_status: int = 0
    pump_tertiary_status: int = 0
    
    # Rod positions (0-100%)
    safety_rod: int = 0
    shim_rod: int = 0
    regulating_rod: int = 0
    
    # Thermal power from ESP-B
    thermal_kw: float = 0.0
    
    # Humidifier commands
    humidifier_sg_cmd: int = 0
    humidifier_ct_cmd: int = 0
    
    # Emergency state
    emergency_active: bool = False
    
    # Interlock satisfied flag
    interlock_satisfied: bool = False
    
    # System running flag
    running: bool = True


class PLTNPanelController:
    """
    Main PLTN Panel Controller Class
    Manages 15 buttons, 9 OLEDs, humidifier control
    """
    
    def __init__(self):
        """Initialize PLTN Panel Controller"""
        logger.info("="*60)
        logger.info("PLTN Simulator v2.5 - Panel Control System")
        logger.info("15 Buttons | 9 OLEDs | Humidifier Control")
        logger.info("="*60)
        
        self.state = PanelState()
        
        # Initialize hardware components
        self.init_multiplexers()
        self.init_i2c_master()
        self.init_buttons()
        self.init_humidifier()
        
        # Threading locks
        self.i2c_lock = threading.Lock()
        self.state_lock = threading.Lock()
        
        logger.info("PLTN Panel Controller initialized successfully")
    
    def init_multiplexers(self):
        """Initialize TCA9548A multiplexers"""
        try:
            self.mux_manager = DualMultiplexerManager(
                display_bus=config.I2C_BUS_DISPLAY,
                esp_bus=config.I2C_BUS_ESP,
                display_addr=config.TCA9548A_DISPLAY_ADDRESS,
                esp_addr=config.TCA9548A_ESP_ADDRESS
            )
            logger.info("Multiplexers initialized")
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
    
    def init_buttons(self):
        """Initialize button manager with 15 buttons"""
        try:
            self.button_manager = ButtonManager()
            
            # Register button callbacks
            # Pressure control
            self.button_manager.register_callback("PRES_UP", self.on_pressure_up)
            self.button_manager.register_callback("PRES_DOWN", self.on_pressure_down)
            
            # Pump controls
            self.button_manager.register_callback("PUMP_PRIM_ON", self.on_pump_primary_on)
            self.button_manager.register_callback("PUMP_PRIM_OFF", self.on_pump_primary_off)
            self.button_manager.register_callback("PUMP_SEC_ON", self.on_pump_secondary_on)
            self.button_manager.register_callback("PUMP_SEC_OFF", self.on_pump_secondary_off)
            self.button_manager.register_callback("PUMP_TER_ON", self.on_pump_tertiary_on)
            self.button_manager.register_callback("PUMP_TER_OFF", self.on_pump_tertiary_off)
            
            # Rod controls
            self.button_manager.register_callback("SAFETY_UP", self.on_safety_rod_up)
            self.button_manager.register_callback("SAFETY_DOWN", self.on_safety_rod_down)
            self.button_manager.register_callback("SHIM_UP", self.on_shim_rod_up)
            self.button_manager.register_callback("SHIM_DOWN", self.on_shim_rod_down)
            self.button_manager.register_callback("REG_UP", self.on_regulating_rod_up)
            self.button_manager.register_callback("REG_DOWN", self.on_regulating_rod_down)
            
            # Emergency button
            self.button_manager.register_callback("EMERGENCY", self.on_emergency)
            
            logger.info("Button manager initialized with 15 buttons")
        except Exception as e:
            logger.error(f"Failed to initialize buttons: {e}")
            raise
    
    def init_humidifier(self):
        """Initialize humidifier controller"""
        try:
            self.humidifier = HumidifierController()
            logger.info("Humidifier controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize humidifier: {e}")
            raise
    
    # ============================================
    # Button Callbacks
    # ============================================
    
    def on_pressure_up(self):
        """Pressure UP button pressed"""
        with self.state_lock:
            self.state.pressure = min(self.state.pressure + 5.0, 200.0)
            logger.info(f"Pressure: {self.state.pressure:.1f} bar")
    
    def on_pressure_down(self):
        """Pressure DOWN button pressed"""
        with self.state_lock:
            self.state.pressure = max(self.state.pressure - 5.0, 0.0)
            logger.info(f"Pressure: {self.state.pressure:.1f} bar")
    
    def on_pump_primary_on(self):
        """Primary pump ON button"""
        with self.state_lock:
            if self.state.pump_primary_status == 0:  # OFF
                self.state.pump_primary_status = 1  # STARTING
                logger.info("Primary pump: STARTING")
    
    def on_pump_primary_off(self):
        """Primary pump OFF button"""
        with self.state_lock:
            if self.state.pump_primary_status == 2:  # ON
                self.state.pump_primary_status = 3  # SHUTTING_DOWN
                logger.info("Primary pump: SHUTTING DOWN")
    
    def on_pump_secondary_on(self):
        """Secondary pump ON button"""
        with self.state_lock:
            if self.state.pump_secondary_status == 0:
                self.state.pump_secondary_status = 1
                logger.info("Secondary pump: STARTING")
    
    def on_pump_secondary_off(self):
        """Secondary pump OFF button"""
        with self.state_lock:
            if self.state.pump_secondary_status == 2:
                self.state.pump_secondary_status = 3
                logger.info("Secondary pump: SHUTTING DOWN")
    
    def on_pump_tertiary_on(self):
        """Tertiary pump ON button"""
        with self.state_lock:
            if self.state.pump_tertiary_status == 0:
                self.state.pump_tertiary_status = 1
                logger.info("Tertiary pump: STARTING")
    
    def on_pump_tertiary_off(self):
        """Tertiary pump OFF button"""
        with self.state_lock:
            if self.state.pump_tertiary_status == 2:
                self.state.pump_tertiary_status = 3
                logger.info("Tertiary pump: SHUTTING DOWN")
    
    def on_safety_rod_up(self):
        """Safety rod UP button"""
        if not self.check_interlock():
            logger.warning("Safety rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.safety_rod = min(self.state.safety_rod + 5, 100)
            logger.info(f"Safety rod: {self.state.safety_rod}%")
    
    def on_safety_rod_down(self):
        """Safety rod DOWN button"""
        with self.state_lock:
            self.state.safety_rod = max(self.state.safety_rod - 5, 0)
            logger.info(f"Safety rod: {self.state.safety_rod}%")
    
    def on_shim_rod_up(self):
        """Shim rod UP button"""
        if not self.check_interlock():
            logger.warning("Shim rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.shim_rod = min(self.state.shim_rod + 5, 100)
            logger.info(f"Shim rod: {self.state.shim_rod}%")
    
    def on_shim_rod_down(self):
        """Shim rod DOWN button"""
        with self.state_lock:
            self.state.shim_rod = max(self.state.shim_rod - 5, 0)
            logger.info(f"Shim rod: {self.state.shim_rod}%")
    
    def on_regulating_rod_up(self):
        """Regulating rod UP button"""
        if not self.check_interlock():
            logger.warning("Regulating rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.regulating_rod = min(self.state.regulating_rod + 5, 100)
            logger.info(f"Regulating rod: {self.state.regulating_rod}%")
    
    def on_regulating_rod_down(self):
        """Regulating rod DOWN button"""
        with self.state_lock:
            self.state.regulating_rod = max(self.state.regulating_rod - 5, 0)
            logger.info(f"Regulating rod: {self.state.regulating_rod}%")
    
    def on_emergency(self):
        """EMERGENCY button pressed"""
        with self.state_lock:
            self.state.emergency_active = True
            self.state.safety_rod = 0
            self.state.shim_rod = 0
            self.state.regulating_rod = 0
            self.state.pump_primary_status = 3  # SHUTTING_DOWN
            self.state.pump_secondary_status = 3
            self.state.pump_tertiary_status = 3
            logger.critical("EMERGENCY SHUTDOWN ACTIVATED!")
    
    # ============================================
    # Interlock Logic
    # ============================================
    
    def check_interlock(self) -> bool:
        """
        Check if interlock conditions are satisfied for rod movement
        
        Returns:
            True if safe to move rods, False otherwise
        """
        with self.state_lock:
            # Check pressure >= 40 bar
            if self.state.pressure < 40.0:
                return False
            
            # Check primary pump ON
            if self.state.pump_primary_status != 2:
                return False
            
            # Check secondary pump ON
            if self.state.pump_secondary_status != 2:
                return False
            
            # Check no emergency
            if self.state.emergency_active:
                return False
            
            return True
    
    # ============================================
    # Control Logic Thread
    # ============================================
    
    def control_logic_thread(self):
        """Thread for control logic (50ms cycle)"""
        logger.info("Control logic thread started")
        
        while self.state.running:
            try:
                # Update interlock status
                with self.state_lock:
                    self.state.interlock_satisfied = self.check_interlock()
                
                # Update humidifier commands
                with self.state_lock:
                    sg_on, ct_on = self.humidifier.update(
                        self.state.shim_rod,
                        self.state.regulating_rod,
                        self.state.thermal_kw
                    )
                    self.state.humidifier_sg_cmd = 1 if sg_on else 0
                    self.state.humidifier_ct_cmd = 1 if ct_on else 0
                
                # Simulate pump startup/shutdown
                self.update_pump_status()
                
                time.sleep(0.05)  # 50ms
                
            except Exception as e:
                logger.error(f"Error in control logic thread: {e}")
                time.sleep(0.1)
        
        logger.info("Control logic thread stopped")
    
    def update_pump_status(self):
        """Update pump status (simulate startup/shutdown)"""
        with self.state_lock:
            # Primary pump
            if self.state.pump_primary_status == 1:  # STARTING
                time.sleep(2.0)  # Simulate startup delay
                self.state.pump_primary_status = 2  # ON
                logger.info("Primary pump: ON")
            elif self.state.pump_primary_status == 3:  # SHUTTING_DOWN
                time.sleep(1.0)
                self.state.pump_primary_status = 0  # OFF
                logger.info("Primary pump: OFF")
            
            # Secondary pump
            if self.state.pump_secondary_status == 1:
                time.sleep(2.0)
                self.state.pump_secondary_status = 2
                logger.info("Secondary pump: ON")
            elif self.state.pump_secondary_status == 3:
                time.sleep(1.0)
                self.state.pump_secondary_status = 0
                logger.info("Secondary pump: OFF")
            
            # Tertiary pump
            if self.state.pump_tertiary_status == 1:
                time.sleep(2.0)
                self.state.pump_tertiary_status = 2
                logger.info("Tertiary pump: ON")
            elif self.state.pump_tertiary_status == 3:
                time.sleep(1.0)
                self.state.pump_tertiary_status = 0
                logger.info("Tertiary pump: OFF")
    
    # ============================================
    # ESP Communication Thread
    # ============================================
    
    def esp_communication_thread(self):
        """Thread for ESP communication (100ms cycle)"""
        logger.info("ESP communication thread started")
        
        while self.state.running:
            try:
                with self.i2c_lock:
                    with self.state_lock:
                        # Send rod targets to ESP-B
                        success = self.i2c_master.send_rod_targets_to_esp_b(
                            self.state.safety_rod,
                            self.state.shim_rod,
                            self.state.regulating_rod
                        )
                        
                        if success:
                            # Get ESP-B data
                            esp_b_data = self.i2c_master.get_esp_b_data()
                            self.state.thermal_kw = esp_b_data.kw_thermal
                            
                            # Send to ESP-C with humidifier commands
                            self.i2c_master.send_to_esp_c_with_humidifier(
                                esp_b_data.safety_actual,
                                esp_b_data.shim_actual,
                                esp_b_data.regulating_actual,
                                esp_b_data.kw_thermal,
                                self.state.humidifier_sg_cmd,
                                self.state.humidifier_ct_cmd
                            )
                            
                            # Send to ESP-E (visualizer)
                            self.i2c_master.update_all_visualizers(
                                pressure_primary=self.state.pressure,
                                pump_status_primary=self.state.pump_primary_status,
                                pressure_secondary=self.state.pressure * 0.35,
                                pump_status_secondary=self.state.pump_secondary_status,
                                pressure_tertiary=self.state.pressure * 0.10,
                                pump_status_tertiary=self.state.pump_tertiary_status
                            )
                
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                logger.error(f"Error in ESP communication thread: {e}")
                time.sleep(0.2)
        
        logger.info("ESP communication thread stopped")
    
    # ============================================
    # Button Polling Thread
    # ============================================
    
    def button_polling_thread(self):
        """Thread for button polling (10ms cycle)"""
        logger.info("Button polling thread started")
        
        while self.state.running:
            try:
                self.button_manager.poll()
                time.sleep(0.01)  # 10ms
                
            except Exception as e:
                logger.error(f"Error in button polling thread: {e}")
                time.sleep(0.05)
        
        logger.info("Button polling thread stopped")
    
    # ============================================
    # Main Loop
    # ============================================
    
    def run(self):
        """Main control loop"""
        logger.info("Starting PLTN Panel Controller...")
        
        # Start threads
        threads = [
            threading.Thread(target=self.button_polling_thread, daemon=True),
            threading.Thread(target=self.control_logic_thread, daemon=True),
            threading.Thread(target=self.esp_communication_thread, daemon=True)
        ]
        
        for t in threads:
            t.start()
        
        try:
            while self.state.running:
                time.sleep(1.0)
                
                # Print status every second
                with self.state_lock:
                    logger.info(f"Status: P={self.state.pressure:.1f}bar, "
                              f"Rods=[{self.state.safety_rod},{self.state.shim_rod},"
                              f"{self.state.regulating_rod}]%, "
                              f"Thermal={self.state.thermal_kw:.1f}kW, "
                              f"Humid=[SG:{self.state.humidifier_sg_cmd},"
                              f"CT:{self.state.humidifier_ct_cmd}]")
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown system gracefully"""
        logger.info("Shutting down PLTN Panel Controller...")
        
        self.state.running = False
        time.sleep(0.5)
        
        self.button_manager.cleanup()
        self.i2c_master.close()
        self.mux_manager.close()
        
        logger.info("PLTN Panel Controller shutdown complete")


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
        controller = PLTNPanelController()
        controller.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
