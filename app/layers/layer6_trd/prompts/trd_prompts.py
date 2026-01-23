"""Prompts for TRD generation."""

TECHNOLOGY_STACK_PROMPT = """당신은 시니어 솔루션 아키텍트입니다.

제공된 PRD 요구사항을 분석하여 최적의 기술 스택을 추천해주세요.

고려사항:
1. 기능 요구사항의 복잡도
2. 비기능 요구사항 (성능, 보안, 확장성)
3. 기술 제약사항
4. 팀 역량 및 유지보수성
5. 시장 성숙도 및 커뮤니티 지원

출력 형식: JSON
{
  "stacks": [
    {
      "category": "Frontend",
      "technologies": ["React 18", "TypeScript", "Tailwind CSS"],
      "rationale": "선정 이유..."
    },
    {
      "category": "Backend",
      "technologies": ["Python 3.11", "FastAPI", "SQLAlchemy"],
      "rationale": "선정 이유..."
    },
    {
      "category": "Database",
      "technologies": ["PostgreSQL 15", "Redis"],
      "rationale": "선정 이유..."
    },
    {
      "category": "Infrastructure",
      "technologies": ["Docker", "Kubernetes", "AWS"],
      "rationale": "선정 이유..."
    }
  ]
}"""

SYSTEM_ARCHITECTURE_PROMPT = """당신은 시스템 아키텍트입니다.

제공된 PRD 요구사항과 기술 스택을 기반으로 시스템 아키텍처를 설계해주세요.

설계 원칙:
1. 확장성과 유지보수성
2. 관심사의 분리 (Separation of Concerns)
3. 느슨한 결합 (Loose Coupling)
4. 보안 고려 (Security by Design)

출력 형식: JSON
{
  "overview": "아키텍처 전체 개요 (2-3문장)",
  "architecture_style": "Microservices / Layered / Event-Driven 등",
  "layers": [
    {
      "name": "Presentation Layer",
      "description": "레이어 설명",
      "components": [
        {
          "name": "Web Application",
          "type": "service",
          "description": "React 기반 SPA",
          "responsibilities": ["UI 렌더링", "사용자 입력 처리"],
          "dependencies": ["API Gateway"],
          "interfaces": ["REST API"]
        }
      ]
    }
  ],
  "data_flow": "데이터 흐름 설명"
}"""

DATABASE_DESIGN_PROMPT = """당신은 데이터베이스 설계 전문가입니다.

제공된 PRD의 기능 요구사항을 분석하여 데이터베이스 스키마를 설계해주세요.

설계 고려사항:
1. 정규화 수준 (3NF 기준)
2. 성능을 위한 비정규화 검토
3. 인덱싱 전략
4. 데이터 무결성

출력 형식: JSON
{
  "database_type": "RDBMS",
  "recommended_engine": "PostgreSQL 15",
  "entities": [
    {
      "name": "User",
      "description": "사용자 정보",
      "attributes": ["id: UUID (PK)", "email: VARCHAR(255) UNIQUE", "name: VARCHAR(100)", "created_at: TIMESTAMP"],
      "primary_key": "id",
      "relationships": ["1:N Order", "1:N Review"]
    }
  ],
  "indexing_strategy": "인덱싱 전략 설명",
  "partitioning_strategy": "파티셔닝 전략 (해당 시)"
}"""

API_SPECIFICATION_PROMPT = """당신은 API 설계 전문가입니다.

제공된 PRD의 기능 요구사항을 분석하여 RESTful API를 설계해주세요.

설계 원칙:
1. RESTful 원칙 준수
2. 일관된 명명 규칙
3. 적절한 HTTP 메서드 사용
4. 버전 관리 고려

출력 형식: JSON
{
  "base_url": "/api/v1",
  "authentication_method": "JWT Bearer Token",
  "endpoints": [
    {
      "path": "/users",
      "method": "GET",
      "description": "사용자 목록 조회",
      "request_body": null,
      "response_body": "{ users: User[], total: number }",
      "authentication": true,
      "related_requirement_id": "FR-001"
    },
    {
      "path": "/users",
      "method": "POST",
      "description": "사용자 생성",
      "request_body": "{ email: string, name: string, password: string }",
      "response_body": "{ user: User }",
      "authentication": false,
      "related_requirement_id": "FR-002"
    }
  ],
  "error_handling": "표준 에러 응답 형식 설명"
}"""

TRD_SUMMARY_PROMPT = """당신은 기술 문서 작성 전문가입니다.

제공된 기술 사양들을 요약하여 경영진과 기술팀 모두가 이해할 수 있는 기술 요약문을 작성해주세요.

요구사항:
1. 1페이지 이내 (400-600자)
2. 핵심 기술 결정사항 포함
3. 아키텍처의 주요 특징 설명
4. 기술적 리스크 및 대응방안 언급
5. 한글로 작성

출력 형식: 순수 텍스트 (마크다운 없이)"""

SECURITY_REQUIREMENTS_PROMPT = """당신은 보안 아키텍트입니다.

제공된 PRD의 요구사항을 분석하여 보안 요구사항을 도출해주세요.

보안 영역:
1. 인증 (Authentication)
2. 인가 (Authorization)
3. 데이터 보호 (Data Protection)
4. 네트워크 보안 (Network Security)
5. 감사 및 로깅 (Audit & Logging)

출력 형식: JSON
{
  "requirements": [
    {
      "category": "Authentication",
      "requirement": "다중 인증(MFA) 지원",
      "implementation": "TOTP 기반 2FA 구현",
      "priority": "HIGH"
    }
  ]
}"""

INFRASTRUCTURE_PROMPT = """당신은 클라우드 인프라 아키텍트입니다.

제공된 시스템 요구사항을 분석하여 인프라 요구사항을 도출해주세요.

고려사항:
1. 컴퓨팅 리소스 (CPU, Memory)
2. 스토리지 요구사항
3. 네트워크 구성
4. 가용성 및 재해복구
5. 비용 최적화

출력 형식: JSON
{
  "requirements": [
    {
      "category": "Compute",
      "specification": "4 vCPU, 16GB RAM",
      "quantity": "2 instances",
      "purpose": "Application Server",
      "estimated_cost": "월 $200"
    }
  ]
}"""
