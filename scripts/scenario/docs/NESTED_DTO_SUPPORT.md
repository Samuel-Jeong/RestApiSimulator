# 중첩 DTO 분석 지원

## 개요

시나리오 생성기는 **중첩된 제네릭 DTO 구조**를 완벽하게 분석하여 시나리오를 생성합니다.

## 지원하는 구조

### 1. 단일 레벨 제네릭

```java
public DefaultResultDto<UserDto> getUser() {
    // ...
}
```

**추출 결과**: `UserDto`

### 2. 이중 중첩 제네릭 (가장 흔한 경우)

```java
public ResponseEntity<RestResponseDto<SgiTokenResDto>> login(
    HttpServletRequest request,
    @NotBlank @RequestHeader("X-Auth-Server") String xAuthServer,
    @Valid @RequestBody SgiLoginReqDto param
) throws Exception {
    // ...
}
```

**구조**:
- `ResponseEntity` (Wrapper 1)
  - `RestResponseDto` (Wrapper 2)
    - `SgiTokenResDto` (실제 DTO) ✅

**추출 결과**: `SgiTokenResDto`

### 3. 삼중 이상 중첩

```java
public Wrapper1<Wrapper2<Wrapper3<ActualDto>>> complexMethod() {
    // ...
}
```

**추출 결과**: `ActualDto`

### 4. 컬렉션 타입

```java
public ResponseEntity<List<UserDto>> getUsers() {
    // ...
}
```

**추출 결과**: `UserDto`

## 동작 원리

### 재귀적 제네릭 추출 알고리즘

```python
def _extract_response_type(self, return_type: str) -> Optional[str]:
    """
    재귀적으로 가장 안쪽 제네릭 타입 추출
    
    1. 첫 번째 < 찾기
    2. 대응하는 > 찾기 (괄호 균형 맞추기)
    3. 사이의 내용 추출
    4. 제네릭이 없으면 반환, 있으면 재귀
    """
```

### 예시 처리 과정

**입력**: `ResponseEntity<RestResponseDto<SgiTokenResDto>>`

1. **1단계**: `ResponseEntity<...>` 분석
   - 내부: `RestResponseDto<SgiTokenResDto>`
   - 제네릭 있음 → 계속 추출

2. **2단계**: `RestResponseDto<...>` 분석
   - 내부: `SgiTokenResDto`
   - 제네릭 없음 → 반환! ✅

**결과**: `SgiTokenResDto`

## 시나리오 생성 예시

### Java 컨트롤러

```java
@RestController
@RequestMapping("/api/v2/user")
public class SgiController {
    
    @PostMapping("/login")
    public ResponseEntity<RestResponseDto<SgiTokenResDto>> login(
        HttpServletRequest request,
        @NotBlank @RequestHeader("X-Auth-Server") String xAuthServer,
        @Valid @RequestBody SgiLoginReqDto param
    ) throws Exception {
        return ResponseEntity.ok(sgiService.login(request, xAuthServer, param));
    }
}
```

### 생성된 시나리오

```yaml
name: Login - Success Test
description: '정상 케이스: POST /api/v2/user/login'
steps:
  - name: Login - Success Case
    method: POST
    path: /api/v2/user/login
    headers:
      X-Auth-Server: CAPSHOME
    body:
      fcmToken: test
      osType: web
    assertions:
      - field: status
        operator: eq
        value: 200
      - field: body
        operator: exists
      - field: body.code
        operator: exists
      - field: body.message
        operator: exists
      - field: body.data            # ← RestResponseDto.data
        operator: exists
      - field: body.data.accessToken  # ← SgiTokenResDto.accessToken
        operator: exists
      - field: body.data.refreshToken # ← SgiTokenResDto.refreshToken
        operator: exists
```

## DTO 필드 분석

중첩된 DTO의 모든 필드가 분석되어 assertion이 자동 생성됩니다.

### DTO 구조

```java
// RestResponseDto.java
public class RestResponseDto<T> {
    private Integer code;
    private String message;
    private T data;  // ← 제네릭 타입
}

// SgiTokenResDto.java
public class SgiTokenResDto {
    private String accessToken;
    private String refreshToken;
    private String userId;
}
```

### 생성된 Assertions

```yaml
assertions:
  # RestResponseDto 필드
  - field: body.code
    operator: exists
  - field: body.message
    operator: exists
  - field: body.data
    operator: exists
  
  # SgiTokenResDto 필드 (data 안쪽)
  - field: body.data.accessToken
    operator: exists
  - field: body.data.refreshToken
    operator: exists
  - field: body.data.userId
    operator: exists
```

## 실제 테스트 결과

```bash
$ python3 test_nested_generic_extraction.py

================================================================================
Nested Generic Type Extraction Test
================================================================================

1. 이중 중첩 (ResponseEntity + RestResponseDto)
   Input:    ResponseEntity<RestResponseDto<SgiTokenResDto>>
   Expected: SgiTokenResDto
   Result:   SgiTokenResDto
   ✅ PASS

2. 삼중 중첩
   Input:    Wrapper1<Wrapper2<Wrapper3<ActualDto>>>
   Expected: ActualDto
   Result:   ActualDto
   ✅ PASS

3. 단일 제네릭
   Input:    DefaultResultDto<DrgInfGetBatteryStatusRes>
   Expected: DrgInfGetBatteryStatusRes
   Result:   DrgInfGetBatteryStatusRes
   ✅ PASS

4. 제네릭 없음
   Input:    String
   Expected: String
   Result:   String
   ✅ PASS

5. ResponseEntity<String>
   Input:    ResponseEntity<String>
   Expected: String
   Result:   String
   ✅ PASS

6. ResponseEntity<Void>
   Input:    ResponseEntity<Void>
   Expected: Void
   Result:   Void
   ✅ PASS

7. List 내부 타입 추출
   Input:    ResponseEntity<List<UserDto>>
   Expected: UserDto
   Result:   UserDto
   ✅ PASS

8. 실제 CAPSHOME 예시
   Input:    ResponseEntity<RestResponseDto<ResTokenRefreshDto>>
   Expected: ResTokenRefreshDto
   Result:   ResTokenRefreshDto
   ✅ PASS

================================================================================
Test Results: 8 passed, 0 failed
================================================================================
```

## 제한사항

### 1. DTO 파일 위치

DTO 파일이 다음 위치에 있어야 자동 파싱됩니다:
- `src/main/java/**/*.java`
- Import 경로를 따라 탐색

### 2. 순환 참조

DTO 간 순환 참조는 무한 루프를 방지하기 위해 캐싱으로 처리됩니다.

### 3. 복잡한 제네릭

다음과 같은 매우 복잡한 경우는 제한적으로 지원될 수 있습니다:
```java
Map<String, List<ComplexDto<InnerDto>>>
```

## 관련 문서

- [USAGE.md](./USAGE.md) - 전체 사용법
- [README.md](./README.md) - 시나리오 생성기 개요

## 변경 이력

- **2026-02-03**: 중첩 제네릭 완벽 지원 추가 (재귀적 추출 알고리즘)
