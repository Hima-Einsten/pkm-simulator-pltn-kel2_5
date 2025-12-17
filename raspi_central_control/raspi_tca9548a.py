"""
TCA9548A I2C Multiplexer Driver
Manages dual TCA9548A for OLED displays and ESP slaves
"""

import smbus2
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class TCA9548A:
    """
    TCA9548A I2C Multiplexer Driver
    
    Allows selecting one of 8 I2C channels to communicate with devices
    that share the same I2C address.
    """
    
    def __init__(self, bus_number: int, address: int = 0x70):
        """
        Initialize TCA9548A multiplexer
        
        Args:
            bus_number: I2C bus number (0 or 1)
            address: I2C address of TCA9548A (default 0x70)
        """
        self.bus_number = bus_number
        self.address = address
        self.current_channel = None
        
        try:
            self.bus = smbus2.SMBus(bus_number)
            
            # Disable all channels on init (clear any previous state)
            try:
                self.bus.write_byte(self.address, 0x00)
                logger.debug(f"TCA9548A 0x{address:02X} channels cleared on init")
            except:
                pass  # Multiplexer might not be connected yet
            
            logger.info(f"TCA9548A initialized on bus {bus_number}, address 0x{address:02X}")
        except Exception as e:
            logger.error(f"Failed to initialize TCA9548A: {e}")
            raise
    
    def select_channel(self, channel: int, force: bool = False) -> bool:
        """
        Select an I2C channel (0-7)
        
        Optimization: Skip selection if channel is already active
        
        Args:
            channel: Channel number (0-7) or None to deselect
            force: Force channel selection even if already active
            
        Returns:
            True if successful, False otherwise
        """
        # Allow None to deselect all channels
        if channel is None:
            return self.disable_all_channels()
        
        if channel < 0 or channel > 7:
            logger.error(f"Invalid channel: {channel}. Must be 0-7")
            return False
        
        # Optimization: Skip if channel already selected
        if not force and self.current_channel == channel:
            logger.debug(f"Channel {channel} already active, skipping selection")
            return True
        
        try:
            # Write channel selection byte (bit mask)
            channel_mask = 1 << channel
            self.bus.write_byte(self.address, channel_mask)
            self.current_channel = channel
            
            # Small delay for I2C bus to settle (prevent bus collision)
            time.sleep(0.005)  # 5ms delay
            
            logger.debug(f"Selected TCA9548A channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to select channel {channel}: {e}")
            return False
    
    def disable_all_channels(self) -> bool:
        """
        Disable all channels (no device selected)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
            logger.debug("All TCA9548A channels disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable channels: {e}")
            return False
    
    def scan_channels(self) -> dict:
        """
        Scan all channels for connected I2C devices
        
        Returns:
            Dictionary mapping channel numbers to list of device addresses
        """
        devices = {}
        
        for channel in range(8):
            if self.select_channel(channel):
                channel_devices = []
                # Scan I2C addresses 0x03 to 0x77
                for addr in range(0x03, 0x78):
                    try:
                        self.bus.read_byte(addr)
                        channel_devices.append(addr)
                    except:
                        pass
                
                if channel_devices:
                    devices[channel] = channel_devices
                    logger.info(f"Channel {channel}: {[hex(a) for a in channel_devices]}")
        
        self.disable_all_channels()
        return devices
    
    def close(self):
        """Close I2C bus connection with proper cleanup"""
        try:
            # Disable all channels before closing
            self.disable_all_channels()
            
            # Close bus
            if hasattr(self, 'bus'):
                self.bus.close()
            
            logger.info("TCA9548A closed")
        except Exception as e:
            logger.error(f"Error closing TCA9548A: {e}")


class DualMultiplexerManager:
    """
    Manages two TCA9548A multiplexers:
    - TCA9548A #1 (0x70): ESP-BC + 7 OLED displays
    - TCA9548A #2 (0x71): ESP-E + 2 OLED displays
    
    Hardware Mapping:
    - MUX #1 (0x70):
      - Channel 0: ESP-BC (0x08) - Control Rods + Turbine + Humidifier
      - Channel 1-7: OLED #1-7 (all at 0x3C)
    - MUX #2 (0x71):
      - Channel 0: ESP-E (0x0A) - 48 LED Visualizer
      - Channel 1-2: OLED #8-9 (all at 0x3C)
    """
    
    def __init__(self, display_bus: int, esp_bus: int, 
                 display_addr: int = 0x70, esp_addr: int = 0x71):
        """
        Initialize dual multiplexer manager
        
        Args:
            display_bus: I2C bus for multiplexer #1 (0x70)
            esp_bus: I2C bus for multiplexer #2 (0x71)
            display_addr: Address of TCA9548A #1 (default 0x70)
            esp_addr: Address of TCA9548A #2 (default 0x71)
        """
        self.mux1 = TCA9548A(display_bus, display_addr)  # TCA9548A #1 (0x70)
        self.mux2 = TCA9548A(esp_bus, esp_addr)          # TCA9548A #2 (0x71)
        self.mux1_addr = display_addr
        self.mux2_addr = esp_addr
        self.last_mux = None  # Track which MUX was last used (1 or 2)
        logger.info(f"Dual multiplexer manager initialized:")
        logger.info(f"  MUX #1 (ESP-BC + OLED 1-7): 0x{display_addr:02X}")
        logger.info(f"  MUX #2 (ESP-E + OLED 8-9): 0x{esp_addr:02X}")
    
    def select_mux1_channel(self, channel: int) -> bool:
        """
        Select channel on TCA9548A #1 (0x70)
        - Channel 0: ESP-BC
        - Channel 1-7: OLED #1-7
        """
        return self.mux1.select_channel(channel)
    
    def select_mux2_channel(self, channel: int) -> bool:
        """
        Select channel on TCA9548A #2 (0x71)
        - Channel 0: ESP-E
        - Channel 1-2: OLED #8-9
        """
        return self.mux2.select_channel(channel)
    
    def select_display_channel(self, channel: int) -> bool:
        """
        Select OLED display channel (for backward compatibility with OLED manager)
        
        Maps OLED manager channel calls to physical multiplexer channels:
        - Channels 1-7: TCA9548A #1 (0x70), channels 1-7 → OLED #1-7
        - Channels 8-9 (via select_esp_channel 1-2): TCA9548A #2 (0x71), channels 1-2 → OLED #8-9
        
        NOTE: OLED manager code uses:
        - select_display_channel(1-7) for OLED #1-7 on MUX #1
        - select_esp_channel(1-2) for OLED #8-9 on MUX #2 (legacy naming, will be fixed)
        """
        if channel < 1 or channel > 7:
            logger.error(f"Invalid display channel: {channel}. Must be 1-7 for MUX #1")
            return False
        
        # Add delay when switching from MUX #2 to MUX #1
        if self.last_mux == 2:
            time.sleep(0.003)  # 3ms delay when switching between MUX
        
        # Direct mapping: channel 1-7 → MUX #1 channels 1-7
        logger.debug(f"OLED #{channel} → MUX #1 (0x{self.mux1_addr:02X}), Channel {channel}")
        result = self.mux1.select_channel(channel)
        if result:
            self.last_mux = 1
        return result
    
    def select_esp_channel(self, channel: int) -> bool:
        """
        Select channel on TCA9548A #2 (0x71)
        
        This is used for TWO purposes (legacy design):
        1. ESP-E communication: channel 0 (via I2C Master with esp_id=1)
        2. OLED #8-9 on MUX #2: channel 1-2 (via OLED manager)
        
        Args:
            channel: 0 = ESP-E, 1-2 = OLED #8-9
        """
        if channel < 0 or channel > 2:
            logger.error(f"Invalid MUX #2 channel: {channel}. Must be 0-2")
            return False
        
        # Add delay when switching from MUX #1 to MUX #2
        if self.last_mux == 1:
            time.sleep(0.003)  # 3ms delay when switching between MUX
        
        if channel == 0:
            logger.debug(f"ESP-E → MUX #2 (0x{self.mux2_addr:02X}), Channel 0")
        else:
            logger.debug(f"OLED #{channel + 7} → MUX #2 (0x{self.mux2_addr:02X}), Channel {channel}")
        
        result = self.mux2.select_channel(channel)
        if result:
            self.last_mux = 2
        return result
    
    def scan_all(self) -> dict:
        """
        Scan all channels on both multiplexers
        
        Returns:
            Dictionary with 'mux1' and 'mux2' keys containing device maps
        """
        return {
            'mux1': self.mux1.scan_channels(),
            'mux2': self.mux2.scan_channels()
        }
    
    def close(self):
        """Close all multiplexer connections with proper cleanup"""
        try:
            # Disable all channels on both multiplexers
            logger.info("Closing multiplexers and disabling all channels...")
            
            if hasattr(self, 'mux1'):
                self.mux1.close()
            
            if hasattr(self, 'mux2'):
                self.mux2.close()
            
            logger.info("Dual multiplexer manager closed")
        except Exception as e:
            logger.error(f"Error closing multiplexer manager: {e}")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing TCA9548A Multiplexer...")
    
    try:
        # Test single multiplexer
        mux = TCA9548A(bus_number=1, address=0x70)
        
        print("\nScanning all channels:")
        devices = mux.scan_channels()
        
        for channel, addrs in devices.items():
            print(f"  Channel {channel}: {[hex(a) for a in addrs]}")
        
        mux.close()
        
    except Exception as e:
        print(f"Error: {e}")
