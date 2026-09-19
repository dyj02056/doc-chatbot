"""
main.py — 회사 문서 AI 챗봇의 FastAPI 백엔드
ponytail: rag.py를 그대로 감싸는 최소 API.

변경 이력:
- 최초 작성: /ask, /health
- 로깅 추가
- 문서 관리: /upload, /documents, /reindex, DELETE
- 재인덱싱 상태 관리 + 실패 시 명확한 안내 (대안 C)
"""

import gc
import logging
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag import (
    init_rag, rebuild_index, delete_document, list_documents, DATA_DIR
)

# ===== 로깅 =====
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("doc_chatbot")
logger.setLevel(logging.INFO)

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

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)


# ===== 전역 상태 =====
_state = {"chain": None, "retriever": None, "reindexing": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG 체인 로드 중...")
    chain, retriever = init_rag(rebuild=False)
    _state["chain"] = chain
    _state["retriever"] = retriever
    logger.info("준비 완료")
    yield
    logger.info("서버 종료")


app = FastAPI(title="Doc Chatbot API", lifespan=lifespan)


# ===== 모델 =====
class Query(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str]


class Document(BaseModel):
    name: str
    size_mb: float


# ===== 엔드포인트 =====
@app.get("/health")
def health():
    ready = _state["chain"] is not None
    return {
        "status": "ok" if ready else "loading",
        "ready": ready,
        "reindexing": _state["reindexing"],
    }


@app.post("/ask", response_model=Answer)
def ask(q: Query):
    if _state["reindexing"]:
        raise HTTPException(
            status_code=503,
            detail="재인덱싱 중입니다. 잠시 후 다시 시도하세요",
        )

    if _state["chain"] is None:
        logger.warning("RAG 체인 미준비 상태에서 요청")
        raise HTTPException(status_code=503, detail="RAG 체인 로드 중입니다")

    if not q.question.strip():
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다")

    logger.info(f"질문: {q.question}")

    try:
        answer = _state["chain"].invoke(q.question)
        docs = _state["retriever"].invoke(q.question)
        sources = sorted({Path(d.metadata.get("source", "")).name for d in docs})

        logger.info(f"답변: {answer}")
        logger.info(f"출처: {', '.join(sources)}")

        return Answer(answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"답변 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"답변 생성 실패: {e}")


@app.get("/documents", response_model=list[Document])
def get_documents():
    return list_documents()


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

    dest = Path(DATA_DIR) / file.filename
    dest.parent.mkdir(exist_ok=True)

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info(f"업로드: {file.filename}")
    return {
        "status": "ok",
        "filename": file.filename,
        "message": "재인덱싱이 필요합니다",
    }


@app.delete("/documents/{filename}")
def delete_document_endpoint(filename: str):
    try:
        delete_document(filename)
        logger.info(f"삭제: {filename}")
        return {
            "status": "ok",
            "filename": filename,
            "message": "재인덱싱이 필요합니다",
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reindex")
def reindex():
    """
    전체 재인덱싱.
    대안 A (폴더 이름 변경) 사용.
    실패 시 대안 C (CLI 재인덱싱) 안내 메시지 반환.
    """
    if _state["reindexing"]:
        raise HTTPException(status_code=409, detail="이미 재인덱싱 중입니다")

    _state["reindexing"] = True
    logger.info("재인덱싱 시작")

    try:
        # ★ 핵심: 기존 체인 참조 해제
        _state["chain"] = None
        _state["retriever"] = None
        gc.collect()

        # 재구축 (대안 A: 이름 변경 방식)
        chain, retriever = rebuild_index()
        _state["chain"] = chain
        _state["retriever"] = retriever
        logger.info("재인덱싱 완료")
        return {"status": "ok", "message": "재인덱싱 완료"}

    except RuntimeError as e:
        # 대안 A 실패 → 대안 C 안내
        logger.error(f"재인덱싱 실패 (파일 잠금): {e}")

        # 재로드 시도
        try:
            chain, retriever = init_rag(rebuild=False)
            _state["chain"] = chain
            _state["retriever"] = retriever
        except Exception as reload_err:
            logger.error(f"재로드도 실패: {reload_err}", exc_info=True)

        raise HTTPException(
            status_code=409,
            detail=(
                "재인덱싱 실패: chroma_db 폴더가 잠겨 있습니다. "
                "터미널에서 다음을 실행하세요:\n"
                "1. uvicorn 종료 (Ctrl+C)\n"
                "2. Remove-Item -Recurse -Force chroma_db\n"
                "3. python rag.py --rebuild\n"
                "4. uvicorn 재시작 (uvicorn main:app --reload --port 8000)\n"
                "5. 브라우저 새로고침"
            ),
        )

    except Exception as e:
        logger.error(f"재인덱싱 실패: {e}", exc_info=True)
        try:
            chain, retriever = init_rag(rebuild=False)
            _state["chain"] = chain
            _state["retriever"] = retriever
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"재인덱싱 실패: {e}")

    finally:
        _state["reindexing"] = False