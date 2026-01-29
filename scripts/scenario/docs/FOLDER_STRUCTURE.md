# 시나리오 폴더 구조 자동 생성

## 변경 사항

시나리오 자동 생성 스크립트가 이제 **폴더별로 정리된 구조**로 파일을 생성합니다.

### Before (기존)
```
projects/user/scenario/
├── getallusers_success.json
├── getuserbyid_success.json
├── createuser_success.json
├── createuser_failure_1.json
├── createuser_failure_2.json
├── user_integration.json
├── getallusers_load_test.json
└── user_stress_test.json
```
❌ 모든 파일이 한 폴더에 섞여 있어 관리가 어려움

### After (개선)
```
projects/user/scenario/
├── success/                    # 정상 시나리오
│   ├── getallusers_success.json
│   ├── getuserbyid_success.json
│   └── createuser_success.json
├── failure/                    # 실패 시나리오
│   ├── createuser_failure_1.json
│   └── createuser_failure_2.json
├── integration/                # 통합 테스트
│   └── user_full_integration.json
└── load_test/                  # 성능/부하 테스트
    ├── getallusers_load_test.json
    └── user_stress_test.json
```
✅ 목적별로 폴더 분리, 관리 용이

## 코드 변경

### 1. `ScenarioGenerator.generate()` 메서드

```python
def generate(self):
    """시나리오 파일 생성"""
    # 폴더 구조 생성
    success_dir = os.path.join(scenario_dir, 'success')
    failure_dir = os.path.join(scenario_dir, 'failure')
    integration_dir = os.path.join(scenario_dir, 'integration')
    load_test_dir = os.path.join(scenario_dir, 'load_test')
    
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(failure_dir, exist_ok=True)
    os.makedirs(integration_dir, exist_ok=True)
    os.makedirs(load_test_dir, exist_ok=True)
    
    # 각 폴더에 해당하는 시나리오 저장
    self._generate_success_failure_scenarios(success_dir, failure_dir)
    self._generate_integration_scenario(integration_dir)
    self._generate_load_test_scenarios(load_test_dir)
```

### 2. `_generate_success_failure_scenarios()` 메서드

```python
def _generate_success_failure_scenarios(self, success_dir: str, failure_dir: str):
    """각 API별 정상/실패 시나리오 생성"""
    for endpoint in self.parser.endpoints:
        # 정상 시나리오 → success/ 폴더
        success_scenario = self._create_success_scenario(endpoint)
        self._write_json(os.path.join(success_dir, filename), success_scenario)
        
        # 실패 시나리오 → failure/ 폴더
        failure_scenarios = self._create_failure_scenarios(endpoint)
        for failure_scenario in failure_scenarios:
            self._write_json(os.path.join(failure_dir, filename), failure_scenario)
```

### 3. `_write_json()` 메서드 개선

```python
def _write_json(self, filepath: str, data: Dict[str, Any]):
    """JSON 파일 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 폴더명 포함해서 표시
    path_obj = Path(filepath)
    folder_name = path_obj.parent.name
    if folder_name != 'scenario':
        print(f"  ✓ {folder_name}/{path_obj.name}")
    else:
        print(f"  ✓ {path_obj.name}")
```

## 실행 결과

### 콘솔 출력
```bash
$ python3 scripts/scenario/generate_scenario.py WorkerController.java

🚀 시나리오 자동 생성 시작
📂 입력: WorkerController.java
📂 출력: projects/wpm
📊 발견된 엔드포인트: 4개

📁 생성 위치: projects/wpm/workercontroller/scenario/
   ├── success/
   ├── failure/
   ├── integration/
   └── load_test/

1️⃣  정상/실패 시나리오 생성 중...
  ✓ success/getworkercommutetoday_success.json
  ✓ failure/getworkercommutetoday_failure_1.json
  ✓ success/checkinout_success.json
  ✓ failure/checkinout_failure_1.json
  ✓ failure/checkinout_failure_2.json
  ...

2️⃣  통합 테스트 시나리오 생성 중...
  ✓ integration/workercontroller_full_integration.json

3️⃣  성능/부하 테스트 시나리오 생성 중...
  ✓ load_test/getworkercommutetoday_load_test.json
  ✓ load_test/workercontroller_stress_test.json

✅ 시나리오 파일 생성 완료!
📊 총 14개 파일 생성

🎉 모든 시나리오 생성 완료!
```

### 생성된 폴더 구조
```
projects/wpm/workercontroller/
└── scenario/
    ├── success/
    │   ├── getworkercommutetoday_success.json
    │   ├── getworkercommutehistorylist_success.json
    │   ├── checkinout_success.json
    │   └── updateworkerhistorymemo_success.json
    ├── failure/
    │   ├── getworkercommutetoday_failure_1.json
    │   ├── getworkercommutehistorylist_failure_1.json
    │   ├── checkinout_failure_1.json
    │   ├── checkinout_failure_2.json
    │   ├── updateworkerhistorymemo_failure_1.json
    │   └── updateworkerhistorymemo_failure_2.json
    ├── integration/
    │   └── workercontroller_full_integration.json
    └── load_test/
        ├── getworkercommutetoday_load_test.json
        ├── getworkercommutehistorylist_load_test.json
        └── workercontroller_stress_test.json
```

## 시뮬레이터 연동

생성된 폴더 구조는 시뮬레이터에서 **트리 형태**로 표시됩니다:

```
╔═ SCENARIOS - wpm/workercontroller ═══════════╗

Available Scenarios:

├── 📁 failure/
│   ├── [ 1] 📄 checkinout_failure_1
│   ├── [ 2] 📄 checkinout_failure_2
│   ├── [ 3] 📄 getworkercommutehistorylist_failure_1
│   ├── [ 4] 📄 getworkercommutetoday_failure_1
│   ├── [ 5] 📄 updateworkerhistorymemo_failure_1
│   └── [ 6] 📄 updateworkerhistorymemo_failure_2
├── 📁 integration/
│   └── [ 7] 📄 workercontroller_full_integration
├── 📁 load_test/
│   ├── [ 8] 📄 getworkercommutehistorylist_load_test
│   ├── [ 9] 📄 getworkercommutetoday_load_test
│   └── [10] 📄 workercontroller_stress_test
└── 📁 success/
    ├── [11] 📄 checkinout_success
    ├── [12] 📄 getworkercommutehistorylist_success
    ├── [13] 📄 getworkercommutetoday_success
    └── [14] 📄 updateworkerhistorymemo_success

────────────────────────────────────────────────

Scenarios: 14 files | Project: wpm/workercontroller
```

## 장점

✅ **체계적 관리**: 시나리오 목적별로 폴더 분리  
✅ **빠른 탐색**: 원하는 시나리오를 쉽게 찾을 수 있음  
✅ **시각적 구조**: 폴더 트리로 한눈에 파악  
✅ **확장성**: 새로운 시나리오 타입 추가 용이  
✅ **유지보수**: 파일 관리가 훨씬 수월  

## 사용 예시

```bash
# 1. 컨트롤러에서 시나리오 생성
python3 scripts/scenario/generate_scenario.py \
  /path/to/WorkerController.java \
  --output projects/wpm

# 2. 시뮬레이터 실행
python3 main.py

# 3. 프로젝트 선택: wpm/workercontroller
# 4. 시나리오 화면에서 폴더별로 정리된 트리 확인
# 5. 번호로 시나리오 선택 (예: 11 입력 → success/checkinout_success)
```

## 폴더 구조 설명

| 폴더 | 설명 | 파일 형식 |
|------|------|----------|
| `success/` | 정상 동작 테스트 | `*_success.json` |
| `failure/` | 실패 케이스 테스트 | `*_failure_*.json` |
| `integration/` | API 통합 테스트 | `*_integration.json` |
| `load_test/` | 성능/부하 테스트 | `*_load_test.json`, `*_stress_test.json` |

## 호환성

- ✅ 기존에 생성된 flat 구조 프로젝트도 정상 작동
- ✅ 새로 생성되는 모든 프로젝트는 폴더 구조로 자동 생성
- ✅ 시뮬레이터가 두 구조를 모두 지원

## 마이그레이션

기존 flat 구조를 폴더 구조로 변경하려면:

```bash
cd projects/yourproject/scenario

# 폴더 생성
mkdir -p success failure integration load_test

# 파일 이동
mv *_success.json success/
mv *_failure_*.json failure/
mv *_integration.json integration/
mv *_load_test.json *_stress_test.json load_test/
```

시뮬레이터를 재시작하면 자동으로 트리 구조로 표시됩니다! 🌳
