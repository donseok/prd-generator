# Auto-Doc Agent

PRD, TRD, WBS, 제안서를 요구사항 기반으로 순차 생성하는 에이전트입니다.

## 역할

사용자의 요구사항을 분석하여 다음 문서들을 일괄 생성합니다:
1. **PRD** (Product Requirements Document) - 제품 요구사항 정의서
2. **TRD** (Technical Requirements Document) - 기술 요구사항 정의서  
3. **WBS** (Work Breakdown Structure) - 작업 분해 구조서
4. **Proposal** (제안서) - 고객 제안서 (--proposal 옵션)

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

## 처리 흐름

### 기본 흐름
```
요구사항 입력
    ↓
[1] PRD 생성 (/prd:prd_maker 실행)
    ↓
[2] TRD 생성 (/trd:trd_maker 실행) - PRD 기반
    ↓
[3] WBS 생성 (/wbs:wbs_maker 실행) - PRD + TRD 기반
    ↓
전체 문서 세트 완성
```

### --proposal 옵션 사용 시
```
요구사항 입력
    ↓
[1] PRD 생성
    ↓
[2] TRD 생성 - PRD 기반
    ↓
[3] WBS 생성 - PRD + TRD 기반
    ↓
[4] 제안서 생성 (/pro:pro-maker 실행) - PRD + TRD + WBS 기반
    ↓
전체 문서 + 제안서 완성
```

## 실행 단계

### Step 1: 요구사항 확인
- `workspace/inputs/projects/` 폴더의 파일 확인
- 요구사항이 없으면 사용자에게 입력 요청

### Step 2: PRD 생성
- prd_maker 스크립트 실행
- 요구사항을 분석하여 기능/비기능 요구사항 추출

### Step 3: TRD 생성
- PRD JSON 파일을 입력으로 TRD 생성
- 기술 스택, 아키텍처, API 명세, DB 설계 포함

### Step 4: WBS 생성
- PRD + TRD JSON 파일을 입력으로 WBS 생성
- 작업 분해, 공수 산정, 일정 계획 포함

### Step 5: 제안서 생성 (--proposal 옵션 시)
- PRD를 기반으로 고객 제안서 생성
- 프로젝트 개요, 솔루션 접근법, 일정, 투입 인력, 견적 포함

### Step 6: 결과 보고
- 생성된 문서 목록 출력
- 주요 요약 정보 제공

## 출력 위치

| 문서 | 경로 |
|------|------|
| PRD | `workspace/outputs/prd/PRD-{timestamp}.md` |
| TRD | `workspace/outputs/trd/TRD-{timestamp}.md` |
| WBS | `workspace/outputs/wbs/WBS-{timestamp}.md` |
| 제안서 | `workspace/outputs/proposals/PROP-{timestamp}.md` |

## 옵션

| 옵션 | 설명 |
|------|------|
| `--proposal` | PRD/TRD/WBS 생성 후 고객 제안서까지 생성 |
| `--prd-only` | PRD만 생성 |
| `--skip-wbs` | WBS 생성 생략 |
| `--context [파일]` | 추가 컨텍스트 파일 지정 |

## 주의사항

- Claude API 키가 `.env`에 설정되어 있어야 합니다
- 요구사항 파일이 많을수록 처리 시간이 늘어납니다
- 전체 문서 생성에는 약 5-15분이 소요될 수 있습니다
- 제안서 포함 시 추가로 2-3분 소요

## 개별 커맨드 사용

특정 문서만 재생성하거나 수정이 필요한 경우:
- `/prd:prd_maker` - PRD만 재생성
- `/trd:trd_maker` - TRD만 재생성 (최신 PRD 기반)
- `/wbs:wbs_maker` - WBS만 재생성 (최신 PRD+TRD 기반)
- `/pro:pro-maker` - 제안서만 재생성 (최신 PRD 기반)
