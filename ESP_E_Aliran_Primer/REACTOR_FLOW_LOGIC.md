# PWR Reactor Flow Logic & Startup Sequence

## 🔬 Logika Aliran PWR (Pressurized Water Reactor)

### System Architecture:
```
┌─────────────────────────────────────────────────────────────┐
│                    PWR 3-Loop System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │  TERTIARY    │ ←── │  SECONDARY   │ ←── │  PRIMARY   │ │
│  │  (Condenser) │     │ (Steam Gen)  │     │ (Reactor)  │ │
│  │   ~15 bar    │     │   ~50 bar    │     │  ~155 bar  │ │
│  └──────────────┘     └──────────────┘     └────────────┘ │
│        ↑                     ↑                    ↑        │
│        │                     │                    │        │
│   Pump #3 (T)           Pump #2 (S)          Pump #1 (P)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Correct Startup Sequence

### Phase 1: Initial State (All OFF)
```
Primary:   OFF (0 bar) - Reactor coolant stagnant
Secondary: OFF (0 bar) - No steam circulation
Tertiary:  OFF (0 bar) - No condenser cooling
```

### Phase 2: Start Cooling Loops FIRST
```
Step 1: Start Tertiary Pump (Condenser)
   - Pressure: 0 → 10 bar (STARTING)
   - Wait 5 seconds
   - Pressure: 10 → 15 bar (ON)
   ✅ Condenser cooling established

Step 2: Start Secondary Pump (Steam Generator)
   - Pressure: 0 → 20 bar (STARTING)
   - Wait 5 seconds
   - Pressure: 20 → 50 bar (ON)
   ✅ Heat removal path ready
```

**Why this order?**
- ✅ Heat sink must be ready BEFORE heat source
- ✅ Steam needs somewhere to condense
- ✅ Prevents pressure buildup in reactor

### Phase 3: Start Primary Loop (Reactor)
```
Step 3: Start Primary Pump (ONLY after cooling ready!)
   - Pressure: 0 → 50 bar (STARTING)
   - Wait 5 seconds
   - Pressure: 50 → 155 bar (ON)
   ✅ Reactor coolant circulating
   ✅ Heat removal active
```

**Why last?**
- ⚠️  Primary contains radioactive water
- ⚠️  Generates decay heat even when shutdown
- ⚠️  Must have cooling path ready

### Phase 4: Normal Operation
```
Primary:   155 bar (ON) - Reactor coolant flowing
Secondary:  50 bar (ON) - Steam generation
Tertiary:   15 bar (ON) - Condenser cooling

All systems nominal ✅
```

## ❌ Wrong Startup (DON'T DO THIS!)

### Dangerous Sequence:
```
Step 1: Start Primary FIRST ❌
   - Pressure: 155 bar
   - Status: ON
   - Problem: No heat removal!

Step 2: Reactor heats up
   - Temperature rising
   - Pressure increasing
   - Steam buildup
   - No condenser!

Result: 🚨 EMERGENCY SHUTDOWN NEEDED
```

**Why dangerous?**
- ❌ Heat generated but nowhere to go
- ❌ Pressure builds up uncontrolled
- ❌ Risk of overpressure
- ❌ Could damage equipment

## 🛑 Correct Shutdown Sequence

### Reverse Order (Last ON, First OFF):
```
Phase 1: Shutdown Primary FIRST
   - Primary: SHUTTING_DOWN (5s)
   - Primary: OFF
   - Secondary & Tertiary: Still ON
   ✅ Decay heat still being removed

Phase 2: Wait for Decay Heat
   - Wait 5-10 seconds
   - Temperature drops
   ✅ Safe to continue

Phase 3: Shutdown Secondary
   - Secondary: SHUTTING_DOWN (5s)
   - Secondary: OFF
   - Tertiary: Still ON
   ✅ Condenser still available

Phase 4: Shutdown Tertiary (Last)
   - Tertiary: SHUTTING_DOWN (5s)
   - Tertiary: OFF
   ✅ All systems secured
```

## 📊 Status Codes

| Code | Name | Meaning | LED Animation |
|------|------|---------|---------------|
| 0 | OFF | System tidak aktif | All LEDs off |
| 1 | STARTING | Pompa mulai berputar | Slow flow (300ms) |
| 2 | ON | Operasi normal | Fast flow (100ms) |
| 3 | SHUTTING_DOWN | Pompa berhenti perlahan | Very slow (500ms) |

## 🎯 Integration dengan Program

### Current Code (raspi_i2c_master.py):
```python
# NEW METHOD - Send all 3 flows to ESP-E
i2c_master.update_all_visualizers(
    pressure_primary=155.0,    # Primary pressure
    pump_status_primary=2,      # Primary ON
    pressure_secondary=50.0,    # Secondary pressure
    pump_status_secondary=2,    # Secondary ON
    pressure_tertiary=15.0,     # Tertiary pressure
    pump_status_tertiary=2      # Tertiary ON
)
```

### Integration dengan Simulator:
```python
def update_flow_visualizers(system_state):
    """
    Update visualizers berdasarkan kondisi sistem
    """
    # Determine pump status based on system state
    primary_status = get_pump_status(
        system_state.pump_primary,
        system_state.cooling_ready,
        system_state.pressure > 100
    )
    
    secondary_status = get_pump_status(
        system_state.pump_secondary,
        system_state.condenser_ready,
        system_state.pressure > 30
    )
    
    tertiary_status = get_pump_status(
        system_state.pump_tertiary,
        True,  # Always can start
        system_state.pressure > 5
    )
    
    # Send to ESP-E
    i2c_master.update_all_visualizers(
        system_state.pressure_primary, primary_status,
        system_state.pressure_secondary, secondary_status,
        system_state.pressure_tertiary, tertiary_status
    )

def get_pump_status(pump_enabled, precondition_met, pressure_ok):
    """
    Determine pump status based on conditions
    """
    if not pump_enabled:
        return PUMP_OFF
    
    if not precondition_met:
        return PUMP_OFF  # Can't start yet
    
    if pump_enabled and not pressure_ok:
        return PUMP_STARTING  # Ramping up
    
    if pump_enabled and pressure_ok:
        return PUMP_ON  # Fully operational
    
    return PUMP_OFF
```

## 🧪 Testing

### Test Script: `test_reactor_flow_sequence.py`

**Features:**
1. ✅ Correct startup sequence demo
2. ❌ Wrong startup warning demo
3. 🎮 Manual control mode

**Run:**
```bash
cd ~/pkm-simulator-PLTN/raspi_central_control
python3 test_reactor_flow_sequence.py
```

**What to observe:**
- LED animations reflect pump status
- Different speeds for different flows
- Independent control of each flow
- Realistic startup/shutdown timing

## 💡 Safety Interlocks (Recommended for Full Simulator)

```python
class ReactorSafetyInterlocks:
    def can_start_primary(self, state):
        """Check if safe to start primary pump"""
        if not state.secondary_running:
            return False, "Secondary cooling not available"
        
        if not state.tertiary_running:
            return False, "Condenser cooling not available"
        
        if state.pressure_secondary < 30:
            return False, "Secondary pressure too low"
        
        return True, "Safe to start"
    
    def can_start_secondary(self, state):
        """Check if safe to start secondary pump"""
        if not state.tertiary_running:
            return False, "Condenser not ready"
        
        return True, "Safe to start"
    
    def can_start_tertiary(self, state):
        """Check if safe to start tertiary pump"""
        return True, "Always safe to start"
```

## 📚 Educational Value

**Students learn:**
1. ✅ Heat removal hierarchy
2. ✅ Importance of startup sequence
3. ✅ Why cooling precedes heating
4. ✅ Emergency shutdown procedures
5. ✅ Decay heat management

**Visual feedback:**
- Fast flowing LEDs = High flow rate
- Slow flowing LEDs = Starting/Stopping
- OFF LEDs = System secured
- Multiple independent flows = Complex system

---

✅ **Program sudah mendukung logika reaktor yang benar!**
