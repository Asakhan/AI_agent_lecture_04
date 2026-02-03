# Python 3.12 설치 가이드

`chromadb`를 사용하기 위해 Python 3.12가 필요합니다.

## 설치 방법

### 방법 1: 공식 웹사이트에서 다운로드 (권장)

1. 다음 링크에서 Python 3.12를 다운로드하세요:
   - https://www.python.org/downloads/latest/python3.12/
   - 또는 직접: https://www.python.org/ftp/python/3.12.12/python-3.12.12-amd64.exe

2. 다운로드한 설치 파일을 실행하세요.

3. **중요**: 설치 시 다음 옵션을 반드시 체크하세요:
   - ✅ **"Add Python 3.12 to PATH"** (PATH에 Python 3.12 추가)
   - ✅ **"Install for all users"** (선택사항, 관리자 권한 필요)

4. 설치가 완료되면 터미널을 다시 열고 다음 명령어로 확인하세요:
   ```powershell
   py -3.12 --version
   ```
   출력: `Python 3.12.x`

### 방법 2: py launcher를 사용한 자동 설치 (Windows 10/11)

Windows의 `py` launcher를 사용하여 Python 3.12를 설치할 수 있습니다:

```powershell
# Python 3.12 설치 (Microsoft Store에서 자동 다운로드)
py install 3.12
```

또는:

```powershell
# winget을 사용한 설치 (Windows 10/11)
winget install Python.Python.3.12
```

## 설치 확인

설치 후 다음 명령어로 확인하세요:

```powershell
py -3.12 --version
python --version  # 기본 Python 버전 (3.14.2일 수 있음)
py -0  # 설치된 모든 Python 버전 목록
```

## 가상환경 재생성

Python 3.12가 설치되면 다음 단계를 수행하세요:

1. 기존 가상환경 삭제:
   ```powershell
   Remove-Item -Recurse -Force venv
   ```

2. Python 3.12로 새 가상환경 생성:
   ```powershell
   py -3.12 -m venv venv
   ```

3. 가상환경 활성화:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. 패키지 설치:
   ```powershell
   pip install -r requirements.txt
   ```

또는 `run.bat`를 실행하면 자동으로 처리됩니다:
```powershell
.\run.bat
```

## 문제 해결

### "py -3.12"가 작동하지 않는 경우

1. Python 3.12가 올바르게 설치되었는지 확인:
   ```powershell
   py -0
   ```

2. Python 3.12의 전체 경로를 사용:
   ```powershell
   # 일반적인 설치 경로
   C:\Users\<사용자명>\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
   ```

3. 또는 환경 변수 PATH에 Python 3.12가 추가되었는지 확인
