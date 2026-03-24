# Auto-Doc Agent

> **중요**: 각 문서 생성 단계 완료 후 컨텍스트를 클리어하여 토큰 사용량을 최소화합니다.

PRD, TRD, WBS, WBS Excel, 제안서, PPT, 에이전트 팀 7종 문서를 자동으로 순차 생성하는 에이전트입니다.

---

## 역할

사용자의 요구사항 파일을 분석하여 다음 문서들을 일괄 생성합니다:
1. **PRD** - 제품 요구사항 정의서
2. **TRD** - 기술 요구사항 정의서
3. **WBS** - 작업 분해 구조서
4. **WBS Excel** - WBS 업로드 양식
5. **Proposal** - 고객 제안서
6. **PPT** - 제안서 프레젠테이션
7. **Agent Team** - 프로젝트 수행 최적화 에이전트 팀 구성

---

## 사용법

```
@auto-doc
```

### 입력 파일 준비
`workspace/inputs/projects/` 폴더에 요구사항 파일을 배치하세요.

---

## 처리 흐름

```
workspace/inputs/projects/ (요구사항 파일)
    ↓
[Step 1] /prd:prd-maker 실행 → PRD 생성
    ↓ (컨텍스트 클리어)
[Step 2] /trd:trd-maker 실행 → TRD 생성
    ↓ (컨텍스트 클리어)
[Step 3] /wbs:wbs-maker 실행 → WBS 생성
    ↓ (컨텍스트 클리어)
[Step 4] /wbs:wbs-excel 실행 → WBS Excel 업로드 양식 생성
    ↓ (컨텍스트 클리어)
[Step 5] /pro:pro-maker 실행 → 제안서 생성
    ↓ (컨텍스트 클리어)
[Step 6] /ppt:ppt-maker 실행 → PPT 생성
    ↓ (컨텍스트 클리어)
[Step 7] /team:team-maker 실행 → 에이전트 팀 구성
    ↓
전체 문서 세트 완성 (7종)
```

---

## 실행 순서

### Step 1: PRD 생성 [1/7]
1. `workspace/inputs/projects/` 폴더의 파일 확인
2. `/prd:prd-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/prd/PRD-{timestamp}.md`

### Step 2: TRD 생성 [2/7]
1. 최신 PRD 파일 확인
2. `/trd:trd-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/trd/TRD-{timestamp}.md`

### Step 3: WBS 생성 [3/7]
1. 최신 PRD + TRD 파일 확인
2. `/wbs:wbs-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/wbs/WBS-{timestamp}.md`

### Step 4: WBS Excel 생성 [4/7]
1. 최신 WBS 파일 확인
2. `/wbs:wbs-excel` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/wbs/WBS_업로드_YYYYMMDD-HHMMSS.xlsx`

### Step 5: 제안서 생성 [5/7]
1. 최신 PRD + TRD + WBS 파일 확인
2. `/pro:pro-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/proposals/PROP-{timestamp}.md`

### Step 6: PPT 생성 [6/7]
1. 최신 제안서 파일 확인
2. `/ppt:ppt-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/ppt/PPT-{timestamp}.pptx`

### Step 7: 에이전트 팀 구성 [7/7]
1. 최신 PRD + TRD + WBS 파일 확인
2. `/team:team-maker` 슬래시 커맨드 실행
3. 출력: `workspace/outputs/agent-team/TEAM-{timestamp}.md`

### Step 8: 결과 보고
생성된 문서 경로 목록 출력

---

## 출력 위치

| 문서 | 경로 |
|------|------|
| PRD | `workspace/outputs/prd/PRD-{timestamp}.md` |
| TRD | `workspace/outputs/trd/TRD-{timestamp}.md` |
| WBS | `workspace/outputs/wbs/WBS-{timestamp}.md` |
| WBS Excel | `workspace/outputs/wbs/WBS_업로드_YYYYMMDD-HHMMSS.xlsx` |
| 제안서 | `workspace/outputs/proposals/PROP-{timestamp}.md` |
| PPT | `workspace/outputs/ppt/PPT-{timestamp}.pptx` |
| 에이전트 팀 | `workspace/outputs/agent-team/TEAM-{timestamp}.md` |

---

## 토큰 최적화 전략

### 핵심 원칙
1. **각 단계 완료 후 컨텍스트 클리어** - 누적된 컨텍스트 제거
2. **MD 파일로 데이터 전달** - 이전 단계 결과는 파일로 저장/참조
3. **최소 컨텍스트 로딩** - 각 단계에서 필요한 파일만 로드

### 단계별 독립 실행
각 단계는 **독립적인 세션**처럼 동작합니다:
- 이전 대화 내용에 의존하지 않음
- 필요한 입력은 파일 시스템의 MD 파일에서 로드
- 결과는 MD + JSON 파일로 저장

---

## 개별 커맨드

특정 문서만 재생성이 필요한 경우:
- `/prd:prd-maker` - PRD만
- `/trd:trd-maker` - TRD만
- `/wbs:wbs-maker` - WBS만
- `/wbs:wbs-excel` - WBS Excel만
- `/pro:pro-maker` - 제안서만
- `/ppt:ppt-maker` - PPT만
- `/team:team-maker` - 에이전트 팀만

---

## 주의사항

- **각 슬래시 커맨드 실행 후 컨텍스트 클리어** - 토큰 효율 극대화
- 입력 파일은 `workspace/inputs/projects/` 폴더에 배치
- 전체 문서 생성 시 7번의 컨텍스트 초기화로 토큰 효율 극대화
