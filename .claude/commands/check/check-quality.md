# Code Quality Check

백엔드(Python)와 프론트엔드(TypeScript)의 코드 품질을 검사합니다.

---

## 검사 항목

### 1. Python 백엔드 검사

```bash
# 문법 오류 검사 (py_compile)
python -m py_compile app/main.py
python -m py_compile app/config.py
python -m py_compile app/services/claude_client.py
python -m py_compile app/services/orchestrator.py
python -m py_compile app/services/document_orchestrator.py

# 주요 스크립트 문법 검사
python -m py_compile app/scripts/prd_maker.py
python -m py_compile app/scripts/trd_maker.py
python -m py_compile app/scripts/wbs_maker.py
python -m py_compile app/scripts/pro_maker.py
python -m py_compile app/scripts/ppt_maker.py
python -m py_compile app/scripts/arch_diagram.py
python -m py_compile app/scripts/auto_doc.py
```

실패한 파일이 있으면 오류 내용과 수정 방안을 보고합니다.

### 2. Python import 검증

```bash
# 주요 의존성 import 가능 여부 확인
python -c "import fastapi; import pydantic; import pptx; from PIL import Image; print('OK: 핵심 패키지 정상')"
```

### 3. Frontend 빌드 검사

```bash
cd frontend
npm run lint 2>&1 | head -30
npm run build 2>&1 | tail -20
```

### 4. API 엔드포인트 구조 확인

`app/api/router.py`와 `app/api/endpoints/` 폴더의 라우터 등록 상태를 확인합니다.

---

## 출력 형식

```
[코드 품질 검사 결과]

1. Python 문법 검사
   - 검사 파일: N개
   - 통과: N개
   - 실패: N개 (상세 내역)

2. 의존성 검증
   - 핵심 패키지: OK / FAIL

3. Frontend 검사
   - Lint: OK / FAIL (경고 N건)
   - Build: OK / FAIL

4. 종합 판정: PASS / FAIL
```

---

## 주의사항

- 이 검사는 비파괴적입니다 (코드를 수정하지 않음)
- build 실패 시에도 기존 빌드 결과물에 영향 없음
- Python 경로: 시스템 python 또는 Anaconda python 자동 감지
