# Package Library - Basic Auth 자동 인코딩

## 개요

Package Library 파일에서 `Authorization` 헤더를 `Basic user:password` 형식으로 작성하면 자동으로 Base64 인코딩하여 HTTP 요청을 수행합니다.

## 기능

### 자동 감지 및 인코딩

Package library 실행 시, 다음 조건을 만족하면 자동으로 Base64 인코딩합니다:

1. `Authorization` 헤더가 존재
2. `Basic ` 으로 시작 (공백 포함)
3. 크레덴셜에 `:` (콜론)이 포함되어 있음 (즉, `user:password` 형식)

### 안전한 처리

- **이미 인코딩된 값**: 다시 인코딩하지 않음 (콜론이 없으면 이미 인코딩된 것으로 간주)
- **다른 인증 방식**: `Bearer`, `Digest` 등 다른 인증 방식은 영향받지 않음
- **에러 방지**: 잘못된 형식이어도 에러 없이 원본 값 사용

## 사용 방법

### 1. Package Library 파일 작성

`projects/capshome/package_library/capshome-user-auth.json`:

```json
{
  "name": "CAPSHOME User Authentication",
  "description": "Get user certification token before test execution",
  "steps": [
    {
      "name": "Get User Cert Token",
      "method": "POST",
      "url": "{{env.HOST}}/api/v2/user/login",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Basic {{env.USER_ID}}:{{env.USER_PW}}",
        "X-Auth-Server": "CAPSHOME"
      },
      "body": {
        "fcmToken": "{{env.FCM_TOKEN}}",
        "osType": "{{env.OS_TYPE}}"
      },
      "extract": {
        "USER_CERT_TOKEN": "data"
      }
    }
  ]
}
```

### 2. 환경 변수 설정

`projects/capshome/env/development.json`:

```json
{
  "params": {
    "HOST": "https://api.example.com",
    "USER_ID": "kimmo",
    "USER_PW": "11qqaa..",
    "FCM_TOKEN": "test-fcm-token",
    "OS_TYPE": "iOS"
  }
}
```

### 3. 시나리오 생성 스크립트

```bash
python3 generate_scenario.py \
  /path/to/SgiController.java \
  --output /path/to/projects/capshome \
  --environment development \
  --auth-mode all \
  --default-auth bearer \
  --default-auth-token "{{USER_CERT_TOKEN}}" \
  --default-auth-library "capshome-user-auth.json" \
  --context-path /api/v2/user \
  --format yaml
```

## 처리 과정

### Step 1: 변수 치환

Library 파일:
```json
"Authorization": "Basic {{env.USER_ID}}:{{env.USER_PW}}"
```

환경 변수 치환 후:
```
Authorization: Basic kimmo:11qqaa..
```

### Step 2: 자동 Base64 인코딩

시스템이 자동으로 감지하고 인코딩:
```
Authorization: Basic a2ltbW86MTFxcWFhLi4=
```

### Step 3: HTTP 요청

인코딩된 헤더로 실제 HTTP 요청 수행:
```http
POST /api/v2/user/login HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Basic a2ltbW86MTFxcWFhLi4=
X-Auth-Server: CAPSHOME

{
  "fcmToken": "test-fcm-token",
  "osType": "iOS"
}
```

## 예시

### 정상 인코딩되는 경우

| 입력 | 출력 | 설명 |
|------|------|------|
| `Basic user:pass` | `Basic dXNlcjpwYXNz` | ✅ 자동 인코딩 |
| `Basic admin:password123` | `Basic YWRtaW46cGFzc3dvcmQxMjM=` | ✅ 자동 인코딩 |
| `Basic kimmo:11qqaa..` | `Basic a2ltbW86MTFxcWFhLi4=` | ✅ 자동 인코딩 |
| `Basic {{env.USER}}:{{env.PW}}` | 변수 치환 후 인코딩 | ✅ 변수 치환 + 자동 인코딩 |

### 인코딩하지 않는 경우

| 입력 | 출력 | 설명 |
|------|------|------|
| `Basic dXNlcjpwYXNz` | `Basic dXNlcjpwYXNz` | ✅ 이미 인코딩됨 (콜론 없음) |
| `Bearer eyJhbGc...` | `Bearer eyJhbGc...` | ✅ Bearer 토큰 (영향 없음) |
| `Digest username="admin"` | `Digest username="admin"` | ✅ 다른 인증 방식 |

## 기술적 세부사항

### 구현 위치

- **파일**: `app/core/json_pre_request_engine.py`
- **메서드**: `_process_auth_header()`

### 로직

```python
def _process_auth_header(self, auth_value: str) -> str:
    """Basic Auth 자동 인코딩"""
    if not isinstance(auth_value, str):
        return auth_value
    
    # Basic Auth인지 확인
    if not auth_value.startswith('Basic '):
        return auth_value
    
    credentials = auth_value[6:].strip()  # "Basic " 제거
    
    # 콜론이 있으면 아직 인코딩 안된 것 -> 인코딩 필요
    if ':' in credentials:
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    # 이미 인코딩됨 또는 잘못된 형식 -> 그대로 반환
    return auth_value
```

### 테스트

테스트 실행:
```bash
python3 test_basic_auth_encoding.py
python3 test_unit_basic_auth.py
```

## 주의사항

### 보안

- **환경 변수 사용 권장**: 하드코딩된 비밀번호 대신 `{{env.USER_PW}}` 사용
- **Git 제외**: 환경 파일 (`env/`) 을 `.gitignore`에 추가
- **Base64는 암호화 아님**: Base64는 인코딩일 뿐 암호화가 아니므로 HTTPS 사용 필수

### 제한사항

- **콜론 감지 방식**: 콜론(`:`)의 존재로 인코딩 여부를 판단하므로, 매우 드물게 오작동 가능
- **단방향 처리**: 한 번 인코딩하면 자동으로 디코딩하지 않음

### 모범 사례

1. **변수 사용**: 직접 비밀번호 입력 대신 환경 변수 사용
2. **환경별 분리**: development, staging, production 환경별로 다른 env 파일 관리
3. **버전 관리**: env 파일은 Git에 커밋하지 않고, env.example 파일만 커밋

## 관련 문서

- [USAGE.md](./USAGE.md) - 전체 사용법
- [README.md](./README.md) - 시나리오 생성기 개요
- [AUTH_MODE_GUIDE.md](./AUTH_MODE_GUIDE.md) - 인증 모드 가이드

## 변경 이력

- **2026-02-03**: Basic Auth 자동 인코딩 기능 추가
