"""
UART Master Communication Module
Replaces I2C communication with UART for ESP32 slaves

Architecture:
- ESP-BC: /dev/ttyAMA0 (GPIO 14/15) - Control Rods + Turbine + Humidifier
- ESP-E:  /dev/ttyAMA3 (GPIO 4/5)   - LED Visualizer

Protocol: JSON over UART (115200 baud, 8N1)
"""

import serial
import json
import time
import logging
from typing import Optional, Dict
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class ESP_BC_Data:
    """Data structure for ESP-BC (Control Rods + Turbine + Pumps + Motor Driver + Cooling Tower Relays)"""
    # To ESP-BC
    safety_target: int = 0
    shim_target: int = 0
    regulating_target: int = 0
    
    humid_ct1_cmd: int = 0
    humid_ct2_cmd: int = 0
    humid_ct3_cmd: int = 0
    humid_ct4_cmd: int = 0
    
    # From ESP-BC - Control Rods
    safety_actual: int = 0
    shim_actual: int = 0
    regulating_actual: int = 0
    
    # From ESP-BC - Turbine & Power
    kw_thermal: float = 0.0
    power_level: float = 0.0
    state: int = 0
    generator_status: int = 0
    turbine_status: int = 0
    turbine_speed: float = 0.0
    
    # From ESP-BC - Pump Speeds (automatic control by ESP)
    pump_primary_speed: float = 0.0
    pump_secondary_speed: float = 0.0
    pump_tertiary_speed: float = 0.0
    
    # From ESP-BC - Cooling Tower Humidifier Status (4 relays only)
    humid_ct1_status: int = 0
    humid_ct2_status: int = 0
    humid_ct3_status: int = 0
    humid_ct4_status: int = 0


@dataclass
class ESP_E_Data:
    """Data structure for ESP-E (Power Indicator Only - Simplified)"""
    # To ESP-E
    thermal_power_kw: float = 0.0
    
    # From ESP-E
    power_mwe: float = 0.0
    pwm: int = 0


class UARTDevice:
    """Base class for UART device communication"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize UART device
        
        Args:
            port: Serial port path (e.g., '/dev/ttyAMA0')
            baudrate: Communication speed (default 115200)
            timeout: Read timeout in seconds (default 1.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.lock = threading.Lock()
        self.error_count = 0
        self.last_comm_time = 0.0
        
    def connect(self) -> bool:
        """
        Open serial connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=1.0
            )
            
            # Flush buffers and wait for ESP32 to be ready
            time.sleep(2.0)  # Wait for ESP32 to fully initialize (same as test_uart_timing)
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            logger.info(f"✅ UART connected: {self.port} at {self.baudrate} baud")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to open {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                logger.info(f"UART disconnected: {self.port}")
        except Exception as e:
            logger.error(f"Error closing {self.port}: {e}")
    
    
    def send_json(self, data: dict) -> bool:
        """
        Send JSON message to device (fire-and-forget, no response expected)
        
        For request-response communication, use send_receive() instead.
        
        Args:
            data: Dictionary to send as JSON
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                if not self.serial or not self.serial.is_open:
                    logger.error(f"Serial port {self.port} not open")
                    return False
                
                # Flush buffers before send (fire-and-forget mode)
                try:
                    self.serial.reset_input_buffer()
                    self.serial.reset_output_buffer()
                except Exception:
                    pass

                # Convert to JSON and add newline
                json_str = json.dumps(data) + '\n'
                
                # Send
                self.serial.write(json_str.encode('utf-8'))
                self.serial.flush()  # Ensure data is sent
                time.sleep(0.010)  # 10ms for ESP to process
                logger.info(f"TX {self.port}: {json_str.strip()}")
                return True
                
            except Exception as e:
                logger.error(f"Error sending to {self.port}: {e}")
                self.error_count += 1
                return False
    
    def receive_json(self, timeout: Optional[float] = None) -> Optional[dict]:
        """
        Receive JSON message from device
        
        Args:
            timeout: Optional timeout override
            
        Returns:
            Dictionary if successful, None otherwise
        """
        with self.lock:
            try:
                if not self.serial or not self.serial.is_open:
                    logger.error(f"Serial port {self.port} not open")
                    return None
                
                # Set timeout if provided
                old_timeout = self.serial.timeout
                if timeout is not None:
                    self.serial.timeout = timeout
                
                # Read line
                line = self.serial.readline()
                
                # Restore timeout
                if timeout is not None:
                    self.serial.timeout = old_timeout
                
                if not line:
                    logger.warning(f"No response from {self.port} (timeout)")
                    self.error_count += 1
                    return None
                
                # Decode and parse JSON
                json_str = line.decode('utf-8').strip()
                logger.info(f"RX {self.port}: {json_str}")
                
                data = json.loads(json_str)
                
                # Reset error count on success
                self.last_comm_time = time.time()
                if self.error_count > 0:
                    logger.info(f"Communication restored with {self.port}")
                    self.error_count = 0
                
                return data
                
            except json.JSONDecodeError as e:
                # Attempt to show raw bytes received for debugging
                try:
                    raw = line
                except Exception:
                    raw = b''
                logger.error(f"JSON decode error from {self.port}: {e}")
                logger.error(f"  --> Received raw bytes: {raw}")
                logger.error(f"  --> Decoded string attempted: '{json_str if 'json_str' in locals() else '<none>'}'")
                self.error_count += 1
                return None
                
            except Exception as e:
                logger.error(f"Error receiving from {self.port}: {e}")
                self.error_count += 1
                return None
    
    
    def send_receive(self, data: dict, timeout: float = 1.0) -> Optional[dict]:
        """
        Send command and wait for response
        
        Args:
            data: Dictionary to send
            timeout: Response timeout
            
        Returns:
            Response dictionary or None
        """
        with self.lock:
            try:
                if not self.serial or not self.serial.is_open:
                    logger.error(f"Serial port {self.port} not open")
                    return None
                
                # CRITICAL: Flush output buffer ONLY (not input!)
                # Input buffer should NOT be flushed here because previous response might still be there
                try:
                    self.serial.reset_output_buffer()  # Clear old TX data only
                except Exception:
                    pass

                # Convert to JSON and add newline
                json_str = json.dumps(data) + '\n'
                
                # Send
                self.serial.write(json_str.encode('utf-8'))
                self.serial.flush()  # Ensure data is sent
                logger.info(f"TX {self.port}: {json_str.strip()}")
                
                # Wait for ESP to process (don't flush input yet!)
                time.sleep(0.010)  # 10ms for ESP to start processing
                
                # Now receive response
                # Set timeout if provided
                old_timeout = self.serial.timeout
                if timeout is not None:
                    self.serial.timeout = timeout
                
                # Read line
                line = self.serial.readline()
                
                # Restore timeout
                if timeout is not None:
                    self.serial.timeout = old_timeout
                
                if not line:
                    logger.warning(f"No response from {self.port} (timeout)")
                    self.error_count += 1
                    # Flush input buffer NOW (after failed read)
                    try:
                        self.serial.reset_input_buffer()
                    except Exception:
                        pass
                    return None
                
                # Decode and parse JSON
                json_str_response = line.decode('utf-8').strip()
                logger.info(f"RX {self.port}: {json_str_response}")
                
                response_data = json.loads(json_str_response)
                
                # Reset error count on success
                self.last_comm_time = time.time()
                if self.error_count > 0:
                    logger.info(f"Communication restored with {self.port}")
                    self.error_count = 0
                
                # Flush input buffer NOW (after successful read)
                # This clears any garbage that might have accumulated
                try:
                    self.serial.reset_input_buffer()
                except Exception:
                    pass
                
                return response_data
                
            except json.JSONDecodeError as e:
                # Attempt to show raw bytes received for debugging
                try:
                    raw = line
                except Exception:
                    raw = b''
                logger.error(f"JSON decode error from {self.port}: {e}")
                logger.error(f"  --> Received raw bytes: {raw}")
                logger.error(f"  --> Decoded string attempted: '{json_str_response if 'json_str_response' in locals() else '<none>'}'")
                self.error_count += 1
                # Flush input buffer after error
                try:
                    self.serial.reset_input_buffer()
                except Exception:
                    pass
                return None
                
            except Exception as e:
                logger.error(f"Error in send_receive from {self.port}: {e}")
                self.error_count += 1
                # Flush input buffer after error
                try:
                    self.serial.reset_input_buffer()
                except Exception:
                    pass
                return None



class UARTMaster:
    """
    UART Master for ESP32 communication
    Manages 2 UART devices: ESP-BC and ESP-E
    """
    
    def __init__(self, esp_bc_port: str = '/dev/ttyAMA0', 
                 esp_e_port: str = '/dev/ttyAMA3',  # GPIO 4/5
                 baudrate: int = 115200):
        """
        Initialize UART Master
        
        Args:
            esp_bc_port: Serial port for ESP-BC (required)
            esp_e_port: Serial port for ESP-E (optional, None to disable)
            baudrate: Communication speed
        """
        logger.info("="*70)
        logger.info("UART Master Initialization")
        logger.info("="*70)
        
        # Create UART devices
        self.esp_bc = UARTDevice(esp_bc_port, baudrate)
        self.esp_e = None
        self.esp_e_enabled = esp_e_port is not None
        
        if self.esp_e_enabled:
            self.esp_e = UARTDevice(esp_e_port, baudrate)
        
        # Data storage
        self.esp_bc_data = ESP_BC_Data()
        self.esp_e_data = ESP_E_Data()
        
        # Connect devices
        self.esp_bc_connected = self.esp_bc.connect()
        self.esp_e_connected = False
        
        # Additional stabilization delay after connection (critical for reliability)
        if self.esp_bc_connected:
            logger.info("⏳ Waiting 1 second for ESP32 to stabilize...")
            time.sleep(1.0)
            # Handshake ping to ensure ESP firmware ready to parse JSON
            try:
                ping_resp = self.esp_bc.send_receive({"cmd":"ping"}, timeout=1.0)
                if ping_resp and ping_resp.get("status") == "ok" and ping_resp.get("message") == "pong":
                    logger.info("✅ ESP-BC handshake successful (pong)")
                else:
                    logger.warning("⚠️  ESP-BC did not respond to ping - marking as not connected")
                    self.esp_bc_connected = False
            except Exception as e:
                logger.warning(f"⚠️  ESP-BC handshake error: {e}")
                self.esp_bc_connected = False
        
        if self.esp_bc_connected:
            logger.info(f"✅ ESP-BC: {esp_bc_port} (Control Rods + Turbine + Motor + Humid)")
        else:
            logger.error(f"❌ ESP-BC: {esp_bc_port} - NOT CONNECTED!")
        
        if self.esp_e_enabled:
            self.esp_e_connected = self.esp_e.connect()
            if self.esp_e_connected:
                logger.info("⏳ Waiting 1 second for ESP32 to stabilize...")
                time.sleep(1.0)
                # Handshake ping to ensure ESP-E firmware ready
                try:
                    ping_resp_e = self.esp_e.send_receive({"cmd":"ping"}, timeout=1.0)
                    if ping_resp_e and ping_resp_e.get("status") == "ok" and ping_resp_e.get("message") == "pong":
                        logger.info("✅ ESP-E handshake successful (pong)")
                    else:
                        logger.warning("⚠️  ESP-E did not respond to ping - marking as not connected")
                        self.esp_e_connected = False
                except Exception as e:
                    logger.warning(f"⚠️  ESP-E handshake error: {e}")
                    self.esp_e_connected = False

                if self.esp_e_connected:
                    logger.info(f"✅ ESP-E: {esp_e_port} (LED Visualizer)")
                else:
                    logger.warning(f"⚠️  ESP-E: {esp_e_port} - NOT CONNECTED (non-critical)")
            else:
                logger.warning(f"⚠️  ESP-E: {esp_e_port} - NOT CONNECTED (non-critical)")
        else:
            logger.info("ℹ️  ESP-E: Disabled (not configured)")
        
        logger.info("="*70)
    
    def update_esp_bc(self, safety: int, shim: int, regulating: int,
                      pump_primary: int = 0, pump_secondary: int = 0, pump_tertiary: int = 0,
                      humid_ct1: int = 0, humid_ct2: int = 0,
                      humid_ct3: int = 0, humid_ct4: int = 0) -> bool:
        """
        Send update to ESP-BC
        
        Args:
            safety: Safety rod target (0-100%)
            shim: Shim rod target (0-100%)
            regulating: Regulating rod target (0-100%)
            pump_primary: Primary pump status (0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN)
            pump_secondary: Secondary pump status (0-3)
            pump_tertiary: Tertiary pump status (0-3)
            humid_ct1-4: Cooling Tower humidifiers (0/1)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.esp_bc_connected:
            return False
        
        # Update internal state
        self.esp_bc_data.safety_target = safety
        self.esp_bc_data.shim_target = shim
        self.esp_bc_data.regulating_target = regulating
        self.esp_bc_data.humid_ct1_cmd = humid_ct1
        self.esp_bc_data.humid_ct2_cmd = humid_ct2
        self.esp_bc_data.humid_ct3_cmd = humid_ct3
        self.esp_bc_data.humid_ct4_cmd = humid_ct4
        
        # Coerce and validate inputs to safe JSON-friendly primitives
        try:
            safety_i = int(max(0, min(100, int(safety))))
        except Exception:
            safety_i = 0
        try:
            shim_i = int(max(0, min(100, int(shim))))
        except Exception:
            shim_i = 0
        try:
            regulating_i = int(max(0, min(100, int(regulating))))
        except Exception:
            regulating_i = 0

        def clamp_pump(x):
            try:
                xi = int(x)
            except Exception:
                return 0
            return max(0, min(3, xi))

        pump_p = clamp_pump(pump_primary)
        pump_s = clamp_pump(pump_secondary)
        pump_t = clamp_pump(pump_tertiary)

        def bool_to_int(v):
            try:
                return 1 if int(v) != 0 else 0
            except Exception:
                return 0

        humid_ct1_i = bool_to_int(humid_ct1)
        humid_ct2_i = bool_to_int(humid_ct2)
        humid_ct3_i = bool_to_int(humid_ct3)
        humid_ct4_i = bool_to_int(humid_ct4)

        # Prepare command (sanitized)
        command = {
            "cmd": "update",
            "rods": [safety_i, shim_i, regulating_i],
            "pumps": [pump_p, pump_s, pump_t],
            "humid_ct": [humid_ct1_i, humid_ct2_i, humid_ct3_i, humid_ct4_i]
        }

        # Send and receive (increased timeout for reliability)
        # ESP-BC has more processing (rods + pumps + turbine + humid) so needs longer timeout
        try:
            response = self.esp_bc.send_receive(command, timeout=2.5)  # Increased from 2.0s
        except Exception as e:
            logger.error(f"Error sending to ESP-BC: {e}")
            response = None
        
        if response and response.get("status") == "ok":
            # Parse response - Control Rods
            self.esp_bc_data.safety_actual = response.get("rods", [0,0,0])[0]
            self.esp_bc_data.shim_actual = response.get("rods", [0,0,0])[1]
            self.esp_bc_data.regulating_actual = response.get("rods", [0,0,0])[2]
            
            # Parse response - Turbine & Power
            self.esp_bc_data.kw_thermal = response.get("thermal_kw", 0.0)
            self.esp_bc_data.power_level = response.get("power_level", 0.0)
            self.esp_bc_data.state = response.get("state", 0)
            self.esp_bc_data.turbine_speed = response.get("turbine_speed", 0.0)
            
            # Parse response - Pump Speeds (automatic by ESP)
            pump_speeds = response.get("pump_speeds", [0.0, 0.0, 0.0])
            self.esp_bc_data.pump_primary_speed = pump_speeds[0]
            self.esp_bc_data.pump_secondary_speed = pump_speeds[1]
            self.esp_bc_data.pump_tertiary_speed = pump_speeds[2]
            
            # Parse response - Cooling Tower Humidifier Status (flat array)
            humid_status = response.get("humid_status", [0, 0, 0, 0])
            self.esp_bc_data.humid_ct1_status = humid_status[0]
            self.esp_bc_data.humid_ct2_status = humid_status[1]
            self.esp_bc_data.humid_ct3_status = humid_status[2]
            self.esp_bc_data.humid_ct4_status = humid_status[3]
            
            logger.debug(f"ESP-BC: Rods={response.get('rods')}, "
                        f"Thermal={self.esp_bc_data.kw_thermal:.1f}kW, "
                        f"Pumps=[{self.esp_bc_data.pump_primary_speed:.1f}%, "
                        f"{self.esp_bc_data.pump_secondary_speed:.1f}%, "
                        f"{self.esp_bc_data.pump_tertiary_speed:.1f}%]")
            return True
        else:
            if response is None:
                logger.warning("ESP-BC: No response or timeout")
            else:
                logger.warning(f"ESP-BC: Invalid response: {response}")
            return False
    
    def update_esp_e(self, thermal_power_kw: float = 0.0) -> bool:
        """
        Send update to ESP-E (Power Indicator Only - Simplified)
        
        Args:
            thermal_power_kw: Thermal power for LED indicator (0-300000 kW)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.esp_e_enabled or not self.esp_e_connected:
            return False
        
        # Update internal state
        self.esp_e_data.thermal_power_kw = thermal_power_kw
        
        # Prepare simplified command - only thermal power
        command = {
            "cmd": "update",
            "thermal_kw": float(thermal_power_kw)
        }
        
        # Send without retry - ESP-E is non-critical (just visualization)
        try:
            response = self.esp_e.send_receive(command, timeout=1.0)  # Increased from 0.5s
        except Exception as e:
            logger.debug(f"Error sending to ESP-E: {e}")
            return False
        
        if response and response.get("status") == "ok":
            # Parse simplified response
            self.esp_e_data.power_mwe = response.get("power_mwe", 0.0)
            self.esp_e_data.pwm = response.get("pwm", 0)
            
            logger.debug(f"ESP-E: Power={self.esp_e_data.power_mwe:.1f} MWe, "
                        f"PWM={self.esp_e_data.pwm}/255")
            return True
        
        # Don't log errors - ESP-E is non-critical
        return False
    
    def get_esp_bc_data(self) -> ESP_BC_Data:
        """Get latest data from ESP-BC"""
        return self.esp_bc_data
    
    def get_esp_e_data(self) -> ESP_E_Data:
        """Get latest data from ESP-E"""
        return self.esp_e_data
    
    def get_health_status(self) -> Dict:
        """
        Get health status of both ESP devices
        
        Returns:
            Dictionary with health information
        """
        return {
            'esp_bc': {
                'connected': self.esp_bc_connected,
                'port': self.esp_bc.port,
                'error_count': self.esp_bc.error_count,
                'last_comm': self.esp_bc.last_comm_time,
                'status': 'OK' if self.esp_bc.error_count < 5 else 'ERROR'
            },
            'esp_e': {
                'connected': self.esp_e_connected,
                'port': self.esp_e.port,
                'error_count': self.esp_e.error_count,
                'last_comm': self.esp_e.last_comm_time,
                'status': 'OK' if self.esp_e.error_count < 5 else 'WARNING'
            }
        }
    
    def close(self):
        """Close all UART connections"""
        logger.info("Closing UART connections...")
        
        # Send safe state before closing
        try:
            if self.esp_bc_connected:
                logger.info("Sending safe state to ESP-BC...")
                self.update_esp_bc(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        except:
            pass
        
        try:
            if self.esp_e_enabled and self.esp_e_connected:
                logger.info("Sending safe state to ESP-E...")
                self.update_esp_e(0.0)
        except:
            pass
        
        # Close connections
        self.esp_bc.disconnect()
        if self.esp_e_enabled:
            self.esp_e.disconnect()
        
        logger.info("✅ UART Master closed")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("\n" + "="*70)
    print("Testing UART Master - ESP-BC Only")
    print("="*70)
    
    try:
        # Initialize (ESP-E disabled)
        master = UARTMaster(esp_bc_port='/dev/ttyAMA0', esp_e_port=None)
        
        # Wait for ESP to be fully ready
        print("\n⏳ Waiting 1 second for ESP32 to stabilize...")
        time.sleep(1.0)
        
        # Test ESP-BC
        print("\n[TEST] ESP-BC Communication...")
        success = master.update_esp_bc(
            safety=50, shim=60, regulating=70,
            pump_primary=2, pump_secondary=2, pump_tertiary=1,
            humid_ct1=1, humid_ct2=0, humid_ct3=1, humid_ct4=0
        )
        
        if success:
            data = master.get_esp_bc_data()
            print(f"  ✅ Rod positions: {data.safety_actual}, {data.shim_actual}, {data.regulating_actual}")
            print(f"  ✅ Thermal power: {data.kw_thermal} kW")
            print(f"  ✅ Turbine power: {data.power_level}%")
            print(f"  ✅ Turbine speed: {data.turbine_speed}%")
            print(f"  ✅ Pump speeds: Primary={data.pump_primary_speed}%, Secondary={data.pump_secondary_speed}%, Tertiary={data.pump_tertiary_speed}%")
            print(f"  ✅ Turbine state: {data.state} (0=IDLE, 1=STARTING, 2=RUNNING, 3=SHUTDOWN)")
        else:
            print("  ❌ Failed to communicate with ESP-BC")
        
        # Health check
        print("\n[TEST] Health Status:")
        health = master.get_health_status()
        for esp, info in health.items():
            print(f"  {esp.upper()}: {info['status']} (errors: {info['error_count']})")
        
        # Close
        master.close()
        
        print("\n" + "="*70)
        print("✅ Test complete")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
