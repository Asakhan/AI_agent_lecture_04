@echo off
REM Python 3.12 설치 및 가상환경 재생성 스크립트
REM 이 스크립트는 Python 3.12 설치를 안내하고, 설치 후 가상환경을 자동으로 재생성합니다.

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%venv"

echo ========================================
echo Python 3.12 설치 및 가상환경 설정
echo ========================================
echo.

REM Python 3.12 설치 확인
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [경고] Python 3.12가 설치되어 있지 않습니다.
    echo.
    echo Python 3.12를 설치하는 방법:
    echo.
    echo 방법 1: 공식 웹사이트에서 다운로드
    echo   https://www.python.org/downloads/latest/python3.12/
    echo   설치 시 "Add Python to PATH" 옵션을 체크하세요.
    echo.
    echo 방법 2: py launcher 사용 (Windows 10/11)
    echo   py install 3.12
    echo.
    echo 방법 3: winget 사용 (Windows 10/11)
    echo   winget install Python.Python.3.12
    echo.
    echo.
    set /p install_now="지금 py launcher로 Python 3.12를 설치하시겠습니까? (y/n): "
    if /i "!install_now!"=="y" (
        echo.
        echo Python 3.12 설치 중...
        py install 3.12
        if errorlevel 1 (
            echo [오류] py launcher를 통한 설치에 실패했습니다.
            echo 공식 웹사이트에서 수동으로 설치해주세요.
            pause
            exit /b 1
        )
        echo [성공] Python 3.12가 설치되었습니다.
        echo.
        echo 터미널을 다시 시작한 후 이 스크립트를 다시 실행해주세요.
        pause
        exit /b 0
    ) else (
        echo.
        echo Python 3.12를 설치한 후 이 스크립트를 다시 실행해주세요.
        pause
        exit /b 1
    )
)

echo [확인] Python 3.12가 설치되어 있습니다.
py -3.12 --version
echo.

REM 기존 가상환경 확인 및 삭제
if exist "%VENV_DIR%" (
    echo [경고] 기존 가상환경이 발견되었습니다.
    echo Python 3.12로 재생성하기 위해 삭제합니다...
    rmdir /s /q "%VENV_DIR%"
    if errorlevel 1 (
        echo [오류] 기존 가상환경 삭제에 실패했습니다.
        echo 가상환경이 사용 중일 수 있습니다. 터미널을 닫고 다시 시도해주세요.
        pause
        exit /b 1
    )
    echo [성공] 기존 가상환경이 삭제되었습니다.
)

REM Python 3.12로 새 가상환경 생성
echo.
echo Python 3.12로 새 가상환경 생성 중...
py -3.12 -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [오류] 가상환경 생성에 실패했습니다.
    pause
    exit /b 1
)
echo [성공] 가상환경이 생성되었습니다.
echo.

REM 가상환경 활성화 및 패키지 설치
echo 가상환경 활성화 중...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [오류] 가상환경 활성화에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo Python 버전 확인:
python --version
echo.

echo pip 업그레이드 중...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [경고] pip 업그레이드에 실패했습니다. 계속 진행합니다...
)

echo.
echo 필수 패키지 설치 중...
echo (chromadb 설치에는 시간이 걸릴 수 있습니다)
python -m pip install -r "%PROJECT_ROOT%requirements.txt"
if errorlevel 1 (
    echo [오류] 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [성공] 모든 설정이 완료되었습니다!
echo ========================================
echo.
echo 설치된 패키지 확인:
python -c "import chromadb; print('chromadb:', chromadb.__version__)" 2>nul
if errorlevel 1 (
    echo [경고] chromadb 확인에 실패했습니다.
) else (
    echo [확인] chromadb가 정상적으로 설치되었습니다.
)
echo.

pause

endlocal
