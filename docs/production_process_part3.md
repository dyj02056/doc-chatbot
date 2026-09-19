---

## 🌐 Step 5: FastAPI 백엔드

### Step 5-1: 목표

CLI(터미널)에서만 되던 RAG를 **웹 API**로 변환.

**ponytail 판정:** `/ask`와 `/health` 두 엔드포인트만. `/upload`는 필요해지면 추가.

### Step 5-2: `main.py` 구조

**핵심 개념:**

| 요소 | 역할 |
|---|---|
| `lifespan` | 서버 시작 시 RAG 체인 한 번만 로드 |
| `_state` | 로드된 체인을 전역 보관 |
| `Query` / `Answer` | 요청/응답 형식 (Pydantic) |
| `/health` | 서버 상태 확인 |
| `/ask` | 질문 → 답변 |

### Step 5-3: RAG 체인을 전역에 저장하는 이유

**문제:** 매 요청마다 `init_rag()` 호출하면?
- ChromaDB 로드 + 임베딩 = 5~15초
- 10명이 동시에 쓰면 10번 로드

**해결:** 서버 시작 시 **한 번만** 로드.

```python
_state = {"chain": None, "retriever": None}

@asynccontextmanager
async def lifespan(app):
    chain, retriever = init_rag(rebuild=False)
    _state["chain"] = chain
    _state["retriever"] = retriever
    yield
비유: 은행 문 열 때 금고 잠금 해제. 손님마다 다시 안 함.

Step 5-4: 테스트 결과
실행:

powershell
uvicorn main:app --reload --port 8000
Swagger UI에서 /ask 테스트:

요청:

json
{"question": "연차 휴가는 며칠인가요?"}
응답:

json
{
  "answer": "15일",
  "sources": ["company_policy.pdf", "project_report.pdf"]
}
성공!

Step 5-5: 예상 못 한 로그
터미널에 뜬 것:

text
INFO: 127.0.0.1:50752 - "GET /favicon.ico HTTP/1.1" 404 Not Found
분석: 브라우저가 탭 아이콘을 요청. FastAPI는 기본 파비콘 없음 → 404.

결론: 에러 아님. 정상 동작.

교훈:

"404가 다 에러는 아니다."
/favicon.ico 404는 무시.

🎨 Step 6: Streamlit 프론트엔드
Step 6-1: 목표
웹 API를 채팅 화면으로 감싸기.

ponytail 판정: 채팅 + 답변 + 출처만. 업로드/설정은 나중.

Step 6-2: streamlit_app.py 구조
핵심 개념:

요소	역할
session_state	새로고침해도 대화 유지
st.chat_input	사용자 입력창
st.chat_message	말풍선
requests.post	main.py에 질문 전달
try/except	에러 대응
Step 6-3: 첫 실행 (Streamlit 첫인사)
터미널에 뜬 것:

text
Welcome to Streamlit!
Email:
분석: 첫 실행 시 이메일 입력 요청. 그냥 Enter.

Step 6-4: 첫 테스트 결과
5개 질문 결과:

#	질문	답변	판정
1	연차 휴가	15일	✅
2	병가	10일	✅
3	식대	3만원	✅
4	허브 연결	Wi-Fi 비밀번호	✅
5	작년 매출	"None of the above"	❌
문제: CLI에서는 "찾을 수 없습니다"가 나왔는데 Streamlit에서는 영어로 도망.

원인: Kanana 3B의 확률적 변동. 같은 프롬프트라도 매번 답이 조금씩 다름.

Step 6-5: 후처리 추가
해결: rag.py에 postprocess 함수 추가.

python
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | PROMPT
    | llm
    | StrOutputParser()
    | RunnableLambda(postprocess)  # ← 추가
)
결과: 5/5 정답!

Step 6-6: UI 한국어화
문제: Streamlit 기본 UI가 영어 ("Deploy", "Made with Streamlit", "Rerun").

해결 1: .streamlit/config.toml 설정 파일.

toml
[client]
toolbarMode = "minimal"
showErrorDetails = false

[browser]
gatherUsageStats = false
해결 2: streamlit_app.py에 CSS 주입.

python
st.markdown("""
<style>
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
Step 6-7: 사이드바 문제
문제 1: 사이드바 토글이 흰 배경에서 안 보임.

원인: config.toml에서 [ui] hideTopBar = true 설정이 사이드바 토글까지 숨김.

해결: [ui] 섹션 삭제, initial_sidebar_state="expanded" (항상 열림).

문제 2: 다크모드 지정 안 됨.

원인: [theme] base = "light" → 라이트 모드 강제.

해결: [theme] 섹션 전체 삭제 → OS 설정 자동 감지.

결과: 사용자 스크린샷에서 다크모드 + 사이드바 정상 표시 확인.

Step 6-8: 사이드바 강화
추가:

서버 상태 (/health 요청)

등록된 문서 목록 (data/ 폴더 스캔)

앱 정보 (버전, 모델, 임베딩)

결과: 사이드바가 알찬 대시보드로 변신.

Step 6-9: 미래 기능 요청 (3일차로 연기)
사용자 요청:

채팅 기록 목록 (사이드바에)

이름 변경 / 삭제

프로젝트 (관련 채팅 묶기)

프로젝트 설명