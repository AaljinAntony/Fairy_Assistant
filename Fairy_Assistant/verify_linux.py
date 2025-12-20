import sys
import os
import time
sys.path.append(os.getcwd())

from tools import linux_ops

def test_screenshot():
    print("Testing Screenshot...")
    path = linux_ops.take_screenshot()
    if path and os.path.exists(path):
        print(f"SUCCESS: Screenshot saved at {path}")
    else:
        print("FAILURE: Screenshot returned empty path or file missing")

def test_volume():
    print("Testing Volume Control...")
    # Just test execution, harder to verify effect programmatically without listening
    if linux_ops.system_control('volume_up'):
        print("SUCCESS: Volume Up executed")
    else:
        print("FAILURE: Volume Up failed")

def test_app_launch():
    print("Testing App Launch (gnome-calculator)...")
    # Using calculator as it's safe and visible
    if linux_ops.open_app('gnome-calculator'):
        print("SUCCESS: Calculator launched")
        time.sleep(2) # Give it time to appear
    else:
        print("FAILURE: Calculator launch failed (might be missing or named differently)")

if __name__ == "__main__":
    print("--- Starting Linux Ops Verification ---")
    test_screenshot()
    test_volume()
    # test_app_launch() # Uncomment if you want to pop up windows
    print("--- Verification Complete ---")
