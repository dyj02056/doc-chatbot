# 📝 프로젝트 제작 과정 기록

> 2026-09-19, 처음부터 끝까지의 모든 과정을 시간순으로 기록.

---

## 📌 프로젝트 개요

### 최종 목표
> **"회사 문서를 올리면, 내 컴퓨터에서 AI가 답해주는 웹 서비스"**
> API 비용 0원, 문서 유출 0%, 인터넷 없이도 작동

### 시작 시점의 계획
- **원래 계획**: 3개월 (초심자 기준)
- **실제 진행**: **1일** (LLM과 함께 코딩)
- **이유**: LLM이 코드 작성 + 에러 진단 + 수정을 즉시 처리

### 최종 산출물
| 항목 | 결과 |
|---|---|
| 소요 시간 | 약 6~8시간 |
| 코드 파일 | 3개 (`rag.py`, `main.py`, `streamlit_app.py`) |
| 스크립트 | 2개 (`run.ps1`, `backup.ps1`) |
| 문서 | 4개 (README, structure, process, incident_playbook) |
| 최종 테스트 | **5/5 정답** |

---

## 🔥 사전 검증 (grill-me)

프로젝트 시작 **전에** "이 계획 진짜 가능한가?" 캐물음.

### 초기 가정 (수정 전)
- 3개월 계획
- "회사에 배포 가능한 완성품"
- Docker + 인증 포함

### grill-me가 지적한 문제
1. **"2일 안에 완성품"** → 불가능 (검증 시간 없음)
2. **"회사 문서"** → HWP/스캔 PDF 가능성
3. **"문서 유출 0%"** → 인증 없이? 보안 검토는?

### 재정의된 목표 (확정)
> **"내 PC에서 돌아가는 데모 가능한 프로토타입. PDF 올리고 한국어 질문하면 출처와 함께 답변."**

| 항목 | 결정 |
|---|---|
| 배포 형태 | A (내 노트북 + 동료 1명 옆에서 봄) |
| 운영 | 시뮬레이션 (로그/백업/장애) |
| 보안 | 시뮬레이션 (가상 보안 검토) |
| 사용자 | 본인 + 시뮬레이션 사용자 |

### 핵심 인사이트
> **"2일 안에 돌아가는 데모 = 가능 ✅"**
> **"2일 안에 회사 배포 가능한 완성품 = 불가능 ❌"**

**범위를 명확히 한 것이 성공의 시작.**

---

## ⚙️ Step 1: 환경 구축

### Step 1-0: 시스템 확인

| 항목 | 값 |
|---|---|
| OS | Windows |
| Python | 3.14 (초기) → **3.11로 다운그레이드** |
| Ollama | 이미 설치됨 |
| GPU | 내장 GPU (iGPU) |

### 🚨 문제 발견: Python 3.14

**원인:** Python 3.14는 너무 새 버전. LangChain, ChromaDB 등이 호환 안 됨.

**증거:**
- `pystemmer<3` 제약으로 llama-index BM25 설치 실패
- pandas 구버전 wheel 없음
- numcodecs import 에러

**해결:** Python 3.11로 다운그레이드.

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
교훈:

"최신 버전이 항상 좋은 게 아니다."
LLM과 함께하는 프로젝트는 안정 버전을 골라야 함.

Step 1-1: Ollama 모델 선택
초기 계획: llama3.2:3b

변경: kanana-2-3b-instruct

이유:

Kanana-2는 Kakao가 공개한 한국어 특화 모델

KoMT-Bench (한국어 벤치마크) 6.92점 vs Qwen3.5-2B 5.21

회사 문서가 한국어이므로 적합

다운로드:

powershell
ollama run hf.co/mradermacher/kanana-2-3b-instruct-GGUF:Q4_K_M
ollama pull bge-m3
Step 1-2: Python 패키지 설치
초기 계획: 9개 패키지

ponytail 판정: langchain-chroma는 스킵 → 결국 다 필요했음

powershell
pip install langchain langchain-community langchain-ollama langchain-text-splitters langchain-chroma chromadb fastapi uvicorn streamlit pypdf python-multipart requests
Step 1-3: 환경 테스트
test_connection.py로 Ollama + LangChain 연결 확인.

결과:

[LLM] 한국어 자기소개 정상

[EMB] 벡터 차원 768 정상

성공 기준 3가지 달성.

📦 Step 2: 패키지 설치 및 문제 해결
Step 2-1: import 에러
첫 실행 시 에러:

text
ModuleNotFoundError: No module named 'langchain.text_splitter'
원인: LangChain이 패키지 구조 개편. langchain.text_splitter deprecated.

해결:

python
# 변경 전
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 변경 후
from langchain_text_splitters import RecursiveCharacterTextSplitter
Step 2-2: Chroma import 에러
text
ModuleNotFoundError: No module named 'langchain_chroma'
원인: 별도 패키지로 분리됨.

해결:

powershell
pip install langchain-chroma
Step 2-3: 최종 패키지 버전 확정
txt
fastapi==0.141.1
uvicorn[standard]==0.53.0
python-multipart==0.0.32
streamlit==1.64.0
langchain==1.4.2
langchain-community==0.4.2
langchain-ollama==1.1.0
langchain-text-splitters==1.1.2
langchain-chroma==1.1.0
chromadb==1.5.9
pypdf==6.19.0
requests==2.34.2
핵심 인사이트
"패키지 import 에러는 90%가 이름 변경 때문."
LangChain처럼 빠르게 변하는 라이브러리는 공식 문서를 먼저 확인.

(다음 파트: Step 3 — RAG 파이프라인)

text

---

## ✅ 확인

`docs/production_process.md` 파일이 생성됐는지 확인:

```powershell
dir docs\production_process.md