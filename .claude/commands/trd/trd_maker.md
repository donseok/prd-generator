# TRD (Technical Requirements Document) 생성

> **중요**: 이 작업을 시작하기 전에 이전 컨텍스트를 클리어하고 새로운 세션으로 시작합니다.

당신은 기술 설계 및 아키텍처 전문가입니다.
최신 PRD 문서를 기반으로 TRD (Technical Requirements Document)를 생성하세요.

---

## 1단계: PRD 파일 읽기

`workspace/outputs/prd/` 폴더에서 가장 최신 PRD 파일을 읽으세요:
- PRD-*.md 또는 PRD-*.json 파일 중 가장 최신 파일 선택
- 파일명의 타임스탬프 기준으로 최신 파일 판별

PRD에서 다음 정보를 추출하세요:
- 프로젝트 개요 및 목표
- 기능 요구사항 (FR)
- 비기능 요구사항 (NFR) - 성능, 보안, 확장성
- 제약조건 - 기술 스택, 외부 시스템

---

## 2단계: TRD 문서 작성

다음 구조로 TRD 문서를 작성하세요:

```markdown
# [프로젝트명] TRD (Technical Requirements Document)

**버전**: 1.0
**작성일**: [오늘 날짜]
**기반 PRD**: [PRD 파일명]
**상태**: Draft

---

## 1. 기술 스택 (Technology Stack)

### 1.1 Frontend
| 구분 | 기술 | 버전 | 선정 사유 |
|------|------|------|----------|
| Framework | [React/Vue/Next.js 등] | [버전] | [선정 사유] |
| State Management | [Redux/Zustand 등] | [버전] | [선정 사유] |
| UI Library | [Material-UI/Tailwind 등] | [버전] | [선정 사유] |
| Build Tool | [Vite/Webpack 등] | [버전] | [선정 사유] |

### 1.2 Backend
| 구분 | 기술 | 버전 | 선정 사유 |
|------|------|------|----------|
| Language | [Python/Node.js/Java 등] | [버전] | [선정 사유] |
| Framework | [FastAPI/Express/Spring 등] | [버전] | [선정 사유] |
| ORM | [SQLAlchemy/Prisma 등] | [버전] | [선정 사유] |

### 1.3 Database
| 구분 | 기술 | 버전 | 선정 사유 |
|------|------|------|----------|
| Primary DB | [PostgreSQL/MySQL 등] | [버전] | [선정 사유] |
| Cache | [Redis 등] | [버전] | [선정 사유] |
| Search | [Elasticsearch 등] | [버전] | [필요시] |

### 1.4 Infrastructure
| 구분 | 기술 | 선정 사유 |
|------|------|----------|
| Cloud Provider | [AWS/GCP/Azure 등] | [선정 사유] |
| Container | [Docker/Kubernetes 등] | [선정 사유] |
| CI/CD | [GitHub Actions/Jenkins 등] | [선정 사유] |
| Monitoring | [Prometheus/Grafana 등] | [선정 사유] |

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 전체 아키텍처

```
[아스키 아트 또는 mermaid 다이어그램으로 전체 시스템 구조 표현]

예시:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   API GW    │────▶│  Backend    │
│  (Web/App)  │     │  (nginx)    │     │  (FastAPI)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │  Database   │
                                        │ (PostgreSQL)│
                                        └─────────────┘
```

### 2.2 컴포넌트 설명
| 컴포넌트 | 역할 | 기술 |
|----------|------|------|
| [컴포넌트1] | [역할 설명] | [사용 기술] |
| [컴포넌트2] | [역할 설명] | [사용 기술] |

### 2.3 통신 방식
| From | To | 프로토콜 | 설명 |
|------|-----|---------|------|
| Client | API Server | HTTPS/REST | [설명] |
| API Server | Database | TCP | [설명] |

---

## 3. 데이터베이스 설계 (Database Design)

### 3.1 엔티티 관계도 (ERD)

```
[mermaid erDiagram 또는 텍스트 형태의 ERD]

예시:
┌──────────────┐       ┌──────────────┐
│    User      │       │    Order     │
├──────────────┤       ├──────────────┤
│ id (PK)      │───────│ id (PK)      │
│ name         │       │ user_id (FK) │
│ email        │       │ status       │
│ created_at   │       │ created_at   │
└──────────────┘       └──────────────┘
```

### 3.2 테이블 명세

#### [테이블명]
| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
|--------|------|------|--------|------|
| id | BIGINT | NO | AUTO | Primary Key |
| [컬럼] | [타입] | [NULL 여부] | [기본값] | [설명] |

### 3.3 인덱스 전략
| 테이블 | 인덱스명 | 컬럼 | 유형 | 용도 |
|--------|---------|------|------|------|
| [테이블] | [인덱스명] | [컬럼] | [B-Tree/Hash] | [검색 최적화 등] |

---

## 4. API 명세 (API Specification)

### 4.1 공통 사항
- Base URL: `/api/v1`
- 인증: Bearer Token (JWT)
- 응답 형식: JSON

### 4.2 엔드포인트 목록

#### [도메인] API

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | /[resource] | [설명] | Required |
| POST | /[resource] | [설명] | Required |
| PUT | /[resource]/{id} | [설명] | Required |
| DELETE | /[resource]/{id} | [설명] | Required |

#### 상세 명세

##### GET /[resource]
**설명**: [API 설명]

**Request**:
- Headers: `Authorization: Bearer {token}`
- Query Parameters:
  - `page` (integer, optional): 페이지 번호
  - `limit` (integer, optional): 페이지당 항목 수

**Response** (200 OK):
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

---

## 5. 보안 요구사항 (Security Requirements)

### 5.1 인증/인가
| 항목 | 구현 방식 |
|------|----------|
| 인증 | JWT (Access Token + Refresh Token) |
| 권한 관리 | RBAC (Role-Based Access Control) |
| 세션 관리 | [설명] |

### 5.2 데이터 보안
| 항목 | 구현 방식 |
|------|----------|
| 전송 암호화 | TLS 1.3 |
| 저장 암호화 | AES-256 (민감 데이터) |
| 비밀번호 | bcrypt (cost factor 12) |

### 5.3 보안 정책
- [ ] OWASP Top 10 대응
- [ ] SQL Injection 방지
- [ ] XSS 방지
- [ ] CSRF 방지
- [ ] Rate Limiting

---

## 6. 성능 요구사항 (Performance Requirements)

### 6.1 응답 시간
| 구분 | 목표값 | 측정 방법 |
|------|--------|----------|
| API 응답 (p50) | < 100ms | [측정 도구] |
| API 응답 (p95) | < 500ms | [측정 도구] |
| 페이지 로딩 | < 2s | Lighthouse |

### 6.2 처리량
| 구분 | 목표값 |
|------|--------|
| 동시 접속자 | [수치] |
| TPS | [수치] |

### 6.3 최적화 전략
- [ ] CDN 적용
- [ ] Database Connection Pooling
- [ ] Query Optimization
- [ ] Caching 전략

---

## 7. 인프라 요구사항 (Infrastructure Requirements)

### 7.1 서버 구성
| 환경 | 구성 | 스펙 |
|------|------|------|
| Development | [구성] | [스펙] |
| Staging | [구성] | [스펙] |
| Production | [구성] | [스펙] |

### 7.2 배포 전략
- 배포 방식: [Blue-Green / Rolling / Canary]
- 롤백 전략: [설명]

### 7.3 모니터링
| 대상 | 도구 | 알림 조건 |
|------|------|----------|
| Application | [도구] | [조건] |
| Infrastructure | [도구] | [조건] |
| Log | [도구] | [조건] |

---

## 8. 기술 리스크 (Technical Risks)

| ID | 리스크 | 영향도 | 발생 가능성 | 대응 방안 |
|----|--------|--------|------------|----------|
| TR-001 | [리스크 설명] | HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW | [대응 방안] |

---

## 9. 참고 문서

- 기반 PRD: [PRD 파일 경로]
- [기타 참고 문서]

---
*이 문서는 TRD 자동 생성 시스템에 의해 작성되었습니다.*
```

---

## 3단계: 파일 저장

생성한 TRD 문서를 다음 위치에 저장하세요:

1. **Markdown 파일**: `workspace/outputs/trd/TRD-[YYYYMMDD-HHMMSS].md`
2. **JSON 파일**: `workspace/outputs/trd/TRD-[YYYYMMDD-HHMMSS].json`

JSON 형식:
```json
{
  "id": "TRD-[YYYYMMDD-HHMMSS]",
  "title": "[프로젝트명]",
  "version": "1.0",
  "status": "draft",
  "based_on_prd": "[PRD ID]",
  "created_at": "[ISO 8601]",
  "technology_stack": {
    "frontend": [...],
    "backend": [...],
    "database": [...],
    "infrastructure": [...]
  },
  "system_architecture": {...},
  "database_design": {...},
  "api_specification": {...},
  "security_requirements": {...},
  "performance_requirements": {...},
  "infrastructure_requirements": {...},
  "technical_risks": [...]
}
```

---

## 작성 지침

1. **PRD 기반**: PRD의 요구사항을 기술적으로 구현하는 방법 제시
2. **구체성**: 기술 버전, 스펙, 수치를 구체적으로 명시
3. **일관성**: PRD의 NFR과 제약조건 반영
4. **실용성**: 개발팀이 바로 구현할 수 있는 수준의 상세도
5. **최신성**: 현재 널리 사용되는 안정적인 기술 스택 추천

이제 `workspace/outputs/prd/` 폴더에서 최신 PRD를 읽고 TRD 문서를 생성하세요.
