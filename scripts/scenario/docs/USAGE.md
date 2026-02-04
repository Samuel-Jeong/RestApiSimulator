# 시나리오 자동 생성 스크립트 사용법

## 빠른 시작

```bash
# 단일 컨트롤러
python3 scripts/scenario/generate_scenario.py /path/to/YourController.java

# 디렉토리 전체 (모든 컨트롤러 자동 처리)
python3 scripts/scenario/generate_scenario.py /path/to/controller/directory

# 실제 사용 예제
python3 scripts/scenario/generate_scenario.py \
  /Volumes/WORK/GIT_PROJECTS/TELCOWARE/sks-wpm-container-apps/app-mod/worker-app/src/main/java/com/sks/wpm/controller

# 출력 경로 지정
python3 scripts/scenario/generate_scenario.py /path/to/controller --output /custom/path

# Context Path 지정 (API 버전, 서비스별 경로)
python3 scripts/scenario/generate_scenario.py /path/to/controller --context-path /api/v1

# Bearer 토큰 인증
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --auth-bearer-token "your-jwt-token" \
  --auth-annotations UserCert Authenticated

# Basic 인증
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --auth-basic-token "username:password"

# 커스텀 헤더
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --header "X-API-Key:your-api-key" \
  --header "X-Custom:value"

# Assertion 실패 시에도 계속 진행
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --continue-on-error

# 환경 지정
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --environment development

# 모든 옵션 사용
python3 scripts/scenario/generate_scenario.py /path/to/controller \
  --output /custom/path \
  --context-path /api/v1 \
  --auth-bearer-token "your-jwt-token" \
  --auth-basic-token "admin:password" \
  --header "X-API-Key:my-key" \
  --auth-annotations UserCert \
  --continue-on-error \
  --environment development

# 도움말
python3 scripts/scenario/generate_scenario.py --help
```

## 실제 사용 예제

### 1. 컨트롤러 파일 준비

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
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody UserDto userDto) {
        // ...
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        // ...
    }
}
```

### 2. 스크립트 실행

```bash
python3 scripts/scenario/generate_scenario.py \
  /Users/dev/myproject/src/main/java/com/example/controller/UserController.java
```

### 3. 결과 확인

```
🔍 컨트롤러 파싱 중: .../UserController.java
📊 발견된 엔드포인트: 5개
📁 출력 디렉토리: projects
  📝 생성됨: projects/user/scenario/getallusers.json
  📝 생성됨: projects/user/scenario/getuserbyid.json
  📝 생성됨: projects/user/scenario/createuser.json
  📝 생성됨: projects/user/scenario/updateuser.json
  📝 생성됨: projects/user/scenario/deleteuser.json
  📝 생성됨: projects/user/scenario/user_crud.json
  📝 생성됨: projects/user/scenario/user_integration.json
✅ 시나리오 파일 생성 완료: projects/user

🎉 완료!
```

### 4. 생성된 파일 구조 (폴더별 자동 정리)

```
projects/user/
└── scenario/
    ├── success/                     # 정상 시나리오
    │   ├── getallusers_success.json
    │   ├── getuserbyid_success.json
    │   ├── createuser_success.json
    │   ├── updateuser_success.json
    │   └── deleteuser_success.json
    ├── failure/                     # 실패 시나리오
    │   ├── createuser_failure_1.json    # 필수 필드 누락
    │   ├── createuser_failure_2.json    # 빈 본문
    │   ├── getuserbyid_failure_1.json   # 잘못된 ID (404)
    │   ├── updateuser_failure_1.json    # 존재하지 않는 리소스
    │   └── deleteuser_failure_1.json    # 존재하지 않는 리소스
    ├── integration/                 # 통합 테스트
    │   └── user_full_integration.json   # 모든 엔드포인트
    └── load_test/                   # 성능/부하 테스트
        ├── getallusers_load_test.json
        ├── getuserbyid_load_test.json
        └── user_stress_test.json        # 전체 스트레스 테스트
```

## 생성된 시나리오 커스터마이징

생성된 시나리오는 **초안**입니다. 프로젝트에 맞게 수정하세요:

### 1. 요청 본문 수정

```json
{
  "body": {
    "name": "Test User",        // ← 실제 필드명으로 수정
    "email": "test@example.com"  // ← 실제 데이터로 수정
  }
}
```

### 2. Assertion 추가/수정

```json
{
  "assertions": [
    {
      "field": "status",
      "operator": "eq",
      "value": 200
    },
    {
      "field": "body.username",    // ← 비즈니스 로직에 맞는 검증 추가
      "operator": "eq",
      "value": "testuser"
    }
  ]
}
```

### 3. 변수 추출 추가

```json
{
  "extract": {
    "user_id": "body.id",
    "username": "body.username"   // ← 필요한 변수 추가
  }
}
```

### 4. 호스트 설정

`projects/{project_name}/config/hosts.json` 파일 생성:

```json
{
  "default": {
    "base_url": "http://localhost:8080",
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "dev": {
    "base_url": "https://dev-api.example.com",
    "headers": {
      "Authorization": "Bearer ${API_KEY}"
    }
  }
}
```

## 샘플 컨트롤러로 테스트

테스트용 샘플 컨트롤러가 포함되어 있습니다:

```bash
python3 scripts/scenario/generate_scenario.py \
  scripts/scenario/sample_controller.java \
  --output projects
```

## 팁

1. **절대 경로 사용**: 컨트롤러 파일은 절대 경로로 지정하세요
2. **프로젝트별 관리**: 각 컨트롤러별로 별도 프로젝트 폴더가 생성됩니다
3. **CRUD 시나리오**: POST, GET(단일), DELETE가 있으면 자동으로 CRUD 시나리오가 생성됩니다
4. **Path Variable**: `{id}` 같은 경로 변수는 자동으로 `{{resource_id}}`로 변환됩니다

## 지원하는 어노테이션

### HTTP 메서드 매핑
- `@GetMapping` / `@GetMapping("/path")`
- `@PostMapping` / `@PostMapping("/path")`
- `@PutMapping` / `@PutMapping("/path")`
- `@DeleteMapping` / `@DeleteMapping("/path")`
- `@PatchMapping` / `@PatchMapping("/path")`
- `@RequestMapping` (클래스 레벨 - 베이스 경로)

### 파라미터 바인딩
- `@PathVariable` (경로 변수)
- `@RequestParam` (쿼리 파라미터)
- `@RequestBody` (요청 본문)
- `@ModelAttribute` (모델 속성 - Query Parameter로 변환)

### 인증 어노테이션 (--auth-annotations 옵션)
인증 헤더를 추가할 메서드를 식별하는 커스텀 어노테이션:
- `@UserCert`
- `@Authenticated`
- `@Secured`
- `@PreAuthorize`
- `@RolesAllowed`
- 프로젝트별 커스텀 어노테이션

## 인증 및 헤더 설정

### 1. Bearer 토큰 인증 (JWT)

#### 기본 사용
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/WorkerController.java \
  --auth-bearer-token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 특정 어노테이션이 있는 메서드에만 적용
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "your-token" \
  --auth-annotations UserCert Authenticated
```

#### 생성된 시나리오
```json
{
  "steps": [{
    "headers": {
      "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }]
}
```

### 2. Basic 인증

#### username:password 형식 (자동 Base64 인코딩)
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-basic-token "admin:password123"
```

#### 이미 인코딩된 토큰
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-basic-token "YWRtaW46cGFzc3dvcmQxMjM="
```

#### 생성된 시나리오
```json
{
  "steps": [{
    "headers": {
      "Authorization": "Basic YWRtaW46cGFzc3dvcmQxMjM="
    }
  }]
}
```

### 3. 커스텀 헤더

#### 단일 헤더
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --header "X-API-Key:your-api-key-here"
```

#### 여러 헤더
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --header "X-API-Key:my-key" \
  --header "X-Tenant-ID:tenant-001" \
  --header "X-Request-ID:req-12345"
```

#### 생성된 시나리오
```json
{
  "steps": [{
    "headers": {
      "X-API-Key": "my-key",
      "X-Tenant-ID": "tenant-001",
      "X-Request-ID": "req-12345"
    }
  }]
}
```

### 4. 모든 인증 방식 조합

```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --header "X-API-Key:api-key" \
  --header "X-Custom:value" \
  --auth-annotations UserCert
```

#### 생성된 시나리오
```json
{
  "steps": [{
    "headers": {
      "Authorization": "Bearer jwt-token",
      "X-API-Key": "api-key",
      "X-Custom": "value"
    }
  }]
}
```

### 5. 인증 모드 (Auth Mode)

인증 적용 방식을 두 가지 모드로 선택할 수 있습니다:

#### Include 모드 (기본값)
특정 어노테이션이 있는 메서드만 인증이 필요한 경우:

Java 컨트롤러:
```java
@RestController
@RequestMapping("/api/worker")
public class WorkerController {
    
    @UserCert  // ← 이 어노테이션이 있으면 인증 필요
    @GetMapping("/{id}")
    public ResponseEntity getWorker(@PathVariable Long id) {
        // ...
    }
    
    @GetMapping("/public")  // ← 어노테이션 없으면 인증 불필요
    public ResponseEntity getPublicInfo() {
        // ...
    }
}
```

```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert \
  --auth-mode include  # 기본값이므로 생략 가능
```

생성된 시나리오:
- `getWorker`: Bearer 토큰 포함 (인증 필요)
- `getPublicInfo`: Bearer 토큰 제외 (인증 불필요)

#### Exclude 모드 (AOP 전역 인증)
기본적으로 모든 메서드에 AOP로 인증이 적용되고, 특정 어노테이션이 있으면 인증을 제외하는 경우:

Java 컨트롤러:
```java
@RestController
@RequestMapping("/api/worker")
public class WorkerController {
    
    @GetMapping("/{id}")
    public ResponseEntity getWorker(@PathVariable Long id) {
        // 기본적으로 인증 필요 (AOP)
    }
    
    @NoAuth  // ← 이 어노테이션이 있으면 인증 제외
    @GetMapping("/public")
    public ResponseEntity getPublicInfo() {
        // 인증 불필요
    }
}
```

```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations NoAuth PermitAll \
  --auth-mode exclude  # Exclude 모드 명시
```

생성된 시나리오:
- `getWorker`: Bearer 토큰 포함 (인증 필요)
- `getPublicInfo`: Bearer 토큰 제외 (인증 제외 어노테이션 있음)

#### 실제 사용 예제

**Include 모드 예제 (Spring Security @PreAuthorize)**
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations PreAuthorize Secured RolesAllowed \
  --auth-mode include
```

**Exclude 모드 예제 (커스텀 AOP + @NoAuth)**
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations NoAuth PermitAll PublicAPI \
  --auth-mode exclude
```

### 6. 어노테이션 조건부 적용 및 Pre-request 매핑

#### 단순 인증 헤더만 적용
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert
```

#### Pre-request 라이브러리 매핑
특정 어노테이션이 있는 API에만 pre-request 스크립트를 실행하도록 매핑:

```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/WorkerController.java \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --header "X-Header-Extra-Info:{{USER_CERT_TOKEN}}"
```

생성된 시나리오:
```json
{
  "name": "Get Worker - Success Test",
  "pre_request_scripts": [
    "wpm-get-user-info.json"
  ],
  "steps": [{
    "headers": {
      "Authorization": "Bearer jwt-token",
      "X-Header-Extra-Info": "{{USER_CERT_TOKEN}}"
    }
  }]
}
```

#### 여러 어노테이션과 Pre-request 매핑
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert:wpm-get-user-info.json \
  --auth-annotations AdminAuth:admin-auth.json \
  --auth-annotations PublicAPI
```

- `@UserCert` → `wpm-get-user-info.json` 실행 후 인증 헤더 추가
- `@AdminAuth` → `admin-auth.json` 실행 후 인증 헤더 추가
- `@PublicAPI` → 인증 헤더만 추가 (pre-request 없음)

#### Pre-request 라이브러리 파일 위치
```
projects/{project}/package_library/
├── wpm-get-user-info.json
├── admin-auth.json
└── other-script.json
```

#### Pre-request 라이브러리 예시
`package_library/wpm-get-user-info.json`:
```json
{
  "name": "WPM User Authentication",
  "description": "Get user certification token before test execution",
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

#### 변수 치환 규칙
- `{{env.변수명}}`: 환경 파일 (`env/development.json`)에서 로드
- `{{변수명}}`: Pre-request에서 추출한 변수
- Pre-request에서 추출한 변수를 시나리오 헤더/본문에서 사용 가능

### 7. 기본 인증 토큰을 위한 Package Library 매핑

#### 개요
`--default-auth-token`에서 사용하는 토큰 값을 package library를 통해 동적으로 가져올 수 있습니다.

#### 사용 방법
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --auth-mode all \
  --default-auth bearer \
  --default-auth-token "{{USER_CERT_TOKEN}}" \
  --default-auth-library "get-user-token.json"
```

#### 동작 방식
1. 엔드포인트에 어노테이션/패키지 매핑이 없는 경우
2. `get-user-token.json` 라이브러리를 먼저 실행
3. 응답에서 `USER_CERT_TOKEN` 값을 추출
4. `Bearer {{USER_CERT_TOKEN}}` 헤더 적용

#### 기본 인증 라이브러리 예시
`package_library/get-user-token.json`:
```json
{
  "name": "Get User Authentication Token",
  "description": "사용자 인증 토큰을 동적으로 가져오는 pre-request 라이브러리",
  "steps": [
    {
      "name": "Get User Token",
      "method": "POST",
      "url": "{{env.BaseUrl}}/api/v2/auth/login",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "userId": "{{env.UserId}}",
        "userPassword": "{{env.UserPassword}}"
      },
      "extract": {
        "USER_CERT_TOKEN": "data.token"
      }
    }
  ]
}
```

#### 실제 사용 예시
```bash
python3 generate_scenario.py \
  /path/to/SgiController.java \
  --auth-mode all \
  --default-auth bearer \
  --default-auth-token "{{USER_CERT_TOKEN}}" \
  --default-auth-library "get-user-token.json" \
  --annotation-auth-mapping "NoAuth:basic:{{USER_ID}}:{{USER_PW}}"
```

생성된 시나리오:
```yaml
name: Get User Info - Success Test
pre_request_scripts:
  - get-user-token.json  # ← 기본 인증 라이브러리 추가됨
steps:
  - name: Get User Info
    method: GET
    url: /api/v2/user/info
    headers:
      Authorization: Bearer {{USER_CERT_TOKEN}}  # ← 라이브러리에서 추출한 토큰 사용
```

### 8. Package Library에서 Basic Auth 자동 인코딩

#### 개요
Package library 파일에서 `Authorization: "Basic {{env.USER_ID}}:{{env.USER_PW}}"` 형식으로 작성하면 자동으로 Base64 인코딩되어 요청됩니다.

#### 동작 방식
1. Package library에서 `Authorization` 헤더 감지
2. `Basic user:password` 형식인지 확인
3. 자동으로 Base64 인코딩: `Basic base64(user:password)`
4. 인코딩된 헤더로 HTTP 요청 실행

#### Package Library 예시
`package_library/capshome-user-auth.json`:
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

#### 실제 요청 예시
**Library 파일 작성:**
```json
"Authorization": "Basic {{env.USER_ID}}:{{env.USER_PW}}"
```

**환경 변수 (env/development.json):**
```json
{
  "params": {
    "USER_ID": "kimmo",
    "USER_PW": "11qqaa.."
  }
}
```

**변수 치환 후:**
```
Authorization: Basic kimmo:11qqaa..
```

**자동 Base64 인코딩 적용:**
```
Authorization: Basic a2ltbW86MTFxcWFhLi4=
```

#### 주의사항
- `:` (콜론)이 포함된 경우에만 자동 인코딩됩니다
- 이미 Base64로 인코딩된 값은 다시 인코딩하지 않습니다
- `Bearer` 토큰 등 다른 인증 방식은 영향받지 않습니다

#### 사용 예시
```bash
python3 generate_scenario.py \
  /path/to/SgiController.java \
  --auth-mode all \
  --default-auth bearer \
  --default-auth-token "{{USER_CERT_TOKEN}}" \
  --default-auth-library "capshome-user-auth.json"
```

## Continue on Error (Assertion 실패 시 계속 진행)

### 기능 설명
기본적으로 시나리오 실행 중 assertion이 실패하면 다음 스텝을 실행하지 않고 중단됩니다.
`--continue-on-error` 옵션을 사용하면 assertion이 실패해도 모든 API를 계속 테스트합니다.

### 사용 방법
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/controller \
  --continue-on-error
```

### 생성된 시나리오
```json
{
  "name": "Get Worker - Success Test",
  "continue_on_error": true,
  "steps": [...]
}
```

### 동작 방식
- **continue_on_error: false (기본값)**: 첫 번째 assertion 실패 시 시나리오 중단
- **continue_on_error: true**: 모든 스텝 실행, 실패한 스텝은 기록하고 계속 진행

### 사용 사례
1. **통합 테스트**: 모든 API 상태를 한 번에 확인
2. **Smoke Test**: 전체 시스템 헬스 체크
3. **디버깅**: 어떤 API가 실패하는지 전체 파악

## 문제 해결

### 엔드포인트를 찾을 수 없음

- 어노테이션 형식 확인 (`@GetMapping`, `@PostMapping` 등)
- public 메서드인지 확인
- 주석으로 감싸져 있지 않은지 확인

### 샘플 데이터가 부적절함

- 생성된 JSON 파일에서 `body` 필드를 직접 수정
- DTO 클래스명에 따라 샘플 데이터가 자동 생성됨:
  - `UserDto` → 사용자 샘플 데이터
  - `PostDto` / `ArticleDto` → 게시글 샘플 데이터
  - 기타 → 기본 샘플 데이터

### 경로가 잘못됨

- `@RequestMapping` 클래스 레벨 어노테이션 확인
- 베이스 경로와 메서드 경로가 올바르게 결합되는지 확인
