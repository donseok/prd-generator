# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRD 자동 생성 시스템 - Converts various input formats (text, email, Excel, PowerPoint, images, chat logs, documents) into standardized PRD (Product Requirements Document) through a 4-layer AI pipeline.

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

## Architecture

### 4-Layer Processing Pipeline

```
Documents → [Layer 1: Parsing] → [Layer 2: Normalization] → [Layer 3: Validation] → [Layer 4: Generation] → PRD
                                                                    ↓
                                                            PM_REVIEW (if low confidence)
```

**Layer 1 (Parsing):** `app/layers/layer1_parsing/` - ParserFactory auto-selects parser based on input type. Outputs ParsedContent.

**Layer 2 (Normalization):** `app/layers/layer2_normalization/` - Uses Claude CLI to extract requirements, classify (FR/NFR/Constraint), generate user stories, calculate confidence scores.

**Layer 3 (Validation):** `app/layers/layer3_validation/` - Completeness/consistency checks. Routes low-confidence items to PM review.

**Layer 4 (Generation):** `app/layers/layer4_generation/` - Produces final PRDDocument with categorized requirements and milestones.

### Key Services

- `app/services/claude_client.py` - Claude Code CLI wrapper (`claude -p <prompt> --output-format text`)
- `app/services/orchestrator.py` - Pipeline orchestration, status management
- `app/services/file_storage.py` - JSON file-based storage in `/data/`

### Data Flow

Jobs and PRDs stored as JSON files:
- `/data/jobs/{job_id}.json` - Processing job state
- `/data/prd/{prd_id}.json` - Generated PRD documents
- `/data/uploads/{doc_id}/` - Uploaded files with metadata

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

- `ParsedContent` - Layer 1 output with raw_text, sections, metadata
- `NormalizedRequirement` - Layer 2 output with user_story, acceptance_criteria, confidence_score
- `PRDDocument` - Final output with functional_requirements, non_functional_requirements, milestones

## Git Workflow

Remote: `https://github.com/donseok/prd-generator.git`

Use `/git:git-commander` skill for automated commit and push workflow.
- 프로그램 테스트 해보자