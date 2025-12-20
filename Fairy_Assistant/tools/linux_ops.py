"""
linux_ops.py - Desktop automation tools for X11/Linux.

Provides functions to control the Linux desktop using subprocess and pyautogui.
IMPORTANT: Requires X11 (Xorg). Does NOT work on Wayland.
"""

import subprocess
import os
import pyautogui

# Ensure DISPLAY is set for X11 operations
os.environ.setdefault('DISPLAY', ':0')

# Configure pyautogui
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions


def open_app(app_name: str) -> bool:
    """
    Open an application by name.
    
    Args:
        app_name: Name of the application to open (e.g., 'firefox', 'code').
    
    Returns:
        True if the app was launched successfully, False otherwise.
    """
    try:
        app_name = app_name.strip()
        # Use Popen to launch without blocking
        subprocess.Popen(
            [app_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"[Linux] Opened app: {app_name}")
        return True
    except FileNotFoundError:
        print(f"[Linux] App not found: {app_name}")
        return False
    except Exception as e:
        print(f"[Linux] Error opening app {app_name}: {e}")
        return False


def type_text(text: str, interval: float = 0.02) -> bool:
    """
    Type text using pyautogui (simulates keyboard input).
    
    Args:
        text: The text to type.
        interval: Time in seconds between each character.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        pyautogui.write(text, interval=interval)
        print(f"[Linux] Typed: {text[:50]}...")
        return True
    except Exception as e:
        print(f"[Linux] Error typing text: {e}")
        return False


def system_control(command: str) -> bool:
    """
    Execute system control commands.
    
    Args:
        command: The command to execute ('lock', 'mute', 'unmute', 'volume_up', 'volume_down').
    
    Returns:
        True if successful, False otherwise.
    """
    command = command.lower().strip()
    
    try:
        if command == 'lock':
            # Try gnome-screensaver first, then xdg-screensaver
            try:
                subprocess.run(['gnome-screensaver-command', '-l'], check=True, stderr=subprocess.DEVNULL)
            except (FileNotFoundError, subprocess.CalledProcessError):
                subprocess.run(['xdg-screensaver', 'lock'], check=True)
            print("[Linux] Screen locked")
            return True
            
        elif command == 'mute':
            subprocess.run(
                ['amixer', '-D', 'pulse', 'sset', 'Master', 'toggle'],
                check=True,
                capture_output=True
            )
            print("[Linux] Audio toggled (mute/unmute)")
            return True
            
        elif command == 'unmute':
            subprocess.run(
                ['amixer', '-D', 'pulse', 'sset', 'Master', 'on'],
                check=True,
                capture_output=True
            )
            print("[Linux] Audio unmuted")
            return True

        elif command == 'volume_up':
            try:
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%+'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Fallback to default device
                subprocess.run(['amixer', 'sset', 'Master', '5%+'], check=True, capture_output=True)
            print("[Linux] Volume increased")
            return True

        elif command == 'volume_down':
            try:
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%-'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Fallback
                subprocess.run(['amixer', 'sset', 'Master', '5%-'], check=True, capture_output=True)
            print("[Linux] Volume decreased")
            return True
            
        else:
            print(f"[Linux] Unknown system command: {command}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[Linux] System command failed: {e}")
        return False
    except FileNotFoundError as e:
        print(f"[Linux] Required tool not found: {e}")
        return False
    except Exception as e:
        print(f"[Linux] Error executing system command: {e}")
        return False


def press_key(key: str) -> bool:
    """
    Press a single key or key combination.
    
    Args:
        key: Key name (e.g., 'enter', 'escape', 'ctrl+c').
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        if '+' in key:
            # Key combination (e.g., 'ctrl+c')
            keys = key.split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        print(f"[Linux] Pressed key: {key}")
        return True
    except Exception as e:
        print(f"[Linux] Error pressing key {key}: {e}")
        return False


def take_screenshot() -> str:
    """
    Take a screenshot using scrot and save it to ./context/vision_input.png.
    
    Returns:
        Path to the screenshot file, or empty string if failed.
    """
    try:
        # Ensure context directory exists
        context_dir = os.path.join(os.getcwd(), 'context')
        os.makedirs(context_dir, exist_ok=True)
        
        file_path = os.path.join(context_dir, 'vision_input.png')
        
        # Use scrot to take screenshot (overwrite)
        subprocess.run(['scrot', '--overwrite', file_path], check=True)
        
        print(f"[Linux] Screenshot saved to {file_path}")
        return file_path
    except FileNotFoundError:
        print("[Linux] 'scrot' not found. Please install it (sudo apt install scrot).")
        return ""
    except Exception as e:
        print(f"[Linux] Error taking screenshot: {e}")
        return ""
