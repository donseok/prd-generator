# API Health Check

백엔드 서버 상태와 API 엔드포인트를 점검합니다.

---

## 검사 항목

### 1. 서버 프로세스 확인

```bash
# 포트 8000 사용 여부 확인
netstat -ano | findstr :8000
```

- 사용 중: 서버 실행 중 (PID 표시)
- 미사용: 서버 미실행

### 2. 루트 엔드포인트

```bash
curl -s http://localhost:8000/ | python -m json.tool
```

정상 응답:
```json
{
    "name": "PRD 자동 생성 시스템",
    "version": "1.0.0"
}
```

### 3. API 엔드포인트 점검

```bash
# Swagger UI 접근
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs

# 주요 API 엔드포인트 점검
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/outputs/
```

### 4. 프론트엔드 서버 확인

```bash
# 포트 3000 사용 여부 확인
netstat -ano | findstr :3000

# 프론트엔드 접근
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

---

## 출력 형식

```
[API 헬스체크 결과]

1. 백엔드 서버 (port 8000)
   - 상태: 실행 중 / 중지됨
   - 루트: 200 OK
   - Swagger: 200 OK
   - API: 200 OK

2. 프론트엔드 서버 (port 3000)
   - 상태: 실행 중 / 중지됨
   - 페이지: 200 OK

3. 종합: 정상 / 일부 이상 / 서버 미실행
```

---

## 서버 미실행 시

서버가 실행되지 않은 경우 `/web:dash-board`로 서버를 시작할 수 있습니다.

```bash
# 수동 시작
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # 백엔드
cd frontend && npm run dev  # 프론트엔드
```
