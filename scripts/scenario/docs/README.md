# 시나리오 자동 생성 스크립트 (Advanced)

자바 Spring Boot 컨트롤러 코드를 **완전 자동**으로 분석하여 REST API 테스트 시나리오를 생성합니다.

## 🎯 출력 형식

**기본 출력: YAML** (가독성 우수, 40% 더 간결)
- JSON 형식도 지원 (`--format json`)
- 생성된 시나리오는 YAML과 JSON 모두 실행 가능

## 핵심 기능

### 지능형 코드 분석
- **DTO 클래스 자동 탐색**: import 경로 분석 → DTO 파일 자동 검색 → 필드 추출
- **Validation 어노테이션 인식**: `@NotNull`, `@Size`, `@Pattern`, 커스텀 어노테이션 등 자동 파싱
- **비즈니스 로직 추론**: 필드명/타입 기반 샘플 데이터 자동 생성
- **의존성 추적**: import 경로를 따라 관련 클래스 자동 분석
- **인증 모드 지원**: Include/Exclude 모드로 다양한 인증 패턴 지원

### 자동 생성되는 시나리오
1. **정상 시나리오**: 각 API별 성공 케이스
2. **실패 시나리오**: 
   - 필수 필드 누락
   - 잘못된 ID (404)
   - 빈 요청 본문 (400)
3. **통합 테스트**: CRUD 전체 플로우
4. **성능/부하 테스트**: 
   - 개별 API 부하 테스트
   - 전체 시나리오 스트레스 테스트

### 완전 자동화
- **하드코딩 제거**: 모든 데이터가 동적으로 생성
- **배치 처리**: 디렉토리 내 모든 컨트롤러 한번에 처리
- **프로젝트별 폴더 자동 생성**
- **자동 백업**: 기존 scenario 폴더를 타임스탬프로 백업 후 재생성

## 사용법

### 기본 사용법

```bash
# 기본 (YAML 형식으로 생성)
python3 scripts/scenario/generate_scenario.py \
  /path/to/your/project/src/main/java/com/example/controller

# JSON 형식으로 생성
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --format json

# YAML 형식 명시적 지정
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --format yaml
```

### 출력 형식 비교

**YAML (권장) - 40% 더 간결:**
```yaml
name: Create User - Success Test
host: default
tags: [success, user, post]
steps:
  - name: Create User
    method: POST
    path: /api/users
    body:
      username: testuser
      email: test@example.com
    assertions:
      - field: status
        operator: eq
        value: 201
```

**JSON (호환성):**
```json
{
  "name": "Create User - Success Test",
  "host": "default",
  "tags": ["success", "user", "post"],
  "steps": [{
    "name": "Create User",
    "method": "POST",
    "path": "/api/users",
    "body": {
      "username": "testuser",
      "email": "test@example.com"
    },
    "assertions": [
      {"field": "status", "operator": "eq", "value": 201}
    ]
  }]
}
```

### Context Path 지정

```bash
# API 버전별 경로 지정
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --context-path /api/v1

# 출력 경로와 함께 사용
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --output projects/myapp \
  --context-path /api/v1
```

**생성 결과:**
- Context path 없음: `/worker/1/commute`
- Context path 있음: `/api/v1/worker/1/commute`

자세한 내용: [CONTEXT_PATH.md](CONTEXT_PATH.md)

### Bearer 토큰 인증

```bash
# Bearer 토큰 추가
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "your-jwt-token-here"

# Basic 인증 추가
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-basic-token "username:password"

# 커스텀 헤더 추가
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --header "X-API-Key:your-api-key" \
  --header "X-Custom-Header:custom-value"

# 특정 어노테이션이 있는 메서드에만 인증 헤더 추가
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "your-jwt-token" \
  --auth-annotations UserCert Authenticated

# 어노테이션별 Pre-request 라이브러리 매핑
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "your-jwt-token" \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --header "X-Token:{{USER_CERT_TOKEN}}"

# Continue on Error 옵션 (Assertion 실패 시에도 계속 진행)
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --continue-on-error

# 환경 지정 (생성된 시나리오가 특정 환경 사용)
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --environment development

# 모든 옵션 함께 사용
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --output projects/myapp \
  --format yaml \
  --context-path /api/v1 \
  --auth-bearer-token "your-jwt-token" \
  --auth-basic-token "admin:password" \
  --header "X-API-Key:my-key" \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --continue-on-error \
  --environment development
```

**생성 결과 (YAML):**
```yaml
environment: development
pre_request_scripts:
  - wpm-get-user-info.json
continue_on_error: true
steps:
  - method: POST
    path: /api/v1/worker/1/commute
    headers:
      Authorization: Bearer your-jwt-token
      X-API-Key: my-key
```

**주요 특징:**
- **Bearer 인증**: JWT 토큰 자동 추가 (`--auth-bearer-token`)
- **Basic 인증**: username:password를 자동으로 Base64 인코딩 (`--auth-basic-token`)
- **커스텀 헤더**: X-API-Key, X-Custom-Header 등 자유롭게 추가 (`--header`)
- **Pre-request 매핑**: 어노테이션별로 실행할 pre-request 스크립트 지정 (`UserCert:wpm-get-user-info.json`)
- **환경 변수**: 시나리오가 사용할 환경 지정 (`--environment development`)
- **Continue on Error**: Assertion 실패 시에도 계속 진행 (`--continue-on-error`)
- 지정된 인증 어노테이션이 있는 메서드에만 인증 헤더 및 pre-request 적용
- `@UserCert`, `@Authenticated`, `@Secured` 등 커스텀 어노테이션 지원
- 모든 시나리오 타입에 자동 적용 (success, failure, integration, load_test)

### 실제 사용 예제

```bash
# SKS WPM 프로젝트 예시
python3 scripts/scenario/generate_scenario.py \
  /Volumes/WORK/GIT_PROJECTS/TELCOWARE/sks-wpm-container-apps/app-mod/worker-app/src/main/java/com/sks/wpm/controller

# 출력 결과:
# [INFO] 5개의 컨트롤러 발견
# 
# ================================================================================
# [INFO] 처리 중: UserController.java
# ================================================================================
# [INFO] 발견된 엔드포인트: 8개
# 
# [INFO] 생성 위치: projects/user/scenario/
# 
# [1/3] 정상/실패 시나리오 생성 중...
#   - getallusers_success.json
#   - getallusers_load_test.json
#   ...
# 
# [2/3] 통합 테스트 시나리오 생성 중...
#   - user_crud_integration.json
#   - user_full_integration.json
# 
# [3/3] 성능/부하 테스트 시나리오 생성 중...
#   - user_stress_test.yaml
# 
# [SUCCESS] 시나리오 파일 생성 완료!
# [INFO] 총 25개 YAML 파일 생성
```

**참고:** `--format json`을 사용하면 JSON 형식으로 생성됩니다.

## 지원하는 어노테이션

### 컨트롤러 레벨
- `@RestController`
- `@RequestMapping`

### 메서드 레벨
- `@GetMapping`
- `@PostMapping`
- `@PutMapping`
- `@DeleteMapping`
- `@PatchMapping`

### 파라미터 레벨
- `@RequestBody` - 요청 본문
- `@PathVariable` - 경로 변수
- `@RequestParam` - 쿼리 파라미터
- `@ModelAttribute` - 모델 속성 (Query Parameter로 변환)

## 생성되는 시나리오 파일

### 파일 형식
- **기본**: `.yaml` (YAML 형식)
- **옵션**: `.json` (JSON 형식, `--format json` 사용 시)

### 1. 정상 시나리오 (`*_success.yaml`)
각 API의 정상 동작 테스트
- DTO 필드 기반 실제 데이터 자동 생성
- 적절한 HTTP 상태 코드 검증
- 응답 필드 존재 여부 확인

### 2. 실패 시나리오 (`*_failure_*.yaml`)

#### a) 필수 필드 누락 테스트
```yaml
name: Create User - Missing Required Field
description: 실패 케이스 - 필수 필드(email) 누락
steps:
  - body:
      username: test
      # email 필드 누락
    assertions:
      - field: status
        operator: eq
        value: 400
```

#### b) 존재하지 않는 리소스 테스트
```yaml
name: Get User By Id - Not Found
description: 실패 케이스 - 존재하지 않는 리소스
steps:
  - path: /api/users/99999  # 존재하지 않는 ID
    assertions:
      - field: status
        operator: eq
        value: 404
```

#### c) 빈 요청 본문 테스트
```yaml
name: Create User - Empty Request Body
description: 실패 케이스 - 빈 요청 본문
steps:
  - body: {}
    assertions:
      - field: status
        operator: eq
        value: 400
```

### 3. CRUD 통합 시나리오 (`*_crud_integration.yaml`)
Create → Read → Update → Delete 전체 흐름
```
1. 리소스 생성 → ID 추출
2. 목록 조회
3. 상세 조회 (생성된 ID 사용)
4. 리소스 수정
5. 수정 확인
6. 리소스 삭제
7. 삭제 확인 (404)
```

### 4. 전체 통합 시나리오 (`*_full_integration.yaml`)
모든 엔드포인트를 순차적으로 실행

### 5. 성능 테스트 (`*_load_test.yaml`)
개별 API 부하 테스트
```yaml
load_test:
  enabled: true
  users: 10
  spawn_rate: 2
  duration: 60
steps:
  - assertions:
      - field: response_time
        operator: lt
        value: 1000
```

### 6. 스트레스 테스트 (`*_stress_test.yaml`)
전체 시나리오 고부하 테스트
```yaml
load_test:
  enabled: true
  users: 50
  spawn_rate: 5
  duration: 120
```

## DTO 자동 파싱

### 동작 방식

1. **컨트롤러 파싱**: `@RequestBody UserDto` 발견
2. **import 경로 추적**: `import com.example.dto.UserDto;`
3. **DTO 파일 검색**: 프로젝트 내에서 `UserDto.java` 자동 탐색
4. **필드 분석**: private 필드 및 validation 어노테이션 파싱
5. **샘플 데이터 생성**: 필드명/타입 기반 지능형 데이터 생성

### DTO 예제

```java
public class UserDto {
    
    @NotNull
    private String username;
    
    @NotBlank
    @Email
    private String email;
    
    @Size(min = 2, max = 50)
    private String name;
    
    @Pattern(regexp = "^010-\\d{4}-\\d{4}$")
    private String phone;
    
    @Min(0)
    @Max(150)
    private Integer age;
    
    private Boolean active;
}
```

### 자동 생성되는 샘플 데이터

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "name": "Test User",
  "phone": "010-1234-5678",
  "age": 25,
  "active": true
}
```

### 지원하는 Validation 어노테이션

- `@NotNull`, `@NotEmpty`, `@NotBlank` → required 필드 인식
- `@Size(min, max)` → 문자열 길이 제약
- `@Min`, `@Max` → 숫자 범위 제약
- `@Pattern` → 정규식 패턴 (향후 지원 예정)
- `@Email` → 이메일 형식 자동 생성

### 필드명 기반 지능형 데이터 생성

| 필드명 패턴 | 생성되는 샘플 데이터 |
|------------|-------------------|
| email, mail | test@example.com |
| name, username | Test User, testuser |
| phone, tel | 010-1234-5678 |
| address, addr | 서울시 강남구 |
| url | https://example.com |
| code | TEST001 |
| title | Test Title |
| content, body, description | Test Content |
| price, amount | 10000 |
| age | 25 |
| count, num | 10 |
| status | ACTIVE |
| type | DEFAULT |

## 자바 컨트롤러 예제

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        // ...
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        // ...
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody UserDto userDto) {
        // ...
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(
        @PathVariable Long id, 
        @RequestBody UserDto userDto
    ) {
        // ...
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        // ...
    }
}
```

위 컨트롤러로부터 자동 생성되는 시나리오:

**정상 시나리오 (5개)**
- `getallusers_success.yaml`
- `getuserbyid_success.yaml`
- `createuser_success.yaml`
- `updateuser_success.yaml`
- `deleteuser_success.yaml`

**실패 시나리오 (7개)**
- `createuser_failure_1.yaml` - 필수 필드 누락
- `createuser_failure_2.yaml` - 빈 본문
- `getuserbyid_failure_1.yaml` - 존재하지 않는 ID
- `updateuser_failure_1.yaml` - 필수 필드 누락
- `updateuser_failure_2.yaml` - 존재하지 않는 리소스
- `deleteuser_failure_1.yaml` - 존재하지 않는 리소스

**통합 테스트 (2개)**
- `user_crud_integration.yaml` - CRUD 전체 플로우
- `user_full_integration.yaml` - 모든 엔드포인트

**성능 테스트 (3개)**
- `getallusers_load_test.yaml`
- `getuserbyid_load_test.yaml`
- `user_stress_test.yaml`

**총 17개 YAML 시나리오 파일 자동 생성 (폴더별로 정리됨)**

생성된 폴더 구조:
```
projects/user/scenario/
├── success/        (5개 .yaml)
├── failure/        (7개 .yaml)
├── integration/    (2개 .yaml)
└── load_test/      (3개 .yaml)
```

**JSON 형식으로 생성하려면:** `--format json` 옵션을 추가하세요.

## 시나리오 파일 구조

생성된 YAML 파일은 다음 형식을 따릅니다:

```yaml
name: 시나리오 이름
description: 시나리오 설명
host: default
tags: [태그1, 태그2]
steps:
  - name: 단계 이름
    method: GET  # POST, PUT, DELETE, PATCH
    path: /api/endpoint/{param}
    body:
      key: value
    assertions:
      - field: status
        operator: eq
        value: 200
    extract:
      variable_name: body.id
    delay_before: 0.2
```

**JSON 형식도 지원:** `--format json` 옵션 사용 시 JSON으로 생성

## 주의사항

1. **자바 파일 경로**: 절대 경로를 사용해야 합니다
2. **파일 인코딩**: UTF-8 인코딩을 사용합니다
3. **컨트롤러 네이밍**: `*Controller.java` 형식을 권장합니다
4. **RequestBody 타입**: DTO 클래스명에 따라 샘플 데이터가 생성됩니다
   - `UserDto` → 사용자 관련 샘플 데이터
   - `PostDto` / `ArticleDto` → 게시글 관련 샘플 데이터
   - `CommentDto` → 댓글 관련 샘플 데이터

## 커스터마이징

생성된 시나리오 파일은 초안입니다. 다음 항목들을 프로젝트에 맞게 수정하세요:

1. **요청 본문**: 실제 필드명과 값으로 수정
2. **Assertions**: 비즈니스 로직에 맞는 검증 조건 추가
3. **변수 추출**: 필요한 값들을 extract로 추가
4. **호스트 설정**: `hosts.json`에서 실제 호스트 정보 설정
5. **태그**: 프로젝트에 맞는 태그로 변경

## 트러블슈팅

### 엔드포인트를 찾을 수 없음
- 컨트롤러 어노테이션(`@GetMapping`, `@PostMapping` 등)이 제대로 작성되어 있는지 확인
- 주석 처리된 메서드는 제외됨

### 샘플 데이터가 부적절함
- 생성된 JSON 파일에서 `body` 필드를 직접 수정
- 실제 DTO 구조에 맞게 커스터마이징

### 경로 변수가 제대로 추출되지 않음
- `@PathVariable` 어노테이션 확인
- 경로 패턴이 `{변수명}` 형식인지 확인

## Pre-request 라이브러리 매핑

특정 어노테이션이 있는 API에만 자동으로 pre-request 스크립트를 실행하고 변수를 추출할 수 있습니다.

### 사용 방법

```bash
# 단일 매핑
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-annotations UserCert:wpm-get-user-info.json

# 여러 매핑
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --auth-annotations AdminAuth:admin-auth.json \
  --auth-annotations PublicAPI
```

### 인증 모드 (Auth Mode)

인증 적용 방식을 선택할 수 있습니다:

#### Include 모드 (기본값)
특정 어노테이션이 있는 메서드만 인증이 필요한 경우:
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert Authenticated \
  --auth-mode include  # 기본값이므로 생략 가능
```

#### Exclude 모드 (AOP 전역 인증)
기본적으로 모든 메서드에 인증이 적용되고, 특정 어노테이션으로 인증을 제외하는 경우:
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations NoAuth PermitAll \
  --auth-mode exclude
```

**자세한 내용**: [AUTH_MODE_GUIDE.md](./AUTH_MODE_GUIDE.md) 참고

### 동작 방식

1. `@UserCert` 어노테이션이 있는 메서드 발견
2. `wpm-get-user-info.json` pre-request 실행
3. 응답에서 변수 추출 (예: `USER_CERT_TOKEN`)
4. 추출된 변수를 헤더/본문에서 사용 가능 (`{{USER_CERT_TOKEN}}`)

### Pre-request 라이브러리 예시

`projects/{project}/package_library/wpm-get-user-info.json`:
```json
{
  "name": "WPM User Authentication",
  "description": "Get user certification token",
  "steps": [
    {
      "name": "Get User Cert Token",
      "method": "POST",
      "url": "{{env.WPM_DEVICE_APP_URL}}/api/v1/token/extrainfo/create",
      "headers": {
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

### 변수 치환 규칙

- `{{env.변수명}}`: 환경 파일 (`env/development.json`)의 변수
- `{{변수명}}`: Pre-request에서 추출한 변수

자세한 내용: [JSON_PRE_REQUEST.md](../../docs/JSON_PRE_REQUEST.md), [ENVIRONMENT.md](../../docs/ENVIRONMENT.md)

## 관련 문서

### 시나리오 작성
- **[YAML_GUIDE.md](YAML_GUIDE.md)** - YAML 시나리오 생성 가이드 ⭐
- **[../../docs/YAML_SCENARIOS.md](../../docs/YAML_SCENARIOS.md)** - YAML 시나리오 작성 완전 가이드 ⭐
- [FEATURES.md](FEATURES.md) - 주요 기능 상세 설명
- [USAGE.md](USAGE.md) - 사용 예제
- [convert_json_to_yaml.py](convert_json_to_yaml.py) - JSON→YAML 변환 도구

### 고급 기능
- [CONTEXT_PATH.md](CONTEXT_PATH.md) - Context Path 기능
- [BACKUP_FEATURE.md](BACKUP_FEATURE.md) - 자동 백업 기능
- [API_PARAMETER_PARSING.md](API_PARAMETER_PARSING.md) - API 파라미터 파싱
- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - 폴더 구조
- [../../docs/JSON_PRE_REQUEST.md](../../docs/JSON_PRE_REQUEST.md) - Pre-request 스크립트 (JSON)
- [../../docs/ENVIRONMENT.md](../../docs/ENVIRONMENT.md) - 환경 변수
- [NESTED_PROJECT_SUPPORT.md](NESTED_PROJECT_SUPPORT.md) - 중첩 프로젝트 지원
- [README_VENV.md](README_VENV.md) - 가상환경 사용 가이드
