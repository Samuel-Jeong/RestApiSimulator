# YAML 시나리오 생성 가이드

## 🎯 YAML vs JSON

### 가독성 비교

**JSON (21줄)**
```json
{
  "name": "User API Test",
  "host": "default",
  "tags": ["user", "api"],
  "steps": [
    {
      "name": "Get User",
      "method": "GET",
      "path": "/api/users/1",
      "assertions": [
        {
          "field": "status",
          "operator": "eq",
          "value": 200
        }
      ]
    }
  ]
}
```

**YAML (13줄) - 40% 더 간결!**
```yaml
name: User API Test
host: default
tags: [user, api]
steps:
  - name: Get User
    method: GET
    path: /api/users/1
    assertions:
      - field: status
        operator: eq
        value: 200
```

## 사용법

### 1. YAML 형식으로 생성 (기본값)

```bash
# 기본 - YAML 형식
python3 generate_scenario.py /path/to/Controller.java

# 명시적으로 YAML 지정
python3 generate_scenario.py /path/to/Controller.java --format yaml
```

### 2. JSON 형식으로 생성

```bash
python3 generate_scenario.py /path/to/Controller.java --format json
```

### 3. 전체 옵션 예제

```bash
python3 generate_scenario.py \
  /path/to/controller \
  --format yaml \
  --output projects/myapp \
  --context-path /api/v1 \
  --environment development \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --continue-on-error
```

## 생성 결과 예시

### 폴더 구조

```
projects/
└── myapp/
    └── scenario/
        ├── success/
        │   ├── get_user_success.yaml
        │   ├── create_user_success.yaml
        │   └── update_user_success.yaml
        ├── failure/
        │   ├── create_user_failure_1.yaml
        │   └── get_user_failure_1.yaml
        ├── integration/
        │   ├── myapp_crud_integration.yaml
        │   └── myapp_full_integration.yaml
        └── load_test/
            ├── get_user_load_test.yaml
            └── myapp_stress_test.yaml
```

### YAML 시나리오 예시

**success/get_user_success.yaml**
```yaml
name: Get User - Success Test
description: '정상 케이스: GET /api/v1/users/1'
host: default
tags:
  - success
  - user
  - get
continue_on_error: false
environment: development
steps:
  - name: Get User - Success Case
    method: GET
    path: /api/v1/users/1
    headers:
      X-API-Key: '{{env.API_KEY}}'
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body
        operator: exists
      - field: body.id
        operator: exists
```

**integration/user_full_integration.yaml**
```yaml
name: User - Full Integration Test
description: 전체 엔드포인트 통합 테스트
host: default
tags:
  - integration
  - full
  - user
continue_on_error: true
environment: development
pre_request_scripts:
  - auth-setup.json
steps:
  - name: 1. Get User List
    method: GET
    path: /api/v1/users
    assertions:
      - field: status
        operator: eq
        value: 200

  - name: 2. Get User Detail
    method: GET
    path: /api/v1/users/1
    delay_before: 0.2
    assertions:
      - field: status
        operator: eq
        value: 200
    extract:
      user_id: body.id

  - name: 3. Create User
    method: POST
    path: /api/v1/users
    delay_before: 0.2
    body:
      username: testuser
      email: test@example.com
    assertions:
      - field: status
        operator: eq
        value: 201
```

## JSON을 YAML로 변환

기존 JSON 시나리오를 YAML로 변환할 수 있습니다:

```bash
# 단일 파일 변환
python3 convert_json_to_yaml.py scenario.json

# 디렉토리 전체 변환 (재귀적)
python3 convert_json_to_yaml.py projects/myproject/scenario/

# 변환 후 원본 JSON 삭제
python3 convert_json_to_yaml.py projects/myproject/scenario/ --delete-json
```

## 장점

### YAML의 장점 ✅
- **가독성**: 중괄호와 따옴표가 적어 읽기 쉬움
- **간결함**: 동일한 내용을 더 적은 줄로 표현 (평균 40% 감소)
- **주석**: `#`으로 주석 작성 가능
- **멀티라인**: 긴 텍스트를 여러 줄로 자연스럽게 작성
- **구조 파악**: 들여쓰기로 계층 구조가 명확함
- **유지보수**: 복잡한 시나리오도 쉽게 수정 가능

### JSON의 장점 ✅
- **표준**: 널리 사용되는 표준 형식
- **도구 지원**: 대부분의 도구와 라이브러리가 지원
- **파싱 속도**: 일반적으로 파싱이 약간 더 빠름

## 권장사항

1. **새로운 시나리오**: YAML 형식 사용 (기본값)
2. **복잡한 통합 테스트**: YAML이 훨씬 관리하기 쉬움
3. **기존 JSON 시나리오**: 그대로 사용 가능, 필요시 변환
4. **API 문서와 함께 공유**: YAML이 더 직관적

## 참고 자료

- [YAML 시나리오 작성 가이드](../../docs/YAML_SCENARIOS.md)
- [시나리오 자동 생성 README](./README.md)
- [REST API Simulator 메인 README](../../README.md)
