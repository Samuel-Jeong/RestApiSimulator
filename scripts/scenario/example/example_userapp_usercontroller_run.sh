#! /bin/bash

# =============================================================================
# 경로 설정 (필요 시 수정)
# =============================================================================

# 자동 경로 탐지 (기본값)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# 수동 경로 설정 (필요 시 아래 주석 해제 후 수정)
# PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/MINE/restapisimulator"
# VENV_PATH="$PROJECT_ROOT/venv"
# SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# 경로 설정 (자동/수동)
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/venv}"
SCENARIO_GENERATOR_DIR="${SCENARIO_GENERATOR_DIR:-$PROJECT_ROOT/scripts/scenario}"

# =============================================================================
# 가상 환경 활성화
# =============================================================================

if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ 가상 환경 활성화: $VENV_PATH"
else
    echo "❌ 가상 환경을 찾을 수 없습니다: $VENV_PATH"
    exit 1
fi

# =============================================================================
# 시나리오 생성기 실행
# =============================================================================

cd "$SCENARIO_GENERATOR_DIR" || exit 1

python3 generate_scenario.py \
/Volumes/WORK/GIT_PROJECTS/MINE/example/user-app/src/main/java/com/example/controller/UserController.java \
--output /Volumes/WORK/GIT_PROJECTS/MINE/restapisimulator/projects/example \
--environment development \
--context-path /api/v1/user \
--auth-bearer-token "{{USER_CERT_TOKEN}}" \
--auth-mode exclude \
--auth-annotations NoAuth \
--continue-on-error \
--format yaml