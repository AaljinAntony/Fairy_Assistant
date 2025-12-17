#!/bin/bash

# Fairy Assistant Developer Utility Script
# Starts the Python backend and Flutter app together

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PID=""

# Cleanup function to kill background process on exit
cleanup() {
    echo ""
    echo "Shutting down Fairy Brain..."
    if [ -n "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
        kill "$PYTHON_PID"
        wait "$PYTHON_PID" 2>/dev/null
    fi
    echo "Goodbye!"
    exit 0
}

# Set trap to call cleanup on Ctrl+C or script exit
trap cleanup SIGINT SIGTERM EXIT

# Step 1: Start the Python backend
echo "Starting Fairy Brain..."
cd "$SCRIPT_DIR"
source .venv/bin/activate
python main.py &
PYTHON_PID=$!

# Step 2: Wait for server to initialize
echo "Waiting for server to initialize..."
sleep 5

# Step 3: Launch Flutter app
echo "Launching Flutter App on Emulator..."
cd "$SCRIPT_DIR/mobile_app"
flutter run

# Wait for Flutter to finish (this keeps the script running)
wait
