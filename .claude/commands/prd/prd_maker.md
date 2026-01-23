# PRD Maker

`workspace/inputs/projects` 폴더의 파일을 분석하여 PRD 문서를 생성합니다.

## 실행 방법

```bash
python -m app.scripts.prd_maker
```

## 입력

- **경로**: `workspace/inputs/projects/`
- **지원 포맷**: txt, md, json, csv, xlsx, pptx, docx, png, jpg

## 출력

- **Markdown**: `workspace/outputs/prd/PRD-{timestamp}.md`
- **JSON**: `workspace/outputs/prd/PRD-{timestamp}.json`

## 처리 파이프라인

1. **Layer 1** - 파싱: 각 파일 형식에 맞게 텍스트 추출
2. **Layer 2** - 정규화: 요구사항 추출 및 분류 (FR/NFR/CONSTRAINT)
3. **Layer 3** - 검증: 완전성/일관성 검증, 신뢰도 산정
4. **Layer 4** - 생성: PRD 문서 생성

## 주의사항

- Claude API 키가 `.env`에 설정되어 있어야 합니다
- 파일이 많을 경우 처리 시간이 길어질 수 있습니다
