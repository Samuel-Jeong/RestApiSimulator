# REST API Simulator - 기능 목록

## 핵심 기능 (요구사항)

### ✅ 1. 프로그램 중복 실행 방지
- PID 기반 프로세스 락 메커니즘
- 기존 프로세스 실행 여부 체크
- 안전한 락 파일 관리
- **구현 위치**: `app/utils/lock.py`

### ✅ 2. TUI 기반 프로그램
- Textual 프레임워크 사용
- 직관적인 인터페이스
- 키보드 단축키 지원
- **구현 위치**: `app/ui/app.py`

### ✅ 3. 3단 레이아웃
- **상단**: 헤더 (타이틀, 시계)
- **중간**: 
  - 왼쪽: 메뉴 패널
  - 오른쪽: 컨텐츠 영역
- **하단**: 상태바 (진행률, 명령어 입력)
- **구현 위치**: `app/ui/app.py`

### ✅ 4. 프로젝트 폴더 관리
- `projects/` 디렉토리에서 프로젝트 자동 인식
- 프로젝트 생성/선택 기능
- 프로젝트별 독립적인 설정 관리
- **구현 위치**: `app/core/project_manager.py`

### ✅ 5. 시나리오 파일 읽기 (JSON)
- `scenario/` 폴더에서 JSON 시나리오 로드
- Pydantic 기반 스키마 검증
- 다양한 시나리오 지원
- **구현 위치**: `app/core/project_manager.py`, `app/models/scenario.py`

### ✅ 6. 호스트 설정 읽기 (JSON)
- `config/hosts.json`에서 API 호스트 정보 로드
- 다중 호스트 설정 지원
- 호스트별 헤더/타임아웃 설정
- **구현 위치**: `app/core/project_manager.py`, `app/models/config.py`

### ✅ 7. TPS 테스트 + 부하 테스트
- 목표 TPS 설정 및 실행
- 다양한 부하 분산 패턴 (constant, linear, exponential)
- Ramp-up 기능
- 실시간 메트릭 모니터링
- **구현 위치**: `app/core/load_test_engine.py`

### ✅ 8. 시나리오 테스트
- 커스텀 시나리오 실행
- 단계별 실행 및 검증
- 변수 추출 및 전달
- Assertion 기반 검증
- **구현 위치**: `app/core/scenario_engine.py`

### ✅ 9. 테스트 결과 저장
- `result/` 폴더에 JSON 형식 저장
- 타임스탬프 기반 파일명
- 상세한 메트릭 포함
- **구현 위치**: `app/core/report_generator.py`

### ✅ 10. 시나리오 UML 작성
- PlantUML 시퀀스 다이어그램
- PlantUML 플로우차트
- ASCII 텍스트 다이어그램
- **구현 위치**: `app/core/uml_generator.py`

## 추가 기능 (보완)

### ✅ 11. 실시간 모니터링 대시보드
- 테스트 진행 중 실시간 메트릭 표시
- TPS, 응답시간, 에러율 시각화
- 1초 단위 메트릭 수집
- **구현 위치**: `app/core/load_test_engine.py` (metrics_timeline)

### ✅ 12. 응답 시간 분석
- 평균, 최소, 최대 응답시간
- P50, P95, P99 백분위수
- 응답 시간 히스토그램 데이터
- **구현 위치**: `app/core/load_test_engine.py`, `app/models/result.py`

### ✅ 13. 에러 로깅 및 분석
- 스텝별 상세 에러 메시지
- 에러 유형별 분류 및 집계
- HTTP 상태 코드 분포
- **구현 위치**: `app/models/result.py`, `app/core/scenario_engine.py`

### ✅ 14. 시나리오 검증
- Pydantic 기반 자동 스키마 검증
- 필수 필드 체크
- 타입 검증
- **구현 위치**: `app/models/scenario.py`

### ✅ 15. 변수 시스템
- 시나리오 레벨 변수
- 스텝 간 변수 전달
- `{{variable}}` 문법 지원
- 응답에서 변수 추출
- **구현 위치**: `app/core/http_client.py`, `app/core/scenario_engine.py`

### ✅ 16. Assertion 엔진
- 다양한 비교 연산자 (eq, ne, gt, lt, gte, lte)
- 문자열 검증 (contains, regex)
- 배열 검증 (in, not_in)
- 존재 여부 검증 (exists)
- 중첩 필드 접근 (dot notation)
- **구현 위치**: `app/core/assertion_engine.py`

### ✅ 17. 재시도 메커니즘
- 스텝별 재시도 횟수 설정
- 실패 시 자동 재시도
- 재시도 간 딜레이
- **구현 위치**: `app/core/scenario_engine.py`

### ✅ 18. 조건부 실행
- `skip_on_failure` 옵션
- 스텝 실패 시 계속 진행 가능
- 시나리오 중단 제어
- **구현 위치**: `app/core/scenario_engine.py`

### ✅ 19. 딜레이 제어
- `delay_before`: 요청 전 대기
- `delay_after`: 요청 후 대기
- API 레이트 리밋 대응
- **구현 위치**: `app/core/http_client.py`

### ✅ 20. 동시성 제어
- 최대 동시 요청 수 제한
- 리소스 관리
- 안정적인 부하 테스트
- **구현 위치**: `app/core/load_test_engine.py`

### ✅ 21. 다중 호스트 지원
- 프로젝트당 여러 호스트 설정
- 호스트별 개별 설정 (타임아웃, 헤더)
- 시나리오별 호스트 선택
- **구현 위치**: `app/models/config.py`

### ✅ 22. 템플릿 시스템
- 예제 프로젝트 제공
- 샘플 시나리오 자동 생성
- 프로젝트 생성 시 기본 구조 제공
- **구현 위치**: `app/core/project_manager.py`

### ✅ 23. 상세한 리포트
- 시나리오 실행 결과
- 부하 테스트 결과
- 메트릭 타임라인
- 요약 정보
- **구현 위치**: `app/core/report_generator.py`

### ✅ 24. 완전한 문서화
- 사용자 가이드 (`docs/USER_GUIDE.md`)
- API 레퍼런스 (`docs/API_REFERENCE.md`)
- 기능 목록 (`docs/FEATURES.md`)
- README.md
- **구현 위치**: `docs/`, `README.md`

### ✅ 25. 예제 프로젝트
- JSONPlaceholder 기반 예제
- CRUD 시나리오
- 간단한 GET 시나리오
- 부하 테스트 시나리오
- **구현 위치**: `projects/example/`

## 아키텍처 특징

### 모듈화
- 명확한 책임 분리
- 독립적인 컴포넌트
- 쉬운 확장성

### 비동기 처리
- asyncio 기반
- 높은 성능
- 효율적인 리소스 사용

### 타입 안정성
- Pydantic 모델
- 타입 힌트
- 런타임 검증

### 에러 핸들링
- 적절한 예외 처리
- 명확한 에러 메시지
- 안정적인 실행

### 성능 최적화
- orjson 사용 (빠른 JSON 처리)
- httpx 사용 (async HTTP)
- 효율적인 메트릭 수집

## 보안 기능

### SSL 검증
- 기본적으로 SSL 인증서 검증
- 테스트 환경용 비활성화 옵션

### 안전한 파일 처리
- 경로 검증
- 안전한 파일 읽기/쓰기

### 프로세스 격리
- 중복 실행 방지
- 안전한 락 파일 관리

## 확장 가능한 기능

### 플러그인 시스템 (향후)
- 커스텀 assertion 추가
- 커스텀 리포트 포맷
- 커스텀 부하 패턴

### 통합 (향후)
- CI/CD 통합
- 웹훅 지원
- 알림 시스템

### 데이터 소스 (향후)
- CSV 데이터 로딩
- 데이터베이스 연동
- 외부 API 연동

## 품질 보증

### 코드 품질
- 타입 힌트 사용
- 명확한 네이밍
- 모듈화된 구조

### 안정성
- 예외 처리
- 리소스 관리
- 락 메커니즘

### 유지보수성
- 명확한 문서
- 예제 코드
- 일관된 패턴

## 성능 특징

- **고성능**: asyncio 기반 비동기 처리
- **확장성**: 높은 동시성 지원
- **효율성**: 메모리 및 CPU 효율적 사용
- **신뢰성**: 안정적인 에러 핸들링

## 사용성

- **직관적 UI**: TUI 기반 쉬운 인터페이스
- **완전한 문서**: 상세한 가이드 제공
- **예제 제공**: 즉시 사용 가능한 예제
- **에러 메시지**: 명확한 에러 안내

