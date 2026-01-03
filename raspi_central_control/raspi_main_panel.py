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
from queue import Queue, Empty
from enum import Enum

# Import our modules
import raspi_config as config
from raspi_tca9548a import DualMultiplexerManager
from raspi_uart_master import UARTMaster  # UART instead of I2C
from raspi_gpio_buttons import ButtonHandler as ButtonManager, ButtonPin
from raspi_humidifier_control import HumidifierController
from raspi_buzzer_alarm import BuzzerAlarm
from raspi_system_health import SystemHealthMonitor

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


# ============================================
# Button Event Enum
# ============================================

class ButtonEvent(Enum):
    """Button event types for queue-based processing"""
    PRESSURE_UP = "PRESSURE_UP"
    PRESSURE_DOWN = "PRESSURE_DOWN"
    PUMP_PRIMARY_ON = "PUMP_PRIMARY_ON"
    PUMP_PRIMARY_OFF = "PUMP_PRIMARY_OFF"
    PUMP_SECONDARY_ON = "PUMP_SECONDARY_ON"
    PUMP_SECONDARY_OFF = "PUMP_SECONDARY_OFF"
    PUMP_TERTIARY_ON = "PUMP_TERTIARY_ON"
    PUMP_TERTIARY_OFF = "PUMP_TERTIARY_OFF"
    SAFETY_ROD_UP = "SAFETY_ROD_UP"
    SAFETY_ROD_DOWN = "SAFETY_ROD_DOWN"
    SHIM_ROD_UP = "SHIM_ROD_UP"
    SHIM_ROD_DOWN = "SHIM_ROD_DOWN"
    REGULATING_ROD_UP = "REGULATING_ROD_UP"
    REGULATING_ROD_DOWN = "REGULATING_ROD_DOWN"
    REACTOR_START = "REACTOR_START"
    REACTOR_RESET = "REACTOR_RESET"
    EMERGENCY = "EMERGENCY"
    START_AUTO_SIMULATION = "START_AUTO_SIMULATION"  # NEW: Start auto mode


@dataclass
class PanelState:
    """Panel control system state"""
    # System control
    reactor_started: bool = False  # Sistem reaktor sudah dimulai atau belum
    
    # Simulation mode: 'manual' atau 'auto'
    simulation_mode: str = 'manual'  # Default: manual mode
    auto_sim_running: bool = False   # Flag untuk auto simulation berjalan
    auto_sim_step: int = 0           # Langkah simulasi otomatis saat ini
    
    # Pressure control
    pressure: float = 0.0
    
    # Pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
    pump_primary_status: int = 0
    pump_secondary_status: int = 0
    pump_tertiary_status: int = 0
    
    # Pump transition timers (untuk tracking waktu startup/shutdown)
    pump_primary_transition_start: float = 0.0
    pump_secondary_transition_start: float = 0.0
    pump_tertiary_transition_start: float = 0.0
    
    # Rod positions (0-100%)
    safety_rod: int = 0
    shim_rod: int = 0
    regulating_rod: int = 0
    
    # Thermal power from ESP-B
    thermal_kw: float = 0.0
    
    # Turbine speed from ESP-BC
    turbine_speed: float = 0.0
    
    
    # Humidifier commands (Cooling Tower only - 4 relays)
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
    Uses event queue pattern for button handling
    """
    
    def __init__(self):
        """Initialize PLTN Panel Controller"""
        logger.info("="*60)
        logger.info("PLTN Simulator v3.3 - Event Queue Pattern")
        logger.info("ESP-BC (Rods+Turbine+Humid) | ESP-E (48 LED)")
        logger.info("="*60)
        
        self.state = PanelState()
        
        # Event queue for button presses (non-blocking)
        self.button_event_queue = Queue(maxsize=100)
        
        # Flag for immediate ESP communication (bypass cycle wait)
        self.esp_send_immediate = threading.Event()
        
        # Initialize hardware components with graceful degradation
        logger.info("Phase 1: Core hardware initialization...")
        try:
            self.init_multiplexers()
            self.init_uart_master()  # Changed from init_i2c_master
            self.init_buttons()
        except Exception as e:
            logger.error(f"Critical hardware initialization failed: {e}")
            logger.error("Cannot continue without core hardware")
            raise
        
        # Optional hardware (can fail without stopping system)
        logger.info("Phase 1b: Optional hardware initialization...")
        self.init_humidifier()  # Won't raise
        self.init_buzzer()  # Won't raise
        
        # Optional hardware with timeout (non-blocking)
        logger.info("Phase 2: Optional hardware (OLED displays)...")
        self.init_oled_displays()  # Non-blocking with timeout
        
        # Threading locks
        self.uart_lock = threading.Lock()  # Changed from i2c_lock
        self.state_lock = threading.Lock()
        
        # System health monitor
        logger.info("Phase 3: System health check...")
        self.health_monitor = SystemHealthMonitor()
        system_ready = self.health_monitor.check_all(self)
        
        if not system_ready:
            logger.error("="*60)
            logger.error("⚠️  SYSTEM NOT READY - Critical issues detected!")
            logger.error("   Review health check above and fix critical issues")
            logger.error("   System will continue in degraded mode")
            logger.error("="*60)
        
        logger.info("="*60)
        logger.info("✓ PLTN Panel Controller initialized")
        if system_ready:
            logger.info("✅ SYSTEM READY - All critical components operational")
        else:
            logger.warning("⚠️  SYSTEM DEGRADED - Some components unavailable")
        logger.info("="*60)
    
    def init_multiplexers(self):
        """Initialize TCA9548A multiplexers (for OLEDs only now)"""
        try:
            self.mux_manager = DualMultiplexerManager(
                display_bus=config.I2C_BUS_DISPLAY,
                esp_bus=config.I2C_BUS_DISPLAY,  # Both on same bus now (OLEDs only)
                display_addr=config.TCA9548A_DISPLAY_ADDRESS,
                esp_addr=config.TCA9548A_ESP_ADDRESS
            )
            logger.info("✓ Multiplexers initialized (OLEDs only)")
        except Exception as e:
            logger.warning(f"⚠️  Multiplexers unavailable: {e}")
            logger.warning("   OLED displays will not work")
            self.mux_manager = None
            # Don't raise - OLEDs are optional
    
    def init_uart_master(self):
        """Initialize UART Master for 2 ESP communication"""
        try:
            self.uart_master = UARTMaster(
                esp_bc_port=config.UART_ESP_BC_PORT,
                esp_e_port=config.UART_ESP_E_PORT,
                baudrate=config.UART_BAUDRATE
            )
            logger.info("✓ UART Master initialized (2 ESP via Serial)")
        except Exception as e:
            logger.error(f"❌ UART Master unavailable: {e}")
            logger.error("   ESPs will not work!")
            self.uart_master = None
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
            
            # System control buttons (3 buttons) - UPDATED: Added AUTO_SIMULATION
            self.button_manager.register_callback(ButtonPin.REACTOR_START, self.on_reactor_start)
            self.button_manager.register_callback(ButtonPin.REACTOR_RESET, self.on_reactor_reset)
            self.button_manager.register_callback(ButtonPin.START_AUTO_SIMULATION, self.on_start_auto_simulation)
            
            # Emergency button (1 button)
            self.button_manager.register_callback(ButtonPin.EMERGENCY, self.on_emergency)
            
            callback_count = len(self.button_manager.callbacks)
            logger.info(f"✓ Button manager initialized: {callback_count} callbacks registered")
            if callback_count != 18:
                logger.warning(f"⚠️  Expected 18 callbacks, but {callback_count} registered!")
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
            logger.error(f"❌ Failed to initialize humidifier: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("   Humidifier control will not be available")
            self.humidifier = None
            # Don't raise - make it non-critical
    
    def init_buzzer(self):
        """Initialize buzzer alarm system"""
        try:
            self.buzzer = BuzzerAlarm()
            logger.info("✓ Buzzer alarm initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize buzzer: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("   Alarm buzzer will not be available")
            self.buzzer = None
            # Don't raise - make it non-critical
    
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
    # Lightweight Button Callbacks (NO LOCK, NO HEAVY WORK)
    # ============================================
    
    def on_pressure_up(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PRESSURE_UP)
        logger.info("⚡ Button event queued: PRESSURE_UP")
    
    def on_pressure_down(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PRESSURE_DOWN)
        logger.info("⚡ Button event queued: PRESSURE_DOWN")
    
    def on_pump_primary_on(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_PRIMARY_ON)
        logger.info("⚡ Button event queued: PUMP_PRIMARY_ON")
    
    def on_pump_primary_off(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_PRIMARY_OFF)
        logger.info("⚡ Button event queued: PUMP_PRIMARY_OFF")
    
    def on_pump_secondary_on(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_SECONDARY_ON)
        logger.info("⚡ Button event queued: PUMP_SECONDARY_ON")
    
    def on_pump_secondary_off(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_SECONDARY_OFF)
        logger.info("⚡ Button event queued: PUMP_SECONDARY_OFF")
    
    def on_pump_tertiary_on(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_TERTIARY_ON)
        logger.info("⚡ Button event queued: PUMP_TERTIARY_ON")
    
    def on_pump_tertiary_off(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.PUMP_TERTIARY_OFF)
        logger.info("⚡ Button event queued: PUMP_TERTIARY_OFF")
    
    def on_safety_rod_up(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.SAFETY_ROD_UP)
        logger.info("⚡ Button event queued: SAFETY_ROD_UP")
    
    def on_safety_rod_down(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.SAFETY_ROD_DOWN)
        logger.info("⚡ Button event queued: SAFETY_ROD_DOWN")
    
    def on_shim_rod_up(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.SHIM_ROD_UP)
        logger.info("⚡ Event queued: SHIM_ROD_UP")
    
    def on_shim_rod_down(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.SHIM_ROD_DOWN)
        logger.info("⚡ Button event queued: SHIM_ROD_DOWN")
    
    def on_regulating_rod_up(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.REGULATING_ROD_UP)
        logger.info("⚡ Button event queued: REGULATING_ROD_UP")
    
    def on_regulating_rod_down(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.REGULATING_ROD_DOWN)
        logger.info("⚡ Button event queued: REGULATING_ROD_DOWN")
    
    def on_emergency(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.EMERGENCY)
        logger.critical("⚡ Button event queued: EMERGENCY")
    
    def on_reactor_start(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.REACTOR_START)
        logger.info("⚡ Event queued: REACTOR_START")
    
    def on_reactor_reset(self):
        """Lightweight callback - just enqueue event"""
        self.button_event_queue.put(ButtonEvent.REACTOR_RESET)
        logger.info("⚡ Button event queued: REACTOR_RESET")
    
    def on_start_auto_simulation(self):
        """Lightweight callback - start auto simulation"""
        self.button_event_queue.put(ButtonEvent.START_AUTO_SIMULATION)
        logger.info("⚡ Event queued: START_AUTO_SIMULATION")
    
    
    # ============================================
    # Event Processing (Heavy Work with Lock)
    # ============================================
    
    def process_button_event(self, event: ButtonEvent):
        """
        Process button event with proper locking and state update
        This runs in dedicated thread, NOT in interrupt context
        """
        with self.state_lock:
            
            if event == ButtonEvent.PRESSURE_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.pressure = min(self.state.pressure + 1.0, 200.0)  # 1 bar increment
                logger.info(f"✓ Pressure UP: {self.state.pressure:.1f} bar")
            
            elif event == ButtonEvent.PRESSURE_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.pressure = max(self.state.pressure - 1.0, 0.0)  # 1 bar decrement
                logger.info(f"✓ Pressure DOWN: {self.state.pressure:.1f} bar")
            
            elif event == ButtonEvent.PUMP_PRIMARY_ON:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_primary_status == 0:
                    self.state.pump_primary_status = 1
                    logger.info("✓ Primary pump: STARTING")
            
            elif event == ButtonEvent.PUMP_PRIMARY_OFF:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_primary_status == 2:
                    self.state.pump_primary_status = 3
                    logger.info("✓ Primary pump: SHUTTING DOWN")
            
            elif event == ButtonEvent.PUMP_SECONDARY_ON:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_secondary_status == 0:
                    self.state.pump_secondary_status = 1
                    logger.info("✓ Secondary pump: STARTING")
            
            elif event == ButtonEvent.PUMP_SECONDARY_OFF:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_secondary_status == 2:
                    self.state.pump_secondary_status = 3
                    logger.info("✓ Secondary pump: SHUTTING DOWN")
            
            elif event == ButtonEvent.PUMP_TERTIARY_ON:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_tertiary_status == 0:
                    self.state.pump_tertiary_status = 1
                    logger.info("✓ Tertiary pump: STARTING")
            
            elif event == ButtonEvent.PUMP_TERTIARY_OFF:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if self.state.pump_tertiary_status == 2:
                    self.state.pump_tertiary_status = 3
                    logger.info("✓ Tertiary pump: SHUTTING DOWN")
            
            elif event == ButtonEvent.SAFETY_ROD_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if not self._check_interlock_internal():
                    logger.warning("⚠️  Interlock not satisfied!")
                    return
                self.state.safety_rod = min(self.state.safety_rod + 1, 100)  # 1% increment
                logger.info(f"✓ Safety rod UP: {self.state.safety_rod}%")
            
            elif event == ButtonEvent.SAFETY_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return

                # Safety rod hanya bisa turun jika shim dan regulating sudah 0%
                if self.state.shim_rod > 0 or self.state.regulating_rod > 0:
                    logger.warning("⚠️  Cannot lower Safety Rod! Lower Shim & Regulating first!")
                    # Trigger buzzer warning if available
                    if self.buzzer:
                        try:
                            self.buzzer.beep(duration=0.2)
                        except Exception:
                            logger.debug("Buzzer beep failed")
                    return

                self.state.safety_rod = max(self.state.safety_rod - 1, 0)  # 1% decrement
                logger.info(f"✓ Safety rod DOWN: {self.state.safety_rod}%")
            
            elif event == ButtonEvent.SHIM_ROD_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if not self._check_interlock_internal():
                    logger.warning("⚠️  Interlock not satisfied!")
                    return
                self.state.shim_rod = min(self.state.shim_rod + 1, 100)  # 1% increment
                logger.info(f"✓ Shim rod UP: {self.state.shim_rod}%")
            
            elif event == ButtonEvent.SHIM_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.shim_rod = max(self.state.shim_rod - 1, 0)  # 1% decrement
                logger.info(f"✓ Shim rod DOWN: {self.state.shim_rod}%")
            
            elif event == ButtonEvent.REGULATING_ROD_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if not self._check_interlock_internal():
                    logger.warning("⚠️  Interlock not satisfied!")
                    return
                self.state.regulating_rod = min(self.state.regulating_rod + 1, 100)  # 1% increment
                logger.info(f"✓ Regulating rod UP: {self.state.regulating_rod}%")
            
            elif event == ButtonEvent.REGULATING_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.regulating_rod = max(self.state.regulating_rod - 1, 0)  # 1% decrement
                logger.info(f"✓ Regulating rod DOWN: {self.state.regulating_rod}%")
            
            elif event == ButtonEvent.EMERGENCY:
                self.state.emergency_active = True
                self.state.safety_rod = 0
                self.state.shim_rod = 0
                self.state.regulating_rod = 0
                self.state.pump_primary_status = 3
                self.state.pump_secondary_status = 3
                self.state.pump_tertiary_status = 3
                logger.critical("✓ EMERGENCY SHUTDOWN ACTIVATED!")
            
            elif event == ButtonEvent.REACTOR_START:
                if not self.state.reactor_started:
                    self.state.reactor_started = True
                    logger.info("=" * 60)
                    logger.info("🟢 REACTOR SYSTEM STARTED")
                    logger.info("System is now operational.")
                    logger.info("=" * 60)
            
            elif event == ButtonEvent.REACTOR_RESET:
                # Stop auto simulation if running
                self.state.auto_sim_running = False
                self.state.simulation_mode = 'manual'
                
                self.state.reactor_started = False
                self.state.emergency_active = False
                self.state.pressure = 0.0
                self.state.thermal_kw = 0.0
                self.state.pump_primary_status = 0
                self.state.pump_secondary_status = 0
                self.state.pump_tertiary_status = 0
                self.state.pump_primary_transition_start = 0.0
                self.state.pump_secondary_transition_start = 0.0
                self.state.pump_tertiary_transition_start = 0.0
                self.state.safety_rod = 0
                self.state.shim_rod = 0
                self.state.regulating_rod = 0
                self.state.humid_ct1_cmd = 0
                self.state.humid_ct2_cmd = 0
                self.state.humid_ct3_cmd = 0
                self.state.humid_ct4_cmd = 0
                self.state.interlock_satisfied = False
                logger.info("=" * 60)
                logger.info("🔄 SIMULATION RESET")
                logger.info("All parameters reset. Press START to begin.")
                logger.info("=" * 60)
            
            elif event == ButtonEvent.START_AUTO_SIMULATION:
                if self.state.auto_sim_running:
                    logger.warning("⚠️  Auto simulation already running!")
                    return
                if self.state.reactor_started:
                    logger.warning("⚠️  Reactor already started! Reset first for auto mode.")
                    return
                
                # Start auto simulation
                self.state.reactor_started = True  # Auto-start reactor
                self.state.simulation_mode = 'auto'
                self.state.auto_sim_running = True
                logger.info("=" * 60)
                logger.info("🤖 AUTO SIMULATION MODE ACTIVATED")
                logger.info("Simulasi akan berjalan otomatis dengan kecepatan lambat")
                logger.info("untuk memudahkan pemahaman cara kerja PLTN")
                logger.info("=" * 60)
            
            # Log if event not recognized
            else:
                logger.warning(f"⚠️  Unknown event: {event}")
    
    def button_event_processor_thread(self):
        """
        Process button events from queue
        This thread can safely use locks and do heavy work
        """
        try:
            logger.info("🚀 Button event processor thread STARTING...")
            
            # Verify queue exists
            if not hasattr(self, 'button_event_queue'):
                logger.error("❌ button_event_queue not initialized!")
                return
            
            logger.info(f"✓ Event queue initialized (max size: 100)")
            logger.info("✓ Button event processor thread started - waiting for events...")
            
            loop_count = 0
            while self.state.running:
                try:
                    # Heartbeat every 10 seconds
                    loop_count += 1
                    if loop_count >= 100:  # 100 * 0.1s = 10s
                        logger.info(f"💓 Event processor alive - Queue size: {self.button_event_queue.qsize()}")
                        loop_count = 0
                    
                    # Wait for event (blocking, with timeout) - optimized to 10ms for fast response
                    event = self.button_event_queue.get(timeout=0.01)
                    
                    logger.info(f"🔹 Processing: {event.value}")
                    
                    # Process event with lock
                    self.process_button_event(event)
                    
                    # Trigger immediate ESP communication for fast response
                    self.esp_send_immediate.set()
                    
                    # Mark task done
                    self.button_event_queue.task_done()
                    
                except Empty:
                    # No events, continue loop
                    pass
                except Exception as e:
                    logger.error(f"Event processor error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            logger.info("Button event processor thread stopped")
            
        except Exception as e:
            logger.critical(f"❌ FATAL: Event processor thread crashed on startup: {e}")
            import traceback
            logger.critical(traceback.format_exc())
    
    # ============================================
    # Interlock Logic
    # ============================================
    
    def check_interlock(self) -> bool:
        """
        Check if interlock conditions are satisfied for rod movement
        PUBLIC version - acquires lock
        
        Returns:
            True if safe to move rods, False otherwise
        """
        with self.state_lock:
            return self._check_interlock_internal()
    
    def _check_interlock_internal(self) -> bool:
        """
        Check if interlock conditions are satisfied for rod movement
        INTERNAL version - assumes caller already holds state_lock
        
        INTERLOCK LOGIC v3.3 (FIXED):
        Berdasarkan alur simulasi 8-phase PWR startup yang realistis:
        
        Phase 1-2: Reactor START → Raise pressure → Raise rods
        - Allow: Pressure >= 40 bar
        - Allow: Reactor started
        - Allow: No emergency
        - Require: All three pumps in ON state (status == 2)
        - NO NEED: Turbine running (turbine belum jalan saat initial rod raise)
        
        Phase 3+: Normal operation
        - Same checks as above
        - Turbine akan auto-start dari ESP-BC ketika thermal > 50 MWth
        
        Returns:
            True if safe to move rods, False otherwise
        """
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
        
        # Check 4: All pumps must be ON (status == 2)
        # Status codes: 0=OFF,1=STARTING,2=ON,3=SHUTTING_DOWN
        if self.state.pump_primary_status != 2:
            logger.debug(f"Interlock: Primary pump not ON (status={self.state.pump_primary_status})")
            return False
        if self.state.pump_secondary_status != 2:
            logger.debug(f"Interlock: Secondary pump not ON (status={self.state.pump_secondary_status})")
            return False
        if self.state.pump_tertiary_status != 2:
            logger.debug(f"Interlock: Tertiary pump not ON (status={self.state.pump_tertiary_status})")
            return False
        
        # All checks passed - safe to move rods
        return True
    
    # ============================================
    # Control Logic Thread
    # ============================================
    
    def control_logic_thread(self):
        """Thread for control logic (50ms cycle)"""
        logger.info("Control logic thread started")
        
        loop_count = 0
        while self.state.running:
            try:
                logger.debug("Control: About to acquire state_lock...")
                
                # === ATOMIC OPERATION: Update all control logic in ONE lock ===
                with self.state_lock:
                    logger.debug("Control: Lock acquired, starting updates...")
                    
                    # 1. Update interlock status
                    try:
                        self.state.interlock_satisfied = self._check_interlock_internal()
                        logger.debug("Control: Interlock check done")
                    except Exception as e:
                        logger.error(f"Control: Interlock check failed: {e}")
                    
                    # 2. Update humidifier commands
                    try:
                        if self.humidifier:
                            logger.debug("Control: Calling humidifier.update()...")
                            sg_on, ct1, ct2, ct3, ct4 = self.humidifier.update(
                                self.state.shim_rod,
                                self.state.regulating_rod,
                                self.state.thermal_kw
                            )
                            logger.debug("Control: Humidifier update done")
                            
                            # Cooling Tower: 4 humidifier (STAGED 1-by-1)
                            # Note: SG humidifiers no longer controlled by ESP
                            self.state.humid_ct1_cmd = 1 if ct1 else 0
                            self.state.humid_ct2_cmd = 1 if ct2 else 0
                            self.state.humid_ct3_cmd = 1 if ct3 else 0
                            self.state.humid_ct4_cmd = 1 if ct4 else 0
                        else:
                            logger.debug("Control: Humidifier not available, skipping")
                    except Exception as e:
                        logger.error(f"Control: Humidifier update failed: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # 3. Check and update alarm status
                    try:
                        if self.buzzer:
                            self.buzzer.check_alarms(self.state)
                        logger.debug("Control: Buzzer check done")
                    except Exception as e:
                        logger.error(f"Control: Buzzer check failed: {e}")
                    
                    # 4. Update pump status (non-blocking timer check)
                    try:
                        self._update_pump_status_internal(time.time())
                        logger.debug("Control: Pump status update done")
                    except Exception as e:
                        logger.error(f"Control: Pump status update failed: {e}")
                    
                    logger.debug("Control: All updates done, releasing lock...")
                
                logger.debug("Control: Lock released")
                time.sleep(0.05)  # 50ms
                
                # Log heartbeat every 10 seconds (200 loops x 50ms)
                loop_count += 1
                if loop_count >= 200:
                    logger.info("Control logic thread: alive (200 loops)")
                    loop_count = 0
                
            except Exception as e:
                logger.error(f"Error in control logic thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(0.1)
        
        logger.info("Control logic thread stopped")
    
    def _update_pump_status_internal(self, current_time):
        """
        Update pump status (simulate startup/shutdown) - NON-BLOCKING
        INTERNAL version - assumes state_lock is already held by caller
        """
        # Primary pump
        if self.state.pump_primary_status == 1:  # STARTING
            if self.state.pump_primary_transition_start == 0:
                self.state.pump_primary_transition_start = current_time
                logger.info("Primary pump: STARTING (2s delay)")
            elif current_time - self.state.pump_primary_transition_start >= 2.0:
                self.state.pump_primary_status = 2  # ON
                self.state.pump_primary_transition_start = 0
                logger.info("Primary pump: ON")
        elif self.state.pump_primary_status == 3:  # SHUTTING_DOWN
            if self.state.pump_primary_transition_start == 0:
                self.state.pump_primary_transition_start = current_time
                logger.info("Primary pump: SHUTTING DOWN (1s delay)")
            elif current_time - self.state.pump_primary_transition_start >= 1.0:
                self.state.pump_primary_status = 0  # OFF
                self.state.pump_primary_transition_start = 0
                logger.info("Primary pump: OFF")
        else:
            self.state.pump_primary_transition_start = 0
        
        # Secondary pump
        if self.state.pump_secondary_status == 1:  # STARTING
            if self.state.pump_secondary_transition_start == 0:
                self.state.pump_secondary_transition_start = current_time
                logger.info("Secondary pump: STARTING (2s delay)")
            elif current_time - self.state.pump_secondary_transition_start >= 2.0:
                self.state.pump_secondary_status = 2  # ON
                self.state.pump_secondary_transition_start = 0
                logger.info("Secondary pump: ON")
        elif self.state.pump_secondary_status == 3:  # SHUTTING_DOWN
            if self.state.pump_secondary_transition_start == 0:
                self.state.pump_secondary_transition_start = current_time
                logger.info("Secondary pump: SHUTTING DOWN (1s delay)")
            elif current_time - self.state.pump_secondary_transition_start >= 1.0:
                self.state.pump_secondary_status = 0  # OFF
                self.state.pump_secondary_transition_start = 0
                logger.info("Secondary pump: OFF")
        else:
            self.state.pump_secondary_transition_start = 0
        
        # Tertiary pump
        if self.state.pump_tertiary_status == 1:  # STARTING
            if self.state.pump_tertiary_transition_start == 0:
                self.state.pump_tertiary_transition_start = current_time
                logger.info("Tertiary pump: STARTING (2s delay)")
            elif current_time - self.state.pump_tertiary_transition_start >= 2.0:
                self.state.pump_tertiary_status = 2  # ON
                self.state.pump_tertiary_transition_start = 0
                logger.info("Tertiary pump: ON")
        elif self.state.pump_tertiary_status == 3:  # SHUTTING_DOWN
            if self.state.pump_tertiary_transition_start == 0:
                self.state.pump_tertiary_transition_start = current_time
                logger.info("Tertiary pump: SHUTTING DOWN (1s delay)")
            elif current_time - self.state.pump_tertiary_transition_start >= 1.0:
                self.state.pump_tertiary_status = 0  # OFF
                self.state.pump_tertiary_transition_start = 0
                logger.info("Tertiary pump: OFF")
        else:
            self.state.pump_tertiary_transition_start = 0
    
    # ============================================
    # ESP Communication Thread
    # ============================================
    
    def esp_communication_thread(self):
        """Thread for ESP communication via UART (50ms cycle with immediate trigger)"""
        logger.info("ESP communication thread started (2 ESP via UART)")
        
        # Verify uart_master exists
        if not self.uart_master:
            logger.error("❌ uart_master not initialized! ESP communication disabled.")
            return
        
        logger.info("✓ UART master verified, starting communication loop...")
        
        # Throttle ESP-E updates to prevent buffer overflow
        last_esp_e_update = 0
        ESP_E_UPDATE_INTERVAL = 0.2  # 200ms (5x per second) - was 50ms (20x per second)
        
        while self.state.running:
            try:
                # Wait for either timeout (50ms) OR immediate trigger from button event
                triggered = self.esp_send_immediate.wait(timeout=0.05)  # 50ms optimized cycle
                
                if triggered:
                    logger.debug("⚡ Immediate ESP send triggered by button event")
                    self.esp_send_immediate.clear()  # Reset flag
                
                with self.uart_lock:
                    with self.state_lock:
                        # Send to ESP-BC (Control Rods + Pumps + Turbine + Humidifier)
                        logger.info(f"TX /dev/ttyAMA0: { {'cmd':'update', 'rods':[self.state.safety_rod,self.state.shim_rod,self.state.regulating_rod], 'pumps':[self.state.pump_primary_status,self.state.pump_secondary_status,self.state.pump_tertiary_status], 'humid_ct':[self.state.humid_ct1_cmd,self.state.humid_ct2_cmd,self.state.humid_ct3_cmd,self.state.humid_ct4_cmd]} }")
                        
                        if not self.uart_master.esp_bc_connected:
                            logger.warning("⚠️  ESP-BC not connected, skipping UART send")
                            success = False
                        else:
                            success = self.uart_master.update_esp_bc(
                            self.state.safety_rod,
                            self.state.shim_rod,
                            self.state.regulating_rod,
                            self.state.pump_primary_status,
                            self.state.pump_secondary_status,
                            self.state.pump_tertiary_status,
                            self.state.humid_ct1_cmd,
                            self.state.humid_ct2_cmd,
                            self.state.humid_ct3_cmd,
                            self.state.humid_ct4_cmd
                        )
                        
                        if success:
                            logger.debug("✓ ESP-BC update success")
                            # Get data back from ESP-BC
                            esp_bc_data = self.uart_master.get_esp_bc_data()
                            self.state.thermal_kw = esp_bc_data.kw_thermal
                            self.state.turbine_speed = esp_bc_data.turbine_speed
                            # Small gap before sending to ESP-E to avoid UART contention
                            time.sleep(0.02)
                        else:
                            logger.warning("⚠️  ESP-BC update failed")
                
                # Send to ESP-E outside of state_lock (non-critical, can be slower)
                # THROTTLED: Only send every 200ms to prevent buffer overflow
                current_time = time.time()
                if current_time - last_esp_e_update >= ESP_E_UPDATE_INTERVAL:
                    with self.uart_lock:
                        try:
                            # Add delay before ESP-E to ensure UART buffers are clear
                            time.sleep(0.05)  # 50ms delay for UART stability
                            
                            # Send to ESP-E (Power Indicator Only - Simplified)
                            logger.debug(f"Sending to ESP-E: Thermal={self.state.thermal_kw:.1f}kW")
                            self.uart_master.update_esp_e(
                                thermal_power_kw=self.state.thermal_kw
                            )
                            logger.debug("✓ ESP-E update success")
                            last_esp_e_update = current_time
                        except Exception as e:
                            logger.debug(f"ESP-E communication error (non-critical): {e}")
                
            except Exception as e:
                logger.error(f"Error in ESP communication thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(0.1)
        
        logger.info("ESP communication thread stopped")
    
    # ============================================
    # Button Polling Thread
    # ============================================
    
    def button_polling_thread(self):
        """Thread for button polling (10ms cycle)"""
        logger.info("Button polling thread started")
        
        loop_count = 0
        while self.state.running:
            try:
                self.button_manager.check_all_buttons()
                time.sleep(0.01)  # 10ms
                
                # Log heartbeat every 10 seconds (1000 loops x 10ms)
                loop_count += 1
                if loop_count >= 1000:
                    logger.debug("Button polling thread: alive (1000 loops)")
                    loop_count = 0
                
            except Exception as e:
                logger.error(f"Error in button polling thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(0.05)
        
        logger.info("Button polling thread stopped")
    
    def button_hold_thread(self):
        """Thread for detecting held buttons (rod and pressure control)"""
        logger.info("Button hold detection thread started")
        
        # Define which buttons support hold
        HOLD_BUTTONS = {
            ButtonPin.SAFETY_ROD_UP,
            ButtonPin.SAFETY_ROD_DOWN,
            ButtonPin.SHIM_ROD_UP,
            ButtonPin.SHIM_ROD_DOWN,
            ButtonPin.REGULATING_ROD_UP,
            ButtonPin.REGULATING_ROD_DOWN,
            ButtonPin.PRESSURE_UP,
            ButtonPin.PRESSURE_DOWN
        }
        
        while self.state.running:
            try:
                # Check which buttons are held (50ms interval)
                pressed = self.button_manager.check_hold_buttons(hold_interval=0.05)
                
                # Process only hold-supported buttons
                for pin in pressed & HOLD_BUTTONS:
                    # Queue event for held button
                    if pin == ButtonPin.SAFETY_ROD_UP:
                        self.button_event_queue.put(ButtonEvent.SAFETY_ROD_UP)
                    elif pin == ButtonPin.SAFETY_ROD_DOWN:
                        self.button_event_queue.put(ButtonEvent.SAFETY_ROD_DOWN)
                    elif pin == ButtonPin.SHIM_ROD_UP:
                        self.button_event_queue.put(ButtonEvent.SHIM_ROD_UP)
                    elif pin == ButtonPin.SHIM_ROD_DOWN:
                        self.button_event_queue.put(ButtonEvent.SHIM_ROD_DOWN)
                    elif pin == ButtonPin.REGULATING_ROD_UP:
                        self.button_event_queue.put(ButtonEvent.REGULATING_ROD_UP)
                    elif pin == ButtonPin.REGULATING_ROD_DOWN:
                        self.button_event_queue.put(ButtonEvent.REGULATING_ROD_DOWN)
                    elif pin == ButtonPin.PRESSURE_UP:
                        self.button_event_queue.put(ButtonEvent.PRESSURE_UP)
                    elif pin == ButtonPin.PRESSURE_DOWN:
                        self.button_event_queue.put(ButtonEvent.PRESSURE_DOWN)
                
                time.sleep(0.01)  # 10ms polling (same as button_polling)
                
            except Exception as e:
                logger.error(f"Error in button hold thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(0.05)
        
        logger.info("Button hold detection thread stopped")
    
    def oled_update_thread(self):
        """Thread for updating 9 OLED displays (100ms cycle - optimized for faster visual feedback)"""
        logger.info("OLED update thread started")
        
        if self.oled_manager is None:
            logger.warning("OLED manager not available, thread exiting")
            return
        
        while self.state.running:
            try:
                with self.state_lock:
                    # Update all 9 OLED displays
                    self.oled_manager.update_all(self.state)
                
                time.sleep(0.1)  # 100ms update rate (faster visual feedback)
                
            except Exception as e:
                # Don't spam logs with OLED errors - it's not critical
                logger.debug(f"OLED update error: {e}")
                time.sleep(0.5)  # Slower retry on error
        
        logger.info("OLED update thread stopped")
    
    # ============================================
    # Auto Simulation Thread (NEW)
    # ============================================
    
    def auto_simulation_thread(self):
        """
        Thread untuk menjalankan simulasi otomatis (slow paced)
        Simulasi berjalan bertahap dengan delay agar mudah dipahami
        """
        logger.info("Auto simulation thread started (waiting for trigger)")
        
        while self.state.running:
            # Wait for auto simulation to be triggered
            if not self.state.auto_sim_running:
                time.sleep(0.5)
                continue
            
            try:
                logger.info("="*70)
                logger.info("🤖 AUTO SIMULATION MODE - Full PWR Startup Sequence")
                logger.info("   Simulasi berjalan otomatis dengan kecepatan lambat")
                logger.info("   untuk memudahkan pemahaman cara kerja PLTN")
                logger.info("="*70)
                
                # Phase 1: System Initialization (already done by START)
                logger.info("\n📍 Phase 1: System Initialization")
                logger.info("   ✓ Reactor system started")
                time.sleep(3)
                
                # Phase 2: Raise Pressure to minimum required (40 bar)
                logger.info("\n📍 Phase 2: Pressurizer Activation")
                logger.info("   Raising pressure to minimum 40 bar...")
                with self.state_lock:
                    for i in range(45):  # 45 bar (sedikit lebih dari minimum)
                        self.state.pressure += 1.0
                        if i % 5 == 0:
                            logger.info(f"   Pressure: {self.state.pressure:.1f} bar")
                        time.sleep(0.2)  # 0.2s per bar = 9s total
                logger.info(f"   ✓ Pressure reached: {self.state.pressure:.1f} bar")
                time.sleep(2)
                
                # Phase 3: Start Pumps (Tertiary → Secondary → Primary)
                logger.info("\n📍 Phase 3: Coolant Pumps Startup Sequence")
                
                # Tertiary pump first
                logger.info("   Starting Tertiary Pump (Cooling path)...")
                with self.state_lock:
                    self.state.pump_tertiary_status = 1  # STARTING
                time.sleep(3)  # Wait for pump to start
                logger.info("   ✓ Tertiary Pump: ON")
                
                # Secondary pump
                logger.info("   Starting Secondary Pump (Heat exchanger)...")
                with self.state_lock:
                    self.state.pump_secondary_status = 1  # STARTING
                time.sleep(3)  # Wait for pump to start
                logger.info("   ✓ Secondary Pump: ON")
                
                # Primary pump
                logger.info("   Starting Primary Pump (Main loop)...")
                with self.state_lock:
                    self.state.pump_primary_status = 1  # STARTING
                time.sleep(3)  # Wait for pump to start
                logger.info("   ✓ Primary Pump: ON")
                logger.info("   ✓ All pumps operational - Interlock satisfied")
                time.sleep(3)
                
                # Phase 4: Control Rod Withdrawal (Gradual)
                logger.info("\n📍 Phase 4: Control Rod Withdrawal")
                logger.info("   Slowly raising Shim and Regulating rods...")
                logger.info("   (Safety rod kept at 0% - used for SCRAM only)")
                
                # Raise rods gradually to 50% (safe operational level)
                target_rod_position = 50
                with self.state_lock:
                    for i in range(target_rod_position):
                        # Check if still in auto mode (could be cancelled)
                        if not self.state.auto_sim_running:
                            logger.warning("   ⚠️ Auto simulation cancelled by user")
                            return
                        
                        self.state.shim_rod += 1
                        self.state.regulating_rod += 1
                        
                        if i % 5 == 0 or i == target_rod_position - 1:
                            logger.info(f"   Rods: Shim={self.state.shim_rod}%, "
                                      f"Regulating={self.state.regulating_rod}%")
                        time.sleep(0.5)  # 0.5s per 1% = 25s total to 50%
                
                logger.info(f"   ✓ Control rods raised to {target_rod_position}%")
                logger.info("   ✓ Reactor criticality achieved - Thermal power rising")
                time.sleep(4)
                
                # Phase 5: Steam Generator Activation (automatic via humidifier control)
                logger.info("\n📍 Phase 5: Steam Generator Operation")
                logger.info("   Steam generators activate automatically (Shim & Reg >= 40%)")
                logger.info("   Visual: Humidifiers creating steam effect 💨")
                time.sleep(5)
                
                # Phase 6: Turbine Starting (automatic via ESP-BC)
                logger.info("\n📍 Phase 6: Turbine-Generator Startup")
                logger.info("   Turbine starting automatically (Thermal power > threshold)")
                logger.info("   Speed increasing gradually to 100%...")
                time.sleep(8)
                logger.info("   ✓ Turbine at full speed")
                logger.info("   ✓ Generator synchronized to grid")
                time.sleep(3)
                
                # Phase 7: Power Generation Begins
                logger.info("\n📍 Phase 7: Electrical Power Generation")
                logger.info("   Reactor thermal: ~900 MWth")
                logger.info("   Turbine efficiency: 33%")
                logger.info("   Electrical output: ~200-250 MWe")
                logger.info("   Visual: 10 Power indicator LEDs brightness increasing 💡")
                time.sleep(5)
                
                # Phase 8: Cooling Tower Activation (automatic)
                logger.info("\n📍 Phase 8: Cooling Tower Humidifiers")
                logger.info("   Cooling towers activate in stages as power increases")
                logger.info("   Visual: 4 CT humidifiers creating steam effect 💨")
                time.sleep(5)
                
                # Phase 9: Stable Operation
                logger.info("\n📍 Phase 9: Normal Operation Achieved")
                logger.info("="*70)
                logger.info("✅ REACTOR AT STABLE OPERATION")
                logger.info(f"   Pressure: {self.state.pressure:.1f} bar")
                logger.info(f"   Control Rods: Shim={self.state.shim_rod}%, "
                          f"Reg={self.state.regulating_rod}%")
                logger.info("   Pumps: All operational")
                logger.info("   Turbine: Running at full speed")
                logger.info("   Power Output: ~200-250 MWe")
                logger.info("   Humidifiers: SG + CT all active")
                logger.info("")
                logger.info("🎓 EDUCATIONAL NOTE:")
                logger.info("   - Operator dapat adjust control rods untuk fine tuning")
                logger.info("   - Pressure dapat disesuaikan sesuai kebutuhan")
                logger.info("   - Emergency button siap untuk SCRAM jika diperlukan")
                logger.info("="*70)
                
                # Auto simulation complete
                with self.state_lock:
                    self.state.auto_sim_running = False
                    self.state.simulation_mode = 'manual'  # Back to manual mode
                
                logger.info("\n✅ Auto simulation complete - switched to MANUAL mode")
                logger.info("   Operator dapat melanjutkan kontrol manual")
                
            except Exception as e:
                logger.error(f"Error in auto simulation: {e}")
                import traceback
                logger.error(traceback.format_exc())
                with self.state_lock:
                    self.state.auto_sim_running = False
                time.sleep(1)
        
        logger.info("Auto simulation thread stopped")
    
    # ============================================
    # Main Loop
    # ============================================
    
    def run(self):
        """Main control loop with periodic health monitoring"""
        logger.info("Starting PLTN Controller (2 ESP + Event Queue + Auto Sim)...")
        
        # Start threads
        threads = [
            threading.Thread(target=self.button_polling_thread, daemon=True, name="ButtonThread"),
            threading.Thread(target=self.button_hold_thread, daemon=True, name="ButtonHoldThread"),
            threading.Thread(target=self.button_event_processor_thread, daemon=True, name="EventThread"),
            threading.Thread(target=self.control_logic_thread, daemon=True, name="ControlThread"),
            threading.Thread(target=self.esp_communication_thread, daemon=True, name="ESPCommThread"),
            threading.Thread(target=self.oled_update_thread, daemon=True, name="OLEDThread"),
            threading.Thread(target=self.health_monitoring_thread, daemon=True, name="HealthThread"),
            threading.Thread(target=self.auto_simulation_thread, daemon=True, name="AutoSimThread")  # NEW
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
                    if self.uart_master:
                        esp_bc_data = self.uart_master.get_esp_bc_data()
                        
                        logger.info(f"Status: P={self.state.pressure:.1f}bar, "
                                  f"Rods=[{self.state.safety_rod},{self.state.shim_rod},"
                                  f"{self.state.regulating_rod}]%, "
                                  f"Thermal={self.state.thermal_kw:.1f}kW, "
                                  f"Turbine={esp_bc_data.power_level:.1f}%, "
                                  f"Humid=[CT:{self.state.humid_ct1_cmd},{self.state.humid_ct2_cmd},"\
                                  f"{self.state.humid_ct3_cmd},{self.state.humid_ct4_cmd}]")
                    else:
                        logger.info(f"Status: P={self.state.pressure:.1f}bar (Simulation mode)")
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
    
    def health_monitoring_thread(self):
        """Thread for system health monitoring - run once at startup only"""
        logger.info("Health monitoring: Running initial check...")
        
        # Run health check ONCE at startup
        try:
            time.sleep(2.0)  # Wait for system to stabilize
            
            logger.info("\n" + "="*70)
            logger.info("INITIAL SYSTEM HEALTH CHECK")
            logger.info("="*70)
            
            with self.uart_lock:
                self.health_monitor.check_all(self)
            
            logger.info("Initial health check complete - periodic checks disabled")
            logger.info("(Periodic checks would reset simulation by sending rods=0)")
            
        except Exception as e:
            logger.error(f"Initial health check error: {e}")
        
        # Thread stays alive but does nothing (just sleeps)
        while self.state.running:
            time.sleep(60.0)  # Just keep thread alive
        
        logger.info("Health monitoring thread stopped")
    
    def shutdown(self):
        """Shutdown system gracefully with proper UART cleanup"""
        logger.info("="*60)
        logger.info("Shutting down PLTN Panel Controller...")
        logger.info("="*60)
        
        # Stop all threads
        self.state.running = False
        time.sleep(0.5)  # Give threads time to exit
        
        # Cleanup in reverse order of initialization
        try:
            # 1. Cleanup GPIO buttons
            if self.button_manager:
                logger.info("Cleaning up GPIO buttons...")
                self.button_manager.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up buttons: {e}")

        try:
            # 2. Cleanup buzzer
            if self.buzzer:
                logger.info("Cleaning up buzzer...")
                self.buzzer.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up buzzer: {e}")
        
        try:
            # 3. Send safe state to ESPs before closing UART
            if self.uart_master:
                logger.info("Sending safe state to ESPs via UART...")
                
                # ESP-BC: All rods to 0%, all pumps off, all humidifiers off
                self.uart_master.update_esp_bc(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                time.sleep(0.05)
                
                # ESP-E: Power off
                self.uart_master.update_esp_e(0.0)
                time.sleep(0.05)
                
                logger.info("Safe state sent to ESPs")
        except Exception as e:
            logger.error(f"Error sending safe state: {e}")
        
        try:
            # 3. Close UART connections
            if self.uart_master:
                logger.info("Closing UART connections...")
                self.uart_master.close()
        except Exception as e:
            logger.error(f"Error closing UART: {e}")
        
        try:
            # 4. Close multiplexers (for OLEDs)
            if self.mux_manager:
                logger.info("Closing multiplexers (OLEDs)...")
                self.mux_manager.close()
        except Exception as e:
            logger.error(f"Error closing multiplexers: {e}")
        
        logger.info("="*60)
        logger.info("✅ PLTN Panel Controller shutdown complete")
        logger.info("="*60)


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
