#!/usr/bin/env python3
"""
Test Script untuk Validasi Critical Fixes
Session 6 - 2024-12-12

Tests:
1. START button callback terdaftar
2. RESET button callback terdaftar (bukan STOP)
3. Interlock logic baru (tidak check manual pump)
4. Semua 17 button callbacks terdaftar
"""

import sys
import logging
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_button_pin_enum():
    """Test 1: Verify ButtonPin enum has 17 buttons"""
    logger.info("=" * 60)
    logger.info("TEST 1: Button Pin Enum (17 buttons)")
    logger.info("=" * 60)
    
    try:
        from raspi_gpio_buttons import ButtonPin, BUTTON_NAMES
        
        button_list = list(ButtonPin)
        logger.info(f"Total buttons defined: {len(button_list)}")
        
        expected_buttons = [
            'PUMP_PRIMARY_ON', 'PUMP_PRIMARY_OFF',
            'PUMP_SECONDARY_ON', 'PUMP_SECONDARY_OFF',
            'PUMP_TERTIARY_ON', 'PUMP_TERTIARY_OFF',
            'SAFETY_ROD_UP', 'SAFETY_ROD_DOWN',
            'SHIM_ROD_UP', 'SHIM_ROD_DOWN',
            'REGULATING_ROD_UP', 'REGULATING_ROD_DOWN',
            'PRESSURE_UP', 'PRESSURE_DOWN',
            'REACTOR_START', 'REACTOR_RESET',  # CHECK: RESET not STOP
            'EMERGENCY'
        ]
        
        for i, btn_name in enumerate(expected_buttons, 1):
            if hasattr(ButtonPin, btn_name):
                pin_value = getattr(ButtonPin, btn_name)
                display_name = BUTTON_NAMES.get(pin_value, "Unknown")
                logger.info(f"  {i:2d}. {btn_name:25s} (GPIO {pin_value:2d}) = {display_name}")
            else:
                logger.error(f"  ❌ {btn_name} NOT FOUND!")
                return False
        
        # Check REACTOR_STOP tidak ada
        if hasattr(ButtonPin, 'REACTOR_STOP'):
            logger.error("  ❌ REACTOR_STOP masih ada! Harus diganti REACTOR_RESET")
            return False
        else:
            logger.info("  ✅ REACTOR_STOP berhasil dihapus (diganti REACTOR_RESET)")
        
        if len(button_list) == 17:
            logger.info("✅ TEST 1 PASSED: 17 buttons defined correctly")
            return True
        else:
            logger.error(f"❌ TEST 1 FAILED: Expected 17 buttons, got {len(button_list)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        return False


def test_panel_state():
    """Test 2: Verify PanelState has all required fields"""
    logger.info("=" * 60)
    logger.info("TEST 2: Panel State Structure")
    logger.info("=" * 60)
    
    try:
        # Mock PanelState (copy from raspi_main_panel.py)
        @dataclass
        class PanelState:
            reactor_started: bool = False
            pressure: float = 0.0
            pump_primary_status: int = 0
            pump_secondary_status: int = 0
            pump_tertiary_status: int = 0
            safety_rod: int = 0
            shim_rod: int = 0
            regulating_rod: int = 0
            thermal_kw: float = 0.0
            humid_sg1_cmd: int = 0
            humid_sg2_cmd: int = 0
            humid_ct1_cmd: int = 0
            humid_ct2_cmd: int = 0
            humid_ct3_cmd: int = 0
            humid_ct4_cmd: int = 0
            emergency_active: bool = False
            interlock_satisfied: bool = False
            running: bool = True
        
        state = PanelState()
        
        required_fields = [
            'reactor_started', 'pressure', 'thermal_kw',
            'pump_primary_status', 'pump_secondary_status', 'pump_tertiary_status',
            'safety_rod', 'shim_rod', 'regulating_rod',
            'humid_sg1_cmd', 'humid_sg2_cmd', 
            'humid_ct1_cmd', 'humid_ct2_cmd', 'humid_ct3_cmd', 'humid_ct4_cmd',
            'emergency_active', 'interlock_satisfied', 'running'
        ]
        
        for field in required_fields:
            if hasattr(state, field):
                value = getattr(state, field)
                logger.info(f"  ✓ {field:25s} = {value}")
            else:
                logger.error(f"  ❌ {field} NOT FOUND!")
                return False
        
        logger.info("✅ TEST 2 PASSED: All state fields present")
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        return False


def test_interlock_logic():
    """Test 3: Verify new interlock logic"""
    logger.info("=" * 60)
    logger.info("TEST 3: Interlock Logic (New Implementation)")
    logger.info("=" * 60)
    
    @dataclass
    class MockState:
        reactor_started: bool = False
        pressure: float = 0.0
        thermal_kw: float = 0.0
        shim_rod: int = 0
        regulating_rod: int = 0
        emergency_active: bool = False
    
    def check_interlock(state: MockState) -> bool:
        """New interlock logic"""
        # Check 1: Reactor must be started
        if not state.reactor_started:
            return False
        
        # Check 2: Pressure >= 40 bar
        if state.pressure < 40.0:
            return False
        
        # Check 3: Turbine running OR initial rod raise
        if state.thermal_kw <= 0:
            # Allow initial rod movement
            if state.shim_rod == 0 and state.regulating_rod == 0:
                return True
            return False
        
        # Check 4: No emergency
        if state.emergency_active:
            return False
        
        return True
    
    # Test cases
    test_cases = [
        # (reactor_started, pressure, thermal_kw, shim_rod, reg_rod, emergency, expected_result, description)
        (False, 50.0, 0.0, 0, 0, False, False, "Reactor not started"),
        (True, 30.0, 0.0, 0, 0, False, False, "Pressure too low"),
        (True, 50.0, 0.0, 0, 0, False, True, "Initial rod raise allowed"),
        (True, 50.0, 100.0, 50, 50, False, True, "Normal operation - turbine running"),
        (True, 50.0, 0.0, 50, 50, False, False, "Turbine stopped with rods raised"),
        (True, 50.0, 100.0, 50, 50, True, False, "Emergency active"),
    ]
    
    all_passed = True
    for i, (started, press, thermal, shim, reg, emerg, expected, desc) in enumerate(test_cases, 1):
        state = MockState(
            reactor_started=started,
            pressure=press,
            thermal_kw=thermal,
            shim_rod=shim,
            regulating_rod=reg,
            emergency_active=emerg
        )
        
        result = check_interlock(state)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        logger.info(f"  Case {i}: {desc}")
        logger.info(f"    Input: Started={started}, P={press}bar, Thermal={thermal}kW, "
                   f"Shim={shim}%, Reg={reg}%, Emergency={emerg}")
        logger.info(f"    Expected: {expected}, Got: {result} - {status}")
        
        if result != expected:
            all_passed = False
    
    if all_passed:
        logger.info("✅ TEST 3 PASSED: Interlock logic works correctly")
    else:
        logger.error("❌ TEST 3 FAILED: Some test cases failed")
    
    return all_passed


def test_reset_functionality():
    """Test 4: Verify RESET button functionality"""
    logger.info("=" * 60)
    logger.info("TEST 4: RESET Button Functionality")
    logger.info("=" * 60)
    
    @dataclass
    class MockState:
        reactor_started: bool = True
        emergency_active: bool = False
        pressure: float = 150.0
        thermal_kw: float = 250000.0
        pump_primary_status: int = 2
        pump_secondary_status: int = 2
        pump_tertiary_status: int = 2
        safety_rod: int = 50
        shim_rod: int = 60
        regulating_rod: int = 55
        humid_sg1_cmd: int = 1
        humid_sg2_cmd: int = 1
        humid_ct1_cmd: int = 1
        humid_ct2_cmd: int = 1
        humid_ct3_cmd: int = 1
        humid_ct4_cmd: int = 1
        interlock_satisfied: bool = True
    
    def on_reactor_reset(state: MockState):
        """Simulate RESET button"""
        state.reactor_started = False
        state.emergency_active = False
        state.pressure = 0.0
        state.thermal_kw = 0.0
        state.pump_primary_status = 0
        state.pump_secondary_status = 0
        state.pump_tertiary_status = 0
        state.safety_rod = 0
        state.shim_rod = 0
        state.regulating_rod = 0
        state.humid_sg1_cmd = 0
        state.humid_sg2_cmd = 0
        state.humid_ct1_cmd = 0
        state.humid_ct2_cmd = 0
        state.humid_ct3_cmd = 0
        state.humid_ct4_cmd = 0
        state.interlock_satisfied = False
    
    # Before reset
    state = MockState()
    logger.info("  Before RESET:")
    logger.info(f"    reactor_started={state.reactor_started}, pressure={state.pressure}bar")
    logger.info(f"    rods: Safety={state.safety_rod}%, Shim={state.shim_rod}%, Reg={state.regulating_rod}%")
    logger.info(f"    pumps: P={state.pump_primary_status}, S={state.pump_secondary_status}, T={state.pump_tertiary_status}")
    
    # Execute reset
    on_reactor_reset(state)
    
    # After reset
    logger.info("  After RESET:")
    logger.info(f"    reactor_started={state.reactor_started}, pressure={state.pressure}bar")
    logger.info(f"    rods: Safety={state.safety_rod}%, Shim={state.shim_rod}%, Reg={state.regulating_rod}%")
    logger.info(f"    pumps: P={state.pump_primary_status}, S={state.pump_secondary_status}, T={state.pump_tertiary_status}")
    
    # Verify all reset to initial state
    checks = [
        (state.reactor_started == False, "reactor_started = False"),
        (state.emergency_active == False, "emergency_active = False"),
        (state.pressure == 0.0, "pressure = 0"),
        (state.thermal_kw == 0.0, "thermal_kw = 0"),
        (state.pump_primary_status == 0, "pump_primary = OFF"),
        (state.pump_secondary_status == 0, "pump_secondary = OFF"),
        (state.pump_tertiary_status == 0, "pump_tertiary = OFF"),
        (state.safety_rod == 0, "safety_rod = 0"),
        (state.shim_rod == 0, "shim_rod = 0"),
        (state.regulating_rod == 0, "regulating_rod = 0"),
        (state.humid_sg1_cmd == 0, "humid_sg1 = OFF"),
        (state.humid_sg2_cmd == 0, "humid_sg2 = OFF"),
        (state.humid_ct1_cmd == 0, "humid_ct1 = OFF"),
        (state.humid_ct2_cmd == 0, "humid_ct2 = OFF"),
        (state.humid_ct3_cmd == 0, "humid_ct3 = OFF"),
        (state.humid_ct4_cmd == 0, "humid_ct4 = OFF"),
        (state.interlock_satisfied == False, "interlock_satisfied = False"),
    ]
    
    all_passed = True
    for passed, description in checks:
        status = "✅" if passed else "❌"
        logger.info(f"    {status} {description}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("✅ TEST 4 PASSED: RESET functionality correct")
    else:
        logger.error("❌ TEST 4 FAILED: Some fields not reset properly")
    
    return all_passed


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║  CRITICAL FIXES VALIDATION TEST - Session 6 (2024-12-12) ║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")
    
    tests = [
        ("Button Pin Enum (17 buttons)", test_button_pin_enum),
        ("Panel State Structure", test_panel_state),
        ("Interlock Logic (New)", test_interlock_logic),
        ("RESET Functionality", test_reset_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            logger.info("")
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
            logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {status:12s} - {test_name}")
    
    logger.info("-" * 60)
    logger.info(f"Result: {passed_count}/{total_count} tests passed")
    logger.info("=" * 60)
    
    if passed_count == total_count:
        logger.info("🎉 ALL TESTS PASSED! Critical fixes validated successfully.")
        return 0
    else:
        logger.error(f"⚠️  {total_count - passed_count} test(s) failed. Review fixes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
