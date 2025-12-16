"""
test_server.py - Test the Fairy Assistant SocketIO server.

Tests the server's ability to receive commands and process them correctly.
Uses python-socketio client to connect and emit events.
"""

import sys
import time
import threading
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import socketio


class TestResults:
    """Store test results for assertions."""
    def __init__(self):
        self.received_response = None
        self.response_received = threading.Event()
        self.connected = threading.Event()
        self.logs = []


def test_client_command():
    """Test 1: Emit client_command and verify server processes it."""
    print("\n" + "=" * 60)
    print("TEST: Client Command with Action Tag")
    print("=" * 60)
    
    results = TestResults()
    
    # Create SocketIO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("[Test] ✓ Connected to server")
        results.connected.set()
    
    @sio.event
    def disconnect():
        print("[Test] Disconnected from server")
    
    @sio.on('server_action')
    def on_server_action(data):
        print(f"[Test] Received server_action: {data}")
        results.received_response = data
        results.logs.append(data)
        if data.get('type') == 'speak':
            results.response_received.set()
    
    try:
        # Connect to server
        print("[Test] Connecting to localhost:5000...")
        sio.connect('http://localhost:5000', wait_timeout=10)
        
        # Wait for connection
        if not results.connected.wait(timeout=5):
            print("[Test] ✗ Connection timeout")
            return False
        
        # Send client_command
        test_payload = {"text": "Open Firefox"}
        print(f"[Test] Emitting client_command: {test_payload}")
        sio.emit('client_command', test_payload)
        
        # Wait for response
        print("[Test] Waiting for server response...")
        if results.response_received.wait(timeout=30):
            print("[Test] ✓ Received response from server")
            
            # Check if response was received
            if results.received_response:
                response_type = results.received_response.get('type')
                message = results.received_response.get('message', '')
                
                print(f"[Test] Response type: {response_type}")
                print(f"[Test] Message preview: {message[:200]}..." if len(message) > 200 else f"[Test] Message: {message}")
                
                # The LLM should ideally include action tags, but we can't guarantee it
                # Check that we got a valid response
                if response_type == 'speak' and message:
                    print("[Test] ✓ Server processed command and returned response")
                    return True
                else:
                    print("[Test] ✗ Invalid response format")
                    return False
            else:
                print("[Test] ✗ No response data received")
                return False
        else:
            print("[Test] ✗ Response timeout (30s)")
            print("[Test] Note: This may happen if Ollama is not running or slow to respond")
            return False
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[Test] ✗ Connection failed: {e}")
        print("[Test] Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"[Test] ✗ Error: {e}")
        return False
    finally:
        if sio.connected:
            sio.disconnect()


def test_action_parser_mock():
    """Test 2: Test action_parser directly with mocked linux_ops."""
    print("\n" + "=" * 60)
    print("TEST: Action Parser with Mocked Execution")
    print("=" * 60)
    
    try:
        # Import action_parser
        sys.path.insert(0, '..')
        from action_parser import parse_and_execute
        from tools import linux_ops
        
        # Mock linux_ops.open_app
        with patch.object(linux_ops, 'open_app', return_value=True) as mock_open:
            # Test response containing action tag
            test_response = "Sure! I'll open Firefox for you. [ACTION: OPEN_LINUX | firefox]"
            
            print(f"[Test] Input: {test_response}")
            result = parse_and_execute(test_response)
            
            print(f"[Test] Actions found: {result['actions_found']}")
            print(f"[Test] Actions executed: {result['actions_executed']}")
            print(f"[Test] Clean text: {result['clean_text']}")
            print(f"[Test] Results: {result['results']}")
            
            # Assertions
            assert result['actions_found'] == 1, "Expected 1 action found"
            assert result['actions_executed'] == 1, "Expected 1 action executed"
            assert 'firefox' not in result['clean_text'].lower() or '[ACTION' not in result['clean_text'], "Clean text should not contain action tag"
            
            # Verify mock was called
            mock_open.assert_called_once_with('firefox')
            print("[Test] ✓ linux_ops.open_app was called with 'firefox'")
            
            print("[Test] ✓ All assertions passed!")
            return True
            
    except AssertionError as e:
        print(f"[Test] ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"[Test] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "#" * 60)
    print("# FAIRY ASSISTANT - SERVER TESTS")
    print("#" * 60)
    
    results = {}
    
    # Test 1: Action Parser (doesn't require server)
    results['action_parser'] = test_action_parser_mock()
    
    # Test 2: Client Command (requires server running)
    print("\n[Info] Test 2 requires the server to be running.")
    print("[Info] If server is not running, this test will fail gracefully.")
    results['client_command'] = test_client_command()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
