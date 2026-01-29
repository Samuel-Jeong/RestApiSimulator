# 테스트 결과 트리 구조 표시 개선 (Results Tree View Enhancement)

## 개요
테스트 결과를 프로젝트별, 폴더별 트리 구조로 표시하여 시나리오/프로젝트와 동일한 직관적인 탐색 경험 제공

## 변경된 파일

### 1. `app/core/project_manager.py`
**추가된 메서드:**
- `get_results_tree()`: 결과 파일을 트리 구조로 반환

**기능:**
- 폴더 구조를 계층적으로 표현
- 파일 메타데이터 포함 (크기, 수정 시간, 테스트 타입)
- 시나리오 테스트와 부하 테스트 구분
- 날짜별 폴더 자동 인식 (YYYYMMDD 형식)

**트리 구조:**
```
result/
├── 📁 scenarios (Scenario Tests)
│   ├── 📅 20260128
│   │   ├── [1] 📄 scenario_test1_20260128_150000 (15.2KB)
│   │   └── [2] 📄 scenario_test2_20260128_151000 (12.8KB)
│   └── 📅 20260127
│       └── [3] 📄 scenario_test3_20260127_180000 (18.5KB)
├── 📁 loadtests (Load Tests)
│   └── 📅 20260128
│       └── [4] ⚡ loadtest_performance_20260128_140000 (125.3KB)
└── 📁 exports
    └── 📅 20260128
        └── ...
```

### 2. `app/ui/app.py`
**수정된 메서드:**
- `__init__()`: `_results_index_map` 초기화 추가
- `show_results_screen()`: 트리 구조 표시로 변경
- `handle_results_input()`: 트리 인덱스 매핑 지원

**추가된 메서드:**
- `show_results_flat_view()`: 전체 결과를 플랫 리스트로 표시 (기존 방식)

**주요 기능:**
1. **트리 구조 표시**
   - 폴더별 계층 구조
   - 아이콘으로 타입 구분 (📄 시나리오, ⚡ 부하 테스트)
   - 파일 크기 표시
   - 번호 매핑으로 쉬운 선택

2. **타입별 구분**
   - Scenario Tests: 📄 아이콘
   - Load Tests: ⚡ 아이콘
   - 날짜 폴더: 📅 아이콘

3. **듀얼 뷰 지원**
   - 기본: 트리 뷰 (폴더 구조)
   - 'all' 명령: 플랫 뷰 (전체 리스트)

## 사용 방법

### 1. 트리 뷰 (기본)
```
╔═ TEST RESULTS - wpm/workercontroller ═══════════════════╗

Test Results by Folder:

📁 scenarios (Scenario Tests)
├── 📅 20260128
│   ├── [1] 📄 WorkerController - Full Integration Test (15.2KB)
│   ├── [2] 📄 WorkerController - CRUD Integration Test (12.8KB)
│   └── [3] 📄 createWorker_success (8.5KB)
└── 📅 20260127
    └── [4] 📄 WorkerController - Full Integration Test (18.5KB)

📁 loadtests (Load Tests)
└── 📅 20260128
    └── [5] ⚡ WorkerController - Load Test (125.3KB)

📊 Total: 5 result files

────────────────────────────────────────────────────────

Actions:
• Type result number to view details
• Type 'all' to list all results (flat view)
```

**명령어:**
- `숫자`: 해당 번호의 결과 상세 보기
- `all`: 플랫 뷰로 전환
- `back`: 분석 화면에서 목록으로 돌아가기

### 2. 플랫 뷰
```
╔═ TEST RESULTS (Flat View) - wpm/workercontroller ═══════╗

All Test Results (Total: 5):

📄 Scenario Tests (4):
  1. scenarios/20260128/scenario_test1.json
  2. scenarios/20260128/scenario_test2.json
  3. scenarios/20260128/scenario_test3.json
  4. scenarios/20260127/scenario_test4.json

⚡ Load Tests (1):
  5. loadtests/20260128/loadtest_performance.json

────────────────────────────────────────────────────────

Actions:
• Type result number to view details
• Type 'back' to return to tree view
```

**명령어:**
- `숫자`: 해당 번호의 결과 상세 보기
- `back`: 트리 뷰로 전환

## 장점

1. **직관적인 탐색**
   - 프로젝트/시나리오와 동일한 트리 구조
   - 폴더별 그룹화로 결과 찾기 쉬움
   - 날짜별 자동 정리

2. **풍부한 정보**
   - 파일 크기 표시
   - 테스트 타입 아이콘으로 즉시 구분
   - 총 파일 수 표시

3. **유연한 뷰**
   - 트리 뷰: 폴더 구조 탐색
   - 플랫 뷰: 전체 목록 확인
   - 자유롭게 전환 가능

4. **일관성**
   - 프로젝트 선택과 동일한 UX
   - 시나리오 선택과 동일한 번호 매핑
   - 통일된 인터페이스

5. **확장성**
   - 새로운 폴더 구조 자동 반영
   - 메타데이터 추가 가능
   - 필터링/정렬 기능 확장 가능

## 파일 메타데이터

각 결과 파일은 다음 정보를 포함:
- `name`: 파일명 (확장자 제외)
- `path`: 상대 경로
- `type`: 'file' 또는 'folder'
- `full_name`: 전체 파일명
- `size`: 파일 크기 (바이트)
- `modified`: 수정 시간 (timestamp)
- `test_type`: 'scenario', 'loadtest', 또는 'unknown'

## 폴더 구조 표준

결과 파일은 다음 구조로 저장:
```
result/
├── scenarios/      # 시나리오 테스트 결과
│   └── YYYYMMDD/   # 날짜별 폴더
├── loadtests/      # 부하 테스트 결과
│   └── YYYYMMDD/   # 날짜별 폴더
├── exports/        # 내보낸 분석 데이터
│   └── YYYYMMDD/   # 날짜별 폴더
└── uml/            # UML 다이어그램
    └── YYYYMMDD/   # 날짜별 폴더
```

## 호환성

- **하위 호환성**: 기존 번호 기반 접근도 지원 (Fallback)
- **폴더 없음**: 빈 폴더는 자동으로 숨김
- **권한 오류**: 접근 불가 폴더는 무시

## 향후 개선 계획

1. **필터링**: 날짜 범위, 테스트 타입으로 필터링
2. **정렬**: 이름, 날짜, 크기로 정렬
3. **검색**: 파일명 검색 기능
4. **통계**: 폴더별 통계 (성공률, 평균 시간 등)
5. **삭제**: 오래된 결과 자동 정리
6. **비교**: 두 결과 비교 기능

## 날짜
2026-01-28
