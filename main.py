"""
main.py — 회사 문서 AI 챗봇의 FastAPI 백엔드
ponytail: rag.py를 그대로 감싸는 최소 API. /ask와 /health만.
업로드 기능은 필요해지면 추가.

변경 이력:
- 최초 작성: /ask, /health 두 엔드포인트
- 로깅 추가: logs/app.log에 질문/답변/에러 기록
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag import init_rag

# ===== 로깅 설정 =====
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("doc_chatbot")
logger.setLevel(logging.INFO)

# 파일 핸들러 (최대 5MB, 3개 백업)
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

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)


# ===== 전역 상태 =====
_state = {"chain": None, "retriever": None}


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


app = FastAPI(title="Doc Chatbot API", lifespan=lifespan)


# ===== 요청/응답 모델 =====
class Query(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str]


# ===== 엔드포인트 =====
@app.get("/health")
def health():
    """서버 상태 확인."""
    ready = _state["chain"] is not None
    return {"status": "ok" if ready else "loading", "ready": ready}


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