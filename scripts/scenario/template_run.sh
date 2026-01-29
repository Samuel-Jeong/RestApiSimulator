#!/bin/bash

# =============================================================================
# 시나리오 생성 스크립트 템플릿
# 이 파일을 복사하여 프로젝트별 스크립트를 만드세요
# =============================================================================

# =============================================================================
# 경로 설정
# =============================================================================

# 방법 1: 자동 경로 탐지 (권장)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 방법 2: 절대 경로 직접 지정 (필요 시 아래 주석 해제 후 수정)
# PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"
# VENV_PATH="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/venv"
# SCENARIO_GENERATOR_DIR="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/scripts/scenario"

# 방법 3: 환경 변수 사용
# export PROJECT_ROOT="/your/custom/path"
# export VENV_PATH="/your/custom/venv"
# export SCENARIO_GENERATOR_DIR="/your/custom/generator"

# 최종 경로 설정 (우선순위: 환경변수 > 직접지정 > 자동탐지)
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/venv}"
SCENARIO_GENERATOR_DIR="${SCENARIO_GENERATOR_DIR:-$PROJECT_ROOT/scripts/scenario}"

# =============================================================================
# 가상 환경 활성화
# =============================================================================

echo "================================"
echo "시나리오 생성 스크립트"
echo "================================"
echo "📂 프로젝트 루트: $PROJECT_ROOT"
echo "🐍 가상 환경: $VENV_PATH"
echo "⚙️  생성기 경로: $SCENARIO_GENERATOR_DIR"
echo ""

if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ 가상 환경 활성화 성공"
else
    echo "❌ 가상 환경을 찾을 수 없습니다: $VENV_PATH"
    echo ""
    echo "해결 방법:"
    echo "1. 가상 환경 생성: python3 -m venv $PROJECT_ROOT/venv"
    echo "2. 스크립트에서 VENV_PATH 경로 수정"
    exit 1
fi

# =============================================================================
# 시나리오 생성기 실행
# =============================================================================

if [ ! -f "$SCENARIO_GENERATOR_DIR/generate_scenario.py" ]; then
    echo "❌ 시나리오 생성기를 찾을 수 없습니다: $SCENARIO_GENERATOR_DIR/generate_scenario.py"
    exit 1
fi

cd "$SCENARIO_GENERATOR_DIR" || exit 1

# =============================================================================
# 여기부터 프로젝트별 설정을 수정하세요
# =============================================================================

python3 generate_scenario.py \
/path/to/your/controller/YourController.java \
--output /path/to/output \
--environment development \
--context-path /api/v1 \
--auth-bearer-token "your-token" \
--auth-annotations YourAnnotation \
--auth-mode include \
--continue-on-error \
--format yaml

echo ""
echo "✅ 시나리오 생성 완료!"
