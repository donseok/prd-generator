# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRD 자동 생성 및 제안서/TRD/WBS 생성 시스템 - 다양한 입력 포맷(텍스트, 이메일, Excel, PowerPoint, 이미지, 채팅 로그, 문서)을 7-Layer AI 파이프라인을 통해 표준 PRD로 변환하고, PRD 기반으로 제안서, TRD, WBS, PPT, DOCX를 생성한다.

## Python Environment

**Python 3.12 사용 (Windows):**
```bash
"/c/Users/donse/AppData/Local/Programs/Python/Python312/python.exe" -m app.scripts.ppt_maker
```
> Windows App Store Python은 권한 문제가 있으므로 위 경로의 Python 3.12를 사용할 것.

## Build & Run Commands

### Backend (FastAPI)
```bash
pip install -r requirements.txt
python app/main.py                    # Port 8000, auto-reload
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev      # Port 3000
npm run build    # Production build
npm run lint     # ESLint
```

### Environment
```bash
cp .env.example .env
# Configure: AUTO_APPROVE_THRESHOLD (default 0.8), HOST, PORT
```

### Tests
```bash
python test_all_examples.py    # PRD 생성 테스트
python test_proposal.py        # 제안서 테스트
python test_trd_wbs.py         # TRD/WBS 테스트
```

## CLI Scripts

```bash
# 전체 문서 일괄 생성 (PRD→TRD→WBS→제안서→PPT)
python -m app.scripts.auto_doc

# 개별 문서 생성
python -m app.scripts.prd_maker                    # PRD
python -m app.scripts.trd_maker                    # TRD
python -m app.scripts.wbs_maker                    # WBS (MD+JSON)
python -m app.scripts.wbs_excel_maker              # WBS Excel 업로드 양식 (XLSX)
python -m app.scripts.pro_maker                    # 제안서
python -m app.scripts.pro_maker --client "고객사명"  # 고객사명 지정
python -m app.scripts.ppt_maker                    # PPT (제안서 기반, ~23 슬라이드)
python -m app.scripts.doc_maker                    # DOCX 전체 변환
python -m app.scripts.doc_maker --type prd         # 개별 DOCX 변환 (prd|trd|wbs|proposal)
python -m app.scripts.arch_diagram                 # 아키텍처 다이어그램 PNG 생성
```

## Custom Slash Commands & Agents

### 문서 생성
| 커맨드 | 입력 | 출력 |
|--------|------|------|
| `/prd:prd-maker` | `workspace/inputs/projects/*` | PRD MD+JSON |
| `/trd:trd-maker` | 최신 PRD JSON | TRD MD+JSON |
| `/wbs:wbs-maker` | 최신 PRD+TRD JSON | WBS MD+JSON |
| `/wbs:wbs-excel` | 최신 WBS JSON | WBS 업로드 양식 XLSX |
| `/pro:pro-maker` | 최신 PRD+TRD+WBS JSON | 제안서 MD+JSON |
| `/ppt:ppt-maker` | 최신 PROP JSON | PPTX |
| `/diagram:arch-diagram` | 최신 TRD JSON | 아키텍처 PNG |

### 문서 변환
| 커맨드 | 설명 |
|--------|------|
| `/doc:doc-maker` | DOCX 전체 변환 (PRD+TRD+WBS+제안서) |
| `/doc:doc-prd` `/doc:doc-trd` `/doc:doc-wbs` `/doc:doc-proposal` | 개별 DOCX 변환 |

### 유틸리티
| 커맨드 | 설명 |
|--------|------|
| `/del:del-doc` | 생성된 문서 삭제 |
| `/del:del-input` | 입력 파일 삭제 |
| `/del:del-all` | 전체 초기화 (입력+출력) |
| `/check:check-status` | 생성된 문서 현황 확인 |
| `/check:check-quality` | 코드 품질 검사 |
| `/deps:deps-check` | 의존성 검사 |
| `/test:test-run` | 테스트 실행 |
| `/web:dash-board` | 대시보드 실행 (백엔드+프론트엔드+브라우저) |
| `/web:api-health` | API 상태 확인 |
| `/help:help-commands` | 전체 커맨드 목록 |

### Agents
| 에이전트 | 설명 |
|----------|------|
| `@auto-doc` | PRD→TRD→WBS→제안서→PPT 5종 순차 생성 (단계별 컨텍스트 클리어) |

### Git
```bash
/git:git-push    # 커밋 및 푸시
/git:git-pull    # 최신 코드 가져오기
```

## Architecture

### 7-Layer Processing Pipeline

```
입력 파일 → [L1: Parsing] → [L2: Normalization] → [L3: Validation] → [L4: Generation] → PRD
                                                         ↓                                 ↓
                                                   PM_REVIEW (confidence < 0.8)    ┌───────┴───────┐
                                                                                    ↓               ↓
                                                                             [L5: Proposal]  [L6: TRD]
                                                                                    ↓               ↓
                                                                                 제안서       [L7: WBS]
```

- **Layer 1** `app/layers/layer1_parsing/` - ParserFactory가 입력 타입별 파서 자동 선택 (text, email, excel, ppt, image, chat, document)
- **Layer 2** `app/layers/layer2_normalization/` - 요구사항 추출, FR/NFR/Constraint 분류, User Story 생성
- **Layer 3** `app/layers/layer3_validation/` - 완전성/일관성 검증, 낮은 신뢰도 항목은 PM 리뷰로 라우팅
- **Layer 4** `app/layers/layer4_generation/` - BaseGenerator 상속, PRDDocument 생성
- **Layer 5** `app/layers/layer5_proposal/` - PRD → ProposalDocument (스토리텔링 기반 제안서)
- **Layer 6** `app/layers/layer6_trd/` - PRD → TRDDocument (기술 아키텍처, API 명세)
- **Layer 7** `app/layers/layer7_wbs/` - PRD → WBSDocument (작업 분해, 공수 산정)

### Key Services

- `app/services/claude_client.py` - **Claude Code CLI wrapper** (subprocess로 `claude` CLI 호출, API 아님). 재시도 로직, 비동기 처리(ThreadPoolExecutor) 포함
- `app/services/orchestrator.py` - Layer 1-4 파이프라인 오케스트레이션
- `app/services/document_orchestrator.py` - 전체 문서 파이프라인 (PRD→TRD→WBS→Proposal)
- `app/services/file_storage.py` - JSON 파일 기반 저장소 (`/data/`)

### Scripts (독립 실행 가능)

CLI 스크립트는 **슬래시 커맨드와 1:1 대응**. 각 스크립트는 독립적으로 실행 가능하며, `workspace/outputs/`의 파일을 읽어 다음 문서를 생성:
- `ppt_maker.py` - `normalize_proposal_data()`로 제안서 JSON을 PPT 구조로 정규화 후 python-pptx로 생성
- `doc_maker.py` - MD → DOCX 변환 (python-docx)
- `arch_diagram.py` - TRD JSON 기반 아키텍처 다이어그램 PNG 생성

### Data Flow

**Workspace (파일 기반 I/O):**
- `workspace/inputs/projects/` - 입력 파일 (txt, md, json, csv, xlsx, pptx, docx, png, jpg)
- `workspace/outputs/prd/` - PRD (MD + JSON)
- `workspace/outputs/trd/` - TRD (MD + JSON)
- `workspace/outputs/wbs/` - WBS (MD + JSON)
- `workspace/outputs/proposals/` - 제안서 (MD + JSON)
- `workspace/outputs/ppt/` - PPT (PPTX)
- `workspace/outputs/doc/` - Word (DOCX)
- `workspace/outputs/diagrams/` - 아키텍처 다이어그램 (PNG)

**파일 네이밍**: `{TYPE}-{YYYYMMDD-HHMMSS}.{ext}` (타임스탬프 기반, 최신 파일 우선)

**Runtime (API 모드):**
- `/data/jobs/{job_id}.json` - 처리 작업 상태
- `/data/uploads/{doc_id}/` - 업로드 파일 + 메타데이터

### Processing Statuses
```
PENDING → PARSING → NORMALIZING → VALIDATING → GENERATING → COMPLETED
                                      ↓
                                  PM_REVIEW → GENERATING → COMPLETED
```

## API Structure

Base URL: `/api/v1` | Swagger UI: `http://localhost:8000/docs`

| Endpoint | Purpose |
|----------|---------|
| `POST /documents/upload` | 파일 업로드 |
| `POST /processing/start` | 파이프라인 시작 |
| `GET /processing/status/{job_id}` | 진행 상태 조회 |
| `GET /prd/{prd_id}` | PRD 조회 |
| `GET /prd/{prd_id}/export?format=markdown\|json` | PRD 내보내기 |
| `POST /review/decision` | PM 리뷰 결정 제출 |
| `POST /review/complete/{job_id}` | 리뷰 후 처리 재개 |

## Key Models

- `PRDDocument` (`app/models/prd.py`) - functional_requirements, non_functional_requirements, milestones, unresolved_items
- `ProposalDocument` (`app/layers/layer5_proposal/models/`) - executive_summary, scope_of_work, timeline, resource_plan
- `TRDDocument` (`app/layers/layer6_trd/models/`) - technology_stack, system_architecture, database_design, api_specification
- `WBSDocument` (`app/layers/layer7_wbs/models/`) - phases, work_packages, tasks, summary (total_hours, man_months, critical_path)

## PPT Generation

`ppt_maker.py`가 제안서 JSON을 `normalize_proposal_data()`로 정규화한 후 ~23장 슬라이드 생성. TRD가 있으면 `arch_diagram.py`로 아키텍처 다이어그램 자동 포함.

슬라이드 순서: 표지 → 목차 → 경영진 요약(2) → 현재 상황 섹션(4) → 프로젝트 목표 섹션(2) → 솔루션 섹션(4) → 일정 계획 섹션(4) → 기대 효과 → 다음 단계 → Q&A

## Git Workflow

Remote: `https://github.com/donseok/prd-generator.git`
Branch: `main`
# currentDate
Today's date is 2026-03-05.
