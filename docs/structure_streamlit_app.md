---

# 🎨 `streamlit_app.py` — 얼굴 (프론트엔드)

## 📌 이 파일이 하는 일

> **"터미널(검은 화면)에서만 되던 질문을, 브라우저 예쁜 채팅 화면으로 바꿔주는 파일"**

## 🍕 비유: 은행 창구에 의자 놓기

- `rag.py` = 은행원 (실무)
- `main.py` = 창구 직원 (접수)
- **`streamlit_app.py`** = **대기 의자 + 안내판** (손님이 앉고 보는 곳)

은행원과 창구는 이미 있었지만, **손님이 앉을 자리**가 없었습니다. 그게 바로 이 파일.

---

## 🔍 코드 한 줄씩

### ① 모듈 docstring

```python
"""
streamlit_app.py — 회사 문서 AI 챗봇의 Streamlit 프론트엔드
ponytail: 채팅 + 출처 + 서버 상태 + 문서 목록. 그 이상은 필요해지면 추가.

변경 이력:
- 최초 작성: 채팅 UI, 출처 표시, 대화 기록 유지
- 한국어화: CSS로 영어 UI 요소 숨김, 사이드바 한국어화
- 사이드바 토글 문제 해결: 사이드바 항상 열림
- 사이드바 강화: 서버 상태, 문서 목록, 앱 정보 추가
"""
하는 일: 파일 정체와 변경 이력.

② 라이브러리 import
python
import streamlit as st
import requests
from pathlib import Path
라이브러리	역할
streamlit	웹 화면 만들기
requests	main.py에 HTTP 요청 보내기
Path	파일 경로 다루기 (문서 목록)
비유:

streamlit = "예쁜 웹페이지를 만드는 붓"

requests = "다른 서버에 전화 거는 전화기"

Path = "파일 탐색기"

③ 설정
python
API_URL = "http://localhost:8000"
DATA_DIR = "data"
APP_VERSION = "0.1.0"

st.set_page_config(
    page_title="회사 문서 AI 챗봇",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)
하는 일:

항목	의미
API_URL	백엔드 주소 (main.py가 8000번 포트)
DATA_DIR	PDF 폴더
APP_VERSION	버전
page_title	브라우저 탭 제목
page_icon	탭 아이콘 (📄)
layout	화면 폭 ("centered" = 가운데)
initial_sidebar_state	사이드바 항상 열림
결과: 브라우저 탭에 📄 회사 문서 AI 챗봇 뜸.

④ CSS 주입 (영어 UI 숨기기)
python
st.markdown("""
<style>
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
</style>
""", unsafe_allow_html=True)
하는 일:

Streamlit 기본 UI의 영어 요소 숨기기

footer = "Made with Streamlit" 문구

#MainMenu = 우측 상단 ⋮ 메뉴

한글 폰트 지정 (맑은 고딕)

unsafe_allow_html=True: HTML/CSS를 그대로 실행하라는 옵션.

비유: Streamlit이 자동으로 붙이는 "광고판"을 떼어내기.

⑤ 화면 제목
python
st.title("📄 회사 문서 AI 챗봇")
st.caption("PDF 문서를 기반으로 답변합니다. 문서에 없는 내용은 답하지 않습니다.")
하는 일:

title = 큰 제목

caption = 작은 설명

⑥ 대화 기록 초기화
python
if "messages" not in st.session_state:
    st.session_state.messages = []
하는 일:

대화 기록을 담을 빈 리스트 생성

session_state = 이 사용자만의 임시 저장소

왜 필요?

Streamlit은 새로고침할 때마다 코드를 처음부터 다시 실행함

session_state에 저장 안 하면 이전 대화가 다 날아감

비유: 손님이 은행에 오면 "이 손님의 상담 기록 카드" 를 새로 만듦.

⑦ 기존 대화 화면 표시
python
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            st.caption(f"출처: {', '.join(msg['sources'])}")
하는 일:

저장된 대화를 하나씩 꺼내서 화면에 그림

role = "user" 또는 "assistant"

user = 오른쪽 말풍선 (🧑)

assistant = 왼쪽 말풍선 (🤖)

출처 표시 (있으면)

결과:

text
🧑 연차 휴가는 며칠인가요?
🤖 15일
   출처: company_policy.pdf
비유: 지금까지의 상담 기록을 카드에서 읽어서 칠판에 붙이는 것.

⑧ 사용자 입력 받기 (핵심!)
python
if prompt := st.chat_input("질문을 입력하세요"):
하는 일:

화면 아래 입력창을 만듦

사용자가 뭔가 입력하고 Enter 누르면 → prompt에 저장

아무것도 안 넣으면 이 블록 실행 안 됨

:= (왈러스 연산자):

"값을 받으면서 동시에 그 값이 있는지 검사"

비전공자용: "입력이 있으면 아래를 실행해라"

비유: 손님이 창구에 "질문 카드" 를 냄. 카드를 안 내면 아무 일도 안 일어남.

⑨ 사용자 메시지 화면에 표시
python
st.session_state.messages.append({"role": "user", "content": prompt})
with st.chat_message("user"):
    st.write(prompt)
하는 일:

대화 기록에 추가 (새로고침해도 남게)

화면에 즉시 표시

비유:

손님이 질문 카드를 냄

① 기록 카드에 적기 (나중을 위해)

② 칠판에 붙이기 (즉시 보이게)

왜 둘 다?

화면 표시만 하면 → 새로고침 시 사라짐

기록만 하면 → 화면에 안 보임

둘 다 해야 함

⑩ 백엔드에 질문 보내기 (핵심!)
python
with st.chat_message("assistant"):
    with st.spinner("문서를 찾는 중..."):
        try:
            res = requests.post(
                f"{API_URL}/ask",
                json={"question": prompt},
                timeout=120,
            )
            res.raise_for_status()
            data = res.json()
            answer = data.get("answer", "오류: 답변이 없습니다")
            sources = data.get("sources", [])
하는 일 (순서대로):

1단계: 🤖 말풍선 준비 (st.chat_message("assistant"))

2단계: "문서를 찾는 중..." 회전 로딩 (st.spinner)

3단계: main.py에 질문 전송 (requests.post)

주소: http://localhost:8000/ask

내용: {"question": "연차 휴가는 며칠인가요?"}

최대 대기: 120초

4단계: 응답 확인 (raise_for_status) — 에러면 예외 발생

5단계: JSON으로 변환 (res.json())

6단계: 답변/출처 추출 (data.get(...))

비유:

창구 직원이 은행원에게 질문 전달

"잠시만 기다려주세요" 안내

답이 오면 받아서 정리

timeout=120: AI가 답하는 데 오래 걸릴 수 있음. 120초까지 기다림 (iGPU는 30초~1분).

⑪ 에러 처리
python
except requests.exceptions.ConnectionError:
    answer = "오류: 백엔드 서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인하세요."
    sources = []
except requests.exceptions.Timeout:
    answer = "오류: 응답 시간이 초과되었습니다 (120초)."
    sources = []
except Exception as e:
    answer = f"오류: {e}"
    sources = []
하는 일: 3가지 상황 대응

상황	메시지
main.py가 꺼져있음	"백엔드 서버에 연결할 수 없습니다"
120초 넘김	"응답 시간이 초과되었습니다"
기타 오류	오류 내용 표시
비유: 은행원이 자리에 없거나, 너무 오래 걸리거나, 뭔가 터졌을 때 손님에게 친절히 안내.

왜 필요?

없으면 프로그램이 빨간 에러 화면으로 죽음

있으면 친절한 메시지가 나옴

⑫ 답변 화면에 표시
python
st.write(answer)
if sources:
    st.caption(f"출처: {', '.join(sources)}")
하는 일:

답변을 🤖 말풍선에 표시

출처가 있으면 작은 글씨로 표시

결과:

text
🤖 15일
   출처: company_policy.pdf, project_report.pdf
⑬ 대화 기록에 답변 저장
python
st.session_state.messages.append({
    "role": "assistant",
    "content": answer,
    "sources": sources,
})
하는 일:

🤖 답변도 기록 카드에 저장

이제 새로고침해도 대화가 남아있음

⑭ 사이드바
python
with st.sidebar:
    st.header("⚙️ 설정")
    st.markdown("---")

    # --- 서버 상태 ---
    st.subheader("🖥️ 서버 상태")
    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        if health.get("ready"):
            st.success("✅ 정상 동작 중")
        else:
            st.warning("⏳ 로딩 중...")
    except Exception:
        st.error("❌ 서버 연결 실패")
    st.caption(f"주소: {API_URL}")

    st.markdown("---")

    # --- 문서 목록 ---
    st.subheader("📚 등록된 문서")
    if Path(DATA_DIR).exists():
        pdfs = list(Path(DATA_DIR).glob("*.pdf"))
        if pdfs:
            for pdf in pdfs:
                size_mb = pdf.stat().st_size / (1024 * 1024)
                st.caption(f"📄 {pdf.name} ({size_mb:.1f} MB)")
        else:
            st.caption("문서 없음")
    else:
        st.caption("data/ 폴더 없음")

    st.markdown("---")

    # --- 대화 ---
    st.subheader("💬 대화")
    msg_count = len(st.session_state.messages) // 2
    st.caption(f"현재 {msg_count}개 질문")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # --- 앱 정보 ---
    st.subheader("ℹ️ 앱 정보")
    st.caption(f"버전: v{APP_VERSION}")
    st.caption("모델: Kanana-2-3B-Instruct")
    st.caption("임베딩: bge-m3")
    st.caption("벡터DB: ChromaDB")
하는 일 (사이드바 구성):

1. 서버 상태

/health 요청으로 서버 살아있는지 확인

정상: ✅ 초록색

로딩 중: ⏳ 노란색

실패: ❌ 빨간색

2. 문서 목록

data/ 폴더의 PDF 나열

파일 크기 표시

3. 대화

현재 질문 개수 표시 (메시지 ÷ 2)

대화 초기화 버튼

4. 앱 정보

버전, 모델, 임베딩, DB

비유: 은행 안내판. 손님이 필요한 정보를 한눈에 봄.

use_container_width=True: 버튼을 사이드바 폭에 꽉 채움.

st.rerun(): 화면 즉시 새로고침.

📊 streamlit_app.py의 3가지 핵심
기능	이유
session_state	새로고침해도 대화 유지
st.chat_input	사용자 입력 유일한 통로
try/except	에러 나도 안 죽고 친절 안내
🎯 3개 파일 비교
파일	역할	비유
rag.py	문서 검색 + 답변 생성	은행원
main.py	API 창구	창구 직원
streamlit_app.py	사용자 화면	대기 의자 + 안내판
세 개가 다 있어야 완성:

rag.py만 있으면 → 터미널에서만 됨

main.py만 있으면 → 프로그램에서만 됨

셋 다 있어야 → 누구나 브라우저로 씀 ✅

🎯 전체 흐름도
text
[사용자]
   ↓ 질문 입력
[streamlit_app.py]
   ↓ requests.post
[main.py (8000)]
   ↓ chain.invoke
[rag.py]
   ↓ ① ChromaDB 검색
   ↓ ② Kanana 답변
[답변 + 출처]
   ↑ JSON
[main.py]
   ↑ HTTP 응답
[streamlit_app.py]
   ↓ 화면 표시 + 기록 저장
[사용자]