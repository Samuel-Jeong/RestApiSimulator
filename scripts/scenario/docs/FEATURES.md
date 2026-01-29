# 시나리오 자동 생성 스크립트 - 주요 기능

## 🎯 핵심 개선사항

### 0. 🔄 자동 백업 시스템 (NEW!)

#### 기능 설명
시나리오 재생성 시 **기존 scenario 폴더를 자동으로 백업**합니다.

#### 실행 화면
```
⚠️  기존 scenario 폴더 발견!
📦 백업 중: scenario → scenario_20260121113727
✅ 백업 완료!
```

#### 생성 구조
```
projects/wpm/workercontroller/
├── scenario_20260121113727/    ← 백업된 이전 버전
└── scenario/                    ← 새로 생성된 버전
```

#### 장점
- ✅ 기존 시나리오 자동 보존
- ✅ 타임스탬프로 버전 관리
- ✅ 언제든 이전 버전 복구 가능
- ✅ A/B 테스트 지원

자세한 내용: [BACKUP_FEATURE.md](BACKUP_FEATURE.md)

---

### 0.5. 🔗 Context Path 지정 (NEW!)

#### 기능 설명
API 시나리오 생성 시 **context path를 지정**할 수 있습니다.

#### 사용 방법
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --context-path /api/v1
```

#### 실행 화면
```
🚀 시나리오 자동 생성 시작
📂 입력: /path/to/WorkerController.java
📂 출력: projects/wpm
🔗 Context Path: /api/v1
📊 발견된 엔드포인트: 4개
```

#### 생성된 경로
```json
// Context path 없음
{
  "path": "/worker/1/commute"
}

// Context path 있음 (--context-path /api/v1)
{
  "path": "/api/v1/worker/1/commute"
}
```

#### 장점
- ✅ API 버전별 경로 관리 (/api/v1, /api/v2)
- ✅ 서비스별 경로 지정 (/api/users, /api/orders)
- ✅ 환경별 경로 설정 (/dev/api, /prod/api)
- ✅ 마이크로서비스 아키텍처 지원

자세한 내용: [CONTEXT_PATH.md](CONTEXT_PATH.md)

---

### 0.6. 🔐 인증 및 헤더 관리 (NEW!)

#### 기능 설명
다양한 **인증 방식과 커스텀 헤더**를 자동으로 추가할 수 있습니다.

#### 지원하는 인증 방식
1. **Bearer 토큰 (JWT)**: `--auth-bearer-token`
2. **Basic 인증**: `--auth-basic-token` (자동 Base64 인코딩)
3. **커스텀 헤더**: `--header` (X-API-Key, X-Custom 등)

#### 사용 방법
```bash
# Bearer 토큰
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "your-jwt-token"

# Basic 인증
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-basic-token "admin:password"

# 커스텀 헤더
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --header "X-API-Key:my-key" \
  --header "X-Tenant-ID:tenant-001"

# 모두 함께 사용
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --header "X-API-Key:my-key" \
  --auth-annotations UserCert
```

#### 실행 화면
```
🚀 시나리오 자동 생성 시작
📂 입력: /path/to/WorkerController.java
🔐 Bearer Token: jwt-token
📋 Custom Headers: X-API-Key=my-key
🔒 Auth Annotations: UserCert
📊 발견된 엔드포인트: 4개
```

#### 생성된 시나리오
```json
{
  "name": "Get Worker - Success Test",
  "steps": [{
    "method": "GET",
    "path": "/api/v1/worker/1",
    "headers": {
      "Authorization": "Bearer jwt-token",
      "X-API-Key": "my-key"
    }
  }]
}
```

#### Basic 인증 자동 인코딩
```bash
# 입력
--auth-basic-token "admin:password123"

# 생성된 헤더
{
  "Authorization": "Basic YWRtaW46cGFzc3dvcmQxMjM="
}
```

#### 인증 어노테이션 필터링
```java
@RestController
public class WorkerController {
    
    @UserCert  // ← 인증 어노테이션이 있으면 인증 헤더 추가
    @GetMapping("/{id}")
    public ResponseEntity getWorker(@PathVariable Long id) { }
    
    @GetMapping("/public")  // ← 어노테이션 없으면 커스텀 헤더만 추가
    public ResponseEntity getPublicInfo() { }
}
```

#### 장점
- ✅ Bearer, Basic 등 다양한 인증 방식 지원
- ✅ username:password를 자동으로 Base64 인코딩
- ✅ 무제한 커스텀 헤더 추가 가능
- ✅ 특정 어노테이션이 있는 메서드에만 인증 헤더 선택적 적용
- ✅ 모든 시나리오 타입에 자동 적용 (success, failure, integration, load_test)
- ✅ 여러 인증 어노테이션 동시 지원
- ✅ 수동 편집 불필요

---

### 0.7. ✅ Continue on Error (NEW!)

#### 기능 설명
Assertion 실패 시에도 **다음 API를 계속 테스트**할 수 있습니다.

#### 사용 방법
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --continue-on-error
```

#### 실행 화면
```
🚀 시나리오 자동 생성 시작
✅ Continue on Error: Assertion 실패 시에도 계속 진행
```

#### 생성된 시나리오
```json
{
  "name": "Full Integration Test",
  "continue_on_error": true,
  "steps": [
    {"name": "API 1", "assertions": [...]},
    {"name": "API 2", "assertions": [...]},
    {"name": "API 3", "assertions": [...]}
  ]
}
```

#### 동작 방식
**기본 동작 (continue_on_error: false)**
```
API 1 ✅ → API 2 ❌ → 중단 (API 3 실행 안 됨)
```

**continue_on_error: true**
```
API 1 ✅ → API 2 ❌ → API 3 ✅ (모든 API 테스트)
```

#### 장점
- ✅ 전체 시스템 상태를 한 번에 파악
- ✅ 통합 테스트 시 모든 API 테스트 가능
- ✅ 디버깅 시간 단축 (어떤 API가 실패하는지 전체 확인)
- ✅ Smoke Test 및 Health Check에 최적

#### 사용 사례
1. **통합 테스트**: 전체 워크플로우 검증
2. **Smoke Test**: 배포 후 전체 API 상태 확인
3. **디버깅**: 실패한 모든 API 한 번에 파악

---

### 1. 완전 자동화 - 하드코딩 제거

#### AS-IS (기존)
```python
# 하드코딩된 샘플 데이터
body = {
    "data": "sample"
}
```

#### TO-BE (개선)
```python
# DTO 파일 자동 분석 → 실제 필드 추출 → 동적 데이터 생성
# UserDto.java 파일을 찾아서 분석
fields = {
    "username": "testuser",      # 필드명 기반 지능형 생성
    "email": "test@example.com", # 이메일 패턴 인식
    "name": "Test User",         # 사용자 이름 패턴
    "phone": "010-1234-5678"     # 전화번호 패턴
}
```

---

## 🔍 지능형 분석 기능

### DTO 자동 탐색 알고리즘

```
1. 컨트롤러 파싱
   @PostMapping
   public ResponseEntity create(@RequestBody UserDto dto)
   
   ↓ "UserDto" 추출

2. import 경로 추적
   import com.sks.wpm.dto.UserDto;
   
   ↓ 패키지 경로 파악

3. 프로젝트 내 DTO 파일 자동 검색
   - src/main/java/com/sks/wpm/dto/UserDto.java
   - dto/**/*UserDto.java
   - request/**/*UserDto.java
   
   ↓ 파일 발견

4. DTO 필드 파싱
   private String username;
   @NotNull
   private String email;
   @Size(min=2, max=50)
   private String name;
   
   ↓ 필드 정보 추출

5. Validation 인식
   @NotNull → required: true
   @Size(min, max) → 길이 제약
   @Pattern → 정규식 패턴
   
   ↓ 검증 규칙 파악

6. 지능형 샘플 데이터 생성
   username → "testuser"
   email → "test@example.com"
   name → "Test User"
```

---

## 📊 생성되는 시나리오

### 1. 정상 시나리오 (Success)

모든 필드를 올바르게 채워서 요청
```json
{
  "name": "Create User - Success Test",
  "steps": [{
    "method": "POST",
    "path": "/api/users",
    "body": {
      "username": "testuser",
      "email": "test@example.com",
      "name": "Test User"
    },
    "assertions": [
      {"field": "status", "operator": "eq", "value": 201},
      {"field": "body.id", "operator": "exists"}
    ]
  }]
}
```

### 2. 실패 시나리오 (Failure)

#### A. 필수 필드 누락
```json
{
  "name": "Create User - Missing Required Field",
  "description": "실패 케이스: 필수 필드(username) 누락",
  "steps": [{
    "body": {
      "email": "test@example.com",
      "name": "Test User"
      // username 누락
    },
    "assertions": [
      {"field": "status", "operator": "eq", "value": 400}
    ]
  }]
}
```

#### B. 존재하지 않는 리소스
```json
{
  "name": "Get User By Id - Not Found",
  "steps": [{
    "path": "/api/users/99999",  // 존재하지 않는 ID
    "assertions": [
      {"field": "status", "operator": "eq", "value": 404}
    ]
  }]
}
```

#### C. 빈 요청 본문
```json
{
  "name": "Create User - Empty Request Body",
  "steps": [{
    "body": {},
    "assertions": [
      {"field": "status", "operator": "eq", "value": 400}
    ]
  }]
}
```

### 3. CRUD 통합 시나리오

```json
{
  "name": "CRUD Integration Test",
  "steps": [
    {
      "name": "1. 리소스 생성",
      "method": "POST",
      "extract": {"resource_id": "body.id"}
    },
    {
      "name": "2. 목록 조회",
      "method": "GET"
    },
    {
      "name": "3. 상세 조회",
      "method": "GET",
      "path": "/api/users/{{resource_id}}"  // 생성된 ID 사용
    },
    {
      "name": "4. 리소스 수정",
      "method": "PUT",
      "path": "/api/users/{{resource_id}}"
    },
    {
      "name": "5. 수정 확인",
      "method": "GET"
    },
    {
      "name": "6. 리소스 삭제",
      "method": "DELETE"
    },
    {
      "name": "7. 삭제 확인 (404)",
      "assertions": [
        {"field": "status", "operator": "eq", "value": 404}
      ]
    }
  ]
}
```

### 4. 성능 테스트

#### 개별 API 부하 테스트
```json
{
  "name": "Get All Users - Load Test",
  "load_test": {
    "enabled": true,
    "users": 10,        // 동시 사용자 수
    "spawn_rate": 2,    // 초당 증가율
    "duration": 60      // 테스트 시간(초)
  },
  "steps": [{
    "assertions": [
      {"field": "response_time", "operator": "lt", "value": 1000}  // 1초 이내
    ]
  }]
}
```

#### 스트레스 테스트
```json
{
  "name": "Stress Test",
  "load_test": {
    "users": 50,        // 고부하
    "spawn_rate": 5,
    "duration": 120
  },
  "steps": [
    // 모든 엔드포인트를 순차 실행
  ]
}
```

---

## 🎨 지능형 샘플 데이터 생성

### 필드명 패턴 인식

| 필드명 | 생성되는 데이터 | 규칙 |
|--------|---------------|------|
| username, user_name | testuser | 사용자명 패턴 |
| email, mail | test@example.com | 이메일 형식 |
| name | Test User | 일반 이름 |
| phone, tel | 010-1234-5678 | 한국 전화번호 |
| address, addr | 서울시 강남구 | 주소 패턴 |
| url, link | https://example.com | URL 형식 |
| code | TEST001 | 코드 패턴 |
| title | Test Title | 제목 |
| content, body, desc | Test Content | 본문 |
| price, amount | 10000 | 금액 (숫자) |
| age | 25 | 나이 |
| count, num | 10 | 개수 |
| status | ACTIVE | 상태 |
| type | DEFAULT | 타입 |
| is*, has*, enable* | true | boolean 플래그 |

### 타입별 생성

```python
# String
"test" 또는 필드명 기반 지능형 생성

# Integer/Long
필드명에 따라:
- id → 1
- age → 25
- count → 10
- price → 10000

# Boolean
필드명이 is/has/enable로 시작 → true
기타 → false

# Date
"2024-01-01"

# DateTime
"2024-01-01T10:00:00"

# List/Set
[]

# Map
{}
```

---

## 📁 파일 구조

### 입력
```
/path/to/project/
└── src/main/java/com/example/
    ├── controller/
    │   └── UserController.java    # 입력
    └── dto/
        └── UserDto.java            # 자동 탐색
```

### 출력 (폴더 구조로 자동 정리)
```
projects/user/
└── scenario/
    ├── success/                    # 정상 시나리오
    │   ├── getallusers_success.json
    │   ├── getuserbyid_success.json
    │   ├── createuser_success.json
    │   ├── updateuser_success.json
    │   └── deleteuser_success.json
    ├── failure/                    # 실패 시나리오
    │   ├── getuserbyid_failure_1.json      # 404
    │   ├── createuser_failure_1.json       # 필수 필드 누락
    │   ├── createuser_failure_2.json       # 빈 본문
    │   ├── updateuser_failure_1.json       # 필수 필드 누락
    │   ├── updateuser_failure_2.json       # 404
    │   ├── updateuser_failure_3.json       # 빈 본문
    │   └── deleteuser_failure_1.json       # 404
    ├── integration/                # 통합 테스트
    │   └── user_full_integration.json
    └── load_test/                  # 성능/부하 테스트
        ├── getallusers_load_test.json
        ├── getuserbyid_load_test.json
        └── user_stress_test.json
```

---

## 🚀 사용 시나리오

### 1. 단일 컨트롤러

```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/UserController.java
```

### 2. 디렉토리 전체 (권장)

```bash
# 모든 컨트롤러를 한 번에 처리
python3 scripts/scenario/generate_scenario.py \
  /path/to/project/src/main/java/com/example/controller
```

**출력:**
```
🚀 시나리오 자동 생성 시작
🔍 5개의 컨트롤러 발견

================================================================================
📋 처리 중: UserController.java
================================================================================
📊 발견된 엔드포인트: 5개
  ⚠️  DTO 파일 읽기 실패: UserDto (기본 필드 사용)
  또는
  ✓ DTO 파일 발견: /path/to/UserDto.java
  ✓ 7개 필드 파싱 완료

📁 생성 위치: projects/user/scenario/

1️⃣  정상/실패 시나리오 생성 중...
  ✓ getallusers_success.json
  ✓ createuser_success.json
  ✓ createuser_failure_1.json
  ...

2️⃣  통합 테스트 시나리오 생성 중...
  ✓ user_crud_integration.json
  ✓ user_full_integration.json

3️⃣  성능/부하 테스트 시나리오 생성 중...
  ✓ getallusers_load_test.json
  ✓ user_stress_test.json

✅ 시나리오 파일 생성 완료!
📊 총 17개 파일 생성

================================================================================
📋 처리 중: PostController.java
================================================================================
...

🎉 모든 시나리오 생성 완료!
```

---

## 💡 장점

### 1. 완전 자동화
- 수동 작업 없이 모든 시나리오 자동 생성
- DTO 분석 → 필드 추출 → 샘플 데이터 생성

### 2. 비즈니스 로직 반영
- Validation 어노테이션 인식
- 필수/선택 필드 자동 구분
- 필드명 기반 지능형 데이터 생성

### 3. 포괄적 테스트
- 정상 케이스
- 다양한 실패 케이스
- 통합 테스트
- 성능/부하 테스트

### 4. 확장성
- 새로운 컨트롤러 추가 시 즉시 시나리오 생성
- 배치 처리로 대규모 프로젝트 지원
- 프로젝트별 독립 관리

### 5. 유지보수성
- 컨트롤러 변경 시 재실행으로 시나리오 갱신
- 일관된 시나리오 구조
- 태그 기반 분류
