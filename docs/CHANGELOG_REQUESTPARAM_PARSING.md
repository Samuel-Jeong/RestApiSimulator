# @RequestParam 어노테이션 파싱 개선

## 문제

시나리오 자동 생성 시 `@RequestParam` 어노테이션의 **다양한 형태를 감지하지 못하는** 문제

### 감지 못했던 형태 (❌)

**가장 흔한 형태 - 직접 값 지정:**
```java
@RequestParam("deviceId") String deviceId
@RequestParam("type") Integer type
```

**value 속성 사용:**
```java
@RequestParam(value="deviceId") String deviceId
@RequestParam(value="type", required=true) Integer type
```

### 감지 가능했던 형태 (✅)

**name 속성만 가능:**
```java
@RequestParam(name="deviceId") String deviceId  // 이것만 가능
@RequestParam String deviceId                    // 속성 없음 (변수명 사용)
```

## 실제 사례

**DrgController.controlSiren:**
```java
@GetMapping("/drg/siren")
public ResponseEntity<RestResponseDto<Void>> controlSiren(
    @RequestParam("deviceId") String deviceId,    // ❌ 감지 안됨
    @RequestParam("type") Integer type             // ❌ 감지 안됨
)
```

**생성된 시나리오 (문제):**
```yaml
steps:
- name: Control Siren - Success Case
  method: GET
  path: /api/v2/user/device/drg/siren
  # ❌ query_params가 없음!
```

**기대하는 시나리오:**
```yaml
steps:
- name: Control Siren - Success Case
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:              # ✅ 추가되어야 함
    deviceId: "test-id-001"
    type: 1
```

## 원인 분석

### 기존 정규식 (621줄)
```python
r'@RequestParam(?:\([^)]*name\s*=\s*["\'](\w+)["\'][^)]*\))?\s+[\w<>]+\s+(\w+)'
```

**문제점:**
1. `name=` 속성만 찾음
2. `value=` 속성 무시
3. 직접 값 지정 `@RequestParam("value")` 무시
4. 가장 흔한 형태를 감지 못함

## 수정 내용

### 새로운 파싱 로직

**정규식:**
```python
r'@RequestParam\s*(?:\(([^)]*)\))?\s+(?:@[\w]+\s+)*[\w<>]+\s+(\w+)'
```

**파싱 알고리즘:**
```python
for match in param_matches:
    annotation_content = match.group(1)  # 괄호 안 내용
    variable_name = match.group(2)       # 변수명
    
    param_name = None
    
    if annotation_content:
        # 1. value 또는 name 속성에서 추출
        attr_match = re.search(r'(?:value|name)\s*=\s*["\'](\w+)["\']', annotation_content)
        if attr_match:
            param_name = attr_match.group(1)
        else:
            # 2. 직접 값 지정: @RequestParam("paramName")
            direct_match = re.search(r'^["\'](\w+)["\']', annotation_content.strip())
            if direct_match:
                param_name = direct_match.group(1)
    
    # 3. 파라미터명을 찾지 못했으면 변수명 사용
    if not param_name:
        param_name = variable_name
    
    result['query_params'].append(param_name)
```

## 지원하는 형태

### ✅ 모든 형태 지원

**1. 직접 값 지정 (가장 흔함):**
```java
@RequestParam("deviceId") String deviceId
@RequestParam("type") Integer type
```

**2. value 속성:**
```java
@RequestParam(value="deviceId") String deviceId
@RequestParam(value="type", required=true) Integer type
```

**3. name 속성:**
```java
@RequestParam(name="deviceId") String deviceId
@RequestParam(name="type") Integer type
```

**4. 속성 없음 (변수명 사용):**
```java
@RequestParam String deviceId
@RequestParam Integer type
```

**5. 복합 속성:**
```java
@RequestParam(value="deviceId", required=true, defaultValue="default") String deviceId
```

**6. required만:**
```java
@RequestParam(required=false) String deviceId
```

**7. Validation 어노테이션과 함께:**
```java
@RequestParam("deviceId") @NotBlank String deviceId
@RequestParam(value="soundType") @NotNull Integer soundType
```

## 테스트 결과

**테스트 스크립트:** `test_requestparam_parsing.py`

```
======================================================================
@RequestParam 파싱 테스트
======================================================================

[테스트 1] 직접 값 지정: ✅ PASS
[테스트 2] value 속성: ✅ PASS
[테스트 3] name 속성: ✅ PASS
[테스트 4] 속성 없음: ✅ PASS
[테스트 5] 복합 속성: ✅ PASS
[테스트 6] required만: ✅ PASS
[테스트 7] validation 어노테이션: ✅ PASS
[테스트 8] DrgController 실제 코드: ✅ PASS
[테스트 9] 줄바꿈: ✅ PASS

======================================================================
✅ 모든 테스트 통과!
======================================================================
```

## 적용 방법

### 1. 시나리오 재생성 필요

수정된 파싱 로직을 적용하려면 **시나리오를 다시 생성**해야 합니다:

```bash
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator

# DrgController 시나리오 재생성
./scripts/scenario/capshome/capshome_deviceuserapp_drgcontroller_run.sh
```

### 2. 생성 후 확인

```bash
# Success 시나리오 확인
cat projects/capshome/drgcontroller/scenario/success/controlsiren_success.yaml

# Failure 시나리오 확인
cat projects/capshome/drgcontroller/scenario/failure/controlsiren_failure_unauthorized_401.yaml
```

### 3. 예상 결과

**수정 후 생성될 시나리오:**
```yaml
name: Control Siren - Success Case
steps:
- name: Control Siren - Success Case
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:              # ✅ 이제 생성됨!
    deviceId: "test-id-001"
    type: 1
  assertions:
  - field: status
    operator: eq
    value: 200
  headers:
    Authorization: Bearer {{USER_CERT_TOKEN}}
```

## 영향받는 파일

- `scripts/scenario/generate_scenario.py`: `_parse_method_params()` 메서드 수정
- `test_requestparam_parsing.py`: 파싱 로직 테스트 스크립트 추가

## 장점

1. **완전한 지원**: 모든 @RequestParam 형태 감지
2. **실전 반영**: 가장 흔한 형태 (직접 값 지정) 지원
3. **유연성**: 다양한 속성 조합 처리
4. **검증**: 9가지 테스트 케이스로 검증
5. **안정성**: 변수명 fallback으로 안정적

## 기술적 개선

### Before
- **단순 정규식**: `name=` 속성만 찾음
- **제한적**: 2가지 형태만 지원
- **실전 미흡**: 가장 흔한 형태 누락

### After
- **2단계 파싱**: 정규식 + 로직 조합
- **완전 지원**: 모든 형태 커버
- **실전 최적화**: 직접 값 지정 우선 지원
- **Fallback**: 변수명 사용 보장

## 관련 변경

이 수정은 다음 이슈와 함께 해결됩니다:
- **CHANGELOG_SCENARIO_PARAMS_FIX.md**: 401/404 시나리오에 query_params 추가
- 두 변경사항이 함께 적용되어야 완전한 시나리오 생성

## 날짜
2026-01-28
