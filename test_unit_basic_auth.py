#!/usr/bin/env python3
"""Unit test for Basic Auth auto-encoding logic"""

import base64


def process_auth_header(auth_value: str) -> str:
    """
    Process Authorization header and auto-encode Basic Auth if needed
    (Copy of the implementation from json_pre_request_engine.py)
    """
    if not isinstance(auth_value, str):
        return auth_value
    
    if not auth_value.startswith('Basic '):
        return auth_value
    
    credentials = auth_value[6:].strip()
    
    if ':' in credentials:
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    return auth_value


def test_basic_auth_scenarios():
    """Test various Basic Auth scenarios with detailed output"""
    
    print("="*70)
    print("Unit Test: Basic Auth Auto-Encoding Logic")
    print("="*70)
    print()
    
    test_cases = [
        {
            "name": "1. Simple user:password",
            "input": "Basic admin:password123",
            "should_encode": True,
            "verify_decode": True
        },
        {
            "name": "2. With special characters",
            "input": "Basic kimmo:11qqaa..",
            "should_encode": True,
            "verify_decode": True
        },
        {
            "name": "3. Already Base64 encoded",
            "input": "Basic YWRtaW46cGFzc3dvcmQxMjM=",
            "should_encode": False,
            "verify_decode": False
        },
        {
            "name": "4. Bearer token (should not change)",
            "input": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "should_encode": False,
            "verify_decode": False
        },
        {
            "name": "5. Empty credentials",
            "input": "Basic :",
            "should_encode": True,
            "verify_decode": True
        },
        {
            "name": "6. CAPSHOME example with env vars resolved",
            "input": "Basic testuser:testpass",
            "should_encode": True,
            "verify_decode": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"{test['name']}")
        print(f"{'─' * 70}")
        print(f"Input:  {test['input']}")
        
        result = process_auth_header(test['input'])
        print(f"Output: {result}")
        
        # Verify encoding happened or not
        if test['should_encode']:
            # Check if output is different and properly formatted
            if result.startswith("Basic ") and result != test['input']:
                credentials_part = result.split(' ')[1]
                
                # Verify it doesn't contain colon (should be encoded)
                if ':' not in credentials_part:
                    if test['verify_decode']:
                        try:
                            # Decode and verify
                            decoded = base64.b64decode(credentials_part).decode()
                            original_creds = test['input'].split(' ')[1]
                            
                            print(f"Decoded: {decoded}")
                            
                            if decoded == original_creds:
                                print(f"✅ PASS - Correctly encoded and verified")
                                passed += 1
                            else:
                                print(f"❌ FAIL - Decoded mismatch")
                                print(f"   Expected: {original_creds}")
                                print(f"   Got:      {decoded}")
                                failed += 1
                        except Exception as e:
                            print(f"❌ FAIL - Decode error: {e}")
                            failed += 1
                    else:
                        print(f"✅ PASS - Encoded (skip verification)")
                        passed += 1
                else:
                    print(f"❌ FAIL - Still contains colon, not encoded")
                    failed += 1
            else:
                print(f"❌ FAIL - Not encoded when it should be")
                failed += 1
        else:
            # Should remain unchanged
            if result == test['input']:
                print(f"✅ PASS - Correctly unchanged")
                passed += 1
            else:
                print(f"❌ FAIL - Should not change")
                print(f"   Expected: {test['input']}")
                print(f"   Got:      {result}")
                failed += 1
        
        print()
    
    print("="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = test_basic_auth_scenarios()
    exit(0 if success else 1)
