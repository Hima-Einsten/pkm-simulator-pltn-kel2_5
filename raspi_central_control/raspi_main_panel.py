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
from raspi_gpio_buttons import ButtonHandler as ButtonManager
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
                self.state.pressure = min(self.state.pressure + 5.0, 200.0)
                logger.info(f"✓ Pressure UP: {self.state.pressure:.1f} bar")
            
            elif event == ButtonEvent.PRESSURE_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.pressure = max(self.state.pressure - 5.0, 0.0)
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
                self.state.safety_rod = min(self.state.safety_rod + 5, 100)
                logger.info(f"✓ Safety rod UP: {self.state.safety_rod}%")
            
            elif event == ButtonEvent.SAFETY_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.safety_rod = max(self.state.safety_rod - 5, 0)
                logger.info(f"✓ Safety rod DOWN: {self.state.safety_rod}%")
            
            elif event == ButtonEvent.SHIM_ROD_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if not self._check_interlock_internal():
                    logger.warning("⚠️  Interlock not satisfied!")
                    return
                self.state.shim_rod = min(self.state.shim_rod + 5, 100)
                logger.info(f"✓ Shim rod UP: {self.state.shim_rod}%")
            
            elif event == ButtonEvent.SHIM_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.shim_rod = max(self.state.shim_rod - 5, 0)
                logger.info(f"✓ Shim rod DOWN: {self.state.shim_rod}%")
            
            elif event == ButtonEvent.REGULATING_ROD_UP:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                if not self._check_interlock_internal():
                    logger.warning("⚠️  Interlock not satisfied!")
                    return
                self.state.regulating_rod = min(self.state.regulating_rod + 5, 100)
                logger.info(f"✓ Regulating rod UP: {self.state.regulating_rod}%")
            
            elif event == ButtonEvent.REGULATING_ROD_DOWN:
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.regulating_rod = max(self.state.regulating_rod - 5, 0)
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
                self.state.humid_sg1_cmd = 0
                self.state.humid_sg2_cmd = 0
                self.state.humid_ct1_cmd = 0
                self.state.humid_ct2_cmd = 0
                self.state.humid_ct3_cmd = 0
                self.state.humid_ct4_cmd = 0
                self.state.interlock_satisfied = False
                logger.info("=" * 60)
                logger.info("🔄 SIMULATION RESET")
                logger.info("All parameters reset. Press START to begin.")
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
                    
                    # Wait for event (blocking, with timeout)
                    event = self.button_event_queue.get(timeout=0.1)
                    
                    logger.info(f"🔹 Processing: {event.value}")
                    
                    # Process event with lock
                    self.process_button_event(event)
                    
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
                            
                            # Steam Generator: 2 humidifier (both controlled together)
                            self.state.humid_sg1_cmd = 1 if sg_on else 0
                            self.state.humid_sg2_cmd = 1 if sg_on else 0
                            
                            # Cooling Tower: 4 humidifier (STAGED 1-by-1)
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
        """Thread for ESP communication via UART (100ms cycle)"""
        logger.info("ESP communication thread started (2 ESP via UART)")
        
        # Verify uart_master exists
        if not self.uart_master:
            logger.error("❌ uart_master not initialized! ESP communication disabled.")
            return
        
        logger.info("✓ UART master verified, starting communication loop...")
        
        while self.state.running:
            try:
                with self.uart_lock:
                    with self.state_lock:
                        # Send to ESP-BC (Control Rods + Turbine + Humidifier)
                        logger.debug(f"Sending to ESP-BC: rods=[{self.state.safety_rod},{self.state.shim_rod},{self.state.regulating_rod}]")
                        
                        success = self.uart_master.update_esp_bc(
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
                            logger.debug("✓ ESP-BC update success")
                            # Get data back from ESP-BC
                            esp_bc_data = self.uart_master.get_esp_bc_data()
                            self.state.thermal_kw = esp_bc_data.kw_thermal
                            
                            # Small delay between ESP commands for stability
                            time.sleep(0.05)
                            
                            # Send to ESP-E (LED Visualizer)
                            logger.debug(f"Sending to ESP-E: P={self.state.pressure:.1f}bar")
                            self.uart_master.update_esp_e(
                                pressure_primary=self.state.pressure,
                                pump_status_primary=self.state.pump_primary_status,
                                pressure_secondary=self.state.pressure * 0.35,
                                pump_status_secondary=self.state.pump_secondary_status,
                                pressure_tertiary=self.state.pressure * 0.10,
                                pump_status_tertiary=self.state.pump_tertiary_status,
                                thermal_power_kw=self.state.thermal_kw
                            )
                            logger.debug("✓ ESP-E update success")
                        else:
                            logger.warning("⚠️  ESP-BC update failed")
                
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                logger.error(f"Error in ESP communication thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(0.2)
        
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
                # Don't spam logs with OLED errors - it's not critical
                logger.debug(f"OLED update error: {e}")
                time.sleep(0.5)  # Slower retry on error
        
        logger.info("OLED update thread stopped")
    
    # ============================================
    # Main Loop
    # ============================================
    
    def run(self):
        """Main control loop with periodic health monitoring"""
        logger.info("Starting PLTN Controller (2 ESP + Event Queue)...")
        
        # Start threads
        threads = [
            threading.Thread(target=self.button_polling_thread, daemon=True, name="ButtonThread"),
            threading.Thread(target=self.button_event_processor_thread, daemon=True, name="EventThread"),
            threading.Thread(target=self.control_logic_thread, daemon=True, name="ControlThread"),
            threading.Thread(target=self.esp_communication_thread, daemon=True, name="ESPCommThread"),
            threading.Thread(target=self.oled_update_thread, daemon=True, name="OLEDThread"),
            threading.Thread(target=self.health_monitoring_thread, daemon=True, name="HealthThread")
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
                                  f"Humid=[SG:{self.state.humid_sg1_cmd},{self.state.humid_sg2_cmd},"
                                  f"CT:{self.state.humid_ct1_cmd},{self.state.humid_ct2_cmd},"
                                  f"{self.state.humid_ct3_cmd},{self.state.humid_ct4_cmd}]")
                    else:
                        logger.info(f"Status: P={self.state.pressure:.1f}bar (Simulation mode)")
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
    
    def health_monitoring_thread(self):
        """Thread for periodic system health monitoring"""
        logger.info("Health monitoring thread started (check every 60s)")
        
        last_check = time.time()
        
        while self.state.running:
            try:
                current_time = time.time()
                
                # Run health check every 60 seconds
                if current_time - last_check >= 60:
                    logger.info("\n" + "="*70)
                    logger.info("PERIODIC HEALTH CHECK (60s interval)")
                    logger.info("="*70)
                    
                    with self.uart_lock:
                        self.health_monitor.check_all(self)
                    
                    last_check = current_time
                
                time.sleep(5.0)  # Check timer every 5 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(10.0)
    
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
            # 2. Send safe state to ESPs before closing UART
            if self.uart_master:
                logger.info("Sending safe state to ESPs via UART...")
                
                # ESP-BC: All rods to 0%, all humidifiers off
                self.uart_master.update_esp_bc(0, 0, 0, 0, 0, 0, 0, 0, 0)
                time.sleep(0.05)
                
                # ESP-E: All pumps off
                self.uart_master.update_esp_e(0.0, 0, 0.0, 0, 0.0, 0, 0.0)
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
