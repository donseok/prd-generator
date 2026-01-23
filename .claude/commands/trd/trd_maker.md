# TRD Maker

최신 PRD JSON 파일을 기반으로 TRD (Technical Requirements Document)를 생성합니다.

## 실행 방법

```bash
python -m app.scripts.trd_maker
```

## 입력

- **경로**: `workspace/outputs/prd/PRD-*.json` (최신 파일 자동 선택)

## 출력

- **Markdown**: `workspace/outputs/trd/TRD-{timestamp}.md`
- **JSON**: `workspace/outputs/trd/TRD-{timestamp}.json`

## 생성 항목

- 기술 스택 추천 (Frontend, Backend, Database, Infrastructure)
- 시스템 아키텍처 설계
- 데이터베이스 설계 (엔티티, 관계)
- API 명세 (RESTful 엔드포인트)
- 보안/성능/인프라 요구사항
- 기술 리스크 평가

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다
- Claude API 키가 `.env`에 설정되어 있어야 합니다
