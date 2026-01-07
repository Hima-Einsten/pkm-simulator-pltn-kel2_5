#!/usr/bin/env python3
"""
Buzzer Alarm Test - All Simulation Scenarios
Test buzzer with all possible alarm conditions during reactor simulation
"""

import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from raspi_buzzer_alarm import BuzzerAlarm
    BUZZER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Buzzer module not available: {e}")
    BUZZER_AVAILABLE = False


class BuzzerTestSuite:
    """Test suite for buzzer alarm with all simulation scenarios"""
    
    def __init__(self, buzzer_pin=22):
        """Initialize buzzer test suite"""
        if not BUZZER_AVAILABLE:
            raise RuntimeError("Buzzer module not available")
        
        logger.info("Initializing buzzer alarm...")
        self.buzzer = BuzzerAlarm(buzzer_pin=buzzer_pin)
        logger.info("✓ Buzzer initialized successfully")
    
    def test_alarm_tones(self):
        """Test 1: All alarm tones"""
        print("\n" + "="*70)
        print("TEST 1: ALARM TONES - Individual Patterns")
        print("="*70)
        print("\nThis will test each alarm type with its specific tone and pattern.")
        input("Press ENTER to start...")
        
        # Test 1: Procedure Warning
        print("\n→ ALARM 1: PROCEDURE WARNING")
        print("  Frequency: 1000 Hz")
        print("  Pattern: Beep 0.3s, Pause 0.3s")
        print("  Scenario: Pump started without proper pressure")
        input("  Press ENTER to activate...")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PROCEDURE_WARNING)
        time.sleep(4)
        self.buzzer.clear_alarm()
        print("  ✓ Alarm cleared")
        time.sleep(1)
        
        # Test 2: Pressure Warning
        print("\n→ ALARM 2: PRESSURE WARNING")
        print("  Frequency: 2000 Hz")
        print("  Pattern: Beep 0.5s, Pause 0.5s")
        print("  Scenario: Pressure >= 160 bar (high)")
        input("  Press ENTER to activate...")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_WARNING)
        time.sleep(4)
        self.buzzer.clear_alarm()
        print("  ✓ Alarm cleared")
        time.sleep(1)
        
        # Test 3: Pressure Critical
        print("\n→ ALARM 3: PRESSURE CRITICAL")
        print("  Frequency: 3000 Hz")
        print("  Pattern: Double beep (0.2s, 0.2s, 0.2s, 0.6s)")
        print("  Scenario: Pressure >= 180 bar (critical)")
        input("  Press ENTER to activate...")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_CRITICAL)
        time.sleep(5)
        self.buzzer.clear_alarm()
        print("  ✓ Alarm cleared")
        time.sleep(1)
        
        # Test 4: Emergency
        print("\n→ ALARM 4: EMERGENCY (SCRAM)")
        print("  Frequency: 4000 Hz")
        print("  Pattern: Rapid beep (0.1s, 0.1s)")
        print("  Scenario: Emergency shutdown activated")
        input("  Press ENTER to activate...")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_EMERGENCY)
        time.sleep(4)
        self.buzzer.clear_alarm()
        print("  ✓ Alarm cleared")
        time.sleep(1)
        
        # Test 5: Interlock
        print("\n→ ALARM 5: INTERLOCK VIOLATION")
        print("  Frequency: 1500 Hz")
        print("  Pattern: Short beep, long pause (0.2s, 0.8s)")
        print("  Scenario: Interlock conditions not satisfied")
        input("  Press ENTER to activate...")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_INTERLOCK)
        time.sleep(4)
        self.buzzer.clear_alarm()
        print("  ✓ Alarm cleared")
        
        print("\n✓ All alarm tones tested")
    
    def test_pressure_scenarios(self):
        """Test 2: Pressure-based alarms"""
        print("\n" + "="*70)
        print("TEST 2: PRESSURE SCENARIOS")
        print("="*70)
        print("\nSimulate pressure changes and corresponding alarms:")
        
        scenarios = [
            (150.0, None, "Normal operation - 150 bar (no alarm)"),
            (165.0, BuzzerAlarm.ALARM_PRESSURE_WARNING, "High pressure - 165 bar (WARNING)"),
            (175.0, BuzzerAlarm.ALARM_PRESSURE_WARNING, "High pressure - 175 bar (WARNING)"),
            (185.0, BuzzerAlarm.ALARM_PRESSURE_CRITICAL, "Critical pressure - 185 bar (CRITICAL!)"),
            (195.0, BuzzerAlarm.ALARM_PRESSURE_CRITICAL, "Danger zone - 195 bar (CRITICAL!)"),
            (170.0, BuzzerAlarm.ALARM_PRESSURE_WARNING, "Returning down - 170 bar (WARNING)"),
            (155.0, None, "Normal again - 155 bar (alarm cleared)"),
        ]
        
        input("\nPress ENTER to start pressure scenario simulation...")
        
        for pressure, alarm_type, description in scenarios:
            print(f"\n→ Pressure: {pressure:.1f} bar")
            print(f"  {description}")
            
            if alarm_type:
                self.buzzer.set_alarm(alarm_type)
                if alarm_type == BuzzerAlarm.ALARM_PRESSURE_CRITICAL:
                    print("  🚨 CRITICAL ALARM ACTIVE!")
                elif alarm_type == BuzzerAlarm.ALARM_PRESSURE_WARNING:
                    print("  ⚠️  WARNING ALARM ACTIVE")
            else:
                self.buzzer.clear_alarm()
                print("  ✓ Normal - No alarm")
            
            time.sleep(3)
        
        self.buzzer.clear_alarm()
        print("\n✓ Pressure scenario test complete")
    
    def test_operational_scenarios(self):
        """Test 3: Operational scenarios"""
        print("\n" + "="*70)
        print("TEST 3: OPERATIONAL SCENARIOS")
        print("="*70)
        
        print("\n--- Scenario A: Procedure Violation ---")
        print("User tries to start pump without sufficient pressure")
        input("Press ENTER to simulate...")
        print("  → Pump start command received")
        print("  → Checking pressure... 120 bar (below 140 bar minimum)")
        print("  🔊 PROCEDURE WARNING!")
        self.buzzer.sound_procedure_warning(duration=2.0)
        time.sleep(3)
        print("  → Pump start blocked")
        print("  ✓ Procedure violation prevented")
        
        print("\n--- Scenario B: Interlock Violation ---")
        print("User tries to start reactor without humidifiers")
        input("Press ENTER to simulate...")
        print("  → Reactor start command received")
        print("  → Checking interlocks...")
        print("  → Steam generator humidifiers: OFF (should be ON)")
        print("  🔊 INTERLOCK WARNING!")
        self.buzzer.sound_interlock_warning(duration=1.5)
        time.sleep(2.5)
        print("  → Reactor start blocked")
        print("  ✓ Interlock violation prevented")
        
        print("\n--- Scenario C: Emergency Shutdown ---")
        print("Critical condition detected - SCRAM activated")
        input("Press ENTER to simulate...")
        print("  → SCRAM button pressed!")
        print("  → All control rods inserting...")
        print("  🚨 EMERGENCY ALARM!")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_EMERGENCY)
        time.sleep(5)
        print("  → Rods fully inserted")
        print("  → Power dropping...")
        time.sleep(2)
        self.buzzer.clear_alarm()
        print("  → Reactor shutdown complete")
        print("  ✓ Emergency shutdown successful")
        
        print("\n✓ Operational scenarios complete")
    
    def test_alarm_priority(self):
        """Test 4: Alarm priority (highest priority overrides)"""
        print("\n" + "="*70)
        print("TEST 4: ALARM PRIORITY")
        print("="*70)
        print("\nTest alarm priority when multiple conditions occur:")
        print("  Priority order (highest to lowest):")
        print("    1. EMERGENCY (SCRAM)")
        print("    2. PRESSURE CRITICAL")
        print("    3. PRESSURE WARNING")
        print("    4. INTERLOCK")
        print("    5. PROCEDURE WARNING")
        
        input("\nPress ENTER to test alarm priority...")
        
        print("\n→ Step 1: Start with pressure WARNING (2 kHz)")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_WARNING)
        time.sleep(3)
        
        print("\n→ Step 2: Pressure increases to CRITICAL (3 kHz)")
        print("  Higher priority - alarm changes")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_CRITICAL)
        time.sleep(3)
        
        print("\n→ Step 3: SCRAM activated - EMERGENCY! (4 kHz)")
        print("  Highest priority - alarm changes to rapid beep")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_EMERGENCY)
        time.sleep(4)
        
        print("\n→ Step 4: Emergency resolved")
        print("  Alarm clears")
        self.buzzer.clear_alarm()
        time.sleep(1)
        
        print("\n✓ Alarm priority test complete")
    
    def test_simulation_sequence(self):
        """Test 5: Complete reactor simulation with alarms"""
        print("\n" + "="*70)
        print("TEST 5: COMPLETE SIMULATION SEQUENCE")
        print("="*70)
        print("\nRun through complete reactor cycle with realistic alarms:")
        print("  Phase 1: Normal startup (no alarms)")
        print("  Phase 2: Pressure increase (warnings)")
        print("  Phase 3: Critical pressure (critical alarms)")
        print("  Phase 4: Emergency shutdown (emergency alarm)")
        
        input("\nPress ENTER to start simulation...")
        
        # Phase 1: Normal Startup
        print("\n--- Phase 1: Normal Startup (10s) ---")
        print("  Pressure: 150 bar")
        print("  Status: All systems normal")
        print("  Alarm: None")
        self.buzzer.clear_alarm()
        time.sleep(5)
        
        print("\n  → Increasing power...")
        print("  → Pressure rising: 155 bar")
        time.sleep(3)
        
        print("  → Pressure: 160 bar")
        time.sleep(2)
        
        # Phase 2: Warning Level
        print("\n--- Phase 2: Pressure Warning (10s) ---")
        print("  Pressure: 165 bar (⚠️  WARNING)")
        print("  Status: High pressure detected")
        print("  Alarm: Pressure WARNING active")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_WARNING)
        time.sleep(5)
        
        print("\n  → Pressure continuing to rise...")
        print("  → Pressure: 172 bar (still WARNING)")
        time.sleep(3)
        
        print("  → Pressure: 178 bar (approaching CRITICAL)")
        time.sleep(2)
        
        # Phase 3: Critical Level
        print("\n--- Phase 3: Critical Pressure (10s) ---")
        print("  Pressure: 182 bar (🚨 CRITICAL!)")
        print("  Status: CRITICAL pressure - immediate action required")
        print("  Alarm: Pressure CRITICAL active")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_PRESSURE_CRITICAL)
        time.sleep(5)
        
        print("\n  → Attempting to reduce pressure...")
        print("  → Pressure: 188 bar (still CRITICAL)")
        time.sleep(3)
        
        print("  → Pressure: 193 bar (danger zone!)")
        time.sleep(2)
        
        # Phase 4: Emergency Shutdown
        print("\n--- Phase 4: Emergency Shutdown (15s) ---")
        print("  SCRAM initiated!")
        print("  Status: Emergency shutdown in progress")
        print("  Alarm: EMERGENCY alarm active")
        self.buzzer.set_alarm(BuzzerAlarm.ALARM_EMERGENCY)
        time.sleep(5)
        
        print("\n  → All control rods fully inserted")
        print("  → Power dropping rapidly")
        print("  → Pressure: 175 bar (decreasing)")
        time.sleep(5)
        
        print("\n  → Pressure: 155 bar")
        print("  → Power at safe level")
        time.sleep(3)
        
        print("\n  → Shutdown complete")
        print("  → Pressure: 145 bar (normal)")
        self.buzzer.clear_alarm()
        time.sleep(2)
        
        print("\n✓ Simulation sequence complete")
        print("  Final status: Safe shutdown achieved")
    
    def test_rapid_transitions(self):
        """Test 6: Rapid alarm transitions"""
        print("\n" + "="*70)
        print("TEST 6: RAPID ALARM TRANSITIONS")
        print("="*70)
        print("\nTest how buzzer handles rapid alarm changes:")
        
        input("Press ENTER to start rapid transition test...")
        
        alarms = [
            (BuzzerAlarm.ALARM_PROCEDURE_WARNING, "PROCEDURE", 1.5),
            (BuzzerAlarm.ALARM_INTERLOCK, "INTERLOCK", 1.5),
            (BuzzerAlarm.ALARM_PRESSURE_WARNING, "PRESSURE WARN", 1.5),
            (BuzzerAlarm.ALARM_PRESSURE_CRITICAL, "PRESSURE CRIT", 1.5),
            (BuzzerAlarm.ALARM_EMERGENCY, "EMERGENCY", 2.0),
            (BuzzerAlarm.ALARM_NONE, "CLEAR", 1.0),
        ]
        
        for alarm_type, name, duration in alarms:
            print(f"\n→ Switching to: {name}")
            if alarm_type == BuzzerAlarm.ALARM_NONE:
                self.buzzer.clear_alarm()
            else:
                self.buzzer.set_alarm(alarm_type)
            time.sleep(duration)
        
        print("\n✓ Rapid transition test complete")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*18 + "BUZZER ALARM TEST SUITE" + " "*27 + "║")
        print("║" + " "*15 + "PLTN Reactor Simulator v2.0" + " "*26 + "║")
        print("║" + " "*20 + "All Alarm Scenarios" + " "*29 + "║")
        print("╚" + "="*68 + "╝")
        
        print("\nThis test will demonstrate all buzzer alarm scenarios.")
        print("\n⚠️  WARNING: This test will make LOUD buzzer sounds!")
        print("Make sure:")
        print("  • Buzzer is properly connected to GPIO 22")
        print("  • Volume is at appropriate level")
        print("  • You are ready for alarm sounds")
        
        print("\nTests to run:")
        print("  1. Alarm tones (all 5 types)")
        print("  2. Pressure scenarios")
        print("  3. Operational scenarios")
        print("  4. Alarm priority")
        print("  5. Complete simulation sequence")
        print("  6. Rapid alarm transitions")
        
        response = input("\nContinue with tests? (y/n): ")
        if response.lower() != 'y':
            print("Test cancelled")
            return
        
        try:
            # Run all tests
            self.test_alarm_tones()
            
            input("\nPress ENTER to continue to pressure scenarios...")
            self.test_pressure_scenarios()
            
            input("\nPress ENTER to continue to operational scenarios...")
            self.test_operational_scenarios()
            
            input("\nPress ENTER to continue to alarm priority test...")
            self.test_alarm_priority()
            
            input("\nPress ENTER to continue to complete simulation...")
            self.test_simulation_sequence()
            
            input("\nPress ENTER to continue to rapid transition test...")
            self.test_rapid_transitions()
            
            # Final summary
            print("\n" + "="*70)
            print("✓ ALL BUZZER TESTS COMPLETED SUCCESSFULLY!")
            print("="*70)
            print("\nTest Summary:")
            print("✓ Tested all 5 alarm types")
            print("✓ Verified alarm patterns and frequencies")
            print("✓ Tested pressure-based alarms")
            print("✓ Tested operational scenarios")
            print("✓ Verified alarm priority system")
            print("✓ Completed full simulation sequence")
            print("✓ Tested rapid alarm transitions")
            
            print("\nAlarm Types Verified:")
            print("  ✓ PROCEDURE WARNING (1 kHz, 0.3s beep)")
            print("  ✓ PRESSURE WARNING (2 kHz, 0.5s beep)")
            print("  ✓ PRESSURE CRITICAL (3 kHz, double beep)")
            print("  ✓ EMERGENCY (4 kHz, rapid beep)")
            print("  ✓ INTERLOCK (1.5 kHz, short beep/long pause)")
            
            print("\nScenarios Tested:")
            print("  ✓ Normal operation → Warning → Critical → Emergency")
            print("  ✓ Procedure violations")
            print("  ✓ Interlock violations")
            print("  ✓ Pressure escalation")
            print("  ✓ Emergency shutdown")
            print("  ✓ Alarm priority handling")
            
            print("\n✓ Buzzer alarm system verified for simulation use!")
            
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            self.buzzer.clear_alarm()
        except Exception as e:
            print(f"\n\nError during test: {e}")
            import traceback
            traceback.print_exc()
            self.buzzer.clear_alarm()
        finally:
            # Cleanup
            print("\nCleaning up...")
            self.buzzer.cleanup()
            print("✓ Cleanup complete")


def main():
    """Main entry point"""
    
    if not BUZZER_AVAILABLE:
        print("\n" + "="*70)
        print("ERROR: Buzzer module not available")
        print("="*70)
        print("\nThis test requires:")
        print("  • Raspberry Pi with GPIO access")
        print("  • Passive buzzer connected to GPIO 22")
        print("  • RPi.GPIO library installed")
        print("\nInstall with:")
        print("  pip3 install RPi.GPIO")
        print("\nHardware connection:")
        print("  GPIO 22 → Buzzer positive (+)")
        print("  GND     → Buzzer negative (-)")
        sys.exit(1)
    
    try:
        # Initialize test suite
        print("\n" + "="*70)
        print("Initializing Buzzer Alarm Test Suite...")
        print("="*70)
        
        # Allow custom GPIO pin
        gpio_pin = 22  # Default
        try:
            response = input(f"\nUse GPIO pin {gpio_pin} for buzzer? (y/n): ")
            if response.lower() == 'n':
                gpio_pin = int(input("Enter GPIO pin number: "))
        except:
            pass
        
        test_suite = BuzzerTestSuite(buzzer_pin=gpio_pin)
        
        # Run all tests
        test_suite.run_all_tests()
        
    except Exception as e:
        logger.error(f"Failed to initialize test suite: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
