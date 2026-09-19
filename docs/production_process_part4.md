---

## 🧪 Step 7: 시뮬레이션

### Step 7-0: 시뮬레이션의 배경

**grill-me에서 확정:**
> "회사가 아직 없어서 시뮬레이션으로 검토"

**3가지 시뮬레이션:**
1. 로그 (질문/답변 기록)
2. 백업 (파일 저장)
3. 장애 (서버 다운 대응)

### Step 7-1: 로깅

**목표:** 질문/답변을 `logs/app.log`에 기록.

**ponytail 판정:** Python `logging` 모듈이면 충분. 별도 라이브러리 X.

**구현:**
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3,
    encoding="utf-8",
)
로테이션 동작:

text
[정상] app.log에 계속 기록
   ↓ (5MB 도달)
[로테이션] app.log → app.log.1
           app.log 새로 시작
   ↓ (또 5MB)
[로테이션] app.log.1 → app.log.2
           app.log → app.log.1
           app.log 새로 시작
   ↓ (3개 초과)
[자동 삭제] 가장 오래된 것부터
최대 20MB (5MB × 4개)로 제한.

Step 7-1 결과
실제 로그:

text
2026-09-19 18:34:28 [INFO] RAG 체인 로드 중...
2026-09-19 18:34:28 [INFO] 준비 완료
2026-09-19 18:35:27 [INFO] 질문: 식대 지원비는?
2026-09-19 18:35:36 [INFO] 답변: 3만원까지 지원됩니다.
2026-09-19 18:35:36 [INFO] 출처: company_policy.pdf
관찰:

질문→답변 9초 (iGPU 치고 양호)

시간순 정렬 정상

Step 7-2: 백업
목표: 1줄 명령어로 주요 폴더 백업.

ponytail 판정: PowerShell 스크립트 1개.

백업 대상:

data/ (원본 PDF)

chroma_db/ (임베딩)

logs/ (기록)

rag.py, main.py, streamlit_app.py (코드)

backup.ps1 실행 결과:

text
[백업 시작] backups\20260919_183641
  [OK] data
  [OK] chroma_db
  [OK] logs
  [OK] rag.py
  [OK] main.py
  [OK] streamlit_app.py
[백업 완료] 6 개 항목, 0.87 MB
관찰: 0.87MB — PDF가 텍스트만 있어서 작음.

Step 7-3: 장애 대응 문서
목표: docs/incident_playbook.md 작성.

4가지 시나리오:

백엔드(uvicorn)가 죽었을 때

Ollama가 죽었을 때

답변이 부정확할 때

로그 파일이 너무 커졌을 때

각 시나리오마다:

증상

원인

대응

예방

긴급 복구 체크리스트 7단계 + 백업 복원 방법 포함.

📖 Step 8: 마감
Step 8-1: requirements.txt + .gitignore
requirements.txt: 패키지 버전 고정 (재현성).

.gitignore: Git 제외 파일 정의.

gitignore
__pycache__/
venv/
chroma_db/
logs/
backups/
.vscode/
이유: 재생성 가능한 것은 Git에 안 올림.

Step 8-2: run.ps1 (실행 자동화)
목표: 백엔드 + 프론트 한 번에 실행.

ponytail 판정: 새 PowerShell 창 2개 띄우기 + 5초 대기 + 브라우저 열기.

run.ps1 실행 결과:

창 1: uvicorn 자동 실행

창 2: streamlit 자동 실행

5초 후 브라우저 자동 열림

1줄 명령어로 전체 시스템 기동.

Step 8-2 개선: 브라우저 자동 열기
첫 시도: 브라우저가 안 열림.

원인: Start-Process가 기본 브라우저 못 찾음.

해결: Start-Process "http://localhost:8501" 명시.

결과: 자동 열림 확인.

Step 8-3: README.md
목표: 처음 보는 사람도 설치/실행할 수 있게.

포함 내용:

프로젝트 소개 (1줄)

기술 스택

사전 요구사항

설치 방법 (7단계)

실행 방법 (1줄 + 수동)

테스트 질문 5개

폴더 구조

운영 (백업, 로그)

문제 해결 표

제약사항

Step 8-4: 최종 문서 2개
docs/structure.md — 각 파일 코드의 비전공자용 설명.

4개 파트:

개요 + rag.py

main.py

streamlit_app.py

run.ps1, backup.ps1 + 마무리

docs/production_process.md — 이 문서. 전체 과정 기록.

4개 파트:

개요 + grill-me + Step 1~2

Step 3 (RAG)

Step 5~6 (FastAPI + Streamlit)

Step 7~8 (시뮬레이션 + 마감) + 회고

🎓 회고
예상 vs 실제
항목	예상	실제
기간	3개월 (초심자) → 2일 (재정의)	1일
파일 개수	6개 (loader, splitter 등)	3개 (통합)
테스트	몇 개	5/5 정답
Docker	포함	연기 (YAGNI)
인증	포함	연기 (A 기준)
핵심 성공 요인
1. grill-me로 사전 검증

"2일 안에 완성품" → "데모 프로토타입"으로 범위 명확화

덕분에 방향 흔들림 없음

2. ponytail (YAGNI)

파일 6개 → 1개

Docker 스킵

불필요한 추상화 거부

3. LLM과 협업

에러 즉시 진단 + 수정

3개월 → 1일

4. Few-shot 학습 (핵심 발견)

3B 모델은 "규칙"보다 "예시"를 잘 따라함

프롬프트 v1(규칙 4개) → 실패

프롬프트 v3(예시 6개) → 성공

5. 후처리 (마지막 방어선)

프롬프트로 100% 못 막는 건 코드로 잡음

"None of the above" → "문서에서 찾을 수 없습니다"

문제 해결 기록
#	문제	해결
1	Python 3.14 호환성	3.11로 다운그레이드
2	PDF 손상	크롬으로 재저장
3	LangChain import 에러	패키지명 변경
4	연차 "15일"→"11일"	few-shot 예시 추가
5	"None of the above"	후처리 함수
6	사이드바 토글 안 보임	config.toml 수정
7	다크모드 미적용	theme 섹션 삭제
8	브라우저 자동 열기 실패	Start-Process URL 명시
배운 것 (비전공자 관점)
1. RAG (검색 증강 생성)

AI가 모르는 걸 "찾아서" 알려주는 기술.
AI 혼자 답하면 거짓말(환각). 문서를 먼저 찾아 보여주면 정확.

2. 임베딩 (숫자로 바꾸기)

글자를 숫자로 바꿔서 "비슷한 의미"를 찾는 기술.

3. Few-shot (예시 주기)

작은 AI는 "규칙"보다 "예시"를 잘 따라함.

4. YAGNI (You Aren't Gonna Need It)

"필요해질 때 추가하라." 미리 만들지 마라.

5. 시뮬레이션 검증

"회사가 없다" → 실제 환경 대신 시뮬레이션.

다음 단계 (3일차 예정)
기능	예상 시간
채팅 기록 목록 (JSON 저장)	5~6시간
프로젝트 생성/이름/설명	
채팅에 프로젝트 담기	
이름 변경/삭제	
최종 소감
"3개월 계획이 1일 만에 끝났다."

이유:

LLM과 함께 코딩

grill-me로 범위 사전 확정

ponytail로 최소 구현

문제마다 즉시 진단 + 수정

"빠르지만, 검증을 건너뛰지 않았다."

5/5 정답 테스트

로그/백업/장애 시뮬레이션

문서 4개 작성

📅 최종 타임라인
시각	단계	상태
11:19	프로젝트 폴더 생성	✅
11:30	grill-me 사전 검증	✅
12:00	Python 3.11 설치	✅
12:30	Ollama 모델 다운로드	✅
13:00	Step 1~2 (환경)	✅
14:00	Step 3 (RAG 파이프라인)	✅
15:30	Step 5 (FastAPI)	✅
16:00	Step 6 (Streamlit)	✅
17:00	UI 한국어화 + 사이드바	✅
18:00	Step 7 (시뮬레이션)	✅
18:40	Step 8 (마감)	✅
총 소요: 약 7시간 30분.