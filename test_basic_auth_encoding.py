#!/usr/bin/env python3
"""Test Basic Auth encoding logic"""

import base64


def process_auth_header(auth_value: str) -> str:
    """
    Process Authorization header and auto-encode Basic Auth if needed
    
    Args:
        auth_value: Authorization header value
        
    Returns:
        Processed authorization header value
    """
    if not isinstance(auth_value, str):
        return auth_value
    
    # Check if it's Basic Auth
    if not auth_value.startswith('Basic '):
        return auth_value
    
    credentials = auth_value[6:].strip()  # Remove "Basic " prefix
    
    # Check if already Base64 encoded (Base64 doesn't contain colons)
    # If it contains a colon, it's in "user:password" format and needs encoding
    if ':' in credentials:
        # Encode to Base64
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    # Already encoded or invalid format, return as-is
    return auth_value


def test_basic_auth_encoding():
    """Test various Basic Auth scenarios"""
    
    print("="*70)
    print("Testing Basic Auth Auto-Encoding")
    print("="*70)
    
    test_cases = [
        {
            "name": "Plain user:password format",
            "input": "Basic testuser:testpass123",
            "expected_pattern": "Basic "
        },
        {
            "name": "Already encoded",
            "input": "Basic dGVzdHVzZXI6dGVzdHBhc3MxMjM=",
            "expected": "Basic dGVzdHVzZXI6dGVzdHBhc3MxMjM="
        },
        {
            "name": "Bearer token (should not change)",
            "input": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "expected": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        },
        {
            "name": "CAPSHOME example",
            "input": "Basic kimmo:11qqaa..",
            "expected_pattern": "Basic "
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Input:  {test['input']}")
        
        result = process_auth_header(test['input'])
        print(f"   Output: {result}")
        
        if 'expected' in test:
            if result == test['expected']:
                print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL - Expected: {test['expected']}")
        elif 'expected_pattern' in test:
            if result.startswith(test['expected_pattern']):
                # Decode and verify
                if 'user:password' in test['input'] or 'kimmo:11qqaa' in test['input']:
                    try:
                        encoded_part = result.split(' ')[1]
                        decoded = base64.b64decode(encoded_part).decode()
                        original_creds = test['input'].split(' ')[1]
                        if decoded == original_creds:
                            print(f"   ✅ PASS - Correctly encoded to Base64")
                            print(f"      Decoded: {decoded}")
                        else:
                            print(f"   ❌ FAIL - Decoded doesn't match original")
                    except Exception as e:
                        print(f"   ❌ FAIL - Decoding error: {e}")
                else:
                    print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL - Doesn't start with expected pattern")
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)


if __name__ == "__main__":
    test_basic_auth_encoding()
