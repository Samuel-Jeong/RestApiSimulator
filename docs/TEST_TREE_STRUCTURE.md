# 시나리오 트리 구조 표시 기능

## 변경 사항

### 1. `app/core/project_manager.py`

#### 수정된 메서드
- `list_scenarios()`: 이제 하위 폴더 경로를 포함한 시나리오 리스트 반환
- `load_scenario()`: 경로 형식 시나리오 로딩 지원 (예: `success/test_api`)

#### 새로운 메서드
- `get_scenario_tree()`: 폴더 구조를 트리 형태로 반환

```python
{
    'name': 'scenario',
    'path': '',
    'type': 'folder',
    'children': [
        {
            'name': 'success',
            'path': 'success',
            'type': 'folder',
            'children': [
                {
                    'name': 'test_api',
                    'path': 'success/test_api',
                    'type': 'file'
                }
            ]
        }
    ]
}
```

### 2. `app/ui/app.py`

#### 수정된 메서드
- `show_scenarios_screen()`: 트리 구조로 시나리오 표시
  - 폴더: `📁 folder_name/`
  - 파일: `[ 1] 📄 file_name`
  - 번호 매핑 저장: `_scenario_index_map`

- `handle_scenario_input()`: 번호 입력 시 매핑된 경로 사용

## 사용 예시

### 폴더 구조
```
projects/example/scenario/
├── success/
│   ├── simple_get.json
│   ├── user_crud.json
│   └── local_test.json
├── failure/
│   └── (empty)
├── integration/
│   └── complex_workflow.json
└── load_test/
    ├── load_test_scenario.json
    └── stress_test.json
```

### UI 표시
```
╔═ SCENARIOS - example ═══════════════════════╗

Available Scenarios:

├── 📁 failure/
├── 📁 integration/
│   └── [ 1] 📄 complex_workflow
├── 📁 load_test/
│   ├── [ 2] 📄 load_test_scenario
│   └── [ 3] 📄 stress_test
└── 📁 success/
    ├── [ 4] 📄 local_test
    ├── [ 5] 📄 simple_get
    └── [ 6] 📄 user_crud

────────────────────────────────────────────────

Actions:
• Type scenario number to view/run
• Type scenario path (e.g., 'success/simple_get') to run
• Type 'new:<name>' to create new scenario
```

### 입력 방법

1. **번호로 선택**: `5` 입력 → `success/simple_get` 실행
2. **경로로 선택**: `success/simple_get` 입력 → 해당 시나리오 실행
3. **새 시나리오**: `new:test_scenario` 입력 → 시나리오 생성

## 테스트 방법

```bash
# 1. 시뮬레이터 실행
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator
python3 main.py

# 2. 프로젝트 선택 (Press P)
# 3. "example" 프로젝트 선택 (입력: 1 또는 example)
# 4. 시나리오 화면으로 이동 (Press S)
# 5. 트리 구조 확인
# 6. 번호로 시나리오 선택 (예: 5)
```

## 특징

✅ **폴더 구조 반영**: 실제 파일 시스템 구조 그대로 표시
✅ **계층적 표시**: 폴더와 파일을 트리 형태로 시각화
✅ **번호 매핑**: 각 시나리오에 번호 부여, 빠른 선택 가능
✅ **경로 지원**: 전체 경로로도 시나리오 선택 가능
✅ **빈 폴더 표시**: 빈 폴더도 구조에 표시

## 호환성

- 기존 flat 구조 프로젝트: 정상 동작 (모든 파일이 루트에 표시)
- 새로운 폴더 구조: 트리 형태로 표시
- 하위 폴더 무제한 지원

## 자동 생성 스크립트 연동

`scripts/scenario/generate_scenario.py`로 생성된 시나리오들이 폴더 구조로 정리되어 있으면, 자동으로 트리 형태로 표시됩니다.

예:
```
projects/workercontroller/scenario/
├── success/
│   ├── checkinout_success.json
│   ├── getworker_success.json
│   └── ...
├── failure/
│   ├── checkinout_failure_1.json
│   ├── checkinout_failure_2.json
│   └── ...
├── integration/
│   ├── crud_integration.json
│   └── full_integration.json
└── load_test/
    ├── checkinout_load_test.json
    └── stress_test.json
```

모두 트리 구조로 깔끔하게 표시됩니다! 🌳
