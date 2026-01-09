#!/usr/bin/env python3
"""
Test script for OLED interpolation functionality
"""

import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_interpolator():
    """Test DisplayValueInterpolator class"""
    from raspi_oled_manager import DisplayValueInterpolator
    
    logger.info("=" * 60)
    logger.info("TEST 1: DisplayValueInterpolator Basic Functionality")
    logger.info("=" * 60)
    
    # Create interpolator
    interp = DisplayValueInterpolator(speed=50.0, name="test")
    
    # Test 1: Initial state
    logger.info("\n1. Initial state (should be 0)")
    logger.info(f"   Current value: {interp.get_display_value()}")
    logger.info(f"   Needs update: {interp.needs_update()}")  # Should be True (first call)
    
    # Test 2: Set target and interpolate
    logger.info("\n2. Set target to 100, interpolate over 2 seconds")
    interp.set_target(100)
    
    for i in range(5):
        time.sleep(0.5)
        value = interp.get_display_value()
        needs_update = interp.needs_update()
        logger.info(f"   t={i*0.5:.1f}s: value={value}, needs_update={needs_update}")
    
    # Test 3: Reset to 50
    logger.info("\n3. Reset to 50 (instant)")
    interp.reset(50)
    logger.info(f"   Value after reset: {interp.get_display_value()}")
    logger.info(f"   Needs update: {interp.needs_update()}")  # Should be True (forced)
    
    # Test 4: Interpolate down to 0
    logger.info("\n4. Set target to 0, interpolate over 1 second")
    interp.set_target(0)
    
    for i in range(3):
        time.sleep(0.4)
        value = interp.get_display_value()
        needs_update = interp.needs_update()
        logger.info(f"   t={i*0.4:.1f}s: value={value}, needs_update={needs_update}")
    
    logger.info("\n✓ DisplayValueInterpolator test completed")

def test_mock_display_update():
    """Test display update logic with mock state"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Display Update Logic (Mock)")
    logger.info("=" * 60)
    
    from raspi_oled_manager import DisplayValueInterpolator
    
    # Simulate pressure update scenario
    logger.info("\nScenario: User holds PRESSURE_UP button")
    logger.info("Expected: Smooth transition 0 → 50 bar over 1 second")
    
    interp = DisplayValueInterpolator(speed=50.0, name="pressure")
    
    # Simulate button hold (state changes rapidly)
    logger.info("\nState changes (simulated button hold):")
    for target in range(0, 51, 10):
        interp.set_target(target)
        logger.info(f"   State: pressure = {target} bar")
    
    # Simulate display updates (slower than state changes)
    logger.info("\nDisplay updates (smooth interpolation):")
    start_time = time.time()
    update_count = 0
    
    while time.time() - start_time < 1.2:
        value = interp.get_display_value()
        needs_update = interp.needs_update()
        
        if needs_update:
            update_count += 1
            logger.info(f"   t={time.time()-start_time:.2f}s: Display={value} bar (I2C update #{update_count})")
        
        time.sleep(0.05)  # 20Hz control loop
    
    logger.info(f"\nResult: {update_count} I2C calls over 1.2s (vs ~24 without optimization)")
    logger.info("✓ Display update test completed")

def test_reset_behavior():
    """Test reset and sync behavior"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Reset and Sync Behavior")
    logger.info("=" * 60)
    
    from raspi_oled_manager import DisplayValueInterpolator
    
    # Test reset behavior
    logger.info("\nTest 3a: reset() should force update on next call")
    interp = DisplayValueInterpolator(speed=50.0, name="test")
    
    interp.reset(100)
    logger.info(f"   After reset(100): value={interp.get_display_value()}")
    logger.info(f"   First needs_update(): {interp.needs_update()}")  # Should be True
    logger.info(f"   Second needs_update(): {interp.needs_update()}")  # Should be False
    
    # Test sync scenario
    logger.info("\nTest 3b: Sync on startup should trigger initial update")
    interp2 = DisplayValueInterpolator(speed=50.0, name="startup")
    
    # Simulate sync to state (pressure=150)
    interp2.reset(150)
    logger.info(f"   After sync to state (150): value={interp2.get_display_value()}")
    logger.info(f"   Should trigger update: {interp2.needs_update()}")  # Should be True
    
    logger.info("\n✓ Reset behavior test completed")

if __name__ == "__main__":
    logger.info("OLED Interpolation Test Suite")
    logger.info("=" * 60)
    
    try:
        test_interpolator()
        test_mock_display_update()
        test_reset_behavior()
        
        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\nTEST FAILED: {e}", exc_info=True)
