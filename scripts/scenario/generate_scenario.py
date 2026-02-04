#!/usr/bin/env python3
"""
자바 컨트롤러 코드를 파싱하여 REST API 시나리오 파일을 자동 생성하는 스크립트
- DTO 클래스 분석
- 비즈니스 로직 파악
- 정상/실패 시나리오 자동 생성
- 성능/부하 테스트 시나리오 생성

사용법:
    python3 generate_scenario.py /path/to/controller/directory --output /path/to/output/folder
"""

import re
import json
import os
import argparse
import base64
import copy
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import glob


class JavaDtoParser:
    """자바 DTO 클래스 파싱"""
    
    def __init__(self, base_path: str, env_params: dict = None):
        # 프로젝트 루트 찾기: src 디렉토리의 부모 디렉토리
        path = Path(base_path)
        while path != path.parent:
            if (path / 'src').exists():
                self.base_path = path
                break
            path = path.parent
        else:
            # src를 찾지 못한 경우 기본 동작 (2단계 위)
            self.base_path = Path(base_path).parent.parent
        self.dto_cache = {}
        self.env_params = env_params or {}  # 환경설정의 params
        
    def parse_dto(self, dto_class_name: str, import_paths: List[str]) -> Dict[str, Any]:
        """DTO 클래스 파싱"""
        if dto_class_name in self.dto_cache:
            return self.dto_cache[dto_class_name]
        
        # DTO 파일 찾기
        dto_file = self._find_dto_file(dto_class_name, import_paths)
        if not dto_file:
            return self._generate_default_dto_fields(dto_class_name)
        
        # 파일 읽기
        try:
            with open(dto_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 부모 클래스 찾기
            parent_class = self._extract_parent_class(content)
            fields = {}
            
            # 부모 클래스가 있으면 먼저 파싱
            if parent_class:
                parent_fields = self.parse_dto(parent_class, import_paths)
                fields.update(parent_fields)
            
            # 현재 클래스 필드 파싱 (import_paths 전달)
            current_fields = self._parse_fields(content, import_paths)
            fields.update(current_fields)
            
            self.dto_cache[dto_class_name] = fields
            return fields
        except Exception as e:
            print(f"  ⚠️  DTO 파일 읽기 실패 ({dto_class_name}): {e}")
            return self._generate_default_dto_fields(dto_class_name)
    
    def _extract_parent_class(self, content: str) -> Optional[str]:
        """부모 클래스 추출 (extends)"""
        # public class ChildClass extends ParentClass 형식 찾기
        pattern = r'public\s+(?:abstract\s+)?class\s+\w+\s+extends\s+([\w<>]+)'
        match = re.search(pattern, content)
        if match:
            parent_class = match.group(1).strip()
            # 제네릭 타입 제거
            parent_class = re.sub(r'<.*?>', '', parent_class).strip()
            return parent_class
        return None
    
    def _extract_nested_type(self, field_type: str) -> Optional[str]:
        """
        필드 타입에서 중첩된 커스텀 타입 추출
        예: List<DrgInfApplyPrivacyMaskingReqAddedInfo> -> DrgInfApplyPrivacyMaskingReqAddedInfo
        예: Map<String, CustomType> -> CustomType
        예: CustomType -> CustomType
        """
        # List, Set, Collection 등의 제네릭 타입에서 내부 타입 추출
        generic_match = re.search(r'(?:List|Set|Collection)<\s*([^<>,]+)\s*>', field_type)
        if generic_match:
            inner_type = generic_match.group(1).strip()
            # 기본 타입이 아니면 반환 (커스텀 DTO인지 확인)
            if self._is_custom_type(inner_type):
                return inner_type
        
        # Map의 경우 value 타입 추출
        map_match = re.search(r'Map<[^,]+,\s*([^<>]+)>', field_type)
        if map_match:
            value_type = map_match.group(1).strip()
            if self._is_custom_type(value_type):
                return value_type
        
        # 일반 커스텀 타입 (제네릭 없는 경우)
        if self._is_custom_type(field_type):
            return field_type
        
        return None
    
    def _is_custom_type(self, type_name: str) -> bool:
        """커스텀 타입인지 확인 (Java 기본 타입이 아닌지)"""
        basic_types = [
            'String', 'Integer', 'int', 'Long', 'long', 'Double', 'double',
            'Float', 'float', 'Boolean', 'boolean', 'Byte', 'byte',
            'Short', 'short', 'Character', 'char', 'Object', 'Date',
            'LocalDate', 'LocalTime', 'LocalDateTime', 'BigDecimal', 'BigInteger'
        ]
        return type_name not in basic_types and type_name[0].isupper()
    
    def _find_dto_file(self, dto_class_name: str, import_paths: List[str]) -> Optional[str]:
        """DTO 파일 찾기"""
        # import 경로에서 찾기
        for import_path in import_paths:
            if dto_class_name in import_path:
                # 패키지 경로를 파일 경로로 변환
                relative_path = import_path.replace('.', '/') + '.java'
                # 여러 프로젝트 구조 지원
                possible_paths = [
                    self.base_path / 'src' / 'main' / 'java' / relative_path,  # Maven/Gradle 표준
                    self.base_path / 'src' / relative_path,  # 단순 구조
                    self.base_path / relative_path  # 직접 경로
                ]
                for path in possible_paths:
                    if path.exists():
                        return str(path)
        
        # dto, request, response 디렉토리에서 찾기
        search_patterns = [
            f'**/*dto*/**/{dto_class_name}.java',
            f'**/*request*/**/{dto_class_name}.java',
            f'**/*response*/**/{dto_class_name}.java',
            f'**/{dto_class_name}.java'
        ]
        
        for pattern in search_patterns:
            matches = list(self.base_path.glob(pattern))
            if matches:
                return str(matches[0])
        
        return None
    
    def _parse_fields(self, content: str, import_paths: List[str] = None) -> Dict[str, Any]:
        """DTO 필드 파싱 (재귀적으로 중첩 DTO 분석)"""
        fields = {}
        import_paths = import_paths or []
        
        # 주석 제거
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        content = re.sub(r'//[^\n]*', '', content)
        
        # private 필드 찾기
        field_pattern = r'private\s+([\w<>,\s]+)\s+(\w+)\s*;'
        matches = re.finditer(field_pattern, content)
        
        for match in matches:
            field_type = match.group(1).strip()
            field_name = match.group(2).strip()
            
            # validation 어노테이션 찾기
            # 이전 필드 선언 이후부터 현재 필드 선언까지만 확인 (더 정확하게)
            field_start = match.start()
            field_end = match.end()
            
            # 이전 private 필드를 찾아서 그 이후부터만 확인
            before_content = content[max(0, field_start-1000):field_start]
            
            # 이전 private 필드 위치 찾기
            prev_private_match = None
            for prev_match in re.finditer(r'private\s+[\w<>,\s]+\s+\w+\s*;', before_content):
                prev_private_match = prev_match
            
            if prev_private_match:
                # 이전 필드 선언 이후부터 현재 필드까지
                start_pos = field_start - 1000 + prev_private_match.end()
                before_field = content[start_pos:field_start]
            else:
                # 이전 필드가 없으면 클래스 선언 이후부터 (최대 300자)
                before_field = content[max(0, field_start-300):field_start]
            
            validation_info = self._extract_validation(before_field, field_name)
            
            fields[field_name] = {
                'type': field_type,
                'required': validation_info.get('required', False),
                'pattern': validation_info.get('pattern'),
                'min': validation_info.get('min'),
                'max': validation_info.get('max'),
                'sample_value': self._generate_sample_value(field_name, field_type, validation_info, import_paths),
                'nested_fields': None  # 중첩된 DTO 필드 정보
            }
            
            # List<CustomType> 또는 커스텀 타입의 경우 재귀 파싱
            nested_type = self._extract_nested_type(field_type)
            if nested_type:
                nested_fields = self.parse_dto(nested_type, import_paths)
                if nested_fields:
                    fields[field_name]['nested_fields'] = nested_fields
        
        return fields
    
    def _extract_validation(self, before_field: str, field_name: str) -> Dict[str, Any]:
        """Validation 어노테이션 추출 - Jakarta Bean Validation 완벽 지원"""
        validation = {}
        
        # 1. Null/Empty 체크
        # @NotNull, @NotEmpty, @NotBlank
        if re.search(r'@Not(Null|Empty|Blank)', before_field):
            validation['required'] = True
        
        # 2. 숫자 범위 검증
        # @Min(value) - long 타입
        min_match = re.search(r'@Min\(\s*(?:value\s*=\s*)?(-?\d+)', before_field)
        if min_match:
            validation['min'] = int(min_match.group(1))
        
        # @Max(value) - long 타입
        max_match = re.search(r'@Max\(\s*(?:value\s*=\s*)?(-?\d+)', before_field)
        if max_match:
            validation['max'] = int(max_match.group(1))
        
        # @DecimalMin(value, inclusive) - String 타입
        decimal_min_match = re.search(r'@DecimalMin\(\s*(?:value\s*=\s*)?"([^"]+)"', before_field)
        if decimal_min_match:
            validation['decimal_min'] = decimal_min_match.group(1)
            # inclusive 옵션 (기본값 true)
            inclusive_match = re.search(r'@DecimalMin\([^)]*inclusive\s*=\s*(false)', before_field)
            validation['decimal_min_inclusive'] = False if inclusive_match else True
        
        # @DecimalMax(value, inclusive) - String 타입
        decimal_max_match = re.search(r'@DecimalMax\(\s*(?:value\s*=\s*)?"([^"]+)"', before_field)
        if decimal_max_match:
            validation['decimal_max'] = decimal_max_match.group(1)
            # inclusive 옵션 (기본값 true)
            inclusive_match = re.search(r'@DecimalMax\([^)]*inclusive\s*=\s*(false)', before_field)
            validation['decimal_max_inclusive'] = False if inclusive_match else True
        
        # @Positive - 0보다 큰 값 (0 제외)
        if '@Positive' in before_field and '@PositiveOrZero' not in before_field:
            validation['positive'] = True
        
        # @PositiveOrZero - 0 이상
        if '@PositiveOrZero' in before_field:
            validation['positive_or_zero'] = True
        
        # @Negative - 0보다 작은 값 (0 제외)
        if '@Negative' in before_field and '@NegativeOrZero' not in before_field:
            validation['negative'] = True
        
        # @NegativeOrZero - 0 이하
        if '@NegativeOrZero' in before_field:
            validation['negative_or_zero'] = True
        
        # @Digits(integer, fraction) - 자릿수 제한
        digits_match = re.search(r'@Digits\(\s*integer\s*=\s*(\d+)\s*,\s*fraction\s*=\s*(\d+)', before_field)
        if digits_match:
            validation['digits_integer'] = int(digits_match.group(1))
            validation['digits_fraction'] = int(digits_match.group(2))
        
        # 3. 크기/길이 검증
        # @Size(min, max)
        size_min_match = re.search(r'@Size\([^)]*min\s*=\s*(\d+)', before_field)
        if size_min_match:
            validation['min_length'] = int(size_min_match.group(1))
        
        size_max_match = re.search(r'@Size\([^)]*max\s*=\s*(\d+)', before_field)
        if size_max_match:
            validation['max_length'] = int(size_max_match.group(1))
        
        # @Length (Hibernate Validator)
        length_min_match = re.search(r'@Length\([^)]*min\s*=\s*(\d+)', before_field)
        if length_min_match:
            validation['min_length'] = int(length_min_match.group(1))
        
        length_max_match = re.search(r'@Length\([^)]*max\s*=\s*(\d+)', before_field)
        if length_max_match:
            validation['max_length'] = int(length_max_match.group(1))
        
        # 4. 패턴/포맷 검증
        # @Pattern(regexp, flags)
        pattern_match = re.search(r'@Pattern\([^)]*regexp\s*=\s*"([^"]+)"', before_field)
        if pattern_match:
            validation['pattern'] = pattern_match.group(1)
        
        # @Email
        if '@Email' in before_field:
            validation['email'] = True
        
        # @URL (Hibernate Validator)
        if '@URL' in before_field:
            validation['url'] = True
        
        # @CreditCardNumber (Hibernate Validator)
        if '@CreditCardNumber' in before_field:
            validation['credit_card'] = True
        
        # @Range (Hibernate Validator) - @Min + @Max 조합
        range_match = re.search(r'@Range\(\s*min\s*=\s*(-?\d+)\s*,\s*max\s*=\s*(-?\d+)', before_field)
        if range_match:
            validation['min'] = int(range_match.group(1))
            validation['max'] = int(range_match.group(2))
            validation['range'] = True
        
        # 5. 날짜/시간 검증
        # @Future - 미래 날짜
        if '@Future' in before_field and '@FutureOrPresent' not in before_field:
            validation['future'] = True
        
        # @FutureOrPresent - 현재 또는 미래
        if '@FutureOrPresent' in before_field:
            validation['future_or_present'] = True
        
        # @Past - 과거 날짜
        if '@Past' in before_field and '@PastOrPresent' not in before_field:
            validation['past'] = True
        
        # @PastOrPresent - 현재 또는 과거
        if '@PastOrPresent' in before_field:
            validation['past_or_present'] = True
        
        # 6. Boolean 검증
        # @AssertTrue
        if '@AssertTrue' in before_field:
            validation['assert_true'] = True
        
        # @AssertFalse
        if '@AssertFalse' in before_field:
            validation['assert_false'] = True
        
        # 7. 커스텀 어노테이션 (프로젝트 특화)
        if '@LocalTimeFormat' in before_field:
            validation['custom_format'] = 'LocalTime'
        
        if '@LocalDateFormat' in before_field:
            validation['custom_format'] = 'LocalDate'
        
        if '@LocalDateTimeFormat' in before_field:
            validation['custom_format'] = 'LocalDateTime'
        
        if '@DayBitFlag' in before_field:
            validation['custom_format'] = 'DayBitFlag'
        
        return validation
    
    def _generate_sample_value(self, field_name: str, field_type: str, validation: Dict, import_paths: List[str] = None) -> Any:
        """필드에 맞는 샘플 값 생성 (재귀적으로 중첩 DTO 포함)"""
        field_lower = field_name.lower()
        import_paths = import_paths or []
        
        # 커스텀 포맷 우선 처리
        custom_format = validation.get('custom_format')
        if custom_format:
            if custom_format == 'LocalTime':
                # HH:mm:ss 형식
                if 'start' in field_lower:
                    return "09:00:00"
                elif 'end' in field_lower:
                    return "18:00:00"
                return "12:00:00"
            elif custom_format == 'LocalDate':
                # yyyy-MM-dd 형식
                return "2024-01-01"
            elif custom_format == 'LocalDateTime':
                # yyyy-MM-ddTHH:mm:ss 형식
                return "2024-01-01T12:00:00"
            elif custom_format == 'DayBitFlag':
                # 요일 비트플래그 (월~일: 1~127, 평일: 62)
                return 62
            elif custom_format == 'Email':
                return "test@example.com"
        
        # 타입별 기본값
        if 'String' in field_type:
            # Validation 어노테이션 기반 샘플 값 우선
            if validation.get('email'):
                return "test@example.com"
            elif validation.get('url'):
                return "https://example.com"
            elif validation.get('credit_card'):
                return "4532-1488-0343-6467"  # Valid test Visa card (Luhn check passes)
            
            # 필드명 기반 샘플 데이터
            if 'email' in field_lower:
                return "test@example.com"
            elif 'time' in field_lower:
                # startTime, endTime 등 시간 필드
                if 'start' in field_lower:
                    return "09:00:00"
                elif 'end' in field_lower:
                    return "18:00:00"
                return "12:00:00"
            elif 'date' in field_lower:
                if 'time' in field_lower:  # datetime
                    return "2024-01-01T12:00:00"
                return "2024-01-01"
            elif 'color' in field_lower:
                # 색상 코드
                return "#FF5733"
            elif 'name' in field_lower:
                if 'user' in field_lower or 'author' in field_lower:
                    return "Test User"
                elif 'schedule' in field_lower:
                    return "주간 근무"
                return "Test Name"
            elif 'phone' in field_lower or 'tel' in field_lower:
                return "010-1234-5678"
            elif 'addr' in field_lower or 'address' in field_lower:
                return "서울시 강남구"
            elif 'url' in field_lower:
                return "https://example.com"
            elif 'code' in field_lower:
                return "TEST001"
            elif 'desc' in field_lower or 'description' in field_lower:
                return "Test description"
            elif 'title' in field_lower:
                return "Test Title"
            elif 'content' in field_lower or 'body' in field_lower:
                return "Test Content"
            elif 'id' in field_lower:
                # env params에 정의된 키와 매칭 (대소문자 무관)
                for param_key in self.env_params.keys():
                    if field_name.lower() == param_key.lower():
                        return "{{" + param_key + "}}"
                # params에 없으면 기본값
                return "test-id-001"
            elif 'status' in field_lower:
                return "ACTIVE"
            elif 'type' in field_lower:
                return "DEFAULT"
            elif 'password' in field_lower or 'pwd' in field_lower:
                return "Test1234!"
            elif 'comment' in field_lower:
                return "Test comment"
            else:
                # 길이 제약이 있으면 적용
                max_length = validation.get('max_length')
                if max_length:
                    if max_length <= 10:
                        return "test"[:max_length]
                    elif max_length <= 20:
                        return "test value"[:max_length]
                    elif max_length <= 50:
                        return "test sample value"[:max_length]
                    else:
                        return "test sample value for testing"[:max_length]
                return "test"
        
        elif field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short']:
            # env params에 정의된 키와 매칭 (대소문자 무관)
            for param_key in self.env_params.keys():
                if field_name.lower() == param_key.lower():
                    return "{{" + param_key + "}}"
            # params에 없으면 기존 로직
            # 요일 비트플래그 체크 - 더 정확하게 매칭
            if ('day' in field_lower and 'week' in field_lower) or ('day' in field_lower and 'of' in field_lower):
                return 62  # 평일 (월~금)
            elif 'bit' in field_lower or 'flag' in field_lower:
                return 1
            elif validation.get('min') is not None:
                return validation['min']
            elif 'count' in field_lower or 'num' in field_lower:
                return 10
            elif 'idx' in field_lower or 'id' in field_lower:
                return 1
            elif 'age' in field_lower:
                return 25
            elif 'price' in field_lower or 'amount' in field_lower:
                return 10000
            elif 'year' in field_lower:
                return 2024
            elif 'month' in field_lower:
                return 1
            elif 'day' in field_lower and 'week' not in field_lower:
                return 1
            elif 'hour' in field_lower:
                return 9
            elif 'minute' in field_lower:
                return 0
            else:
                return 1
        
        elif field_type in ['double', 'Double', 'float', 'Float', 'BigDecimal']:
            if 'rate' in field_lower or 'ratio' in field_lower:
                return 0.5
            elif 'price' in field_lower or 'amount' in field_lower:
                return 10000.0
            else:
                return 1.0
        
        elif field_type in ['boolean', 'Boolean']:
            if 'is' in field_lower or 'has' in field_lower or 'enable' in field_lower:
                return True
            return False
        
        elif 'Date' in field_type or 'LocalDate' in field_type:
            return "2024-01-01"
        
        elif 'Time' in field_type:
            if 'LocalDateTime' in field_type:
                return "2024-01-01T12:00:00"
            elif 'LocalTime' in field_type:
                if 'start' in field_lower:
                    return "09:00:00"
                elif 'end' in field_lower:
                    return "18:00:00"
                return "12:00:00"
            else:
                return "2024-01-01T12:00:00"
        
        elif 'List<' in field_type or 'Set<' in field_type:
            # List 내부의 커스텀 타입 추출 및 샘플 객체 생성
            nested_type = self._extract_nested_type(field_type)
            if nested_type and import_paths:
                # 중첩 DTO 파싱
                nested_fields = self.parse_dto(nested_type, import_paths)
                if nested_fields:
                    # 중첩 DTO의 샘플 객체 생성
                    sample_obj = {}
                    for nested_field_name, nested_field_info in nested_fields.items():
                        sample_obj[nested_field_name] = nested_field_info['sample_value']
                    # 샘플 객체 1개를 담은 배열 반환
                    return [sample_obj]
            return []
        
        elif 'Map<' in field_type:
            # Map의 value 타입이 커스텀 DTO인 경우
            nested_type = self._extract_nested_type(field_type)
            if nested_type and import_paths:
                nested_fields = self.parse_dto(nested_type, import_paths)
                if nested_fields:
                    sample_obj = {}
                    for nested_field_name, nested_field_info in nested_fields.items():
                        sample_obj[nested_field_name] = nested_field_info['sample_value']
                    return {"key1": sample_obj}
            return {}
        
        # 일반 커스텀 타입 (List, Map이 아닌 경우)
        elif self._is_custom_type(field_type) and import_paths:
            nested_fields = self.parse_dto(field_type, import_paths)
            if nested_fields:
                sample_obj = {}
                for nested_field_name, nested_field_info in nested_fields.items():
                    sample_obj[nested_field_name] = nested_field_info['sample_value']
                return sample_obj
        
        return "test"
    
    def _generate_default_dto_fields(self, dto_class_name: str) -> Dict[str, Any]:
        """기본 DTO 필드 생성"""
        fields = {}
        
        # DTO 타입별 기본 필드
        if 'User' in dto_class_name:
            fields = {
                'username': {'type': 'String', 'required': True, 'sample_value': 'testuser'},
                'email': {'type': 'String', 'required': True, 'sample_value': 'test@example.com'},
                'name': {'type': 'String', 'required': False, 'sample_value': 'Test User'}
            }
        elif 'Post' in dto_class_name or 'Article' in dto_class_name:
            fields = {
                'title': {'type': 'String', 'required': True, 'sample_value': 'Test Title'},
                'content': {'type': 'String', 'required': True, 'sample_value': 'Test Content'}
            }
        elif 'Comment' in dto_class_name:
            fields = {
                'content': {'type': 'String', 'required': True, 'sample_value': 'Test Comment'}
            }
        else:
            fields = {
                'data': {'type': 'String', 'required': False, 'sample_value': 'test'}
            }
        
        return fields


class JavaControllerParser:
    """자바 컨트롤러 파싱 클래스"""
    
    HTTP_METHODS = ['Get', 'Post', 'Put', 'Delete', 'Patch']
    
    def __init__(self, java_file_path: str, context_path: str = "", auth_annotations: list = None, auth_mode: str = "include", env_params: dict = None, auth_header_exclude_keyword: list = None):
        self.java_file_path = java_file_path
        self.content = self._read_file()
        self.context_path = context_path.rstrip('/') if context_path else ""
        self.auth_annotations = auth_annotations if auth_annotations else []
        self.auth_mode = auth_mode.lower()  # "include" or "exclude"
        self.controller_base_path = ""
        self.controller_name = ""
        self.package_name = ""  # 패키지 경로 (예: com.oauth.controller)
        self.endpoints = []
        self.import_paths = []
        self.env_params = env_params or {}  # 환경설정의 params
        self.auth_header_exclude_keyword = auth_header_exclude_keyword or []  # Authorization 헤더 제외 키워드
        self.dto_parser = JavaDtoParser(java_file_path, env_params)
        
    def _read_file(self) -> str:
        """파일 읽기"""
        with open(self.java_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse(self):
        """컨트롤러 파싱"""
        self._extract_package()
        self._extract_imports()
        self._extract_controller_name()
        self._extract_base_path()
        self._extract_endpoints()
        
    def _extract_package(self):
        """패키지 경로 추출"""
        pattern = r'package\s+([\w.]+);'
        match = re.search(pattern, self.content)
        if match:
            self.package_name = match.group(1)
    
    def _extract_imports(self):
        """import 경로 추출"""
        pattern = r'import\s+([\w.]+);'
        matches = re.finditer(pattern, self.content)
        for match in matches:
            self.import_paths.append(match.group(1))
    
    def _extract_controller_name(self):
        """컨트롤러 클래스명 추출"""
        pattern = r'public\s+class\s+(\w+Controller)'
        match = re.search(pattern, self.content)
        if match:
            self.controller_name = match.group(1)
        else:
            self.controller_name = Path(self.java_file_path).stem.replace('Controller', '')
    
    def _extract_base_path(self):
        """컨트롤러 베이스 경로 추출"""
        pattern = r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)'
        match = re.search(pattern, self.content)
        if match:
            self.controller_base_path = match.group(1)
        else:
            pattern = r'@RequestMapping\s*\([^)]*value\s*=\s*["\']([^"\']+)["\'][^)]*\)'
            match = re.search(pattern, self.content)
            if match:
                self.controller_base_path = match.group(1)
    
    def _extract_endpoints(self):
        """엔드포인트 추출"""
        # 주석 제거 (/* */, //)
        content_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', self.content)
        content_no_comments = re.sub(r'//[^\n]*', '', content_no_comments)
        
        # 1. @GetMapping, @PostMapping 등의 축약형 어노테이션 찾기
        for method in self.HTTP_METHODS:
            # @GetMapping, @PostMapping 등의 어노테이션 찾기
            # 괄호가 있는 경우와 없는 경우 모두 처리
            pattern = r'@' + method + r'Mapping(?:\s*\([^)]*\))?'
            annotation_matches = re.finditer(pattern, content_no_comments)
            
            for anno_match in annotation_matches:
                full_annotation = anno_match.group(0)
                anno_start = anno_match.start()
                anno_end = anno_match.end()
                
                # 어노테이션 파라미터 추출
                annotation_params = ""
                if '(' in full_annotation:
                    params_match = re.search(r'\(([^)]*)\)', full_annotation)
                    if params_match:
                        annotation_params = params_match.group(1)
                
                # 어노테이션 앞쪽 텍스트에서 인증 어노테이션 확인 (500자 범위)
                preceding_text = content_no_comments[max(0, anno_start-500):anno_start]
                has_auth_annotation, found_annotations = self._check_auth_annotations(preceding_text)
                
                # 어노테이션 이후 public 메서드 찾기 (최대 5000자 범위)
                # 다른 어노테이션들이 중간에 있을 수 있으므로 범위를 넓힘
                # Swagger 어노테이션(@Operation, @ApiResponseExamples)이 복잡하게 중첩된 경우를 고려
                search_text = content_no_comments[anno_end:anno_end+5000]
                
                # public 메서드 패턴 (반환 타입, 제너릭 타입, 여러 줄 파라미터 지원)
                # public @ResponseBody 같은 inline annotation 지원
                # ResponseEntity<?> 같은 와일드카드 제네릭 타입 지원
                # throws 절 지원 (파라미터에 메서드 본문이 포함되지 않도록)
                method_pattern = r'public\s+(?:@\w+\s+)*([\w<>,\s?]+)\s+(\w+)\s*\(([^)]*(?:\([^)]*\))*[^)]*)\)\s*(?:throws\s+[\w,\s.]+)?\s*\{'
                method_match = re.search(method_pattern, search_text)
                
                if method_match:
                    return_type = method_match.group(1).strip()  # 반환 타입
                    method_name = method_match.group(2)
                    method_params = method_match.group(3)
                    
                    # 중복 체크
                    if not any(e['original_method_name'] == method_name for e in self.endpoints):
                        endpoint = self._parse_endpoint(method, annotation_params, method_name, method_params, has_auth_annotation, found_annotations, return_type)
                        if endpoint:
                            self.endpoints.append(endpoint)
        
        # 2. @RequestMapping(method = RequestMethod.XXX) 형식 찾기
        # @RequestMapping(value = "/path", method = RequestMethod.POST) 또는
        # @RequestMapping(method = RequestMethod.GET, value = "/path") 형식
        request_mapping_pattern = r'@RequestMapping\s*\([^)]*method\s*=\s*RequestMethod\.(\w+)[^)]*\)'
        request_mapping_matches = re.finditer(request_mapping_pattern, content_no_comments)
        
        for anno_match in request_mapping_matches:
            full_annotation = anno_match.group(0)
            http_method = anno_match.group(1)  # GET, POST, PUT, DELETE, PATCH
            anno_start = anno_match.start()
            anno_end = anno_match.end()
            
            # 어노테이션 파라미터 추출 (전체 괄호 안 내용)
            params_match = re.search(r'\(([^)]*)\)', full_annotation)
            annotation_params = params_match.group(1) if params_match else ""
            
            # 어노테이션 앞쪽 텍스트에서 인증 어노테이션 확인 (500자 범위)
            preceding_text = content_no_comments[max(0, anno_start-500):anno_start]
            has_auth_annotation, found_annotations = self._check_auth_annotations(preceding_text)
            
            # 어노테이션 이후 public 메서드 찾기 (최대 5000자 범위)
            # Swagger 어노테이션(@Operation, @ApiResponseExamples)이 복잡하게 중첩된 경우를 고려
            search_text = content_no_comments[anno_end:anno_end+5000]
            
            # public 메서드 패턴 (반환 타입, 제너릭 타입, 여러 줄 파라미터 지원)
            # public @ResponseBody 같은 inline annotation 지원
            # ResponseEntity<?> 같은 와일드카드 제네릭 타입 지원
            # throws 절 지원 (파라미터에 메서드 본문이 포함되지 않도록)
            method_pattern = r'public\s+(?:@\w+\s+)*([\w<>,\s?]+)\s+(\w+)\s*\(([^)]*(?:\([^)]*\))*[^)]*)\)\s*(?:throws\s+[\w,\s.]+)?\s*\{'
            method_match = re.search(method_pattern, search_text)
            
            if method_match:
                return_type = method_match.group(1).strip()  # 반환 타입
                method_name = method_match.group(2)
                method_params = method_match.group(3)
                
                # 중복 체크
                if not any(e['original_method_name'] == method_name for e in self.endpoints):
                    endpoint = self._parse_endpoint(http_method, annotation_params, method_name, method_params, has_auth_annotation, found_annotations, return_type)
                    if endpoint:
                        self.endpoints.append(endpoint)
    
    def _check_auth_annotations(self, text: str) -> tuple[bool, list]:
        """인증 관련 어노테이션 확인 및 발견된 어노테이션 리스트 반환
        
        auth_mode에 따라 동작 방식이 다름:
        - include: auth_annotations에 지정된 어노테이션이 있으면 인증 필요 (기본값)
        - exclude: 기본적으로 모두 인증 필요, auth_annotations에 지정된 어노테이션이 있으면 인증 불필요
        - all: 모든 메서드에 인증 필요 (어노테이션별로 다른 인증 방식 사용)
        """
        # all 모드: 모든 어노테이션 찾아서 반환
        if self.auth_mode == "all":
            found_annotations = []
            # auth_annotations 뿐만 아니라 모든 어노테이션 찾기
            all_annotations = re.findall(r'@(\w+)', text)
            for anno in all_annotations:
                if anno not in ['Override', 'Deprecated', 'SuppressWarnings']:  # Java 기본 어노테이션 제외
                    found_annotations.append(anno)
            return True, found_annotations  # 항상 인증 필요
        
        # auth_annotations가 비어있으면
        if not self.auth_annotations:
            if self.auth_mode == "exclude":
                # exclude 모드에서 auth_annotations가 없으면 모두 인증 필요
                return True, []
            else:
                # include 모드에서 auth_annotations가 없으면 모두 인증 불필요
                return False, []
        
        found_annotations = []
        for annotation_mapping in self.auth_annotations:
            # "UserCert:wpm-get-user-info.json" 또는 "UserCert" 형식
            # 콜론(:)이 있으면 콜론 앞의 어노테이션만 추출
            annotation = annotation_mapping.split(':')[0].strip()
            
            # @ 기호가 없으면 자동으로 추가
            if not annotation.startswith('@'):
                annotation_with_at = '@' + annotation
            else:
                annotation_with_at = annotation
                annotation = annotation[1:]  # @ 제거
            
            if annotation_with_at in text:
                found_annotations.append(annotation)
        
        has_annotation = len(found_annotations) > 0
        
        # auth_mode에 따라 결과 반환
        if self.auth_mode == "exclude":
            # exclude 모드: 어노테이션이 있으면 인증 불필요 (NOT 연산)
            return not has_annotation, found_annotations
        else:
            # include 모드: 어노테이션이 있으면 인증 필요 (기본 동작)
            return has_annotation, found_annotations
    
    def _parse_endpoint(self, http_method: str, annotation_params: str, 
                       method_name: str, method_params: str, has_auth: bool = False, 
                       annotations: list = None, return_type: str = None) -> Optional[Dict[str, Any]]:
        """개별 엔드포인트 파싱"""
        http_method = http_method.upper()
        
        path = self._extract_path(annotation_params)
        if not path:
            path = ""
        
        # context_path + controller_base_path + path 조합
        full_path = self.context_path + self.controller_base_path + path
        if not full_path.startswith('/'):
            full_path = '/' + full_path
        
        readable_name = self._method_name_to_readable(method_name)
        params_info = self._parse_method_params(method_params)
        
        # DTO 정보 파싱
        dto_fields = {}
        model_attribute_fields = {}
        
        # @RequestBody DTO 파싱
        if params_info['request_body_type']:
            dto_fields = self.dto_parser.parse_dto(
                params_info['request_body_type'],
                self.import_paths
            )
        
        # @ModelAttribute DTO 파싱 (GET 요청의 query parameter로 사용)
        if params_info.get('model_attribute_type'):
            model_attribute_fields = self.dto_parser.parse_dto(
                params_info['model_attribute_type'],
                self.import_paths
            )
        
        # 응답 타입 파싱 (DefaultResultDto<ResponseDto> 형식)
        response_type = None
        response_dto_fields = {}
        if return_type:
            response_type = self._extract_response_type(return_type)
            if response_type and response_type != 'Void':
                response_dto_fields = self.dto_parser.parse_dto(
                    response_type,
                    self.import_paths
                )
        
        # Path variables는 params_info에서 더 자세한 정보 (타입 포함) 가져오기
        path_variables = params_info.get('path_variables', [])
        
        endpoint = {
            'name': readable_name,
            'method': http_method,
            'path': full_path,
            'original_method_name': method_name,
            'path_variables': path_variables,
            'has_request_body': params_info['has_request_body'],
            'request_body_type': params_info['request_body_type'],
            'query_params': params_info['query_params'],
            'dynamic_params': params_info.get('dynamic_params'),  # @RequestParam Map<String, String>
            'dto_fields': dto_fields,
            'model_attribute_fields': model_attribute_fields,
            'requires_auth': has_auth,
            'annotations': annotations or [],
            'response_type': response_type,
            'response_dto_fields': response_dto_fields,
            'package': self.package_name,  # 패키지 경로 추가
            'has_auth_header_param': params_info.get('has_auth_header_param', False)  # Authorization 헤더 파라미터 체크
        }
        
        return endpoint
    
    def _extract_path(self, annotation_params: str) -> str:
        """어노테이션에서 경로 추출"""
        if not annotation_params or not annotation_params.strip():
            return ""
        
        # value = "path" 또는 path = "path" 형식
        match = re.search(r'(?:value|path)\s*=\s*["\']([^"\']+)["\']', annotation_params)
        if match:
            return match.group(1)
        
        # 단순 "path" 형식
        match = re.search(r'["\']([^"\']+)["\']', annotation_params)
        if match:
            return match.group(1)
        
        return ""
    
    def _method_name_to_readable(self, method_name: str) -> str:
        """메서드명을 읽기 쉬운 이름으로 변환"""
        words = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', method_name)).split()
        return ' '.join(word.capitalize() for word in words)
    
    def _extract_response_type(self, return_type: str) -> Optional[str]:
        """
        반환 타입에서 실제 응답 DTO 타입 추출 (중첩 제네릭 지원)
        
        예시:
        - ResponseEntity<RestResponseDto<SgiTokenResDto>> -> SgiTokenResDto
        - DefaultResultDto<DrgInfGetBatteryStatusRes> -> DrgInfGetBatteryStatusRes
        - ResponseEntity<String> -> String
        - DefaultResultDto<Void> -> Void
        - String -> String
        - ResponseEntity<List<UserDto>> -> List<UserDto> (컬렉션은 유지)
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
    
    def _get_sample_value_for_type(self, type_name: str, param_name: str = "") -> Any:
        """
        자료형에 맞는 샘플 데이터 생성
        
        Args:
            type_name: Java 자료형 (String, Integer, Long, Boolean 등)
            param_name: 파라미터 이름 (의미있는 샘플 값 생성에 사용)
        
        Returns:
            자료형에 맞는 샘플 데이터
        """
        # 제네릭 타입 제거 (List<String> -> List)
        base_type = re.sub(r'<.*?>', '', type_name).strip()
        
        # 파라미터 이름 기반 샘플 값 매핑
        param_lower = param_name.lower()
        
        # String 타입
        if base_type in ['String', 'str']:
            # env params에 정의된 키와 매칭 (대소문자 무관)
            for param_key in self.env_params.keys():
                if param_name.lower() == param_key.lower():
                    return "{{" + param_key + "}}"
            # params에 없으면 기존 로직
            if 'id' in param_lower:
                return "test-id-001"
            elif 'name' in param_lower:
                return "test-name"
            elif 'email' in param_lower:
                return "test@example.com"
            elif 'phone' in param_lower or 'tel' in param_lower:
                return "010-1234-5678"
            elif 'url' in param_lower or 'uri' in param_lower:
                return "https://example.com"
            elif 'code' in param_lower:
                return "TEST001"
            elif 'message' in param_lower or 'msg' in param_lower:
                return "test message"
            elif 'description' in param_lower or 'desc' in param_lower:
                return "test description"
            else:
                return "test-value"
        
        # Integer 타입
        elif base_type in ['Integer', 'int']:
            # env params에 정의된 키와 매칭 (대소문자 무관)
            for param_key in self.env_params.keys():
                if param_name.lower() == param_key.lower():
                    # params 값이 숫자로 변환 가능하면 숫자로, 아니면 변수 참조
                    param_value = self.env_params[param_key]
                    if isinstance(param_value, int):
                        return f"{{{{{param_key}}}}}"  # 변수 참조 형태
                    elif isinstance(param_value, str):
                        try:
                            # 문자열이 숫자로 변환 가능한지 확인
                            int(param_value)
                            return f"{{{{{param_key}}}}}"  # 변수 참조 형태
                        except ValueError:
                            pass  # 숫자가 아니면 기본 로직 사용
            # params에 없으면 기존 로직
            if 'page' in param_lower:
                return 1
            elif 'size' in param_lower or 'limit' in param_lower:
                return 10
            elif 'count' in param_lower or 'cnt' in param_lower:
                return 5
            elif 'type' in param_lower:
                return 1
            elif 'status' in param_lower:
                return 1
            elif 'year' in param_lower:
                return 2024
            elif 'month' in param_lower:
                return 1
            elif 'day' in param_lower:
                return 1
            else:
                return 1
        
        # Long 타입
        elif base_type in ['Long', 'long']:
            # env params에 정의된 키와 매칭 (대소문자 무관)
            for param_key in self.env_params.keys():
                if param_name.lower() == param_key.lower():
                    return f"{{{{{param_key}}}}}"  # 변수 참조 형태
            # params에 없으면 기존 로직
            if 'id' in param_lower:
                return 1000
            elif 'time' in param_lower or 'timestamp' in param_lower:
                return 1704067200000  # 2024-01-01 00:00:00
            else:
                return 1000
        
        # Boolean 타입
        elif base_type in ['Boolean', 'boolean', 'bool']:
            if 'is' in param_lower or 'has' in param_lower or 'enable' in param_lower:
                return True
            else:
                return True
        
        # Double, Float 타입
        elif base_type in ['Double', 'double', 'Float', 'float']:
            if 'rate' in param_lower or 'ratio' in param_lower:
                return 0.5
            elif 'price' in param_lower or 'amount' in param_lower:
                return 1000.0
            elif 'percent' in param_lower:
                return 50.0
            else:
                return 1.0
        
        # Date 관련 타입
        elif base_type in ['LocalDate', 'Date']:
            return "2024-01-01"
        
        elif base_type in ['LocalDateTime', 'DateTime', 'Timestamp']:
            return "2024-01-01T00:00:00"
        
        elif base_type == 'LocalTime':
            return "00:00:00"
        
        # Collection 타입
        elif base_type in ['List', 'ArrayList', 'Set', 'HashSet']:
            return []
        
        elif base_type in ['Map', 'HashMap']:
            return {}
        
        # 기타 객체 타입이나 알 수 없는 타입
        else:
            # 기본값으로 문자열 반환
            return "test-value"
    
    def _parse_method_params(self, method_params: str) -> Dict[str, Any]:
        """메서드 파라미터 파싱"""
        result = {
            'has_request_body': False,
            'request_body_type': None,
            'query_params': [],
            'path_variables': [],
            'model_attribute_type': None,
            'dynamic_params': None,  # @RequestParam Map<String, String> 처리
            'has_auth_header_param': False  # @RequestHeader(Authorization) 체크
        }
        
        if not method_params.strip():
            return result
        
        # @RequestHeader에서 Authorization 헤더 제외 키워드 체크
        # 이 경우 자동 auth 헤더 추가를 건너뜀
        if '@RequestHeader' in method_params and self.auth_header_exclude_keyword:
            for keyword in self.auth_header_exclude_keyword:
                # 키워드가 method_params에 포함되어 있는지 체크
                if keyword in method_params:
                    result['has_auth_header_param'] = True
                    break
                # "키워드" 문자열 패턴 체크 (따옴표로 감싸진 경우)
                elif re.search(rf'@RequestHeader\s*\(\s*["\']' + re.escape(keyword) + r'["\']', method_params):
                    result['has_auth_header_param'] = True
                    break
                # value="키워드" 패턴 체크
                elif re.search(rf'@RequestHeader\s*\([^)]*value\s*=\s*["\']' + re.escape(keyword) + r'["\']', method_params):
                    result['has_auth_header_param'] = True
                    break
        
        # 줄바꿈 제거 및 공백 정리
        method_params = ' '.join(method_params.split())
        
        # @RequestBody 처리
        if '@RequestBody' in method_params:
            result['has_request_body'] = True
            # @Valid @RequestBody CheckInOutReqDto checkInOutReqDto 형식 처리
            match = re.search(r'@RequestBody\s+(\w+)\s+\w+', method_params)
            if match:
                result['request_body_type'] = match.group(1)
        
        # @RequestParam 처리
        # 다양한 형태 지원:
        # 1. @RequestParam("paramName") String paramName
        # 2. @RequestParam(value="paramName") String paramName
        # 3. @RequestParam(name="paramName") String paramName
        # 4. @RequestParam String paramName
        # 5. @RequestParam(value="paramName", required=true) String paramName
        
        # 먼저 @RequestParam이 있는 모든 파라미터를 찾기 (자료형도 캡처)
        # Map<String, String> 같은 제네릭 타입을 위해 쉼표와 공백도 포함
        # +? 대신 + 사용하여 제네릭 타입 전체 캡처
        param_pattern = r'@RequestParam\s*(?:\(([^)]*)\))?\s+(?:@[\w]+\s+)*([\w<>,\s]+)\s+(\w+)'
        param_matches = re.finditer(param_pattern, method_params)
        
        for match in param_matches:
            annotation_content = match.group(1)  # 괄호 안 내용
            param_type = match.group(2)          # 자료형 (String, Integer 등)
            variable_name = match.group(3)       # 변수명
            
            # Map<String, String> 타입 체크 - 동적 파라미터
            if 'Map<' in param_type or 'Map <' in param_type:
                # 환경 설정 파일의 params에서 해당 변수명으로 값 찾기
                # 예: parameters 변수 → env_params['parameters'] → "grant_type=client_credentials"
                result['dynamic_params'] = {
                    'variable_name': variable_name,
                    'type': param_type
                }
                continue  # 일반 query_params에는 추가하지 않음
            
            param_name = None
            
            if annotation_content:
                # value 또는 name 속성에서 파라미터명 추출
                # value="paramName" 또는 name="paramName" 형태
                attr_match = re.search(r'(?:value|name)\s*=\s*["\'](\w+)["\']', annotation_content)
                if attr_match:
                    param_name = attr_match.group(1)
                else:
                    # 직접 값 지정: @RequestParam("paramName")
                    direct_match = re.search(r'^["\'](\w+)["\']', annotation_content.strip())
                    if direct_match:
                        param_name = direct_match.group(1)
            
            # 파라미터명을 찾지 못했으면 변수명 사용
            if not param_name:
                param_name = variable_name
            
            result['query_params'].append({
                'name': param_name,
                'type': param_type
            })
        
        # @PathVariable 처리 (자료형도 캡처)
        path_matches = re.finditer(r'@PathVariable(?:\s*\([^)]*\))?\s+([\w<>]+)\s+(\w+)', method_params)
        for match in path_matches:
            param_type = match.group(1)    # 자료형
            variable_name = match.group(2)  # 변수명
            result['path_variables'].append({
                'name': variable_name,
                'type': param_type
            })
        
        # @ModelAttribute 처리 (GET 요청의 경우 query parameter로 처리)
        if '@ModelAttribute' in method_params:
            match = re.search(r'@ModelAttribute\s+(\w+)\s+\w+', method_params)
            if match:
                # ModelAttribute는 query parameter나 form data로 사용됨
                # 여기서는 DTO 타입만 저장하고 나중에 처리
                result['model_attribute_type'] = match.group(1)
        
        return result


class ScenarioGenerator:
    """시나리오 파일 생성 클래스"""
    
    def __init__(self, parser: JavaControllerParser, output_dir: str, auth_bearer_token: str = "", auth_basic_token: str = "", custom_headers: dict = None, continue_on_error: bool = False, environment: str = "", auth_annotations: List[str] = None, output_format: str = 'yaml', env_file_path: str = None, auth_mode: str = 'include', default_auth: str = 'bearer', default_auth_token: str = '', default_auth_library: str = '', annotation_auth_mapping: List[str] = None, package_auth_mapping: List[str] = None, auth_header_exclude_keyword: List[str] = None):
        self.parser = parser
        self.output_dir = output_dir
        self.auth_bearer_token = auth_bearer_token
        self.auth_basic_token = auth_basic_token
        self.custom_headers = custom_headers or {}
        self.continue_on_error = continue_on_error
        self.environment = environment
        self.output_format = output_format  # 'yaml' or 'json'
        self.auth_mode = auth_mode  # 'include', 'exclude', 'all'
        self.default_auth = default_auth  # 'bearer', 'basic', 'none'
        self.default_auth_token = default_auth_token  # 기본 인증 토큰
        self.default_auth_library = default_auth_library  # 기본 인증 토큰을 위한 package library
        self.auth_header_exclude_keyword = auth_header_exclude_keyword or []  # Authorization 헤더 제외 키워드
        
        # 환경 파일 로드
        self.env_params = {}
        self.env_variables = {}
        if env_file_path and os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    env_data = json.load(f)
                    self.env_params = env_data.get('params', {})
                    self.env_variables = env_data.get('variables', {})
                    print(f"✅ 환경 파일 로드: {env_file_path}")
                    print(f"   📝 params: {list(self.env_params.keys())}")
                    print(f"   📝 variables: {list(self.env_variables.keys())}")
            except Exception as e:
                print(f"⚠️  환경 파일 로드 실패: {e}")
        
        # 어노테이션별 pre-request 매핑 파싱
        # 형식: "UserCert:wpm-get-user-info.json" 또는 "Authenticated"
        self.annotation_pre_request_map = {}  # {annotation: pre_request_file}
        self.auth_annotations_set = set()  # 인증이 필요한 어노테이션 목록
        
        if auth_annotations:
            for mapping in auth_annotations:
                if ':' in mapping:
                    # "UserCert:wpm-get-user-info.json" 형식
                    annotation, pre_request_file = mapping.split(':', 1)
                    annotation = annotation.strip().replace('@', '')
                    pre_request_file = pre_request_file.strip()
                    self.annotation_pre_request_map[annotation] = pre_request_file
                    self.auth_annotations_set.add(annotation)
                else:
                    # "UserCert" 형식 (pre-request 없이 인증만)
                    annotation = mapping.strip().replace('@', '')
                    self.auth_annotations_set.add(annotation)
        
        # 어노테이션별 인증 방식 매핑 파싱 (auth-mode=all 사용 시)
        # 형식: "NoAuth:basic:{{USER_ID}}:{{USER_PW}}" 
        #      또는 "NoAuth:basic:{{USER_ID}}:{{USER_PW}}:X-Auth-Server={{SERVER_ID}}"
        #      또는 "UserCert:bearer:{{USER_CERT_TOKEN}}:X-Custom={{VALUE}}"
        self.annotation_auth_map = {}  # {annotation: {'type': 'bearer'|'basic', 'token': '...', 'headers': {...}}}
        
        if annotation_auth_mapping:
            for mapping in annotation_auth_mapping:
                parts = mapping.split(':')  # 전체 분리
                if len(parts) >= 3:
                    annotation = parts[0].strip().replace('@', '')
                    auth_type = parts[1].strip().lower()
                    
                    token = None
                    extra_headers = {}
                    header_start_idx = 3
                    
                    if auth_type == 'basic' and len(parts) >= 4:
                        # "NoAuth:basic:{{USER_ID}}:{{USER_PW}}" 형식
                        token = f"{parts[2].strip()}:{parts[3].strip()}"
                        header_start_idx = 4
                    elif auth_type == 'bearer':
                        # "UserCert:bearer:{{USER_CERT_TOKEN}}" 형식
                        token = parts[2].strip()
                        header_start_idx = 3
                    else:
                        continue
                    
                    # 추가 헤더 파싱 (Key=Value 또는 Key={{VAR}} 형식)
                    for i in range(header_start_idx, len(parts)):
                        header_part = parts[i].strip()
                        if '=' in header_part:
                            key, value = header_part.split('=', 1)
                            extra_headers[key.strip()] = value.strip()
                    
                    self.annotation_auth_map[annotation] = {
                        'type': auth_type,
                        'token': token,
                        'headers': extra_headers
                    }
        
        # 패키지별 인증 방식 매핑 파싱 (auth-mode=all 사용 시)
        # 형식: "com.oauth:basic:{{USER_ID}}:{{USER_PW}}" 
        #      또는 "com.oauth:basic:{{USER_ID}}:{{USER_PW}}:X-Auth-Server={{SERVER_ID}}"
        #      또는 "com.user.api:bearer:{{USER_CERT_TOKEN}}:X-Custom={{VALUE}}"
        self.package_auth_map = {}  # {package: {'type': 'bearer'|'basic', 'token': '...', 'headers': {...}}}
        
        if package_auth_mapping:
            for mapping in package_auth_mapping:
                parts = mapping.split(':')  # 전체 분리
                if len(parts) >= 3:
                    package = parts[0].strip()
                    auth_type = parts[1].strip().lower()
                    
                    token = None
                    extra_headers = {}
                    header_start_idx = 3
                    
                    if auth_type == 'basic' and len(parts) >= 4:
                        # "com.oauth:basic:{{USER_ID}}:{{USER_PW}}" 형식
                        token = f"{parts[2].strip()}:{parts[3].strip()}"
                        header_start_idx = 4
                    elif auth_type == 'bearer':
                        # "com.user.api:bearer:{{USER_CERT_TOKEN}}" 형식
                        token = parts[2].strip()
                        header_start_idx = 3
                    else:
                        continue
                    
                    # 추가 헤더 파싱 (Key=Value 또는 Key={{VAR}} 형식)
                    for i in range(header_start_idx, len(parts)):
                        header_part = parts[i].strip()
                        if '=' in header_part:
                            key, value = header_part.split('=', 1)
                            extra_headers[key.strip()] = value.strip()
                    
                    self.package_auth_map[package] = {
                        'type': auth_type,
                        'token': token,
                        'headers': extra_headers
                    }
                    
                    headers_info = f" + {len(extra_headers)} headers" if extra_headers else ""
                    print(f"📦 패키지 인증 매핑: {package} → {auth_type} ({token[:20]}...){headers_info}")
    
    def _replace_path_variables(self, path: str, endpoint: Dict[str, Any] = None) -> tuple[str, dict]:
        """Path variable을 샘플 값으로 치환하고 치환된 값들을 반환"""
        # endpoint의 path_variables에서 자료형 정보 추출
        path_var_types = {}
        if endpoint and endpoint.get('path_variables'):
            for var in endpoint['path_variables']:
                if isinstance(var, dict):
                    path_var_types[var['name']] = var['type']
        
        # 치환된 값들을 저장할 딕셔너리
        replaced_values = {}
        
        # {id}, {contractIdx} 등의 path variable을 샘플 값으로 변경
        def replace_var(match):
            var_name = match.group(1)
            
            # 자료형 정보가 있으면 자료형 기반으로 샘플 값 생성
            if var_name in path_var_types:
                var_type = path_var_types[var_name]
                sample_value = self.parser._get_sample_value_for_type(var_type, var_name)
                # Path variable은 URL에 들어가므로 문자열로 변환
                str_value = str(sample_value)
                replaced_values[var_name] = sample_value  # 원본 값 저장
                return str_value
            
            # 자료형 정보가 없으면 기존 방식 사용
            var_lower = var_name.lower()
            if 'id' in var_lower or 'idx' in var_lower:
                replaced_values[var_name] = "1"
                return "1"
            elif 'code' in var_lower:
                replaced_values[var_name] = "TEST001"
                return "TEST001"
            elif 'name' in var_lower:
                replaced_values[var_name] = "testname"
                return "testname"
            else:
                replaced_values[var_name] = "test"
                return "test"
        
        new_path = re.sub(r'\{(\w+)\}', replace_var, path)
        return new_path, replaced_values
    
    def _get_pre_request_scripts(self, endpoint: Dict[str, Any]) -> Optional[List[str]]:
        """엔드포인트의 어노테이션을 기반으로 필요한 pre-request 스크립트 목록 반환"""
        if not endpoint:
            return None
        
        annotations = endpoint.get('annotations', [])
        has_auth_header_param = endpoint.get('has_auth_header_param', False)
        pre_request_scripts = []
        
        # @RequestHeader(Authorization) 파라미터가 있는 경우:
        # - 어노테이션별 pre-request는 무시
        # - 하지만 default_auth_library는 추가 (환경 변수 채우기 위해)
        if has_auth_header_param:
            if self.auth_mode == 'all' and self.default_auth_library:
                if self.default_auth_library not in pre_request_scripts:
                    pre_request_scripts.append(self.default_auth_library)
            return pre_request_scripts if pre_request_scripts else None
        
        # 어노테이션별 pre-request 추가
        for annotation in annotations:
            if annotation in self.annotation_pre_request_map:
                script_file = self.annotation_pre_request_map[annotation]
                if script_file not in pre_request_scripts:
                    pre_request_scripts.append(script_file)
        
        # auth_mode=all이고 기본 인증 라이브러리가 설정된 경우
        if self.auth_mode == 'all' and self.default_auth_library:
            # 어노테이션이나 패키지 매핑이 없어서 기본 인증이 적용되는지 확인
            has_annotation_mapping = any(ann in self.annotation_auth_map for ann in annotations)
            package_name = endpoint.get('package', '')
            has_package_mapping = any(package_name.startswith(pkg) for pkg in self.package_auth_map.keys())
            
            # 어노테이션/패키지 매핑이 없으면 기본 인증 라이브러리 추가
            if not has_annotation_mapping and not has_package_mapping:
                if self.default_auth_library not in pre_request_scripts:
                    pre_request_scripts.append(self.default_auth_library)
        
        return pre_request_scripts if pre_request_scripts else None
    
    def _substitute_env_vars(self, text: str) -> str:
        """
        텍스트 내의 {{VAR_NAME}} 패턴을 환경 변수 값으로 치환
        예: "{{USER_ID}}:{{USER_PW}}" -> "kimmo:11qqaa.."
        """
        result = text
        # {{VAR_NAME}} 패턴 찾기
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, text)
        
        for var_name in matches:
            if var_name in self.env_variables:
                # 환경 변수 값으로 치환
                result = result.replace(f"{{{{{var_name}}}}}", self.env_variables[var_name])
            else:
                print(f"⚠️  환경 변수 '{var_name}'을 찾을 수 없습니다.")
        
        return result
    
    def _add_headers(self, step: Dict[str, Any], endpoint: Dict[str, Any] = None) -> None:
        """인증 헤더 및 커스텀 헤더 추가"""
        if 'headers' not in step:
            step['headers'] = {}
        
        # @RequestHeader(Authorization)이 파라미터로 있는지 체크
        has_auth_header_param = endpoint and endpoint.get('has_auth_header_param', False)
        
        # @RequestHeader(Authorization) 파라미터가 있는 경우:
        # - 기존 인증 옵션 맵핑은 무시
        # - 하지만 Authorization 헤더를 환경 변수 참조로 추가
        if has_auth_header_param:
            # 환경 변수에서 authorization 찾기
            auth_var = None
            for var_name in self.env_variables.keys():
                if var_name.lower() == 'authorization':
                    auth_var = var_name
                    break
            
            if auth_var:
                step['headers']['Authorization'] = f"{{{{{auth_var}}}}}"
            else:
                # 환경 변수에 없으면 기본값으로 {{authorization}} 사용
                step['headers']['Authorization'] = "{{authorization}}"
            
            # 커스텀 헤더만 추가하고 리턴
            for key, value in self.custom_headers.items():
                step['headers'][key] = value
            return
        
        should_add_auth = endpoint is None or endpoint.get('requires_auth', False)
        
        # auth_mode=all: 어노테이션별 인증 방식 적용
        if self.auth_mode == 'all' and endpoint:
            endpoint_annotations = endpoint.get('annotations', [])
            
            # 어노테이션별 인증 매핑 확인
            auth_applied = False
            for annotation in endpoint_annotations:
                if annotation in self.annotation_auth_map:
                    auth_info = self.annotation_auth_map[annotation]
                    auth_type = auth_info['type']
                    token = auth_info['token']
                    
                    # has_auth_header_param이 True이면 모든 인증 관련 헤더 추가를 건너뜀
                    if not has_auth_header_param:
                        # Authorization 헤더 추가
                        if auth_type == 'bearer':
                            # Bearer 토큰
                            if '{{' in token and '}}' in token:
                                # 환경 변수 참조
                                step['headers']['Authorization'] = f"Bearer {token}"
                            else:
                                step['headers']['Authorization'] = f"Bearer {token}"
                        elif auth_type == 'basic':
                            # Basic 인증
                            if ':' in token:
                                # {{USER_ID}}:{{USER_PW}} 같은 환경 변수 참조 감지
                                if '{{' in token and '}}' in token:
                                    auth_value = self._substitute_env_vars(token)
                                    encoded = base64.b64encode(auth_value.encode()).decode()
                                else:
                                    encoded = base64.b64encode(token.encode()).decode()
                                step['headers']['Authorization'] = f"Basic {encoded}"
                        
                        # 추가 헤더 적용 (Authorization이 아닌 다른 인증 관련 헤더들)
                        extra_headers = auth_info.get('headers', {})
                        for header_key, header_value in extra_headers.items():
                            # 환경 변수 치환
                            if '{{' in header_value and '}}' in header_value:
                                header_value = self._substitute_env_vars(header_value)
                            step['headers'][header_key] = header_value
                    
                    auth_applied = True
                    break
            
            # 어노테이션 매핑이 없으면 패키지 매핑 확인
            if not auth_applied:
                endpoint_package = endpoint.get('package', '')
                for package_pattern, auth_info in self.package_auth_map.items():
                    # 패키지 경로 매칭 (부분 매칭 지원)
                    if endpoint_package.startswith(package_pattern):
                        auth_type = auth_info['type']
                        token = auth_info['token']
                        
                        # has_auth_header_param이 True이면 모든 인증 관련 헤더 추가를 건너뜀
                        if not has_auth_header_param:
                            # Authorization 헤더 추가
                            if auth_type == 'bearer':
                                # Bearer 토큰
                                if '{{' in token and '}}' in token:
                                    step['headers']['Authorization'] = f"Bearer {token}"
                                else:
                                    step['headers']['Authorization'] = f"Bearer {token}"
                            elif auth_type == 'basic':
                                # Basic 인증
                                if ':' in token:
                                    if '{{' in token and '}}' in token:
                                        auth_value = self._substitute_env_vars(token)
                                        encoded = base64.b64encode(auth_value.encode()).decode()
                                    else:
                                        encoded = base64.b64encode(token.encode()).decode()
                                    step['headers']['Authorization'] = f"Basic {encoded}"
                            
                            # 추가 헤더 적용 (Authorization이 아닌 다른 인증 관련 헤더들)
                            extra_headers = auth_info.get('headers', {})
                            for header_key, header_value in extra_headers.items():
                                # 환경 변수 치환
                                if '{{' in header_value and '}}' in header_value:
                                    header_value = self._substitute_env_vars(header_value)
                                step['headers'][header_key] = header_value
                        
                        auth_applied = True
                        break
            
            # 어노테이션과 패키지 매핑 모두 없으면 기본 인증 적용
            # Authorization 헤더는 has_auth_header_param이 True이면 추가하지 않음
            if not auth_applied and not has_auth_header_param and self.default_auth != 'none' and self.default_auth_token:
                if self.default_auth == 'bearer':
                    step['headers']['Authorization'] = f"Bearer {self.default_auth_token}"
                elif self.default_auth == 'basic':
                    if ':' in self.default_auth_token:
                        if '{{' in self.default_auth_token and '}}' in self.default_auth_token:
                            auth_value = self._substitute_env_vars(self.default_auth_token)
                            encoded = base64.b64encode(auth_value.encode()).decode()
                        else:
                            encoded = base64.b64encode(self.default_auth_token.encode()).decode()
                        step['headers']['Authorization'] = f"Basic {encoded}"
            
            # 커스텀 헤더 추가
            for key, value in self.custom_headers.items():
                step['headers'][key] = value
            return
        
        # 기존 로직 (include/exclude 모드)
        # 환경 변수에서 Bearer 토큰 찾기
        bearer_token_var = None
        for var_name in self.env_variables.keys():
            if 'TOKEN' in var_name.upper() or 'API_KEY' in var_name.upper():
                bearer_token_var = var_name
                break
        
        # 환경 변수에서 Basic 인증 정보 찾기 (명시적으로 BASIC_AUTH만)
        basic_auth_var = None
        for var_name in self.env_variables.keys():
            upper_name = var_name.upper()
            if 'BASIC_AUTH' in upper_name or 'BASIC_TOKEN' in upper_name:
                basic_auth_var = var_name
                break
        
        # Authorization 헤더는 has_auth_header_param이 True이면 추가하지 않음
        if should_add_auth and not has_auth_header_param:
            if bearer_token_var and not self.auth_basic_token:
                # 환경 변수 Bearer 토큰 (Basic 토큰 옵션이 없을 때만)
                step['headers']['Authorization'] = f"Bearer {{{{{bearer_token_var}}}}}"
            elif basic_auth_var:
                # 환경 변수에 직접 Basic 인증 토큰이 있는 경우
                step['headers']['Authorization'] = f"Basic {{{{{basic_auth_var}}}}}"
            elif self.auth_basic_token:
                # 인자로 전달된 Basic 토큰 (Bearer보다 우선)
                # username:password 형식이면 base64 인코딩
                if ':' in self.auth_basic_token and not self.auth_basic_token.startswith('Basic '):
                    # {{USER_ID}}:{{USER_PW}} 같은 환경 변수 참조 감지
                    if '{{' in self.auth_basic_token and '}}' in self.auth_basic_token:
                        # 환경 변수 참조를 YAML에 그대로 저장 (런타임에 치환하도록)
                        # development.json에 미리 Base64 인코딩된 값을 BASIC_AUTH_TOKEN으로 저장
                        # 예: "BASIC_AUTH_TOKEN": "a2ltbW86RUR..."
                        # YAML에는: Authorization: Basic {{BASIC_AUTH_TOKEN}}
                        
                        # 하지만 현재 방식과의 호환성을 위해 시나리오 생성 시 치환
                        auth_value = self._substitute_env_vars(self.auth_basic_token)
                        # 치환된 값으로 Base64 인코딩
                        encoded = base64.b64encode(auth_value.encode()).decode()
                        step['headers']['Authorization'] = f"Basic {encoded}"
                    else:
                        # 일반 username:password 형식
                        encoded = base64.b64encode(self.auth_basic_token.encode()).decode()
                        step['headers']['Authorization'] = f"Basic {encoded}"
                else:
                    # 이미 인코딩되었거나 Basic이 포함된 경우
                    token = self.auth_basic_token.replace('Basic ', '')
                    step['headers']['Authorization'] = f"Basic {token}"
            elif bearer_token_var:
                # 환경 변수 Bearer 토큰 (auth_basic_token이 있었지만 처리됨)
                step['headers']['Authorization'] = f"Bearer {{{{{bearer_token_var}}}}}"
            elif self.auth_bearer_token:
                # 인자로 전달된 Bearer 토큰
                step['headers']['Authorization'] = f"Bearer {self.auth_bearer_token}"
        
        # 커스텀 헤더 추가
        for key, value in self.custom_headers.items():
            step['headers'][key] = value
        
        # 헤더가 비어있으면 제거
        if not step['headers']:
            del step['headers']
        
    def generate(self):
        """시나리오 파일 생성"""
        project_name = self.parser.controller_name.lower()
        project_dir = os.path.join(self.output_dir, project_name)
        scenario_dir = os.path.join(project_dir, 'scenario')
        
        # 환경 파일이 지정되지 않았지만 environment가 있으면 기존 프로젝트에서 찾기
        if self.environment and not self.env_params and not self.env_variables:
            env_file = os.path.join(project_dir, 'env', f'{self.environment}.json')
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        env_data = json.load(f)
                        self.env_params = env_data.get('params', {})
                        self.env_variables = env_data.get('variables', {})
                        print(f"✅ 환경 파일 로드: {env_file}")
                        print(f"   📝 params: {list(self.env_params.keys())}")
                        print(f"   📝 variables: {list(self.env_variables.keys())}")
                except Exception as e:
                    print(f"⚠️  환경 파일 로드 실패: {e}")
        
        # 기존 scenario 폴더가 있으면 백업
        if os.path.exists(scenario_dir):
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_dir = os.path.join(project_dir, f'scenario_{timestamp}')
            
            print(f"\n⚠️  기존 scenario 폴더 발견!")
            print(f"📦 백업 중: scenario → scenario_{timestamp}")
            
            import shutil
            shutil.move(scenario_dir, backup_dir)
            print(f"✅ 백업 완료: {backup_dir}")
        
        # 새로운 폴더 구조 생성
        success_dir = os.path.join(scenario_dir, 'success')
        failure_dir = os.path.join(scenario_dir, 'failure')
        integration_dir = os.path.join(scenario_dir, 'integration')
        load_test_dir = os.path.join(scenario_dir, 'load_test')
        
        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(failure_dir, exist_ok=True)
        os.makedirs(integration_dir, exist_ok=True)
        os.makedirs(load_test_dir, exist_ok=True)
        
        print(f"\n📁 생성 위치: {project_dir}/scenario/")
        print(f"   ├── success/")
        print(f"   ├── failure/")
        print(f"   ├── integration/")
        print(f"   └── load_test/")
        
        # 1. 각 API별 정상/실패 시나리오
        self._generate_success_failure_scenarios(success_dir, failure_dir)
        
        # 2. API 통합 테스트
        self._generate_integration_scenario(integration_dir)
        
        # 3. 성능 및 부하 테스트
        self._generate_load_test_scenarios(load_test_dir)
        
        print(f"\n✅ 시나리오 파일 생성 완료!")
        
        # 전체 파일 개수 계산 (재귀적으로 모든 하위 폴더 포함)
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        
        def count_files_recursive(directory):
            """재귀적으로 특정 확장자 파일 개수 카운트"""
            count = 0
            for root, dirs, files in os.walk(directory):
                count += len([f for f in files if f.endswith(ext)])
            return count
        
        total_files = sum([
            count_files_recursive(success_dir),
            count_files_recursive(failure_dir),
            count_files_recursive(integration_dir),
            count_files_recursive(load_test_dir)
        ])
        print(f"📊 총 {total_files}개 {self.output_format.upper()} 파일 생성")
        
        # 4. TC 문서용 README 생성
        print(f"\n4️⃣  TC 문서 생성 중...")
        self._generate_test_case_documentation(scenario_dir, success_dir, failure_dir, integration_dir, load_test_dir)
        
    def _generate_success_failure_scenarios(self, success_dir: str, failure_dir: str):
        """각 API별 정상/실패 시나리오 생성"""
        print("\n1️⃣  정상/실패 시나리오 생성 중...")
        
        for endpoint in self.parser.endpoints:
            # API별 폴더명
            api_folder_name = endpoint['original_method_name'].lower()
            
            # 정상 시나리오 → success/{api_name}/ 폴더
            success_api_dir = os.path.join(success_dir, api_folder_name)
            os.makedirs(success_api_dir, exist_ok=True)
            
            success_scenario = self._create_success_scenario(endpoint)
            filename = f"{api_folder_name}_success"
            self._write_scenario(os.path.join(success_api_dir, filename), success_scenario, endpoint)
            
            # 실패 시나리오 → failure/{api_name}/ 폴더
            failure_api_dir = os.path.join(failure_dir, api_folder_name)
            os.makedirs(failure_api_dir, exist_ok=True)
            
            failure_scenarios = self._create_failure_scenarios(endpoint)
            for failure_info in failure_scenarios:
                failure_scenario = failure_info['scenario']
                failure_type = failure_info['type']
                status_code = failure_info['status_code']
                
                # 모든 실패 케이스는 failure 폴더에 저장
                filename = f"{api_folder_name}_failure_{failure_type}_{status_code}"
                self._write_scenario(os.path.join(failure_api_dir, filename), failure_scenario, endpoint)
    
    def _build_request_body(self, dto_fields: Dict[str, Any], exclude_fields: List[str] = None) -> Dict[str, Any]:
        """
        요청 본문 생성 (중첩 DTO 구조 포함, 환경 변수 참조)
        
        Args:
            dto_fields: DTO 필드 정보
            exclude_fields: 제외할 필드 목록 (실패 케이스용)
        
        Returns:
            생성된 요청 본문
        """
        exclude_fields = exclude_fields or []
        body = {}
        
        for field_name, field_info in dto_fields.items():
            if field_name in exclude_fields:
                continue
            
            # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
            if field_name in self.env_params:
                body[field_name] = f"{{{{{field_name}}}}}"
            else:
                body[field_name] = field_info['sample_value']
        
        return body
    
    def _create_success_scenario(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """정상 시나리오 생성"""
        # Path variable을 샘플 값으로 치환 (자료형 기반)
        path, path_var_values = self._replace_path_variables(endpoint['path'], endpoint)
        
        step = {
            "name": f"{endpoint['name']} - Success Case",
            "method": endpoint['method'],
            "path": path
        }
        
        # Path variable 값들을 step에 저장 (TSV 생성 시 사용)
        if path_var_values:
            step['path_var_values'] = path_var_values
        
        # 요청 본문 (DTO 필드 기반 - 중첩 DTO 구조 포함)
        if endpoint['dto_fields']:
            step['body'] = self._build_request_body(endpoint['dto_fields'])
        
        # Query 파라미터 (일반 RequestParam)
        query_params = {}
        if endpoint['query_params']:
            for param in endpoint['query_params']:
                param_name = param['name'] if isinstance(param, dict) else param
                param_type = param['type'] if isinstance(param, dict) else 'String'
                # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                if param_name in self.env_params:
                    query_params[param_name] = f"{{{{{param_name}}}}}"
                else:
                    query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
        
        # 동적 파라미터 처리 (@RequestParam Map<String, String> parameters)
        if endpoint.get('dynamic_params'):
            variable_name = endpoint['dynamic_params']['variable_name']
            # env_params에서 해당 변수명으로 값 찾기
            if variable_name in self.env_params:
                # "grant_type=client_credentials,test=abc" 형태를 파싱
                param_string = self.env_params[variable_name]
                # & 또는 , 로 분리된 key=value 파싱
                for pair in re.split(r'[&,]', param_string):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        # 각 value를 환경변수 참조 형태로 (실제 값도 같이)
                        query_params[key.strip()] = value.strip()
        
        # ModelAttribute 필드를 query parameter로 추가 (GET 요청)
        if endpoint.get('model_attribute_fields'):
            for field_name, field_info in endpoint['model_attribute_fields'].items():
                # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                if field_name in self.env_params:
                    query_params[field_name] = f"{{{{{field_name}}}}}"
                else:
                    query_params[field_name] = field_info['sample_value']
        
        if query_params:
            step['query_params'] = query_params
        
        # Assertions
        step['assertions'] = self._generate_success_assertions(endpoint)
        
        # 변수 추출 (POST의 경우)
        if endpoint['method'] == 'POST':
            step['extract'] = {"created_id": "body.id"}
        
        # Bearer 토큰 헤더 추가
        self._add_headers(step, endpoint)
        
        scenario = {
            "name": f"{endpoint['name']} - Success Test",
            "description": f"정상 케이스: {endpoint['method']} {endpoint['path']}",
            "host": "default",
            "tags": ["success", self.parser.controller_name.lower(), endpoint['method'].lower()],
            "continue_on_error": self.continue_on_error,
            "steps": [step]
        }
        
        if self.environment:
            scenario["environment"] = self.environment
        
        # Pre-request 스크립트 추가
        pre_request_scripts = self._get_pre_request_scripts(endpoint)
        if pre_request_scripts:
            scenario["pre_request_scripts"] = pre_request_scripts
        
        return scenario
    
    def _create_failure_scenarios(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """실패 시나리오 생성 - 모든 파라미터 오류 경우의 수 분석"""
        scenarios = []
        
        # Path variable 치환 (자료형 기반)
        path, path_var_values = self._replace_path_variables(endpoint['path'], endpoint)
        
        # 1. 권한 오류 시나리오 (401) - 인증이 필요한 API에 대해
        if endpoint.get('requires_auth', False):
            step = {
                "name": f"{endpoint['name']} - Unauthorized",
                "method": endpoint['method'],
                "path": path,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 401}
                ]
            }
            
            # Path variable 값들을 step에 저장
            if path_var_values:
                step['path_var_values'] = path_var_values
            
            # 요청 본문이 있으면 추가 (중첩 DTO 구조 포함)
            if endpoint['dto_fields']:
                step['body'] = self._build_request_body(endpoint['dto_fields'])
            
            # Query 파라미터 추가 (일반 RequestParam)
            query_params = {}
            if endpoint['query_params']:
                for param in endpoint['query_params']:
                    param_name = param['name'] if isinstance(param, dict) else param
                    param_type = param['type'] if isinstance(param, dict) else 'String'
                    # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                    if param_name in self.env_params:
                        query_params[param_name] = f"{{{{{param_name}}}}}"
                    else:
                        query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
            
            # 동적 파라미터 처리 (@RequestParam Map<String, String> parameters)
            if endpoint.get('dynamic_params'):
                variable_name = endpoint['dynamic_params']['variable_name']
                # env_params에서 해당 변수명으로 값 찾기
                if variable_name in self.env_params:
                    # "grant_type=client_credentials,test=abc" 형태를 파싱
                    param_string = self.env_params[variable_name]
                    # & 또는 , 로 분리된 key=value 파싱
                    for pair in re.split(r'[&,]', param_string):
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            # 각 value를 환경변수 참조 형태로 (실제 값도 같이)
                            query_params[key.strip()] = value.strip()
            
            # ModelAttribute 필드를 query parameter로 추가 (GET 요청)
            if endpoint.get('model_attribute_fields'):
                for field_name, field_info in endpoint['model_attribute_fields'].items():
                    # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                    if field_name in self.env_params:
                        query_params[field_name] = f"{{{{{field_name}}}}}"
                    else:
                        query_params[field_name] = field_info['sample_value']
            
            if query_params:
                step['query_params'] = query_params
            
            # 헤더는 추가하지 않음 (인증 정보 없이 요청)
            
            scenario = {
                "name": f"{endpoint['name']} - Unauthorized Access",
                "description": f"실패 케이스 (401): 인증 정보 없이 접근",
                "host": "default",
                "tags": ["failure", "unauthorized", "401", self.parser.controller_name.lower()],
                "continue_on_error": self.continue_on_error,
                "steps": [step]
            }
            
            if self.environment:
                scenario["environment"] = self.environment
            
            scenarios.append({
                'scenario': scenario,
                'type': 'unauthorized',
                'status_code': 401
            })
        
        # 2. 필수 필드 누락 (400)
        
        # 2-0. GET 요청의 ModelAttribute 필수 필드 누락 (Query Parameter)
        if endpoint['method'] == 'GET' and endpoint.get('model_attribute_fields'):
            required_fields = [
                name for name, info in endpoint['model_attribute_fields'].items() 
                if info.get('required')
            ]
            
            for field_name in required_fields:
                # 필수 query parameter를 제외하고 생성
                query_params = {}
                for qp_name, qp_info in endpoint['model_attribute_fields'].items():
                    if qp_name != field_name:
                        if qp_name in self.env_params:
                            query_params[qp_name] = f"{{{{{qp_name}}}}}"
                        else:
                            query_params[qp_name] = qp_info['sample_value']
                
                step = {
                    "name": f"{endpoint['name']} - Missing {field_name}",
                    "method": endpoint['method'],
                    "path": path,
                    "query_params": query_params,
                    "assertions": [
                        {"field": "status", "operator": "eq", "value": 400}
                    ]
                }
                
                # Path variable 값들을 step에 저장
                if path_var_values:
                    step['path_var_values'] = path_var_values
                
                self._add_headers(step, endpoint)
                
                scenario = {
                    "name": f"{endpoint['name']} - Missing Required Query Parameter ({field_name})",
                    "description": f"실패 케이스 (400): 필수 Query Parameter({field_name}) 누락",
                    "host": "default",
                    "tags": ["failure", "validation", "400", "missing_query_param", self.parser.controller_name.lower()],
                    "continue_on_error": self.continue_on_error,
                    "steps": [step]
                }
                
                if self.environment:
                    scenario["environment"] = self.environment
                
                pre_request_scripts = self._get_pre_request_scripts(endpoint)
                if pre_request_scripts:
                    scenario["pre_request_scripts"] = pre_request_scripts
                
                scenarios.append({
                    'scenario': scenario,
                    'type': f'missing_{field_name}',
                    'status_code': 400
                })
        
        # 2-1. POST, PUT, PATCH의 Request Body 필수 필드 누락
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            # 최상위 레벨 필수 필드 누락
            required_fields = [
                name for name, info in endpoint['dto_fields'].items() 
                if info.get('required')
            ]
            
            for field_name in required_fields:
                # 필수 필드를 제외한 body 생성 (중첩 DTO 구조 포함)
                body = self._build_request_body(endpoint['dto_fields'], exclude_fields=[field_name])
                
                step = {
                    "name": f"{endpoint['name']} - Missing {field_name}",
                    "method": endpoint['method'],
                    "path": path,
                    "body": body,
                    "assertions": [
                        {"field": "status", "operator": "eq", "value": 400}
                    ]
                }
                
                # Path variable 값들을 step에 저장
                if path_var_values:
                    step['path_var_values'] = path_var_values
                
                self._add_headers(step, endpoint)
                
                scenario = {
                    "name": f"{endpoint['name']} - Missing Required Field ({field_name})",
                    "description": f"실패 케이스 (400): 필수 필드({field_name}) 누락",
                    "host": "default",
                    "tags": ["failure", "validation", "400", "missing_field", self.parser.controller_name.lower()],
                    "continue_on_error": self.continue_on_error,
                    "steps": [step]
                }
                
                if self.environment:
                    scenario["environment"] = self.environment
                
                pre_request_scripts = self._get_pre_request_scripts(endpoint)
                if pre_request_scripts:
                    scenario["pre_request_scripts"] = pre_request_scripts
                
                scenarios.append({
                    'scenario': scenario,
                    'type': f'missing_{field_name}',
                    'status_code': 400
                })
            
            # 2-2. 중첩 DTO 내부의 필수 필드 누락
            for parent_field_name, parent_field_info in endpoint['dto_fields'].items():
                nested_fields = parent_field_info.get('nested_fields')
                if not nested_fields:
                    continue
                
                # 중첩 DTO의 필수 필드 찾기
                nested_required_fields = [
                    name for name, info in nested_fields.items()
                    if info.get('required')
                ]
                
                for nested_field_name in nested_required_fields:
                    # 정상 body 생성 (매번 새로운 객체 생성 - deep copy 필요)
                    body = copy.deepcopy(self._build_request_body(endpoint['dto_fields']))
                    
                    # 중첩 필드에서 해당 필수 필드만 제거
                    if parent_field_name in body:
                        parent_value = body[parent_field_name]
                        
                        # List인 경우
                        if isinstance(parent_value, list) and len(parent_value) > 0:
                            for item in parent_value:
                                if isinstance(item, dict) and nested_field_name in item:
                                    del item[nested_field_name]
                        
                        # Dict인 경우
                        elif isinstance(parent_value, dict) and nested_field_name in parent_value:
                            del parent_value[nested_field_name]
                    
                    step = {
                        "name": f"{endpoint['name']} - Missing {parent_field_name}.{nested_field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Missing Nested Field ({parent_field_name}.{nested_field_name})",
                        "description": f"실패 케이스 (400): 중첩 필수 필드({parent_field_name}.{nested_field_name}) 누락",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "missing_nested_field", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step]
                    }
                    
                    if self.environment:
                        scenario["environment"] = self.environment
                    
                    pre_request_scripts = self._get_pre_request_scripts(endpoint)
                    if pre_request_scripts:
                        scenario["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario,
                        'type': f'missing_{parent_field_name}_{nested_field_name}',
                        'status_code': 400
                    })
            
            # 2-3. 리스트/컬렉션 필드 검증 (빈 리스트, null) - 필수 어노테이션이 있는 경우만
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                nested_fields = field_info.get('nested_fields')
                is_required = field_info.get('required', False)
                
                # List, Set 등의 컬렉션 타입이고 중첩 필드가 있으며, 필수 필드인 경우만
                if nested_fields and is_required and any(collection in field_type for collection in ['List<', 'Set<', 'Collection<']):
                    
                    # 케이스 1: 빈 리스트
                    body_empty = copy.deepcopy(self._build_request_body(endpoint['dto_fields']))
                    body_empty[field_name] = []
                    
                    step_empty = {
                        "name": f"{endpoint['name']} - Empty {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_empty,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step_empty, endpoint)
                    
                    scenario_empty = {
                        "name": f"{endpoint['name']} - Empty Collection Field ({field_name})",
                        "description": f"실패 케이스 (400): 컬렉션 필드({field_name})가 비어있음",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "empty_collection", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step_empty]
                    }
                    
                    if self.environment:
                        scenario_empty["environment"] = self.environment
                    
                    pre_request_scripts = self._get_pre_request_scripts(endpoint)
                    if pre_request_scripts:
                        scenario_empty["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario_empty,
                        'type': f'empty_{field_name}',
                        'status_code': 400
                    })
                    
                    # 케이스 2: null (필드 제거)
                    body_null = self._build_request_body(endpoint['dto_fields'], exclude_fields=[field_name])
                    
                    step_null = {
                        "name": f"{endpoint['name']} - Null {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_null,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step_null, endpoint)
                    
                    scenario_null = {
                        "name": f"{endpoint['name']} - Null Collection Field ({field_name})",
                        "description": f"실패 케이스 (400): 컬렉션 필드({field_name})가 null",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "null_collection", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step_null]
                    }
                    
                    if self.environment:
                        scenario_null["environment"] = self.environment
                    
                    if pre_request_scripts:
                        scenario_null["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario_null,
                        'type': f'null_{field_name}',
                        'status_code': 400
                    })
        
        # 3. 잘못된 필드 타입/포맷 (400) - POST, PUT, PATCH (validation 어노테이션이 있는 필드만)
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            # 각 필드의 타입과 포맷에 맞는 잘못된 값 생성
            for field_name, field_info in endpoint['dto_fields'].items():
                # validation 어노테이션이 있는 필드만 테스트
                has_validation = (
                    field_info.get('required') or
                    field_info.get('pattern') or
                    field_info.get('min') is not None or
                    field_info.get('max') is not None or
                    field_info.get('min_length') is not None or
                    field_info.get('max_length') is not None or
                    field_info.get('custom_format')
                )
                
                if not has_validation:
                    continue  # validation이 없는 필드는 스킵
                
                field_type = field_info.get('type', '')
                custom_format = field_info.get('custom_format')
                invalid_value = None
                error_desc = ""
                
                # 커스텀 포맷 체크
                if custom_format == 'LocalTime':
                    invalid_value = "25:99:99"  # 잘못된 시간 형식
                    error_desc = "시간 형식이어야 함(HH:mm:ss)"
                elif custom_format == 'LocalDate':
                    invalid_value = "2024-13-99"  # 잘못된 날짜
                    error_desc = "날짜 형식이어야 함(yyyy-MM-dd)"
                elif custom_format == 'LocalDateTime':
                    invalid_value = "2024-13-99T25:99:99"  # 잘못된 날짜시간
                    error_desc = "날짜시간 형식이어야 함(yyyy-MM-ddTHH:mm:ss)"
                elif custom_format == 'DayBitFlag':
                    invalid_value = "invalid_number"  # 숫자가 아님
                    error_desc = "숫자여야 함(요일 비트플래그)"
                elif custom_format == 'Email':
                    invalid_value = "invalid-email"  # 잘못된 이메일
                    error_desc = "이메일 형식이어야 함"
                # 일반 타입 체크
                elif field_type in ['int', 'Integer', 'long', 'Long']:
                    invalid_value = "invalid_number"
                    error_desc = "정수 타입이어야 함"
                elif field_type in ['double', 'Double', 'float', 'Float']:
                    invalid_value = "invalid_number"
                    error_desc = "실수 타입이어야 함"
                elif field_type in ['boolean', 'Boolean']:
                    invalid_value = "invalid_boolean"
                    error_desc = "boolean 타입이어야 함"
                # String 타입에서 특정 필드명 기반 체크
                elif field_type == 'String':
                    field_lower = field_name.lower()
                    if 'time' in field_lower and ('start' in field_lower or 'end' in field_lower):
                        invalid_value = "25:99:99"
                        error_desc = "시간 형식이어야 함(HH:mm:ss)"
                    elif 'date' in field_lower:
                        invalid_value = "2024-13-99"
                        error_desc = "날짜 형식이어야 함"
                    elif 'color' in field_lower:
                        invalid_value = "invalid_color_code"
                        error_desc = "색상 코드 형식이어야 함"
                    elif 'email' in field_lower:
                        invalid_value = "invalid-email"
                        error_desc = "이메일 형식이어야 함"
                
                # 잘못된 값이 있으면 시나리오 생성
                if invalid_value:
                    # 정상 body 먼저 생성 (중첩 DTO 구조 포함)
                    body = self._build_request_body(endpoint['dto_fields'])
                    # 해당 필드만 잘못된 값으로 덮어쓰기
                    body[field_name] = invalid_value
                    
                    step = {
                        "name": f"{endpoint['name']} - Invalid Format for {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Invalid Field Format ({field_name})",
                        "description": f"실패 케이스 (400): 잘못된 필드 형식({field_name}은 {error_desc})",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "invalid_format", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step]
                    }
                    
                    if self.environment:
                        scenario["environment"] = self.environment
                    
                    pre_request_scripts = self._get_pre_request_scripts(endpoint)
                    if pre_request_scripts:
                        scenario["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario,
                        'type': f'invalid_format_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 4. 경계값 테스트 (400) - min/max validation
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # 숫자 타입에서 max 경계값 테스트 (실패 케이스: max+1만 생성)
                if field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'String'] and field_info.get('max'):
                    max_value = field_info['max']
                    
                    # 경계값 실패 케이스: max + 1
                    body_fail = self._build_request_body(endpoint['dto_fields'])
                    # String 타입인 경우 문자열로 변환
                    body_fail[field_name] = str(max_value + 1) if field_type == 'String' else (max_value + 1)
                    
                    step_fail = {
                        "name": f"{endpoint['name']} - Boundary Max Exceeded ({field_name})",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_fail,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_fail['path_var_values'] = path_var_values
                    
                    self._add_headers(step_fail, endpoint)
                    
                    scenario_fail = {
                        "name": f"{endpoint['name']} - Boundary Failure (Max+1)",
                        "description": f"경계값 실패 케이스 (400): {field_name} = {max_value + 1} (최대값+1 초과)",
                        "host": "default",
                        "tags": ["failure", "boundary", "validation", "400", "max_exceeded", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step_fail]
                    }
                    
                    if self.environment:
                        scenario_fail["environment"] = self.environment
                    
                    if pre_request_scripts:
                        scenario_fail["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario_fail,
                        'type': f'boundary_max_exceeded_{field_name}',
                        'status_code': 400
                    })
                
                # 숫자 타입에서 min 경계값 테스트 (실패 케이스: min-1만 생성)
                if field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'String'] and field_info.get('min') is not None:
                    min_value = field_info['min']
                    
                    # 경계값 실패 케이스: min - 1
                    body_fail = self._build_request_body(endpoint['dto_fields'])
                    # String 타입인 경우 문자열로 변환
                    body_fail[field_name] = str(min_value - 1) if field_type == 'String' else (min_value - 1)
                    
                    step_fail = {
                        "name": f"{endpoint['name']} - Boundary Min Not Met ({field_name})",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_fail,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_fail['path_var_values'] = path_var_values
                    
                    self._add_headers(step_fail, endpoint)
                    
                    scenario_fail = {
                        "name": f"{endpoint['name']} - Boundary Failure (Min-1)",
                        "description": f"경계값 실패 케이스 (400): {field_name} = {min_value - 1} (최소값-1 미만)",
                        "host": "default",
                        "tags": ["failure", "boundary", "validation", "400", "min_not_met", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step_fail]
                    }
                    
                    if self.environment:
                        scenario_fail["environment"] = self.environment
                    
                    if pre_request_scripts:
                        scenario_fail["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario_fail,
                        'type': f'boundary_min_not_met_{field_name}',
                        'status_code': 400
                    })
                
                # 문자열 길이 초과
                if field_type == 'String' and field_info.get('max_length'):
                    body = {}
                    for name, info in endpoint['dto_fields'].items():
                        if name == field_name:
                            body[name] = "x" * (field_info['max_length'] + 10)  # 길이 초과
                        else:
                            body[name] = info['sample_value']
                    
                    step = {
                        "name": f"{endpoint['name']} - Max Length Exceeded for {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Max Length Exceeded ({field_name})",
                        "description": f"실패 케이스 (400): 최대 길이 초과({field_name} > {field_info['max_length']}자)",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "max_length_exceeded", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step]
                    }
                    
                    if self.environment:
                        scenario["environment"] = self.environment
                    
                    pre_request_scripts = self._get_pre_request_scripts(endpoint)
                    if pre_request_scripts:
                        scenario["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario,
                        'type': f'max_length_exceeded_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 4-1. @DecimalMin, @DecimalMax 경계값 테스트 (String 값)
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # @DecimalMax - 최대값 초과 테스트
                if field_info.get('decimal_max') and field_type in ['BigDecimal', 'BigInteger', 'String', 'int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short']:
                    decimal_max_value = field_info['decimal_max']
                    is_inclusive = field_info.get('decimal_max_inclusive', True)
                    
                    try:
                        from decimal import Decimal
                        max_decimal = Decimal(decimal_max_value)
                        
                        # 실패 케이스: max 초과
                        body_fail = self._build_request_body(endpoint['dto_fields'])
                        exceeded_value = max_decimal + Decimal('0.01')
                        body_fail[field_name] = str(exceeded_value) if field_type == 'String' else float(exceeded_value)
                        
                        step_fail = {
                            "name": f"{endpoint['name']} - DecimalMax Exceeded",
                            "method": endpoint['method'],
                            "path": path,
                            "body": body_fail,
                            "assertions": [
                                {"field": "status", "operator": "eq", "value": 400}
                            ]
                        }
                        
                        if path_var_values:
                            step_fail['path_var_values'] = path_var_values
                        
                        self._add_headers(step_fail, endpoint)
                        
                        scenarios.append({
                            'scenario': {
                                "name": f"{endpoint['name']} - @DecimalMax Exceeded",
                                "description": f"경계값 실패 케이스 (400): {field_name} > {decimal_max_value} (최대값 초과)",
                                "host": "default",
                                "tags": ["failure", "boundary", "validation", "400", "decimal_max_exceeded", self.parser.controller_name.lower()],
                                "continue_on_error": self.continue_on_error,
                                "steps": [step_fail],
                                "environment": self.environment if self.environment else None,
                                "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                            },
                            'type': f'decimal_max_exceeded_{field_name}',
                            'status_code': 400
                        })
                    except:
                        pass  # 변환 실패 시 스킵
                
                # @DecimalMin - 최소값 미만 테스트
                if field_info.get('decimal_min') and field_type in ['BigDecimal', 'BigInteger', 'String', 'int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short']:
                    decimal_min_value = field_info['decimal_min']
                    is_inclusive = field_info.get('decimal_min_inclusive', True)
                    
                    try:
                        from decimal import Decimal
                        min_decimal = Decimal(decimal_min_value)
                        
                        # 실패 케이스: min 미만
                        body_fail = self._build_request_body(endpoint['dto_fields'])
                        below_value = min_decimal - Decimal('0.01')
                        body_fail[field_name] = str(below_value) if field_type == 'String' else float(below_value)
                        
                        step_fail = {
                            "name": f"{endpoint['name']} - DecimalMin Not Met",
                            "method": endpoint['method'],
                            "path": path,
                            "body": body_fail,
                            "assertions": [
                                {"field": "status", "operator": "eq", "value": 400}
                            ]
                        }
                        
                        if path_var_values:
                            step_fail['path_var_values'] = path_var_values
                        
                        self._add_headers(step_fail, endpoint)
                        
                        scenarios.append({
                            'scenario': {
                                "name": f"{endpoint['name']} - @DecimalMin Not Met",
                                "description": f"경계값 실패 케이스 (400): {field_name} < {decimal_min_value} (최소값 미만)",
                                "host": "default",
                                "tags": ["failure", "boundary", "validation", "400", "decimal_min_not_met", self.parser.controller_name.lower()],
                                "continue_on_error": self.continue_on_error,
                                "steps": [step_fail],
                                "environment": self.environment if self.environment else None,
                                "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                            },
                            'type': f'decimal_min_not_met_{field_name}',
                            'status_code': 400
                        })
                    except:
                        pass  # 변환 실패 시 스킵
        
        # 4-2. @Positive, @PositiveOrZero 검증
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # @Positive - 0과 음수 실패
                if field_info.get('positive') and field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'float', 'Float', 'double', 'Double', 'BigDecimal', 'BigInteger']:
                    # 실패 케이스 1: 0 (0은 실패)
                    body_zero = self._build_request_body(endpoint['dto_fields'])
                    body_zero[field_name] = 0
                    
                    step_zero = {
                        "name": f"{endpoint['name']} - Positive Constraint Failed (Zero)",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_zero,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_zero['path_var_values'] = path_var_values
                    
                    self._add_headers(step_zero, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Positive Failed (Zero)",
                            "description": f"실패 케이스 (400): @Positive 제약 위반 ({field_name} = 0, 양수여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "positive_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_zero],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'positive_zero_{field_name}',
                        'status_code': 400
                    })
                    
                    # 실패 케이스 2: 음수
                    body_negative = self._build_request_body(endpoint['dto_fields'])
                    body_negative[field_name] = -1
                    
                    step_negative = {
                        "name": f"{endpoint['name']} - Positive Constraint Failed (Negative)",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_negative,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_negative['path_var_values'] = path_var_values
                    
                    self._add_headers(step_negative, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Positive Failed (Negative)",
                            "description": f"실패 케이스 (400): @Positive 제약 위반 ({field_name} = -1, 양수여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "positive_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_negative],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'positive_negative_{field_name}',
                        'status_code': 400
                    })
                
                # @PositiveOrZero - 음수만 실패
                if field_info.get('positive_or_zero') and field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'float', 'Float', 'double', 'Double', 'BigDecimal', 'BigInteger']:
                    body_negative = self._build_request_body(endpoint['dto_fields'])
                    body_negative[field_name] = -1
                    
                    step_negative = {
                        "name": f"{endpoint['name']} - PositiveOrZero Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_negative,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_negative['path_var_values'] = path_var_values
                    
                    self._add_headers(step_negative, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @PositiveOrZero Failed",
                            "description": f"실패 케이스 (400): @PositiveOrZero 제약 위반 ({field_name} = -1, 0 이상이어야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "positive_or_zero_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_negative],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'positive_or_zero_negative_{field_name}',
                        'status_code': 400
                    })
                
                # @Negative - 0과 양수 실패
                if field_info.get('negative') and field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'float', 'Float', 'double', 'Double', 'BigDecimal', 'BigInteger']:
                    # 실패 케이스 1: 0
                    body_zero = self._build_request_body(endpoint['dto_fields'])
                    body_zero[field_name] = 0
                    
                    step_zero = {
                        "name": f"{endpoint['name']} - Negative Constraint Failed (Zero)",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_zero,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_zero['path_var_values'] = path_var_values
                    
                    self._add_headers(step_zero, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Negative Failed (Zero)",
                            "description": f"실패 케이스 (400): @Negative 제약 위반 ({field_name} = 0, 음수여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "negative_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_zero],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'negative_zero_{field_name}',
                        'status_code': 400
                    })
                    
                    # 실패 케이스 2: 양수
                    body_positive = self._build_request_body(endpoint['dto_fields'])
                    body_positive[field_name] = 1
                    
                    step_positive = {
                        "name": f"{endpoint['name']} - Negative Constraint Failed (Positive)",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_positive,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_positive['path_var_values'] = path_var_values
                    
                    self._add_headers(step_positive, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Negative Failed (Positive)",
                            "description": f"실패 케이스 (400): @Negative 제약 위반 ({field_name} = 1, 음수여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "negative_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_positive],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'negative_positive_{field_name}',
                        'status_code': 400
                    })
                
                # @NegativeOrZero - 양수만 실패
                if field_info.get('negative_or_zero') and field_type in ['int', 'Integer', 'long', 'Long', 'byte', 'Byte', 'short', 'Short', 'float', 'Float', 'double', 'Double', 'BigDecimal', 'BigInteger']:
                    body_positive = self._build_request_body(endpoint['dto_fields'])
                    body_positive[field_name] = 1
                    
                    step_positive = {
                        "name": f"{endpoint['name']} - NegativeOrZero Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_positive,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_positive['path_var_values'] = path_var_values
                    
                    self._add_headers(step_positive, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @NegativeOrZero Failed",
                            "description": f"실패 케이스 (400): @NegativeOrZero 제약 위반 ({field_name} = 1, 0 이하여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "negative_or_zero_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_positive],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'negative_or_zero_positive_{field_name}',
                        'status_code': 400
                    })
        
        # 4-3. @Digits 검증 - 자릿수 초과
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                if field_info.get('digits_integer') is not None and field_info.get('digits_fraction') is not None:
                    integer_digits = field_info['digits_integer']
                    fraction_digits = field_info['digits_fraction']
                    
                    # 정수 자릿수 초과 테스트
                    body_integer_exceeded = self._build_request_body(endpoint['dto_fields'])
                    # 정수 자릿수 +1 생성 (예: integer=3이면 1000)
                    invalid_integer = "9" * (integer_digits + 1) + "." + "0" * fraction_digits
                    body_integer_exceeded[field_name] = invalid_integer
                    
                    step_integer = {
                        "name": f"{endpoint['name']} - Digits Integer Exceeded",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_integer_exceeded,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_integer['path_var_values'] = path_var_values
                    
                    self._add_headers(step_integer, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Digits Integer Exceeded",
                            "description": f"실패 케이스 (400): @Digits 정수 자릿수 초과 ({field_name}, 최대 {integer_digits}자리)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "digits_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_integer],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'digits_integer_exceeded_{field_name}',
                        'status_code': 400
                    })
                    
                    # 소수 자릿수 초과 테스트
                    body_fraction_exceeded = self._build_request_body(endpoint['dto_fields'])
                    invalid_fraction = "9" * integer_digits + "." + "9" * (fraction_digits + 1)
                    body_fraction_exceeded[field_name] = invalid_fraction
                    
                    step_fraction = {
                        "name": f"{endpoint['name']} - Digits Fraction Exceeded",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_fraction_exceeded,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_fraction['path_var_values'] = path_var_values
                    
                    self._add_headers(step_fraction, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Digits Fraction Exceeded",
                            "description": f"실패 케이스 (400): @Digits 소수 자릿수 초과 ({field_name}, 최대 {fraction_digits}자리)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "digits_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_fraction],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'digits_fraction_exceeded_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 4-4. @AssertTrue, @AssertFalse 검증
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # @AssertTrue - false일 때 실패
                if field_info.get('assert_true') and field_type in ['boolean', 'Boolean']:
                    body_false = self._build_request_body(endpoint['dto_fields'])
                    body_false[field_name] = False
                    
                    step_false = {
                        "name": f"{endpoint['name']} - AssertTrue Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_false,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_false['path_var_values'] = path_var_values
                    
                    self._add_headers(step_false, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @AssertTrue Failed",
                            "description": f"실패 케이스 (400): @AssertTrue 제약 위반 ({field_name} = false, true여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "assert_true_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_false],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'assert_true_failed_{field_name}',
                        'status_code': 400
                    })
                
                # @AssertFalse - true일 때 실패
                if field_info.get('assert_false') and field_type in ['boolean', 'Boolean']:
                    body_true = self._build_request_body(endpoint['dto_fields'])
                    body_true[field_name] = True
                    
                    step_true = {
                        "name": f"{endpoint['name']} - AssertFalse Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_true,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_true['path_var_values'] = path_var_values
                    
                    self._add_headers(step_true, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @AssertFalse Failed",
                            "description": f"실패 케이스 (400): @AssertFalse 제약 위반 ({field_name} = true, false여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "assert_false_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_true],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'assert_false_failed_{field_name}',
                        'status_code': 400
                    })
        
        # 5. 패턴 불일치 (400) - Pattern validation
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_pattern = field_info.get('pattern')
                custom_format = field_info.get('custom_format')
                
                # 패턴이 있거나 커스텀 포맷이 있는 경우
                if field_pattern or custom_format:
                    invalid_value = "INVALID_PATTERN_@@##"
                    pattern_desc = "정규식 패턴"
                    
                    # 필드명 기반 더 구체적인 잘못된 값 생성
                    field_lower = field_name.lower()
                    if custom_format == 'Email' or 'email' in field_lower:
                        invalid_value = "invalid.email.format"
                        pattern_desc = "이메일 형식"
                    elif 'phone' in field_lower or 'tel' in field_lower:
                        invalid_value = "123-456"
                        pattern_desc = "전화번호 형식"
                    elif 'url' in field_lower:
                        invalid_value = "not-a-valid-url"
                        pattern_desc = "URL 형식"
                    elif 'color' in field_lower:
                        invalid_value = "GGGGGG"
                        pattern_desc = "색상 코드 형식"
                    elif custom_format == 'LocalTime' or ('time' in field_lower and field_info.get('type') == 'String'):
                        invalid_value = "99:99:99"
                        pattern_desc = "시간 형식(HH:mm:ss)"
                    elif custom_format == 'LocalDate' or ('date' in field_lower and field_info.get('type') == 'String'):
                        invalid_value = "9999-99-99"
                        pattern_desc = "날짜 형식(yyyy-MM-dd)"
                    
                    body = {}
                    for name, info in endpoint['dto_fields'].items():
                        if name == field_name:
                            body[name] = invalid_value
                        else:
                            body[name] = info['sample_value']
                    
                    step = {
                        "name": f"{endpoint['name']} - Pattern Mismatch for {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Pattern Mismatch ({field_name})",
                        "description": f"실패 케이스 (400): 패턴 불일치({field_name}이 {pattern_desc}와 불일치)",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "pattern_mismatch", self.parser.controller_name.lower()],
                        "continue_on_error": self.continue_on_error,
                        "steps": [step]
                    }
                    
                    if self.environment:
                        scenario["environment"] = self.environment
                    
                    pre_request_scripts = self._get_pre_request_scripts(endpoint)
                    if pre_request_scripts:
                        scenario["pre_request_scripts"] = pre_request_scripts
                    
                    scenarios.append({
                        'scenario': scenario,
                        'type': f'pattern_mismatch_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 5-2. @Email 검증
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                if field_info.get('email'):
                    # 잘못된 이메일 형식
                    body_invalid = self._build_request_body(endpoint['dto_fields'])
                    body_invalid[field_name] = "invalid-email-format"
                    
                    step_invalid = {
                        "name": f"{endpoint['name']} - Email Format Invalid",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_invalid,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_invalid['path_var_values'] = path_var_values
                    
                    self._add_headers(step_invalid, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Email Invalid Format",
                            "description": f"실패 케이스 (400): @Email 형식 오류 ({field_name}, 이메일 형식이어야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "email_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_invalid],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'email_invalid_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 5-3. @Future, @Past 날짜/시간 검증
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # @Future - 과거 날짜로 테스트 (실패해야 함)
                if field_info.get('future') and field_type in ['LocalDate', 'LocalDateTime', 'Date', 'Instant']:
                    body_past = self._build_request_body(endpoint['dto_fields'])
                    body_past[field_name] = "2020-01-01" if 'Date' in field_type else "2020-01-01T00:00:00"
                    
                    step_past = {
                        "name": f"{endpoint['name']} - Future Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_past,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_past['path_var_values'] = path_var_values
                    
                    self._add_headers(step_past, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Future Failed",
                            "description": f"실패 케이스 (400): @Future 제약 위반 ({field_name}, 미래 날짜여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "future_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_past],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'future_failed_{field_name}',
                        'status_code': 400
                    })
                
                # @Past - 미래 날짜로 테스트 (실패해야 함)
                if field_info.get('past') and field_type in ['LocalDate', 'LocalDateTime', 'Date', 'Instant']:
                    body_future = self._build_request_body(endpoint['dto_fields'])
                    body_future[field_name] = "2099-12-31" if 'Date' in field_type else "2099-12-31T23:59:59"
                    
                    step_future = {
                        "name": f"{endpoint['name']} - Past Constraint Failed",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_future,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_future['path_var_values'] = path_var_values
                    
                    self._add_headers(step_future, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @Past Failed",
                            "description": f"실패 케이스 (400): @Past 제약 위반 ({field_name}, 과거 날짜여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "past_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_future],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'past_failed_{field_name}',
                        'status_code': 400
                    })
        
        # 5-4. @URL 검증 (Hibernate Validator)
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                if field_info.get('url'):
                    # 잘못된 URL 형식
                    body_invalid = self._build_request_body(endpoint['dto_fields'])
                    body_invalid[field_name] = "not-a-valid-url"
                    
                    step_invalid = {
                        "name": f"{endpoint['name']} - URL Format Invalid",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_invalid,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_invalid['path_var_values'] = path_var_values
                    
                    self._add_headers(step_invalid, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @URL Invalid Format",
                            "description": f"실패 케이스 (400): @URL 형식 오류 ({field_name}, URL 형식이어야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "url_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_invalid],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'url_invalid_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 5-5. @CreditCardNumber 검증 (Hibernate Validator)
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                if field_info.get('credit_card'):
                    # 잘못된 신용카드 번호 (Luhn 알고리즘 실패)
                    body_invalid = self._build_request_body(endpoint['dto_fields'])
                    body_invalid[field_name] = "1234-5678-9012-3456"  # Invalid by Luhn
                    
                    step_invalid = {
                        "name": f"{endpoint['name']} - CreditCard Invalid",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body_invalid,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    if path_var_values:
                        step_invalid['path_var_values'] = path_var_values
                    
                    self._add_headers(step_invalid, endpoint)
                    
                    scenarios.append({
                        'scenario': {
                            "name": f"{endpoint['name']} - @CreditCardNumber Invalid",
                            "description": f"실패 케이스 (400): @CreditCardNumber 제약 위반 ({field_name}, 유효한 신용카드 번호여야 함)",
                            "host": "default",
                            "tags": ["failure", "validation", "400", "credit_card_constraint", self.parser.controller_name.lower()],
                            "continue_on_error": self.continue_on_error,
                            "steps": [step_invalid],
                            "environment": self.environment if self.environment else None,
                            "pre_request_scripts": self._get_pre_request_scripts(endpoint)
                        },
                        'type': f'credit_card_invalid_{field_name}',
                        'status_code': 400
                    })
                    break  # 한 개만 테스트
        
        # 6. 빈 본문 (400) - POST, PUT, PATCH
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['has_request_body']:
            step = {
                "name": f"{endpoint['name']} - Empty Body",
                "method": endpoint['method'],
                "path": path,
                "body": {},
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 400}
                ]
            }
            
            self._add_headers(step, endpoint)
            
            scenario = {
                "name": f"{endpoint['name']} - Empty Request Body",
                "description": f"실패 케이스 (400): 빈 요청 본문",
                "host": "default",
                "tags": ["failure", "validation", "400", "empty_body", self.parser.controller_name.lower()],
                "continue_on_error": self.continue_on_error,
                "steps": [step]
            }
            
            if self.environment:
                scenario["environment"] = self.environment
            
            pre_request_scripts = self._get_pre_request_scripts(endpoint)
            if pre_request_scripts:
                scenario["pre_request_scripts"] = pre_request_scripts
            
            scenarios.append({
                'scenario': scenario,
                'type': 'empty_body',
                'status_code': 400
            })
        
        # 7. 잘못된 ID (404) - GET, PUT, DELETE with path variable
        if endpoint['path_variables'] and endpoint['method'] in ['GET', 'PUT', 'DELETE']:
            invalid_path = re.sub(r'\{[^}]+\}', '99999', endpoint['path'])
            
            # Path Variable들을 모두 99999로 매핑 (TSV 생성용)
            invalid_path_var_values = {}
            for var in endpoint['path_variables']:
                if isinstance(var, dict):
                    var_name = var.get('name')
                    # 타입에 따라 99999 또는 "99999" 사용
                    var_type = var.get('type', 'String')
                    if var_type in ['int', 'Integer', 'long', 'Long']:
                        invalid_path_var_values[var_name] = 99999
                    else:
                        invalid_path_var_values[var_name] = "99999"
            
            step = {
                "name": f"{endpoint['name']} - Invalid ID",
                "method": endpoint['method'],
                "path": invalid_path,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 404}
                ]
            }
            
            # Path variable 값들을 step에 저장 (TSV 생성 시 사용)
            if invalid_path_var_values:
                step['path_var_values'] = invalid_path_var_values
            
            if endpoint['method'] == 'PUT' and endpoint['dto_fields']:
                body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
                step['body'] = body
            
            # Query 파라미터 추가 (GET, DELETE에도 있을 수 있음)
            query_params = {}
            if endpoint['query_params']:
                for param in endpoint['query_params']:
                    param_name = param['name'] if isinstance(param, dict) else param
                    param_type = param['type'] if isinstance(param, dict) else 'String'
                    # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                    if param_name in self.env_params:
                        query_params[param_name] = f"{{{{{param_name}}}}}"
                    else:
                        query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
            
            # ModelAttribute 필드를 query parameter로 추가
            if endpoint.get('model_attribute_fields'):
                for field_name, field_info in endpoint['model_attribute_fields'].items():
                    # env_params에 해당 필드가 있으면 변수 참조 형태로 생성
                    if field_name in self.env_params:
                        query_params[field_name] = f"{{{{{field_name}}}}}"
                    else:
                        query_params[field_name] = field_info['sample_value']
            
            if query_params:
                step['query_params'] = query_params
            
            self._add_headers(step, endpoint)
            
            scenario = {
                "name": f"{endpoint['name']} - Not Found",
                "description": f"실패 케이스 (404): 존재하지 않는 리소스",
                "host": "default",
                "tags": ["failure", "not_found", "404", self.parser.controller_name.lower()],
                "continue_on_error": self.continue_on_error,
                "steps": [step]
            }
            
            if self.environment:
                scenario["environment"] = self.environment
            
            pre_request_scripts = self._get_pre_request_scripts(endpoint)
            if pre_request_scripts:
                scenario["pre_request_scripts"] = pre_request_scripts
            
            scenarios.append({
                'scenario': scenario,
                'type': 'not_found',
                'status_code': 404
            })
        
        return scenarios
    
    def _generate_success_assertions(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """정상 케이스 assertion 생성"""
        assertions = []
        
        # 모든 메서드에 대해 200 응답 코드 사용
        expected_status = 200
        
        assertions.append({
            "field": "status",
            "operator": "eq",
            "value": expected_status
        })
        
        # 응답 body 존재 확인
        if endpoint['method'] in ['GET', 'POST', 'PUT', 'DELETE']:
            assertions.append({
                "field": "body",
                "operator": "exists"
            })
            
            # DefaultResultDto 구조 검증
            assertions.append({
                "field": "body.code",
                "operator": "exists"
            })
            assertions.append({
                "field": "body.message",
                "operator": "exists"
            })
        
        # 응답 DTO 필드 기반 검증 추가 (body.data 내부)
        response_type = endpoint.get('response_type')
        if response_type and response_type != 'Void':
            # data 필드 존재 확인
            assertions.append({
                "field": "body.data",
                "operator": "exists"
            })
            
            # 응답 DTO의 각 필드 검증 (최대 5개 필드)
            if endpoint.get('response_dto_fields'):
                field_count = 0
                for field_name, field_info in endpoint['response_dto_fields'].items():
                    # 필수 필드 또는 첫 5개 필드를 검증 (너무 많으면 assertion이 과도해짐)
                    if field_info.get('required', False) or field_count < 5:
                        assertions.append({
                            "field": f"body.data.{field_name}",
                            "operator": "exists"
                        })
                        field_count += 1
                        if field_count >= 5:
                            break
        
        return assertions
    
    def _generate_integration_scenario(self, output_dir: str):
        """API 통합 테스트 시나리오 생성"""
        print("\n2️⃣  통합 테스트 시나리오 생성 중...")
        
        # CRUD 통합 시나리오
        crud_scenario = self._create_crud_integration(output_dir)
        if crud_scenario:
            self._write_scenario(
                os.path.join(output_dir, f"{self.parser.controller_name.lower()}_crud_integration"),
                crud_scenario
            )
        
        # 전체 엔드포인트 통합 시나리오
        full_integration = self._create_full_integration(output_dir)
        self._write_scenario(
            os.path.join(output_dir, f"{self.parser.controller_name.lower()}_full_integration"),
            full_integration
        )
    
    def _create_crud_integration(self, output_dir: str) -> Optional[Dict[str, Any]]:
        """CRUD 통합 시나리오"""
        post_endpoint = None
        get_single_endpoint = None
        get_list_endpoint = None
        put_endpoint = None
        delete_endpoint = None
        
        for endpoint in self.parser.endpoints:
            if endpoint['method'] == 'POST' and not post_endpoint:
                post_endpoint = endpoint
            elif endpoint['method'] == 'GET':
                if endpoint['path_variables']:
                    get_single_endpoint = endpoint
                else:
                    get_list_endpoint = endpoint
            elif endpoint['method'] == 'PUT' and not put_endpoint:
                put_endpoint = endpoint
            elif endpoint['method'] == 'DELETE' and not delete_endpoint:
                delete_endpoint = endpoint
        
        if not (post_endpoint and get_single_endpoint and delete_endpoint):
            return None
        
        steps = []
        
        # 1. Create
        # 중첩 DTO 구조 포함하여 body 생성
        create_body = self._build_request_body(post_endpoint['dto_fields'])
        create_step = {
            "name": "1. 리소스 생성",
            "method": "POST",
            "path": self._replace_path_variables(post_endpoint['path'], post_endpoint),
            "body": create_body,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 200},
                {"field": "body.id", "operator": "exists"}
            ],
            "extract": {"resource_id": "body.id"}
        }
        self._add_headers(create_step)
        steps.append(create_step)
        
        # 2. Get List
        if get_list_endpoint:
            get_list_step = {
                "name": "2. 목록 조회",
                "method": "GET",
                "path": self._replace_path_variables(get_list_endpoint['path'], get_list_endpoint),
                "delay_before": 0.2,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 200}
                ]
            }
            self._add_headers(get_list_step)
            steps.append(get_list_step)
        
        # 3. Get Single
        get_path = re.sub(r'\{[^}]+\}', '{{resource_id}}', get_single_endpoint['path'])
        get_single_step = {
            "name": "3. 상세 조회",
            "method": "GET",
            "path": get_path,
            "delay_before": 0.2,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 200},
                {"field": "body.id", "operator": "exists"}
            ]
        }
        self._add_headers(get_single_step)
        steps.append(get_single_step)
        
        # 4. Update
        if put_endpoint:
            # 중첩 DTO 구조 포함하여 body 생성 (문자열 필드는 _updated 추가)
            update_body = self._build_request_body(put_endpoint['dto_fields'])
            # 문자열 필드에 _updated 추가 (단순 값만)
            for name, value in update_body.items():
                if isinstance(value, str) and not value.startswith('{{'):
                    update_body[name] = f"{value}_updated"
            update_path = re.sub(r'\{[^}]+\}', '{{resource_id}}', put_endpoint['path'])
            update_step = {
                "name": "4. 리소스 수정",
                "method": "PUT",
                "path": update_path,
                "body": update_body,
                "delay_before": 0.2,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 200}
                ]
            }
            self._add_headers(update_step)
            steps.append(update_step)
            
            update_check_step = {
                "name": "5. 수정 확인",
                "method": "GET",
                "path": get_path,
                "delay_before": 0.2,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 200}
                ]
            }
            self._add_headers(update_check_step)
            steps.append(update_check_step)
        
        # 5. Delete
        delete_path = re.sub(r'\{[^}]+\}', '{{resource_id}}', delete_endpoint['path'])
        delete_step = {
            "name": "6. 리소스 삭제",
            "method": "DELETE",
            "path": delete_path,
            "delay_before": 0.3,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 200}
            ]
        }
        self._add_headers(delete_step)
        steps.append(delete_step)
        
        delete_check_step = {
            "name": "7. 삭제 확인",
            "method": "GET",
            "path": get_path,
            "skip_on_failure": True,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 404}
            ]
        }
        self._add_headers(delete_check_step)
        steps.append(delete_check_step)
        
        scenario = {
            "name": f"{self.parser.controller_name} - CRUD Integration Test",
            "description": f"CRUD 통합 테스트: 생성→조회→수정→삭제",
            "host": "default",
            "tags": ["integration", "crud", self.parser.controller_name.lower()],
            "continue_on_error": self.continue_on_error,
            "steps": steps
        }
        
        if self.environment:
            scenario["environment"] = self.environment
        
        # Pre-request 스크립트 수집 (CRUD에 사용된 모든 엔드포인트에서)
        all_pre_request_scripts = set()
        for endpoint in [post_endpoint, get_single_endpoint, get_list_endpoint, put_endpoint, delete_endpoint]:
            if endpoint:
                scripts = self._get_pre_request_scripts(endpoint)
                if scripts:
                    all_pre_request_scripts.update(scripts)
        
        if all_pre_request_scripts:
            scenario["pre_request_scripts"] = list(all_pre_request_scripts)
        
        return scenario
    
    def _create_full_integration(self, output_dir: str) -> Dict[str, Any]:
        """전체 엔드포인트 통합 시나리오"""
        steps = []
        
        for i, endpoint in enumerate(self.parser.endpoints):
            step = {
                "name": f"{i+1}. {endpoint['name']}",
                "method": endpoint['method'],
                "path": self._replace_path_variables(endpoint['path'], endpoint)
            }
            
            if i > 0:
                step['delay_before'] = 0.2
            
            if endpoint['dto_fields']:
                # 중첩 DTO 구조 포함하여 body 생성
                step['body'] = self._build_request_body(endpoint['dto_fields'])
            
            step['assertions'] = self._generate_success_assertions(endpoint)
            
            # Bearer 토큰 헤더 추가
            self._add_headers(step)
            
            steps.append(step)
        
        scenario = {
            "name": f"{self.parser.controller_name} - Full Integration Test",
            "description": f"전체 엔드포인트 통합 테스트",
            "host": "default",
            "tags": ["integration", "full", self.parser.controller_name.lower()],
            "continue_on_error": self.continue_on_error,
            "steps": steps
        }
        
        if self.environment:
            scenario["environment"] = self.environment
        
        # Pre-request 스크립트 수집 (모든 엔드포인트에서)
        all_pre_request_scripts = set()
        for endpoint in self.parser.endpoints:
            scripts = self._get_pre_request_scripts(endpoint)
            if scripts:
                all_pre_request_scripts.update(scripts)
        
        if all_pre_request_scripts:
            scenario["pre_request_scripts"] = list(all_pre_request_scripts)
        
        return scenario
    
    def _generate_load_test_scenarios(self, output_dir: str):
        """성능 및 부하 테스트 시나리오 생성"""
        print("\n3️⃣  성능/부하 테스트 시나리오 생성 중...")
        
        for endpoint in self.parser.endpoints:
            # GET 메서드만 부하 테스트 (조회 성능 테스트)
            if endpoint['method'] == 'GET':
                load_scenario = self._create_load_test_scenario(endpoint)
                filename = f"{endpoint['original_method_name'].lower()}_load_test"
                self._write_scenario(os.path.join(output_dir, filename), load_scenario)
        
        # 전체 시나리오 부하 테스트
        stress_scenario = self._create_stress_test_scenario()
        self._write_scenario(
            os.path.join(output_dir, f"{self.parser.controller_name.lower()}_stress_test"),
            stress_scenario
        )
    
    def _create_load_test_scenario(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """개별 API 부하 테스트"""
        path, path_var_values = self._replace_path_variables(endpoint['path'], endpoint)
        
        step = {
            "name": endpoint['name'],
            "method": endpoint['method'],
            "path": path,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 200},
                {"field": "response_time", "operator": "lt", "value": 1000}  # 1초 이내
            ]
        }
        
        # Path variable 값들을 step에 저장
        if path_var_values:
            step['path_var_values'] = path_var_values
        
        # Bearer 토큰 헤더 추가
        self._add_headers(step)
        
        scenario = {
            "name": f"{endpoint['name']} - Load Test",
            "description": f"부하 테스트: {endpoint['method']} {path}",
            "host": "default",
            "tags": ["load_test", "performance", self.parser.controller_name.lower()],
            "continue_on_error": self.continue_on_error,
            "load_test": {
                "enabled": True,
                "users": 10,
                "spawn_rate": 2,
                "duration": 60
            },
            "steps": [step]
        }
        
        if self.environment:
            scenario["environment"] = self.environment
        
        # Pre-request 스크립트 추가
        pre_request_scripts = self._get_pre_request_scripts(endpoint)
        if pre_request_scripts:
            scenario["pre_request_scripts"] = pre_request_scripts
        
        return scenario
    
    def _create_stress_test_scenario(self) -> Dict[str, Any]:
        """전체 시나리오 스트레스 테스트"""
        steps = []
        
        for endpoint in self.parser.endpoints:
            step = {
                "name": endpoint['name'],
                "method": endpoint['method'],
                "path": self._replace_path_variables(endpoint['path'], endpoint),
                "delay_before": 0.1
            }
            
            if endpoint['dto_fields']:
                # 중첩 DTO 구조 포함하여 body 생성
                step['body'] = self._build_request_body(endpoint['dto_fields'])
            
            step['assertions'] = [
                {"field": "status", "operator": "lt", "value": 500},  # 5xx 에러 제외
                {"field": "response_time", "operator": "lt", "value": 2000}  # 2초 이내
            ]
            
            # Bearer 토큰 헤더 추가
            self._add_headers(step)
            
            steps.append(step)
        
        scenario = {
            "name": f"{self.parser.controller_name} - Stress Test",
            "description": f"스트레스 테스트: 모든 엔드포인트 동시 부하",
            "host": "default",
            "tags": ["stress_test", "performance", self.parser.controller_name.lower()],
            "continue_on_error": self.continue_on_error,
            "load_test": {
                "enabled": True,
                "users": 50,
                "spawn_rate": 5,
                "duration": 120
            },
            "steps": steps
        }
        
        if self.environment:
            scenario["environment"] = self.environment
        
        # Pre-request 스크립트 수집 (모든 엔드포인트에서)
        all_pre_request_scripts = set()
        for endpoint in self.parser.endpoints:
            scripts = self._get_pre_request_scripts(endpoint)
            if scripts:
                all_pre_request_scripts.update(scripts)
        
        if all_pre_request_scripts:
            scenario["pre_request_scripts"] = list(all_pre_request_scripts)
        
        return scenario
    
    def _write_scenario(self, filepath: str, data: Dict[str, Any], endpoint: Dict[str, Any] = None):
        """시나리오 파일 저장 (YAML 또는 JSON)"""
        # Remove None values for cleaner output
        data = self._clean_dict(data)
        
        # Change extension based on format
        path_obj = Path(filepath)
        if self.output_format == 'yaml':
            filepath = str(path_obj.with_suffix('.yaml'))
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        else:
            filepath = str(path_obj.with_suffix('.json'))
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 각 시나리오마다 개별 README 생성
        self._write_scenario_readme(filepath, data, endpoint)
        
        # 엑셀용 TSV 문서 생성
        self._write_scenario_csv(filepath, data, endpoint)
        
        # 파일 경로에서 폴더명 추출해서 표시
        path_obj = Path(filepath)
        folder_name = path_obj.parent.name
        if folder_name != 'scenario':
            print(f"  ✓ {folder_name}/{path_obj.name}")
        else:
            print(f"  ✓ {path_obj.name}")
    
    def _format_json_for_tsv(self, data: Any, indent: int = 0) -> List[str]:
        """JSON 데이터를 TSV에 표시할 수 있는 텍스트 라인 리스트로 변환 (따옴표 escape 없이)"""
        lines = []
        indent_str = '  ' * indent
        
        if data is None:
            return ['null']
        elif isinstance(data, bool):
            return ['true' if data else 'false']
        elif isinstance(data, (int, float)):
            return [str(data)]
        elif isinstance(data, str):
            # 문자열은 따옴표로 감싸되, escape 없이
            return [f'"{data}"']
        elif isinstance(data, list):
            if not data:
                return ['[]']
            lines.append('[')
            for i, item in enumerate(data):
                item_lines = self._format_json_for_tsv(item, indent + 1)
                is_last_item = i == len(data) - 1
                for j, line in enumerate(item_lines):
                    if j == 0:
                        # 첫 줄
                        prefix = '  ' * (indent + 1)
                        if len(item_lines) == 1:
                            # 단일 라인 (primitive)
                            lines.append(prefix + line + ('' if is_last_item else ','))
                        else:
                            # 멀티 라인 (object/array)
                            lines.append(prefix + line)
                    elif j == len(item_lines) - 1:
                        # 마지막 줄
                        lines.append(line + ('' if is_last_item else ','))
                    else:
                        # 중간 줄
                        lines.append(line)
            lines.append('  ' * indent + ']')
        elif isinstance(data, dict):
            if not data:
                return ['{}']
            lines.append('{')
            items = list(data.items())
            for idx, (key, value) in enumerate(items):
                value_lines = self._format_json_for_tsv(value, indent + 1)
                is_last = idx == len(items) - 1
                for i, line in enumerate(value_lines):
                    if i == 0:
                        # 첫 줄에 키 추가
                        prefix = '  ' * (indent + 1)
                        if len(value_lines) == 1:
                            # 단일 라인 값
                            lines.append(f'{prefix}"{key}": {line}' + ('' if is_last else ','))
                        else:
                            # 멀티 라인 값
                            lines.append(f'{prefix}"{key}": {line}')
                    elif i == len(value_lines) - 1:
                        # 마지막 줄
                        lines.append(line + ('' if is_last else ','))
                    else:
                        # 중간 줄
                        lines.append(line)
            lines.append('  ' * indent + '}')
        return lines
    
    def _write_scenario_csv(self, scenario_filepath: str, scenario_data: Dict[str, Any], endpoint: Dict[str, Any] = None):
        """각 시나리오 파일마다 엑셀용 TSV 생성 (탭 구분자)"""
        path_obj = Path(scenario_filepath)
        
        scenario_name = scenario_data.get('name', 'Test Scenario')
        description = scenario_data.get('description', '')
        steps = scenario_data.get('steps', [])
        tags = scenario_data.get('tags', [])
        
        # CSV 데이터 준비
        rows = []
        
        # 헤더
        rows.append(['TC 정보', ''])
        rows.append(['TC ID', path_obj.stem])
        rows.append(['테스트명', scenario_name])
        rows.append(['설명', description])
        rows.append(['태그', ', '.join(tags)])
        rows.append([])
        
        # 전제조건 (명사형 종결)
        rows.append(['전제조건', ''])
        rows.append(['', '- 테스트 환경 준비'])
        rows.append(['', '- API 서버 정상 동작'])
        
        # 인증이 필요한 경우
        has_auth = any(step.get('headers', {}).get('Authorization') for step in steps)
        if has_auth:
            rows.append(['', '- 유효한 인증 토큰 설정'])
        
        rows.append([])
        
        # 테스트 단계별로 작성 (구어체)
        for i, step in enumerate(steps, 1):
            step_name = step.get('name', f'Step {i}')
            method = step.get('method', 'GET')
            path = step.get('path', '')
            
            rows.append([f'Step {i}', step_name])
            rows.append([])
            
            # 테스트 절차 (명사형 종결)
            rows.append(['테스트 절차', ''])
            
            procedure_num = 1
            
            # 1. 요청 준비
            rows.append(['', f'{procedure_num}. {method} 방식으로 {path} 엔드포인트 요청 준비'])
            procedure_num += 1
            
            # 2. Path Variables (있으면)
            if endpoint and endpoint.get('path_variables'):
                path_vars = endpoint['path_variables']
                if path_vars:
                    rows.append(['', ''])
                    rows.append(['', f'{procedure_num}. Path Variable 설정:'])
                    
                    # step에 저장된 실제 치환된 값 사용 (있으면)
                    path_var_values = step.get('path_var_values', {})
                    
                    # step에 값이 없으면 Path에서 추출 시도
                    if not path_var_values and endpoint.get('path') and step.get('path'):
                        # endpoint path pattern: /api/v2/device/wifi/{deviceType}/list
                        # step path actual: /api/v2/device/wifi/1/list
                        # 추출하여 매핑
                        pattern = endpoint['path']
                        actual = step['path']
                        
                        # {var_name} 을 정규식 그룹으로 변환
                        regex_pattern = pattern
                        var_names = []
                        for var in path_vars:
                            if isinstance(var, dict):
                                var_name = var.get('name')
                                var_names.append(var_name)
                                regex_pattern = regex_pattern.replace('{' + var_name + '}', '([^/]+)')
                        
                        # 실제 path에서 값 추출
                        match = re.match(regex_pattern, actual)
                        if match:
                            for i, var_name in enumerate(var_names, 1):
                                path_var_values[var_name] = match.group(i)
                    
                    # Path Variable 출력
                    for var in path_vars:
                        if isinstance(var, dict):
                            var_name = var.get('name')
                            var_type = var.get('type', 'String')
                            # step에 저장된 값 또는 추출된 값 사용, 없으면 생성
                            if var_name in path_var_values:
                                sample_value = path_var_values[var_name]
                            else:
                                # 자료형에 맞는 샘플 값 생성
                                sample_value = self.parser._get_sample_value_for_type(var_type, var_name)
                            rows.append(['', f'   - {var_name}: {sample_value}'])
                    procedure_num += 1
            
            # 3. Query Parameters (있으면)
            if step.get('query_params'):
                rows.append(['', ''])
                rows.append(['', f'{procedure_num}. 쿼리 파라미터 설정:'])
                for key, value in step['query_params'].items():
                    rows.append(['', f'   - {key}: {value}'])
                procedure_num += 1
            
            # 4. Headers (있으면)
            if step.get('headers'):
                rows.append(['', ''])
                rows.append(['', f'{procedure_num}. 요청 헤더 설정:'])
                for key, value in step['headers'].items():
                    rows.append(['', f'   - {key}: {value}'])
                procedure_num += 1
            
            # 5. Request Body (있으면)
            if step.get('body'):
                rows.append(['', ''])
                rows.append(['', f'{procedure_num}. 요청 본문 작성:'])
                # 실제 body 데이터를 JSON 포맷으로 변환 (따옴표 escape 없이)
                body_lines = self._format_json_for_tsv(step['body'], indent=0)
                for line in body_lines:
                    rows.append(['', f'   {line}'])
                procedure_num += 1
            
            # 6. 요청 실행
            rows.append(['', ''])
            rows.append(['', f'{procedure_num}. 타겟 호스트로 요청 전송'])
            rows.append([])
            
            # 예상 결과 (명사형 종결 + 실제 DTO 필드)
            rows.append(['예상 결과', ''])
            
            # Assertions에서 예상 결과 추출
            assertions = step.get('assertions', [])
            status_code = 200
            result_num = 1
            
            for assertion in assertions:
                field = assertion.get('field', '')
                operator = assertion.get('operator', '')
                value = assertion.get('value', '')
                
                if field == 'status':
                    status_code = value
                    status_msg = {
                        200: '성공(200 OK)',
                        201: '생성 성공(201 Created)',
                        400: '잘못된 요청(400 Bad Request)',
                        401: '인증 실패(401 Unauthorized)',
                        403: '권한 없음(403 Forbidden)',
                        404: '찾을 수 없음(404 Not Found)',
                        500: '서버 오류(500 Internal Server Error)'
                    }.get(value, f'{value}')
                    rows.append(['', f'{result_num}. HTTP 상태 코드 {status_msg} 응답'])
                    result_num += 1
                elif field == 'body':
                    rows.append(['', f'{result_num}. 응답 본문 정상 반환'])
                    result_num += 1
                elif 'body.' in field:
                    field_name = field.replace('body.', '')
                    if operator == 'exists':
                        rows.append(['', f'{result_num}. 응답 본문 {field_name} 필드 존재 확인'])
                    elif operator == 'eq':
                        rows.append(['', f'{result_num}. 응답 본문 {field_name} 값 {value} 확인'])
                    result_num += 1
                elif field == 'response_time':
                    rows.append(['', f'{result_num}. 응답 시간 {value}ms 이내 확인'])
                    result_num += 1
            
            # 성공/실패에 따른 추가 설명 (명사형)
            if status_code == 200 or status_code == 201:
                rows.append(['', ''])
                rows.append(['', '※ 정상 처리 시 성공 응답 반환'])
            elif status_code == 400:
                rows.append(['', ''])
                rows.append(['', '※ 잘못된 요청 데이터로 인한 에러 응답 반환'])
            elif status_code == 401:
                rows.append(['', ''])
                rows.append(['', '※ 인증 정보 없음 또는 만료로 인한 접근 거부'])
            
            rows.append([])
            
            # Expected Result (실제 응답 DTO 기반 예시)
            rows.append(['Expected Result', ''])
            rows.append(['', 'Response Body 예시:'])
            
            # 실제 Response DTO 분석해서 JSON 생성
            if endpoint and (status_code == 200 or status_code == 201):
                # 성공 응답 - 실제 DTO 구조 사용
                response_type = endpoint.get('response_type')
                response_dto_fields = endpoint.get('response_dto_fields', {})
                
                if response_type and response_type != 'Void' and response_dto_fields:
                    # data 필드에 실제 DTO 샘플 생성
                    data_sample = {}
                    for field_name, field_info in response_dto_fields.items():
                        data_sample[field_name] = field_info.get('sample_value', 'sample')
                    
                    example_response = {
                        "code": "0",
                        "message": "Success",
                        "data": data_sample
                    }
                else:
                    # Response DTO가 없거나 Void인 경우
                    example_response = {
                        "code": "0",
                        "message": "Success",
                        "data": None
                    }
            elif status_code == 400:
                example_response = {
                    "code": "400",
                    "message": "Bad Request",
                    "data": None
                }
            elif status_code == 401:
                example_response = {
                    "code": "401",
                    "message": "Unauthorized",
                    "data": None
                }
            elif status_code == 404:
                example_response = {
                    "code": "404",
                    "message": "Not Found",
                    "data": None
                }
            else:
                example_response = {
                    "code": "500",
                    "message": "Internal Server Error",
                    "data": None
                }
            
            # 실제 response 데이터를 JSON 포맷으로 변환 (따옴표 escape 없이)
            response_lines = self._format_json_for_tsv(example_response, indent=0)
            for line in response_lines:
                rows.append(['', f'   {line}'])
            
            rows.append([])
            
            # 실제 결과 (테스터가 작성)
            rows.append(['실제 결과', ''])
            rows.append(['', '(테스트 수행 후 실제 결과 기록)'])
            rows.append([])
            
            # 테스트 결과
            rows.append(['테스트 결과', 'Pass / Fail'])
            rows.append([])
            
            # 비고
            rows.append(['비고', ''])
            rows.append(['', '(특이사항 또는 추가 메모 작성)'])
            rows.append([])
            rows.append([])
        
        # 추가 정보
        rows.append(['추가 정보', ''])
        rows.append(['생성 일시', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        rows.append(['시나리오 파일', path_obj.name])
        
        # TSV 파일로 저장 (탭 구분자 사용, JSON 따옴표 escape 방지)
        tsv_path = path_obj.with_suffix('.tsv')
        with open(tsv_path, 'w', encoding='utf-8-sig', newline='') as f:
            for row in rows:
                # 각 행을 탭으로 연결 (따옴표 escape 없이)
                line = '\t'.join(str(cell) for cell in row)
                f.write(line + '\n')
    
    def _find_scenario_files_recursive(self, directory: str, extension: str) -> List[str]:
        """디렉토리에서 재귀적으로 시나리오 파일 찾기"""
        files = []
        if not os.path.exists(directory):
            return files
        
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(extension) and not filename.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, filename), directory)
                    files.append(rel_path)
        return sorted(files)
    
    def _count_scenario_files_recursive(self, directory: str) -> int:
        """디렉토리에서 재귀적으로 시나리오 파일 개수 세기"""
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        return len(self._find_scenario_files_recursive(directory, ext))
    
    def _write_scenario_readme(self, scenario_filepath: str, scenario_data: Dict[str, Any], endpoint: Dict[str, Any] = None):
        """각 시나리오 파일마다 개별 README 생성"""
        path_obj = Path(scenario_filepath)
        readme_path = path_obj.with_suffix('.md')
        
        scenario_name = scenario_data.get('name', 'Test Scenario')
        description = scenario_data.get('description', '')
        steps = scenario_data.get('steps', [])
        environment = scenario_data.get('environment', 'N/A')
        
        content = f"""# {scenario_name}

## 테스트 정보

- **파일명**: `{path_obj.name}`
- **환경**: {environment}
- **설명**: {description}

## Test Procedure

"""
        
        # 각 단계별로 procedure 작성
        for i, step in enumerate(steps, 1):
            step_name = step.get('name', f'Step {i}')
            method = step.get('method', 'GET')
            path = step.get('path', '')
            
            content += f"""### Step {i}: {step_name}

**(1) 타겟 호스트로 요청 송신**

```
{method} {path}
```

"""
            
            # Request Headers
            if step.get('headers'):
                content += "**Headers:**\n```json\n"
                content += json.dumps(step['headers'], indent=2, ensure_ascii=False)
                content += "\n```\n\n"
            
            # Request Body
            if step.get('body'):
                content += "**Request Body:**\n```json\n"
                content += json.dumps(step['body'], indent=2, ensure_ascii=False)
                content += "\n```\n\n"
            
            # Query Parameters
            if step.get('query_params'):
                content += "**Query Parameters:**\n```json\n"
                content += json.dumps(step['query_params'], indent=2, ensure_ascii=False)
                content += "\n```\n\n"
            
            # Expected Response
            content += "**(2) 타겟 호스트로부터 응답 수신**\n\n"
            
            # Assertions (예상 결과)
            if step.get('assertions'):
                content += "**예상 결과:**\n\n"
                for assertion in step['assertions']:
                    field = assertion.get('field', '')
                    operator = assertion.get('operator', '')
                    value = assertion.get('value', '')
                    
                    if field == 'status':
                        content += f"- HTTP 상태 코드: {value}\n"
                    elif field == 'body':
                        content += f"- 응답 본문 존재\n"
                    else:
                        content += f"- `{field}` {operator} `{value}`\n"
                
                content += "\n"
            
            # Response Body 예시 (있는 경우)
            content += "**Response Body 예시:**\n```json\n"
            
            # HTTP 상태 코드에 따른 예시 응답
            status_assertion = next((a for a in step.get('assertions', []) if a.get('field') == 'status'), None)
            expected_status = status_assertion.get('value', 200) if status_assertion else 200
            
            if expected_status == 200 or expected_status == 201:
                content += """{\n  "code": "0",\n  "message": "Success",\n  "data": { }\n}"""
            elif expected_status == 400:
                content += """{\n  "code": "400",\n  "message": "Bad Request",\n  "data": null\n}"""
            elif expected_status == 401:
                content += """{\n  "code": "401",\n  "message": "Unauthorized",\n  "data": null\n}"""
            elif expected_status == 404:
                content += """{\n  "code": "404",\n  "message": "Not Found",\n  "data": null\n}"""
            else:
                content += """{\n  "code": "500",\n  "message": "Internal Server Error",\n  "data": null\n}"""
            
            content += "\n```\n\n"
            
            # Extracted Variables (있는 경우)
            if step.get('extract'):
                content += "**추출 변수:**\n\n"
                for var_name, json_path in step['extract'].items():
                    content += f"- `{var_name}` ← `{json_path}`\n"
                content += "\n"
            
            content += "---\n\n"
        
        # Tags
        if scenario_data.get('tags'):
            content += "## Tags\n\n"
            for tag in scenario_data['tags']:
                content += f"- `{tag}`\n"
            content += "\n"
        
        content += """
## 실행 방법

```bash
# 단일 시나리오 실행
python run_scenario.py --scenario """ + str(path_obj.relative_to(Path(scenario_filepath).parent.parent.parent)) + """

# 환경 지정 실행
python run_scenario.py --scenario """ + str(path_obj.relative_to(Path(scenario_filepath).parent.parent.parent)) + f""" --env {environment}
```

---
*본 문서는 자동 생성되었습니다.*
"""
        
        # README 파일 저장
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_test_case_documentation(self, scenario_dir: str, success_dir: str, failure_dir: str, integration_dir: str, load_test_dir: str):
        """TC 문서용 README 파일 생성"""
        
        # 1. 전체 개요 README
        self._write_main_readme(scenario_dir)
        
        # 2. 성공 케이스 README
        self._write_success_readme(success_dir)
        
        # 3. 실패 케이스 README
        self._write_failure_readme(failure_dir)
        
        # 4. 통합 테스트 README
        self._write_integration_readme(integration_dir)
        
        # 5. 부하 테스트 README
        self._write_load_test_readme(load_test_dir)
        
        print(f"  ✓ README.md (전체 개요)")
        print(f"  ✓ success/README.md")
        print(f"  ✓ failure/README.md")
        print(f"  ✓ integration/README.md")
        print(f"  ✓ load_test/README.md")
    
    def _write_main_readme(self, scenario_dir: str):
        """메인 README 생성"""
        controller_name = self.parser.controller_name
        total_endpoints = len(self.parser.endpoints)
        
        # 엔드포인트 통계
        method_stats = {}
        for endpoint in self.parser.endpoints:
            method = endpoint['method']
            method_stats[method] = method_stats.get(method, 0) + 1
        
        content = f"""# {controller_name} API 테스트 시나리오

## 📋 개요

본 문서는 `{controller_name}` API의 자동 생성된 테스트 시나리오에 대한 상세 문서입니다.

## 📊 테스트 대상 API

- **Controller**: {controller_name}
- **총 엔드포인트**: {total_endpoints}개
- **HTTP 메서드 분포**:
"""
        for method, count in sorted(method_stats.items()):
            content += f"  - {method}: {count}개\n"
        
        # 각 폴더별 파일 개수 재귀적으로 계산
        success_count = self._count_scenario_files_recursive(os.path.join(scenario_dir, 'success'))
        failure_count = self._count_scenario_files_recursive(os.path.join(scenario_dir, 'failure'))
        integration_count = self._count_scenario_files_recursive(os.path.join(scenario_dir, 'integration'))
        load_test_count = self._count_scenario_files_recursive(os.path.join(scenario_dir, 'load_test'))
        
        content += f"""
## 🗂️ 테스트 시나리오 구조

```
scenario/
├── success/          # 정상 케이스 ({success_count}개)
├── failure/          # 실패 케이스 ({failure_count}개)
├── integration/      # 통합 테스트 ({integration_count}개)
└── load_test/        # 부하 테스트 ({load_test_count}개)
```

## 📝 API 엔드포인트 목록

| No | Method | Path | 설명 |
|----|--------|------|------|
"""
        for i, endpoint in enumerate(self.parser.endpoints, 1):
            method = endpoint['method']
            path = endpoint['path']
            name = endpoint['name']
            content += f"| {i} | `{method}` | `{path}` | {name} |\n"
        
        content += f"""
## 🧪 테스트 케이스 분류

### 1. 성공 케이스 (Success Cases)
정상적인 요청에 대한 성공 응답을 검증합니다.
- 상세 문서: [success/README.md](success/README.md)

### 2. 실패 케이스 (Failure Cases)
다양한 오류 상황에 대한 에러 처리를 검증합니다.
- 상세 문서: [failure/README.md](failure/README.md)

### 3. 통합 테스트 (Integration Tests)
여러 API를 조합한 비즈니스 플로우를 검증합니다.
- 상세 문서: [integration/README.md](integration/README.md)

### 4. 부하 테스트 (Load Tests)
시스템 성능 및 안정성을 검증합니다.
- 상세 문서: [load_test/README.md](load_test/README.md)

## 🚀 시나리오 실행 방법

```bash
# 전체 시나리오 실행
python run_scenario.py --project {self.parser.controller_name.lower()}

# 특정 카테고리 실행
python run_scenario.py --project {self.parser.controller_name.lower()} --filter success
python run_scenario.py --project {self.parser.controller_name.lower()} --filter failure

# 특정 시나리오 실행
python run_scenario.py --scenario scenario/success/endpoint_success.yaml
```

## 📅 문서 생성 정보

- **생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **생성 도구**: generate_scenario.py (자동 생성)
- **환경**: {self.environment if self.environment else 'N/A'}

---
*본 문서는 자동 생성되었습니다. 수정 시 재생성 시 덮어쓰여질 수 있습니다.*
"""
        
        readme_path = os.path.join(scenario_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_success_readme(self, success_dir: str):
        """성공 케이스 README 생성"""
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        
        # 서브디렉토리 구조 지원: success/{api_name}/*.yaml (재귀적 탐색)
        files = self._find_scenario_files_recursive(success_dir, ext)
        
        content = f"""# 성공 케이스 테스트 시나리오

## 📋 개요

정상적인 API 호출에 대한 성공 응답을 검증하는 테스트 케이스입니다.

## 🎯 테스트 목적

- API가 정상적인 요청 파라미터를 올바르게 처리하는지 검증
- 성공 응답 상태 코드(200)와 응답 구조 검증
- 필수 응답 필드의 존재 여부 확인

## 📊 테스트 케이스 목록

총 **{len(files)}개**의 성공 케이스

| TC ID | 테스트명 | HTTP Method | Endpoint | 설명 |
|-------|---------|-------------|----------|------|
"""
        
        for i, filename in enumerate(files, 1):
            # 파일에서 시나리오 정보 읽기
            filepath = os.path.join(success_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-S-{i:03d}"
                name = scenario.get('name', filename)
                step = scenario['steps'][0] if scenario.get('steps') else {}
                method = step.get('method', 'N/A')
                path = step.get('path', 'N/A')
                desc = scenario.get('description', '')
                
                content += f"| {tc_id} | {name} | `{method}` | `{path}` | {desc} |\n"
            except:
                continue
        
        content += f"""
## 🧪 테스트 전제 조건

- API 서버가 정상 동작 중
- 유효한 인증 토큰 (환경 변수 설정)
- 테스트 데이터베이스 또는 테스트 환경 준비

## ✅ 공통 검증 항목

각 성공 케이스는 다음을 검증합니다:

1. **HTTP 상태 코드**: 200 OK
2. **응답 구조**: DefaultResultDto 형식
   - `code`: 응답 코드 존재
   - `message`: 응답 메시지 존재
   - `data`: 응답 데이터 존재 (있는 경우)
3. **응답 필드**: 요청 DTO의 필수 필드 존재 확인

## 📝 테스트 케이스 상세

"""
        
        # 각 테스트 케이스 상세 정보
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(success_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-S-{i:03d}"
                name = scenario.get('name', filename)
                desc = scenario.get('description', '')
                step = scenario['steps'][0] if scenario.get('steps') else {}
                
                content += f"""### {tc_id}: {name}

**파일명**: `{filename}`

**테스트 목적**: {desc if desc else '정상 케이스 검증'}

**HTTP 요청**:
- Method: `{step.get('method', 'N/A')}`
- Path: `{step.get('path', 'N/A')}`

**요청 파라미터**:
```json
{json.dumps(step.get('body', step.get('query_params', {})), indent=2, ensure_ascii=False)}
```

**예상 결과**:
- 상태 코드: 200
- 응답 구조: DefaultResultDto 형식

**검증 항목**:
"""
                assertions = step.get('assertions', [])
                for assertion in assertions:
                    field = assertion.get('field', '')
                    operator = assertion.get('operator', '')
                    value = assertion.get('value', '')
                    content += f"- {field} {operator} {value}\n"
                
                content += "\n---\n\n"
            except:
                continue
        
        content += """
## 🔄 실행 방법

```bash
# 전체 성공 케이스 실행
python run_scenario.py --filter success

# 특정 시나리오 실행
python run_scenario.py --scenario success/<filename>
```

---
*본 문서는 자동 생성되었습니다.*
"""
        
        readme_path = os.path.join(success_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_failure_readme(self, failure_dir: str):
        """실패 케이스 README 생성"""
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        
        # 서브디렉토리 구조 지원: failure/{api_name}/*.yaml (재귀적 탐색)
        files = self._find_scenario_files_recursive(failure_dir, ext)
        
        # 실패 케이스 분류
        unauthorized_cases = [f for f in files if 'unauthorized' in f or '401' in f]
        missing_field_cases = [f for f in files if 'missing' in f and '400' in f]
        invalid_format_cases = [f for f in files if 'invalid' in f and '400' in f]
        empty_cases = [f for f in files if 'empty' in f]
        null_cases = [f for f in files if 'null' in f]
        other_cases = [f for f in files if f not in unauthorized_cases + missing_field_cases + invalid_format_cases + empty_cases + null_cases]
        
        content = f"""# 실패 케이스 테스트 시나리오

## 📋 개요

다양한 오류 상황에 대한 API 에러 처리를 검증하는 테스트 케이스입니다.

## 🎯 테스트 목적

- API가 잘못된 요청을 적절히 거부하는지 검증
- 적절한 HTTP 상태 코드 반환 확인
- 에러 메시지의 명확성 검증
- 시스템 안정성 및 보안 검증

## 📊 실패 케이스 통계

총 **{len(files)}개**의 실패 케이스

| 분류 | 케이스 수 | 상태 코드 | 설명 |
|------|-----------|-----------|------|
| 인증 오류 | {len(unauthorized_cases)} | 401 | 인증 정보 없음 또는 만료 |
| 필수 필드 누락 | {len(missing_field_cases)} | 400 | 필수 파라미터 누락 |
| 잘못된 형식 | {len(invalid_format_cases)} | 400 | 데이터 타입 또는 형식 오류 |
| 빈 컬렉션 | {len(empty_cases)} | 400 | 빈 리스트 또는 빈 본문 |
| Null 값 | {len(null_cases)} | 400 | Null 또는 필드 누락 |
| 기타 | {len(other_cases)} | 400+ | 범위 초과 등 |

## 📝 테스트 케이스 분류

"""
        
        # 각 분류별 테스트 케이스
        categories = [
            ("인증 오류 (401)", unauthorized_cases),
            ("필수 필드 누락 (400)", missing_field_cases),
            ("잘못된 형식 (400)", invalid_format_cases),
            ("빈 컬렉션 (400)", empty_cases),
            ("Null 값 (400)", null_cases),
            ("기타", other_cases)
        ]
        
        tc_counter = 1
        for category_name, category_files in categories:
            if not category_files:
                continue
            
            content += f"""### {category_name}

총 {len(category_files)}개 케이스

| TC ID | 테스트명 | Endpoint | 오류 내용 |
|-------|---------|----------|----------|
"""
            
            for filename in category_files:
                filepath = os.path.join(failure_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if self.output_format == 'yaml':
                            scenario = yaml.safe_load(f)
                        else:
                            scenario = json.load(f)
                    
                    tc_id = f"TC-F-{tc_counter:03d}"
                    tc_counter += 1
                    name = scenario.get('name', filename)
                    desc = scenario.get('description', '')
                    step = scenario['steps'][0] if scenario.get('steps') else {}
                    path = step.get('path', 'N/A')
                    
                    content += f"| {tc_id} | {name} | `{path}` | {desc} |\n"
                except:
                    continue
            
            content += "\n"
        
        content += f"""
## 🧪 테스트 전제 조건

- API 서버가 정상 동작 중
- 적절한 에러 핸들링 구현 완료
- 에러 응답 형식 표준화

## ✅ 공통 검증 항목

각 실패 케이스는 다음을 검증합니다:

1. **HTTP 상태 코드**: 400, 401, 404 등 적절한 에러 코드
2. **에러 응답 구조**: 일관된 에러 응답 형식
3. **에러 메시지**: 명확하고 이해하기 쉬운 메시지
4. **시스템 안정성**: 에러 발생 시 서버 중단 없음

## 📝 실패 케이스 상세

"""
        
        # 대표 케이스 몇 개만 상세 설명 (너무 많으면 파일이 커짐)
        sample_files = files[:10] if len(files) > 10 else files
        
        for i, filename in enumerate(sample_files, 1):
            filepath = os.path.join(failure_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-F-{i:03d}"
                name = scenario.get('name', filename)
                desc = scenario.get('description', '')
                step = scenario['steps'][0] if scenario.get('steps') else {}
                
                content += f"""### {tc_id}: {name}

**파일명**: `{filename}`

**테스트 목적**: {desc}

**HTTP 요청**:
- Method: `{step.get('method', 'N/A')}`
- Path: `{step.get('path', 'N/A')}`

**의도적 오류**:
```json
{json.dumps(step.get('body', step.get('query_params', {})), indent=2, ensure_ascii=False)}
```

**예상 결과**:
"""
                assertions = step.get('assertions', [])
                for assertion in assertions:
                    field = assertion.get('field', '')
                    operator = assertion.get('operator', '')
                    value = assertion.get('value', '')
                    if field == 'status':
                        content += f"- HTTP 상태 코드: {value}\n"
                    else:
                        content += f"- {field} {operator} {value}\n"
                
                content += "\n---\n\n"
            except:
                continue
        
        if len(files) > 10:
            content += f"\n*(나머지 {len(files) - 10}개 케이스는 파일 참조)*\n\n"
        
        content += """
## 🔄 실행 방법

```bash
# 전체 실패 케이스 실행
python run_scenario.py --filter failure

# 특정 에러 타입만 실행
python run_scenario.py --filter failure --tag 401
python run_scenario.py --filter failure --tag missing_field
```

---
*본 문서는 자동 생성되었습니다.*
"""
        
        readme_path = os.path.join(failure_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_integration_readme(self, integration_dir: str):
        """통합 테스트 README 생성"""
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        
        # 서브디렉토리 구조 지원 (재귀적 탐색)
        files = self._find_scenario_files_recursive(integration_dir, ext)
        
        content = f"""# 통합 테스트 시나리오

## 📋 개요

여러 API를 조합한 비즈니스 플로우를 검증하는 통합 테스트입니다.

## 🎯 테스트 목적

- 실제 사용자 시나리오 재현
- API 간 데이터 연동 검증
- 트랜잭션 일관성 확인
- 전체 비즈니스 프로세스 검증

## 📊 통합 테스트 목록

총 **{len(files)}개**의 통합 테스트

| TC ID | 테스트명 | 단계 수 | 설명 |
|-------|---------|---------|------|
"""
        
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(integration_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-I-{i:03d}"
                name = scenario.get('name', filename)
                steps_count = len(scenario.get('steps', []))
                desc = scenario.get('description', '')
                
                content += f"| {tc_id} | {name} | {steps_count} | {desc} |\n"
            except:
                continue
        
        content += f"""
## 🧪 테스트 전제 조건

- API 서버가 정상 동작 중
- 유효한 인증 토큰
- 테스트 데이터베이스 초기화
- 종속 서비스 정상 동작

## 📝 통합 테스트 상세

"""
        
        # 각 통합 테스트 상세 정보
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(integration_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-I-{i:03d}"
                name = scenario.get('name', filename)
                desc = scenario.get('description', '')
                steps = scenario.get('steps', [])
                
                content += f"""### {tc_id}: {name}

**파일명**: `{filename}`

**테스트 목적**: {desc}

**테스트 시나리오**:

"""
                for j, step in enumerate(steps, 1):
                    step_name = step.get('name', f'Step {j}')
                    method = step.get('method', '')
                    path = step.get('path', '')
                    content += f"{j}. **{step_name}**\n"
                    content += f"   - Method: `{method}` Path: `{path}`\n"
                    
                    if step.get('extract'):
                        content += f"   - 추출: {', '.join(step['extract'].keys())}\n"
                    
                    assertions = step.get('assertions', [])
                    if assertions:
                        content += f"   - 검증: "
                        status_assertions = [a for a in assertions if a.get('field') == 'status']
                        if status_assertions:
                            content += f"상태={status_assertions[0].get('value', '')}"
                        content += "\n"
                
                content += "\n**예상 결과**: 전체 플로우가 성공적으로 완료되어야 함\n\n---\n\n"
            except:
                continue
        
        content += """
## 🔄 실행 방법

```bash
# 전체 통합 테스트 실행
python run_scenario.py --filter integration

# 특정 통합 테스트 실행
python run_scenario.py --scenario integration/<filename>
```

## ⚠️ 주의사항

- 통합 테스트는 데이터베이스를 수정할 수 있습니다
- 테스트 환경에서만 실행하세요
- 각 테스트는 독립적으로 실행 가능해야 합니다

---
*본 문서는 자동 생성되었습니다.*
"""
        
        readme_path = os.path.join(integration_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_load_test_readme(self, load_test_dir: str):
        """부하 테스트 README 생성"""
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        
        # 서브디렉토리 구조 지원 (재귀적 탐색)
        files = self._find_scenario_files_recursive(load_test_dir, ext)
        
        content = f"""# 부하 테스트 시나리오

## 📋 개요

시스템 성능, 확장성, 안정성을 검증하는 부하 테스트입니다.

## 🎯 테스트 목적

- 시스템 최대 처리 용량 확인
- 응답 시간 성능 측정
- 동시 사용자 처리 능력 검증
- 시스템 안정성 및 복구력 확인
- 병목 지점 식별

## 📊 부하 테스트 목록

총 **{len(files)}개**의 부하 테스트

| TC ID | 테스트명 | 사용자 수 | 지속 시간 | 목표 응답 시간 |
|-------|---------|-----------|-----------|---------------|
"""
        
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(load_test_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-L-{i:03d}"
                name = scenario.get('name', filename)
                load_config = scenario.get('load_test', {})
                users = load_config.get('users', 'N/A')
                duration = load_config.get('duration', 'N/A')
                
                # 응답 시간 목표 찾기
                target_response_time = 'N/A'
                steps = scenario.get('steps', [])
                if steps:
                    assertions = steps[0].get('assertions', [])
                    for assertion in assertions:
                        if assertion.get('field') == 'response_time':
                            target_response_time = f"{assertion.get('value', 'N/A')}ms"
                
                content += f"| {tc_id} | {name} | {users} | {duration}s | {target_response_time} |\n"
            except:
                continue
        
        content += f"""
## 🧪 테스트 전제 조건

- 프로덕션 환경과 유사한 테스트 환경
- 충분한 시스템 리소스 (CPU, 메모리, 네트워크)
- 모니터링 도구 설정 (Prometheus, Grafana 등)
- 테스트 데이터 준비

## 📈 성능 지표

각 부하 테스트에서 다음 지표를 측정합니다:

1. **응답 시간 (Response Time)**
   - 평균 (Average)
   - 중앙값 (Median)
   - 95 백분위수 (95th percentile)
   - 99 백분위수 (99th percentile)
   - 최대 (Max)

2. **처리량 (Throughput)**
   - 초당 요청 수 (RPS)
   - 초당 트랜잭션 수 (TPS)

3. **에러율 (Error Rate)**
   - 전체 요청 대비 실패 비율
   - 에러 타입별 분포

4. **시스템 리소스**
   - CPU 사용률
   - 메모리 사용량
   - 네트워크 대역폭

## 📝 부하 테스트 상세

"""
        
        # 각 부하 테스트 상세 정보
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(load_test_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if self.output_format == 'yaml':
                        scenario = yaml.safe_load(f)
                    else:
                        scenario = json.load(f)
                
                tc_id = f"TC-L-{i:03d}"
                name = scenario.get('name', filename)
                desc = scenario.get('description', '')
                load_config = scenario.get('load_test', {})
                
                content += f"""### {tc_id}: {name}

**파일명**: `{filename}`

**테스트 목적**: {desc}

**부하 테스트 설정**:
- 가상 사용자 수: {load_config.get('users', 'N/A')}
- 사용자 증가율: {load_config.get('spawn_rate', 'N/A')}/초
- 테스트 지속 시간: {load_config.get('duration', 'N/A')}초

**테스트 대상**:
"""
                steps = scenario.get('steps', [])
                for step in steps:
                    method = step.get('method', '')
                    path = step.get('path', '')
                    content += f"- `{method} {path}`\n"
                
                content += f"""
**성능 목표**:
"""
                if steps:
                    assertions = steps[0].get('assertions', [])
                    for assertion in assertions:
                        field = assertion.get('field', '')
                        operator = assertion.get('operator', '')
                        value = assertion.get('value', '')
                        if field == 'response_time':
                            content += f"- 응답 시간: {operator} {value}ms\n"
                        elif field == 'status':
                            content += f"- 상태 코드: {operator} {value} (에러 최소화)\n"
                
                content += "\n**측정 항목**: 응답 시간, 처리량, 에러율, 시스템 리소스\n\n---\n\n"
            except:
                continue
        
        content += """
## 🔄 실행 방법

```bash
# 개별 부하 테스트 실행
python run_scenario.py --scenario load_test/<filename>

# 전체 부하 테스트 실행
python run_scenario.py --filter load_test
```

## ⚠️ 주의사항

- 프로덕션 환경에서 부하 테스트를 실행하지 마세요
- 부하 테스트 중 시스템 모니터링 필수
- 테스트 결과를 분석하고 문서화하세요
- 필요 시 부하 설정을 조정하세요

## 📊 결과 분석

부하 테스트 완료 후 다음을 분석하세요:

1. **성능 목표 달성 여부**
2. **병목 지점 식별**
3. **시스템 확장성 평가**
4. **개선 필요 영역 도출**

---
*본 문서는 자동 생성되었습니다.*
"""
        
        readme_path = os.path.join(load_test_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _clean_dict(self, data: Any) -> Any:
        """Remove None values and empty dicts recursively (empty lists are preserved for validation tests)"""
        if isinstance(data, dict):
            # 빈 리스트는 유지 (validation test용), 빈 dict와 None만 제거
            return {k: self._clean_dict(v) for k, v in data.items() if v is not None and v != {}}
        elif isinstance(data, list):
            return [self._clean_dict(item) for item in data]
        else:
            return data


def process_directory(controller_dir: str, output_dir: str, context_path: str = "", auth_bearer_token: str = "", auth_basic_token: str = "", custom_headers: dict = None, auth_annotations: list = None, auth_mode: str = "include", continue_on_error: bool = False, environment: str = "", output_format: str = 'yaml', default_auth: str = 'bearer', default_auth_token: str = '', default_auth_library: str = '', annotation_auth_mapping: list = None, package_auth_mapping: list = None, auth_header_exclude_keyword: list = None):
    """디렉토리의 모든 컨트롤러 처리"""
    controller_files = glob.glob(os.path.join(controller_dir, '*Controller.java'))
    
    if not controller_files:
        print(f"❌ 컨트롤러 파일을 찾을 수 없습니다: {controller_dir}")
        return
    
    print(f"🔍 {len(controller_files)}개의 컨트롤러 발견")
    
    for controller_file in controller_files:
        print(f"\n{'='*80}")
        print(f"📋 처리 중: {Path(controller_file).name}")
        print(f"{'='*80}")
        
        # 임시 parser로 controller_name 추출 (env 파일 경로 결정용)
        temp_parser = JavaControllerParser(controller_file, context_path, auth_annotations, auth_mode, None, auth_header_exclude_keyword)
        temp_parser._extract_controller_name()
        
        # 환경 파일 경로 찾기 및 params 로드
        env_file_path = None
        env_params = {}
        if environment:
            project_name = temp_parser.controller_name.lower()
            project_dir = os.path.join(output_dir, project_name)
            env_file = os.path.join(project_dir, 'env', f'{environment}.json')
            if os.path.exists(env_file):
                env_file_path = env_file
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        env_data = json.load(f)
                        env_params = env_data.get('params', {})
                        print(f"✅ 환경 파일 로드: {env_file}")
                        print(f"   📝 params: {list(env_params.keys())}")
                except Exception as e:
                    print(f"⚠️  환경 파일 로드 실패: {e}")
        
        # env_params를 포함하여 parser 생성
        parser = JavaControllerParser(controller_file, context_path, auth_annotations, auth_mode, env_params, auth_header_exclude_keyword)
        parser.parse()
        
        print(f"📊 발견된 엔드포인트: {len(parser.endpoints)}개")
        
        # 엔드포인트 상세 정보 출력
        for endpoint in parser.endpoints:
            print(f"   • {endpoint['method']:6s} {endpoint['path']}")
            if endpoint.get('request_body_type'):
                print(f"     ↳ 요청: {endpoint['request_body_type']}")
            if endpoint.get('response_type'):
                print(f"     ↳ 응답: {endpoint['response_type']}")
                if endpoint.get('response_dto_fields'):
                    print(f"       (필드 {len(endpoint['response_dto_fields'])}개)")
        
        if not parser.endpoints:
            print("⚠️  엔드포인트를 찾을 수 없습니다. 건너뜁니다.")
            continue
        
        generator = ScenarioGenerator(
            parser, 
            output_dir, 
            auth_bearer_token, 
            auth_basic_token, 
            custom_headers or {}, 
            continue_on_error, 
            environment, 
            auth_annotations or [], 
            output_format, 
            env_file_path,
            auth_mode,
            default_auth,
            default_auth_token,
            default_auth_library,
            annotation_auth_mapping or [],
            package_auth_mapping or [],
            auth_header_exclude_keyword or []
        )
        generator.generate()


def main():
    parser = argparse.ArgumentParser(
        description='자바 컨트롤러에서 REST API 시나리오 파일 자동 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 파일
  python3 generate_scenario.py /path/to/UserController.java
  
  # 디렉토리 (모든 컨트롤러)
  python3 generate_scenario.py /path/to/controller/directory
  
  # 출력 경로 지정
  python3 generate_scenario.py /path/to/controller --output /custom/path
        """
    )
    
    parser.add_argument(
        'controller_path',
        help='자바 컨트롤러 파일 또는 디렉토리 경로'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/projects',
        help='시나리오 파일을 생성할 출력 디렉토리'
    )
    
    parser.add_argument(
        '--context-path', '-c',
        default='',
        help='API context path (예: /api/v1, /api/v2)'
    )
    
    parser.add_argument(
        '--auth-bearer-token',
        default='',
        help='Bearer 토큰 (예: your-jwt-token-here)'
    )
    
    parser.add_argument(
        '--auth-basic-token',
        default='',
        help='Basic 인증 토큰 (예: base64(username:password) 또는 username:password)'
    )
    
    parser.add_argument(
        '--auth-annotations', '-a',
        nargs='+',
        default=[],
        help='인증 어노테이션과 pre-request 매핑 (예: UserCert:wpm-get-user-info.json Authenticated:auth.json 또는 단순 UserCert)'
    )
    
    parser.add_argument(
        '--auth-mode', '-am',
        choices=['include', 'exclude', 'all'],
        default='include',
        help='''인증 적용 모드 선택:
        - include (기본값): auth-annotations에 지정된 어노테이션이 있는 메서드만 인증 필요
        - exclude: 기본적으로 모든 메서드에 인증 필요, auth-annotations에 지정된 어노테이션이 있는 메서드만 인증 불필요
        - all: 모든 메서드에 인증 적용 (어노테이션별 다른 인증 방식 사용 가능)'''
    )
    
    parser.add_argument(
        '--default-auth',
        choices=['bearer', 'basic', 'none'],
        default='bearer',
        help='기본 인증 방식 (auth-mode=all 사용 시)'
    )
    
    parser.add_argument(
        '--default-auth-token',
        default='',
        help='기본 인증 토큰 (auth-mode=all 사용 시, 예: {{USER_CERT_TOKEN}})'
    )
    
    parser.add_argument(
        '--default-auth-library',
        default='',
        help='기본 인증 토큰을 위한 package library 파일 (auth-mode=all 사용 시, 예: get-user-token.json)'
    )
    
    parser.add_argument(
        '--annotation-auth-mapping',
        nargs='+',
        default=[],
        help='어노테이션별 인증 방식 매핑 (예: "NoAuth:basic:{{USER_ID}}:{{USER_PW}}" "NoAuth:basic:{{USER_ID}}:{{USER_PW}}:X-Auth-Server={{SERVER_ID}}")'
    )
    
    parser.add_argument(
        '--package-auth-mapping',
        nargs='+',
        default=[],
        help='패키지별 인증 방식 매핑 (예: "com.oauth:basic:{{USER_ID}}:{{USER_PW}}:X-Auth-Server={{SERVER_ID}}" "com.user.api:bearer:{{USER_CERT_TOKEN}}")'
    )
    
    parser.add_argument(
        '--auth-header-exclude-keyword',
        nargs='+',
        default=[],
        help='@RequestHeader에서 Authorization 헤더 자동 추가를 제외할 키워드 목록 (예: "HttpHeaders.AUTHORIZATION" "Authorization")'
    )
    
    parser.add_argument(
        '--header', '-H',
        action='append',
        default=[],
        help='커스텀 헤더 추가 (예: "X-API-Key:your-key" "X-Custom:value")'
    )
    
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='Assertion 실패 시에도 다음 스텝 계속 실행'
    )
    
    parser.add_argument(
        '--environment', '-e',
        default='',
        help='시나리오에서 사용할 환경 이름 (예: development, production)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['yaml', 'json'],
        default='yaml',
        help='출력 파일 형식 (기본값: yaml)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.controller_path):
        print(f"❌ 경로를 찾을 수 없습니다: {args.controller_path}")
        return
    
    # 커스텀 헤더 파싱
    custom_headers = {}
    for header in args.header:
        if ':' in header:
            key, value = header.split(':', 1)
            custom_headers[key.strip()] = value.strip()
    
    print(f"\n🚀 시나리오 자동 생성 시작")
    print(f"📂 입력: {args.controller_path}")
    print(f"📂 출력: {args.output}")
    print(f"📄 형식: {args.format.upper()}")
    if args.context_path:
        print(f"🔗 Context Path: {args.context_path}")
    if args.auth_bearer_token:
        print(f"🔐 Bearer Token: {args.auth_bearer_token[:10]}..." if len(args.auth_bearer_token) > 10 else f"🔐 Bearer Token: {args.auth_bearer_token}")
    if args.auth_basic_token:
        print(f"🔐 Basic Token: {args.auth_basic_token[:10]}..." if len(args.auth_basic_token) > 10 else f"🔐 Basic Token: {args.auth_basic_token}")
    if custom_headers:
        print(f"📋 Custom Headers: {', '.join([f'{k}={v[:10]}...' if len(v) > 10 else f'{k}={v}' for k, v in custom_headers.items()])}")
    if args.auth_annotations:
        print(f"🔒 Auth Annotations: {', '.join(args.auth_annotations)}")
        auth_mode_desc = "Include Mode (어노테이션 있으면 인증 필요)" if args.auth_mode == 'include' else "Exclude Mode (어노테이션 있으면 인증 불필요, 기본 인증)"
        print(f"🔐 Auth Mode: {auth_mode_desc}")
    if args.continue_on_error:
        print(f"✅ Continue on Error: Assertion 실패 시에도 계속 진행")
    if args.environment:
        print(f"🌍 Environment: {args.environment}")
    
    if os.path.isdir(args.controller_path):
        process_directory(
            args.controller_path, 
            args.output, 
            args.context_path, 
            args.auth_bearer_token, 
            args.auth_basic_token, 
            custom_headers, 
            args.auth_annotations, 
            args.auth_mode, 
            args.continue_on_error, 
            args.environment, 
            args.format,
            args.default_auth,
            args.default_auth_token,
            args.default_auth_library,
            args.annotation_auth_mapping,
            args.package_auth_mapping,
            args.auth_header_exclude_keyword
        )
    elif args.controller_path.endswith('.java'):
        # 임시 parser로 controller_name 추출 (env 파일 경로 결정용)
        temp_parser = JavaControllerParser(args.controller_path, args.context_path, args.auth_annotations, args.auth_mode, None, args.auth_header_exclude_keyword)
        temp_parser._extract_controller_name()
        
        # 환경 파일 경로 찾기 및 params 로드
        env_file_path = None
        env_params = {}
        if args.environment:
            project_name = temp_parser.controller_name.lower()
            project_dir = os.path.join(args.output, project_name)
            env_file = os.path.join(project_dir, 'env', f'{args.environment}.json')
            if os.path.exists(env_file):
                env_file_path = env_file
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        env_data = json.load(f)
                        env_params = env_data.get('params', {})
                        print(f"✅ 환경 파일 로드: {env_file}")
                        print(f"   📝 params: {list(env_params.keys())}")
                except Exception as e:
                    print(f"⚠️  환경 파일 로드 실패: {e}")
        
        # env_params를 포함하여 parser 생성
        java_parser = JavaControllerParser(args.controller_path, args.context_path, args.auth_annotations, args.auth_mode, env_params, args.auth_header_exclude_keyword)
        java_parser.parse()
        
        print(f"📊 발견된 엔드포인트: {len(java_parser.endpoints)}개")
        
        # 엔드포인트 상세 정보 출력
        for endpoint in java_parser.endpoints:
            print(f"   • {endpoint['method']:6s} {endpoint['path']}")
            if endpoint.get('request_body_type'):
                print(f"     ↳ 요청: {endpoint['request_body_type']}")
            if endpoint.get('response_type'):
                print(f"     ↳ 응답: {endpoint['response_type']}")
                if endpoint.get('response_dto_fields'):
                    print(f"       (필드 {len(endpoint['response_dto_fields'])}개)")
        
        if not java_parser.endpoints:
            print("⚠️  엔드포인트를 찾을 수 없습니다")
            return
        
        generator = ScenarioGenerator(
            java_parser, 
            args.output, 
            args.auth_bearer_token, 
            args.auth_basic_token, 
            custom_headers, 
            args.continue_on_error, 
            args.environment, 
            args.auth_annotations or [], 
            args.format, 
            env_file_path,
            args.auth_mode,
            args.default_auth,
            args.default_auth_token,
            args.default_auth_library,
            args.annotation_auth_mapping or [],
            args.package_auth_mapping or [],
            args.auth_header_exclude_keyword or []
        )
        generator.generate()
    else:
        print("❌ 자바 파일(.java) 또는 디렉토리만 지원됩니다")
        return
    
    print("\n" + "="*80)
    print("🎉 모든 시나리오 생성 완료!")
    print("="*80)


if __name__ == '__main__':
    main()
