---

# 🔧 `main.py` — 창구 (API 백엔드)

## 📌 이 파일이 하는 일

> **"rag.py의 기능을 웹 API로 감싸서, 브라우저나 다른 프로그램에서 쓸 수 있게 한다."**

## 🍕 비유: 은행 창구

- `rag.py` = **은행원** (실제 일하는 사람)
- `main.py` = **창구** (손님 받는 곳)
- 손님(브라우저)이 창구에 질문 → 은행원이 처리 → 창구가 답변 전달

---

## 🔍 코드 한 줄씩

### ① 모듈 docstring

```python
"""
main.py — 회사 문서 AI 챗봇의 FastAPI 백엔드
ponytail: rag.py를 그대로 감싸는 최소 API. /ask와 /health만.
업로드 기능은 필요해지면 추가.

변경 이력:
- 최초 작성: /ask, /health 두 엔드포인트
- 로깅 추가: logs/app.log에 질문/답변/에러 기록
"""
하는 일: 파일 정체와 변경 이력 기록.

② 라이브러리 import
python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag import init_rag
하는 일: 외부 도구 + rag.py의 함수 불러오기.

라이브러리	역할
logging	로그 기록
RotatingFileHandler	로그 자동 순환 (5MB × 4개)
FastAPI	웹 API 서버
HTTPException	HTTP 에러 응답
BaseModel	요청/응답 데이터 형식 정의
asynccontextmanager	서버 시작/종료 시 실행할 코드
init_rag	rag.py의 RAG 초기화 함수
from rag import init_rag — 이 한 줄이 두 파일을 연결합니다.

③ 로깅 설정
python
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("doc_chatbot")
logger.setLevel(logging.INFO)
하는 일:

logs/ 폴더 생성 (없으면)

로거 객체 생성

로그 레벨 = INFO (일반 정보부터 기록)

exist_ok=True: 폴더가 이미 있어도 에러 안 냄.

④ 파일 핸들러 (로그 저장)
python
file_handler = RotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(file_handler)
하는 일:

logs/app.log 파일에 로그 기록

5MB 넘으면 자동 순환 (app.log → app.log.1 → app.log.2 → app.log.3)

백업 3개 유지 → 최대 20MB

형식: 2026-09-19 18:35:27 [INFO] 질문: 식대 지원비는?

RotatingFileHandler 동작:

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
비유: 노트가 꽉 차면 새 노트로 갈아타고, 오래된 노트는 3권까지만 보관.

⑤ 콘솔 핸들러 (터미널 출력)
python
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)
하는 일: 터미널에도 로그 출력 (파일과 별도).

결과: 터미널에 [INFO] 질문: ... 뜸.

⑥ 전역 상태 (RAG 체인 저장)
python
_state = {"chain": None, "retriever": None}
하는 일:

서버 시작 시 로드한 RAG 체인을 전역에 보관

매 요청마다 재사용 (매번 새로 로드 안 함)

비유: 은행 문 열 때 금고 잠금 해제. 손님마다 다시 안 함.

None으로 초기화: 아직 로드 안 됐다는 표시.

⑦ 서버 시작/종료 이벤트
python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 RAG 체인을 한 번만 로드."""
    logger.info("RAG 체인 로드 중...")
    chain, retriever = init_rag(rebuild=False)
    _state["chain"] = chain
    _state["retriever"] = retriever
    logger.info("준비 완료")
    yield
    logger.info("서버 종료")
하는 일 (서버 생애주기):

서버 시작 시 (yield 이전):

init_rag() 호출 → ChromaDB 로드

전역 _state에 저장

"준비 완료" 로그

서버 실행 중 (yield):

요청 처리 (아래 엔드포인트)

서버 종료 시 (yield 이후):

"서버 종료" 로그

비유: 은행 문 열 때 준비, 문 닫을 때 정리.

yield: "여기서 잠시 멈추고 서버를 실행시켜라"는 표시.

⑧ FastAPI 앱 생성
python
app = FastAPI(title="Doc Chatbot API", lifespan=lifespan)
하는 일:

웹 서버 앱 생성

lifespan=lifespan → 위에서 만든 시작/종료 이벤트 연결

⑨ 요청/응답 데이터 형식
python
class Query(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str]
하는 일:

들어오는 데이터 형식 (Query): {"question": "..."}

나가는 데이터 형식 (Answer): {"answer": "...", "sources": [...]}

비유:

창구에 낼 신청서 양식 (Query)

창구에서 받을 결과 확인서 양식 (Answer)

BaseModel: Pydantic이 자동 검증해줌.

⑩ /health 엔드포인트
python
@app.get("/health")
def health():
    """서버 상태 확인."""
    ready = _state["chain"] is not None
    return {"status": "ok" if ready else "loading", "ready": ready}
하는 일:

브라우저에서 http://localhost:8000/health 접속 시

서버 상태 반환

응답 예:

json
{"status": "ok", "ready": true}
용도: "서버 살아있나?" 확인. 모니터링에도 유용.

⑪ /ask 엔드포인트 (핵심!)
python
@app.post("/ask", response_model=Answer)
def ask(q: Query):
    """질문을 받아 문서 기반 답변과 출처를 반환."""
    if _state["chain"] is None:
        logger.warning("RAG 체인 미준비 상태에서 요청 들어옴")
        raise HTTPException(status_code=503, detail="RAG 체인 로드 중입니다")

    if not q.question.strip():
        logger.warning("빈 질문 요청")
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다")

    logger.info(f"질문: {q.question}")

    try:
        answer = _state["chain"].invoke(q.question)
        docs = _state["retriever"].invoke(q.question)

        from pathlib import Path as P
        sources = sorted({P(d.metadata.get("source", "")).name for d in docs})

        logger.info(f"답변: {answer}")
        logger.info(f"출처: {', '.join(sources)}")

        return Answer(answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"답변 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"답변 생성 실패: {e}")
하는 일 (순서대로):

1단계: 준비 상태 확인

RAG 체인이 아직 로드 안 됐으면 → 503 에러

"잠시 후 다시 시도하세요"

2단계: 빈 질문 검사

공백만 있으면 → 400 에러

"질문이 비어 있습니다"

3단계: 로그 기록

질문: 연차 휴가는 며칠인가요?

4단계: 답변 생성

chain.invoke() → RAG 파이프라인 실행

5~30초 소요

5단계: 출처 추출

검색된 문서들에서 파일명만 뽑기

sorted({...}) → 중복 제거 + 정렬

6단계: 로그 기록

답변: 15일

출처: company_policy.pdf

7단계: 응답 반환

json
{
  "answer": "15일",
  "sources": ["company_policy.pdf"]
}
8단계 (예외 시): 에러 처리

어떤 에러든 500 응답

로그에 상세 기록

비유: 창구 직원 업무 매뉴얼:

서버 준비됐나?

질문 비었나?

접수 (로그)

은행원에게 전달

결과 정리

접수 완료 (로그)

손님에게 전달

문제 시 에러 안내

📊 main.py의 4가지 핵심
기능	이유
전역 상태 (_state)	RAG 체인 한 번만 로드 → 빠름
RotatingFileHandler	로그 무한 증가 방지 (최대 20MB)
HTTPException	에러 시 적절한 상태 코드
try/except	어떤 에러든 500 응답 + 로그
🎯 main.py vs rag.py
항목	rag.py	main.py
역할	실제 RAG 처리	웹 API 감싸기
실행	직접 (python rag.py)	uvicorn으로 (uvicorn main:app)
인터페이스	터미널 input/output	HTTP (JSON)
사용자	개발자	브라우저, 앱
로그	print	logging (파일 + 콘솔)