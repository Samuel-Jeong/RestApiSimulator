# Context Path 기능

## 🎯 기능 설명

API 시나리오 생성 시 **context path를 지정**할 수 있습니다.

### 사용 사례
- 버전별 API: `/api/v1`, `/api/v2`
- 서비스별 API: `/api/users`, `/api/products`
- 환경별 API: `/dev/api`, `/prod/api`

---

## 📋 사용법

### 기본 사용 (context path 없음)
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/WorkerController.java \
  --output projects/wpm
```

**생성된 경로:**
```json
{
  "path": "/worker/1/commute"
}
```

---

### Context Path 지정
```bash
python3 scripts/scenario/generate_scenario.py \
  /path/to/WorkerController.java \
  --output projects/wpm \
  --context-path /api/v1
```

**실행 화면:**
```
🚀 시나리오 자동 생성 시작
📂 입력: /path/to/WorkerController.java
📂 출력: projects/wpm
🔗 Context Path: /api/v1
📊 발견된 엔드포인트: 4개
```

**생성된 경로:**
```json
{
  "path": "/api/v1/worker/1/commute"
}
```

---

## 🔧 다양한 사용 예시

### 1. 버전별 API 관리

#### API v1
```bash
python3 scripts/scenario/generate_scenario.py \
  UserController.java \
  --output projects/myapp/v1 \
  --context-path /api/v1
```

**결과:**
```json
{
  "name": "Get User - Success Test",
  "path": "/api/v1/users/1"
}
```

#### API v2
```bash
python3 scripts/scenario/generate_scenario.py \
  UserControllerV2.java \
  --output projects/myapp/v2 \
  --context-path /api/v2
```

**결과:**
```json
{
  "name": "Get User - Success Test",
  "path": "/api/v2/users/1"
}
```

---

### 2. 마이크로서비스별 Context Path

#### User Service
```bash
python3 scripts/scenario/generate_scenario.py \
  controller/ \
  --output projects/user-service \
  --context-path /api/users
```

**결과:**
```json
{
  "path": "/api/users/profile"
}
```

#### Order Service
```bash
python3 scripts/scenario/generate_scenario.py \
  controller/ \
  --output projects/order-service \
  --context-path /api/orders
```

**결과:**
```json
{
  "path": "/api/orders/checkout"
}
```

---

### 3. 환경별 Context Path

#### Development
```bash
python3 scripts/scenario/generate_scenario.py \
  controller/ \
  --output projects/myapp/dev \
  --context-path /dev/api
```

**결과:**
```json
{
  "path": "/dev/api/users/1"
}
```

#### Production
```bash
python3 scripts/scenario/generate_scenario.py \
  controller/ \
  --output projects/myapp/prod \
  --context-path /api
```

**결과:**
```json
{
  "path": "/api/users/1"
}
```

---

## 📌 옵션 상세

### --context-path (또는 -c)

**형식:**
```bash
--context-path <경로>
-c <경로>
```

**특징:**
- 선택적 파라미터 (기본값: 빈 문자열)
- 자동으로 슬래시(`/`) 정규화
- 모든 엔드포인트 경로 앞에 추가됨

**슬래시 처리:**
```bash
# 아래 모두 동일하게 처리됨
--context-path /api/v1
--context-path /api/v1/
--context-path api/v1
```

**결과:** 모두 `/api/v1`로 정규화

---

## 🔍 동작 원리

### 1. 컨트롤러 파싱
```java
@RestController
@RequestMapping("/worker")
public class WorkerController {
    
    @PostMapping("/{contractIdx}/commute")
    public ResponseEntity checkInOut(...) {
        // ...
    }
}
```

### 2. 경로 생성 로직
```python
# context_path: "/api/v1"
# controller_base_path: "/worker"
# method_path: "/{contractIdx}/commute"

full_path = context_path + controller_base_path + method_path
# 결과: "/api/v1/worker/{contractIdx}/commute"
```

### 3. Path Variable 치환
```python
# full_path: "/api/v1/worker/{contractIdx}/commute"
# {contractIdx} → 1

final_path = "/api/v1/worker/1/commute"
```

---

## 📊 비교표

| Context Path | Controller Path | Method Path | 최종 결과 |
|-------------|----------------|-------------|----------|
| (없음) | `/worker` | `/{id}/commute` | `/worker/1/commute` |
| `/api` | `/worker` | `/{id}/commute` | `/api/worker/1/commute` |
| `/api/v1` | `/worker` | `/{id}/commute` | `/api/v1/worker/1/commute` |
| `/api/v2` | `/worker` | `/{id}/commute` | `/api/v2/worker/1/commute` |

---

## 🎯 실제 사용 예제

### SKS WPM 프로젝트 - v1 API

```bash
python3 scripts/scenario/generate_scenario.py \
  /Volumes/WORK/GIT_PROJECTS/TELCOWARE/sks-wpm-container-apps/app-mod/worker-app/src/main/java/com/sks/wpm/controller/WorkerController.java \
  --output projects/wpm \
  --context-path /api/v1
```

**생성된 시나리오:**
```json
{
  "name": "Check In Out - Success Test",
  "description": "정상 케이스: POST /api/v1/worker/{contractIdx}/commute",
  "host": "default",
  "steps": [{
    "name": "Check In Out - Success Case",
    "method": "POST",
    "path": "/api/v1/worker/1/commute",
    "body": {
      "workerHistoryIdx": 1,
      "workingDatetime": "test",
      "memo": "test"
    }
  }]
}
```

---

## 💡 활용 팁

### 1. 버전 관리
```bash
# v1과 v2 API를 별도로 생성
python3 generate_scenario.py controller/ -o projects/v1 -c /api/v1
python3 generate_scenario.py controller/ -o projects/v2 -c /api/v2
```

### 2. A/B 테스트
```bash
# 기존 API
python3 generate_scenario.py controller/ -o projects/old -c /api

# 신규 API
python3 generate_scenario.py controller/ -o projects/new -c /api/v2
```

### 3. 환경별 설정
```bash
# hosts.json에 환경별 host 설정
{
  "dev": {
    "base_url": "http://dev.example.com/dev/api"
  },
  "prod": {
    "base_url": "http://example.com/api"
  }
}

# 시나리오는 환경에 맞게 생성
python3 generate_scenario.py controller/ -o projects/dev -c /dev/api
python3 generate_scenario.py controller/ -o projects/prod -c /api
```

---

## 🚨 주의사항

### 1. 중복 슬래시
Context path는 자동으로 정규화되므로 중복 슬래시를 걱정할 필요 없습니다.

**모두 동일한 결과:**
```bash
--context-path /api/v1
--context-path /api/v1/
--context-path api/v1
```

### 2. 통합 시나리오
통합 시나리오(integration)에서도 context path가 모든 단계에 적용됩니다.

```json
{
  "name": "Full Integration Test",
  "steps": [
    {
      "name": "Step 1",
      "path": "/api/v1/worker/{contractIdx}/commute/today"
    },
    {
      "name": "Step 2",
      "path": "/api/v1/worker/{contractIdx}/commute/list"
    }
  ]
}
```

### 3. 부하 테스트
부하 테스트 시나리오에도 context path가 적용됩니다.

---

## ✨ 장점

✅ **유연성**: 다양한 API 구조 지원  
✅ **버전 관리**: API 버전별 시나리오 관리 용이  
✅ **환경 대응**: 환경별 경로 설정 가능  
✅ **마이크로서비스**: 서비스별 context path 지원  
✅ **자동화**: 수동 경로 수정 불필요

---

## 🔄 기존 시나리오 마이그레이션

### Before (수동 수정)
```json
{
  "path": "/worker/1/commute"
}
```
↓ 수동으로 편집
```json
{
  "path": "/api/v1/worker/1/commute"
}
```

### After (자동 생성)
```bash
python3 generate_scenario.py controller.java -c /api/v1
```
자동으로 생성됨:
```json
{
  "path": "/api/v1/worker/1/commute"
}
```

---

## 🎉 결론

이제 시나리오 생성 스크립트가:
- ✅ Context path 지정 가능 (`--context-path`)
- ✅ 모든 경로에 자동 적용
- ✅ 버전/환경별 API 관리 용이
- ✅ 마이크로서비스 아키텍처 지원

**유연하고 강력한 API 시나리오 생성이 가능합니다!** 🎊
