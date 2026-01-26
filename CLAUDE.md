# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRD 자동 생성 및 제안서/TRD/WBS 생성 시스템 - Converts various input formats (text, email, Excel, PowerPoint, images, chat logs, documents) into standardized PRD (Product Requirements Document) through a 7-layer AI pipeline, and generates customer proposals, TRD (Technical Requirements Document), and WBS (Work Breakdown Structure) from PRD.

## Python Environment

**Windows에서 Anaconda Python 사용 (권장):**
```bash
# Windows App Store Python 권한 문제 회피
C:\Users\donse\anaconda3\python.exe -m app.scripts.ppt_maker

# 또는 Anaconda Prompt에서 실행
python -m app.scripts.ppt_maker
```

## Build & Run Commands

### Backend (FastAPI)
```bash
pip install -r requirements.txt
python app/main.py                    # Runs on port 8000 with auto-reload
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev      # Development server on port 3000
npm run build    # Production build
npm run lint     # ESLint
```

### Environment Setup
```bash
cp .env.example .env
# Configure: AUTO_APPROVE_THRESHOLD (default 0.8), HOST, PORT
```

### Test Commands
```bash
# PRD 생성 테스트 (전체 파일)
python test_all_examples.py

# 제안서 생성 테스트 (PRD → Proposal)
python test_proposal.py

# TRD/WBS 생성 테스트
python test_trd_wbs.py
```

## CLI Scripts

### 전체 문서 생성 (@auto-doc)
```bash
# PRD + TRD + WBS 생성
python -m app.scripts.auto_doc

# 제안서 포함
python -m app.scripts.auto_doc --proposal --client "ABC Corporation"
```

### 개별 문서 생성
```bash
python -m app.scripts.prd_maker    # PRD 생성
python -m app.scripts.trd_maker    # TRD 생성
python -m app.scripts.wbs_maker    # WBS 생성
python -m app.scripts.pro_maker    # 제안서 생성
python -m app.scripts.pro_maker --client "고객사명"
python -m app.scripts.ppt_maker    # PPT 생성 (제안서 기반)
```

### Custom Slash Commands
```bash
/prd:prd-maker    # PRD 생성 (입력: workspace/inputs/projects/)
/trd:trd-maker    # TRD 생성 (입력: 최신 PRD JSON)
/wbs:wbs-maker    # WBS 생성 (입력: 최신 PRD JSON)
/pro:pro-maker    # 제안서 생성 (입력: 최신 PRD JSON)
/ppt:ppt-maker    # PPT 생성 (입력: 최신 제안서 PROP-*.md)
/del:del-doc      # 생성된 문서 삭제 (테스트 초기화)
```

### Custom Agents
```bash
@auto-doc                    # PRD + TRD + WBS 생성
@auto-doc --proposal         # PRD + TRD + WBS + 제안서 생성
```

## Architecture

### 7-Layer Processing Pipeline

```
Documents → [Layer 1: Parsing] → [Layer 2: Normalization] → [Layer 3: Validation] → [Layer 4: Generation] → PRD
                                                                    ↓                                        ↓
                                                            PM_REVIEW (if low confidence)          ┌────────┴────────┐
                                                                                                    ↓                 ↓
                                                                                          [Layer 5: Proposal]  [Layer 6: TRD]
                                                                                                    ↓                 ↓
                                                                                               제안서          [Layer 7: WBS]
                                                                                                                      ↓
                                                                                                                    WBS
```

**Layer 1 (Parsing):** `app/layers/layer1_parsing/` - ParserFactory auto-selects parser based on input type.

**Layer 2 (Normalization):** `app/layers/layer2_normalization/` - Extracts requirements, classifies (FR/NFR/Constraint), generates user stories.

**Layer 3 (Validation):** `app/layers/layer3_validation/` - Completeness/consistency checks. Routes low-confidence items to PM review.

**Layer 4 (Generation):** `app/layers/layer4_generation/` - Inherits from BaseGenerator. Produces PRDDocument.

**Layer 5 (Proposal):** `app/layers/layer5_proposal/` - Inherits from BaseGenerator. Converts PRD to ProposalDocument.

**Layer 6 (TRD):** `app/layers/layer6_trd/` - Inherits from BaseGenerator. Converts PRD to TRDDocument.

**Layer 7 (WBS):** `app/layers/layer7_wbs/` - Inherits from BaseGenerator. Converts PRD to WBSDocument.

### Key Services

- `app/services/claude_client.py` - Claude Code CLI wrapper
- `app/services/orchestrator.py` - Layer 1-4 pipeline orchestration
- `app/services/document_orchestrator.py` - Full document pipeline (PRD→TRD→WBS→Proposal)
- `app/services/file_storage.py` - JSON file-based storage in `/data/`

### Scripts

- `app/scripts/auto_doc.py` - CLI for full document generation
- `app/scripts/prd_maker.py` - PRD generation
- `app/scripts/trd_maker.py` - TRD generation
- `app/scripts/wbs_maker.py` - WBS generation
- `app/scripts/pro_maker.py` - Proposal generation
- `app/scripts/ppt_maker.py` - PPT generation (dark theme, 20 slides)

### Data Flow

**Workspace Structure:**
- `/workspace/inputs/projects/` - Input files (txt, md, json, csv, xlsx, pptx, docx, png, jpg)
- `/workspace/outputs/prd/` - Generated PRD documents (MD + JSON)
- `/workspace/outputs/trd/` - Generated TRD documents (MD + JSON)
- `/workspace/outputs/wbs/` - Generated WBS documents (MD + JSON)
- `/workspace/outputs/proposals/` - Generated customer proposals (MD + JSON)
- `/workspace/outputs/ppt/` - Generated PPT presentations (PPTX)

**Runtime Data:**
- `/data/jobs/{job_id}.json` - Processing job state
- `/data/uploads/{doc_id}/` - Uploaded files with metadata (API)

### Processing Statuses
```
PENDING → PARSING → NORMALIZING → VALIDATING → GENERATING → COMPLETED
                                      ↓
                                  PM_REVIEW → GENERATING → COMPLETED
```

## API Structure

Base URL: `/api/v1`

| Endpoint | Purpose |
|----------|---------|
| `POST /documents/upload` | Upload files |
| `POST /processing/start` | Start pipeline |
| `GET /processing/status/{job_id}` | Get progress |
| `GET /prd/{prd_id}` | Get PRD |
| `GET /prd/{prd_id}/export?format=markdown\|json` | Export PRD |
| `POST /review/decision` | Submit PM review |
| `POST /review/complete/{job_id}` | Resume after review |

Swagger UI: `http://localhost:8000/docs`

## Key Models

- `PRDDocument` - Layer 4 output with functional_requirements, non_functional_requirements, milestones
- `PRDContext` - Layer 4 input context (title, source_documents)
- `ProposalDocument` - Layer 5 output with executive_summary, scope_of_work, timeline, resource_plan
- `ProposalContext` - Layer 5 input context (client_name, project_name, duration)
- `TRDDocument` - Layer 6 output with technology_stack, system_architecture, database_design, api_specification
- `TRDContext` - Layer 6 input context (target_environment, preferred_stack, scalability_requirement)
- `WBSDocument` - Layer 7 output with phases, work_packages, tasks, summary (total_hours, man_months, critical_path)
- `WBSContext` - Layer 7 input context (start_date, team_size, methodology, sprint_duration)

## PPT Generation

### 다크 테마 설정
```python
COLORS = {
    "background": "#1E1E2E",  # 배경색
    "surface": "#2D2D3F",     # 카드/박스 배경
    "primary": "#7C3AED",     # 포인트 (보라)
    "secondary": "#06B6D4",   # 보조 (청록)
    "accent": "#F59E0B",      # 강조 (주황)
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0AEC0",
}
```

### 슬라이드 구성 (20장)
1. 표지
2. 목차
3. 경영진 요약 (핵심 메시지)
4. 경영진 요약 (상세)
5. 섹션: 현재 상황
6. 현재의 도전과 과제
7. 변화하지 않으면?
8. Before vs After
9. 섹션: 프로젝트 목표
10. KPI 카드
11. 섹션: 솔루션
12. 솔루션 개요
13. 작업 범위
14. 기술 스택
15. 섹션: 일정 계획
16. 타임라인
17. 팀 구성
18. 리스크 관리
19. 기대 효과
20. 다음 단계
21. Q&A

### 데이터 정규화
`ppt_maker.py`의 `normalize_proposal_data()` 함수가 ProposalDocument JSON 구조를 PPT 생성에 필요한 구조로 자동 변환합니다.

## Git Workflow

Remote: `https://github.com/donseok/prd-generator.git`

```bash
/git:git-push    # 변경사항 커밋 및 푸시
/git:git-pull    # 최신 코드 가져오기
```