#!/bin/bash
# Deep Debug - State File Issue

echo "=========================================="
echo "DEEP DEBUG: Why Can't Read State File?"
echo "=========================================="
echo ""

echo "1. File exists and readable:"
ls -la /tmp/pltn_state.json
echo ""

echo "2. File content:"
cat /tmp/pltn_state.json
echo ""
echo ""

echo "3. File can be read by current user?"
cat /tmp/pltn_state.json > /dev/null && echo "✅ YES, readable" || echo "❌ NO, cannot read"
echo ""

echo "4. Python can read it?"
python3 -c "import json; print(json.load(open('/tmp/pltn_state.json')))" && echo "✅ YES, Python can read" || echo "❌ NO, Python cannot read"
echo ""

echo "5. Check video display process user:"
ps aux | grep video_display_app.py | grep -v grep
echo ""

echo "6. Test read as video display would:"
python3 << 'EOF'
from pathlib import Path
import json

state_file = Path("/tmp/pltn_state.json")
print(f"File exists: {state_file.exists()}")
print(f"File is_file: {state_file.is_file()}")
print(f"File readable: {state_file.exists() and state_file.is_file()}")

if state_file.exists():
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Successfully read JSON")
        print(f"Content: {data}")
    except Exception as e:
        print(f"❌ Error reading: {e}")
else:
    print("❌ File does not exist for Python!")
EOF
echo ""

echo "7. Check video display code state_file path:"
grep -n "state_file = Path" ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py
echo ""

echo "8. Check read_simulation_state function:"
grep -A 10 "def read_simulation_state" ~/pkm-simulator-PLTN/pltn_video_display/video_display_app.py | head -20
echo ""

echo "=========================================="
echo "DIAGNOSIS:"
echo ""
echo "If Python CAN read the file above, but video display"
echo "shows 'No state file', then the issue is in the code logic."
echo ""
echo "Check:"
echo "  1. Path in video_display_app.py matches /tmp/pltn_state.json"
echo "  2. read_simulation_state() function is correct"
echo "  3. JSON parsing is not failing silently"
echo "=========================================="
