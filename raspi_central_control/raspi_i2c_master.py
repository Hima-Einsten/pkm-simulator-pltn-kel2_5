"""
I2C Master Communication Module - 2 ESP Architecture
Handles communication with 2 ESP32 slaves (ESP-BC and ESP-E)
"""

import smbus2
import struct
import logging
import time
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ESP_BC_Data:
    """Data structure for ESP-BC (Control Rods + Turbine + Humidifier) - MERGED"""
    # To ESP-BC
    safety_target: int = 0
    shim_target: int = 0
    regulating_target: int = 0
    humidifier_sg_cmd: int = 0
    humidifier_ct_cmd: int = 0
    
    # From ESP-BC
    safety_actual: int = 0
    shim_actual: int = 0
    regulating_actual: int = 0
    kw_thermal: float = 0.0
    power_level: float = 0.0
    state: int = 0
    generator_status: int = 0
    turbine_status: int = 0
    humidifier_sg_status: int = 0
    humidifier_ct_status: int = 0


@dataclass
class ESP_E_Data:
    """Data structure for ESP-E (3-Flow LED Visualizer)"""
    # To ESP-E
    pressure_primary: float = 0.0
    pump_status_primary: int = 0
    pressure_secondary: float = 0.0
    pump_status_secondary: int = 0
    pressure_tertiary: float = 0.0
    pump_status_tertiary: int = 0
    
    # From ESP-E
    animation_speed: int = 0
    led_count: int = 0


class I2CMaster:
    """
    I2C Master for communicating with 2 ESP32 slaves
    - ESP-BC (0x08): Control rods + Turbine + Humidifier
    - ESP-E (0x0A): 48 LED visualizer
    """
    
    def __init__(self, bus_number: int, mux_select_callback=None):
        """
        Initialize I2C Master
        
        Args:
            bus_number: I2C bus number
            mux_select_callback: Function to select TCA9548A channel
        """
        self.bus_number = bus_number
        self.mux_select = mux_select_callback
        
        try:
            self.bus = smbus2.SMBus(bus_number)
            logger.info(f"I2C Master initialized on bus {bus_number} (2 ESP Architecture)")
        except Exception as e:
            logger.error(f"Failed to initialize I2C Master: {e}")
            raise
        
        # Data storage (Only 2 ESP)
        self.esp_bc_data = ESP_BC_Data()
        self.esp_e_data = ESP_E_Data()
        
        # Error tracking
        self.error_counts = {0x08: 0, 0x0A: 0}
        self.last_comm_time = {0x08: 0, 0x0A: 0}
    
    def write_read_with_retry(self, address: int, write_data: bytes, 
                               read_length: int, retry_count: int = 3) -> Optional[bytes]:
        """
        Write data to slave and read response with retry logic
        
        Args:
            address: I2C slave address
            write_data: Bytes to write
            read_length: Number of bytes to read
            retry_count: Number of retries on failure
            
        Returns:
            Bytes read from slave, or None on failure
        """
        for attempt in range(retry_count):
            try:
                # Write data
                self.bus.write_i2c_block_data(address, 0x00, list(write_data))
                time.sleep(0.01)  # Short delay for slave to process
                
                # Read response
                data = self.bus.read_i2c_block_data(address, 0x00, read_length)
                
                # Update last communication time
                self.last_comm_time[address] = time.time()
                
                # Reset error count on success
                if self.error_counts[address] > 0:
                    logger.info(f"Communication restored with ESP 0x{address:02X}")
                    self.error_counts[address] = 0
                
                return bytes(data)
                
            except OSError as e:
                if e.errno == 121:  # Remote I/O error
                    logger.warning(f"ESP 0x{address:02X} not responding (attempt {attempt+1})")
                elif e.errno == 110:  # Timeout
                    logger.warning(f"I2C timeout for ESP 0x{address:02X} (attempt {attempt+1})")
                else:
                    logger.error(f"I2C error {e.errno} for ESP 0x{address:02X}")
                
                self.error_counts[address] += 1
                
                if attempt < retry_count - 1:
                    time.sleep(0.05)  # Delay before retry
                    
            except Exception as e:
                logger.error(f"Unexpected error communicating with ESP 0x{address:02X}: {e}")
                self.error_counts[address] += 1
                
                if attempt < retry_count - 1:
                    time.sleep(0.05)
        
        return None
    
    # ============================================
    # ESP-BC Communication (Control Rods + Turbine + Humidifier)
    # ============================================
    
    def update_esp_bc(self, safety: int, shim: int, regulating: int,
                      humid_sg_cmd: int, humid_ct_cmd: int) -> bool:
        """
        Send rod positions and humidifier commands to ESP-BC
        
        Args:
            safety: Safety rod target (0-100%)
            shim: Shim rod target (0-100%)
            regulating: Regulating rod target (0-100%)
            humid_sg_cmd: Steam Generator humidifier command (0/1)
            humid_ct_cmd: Cooling Tower humidifier command (0/1)
            
        Returns:
            True if successful, False otherwise
        """
        if self.mux_select:
            self.mux_select(0)  # Select ESP-BC channel
        
        try:
            # Update internal state
            self.esp_bc_data.safety_target = safety
            self.esp_bc_data.shim_target = shim
            self.esp_bc_data.regulating_target = regulating
            self.esp_bc_data.humidifier_sg_cmd = humid_sg_cmd
            self.esp_bc_data.humidifier_ct_cmd = humid_ct_cmd
            
            # Pack data: 12 bytes
            write_data = struct.pack('<BBBBfBBBB',
                                    safety, shim, regulating, 0,
                                    0.0,  # Reserved float
                                    humid_sg_cmd, humid_ct_cmd,
                                    0, 0)  # Reserved bytes
            
            # Read response: 20 bytes
            response = self.write_read_with_retry(0x08, write_data, 20)
            
            if response:
                # Unpack response
                values = struct.unpack('<BBBBffIBBBB', response)
                self.esp_bc_data.safety_actual = values[0]
                self.esp_bc_data.shim_actual = values[1]
                self.esp_bc_data.regulating_actual = values[2]
                # values[3] reserved
                self.esp_bc_data.kw_thermal = values[4]
                self.esp_bc_data.power_level = values[5]
                self.esp_bc_data.state = values[6]
                self.esp_bc_data.generator_status = values[7]
                self.esp_bc_data.turbine_status = values[8]
                self.esp_bc_data.humidifier_sg_status = values[9]
                self.esp_bc_data.humidifier_ct_status = values[10]
                
                logger.debug(f"ESP-BC: Rods=[{values[0]},{values[1]},{values[2]}], "
                           f"Thermal={values[4]:.1f}kW, Power={values[5]:.1f}%, "
                           f"Humid=[SG:{values[9]}, CT:{values[10]}]")
                return True
            
        except Exception as e:
            logger.error(f"Error updating ESP-BC: {e}")
        
        return False
    
    def get_esp_bc_data(self) -> ESP_BC_Data:
        """Get latest data from ESP-BC"""
        return self.esp_bc_data
    

    
    # ============================================
    # ESP-E Communication (3-Flow LED Visualizer)
    # ============================================
    
    def update_esp_e(self, 
                    pressure_primary: float, pump_status_primary: int,
                    pressure_secondary: float, pump_status_secondary: int,
                    pressure_tertiary: float, pump_status_tertiary: int) -> bool:
        """
        Update ESP-E with all 3 flow visualizers
        
        Args:
            pressure_primary: Primary flow pressure
            pump_status_primary: Primary pump status (0-3)
            pressure_secondary: Secondary flow pressure
            pump_status_secondary: Secondary pump status
            pressure_tertiary: Tertiary flow pressure
            pump_status_tertiary: Tertiary pump status
            
        Returns:
            True if successful, False otherwise
        """
        if self.mux_select:
            self.mux_select(2)  # Select ESP-E channel
        
        try:
            # Update internal state
            self.esp_e_data.pressure_primary = pressure_primary
            self.esp_e_data.pump_status_primary = pump_status_primary
            self.esp_e_data.pressure_secondary = pressure_secondary
            self.esp_e_data.pump_status_secondary = pump_status_secondary
            self.esp_e_data.pressure_tertiary = pressure_tertiary
            self.esp_e_data.pump_status_tertiary = pump_status_tertiary
            
            # Pack data: 16 bytes (3 x (float + uint8) + padding)
            write_data = struct.pack('<BfBfBfB',
                                    0,  # Register address
                                    pressure_primary, pump_status_primary,
                                    pressure_secondary, pump_status_secondary,
                                    pressure_tertiary, pump_status_tertiary)
            
            # Read response: 2 bytes
            response = self.write_read_with_retry(0x0A, write_data, 2)
            
            if response:
                values = struct.unpack('<BB', response)
                self.esp_e_data.animation_speed = values[0]
                self.esp_e_data.led_count = values[1]
                
                logger.debug(f"ESP-E: Speed={values[0]}, LEDs={values[1]}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating ESP-E: {e}")
        
        return False
    
    def get_esp_e_data(self) -> ESP_E_Data:
        """Get latest data from ESP-E"""
        return self.esp_e_data
    
    # ============================================
    # Health Check
    # ============================================
    
    def get_health_status(self) -> Dict[int, dict]:
        """
        Get health status of all ESP slaves
        
        Returns:
            Dictionary mapping addresses to health info
        """
        current_time = time.time()
        health = {}
        
        for addr in [0x08, 0x0A]:  # Only 2 ESP (ESP-BC and ESP-E)
            last_comm = self.last_comm_time.get(addr, 0)
            time_since = current_time - last_comm if last_comm > 0 else -1
            
            health[addr] = {
                'error_count': self.error_counts.get(addr, 0),
                'last_comm': last_comm,
                'time_since': time_since,
                'status': 'OK' if self.error_counts.get(addr, 0) < 5 else 'ERROR'
            }
        
        return health
    
    def close(self):
        """Close I2C bus"""
        try:
            self.bus.close()
            logger.info("I2C Master closed")
        except Exception as e:
            logger.error(f"Error closing I2C Master: {e}")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing I2C Master (2 ESP Architecture)...")
    
    try:
        master = I2CMaster(bus_number=1)
        
        # Test ESP-BC communication
        print("\nTesting ESP-BC communication...")
        success = master.update_esp_bc(
            safety=50, shim=60, regulating=70,
            humid_sg_cmd=1, humid_ct_cmd=1
        )
        
        if success:
            data = master.get_esp_bc_data()
            print(f"  Rod positions: {data.safety_actual}, {data.shim_actual}, {data.regulating_actual}")
            print(f"  Thermal power: {data.kw_thermal} kW")
            print(f"  Turbine power: {data.power_level}%")
            print(f"  Humidifiers: SG={data.humidifier_sg_status}, CT={data.humidifier_ct_status}")
        else:
            print("  Failed to communicate with ESP-BC")
        
        # Test ESP-E communication
        print("\nTesting ESP-E communication...")
        success = master.update_esp_e(
            pressure_primary=155.0, pump_status_primary=2,
            pressure_secondary=50.0, pump_status_secondary=2,
            pressure_tertiary=15.0, pump_status_tertiary=2
        )
        
        if success:
            data = master.get_esp_e_data()
            print(f"  Animation speed: {data.animation_speed}")
            print(f"  LED count: {data.led_count}")
        else:
            print("  Failed to communicate with ESP-E")
        
        # Health check
        print("\nHealth Status:")
        health = master.get_health_status()
        for addr, info in health.items():
            print(f"  ESP 0x{addr:02X}: {info['status']} (errors: {info['error_count']})")
        
        master.close()
        
    except Exception as e:
        print(f"Error: {e}")
