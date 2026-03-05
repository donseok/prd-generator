# Test Runner

프로젝트의 테스트를 실행하고 결과를 보고합니다.

---

## 테스트 대상

### 1. 백엔드 단위 테스트

프로젝트 루트의 테스트 파일들을 실행합니다:

```bash
# 전체 테스트 실행
python -m pytest tests/ -v --tb=short 2>&1 || echo "pytest 미설치 또는 tests/ 폴더 없음"

# pytest가 없을 경우 개별 테스트 파일 직접 실행
python test_all_examples.py 2>&1 | tail -20
python test_proposal.py 2>&1 | tail -20
python test_trd_wbs.py 2>&1 | tail -20
```

### 2. API 헬스체크 테스트

백엔드 서버가 실행 중일 때:

```bash
# 헬스체크
curl -s http://localhost:8000/ | python -m json.tool

# API 엔드포인트 확인
curl -s http://localhost:8000/docs -o /dev/null -w "Swagger UI: HTTP %{http_code}\n"
```

### 3. Frontend 빌드 테스트

```bash
cd frontend
npm run build 2>&1 | tail -10
```

### 4. 스크립트 import 테스트

모든 스크립트가 정상적으로 import 가능한지 확인:

```python
import sys
sys.path.insert(0, '.')

scripts = [
    "app.scripts.prd_maker",
    "app.scripts.trd_maker",
    "app.scripts.wbs_maker",
    "app.scripts.pro_maker",
    "app.scripts.ppt_maker",
    "app.scripts.arch_diagram",
    "app.scripts.auto_doc",
]

for script in scripts:
    try:
        __import__(script)
        print(f"  OK: {script}")
    except Exception as e:
        print(f"  FAIL: {script} - {e}")
```

---

## 출력 형식

```
[테스트 결과]

1. 백엔드 단위 테스트: PASS/FAIL (N passed, N failed)
2. API 헬스체크: OK/SKIP (서버 미실행)
3. Frontend 빌드: PASS/FAIL
4. 스크립트 Import: N/N 성공

종합: PASS / FAIL
```

---

## 옵션

- 서버가 실행 중이지 않으면 API 테스트는 건너뜁니다
- 테스트 실패 시 오류 상세 내용을 출력합니다
- 기존 코드나 데이터를 수정하지 않습니다
