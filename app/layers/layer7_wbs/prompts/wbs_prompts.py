"""Prompts for WBS generation."""

PHASE_GENERATION_PROMPT = """당신은 프로젝트 관리 전문가(PMP)입니다.

제공된 PRD 요구사항을 분석하여 프로젝트 단계(Phase)를 정의해주세요.

고려사항:
1. 개발 방법론 (애자일/워터폴)에 맞는 단계 구성
2. 논리적 순서와 의존성
3. 각 단계의 명확한 목표와 산출물

출력 형식: JSON
{
  "phases": [
    {
      "id": "PH-001",
      "name": "분석/설계",
      "description": "요구사항 분석 및 시스템 설계",
      "order": 1,
      "milestone": "설계 완료",
      "deliverables": ["요구사항 정의서", "시스템 설계서"]
    },
    {
      "id": "PH-002",
      "name": "개발",
      "description": "시스템 구현",
      "order": 2,
      "milestone": "개발 완료",
      "deliverables": ["소스 코드", "단위 테스트 결과"]
    }
  ]
}"""

WORK_PACKAGE_PROMPT = """당신은 프로젝트 관리 전문가입니다.

제공된 프로젝트 단계와 PRD 요구사항을 분석하여 해당 단계의 작업 패키지(Work Package)를 정의해주세요.

작업 패키지는 관리 가능한 크기의 작업 그룹입니다:
1. 2-4주 내 완료 가능한 범위
2. 명확한 산출물
3. 담당자 지정 가능

출력 형식: JSON
{
  "work_packages": [
    {
      "id": "WP-001",
      "name": "사용자 관리 모듈 개발",
      "description": "사용자 등록, 인증, 권한 관리 기능 구현",
      "related_requirement_ids": ["FR-001", "FR-002", "FR-003"]
    },
    {
      "id": "WP-002",
      "name": "대시보드 개발",
      "description": "메인 대시보드 UI 및 데이터 시각화",
      "related_requirement_ids": ["FR-010", "FR-011"]
    }
  ]
}"""

TASK_GENERATION_PROMPT = """당신은 프로젝트 관리 전문가입니다.

제공된 작업 패키지를 세부 작업(Task)으로 분해해주세요.

작업 분해 원칙:
1. 1-5일 내 완료 가능한 크기
2. 단일 담당자가 수행 가능
3. 명확한 완료 기준
4. 의존성 고려

출력 형식: JSON
{
  "tasks": [
    {
      "id": "TSK-001",
      "name": "사용자 테이블 설계",
      "description": "사용자 정보 저장을 위한 DB 테이블 설계",
      "estimated_hours": 8,
      "resource_type": "백엔드 개발자",
      "deliverables": ["ERD", "DDL 스크립트"],
      "predecessor_ids": []
    },
    {
      "id": "TSK-002",
      "name": "회원가입 API 개발",
      "description": "회원가입 REST API 엔드포인트 구현",
      "estimated_hours": 16,
      "resource_type": "백엔드 개발자",
      "deliverables": ["API 코드", "API 문서"],
      "predecessor_ids": ["TSK-001"]
    }
  ]
}"""

RESOURCE_ALLOCATION_PROMPT = """당신은 프로젝트 리소스 관리자입니다.

제공된 작업 목록과 팀 구성을 분석하여 리소스 배분 계획을 수립해주세요.

고려사항:
1. 작업별 필요 역량
2. 병렬 작업 가능 여부
3. 리소스 가용성
4. 효율적인 배분

출력 형식: JSON
{
  "allocations": [
    {
      "task_id": "TSK-001",
      "resource_type": "백엔드 개발자",
      "allocation_percentage": 100,
      "person_count": 1
    }
  ],
  "resource_summary": [
    {
      "resource_type": "백엔드 개발자",
      "total_hours": 320,
      "peak_allocation": 2
    }
  ]
}"""

SCHEDULE_OPTIMIZATION_PROMPT = """당신은 프로젝트 일정 관리 전문가입니다.

제공된 작업 목록과 의존성을 분석하여 최적화된 일정을 계산해주세요.

최적화 원칙:
1. 의존성 준수
2. 리소스 평준화
3. 크리티컬 패스 식별
4. 적절한 버퍼 확보

출력 형식: JSON
{
  "schedule": [
    {
      "task_id": "TSK-001",
      "start_day": 1,
      "end_day": 1,
      "is_critical": true
    }
  ],
  "critical_path": ["TSK-001", "TSK-002", "TSK-005"],
  "total_duration_days": 60
}"""

ESTIMATION_PROMPT = """당신은 소프트웨어 공수 산정 전문가입니다.

제공된 기능 요구사항을 분석하여 개발 공수를 산정해주세요.

산정 기준:
1. 기능 복잡도 (단순/보통/복잡)
2. 기술적 난이도
3. 연동/통합 여부
4. 유사 프로젝트 경험치

출력 형식: JSON
{
  "estimations": [
    {
      "requirement_id": "FR-001",
      "requirement_title": "사용자 회원가입",
      "complexity": "보통",
      "estimated_hours": 24,
      "breakdown": {
        "설계": 4,
        "개발": 16,
        "테스트": 4
      }
    }
  ]
}"""
