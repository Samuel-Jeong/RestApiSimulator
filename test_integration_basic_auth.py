#!/usr/bin/env python3
"""Integration test for Basic Auth auto-encoding in package library"""

import sys
import json
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.json_pre_request_engine import JsonPreRequestEngine
from app.utils.variable_resolver import VariableResolver


def test_basic_auth_auto_encoding():
    """Test that Basic Auth is automatically encoded in package library execution"""
    
    print("="*70)
    print("Integration Test: Basic Auth Auto-Encoding in Package Library")
    print("="*70)
    print()
    
    # Test 1: VariableResolver with Basic Auth format
    print("Test 1: Variable Resolution")
    print("-" * 70)
    
    variables = {
        'env': {
            'USER_ID': 'testuser',
            'USER_PW': 'testpass123',
            'HOST': 'https://api.example.com'
        }
    }
    
    resolver = VariableResolver(variables)
    
    # Test Authorization header with Basic Auth
    auth_header = "Basic {{env.USER_ID}}:{{env.USER_PW}}"
    resolved = resolver.resolve(auth_header)
    
    print(f"   Original: {auth_header}")
    print(f"   Resolved: {resolved}")
    print(f"   Expected: Basic testuser:testpass123")
    print(f"   Status:   {'✅ PASS' if resolved == 'Basic testuser:testpass123' else '❌ FAIL'}")
    print()
    
    # Test 2: JsonPreRequestEngine._process_auth_header
    print("Test 2: Auth Header Processing")
    print("-" * 70)
    
    engine = JsonPreRequestEngine("projects/capshome")
    
    test_cases = [
        ("Basic testuser:testpass123", "Should encode"),
        ("Basic dGVzdHVzZXI6dGVzdHBhc3MxMjM=", "Already encoded"),
        ("Bearer eyJhbGc...", "Bearer token"),
    ]
    
    for auth_value, description in test_cases:
        processed = engine._process_auth_header(auth_value)
        print(f"   {description}:")
        print(f"      Input:  {auth_value}")
        print(f"      Output: {processed}")
        
        if "testuser:testpass123" in auth_value and ":" in auth_value.split(' ')[1]:
            # Should be encoded
            if processed.startswith("Basic ") and ":" not in processed.split(' ')[1]:
                print(f"      ✅ PASS - Correctly encoded")
            else:
                print(f"      ❌ FAIL - Not encoded")
        else:
            # Should remain unchanged
            if processed == auth_value:
                print(f"      ✅ PASS - Unchanged")
            else:
                print(f"      ❌ FAIL - Should not change")
        print()
    
    print("="*70)
    print("Integration Test Complete")
    print("="*70)


if __name__ == "__main__":
    test_basic_auth_auto_encoding()
