# WBS Maker

최신 PRD 및 TRD 파일을 기반으로 WBS (Work Breakdown Structure)를 생성합니다.

## 실행 방법

```bash
python -m app.scripts.wbs_maker
```

## 입력

- **PRD**: `workspace/outputs/prd/PRD-*.json` (최신 파일)
- **TRD**: `workspace/outputs/trd/TRD-*.json` (선택, 있으면 활용)

## 출력

- **Markdown**: `workspace/outputs/wbs/WBS-{timestamp}.md`
- **JSON**: `workspace/outputs/wbs/WBS-{timestamp}.json`

## 생성 항목

- 프로젝트 단계 (Phase)
- 작업 패키지 (Work Package)
- 세부 작업 (Task) 및 공수 산정
- 의존성 및 일정 계획
- 크리티컬 패스 분석
- 리소스 배분 계획

## 컨텍스트 기본값

| 항목 | 기본값 |
|------|--------|
| 팀 규모 | 5명 |
| 방법론 | Agile |
| 스프린트 주기 | 2주 |
| 버퍼 비율 | 20% |

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다
- TRD가 있으면 더 정확한 공수 산정이 가능합니다
