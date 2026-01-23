# Auto-Doc Agent

PRD, TRD, WBS, 제안서를 자동으로 순차 생성하는 에이전트입니다.

## 역할

사용자의 요구사항을 분석하여 다음 문서들을 일괄 생성합니다:
1. **PRD** - 제품 요구사항 정의서
2. **TRD** - 기술 요구사항 정의서  
3. **WBS** - 작업 분해 구조서
4. **Proposal** - 고객 제안서 (--proposal 옵션)

## 사용법

### 기본 사용 (PRD + TRD + WBS)
```
@auto-doc [요구사항 설명]
```

### 제안서 포함 생성
```
@auto-doc --proposal [요구사항 설명]
```

### 파일 기반 사용
`workspace/inputs/projects/` 폴더에 요구사항 파일을 넣고:
```
@auto-doc
@auto-doc --proposal
```

## 실행 방법

### CLI 스크립트 사용 (권장)
```bash
# 기본 실행 (PRD + TRD + WBS)
python -m app.scripts.auto_doc

# 제안서 포함
python -m app.scripts.auto_doc --proposal

# 고객사명 지정
python -m app.scripts.auto_doc --proposal --client "ABC Corporation"
```

### CLI 옵션
| 옵션 | 설명 |
|------|------|
| `--proposal` | 제안서까지 생성 |
| `--client [이름]` | 고객사명 (기본: 귀사) |
| `--input-dir [경로]` | 입력 디렉토리 |
| `--output-dir [경로]` | 출력 디렉토리 |
| `--quiet` | 상세 로그 숨기기 |

## 처리 흐름 (토큰 최적화)

**중요: 각 단계 완료 후 `/clear` 명령으로 컨텍스트를 초기화하여 토큰 사용량을 최소화합니다.**

```
workspace/inputs/projects/ (요구사항 파일)
    ↓
[1] PRD 생성 (Layer 1-4)
    ↓ /clear ← 컨텍스트 초기화
[2] TRD 생성 (Layer 6) - PRD JSON 파일 참조
    ↓ /clear ← 컨텍스트 초기화
[3] WBS 생성 (Layer 7) - PRD + TRD JSON 파일 참조
    ↓ /clear ← 컨텍스트 초기화 (--proposal 시)
[4] 제안서 생성 (Layer 5) - PRD JSON 파일 참조 (--proposal 시)
    ↓
전체 문서 세트 완성
```

## 토큰 최적화 전략

### 핵심 원칙
1. **각 단계 완료 후 `/clear` 실행** - 누적된 컨텍스트 제거
2. **JSON 파일로 데이터 전달** - 이전 단계 결과는 파일로 저장/참조
3. **최소 컨텍스트 로딩** - 각 단계에서 필요한 파일만 로드

### 단계별 실행 방식

각 단계는 **독립적인 세션**처럼 동작합니다:
- 이전 대화 내용에 의존하지 않음
- 필요한 입력은 파일 시스템의 JSON 파일에서 로드
- 결과는 JSON + MD 파일로 저장

### 에이전트 모드 실행 순서

```
Step 1: 요구사항 확인
  - workspace/inputs/projects/ 파일 확인
  - 옵션 파싱

Step 2: PRD 생성
  - /prd:prd_maker 스킬 실행
  - 출력: workspace/outputs/prd/PRD-{timestamp}.json
  - /clear 실행 ← 컨텍스트 초기화

Step 3: TRD 생성
  - 최신 PRD JSON 파일 경로만 확인 (내용 로드 X)
  - /trd:trd_maker 스킬 실행 (내부에서 PRD JSON 로드)
  - 출력: workspace/outputs/trd/TRD-{timestamp}.json
  - /clear 실행 ← 컨텍스트 초기화

Step 4: WBS 생성
  - 최신 PRD + TRD JSON 파일 경로만 확인
  - /wbs:wbs_maker 스킬 실행 (내부에서 JSON 로드)
  - 출력: workspace/outputs/wbs/WBS-{timestamp}.json
  - --proposal 옵션이면 /clear 실행

Step 5: 제안서 생성 (--proposal 옵션 시)
  - 최신 PRD JSON 파일 경로 확인
  - /pro:pro_maker 스킬 실행
  - 출력: workspace/outputs/proposals/PROP-{timestamp}.md

Step 6: 결과 보고
  - 생성된 문서 경로 목록 출력
```

## 출력 위치

| 문서 | 경로 |
|------|------|
| PRD | `workspace/outputs/prd/PRD-{timestamp}.md` |
| TRD | `workspace/outputs/trd/TRD-{timestamp}.md` |
| WBS | `workspace/outputs/wbs/WBS-{timestamp}.md` |
| 제안서 | `workspace/outputs/proposals/PROP-{timestamp}.md` |

## 내부 구현

이 에이전트는 `DocumentOrchestrator` 클래스를 사용합니다:

```python
from app.services import DocumentOrchestrator

orchestrator = DocumentOrchestrator()
bundle = await orchestrator.generate_all(
    include_proposal=True,
    client_name="ABC Corp",
)
```

## 주의사항

- Claude API 키가 `.env`에 설정되어 있어야 합니다
- **각 단계 사이 `/clear` 실행으로 토큰 사용량 최소화** (에이전트 모드)
- JSON 파일은 각 스킬에서 직접 로드하므로 경로만 전달
- 전체 문서 생성 시 4번의 컨텍스트 초기화로 토큰 효율 극대화

## 개별 커맨드

특정 문서만 재생성이 필요한 경우:
- `/prd:prd_maker` - PRD만
- `/trd:trd_maker` - TRD만
- `/wbs:wbs_maker` - WBS만
- `/pro:pro_maker` - 제안서만
