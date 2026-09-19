# run.ps1 — 백엔드(uvicorn) + 프론트(streamlit) 한 번에 실행
# 사용법: .\run.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 회사 문서 AI 챗봇 실행" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# venv 확인
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "[오류] venv 폴더가 없습니다." -ForegroundColor Red
    Write-Host "다음 명령어로 생성하세요:" -ForegroundColor Yellow
    Write-Host "  py -3.11 -m venv venv" -ForegroundColor Yellow
    exit 1
}

# 백엔드 시작 (새 창)
Write-Host "[1/2] 백엔드(uvicorn) 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; Write-Host '[백엔드] uvicorn 실행 중...' -ForegroundColor Cyan; uvicorn main:app --reload --port 8000"
)

# 백엔드 로딩 대기
Write-Host "    5초 대기 (RAG 체인 로딩)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 프론트 시작 (새 창)
Write-Host "[2/2] 프론트(streamlit) 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; Write-Host '[프론트] streamlit 실행 중...' -ForegroundColor Cyan; streamlit run streamlit_app.py"
)

# 프론트 로딩 대기 후 브라우저 열기
Write-Host "    5초 대기 (streamlit 로딩)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "브라우저 열기..." -ForegroundColor Yellow
Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 실행 완료" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  백엔드: http://localhost:8000" -ForegroundColor Green
Write-Host "  프론트: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "종료하려면 열린 터미널 창을 닫으세요." -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Green
