# 시나리오 스크립트 경로 설정 빠른 가이드

## 🚀 빠른 시작

대부분의 경우 **아무 설정 없이 바로 사용 가능**합니다:

```bash
# 그냥 실행하면 됩니다
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

---

## 📂 경로 설정이 필요한 경우

다음과 같은 경우에만 경로를 설정하면 됩니다:

1. ❌ "가상 환경을 찾을 수 없습니다" 에러
2. ❌ "시나리오 생성기를 찾을 수 없습니다" 에러
3. 🔧 표준 구조가 아닌 프로젝트
4. 🔗 심볼릭 링크 사용

---

## 방법 1: 스크립트 직접 수정 (가장 간단)

스크립트 파일을 열고 주석 해제 후 경로 수정:

```bash
# 스크립트 편집
nano scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

다음 부분 수정:
```bash
# 수동 경로 설정 (필요 시 아래 주석 해제 후 수정)
PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
VENV_PATH="$PROJECT_ROOT/venv"
SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"
```

주석(`#`)을 제거하고 경로를 수정하면 됩니다.

---

## 방법 2: 환경 변수 사용

터미널에서 환경 변수를 설정하고 스크립트 실행:

```bash
# 경로 설정
export PROJECT_ROOT="/your/custom/path"
export VENV_PATH="/your/custom/venv"

# 스크립트 실행
bash scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```

**영구 설정** (모든 터미널에서 사용):
```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
echo 'export PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"' >> ~/.zshrc
source ~/.zshrc
```

---

## 방법 3: 설정 파일 사용 (여러 프로젝트 관리 시 권장)

```bash
# 1. 설정 파일 생성
cp scripts/scenario/config_example.sh scripts/scenario/config.sh

# 2. 설정 파일 수정
nano scripts/scenario/config.sh

# 3. 설정 파일 사용
bash scripts/scenario/run_with_config.sh \
  /path/to/Controller.java \
  --output /path/to/output
```

---

## 🔍 경로 확인 방법

스크립트를 실행하면 사용 중인 경로가 출력됩니다:

```
✅ 가상 환경 활성화: /Volumes/WORK/.../venv
📂 프로젝트 루트: /Volumes/WORK/.../restapisimulator
⚙️  생성기 경로: /Volumes/WORK/.../scripts/scenario
```

---

## ⚙️ 새 스크립트 만들기

템플릿을 복사하여 사용하세요:

```bash
# 1. 템플릿 복사
cp scripts/scenario/template_run.sh scripts/scenario/my_project_run.sh

# 2. 스크립트 수정
nano scripts/scenario/my_project_run.sh
# - 컨트롤러 경로 수정
# - 출력 경로 수정
# - 인증 설정 수정

# 3. 실행
bash scripts/scenario/my_project_run.sh
```

---

## 📖 더 자세한 내용

전체 가이드는 [PATH_CONFIGURATION_GUIDE.md](./PATH_CONFIGURATION_GUIDE.md)를 참고하세요.

---

## 💡 자주 묻는 질문

### Q: 가상 환경이 다른 위치에 있습니다

```bash
# 스크립트에서 VENV_PATH 수정
VENV_PATH="/Users/myuser/.virtualenvs/restapisimulator"
```

### Q: 여러 컴퓨터에서 사용해야 합니다

설정 파일을 사용하고 .gitignore에 추가:
```bash
cp config_example.sh config.sh
echo "config.sh" >> .gitignore
```

### Q: 에러 메시지 없이 작동하지 않습니다

디버그 모드로 실행:
```bash
bash -x scripts/scenario/wpm/wpm_workerapp_workercontroller_run.sh
```
