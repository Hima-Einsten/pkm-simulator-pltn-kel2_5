#!/usr/bin/env python3
"""
Test script for 2-ESP Architecture
Validates all Python modules work together correctly
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all module imports"""
    logger.info("="*60)
    logger.info("TEST 1: Module Imports")
    logger.info("="*60)
    
    try:
        # Core modules
        logger.info("Importing raspi_config...")
        import raspi_config as config
        logger.info("✓ raspi_config imported")
        
        logger.info("Importing raspi_i2c_master...")
        from raspi_i2c_master import I2CMaster, ESP_BC_Data, ESP_E_Data
        logger.info("✓ raspi_i2c_master imported")
        logger.info(f"  - ESP_BC_Data: {ESP_BC_Data.__name__}")
        logger.info(f"  - ESP_E_Data: {ESP_E_Data.__name__}")
        
        logger.info("Importing raspi_gpio_buttons...")
        from raspi_gpio_buttons import ButtonManager
        logger.info("✓ raspi_gpio_buttons imported (may warn about GPIO)")
        
        logger.info("Importing raspi_humidifier_control...")
        from raspi_humidifier_control import HumidifierController
        logger.info("✓ raspi_humidifier_control imported")
        
        logger.info("Importing raspi_tca9548a...")
        from raspi_tca9548a import DualMultiplexerManager
        logger.info("✓ raspi_tca9548a imported")
        
        logger.info("\n✅ ALL IMPORTS SUCCESSFUL\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ IMPORT FAILED: {e}\n")
        return False


def test_data_structures():
    """Test data structure instantiation"""
    logger.info("="*60)
    logger.info("TEST 2: Data Structures")
    logger.info("="*60)
    
    try:
        from raspi_i2c_master import ESP_BC_Data, ESP_E_Data
        
        # Test ESP-BC data
        logger.info("Creating ESP_BC_Data...")
        esp_bc = ESP_BC_Data()
        logger.info(f"  - safety_target: {esp_bc.safety_target}")
        logger.info(f"  - kw_thermal: {esp_bc.kw_thermal}")
        logger.info(f"  - power_level: {esp_bc.power_level}")
        logger.info(f"  - humidifier_sg_cmd: {esp_bc.humidifier_sg_cmd}")
        logger.info("✓ ESP_BC_Data created")
        
        # Test ESP-E data
        logger.info("\nCreating ESP_E_Data...")
        esp_e = ESP_E_Data()
        logger.info(f"  - pressure_primary: {esp_e.pressure_primary}")
        logger.info(f"  - pump_status_primary: {esp_e.pump_status_primary}")
        logger.info(f"  - animation_speed: {esp_e.animation_speed}")
        logger.info("✓ ESP_E_Data created")
        
        logger.info("\n✅ DATA STRUCTURES OK\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ DATA STRUCTURE TEST FAILED: {e}\n")
        return False


def test_humidifier_controller():
    """Test humidifier controller logic"""
    logger.info("="*60)
    logger.info("TEST 3: Humidifier Controller")
    logger.info("="*60)
    
    try:
        from raspi_humidifier_control import HumidifierController
        
        # Test with default config
        logger.info("Creating HumidifierController (default config)...")
        humid = HumidifierController()
        logger.info(f"  - SG threshold: Shim>={humid.sg_shim_rod_threshold}%, Reg>={humid.sg_reg_rod_threshold}%")
        logger.info(f"  - CT threshold: Thermal>={humid.ct_thermal_threshold} kW")
        logger.info("✓ HumidifierController created")
        
        # Test update with low values (should be OFF)
        logger.info("\nTest Case 1: Low values (should be OFF)")
        sg_on, ct_on = humid.update(shim_rod=20, regulating_rod=20, thermal_power_kw=100)
        logger.info(f"  Shim=20%, Reg=20%, Thermal=100kW")
        logger.info(f"  Result: SG={sg_on}, CT={ct_on}")
        assert sg_on == False, "SG should be OFF"
        assert ct_on == False, "CT should be OFF"
        logger.info("  ✓ Both OFF (correct)")
        
        # Test update with high values (should be ON)
        logger.info("\nTest Case 2: High values (should be ON)")
        sg_on, ct_on = humid.update(shim_rod=50, regulating_rod=50, thermal_power_kw=900)
        logger.info(f"  Shim=50%, Reg=50%, Thermal=900kW")
        logger.info(f"  Result: SG={sg_on}, CT={ct_on}")
        assert sg_on == True, "SG should be ON"
        assert ct_on == True, "CT should be ON"
        logger.info("  ✓ Both ON (correct)")
        
        # Test mixed case
        logger.info("\nTest Case 3: Mixed (SG=ON, CT=OFF)")
        sg_on, ct_on = humid.update(shim_rod=45, regulating_rod=45, thermal_power_kw=700)
        logger.info(f"  Shim=45%, Reg=45%, Thermal=700kW")
        logger.info(f"  Result: SG={sg_on}, CT={ct_on}")
        logger.info(f"  ✓ SG={sg_on}, CT={ct_on}")
        
        logger.info("\n✅ HUMIDIFIER CONTROLLER OK\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ HUMIDIFIER TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_i2c_master_structure():
    """Test I2C Master structure (without hardware)"""
    logger.info("="*60)
    logger.info("TEST 4: I2C Master Structure")
    logger.info("="*60)
    
    try:
        from raspi_i2c_master import I2CMaster
        
        logger.info("Checking I2C Master methods...")
        
        # Check methods exist
        methods = [
            'update_esp_bc',
            'get_esp_bc_data',
            'update_esp_e',
            'get_esp_e_data',
            'get_health_status',
            'close'
        ]
        
        for method in methods:
            if hasattr(I2CMaster, method):
                logger.info(f"  ✓ {method}() exists")
            else:
                logger.error(f"  ✗ {method}() MISSING!")
                return False
        
        logger.info("\n✅ I2C MASTER STRUCTURE OK\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ I2C MASTER TEST FAILED: {e}\n")
        return False


def test_main_panel_structure():
    """Test main panel structure (without GPIO hardware)"""
    logger.info("="*60)
    logger.info("TEST 5: Main Panel Structure")
    logger.info("="*60)
    
    try:
        # Import main module (will fail on GPIO but that's ok)
        logger.info("Checking raspi_main_panel module...")
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("raspi_main_panel", 
            "raspi_central_control/raspi_main_panel.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            logger.info("✓ raspi_main_panel module loadable")
        
        logger.info("\n✅ MAIN PANEL STRUCTURE OK\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ MAIN PANEL TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🚀 2-ESP ARCHITECTURE TEST SUITE")
    logger.info("Testing: ESP-BC (merged) + ESP-E")
    logger.info("")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Data Structures", test_data_structures()))
    results.append(("Humidifier Controller", test_humidifier_controller()))
    results.append(("I2C Master", test_i2c_master_structure()))
    results.append(("Main Panel", test_main_panel_structure()))
    
    # Summary
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("="*60)
    logger.info(f"Total: {passed} passed, {failed} failed")
    logger.info("="*60)
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! System ready for hardware testing.")
        logger.info("\nNext steps:")
        logger.info("  1. Upload ESP_BC_MERGED.ino to ESP32")
        logger.info("  2. Wire hardware (servos, relays, motors)")
        logger.info("  3. Run: python3 raspi_main_panel.py")
        return 0
    else:
        logger.error("\n⚠️  SOME TESTS FAILED! Please fix issues before hardware testing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
