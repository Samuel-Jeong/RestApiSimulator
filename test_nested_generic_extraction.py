#!/usr/bin/env python3
"""Test nested generic type extraction"""

import re


def extract_response_type(return_type: str):
    """
    반환 타입에서 실제 응답 DTO 타입 추출 (중첩 제네릭 지원)
    """
    current_type = return_type.strip()
    
    # 제네릭이 없으면 바로 반환
    if '<' not in current_type:
        return current_type
    
    # 재귀적으로 가장 안쪽 제네릭 추출
    while '<' in current_type:
        # 첫 번째 < 위치 찾기
        start = current_type.find('<')
        if start == -1:
            break
        
        # 대응하는 > 찾기 (괄호 균형 맞추기)
        depth = 0
        end = -1
        for i in range(start, len(current_type)):
            if current_type[i] == '<':
                depth += 1
            elif current_type[i] == '>':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if end == -1:
            # 매칭되는 >를 못 찾으면 원본 반환
            break
        
        # < > 사이의 내용 추출
        inner_type = current_type[start+1:end].strip()
        
        # 안쪽에 제네릭이 없으면 반환
        if '<' not in inner_type:
            return inner_type
        
        # 안쪽 타입으로 이동하여 계속 추출
        current_type = inner_type
    
    return current_type


def test_nested_generic_extraction():
    """Test various nested generic scenarios"""
    
    print("="*80)
    print("Nested Generic Type Extraction Test")
    print("="*80)
    print()
    
    test_cases = [
        {
            "name": "1. 이중 중첩 (ResponseEntity + RestResponseDto)",
            "input": "ResponseEntity<RestResponseDto<SgiTokenResDto>>",
            "expected": "SgiTokenResDto"
        },
        {
            "name": "2. 삼중 중첩",
            "input": "Wrapper1<Wrapper2<Wrapper3<ActualDto>>>",
            "expected": "ActualDto"
        },
        {
            "name": "3. 단일 제네릭",
            "input": "DefaultResultDto<DrgInfGetBatteryStatusRes>",
            "expected": "DrgInfGetBatteryStatusRes"
        },
        {
            "name": "4. 제네릭 없음",
            "input": "String",
            "expected": "String"
        },
        {
            "name": "5. ResponseEntity<String>",
            "input": "ResponseEntity<String>",
            "expected": "String"
        },
        {
            "name": "6. ResponseEntity<Void>",
            "input": "ResponseEntity<Void>",
            "expected": "Void"
        },
        {
            "name": "7. List 내부 타입 추출",
            "input": "ResponseEntity<List<UserDto>>",
            "expected": "UserDto"
        },
        {
            "name": "8. 실제 CAPSHOME 예시",
            "input": "ResponseEntity<RestResponseDto<ResTokenRefreshDto>>",
            "expected": "ResTokenRefreshDto"
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"{test['name']}")
        print(f"{'─' * 80}")
        print(f"Input:    {test['input']}")
        print(f"Expected: {test['expected']}")
        
        result = extract_response_type(test['input'])
        print(f"Result:   {result}")
        
        if result == test['expected']:
            print(f"✅ PASS")
            passed += 1
        else:
            print(f"❌ FAIL")
            failed += 1
        
        print()
    
    print("="*80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_nested_generic_extraction()
    exit(0 if success else 1)
