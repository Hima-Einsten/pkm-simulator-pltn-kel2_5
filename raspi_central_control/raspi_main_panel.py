"""
Main Control Program for PLTN Simulator - 2 ESP Architecture
Supports 17 buttons, humidifier control, buzzer alarm, optimized for 2 ESP32
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
from raspi_gpio_buttons import ButtonHandler as ButtonManager
from raspi_humidifier_control import HumidifierController
from raspi_buzzer_alarm import BuzzerAlarm

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
    # System control
    reactor_started: bool = False  # Sistem reaktor sudah dimulai atau belum
    
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
    
    # Humidifier commands (6 individual relays)
    humid_sg1_cmd: int = 0
    humid_sg2_cmd: int = 0
    humid_ct1_cmd: int = 0
    humid_ct2_cmd: int = 0
    humid_ct3_cmd: int = 0
    humid_ct4_cmd: int = 0
    
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
        logger.info("PLTN Simulator v3.0 - 2 ESP Architecture")
        logger.info("ESP-BC (Rods+Turbine+Humid) | ESP-E (48 LED)")
        logger.info("="*60)
        
        self.state = PanelState()
        
        # Initialize hardware components with graceful degradation
        logger.info("Phase 1: Core hardware initialization...")
        try:
            self.init_multiplexers()
            self.init_i2c_master()
            self.init_buttons()
            self.init_humidifier()
        except Exception as e:
            logger.error(f"Critical hardware initialization failed: {e}")
            logger.error("Cannot continue without core hardware")
            raise
        
        # Optional hardware with timeout (non-blocking)
        logger.info("Phase 2: Optional hardware (OLED displays)...")
        self.init_oled_displays()  # Non-blocking with timeout
        
        # Threading locks
        self.i2c_lock = threading.Lock()
        self.state_lock = threading.Lock()
        
        logger.info("="*60)
        logger.info("✓ PLTN Panel Controller initialized successfully")
        logger.info("✓ Ready for button input!")
        logger.info("="*60)
    
    def init_multiplexers(self):
        """Initialize TCA9548A multiplexers with fallback"""
        try:
            self.mux_manager = DualMultiplexerManager(
                display_bus=config.I2C_BUS_DISPLAY,
                esp_bus=config.I2C_BUS_ESP,
                display_addr=config.TCA9548A_DISPLAY_ADDRESS,
                esp_addr=config.TCA9548A_ESP_ADDRESS
            )
            logger.info("✓ Multiplexers initialized")
        except Exception as e:
            logger.warning(f"⚠️  Multiplexers unavailable: {e}")
            logger.warning("   Running in simulation mode")
            self.mux_manager = None
            raise
    
    def init_i2c_master(self):
        """Initialize I2C Master for 2 ESP communication with fallback"""
        try:
            self.i2c_master = I2CMaster(
                bus_number=config.I2C_BUS_ESP,
                mux_select_callback=self.mux_manager.select_esp_channel if self.mux_manager else None
            )
            logger.info("✓ I2C Master initialized (2 ESP)")
        except Exception as e:
            logger.warning(f"⚠️  I2C Master unavailable: {e}")
            logger.warning("   Continuing in simulation mode")
            self.i2c_master = None
            raise
    
    def init_buttons(self):
        """Initialize button manager with 17 buttons and fallback"""
        try:
            from raspi_gpio_buttons import ButtonPin
            
            self.button_manager = ButtonManager()
            
            # Register button callbacks using ButtonPin enum
            # Pressure control (2 buttons)
            self.button_manager.register_callback(ButtonPin.PRESSURE_UP, self.on_pressure_up)
            self.button_manager.register_callback(ButtonPin.PRESSURE_DOWN, self.on_pressure_down)
            
            # Pump controls (6 buttons)
            self.button_manager.register_callback(ButtonPin.PUMP_PRIMARY_ON, self.on_pump_primary_on)
            self.button_manager.register_callback(ButtonPin.PUMP_PRIMARY_OFF, self.on_pump_primary_off)
            self.button_manager.register_callback(ButtonPin.PUMP_SECONDARY_ON, self.on_pump_secondary_on)
            self.button_manager.register_callback(ButtonPin.PUMP_SECONDARY_OFF, self.on_pump_secondary_off)
            self.button_manager.register_callback(ButtonPin.PUMP_TERTIARY_ON, self.on_pump_tertiary_on)
            self.button_manager.register_callback(ButtonPin.PUMP_TERTIARY_OFF, self.on_pump_tertiary_off)
            
            # Rod controls (6 buttons)
            self.button_manager.register_callback(ButtonPin.SAFETY_ROD_UP, self.on_safety_rod_up)
            self.button_manager.register_callback(ButtonPin.SAFETY_ROD_DOWN, self.on_safety_rod_down)
            self.button_manager.register_callback(ButtonPin.SHIM_ROD_UP, self.on_shim_rod_up)
            self.button_manager.register_callback(ButtonPin.SHIM_ROD_DOWN, self.on_shim_rod_down)
            self.button_manager.register_callback(ButtonPin.REGULATING_ROD_UP, self.on_regulating_rod_up)
            self.button_manager.register_callback(ButtonPin.REGULATING_ROD_DOWN, self.on_regulating_rod_down)
            
            # System control buttons (2 buttons)
            self.button_manager.register_callback(ButtonPin.REACTOR_START, self.on_reactor_start)
            self.button_manager.register_callback(ButtonPin.REACTOR_RESET, self.on_reactor_reset)
            
            # Emergency button (1 button)
            self.button_manager.register_callback(ButtonPin.EMERGENCY, self.on_emergency)
            
            callback_count = len(self.button_manager.callbacks)
            logger.info(f"✓ Button manager initialized: {callback_count} callbacks registered")
            if callback_count != 17:
                logger.warning(f"⚠️  Expected 17 callbacks, but {callback_count} registered!")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize buttons: {e}")
            logger.warning("   Button input will not be available")
            self.button_manager = None
            raise
    
    def init_humidifier(self):
        """Initialize humidifier controller with fallback"""
        try:
            self.humidifier = HumidifierController()
            logger.info("✓ Humidifier controller initialized")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize humidifier: {e}")
            logger.warning("   Humidifier control will not be available")
            self.humidifier = None
            raise
    
    def init_oled_displays(self):
        """Initialize 9 OLED displays (0.91 inch 128x32) with timeout"""
        try:
            from raspi_oled_manager import OLEDManager
            import threading
            
            self.oled_manager = OLEDManager(
                mux_manager=self.mux_manager,
                width=128,
                height=32  # 0.91 inch OLED
            )
            
            # Initialize displays in separate thread with timeout
            logger.info("Initializing 9 OLED displays (max 5s timeout)...")
            
            def init_displays():
                try:
                    self.oled_manager.init_all_displays()
                except Exception as e:
                    logger.warning(f"OLED init error: {e}")
            
            init_thread = threading.Thread(target=init_displays, daemon=True)
            init_thread.start()
            init_thread.join(timeout=5.0)  # Max 5 seconds total
            
            if init_thread.is_alive():
                logger.warning("⚠️  OLED initialization timeout - continuing without displays")
                self.oled_manager = None
            else:
                logger.info("✓ OLED displays initialization complete")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize OLED displays: {e}")
            logger.warning("Continuing without OLED displays...")
            self.oled_manager = None
    
    # ============================================
    # Button Callbacks
    # ============================================
    
    def on_pressure_up(self):
        """Pressure UP button pressed"""
        logger.info(">>> Callback: on_pressure_up")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            self.state.pressure = min(self.state.pressure + 5.0, 200.0)
            logger.info(f"Pressure: {self.state.pressure:.1f} bar")
    
    def on_pressure_down(self):
        """Pressure DOWN button pressed"""
        logger.info(">>> Callback: on_pressure_down")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            self.state.pressure = max(self.state.pressure - 5.0, 0.0)
            logger.info(f"Pressure: {self.state.pressure:.1f} bar")
    
    def on_pump_primary_on(self):
        """Primary pump ON button"""
        logger.info(">>> Callback: on_pump_primary_on")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_primary_status == 0:  # OFF
                self.state.pump_primary_status = 1  # STARTING
                logger.info("Primary pump: STARTING")
            else:
                logger.info(f"Primary pump already in state: {self.state.pump_primary_status}")
    
    def on_pump_primary_off(self):
        """Primary pump OFF button"""
        logger.info(">>> Callback: on_pump_primary_off")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_primary_status == 2:  # ON
                self.state.pump_primary_status = 3  # SHUTTING_DOWN
                logger.info("Primary pump: SHUTTING DOWN")
            else:
                logger.info(f"Primary pump not ON (state: {self.state.pump_primary_status})")
    
    def on_pump_secondary_on(self):
        """Secondary pump ON button"""
        logger.info(">>> Callback: on_pump_secondary_on")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_secondary_status == 0:
                self.state.pump_secondary_status = 1
                logger.info("Secondary pump: STARTING")
            else:
                logger.info(f"Secondary pump already in state: {self.state.pump_secondary_status}")
    
    def on_pump_secondary_off(self):
        """Secondary pump OFF button"""
        logger.info(">>> Callback: on_pump_secondary_off")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_secondary_status == 2:
                self.state.pump_secondary_status = 3
                logger.info("Secondary pump: SHUTTING DOWN")
            else:
                logger.info(f"Secondary pump not ON (state: {self.state.pump_secondary_status})")
    
    def on_pump_tertiary_on(self):
        """Tertiary pump ON button"""
        logger.info(">>> Callback: on_pump_tertiary_on")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_tertiary_status == 0:
                self.state.pump_tertiary_status = 1
                logger.info("Tertiary pump: STARTING")
            else:
                logger.info(f"Tertiary pump already in state: {self.state.pump_tertiary_status}")
    
    def on_pump_tertiary_off(self):
        """Tertiary pump OFF button"""
        logger.info(">>> Callback: on_pump_tertiary_off")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            if self.state.pump_tertiary_status == 2:
                self.state.pump_tertiary_status = 3
                logger.info("Tertiary pump: SHUTTING DOWN")
            else:
                logger.info(f"Tertiary pump not ON (state: {self.state.pump_tertiary_status})")
    
    def on_safety_rod_up(self):
        """Safety rod UP button"""
        logger.info(">>> Callback: on_safety_rod_up")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
        if not self.check_interlock():
            logger.warning("Safety rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.safety_rod = min(self.state.safety_rod + 5, 100)
            logger.info(f"Safety rod: {self.state.safety_rod}%")
    
    def on_safety_rod_down(self):
        """Safety rod DOWN button"""
        logger.info(">>> Callback: on_safety_rod_down")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            self.state.safety_rod = max(self.state.safety_rod - 5, 0)
            logger.info(f"Safety rod: {self.state.safety_rod}%")
    
    def on_shim_rod_up(self):
        """Shim rod UP button"""
        logger.info(">>> Callback: on_shim_rod_up")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
        if not self.check_interlock():
            logger.warning("Shim rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.shim_rod = min(self.state.shim_rod + 5, 100)
            logger.info(f"Shim rod: {self.state.shim_rod}%")
    
    def on_shim_rod_down(self):
        """Shim rod DOWN button"""
        logger.info(">>> Callback: on_shim_rod_down")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            self.state.shim_rod = max(self.state.shim_rod - 5, 0)
            logger.info(f"Shim rod: {self.state.shim_rod}%")
    
    def on_regulating_rod_up(self):
        """Regulating rod UP button"""
        logger.info(">>> Callback: on_regulating_rod_up")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
        if not self.check_interlock():
            logger.warning("Regulating rod UP: Interlock not satisfied!")
            return
        
        with self.state_lock:
            self.state.regulating_rod = min(self.state.regulating_rod + 5, 100)
            logger.info(f"Regulating rod: {self.state.regulating_rod}%")
    
    def on_regulating_rod_down(self):
        """Regulating rod DOWN button"""
        logger.info(">>> Callback: on_regulating_rod_down")
        with self.state_lock:
            if not self.state.reactor_started:
                logger.warning("⚠️  Reactor not started! Press START button first.")
                return
            self.state.regulating_rod = max(self.state.regulating_rod - 5, 0)
            logger.info(f"Regulating rod: {self.state.regulating_rod}%")
    
    def on_emergency(self):
        """EMERGENCY button pressed"""
        logger.critical(">>> Callback: on_emergency - EMERGENCY SHUTDOWN!")
        with self.state_lock:
            self.state.emergency_active = True
            self.state.safety_rod = 0
            self.state.shim_rod = 0
            self.state.regulating_rod = 0
            self.state.pump_primary_status = 3  # SHUTTING_DOWN
            self.state.pump_secondary_status = 3
            self.state.pump_tertiary_status = 3
            logger.critical("EMERGENCY SHUTDOWN ACTIVATED!")
    
    def on_reactor_start(self):
        """Reactor START button - Initialize reactor system"""
        logger.info(">>> Callback: on_reactor_start")
        with self.state_lock:
            if not self.state.reactor_started:
                self.state.reactor_started = True
                logger.info("=" * 60)
                logger.info("🟢 REACTOR SYSTEM STARTED")
                logger.info("System is now operational. You may begin operations.")
                logger.info("=" * 60)
            else:
                logger.info("Reactor already started. No action taken.")
    
    def on_reactor_reset(self):
        """Reactor RESET button - Force reset simulasi ke kondisi awal"""
        logger.info(">>> Callback: on_reactor_reset (RESET SIMULASI)")
        with self.state_lock:
            # FORCE RESET - tidak perlu check kondisi, langsung reset
            self.state.reactor_started = False
            self.state.emergency_active = False
            
            # Reset semua parameter ke kondisi awal
            self.state.pressure = 0.0
            self.state.thermal_kw = 0.0
            
            # Reset pump status
            self.state.pump_primary_status = 0  # OFF
            self.state.pump_secondary_status = 0
            self.state.pump_tertiary_status = 0
            
            # Reset rod positions
            self.state.safety_rod = 0
            self.state.shim_rod = 0
            self.state.regulating_rod = 0
            
            # Reset humidifier commands
            self.state.humid_sg1_cmd = 0
            self.state.humid_sg2_cmd = 0
            self.state.humid_ct1_cmd = 0
            self.state.humid_ct2_cmd = 0
            self.state.humid_ct3_cmd = 0
            self.state.humid_ct4_cmd = 0
            
            # Reset interlock flag
            self.state.interlock_satisfied = False
            
            logger.info("=" * 60)
            logger.info("🔄 SIMULATION RESET")
            logger.info("All parameters reset to initial state.")
            logger.info("Press START button to begin new simulation.")
            logger.info("=" * 60)
    
    # ============================================
    # Interlock Logic
    # ============================================
    
    def check_interlock(self) -> bool:
        """
        Check if interlock conditions are satisfied for rod movement
        
        INTERLOCK LOGIC v3.3 (FIXED):
        Berdasarkan alur simulasi 8-phase PWR startup yang realistis:
        
        Phase 1-2: Reactor START → Raise pressure → Raise rods
        - Allow: Pressure >= 40 bar
        - Allow: Reactor started
        - Allow: No emergency
        - NO NEED: Turbine running (turbine belum jalan saat initial rod raise)
        
        Phase 3+: Normal operation
        - Same checks as above
        - Turbine akan auto-start dari ESP-BC ketika thermal > 50 MWth
        
        Returns:
            True if safe to move rods, False otherwise
        """
        with self.state_lock:
            # Check 1: Reactor must be started
            if not self.state.reactor_started:
                logger.debug("Interlock: Reactor not started")
                return False
            
            # Check 2: Pressure >= 40 bar (minimum for safe operation)
            # Pressure harus dinaikkan dulu sebelum rod movement
            if self.state.pressure < 40.0:
                logger.debug(f"Interlock: Pressure too low ({self.state.pressure:.1f} bar < 40 bar)")
                return False
            
            # Check 3: No emergency active
            if self.state.emergency_active:
                logger.debug("Interlock: Emergency shutdown active")
                return False
            
            # All checks passed - safe to move rods
            # NOTE: Tidak check turbine running karena:
            # - Turbine belum jalan saat initial rod raise (Phase 2)
            # - Turbine auto-start dari ESP-BC ketika thermal > 50 MWth (Phase 4)
            # - Pompa auto-controlled dari ESP-BC turbine state machine
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
                    # Update humidifier dengan control bertahap (v3.6)
                    sg_on, ct1, ct2, ct3, ct4 = self.humidifier.update(
                        self.state.shim_rod,
                        self.state.regulating_rod,
                        self.state.thermal_kw
                    )
                    
                    # Steam Generator: 2 humidifier (both controlled together)
                    self.state.humid_sg1_cmd = 1 if sg_on else 0
                    self.state.humid_sg2_cmd = 1 if sg_on else 0
                    
                    # Cooling Tower: 4 humidifier (STAGED 1-by-1)
                    self.state.humid_ct1_cmd = 1 if ct1 else 0
                    self.state.humid_ct2_cmd = 1 if ct2 else 0
                    self.state.humid_ct3_cmd = 1 if ct3 else 0
                    self.state.humid_ct4_cmd = 1 if ct4 else 0
                    
                    # Check and update alarm status
                    self.buzzer.check_alarms(self.state)
                
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
        logger.info("ESP communication thread started (2 ESP)")
        
        while self.state.running:
            try:
                with self.i2c_lock:
                    with self.state_lock:
                        # Send to ESP-BC (Control Rods + Turbine + Humidifier)
                        success = self.i2c_master.update_esp_bc(
                            self.state.safety_rod,
                            self.state.shim_rod,
                            self.state.regulating_rod,
                            self.state.humid_sg1_cmd,
                            self.state.humid_sg2_cmd,
                            self.state.humid_ct1_cmd,
                            self.state.humid_ct2_cmd,
                            self.state.humid_ct3_cmd,
                            self.state.humid_ct4_cmd
                        )
                        
                        if success:
                            # Get data back from ESP-BC
                            esp_bc_data = self.i2c_master.get_esp_bc_data()
                            self.state.thermal_kw = esp_bc_data.kw_thermal
                            
                            # Send to ESP-E (LED Visualizer)
                            self.i2c_master.update_esp_e(
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
                self.button_manager.check_all_buttons()
                time.sleep(0.01)  # 10ms
                
            except Exception as e:
                logger.error(f"Error in button polling thread: {e}")
                time.sleep(0.05)
        
        logger.info("Button polling thread stopped")
    
    def oled_update_thread(self):
        """Thread for updating 9 OLED displays (200ms cycle)"""
        logger.info("OLED update thread started")
        
        if self.oled_manager is None:
            logger.warning("OLED manager not available, thread exiting")
            return
        
        while self.state.running:
            try:
                with self.state_lock:
                    # Update all 9 OLED displays
                    self.oled_manager.update_all(self.state)
                
                time.sleep(0.2)  # 200ms update rate
                
            except Exception as e:
                logger.error(f"OLED update error: {e}")
                time.sleep(0.5)  # Slower retry on error
        
        logger.info("OLED update thread stopped")
    
    # ============================================
    # Main Loop
    # ============================================
    
    def run(self):
        """Main control loop"""
        logger.info("Starting PLTN Controller (2 ESP)...")
        
        # Start threads
        threads = [
            threading.Thread(target=self.button_polling_thread, daemon=True, name="ButtonThread"),
            threading.Thread(target=self.control_logic_thread, daemon=True, name="ControlThread"),
            threading.Thread(target=self.esp_communication_thread, daemon=True, name="ESPCommThread"),
            threading.Thread(target=self.oled_update_thread, daemon=True, name="OLEDThread")  # New thread
        ]
        
        for t in threads:
            t.start()
            logger.info(f"Thread started: {t.name}")
        
        try:
            while self.state.running:
                time.sleep(1.0)
                
                # Print status every second
                with self.state_lock:
                    # Get turbine data from ESP-BC
                    esp_bc_data = self.i2c_master.get_esp_bc_data()
                    
                    logger.info(f"Status: P={self.state.pressure:.1f}bar, "
                              f"Rods=[{self.state.safety_rod},{self.state.shim_rod},"
                              f"{self.state.regulating_rod}]%, "
                              f"Thermal={self.state.thermal_kw:.1f}kW, "
                              f"Turbine={esp_bc_data.power_level:.1f}%, "
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
