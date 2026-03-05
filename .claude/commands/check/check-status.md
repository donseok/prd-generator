# Document Status Check

workspace 내 모든 문서의 현황을 한눈에 보여줍니다.

---

## 검사 대상

### 입력 파일
- `workspace/inputs/projects/` - 프로젝트 입력 파일

### 출력 문서
- `workspace/outputs/prd/` - PRD (MD, JSON)
- `workspace/outputs/trd/` - TRD (MD, JSON)
- `workspace/outputs/wbs/` - WBS (MD, JSON)
- `workspace/outputs/proposals/` - 제안서 (MD, JSON)
- `workspace/outputs/ppt/` - PPT (PPTX)
- `workspace/outputs/diagrams/` - 다이어그램 (PNG)

---

## 실행 방법

```python
import os
from datetime import datetime

folders = {
    "입력 파일": "workspace/inputs/projects",
    "PRD": "workspace/outputs/prd",
    "TRD": "workspace/outputs/trd",
    "WBS": "workspace/outputs/wbs",
    "제안서": "workspace/outputs/proposals",
    "PPT": "workspace/outputs/ppt",
    "다이어그램": "workspace/outputs/diagrams",
}

print("=" * 60)
print("문서 현황 (Document Status)")
print("=" * 60)

total = 0
for label, folder in folders.items():
    files = []
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f != ".gitkeep" and os.path.isfile(os.path.join(folder, f))]

    count = len(files)
    total += count
    status = "OK" if count > 0 else "--"
    print(f"\n[{status}] {label}: {count}개")

    for f in sorted(files):
        filepath = os.path.join(folder, f)
        size = os.path.getsize(filepath)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f}MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f}KB"
        else:
            size_str = f"{size}B"

        print(f"     {f}  ({size_str}, {mtime.strftime('%H:%M:%S')})")

print(f"\n{'=' * 60}")
print(f"총 {total}개 파일")

# 파이프라인 진행도 판정
pipeline = {
    "PRD": os.path.exists("workspace/outputs/prd") and any(f.endswith(".json") for f in os.listdir("workspace/outputs/prd") if f != ".gitkeep"),
    "TRD": os.path.exists("workspace/outputs/trd") and any(f.endswith(".json") for f in os.listdir("workspace/outputs/trd") if f != ".gitkeep"),
    "WBS": os.path.exists("workspace/outputs/wbs") and any(f.endswith(".json") for f in os.listdir("workspace/outputs/wbs") if f != ".gitkeep"),
    "제안서": os.path.exists("workspace/outputs/proposals") and any(f.endswith(".json") for f in os.listdir("workspace/outputs/proposals") if f != ".gitkeep"),
    "PPT": os.path.exists("workspace/outputs/ppt") and any(f.endswith(".pptx") for f in os.listdir("workspace/outputs/ppt") if f != ".gitkeep"),
}

steps = list(pipeline.keys())
completed = sum(1 for v in pipeline.values() if v)
print(f"\n파이프라인: {' -> '.join(steps)}")
progress = " -> ".join(f"[{'V' if pipeline[s] else ' '}] {s}" for s in steps)
print(f"진행 상태: {progress}")
print(f"완료율: {completed}/{len(steps)} ({completed/len(steps)*100:.0f}%)")
```

---

## 출력 예시

```
============================================================
문서 현황 (Document Status)
============================================================

[OK] 입력 파일: 3개
     요구사항.md  (12.5KB, 14:30:22)
     시스템_구성도.png  (245.3KB, 14:30:22)

[OK] PRD: 2개
     PRD-20260305-143741.md  (8.2KB, 14:37:41)
     PRD-20260305-143741.json  (15.1KB, 14:37:41)

...

파이프라인: PRD -> TRD -> WBS -> 제안서 -> PPT
진행 상태: [V] PRD -> [V] TRD -> [V] WBS -> [V] 제안서 -> [V] PPT
완료율: 5/5 (100%)
```
