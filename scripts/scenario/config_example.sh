#!/bin/bash

# =============================================================================
# 시나리오 생성 스크립트 설정 파일 예제
# 
# 이 파일을 복사하여 config.sh로 저장하고 사용하세요:
# 1. cp config_example.sh config.sh
# 2. config.sh 내용 수정
# 3. 스크립트에서 source config.sh
# =============================================================================

# =============================================================================
# 프로젝트 경로 설정
# =============================================================================

# 프로젝트 루트 경로 (절대 경로 권장)
export PROJECT_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE/restapisimulator"

# 가상 환경 경로
export VENV_PATH="$PROJECT_ROOT/venv"

# 시나리오 생성기 경로
export SCENARIO_GENERATOR_DIR="$PROJECT_ROOT/scripts/scenario"

# =============================================================================
# 소스 코드 경로
# =============================================================================

# Java 소스 코드 루트 경로
export JAVA_SRC_ROOT="/Volumes/WORK/GIT_PROJECTS/TELCOWARE"

# 프로젝트별 컨트롤러 경로
export WPM_CONTROLLER_PATH="$JAVA_SRC_ROOT/sks-wpm-container-apps/app-mod/worker-app/src/main/java/com/sks/wpm/controller"
export CAPSHOME_CONTROLLER_PATH="$JAVA_SRC_ROOT/sks-capshome-container-apps/app-mod/device-user-app/src/main/java/com/sks/capshome/device/drg/controller"

# =============================================================================
# 출력 경로
# =============================================================================

# 시나리오 출력 루트 경로
export SCENARIO_OUTPUT_ROOT="$PROJECT_ROOT/projects"

# =============================================================================
# 인증 설정
# =============================================================================

# WPM 프로젝트 인증 설정
export WPM_AUTH_MODE="include"
export WPM_AUTH_ANNOTATIONS="UserCert:wpm-get-user-info.json"
export WPM_CUSTOM_HEADER="X-Header-Extra-Info:{{USER_CERT_TOKEN}}"

# CAPS Home 프로젝트 인증 설정
export CAPSHOME_AUTH_MODE="exclude"
export CAPSHOME_AUTH_ANNOTATIONS="NoAuth"
export CAPSHOME_AUTH_TOKEN="{{USER_CERT_TOKEN}}"

# =============================================================================
# 기본 설정
# =============================================================================

# 기본 환경
export DEFAULT_ENVIRONMENT="development"

# 기본 Context Path
export DEFAULT_CONTEXT_PATH="/api/v1"

# 기본 출력 형식
export DEFAULT_FORMAT="yaml"

# Continue on Error 옵션
export DEFAULT_CONTINUE_ON_ERROR="true"

# =============================================================================
# 함수: 설정 출력
# =============================================================================

print_config() {
    echo "================================"
    echo "현재 설정"
    echo "================================"
    echo "📂 프로젝트 루트: $PROJECT_ROOT"
    echo "🐍 가상 환경: $VENV_PATH"
    echo "⚙️  생성기 경로: $SCENARIO_GENERATOR_DIR"
    echo "☕ Java 소스: $JAVA_SRC_ROOT"
    echo "📝 출력 경로: $SCENARIO_OUTPUT_ROOT"
    echo "🌍 환경: $DEFAULT_ENVIRONMENT"
    echo "📄 형식: $DEFAULT_FORMAT"
    echo ""
}
