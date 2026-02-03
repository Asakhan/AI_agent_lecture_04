#!/bin/bash

# AI 리서치 어시스턴트 실행 스크립트 (Mac/Linux)
# 이 스크립트는 가상환경을 확인하고, 환경변수를 확인한 후 프로그램을 실행합니다.

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
VENV_ACTIVATE="$VENV_DIR/bin/activate"
ENV_FILE="$PROJECT_ROOT/.env"
MAIN_SCRIPT="$PROJECT_ROOT/main.py"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI 리서치 어시스턴트 실행${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 가상환경 확인 및 생성
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠ 가상환경이 없습니다. 생성 중...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ 가상환경이 생성되었습니다.${NC}"
else
    echo -e "${GREEN}✓ 가상환경이 존재합니다.${NC}"
fi

# 2. 가상환경 활성화
if [ -f "$VENV_ACTIVATE" ]; then
    echo -e "${BLUE}가상환경 활성화 중...${NC}"
    source "$VENV_ACTIVATE"
    echo -e "${GREEN}✓ 가상환경이 활성화되었습니다.${NC}"
else
    echo -e "${RED}✗ 가상환경 활성화 파일을 찾을 수 없습니다: $VENV_ACTIVATE${NC}"
    exit 1
fi

# 3. 패키지 설치 확인
echo -e "${BLUE}필수 패키지 확인 중...${NC}"
if ! python -c "import openai" 2>/dev/null; then
    echo -e "${YELLOW}⚠ 필수 패키지가 설치되지 않았습니다. 설치 중...${NC}"
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "${GREEN}✓ 패키지 설치가 완료되었습니다.${NC}"
else
    echo -e "${GREEN}✓ 필수 패키지가 설치되어 있습니다.${NC}"
fi

# 4. 환경변수 파일 확인
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ .env 파일을 찾을 수 없습니다!${NC}"
    echo -e "${YELLOW}다음 내용으로 .env 파일을 생성해주세요:${NC}"
    echo ""
    echo "OPENAI_API_KEY=your_api_key_here"
    echo ""
    echo -e "${YELLOW}프로젝트 루트 디렉토리에 .env 파일을 생성하시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "OPENAI_API_KEY=your_api_key_here" > "$ENV_FILE"
        echo -e "${GREEN}✓ .env 파일이 생성되었습니다. API 키를 입력해주세요.${NC}"
        echo -e "${YELLOW}⚠ .env 파일을 열어서 실제 API 키로 변경해주세요!${NC}"
        exit 1
    else
        echo -e "${RED}프로그램을 종료합니다.${NC}"
        exit 1
    fi
else
    # .env 파일에 OPENAI_API_KEY가 있는지 확인
    if ! grep -q "OPENAI_API_KEY" "$ENV_FILE" || grep -q "OPENAI_API_KEY=your_api_key_here" "$ENV_FILE" || grep -q "OPENAI_API_KEY=$" "$ENV_FILE"; then
        echo -e "${YELLOW}⚠ .env 파일에 유효한 OPENAI_API_KEY가 설정되지 않았습니다.${NC}"
        echo -e "${YELLOW}.env 파일을 확인하고 API 키를 설정해주세요.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ .env 파일이 존재합니다.${NC}"
fi

# 5. main.py 파일 확인
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}✗ main.py 파일을 찾을 수 없습니다: $MAIN_SCRIPT${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}모든 준비가 완료되었습니다!${NC}"
echo -e "${GREEN}프로그램을 실행합니다...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 6. main.py 실행
cd "$PROJECT_ROOT"
python "$MAIN_SCRIPT"
