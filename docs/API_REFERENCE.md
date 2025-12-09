# API Reference

## Core Modules

### ProjectManager

프로젝트 관리 클래스

```python
from app.core.project_manager import ProjectManager

pm = ProjectManager(projects_root="projects")

# 프로젝트 목록
projects = pm.list_projects()

# 프로젝트 생성
pm.create_project("my_project")

# 호스트 설정 로드
hosts = pm.load_hosts_config("my_project")

# 시나리오 목록
scenarios = pm.list_scenarios("my_project")

# 시나리오 로드
scenario = pm.load_scenario("my_project", "test_scenario")
```

### ScenarioEngine

시나리오 실행 엔진

```python
from app.core.scenario_engine import ScenarioEngine
from app.models.config import HostConfig

host_config = HostConfig(
    base_url="https://api.example.com",
    timeout=30,
    headers={"Content-Type": "application/json"}
)

engine = ScenarioEngine(host_config)

# 시나리오 실행
result = await engine.execute_scenario(scenario, progress_callback)
```

### LoadTestEngine

부하 테스트 엔진

```python
from app.core.load_test_engine import LoadTestEngine
from app.models.scenario import LoadTestConfig

config = LoadTestConfig(
    duration_seconds=60,
    target_tps=100,
    ramp_up_seconds=10,
    max_concurrent=50,
    distribution="linear"
)

engine = LoadTestEngine(host_config)

# 부하 테스트 실행
result = await engine.execute_load_test(scenario, config, progress_callback)
```

### ReportGenerator

리포트 생성기

```python
from app.core.report_generator import ReportGenerator
from pathlib import Path

# 시나리오 리포트 저장
report_path = ReportGenerator.save_scenario_report(
    result, 
    Path("projects/my_project/result"),
    "my_project"
)

# 부하 테스트 리포트 저장
report_path = ReportGenerator.save_load_test_report(
    result,
    Path("projects/my_project/result"),
    "my_project"
)

# 리포트 로드
report = ReportGenerator.load_report(report_path)

# 요약 텍스트 생성
summary = ReportGenerator.generate_summary_text(report)
```

### UMLGenerator

UML 다이어그램 생성기

```python
from app.core.uml_generator import UMLGenerator

# 시퀀스 다이어그램 생성
sequence_diagram = UMLGenerator.generate_sequence_diagram(scenario)

# 플로우차트 생성
flowchart = UMLGenerator.generate_flowchart(scenario)

# 텍스트 다이어그램 생성
text_diagram = UMLGenerator.generate_text_diagram(scenario)

# 다이어그램 저장
UMLGenerator.save_diagram(sequence_diagram, "output.puml")
```

## Data Models

### Scenario

```python
from app.models.scenario import Scenario, ScenarioStep, Assertion, HttpMethod

scenario = Scenario(
    name="Test Scenario",
    description="Example scenario",
    host="default",
    variables={"user": "test"},
    steps=[
        ScenarioStep(
            name="Create User",
            method=HttpMethod.POST,
            path="/users",
            body={"name": "{{user}}"},
            assertions=[
                Assertion(
                    field="status",
                    operator="eq",
                    value=201
                )
            ],
            extract={"user_id": "body.id"}
        )
    ]
)
```

### HostConfig

```python
from app.models.config import HostConfig

config = HostConfig(
    base_url="https://api.example.com",
    timeout=30,
    headers={"Content-Type": "application/json"},
    verify_ssl=True,
    auth={"type": "bearer", "token": "xxx"}
)
```

### LoadTestConfig

```python
from app.models.scenario import LoadTestConfig

config = LoadTestConfig(
    duration_seconds=60,
    target_tps=100,
    ramp_up_seconds=10,
    max_concurrent=50,
    distribution="linear"
)
```

## Utilities

### ProcessLock

중복 실행 방지

```python
from app.utils.lock import ProcessLock

with ProcessLock():
    # 애플리케이션 로직
    pass
```

### AssertionEngine

응답 검증 엔진

```python
from app.core.assertion_engine import AssertionEngine

# 단일 assertion 검증
passed, message = AssertionEngine.validate_assertion(
    assertion, 
    status_code, 
    response_body
)

# 모든 assertion 검증
passed_count, failed_count, details = AssertionEngine.validate_all(
    assertions,
    status_code,
    response_body
)
```

## CLI Usage

```bash
# 직접 실행
python main.py

# 모듈로 실행
python -m app.ui.app

# 설치 후 실행
pip install -e .
rest-api-sim
```

## Environment Variables

```bash
# 프로젝트 루트 디렉토리
export REST_API_SIM_PROJECTS_ROOT=/path/to/projects

# 로그 레벨
export REST_API_SIM_LOG_LEVEL=DEBUG
```

## Examples

### 예제 1: 간단한 시나리오 실행

```python
import asyncio
from app.core.project_manager import ProjectManager
from app.core.scenario_engine import ScenarioEngine

async def main():
    pm = ProjectManager()
    
    # 시나리오 로드
    scenario = pm.load_scenario("example", "simple_get")
    
    # 호스트 설정 로드
    hosts = pm.load_hosts_config("example")
    
    # 엔진 생성 및 실행
    engine = ScenarioEngine(hosts["default"])
    result = await engine.execute_scenario(scenario)
    
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Success: {result.successful_requests}/{result.total_requests}")

asyncio.run(main())
```

### 예제 2: 부하 테스트 실행

```python
import asyncio
from app.core.project_manager import ProjectManager
from app.core.load_test_engine import LoadTestEngine
from app.models.scenario import LoadTestConfig

async def main():
    pm = ProjectManager()
    
    # 설정
    scenario = pm.load_scenario("example", "load_test_scenario")
    hosts = pm.load_hosts_config("example")
    
    config = LoadTestConfig(
        duration_seconds=30,
        target_tps=50,
        ramp_up_seconds=5,
        max_concurrent=25,
        distribution="linear"
    )
    
    # 실행
    engine = LoadTestEngine(hosts["default"])
    result = await engine.execute_load_test(scenario, config)
    
    print(f"Target TPS: {result.target_tps}")
    print(f"Actual TPS: {result.actual_avg_tps:.2f}")
    print(f"Success Rate: {result.success_rate:.1f}%")

asyncio.run(main())
```

### 예제 3: UML 생성

```python
from app.core.project_manager import ProjectManager
from app.core.uml_generator import UMLGenerator

pm = ProjectManager()
scenario = pm.load_scenario("example", "user_crud")

# 시퀀스 다이어그램
diagram = UMLGenerator.generate_sequence_diagram(scenario)
UMLGenerator.save_diagram(diagram, "user_crud_sequence.puml")

# 텍스트 다이어그램
text = UMLGenerator.generate_text_diagram(scenario)
print(text)
```

## Configuration Files

### hosts.json Schema

```json
{
  "<host_name>": {
    "base_url": "string (required)",
    "timeout": "integer (default: 30)",
    "headers": "object (default: {})",
    "verify_ssl": "boolean (default: true)",
    "auth": "object (optional)"
  }
}
```

### Scenario Schema

```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "host": "string (optional, default: 'default')",
  "tags": "array of strings (optional)",
  "variables": "object (optional)",
  "steps": [
    {
      "name": "string (required)",
      "method": "GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS",
      "path": "string (required)",
      "headers": "object (optional)",
      "query_params": "object (optional)",
      "body": "any (optional)",
      "timeout": "integer (optional)",
      "delay_before": "float (default: 0)",
      "delay_after": "float (default: 0)",
      "assertions": "array (optional)",
      "extract": "object (optional)",
      "skip_on_failure": "boolean (default: false)",
      "retry": "integer (default: 0)"
    }
  ]
}
```

## Error Handling

모든 엔진과 매니저는 적절한 예외를 발생시킵니다:

- `ValueError`: 잘못된 입력값
- `FileNotFoundError`: 파일을 찾을 수 없음
- `TimeoutError`: 요청 타임아웃
- `RuntimeError`: 실행 중 오류

예외 처리 예제:

```python
try:
    result = await engine.execute_scenario(scenario)
except TimeoutError as e:
    print(f"Timeout: {e}")
except RuntimeError as e:
    print(f"Error: {e}")
```

