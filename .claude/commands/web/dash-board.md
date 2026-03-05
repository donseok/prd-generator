# Dashboard 실행

프론트엔드 서버, 백엔드 서버를 시작하고 크롬 브라우저로 대시보드를 엽니다.

---

## 실행 단계

### 1단계: 기존 프로세스 확인

포트 8000(백엔드)과 3000(프론트엔드)이 이미 사용 중인지 확인합니다.
- 사용 중이면 해당 서버가 이미 실행 중임을 알립니다.
- 사용 중이 아니면 다음 단계로 진행합니다.

```bash
# Windows에서 포트 사용 확인
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### 2단계: 백엔드 서버 실행 (FastAPI)

백엔드 서버를 백그라운드로 실행합니다.

```bash
cd C:/Users/donse/prd-generator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```

- 포트: 8000
- 자동 리로드 활성화
- Swagger UI: http://localhost:8000/docs

### 3단계: 프론트엔드 서버 실행 (Next.js)

프론트엔드 서버를 백그라운드로 실행합니다.

```bash
cd C:/Users/donse/prd-generator/frontend
npm run dev &
```

- 포트: 3000
- 개발 모드 (Hot Reload)

### 4단계: 서버 준비 대기

두 서버가 정상적으로 시작될 때까지 잠시 대기합니다 (약 5초).

### 5단계: 크롬 브라우저로 대시보드 열기

```bash
start chrome http://localhost:3000
```

### 6단계: 상태 보고

실행 결과를 사용자에게 보고합니다:

```
[Dashboard 실행 완료]
- Backend:  http://localhost:8000 (FastAPI) ✅
- Frontend: http://localhost:3000 (Next.js) ✅
- Swagger:  http://localhost:8000/docs
- Browser:  Chrome으로 대시보드 열림 ✅
```

---

## 서버 중지 방법

서버를 중지하려면 터미널에서 Ctrl+C를 누르거나:

```bash
# Windows에서 포트별 프로세스 종료
netstat -ano | findstr :8000
netstat -ano | findstr :3000
# 해당 PID로 종료: taskkill /PID <PID> /F
```

---

## 주의사항

- 백엔드는 `.env` 파일의 환경변수를 사용합니다
- 프론트엔드는 `frontend/` 디렉토리에서 실행되어야 합니다
- 두 서버 모두 개발 모드로 실행됩니다 (파일 변경 시 자동 리로드)
- 크롬이 설치되어 있어야 합니다
