"""
android_ops.py - Android bridge for sending commands to the mobile app.

Emits SocketIO events to trigger actions on the connected Android device.
Uses a module-level socketio reference that must be initialized by main.py.
"""

# Module-level socketio reference (set by main.py at startup)
_socketio = None


def init(socketio_instance):
    """
    Initialize the android_ops module with the SocketIO instance.
    
    Args:
        socketio_instance: The Flask-SocketIO instance from main.py.
    """
    global _socketio
    _socketio = socketio_instance
    print("[Android] Bridge initialized")


def send_to_phone(action_type: str, data: dict) -> bool:
    """
    Send an action to the connected Android phone.
    
    Args:
        action_type: Type of action (e.g., 'trigger_intent', 'speak').
        data: Action payload data.
    
    Returns:
        True if emitted successfully, False otherwise.
    """
    global _socketio
    
    if _socketio is None:
        print("[Android] Error: SocketIO not initialized. Call init() first.")
        return False
    
    try:
        payload = {
            'type': action_type,
            **data
        }
        _socketio.emit('server_action', payload)
        print(f"[Android] Sent to phone: {action_type} -> {data}")
        return True
    except Exception as e:
        print(f"[Android] Error sending to phone: {e}")
        return False


def send_sms(phone_number: str, message: str) -> bool:
    """
    Trigger SMS sending on the Android device.
    
    Args:
        phone_number: The recipient's phone number.
        message: The SMS message content.
    
    Returns:
        True if command sent successfully.
    """
    return send_to_phone('trigger_intent', {
        'intent': 'sms',
        'phone_number': phone_number,
        'message': message
    })


def make_call(phone_number: str) -> bool:
    """
    Trigger a phone call on the Android device.
    
    Args:
        phone_number: The number to call.
    
    Returns:
        True if command sent successfully.
    """
    return send_to_phone('trigger_intent', {
        'intent': 'call',
        'phone_number': phone_number
    })


def open_app(package_name: str) -> bool:
    """
    Open an app on the Android device.
    
    Args:
        package_name: The app package name (e.g., 'com.whatsapp').
    
    Returns:
        True if command sent successfully.
    """
    return send_to_phone('trigger_intent', {
        'intent': 'open_app',
        'package': package_name
    })


def send_whatsapp(phone_number: str, message: str) -> bool:
    """
    Send a WhatsApp message.
    
    Args:
        phone_number: The recipient's phone number (with country code).
        message: The message content.
    
    Returns:
        True if command sent successfully.
    """
    return send_to_phone('trigger_intent', {
        'intent': 'whatsapp',
        'phone_number': phone_number,
        'message': message
    })
