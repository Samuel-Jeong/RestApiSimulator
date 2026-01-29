# 가상환경 사용 가이드

## ⚠️ 중요: PyYAML 의존성

시나리오 생성 스크립트는 PyYAML 라이브러리를 사용합니다.
이 라이브러리는 프로젝트의 가상환경에 설치되어 있습니다.

## 해결 방법

### 방법 1: 자동 스크립트 실행 (권장)

제공된 `.sh` 스크립트는 자동으로 가상환경을 활성화합니다:

```bash
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/scripts/scenario
./wpm_workercontroller_run.sh
```

### 방법 2: 수동으로 가상환경 활성화

```bash
# 1. 프로젝트 루트로 이동
cd /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 스크립트 실행
cd scripts/scenario
python3 generate_scenario.py [옵션들...]
```

### 방법 3: 시스템 전역에 PyYAML 설치

```bash
# Homebrew Python 사용 시
pip3 install --user pyyaml

# 또는 (권장하지 않음)
pip3 install --break-system-packages pyyaml
```

## 에러 메시지

만약 다음과 같은 에러가 발생한다면:

```
ModuleNotFoundError: No module named 'yaml'
```

**해결책:**
- 위의 방법 1 또는 방법 2를 사용하세요
- 스크립트 파일이 자동으로 가상환경을 활성화하도록 수정되었습니다

## 스크립트 템플릿

새로운 스크립트를 작성할 때는 다음 템플릿을 사용하세요:

```bash
#!/bin/bash

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Your commands here
python3 generate_scenario.py [your options]
```

## 확인 방법

PyYAML이 올바르게 설치되었는지 확인:

```bash
# 가상환경 활성화 후
python3 -c "import yaml; print('PyYAML installed successfully')"
```

성공 시 출력:
```
PyYAML installed successfully
```
