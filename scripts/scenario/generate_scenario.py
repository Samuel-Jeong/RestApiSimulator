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
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import glob


class JavaDtoParser:
    """자바 DTO 클래스 파싱"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).parent.parent
        self.dto_cache = {}
        
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
            
            fields = self._parse_fields(content)
            self.dto_cache[dto_class_name] = fields
            return fields
        except Exception as e:
            print(f"  ⚠️  DTO 파일 읽기 실패 ({dto_class_name}): {e}")
            return self._generate_default_dto_fields(dto_class_name)
    
    def _find_dto_file(self, dto_class_name: str, import_paths: List[str]) -> Optional[str]:
        """DTO 파일 찾기"""
        # import 경로에서 찾기
        for import_path in import_paths:
            if dto_class_name in import_path:
                # 패키지 경로를 파일 경로로 변환
                relative_path = import_path.replace('.', '/') + '.java'
                # src/main/java/ 기준으로 찾기
                possible_paths = [
                    self.base_path / 'src' / 'main' / 'java' / relative_path,
                    self.base_path / relative_path
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
    
    def _parse_fields(self, content: str) -> Dict[str, Any]:
        """DTO 필드 파싱"""
        fields = {}
        
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
                'sample_value': self._generate_sample_value(field_name, field_type, validation_info)
            }
        
        return fields
    
    def _extract_validation(self, before_field: str, field_name: str) -> Dict[str, Any]:
        """Validation 어노테이션 추출"""
        validation = {}
        
        # @NotNull, @NotEmpty, @NotBlank
        if re.search(r'@Not(Null|Empty|Blank)', before_field):
            validation['required'] = True
        
        # @Pattern
        pattern_match = re.search(r'@Pattern\([^)]*regexp\s*=\s*"([^"]+)"', before_field)
        if pattern_match:
            validation['pattern'] = pattern_match.group(1)
        
        # @Min, @Max
        min_match = re.search(r'@Min\((\d+)\)', before_field)
        if min_match:
            validation['min'] = int(min_match.group(1))
        
        max_match = re.search(r'@Max\((\d+)\)', before_field)
        if max_match:
            validation['max'] = int(max_match.group(1))
        
        # @Size
        size_match = re.search(r'@Size\([^)]*min\s*=\s*(\d+)', before_field)
        if size_match:
            validation['min_length'] = int(size_match.group(1))
        
        size_match = re.search(r'@Size\([^)]*max\s*=\s*(\d+)', before_field)
        if size_match:
            validation['max_length'] = int(size_match.group(1))
        
        # @Length
        length_match = re.search(r'@Length\([^)]*min\s*=\s*(\d+)', before_field)
        if length_match:
            validation['min_length'] = int(length_match.group(1))
        
        length_match = re.search(r'@Length\([^)]*max\s*=\s*(\d+)', before_field)
        if length_match:
            validation['max_length'] = int(length_match.group(1))
        
        # 커스텀 어노테이션
        if '@LocalTimeFormat' in before_field:
            validation['custom_format'] = 'LocalTime'
        
        if '@LocalDateFormat' in before_field:
            validation['custom_format'] = 'LocalDate'
        
        if '@LocalDateTimeFormat' in before_field:
            validation['custom_format'] = 'LocalDateTime'
        
        if '@DayBitFlag' in before_field:
            validation['custom_format'] = 'DayBitFlag'
        
        if '@Email' in before_field:
            validation['custom_format'] = 'Email'
        
        return validation
    
    def _generate_sample_value(self, field_name: str, field_type: str, validation: Dict) -> Any:
        """필드에 맞는 샘플 값 생성"""
        field_lower = field_name.lower()
        
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
        
        elif field_type in ['int', 'Integer', 'long', 'Long']:
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
            return []
        
        elif 'Map<' in field_type:
            return {}
        
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
    
    def __init__(self, java_file_path: str, context_path: str = "", auth_annotations: list = None, auth_mode: str = "include"):
        self.java_file_path = java_file_path
        self.content = self._read_file()
        self.context_path = context_path.rstrip('/') if context_path else ""
        self.auth_annotations = auth_annotations if auth_annotations else []
        self.auth_mode = auth_mode.lower()  # "include" or "exclude"
        self.controller_base_path = ""
        self.controller_name = ""
        self.endpoints = []
        self.import_paths = []
        self.dto_parser = JavaDtoParser(java_file_path)
        
    def _read_file(self) -> str:
        """파일 읽기"""
        with open(self.java_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse(self):
        """컨트롤러 파싱"""
        self._extract_imports()
        self._extract_controller_name()
        self._extract_base_path()
        self._extract_endpoints()
        
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
                
                # 어노테이션 이후 public 메서드 찾기 (최대 2000자 범위)
                # 다른 어노테이션들이 중간에 있을 수 있으므로 범위를 넓힘
                search_text = content_no_comments[anno_end:anno_end+2000]
                
                # public 메서드 패턴 (제너릭 타입, 여러 줄 파라미터 지원)
                method_pattern = r'public\s+[\w<>,\s]+\s+(\w+)\s*\(([\s\S]*?)\)\s*\{'
                method_match = re.search(method_pattern, search_text)
                
                if method_match:
                    method_name = method_match.group(1)
                    method_params = method_match.group(2)
                    
                    # 중복 체크
                    if not any(e['original_method_name'] == method_name for e in self.endpoints):
                        endpoint = self._parse_endpoint(method, annotation_params, method_name, method_params, has_auth_annotation, found_annotations)
                        if endpoint:
                            self.endpoints.append(endpoint)
    
    def _check_auth_annotations(self, text: str) -> tuple[bool, list]:
        """인증 관련 어노테이션 확인 및 발견된 어노테이션 리스트 반환
        
        auth_mode에 따라 동작 방식이 다름:
        - include: auth_annotations에 지정된 어노테이션이 있으면 인증 필요 (기본값)
        - exclude: 기본적으로 모두 인증 필요, auth_annotations에 지정된 어노테이션이 있으면 인증 불필요
        """
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
                       method_name: str, method_params: str, has_auth: bool = False, annotations: list = None) -> Optional[Dict[str, Any]]:
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
        
        path_variables = re.findall(r'\{(\w+)\}', full_path)
        
        endpoint = {
            'name': readable_name,
            'method': http_method,
            'path': full_path,
            'original_method_name': method_name,
            'path_variables': path_variables,
            'has_request_body': params_info['has_request_body'],
            'request_body_type': params_info['request_body_type'],
            'query_params': params_info['query_params'],
            'dto_fields': dto_fields,
            'model_attribute_fields': model_attribute_fields,
            'requires_auth': has_auth,
            'annotations': annotations or []
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
            'model_attribute_type': None
        }
        
        if not method_params.strip():
            return result
        
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
        param_pattern = r'@RequestParam\s*(?:\(([^)]*)\))?\s+(?:@[\w]+\s+)*([\w<>]+)\s+(\w+)'
        param_matches = re.finditer(param_pattern, method_params)
        
        for match in param_matches:
            annotation_content = match.group(1)  # 괄호 안 내용
            param_type = match.group(2)          # 자료형 (String, Integer 등)
            variable_name = match.group(3)       # 변수명
            
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
    
    def __init__(self, parser: JavaControllerParser, output_dir: str, auth_bearer_token: str = "", auth_basic_token: str = "", custom_headers: dict = None, continue_on_error: bool = False, environment: str = "", auth_annotations: List[str] = None, output_format: str = 'yaml'):
        self.parser = parser
        self.output_dir = output_dir
        self.auth_bearer_token = auth_bearer_token
        self.auth_basic_token = auth_basic_token
        self.custom_headers = custom_headers or {}
        self.continue_on_error = continue_on_error
        self.environment = environment
        self.output_format = output_format  # 'yaml' or 'json'
        
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
    
    def _replace_path_variables(self, path: str, endpoint: Dict[str, Any] = None) -> str:
        """Path variable을 샘플 값으로 치환"""
        # endpoint의 path_variables에서 자료형 정보 추출
        path_var_types = {}
        if endpoint and endpoint.get('path_variables'):
            for var in endpoint['path_variables']:
                if isinstance(var, dict):
                    path_var_types[var['name']] = var['type']
        
        # {id}, {contractIdx} 등의 path variable을 샘플 값으로 변경
        def replace_var(match):
            var_name = match.group(1)
            
            # 자료형 정보가 있으면 자료형 기반으로 샘플 값 생성
            if var_name in path_var_types:
                var_type = path_var_types[var_name]
                sample_value = self.parser._get_sample_value_for_type(var_type, var_name)
                # Path variable은 URL에 들어가므로 문자열로 변환
                return str(sample_value)
            
            # 자료형 정보가 없으면 기존 방식 사용
            var_lower = var_name.lower()
            if 'id' in var_lower or 'idx' in var_lower:
                return "1"
            elif 'code' in var_lower:
                return "TEST001"
            elif 'name' in var_lower:
                return "testname"
            else:
                return "test"
        
        return re.sub(r'\{(\w+)\}', replace_var, path)
    
    def _get_pre_request_scripts(self, endpoint: Dict[str, Any]) -> Optional[List[str]]:
        """엔드포인트의 어노테이션을 기반으로 필요한 pre-request 스크립트 목록 반환"""
        if not endpoint:
            return None
        
        annotations = endpoint.get('annotations', [])
        pre_request_scripts = []
        
        for annotation in annotations:
            if annotation in self.annotation_pre_request_map:
                script_file = self.annotation_pre_request_map[annotation]
                if script_file not in pre_request_scripts:
                    pre_request_scripts.append(script_file)
        
        return pre_request_scripts if pre_request_scripts else None
    
    def _add_headers(self, step: Dict[str, Any], endpoint: Dict[str, Any] = None) -> None:
        """인증 헤더 및 커스텀 헤더 추가"""
        if 'headers' not in step:
            step['headers'] = {}
        
        # Bearer 토큰 추가
        if self.auth_bearer_token:
            # endpoint가 제공되었고 requires_auth가 False면 토큰 추가 안 함
            if endpoint is None or endpoint.get('requires_auth', False):
                step['headers']['Authorization'] = f"Bearer {self.auth_bearer_token}"
        
        # Basic 토큰 추가
        if self.auth_basic_token:
            # endpoint가 제공되었고 requires_auth가 False면 토큰 추가 안 함
            if endpoint is None or endpoint.get('requires_auth', False):
                # username:password 형식이면 base64 인코딩
                if ':' in self.auth_basic_token and not self.auth_basic_token.startswith('Basic '):
                    encoded = base64.b64encode(self.auth_basic_token.encode()).decode()
                    step['headers']['Authorization'] = f"Basic {encoded}"
                else:
                    # 이미 인코딩되었거나 Basic이 포함된 경우
                    token = self.auth_basic_token.replace('Basic ', '')
                    step['headers']['Authorization'] = f"Basic {token}"
        
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
        
        # 전체 파일 개수 계산
        ext = '.yaml' if self.output_format == 'yaml' else '.json'
        total_files = sum([
            len([f for f in os.listdir(success_dir) if f.endswith(ext)]),
            len([f for f in os.listdir(failure_dir) if f.endswith(ext)]),
            len([f for f in os.listdir(integration_dir) if f.endswith(ext)]),
            len([f for f in os.listdir(load_test_dir) if f.endswith(ext)])
        ])
        print(f"📊 총 {total_files}개 {self.output_format.upper()} 파일 생성")
        
    def _generate_success_failure_scenarios(self, success_dir: str, failure_dir: str):
        """각 API별 정상/실패 시나리오 생성"""
        print("\n1️⃣  정상/실패 시나리오 생성 중...")
        
        for endpoint in self.parser.endpoints:
            # 정상 시나리오 → success/ 폴더
            success_scenario = self._create_success_scenario(endpoint)
            filename = f"{endpoint['original_method_name'].lower()}_success"
            self._write_scenario(os.path.join(success_dir, filename), success_scenario)
            
            # 실패 시나리오 → failure/ 폴더
            failure_scenarios = self._create_failure_scenarios(endpoint)
            for failure_info in failure_scenarios:
                failure_scenario = failure_info['scenario']
                failure_type = failure_info['type']
                status_code = failure_info['status_code']
                filename = f"{endpoint['original_method_name'].lower()}_failure_{failure_type}_{status_code}"
                self._write_scenario(os.path.join(failure_dir, filename), failure_scenario)
    
    def _create_success_scenario(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """정상 시나리오 생성"""
        # Path variable을 샘플 값으로 치환 (자료형 기반)
        path = self._replace_path_variables(endpoint['path'], endpoint)
        
        step = {
            "name": f"{endpoint['name']} - Success Case",
            "method": endpoint['method'],
            "path": path
        }
        
        # 요청 본문 (DTO 필드 기반)
        if endpoint['dto_fields']:
            body = {}
            for field_name, field_info in endpoint['dto_fields'].items():
                body[field_name] = field_info['sample_value']
            step['body'] = body
        
        # Query 파라미터 (일반 RequestParam)
        query_params = {}
        if endpoint['query_params']:
            for param in endpoint['query_params']:
                param_name = param['name'] if isinstance(param, dict) else param
                param_type = param['type'] if isinstance(param, dict) else 'String'
                query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
        
        # ModelAttribute 필드를 query parameter로 추가 (GET 요청)
        if endpoint.get('model_attribute_fields'):
            for field_name, field_info in endpoint['model_attribute_fields'].items():
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
        path = self._replace_path_variables(endpoint['path'], endpoint)
        
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
            
            # 요청 본문이 있으면 추가
            if endpoint['dto_fields']:
                body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
                step['body'] = body
            
            # Query 파라미터 추가 (일반 RequestParam)
            query_params = {}
            if endpoint['query_params']:
                for param in endpoint['query_params']:
                    param_name = param['name'] if isinstance(param, dict) else param
                    param_type = param['type'] if isinstance(param, dict) else 'String'
                    query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
            
            # ModelAttribute 필드를 query parameter로 추가 (GET 요청)
            if endpoint.get('model_attribute_fields'):
                for field_name, field_info in endpoint['model_attribute_fields'].items():
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
        
        # 2. 필수 필드 누락 (400) - POST, PUT, PATCH
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            required_fields = [
                name for name, info in endpoint['dto_fields'].items() 
                if info.get('required')
            ]
            
            for field_name in required_fields:
                body = {}
                for name, info in endpoint['dto_fields'].items():
                    if name != field_name:  # 해당 필드 제외
                        body[name] = info['sample_value']
                
                step = {
                    "name": f"{endpoint['name']} - Missing {field_name}",
                    "method": endpoint['method'],
                    "path": path,
                    "body": body,
                    "assertions": [
                        {"field": "status", "operator": "eq", "value": 400}
                    ]
                }
                
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
        
        # 3. 잘못된 필드 타입/포맷 (400) - POST, PUT, PATCH
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            # 각 필드의 타입과 포맷에 맞는 잘못된 값 생성
            for field_name, field_info in endpoint['dto_fields'].items():
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
                    body = {}
                    for name, info in endpoint['dto_fields'].items():
                        if name == field_name:
                            body[name] = invalid_value
                        else:
                            body[name] = info['sample_value']
                    
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
        
        # 4. 범위 초과 (400) - min/max validation
        if endpoint['method'] in ['POST', 'PUT', 'PATCH'] and endpoint['dto_fields']:
            for field_name, field_info in endpoint['dto_fields'].items():
                field_type = field_info.get('type', '')
                
                # 숫자 타입에서 max 초과
                if field_type in ['int', 'Integer', 'long', 'Long'] and field_info.get('max'):
                    body = {}
                    for name, info in endpoint['dto_fields'].items():
                        if name == field_name:
                            body[name] = field_info['max'] + 1000  # max 초과
                        else:
                            body[name] = info['sample_value']
                    
                    step = {
                        "name": f"{endpoint['name']} - Max Exceeded for {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Max Value Exceeded ({field_name})",
                        "description": f"실패 케이스 (400): 최대값 초과({field_name} > {field_info['max']})",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "max_exceeded", self.parser.controller_name.lower()],
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
                        'type': f'max_exceeded_{field_name}',
                        'status_code': 400
                    })
                
                # 숫자 타입에서 min 미만
                if field_type in ['int', 'Integer', 'long', 'Long'] and field_info.get('min') is not None:
                    body = {}
                    for name, info in endpoint['dto_fields'].items():
                        if name == field_name:
                            body[name] = field_info['min'] - 1000  # min 미만
                        else:
                            body[name] = info['sample_value']
                    
                    step = {
                        "name": f"{endpoint['name']} - Min Not Met for {field_name}",
                        "method": endpoint['method'],
                        "path": path,
                        "body": body,
                        "assertions": [
                            {"field": "status", "operator": "eq", "value": 400}
                        ]
                    }
                    
                    self._add_headers(step, endpoint)
                    
                    scenario = {
                        "name": f"{endpoint['name']} - Min Value Not Met ({field_name})",
                        "description": f"실패 케이스 (400): 최소값 미만({field_name} < {field_info['min']})",
                        "host": "default",
                        "tags": ["failure", "validation", "400", "min_not_met", self.parser.controller_name.lower()],
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
                        'type': f'min_not_met_{field_name}',
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
            
            step = {
                "name": f"{endpoint['name']} - Invalid ID",
                "method": endpoint['method'],
                "path": invalid_path,
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 404}
                ]
            }
            
            if endpoint['method'] == 'PUT' and endpoint['dto_fields']:
                body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
                step['body'] = body
            
            # Query 파라미터 추가 (GET, DELETE에도 있을 수 있음)
            query_params = {}
            if endpoint['query_params']:
                for param in endpoint['query_params']:
                    param_name = param['name'] if isinstance(param, dict) else param
                    param_type = param['type'] if isinstance(param, dict) else 'String'
                    query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
            
            # ModelAttribute 필드를 query parameter로 추가
            if endpoint.get('model_attribute_fields'):
                for field_name, field_info in endpoint['model_attribute_fields'].items():
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
        
        expected_status = 200
        if endpoint['method'] == 'POST':
            expected_status = 201
        
        assertions.append({
            "field": "status",
            "operator": "eq",
            "value": expected_status
        })
        
        if endpoint['method'] in ['GET', 'POST']:
            assertions.append({
                "field": "body",
                "operator": "exists"
            })
        
        if endpoint['method'] == 'POST':
            assertions.append({
                "field": "body.id",
                "operator": "exists"
            })
        
        # DTO 필드 기반 검증 추가
        if endpoint['method'] == 'POST' and endpoint['dto_fields']:
            for field_name in list(endpoint['dto_fields'].keys())[:2]:  # 처음 2개 필드만
                assertions.append({
                    "field": f"body.{field_name}",
                    "operator": "exists"
                })
        
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
        create_body = {name: info['sample_value'] for name, info in post_endpoint['dto_fields'].items()}
        create_step = {
            "name": "1. 리소스 생성",
            "method": "POST",
            "path": self._replace_path_variables(post_endpoint['path'], post_endpoint),
            "body": create_body,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 201},
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
            update_body = {name: f"{info['sample_value']}_updated" if isinstance(info['sample_value'], str) else info['sample_value'] 
                          for name, info in put_endpoint['dto_fields'].items()}
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
                body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
                step['body'] = body
            
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
        path = self._replace_path_variables(endpoint['path'], endpoint)
        
        step = {
            "name": endpoint['name'],
            "method": endpoint['method'],
            "path": path,
            "assertions": [
                {"field": "status", "operator": "eq", "value": 200},
                {"field": "response_time", "operator": "lt", "value": 1000}  # 1초 이내
            ]
        }
        
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
                body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
                step['body'] = body
            
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
    
    def _write_scenario(self, filepath: str, data: Dict[str, Any]):
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
        
        # 파일 경로에서 폴더명 추출해서 표시
        path_obj = Path(filepath)
        folder_name = path_obj.parent.name
        if folder_name != 'scenario':
            print(f"  ✓ {folder_name}/{path_obj.name}")
        else:
            print(f"  ✓ {path_obj.name}")
    
    def _clean_dict(self, data: Any) -> Any:
        """Remove None values and empty dicts/lists recursively"""
        if isinstance(data, dict):
            return {k: self._clean_dict(v) for k, v in data.items() if v is not None and v != {} and v != []}
        elif isinstance(data, list):
            return [self._clean_dict(item) for item in data]
        else:
            return data


def process_directory(controller_dir: str, output_dir: str, context_path: str = "", auth_bearer_token: str = "", auth_basic_token: str = "", custom_headers: dict = None, auth_annotations: list = None, auth_mode: str = "include", continue_on_error: bool = False, environment: str = "", output_format: str = 'yaml'):
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
        
        parser = JavaControllerParser(controller_file, context_path, auth_annotations, auth_mode)
        parser.parse()
        
        print(f"📊 발견된 엔드포인트: {len(parser.endpoints)}개")
        
        if not parser.endpoints:
            print("⚠️  엔드포인트를 찾을 수 없습니다. 건너뜁니다.")
            continue
        
        generator = ScenarioGenerator(parser, output_dir, auth_bearer_token, auth_basic_token, custom_headers or {}, continue_on_error, environment, auth_annotations or [], output_format)
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
        choices=['include', 'exclude'],
        default='include',
        help='''인증 적용 모드 선택:
        - include (기본값): auth-annotations에 지정된 어노테이션이 있는 메서드만 인증 필요
        - exclude: 기본적으로 모든 메서드에 인증 필요, auth-annotations에 지정된 어노테이션이 있는 메서드만 인증 불필요
        (예: AOP로 전역 인증이 적용되고 @NoAuth, @PermitAll 같은 어노테이션으로 인증 제외하는 경우)'''
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
        process_directory(args.controller_path, args.output, args.context_path, args.auth_bearer_token, args.auth_basic_token, custom_headers, args.auth_annotations, args.auth_mode, args.continue_on_error, args.environment, args.format)
    elif args.controller_path.endswith('.java'):
        java_parser = JavaControllerParser(args.controller_path, args.context_path, args.auth_annotations, args.auth_mode)
        java_parser.parse()
        
        print(f"📊 발견된 엔드포인트: {len(java_parser.endpoints)}개")
        
        if not java_parser.endpoints:
            print("⚠️  엔드포인트를 찾을 수 없습니다")
            return
        
        generator = ScenarioGenerator(java_parser, args.output, args.auth_bearer_token, args.auth_basic_token, custom_headers, args.continue_on_error, args.environment, args.auth_annotations or [], args.format)
        generator.generate()
    else:
        print("❌ 자바 파일(.java) 또는 디렉토리만 지원됩니다")
        return
    
    print("\n" + "="*80)
    print("🎉 모든 시나리오 생성 완료!")
    print("="*80)


if __name__ == '__main__':
    main()
