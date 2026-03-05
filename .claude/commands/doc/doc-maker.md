# Word(DOCX) 문서 변환 - 전체

생성된 MD 문서(PRD, TRD, WBS, Proposal)를 Word(DOCX) 파일로 일괄 변환합니다.

**인수**: $ARGUMENTS

---

## 실행

```bash
C:\Users\donse\anaconda3\python.exe -m app.scripts.doc_maker --type all
```

## 선행 조건

다음 문서 중 하나 이상이 생성되어 있어야 합니다:
- PRD: `workspace/outputs/prd/PRD-*.md`
- TRD: `workspace/outputs/trd/TRD-*.md`
- WBS: `workspace/outputs/wbs/WBS-*.md`
- Proposal: `workspace/outputs/proposals/PROP-*.md`

## 출력

- `workspace/outputs/doc/PRD-[YYYYMMDD-HHMMSS].docx`
- `workspace/outputs/doc/TRD-[YYYYMMDD-HHMMSS].docx`
- `workspace/outputs/doc/WBS-[YYYYMMDD-HHMMSS].docx`
- `workspace/outputs/doc/PROP-[YYYYMMDD-HHMMSS].docx`

위 스크립트를 실행하세요.
