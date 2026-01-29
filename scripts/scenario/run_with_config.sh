#!/bin/bash

# =============================================================================
# 설정 파일을 사용하는 시나리오 생성 스크립트
# =============================================================================

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 설정 파일 로드
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/config.sh}"

if [ -f "$CONFIG_FILE" ]; then
    echo "📋 설정 파일 로드: $CONFIG_FILE"
    source "$CONFIG_FILE"
    
    # 설정 출력 함수가 있으면 실행
    if declare -f print_config > /dev/null; then
        print_config
    fi
else
    echo "⚠️  설정 파일이 없습니다: $CONFIG_FILE"
    echo "📝 예제 파일을 복사하여 사용하세요:"
    echo "   cp $SCRIPT_DIR/config_example.sh $CONFIG_FILE"
    echo ""
    
    # 기본 설정 사용
    echo "📌 기본 설정 사용"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    VENV_PATH="$PROJECT_ROOT/venv"
    SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"
fi

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

# 인자가 없으면 도움말 표시
if [ $# -eq 0 ]; then
    echo ""
    echo "사용법:"
    echo "  $0 <controller-path> [options]"
    echo ""
    echo "예제:"
    echo "  $0 \$WPM_CONTROLLER_PATH/WorkerController.java --output \$SCENARIO_OUTPUT_ROOT/wpm"
    echo ""
    python3 generate_scenario.py --help
    exit 0
fi

# 시나리오 생성기 실행
python3 generate_scenario.py "$@"

echo ""
echo "✅ 시나리오 생성 완료!"
