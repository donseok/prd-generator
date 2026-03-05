# Delete Input Files

입력 파일들을 즉시 삭제합니다. 확인 절차 없이 바로 실행합니다.

## 삭제 대상

다음 폴더 내의 모든 파일을 삭제합니다 (`.gitkeep` 파일 제외):

| 폴더 | 내용 |
|------|------|
| `workspace/inputs/projects/` | 입력 파일 (txt, md, json, csv, xlsx, pptx, docx, png, jpg 등) |

## 실행 방법

**확인 절차 없이 즉시 삭제합니다.**

```python
import os

folder = "workspace/inputs/projects"
total_deleted = 0

if os.path.exists(folder):
    for f in os.listdir(folder):
        if f == ".gitkeep":
            continue
        filepath = os.path.join(folder, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
            total_deleted += 1

print(f"- {folder}/: {total_deleted}개 삭제")
print(f"총 {total_deleted}개 파일 삭제 완료")
```

## 주의사항

- `.gitkeep` 파일은 폴더 유지를 위해 보존합니다
