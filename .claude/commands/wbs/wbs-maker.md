# WBS (Work Breakdown Structure) 생성

> **중요**: 이 작업을 시작하기 전에 이전 컨텍스트를 클리어하고 새로운 세션으로 시작합니다.

당신은 프로젝트 관리 및 WBS 작성 전문가입니다.
최신 PRD 및 TRD 문서를 기반으로 WBS를 생성하세요.

---

## 1단계: 입력 파일 읽기

다음 순서로 파일을 읽으세요:

**읽기 우선순위 (JSON 우선):**
1. **PRD** (필수): `workspace/outputs/prd/PRD-*.json` 우선 → `PRD-*.md` 폴백
2. **TRD** (선택): `workspace/outputs/trd/TRD-*.json` 우선 → `TRD-*.md` 폴백
- 파일명의 타임스탬프(YYYYMMDD-HHMMSS) 기준으로 최신 파일 판별

PRD/TRD에서 추출할 정보:
- 기능 요구사항 (FR) 목록 및 우선순위
- 비기능 요구사항 (NFR)
- 마일스톤 정보
- 기술 스택 (TRD) → 역할 도출 기준
- 시스템 아키텍처 (TRD)

---

## 2단계: 프로젝트 규모 판단

PRD의 기능 요구사항(FR) 개수로 프로젝트 규모를 판단하세요:

| FR 개수 | 규모 | 기본 기간 | 기본 팀 규모 |
|---------|------|----------|-------------|
| 1~10개 | 소규모 | 8~12주 | 3~5명 |
| 11~25개 | 중규모 | 12~20주 | 5~8명 |
| 26개+ | 대규모 | 20~32주 | 8~12명 |

---

## 3단계: 적응형 팀 구성

TRD의 technology_stack에서 역할을 자동 도출하세요:

**역할 도출 규칙:**
| TRD 기술 스택 키워드 | 도출 역할 |
|---------------------|----------|
| Frontend, React, Vue, Next.js, Angular | 프론트엔드 개발자 |
| Backend, FastAPI, Express, Spring, Django | 백엔드 개발자 |
| Mobile, Flutter, React Native, iOS, Android | 모바일 개발자 |
| Edge, Embedded, IoT, Arduino, Raspberry Pi | 임베디드/에지 개발자 |
| AI, ML, TensorFlow, PyTorch | AI/ML 엔지니어 |
| Docker, Kubernetes, AWS, GCP, Azure | DevOps 엔지니어 |

**항상 포함되는 역할:**
- PM/PL (1명, 전 기간)
- QA (0.5~1명, 테스트 단계)
- UI/UX 디자이너 (0.5명, 설계 단계)

**제외 규칙:** TRD에 해당 기술이 없으면 해당 역할은 팀에서 제외합니다.
예: 모바일 기술이 없으면 모바일 개발자 제외.

---

## 4단계: WBS 문서 작성

다음 구조로 WBS 문서를 작성하세요:

```markdown
# [프로젝트명] WBS (Work Breakdown Structure)

**버전**: 1.0
**작성일**: [오늘 날짜]
**기반 문서**: PRD-[ID], TRD-[ID]
**상태**: Draft

---

## 프로젝트 요약

| 항목 | 값 |
|------|-----|
| 총 작업 기간 | [N]주 ([M]개월) |
| 총 공수 | [X] Man-Days ([Y] Man-Months) |
| 팀 규모 | [N]명 |
| 방법론 | Agile / Waterfall |
| 스프린트 주기 | [N]주 |
| 버퍼 비율 | 20% |

---

## 1. 프로젝트 단계 (Phases)

```mermaid
gantt
    title 프로젝트 일정
    dateFormat  YYYY-MM-DD
    section Phase 1
    분석/설계        :a1, [시작일], [기간]
    section Phase 2
    개발             :a2, after a1, [기간]
    section Phase 3
    테스트/배포       :a3, after a2, [기간]
```

### Phase 1: 분석 및 설계
- **기간**: [시작일] ~ [종료일] ([N]주)
- **목표**: [단계 목표]
- **산출물**: [주요 산출물]
- **마일스톤**: [마일스톤명]

### Phase 2: 개발
- **기간**: [시작일] ~ [종료일] ([N]주)
- **목표**: [단계 목표]
- **산출물**: [주요 산출물]
- **마일스톤**: [마일스톤명]

### Phase 3: 테스트 및 배포
- **기간**: [시작일] ~ [종료일] ([N]주)
- **목표**: [단계 목표]
- **산출물**: [주요 산출물]
- **마일스톤**: [마일스톤명]

---

## 2. 작업 패키지 (Work Packages)

### WP-1: [작업 패키지명]
| ID | 작업명 | 담당 역할 | 예상 공수(시간) | 선행 작업 | 산출물 |
|----|--------|----------|---------------|----------|--------|
| WP-1.1 | [작업명] | [역할] | [N]h | - | [산출물] |
| WP-1.2 | [작업명] | [역할] | [N]h | WP-1.1 | [산출물] |

**소계**: [N]시간 ([M] Man-Days)

[각 WP에 대해 반복]

---

## 3. 크리티컬 패스 (Critical Path)

```
[작업 ID] → [작업 ID] → ... → [작업 ID]
```

| 단계 | 작업 ID | 작업명 | 공수(시간) | 누적 |
|------|---------|--------|----------|------|
| 1 | WP-1.1 | [작업명] | [N]h | [N]h |

**총 크리티컬 패스 길이**: [N] Man-Days

---

## 4. 리소스 배분 (Resource Allocation)

### 4.1 역할별 투입 계획

| 역할 | 인원 | 주요 담당 작업 | 투입 공수 | 투입률 |
|------|------|---------------|----------|--------|
| [역할] | [N]명 | [주요 작업] | [N]MD | [N]% |

### 4.2 주차별 투입 현황

| 주차 | [역할1] | [역할2] | [역할3] | ... |
|------|---------|---------|---------|-----|
| W1-W2 | ● | ○ | - | ... |

(● 전담, ○ 부분 투입, - 미투입)

---

## 5. 공수 요약 (Effort Summary)

### 5.1 단계별 공수

| 단계 | 공수 (시간) | Man-Days | 비율 |
|------|-----------|----------|------|
| 분석/설계 | [N] | [N] | [X]% |
| 개발 | [N] | [N] | [X]% |
| 테스트 | [N] | [N] | [X]% |
| 배포 | [N] | [N] | [X]% |
| **소계** | **[N]** | **[N]** | 100% |
| 버퍼 (20%) | [N] | [N] | - |
| **총계** | **[N]** | **[N]** | - |

### 5.2 Man-Month 환산

- 1 Man-Day = 8시간
- 1 Man-Month = 20 Man-Days = 160시간
- **총 공수**: [N]시간 = [N] Man-Days = **[M] Man-Months**

---

## 6. 리스크 및 가정사항

### 가정사항
- [가정1]
- [가정2]

### 일정 리스크
| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| [리스크] | HIGH/MEDIUM/LOW | [대응] |

---

## 7. 참고 문서

- 기반 PRD: [PRD 파일 경로]
- 기반 TRD: [TRD 파일 경로]

---
*이 문서는 WBS 자동 생성 시스템에 의해 작성되었습니다.*
```

---

## 5단계: 파일 저장

생성한 WBS 문서를 다음 위치에 저장하세요:

1. **Markdown**: `workspace/outputs/wbs/WBS-[YYYYMMDD-HHMMSS].md`
2. **JSON**: `workspace/outputs/wbs/WBS-[YYYYMMDD-HHMMSS].json`

JSON 형식 (WBSDocument 모델 준수):
```json
{
  "id": "WBS-[YYYYMMDD-HHMMSS]",
  "title": "[프로젝트명] WBS",
  "phases": [
    {
      "id": "P1",
      "name": "분석/설계",
      "description": "[단계 설명]",
      "order": 1,
      "start_date": "2024-01-01",
      "end_date": "2024-01-21",
      "milestone": "[마일스톤명]",
      "deliverables": ["[산출물1]"],
      "work_packages": [
        {
          "id": "WP-1",
          "name": "[작업 패키지명]",
          "description": "[설명]",
          "start_date": "2024-01-01",
          "end_date": "2024-01-14",
          "tasks": [
            {
              "id": "WP-1.1",
              "name": "[작업명]",
              "description": "[설명]",
              "estimated_hours": 24,
              "status": "NOT_STARTED",
              "resources": [
                {
                  "resource_type": "PM/PL",
                  "allocation_percentage": 100,
                  "person_count": 1
                }
              ],
              "dependencies": [
                {
                  "predecessor_id": "WP-1.0",
                  "dependency_type": "FS",
                  "lag_days": 0
                }
              ],
              "start_date": "2024-01-01",
              "end_date": "2024-01-03",
              "related_requirement_ids": ["FR-001"],
              "deliverables": ["[산출물]"],
              "notes": ""
            }
          ]
        }
      ]
    }
  ],
  "summary": {
    "total_phases": 3,
    "total_work_packages": 8,
    "total_tasks": 25,
    "total_hours": 1200,
    "total_man_days": 150,
    "total_man_months": 7.5,
    "estimated_duration_days": 84,
    "critical_path": ["WP-1.1", "WP-2.1", "WP-3.1"],
    "resource_summary": [
      {
        "resource_type": "백엔드 개발자",
        "total_hours": 320,
        "total_days": 40,
        "peak_allocation": 2
      }
    ]
  },
  "metadata": {
    "version": "1.0",
    "status": "draft",
    "created_at": "[ISO 8601]",
    "source_prd_id": "[PRD ID]",
    "source_prd_title": "[PRD 제목]"
  }
}
```

---

## 작성 지침

1. **PRD/TRD 기반**: 모든 작업은 PRD 요구사항 및 TRD 기술 스택을 반영
2. **적응형 팀 구성**: TRD 기술 스택에서 역할 자동 도출. 불필요한 역할 제외
3. **공수 현실성**: 실제 개발 경험에 기반한 현실적인 공수 산정 (시간 단위)
4. **의존성 명확화**: 작업 간 선후 관계 명확히 정의 (dependency_type: FS/SS/FF/SF)
5. **버퍼 포함**: 총 공수의 20%는 버퍼로 배정
6. **크리티컬 패스 식별**: 일정 지연 리스크가 높은 경로 식별
7. **단위**: 시간(h) 기본, Man-Day = 8h, Man-Month = 20MD = 160h

---

## 에러 처리

- **PRD 파일 없음**: "workspace/outputs/prd/ 폴더에 PRD 파일이 없습니다. /prd:prd-maker를 먼저 실행하세요." 표시 후 중단
- **TRD 파일 없음**: TRD 없이 PRD만으로 WBS 생성 가능. 경고 메시지 출력 후 기본 웹 앱 팀 구성 적용
- **불완전 데이터**: 가용한 정보로 WBS 작성 + 가정사항에 명시

---

## 파이프라인

```
[입력 파일] → PRD → TRD → WBS → Proposal → PPT
                          ^^^^
선행: PRD 생성 완료 필요 (/prd:prd-maker), TRD 권장 (/trd:trd-maker)
후속: /pro:pro-maker
대안: python -m app.scripts.wbs_maker
```

이제 `workspace/outputs/prd/` 및 `workspace/outputs/trd/` 폴더에서 최신 문서를 읽고 WBS를 생성하세요.
