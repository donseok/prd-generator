# TRD (Technical Requirements Document) 생성

> **중요**: 이 작업을 시작하기 전에 이전 컨텍스트를 클리어하고 새로운 세션으로 시작합니다.

당신은 기술 설계 및 아키텍처 전문가입니다.
최신 PRD 문서를 기반으로 TRD (Technical Requirements Document)를 생성하세요.

---

## 1단계: PRD 파일 읽기

`workspace/outputs/prd/` 폴더에서 가장 최신 파일을 읽으세요:

**읽기 우선순위:**
1. **JSON 우선**: `PRD-*.json` (구조화된 데이터, 파싱 정확도 높음)
2. **MD 폴백**: `PRD-*.md` (JSON이 없을 경우)
- 파일명의 타임스탬프(YYYYMMDD-HHMMSS) 기준으로 최신 파일 판별

PRD에서 다음 정보를 추출하세요:
- 프로젝트 개요 및 목표
- 기능 요구사항 (FR) 목록 및 우선순위
- 비기능 요구사항 (NFR) - 성능, 보안, 확장성
- 제약조건 - 기술 스택, 외부 시스템
- 대상 사용자 유형

---

## 2단계: 프로젝트 도메인 감지

PRD 내용의 키워드를 분석하여 프로젝트 도메인을 판별하세요:

| 키워드 패턴 | 도메인 | 기술 스택 가이드 |
|-------------|--------|-----------------|
| IoT, 센서, 계량, 카메라, LPR, SCADA, 게이트웨이, 에지 | **산업/IoT 시스템** | 에지 컴퓨팅, MQTT/Modbus, 시계열DB, 온프레미스 고려 |
| 웹, 대시보드, 포털, 관리자, SaaS, CMS | **웹 애플리케이션** | React/Next.js, REST API, PostgreSQL, 클라우드 |
| 모바일, APP, Flutter, iOS, Android, 푸시 알림 | **모바일 우선** | Flutter/React Native, Firebase, GraphQL |
| AI, ML, 모델, 학습, 추론, 데이터 파이프라인 | **AI/ML 시스템** | Python, TensorFlow/PyTorch, GPU 인프라 |
| 블록체인, 스마트 컨트랙트, 토큰 | **블록체인** | Solidity, Web3, 분산 네트워크 |

**복합 도메인**: 키워드가 여러 도메인에 걸치면 주요 도메인 + 보조 도메인으로 구성합니다.
예: "IoT + 웹 대시보드" → 산업/IoT 시스템 (주) + 웹 애플리케이션 (보조)

감지된 도메인에 따라 기술 스택과 아키텍처 스타일을 조정하세요.

---

## 3단계: TRD 문서 작성

다음 구조로 TRD 문서를 작성하세요:

```markdown
# [프로젝트명] TRD (Technical Requirements Document)

**버전**: 1.0
**작성일**: [오늘 날짜]
**기반 PRD**: [PRD 파일명]
**프로젝트 도메인**: [감지된 도메인]
**상태**: Draft

---

## 1. 기술 요약 (Executive Summary)

[프로젝트의 기술적 접근 방식을 2~3문단으로 요약. 핵심 아키텍처 결정과 기술 선택의 근거를 포함]

---

## 2. 기술 스택 (Technology Stack)

### 2.1 [카테고리: Frontend / Backend / Database / Infrastructure / Edge 등]
| 구분 | 기술 | 버전 | 선정 사유 |
|------|------|------|----------|
| [구분] | [기술명] | [버전] | [선정 사유] |

[PRD의 요구사항과 감지된 도메인에 맞는 기술 스택 구성]

---

## 3. 시스템 아키텍처 (System Architecture)

### 3.1 전체 아키텍처

[아키텍처 스타일: 마이크로서비스 / 모놀리식 / 서버리스 / 에지-클라우드 등]

```
[아스키 아트 또는 mermaid 다이어그램으로 전체 시스템 구조 표현]
```

### 3.2 계층별 설명
| 계층 | 설명 | 핵심 컴포넌트 |
|------|------|-------------|
| [계층명] | [역할 설명] | [컴포넌트 목록] |

### 3.3 데이터 흐름
[시스템 내 데이터의 흐름 설명]

### 3.4 배포 다이어그램
[운영 환경의 배포 구성 설명]

---

## 4. 데이터베이스 설계 (Database Design)

### 4.1 데이터베이스 유형 및 엔진
- **유형**: [RDBMS / NoSQL / 시계열DB / 혼합]
- **추천 엔진**: [PostgreSQL / MySQL / MongoDB / TimescaleDB 등]

### 4.2 엔티티 관계도 (ERD)

```
[mermaid erDiagram 또는 텍스트 형태의 ERD]
```

### 4.3 엔티티 명세
#### [엔티티명]
| 속성 | 타입 | 설명 |
|------|------|------|
| [속성명] | [타입] | [설명] |

### 4.4 인덱싱 전략
[주요 쿼리 패턴에 따른 인덱스 전략]

---

## 5. API 명세 (API Specification)

### 5.1 공통 사항
- **Base URL**: `/api/v1`
- **인증 방식**: [JWT / OAuth / API Key 등]
- **공통 헤더**: [헤더 목록]
- **에러 처리**: [공통 에러 응답 형식]

### 5.2 엔드포인트 목록

| Method | Path | 설명 | 인증 | 관련 FR |
|--------|------|------|------|---------|
| [GET/POST/PUT/DELETE] | [경로] | [설명] | [필요/불필요] | [FR-xxx] |

### 5.3 상세 명세
[주요 API의 Request/Response 예시]

---

## 6. 보안 요구사항 (Security Requirements)

| 카테고리 | 요구사항 | 구현 방식 | 우선순위 |
|----------|---------|----------|---------|
| [인증/암호화/접근제어 등] | [요구사항] | [구현 방식] | HIGH/MEDIUM/LOW |

---

## 7. 성능 요구사항 (Performance Requirements)

| 메트릭 | 목표값 | 측정 방법 | 관련 컴포넌트 |
|--------|--------|----------|-------------|
| [응답시간/처리량/동시접속 등] | [수치] | [측정 도구/방법] | [컴포넌트] |

---

## 8. 인프라 요구사항 (Infrastructure Requirements)

| 카테고리 | 사양 | 수량 | 용도 |
|----------|------|------|------|
| [서버/네트워크/스토리지 등] | [사양] | [수량] | [용도] |

---

## 9. 기술 리스크 (Technical Risks)

| ID | 리스크 | 영향도 | 대응 방안 | 대안 (Contingency) |
|----|--------|--------|----------|-------------------|
| TR-001 | [리스크 설명] | HIGH/MEDIUM/LOW | [대응 방안] | [대안] |

---

## 10. 참고 문서

- 기반 PRD: [PRD 파일 경로]

---
*이 문서는 TRD 자동 생성 시스템에 의해 작성되었습니다.*
```

---

## 4단계: 파일 저장

생성한 TRD 문서를 다음 위치에 저장하세요:

1. **Markdown 파일**: `workspace/outputs/trd/TRD-[YYYYMMDD-HHMMSS].md`
2. **JSON 파일**: `workspace/outputs/trd/TRD-[YYYYMMDD-HHMMSS].json`

JSON 형식 (TRDDocument 모델 준수):
```json
{
  "id": "TRD-[YYYYMMDD-HHMMSS]",
  "title": "[프로젝트명] TRD",
  "executive_summary": "[기술 요약 2~3문단]",
  "technology_stack": [
    {
      "category": "Frontend",
      "technologies": ["React 18", "TypeScript", "Tailwind CSS"],
      "rationale": "[선정 사유]"
    },
    {
      "category": "Backend",
      "technologies": ["Python 3.11", "FastAPI"],
      "rationale": "[선정 사유]"
    }
  ],
  "system_architecture": {
    "overview": "[아키텍처 개요]",
    "architecture_style": "마이크로서비스 | 모놀리식 | 서버리스 | 에지-클라우드",
    "layers": [
      {
        "name": "[계층명]",
        "description": "[설명]",
        "components": [
          {
            "name": "[컴포넌트명]",
            "type": "[서비스/모듈/라이브러리]",
            "description": "[설명]",
            "responsibilities": ["[책임1]"],
            "dependencies": ["[의존성1]"],
            "interfaces": ["[인터페이스1]"]
          }
        ]
      }
    ],
    "data_flow": "[데이터 흐름 설명]",
    "deployment_diagram": "[배포 구성 설명]"
  },
  "database_design": {
    "database_type": "RDBMS | NoSQL | 시계열DB",
    "recommended_engine": "PostgreSQL",
    "entities": [
      {
        "name": "[엔티티명]",
        "description": "[설명]",
        "attributes": ["id: BIGINT PK", "name: VARCHAR(255)"],
        "primary_key": "id",
        "relationships": ["[관계 설명]"]
      }
    ],
    "indexing_strategy": "[인덱싱 전략]",
    "partitioning_strategy": "[파티셔닝 전략]"
  },
  "api_specification": {
    "base_url": "/api/v1",
    "authentication_method": "JWT | OAuth2 | API Key",
    "endpoints": [
      {
        "path": "/[resource]",
        "method": "GET",
        "description": "[설명]",
        "request_body": null,
        "response_body": "{...}",
        "authentication": true,
        "related_requirement_id": "FR-001"
      }
    ],
    "common_headers": {
      "Authorization": "Bearer {token}",
      "Content-Type": "application/json"
    },
    "error_handling": "[에러 처리 방식]"
  },
  "security_requirements": [
    {
      "category": "인증",
      "requirement": "[요구사항]",
      "implementation": "[구현 방식]",
      "priority": "HIGH"
    }
  ],
  "performance_requirements": [
    {
      "metric": "API 응답시간 (p95)",
      "target_value": "< 500ms",
      "measurement_method": "[측정 방법]",
      "related_component": "[관련 컴포넌트]"
    }
  ],
  "infrastructure_requirements": [
    {
      "category": "서버",
      "specification": "[사양]",
      "quantity": "2",
      "purpose": "[용도]",
      "estimated_cost": "[예상 비용]"
    }
  ],
  "technical_risks": [
    {
      "description": "[리스크 설명]",
      "level": "HIGH",
      "impact": "[영향]",
      "mitigation": "[대응 방안]",
      "contingency": "[대안]"
    }
  ],
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

1. **PRD 기반**: PRD의 요구사항을 기술적으로 구현하는 방법 제시
2. **도메인 적응**: 감지된 프로젝트 도메인에 맞는 기술 스택과 아키텍처 제안
3. **구체성**: 기술 버전, 스펙, 수치를 구체적으로 명시
4. **FR 추적**: API 엔드포인트와 FR을 related_requirement_id로 연결
5. **최신성**: 현재 널리 사용되는 안정적인 기술 스택 추천
6. **실용성**: 개발팀이 바로 구현할 수 있는 수준의 상세도

---

## 에러 처리

- **PRD 파일 없음**: "workspace/outputs/prd/ 폴더에 PRD 파일이 없습니다. /prd:prd-maker를 먼저 실행하세요." 표시 후 중단
- **PRD 파싱 실패**: JSON 파싱 실패 시 MD 파일로 폴백
- **불완전 PRD**: 가용한 정보로 TRD 작성 + technical_risks에 "PRD 정보 부족" 리스크 추가

---

## 파이프라인

```
[입력 파일] → PRD → TRD → WBS → Proposal → PPT
                    ^^^^
선행: PRD 생성 완료 필요 (/prd:prd-maker)
후속: /wbs:wbs-maker
대안: python -m app.scripts.trd_maker
```

이제 `workspace/outputs/prd/` 폴더에서 최신 PRD를 읽고 TRD 문서를 생성하세요.
