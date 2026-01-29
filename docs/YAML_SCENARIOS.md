# YAML 시나리오 작성 가이드

## 기본 구조

```yaml
name: 시나리오 이름
description: 시나리오 설명
host: default
environment: development
tags:
  - tag1
  - tag2
continue_on_error: false
pre_request_scripts:
  - script1.json
variables:
  custom_var: value
steps:
  - name: Step 1
    method: GET
    path: /api/endpoint
```

## 필수 필드

```yaml
name: 시나리오 이름     # 필수
steps:                  # 필수 (최소 1개)
  - name: Step Name     # 필수
    method: GET         # 필수 (GET, POST, PUT, PATCH, DELETE)
    path: /api/path     # 필수
```

## 선택 필드

### 시나리오 레벨

```yaml
description: 시나리오 상세 설명
host: default                    # 호스트 설정 이름
environment: development         # 환경 이름
tags: [api, test, integration]   # 태그 목록
continue_on_error: true          # 에러 발생 시에도 계속 실행
pre_request_scripts:             # 사전 실행 스크립트
  - auth-setup.json
variables:                       # 시나리오 변수
  base_id: 1
  username: testuser
```

## 스텝 작성

### 기본 스텝

```yaml
steps:
  - name: Get User
    method: GET
    path: /api/users/1
```

### 헤더

```yaml
steps:
  - name: Authenticated Request
    method: GET
    path: /api/protected
    headers:
      Authorization: Bearer {{TOKEN}}
      Content-Type: application/json
      X-Custom-Header: value
```

### 쿼리 파라미터

```yaml
steps:
  - name: Search Users
    method: GET
    path: /api/users
    query_params:
      page: 1
      limit: 10
      sort: name
      filter: active
```

### 요청 본문 (Body)

```yaml
steps:
  - name: Create User
    method: POST
    path: /api/users
    body:
      username: testuser
      email: test@example.com
      age: 25
      active: true
      tags: [user, test]
```

### 타임아웃과 딜레이

```yaml
steps:
  - name: Slow Request
    method: GET
    path: /api/slow-endpoint
    timeout: 60              # 초 단위
    delay_before: 1.5        # 요청 전 대기 (초)
    delay_after: 0.5         # 요청 후 대기 (초)
```

### 재시도

```yaml
steps:
  - name: Flaky Endpoint
    method: GET
    path: /api/flaky
    retry: 3                 # 실패 시 3번 재시도
```

### 실패 시 건너뛰기

```yaml
steps:
  - name: Optional Step
    method: GET
    path: /api/optional
    skip_on_failure: true    # 실패해도 다음 스텝 계속
```

## Assertion (검증)

### 기본 검증

```yaml
assertions:
  - field: status
    operator: eq
    value: 200
```

### 연산자

```yaml
assertions:
  # 같음
  - field: status
    operator: eq
    value: 200
  
  # 같지 않음
  - field: body.status
    operator: ne
    value: error
  
  # 크기 비교
  - field: body.count
    operator: gt        # >
    value: 0
  
  - field: body.count
    operator: gte       # >=
    value: 1
  
  - field: body.count
    operator: lt        # <
    value: 100
  
  - field: body.count
    operator: lte       # <=
    value: 99
  
  # 포함
  - field: body.message
    operator: contains
    value: success
  
  - field: body.message
    operator: not_contains
    value: error
  
  # 존재 여부
  - field: body.user.id
    operator: exists
  
  # 배열 포함
  - field: body.tags
    operator: in
    value: important
  
  - field: body.tags
    operator: not_in
    value: deprecated
  
  # 정규식
  - field: body.email
    operator: regex
    value: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

### 중첩 필드 접근

```yaml
assertions:
  - field: body.user.id
    operator: exists
  
  - field: body.data.items[0].name
    operator: eq
    value: first
  
  - field: body.metadata.count
    operator: gt
    value: 0
```

### 커스텀 에러 메시지

```yaml
assertions:
  - field: status
    operator: eq
    value: 200
    message: "API should return 200 OK"
```

## 변수 사용

### 변수 추출

```yaml
steps:
  - name: Create User
    method: POST
    path: /api/users
    body:
      username: testuser
    extract:
      user_id: body.id
      token: body.auth_token
      created_at: body.createdAt
```

### 변수 참조

```yaml
steps:
  # 1단계: 변수 추출
  - name: Login
    method: POST
    path: /api/login
    body:
      username: admin
      password: secret
    extract:
      auth_token: body.token
  
  # 2단계: 추출한 변수 사용
  - name: Get Profile
    method: GET
    path: /api/profile
    headers:
      Authorization: Bearer {{auth_token}}
  
  # 3단계: Path에 변수 사용
  - name: Update User
    method: PUT
    path: /api/users/{{user_id}}
    body:
      name: Updated Name
  
  # 4단계: Body에 변수 사용
  - name: Create Comment
    method: POST
    path: /api/comments
    body:
      user_id: '{{user_id}}'
      content: Comment by {{username}}
```

### 환경 변수

```yaml
steps:
  - name: API Call
    method: GET
    path: /api/data
    headers:
      Authorization: Bearer {{env.API_TOKEN}}
      X-API-Key: '{{env.API_KEY}}'
    query_params:
      user: '{{env.TEST_USER_ID}}'
```

### 시나리오 변수

```yaml
# 시나리오 레벨에서 정의
variables:
  base_path: /api/v1
  user_id: 123
  test_email: test@example.com

steps:
  - name: Get User
    method: GET
    path: '{{base_path}}/users/{{user_id}}'
  
  - name: Update Email
    method: PUT
    path: '{{base_path}}/users/{{user_id}}'
    body:
      email: '{{test_email}}'
```

## 완전한 예제

### 단순 조회

```yaml
name: Get User API Test
description: 사용자 조회 API 테스트
host: default
tags: [user, get]
steps:
  - name: Get User Details
    method: GET
    path: /api/users/1
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body.id
        operator: eq
        value: 1
      - field: body.username
        operator: exists
```

### CRUD 통합 테스트

```yaml
name: User CRUD Integration Test
description: 사용자 생성, 조회, 수정, 삭제 통합 테스트
host: default
environment: development
tags: [integration, crud, user]
continue_on_error: false
steps:
  # Create
  - name: Create New User
    method: POST
    path: /api/users
    body:
      username: testuser
      email: test@example.com
      age: 25
    assertions:
      - field: status
        operator: eq
        value: 201
      - field: body.id
        operator: exists
    extract:
      user_id: body.id
  
  # Read
  - name: Get Created User
    method: GET
    path: /api/users/{{user_id}}
    delay_before: 0.2
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body.username
        operator: eq
        value: testuser
  
  # Update
  - name: Update User
    method: PUT
    path: /api/users/{{user_id}}
    delay_before: 0.2
    body:
      username: testuser_updated
      age: 26
    assertions:
      - field: status
        operator: eq
        value: 200
  
  # Verify Update
  - name: Verify Update
    method: GET
    path: /api/users/{{user_id}}
    delay_before: 0.2
    assertions:
      - field: body.username
        operator: eq
        value: testuser_updated
      - field: body.age
        operator: eq
        value: 26
  
  # Delete
  - name: Delete User
    method: DELETE
    path: /api/users/{{user_id}}
    delay_before: 0.2
    assertions:
      - field: status
        operator: eq
        value: 200
  
  # Verify Delete
  - name: Verify Deletion
    method: GET
    path: /api/users/{{user_id}}
    skip_on_failure: true
    assertions:
      - field: status
        operator: eq
        value: 404
```

### 인증 플로우

```yaml
name: Authentication Flow Test
description: 로그인 및 인증된 요청 테스트
host: default
environment: development
tags: [auth, security]
pre_request_scripts:
  - setup-test-user.json
steps:
  - name: Login
    method: POST
    path: /api/auth/login
    body:
      username: '{{env.TEST_USERNAME}}'
      password: '{{env.TEST_PASSWORD}}'
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body.token
        operator: exists
    extract:
      auth_token: body.token
      user_id: body.user.id
  
  - name: Get Protected Resource
    method: GET
    path: /api/protected/data
    headers:
      Authorization: Bearer {{auth_token}}
    assertions:
      - field: status
        operator: eq
        value: 200
  
  - name: Update Profile
    method: PUT
    path: /api/users/{{user_id}}/profile
    headers:
      Authorization: Bearer {{auth_token}}
    body:
      bio: Updated bio
      location: Seoul
    assertions:
      - field: status
        operator: eq
        value: 200
  
  - name: Logout
    method: POST
    path: /api/auth/logout
    headers:
      Authorization: Bearer {{auth_token}}
    assertions:
      - field: status
        operator: eq
        value: 200
```

## 배열 표기법

```yaml
# 짧은 배열은 인라인 표기
tags: [api, test, integration]
items: [1, 2, 3]

# 긴 배열이나 객체 배열은 블록 표기
tags:
  - api
  - test
  - integration

steps:
  - name: Step 1
    method: GET
    path: /api/path1
  
  - name: Step 2
    method: POST
    path: /api/path2

# 중첩 구조
body:
  users:
    - name: User 1
      email: user1@example.com
    - name: User 2
      email: user2@example.com
  metadata:
    count: 2
    total: 100
```

## 특수 문자와 따옴표

```yaml
# 특수 문자가 있으면 따옴표 사용
headers:
  Authorization: 'Bearer {{TOKEN}}'
  X-Custom: 'value:with:colons'

# 변수 사용 시 따옴표 권장
path: '/api/users/{{user_id}}'
value: '{{env.API_KEY}}'

# 숫자나 boolean은 따옴표 불필요
port: 8080
enabled: true
count: 100

# 문자열로 취급하려면 따옴표 사용
version: '1.0'
id: '123'
```

## 주석

```yaml
name: API Test

# 이것은 주석입니다
steps:
  # 첫 번째 단계
  - name: Get Data
    method: GET
    path: /api/data
    # timeout: 30  # 이 줄은 비활성화됨
```

## 들여쓰기 규칙

```yaml
# 들여쓰기는 2칸 (스페이스)
name: Test
steps:
  - name: Step 1
    method: GET
    path: /api/test
    assertions:
      - field: status
        operator: eq
        value: 200

# 탭 사용 금지 - 스페이스만 사용
# 일관된 들여쓰기 유지
```
