
# 🔧 `rag.py` — 두뇌

## 📌 이 파일이 하는 일

> **"PDF를 잘게 쪼개서 저장해두고, 질문이 오면 관련 조각을 찾아서 AI에게 보여주고, AI가 답하게 한다."**

## 🍕 비유: 도서관 사서

- **PDF 로딩** = 책을 도서관에 들여놓기
- **청킹** = 책을 문단 단위로 잘라서 파일링
- **임베딩** = 각 문단에 "주제 태그" 붙이기
- **ChromaDB** = 태그별로 정리된 서랍장
- **검색** = 질문과 비슷한 태그를 가진 문단 꺼내기
- **답변** = 꺼낸 문단을 AI에게 보여주고 "이거 보고 답해" 시키기

---

## 🔍 코드 한 줄씩

### ① 모듈 docstring (파일 맨 위 설명)

```python
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
"""
하는 일:

파일의 정체를 설명

변경 이력을 시간순으로 기록

나중에 "왜 이렇게 했지?" 궁금할 때 답을 줌

비전공자용: 파일의 "이력서". 이 파일이 뭐 하는지, 언제 뭐가 바뀌었는지.

② 라이브러리 import
python
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
하는 일: 외부 도구들을 불러오기

라이브러리	역할
Path	파일 경로 다루기
PyPDFLoader	PDF를 텍스트로 읽기
RecursiveCharacterTextSplitter	긴 글을 잘게 자르기
ChatOllama	Ollama의 AI와 대화
OllamaEmbeddings	Ollama로 문장→숫자 변환
Chroma	벡터 DB 접속
ChatPromptTemplate	AI에게 보낼 프롬프트 양식
StrOutputParser	AI 답변을 문자열로 변환
RunnablePassthrough	데이터를 그대로 통과시키기
RunnableLambda	함수를 체인에 연결
비전공자용: 요리하기 전에 재료와 도구를 꺼내는 것.

③ 설정값
python
DATA_DIR = "data"
CHROMA_DIR = "chroma_db"
LLM_MODEL = "hf.co/mradermacher/kanana-2-3b-instruct-GGUF:Q4_K_M"
EMBED_MODEL = "bge-m3"

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
RETRIEVER_K = 3
하는 일: 프로그램 전체에서 쓸 고정값 정의

항목	의미
DATA_DIR	PDF가 있는 폴더
CHROMA_DIR	벡터 저장 폴더
LLM_MODEL	답변하는 AI 모델
EMBED_MODEL	임베딩 AI 모델
CHUNK_SIZE	문단 자르는 크기 (400자)
CHUNK_OVERLAP	문단끼리 겹치는 글자 수 (80자)
RETRIEVER_K	질문당 꺼낼 문단 개수 (3개)
비전공자용: 요리 레시피의 분량. "소금 3g, 물 400ml" 같은 것.

왜 여기 모아뒀나? 나중에 값을 바꾸고 싶으면 이 한 곳만 고치면 됨.

④ 후처리용 상수 (영어 거부 표현)
python
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
하는 일:

AI가 영어로 도망가는 표현들 목록

그런 표현이 나오면 한국어로 강제 변환

왜 필요?

Kanana 3B가 가끔 "None of the above" 같은 영어로 답함

프롬프트로 100% 막을 수 없어서 후처리로 잡음

비전공자용: AI가 규칙을 어기고 영어로 답하면, 자동으로 한국어로 바꿔주는 장치.

⑤ PDF 로딩 함수
python
def load_pdfs(data_dir: str = DATA_DIR):
    """data/ 폴더의 모든 PDF를 읽어서 Document 리스트로 반환."""
    docs = []
    for pdf_path in Path(data_dir).glob("*.pdf"):
        print(f"[로딩] {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        docs.extend(loader.load())
    print(f"[완료] 총 {len(docs)}페이지 로딩")
    return docs
하는 일 (순서대로):

data/ 폴더에서 .pdf 파일을 다 찾음

각 PDF를 PyPDFLoader로 열어서 텍스트 추출

리스트(docs)에 담기

몇 페이지 로딩됐는지 출력

리스트 반환

비유: 도서관에 책 3권을 들여놓고 내용을 복사해두는 것.

glob("*.pdf"): "폴더 안의 모든 .pdf 파일" 찾기.

loader.load(): PDF 한 페이지당 Document 객체 1개 생성.

예시:

company_policy.pdf (1페이지) → Document 1개

product_manual.pdf (2페이지) → Document 2개

project_report.pdf (1페이지) → Document 1개

합계: 4개 Document

⑥ 청킹 함수 (자르기)
python
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
하는 일:

긴 텍스트를 400자씩 자름

80자는 겹치게 해서 문맥 유지

자른 조각들을 청크(chunk) 리스트로 반환

separators 의미 (자르는 우선순위):

"\n\n" — 빈 줄 (문단 경계) → 최우선

"\n" — 줄바꿈

". " — 마침표 + 공백 (문장 경계)

" " — 공백 (단어 경계)

"" — 글자 단위 → 최후 수단

비유:

원문: "연차 휴가는 입사 1년차에 15일이 부여됩니다. 3년 이상 근무 시 1일 추가됩니다."

400자씩 자르면 이 두 문장이 다른 조각으로 갈 수 있음

80자를 겹쳐서 "15일이 부여됩니다. 3년 이상..." 이렇게 이어지게 함

왜 400자?

처음엔 800자로 했는데 "연차 15일" 질문에 "8일"로 오답

400자로 줄이니 정확해짐

작은 조각 = 정확한 검색

⑦ 벡터 DB 구축 함수
python
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
하는 일:

bge-m3 임베딩 모델 준비

각 청크를 숫자 벡터로 변환 (768개 숫자)

chroma_db/ 폴더에 저장

Chroma 객체 반환

비유:

"연차 휴가 15일" → [0.12, -0.45, 0.78, ...] (768개 숫자)

"병가 10일" → [0.11, -0.43, 0.81, ...] (비슷한 숫자 = 비슷한 의미)

나중에 질문이 오면 숫자가 비슷한 문단을 찾음

왜 필요?

컴퓨터는 글자를 비교 못 함

숫자는 비교할 수 있음

그래서 모든 문장을 숫자로 바꿔서 저장

시간이 걸리는 이유: 청크 100개면 임베딩 100번. iGPU로 5~15분.

⑧ 벡터 DB 재사용 함수
python
def load_vectorstore(persist_dir: str = CHROMA_DIR):
    """이미 저장된 ChromaDB를 불러옴 (재임베딩 불필요)."""
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )
하는 일:

이전에 만들어둔 chroma_db/ 폴더를 그냥 불러오기

재임베딩 안 함 → 빠름 (몇 초)

비유: 도서관 서랍장이 이미 정리되어 있으면, 그대로 쓰기. 새로 정리 안 함.

언제 씀? 두 번째 실행부터.

⑨ 후처리 함수 (영어 → 한국어 강제 변환)
python
def postprocess(text: str) -> str:
    """영어 거부 표현을 한국어로 강제 변환."""
    lowered = text.lower().strip()
    for phrase in FALLBACK_PHRASES:
        if phrase in lowered:
            return FALLBACK_ANSWER
    if text.strip() and all(c.isascii() and not c.isdigit() for c in text.strip()):
        return FALLBACK_ANSWER
    return text
하는 일 (2가지 검사):

검사 1: 금지 표현 포함 여부

"None of the above", "I don't know" 등이 있으면 → "문서에서 찾을 수 없습니다"

검사 2: 답변이 전부 영어인지

한글이 하나도 없으면 → "문서에서 찾을 수 없습니다"

비유: AI가 영어로 도망가면 잡아채서 한국어로 바꿔주는 경비원.

text.lower(): 소문자로 변환 (대소문자 무시)
.strip(): 앞뒤 공백 제거
c.isascii(): 문자가 영어/숫자/기호인지 확인
c.isdigit(): 문자가 숫자인지 확인

⑩ 프롬프트 (AI에게 주는 지시서)
python
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

... (예시 6개)

이제 실제 질문에 답하세요.

[문서 내용]
{context}

[질문]
{question}

[답변]
""")
하는 일:

AI에게 "이렇게 답해라" 라고 알려주는 설명서

규칙 7개 + 예시 6개

{context}: 검색된 문서 조각들이 들어갈 자리

{question}: 사용자 질문이 들어갈 자리

프롬프트의 진화 (핵심!):

버전	내용	결과
v1	규칙 4개	❌ "연차 15일" → "11일"
v2	규칙 6개 (숫자 강조)	❌ 여전히 "8일"
v3	예시 5개 추가	✅ "15일" 정답!
핵심 발견:

작은 AI(3B)는 "규칙"보다 "예시"를 잘 따라한다.

비유:

규칙만 주면: "숫자는 그대로 써" → AI가 무시

예시를 주면: "15일 → 15일" → AI가 따라함

⑪ RAG 체인 함수
python
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
하는 일 (체인 구성):

1단계: LLM 준비

python
llm = ChatOllama(model=LLM_MODEL, temperature=0.0)
temperature=0.0: 완전 결정론적 (창의성 0)

같은 질문 → 같은 답변

2단계: 검색기 준비

python
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
k=3: 질문당 문단 3개 꺼내기

3단계: 문서 포맷터

python
def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)
검색된 문단 3개를 하나의 문자열로 합침

4단계: 체인 연결 (파이프 | 연산자)

python
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | PROMPT
    | llm
    | StrOutputParser()
    | RunnableLambda(postprocess)
)
체인 흐름:

text
질문
  ↓
[retriever] → 관련 문단 3개 검색
  ↓
[format_docs] → 하나의 긴 텍스트로 합침
  ↓
[PROMPT] → 프롬프트 양식에 삽입
  ↓
[llm] → Kanana가 답변 생성
  ↓
[StrOutputParser] → 문자열로 변환
  ↓
[postprocess] → 영어 거부 표현 한국어로 변환
  ↓
최종 답변
비유: 컨베이어 벨트. 각 단계가 순서대로 처리.

| (파이프) 연산자: "앞 단계 결과를 다음 단계로 넘긴다"

⑫ 초기화 함수 (구축 or 재사용)
python
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
하는 일 (분기):

경우 1: rebuild=True 또는 chroma_db/ 없음

PDF 다시 읽기 → 청킹 → 임베딩 → 저장

최초 1회 또는 재구축 시

경우 2: chroma_db/ 있음

기존 벡터 DB 그대로 로드

빠름 (몇 초)

비유:

도서관 서랍장이 없으면 → 새로 정리

있으면 → 그대로 사용

사용:

powershell
python rag.py --rebuild   # 재구축
python rag.py             # 재사용
⑬ CLI 테스트 (파일 실행 시)
python
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
하는 일:

python rag.py 로 직접 실행 시 터미널에서 질문 가능

--rebuild 옵션 인식

exit 입력 시 종료

if __name__ == "__main__": 의미:

"이 파일을 직접 실행할 때만 아래 코드 작동"
(import rag 할 때는 작동 안 함)

비유: 이 파일이 혼자 실행될 때만 나오는 특별 모드.

📊 rag.py 핵심 요약
함수	역할	한 줄 요약
load_pdfs	PDF 읽기	책장에서 책 꺼내기
split_docs	문단 자르기	책을 문단별로 자르기
build_vectorstore	임베딩 + 저장	태그 붙여서 서랍장 정리
load_vectorstore	기존 DB 로드	정리된 서랍장 그대로 쓰기
postprocess	후처리	영어 도망 방지
build_rag_chain	체인 구성	검색 → 답변 파이프라인
init_rag	초기화	상황별 구축/재사용 결정
🎯 rag.py의 3가지 핵심
작은 조각(400자)으로 자른다 → 정확한 검색

예시(few-shot)를 준다 → 3B 모델도 정확

후처리로 잡는다 → 영어 도망 방지