#!/bin/bash

# Exclude 모드 예제
# 기본적으로 모든 메서드에 AOP로 인증이 적용되고, 
# 특정 어노테이션(@NoAuth, @PermitAll)이 있으면 인증 제외

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
echo "Exclude 모드 시나리오 생성"
echo "================================"
echo "- 기본적으로 모든 메서드에 인증 필요 (AOP)"
echo "- @NoAuth, @PermitAll → 인증 헤더 제외"
echo "- 어노테이션 없음 → 인증 헤더 추가"
echo ""

# Run the scenario generator
python3 generate_scenario.py \
/path/to/your/controller/YourController.java \
--output /Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator/projects/your_project \
--environment development \
--context-path /api/v1 \
--auth-bearer-token "your-jwt-token-here" \
--auth-annotations NoAuth PermitAll PublicAPI \
--auth-mode exclude \
--continue-on-error \
--format yaml

echo ""
echo "✅ Exclude 모드 시나리오 생성 완료!"
echo ""
echo "📝 참고: 이 예제는 샘플입니다. 실제 컨트롤러 경로로 변경하세요."
echo "   - 컨트롤러 경로를 실제 파일로 변경"
echo "   - 프로젝트명 수정"
echo "   - JWT 토큰 설정"
echo "   - 인증 제외 어노테이션 목록 확인"
