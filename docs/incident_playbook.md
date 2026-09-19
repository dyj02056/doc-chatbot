@'
# 장애 대응 플레이북

## 개요

회사 문서 AI 챗봇 운영 중 발생할 수 있는 장애 시나리오와 대응 절차.

---

## 시나리오 1: 백엔드(uvicorn)가 죽었을 때

### 증상
- Streamlit에서 질문 시 "오류: 백엔드 서버에 연결할 수 없습니다" 표시
- 브라우저에서 http://localhost:8000 접속 불가

### 원인
- 터미널 1(uvicorn)이 종료됨
- 포트 충돌
- Python 프로세스 강제 종료

### 대응
1. 터미널 1 확인
2. 필요 시 재시작:
   ```powershell
   cd doc-chatbot
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload --port 8000


---

## 🧪 시나리오 1 테스트 (권장)

**실제로 uvicorn을 꺼보고 확인:**

1. 터미널 1에서 `Ctrl + C`
2. Streamlit에서 질문 입력
3. **"오류: 백엔드 서버에 연결할 수 없습니다"** 나오는지 확인
4. 터미널 1에서 uvicorn 재시작
5. Streamlit에서 다시 질문 → 정상 답변

**이 테스트로 "예외 처리가 실제로 작동하는지" 검증합니다.**

---

## 📋 Step 7-3 체크리스트

- [ ] `docs/incident_playbook.md` 생성
- [ ] `dir docs` 로 파일 확인
- [ ] (권장) uvicorn 종료 → Streamlit 반응 확인
- [ ] (권장) 재시작 → 정상 복구 확인

---

**문서 생성 + 시나리오 1 테스트 결과 알려주세요.** 그러면 Step 8 (마감)로 진행합니다.