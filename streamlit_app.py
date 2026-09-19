"""
streamlit_app.py — 회사 문서 AI 챗봇의 Streamlit 프론트엔드
ponytail: 채팅 + 출처 + 서버 상태 + 문서 관리. 그 이상은 필요해지면 추가.

변경 이력:
- 최초 작성: 채팅 UI, 출처 표시, 대화 기록 유지
- 한국어화: CSS로 영어 UI 요소 숨김, 사이드바 한국어화
- 사이드바 토글 문제 해결: 사이드바 항상 열림
- 사이드바 강화: 서버 상태, 문서 목록, 앱 정보 추가
- 문서 관리: 업로드, 삭제, 재인덱싱 UI 추가
- 문서 목록 가독성 개선: 한 줄 표시 + 컬럼 비율 조정
"""

import streamlit as st
import requests

# ===== 설정 =====
API_URL = "http://localhost:8000"
APP_VERSION = "0.2.1"

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
    /* 사이드바 문서 목록 컴팩트 */
    [data-testid="stSidebar"] .stButton button {
        padding: 0.15rem 0.4rem;
        font-size: 0.85rem;
        min-height: 1.6rem;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        margin-bottom: 0.2rem;
        font-size: 0.88rem;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0;
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
                if res.status_code == 503:
                    answer = "재인덱싱 중입니다. 잠시 후 다시 시도하세요."
                    sources = []
                else:
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
    reindexing = False
    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        reindexing = health.get("reindexing", False)
        if reindexing:
            st.warning("🔄 재인덱싱 중...")
        elif health.get("ready"):
            st.success("✅ 정상 동작 중")
        else:
            st.warning("⏳ 로딩 중...")
    except Exception:
        st.error("❌ 서버 연결 실패")

    st.markdown("---")

    # --- 문서 관리 ---
    st.subheader("📚 문서 관리")

    # 업로드
    uploaded = st.file_uploader(
        "PDF 업로드",
        type=["pdf"],
        key="uploader",
        disabled=reindexing,
    )
    if uploaded is not None:
        if st.button("📤 업로드", use_container_width=True, disabled=reindexing):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                res = requests.post(f"{API_URL}/upload", files=files, timeout=30)
                if res.status_code == 200:
                    st.success(f"✅ {uploaded.name} 업로드 완료")
                    st.info("⚠️ 재인덱싱 후 반영됩니다")
                else:
                    st.error(f"업로드 실패: {res.json().get('detail', '알 수 없는 오류')}")
            except Exception as e:
                st.error(f"업로드 오류: {e}")

    st.markdown("**등록된 문서:**")

    # 문서 목록 (한 줄 표시)
    try:
        docs = requests.get(f"{API_URL}/documents", timeout=5).json()
        if docs:
            for doc in docs:
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.caption(f"📄 {doc['name']} · {doc['size_mb']} MB")
                with col2:
                    if st.button("🗑️", key=f"del_{doc['name']}", disabled=reindexing):
                        try:
                            res = requests.delete(
                                f"{API_URL}/documents/{doc['name']}",
                                timeout=10,
                            )
                            if res.status_code == 200:
                                st.success(f"삭제: {doc['name']}")
                                st.info("⚠️ 재인덱싱 후 반영됩니다")
                                st.rerun()
                            else:
                                st.error(res.json().get("detail", "삭제 실패"))
                        except Exception as e:
                            st.error(f"삭제 오류: {e}")
        else:
            st.caption("문서 없음")
    except Exception:
        st.caption("문서 목록 로드 실패")

    st.markdown("---")

    # --- 재인덱싱 ---
    st.subheader("🔄 재인덱싱")
    st.caption("문서 변경 후 실행 (5~15분)")
    if st.button(
        "재인덱싱 시작",
        use_container_width=True,
        disabled=reindexing,
        type="primary",
    ):
        try:
            with st.spinner("재인덱싱 중... (브라우저 닫지 마세요)"):
                res = requests.post(f"{API_URL}/reindex", timeout=1800)
                if res.status_code == 200:
                    st.success("✅ 재인덱싱 완료")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "재인덱싱 실패"))
        except requests.exceptions.Timeout:
            st.error("재인덱싱 시간 초과 (30분)")
        except Exception as e:
            st.error(f"재인덱싱 오류: {e}")

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