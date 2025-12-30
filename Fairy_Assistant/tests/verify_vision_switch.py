import os
import sys
from unittest.mock import patch, MagicMock

# Mock dependencies before importing linux_ops
sys.modules['pyautogui'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.getcwd())

from tools.linux_ops import see_screen

def test_switching_logic():
    print("Testing Switching Logic...")
    
    # Mock subprocess.run for scrot
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock analyze_screen_local and analyze_screen_cloud
        with patch('tools.linux_ops.analyze_screen_local') as mock_local:
            with patch('tools.linux_ops.analyze_screen_cloud') as mock_cloud:
                mock_local.return_value = (True, "Local result")
                mock_cloud.return_value = (True, "Cloud result")
                
                # Test Case 1: Standard screen
                print("\nCase 1: Standard 'screen' context")
                success, result = see_screen("screen")
                print(f"Result: {result}")
                mock_local.assert_called_once()
                mock_cloud.assert_not_called()
                mock_local.reset_mock()
                
                # Test Case 2: Cloud context
                print("\nCase 2: 'cloud' context")
                success, result = see_screen("cloud")
                print(f"Result: {result}")
                mock_cloud.assert_called_once()
                mock_local.assert_not_called()
                mock_cloud.reset_mock()
                
                # Test Case 3: 'detailed' context (should trigger cloud)
                print("\nCase 3: 'detailed' context")
                success, result = see_screen("detailed analysis")
                print(f"Result: {result}")
                mock_cloud.assert_called_once()
                mock_local.reset_mock()
                mock_cloud.reset_mock()

                # Test Case 4: 'heavy' context (should trigger cloud)
                print("\nCase 4: 'heavy' context")
                success, result = see_screen("heavy load")
                print(f"Result: {result}")
                mock_cloud.assert_called_once()
                
    print("\nLogic Test Passed!")

if __name__ == "__main__":
    # Check if GEMINI_API_KEY is available (optional, just for info)
    key = os.getenv("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY available: {key is not None}")
    
    test_switching_logic()
