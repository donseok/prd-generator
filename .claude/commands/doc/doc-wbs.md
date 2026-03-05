# WBS Word(DOCX) 변환

WBS 문서를 Word(DOCX) 파일로 변환합니다.

---

## 실행

```bash
C:\Users\donse\anaconda3\python.exe -m app.scripts.doc_maker --type wbs
```

## 선행 조건
- WBS MD 파일 필요: `workspace/outputs/wbs/WBS-*.md`
- 없으면 `/wbs:wbs-maker` 먼저 실행

## 출력
- `workspace/outputs/doc/WBS-[YYYYMMDD-HHMMSS].docx`

위 스크립트를 실행하세요.
