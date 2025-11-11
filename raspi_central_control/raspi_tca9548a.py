"""
TCA9548A I2C Multiplexer Driver
Manages dual TCA9548A for OLED displays and ESP slaves
"""

import smbus2
import logging
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
            logger.info(f"TCA9548A initialized on bus {bus_number}, address 0x{address:02X}")
        except Exception as e:
            logger.error(f"Failed to initialize TCA9548A: {e}")
            raise
    
    def select_channel(self, channel: int) -> bool:
        """
        Select an I2C channel (0-7)
        
        Args:
            channel: Channel number (0-7)
            
        Returns:
            True if successful, False otherwise
        """
        if channel < 0 or channel > 7:
            logger.error(f"Invalid channel: {channel}. Must be 0-7")
            return False
        
        try:
            # Write channel selection byte (bit mask)
            channel_mask = 1 << channel
            self.bus.write_byte(self.address, channel_mask)
            self.current_channel = channel
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
        """Close I2C bus connection"""
        try:
            self.disable_all_channels()
            self.bus.close()
            logger.info("TCA9548A closed")
        except Exception as e:
            logger.error(f"Error closing TCA9548A: {e}")


class DualMultiplexerManager:
    """
    Manages two TCA9548A multiplexers:
    - One for OLED displays
    - One for ESP32 slaves
    """
    
    def __init__(self, display_bus: int, esp_bus: int, 
                 display_addr: int = 0x70, esp_addr: int = 0x71):
        """
        Initialize dual multiplexer manager
        
        Args:
            display_bus: I2C bus for display multiplexer
            esp_bus: I2C bus for ESP multiplexer
            display_addr: Address of display multiplexer
            esp_addr: Address of ESP multiplexer
        """
        self.mux_display = TCA9548A(display_bus, display_addr)
        self.mux_esp = TCA9548A(esp_bus, esp_addr)
        logger.info("Dual multiplexer manager initialized")
    
    def select_display_channel(self, channel: int) -> bool:
        """Select OLED display channel"""
        return self.mux_display.select_channel(channel)
    
    def select_esp_channel(self, channel: int) -> bool:
        """Select ESP slave channel"""
        return self.mux_esp.select_channel(channel)
    
    def scan_all(self) -> dict:
        """
        Scan all channels on both multiplexers
        
        Returns:
            Dictionary with 'display' and 'esp' keys containing device maps
        """
        return {
            'display': self.mux_display.scan_channels(),
            'esp': self.mux_esp.scan_channels()
        }
    
    def close(self):
        """Close all multiplexer connections"""
        self.mux_display.close()
        self.mux_esp.close()
        logger.info("Dual multiplexer manager closed")


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
