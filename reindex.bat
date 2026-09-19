@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo  재인덱싱 자동 실행
echo ========================================
echo.

cd /d "%~dp0"

REM ===== 1. uvicorn 종료 =====
echo [1/4] uvicorn 종료 중...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo      완료
echo.

REM ===== 2. chroma_db 삭제 =====
echo [2/4] chroma_db 삭제 중...
if exist "chroma_db" (
    rmdir /S /Q "chroma_db"
    if exist "chroma_db" (
        echo      [오류] chroma_db 삭제 실패
        echo      uvicorn이 아직 실행 중일 수 있습니다.
        echo      작업 관리자에서 python.exe를 모두 종료하세요.
        pause
        exit /b 1
    )
    echo      완료
) else (
    echo      폴더 없음 (건너뜀)
)
echo.

REM ===== 3. 재인덱싱 =====
echo [3/4] 재인덱싱 중... (5~15분 소요)
echo      브라우저 창은 닫아도 됩니다.
echo.
call .\venv\Scripts\activate.bat
python rag.py --rebuild
if errorlevel 1 (
    echo.
    echo      [오류] 재인덱싱 실패
    pause
    exit /b 1
)
echo.
echo      재인덱싱 완료
echo.

REM ===== 4. uvicorn 재시작 (새 창) =====
echo [4/4] uvicorn 재시작 중...
start "Doc Chatbot Backend" cmd /k "cd /d %~dp0 && call .\venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000"

echo.
echo ========================================
echo  완료
echo ========================================
echo.
echo  백엔드: http://localhost:8000
echo.
echo  브라우저에서 Ctrl+Shift+R 로 새로고침하세요.
echo.
pause
