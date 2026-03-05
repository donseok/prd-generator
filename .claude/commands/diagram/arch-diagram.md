# Architecture Diagram Generator

TRD 문서에서 시스템 아키텍처 다이어그램 PNG를 생성합니다.

---

## 기능

- TRD JSON의 `system_architecture` 데이터를 읽어 시각적 다이어그램 생성
- 레이어별 컬러 구분 (Presentation, API, Service, Data, Infrastructure)
- 컴포넌트 카드 + 타입 뱃지 + 설명 표시
- 데이터 플로우 하단 시각화
- PPT 슬라이드 삽입용으로 자동 연동됨

---

## 실행 방법

```bash
python -m app.scripts.arch_diagram
```

또는 Python 코드에서 직접 호출:

```python
from app.scripts.arch_diagram import generate_from_trd_file
from pathlib import Path

result = generate_from_trd_file(Path("workspace/outputs/trd/TRD-최신파일.json"))
print(f"생성 완료: {result}")
```

---

## 입력

- `workspace/outputs/trd/TRD-*.json` (최신 파일 자동 선택)

## 출력

- `workspace/outputs/diagrams/ARCH-[YYYYMMDD-HHMMSS].png` (1920x1080)

---

## 선행 조건

- TRD 문서가 생성되어 있어야 합니다 (`/trd:trd-maker` 먼저 실행)
- Pillow 라이브러리 필요 (`pip install Pillow`)

---

## PPT 연동

`/ppt:ppt-maker` 실행 시 자동으로 이 스크립트가 호출되어 아키텍처 슬라이드에 삽입됩니다.
기존 다이어그램이 있으면 재생성 없이 재사용합니다.
