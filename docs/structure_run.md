# 🔧 `run.ps1` — 실행 스크립트

## 📌 이 파일이 하는 일

> **"백엔드(uvicorn)와 프론트(streamlit)를 한 번에 실행해주는 자동화 스크립트"**

## 🍕 비유: 지배인

- 손님(사용자)이 문 열면, **지배인이 직원들(백엔드+프론트)을 한 번에 호출**
- 각 직원을 따로 부를 필요 없음

---

## 🔍 코드 한 줄씩

### ① 기본 설정

```powershell
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 회사 문서 AI 챗봇 실행" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
하는 일:

$ErrorActionPreference = "Stop" → 에러 나면 즉시 중단

Write-Host → 터미널에 글자 출력

-ForegroundColor Cyan → 청록색

비유: 프로그램 시작 시 "출발!" 외치는 것.

② venv 확인
powershell
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "[오류] venv 폴더가 없습니다." -ForegroundColor Red
    Write-Host "다음 명령어로 생성하세요:" -ForegroundColor Yellow
    Write-Host "  py -3.11 -m venv venv" -ForegroundColor Yellow
    exit 1
}
하는 일:

venv 폴더 있는지 확인

없으면 빨간 경고 + 해결법 안내 + 종료

비유: 요리 시작 전 "냉장고 있나?" 확인.

③ 백엔드 시작 (새 창)
powershell
Write-Host "[1/2] 백엔드(uvicorn) 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; Write-Host '[백엔드] uvicorn 실행 중...' -ForegroundColor Cyan; uvicorn main:app --reload --port 8000"
)
하는 일:

새 PowerShell 창 열기 (Start-Process powershell)

-NoExit: 명령 끝나도 창 유지

그 창에서:

현재 폴더로 이동
venv 활성화
안내 메시지 출력
uvicorn 실행
비유: 별도 방에서 은행원 출근시키기.

④ 로딩 대기
powershell
Write-Host "    5초 대기 (RAG 체인 로딩)..." -ForegroundColor Gray
Start-Sleep -Seconds 5
하는 일:

5초 대기

백엔드가 ChromaDB 로딩할 시간을 줌

왜? 백엔드 준비 안 됐는데 프론트가 켜지면 첫 질문 실패.

⑤ 프론트 시작 (새 창)
powershell
Write-Host "[2/2] 프론트(streamlit) 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; Write-Host '[프론트] streamlit 실행 중...' -ForegroundColor Cyan; streamlit run streamlit_app.py"
)
하는 일:

또 다른 새 PowerShell 창 열기

그 창에서 streamlit 실행

비유: 또 다른 방에서 안내원 출근시키기.

⑥ 브라우저 자동 열기
powershell
Write-Host "    5초 대기 (streamlit 로딩)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "브라우저 열기..." -ForegroundColor Yellow
Start-Process "http://localhost:8501"
하는 일:

5초 대기 (streamlit 준비)

브라우저 자동 열기

비유: 손님을 은행 안내데스크로 안내.

⑦ 완료 메시지
powershell
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 실행 완료" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  백엔드: http://localhost:8000" -ForegroundColor Green
Write-Host "  프론트: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "종료하려면 열린 터미널 창을 닫으세요." -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Green
하는 일: 최종 안내 메시지 출력.

📊 run.ps1의 장점
항목	명령어 개수
수동 실행	6줄 (venv 활성화 × 2 + uvicorn + streamlit + 브라우저)
run.ps1	1줄 (.\run.ps1)
비유: 리모컨 하나로 TV + 사운드바 + 조명 다 켜기.

🔧 backup.ps1 — 백업 스크립트
📌 이 파일이 하는 일
"주요 파일들을 시간별 폴더에 자동 백업"

🍕 비유: 사무원
"오늘 업무 자료 백업해둬" 하면

지정된 폴더를 날짜별 폴더에 복사

🔍 코드 한 줄씩
① 백업 대상 정의
powershell
$targets = @("data", "chroma_db", "logs", "rag.py", "main.py", "streamlit_app.py")
하는 일: 백업할 항목 목록.

항목	이유
data	원본 PDF (재생성 어려움)
chroma_db	임베딩 (재생성 5~15분)
logs	기록
rag.py, main.py, streamlit_app.py	코드
② 타임스탬프 + 폴더 생성
powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups\$timestamp"

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
하는 일:

현재 시간 → 20260919_183641 형식

backups/20260919_183641/ 폴더 생성

비유: 오늘 날짜 폴더 만들기.

③ 복사 반복문
powershell
foreach ($target in $targets) {
    if (Test-Path $target) {
        if ((Get-Item $target).PSIsContainer) {
            # 폴더
            Copy-Item -Path $target -Destination $backupDir -Recurse -Force
            $size = (Get-ChildItem $target -Recurse | Measure-Object -Property Length -Sum).Sum
        } else {
            # 파일
            Copy-Item -Path $target -Destination $backupDir -Force
            $size = (Get-Item $target).Length
        }
        $totalSize += $size
        $copiedCount++
        Write-Host "  [OK] $target" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] $target (없음)" -ForegroundColor Yellow
    }
}
하는 일:

각 대상 확인

폴더면 → -Recurse (하위 폴더까지 복사)

파일이면 → 그냥 복사

크기 계산 (통계)

성공: [OK] 초록색

없음: [SKIP] 노란색

비유: 목록 보면서 하나씩 복사.

④ 완료 메시지
powershell
$totalMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "[백업 완료] $copiedCount 개 항목, $totalMB MB" -ForegroundColor Cyan
Write-Host "위치: $backupDir" -ForegroundColor Cyan
결과 예:

text
[백업 완료] 6 개 항목, 0.87 MB
위치: backups\20260919_183641
📊 백업 폴더 구조
text
backups/
├── 20260919_183641/
│   ├── data/
│   │   ├── company_policy.pdf
│   │   ├── product_manual.pdf
│   │   └── project_report.pdf
│   ├── chroma_db/
│   ├── logs/
│   │   └── app.log
│   ├── rag.py
│   ├── main.py
│   └── streamlit_app.py
└── 20260920_090000/   ← 다음 백업
비유: 매번 "타임캡슐" 을 만들어 저장.