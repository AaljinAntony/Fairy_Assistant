"""
action_parser.py - Parse and execute [ACTION] tags from LLM responses.

Parses structured action tags from Ollama responses and routes them
to the appropriate handler functions.
"""

import re
from tools import linux_ops
from tools import android_ops

# Regex pattern to match action tags
# Format: [ACTION: TYPE | arg1 | arg2 | ...]
ACTION_PATTERN = re.compile(
    r'\[ACTION:\s*(\w+)\s*(?:\|\s*([^\]]+))?\]',
    re.IGNORECASE
)


def parse_and_execute(response_text: str) -> dict:
    """
    Parse LLM response for action tags and execute them.
    
    Args:
        response_text: The full response text from the LLM.
    
    Returns:
        dict with 'actions_found', 'actions_executed', 'results', and 'clean_text'.
    """
    results = {
        'actions_found': 0,
        'actions_executed': 0,
        'results': [],
        'clean_text': response_text
    }
    
    # Find all action tags
    matches = ACTION_PATTERN.findall(response_text)
    results['actions_found'] = len(matches)
    
    for match in matches:
        action_type = match[0].upper()
        args_str = match[1].strip() if match[1] else ''
        args = [arg.strip() for arg in args_str.split('|')] if args_str else []
        
        print(f"[Parser] Found action: {action_type} with args: {args}")
        
        success = execute_action(action_type, args)
        results['results'].append({
            'action': action_type,
            'args': args,
            'success': success
        })
        
        if success:
            results['actions_executed'] += 1
    
    # Remove action tags from the text for clean display
    results['clean_text'] = ACTION_PATTERN.sub('', response_text).strip()
    
    return results


def execute_action(action_type: str, args: list) -> bool:
    """
    Execute a single action based on its type.
    
    Args:
        action_type: The type of action (e.g., 'OPEN_LINUX', 'TYPE_LINUX').
        args: List of arguments for the action.
    
    Returns:
        True if action was executed successfully, False otherwise.
    """
    try:
        # Linux app opening
        if action_type == 'OPEN_LINUX':
            if args:
                return linux_ops.open_app(args[0])
            print("[Parser] OPEN_LINUX requires an app name")
            return False
        
        # Linux text typing
        elif action_type == 'TYPE_LINUX':
            if args:
                return linux_ops.type_text(args[0])
            print("[Parser] TYPE_LINUX requires text to type")
            return False
        
        # Linux system control (lock, mute, etc.)
        elif action_type == 'SYSTEM_LINUX':
            if args:
                return linux_ops.system_control(args[0])
            print("[Parser] SYSTEM_LINUX requires a command")
            return False
        
        # Key press
        elif action_type == 'KEY_LINUX':
            if args:
                return linux_ops.press_key(args[0])
            print("[Parser] KEY_LINUX requires a key name")
            return False
        
        # Android SMS
        elif action_type == 'ANDROID_MSG':
            if len(args) >= 2:
                return android_ops.send_sms(args[0], args[1])
            print("[Parser] ANDROID_MSG requires [phone_number, message]")
            return False
        
        # Android Call
        elif action_type == 'ANDROID_CALL':
            if args:
                return android_ops.make_call(args[0])
            print("[Parser] ANDROID_CALL requires [phone_number]")
            return False
        
        # Android App
        elif action_type == 'ANDROID_APP':
            if args:
                return android_ops.open_app(args[0])
            print("[Parser] ANDROID_APP requires [package_name]")
            return False
        
        # Android WhatsApp
        elif action_type == 'ANDROID_WHATSAPP':
            if len(args) >= 2:
                return android_ops.send_whatsapp(args[0], args[1])
            print("[Parser] ANDROID_WHATSAPP requires [phone_number, message]")
            return False
        
        else:
            print(f"[Parser] Unknown action type: {action_type}")
            return False
            
    except Exception as e:
        print(f"[Parser] Error executing {action_type}: {e}")
        return False


def get_supported_actions() -> dict:
    """Return a dict of supported action types and their descriptions."""
    return {
        'OPEN_LINUX': 'Open a Linux application. Args: [app_name]',
        'TYPE_LINUX': 'Type text on the keyboard. Args: [text]',
        'SYSTEM_LINUX': 'System control (lock, mute). Args: [command]',
        'KEY_LINUX': 'Press a key or key combo. Args: [key]',
        'ANDROID_MSG': 'Send SMS via Android. Args: [number | message]',
        'ANDROID_CALL': 'Make a phone call via Android. Args: [number]',
        'ANDROID_APP': 'Open an app on Android. Args: [package_name]',
        'ANDROID_WHATSAPP': 'Send WhatsApp message. Args: [number | message]',
    }
