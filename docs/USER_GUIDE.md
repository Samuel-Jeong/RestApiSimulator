# REST API Simulator - User Guide

## 목차
1. [시작하기](#시작하기)
2. [프로젝트 관리](#프로젝트-관리)
3. [시나리오 작성](#시나리오-작성)
4. [테스트 실행](#테스트-실행)
5. [결과 분석](#결과-분석)
6. [UML 생성](#uml-생성)

## 시작하기

### 설치
```bash
# 의존성 설치
pip install -r requirements.txt

# 프로그램 실행
python main.py
```

### 첫 실행
1. 프로그램이 시작되면 TUI 인터페이스가 나타납니다
2. 왼쪽 메뉴에서 원하는 기능을 선택하세요
3. 키보드 단축키를 사용할 수 있습니다:
   - `p`: Projects
   - `s`: Scenarios
   - `r`: Results
   - `u`: UML
   - `q`: Quit

## 프로젝트 관리

### 프로젝트 구조
```
projects/
  └── project_name/
      ├── config/
      │   └── hosts.json       # API 호스트 설정
      ├── scenario/
      │   └── *.json          # 시나리오 파일들
      └── result/
          └── *.json          # 테스트 결과들
```

### 새 프로젝트 만들기
1. Projects 메뉴 선택
2. 하단 입력창에 `new:<프로젝트명>` 입력
3. 자동으로 디렉토리 구조가 생성됩니다

### 프로젝트 선택
1. Projects 메뉴에서 프로젝트 이름 입력
2. 선택된 프로젝트가 현재 작업 프로젝트가 됩니다

### 호스트 설정 (hosts.json)
```json
{
  "default": {
    "base_url": "https://api.example.com",
    "timeout": 30,
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer YOUR_TOKEN"
    },
    "verify_ssl": true
  },
  "staging": {
    "base_url": "https://staging-api.example.com",
    "timeout": 30,
    "headers": {
      "Content-Type": "application/json"
    },
    "verify_ssl": false
  }
}
```

## 시나리오 작성

### 기본 시나리오 구조
```json
{
  "name": "시나리오 이름",
  "description": "시나리오 설명",
  "host": "default",
  "tags": ["tag1", "tag2"],
  "variables": {
    "base_user": "testuser"
  },
  "steps": [
    {
      "name": "스텝 이름",
      "method": "GET|POST|PUT|PATCH|DELETE",
      "path": "/api/endpoint",
      "headers": {},
      "query_params": {},
      "body": {},
      "timeout": 30,
      "delay_before": 0,
      "delay_after": 0,
      "assertions": [],
      "extract": {},
      "skip_on_failure": false,
      "retry": 0
    }
  ]
}
```

### HTTP 메소드
- `GET`: 데이터 조회
- `POST`: 데이터 생성
- `PUT`: 데이터 전체 수정
- `PATCH`: 데이터 부분 수정
- `DELETE`: 데이터 삭제

### 변수 사용
시나리오에서 변수를 정의하고 사용할 수 있습니다:

```json
{
  "variables": {
    "username": "john",
    "email": "john@example.com"
  },
  "steps": [
    {
      "name": "Create User",
      "method": "POST",
      "path": "/users",
      "body": {
        "username": "{{username}}",
        "email": "{{email}}"
      },
      "extract": {
        "user_id": "body.id"
      }
    },
    {
      "name": "Get User",
      "method": "GET",
      "path": "/users/{{user_id}}"
    }
  ]
}
```

### Assertions (검증)

응답을 검증하기 위한 다양한 연산자:

```json
{
  "assertions": [
    {"field": "status", "operator": "eq", "value": 200},
    {"field": "body.id", "operator": "exists"},
    {"field": "body.name", "operator": "contains", "value": "John"},
    {"field": "body.age", "operator": "gt", "value": 18},
    {"field": "body.email", "operator": "regex", "value": ".*@example\\.com"}
  ]
}
```

#### 연산자 종류
- `eq`: 같음 (equal)
- `ne`: 다름 (not equal)
- `gt`: 큼 (greater than)
- `lt`: 작음 (less than)
- `gte`: 크거나 같음
- `lte`: 작거나 같음
- `contains`: 포함
- `not_contains`: 미포함
- `in`: 배열에 포함
- `not_in`: 배열에 미포함
- `regex`: 정규식 매칭
- `exists`: 존재함

### 변수 추출 (Extract)

응답에서 값을 추출하여 다음 스텝에서 사용:

```json
{
  "extract": {
    "user_id": "body.id",
    "token": "body.auth.token",
    "first_item_id": "body.items.0.id"
  }
}
```

## 테스트 실행

### 시나리오 테스트
1. Scenarios 메뉴 선택 (Press S)
2. 실행할 시나리오 번호 입력
3. 'run' 명령으로 테스트 시작
4. 실시간 진행률 및 결과 확인
5. 테스트 완료 후 자동으로 결과 파일 저장

## 결과 분석

### 결과 파일
테스트 결과는 `projects/{project}/result/` 디렉토리에 JSON 형식으로 저장됩니다.

파일명 형식: `{test_type}_{scenario_name}_{timestamp}.json`

### 결과 구조

#### 시나리오 테스트 결과
```json
{
  "report_id": "scenario_user_crud_20231209_143022",
  "test_type": "scenario",
  "project_name": "example",
  "created_at": "2023-12-09T14:30:22",
  "scenario_results": [
    {
      "scenario_name": "User CRUD Operations",
      "status": "success",
      "duration_seconds": 2.5,
      "steps": [...]
    }
  ],
  "summary": {
    "total_steps": 5,
    "successful_steps": 5,
    "failed_steps": 0
  }
}
```

### 메트릭 이해하기

- **Response Time**: 요청부터 응답까지 걸린 시간
- **Success Rate**: 성공한 요청의 비율
- **Error Distribution**: 에러 유형별 분포

## UML 생성

### 시퀀스 다이어그램
시나리오를 PlantUML 시퀀스 다이어그램으로 변환:

```
@startuml
title User CRUD Operations

actor User
participant Client
participant "API Server" as API

== Step 1: Create New User ==
User -> Client: Initiate Create New User
Client -> API: POST /users
API --> Client: 201 Response
@enduml
```

### 플로우차트
시나리오를 PlantUML 액티비티 다이어그램으로 변환:

```
@startuml
title User CRUD Operations - Flowchart

start
:Create New User;
if (Assertions pass?) then (yes)
  :Extract variables;
else (no)
  :Fail scenario;
  stop
endif
stop
@enduml
```

### 텍스트 다이어그램
ASCII 기반 텍스트 다이어그램:

```
======================================================================
  Scenario: User CRUD Operations
======================================================================

[1] Create New User
    │
    ├─► Method: POST
    ├─► Path: /users
    ├─► Assertions: 2
    │   • status eq 201
    │   • body.id exists
    └─► Extract Variables:
        • user_id ← body.id
        │
        ▼
```

## 고급 기능

### 1. 시나리오 검증
실행 전 시나리오 문법과 논리를 검증합니다.

### 2. 데이터 변수화
CSV나 JSON 파일에서 데이터를 읽어 테스트에 사용할 수 있습니다.

### 3. 히스토리 관리
과거 테스트 결과를 비교하고 재실행할 수 있습니다.

### 4. 템플릿 저장
자주 사용하는 설정을 템플릿으로 저장하여 재사용할 수 있습니다.

### 5. 조건부 실행
특정 조건에 따라 스텝 실행 여부를 결정할 수 있습니다.

## 트러블슈팅

### 프로그램 중복 실행 에러
- 이미 실행 중인 인스턴스가 있는지 확인하세요
- `.app.lock` 파일이 남아있다면 삭제하세요

### SSL 인증 에러
- `hosts.json`에서 `verify_ssl: false` 설정

### 타임아웃 에러
- `timeout` 값을 증가시키세요
- 네트워크 연결 상태를 확인하세요

### 변수 치환 안됨
- 변수 이름이 정확한지 확인하세요
- `{{variable}}` 형식을 사용하세요
- 변수가 이전 스텝에서 추출되었는지 확인하세요

## 팁과 모범 사례

1. **작은 단위로 시작**: 간단한 시나리오부터 테스트
2. **적절한 딜레이**: API 부하를 고려하여 `delay_after` 설정
3. **명확한 네이밍**: 시나리오와 스텝의 이름을 명확하게
4. **재사용 가능한 변수**: 공통 값은 변수로 관리
5. **적절한 Assertion**: 필요한 만큼만 검증
6. **에러 핸들링**: `skip_on_failure`와 `retry` 활용
7. **점진적 부하**: 부하 테스트 시 ramp-up 사용
8. **결과 분석**: P95, P99 메트릭에 주목

## 지원

- GitHub Issues: 버그 리포트 및 기능 요청
- 문서: README.md 및 예제 참고

