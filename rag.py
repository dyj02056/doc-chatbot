"""
rag.py — 회사 문서 AI 챗봇의 핵심 RAG 파이프라인
ponytail: loader+splitter+embedder+vectorstore+rag를 파일 1개로 통합.
나중에 테스트가 필요해지면 그때 쪼갠다.

변경 이력:
- 임베딩 모델: nomic-embed-text → bge-m3 (한국어 검색 성능 향상)
- 청크 크기: 800 → 400 (한국어 문단 단위 검색 정확도 향상)
- retriever_k: 4 → 3 (노이즈 감소)
- 프롬프트: 규칙 번호 매김으로 3B 모델 지시 따르기 강화
- 프롬프트: 규칙 5, 6 추가 (숫자 원문 인용 강제, 근거 문장 인용)
- 프롬프트: few-shot 예시 5개 추가 (3B 모델의 숫자 처리 한계 우회)
- 프롬프트: 규칙 7 추가 (영어 답변 금지)
- 프롬프트: 예시 6번 추가 (문서 외 질문 대응)
- 후처리: 영어 거부 표현을 한국어로 강제 변환
- 문서 관리: rebuild_index(), delete_document() 함수 추가
"""

import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# ===== 설정 =====
DATA_DIR = "data"
CHROMA_DIR = "chroma_db"
LLM_MODEL = "hf.co/mradermacher/kanana-2-3b-instruct-GGUF:Q4_K_M"
EMBED_MODEL = "bge-m3"

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
RETRIEVER_K = 3

# 영어 거부 표현 → 한국어로 변환
FALLBACK_PHRASES = [
    "none of the above",
    "i don't know",
    "not found",
    "no information",
    "cannot find",
    "no relevant",
    "not mentioned",
    "not provided",
    "not available",
    "no answer",
]
FALLBACK_ANSWER = "문서에서 찾을 수 없습니다"


# ===== 1. PDF 로딩 =====
def load_pdfs(data_dir: str = DATA_DIR):
    """data/ 폴더의 모든 PDF를 읽어서 Document 리스트로 반환."""
    docs = []
    for pdf_path in Path(data_dir).glob("*.pdf"):
        print(f"[로딩] {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        docs.extend(loader.load())
    print(f"[완료] 총 {len(docs)}페이지 로딩")
    return docs


# ===== 2. 청킹 =====
def split_docs(docs):
    """긴 텍스트를 400자 단위로 자름. 80자는 겹치게 해서 문맥 유지."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"[청킹] {len(chunks)}개 청크 생성")
    return chunks


# ===== 3. 벡터 DB 구축 =====
def build_vectorstore(chunks, persist_dir: str = CHROMA_DIR):
    """청크를 임베딩해서 ChromaDB에 저장."""
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    print("[임베딩] 벡터 변환 중... (시간 걸림)")
    vs = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    print(f"[완료] ChromaDB 저장: {persist_dir}")
    return vs


def load_vectorstore(persist_dir: str = CHROMA_DIR):
    """이미 저장된 ChromaDB를 불러옴 (재임베딩 불필요)."""
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )


# ===== 4. 후처리 =====
def postprocess(text: str) -> str:
    """영어 거부 표현을 한국어로 강제 변환."""
    lowered = text.lower().strip()
    for phrase in FALLBACK_PHRASES:
        if phrase in lowered:
            return FALLBACK_ANSWER
    if text.strip() and all(c.isascii() and not c.isdigit() for c in text.strip()):
        return FALLBACK_ANSWER
    return text


# ===== 5. RAG 체인 =====
PROMPT = ChatPromptTemplate.from_template("""
당신은 회사 문서를 기반으로 답변하는 어시스턴트입니다.

규칙:
1. 아래 '문서 내용'에 있는 정보만 사용하세요.
2. 문서에 없는 내용은 절대 지어내지 마세요.
3. 답을 모르면 정확히 "문서에서 찾을 수 없습니다"라고만 답하세요.
4. 반드시 한국어로만 답하세요. 영어로 답하지 마세요.
5. 숫자는 문서에 적힌 그대로 인용하세요. 절대 계산하거나 바꾸지 마세요.
6. 답변 시 근거가 된 문장을 그대로 인용하세요.
7. "None of the above", "I don't know", "Not found" 같은 영어 표현을 쓰지 마세요.

아래 예시처럼 답하세요.

[예시 1]
문서 내용: "연차 휴가는 입사 1년차에 15일이 부여됩니다."
질문: 연차는 며칠인가요?
답변: 연차 휴가는 입사 1년차에 15일입니다.

[예시 2]
문서 내용: "식대는 1인당 1일 3만원까지 지원됩니다."
질문: 식대는 얼마인가요?
답변: 식대는 1인당 1일 3만원까지 지원됩니다.

[예시 3]
문서 내용: "병가는 연간 10일까지 사용 가능하며, 3일 초과 시 진단서가 필요합니다."
질문: 병가는 며칠까지 쓸 수 있나요?
답변: 병가는 연간 10일까지 사용 가능하며, 3일 초과 시 진단서가 필요합니다.

[예시 4]
문서 내용: "허브가 연결되지 않으면 Wi-Fi 비밀번호를 확인하세요."
질문: 허브가 연결되지 않으면 어떻게 하나요?
답변: 허브가 연결되지 않으면 Wi-Fi 비밀번호를 확인하세요.

[예시 5]
문서 내용: (관련 내용 없음)
질문: 작년 매출은 얼마인가요?
답변: 문서에서 찾을 수 없습니다.

[예시 6]
문서 내용: (관련 내용 없음)
질문: 오늘 날씨는 어떤가요?
답변: 문서에서 찾을 수 없습니다.

이제 실제 질문에 답하세요.

[문서 내용]
{context}

[질문]
{question}

[답변]
""")


def build_rag_chain(vectorstore):
    """검색 + 답변 생성 체인을 반환."""
    llm = ChatOllama(model=LLM_MODEL, temperature=0.0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
        | RunnableLambda(postprocess)
    )
    return chain, retriever


# ===== 6. 초기 구축 or 재사용 =====
def init_rag(rebuild: bool = False):
    """rebuild=True면 PDF 다시 읽어서 인덱싱, False면 기존 DB 재사용."""
    if rebuild or not Path(CHROMA_DIR).exists():
        docs = load_pdfs()
        chunks = split_docs(docs)
        vs = build_vectorstore(chunks)
    else:
        print(f"[재사용] 기존 ChromaDB 로드: {CHROMA_DIR}")
        vs = load_vectorstore()
    return build_rag_chain(vs)


# ===== 7. 문서 관리 (신규) =====
def rebuild_index():
    """ChromaDB를 삭제하고 전체 재구축. 재인덱싱 함수."""
    print("[재인덱싱] 시작")
    if Path(CHROMA_DIR).exists():
        shutil.rmtree(CHROMA_DIR)
        print(f"[재인덱싱] 기존 {CHROMA_DIR} 삭제")
    docs = load_pdfs()
    chunks = split_docs(docs)
    vs = build_vectorstore(chunks)
    print("[재인덱싱] 완료")
    return build_rag_chain(vs)


def delete_document(filename: str):
    """data/ 폴더에서 특정 PDF 파일 삭제. 실제 재인덱싱은 별도."""
    pdf_path = Path(DATA_DIR) / filename
    if not pdf_path.exists():
        raise FileNotFoundError(f"{filename} 파일이 없습니다")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("PDF 파일만 삭제 가능합니다")
    pdf_path.unlink()
    print(f"[삭제] {filename}")
    return True


def list_documents():
    """data/ 폴더의 PDF 목록 반환."""
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        return []
    pdfs = []
    for pdf in sorted(data_path.glob("*.pdf")):
        pdfs.append({
            "name": pdf.name,
            "size_mb": round(pdf.stat().st_size / (1024 * 1024), 2),
        })
    return pdfs


# ===== 8. CLI 테스트 =====
if __name__ == "__main__":
    import sys

    rebuild = "--rebuild" in sys.argv
    chain, retriever = init_rag(rebuild=rebuild)

    print("\n" + "=" * 50)
    print("질문을 입력하세요. 종료: exit")
    print("=" * 50 + "\n")

    while True:
        q = input("질문: ").strip()
        if q.lower() in ("exit", "quit", "종료"):
            print("종료합니다.")
            break
        if not q:
            continue

        answer = chain.invoke(q)
        sources = {d.metadata.get("source", "") for d in retriever.invoke(q)}

        print(f"\n답변: {answer}")
        print(f"출처: {', '.join(Path(s).name for s in sources)}")
        print("-" * 50 + "\n")