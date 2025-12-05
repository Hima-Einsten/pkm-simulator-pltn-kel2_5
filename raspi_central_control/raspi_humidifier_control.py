#!/usr/bin/env python3
"""
Humidifier Control Logic for PLTN Simulator
Handles 2 humidifiers:
1. Steam Generator Humidifier - Based on Shim + Regulating Rod positions
2. Cooling Tower Humidifier - Based on Thermal Power (kW)
"""

import logging

logger = logging.getLogger(__name__)

class HumidifierController:
    """
    Controls 2 humidifiers based on system conditions:
    - Steam Generator: Based on specific control rods
    - Cooling Tower: Based on thermal power output
    """
    
    def __init__(self, config=None):
        """
        Initialize humidifier controller
        
        Args:
            config: Optional configuration dict with thresholds
        """
        # Use config if provided, otherwise use defaults
        if config is None:
            config = {}
        
        # Thresholds for Steam Generator Humidifier
        self.sg_shim_rod_threshold = config.get('sg_shim_rod_threshold', 40.0)  # 40%
        self.sg_reg_rod_threshold = config.get('sg_reg_rod_threshold', 40.0)    # 40%
        self.sg_hysteresis = config.get('sg_hysteresis', 5.0)  # 5% hysteresis
        
        # Thresholds for Cooling Tower Humidifier
        self.ct_thermal_threshold = config.get('ct_thermal_threshold', 800.0)  # 800 kW
        self.ct_hysteresis = config.get('ct_hysteresis', 100.0)  # 100 kW hysteresis
        
        # Current states
        self.steam_gen_humidifier = False
        self.cooling_tower_humidifier = False
        
        # History for hysteresis
        self.sg_last_state = False
        self.ct_last_state = False
        
        logger.info("Humidifier Controller initialized")
        logger.info(f"  Steam Gen: Shim>={self.sg_shim_rod_threshold}% AND Reg>={self.sg_reg_rod_threshold}%")
        logger.info(f"  Cooling Tower: Thermal>={self.ct_thermal_threshold} kW")
    
    def update_steam_gen_humidifier(self, shim_rod_pos, regulating_rod_pos):
        """
        Update Steam Generator Humidifier based on rod positions
        
        Logic:
        - ON when BOTH Shim Rod >= threshold AND Regulating Rod >= threshold
        - OFF when EITHER rod falls below (threshold - hysteresis)
        
        Args:
            shim_rod_pos: Shim rod position (0-100%)
            regulating_rod_pos: Regulating rod position (0-100%)
            
        Returns:
            bool: True if humidifier should be ON, False otherwise
        """
        # Calculate thresholds with hysteresis
        if self.sg_last_state:
            # Currently ON - use lower threshold to turn OFF
            on_threshold = self.sg_shim_rod_threshold - self.sg_hysteresis
            on_threshold_reg = self.sg_reg_rod_threshold - self.sg_hysteresis
        else:
            # Currently OFF - use normal threshold to turn ON
            on_threshold = self.sg_shim_rod_threshold
            on_threshold_reg = self.sg_reg_rod_threshold
        
        # Check conditions
        shim_ok = shim_rod_pos >= on_threshold
        reg_ok = regulating_rod_pos >= on_threshold_reg
        
        # Both must be above threshold
        new_state = shim_ok and reg_ok
        
        # Log state change
        if new_state != self.sg_last_state:
            if new_state:
                logger.info(f"🌊 Steam Gen Humidifier ON: Shim={shim_rod_pos:.1f}% Reg={regulating_rod_pos:.1f}%")
            else:
                logger.info(f"⭕ Steam Gen Humidifier OFF: Shim={shim_rod_pos:.1f}% Reg={regulating_rod_pos:.1f}%")
        
        self.sg_last_state = new_state
        self.steam_gen_humidifier = new_state
        return new_state
    
    def update_cooling_tower_humidifier(self, thermal_power_kw):
        """
        Update Cooling Tower Humidifier based on thermal power
        
        Logic:
        - ON when thermal power >= threshold
        - OFF when thermal power < (threshold - hysteresis)
        
        Args:
            thermal_power_kw: Thermal power output in kW
            
        Returns:
            bool: True if humidifier should be ON, False otherwise
        """
        # Calculate threshold with hysteresis
        if self.ct_last_state:
            # Currently ON - use lower threshold to turn OFF
            on_threshold = self.ct_thermal_threshold - self.ct_hysteresis
        else:
            # Currently OFF - use normal threshold to turn ON
            on_threshold = self.ct_thermal_threshold
        
        # Check condition
        new_state = thermal_power_kw >= on_threshold
        
        # Log state change
        if new_state != self.ct_last_state:
            if new_state:
                logger.info(f"🌊 Cooling Tower Humidifier ON: Thermal={thermal_power_kw:.1f} kW")
            else:
                logger.info(f"⭕ Cooling Tower Humidifier OFF: Thermal={thermal_power_kw:.1f} kW")
        
        self.ct_last_state = new_state
        self.cooling_tower_humidifier = new_state
        return new_state
    
    def update(self, shim_rod, regulating_rod, thermal_power_kw):
        """
        Update both humidifiers based on current system state
        
        Args:
            shim_rod: Shim rod position (0-100%)
            regulating_rod: Regulating rod position (0-100%)
            thermal_power_kw: Thermal power in kW
            
        Returns:
            tuple: (steam_gen_on, cooling_tower_on) as (bool, bool)
        """
        # Update Steam Generator humidifier (based on Shim + Regulating rods)
        sg_on = self.update_steam_gen_humidifier(shim_rod, regulating_rod)
        
        # Update Cooling Tower humidifier (based on thermal power)
        ct_on = self.update_cooling_tower_humidifier(thermal_power_kw)
        
        # Return as boolean tuple
        return (sg_on, ct_on)
    
    def update_all(self, safety_rod, shim_rod, regulating_rod, thermal_power_kw):
        """
        DEPRECATED: Use update() instead (safety_rod not needed)
        Update both humidifiers based on current system state
        
        Args:
            safety_rod: Safety rod position (0-100%) - not used for humidifier
            shim_rod: Shim rod position (0-100%)
            regulating_rod: Regulating rod position (0-100%)
            thermal_power_kw: Thermal power in kW
            
        Returns:
            tuple: (steam_gen_command, cooling_tower_command) as (0/1, 0/1)
        """
        sg_on, ct_on = self.update(shim_rod, regulating_rod, thermal_power_kw)
        return (1 if sg_on else 0, 1 if ct_on else 0)
    
    def get_status(self):
        """
        Get current humidifier status
        
        Returns:
            dict: Status information
        """
        return {
            'steam_gen_humidifier': self.steam_gen_humidifier,
            'cooling_tower_humidifier': self.cooling_tower_humidifier,
            'sg_threshold': self.sg_shim_rod_threshold,
            'ct_threshold': self.ct_thermal_threshold
        }

# ============================================
# Configuration Example
# ============================================

HUMIDIFIER_CONFIG_DEFAULT = {
    # Steam Generator Humidifier thresholds
    'sg_shim_rod_threshold': 40.0,      # Shim rod must be >= 40%
    'sg_reg_rod_threshold': 40.0,       # Regulating rod must be >= 40%
    'sg_hysteresis': 5.0,               # Turn off when < 35%
    
    # Cooling Tower Humidifier thresholds
    'ct_thermal_threshold': 800.0,      # Turn on when >= 800 kW
    'ct_hysteresis': 100.0,             # Turn off when < 700 kW
}

# Alternative configurations for different scenarios
HUMIDIFIER_CONFIG_CONSERVATIVE = {
    'sg_shim_rod_threshold': 50.0,      # Higher threshold
    'sg_reg_rod_threshold': 50.0,
    'sg_hysteresis': 10.0,
    'ct_thermal_threshold': 1000.0,     # Higher threshold
    'ct_hysteresis': 150.0,
}

HUMIDIFIER_CONFIG_AGGRESSIVE = {
    'sg_shim_rod_threshold': 30.0,      # Lower threshold
    'sg_reg_rod_threshold': 30.0,
    'sg_hysteresis': 3.0,
    'ct_thermal_threshold': 600.0,      # Lower threshold
    'ct_hysteresis': 75.0,
}

# ============================================
# Test Function
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("="*60)
    print("  Humidifier Controller Test")
    print("="*60)
    
    # Create controller with default config
    controller = HumidifierController(HUMIDIFIER_CONFIG_DEFAULT)
    
    print("\nTest Scenario 1: Gradually increase rods and thermal power")
    print("-" * 60)
    
    # Simulate gradual increase
    test_scenarios = [
        (0, 0, 0, 0, "Initial state - all zero"),
        (20, 20, 20, 300, "Low power - rods at 20%"),
        (40, 40, 40, 600, "Moderate - rods at 40%"),
        (45, 45, 45, 850, "Higher - rods at 45%, thermal >800kW"),
        (60, 60, 60, 1200, "High power - rods at 60%"),
        (40, 35, 40, 750, "Decreasing - one rod below threshold"),
        (30, 30, 30, 500, "Low again - back to baseline"),
    ]
    
    for safety, shim, reg, thermal, desc in test_scenarios:
        print(f"\n{desc}")
        print(f"  Rods: Safety={safety}%, Shim={shim}%, Reg={reg}%")
        print(f"  Thermal: {thermal} kW")
        
        sg_cmd, ct_cmd = controller.update_all(safety, shim, reg, thermal)
        
        print(f"  → Steam Gen Humidifier: {'ON' if sg_cmd else 'OFF'}")
        print(f"  → Cooling Tower Humidifier: {'ON' if ct_cmd else 'OFF'}")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)
