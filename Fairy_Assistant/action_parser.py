"""
action_parser.py - Parse and Execute [ACTION] tags.

Parses structured action tags from Ollama responses and executes
them using the linux_ops module.
"""

import re
from tools import linux_ops

# Aliases for action types to handle LLM variations
ACTION_ALIASES = {
    "TYPE": "TYPE_LINUX",
    "WRITE": "TYPE_LINUX",
    "OPEN": "OPEN_LINUX",
    "LAUNCH": "OPEN_LINUX",
    "START": "OPEN_LINUX",
    "SYSTEM": "SYSTEM_LINUX",
    "CONTROL": "SYSTEM_LINUX",
    "PRESS": "KEY_LINUX",
    "KEY": "KEY_LINUX",
    "SCREENSHOT": "SCREENSHOT_LINUX",
    "SNAP": "SCREENSHOT_LINUX"
}

# Regex pattern to match action tags
# Relaxed format: [ACTION: TYPE | arg ... ] or [ACTION: TYPE: arg ...]
# Captures optional arguments
ACTION_PATTERN = re.compile(
    r'\[ACTION:\s*([A-Za-z_]+)(?:\s*[|:]\s*([^\]]*))?\]',
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
        'actions': [], 
        'results': [],
        'observations': [],  # Collect observation messages for ReAct loop
        'clean_text': response_text
    }
    
    # Find all action tags
    matches = ACTION_PATTERN.findall(response_text)
    results['actions_found'] = len(matches)
    
    for match in matches:
        raw_type = match[0].upper().strip()
        args_str = match[1].strip() if match[1] else ''
        
        # Resolve alias
        action_type = ACTION_ALIASES.get(raw_type, raw_type)
        
        # Clean arguments
        args = []
        if args_str:
            # If multiple args separated by pipe were intended but regex swallowed them
            # We can split by pipe again if present
            raw_args = [arg.strip() for arg in args_str.split('|')]
            
            # Clean quotes from args (LLM often quotes the payload e.g. "firefox")
            for arg in raw_args:
                if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                    arg = arg[1:-1]
                args.append(arg)
        
        print(f"[Parser] Found action: {raw_type} -> {action_type} with args: {args}")
        
        # Execute the action
        success, message = execute_action(action_type, args)
        
        results['results'].append({
            'type': action_type,
            'args': args,
            'success': success,
            'message': message
        })
        results['actions'].append({
            'type': action_type,
            'args': args
        })
        results['observations'].append(message)
        
        if success:
            results['actions_executed'] += 1
    
    # Remove action tags from the text for clean display
    results['clean_text'] = ACTION_PATTERN.sub('', response_text).strip()
    
    return results


def execute_action(action_type: str, args: list) -> tuple[bool, str]:
    """
    Execute a single action based on its type using linux_ops.
    
    Returns:
        Tuple of (success, message) for observation feedback.
    """
    try:
        # OPEN_LINUX: Launch an app
        if action_type == 'OPEN_LINUX':
            if args:
                return linux_ops.open_app(args[0])
            return False, "OPEN_LINUX requires an app name"
        
        # TYPE_LINUX: Type text
        elif action_type == 'TYPE_LINUX':
            if args:
                return linux_ops.type_text(args[0])
            return False, "TYPE_LINUX requires text to type"
        
        # SYSTEM_LINUX: System commands (lock, mute, volume)
        elif action_type == 'SYSTEM_LINUX':
            if args:
                return linux_ops.system_control(args[0])
            return False, "SYSTEM_LINUX requires a command"
        
        # KEY_LINUX: Press key combinations
        elif action_type == 'KEY_LINUX':
            if args:
                return linux_ops.press_key(args[0])
            return False, "KEY_LINUX requires a key name"

        # SCREENSHOT_LINUX: Take a screenshot
        elif action_type == 'SCREENSHOT_LINUX':
            return linux_ops.take_screenshot()
        
        else:
            return False, f"Unknown action type: {action_type}"
            
    except Exception as e:
        return False, f"Error executing {action_type}: {e}"
