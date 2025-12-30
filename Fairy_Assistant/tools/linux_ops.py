"""
linux_ops.py - Desktop automation tools for X11/Linux.

Provides functions to control the Linux desktop using subprocess and pyautogui.
IMPORTANT: Requires X11 (Xorg). Does NOT work on Wayland.
"""

import os
import time
import subprocess
from PIL import Image
import pyautogui
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure DISPLAY is set for X11 operations
os.environ.setdefault('DISPLAY', ':0')

# Configure pyautogui
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions

# Configuration from .env
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LOCAL_MODEL = os.getenv("VISION_MODEL_LOCAL", "moondream")
CLOUD_MODEL = os.getenv("VISION_MODEL_CLOUD", "gemini-1.5-flash")
SCREENSHOT_PATH = os.getenv("SCREENSHOT_PATH", "/tmp/fairy_vision_context.png")

# Configure Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


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


# === VISION ANALYSIS TOOL ===
# Vision model for screen analysis


def analyze_screen_local(image_path: str, prompt: str) -> tuple[bool, str]:
    """Analyze image using local Ollama models (moondream/llava)."""
    import base64
    
    if not os.path.exists(image_path):
        return False, "Error: Image not found"
    
    print(f"[Vision] Optimizing image for LOCAL: {image_path}")
    optimized_path = "/tmp/vision_safe.jpg"
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail((640, 640))
            img.save(optimized_path, "JPEG", quality=80)
        image_path = optimized_path
    except Exception as e:
        print(f"[Vision] Error resizing image: {e}")
    
    try:
        import ollama
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            
        print("[Vision] Unloading brain to free VRAM...")
        try:
            for brain_model in ["llama3.2:latest", "llama3.2:3b", "llama3.1:latest"]:
                ollama.generate(model=brain_model, prompt="", keep_alive=0)
            time.sleep(1.0)
        except:
            pass
            
        print(f"[Vision] Loading eyes ({LOCAL_MODEL})...")
        response = ollama.chat(
            model=LOCAL_MODEL,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_data]}],
            keep_alive=0
        )
        
        description = response['message']['content'].strip()
        return True, description
    except Exception as e:
        print(f"[Vision Local Crash] {e}")
        return False, f"Local Vision Error: {e}"


def analyze_screen_cloud(image_path: str, prompt: str) -> tuple[bool, str]:
    """Analyze image using Gemini (Cloud API)."""
    if not GEMINI_KEY:
        return False, "Error: GEMINI_API_KEY not set in environment."
    
    print(f"[Vision] Uploading to Cloud: {image_path}")
    try:
        # Use configured cloud model
        model = genai.GenerativeModel(CLOUD_MODEL)
        
        with Image.open(image_path) as img:
            response = model.generate_content([prompt, img])
            
        description = response.text.strip()
        print(f"[Vision] Cloud analysis complete ({len(description)} chars)")
        return True, description
    except Exception as e:
        print(f"[Vision Cloud Crash] {e}")
        return False, f"Cloud Vision Error: {e}"


def see_screen(context: str = "screen") -> tuple[bool, str]:
    """
    Take a screenshot and analyze it. 
    Switches between Local and Cloud based on context keywords.
    """
    print(f"[Vision] Looking at screen (context: {context})")
    
    # Step 1: Take screenshot
    screenshot_path = SCREENSHOT_PATH
    try:
        subprocess.run(['scrot', '--overwrite', screenshot_path], check=True)
    except Exception as e:
        return False, f"Screenshot Error: {e}"
    
    # Step 2: Customize prompt based on context
    if any(kw in context.lower() for kw in ['error', 'problem', 'issue']):
        prompt = "Describe any error messages, warnings, or problems visible on this screen. Focus on text that indicates errors."
    elif any(kw in context.lower() for kw in ['text', 'read', 'content']):
        prompt = "Read and transcribe all visible text on this screen. Be accurate and complete."
    elif any(kw in context.lower() for kw in ['window', 'app', 'application']):
        prompt = "Describe what application or window is currently active. Include the window title and main content."
    else:
        prompt = "Describe this screen content in detail for an automation agent. Include visible windows, text, buttons, and important UI elements."

    # Step 3: Logic Check for Cloud Override
    cloud_keywords = ["cloud", "api", "online", "heavy", "detailed"]
    if any(keyword in context.lower() for keyword in cloud_keywords):
        print("[Vision] Mode: CLOUD (Offloading to Gemini)")
        success, description = analyze_screen_cloud(screenshot_path, prompt)
    else:
        print("[Vision] Mode: LOCAL (Using GPU)")
        success, description = analyze_screen_local(screenshot_path, prompt)
    
    if success:
        return True, f"[Screen Analysis]\n{description}"
    else:
        return False, description


# === SAFE TERMINAL TOOL ===
# Banned commands/keywords for security
BANNED_COMMANDS = [
    "sudo", "rm", "chmod", "chown", "wget", "curl", 
    ">", ">>", "|", "&&", "||", ";",  # Prevent piping and chaining
    "dd", "mkfs", "fdisk", "mount", "umount",  # Disk operations
    "shutdown", "reboot", "init", "systemctl",  # System control
    "passwd", "useradd", "userdel",  # User management
    "apt", "apt-get", "dpkg", "yum", "pacman",  # Package managers
    "eval", "exec", "source", ".",  # Shell execution
    "$(", "`",  # Command substitution
]


def run_terminal_command(command_str: str) -> tuple[bool, str]:
    """
    Execute a shell command with safety checks.
    
    Args:
        command_str: The shell command to execute.
    
    Returns:
        Tuple of (success, message) for observation feedback.
    
    Safety: Blocks dangerous commands defined in BANNED_COMMANDS.
    Allowed: ls, mkdir, cp, mv, cat, grep, pwd, touch, head, tail, find, etc.
    """
    command_str = command_str.strip()
    
    # Security Check: Scan for banned keywords
    for banned in BANNED_COMMANDS:
        if banned in command_str.lower():
            msg = f"Error: Security Block. Command contains banned keyword: '{banned}'"
            print(f"[Security Alert] Blocked: {command_str}")
            return False, msg
    
    # Log the command being executed
    print(f"[Terminal] Executing: {command_str}")
    
    try:
        result = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout for safety
            cwd=os.path.expanduser("~")  # Default to home directory
        )
        
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        # Build response message
        if result.returncode == 0:
            if stdout:
                msg = f"Output:\n{stdout}"
            else:
                msg = "Command executed successfully (no output)"
            if stderr:
                msg += f"\nWarnings: {stderr}"
            print(f"[Terminal] Success: {command_str}")
            return True, msg
        else:
            msg = f"Command failed (exit code {result.returncode})"
            if stderr:
                msg += f"\nError: {stderr}"
            if stdout:
                msg += f"\nOutput: {stdout}"
            print(f"[Terminal] Failed: {command_str}")
            return False, msg
            
    except subprocess.TimeoutExpired:
        msg = "Error: Command timed out (10 second limit)"
        print(f"[Terminal] Timeout: {command_str}")
        return False, msg
    except Exception as e:
        msg = f"Error executing command: {e}"
        print(f"[Terminal] Error: {command_str} - {e}")
        return False, msg


# === WEB SEARCH TOOL ===
def search_web(query: str, max_results: int = 3) -> tuple[bool, str]:
    """
    Search the web using DuckDuckGo and return formatted results.
    
    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 3).
    
    Returns:
        Tuple of (success, formatted_results_string) for observation feedback.
    """
    try:
        # Try new package name first (ddgs)
        try:
            from ddgs import DDGS
        except ImportError:
            # Fallback to old package name
            from duckduckgo_search import DDGS
    except ImportError:
        msg = "Error: Web search not installed. Run: pip install ddgs"
        print(f"[Search] {msg}")
        return False, msg
    
    query = query.strip()
    if not query:
        return False, "Error: Search query cannot be empty"
    
    print(f"[Search] Searching: {query}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            msg = f"No results found for: {query}"
            print(f"[Search] {msg}")
            return True, msg
        
        # Format results for AI consumption
        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            href = result.get('href', '')
            formatted.append(f"[Result {i}]\nTitle: {title}\nSummary: {body}\nURL: {href}")
        
        output = "\n\n".join(formatted)
        print(f"[Search] Found {len(results)} results for: {query}")
        return True, output
        
    except Exception as e:
        error_str = str(e).lower()
        if 'ratelimit' in error_str or '429' in error_str:
            msg = "Error: Search rate limited. Please try again in a moment."
        elif 'timeout' in error_str or 'connection' in error_str:
            msg = "Error: No internet connection or search service unavailable."
        else:
            msg = f"Error searching: {e}"
        print(f"[Search] {msg}")
        return False, msg
