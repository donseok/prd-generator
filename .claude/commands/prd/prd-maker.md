# PRD 문서 생성

당신은 PRD(Product Requirements Document) 작성 전문가입니다.
`workspace/inputs/projects/` 폴더의 모든 파일을 분석하여 표준 PRD 문서를 생성하세요.

---

## 0단계: 입력 파일 스캔 및 감지

`workspace/inputs/projects/` 폴더를 스캔하여 파일 유형별 개수를 보고하세요:

```
[스캔 결과]
- 텍스트: N개 (txt, md, json)
- 스프레드시트: N개 (csv, xlsx)
- 프레젠테이션: N개 (pptx)
- 문서: N개 (docx)
- 이미지: N개 (png, jpg, jpeg)
→ 총 N개 파일 감지
```

**발견된 파일 유형만** 아래 분석 가이드를 적용합니다. 없는 유형은 건너뜁니다.

---

## 1단계: 파일 유형별 분석 가이드

### 텍스트 파일 (txt, md, json)
- 전체 내용 직접 읽기
- 구조화된 섹션(제목, 목록, 표) 식별
- JSON인 경우 키-값 구조에서 요구사항 추출

### 스프레드시트 (csv, xlsx)
- **시트별 분석**: 각 시트의 헤더와 데이터 패턴 파악
- 요구사항 목록, 기능 매트릭스, 일정표 등 역할 식별
- 수치 데이터 → 비기능 요구사항 또는 성공 지표로 매핑

### 프레젠테이션 (pptx)
- **슬라이드별 분석**: 제목/본문/노트 영역 구분
- 다이어그램/도표 → 시스템 구조나 프로세스 플로우로 해석
- 발표자 노트 → 추가 컨텍스트로 활용

### 문서 (docx)
- **섹션별 분석**: 제목 계층 구조(H1→H2→H3) 추적
- 표 → 구조화된 요구사항으로 변환
- 수정 이력이 있으면 최신 내용 기준

### 이미지 (png, jpg)
- 와이어프레임 → 화면별 기능 요구사항 도출
- 시스템 다이어그램 → 아키텍처 제약조건 추출
- 텍스트가 포함된 이미지 → 내용 읽기 및 해석

### 각 파일에서 공통 추출 항목
- 프로젝트 배경 및 목적
- 기능 요구사항 (사용자가 원하는 기능)
- 비기능 요구사항 (성능, 보안, 확장성 등)
- 제약조건 (기술, 일정, 예산 등)
- 대상 사용자 정보
- 성공 지표

---

## 2단계: PRD 문서 작성

다음 구조로 PRD 문서를 작성하세요:

```markdown
# [프로젝트명] PRD (Product Requirements Document)

**버전**: 1.0
**작성일**: [오늘 날짜]
**상태**: Draft

---

## 1. 개요

### 1.1 배경
[프로젝트가 필요한 이유, 해결하려는 문제 설명 - 2~3문단]

### 1.2 목표
- [구체적이고 측정 가능한 목표 1]
- [목표 2]
- [목표 3]

### 1.3 범위
#### 포함 범위
- [이번 버전에 포함되는 기능/영역]

#### 범위 외
- [명시적으로 제외되는 항목]

### 1.4 대상 사용자
| 사용자 유형 | 역할 및 주요 활동 |
|------------|------------------|
| [사용자 1] | [역할 설명] |
| [사용자 2] | [역할 설명] |

### 1.5 성공 지표
- [KPI 1: 구체적 수치 목표]
- [KPI 2]
- [KPI 3]

---

## 2. 기능 요구사항 (Functional Requirements)

### FR-001: [기능명]
**우선순위**: HIGH | MEDIUM | LOW
**설명**: [기능에 대한 상세 설명]

**User Story**: [역할]로서, 나는 [기능]을 원한다, [목적/이유] 때문에.

**Acceptance Criteria**:
- [ ] [조건 1]
- [ ] [조건 2]
- [ ] [조건 3]

**출처**: [소스 파일명 및 위치]

[각 기능에 대해 위 형식 반복]

---

## 3. 비기능 요구사항 (Non-Functional Requirements)

### NFR-001: [카테고리명]
**우선순위**: HIGH | MEDIUM | LOW
**설명**: [구체적 수치 포함 설명]

[각 NFR에 대해 위 형식 반복]

---

## 4. 제약조건

### CON-001: [제약조건명]
**설명**: [구체적 제약 내용]

[각 제약조건에 대해 위 형식 반복]

---

## 5. 마일스톤

### M1: [마일스톤명] - [예상 기간]
**목표**: [마일스톤 목표]
**주요 산출물**:
- [산출물 1]
- [산출물 2]

---

## 6. 미해결 사항

| ID | 유형 | 설명 | 담당자 | 우선순위 |
|----|------|------|--------|---------|
| UNR-001 | 질문 | [확인이 필요한 사항] | PM | HIGH |

---

## 7. 부록

### 7.1 용어 정의
| 용어 | 정의 |
|------|------|
| [용어 1] | [정의] |

### 7.2 참고 문서
- [분석한 입력 파일 목록]

---
*이 문서는 PRD 자동 생성 시스템에 의해 작성되었습니다.*
```

---

## 3단계: 파일 저장

생성한 PRD 문서를 다음 위치에 저장하세요:

1. **Markdown 파일**: `workspace/outputs/prd/PRD-[YYYYMMDD-HHMMSS].md`
2. **JSON 파일**: `workspace/outputs/prd/PRD-[YYYYMMDD-HHMMSS].json`

JSON 형식 (PRDDocument 모델 준수):
```json
{
  "id": "PRD-[YYYYMMDD-HHMMSS]",
  "title": "[프로젝트명]",
  "overview": {
    "background": "[배경 설명]",
    "goals": ["[목표1]", "[목표2]"],
    "scope": "[포함 범위 설명]",
    "out_of_scope": ["[범위 외 1]"],
    "target_users": ["[사용자 유형1]"],
    "success_metrics": ["[지표1]"]
  },
  "functional_requirements": [
    {
      "id": "FR-001",
      "type": "FUNCTIONAL",
      "title": "[기능명]",
      "description": "[상세 설명]",
      "user_story": "[역할]로서, 나는 [기능]을 원한다, [목적] 때문에.",
      "acceptance_criteria": ["[조건1]", "[조건2]"],
      "priority": "HIGH",
      "confidence_score": 0.85,
      "confidence_reason": "[확신도 이유]",
      "source_reference": "[출처 파일:위치]",
      "source_info": {
        "document_id": "[문서ID]",
        "filename": "[파일명]",
        "section": "[섹션명]"
      },
      "assumptions": [],
      "missing_info": [],
      "related_requirements": []
    }
  ],
  "non_functional_requirements": [
    {
      "id": "NFR-001",
      "type": "NON_FUNCTIONAL",
      "title": "[NFR 제목]",
      "description": "[설명]",
      "priority": "HIGH",
      "confidence_score": 0.8,
      "confidence_reason": "[이유]",
      "source_reference": "[출처]",
      "acceptance_criteria": ["[기준]"],
      "assumptions": [],
      "missing_info": [],
      "related_requirements": []
    }
  ],
  "constraints": [
    {
      "id": "CON-001",
      "type": "CONSTRAINT",
      "title": "[제약조건명]",
      "description": "[설명]",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "[이유]",
      "source_reference": "[출처]",
      "acceptance_criteria": [],
      "assumptions": [],
      "missing_info": [],
      "related_requirements": []
    }
  ],
  "milestones": [
    {
      "id": "M1",
      "name": "[마일스톤명]",
      "description": "[설명]",
      "deliverables": ["[산출물1]"],
      "dependencies": [],
      "order": 1
    }
  ],
  "unresolved_items": [
    {
      "id": "UNR-001",
      "type": "question",
      "description": "[미해결 사항]",
      "related_requirement_ids": [],
      "priority": "HIGH",
      "suggested_action": "[제안 조치]"
    }
  ],
  "metadata": {
    "version": "1.0",
    "status": "draft",
    "author": "PRD Generator",
    "created_at": "[ISO 8601]",
    "source_documents": ["[파일1]", "[파일2]"],
    "overall_confidence": 0.85,
    "requires_pm_review": false,
    "pm_review_reasons": []
  }
}
```

---

## 작성 지침

1. **구체성**: 모호한 표현 대신 구체적인 수치와 조건 사용
2. **완전성**: 각 요구사항에 ID, 우선순위, User Story, Acceptance Criteria 포함
3. **추적성**: 요구사항의 출처 문서(source_reference) 명시
4. **일관성**: 용어와 형식의 일관성 유지
5. **실용성**: 개발팀이 바로 활용할 수 있는 수준의 상세도
6. **confidence_score**: 입력 데이터의 명확도에 따라 0.0~1.0 산정. 0.7 미만은 PM 검토 필요

---

## 에러 처리

- **입력 파일 없음**: "workspace/inputs/projects/ 폴더에 파일이 없습니다. 입력 파일을 추가해주세요." 표시 후 중단
- **파싱 실패**: 해당 파일 건너뛰기 + 경고 메시지 출력. 나머지 파일로 계속 진행
- **불완전 데이터**: 추출 가능한 정보로 PRD 작성 + 부족한 부분을 unresolved_items에 기록

---

## 파이프라인

```
[입력 파일] → PRD → TRD → WBS → Proposal → PPT
              ^^^^
후속: /trd:trd-maker, /wbs:wbs-maker, /pro:pro-maker
대안: python -m app.scripts.prd_maker
```

이제 `workspace/inputs/projects/` 폴더를 스캔하고 PRD 문서를 생성하세요.
