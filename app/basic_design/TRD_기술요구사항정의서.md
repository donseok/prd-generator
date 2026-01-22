# TRD (Technical Requirements Document)
# PRD 자동 생성 시스템 - 기술 요구사항 정의서

**버전**: 1.0
**작성일**: 2026-01-22
**상태**: Draft

---

## 1. 시스템 개요

### 1.1 시스템 목적
다양한 형식의 입력 문서를 4-레이어 AI 파이프라인을 통해 처리하여 표준화된 PRD 문서를 자동 생성하는 웹 애플리케이션 시스템

### 1.2 시스템 구성
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                     │
│                         Port: 3000                               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                         Port: 8000                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Layer (/api/v1)                    │   │
│  │  health │ documents │ processing │ prd │ review          │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Service Layer                          │   │
│  │  ClaudeClient │ FileStorage │ PipelineOrchestrator       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                4-Layer Processing Pipeline                │   │
│  │  Layer1: Parsing → Layer2: Normalization →               │   │
│  │  Layer3: Validation → Layer4: Generation                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  ┌──────────────────┐  ┌──────────────────────────────────┐    │
│  │  Claude Code CLI  │  │  File System Storage (/data)     │    │
│  │  (AI Processing)  │  │  jobs/ │ prd/ │ uploads/         │    │
│  └──────────────────┘  └──────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 기술 스택

### 2.1 Backend

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| Framework | FastAPI | 0.109.0+ | REST API 서버 |
| Server | Uvicorn | 0.27.0+ | ASGI 서버 |
| Validation | Pydantic | 2.6.0+ | 데이터 모델 및 검증 |
| Async I/O | aiofiles | 23.2.1+ | 비동기 파일 처리 |
| Config | python-dotenv | 1.0.0+ | 환경 변수 관리 |

### 2.2 Document Parsing Libraries

| 라이브러리 | 버전 | 대상 형식 |
|-----------|------|----------|
| pandas | 2.2.0+ | Excel, CSV |
| openpyxl | 3.1.2+ | Excel (.xlsx) |
| python-pptx | 0.6.23+ | PowerPoint (.pptx) |
| PyPDF2 | 3.0.1+ | PDF |
| python-docx | 1.1.0+ | Word (.docx) |
| mail-parser | 3.15.0+ | Email (.eml) |
| Pillow | 10.2.0+ | Image 처리 |

### 2.3 Frontend

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| Framework | Next.js | 14.2.0 | React 프레임워크 |
| UI Library | React | 18.2.0 | UI 컴포넌트 |
| Language | TypeScript | 5.3.0 | 타입 안전성 |
| State | Zustand | 4.5.0 | 상태 관리 |
| Data Fetching | React Query | 5.17.0 | 서버 상태 관리 |
| HTTP Client | Axios | 1.6.0 | API 통신 |
| File Upload | react-dropzone | 14.2.3 | 파일 업로드 UI |
| Styling | Tailwind CSS | 3.4.0 | 스타일링 |
| Icons | lucide-react | - | 아이콘 |

### 2.4 AI Service

| 구분 | 기술 | 용도 |
|------|------|------|
| AI Engine | Claude Code CLI | 요구사항 추출, 분류, 분석 |
| 호출 방식 | Subprocess | `claude -p <prompt> --output-format text` |
| 재시도 | 3회 | 지수 백오프 (2s, 4s, 8s) |

---

## 3. 아키텍처 상세

### 3.1 디렉토리 구조

```
app/
├── api/
│   ├── endpoints/
│   │   ├── health.py        # GET /health, /health/detail
│   │   ├── documents.py     # POST /documents/upload, /documents/text
│   │   ├── processing.py    # POST /processing/start, GET /processing/status
│   │   ├── prd.py           # GET /prd, /prd/{id}, /prd/{id}/export
│   │   └── review.py        # POST /review/decision, /review/complete
│   └── router.py            # API 라우터 통합
├── layers/
│   ├── layer1_parsing/      # 문서 파싱 레이어
│   │   ├── base_parser.py   # BaseParser 추상 클래스
│   │   ├── factory.py       # ParserFactory
│   │   └── parsers/         # 개별 파서 구현
│   ├── layer2_normalization/# 정규화 레이어
│   │   ├── normalizer.py    # Normalizer 클래스
│   │   └── prompts/         # Claude 프롬프트
│   ├── layer3_validation/   # 검증 레이어
│   │   └── validator.py     # Validator 클래스
│   └── layer4_generation/   # PRD 생성 레이어
│       └── generator.py     # PRDGenerator 클래스
├── models/
│   ├── input.py             # InputDocument, ParsedContent
│   ├── requirement.py       # NormalizedRequirement, ValidationResult
│   ├── prd.py               # PRDDocument, PRDOverview, Milestone
│   └── processing.py        # ProcessingJob, ProcessingStatus, ReviewItem
├── services/
│   ├── claude_client.py     # ClaudeClient (CLI 래퍼)
│   ├── file_storage.py      # FileStorage (JSON 파일 저장소)
│   └── orchestrator.py      # PipelineOrchestrator
├── config.py                # Settings (환경 설정)
└── main.py                  # FastAPI 앱 진입점
```

### 3.2 4-Layer Pipeline Architecture

#### Layer 1: Parsing
**입력**: 업로드된 파일 또는 텍스트
**출력**: `ParsedContent`

```python
class ParsedContent:
    raw_text: str              # 추출된 원본 텍스트
    structured_data: dict      # 구조화된 데이터 (Excel/CSV)
    metadata: InputMetadata    # 파일 메타데이터
    sections: list[dict]       # 섹션/헤더 구조
```

**지원 파서**:
- TextParser: TXT, MD
- EmailParser: EML
- ExcelParser: XLSX, CSV
- PPTParser: PPTX
- ImageParser: PNG, JPG, GIF
- ChatParser: 슬랙/메신저 로그
- DocumentParser: DOCX, PDF

#### Layer 2: Normalization
**입력**: `List[ParsedContent]`
**출력**: `List[NormalizedRequirement]`

```python
class NormalizedRequirement:
    id: str                    # REQ-001 형식
    type: RequirementType      # FR, NFR, CONSTRAINT
    title: str                 # 요구사항 제목
    description: str           # 상세 설명
    user_story: str            # User Story 형식
    acceptance_criteria: list  # 인수 조건
    priority: Priority         # HIGH, MEDIUM, LOW
    confidence_score: float    # 0.0 ~ 1.0
    source_reference: str      # 원본 참조
```

**처리 단계**:
1. Claude AI로 요구사항 후보 추출
2. 요구사항 유형 분류
3. User Story 생성
4. Acceptance Criteria 생성
5. 신뢰도 점수 계산
6. 요구사항 간 관계 식별

#### Layer 3: Validation
**입력**: `List[NormalizedRequirement]`
**출력**: `(validated_requirements, review_items)`

```python
class ReviewItem:
    requirement_id: str        # 관련 요구사항 ID
    issue_type: ReviewItemType # LOW_CONFIDENCE, CONFLICT, etc.
    description: str           # 이슈 설명
    pm_decision: str           # approve, reject, modify
```

**검증 항목**:
- 완전성 점수 (completeness_score)
- 일관성 검사 (consistency_issues)
- 추적성 점수 (traceability_score)
- 신뢰도 임계값 검사 (threshold: 0.8)

#### Layer 4: Generation
**입력**: `List[NormalizedRequirement]`
**출력**: `PRDDocument`

```python
class PRDDocument:
    id: str                           # PRD ID
    title: str                        # PRD 제목
    overview: PRDOverview             # 개요 섹션
    functional_requirements: list     # 기능 요구사항
    non_functional_requirements: list # 비기능 요구사항
    constraints: list                 # 제약조건
    milestones: list[Milestone]       # 마일스톤
    unresolved_items: list            # 미해결 사항
    metadata: PRDMetadata             # 메타데이터
```

### 3.3 데이터 저장 구조

```
data/
├── jobs/
│   └── {job_id}.json        # ProcessingJob 상태
├── prd/
│   └── {prd_id}.json        # PRDDocument
└── uploads/
    └── {doc_id}/
        ├── metadata.json    # InputDocument 메타데이터
        └── {filename}       # 원본 파일
```

---

## 4. API 명세

### 4.1 Health API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/health | 기본 상태 확인 |
| GET | /api/v1/health/detail | 상세 상태 (설정 정보 포함) |

### 4.2 Documents API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/documents/upload | 파일 업로드 (multipart/form-data) |
| POST | /api/v1/documents/text | 텍스트 직접 입력 |

### 4.3 Processing API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/processing/start | 파이프라인 시작 |
| GET | /api/v1/processing/status/{job_id} | 처리 상태 조회 |
| GET | /api/v1/processing | 작업 목록 조회 |
| POST | /api/v1/processing/cancel/{job_id} | 작업 취소 |

### 4.4 PRD API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/prd | PRD 목록 조회 |
| GET | /api/v1/prd/{prd_id} | PRD 상세 조회 |
| DELETE | /api/v1/prd/{prd_id} | PRD 삭제 |
| GET | /api/v1/prd/{prd_id}/export | PRD 내보내기 (format: markdown, json) |

### 4.5 Review API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/review/pending/{job_id} | 검토 대기 항목 조회 |
| POST | /api/v1/review/decision | 검토 결정 제출 |
| POST | /api/v1/review/complete/{job_id} | 검토 완료 및 재개 |
| GET | /api/v1/review/stats/{job_id} | 검토 통계 |

---

## 5. 처리 상태 흐름

```
PENDING
    │
    ▼
PARSING ─────────────────────────────────┐
    │                                     │
    ▼                                     │
NORMALIZING                               │
    │                                     │
    ▼                                     │
VALIDATING                                │ (오류 발생 시)
    │                                     │
    ├── (검토 필요 시) ──▶ PM_REVIEW      │
    │                          │          │
    │                          ▼          │
    │                   [PM 검토 완료]    │
    │                          │          │
    ▼◀─────────────────────────┘          │
GENERATING                                │
    │                                     │
    ▼                                     │
COMPLETED                              FAILED
```

---

## 6. 환경 설정

### 6.1 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| AUTO_APPROVE_THRESHOLD | 0.8 | 자동 승인 신뢰도 임계값 |
| HOST | 0.0.0.0 | 서버 호스트 |
| PORT | 8000 | 서버 포트 |
| NEXT_PUBLIC_API_URL | http://localhost:8001/api/v1 | 프론트엔드 API URL |

### 6.2 CORS 설정

```python
origins = [
    "http://localhost:3000",    # Next.js 개발 서버
    "http://127.0.0.1:3000",
]
```

---

## 7. 보안 고려사항

### 7.1 파일 업로드 보안
- 허용 확장자 화이트리스트
- 파일 크기 제한 (50MB/개, 200MB/총)
- 임시 파일 자동 삭제

### 7.2 API 보안
- 입력 데이터 Pydantic 검증
- SQL Injection 해당 없음 (파일 기반 저장소)
- CORS 정책 적용

### 7.3 향후 보안 강화 (예정)
- JWT 기반 인증
- API Rate Limiting
- 감사 로깅

---

## 8. 성능 요구사항

| 항목 | 목표 |
|------|------|
| 문서 파싱 | 10초/문서 |
| 요구사항 정규화 | 5초/요구사항 |
| PRD 생성 | 30초 이내 |
| API 응답 시간 | 500ms 이내 (생성 제외) |
| 동시 작업 수 | 최대 10개 |

---

## 9. 모니터링 및 로깅

### 9.1 로깅 레벨
- DEBUG: 상세 처리 과정
- INFO: 주요 이벤트 (레이어 시작/완료)
- WARNING: 비정상 상황
- ERROR: 오류 발생

### 9.2 로깅 위치
- `processing.py`: 파이프라인 이벤트
- `normalizer.py`: 정규화 상세 과정
- `claude_client.py`: Claude CLI 호출 상세

---

## 10. 확장성 고려

### 10.1 파서 확장
- `BaseParser` 상속으로 새 파서 추가
- `ParserFactory`에 매핑 등록

### 10.2 저장소 확장
- `FileStorage` 인터페이스 기반
- DB 저장소로 교체 가능 (MongoDB, PostgreSQL)

### 10.3 AI 서비스 확장
- `ClaudeClient` 인터페이스 기반
- 다른 LLM 서비스로 교체 가능
