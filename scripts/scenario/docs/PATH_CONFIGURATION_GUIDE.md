# 경로 설정 가이드

시나리오 생성 스크립트의 경로를 설정하는 다양한 방법을 설명합니다.

## 개요

시나리오 생성 스크립트는 다음 세 가지 경로를 필요로 합니다:
1. **프로젝트 루트**: restapisimulator 프로젝트의 루트 디렉토리
2. **가상 환경**: Python 가상 환경 경로
3. **시나리오 생성기**: generate_scenario.py가 있는 디렉토리

---

## 방법 1: 자동 경로 탐지 (기본값)

### 설명
스크립트가 자동으로 상대 경로를 계산하여 경로를 찾습니다.

### 장점
- 설정 불필요
- 프로젝트 구조가 표준인 경우 바로 작동
- 이식성 좋음

### 단점
- 프로젝트 구조가 다르면 작동하지 않을 수 있음
- 심볼릭 링크 사용 시 문제 발생 가능

### 사용 방법

스크립트에 이미 적용되어 있습니다:

```bash
#!/bin/bash

# 자동 경로 탐지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

VENV_PATH="$PROJECT_ROOT/venv"
SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 가상 환경 활성화
source "$VENV_PATH/bin/activate"

# 시나리오 생성기 실행
cd "$SCENARIO_GENERATOR_DIR"
python3 generate_scenario.py ...
```

---

## 방법 2: 절대 경로 직접 지정

### 설명
스크립트 상단에 절대 경로를 직접 지정합니다.

### 장점
- 명확하고 확실함
- 구조가 복잡해도 작동
- 디버깅 쉬움

### 단점
- 하드코딩됨
- 컴퓨터마다 다른 경로 사용 시 수정 필요

### 사용 방법

스크립트를 다음과 같이 수정:

```bash
#!/bin/bash

# 방법 1: 절대 경로 직접 지정
PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
VENV_PATH="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/venv"
SCENARIO_GENERATOR_DIR="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/scripts/scenario"

# 방법 2: 기본 경로 + 상대 경로
BASE_PATH="/Volumes/WORK/GIT_PROJECTS/TELCOWARE"
PROJECT_ROOT="$BASE_PATH/restapisimulator"
VENV_PATH="$PROJECT_ROOT/venv"
SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 가상 환경 활성화
source "$VENV_PATH/bin/activate"

# 시나리오 생성기 실행
cd "$SCENARIO_GENERATOR_DIR"
python3 generate_scenario.py ...
```

---

## 방법 3: 환경 변수 사용 (권장)

### 설명
환경 변수로 경로를 설정하고 스크립트에서 사용합니다.

### 장점
- 유연함
- 여러 환경에서 사용 가능
- 중앙 집중식 관리

### 단점
- 환경 변수 설정 필요
- 초기 설정이 필요

### 사용 방법

#### 3-1. 셸 환경 변수 설정

**방법 A: 임시 설정 (현재 터미널에만)**
```bash
export PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
export VENV_PATH="$PROJECT_ROOT/venv"
export SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 스크립트 실행
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

**방법 B: 영구 설정 (모든 터미널)**
```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
echo 'export PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"' >> ~/.zshrc
echo 'export VENV_PATH="$PROJECT_ROOT/venv"' >> ~/.zshrc
echo 'export SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"' >> ~/.zshrc

# 적용
source ~/.zshrc
```

#### 3-2. 스크립트에서 환경 변수 사용

스크립트는 이미 환경 변수를 지원합니다:

```bash
#!/bin/bash

# 자동 경로 탐지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT_AUTO="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# 환경 변수 우선, 없으면 자동 탐지 사용
PROJECT_ROOT="${PROJECT_ROOT:-$PROJECT_ROOT_AUTO}"
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/venv}"
SCENARIO_GENERATOR_DIR="${SCENARIO_GENERATOR_DIR:-$PROJECT_ROOT/scripts/scenario}"
```

---

## 방법 4: 설정 파일 사용 (권장)

### 설명
별도의 설정 파일에 모든 경로를 정의하고 스크립트에서 로드합니다.

### 장점
- 중앙 집중식 관리
- 여러 스크립트에서 공유
- Git에서 제외 가능 (.gitignore)

### 단점
- 설정 파일 관리 필요

### 사용 방법

#### 4-1. 설정 파일 생성

```bash
# 예제 파일 복사
cp scripts/scenario/config_example.sh scripts/scenario/config.sh

# 설정 파일 수정
nano scripts/scenario/config.sh
```

**config.sh:**
```bash
#!/bin/bash

# 프로젝트 루트 경로
export PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"

# 가상 환경 경로
export VENV_PATH="$PROJECT_ROOT/venv"

# 시나리오 생성기 경로
export SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# Java 소스 코드 루트
export JAVA_SRC_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE"

# 출력 경로
export SCENARIO_OUTPUT_ROOT="$PROJECT_ROOT/projects"

# 기본 설정
export DEFAULT_ENVIRONMENT="development"
export DEFAULT_CONTEXT_PATH="/api/v1"
export DEFAULT_FORMAT="yaml"
```

#### 4-2. .gitignore에 추가

```bash
# .gitignore에 추가
echo "scripts/scenario/config.sh" >> .gitignore
```

#### 4-3. 설정 파일을 사용하는 스크립트

**방법 A: 스크립트에서 직접 로드**
```bash
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 설정 파일 로드
if [ -f "$SCRIPT_DIR/../../config.sh" ]; then
    source "$SCRIPT_DIR/../../config.sh"
else
    echo "⚠️  설정 파일이 없습니다. 기본값 사용"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    VENV_PATH="$PROJECT_ROOT/venv"
    SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"
fi

# 스크립트 실행...
```

**방법 B: 설정 파일 전용 실행 스크립트 사용**
```bash
# 설정 파일 사용
bash scripts/scenario/run_with_config.sh \
  /path/to/Controller.java \
  --output $SCENARIO_OUTPUT_ROOT/project_name
```

---

## 방법 5: 하이브리드 (자동 + 수동)

### 설명
기본적으로 자동 탐지를 사용하되, 필요 시 수동 경로를 우선 적용합니다.

### 장점
- 유연성과 편의성 모두 제공
- 대부분의 경우 자동으로 작동
- 필요 시 수동 조정 가능

### 사용 방법

현재 모든 스크립트에 이미 적용되어 있습니다:

```bash
#!/bin/bash

# 자동 경로 탐지 (기본값)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# 수동 경로 설정 (필요 시 아래 주석 해제 후 수정)
# PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
# VENV_PATH="$PROJECT_ROOT/venv"
# SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 최종 경로 설정 (우선순위: 환경변수 > 직접지정 > 자동탐지)
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/venv}"
SCENARIO_GENERATOR_DIR="${SCENARIO_GENERATOR_DIR:-$PROJECT_ROOT/scripts/scenario}"
```

---

## 실제 사용 예제

### 예제 1: 기본 사용 (자동 경로)

```bash
# 그냥 실행
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

### 예제 2: 환경 변수로 경로 지정

```bash
# 환경 변수 설정
export PROJECT_ROOT="/custom/path/to/restapisimulator"
export VENV_PATH="/custom/venv/path"

# 스크립트 실행
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

### 예제 3: 스크립트 직접 수정

```bash
# 스크립트 편집
nano scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh

# 주석 해제 후 수정:
# PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
# VENV_PATH="/Users/myuser/.virtualenvs/restapisimulator"
# SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 저장 후 실행
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

### 예제 4: 설정 파일 사용

```bash
# 설정 파일 생성
cp scripts/scenario/config_example.sh scripts/scenario/config.sh
nano scripts/scenario/config.sh

# 설정 파일 사용하여 실행
bash scripts/scenario/run_with_config.sh \
  $WPM_CONTROLLER_PATH/WorkerController.java \
  --output $SCENARIO_OUTPUT_ROOT/wpm
```

---

## 문제 해결

### Q1: "가상 환경을 찾을 수 없습니다" 에러

**원인:**
- 가상 환경이 설치되지 않았거나
- 경로가 잘못됨

**해결:**
```bash
# 가상 환경 생성
python3 -m venv /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/venv

# 또는 스크립트에서 경로 수정
nano scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
# VENV_PATH를 올바른 경로로 수정
```

### Q2: "시나리오 생성기를 찾을 수 없습니다" 에러

**원인:**
- generate_scenario.py가 없거나
- 경로가 잘못됨

**해결:**
```bash
# 생성기 확인
ls scripts/scenario/generate_scenario.py

# 스크립트에서 경로 확인 및 수정
nano scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

### Q3: 심볼릭 링크 사용 시 경로 오류

**원인:**
- 상대 경로 계산이 심볼릭 링크를 제대로 따라가지 못함

**해결:**
```bash
# 절대 경로 사용
PROJECT_ROOT="/absolute/path/to/restapisimulator"
VENV_PATH="/absolute/path/to/venv"
SCENARIO_GENERATOR_DIR="/absolute/path/to/scripts/scenario"
```

### Q4: 여러 프로젝트에서 동일한 스크립트 사용

**원인:**
- 각 프로젝트마다 다른 경로 필요

**해결:**
```bash
# 방법 1: 설정 파일 사용
cp config_example.sh config_project1.sh
cp config_example.sh config_project2.sh

# 프로젝트별 설정 파일 수정
CONFIG_FILE=config_project1.sh bash run_with_config.sh ...
CONFIG_FILE=config_project2.sh bash run_with_config.sh ...

# 방법 2: 환경 변수로 분리
alias wpm_project="PROJECT_ROOT=/path/to/wpm bash ..."
alias capshome_project="PROJECT_ROOT=/path/to/capshome bash ..."
```

---

## 권장 사항

### 개발 환경

1. **로컬 개발**: 자동 경로 탐지 (기본값)
2. **팀 개발**: 설정 파일 사용 + .gitignore
3. **CI/CD**: 환경 변수 사용

### 프로젝트별

1. **단일 프로젝트**: 자동 경로 탐지
2. **여러 프로젝트**: 설정 파일 사용
3. **복잡한 구조**: 절대 경로 직접 지정

---

## 참고 자료

- [template_run.sh](./template_run.sh) - 스크립트 템플릿
- [config_example.sh](./config_example.sh) - 설정 파일 예제
- [run_with_config.sh](./run_with_config.sh) - 설정 파일 사용 스크립트
- [USAGE.md](./USAGE.md) - 전체 사용법
