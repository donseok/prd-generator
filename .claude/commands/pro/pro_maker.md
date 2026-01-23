# Proposal Maker

최신 PRD JSON 파일을 기반으로 고객 제안서를 생성합니다.

## 실행 방법

```bash
# 기본 실행 (고객사명: 귀사)
python -m app.scripts.pro_maker

# 고객사명 지정
python -m app.scripts.pro_maker --client "ABC Corporation"
```

## 입력

- **경로**: `workspace/outputs/prd/PRD-*.json` (최신 파일)

## 출력

- **Markdown**: `workspace/outputs/proposals/PROP-{timestamp}.md`
- **JSON**: `workspace/outputs/proposals/PROP-{timestamp}.json`

## 생성 항목

1. 경영진 요약
2. 프로젝트 개요 (배경, 목표, 성공 기준)
3. 작업 범위 (포함/제외)
4. 솔루션 접근법 (아키텍처, 기술 스택)
5. 일정 계획 (마일스톤)
6. 산출물 목록
7. 투입 인력 (역할별 인원, M/M)
8. 리스크 및 대응방안
9. 전제 조건
10. 기대 효과
11. 후속 절차

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다
- Claude API 키가 `.env`에 설정되어 있어야 합니다
