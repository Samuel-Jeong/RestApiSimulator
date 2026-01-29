#!/bin/bash

# Include 모드 예제
# 특정 어노테이션(@UserCert)이 있는 메서드만 인증이 필요한 경우

# =============================================================================
# 경로 설정 (필요 시 수정)
# =============================================================================

# 자동 경로 탐지 (기본값)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 수동 경로 설정 (필요 시 아래 주석 해제 후 수정)
# PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
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

cd "$SCENARIO_GENERATOR_DIR" || exit 1

echo "================================"
echo "Include 모드 시나리오 생성"
echo "================================"
echo "- 어노테이션이 있는 메서드만 인증 필요"
echo "- @UserCert → 인증 헤더 추가"
echo "- 어노테이션 없음 → 인증 헤더 제외"
echo ""

# Run the scenario generator
python3 generate_scenario.py \
/Volumes/WORK/GIT_PROJECTS/TELCOWARE/sks-wpm-container-apps/app-mod/worker-app/src/main/java/com/sks/wpm/controller/WorkerManagerController.java \
--output /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/projects/wpm \
--environment development \
--context-path /api/v1 \
--header "X-Header-Extra-Info:{{USER_CERT_TOKEN}}" \
--auth-annotations UserCert:wpm-get-user-info.json \
--auth-mode include \
--continue-on-error \
--format yaml

echo ""
echo "✅ Include 모드 시나리오 생성 완료!"
