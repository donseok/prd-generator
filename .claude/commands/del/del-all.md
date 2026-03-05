# Delete All (Full Reset)

입력 파일 + 출력 문서를 모두 삭제하여 workspace를 초기화합니다.
확인 절차 없이 즉시 실행합니다.

---

## 삭제 대상

| 폴더 | 내용 |
|------|------|
| `workspace/inputs/projects/` | 입력 파일 (txt, md, json, csv, xlsx, pptx, docx, png 등) |
| `workspace/outputs/prd/` | PRD 문서 (MD, JSON) |
| `workspace/outputs/trd/` | TRD 문서 (MD, JSON) |
| `workspace/outputs/wbs/` | WBS 문서 (MD, JSON) |
| `workspace/outputs/proposals/` | 제안서 문서 (MD, JSON) |
| `workspace/outputs/ppt/` | PPT 프레젠테이션 (PPTX) |
| `workspace/outputs/diagrams/` | 다이어그램 이미지 (PNG) |

---

## 실행 방법

**확인 절차 없이 즉시 삭제합니다.**

```python
import os

folders = [
    "workspace/inputs/projects",
    "workspace/outputs/prd",
    "workspace/outputs/trd",
    "workspace/outputs/wbs",
    "workspace/outputs/proposals",
    "workspace/outputs/ppt",
    "workspace/outputs/diagrams",
]

total_deleted = 0
for folder in folders:
    count = 0
    if not os.path.exists(folder):
        continue
    for f in os.listdir(folder):
        if f == ".gitkeep":
            continue
        filepath = os.path.join(folder, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
            count += 1
            total_deleted += 1
    print(f"- {folder}/: {count}개 삭제")

print(f"\n총 {total_deleted}개 파일 삭제 완료")
print("Workspace 초기화 완료")
```

---

## 주의사항

- `.gitkeep` 파일은 폴더 유지를 위해 보존합니다
- 입력 파일과 출력 문서가 **모두** 삭제됩니다
- 입력 파일만 삭제: `/del:del-input`
- 출력 문서만 삭제: `/del:del-doc`
