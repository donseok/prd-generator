# WBS Excel 업로드 양식 생성

> **중요**: 이 작업을 시작하기 전에 이전 컨텍스트를 클리어하고 새로운 세션으로 시작합니다.

WBS JSON 데이터를 기반으로 업로드용 Excel(XLSX) 파일을 생성합니다.

---

## 실행 방법

다음 Python 스크립트를 실행하세요:

```bash
python -m app.scripts.wbs_excel_maker
```

---

## 전제 조건

- `workspace/outputs/wbs/WBS-*.json` 파일이 존재해야 합니다
- WBS JSON이 없으면 `/wbs:wbs-maker`를 먼저 실행하세요

---

## 출력

- **파일명**: `WBS_업로드_YYYYMMDD-HHMMSS.xlsx`
- **저장 위치**: `workspace/outputs/wbs/`
- **시트 구성**:
  - `WBS 데이터`: 3단계 계층 (Phase → Activity → Task)
  - `작성 가이드`: 필드 설명 및 작성 규칙

---

## 파이프라인

```
[입력 파일] → PRD → TRD → WBS (JSON/MD) → WBS Excel
                                           ^^^^
선행: WBS 생성 완료 필요 (/wbs:wbs-maker)
대안: python -m app.scripts.wbs_excel_maker
```

이제 스크립트를 실행하여 WBS Excel 파일을 생성하세요.
