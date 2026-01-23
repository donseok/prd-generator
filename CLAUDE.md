# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRD 자동 생성 및 제안서/TRD/WBS 생성 시스템 - Converts various input formats (text, email, Excel, PowerPoint, images, chat logs, documents) into standardized PRD (Product Requirements Document) through a 7-layer AI pipeline, and generates customer proposals, TRD (Technical Requirements Document), and WBS (Work Breakdown Structure) from PRD.

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

### Custom Commands (Slash Commands)
```bash
/prd:prd_maker    # PRD 생성 (입력: workspace/inputs/projects/)
/trd:trd_maker    # TRD 생성 (입력: 최신 PRD JSON)
/wbs:wbs_maker    # WBS 생성 (입력: 최신 PRD JSON)
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

**Layer 1 (Parsing):** `app/layers/layer1_parsing/` - ParserFactory auto-selects parser based on input type. Outputs ParsedContent.

**Layer 2 (Normalization):** `app/layers/layer2_normalization/` - Uses Claude CLI to extract requirements, classify (FR/NFR/Constraint), generate user stories, calculate confidence scores.

**Layer 3 (Validation):** `app/layers/layer3_validation/` - Completeness/consistency checks. Routes low-confidence items to PM review.

**Layer 4 (Generation):** `app/layers/layer4_generation/` - Produces final PRDDocument with categorized requirements and milestones.

**Layer 5 (Proposal):** `app/layers/layer5_proposal/` - Converts PRDDocument to customer proposal (ProposalDocument). Generates executive summary, solution approach, timeline, resource plan, risks, and expected benefits using Claude.

**Layer 6 (TRD):** `app/layers/layer6_trd/` - Converts PRDDocument to Technical Requirements Document (TRDDocument). Generates technology stack recommendations, system architecture, database design, API specifications, security/performance requirements, infrastructure requirements, and technical risks.

**Layer 7 (WBS):** `app/layers/layer7_wbs/` - Converts PRDDocument to Work Breakdown Structure (WBSDocument). Generates project phases, work packages, tasks with estimates, resource allocation, dependencies, critical path analysis, and project schedule.

### Key Services

- `app/services/claude_client.py` - Claude Code CLI wrapper (`claude -p <prompt> --output-format text`)
- `app/services/orchestrator.py` - Pipeline orchestration, status management
- `app/services/file_storage.py` - JSON file-based storage in `/data/`

### Data Flow

**Workspace Structure:**
- `/workspace/inputs/samples/` - Sample input files for testing
- `/workspace/inputs/projects/` - Real project input files
- `/workspace/outputs/prd/` - Generated PRD documents (MD + JSON)
- `/workspace/outputs/proposals/` - Generated customer proposals
- `/workspace/outputs/trd/` - Generated TRD documents (MD + JSON)
- `/workspace/outputs/wbs/` - Generated WBS documents (MD + JSON)

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
| `POST /proposals/generate` | Generate proposal from PRD (TODO) |
| `GET /proposals/{proposal_id}` | Get proposal (TODO) |

Swagger UI: `http://localhost:8000/docs`

## Key Models

- `ParsedContent` - Layer 1 output with raw_text, sections, metadata
- `NormalizedRequirement` - Layer 2 output with user_story, acceptance_criteria, confidence_score
- `PRDDocument` - Layer 4 output with functional_requirements, non_functional_requirements, milestones
- `ProposalDocument` - Layer 5 output with executive_summary, scope_of_work, timeline, resource_plan, risks
- `ProposalContext` - Layer 5 input context (client_name, project_name, duration)
- `TRDDocument` - Layer 6 output with technology_stack, system_architecture, database_design, api_specification, security/performance/infrastructure_requirements, technical_risks
- `TRDContext` - Layer 6 input context (target_environment, preferred_stack, scalability_requirement, security_level)
- `WBSDocument` - Layer 7 output with phases, work_packages, tasks, summary (total_hours, man_months, critical_path)
- `WBSContext` - Layer 7 input context (start_date, team_size, methodology, sprint_duration, buffer_percentage)

## Git Workflow

Remote: `https://github.com/donseok/prd-generator.git`

Use `/git:git-commander` skill for automated commit and push workflow.