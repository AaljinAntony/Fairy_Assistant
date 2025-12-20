
import sys
import os

# Mock linux_ops to prevent actual execution during test
from unittest.mock import MagicMock
import tools.linux_ops as linux_ops

linux_ops.open_app = MagicMock(return_value=True)
linux_ops.type_text = MagicMock(return_value=True)
linux_ops.take_screenshot = MagicMock(return_value="/tmp/test.png")

from action_parser import parse_and_execute

def test_parser_robustness():
    print("--- Testing Parser Robustness ---")
    
    # Case 1: Alias OPEN -> OPEN_LINUX, and quoted string "firefox"
    text1 = "I will open it. [ACTION: OPEN | \"firefox\"]"
    res1 = parse_and_execute(text1)
    
    ops = res1['results'][0]
    print(f"Test 1 (Alias + Quotes): {ops['type']} args={ops['args']}")
    if ops['type'] == 'OPEN_LINUX' and ops['args'][0] == 'firefox':
        print("✓ PASS")
    else:
        print("✗ FAIL")

    # Case 2: Lenient Separator (Colon instead of Pipe)
    text2 = "[ACTION: TYPE: Hello World]"
    res2 = parse_and_execute(text2)
    
    ops = res2['results'][0]
    print(f"Test 2 (Colon Separator): {ops['type']} args={ops['args']}")
    if ops['type'] == 'TYPE_LINUX' and ops['args'][0] == 'Hello World':
        print("✓ PASS")
    else:
        print("✗ FAIL")

    # Case 3: Alias SNAP -> SCREENSHOT_LINUX
    text3 = "[ACTION: SNAP]"
    res3 = parse_and_execute(text3)
    
    ops = res3['results'][0]
    print(f"Test 3 (Alias No Args): {ops['type']}")
    if ops['type'] == 'SCREENSHOT_LINUX':
        print("✓ PASS")
    else:
        print("✗ FAIL")

if __name__ == "__main__":
    test_parser_robustness()
