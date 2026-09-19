---

## 🔧 Step 3: RAG 파이프라인 구축

### Step 3-0: PDF 준비 (시행착오)

**목표:** 테스트용 PDF 3개 준비

**만든 PDF:**
| 파일명 | 성격 | 테스트 목적 |
|---|---|---|
| `company_policy.pdf` | 사실 정보 | 검색 정확도 |
| `product_manual.pdf` | 절차 설명 | 문맥 이해 |
| `project_report.pdf` | 서술/의견 | 요약 능력 |

### 🚨 문제 1: PDF 손상

**증상:**
pypdf.errors.PdfStreamError: Stream has ended unexpectedly

text

**진단:**
```powershell
Get-Content data\company_policy.pdf -Encoding Byte -TotalCount 4
결과: 237 154 140 236 (한글 텍스트 시작 바이트)

원인: 메모장은 PDF 저장 기능 없음. 확장자만 .pdf로 바꾼 텍스트 파일이었음.

해결: 크롬 브라우저 인쇄 → PDF로 저장 기능 사용.

교훈:

"파일 확장자만 바꾼다고 파일 형식이 바뀌지 않는다."
PDF인지 확인: 첫 4바이트가 %PDF (37 80 68 70).

Step 3-1: rag.py 초기 버전
ponytail 판정: 파일 6개(loader+splitter+embedder+vectorstore+rag+config) → 1개로 통합.

구조:

python
# 6가지 기능을 하나의 파일에
def load_pdfs()       # PDF 로딩
def split_docs()      # 청킹
def build_vectorstore()  # 임베딩 + 저장
def load_vectorstore()   # 재사용
def build_rag_chain()    # RAG 체인
def init_rag()           # 초기화
Step 3-2: 첫 실행 결과 (실패)
테스트 결과:

질문	정답	실제 답변	판정
연차 휴가	15일	11일	❌
허브 연결	Wi-Fi 비밀번호	"네트워크 관리자에게 연락..." (환각)	❌
작년 매출	찾을 수 없음	"찾을 수 없음"	✅
문제 진단:

"11일" — product_manual.pdf의 숫자(16도, 30도, 10%)와 섞임

환각 — 문서에 없는 내용을 지어냄

Step 3-3: 1차 개선 (bge-m3 + 청크 축소)
변경:

항목	이전	이후
임베딩	nomic-embed-text	bge-m3
청크 크기	800	400
오버랩	120	80
retriever_k	4	3
temperature	0.1	0.0
이유:

nomic-embed-text는 영어 중심 → 한국어 검색 부정확

청크 800자는 여러 문단 섞임 → 400자로 축소

결과 (2차 테스트):

질문	정답	실제 답변	판정
연차 휴가	15일	8일	❌
허브 연결	Wi-Fi 비밀번호	"Wi-Fi 비밀번호를 확인하세요"	✅
작년 매출	찾을 수 없음	"매출 정보 없음"	✅
개선: 검색 정확도 향상. 하지만 연차 문제 여전.

Step 3-4: 프롬프트 강화 (규칙 추가)
변경: 규칙 4개 → 6개. "숫자는 원문 그대로 인용" 명시.

결과: 여전히 "8일" ❌

분석:

검색은 정확했음 (company_policy.pdf에서 가져옴)

LLM이 숫자를 잘못 읽음 — Kanana 3B의 한계

Step 3-5: Few-shot 학습 (핵심 발견!)
변경: 프롬프트에 예시 5개 추가.

예시 구조:

text
[예시 1]
문서 내용: "연차 휴가는 입사 1년차에 15일이 부여됩니다."
질문: 연차는 며칠인가요?
답변: 연차 휴가는 입사 1년차에 15일입니다.
...
결과:

질문	정답	실제 답변	판정
연차 휴가	15일	15일	✅
병가	10일	10일	✅
식대	3만원	3만원	✅
허브 연결	Wi-Fi 비밀번호	Wi-Fi 비밀번호	✅
작년 매출	찾을 수 없음	찾을 수 없음	✅
5/5 정답!

🔑 핵심 발견
작은 AI(3B)는 "규칙"보다 "예시"를 잘 따라한다.

접근	결과
규칙만 (v1, v2)	❌ 실패
예시 추가 (v3)	✅ 성공
이유:

규칙은 추상적 → 3B가 해석 못 함

예시는 구체적 → 3B가 패턴 매칭

비전공자용:

"숫자는 그대로 써" (규칙) → AI가 무시

"15일 → 15일" (예시) → AI가 따라함

Step 3-6: 후처리 추가
문제: Streamlit에서 "작년 매출" 질문 시 "None of the above" (영어) 답변.

원인: Kanana 3B가 가끔 영어로 도망감.

해결: 후처리 함수 추가.

python
def postprocess(text: str) -> str:
    """영어 거부 표현을 한국어로 강제 변환."""
    FALLBACK_PHRASES = [
        "none of the above", "i don't know", "not found",
        # ... 총 10개
    ]
    for phrase in FALLBACK_PHRASES:
        if phrase in text.lower():
            return "문서에서 찾을 수 없습니다"
    return text
결과: 완벽.

Step 3 최종 상태
항목	값
임베딩	bge-m3
LLM	Kanana-2-3B-Instruct Q4_K_M
청크	400자 / 오버랩 80자
retriever_k	3
temperature	0.0
프롬프트	규칙 7개 + 예시 6개
후처리	영어 거부 표현 → 한국어
(다음 파트: Step 5~6 — FastAPI + Streamlit)

text

---

## ✅ 확인

`docs/production_process.md` **맨 끝에 이어붙이기** 완료하면 알려주세요.

다음은 **파트 3 (Step 5~6)** 입니다.