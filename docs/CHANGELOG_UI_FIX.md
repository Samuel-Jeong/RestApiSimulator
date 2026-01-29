# UI 파일 확장자 하드코딩 수정

## 🐛 문제

UI (`app/ui/app.py`)에서 시나리오 파일 확장자를 `.json`으로 하드코딩하여 YAML 파일을 인식하지 못했습니다.

### 문제가 발생한 위치

1. **새 시나리오 생성** (722번 줄)
   - 항상 `.json` 파일로 생성
   
2. **시나리오 상세보기** (1393번 줄)
   - `.json` 파일만 찾음

## ✅ 해결

### 1. 동적 파일 찾기 구현

**이전:**
```python
scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.json"
```

**수정 후:**
```python
# Find scenario file (try yaml, yml, json)
base_path = Path("projects") / self.current_project / "scenario"
scenario_path = None
for ext in ['.yaml', '.yml', '.json']:
    candidate = base_path / f"{scenario_name}{ext}"
    if candidate.exists():
        scenario_path = candidate
        break
```

### 2. 확장자별 파싱

**수정 후:**
```python
# Load based on extension
if scenario_path.suffix in ['.yaml', '.yml']:
    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenario_data = yaml.safe_load(f)
else:
    with open(scenario_path, 'r') as f:
        scenario_data = json.load(f)
```

### 3. 새 시나리오는 YAML 형식으로 생성

**이전:**
```python
scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.json"
# ...
import json
with open(scenario_path, 'w') as f:
    json.dump(basic_scenario, f, indent=2)
```

**수정 후:**
```python
scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.yaml"
# ...
with open(scenario_path, 'w', encoding='utf-8') as f:
    yaml.dump(basic_scenario, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

### 4. Import 정리

**추가:**
```python
import json
import yaml
```

**제거:** 불필요한 로컬 import 제거
- `import json` (4곳)
- `import json as json_lib` (2곳)

## 🎯 결과

### 이제 가능한 것들

✅ YAML 시나리오 파일 인식
✅ JSON 시나리오 파일 인식 (기존 호환)
✅ 동일 이름의 시나리오가 다른 확장자로 있을 경우 우선순위: `.yaml` > `.yml` > `.json`
✅ UI에서 새 시나리오 생성 시 YAML 형식으로 생성
✅ 시나리오 상세보기에서 확장자 자동 감지

### 우선순위

시나리오 파일을 찾을 때 다음 순서로 검색:
1. `.yaml`
2. `.yml`
3. `.json`

## 📝 테스트

```bash
# 1. YAML 시나리오 생성 확인
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator
ls -la projects/wpm/workercontroller/scenario/integration/*.yaml

# 2. 시뮬레이터 실행
python3 main.py

# 3. UI에서 확인
# - Projects → wpm/workercontroller 선택
# - Scenarios → integration/workercontroller_full_integration 선택
# - YAML 파일이 정상적으로 로드되는지 확인
```

## 🔗 관련 변경사항

- `app/core/project_manager.py` - 이미 YAML 지원 완료
- `scripts/scenario/generate_scenario.py` - YAML 형식 생성 지원 완료
- `app/ui/app.py` - **이번 수정으로 완료** ✅

## ⚠️ 주의사항

- 기존 JSON 시나리오는 그대로 작동합니다
- 새로 생성되는 시나리오는 YAML 형식입니다
- 동일 이름으로 JSON과 YAML이 모두 있으면 YAML이 우선됩니다
