# Package Library에서 Basic Auth 사용 가이드

Package Library (pre-request 스크립트)에서 Basic Authentication을 사용하는 방법입니다.

## 방법 1: Base64 인코딩된 토큰 사용 (권장)

### 장점
- 간단하고 직관적
- 대부분의 REST API 클라이언트와 호환
- 추가 변환 없이 바로 사용

### 사용 방법

#### 1단계: Base64 인코딩 생성

**터미널에서:**
```bash
echo -n "username:password" | base64
```

**예시:**
```bash
echo -n "kimmo:11qqaa.." | base64
# 결과: a2ltbW86MTFxcWFhLi4=
```

**Python에서:**
```python
import base64
credentials = "username:password"
encoded = base64.b64encode(credentials.encode()).decode()
print(encoded)
```

**온라인 도구:**
- https://www.base64encode.org/

#### 2단계: 환경 변수에 추가

`env/development.json`:
```json
{
  "name": "development",
  "variables": {
    "AUTH_BASIC_TOKEN": "a2ltbW86MTFxcWFhLi4=",
    "AUTH_BASIC_USER_NAME": "kimmo",
    "AUTH_BASIC_PASSWORD": "11qqaa.."
  }
}
```

#### 3단계: Package Library에서 사용

`package_library/your-auth.json`:
```json
{
  "name": "Basic Auth Example",
  "description": "Using Basic Authentication",
  "steps": [
    {
      "name": "Authenticate",
      "method": "POST",
      "url": "{{env.AUTH_APP_URL}}",
      "headers": {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic {{env.AUTH_BASIC_TOKEN}}"
      },
      "extract": {
        "ACCESS_TOKEN": "access_token"
      }
    }
  ]
}
```

---

## 방법 2: auth 객체 사용 (동적)

### 장점
- username과 password를 평문으로 관리
- 런타임에 자동으로 Base64 인코딩
- 가독성 좋음

### 사용 방법

#### 1단계: 환경 변수 설정

`env/development.json`:
```json
{
  "name": "development",
  "variables": {
    "AUTH_BASIC_USER_NAME": "kimmo",
    "AUTH_BASIC_PASSWORD": "11qqaa.."
  }
}
```

#### 2단계: Package Library에서 auth 객체 사용

`package_library/your-auth-dynamic.json`:
```json
{
  "name": "Basic Auth Dynamic Example",
  "description": "Using username:password format",
  "steps": [
    {
      "name": "Authenticate",
      "method": "POST",
      "url": "{{env.AUTH_APP_URL}}",
      "headers": {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      "auth": {
        "type": "basic",
        "username": "{{env.AUTH_BASIC_USER_NAME}}",
        "password": "{{env.AUTH_BASIC_PASSWORD}}"
      },
      "extract": {
        "ACCESS_TOKEN": "access_token"
      }
    }
  ]
}
```

**참고:** `auth` 객체를 사용하면 시스템이 자동으로:
1. `username:password`를 결합
2. Base64로 인코딩
3. `Authorization: Basic {encoded}` 헤더 추가

---

## 방법 3: 시나리오에서 직접 사용

Package Library를 사용하지 않고 시나리오에서 직접 Basic Auth 사용:

### 시나리오 파일

`scenario/success/login_success.yaml`:
```yaml
name: Login with Basic Auth
description: Direct Basic Authentication in scenario
host: default
steps:
  - name: Login
    method: POST
    path: /oauth/token
    headers:
      Content-Type: application/x-www-form-urlencoded
      Authorization: Basic {{env.AUTH_BASIC_TOKEN}}
    body:
      grant_type: client_credentials
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body.access_token
        operator: exists
    extract:
      ACCESS_TOKEN: body.access_token
```

---

## 실제 사용 예제

### OAuth 2.0 Client Credentials with Basic Auth

많은 OAuth 2.0 서버가 Client ID와 Client Secret을 Basic Auth로 전달합니다.

#### 환경 설정

`env/development.json`:
```json
{
  "name": "development",
  "variables": {
    "AUTH_APP_URL": "https://auth-server.com/oauth/token?grant_type=client_credentials",
    "CLIENT_ID": "my-client-id",
    "CLIENT_SECRET": "my-client-secret",
    "AUTH_BASIC_TOKEN": "bXktY2xpZW50LWlkOm15LWNsaWVudC1zZWNyZXQ="
  }
}
```

**Base64 생성:**
```bash
echo -n "my-client-id:my-client-secret" | base64
# bXktY2xpZW50LWlkOm15LWNsaWVudC1zZWNyZXQ=
```

#### Package Library

`package_library/oauth-client-credentials.json`:
```json
{
  "name": "OAuth Client Credentials",
  "description": "Get access token using client credentials",
  "steps": [
    {
      "name": "Get Access Token",
      "method": "POST",
      "url": "{{env.AUTH_APP_URL}}",
      "headers": {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic {{env.AUTH_BASIC_TOKEN}}"
      },
      "assertions": [
        {
          "field": "status",
          "operator": "eq",
          "value": 200
        },
        {
          "field": "body.access_token",
          "operator": "exists"
        }
      ],
      "extract": {
        "ACCESS_TOKEN": "body.access_token",
        "TOKEN_TYPE": "body.token_type",
        "EXPIRES_IN": "body.expires_in"
      }
    }
  ]
}
```

#### 시나리오에서 사용

`scenario/success/get_user_success.yaml`:
```yaml
name: Get User Info
description: Retrieve user information with OAuth token
host: default
pre_request_scripts:
  - oauth-client-credentials.json  # ← Package Library 실행
steps:
  - name: Get User Info
    method: GET
    path: /api/v1/users/me
    headers:
      Authorization: Bearer {{ACCESS_TOKEN}}  # ← 추출된 토큰 사용
    assertions:
      - field: status
        operator: eq
        value: 200
environment: development
```

---

## 보안 고려사항

### 1. 환경 파일 보안

`.gitignore`에 환경 파일 추가:
```gitignore
# 환경 설정 파일
**/env/*.json
!**/env/development.example.json

# Package Library (민감 정보 포함 가능)
**/package_library/*-local.json
```

### 2. 예제 템플릿 제공

`env/development.example.json`:
```json
{
  "name": "development",
  "variables": {
    "AUTH_APP_URL": "https://your-auth-server.com/oauth/token",
    "AUTH_BASIC_USER_NAME": "your-username",
    "AUTH_BASIC_PASSWORD": "your-password",
    "AUTH_BASIC_TOKEN": "base64-encoded-username:password"
  }
}
```

### 3. 암호화 (선택사항)

민감한 정보는 암호화하여 저장:
```bash
# 암호화
echo -n "my-secret-password" | openssl enc -aes-256-cbc -a

# 복호화
echo "encrypted-string" | openssl enc -aes-256-cbc -d -a
```

---

## 문제 해결

### Q1: "Unauthorized" 401 에러

**원인:**
- Base64 인코딩이 잘못됨
- username 또는 password가 틀림
- 공백이나 줄바꿈 포함

**해결:**
```bash
# -n 플래그로 줄바꿈 제거
echo -n "username:password" | base64

# 결과 확인
echo "a2ltbW86MTFxcWFhLi4=" | base64 -d
# 출력: kimmo:11qqaa..
```

### Q2: 특수문자 포함된 비밀번호

**문제:**
```bash
# 잘못된 방법 (특수문자 해석됨)
echo -n "user:p@ssw0rd!" | base64
```

**해결:**
```bash
# 방법 1: 작은따옴표 사용
echo -n 'user:p@ssw0rd!' | base64

# 방법 2: Python 사용
python3 -c "import base64; print(base64.b64encode(b'user:p@ssw0rd!').decode())"

# 방법 3: 이스케이프
echo -n "user:p\@ssw0rd\!" | base64
```

### Q3: 환경 변수가 치환되지 않음

**확인사항:**
1. 환경 파일 경로가 올바른지 확인
2. 변수명이 정확한지 확인 (`{{env.VARIABLE_NAME}}`)
3. JSON 형식이 올바른지 확인

```bash
# JSON 유효성 검사
cat env/development.json | python3 -m json.tool
```

---

## 추가 자료

- [RFC 7617 - HTTP Basic Authentication](https://tools.ietf.org/html/rfc7617)
- [Base64 인코딩 이해하기](https://en.wikipedia.org/wiki/Base64)
- [OAuth 2.0 Client Credentials Grant](https://oauth.net/2/grant-types/client-credentials/)
