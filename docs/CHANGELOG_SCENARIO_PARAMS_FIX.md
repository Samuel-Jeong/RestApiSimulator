# 시나리오 생성 - 실패 케이스 파라미터 누락 수정

## 문제
시나리오 자동 생성 시 실패 케이스(401, 404)에서 **query parameter**와 **ModelAttribute 필드**가 반영되지 않는 문제

### 영향받는 시나리오
1. **401 Unauthorized**: 인증 실패 시나리오
2. **404 Not Found**: 존재하지 않는 리소스 시나리오

### 재현 예시
**DrgController.controlSiren API:**
```java
@GetMapping("/drg/siren")
public ResponseEntity<RestResponseDto<Void>> controlSiren(
    @RequestParam("deviceId") String deviceId,
    @RequestParam("type") Integer type
)
```

**생성된 401 시나리오 (문제):**
```yaml
steps:
- name: Control Siren - Unauthorized
  method: GET
  path: /api/v2/user/device/drg/siren
  # ❌ query_params 누락! deviceId, type 파라미터가 없음
  assertions:
  - field: status
    operator: eq
    value: 401
```

**실제 필요한 형태:**
```yaml
steps:
- name: Control Siren - Unauthorized
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:  # ✅ 파라미터 추가
    deviceId: "test-id-001"
    type: 1
  assertions:
  - field: status
    operator: eq
    value: 401
```

## 수정 내용

### 1. 401 Unauthorized 시나리오 (882-916줄)
**변경 전:**
```python
# 요청 본문이 있으면 추가
if endpoint['dto_fields']:
    body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
    step['body'] = body

# 헤더는 추가하지 않음 (인증 정보 없이 요청)
```

**변경 후:**
```python
# 요청 본문이 있으면 추가
if endpoint['dto_fields']:
    body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
    step['body'] = body

# Query 파라미터 추가 (일반 RequestParam)
query_params = {}
if endpoint['query_params']:
    for param in endpoint['query_params']:
        query_params[param] = "test"

# ModelAttribute 필드를 query parameter로 추가 (GET 요청)
if endpoint.get('model_attribute_fields'):
    for field_name, field_info in endpoint['model_attribute_fields'].items():
        query_params[field_name] = field_info['sample_value']

if query_params:
    step['query_params'] = query_params

# 헤더는 추가하지 않음 (인증 정보 없이 요청)
```

### 2. 404 Not Found 시나리오 (1319-1336줄)
**변경 전:**
```python
if endpoint['method'] == 'PUT' and endpoint['dto_fields']:
    body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
    step['body'] = body

self._add_headers(step, endpoint)
```

**변경 후:**
```python
if endpoint['method'] == 'PUT' and endpoint['dto_fields']:
    body = {name: info['sample_value'] for name, info in endpoint['dto_fields'].items()}
    step['body'] = body

# Query 파라미터 추가 (GET, DELETE에도 있을 수 있음)
query_params = {}
if endpoint['query_params']:
    for param in endpoint['query_params']:
        query_params[param] = "test"

# ModelAttribute 필드를 query parameter로 추가
if endpoint.get('model_attribute_fields'):
    for field_name, field_info in endpoint['model_attribute_fields'].items():
        query_params[field_name] = field_info['sample_value']

if query_params:
    step['query_params'] = query_params

self._add_headers(step, endpoint)
```

## 적용 방법

### 1. 시나리오 재생성
```bash
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator

# 스크립트 실행
./scripts/scenario/capshome/capshome_deviceuserapp_drgcontroller_run.sh
```

또는 직접 실행:
```bash
source venv/bin/activate

python3 scripts/scenario/generate_scenario.py \
  /Volumes/WORK/GIT_PROJECTS/TELCOWARE/sks-capshome-container-apps/app-mod/device-user-app/src/main/java/com/sks/capshome/device/drg/controller/DrgController.java \
  --output projects/capshome \
  --environment development \
  --context-path /api/v2/user/device \
  --auth-bearer-token "{{USER_CERT_TOKEN}}" \
  --auth-mode exclude \
  --auth-annotations NoAuth \
  --continue-on-error \
  --format yaml
```

### 2. 생성된 시나리오 확인
```bash
# 401 시나리오 확인
cat projects/capshome/drgcontroller/scenario/failure/controlsiren_failure_unauthorized_401.yaml

# query_params가 포함되어 있는지 확인
```

## 예상 결과

**수정 후 생성되는 401 시나리오:**
```yaml
name: Control Siren - Unauthorized Access
description: '실패 케이스 (401): 인증 정보 없이 접근'
host: default
tags:
- failure
- unauthorized
- '401'
- drgcontroller
continue_on_error: true
steps:
- name: Control Siren - Unauthorized
  method: GET
  path: /api/v2/user/device/drg/siren
  query_params:              # ✅ 추가됨
    deviceId: "test-id-001"  # ✅ 추가됨
    type: 1                  # ✅ 추가됨
  assertions:
  - field: status
    operator: eq
    value: 401
environment: development
```

## 영향받는 파일
- `scripts/scenario/generate_scenario.py`: 시나리오 생성 로직 수정

## 장점
1. **완전한 테스트**: 실패 케이스도 실제 API와 동일한 파라미터로 테스트
2. **정확한 검증**: 파라미터 누락으로 인한 400 에러 방지
3. **일관성**: 성공/실패 시나리오가 동일한 파라미터 구조 사용
4. **실제 환경 반영**: 프로덕션 환경과 동일한 조건으로 테스트

## 관련 API
- **RequestParam**: GET 요청의 query parameter
- **ModelAttribute**: Form 데이터 또는 query parameter로 전달되는 DTO

## 날짜
2026-01-28
