"""
I2C Master Communication Module
Handles communication with all ESP32 slaves
"""

import smbus2
import struct
import logging
import time
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ESP_B_Data:
    """Data structure for ESP-B (Batang Kendali & Reaktor)"""
    # To ESP-B
    pressure: float = 0.0
    pump1_status: int = 0
    pump2_status: int = 0
    
    # From ESP-B
    rod1_pos: int = 0
    rod2_pos: int = 0
    rod3_pos: int = 0
    kw_thermal: float = 0.0


@dataclass
class ESP_C_Data:
    """Data structure for ESP-C (Turbin & Generator)"""
    # To ESP-C
    rod1_pos: int = 0
    rod2_pos: int = 0
    rod3_pos: int = 0
    
    # From ESP-C
    power_level: float = 0.0
    state: int = 0
    generator_status: int = 0
    turbine_status: int = 0


@dataclass
class ESP_Visualizer_Data:
    """Data structure for ESP-E/F/G (Visualizer)"""
    # To ESP
    pressure: float = 0.0
    pump_status: int = 0
    
    # From ESP
    animation_speed: int = 0
    led_count: int = 0


class I2CMaster:
    """
    I2C Master for communicating with ESP32 slaves
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
            logger.info(f"I2C Master initialized on bus {bus_number}")
        except Exception as e:
            logger.error(f"Failed to initialize I2C Master: {e}")
            raise
        
        # Data storage
        self.esp_b_data = ESP_B_Data()
        self.esp_c_data = ESP_C_Data()
        self.esp_e_data = ESP_Visualizer_Data()
        self.esp_f_data = ESP_Visualizer_Data()
        self.esp_g_data = ESP_Visualizer_Data()
        
        # Error tracking
        self.error_counts = {
            0x08: 0, 0x09: 0, 0x0A: 0, 0x0B: 0, 0x0C: 0
        }
        self.last_comm_time = {
            0x08: 0, 0x09: 0, 0x0A: 0, 0x0B: 0, 0x0C: 0
        }
    
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
    # ESP-B Communication (Batang Kendali)
    # ============================================
    
    def update_esp_b(self, pressure: float, pump1_status: int, pump2_status: int) -> bool:
        """
        Send data to ESP-B and read response
        
        Args:
            pressure: Pressurizer pressure (bar)
            pump1_status: Primary pump status (0-3)
            pump2_status: Secondary pump status (0-3)
            
        Returns:
            True if successful, False otherwise
        """
        if self.mux_select:
            self.mux_select(0)  # Select ESP-B channel
        
        try:
            # Pack data: float, float(reserved), uint8, uint8
            write_data = struct.pack('<ffBB', pressure, 0.0, pump1_status, pump2_status)
            
            # Read response: 3 x uint8 (rod pos), 1 x uint8 (reserved), 3 x float
            response = self.write_read_with_retry(0x08, write_data, 16)
            
            if response:
                # Unpack response
                values = struct.unpack('<BBBBfff', response)
                self.esp_b_data.rod1_pos = values[0]
                self.esp_b_data.rod2_pos = values[1]
                self.esp_b_data.rod3_pos = values[2]
                # values[3] is reserved
                self.esp_b_data.kw_thermal = values[4]
                
                logger.debug(f"ESP-B: Rods=[{values[0]},{values[1]},{values[2]}], "
                           f"kwThermal={values[4]:.1f}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating ESP-B: {e}")
        
        return False
    
    def get_esp_b_data(self) -> ESP_B_Data:
        """Get latest data from ESP-B"""
        return self.esp_b_data
    
    # ============================================
    # ESP-C Communication (Turbin & Generator)
    # ============================================
    
    def update_esp_c(self, rod1: int, rod2: int, rod3: int) -> bool:
        """
        Send rod positions to ESP-C and read response
        
        Args:
            rod1, rod2, rod3: Rod positions (0-100%)
            
        Returns:
            True if successful, False otherwise
        """
        if self.mux_select:
            self.mux_select(1)  # Select ESP-C channel
        
        try:
            # Pack data: 3 x uint8
            write_data = struct.pack('<BBB', rod1, rod2, rod3)
            
            # Read response: float (power), uint32 (state), uint8 x 2 (status)
            response = self.write_read_with_retry(0x09, write_data, 10)
            
            if response:
                # Unpack response
                values = struct.unpack('<fIBB', response)
                self.esp_c_data.power_level = values[0]
                self.esp_c_data.state = values[1]
                self.esp_c_data.generator_status = values[2]
                self.esp_c_data.turbine_status = values[3]
                
                logger.debug(f"ESP-C: Power={values[0]:.1f}%, State={values[1]}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating ESP-C: {e}")
        
        return False
    
    def get_esp_c_data(self) -> ESP_C_Data:
        """Get latest data from ESP-C"""
        return self.esp_c_data
    
    # ============================================
    # ESP-E/F/G Communication (Visualizers)
    # ============================================
    
    def update_visualizer(self, esp_address: int, channel: int, 
                         pressure: float, pump_status: int) -> bool:
        """
        Send data to visualizer ESP
        
        Args:
            esp_address: ESP I2C address (0x0A/0x0B/0x0C)
            channel: TCA9548A channel
            pressure: Pressure value
            pump_status: Pump status
            
        Returns:
            True if successful, False otherwise
        """
        if self.mux_select:
            self.mux_select(channel)
        
        try:
            # Pack data: float, uint8
            write_data = struct.pack('<fB', pressure, pump_status)
            
            # Read response: 2 x uint8 (optional, for debugging)
            response = self.write_read_with_retry(esp_address, write_data, 2)
            
            if response:
                values = struct.unpack('<BB', response)
                
                # Store data based on address
                if esp_address == 0x0A:
                    self.esp_e_data.animation_speed = values[0]
                    self.esp_e_data.led_count = values[1]
                elif esp_address == 0x0B:
                    self.esp_f_data.animation_speed = values[0]
                    self.esp_f_data.led_count = values[1]
                elif esp_address == 0x0C:
                    self.esp_g_data.animation_speed = values[0]
                    self.esp_g_data.led_count = values[1]
                
                logger.debug(f"ESP-{chr(0x45+esp_address-0x0A)}: Speed={values[0]}, LEDs={values[1]}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating ESP 0x{esp_address:02X}: {e}")
        
        return False
    
    def update_esp_e(self, pressure: float, pump_status: int) -> bool:
        """Update ESP-E (Visualizer Primer)"""
        return self.update_visualizer(0x0A, 2, pressure, pump_status)
    
    def update_esp_f(self, pressure: float, pump_status: int) -> bool:
        """Update ESP-F (Visualizer Sekunder)"""
        return self.update_visualizer(0x0B, 3, pressure, pump_status)
    
    def update_esp_g(self, pressure: float, pump_status: int) -> bool:
        """Update ESP-G (Visualizer Tersier)"""
        return self.update_visualizer(0x0C, 4, pressure, pump_status)
    
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
        
        for addr in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
            last_comm = self.last_comm_time[addr]
            time_since = current_time - last_comm if last_comm > 0 else -1
            
            health[addr] = {
                'error_count': self.error_counts[addr],
                'last_comm': last_comm,
                'time_since': time_since,
                'status': 'OK' if self.error_counts[addr] < 5 else 'ERROR'
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
    
    print("Testing I2C Master...")
    
    try:
        master = I2CMaster(bus_number=1)
        
        # Test ESP-B communication
        print("\nTesting ESP-B communication...")
        success = master.update_esp_b(pressure=150.0, pump1_status=2, pump2_status=2)
        
        if success:
            data = master.get_esp_b_data()
            print(f"  Rod positions: {data.rod1_pos}, {data.rod2_pos}, {data.rod3_pos}")
            print(f"  Thermal power: {data.kw_thermal} kW")
        else:
            print("  Failed to communicate with ESP-B")
        
        # Health check
        print("\nHealth Status:")
        health = master.get_health_status()
        for addr, info in health.items():
            print(f"  ESP 0x{addr:02X}: {info['status']} (errors: {info['error_count']})")
        
        master.close()
        
    except Exception as e:
        print(f"Error: {e}")
