# PPT 제안서 생성

> **중요**: 이 작업을 시작하기 전에 이전 컨텍스트를 클리어하고 새로운 세션으로 시작합니다.

당신은 프레젠테이션 디자인 전문가입니다.
제안서(PROP-*.json 또는 PROP-*.md) 파일을 기반으로 **python-pptx**를 사용하여 고객 프레젠테이션 PPT를 생성하세요.

---

## 디자인 설정

| 항목 | 값 |
|------|-----|
| **테마** | 다크 테마 (어두운 배경) |
| **슬라이드 수** | 21장 |
| **로고** | 없음 |

### 컬러 스킴 (다크 테마)
```python
COLORS = {
    "background": "#1E1E2E",      # 어두운 네이비
    "surface": "#2D2D3F",          # 카드/박스 배경
    "primary": "#7C3AED",          # 보라색 (포인트)
    "secondary": "#06B6D4",        # 시안 (보조)
    "accent": "#F59E0B",           # 오렌지 (강조)
    "text_primary": "#FFFFFF",     # 흰색 (제목)
    "text_secondary": "#A0AEC0",   # 회색 (본문)
    "success": "#10B981",          # 초록 (긍정)
    "warning": "#F59E0B",          # 주황 (주의)
}
```

### 폰트
- 제목: 맑은 고딕 Bold, 40-48pt
- 부제: 맑은 고딕 Regular, 28-32pt
- 본문: 맑은 고딕 Regular, 18-24pt

---

## 1단계: 입력 파일 읽기

**읽기 우선순위:**
1. **JSON 우선**: `workspace/outputs/proposals/PROP-*.json` (ppt_maker가 JSON을 직접 파싱)
2. **MD 폴백**: `workspace/outputs/proposals/PROP-*.md`
- 파일명의 타임스탬프(YYYYMMDD-HHMMSS) 기준으로 최신 파일 판별

---

## 2단계: 슬라이드 구성 (21장)

PPT 스크립트(`app/scripts/ppt_maker.py`)는 `normalize_proposal_data()` 함수로 제안서 JSON을 정규화한 후 21장의 슬라이드를 생성합니다.

| # | 슬라이드 | 생성 함수 | 데이터 소스 | 레이아웃 |
|---|---------|----------|-----------|---------|
| 1 | **표지** | `add_title_slide()` | title, metadata | 중앙 정렬, 큰 타이틀 |
| 2 | **목차** | `add_content_slide()` | 하드코딩 목차 | 번호 리스트 |
| 3 | **경영진 요약 (핵심)** | `add_highlight_slide()` | executive_summary | 큰 텍스트 + 키 수치 |
| 4 | **경영진 요약 (상세)** | `add_content_slide()` | executive_summary | 불릿 리스트 |
| 5 | **섹션: 현재 상황** | `add_section_title_slide()` | - | 섹션 타이틀 |
| 6 | **현재의 도전과 과제** | `add_content_slide()` | current_situation.challenges | 불릿 리스트 |
| 7 | **변화하지 않으면?** | `add_content_slide()` | current_situation.risks_if_no_change | 불릿 리스트 |
| 8 | **Before vs After** | `add_two_column_slide()` | current_situation | 2컬럼 비교 |
| 9 | **섹션: 프로젝트 목표** | `add_section_title_slide()` | - | 섹션 타이틀 |
| 10 | **KPI 카드** | `add_kpi_card_slide()` | objectives.kpis | 카드 형식 |
| 11 | **섹션: 우리의 솔루션** | `add_section_title_slide()` | - | 섹션 타이틀 |
| 12 | **솔루션 개요** | `add_highlight_slide()` | solution.value_proposition | 중앙 큰 텍스트 |
| 13 | **작업 범위** | `add_two_column_slide()` | solution.scope | 2컬럼 In/Out |
| 14 | **기술 스택** | `add_content_slide()` | technical_approach.technology_stack | 기술 목록 |
| 15 | **섹션: 일정 계획** | `add_section_title_slide()` | - | 섹션 타이틀 |
| 16 | **타임라인** | `add_timeline_slide()` | timeline.phases | 가로 타임라인 |
| 17 | **팀 구성** | `add_team_slide()` | team.composition | 역할 카드 |
| 18 | **리스크 관리** | `add_risk_table_slide()` | risk_management | 표 형식 |
| 19 | **기대 효과** | `add_highlight_slide()` | expected_benefits | 숫자 강조 |
| 20 | **다음 단계** | `add_steps_slide()` | next_steps | 스텝 다이어그램 |
| 21 | **Q&A** | `add_closing_slide()` | metadata | 중앙 정렬, 감사 인사 |

---

## 3단계: 정규화 데이터 구조

`normalize_proposal_data()` 함수가 제안서 JSON을 다음 구조로 변환합니다. PPT 생성에 사용되는 핵심 키:

```python
{
    "title": "프로젝트명",
    "metadata": {
        "proposal_date": "2024-01-01",
        "client_company": "고객사명",
        "proposer": "제안사"
    },
    "storytelling_structure": {
        "hook": "공감 메시지",
        "solution": "핵심 솔루션",
        "cta": "행동 촉구 메시지"
    },
    "executive_summary": {
        "problem": "핵심 문제",
        "solution": "핵심 솔루션",
        "duration": "N개월",
        "effort": "N M/M",
        "key_benefits": "핵심 기대효과"
    },
    "current_situation": {
        "challenges": [{"area": "영역", "issue": "문제", "impact": "영향"}],
        "risks_if_no_change": ["리스크1", "리스크2"],
        "future_vision": {"positive": ["비전1"], "negative": ["위험1"]}
    },
    "objectives": {
        "kpis": [{"name": "KPI명", "current": "현재", "target": "목표", "improvement": "개선율"}],
        "goals": [{"type": "핵심", "goal": "목표", "criteria": "기준"}]
    },
    "solution": {
        "value_proposition": "가치 제안",
        "overview": "솔루션 개요",
        "scope": {
            "in_scope": ["포함1"],
            "out_of_scope": ["제외1"]
        }
    },
    "technical_approach": {
        "technology_stack": [{"category": "구분", "tech": "기술", "reason": "사유"}]
    },
    "timeline": {
        "total_duration": "N개월",
        "phases": [{"name": "단계명", "duration": "기간", "deliverables": ["산출물"]}]
    },
    "team": {
        "composition": [{"role": "역할", "count": N, "skills": "역량"}],
        "effort_summary": {"total": {"man_months": N}}
    },
    "risk_management": [{"risk": "리스크", "impact": "영향도", "mitigation": "대응"}],
    "expected_benefits": {
        "quantitative": [{"metric": "지표", "before": "현재", "after": "목표", "improvement": "개선"}],
        "qualitative": ["정성적 효과1"]
    },
    "next_steps": [{"step": 1, "action": "내용", "duration": "기간"}]
}
```

---

## 4단계: PPT 생성 스크립트 실행

다음 Python 스크립트를 실행하세요:

```bash
C:\Users\donse\anaconda3\python.exe -m app.scripts.ppt_maker
```

---

## 5단계: 출력 확인

- **PPTX**: `workspace/outputs/ppt/PPT-[YYYYMMDD-HHMMSS].pptx`

---

## 불완전 데이터 처리

PPT 생성 시 일부 데이터가 없을 수 있습니다. `normalize_proposal_data()`가 다음과 같이 폴백합니다:

**최소 필수 필드:**
- `title` (없으면 "프로젝트 제안서")
- `executive_summary` (없으면 빈 문자열)

**선택 필드 기본값:**
- `current_situation.challenges` → 빈 리스트 (슬라이드에 "데이터 없음" 표시)
- `objectives.kpis` → 빈 리스트
- `timeline.phases` → 빈 리스트
- `team.composition` → 빈 리스트
- `risk_management` → 빈 리스트

---

## 디자인 원칙

1. **간결함**: 한 슬라이드에 하나의 메시지
2. **시각화**: 텍스트보다 도형, 아이콘, 차트 활용
3. **대비**: 다크 배경에 밝은 텍스트로 가독성 확보
4. **일관성**: 동일한 컬러, 폰트, 레이아웃 유지
5. **포인트 컬러**: 핵심 수치/키워드에 보라색/시안 강조

---

## 슬라이드별 가이드라인

### 표지 (슬라이드 1)
- 프로젝트명 대형 타이틀 (48pt, 흰색)
- 제안일 + 고객사명 (24pt, 회색)
- 배경: 그라데이션 또는 기하학적 패턴

### 숫자 강조 슬라이드 (3, 12, 19)
- 핵심 수치를 **72pt 이상 크게**
- 단위/설명은 작게 (24pt)
- 예: "**45분 → 20분**" (대기시간 56% 단축)

### 비교 슬라이드 (8, 13)
- 2컬럼 레이아웃
- 왼쪽: 현재 (어두운 빨강 계열)
- 오른쪽: 미래 (밝은 초록 계열)

### 섹션 타이틀 슬라이드 (5, 9, 11, 15)
- 큰 섹션 제목 중앙 배치
- 보라색 포인트 컬러 배경 또는 강조선

---

## 에러 처리

- **제안서 파일 없음**: "workspace/outputs/proposals/ 폴더에 제안서 파일이 없습니다. /pro:pro-maker를 먼저 실행하세요." 표시 후 중단
- **JSON 파싱 실패**: MD 파일로 폴백 시도
- **스크립트 실행 실패**: 에러 메시지 확인 후 python-pptx 설치 여부 점검 (`pip install python-pptx`)

---

## 파이프라인

```
[입력 파일] → PRD → TRD → WBS → Proposal → PPT
                                             ^^^^
선행: 제안서 생성 완료 필요 (/pro:pro-maker)
대안: python -m app.scripts.ppt_maker
```

이제 `workspace/outputs/proposals/` 폴더에서 최신 제안서를 읽고 PPT를 생성하세요.
