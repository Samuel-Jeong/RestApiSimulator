# JSON Pre-request Configuration (간편 모드)

## 개요

Python 코드 없이 **JSON만으로 Pre-request를 정의**할 수 있습니다.
Postman의 Pre-request Scripts보다 훨씬 간단하고 직관적입니다.

## 왜 JSON 방식인가?

### Postman Pre-request Script의 문제점
```javascript
// Postman: 복잡하고 어려움
pm.sendRequest({
    url: pm.environment.get('API_URL') + '/auth',
    method: 'POST',
    header: {...},
    body: {...}
}, function (err, res) {
    if (err) { console.log(err); return; }
    const data = res.json();
    pm.environment.set("token", data.token);
});
```

### REST API Simulator: 간단한 JSON
```json
{
  "name": "Get Auth Token",
  "steps": [{
    "name": "Login",
    "method": "POST",
    "url": "{{env.API_URL}}/auth",
    "body": {"username": "{{env.username}}"},
    "extract": {"token": "token"}
  }]
}
```

## 기본 구조

```json
{
  "name": "Pre-request Configuration Name",
  "description": "Optional description",
  "steps": [
    {
      "name": "Step name",
      "method": "POST|GET|PUT|PATCH|DELETE",
      "url": "{{env.base_url}}/api/endpoint",
      "headers": {"Key": "Value"},
      "body": {"key": "value"},
      "extract": {"variable_name": "json.path"}
    }
  ]
}
```

## 파일 위치

```
projects/
  your_project/
    package_library/
      pre_request.json    ← 여기에 저장
```

## 기본 사용법

### 1. 간단한 인증 토큰 받기

```json
{
  "name": "Get Auth Token",
  "description": "로그인하여 인증 토큰 받기",
  "steps": [
    {
      "name": "Login",
      "method": "POST",
      "url": "{{env.base_url}}/api/v1/auth/login",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "username": "{{env.username}}",
        "password": "{{env.password}}"
      },
      "extract": {
        "auth_token": "data.token",
        "user_id": "data.user.id"
      }
    }
  ]
}
```

**환경 변수 (env/development.json)**
```json
{
  "name": "development",
  "variables": {
    "base_url": "https://api.dev.example.com",
    "username": "testuser",
    "password": "testpass123"
  }
}
```

**결과**
- `auth_token` 변수에 토큰 저장
- `user_id` 변수에 사용자 ID 저장
- 시나리오에서 `{{auth_token}}`, `{{user_id}}` 사용 가능

### 2. 여러 단계 실행 (Chain Requests)

```json
{
  "name": "Multi-step Authentication",
  "description": "토큰 받고 → 사용자 정보 조회 → 권한 확인",
  "steps": [
    {
      "name": "1. Get Token",
      "method": "POST",
      "url": "{{env.base_url}}/api/v1/auth/token",
      "body": {
        "apiKey": "{{env.api_key}}"
      },
      "extract": {
        "auth_token": "data.token"
      }
    },
    {
      "name": "2. Get User Info",
      "method": "GET",
      "url": "{{env.base_url}}/api/v1/user/me",
      "headers": {
        "Authorization": "Bearer {{auth_token}}"
      },
      "extract": {
        "user_id": "data.id",
        "user_role": "data.role"
      }
    },
    {
      "name": "3. Get Permissions",
      "method": "GET",
      "url": "{{env.base_url}}/api/v1/users/{{user_id}}/permissions",
      "headers": {
        "Authorization": "Bearer {{auth_token}}"
      },
      "extract": {
        "permissions": "data.permissions"
      }
    }
  ]
}
```

**특징**
- 각 단계의 결과를 다음 단계에서 사용 가능
- `{{auth_token}}`, `{{user_id}}` 등 이전 단계에서 추출한 변수 자동 사용

## 필드 상세 설명

### Step 필드

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `name` | ✅ | string | 단계 이름 (로그에 표시) |
| `method` | ✅ | string | HTTP 메서드 (GET, POST, PUT, PATCH, DELETE) |
| `url` | ✅ | string | 요청 URL (변수 사용 가능) |
| `headers` | ❌ | object | 요청 헤더 |
| `query_params` | ❌ | object | 쿼리 파라미터 |
| `body` | ❌ | any | 요청 본문 (JSON 자동 직렬화) |
| `timeout` | ❌ | number | 타임아웃 (초, 기본값: 30) |
| `extract` | ❌ | object | 응답에서 추출할 변수 |

### Extract (변수 추출)

응답 JSON에서 값을 추출하여 변수로 저장합니다.

**형식**
```json
{
  "extract": {
    "변수명": "JSON 경로"
  }
}
```

**JSON 경로 예제**

응답:
```json
{
  "status": "success",
  "data": {
    "token": "abc123",
    "user": {
      "id": 100,
      "name": "John",
      "email": "john@example.com"
    },
    "roles": ["admin", "user"]
  }
}
```

추출:
```json
{
  "extract": {
    "token": "data.token",              // "abc123"
    "user_id": "data.user.id",          // 100
    "user_name": "data.user.name",      // "John"
    "user_email": "data.user.email",    // "john@example.com"
    "first_role": "data.roles.0",       // "admin" (배열 인덱스)
    "all_roles": "data.roles"           // ["admin", "user"]
  }
}
```

### 변수 사용

Pre-request에서 사용 가능한 변수:

1. **환경 변수**: `{{env.variable_name}}`
2. **이전 단계 결과**: `{{variable_name}}`
3. **시나리오 변수**: `{{variable_name}}`

## 실제 사용 예제

### 예제 1: WPM 사용자 인증

**파일**: `projects/wpm/workercontroller/package_library/pre_request.json`

```json
{
  "name": "WPM User Authentication",
  "description": "사용자 인증 토큰 발급",
  "steps": [
    {
      "name": "Get User Cert Token",
      "method": "POST",
      "url": "{{env.WPM_DEVICE_APP_URL}}/api/v1/token/extrainfo/create",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{env.testAuthToken}}"
      },
      "body": {
        "userId": "{{env.UserId}}",
        "userName": "{{env.UserName}}"
      },
      "extract": {
        "USER_CERT_TOKEN": "data"
      }
    }
  ]
}
```

**환경 변수**: `env/development.json`
```json
{
  "name": "development",
  "variables": {
    "WPM_DEVICE_APP_URL": "https://dev-workplace.adtcapson.co.kr:32002",
    "testAuthToken": "gA7Y/2tUhPf/9KEWz/w8Kbpdol6W1PBwW6QkIQ63lLinug0=",
    "UserId": "123",
    "UserName": "testuser"
  }
}
```

**시나리오에서 사용**:
```json
{
  "name": "Worker API Test",
  "steps": [
    {
      "name": "Get Worker Info",
      "method": "GET",
      "path": "/api/v1/worker/{{env.UserId}}",
      "headers": {
        "Authorization": "Bearer {{USER_CERT_TOKEN}}"
      }
    }
  ]
}
```

### 예제 2: 복잡한 인증 플로우

```json
{
  "name": "Complete Auth Flow",
  "description": "API Key → Token → User Info → Permissions",
  "steps": [
    {
      "name": "1. Exchange API Key for Token",
      "method": "POST",
      "url": "{{env.auth_url}}/exchange",
      "body": {
        "apiKey": "{{env.api_key}}",
        "clientId": "{{env.client_id}}"
      },
      "extract": {
        "access_token": "access_token",
        "refresh_token": "refresh_token",
        "expires_in": "expires_in"
      }
    },
    {
      "name": "2. Get Current User",
      "method": "GET",
      "url": "{{env.base_url}}/api/v1/user/me",
      "headers": {
        "Authorization": "Bearer {{access_token}}"
      },
      "extract": {
        "user_id": "id",
        "user_email": "email",
        "tenant_id": "tenant.id"
      }
    },
    {
      "name": "3. Get User Permissions",
      "method": "GET",
      "url": "{{env.base_url}}/api/v1/tenants/{{tenant_id}}/users/{{user_id}}/permissions",
      "headers": {
        "Authorization": "Bearer {{access_token}}"
      },
      "extract": {
        "permissions": "permissions",
        "role": "role.name"
      }
    }
  ]
}
```

## Python Pre-request와 비교

### JSON Pre-request (권장)
✅ 간단하고 직관적  
✅ 코드 작성 불필요  
✅ 오류 가능성 낮음  
✅ 선언적 구조  
✅ 버전 관리 용이  

**사용 케이스**:
- API 호출하여 토큰 받기
- 여러 API 순차 호출
- 응답에서 값 추출

### Python Pre-request (고급)
✅ 복잡한 로직 가능  
✅ 외부 라이브러리 사용  
✅ 조건문, 반복문 등 프로그래밍  

**사용 케이스**:
- 복잡한 계산
- 파일 읽기/쓰기
- 외부 시스템 연동
- 암호화/복호화

## 우선순위

같은 폴더에 두 파일이 모두 있으면:
1. `pre_request.json` (JSON 방식 - 우선)
2. `pre_request.py` (Python 방식 - 대체)

## 실행 로그

Pre-request 실행 시 다음과 같은 로그가 표시됩니다:

```
Environment: development
Pre-request: pre_request.json

✅ Pre-request config 'WPM User Authentication' executed successfully
   Executing: Get User Cert Token
   → POST https://dev-workplace.adtcapson.co.kr:32002/api/v1/token/extrainfo/create
   ← Status: 200
   ✓ Extracted USER_CERT_TOKEN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Extracted variables: USER_CERT_TOKEN
```

## 문제 해결

### 변수가 추출되지 않음

**확인사항**:
1. JSON 경로가 정확한지 확인
2. 응답 구조 확인 (로그에서 Status 확인)
3. 경로는 대소문자 구분

**예시**:
```json
// 응답
{"Data": {"Token": "abc"}}  // 대문자 주의!

// 올바른 경로
"extract": {"token": "Data.Token"}

// 잘못된 경로
"extract": {"token": "data.token"}  // ❌
```

### 이전 단계 변수를 다음 단계에서 사용 불가

**해결**:
- `extract`로 추출한 변수는 자동으로 다음 단계에서 사용 가능
- 변수 이름 확인 (`{{auth_token}}` vs `{{authToken}}`)

### 환경 변수가 치환되지 않음

**확인사항**:
1. Environment가 선택되었는지 확인 (`env:development`)
2. 변수명이 정확한지 확인 (`{{env.api_key}}`)
3. `env/` 폴더에 파일이 있는지 확인

## 모범 사례

### 1. 단계별 명확한 이름

```json
{
  "steps": [
    {"name": "1. Get Auth Token", ...},
    {"name": "2. Get User Profile", ...},
    {"name": "3. Verify Permissions", ...}
  ]
}
```

### 2. 의미있는 변수명

```json
{
  "extract": {
    "auth_token": "data.token",        // ✅ 명확함
    "user_id": "data.user.id",         // ✅ 명확함
    "token": "data.token",             // ⚠️ 모호함
    "id": "data.user.id"               // ⚠️ 모호함
  }
}
```

### 3. 타임아웃 설정

느린 API는 타임아웃 늘리기:

```json
{
  "name": "Slow API Call",
  "method": "POST",
  "url": "{{env.base_url}}/slow-endpoint",
  "timeout": 60  // 60초
}
```

### 4. 에러 핸들링

Pre-request가 실패해도 시나리오는 계속 진행됩니다.
실패 시 추출된 변수가 없어 시나리오에서 에러 발생 가능.

**대처 방법**:
- 환경 변수에 기본값 설정
- 시나리오 assertion으로 확인

## 전환 가이드: Postman → REST API Simulator

### Postman
```javascript
pm.sendRequest({
    url: pm.environment.get('BASE_URL') + '/auth',
    method: 'POST',
    header: {
        'Content-Type': 'application/json',
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            username: pm.environment.get('USERNAME'),
            password: pm.environment.get('PASSWORD')
        })
    }
}, function (err, res) {
    if (err) {
        console.log(err);
        return;
    }
    const data = res.json();
    if (data && data.token) {
        pm.environment.set("AUTH_TOKEN", data.token);
        pm.environment.set("USER_ID", data.user.id);
    }
});
```

### REST API Simulator
```json
{
  "name": "Get Auth Token",
  "steps": [
    {
      "name": "Login",
      "method": "POST",
      "url": "{{env.BASE_URL}}/auth",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "username": "{{env.USERNAME}}",
        "password": "{{env.PASSWORD}}"
      },
      "extract": {
        "AUTH_TOKEN": "token",
        "USER_ID": "user.id"
      }
    }
  ]
}
```

**차이점**:
- ❌ JavaScript 콜백 제거
- ❌ 에러 핸들링 코드 불필요
- ❌ `JSON.stringify()` 불필요
- ✅ 선언적 구조
- ✅ 더 짧고 명확함

## 예제 파일

프로젝트 예제:
- `projects/example/package_library/pre_request.json`
- `projects/wpm/workercontroller/package_library/pre_request.json`

## 추가 기능

### Query Parameters

```json
{
  "name": "Search API",
  "method": "GET",
  "url": "{{env.base_url}}/api/search",
  "query_params": {
    "q": "{{env.search_term}}",
    "limit": 10,
    "offset": 0
  }
}
```

### Headers

```json
{
  "headers": {
    "Authorization": "Bearer {{env.api_token}}",
    "X-API-Key": "{{env.api_key}}",
    "X-Tenant-ID": "{{env.tenant_id}}",
    "Accept": "application/json"
  }
}
```

### 배열 처리

```json
// 응답: {"users": [{"id": 1}, {"id": 2}]}

{
  "extract": {
    "first_user_id": "users.0.id",     // 1
    "second_user_id": "users.1.id",    // 2
    "all_users": "users"               // [{"id": 1}, {"id": 2}]
  }
}
```

## 요약

| 항목 | 설명 |
|------|------|
| **파일 위치** | `package_library/pre_request.json` |
| **형식** | JSON |
| **목적** | 시나리오 실행 전 API 호출 및 변수 추출 |
| **장점** | 간단, 직관적, 오류 적음 |
| **사용** | 토큰 발급, 다단계 인증, 데이터 준비 |
| **대안** | `pre_request.py` (Python 스크립트) |

JSON Pre-request로 90% 이상의 사용 케이스를 커버할 수 있습니다!
