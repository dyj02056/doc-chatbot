# 📄 회사 문서 AI 챗봇

PDF 문서를 업로드하면 로컬 LLM이 한국어로 답변하는 웹 서비스.

- **API 비용 0원** — 모든 처리가 로컬에서
- **문서 유출 0%** — 외부 서버 전송 없음
- **인터넷 없이 작동** — 완전 오프라인

---

## 🎯 주요 기능

- PDF 문서 기반 질의응답
- 한국어 답변 (Kanana-2-3B-Instruct)
- 출처 표시 (파일명)
- 환각 방지 ("문서에서 찾을 수 없습니다")
- 채팅 기록 유지
- 로그 자동 기록 (5MB × 4개 로테이션)
- 백업 스크립트

---

## 🛠️ 기술 스택

| 역할 | 도구 |
|---|---|
| LLM | Ollama + Kanana-2-3B-Instruct (Q4_K_M) |
| 임베딩 | Ollama + bge-m3 |
| RAG | LangChain |
| 벡터 DB | ChromaDB |
| 백엔드 | FastAPI |
| 프론트 | Streamlit |
| 배포 | 로컬 (Windows) |

---

## 📋 사전 요구사항

| 항목 | 버전 | 확인 명령어 |
|---|---|---|
| **Python** | **3.11** (3.14 비권장) | `py -3.11 --version` |
| **Ollama** | 0.3.x 이상 | `ollama --version` |
| **RAM** | 8GB 이상 | - |
| **디스크** | 10GB 여유 | - |

---

## 🚀 설치

### 1. Ollama 설치

- Windows: [ollama.com/download](https://ollama.com/download) → `OllamaSetup.exe`

### 2. 모델 다운로드

```powershell
ollama pull hf.co/mradermacher/kanana-2-3b-instruct-GGUF:Q4_K_M
ollama pull bge-m3

3. 프로젝트 클론 (또는 폴더 복사)
powershell
cd doc-chatbot
4. Python 가상환경 생성
powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
5. 패키지 설치
powershell
pip install -r requirements.txt

6. PDF 준비
data/ 폴더에 PDF 3개를 넣습니다:

company_policy.pdf

product_manual.pdf

project_report.pdf

7. 최초 인덱싱 (1회만, 5~15분)
powershell
python rag.py --rebuild
완료되면 chroma_db/ 폴더가 생성됩니다.
exit 로 종료.

▶️ 실행
방법 1: 한 방에 실행 (권장)
powershell
.\run.ps1
백엔드(uvicorn)와 프론트(streamlit)가 새 창 2개로 뜸

5초 후 브라우저 자동 열림 (http://localhost:8501)

실행 정책 에러 시:

powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1
방법 2: 수동 실행 (터미널 2개)
터미널 1 (백엔드):

powershell
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
터미널 2 (프론트):

powershell
.\venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
브라우저: http://localhost:8501

🧪 테스트 질문
질문	예상 답변
연차 휴가는 며칠인가요?	15일
병가는 며칠까지 쓸 수 있나요?	10일
식대는 얼마인가요?	3만원
허브가 연결되지 않으면 어떻게 하나요?	Wi-Fi 비밀번호를 확인하세요
작년 회사 매출은 얼마인가요?	문서에서 찾을 수 없습니다
📁 폴더 구조
text
doc-chatbot/
├── venv/                      # Python 가상환경
├── data/                      # 원본 PDF
│   ├── company_policy.pdf
│   ├── product_manual.pdf
│   └── project_report.pdf
├── chroma_db/                 # 벡터 DB (자동 생성)
├── logs/                      # 로그 (자동 생성)
│   └── app.log
├── backups/                   # 백업 (자동 생성)
├── docs/                      # 문서
│   ├── incident_playbook.md   # 장애 대응
│   ├── structure.md           # 코드 설명
│   └── production_process.md  # 제작 과정
├── rag.py                     # RAG 파이프라인
├── main.py                    # FastAPI 백엔드
├── streamlit_app.py           # Streamlit 프론트
├── backup.ps1                 # 백업 스크립트
├── run.ps1                    # 실행 스크립트
├── requirements.txt           # 패키지 목록
├── .gitignore
└── README.md
🔧 운영
백업
powershell
.\backup.ps1
backups/YYYYMMDD_HHMMSS/ 폴더에 저장.

로그 확인
powershell
Get-Content logs\app.log -Tail 20
장애 대응
docs/incident_playbook.md 참조.

⚠️ 문제 해결
증상	원인	해결
백엔드 연결 실패	uvicorn 미실행	run.ps1 재실행
답변 30초+	iGPU 성능 한계	정상, 대기
답변 부정확	인덱스 손상	Remove-Item -Recurse chroma_db 후 python rag.py --rebuild
PDF 로딩 실패	PDF 손상	PDF 뷰어로 열리는지 확인
포트 충돌 (8000, 8501)	이전 프로세스	이전 터미널 창 닫기
📌 제약사항
Windows 전용 (PowerShell 스크립트 사용)

PDF만 지원 (HWP, DOCX 미지원)

단일 사용자 (동시 접속자 1명 기준)

3B 모델 한계 — 복잡한 추론은 부정확할 수 있음

📄 라이선스
Kanana-2: Kanana Open License (상업적 사용 가능)

bge-m3: MIT

기타: 각 라이브러리 라이선스

📅 버전
v0.1.0 (2026-09-19)

text

---

## 📌 확인 방법

`doc-chatbot/` 폴더에 `README.md` 파일이 생성됐는지 확인:

```powershell
dir README.md
파일이 보이면 성공.