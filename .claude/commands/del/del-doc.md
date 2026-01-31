# Delete Generated Documents

테스트를 위해 생성된 문서들을 삭제하고 다음 테스트를 준비합니다.

## 목적

프로그램 테스트 과정에서 생성된 PRD, TRD, WBS, Proposal, PPT 문서들을 일괄 삭제하여 깨끗한 상태에서 다시 테스트할 수 있도록 합니다.

## 삭제 대상

다음 폴더 내의 모든 파일을 삭제합니다 (`.gitkeep` 파일 제외):

| 폴더 | 내용 |
|------|------|
| `workspace/outputs/prd/` | PRD 문서 (MD, JSON) |
| `workspace/outputs/trd/` | TRD 문서 (MD, JSON) |
| `workspace/outputs/wbs/` | WBS 문서 (MD, JSON) |
| `workspace/outputs/proposals/` | 제안서 문서 (MD, JSON) |
| `workspace/outputs/ppt/` | PPT 프레젠테이션 (PPTX) |

## 실행 단계

1. 각 폴더의 현재 파일 목록을 확인하고 표시
2. 삭제 대상 파일 총 건수 보고
3. 사용자에게 삭제 확인 요청
4. 확인 후 각 폴더의 파일 삭제 실행 (`.gitkeep` 제외)
5. 삭제 완료 후 결과 보고

## 실행 방법 (Python - OS 무관)

```python
import os
import glob

folders = [
    "workspace/outputs/prd",
    "workspace/outputs/trd",
    "workspace/outputs/wbs",
    "workspace/outputs/proposals",
    "workspace/outputs/ppt",
]

total_deleted = 0
for folder in folders:
    if not os.path.exists(folder):
        continue
    for f in os.listdir(folder):
        if f == ".gitkeep":
            continue
        filepath = os.path.join(folder, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
            total_deleted += 1

print(f"삭제 완료: {total_deleted}개 파일")
```

## 결과 보고 형식

```
[삭제 결과]
- workspace/outputs/prd/: N개 삭제
- workspace/outputs/trd/: N개 삭제
- workspace/outputs/wbs/: N개 삭제
- workspace/outputs/proposals/: N개 삭제
- workspace/outputs/ppt/: N개 삭제
→ 총 N개 파일 삭제 완료
```

## 주의사항

- 삭제된 파일은 복구할 수 없습니다
- 실행 전 반드시 삭제할 파일 목록을 확인합니다
- `.gitkeep` 파일은 폴더 유지를 위해 보존합니다
- `workspace/inputs/` 폴더는 삭제하지 않습니다 (입력 파일 보존)
