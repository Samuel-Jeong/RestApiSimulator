#!/usr/bin/env python3
"""Test JSON path extraction logic"""


def get_by_path(data, path):
    """
    Get value from data using dot notation path
    (Copy of implementation from json_pre_request_engine.py)
    """
    if not path:
        return data
    
    parts = path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return None
        
        if current is None:
            return None
    
    return current


def test_json_path_extraction():
    """Test various JSON path extraction scenarios"""
    
    print("="*70)
    print("JSON Path Extraction Test")
    print("="*70)
    print()
    
    # 실제 API 응답 예시들
    test_cases = [
        {
            "name": "1. Simple nested object (data.accessToken)",
            "response": {
                "code": 200,
                "message": "Success",
                "data": {
                    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                    "refreshToken": "def50200a1b2c3",
                    "userId": "kimmo"
                }
            },
            "path": "data.accessToken",
            "expected": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        },
        {
            "name": "2. Direct field (data)",
            "response": {
                "code": 200,
                "data": "simple-token-value"
            },
            "path": "data",
            "expected": "simple-token-value"
        },
        {
            "name": "3. Deep nested (user.profile.id)",
            "response": {
                "user": {
                    "profile": {
                        "id": "12345",
                        "name": "Test User"
                    }
                }
            },
            "path": "user.profile.id",
            "expected": "12345"
        },
        {
            "name": "4. Array access (items.0.id)",
            "response": {
                "items": [
                    {"id": "first", "name": "Item 1"},
                    {"id": "second", "name": "Item 2"}
                ]
            },
            "path": "items.0.id",
            "expected": "first"
        },
        {
            "name": "5. Root level field (token)",
            "response": {
                "token": "abc123xyz"
            },
            "path": "token",
            "expected": "abc123xyz"
        },
        {
            "name": "6. CAPSHOME example",
            "response": {
                "code": 200,
                "message": "로그인 성공",
                "data": {
                    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
                    "refreshToken": "def50200a1b2c3d4e5f6",
                    "userId": "kimmo",
                    "userName": "김모씨"
                }
            },
            "path": "data.accessToken",
            "expected": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        },
        {
            "name": "7. Extract multiple fields",
            "response": {
                "result": {
                    "auth": {
                        "token": "bearer-token",
                        "expiresIn": 3600
                    }
                }
            },
            "extracts": {
                "TOKEN": "result.auth.token",
                "EXPIRES": "result.auth.expiresIn"
            }
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"{test['name']}")
        print(f"{'─' * 70}")
        
        if 'extracts' in test:
            # Multiple extractions
            print(f"Response: {test['response']}")
            print(f"Extracts:")
            
            all_passed = True
            for var_name, path in test['extracts'].items():
                result = get_by_path(test['response'], path)
                print(f"  {var_name}: {path} → {result}")
                
                if result is None:
                    print(f"    ❌ FAIL - Could not extract")
                    all_passed = False
            
            if all_passed:
                print(f"✅ PASS - All extractions successful")
                passed += 1
            else:
                failed += 1
        else:
            # Single extraction
            print(f"Response: {test['response']}")
            print(f"Path:     {test['path']}")
            
            result = get_by_path(test['response'], test['path'])
            print(f"Expected: {test['expected']}")
            print(f"Result:   {result}")
            
            if result == test['expected']:
                print(f"✅ PASS")
                passed += 1
            else:
                print(f"❌ FAIL")
                failed += 1
        
        print()
    
    print("="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = test_json_path_extraction()
    exit(0 if success else 1)
