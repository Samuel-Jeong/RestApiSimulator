# 인증 모드 (Auth Mode) 가이드

시나리오 생성기는 두 가지 인증 적용 방식을 지원합니다.

## 개요

프로젝트마다 인증을 적용하는 방식이 다릅니다:
1. **특정 메서드만 인증**: 어노테이션이 있는 메서드만 인증 필요
2. **전역 인증 + 예외 처리**: AOP로 모든 메서드에 인증 적용, 특정 어노테이션으로 인증 제외

`--auth-mode` 옵션으로 이 두 가지 방식을 선택할 수 있습니다.

---

## Include 모드 (기본값)

### 설명
특정 어노테이션이 **있는** 메서드만 인증이 필요한 경우 사용합니다.

### 동작 방식
```
어노테이션 있음 → 인증 필요 (Bearer 토큰 추가)
어노테이션 없음 → 인증 불필요 (Bearer 토큰 제외)
```

### Java 코드 예제
```java
@RestController
@RequestMapping("/api/worker")
public class WorkerController {
    
    @UserCert  // ← 이 어노테이션이 있으면 인증 필요
    @GetMapping("/{id}")
    public ResponseEntity getWorker(@PathVariable Long id) {
        // 인증 필요한 API
    }
    
    @GetMapping("/public")  // ← 어노테이션 없음
    public ResponseEntity getPublicInfo() {
        // 인증 불필요한 API
    }
    
    @Authenticated  // ← 이 어노테이션이 있으면 인증 필요
    @PostMapping
    public ResponseEntity createWorker(@RequestBody WorkerDto dto) {
        // 인증 필요한 API
    }
}
```

### 사용 방법
```bash
python3 generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations UserCert Authenticated \
  --auth-mode include  # 기본값이므로 생략 가능
```

### 생성된 시나리오
```yaml
# getWorker - 인증 필요 (@UserCert 있음)
steps:
  - name: Get Worker
    headers:
      Authorization: Bearer jwt-token  # ← 추가됨

# getPublicInfo - 인증 불필요 (어노테이션 없음)
steps:
  - name: Get Public Info
    # headers에 Authorization 없음

# createWorker - 인증 필요 (@Authenticated 있음)
steps:
  - name: Create Worker
    headers:
      Authorization: Bearer jwt-token  # ← 추가됨
```

### 실패 시나리오 (401)
`@UserCert`나 `@Authenticated`가 있는 메서드에만 401 시나리오가 생성됩니다.

```yaml
# getWorker_failure_unauthorized_401.yaml
name: Get Worker - Unauthorized Access
steps:
  - name: Get Worker - Unauthorized
    # headers에 Authorization 없음 (인증 정보 제외)
    assertions:
      - field: status
        operator: eq
        value: 401
```

---

## Exclude 모드 (AOP 전역 인증)

### 설명
기본적으로 **모든 메서드**에 AOP로 인증이 적용되고, 특정 어노테이션이 **있으면** 인증을 **제외**하는 경우 사용합니다.

### 동작 방식
```
어노테이션 있음 → 인증 불필요 (Bearer 토큰 제외)
어노테이션 없음 → 인증 필요 (Bearer 토큰 추가)
```

### Java 코드 예제
```java
// AOP로 전역 인증 적용
@Aspect
public class AuthAspect {
    @Around("execution(* com.example.controller..*(..))")
    public Object authenticate(ProceedingJoinPoint joinPoint) {
        // 기본적으로 모든 컨트롤러 메서드에 인증 적용
        // @NoAuth가 있으면 인증 건너뜀
    }
}

@RestController
@RequestMapping("/api/worker")
public class WorkerController {
    
    @GetMapping("/{id}")
    public ResponseEntity getWorker(@PathVariable Long id) {
        // 어노테이션 없음 → AOP에 의해 인증 필요
    }
    
    @NoAuth  // ← 이 어노테이션이 있으면 인증 제외
    @GetMapping("/public")
    public ResponseEntity getPublicInfo() {
        // 인증 제외된 API
    }
    
    @PermitAll  // ← 이 어노테이션이 있으면 인증 제외
    @GetMapping("/health")
    public ResponseEntity healthCheck() {
        // 인증 제외된 API
    }
}
```

### 사용 방법
```bash
python3 generate_scenario.py \
  /path/to/controller \
  --auth-bearer-token "jwt-token" \
  --auth-annotations NoAuth PermitAll PublicAPI \
  --auth-mode exclude  # Exclude 모드 명시
```

### 생성된 시나리오
```yaml
# getWorker - 인증 필요 (어노테이션 없음)
steps:
  - name: Get Worker
    headers:
      Authorization: Bearer jwt-token  # ← 추가됨

# getPublicInfo - 인증 불필요 (@NoAuth 있음)
steps:
  - name: Get Public Info
    # headers에 Authorization 없음

# healthCheck - 인증 불필요 (@PermitAll 있음)
steps:
  - name: Health Check
    # headers에 Authorization 없음
```

### 실패 시나리오 (401)
`@NoAuth`, `@PermitAll` 등이 **없는** 메서드에만 401 시나리오가 생성됩니다.

```yaml
# getWorker_failure_unauthorized_401.yaml
name: Get Worker - Unauthorized Access
steps:
  - name: Get Worker - Unauthorized
    # headers에 Authorization 없음 (인증 정보 제외)
    assertions:
      - field: status
        operator: eq
        value: 401
```

---

## 비교표

| 항목 | Include 모드 | Exclude 모드 |
|------|-------------|-------------|
| **기본 동작** | 인증 불필요 | 인증 필요 (AOP) |
| **어노테이션 있음** | 인증 필요 | 인증 불필요 |
| **어노테이션 없음** | 인증 불필요 | 인증 필요 |
| **사용 케이스** | Spring Security `@PreAuthorize`, `@Secured` | 커스텀 AOP + `@NoAuth`, `@PermitAll` |
| **옵션** | `--auth-mode include` (기본값) | `--auth-mode exclude` |

---

## 실제 사용 예제

### Include 모드 예제 (Spring Security)

프로젝트 구조:
```java
@RestController
public class UserController {
    @PreAuthorize("hasRole('USER')")  // Spring Security 어노테이션
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) { }
    
    @GetMapping("/users/public")  // 어노테이션 없음 → public
    public List<User> getPublicUsers() { }
}
```

시나리오 생성:
```bash
python3 generate_scenario.py \
  /path/to/UserController.java \
  --auth-bearer-token "eyJhbGciOiJIUzI1NiIsInR5cCI6..." \
  --auth-annotations PreAuthorize Secured RolesAllowed \
  --auth-mode include
```

결과:
- `getUser`: Bearer 토큰 포함 + 401 실패 시나리오 생성
- `getPublicUsers`: Bearer 토큰 제외 + 401 실패 시나리오 없음

---

### Exclude 모드 예제 (커스텀 AOP)

프로젝트 구조:
```java
// 전역 AOP 인증
@Aspect
public class GlobalAuthAspect {
    @Around("execution(* com.example.controller..*(..))")
    public Object authenticate(ProceedingJoinPoint joinPoint) {
        Method method = ((MethodSignature) joinPoint.getSignature()).getMethod();
        
        // @NoAuth가 있으면 인증 건너뜀
        if (method.isAnnotationPresent(NoAuth.class)) {
            return joinPoint.proceed();
        }
        
        // 그 외에는 모두 인증 체크
        validateAuth();
        return joinPoint.proceed();
    }
}

@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) { 
        // 어노테이션 없음 → AOP에 의해 인증 필요
    }
    
    @NoAuth  // 인증 제외
    @GetMapping("/users/public")
    public List<User> getPublicUsers() { }
    
    @NoAuth  // 인증 제외
    @GetMapping("/health")
    public String healthCheck() { }
}
```

시나리오 생성:
```bash
python3 generate_scenario.py \
  /path/to/UserController.java \
  --auth-bearer-token "eyJhbGciOiJIUzI1NiIsInR5cCI6..." \
  --auth-annotations NoAuth PermitAll \
  --auth-mode exclude
```

결과:
- `getUser`: Bearer 토큰 포함 + 401 실패 시나리오 생성
- `getPublicUsers`: Bearer 토큰 제외 + 401 실패 시나리오 없음
- `healthCheck`: Bearer 토큰 제외 + 401 실패 시나리오 없음

---

## 예제 스크립트

프로젝트에 예제 스크립트가 포함되어 있습니다:

### Include 모드 예제
```bash
bash scripts/scenario/example_auth_mode_include.sh
```

### Exclude 모드 예제
```bash
bash scripts/scenario/example_auth_mode_exclude.sh
```

---

## 문제 해결

### Q1: 어떤 모드를 사용해야 하나요?

**Include 모드 사용:**
- Spring Security `@PreAuthorize`, `@Secured` 사용
- 대부분의 API가 public이고 일부만 인증 필요
- 명시적으로 어노테이션을 붙인 메서드만 보호

**Exclude 모드 사용:**
- 커스텀 AOP로 전역 인증 적용
- 대부분의 API가 private이고 일부만 public
- 기본적으로 모든 메서드가 인증 필요하고, 예외만 `@NoAuth` 같은 어노테이션으로 표시

### Q2: auth-annotations를 비워두면?

**Include 모드:**
- 모든 메서드가 인증 불필요
- Bearer 토큰이 어디에도 추가되지 않음

**Exclude 모드:**
- 모든 메서드가 인증 필요
- 모든 메서드에 Bearer 토큰 추가됨

### Q3: 여러 어노테이션을 지정하면?

두 모드 모두 OR 조건으로 동작합니다.

**Include 모드:**
```bash
--auth-annotations UserCert Authenticated Secured
```
→ `@UserCert`, `@Authenticated`, `@Secured` 중 하나라도 있으면 인증 필요

**Exclude 모드:**
```bash
--auth-annotations NoAuth PermitAll PublicAPI
```
→ `@NoAuth`, `@PermitAll`, `@PublicAPI` 중 하나라도 있으면 인증 불필요

---

## 참고 자료

- [USAGE.md](./USAGE.md) - 전체 사용법
- [FEATURES.md](./FEATURES.md) - 기능 설명
- [generate_scenario.py](./generate_scenario.py) - 소스 코드
