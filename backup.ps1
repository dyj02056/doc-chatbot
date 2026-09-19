# backup.ps1 — 프로젝트 백업 스크립트
# 사용법: .\backup.ps1
# 결과: backups\YYYYMMDD_HHMMSS\ 폴더에 주요 파일 복사

$ErrorActionPreference = "Stop"

# 백업 대상
$targets = @("data", "chroma_db", "logs", "rag.py", "main.py", "streamlit_app.py")

# 타임스탬프
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups\$timestamp"

# 백업 폴더 생성
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "[백업 시작] $backupDir" -ForegroundColor Cyan

$copiedCount = 0
$totalSize = 0

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

$totalMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "[백업 완료] $copiedCount 개 항목, $totalMB MB" -ForegroundColor Cyan
Write-Host "위치: $backupDir" -ForegroundColor Cyan
