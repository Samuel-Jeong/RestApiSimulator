# 에러 표시 개선 (Error Display Enhancement)

## 개요
시나리오 실행 결과에서 **Package Library 실행 실패**와 **API 요청 실패**를 명확하게 구분하여 표시하도록 개선

## 변경된 파일

### 1. `app/core/json_pre_request_engine.py`
**변경 내용:**
- Config 실행 실패 시 명확한 에러 메시지 출력
- Step 실행 실패 시 상세한 에러 정보 표시

**출력 형식:**
```
============================================================
❌ PACKAGE LIBRARY EXECUTION FAILED
============================================================
Config File: pre_request.json
Error Type:  ConnectionError
Error:       Connection refused
============================================================
```

### 2. `app/core/pre_request_engine.py`
**변경 내용:**
- Script 실행 실패 시 명확한 에러 메시지와 Traceback 출력

**출력 형식:**
```
============================================================
❌ PACKAGE LIBRARY SCRIPT EXECUTION FAILED
============================================================
Script File: pre_request.py
Error Type:  SyntaxError
Error:       invalid syntax

Traceback:
------------------------------------------------------------
[상세 Traceback 정보]
============================================================
```

### 3. `app/core/scenario_engine.py`
**변경 내용:**
- Pre-request 실행 전 로그 출력 추가
- 에러 타입별 Prefix 추가:
  - `[PACKAGE_LIBRARY_ERROR]` - Package Library 실행 실패
  - `[API_REQUEST_ERROR]` - API 요청 실패

**출력 형식:**
```
🔧 Executing package library config: pre_request.json
------------------------------------------------------------
[실행 로그]
```

### 4. `app/ui/app.py`
**변경 내용:**
- 결과 상세 화면에서 에러 타입별 명확한 구분 표시
- Package Library 에러 발생 시 체크리스트 제공
- 실행 로그에서 에러 종류 명확히 표시

**표시 형식:**

#### Step 상세 로그:
```
===========================================================
❌ PACKAGE LIBRARY EXECUTION FAILED
===========================================================
Error: pre_request.json: Connection refused
===========================================================
```

#### Step 요약:
```
✗ 1. Get User Info - 0.0ms (HTTP N/A)
   ❌ PACKAGE LIBRARY: pre_request.json: Connection refused
```

#### 전체 실패 화면:
```
╔═ TEST FAILED - scenario_name ════════════════════════╗

❌ Package Library Execution Failed

Error: pre_request.json: Connection refused

────────────────────────────────────────────────────────

Please check:
• Package library script/config syntax
• Pre-request API endpoint availability
• Environment variables
• Authentication tokens
```

## 사용 예시

### 정상 케이스
```
🔧 Executing package library config: wpm-get-user-info.json
------------------------------------------------------------
   Executing: Get User Info
   → POST https://api.example.com/auth
   ← Status: 200
   ✓ Extracted USER_CERT_TOKEN: eyJ0eXAiOiJKV1QiLCJhbGciOi...
✅ Pre-request config 'wpm-get-user-info.json' executed successfully
   Extracted variables: USER_CERT_TOKEN
```

### Package Library 실패 케이스
```
🔧 Executing package library config: wpm-get-user-info.json
------------------------------------------------------------
   Executing: Get User Info
   → POST https://api.example.com/auth

   ────────────────────────────────────────────────────────
   ❌ PACKAGE LIBRARY STEP FAILED
   ────────────────────────────────────────────────────────
   Step Name:   Get User Info
   Request:     POST https://api.example.com/auth
   Error Type:  ConnectionError
   Error:       Connection refused
   ────────────────────────────────────────────────────────

============================================================
❌ PACKAGE LIBRARY EXECUTION FAILED
============================================================
Config File: wpm-get-user-info.json
Error Type:  Exception
Error:       Connection refused
============================================================
```

### API 요청 실패 케이스
```
✗ 2. Get Device List - 0.0ms (HTTP N/A)
   ⚠ API Error: Connection timeout
```

## 장점

1. **명확한 구분**: Package Library 오류와 API 오류를 즉시 구분 가능
2. **빠른 디버깅**: 오류 타입별로 적절한 체크리스트 제공
3. **상세한 정보**: Traceback 및 에러 타입 정보로 원인 파악 용이
4. **시각적 강조**: 구분선과 이모지를 사용한 명확한 시각적 구분
5. **일관성**: 모든 출력 지점에서 동일한 형식 사용

## 테스트 방법

### 1. Package Library 실패 테스트
```bash
# package_library/pre_request.json 파일에서 잘못된 URL 설정
{
  "name": "Test Pre-request",
  "steps": [{
    "name": "Test",
    "method": "GET",
    "url": "https://invalid-url-that-does-not-exist.com/api"
  }]
}
```

### 2. API 요청 실패 테스트
```bash
# 시나리오 파일에서 잘못된 API 엔드포인트 설정
steps:
  - name: Test API
    method: GET
    path: /invalid/endpoint
```

### 3. 정상 실행 테스트
```bash
# 정상적인 시나리오 실행하여 개선된 로그 확인
```

## 호환성

- **하위 호환성**: 기존 에러 메시지 형식도 지원 (Fallback 로직 포함)
- **Prefix 기반 구분**: 새로운 에러는 `[PACKAGE_LIBRARY_ERROR]` 또는 `[API_REQUEST_ERROR]` prefix 사용
- **기존 코드 영향 없음**: 에러 메시지 형식 변경만으로 기존 로직 유지

## 날짜
2026-01-28
