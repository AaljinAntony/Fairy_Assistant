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


def open_app(app_name: str) -> tuple[bool, str]:
    """
    Open an application by name.
    
    Args:
        app_name: Name of the application to open (e.g., 'firefox', 'code').
    
    Returns:
        Tuple of (success, message) for observation feedback.
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
        msg = f"Launched {app_name} successfully"
        print(f"[Linux] {msg}")
        return True, msg
    except FileNotFoundError:
        msg = f"App not found: {app_name}"
        print(f"[Linux] {msg}")
        return False, msg
    except Exception as e:
        msg = f"Error opening {app_name}: {e}"
        print(f"[Linux] {msg}")
        return False, msg


def type_text(text: str, interval: float = 0.02) -> tuple[bool, str]:
    """
    Type text using pyautogui (simulates keyboard input).
    
    Args:
        text: The text to type.
        interval: Time in seconds between each character.
    
    Returns:
        Tuple of (success, message) for observation feedback.
    """
    try:
        pyautogui.write(text, interval=interval)
        preview = text[:30] + '...' if len(text) > 30 else text
        msg = f"Typed: {preview}"
        print(f"[Linux] {msg}")
        return True, msg
    except Exception as e:
        msg = f"Error typing text: {e}"
        print(f"[Linux] {msg}")
        return False, msg


def system_control(command: str) -> tuple[bool, str]:
    """
    Execute system control commands.
    
    Args:
        command: The command to execute ('lock', 'mute', 'unmute', 'volume_up', 'volume_down').
    
    Returns:
        Tuple of (success, message) for observation feedback.
    """
    command = command.lower().strip()
    
    try:
        if command == 'lock':
            try:
                subprocess.run(['gnome-screensaver-command', '-l'], check=True, stderr=subprocess.DEVNULL)
            except (FileNotFoundError, subprocess.CalledProcessError):
                subprocess.run(['xdg-screensaver', 'lock'], check=True)
            msg = "Screen locked"
            print(f"[Linux] {msg}")
            return True, msg
            
        elif command == 'mute':
            subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', 'toggle'], check=True, capture_output=True)
            msg = "Audio toggled (mute/unmute)"
            print(f"[Linux] {msg}")
            return True, msg
            
        elif command == 'unmute':
            subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', 'on'], check=True, capture_output=True)
            msg = "Audio unmuted"
            print(f"[Linux] {msg}")
            return True, msg

        elif command == 'volume_up':
            try:
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%+'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                subprocess.run(['amixer', 'sset', 'Master', '5%+'], check=True, capture_output=True)
            msg = "Volume increased"
            print(f"[Linux] {msg}")
            return True, msg

        elif command == 'volume_down':
            try:
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%-'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                subprocess.run(['amixer', 'sset', 'Master', '5%-'], check=True, capture_output=True)
            msg = "Volume decreased"
            print(f"[Linux] {msg}")
            return True, msg
            
        else:
            msg = f"Unknown system command: {command}"
            print(f"[Linux] {msg}")
            return False, msg
            
    except subprocess.CalledProcessError as e:
        msg = f"System command failed: {e}"
        print(f"[Linux] {msg}")
        return False, msg
    except FileNotFoundError as e:
        msg = f"Required tool not found: {e}"
        print(f"[Linux] {msg}")
        return False, msg
    except Exception as e:
        msg = f"Error executing system command: {e}"
        print(f"[Linux] {msg}")
        return False, msg


def press_key(key: str) -> tuple[bool, str]:
    """
    Press a single key or key combination.
    
    Args:
        key: Key name (e.g., 'enter', 'escape', 'ctrl+c').
    
    Returns:
        Tuple of (success, message) for observation feedback.
    """
    try:
        if '+' in key:
            keys = key.split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        msg = f"Pressed key: {key}"
        print(f"[Linux] {msg}")
        return True, msg
    except Exception as e:
        msg = f"Error pressing key {key}: {e}"
        print(f"[Linux] {msg}")
        return False, msg


def take_screenshot() -> tuple[bool, str]:
    """
    Take a screenshot using scrot and save it to ./context/vision_input.png.
    
    Returns:
        Tuple of (success, message) for observation feedback.
    """
    try:
        context_dir = os.path.join(os.getcwd(), 'context')
        os.makedirs(context_dir, exist_ok=True)
        
        file_path = os.path.join(context_dir, 'vision_input.png')
        subprocess.run(['scrot', '--overwrite', file_path], check=True)
        
        msg = f"Screenshot saved to {file_path}"
        print(f"[Linux] {msg}")
        return True, msg
    except FileNotFoundError:
        msg = "'scrot' not found. Please install it (sudo apt install scrot)."
        print(f"[Linux] {msg}")
        return False, msg
    except Exception as e:
        msg = f"Error taking screenshot: {e}"
        print(f"[Linux] {msg}")
        return False, msg
