# 제안서 Word(DOCX) 변환

제안서(Proposal) 문서를 Word(DOCX) 파일로 변환합니다.

---

## 실행

```bash
C:\Users\donse\anaconda3\python.exe -m app.scripts.doc_maker --type proposal
```

## 선행 조건
- 제안서 MD 파일 필요: `workspace/outputs/proposals/PROP-*.md`
- 없으면 `/pro:pro-maker` 먼저 실행

## 출력
- `workspace/outputs/doc/PROP-[YYYYMMDD-HHMMSS].docx`

위 스크립트를 실행하세요.
