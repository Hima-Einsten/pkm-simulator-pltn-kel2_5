#!/usr/bin/env python3
"""
Test script to verify button callback flow and threading behavior
Tests for deadlocks, hangs, and proper state updates
"""

import time
import logging
import threading
from dataclasses import dataclass

# Setup logging to see detailed flow
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(threadName)-12s] %(levelname)-7s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class MockState:
    """Mock state for testing"""
    reactor_started: bool = False
    pressure: float = 0.0
    running: bool = True
    

class MockController:
    """Simplified controller to test threading behavior"""
    
    def __init__(self):
        self.state = MockState()
        self.state_lock = threading.Lock()
        logger.info("MockController initialized")
    
    def on_reactor_start(self):
        """Simulated callback"""
        logger.info(">>> Callback: on_reactor_start - ENTRY")
        try:
            logger.info("Attempting to acquire state_lock...")
            with self.state_lock:
                logger.info("state_lock ACQUIRED")
                if not self.state.reactor_started:
                    self.state.reactor_started = True
                    logger.info("🟢 REACTOR STARTED")
                logger.info("Releasing state_lock...")
            logger.info("state_lock RELEASED")
            logger.info(">>> Callback: on_reactor_start - EXIT SUCCESS")
        except Exception as e:
            logger.error(f">>> Callback: on_reactor_start - EXCEPTION: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def on_pressure_up(self):
        """Simulated callback"""
        logger.info(">>> Callback: on_pressure_up - ENTRY")
        try:
            logger.info("Attempting to acquire state_lock...")
            with self.state_lock:
                logger.info("state_lock ACQUIRED")
                if not self.state.reactor_started:
                    logger.warning("⚠️  Reactor not started!")
                    return
                self.state.pressure += 5.0
                logger.info(f"Pressure updated: {self.state.pressure} bar")
                logger.info("Releasing state_lock...")
            logger.info("state_lock RELEASED")
            logger.info(">>> Callback: on_pressure_up - EXIT SUCCESS")
        except Exception as e:
            logger.error(f">>> Callback: on_pressure_up - EXCEPTION: {e}")
    
    def control_logic_thread(self):
        """Simulated control logic thread"""
        logger.info("Control logic thread started")
        
        loop_count = 0
        while self.state.running:
            try:
                logger.debug("Control: Attempting to acquire state_lock...")
                with self.state_lock:
                    logger.debug("Control: state_lock ACQUIRED")
                    # Simulate work
                    time.sleep(0.001)
                    logger.debug("Control: Releasing state_lock...")
                logger.debug("Control: state_lock RELEASED")
                
                time.sleep(0.05)  # 50ms
                
                loop_count += 1
                if loop_count >= 20:  # Log every second
                    logger.info("Control logic: alive (20 loops)")
                    loop_count = 0
                
            except Exception as e:
                logger.error(f"Error in control logic: {e}")
                time.sleep(0.1)
        
        logger.info("Control logic thread stopped")
    
    def button_polling_thread(self):
        """Simulated button polling"""
        logger.info("Button polling thread started")
        
        # Simulate button presses
        time.sleep(0.5)
        logger.info("\n" + "="*60)
        logger.info("SIMULATING: START button press")
        logger.info("="*60)
        self.on_reactor_start()
        
        time.sleep(1.0)
        logger.info("\n" + "="*60)
        logger.info("SIMULATING: PRESSURE UP button press")
        logger.info("="*60)
        self.on_pressure_up()
        
        time.sleep(1.0)
        logger.info("\n" + "="*60)
        logger.info("SIMULATING: PRESSURE UP button press (2nd time)")
        logger.info("="*60)
        self.on_pressure_up()
        
        time.sleep(1.0)
        logger.info("\n" + "="*60)
        logger.info("TEST COMPLETE - Stopping system")
        logger.info("="*60)
        self.state.running = False
        
        logger.info("Button polling thread stopped")


def main():
    """Run threading test"""
    logger.info("="*70)
    logger.info("BUTTON CALLBACK FLOW TEST")
    logger.info("Testing for deadlocks, hangs, and proper state updates")
    logger.info("="*70)
    
    controller = MockController()
    
    # Start threads
    threads = [
        threading.Thread(target=controller.control_logic_thread, daemon=True, name="ControlThread"),
        threading.Thread(target=controller.button_polling_thread, daemon=True, name="ButtonThread"),
    ]
    
    for t in threads:
        t.start()
        logger.info(f"Started: {t.name}")
    
    # Wait for threads
    for t in threads:
        t.join(timeout=10.0)  # Max 10 seconds
        if t.is_alive():
            logger.error(f"⚠️  THREAD TIMEOUT: {t.name} is still running!")
        else:
            logger.info(f"✓ {t.name} completed")
    
    logger.info("="*70)
    logger.info("FINAL STATE:")
    logger.info(f"  reactor_started: {controller.state.reactor_started}")
    logger.info(f"  pressure: {controller.state.pressure} bar")
    logger.info("="*70)
    
    if controller.state.reactor_started and controller.state.pressure == 10.0:
        logger.info("✅ TEST PASSED - All callbacks executed successfully")
    else:
        logger.error("❌ TEST FAILED - State not updated correctly")


if __name__ == "__main__":
    main()
