# 자료형 기반 샘플 데이터 생성

## 문제

시나리오 자동 생성 시 모든 파라미터에 **"test"라는 문자열**만 사용하여 자료형 불일치 발생

### 기존 문제 (❌)

**Java Controller 실제 코드:**
```java
@GetMapping("/drg/siren")
public ResponseEntity<RestResponseDto<Void>> controlSiren(
    @RequestParam("deviceId") String deviceId,    // String 타입
    @RequestParam("type") Integer type             // Integer 타입
)
```

**생성된 시나리오 (문제):**
```yaml
query_params:
  deviceId: test    # String이지만 의미 없는 "test"
  type: test        # ❌ Integer인데 문자열 "test"!
```

**발생하는 문제:**
1. **타입 불일치**: Integer 파라미터에 문자열 전달
2. **400 Bad Request**: 서버에서 타입 변환 실패
3. **테스트 실패**: 정상 시나리오조차 실패
4. **수동 수정 필요**: 모든 파라미터를 일일이 수정해야 함

## 해결 방법

### 1. 자료형별 샘플 데이터 생성 함수 추가

**`_get_sample_value_for_type()` 메서드:**
```python
def _get_sample_value_for_type(self, type_name: str, param_name: str = "") -> Any:
    """
    자료형에 맞는 샘플 데이터 생성
    
    Args:
        type_name: Java 자료형 (String, Integer, Long, Boolean 등)
        param_name: 파라미터 이름 (의미있는 샘플 값 생성에 사용)
    
    Returns:
        자료형에 맞는 샘플 데이터
    """
```

**지원하는 자료형:**
- **String**: 파라미터 이름 기반 지능형 샘플 데이터
- **Integer, int**: 의미있는 정수 값
- **Long, long**: 큰 정수 값
- **Boolean, boolean**: true/false
- **Double, Float**: 실수 값
- **LocalDate, LocalDateTime, LocalTime**: 날짜/시간
- **List, Map**: 빈 컬렉션

### 2. 파라미터 파싱 시 자료형 정보 추출

**@RequestParam 파싱 개선:**
```python
# Before (자료형 무시)
result['query_params'].append(param_name)

# After (자료형 포함)
result['query_params'].append({
    'name': param_name,
    'type': param_type  # String, Integer 등
})
```

**@PathVariable 파싱 개선:**
```python
# Before
result['path_variables'].append(variable_name)

# After
result['path_variables'].append({
    'name': variable_name,
    'type': param_type
})
```

### 3. 시나리오 생성 시 자료형 기반 샘플 데이터 사용

**Success 시나리오:**
```python
for param in endpoint['query_params']:
    param_name = param['name'] if isinstance(param, dict) else param
    param_type = param['type'] if isinstance(param, dict) else 'String'
    query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
```

**Failure 시나리오 (401, 404):**
```python
for param in endpoint['query_params']:
    param_name = param['name'] if isinstance(param, dict) else param
    param_type = param['type'] if isinstance(param, dict) else 'String'
    query_params[param_name] = self.parser._get_sample_value_for_type(param_type, param_name)
```

**PathVariable 치환:**
```python
def _replace_path_variables(self, path: str, endpoint: Dict[str, Any] = None) -> str:
    # 자료형 정보 추출
    path_var_types = {}
    if endpoint and endpoint.get('path_variables'):
        for var in endpoint['path_variables']:
            if isinstance(var, dict):
                path_var_types[var['name']] = var['type']
    
    # 자료형 기반 샘플 값 생성
    if var_name in path_var_types:
        var_type = path_var_types[var_name]
        sample_value = self.parser._get_sample_value_for_type(var_type, var_name)
        return str(sample_value)
```

## 자료형별 샘플 데이터 규칙

### String 타입 (파라미터 이름 기반)

| 파라미터 이름 | 샘플 값 |
|-------------|---------|
| `*id*` | `"test-id-001"` |
| `*name*` | `"test-name"` |
| `*email*` | `"test@example.com"` |
| `*phone*`, `*tel*` | `"010-1234-5678"` |
| `*url*`, `*uri*` | `"https://example.com"` |
| `*code*` | `"TEST001"` |
| `*message*`, `*msg*` | `"test message"` |
| `*description*`, `*desc*` | `"test description"` |
| 기타 | `"test-value"` |

### Integer 타입 (파라미터 이름 기반)

| 파라미터 이름 | 샘플 값 |
|-------------|---------|
| `*page*` | `1` |
| `*size*`, `*limit*` | `10` |
| `*count*`, `*cnt*` | `5` |
| `*type*` | `1` |
| `*status*` | `1` |
| `*year*` | `2024` |
| `*month*` | `1` |
| `*day*` | `1` |
| 기타 | `1` |

### Long 타입

| 파라미터 이름 | 샘플 값 |
|-------------|---------|
| `*id*` | `1000` |
| `*time*`, `*timestamp*` | `1704067200000` |
| 기타 | `1000` |

### Boolean 타입

| 값 |
|----|
| `true` |

### Double/Float 타입

| 파라미터 이름 | 샘플 값 |
|-------------|---------|
| `*rate*`, `*ratio*` | `0.5` |
| `*price*`, `*amount*` | `1000.0` |
| `*percent*` | `50.0` |
| 기타 | `1.0` |

### Date/Time 타입

| 자료형 | 샘플 값 |
|-------|---------|
| `LocalDate`, `Date` | `"2024-01-01"` |
| `LocalDateTime`, `DateTime` | `"2024-01-01T00:00:00"` |
| `LocalTime` | `"00:00:00"` |

### Collection 타입

| 자료형 | 샘플 값 |
|-------|---------|
| `List`, `ArrayList`, `Set` | `[]` |
| `Map`, `HashMap` | `{}` |

## 실제 적용 예시

### DrgController.controlSiren

**Java 코드:**
```java
@GetMapping("/drg/siren")
public ResponseEntity<RestResponseDto<Void>> controlSiren(
    @RequestParam("deviceId") String deviceId,
    @RequestParam("type") Integer type
)
```

**생성된 Success 시나리오:**
```yaml
name: Control Siren - Success Test
steps:
- name: Control Siren - Success Case
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:
    deviceId: test-id-001  # ✅ String, "id" 포함 → test-id-001
    type: 1                # ✅ Integer → 1
  assertions:
  - field: status
    operator: eq
    value: 200
  headers:
    Authorization: Bearer {{USER_CERT_TOKEN}}
```

**생성된 401 Failure 시나리오:**
```yaml
name: Control Siren - Unauthorized Access
steps:
- name: Control Siren - Unauthorized
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:
    deviceId: test-id-001  # ✅ 자료형 기반 샘플 데이터
    type: 1                # ✅ Integer에 맞는 숫자
  assertions:
  - field: status
    operator: eq
    value: 401
```

### DrgController.controlVoice

**Java 코드:**
```java
@GetMapping("/drg/voice")
public ResponseEntity<RestResponseDto<Void>> controlVoice(
    @RequestParam("userId") String userId,
    @RequestParam("deviceId") String deviceId,
    @RequestParam("type") Integer type,
    @RequestParam("streamId") String streamId,
    @RequestParam("refNotiId") String refNotiId
)
```

**생성된 Success 시나리오:**
```yaml
name: Control Voice - Success Test
steps:
- name: Control Voice - Success Case
  method: GET
  path: /api/v2/user/device/drg/voice
  query_params:
    userId: test-id-001      # ✅ String, "id" 포함
    deviceId: test-id-001    # ✅ String, "id" 포함
    type: 1                  # ✅ Integer
    streamId: test-id-001    # ✅ String, "id" 포함
    refNotiId: test-id-001   # ✅ String, "id" 포함
  assertions:
  - field: status
    operator: eq
    value: 200
  headers:
    Authorization: Bearer {{USER_CERT_TOKEN}}
```

## 테스트 결과

**테스트 스크립트:** `test_sample_value_generation.py`

```
================================================================================
자료형별 샘플 데이터 생성 테스트
================================================================================

[테스트 1] ✅ PASS - String deviceId → "test-id-001"
[테스트 2] ✅ PASS - String userName → "test-name"
[테스트 3] ✅ PASS - String email → "test@example.com"
[테스트 4] ✅ PASS - String phone → "010-1234-5678"
[테스트 5] ✅ PASS - String code → "TEST001"
[테스트 6] ✅ PASS - String description → "test description"
[테스트 7] ✅ PASS - String value → "test-value"
[테스트 8] ✅ PASS - Integer type → 1
[테스트 9] ✅ PASS - Integer page → 1
[테스트 10] ✅ PASS - Integer size → 10
[테스트 11] ✅ PASS - Integer count → 5
[테스트 12] ✅ PASS - Integer status → 1
[테스트 13] ✅ PASS - Integer year → 2024
[테스트 14] ✅ PASS - int value → 1
[테스트 15] ✅ PASS - Long id → 1000
[테스트 16] ✅ PASS - Long timestamp → 1704067200000
[테스트 17] ✅ PASS - long value → 1000
[테스트 18] ✅ PASS - Boolean isActive → True
[테스트 19] ✅ PASS - Boolean hasPermission → True
[테스트 20] ✅ PASS - boolean enabled → True
[테스트 21] ✅ PASS - bool flag → True
[테스트 22] ✅ PASS - Double rate → 0.5
[테스트 23] ✅ PASS - Double price → 1000.0
[테스트 24] ✅ PASS - Float percent → 50.0
[테스트 25] ✅ PASS - float value → 1.0
[테스트 26] ✅ PASS - LocalDate date → "2024-01-01"
[테스트 27] ✅ PASS - LocalDateTime dateTime → "2024-01-01T00:00:00"
[테스트 28] ✅ PASS - LocalTime time → "00:00:00"
[테스트 29] ✅ PASS - List items → []
[테스트 30] ✅ PASS - ArrayList items → []
[테스트 31] ✅ PASS - Map data → {}
[테스트 32] ✅ PASS - List<String> items → []
[테스트 33] ✅ PASS - Map<String, Object> data → {}

================================================================================
테스트 결과: 33 passed, 0 failed (total: 33)
✅ 모든 테스트 통과!
================================================================================
```

## 장점

### 1. 타입 안전성
- **자료형 불일치 방지**: Integer에 Integer 값, String에 String 값
- **400 에러 방지**: 서버에서 타입 변환 실패 없음
- **즉시 실행 가능**: 생성 즉시 실행 가능한 시나리오

### 2. 의미 있는 테스트 데이터
- **파라미터 이름 기반**: `deviceId` → `"test-id-001"`, `type` → `1`
- **직관적**: 코드만 봐도 어떤 값이 들어갈지 예상 가능
- **실전적**: 실제 사용될 법한 값

### 3. 생산성 향상
- **수동 수정 불필요**: 모든 파라미터가 올바른 타입으로 생성
- **디버깅 시간 단축**: 타입 오류로 인한 실패 없음
- **유지보수 용이**: 자료형 변경 시 자동 반영

### 4. 확장성
- **새로운 타입 추가 용이**: `_get_sample_value_for_type` 함수만 수정
- **커스텀 규칙 추가 가능**: 파라미터 이름 패턴 추가
- **모든 어노테이션 지원**: RequestParam, PathVariable, ModelAttribute

## 영향받는 파일

### 수정된 파일
1. **scripts/scenario/generate_scenario.py**
   - `_get_sample_value_for_type()` 메서드 추가 (596줄)
   - `_parse_method_params()` 메서드 수정: 자료형 정보 포함
   - `_create_success_scenario()` 수정: 자료형 기반 샘플 데이터 사용
   - `_create_failure_scenarios()` 수정: 401, 404 시나리오도 적용
   - `_replace_path_variables()` 수정: PathVariable도 자료형 기반

### 생성된 파일
2. **test_sample_value_generation.py**
   - 자료형별 샘플 데이터 생성 테스트 (33개 케이스)

3. **docs/CHANGELOG_TYPE_BASED_SAMPLE_DATA.md**
   - 상세 변경 사항 및 사용법 문서

## Before / After 비교

### Before (❌)

**문제:**
- 모든 파라미터에 `"test"` 사용
- 타입 불일치로 400 에러 발생
- 수동 수정 필요

**생성된 시나리오:**
```yaml
query_params:
  deviceId: test    # String
  type: test        # ❌ Integer인데 문자열!
  userId: test      # String
  count: test       # ❌ Integer인데 문자열!
  isActive: test    # ❌ Boolean인데 문자열!
```

### After (✅)

**개선:**
- 자료형에 맞는 샘플 데이터
- 타입 오류 없음
- 즉시 실행 가능

**생성된 시나리오:**
```yaml
query_params:
  deviceId: test-id-001  # ✅ String, 의미있는 값
  type: 1                # ✅ Integer, 숫자!
  userId: test-id-001    # ✅ String, 의미있는 값
  count: 5               # ✅ Integer, 숫자!
  isActive: true         # ✅ Boolean, boolean!
```

## 관련 변경사항

이 변경은 다음 이슈들과 함께 해결됩니다:

1. **CHANGELOG_REQUESTPARAM_PARSING.md**
   - @RequestParam 어노테이션의 모든 형태 감지
   - 직접 값 지정 `@RequestParam("value")` 지원

2. **CHANGELOG_SCENARIO_PARAMS_FIX.md**
   - 401/404 실패 시나리오에 query_params 추가
   - ModelAttribute 필드도 반영

세 변경사항이 함께 적용되어야 완전한 시나리오 생성이 가능합니다.

## 시나리오 재생성 방법

```bash
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator

# DrgController 시나리오 재생성
./scripts/scenario/capshome/capshome_deviceuserapp_drgcontroller_run.sh

# 결과 확인
cat projects/capshome/drgcontroller/scenario/success/controlsiren_success.yaml
cat projects/capshome/drgcontroller/scenario/failure/controlsiren_failure_unauthorized_401.yaml
```

## 날짜
2026-01-28
