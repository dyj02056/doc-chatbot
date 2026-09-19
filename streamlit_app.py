"""
streamlit_app.py — 회사 문서 AI 챗봇의 Streamlit 프론트엔드
ponytail: 채팅 + 출처 + 서버 상태 + 문서 목록. 그 이상은 필요해지면 추가.

변경 이력:
- 최초 작성: 채팅 UI, 출처 표시, 대화 기록 유지
- 한국어화: CSS로 영어 UI 요소 숨김, 사이드바 한국어화
- 사이드바 토글 문제 해결: 사이드바 항상 열림
- 사이드바 강화: 서버 상태, 문서 목록, 앱 정보 추가
"""

import streamlit as st
import requests
from pathlib import Path

# ===== 설정 =====
API_URL = "http://localhost:8000"
DATA_DIR = "data"
APP_VERSION = "0.1.0"

st.set_page_config(
    page_title="회사 문서 AI 챗봇",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ===== CSS =====
st.markdown("""
<style>
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 회사 문서 AI 챗봇")
st.caption("PDF 문서를 기반으로 답변합니다. 문서에 없는 내용은 답하지 않습니다.")

# ===== 대화 기록 초기화 =====
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===== 기존 대화 표시 =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            st.caption(f"출처: {', '.join(msg['sources'])}")

# ===== 입력창 =====
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

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
            except requests.exceptions.ConnectionError:
                answer = "오류: 백엔드 서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인하세요."
                sources = []
            except requests.exceptions.Timeout:
                answer = "오류: 응답 시간이 초과되었습니다 (120초)."
                sources = []
            except Exception as e:
                answer = f"오류: {e}"
                sources = []

        st.write(answer)
        if sources:
            st.caption(f"출처: {', '.join(sources)}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })

# ===== 사이드바 =====
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