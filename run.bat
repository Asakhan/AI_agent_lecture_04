@echo off
REM AI 리서치 어시스턴트 실행 스크립트 (Windows)
REM 이 스크립트는 가상환경을 확인하고, 환경변수를 확인한 후 프로그램을 실행합니다.

REM 한글 출력을 위한 인코딩 설정 (run.ps1 참조)
REM PowerShell에서 실행될 때를 감지하여 인코딩 설정
REM 배치 파일이 PowerShell에서 실행될 때는 PowerShell 세션의 인코딩을 먼저 설정
REM 주의: 배치 파일 내에서 PowerShell 명령을 실행하면 새 프로세스가 시작되므로
REM       현재 세션에 영향을 주지 않을 수 있습니다. PowerShell에서 실행할 때는
REM       run_wrapper.ps1을 사용하거나, PowerShell에서 직접 인코딩을 설정한 후 실행하세요.
if defined PSVersionTable (
    REM PowerShell에서 실행 중이므로 PowerShell 명령으로 현재 세션의 인코딩 설정 시도
    REM 하지만 새 프로세스가 시작되므로 효과가 제한적일 수 있습니다
    powershell -NoProfile -Command "$OutputEncoding = [System.Text.Encoding]::GetEncoding(949); [Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(949); [Console]::InputEncoding = [System.Text.Encoding]::GetEncoding(949)" >nul 2>&1
)
REM 코드 페이지 설정 (CMD에서도 작동)
chcp 65001 >nul 2>&1

setlocal enabledelayedexpansion

REM 프로젝트 루트 디렉토리
set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "ENV_FILE=%PROJECT_ROOT%.env"
set "MAIN_SCRIPT=%PROJECT_ROOT%main.py"

REM Python 버전 설정 (chromadb 호환성을 위해 Python 3.12 사용)
set "PYTHON_CMD=py -3.12"
set "PYTHON_VERSION=3.12"

echo ========================================
echo AI 리서치 어시스턴트 실행
echo ========================================
echo.

REM Python 3.12 설치 확인
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python 3.12가 설치되어 있지 않습니다.
    echo.
    echo chromadb 호환성을 위해 Python 3.12가 필요합니다.
    echo 다음 링크에서 Python 3.12를 다운로드하여 설치해주세요:
    echo https://www.python.org/downloads/latest/python3.12/
    echo.
    echo 설치 시 "Add Python to PATH" 옵션을 체크해주세요.
    pause
    exit /b 1
)

echo [확인] Python 3.12가 설치되어 있습니다.
%PYTHON_CMD% --version

REM 1. 가상환경 확인 및 생성
if not exist "%VENV_DIR%" (
    echo [경고] 가상환경이 없습니다. Python 3.12로 생성 중...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [오류] 가상환경 생성에 실패했습니다.
        echo Python 3.12가 올바르게 설치되어 있는지 확인해주세요.
        pause
        exit /b 1
    )
    echo [성공] 가상환경이 생성되었습니다.
) else (
    REM 기존 가상환경의 Python 버전 확인
    if exist "%VENV_DIR%\Scripts\python.exe" (
        "%VENV_DIR%\Scripts\python.exe" --version 2>nul | findstr /C:"3.12" >nul
        if errorlevel 1 (
            echo [경고] 기존 가상환경이 Python 3.12가 아닙니다.
            echo Python 3.12로 재생성하기 위해 기존 가상환경을 삭제합니다...
            rmdir /s /q "%VENV_DIR%"
            echo Python 3.12로 가상환경 생성 중...
            %PYTHON_CMD% -m venv "%VENV_DIR%"
            if errorlevel 1 (
                echo [오류] 가상환경 생성에 실패했습니다.
                pause
                exit /b 1
            )
            echo [성공] 가상환경이 Python 3.12로 재생성되었습니다.
        ) else (
            echo [성공] 가상환경이 존재합니다 (Python 3.12).
        )
    ) else (
        echo [경고] 가상환경이 손상되었습니다. 재생성 중...
        rmdir /s /q "%VENV_DIR%" 2>nul
        %PYTHON_CMD% -m venv "%VENV_DIR%"
        if errorlevel 1 (
            echo [오류] 가상환경 생성에 실패했습니다.
            pause
            exit /b 1
        )
        echo [성공] 가상환경이 재생성되었습니다.
    )
)

REM 2. 가상환경 활성화
if exist "%VENV_ACTIVATE%" (
    echo 가상환경 활성화 중...
    call "%VENV_ACTIVATE%"
    if errorlevel 1 (
        echo [오류] 가상환경 활성화에 실패했습니다.
        pause
        exit /b 1
    )
    echo [성공] 가상환경이 활성화되었습니다.
) else (
    echo [오류] 가상환경 활성화 파일을 찾을 수 없습니다: %VENV_ACTIVATE%
    pause
    exit /b 1
)

REM 3. 패키지 설치 확인
echo 필수 패키지 확인 중...
python -c "import openai" 2>nul
if errorlevel 1 (
    echo [경고] 필수 패키지가 설치되지 않았습니다. 설치 중...
    python -m pip install --upgrade pip
    echo chromadb 설치 중... (이 작업은 시간이 걸릴 수 있습니다)
    pip install -r "%PROJECT_ROOT%requirements.txt"
    if errorlevel 1 (
        echo [오류] 패키지 설치에 실패했습니다.
        echo.
        echo Python 버전을 확인해주세요:
        python --version
        echo.
        echo Python 3.12가 필요합니다. 다음 명령어로 확인하세요:
        echo py -3.12 --version
        pause
        exit /b 1
    )
    echo [성공] 패키지 설치가 완료되었습니다.
) else (
    REM chromadb 설치 확인
    python -c "import chromadb" 2>nul
    if errorlevel 1 (
        echo [경고] chromadb가 설치되지 않았습니다. 설치 중...
        pip install chromadb>=0.4.0
        if errorlevel 1 (
            echo [오류] chromadb 설치에 실패했습니다.
            echo Python 버전을 확인해주세요: python --version
            pause
            exit /b 1
        )
        echo [성공] chromadb가 설치되었습니다.
    ) else (
        echo [성공] 필수 패키지가 설치되어 있습니다.
    )
)

REM 4. 환경변수 파일 확인
if not exist "%ENV_FILE%" (
    echo [오류] .env 파일을 찾을 수 없습니다!
    echo.
    echo 다음 내용으로 .env 파일을 생성해주세요:
    echo.
    echo OPENAI_API_KEY=your_api_key_here
    echo.
    set /p response="프로젝트 루트 디렉토리에 .env 파일을 생성하시겠습니까? (y/n): "
    if /i "!response!"=="y" (
        echo OPENAI_API_KEY=your_api_key_here > "%ENV_FILE%"
        echo [성공] .env 파일이 생성되었습니다. API 키를 입력해주세요.
        echo [경고] .env 파일을 열어서 실제 API 키로 변경해주세요!
        pause
        exit /b 1
    ) else (
        echo 프로그램을 종료합니다.
        pause
        exit /b 1
    )
) else (
    REM .env 파일에 OPENAI_API_KEY가 있는지 확인
    findstr /C:"OPENAI_API_KEY" "%ENV_FILE%" >nul
    if errorlevel 1 (
        echo [경고] .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.
        echo .env 파일을 확인하고 API 키를 설정해주세요.
        pause
        exit /b 1
    )
    findstr /C:"OPENAI_API_KEY=your_api_key_here" "%ENV_FILE%" >nul
    if not errorlevel 1 (
        echo [경고] .env 파일에 유효한 OPENAI_API_KEY가 설정되지 않았습니다.
        echo .env 파일을 확인하고 API 키를 설정해주세요.
        pause
        exit /b 1
    )
    findstr /C:"OPENAI_API_KEY=$" "%ENV_FILE%" >nul
    if not errorlevel 1 (
        echo [경고] .env 파일에 유효한 OPENAI_API_KEY가 설정되지 않았습니다.
        echo .env 파일을 확인하고 API 키를 설정해주세요.
        pause
        exit /b 1
    )
    echo [성공] .env 파일이 존재합니다.
)

REM 5. main.py 파일 확인
if not exist "%MAIN_SCRIPT%" (
    echo [오류] main.py 파일을 찾을 수 없습니다: %MAIN_SCRIPT%
    pause
    exit /b 1
)

echo.
echo ========================================
echo 모든 준비가 완료되었습니다!
echo 프로그램을 실행합니다...
echo ========================================
echo.

REM 6. main.py 실행
cd /d "%PROJECT_ROOT%"
python "%MAIN_SCRIPT%"

REM 프로그램 종료 후 대기 (오류 발생 시 확인 가능)
if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 오류가 발생했습니다.
    pause
)

endlocal
