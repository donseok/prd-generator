"""Prompts for WBS generation - Enhanced with Few-shot examples and batch processing support."""

PHASE_GENERATION_PROMPT = """당신은 프로젝트 관리 전문가(PMP)입니다.

제공된 PRD 요구사항을 분석하여 프로젝트 단계(Phase)를 정의해주세요.

## 고려사항
1. 개발 방법론 (애자일/워터폴)에 맞는 단계 구성
2. 논리적 순서와 의존성
3. 각 단계의 명확한 목표와 산출물

## 방법론별 단계 가이드
- **애자일**: 스프린트 기반, 반복적 개발 (분석/설계 → MVP 개발 → 기능 확장 → 안정화)
- **워터폴**: 순차적 단계 (요구사항 분석 → 설계 → 개발 → 테스트 → 배포)
- **하이브리드**: 초기 분석/설계는 워터폴, 개발은 애자일 방식

### 입력 예시:
프로젝트: 주식 대시보드 시스템
기능 요구사항 수: 15개
비기능 요구사항 수: 5개
방법론: 애자일
총 기간: 6개월

### 출력 예시:
{
  "phases": [
    {
      "id": "PH-001",
      "name": "프로젝트 준비 및 설계",
      "description": "요구사항 상세화, 아키텍처 설계, 개발 환경 구축",
      "order": 1,
      "duration_weeks": 4,
      "milestone": "설계 완료 및 개발 환경 준비",
      "deliverables": ["요구사항 명세서", "시스템 설계서", "개발 환경", "코딩 표준"]
    },
    {
      "id": "PH-002",
      "name": "MVP 개발 (Sprint 1-4)",
      "description": "핵심 기능 개발: 사용자 인증, 실시간 시세, 기본 차트",
      "order": 2,
      "duration_weeks": 8,
      "milestone": "MVP 릴리스",
      "deliverables": ["로그인/회원가입", "실시간 시세 조회", "기본 차트 표시", "API 문서"]
    },
    {
      "id": "PH-003",
      "name": "기능 확장 (Sprint 5-8)",
      "description": "부가 기능 개발: 관심종목, 알림, 뉴스 피드",
      "order": 3,
      "duration_weeks": 8,
      "milestone": "전체 기능 완료",
      "deliverables": ["관심종목 관리", "가격 알림", "뉴스 피드", "모바일 반응형"]
    },
    {
      "id": "PH-004",
      "name": "안정화 및 배포",
      "description": "통합 테스트, 성능 최적화, 운영 환경 배포",
      "order": 4,
      "duration_weeks": 4,
      "milestone": "서비스 오픈",
      "deliverables": ["테스트 보고서", "성능 테스트 결과", "운영 매뉴얼", "배포 완료"]
    }
  ]
}"""


WORK_PACKAGE_PROMPT = """당신은 프로젝트 관리 전문가입니다.

제공된 프로젝트 단계와 PRD 요구사항을 분석하여 해당 단계의 작업 패키지(Work Package)를 정의해주세요.

## 작업 패키지 기준
1. 2-4주 내 완료 가능한 범위
2. 명확한 산출물
3. 담당자 지정 가능
4. 독립적으로 관리 가능한 단위

## 작업 패키지 유형
- **개발**: 기능 구현, API 개발, UI 개발
- **설계**: 아키텍처, DB, UI/UX 설계
- **인프라**: 환경 구축, 배포, 모니터링
- **품질**: 테스트, 코드 리뷰, 성능 최적화

### 입력 예시:
단계: MVP 개발 (8주)
관련 기능: 사용자 인증, 실시간 시세, 기본 차트

### 출력 예시:
{
  "work_packages": [
    {
      "id": "WP-001",
      "name": "사용자 인증 모듈 개발",
      "description": "회원가입, 로그인, JWT 토큰 관리 기능 구현",
      "duration_weeks": 2,
      "related_requirement_ids": ["FR-001", "FR-002", "NFR-001"],
      "deliverables": ["사용자 API", "인증 미들웨어", "단위 테스트"]
    },
    {
      "id": "WP-002",
      "name": "실시간 시세 연동",
      "description": "외부 API 연동 및 WebSocket 기반 실시간 데이터 처리",
      "duration_weeks": 3,
      "related_requirement_ids": ["FR-003", "FR-004", "NFR-002"],
      "deliverables": ["시세 API", "WebSocket 서버", "캐싱 로직"]
    },
    {
      "id": "WP-003",
      "name": "차트 컴포넌트 개발",
      "description": "캔들스틱 차트, 라인 차트, 지표 표시 구현",
      "duration_weeks": 3,
      "related_requirement_ids": ["FR-005", "FR-006"],
      "deliverables": ["차트 컴포넌트", "차트 설정 UI", "데이터 바인딩"]
    }
  ]
}"""


TASK_GENERATION_PROMPT = """당신은 프로젝트 관리 전문가입니다.

제공된 작업 패키지들을 세부 작업(Task)으로 분해해주세요.

## 작업 분해 원칙
1. 1-5일 내 완료 가능한 크기 (8-40시간)
2. 단일 담당자가 수행 가능
3. 명확한 완료 기준
4. 의존성 고려

## 작업 유형별 예상 시간
- DB 테이블 설계: 4-8시간
- API 엔드포인트 개발: 8-16시간
- UI 컴포넌트 개발: 8-24시간
- 단위 테스트 작성: 4-8시간
- 통합 테스트: 8-16시간
- 문서 작성: 4-8시간

## 배치 처리 안내
여러 작업 패키지가 입력되면, 각 패키지별로 Task를 생성하여 하나의 JSON으로 반환하세요.

### 입력 예시:
작업 패키지 목록:
1. WP-001: 사용자 인증 모듈 개발
2. WP-002: 실시간 시세 연동

### 출력 예시:
{
  "tasks": [
    {
      "id": "TSK-001",
      "work_package_id": "WP-001",
      "name": "사용자 DB 테이블 설계",
      "description": "users, sessions 테이블 DDL 작성",
      "estimated_hours": 8,
      "resource_type": "백엔드 개발자",
      "deliverables": ["DDL 스크립트", "ERD"],
      "predecessor_ids": []
    },
    {
      "id": "TSK-002",
      "work_package_id": "WP-001",
      "name": "회원가입 API 개발",
      "description": "POST /auth/signup 엔드포인트 구현",
      "estimated_hours": 16,
      "resource_type": "백엔드 개발자",
      "deliverables": ["API 코드", "Swagger 문서"],
      "predecessor_ids": ["TSK-001"]
    },
    {
      "id": "TSK-003",
      "work_package_id": "WP-001",
      "name": "로그인 API 개발",
      "description": "POST /auth/login, JWT 발급 로직 구현",
      "estimated_hours": 16,
      "resource_type": "백엔드 개발자",
      "deliverables": ["API 코드", "토큰 관리 로직"],
      "predecessor_ids": ["TSK-001"]
    },
    {
      "id": "TSK-004",
      "work_package_id": "WP-001",
      "name": "인증 단위 테스트",
      "description": "회원가입, 로그인 API 테스트 코드 작성",
      "estimated_hours": 8,
      "resource_type": "백엔드 개발자",
      "deliverables": ["테스트 코드", "테스트 리포트"],
      "predecessor_ids": ["TSK-002", "TSK-003"]
    },
    {
      "id": "TSK-005",
      "work_package_id": "WP-002",
      "name": "외부 시세 API 연동 모듈",
      "description": "한국투자증권/야후 파이낸스 API 클라이언트 구현",
      "estimated_hours": 16,
      "resource_type": "백엔드 개발자",
      "deliverables": ["API 클라이언트", "에러 핸들링"],
      "predecessor_ids": []
    },
    {
      "id": "TSK-006",
      "work_package_id": "WP-002",
      "name": "WebSocket 서버 구현",
      "description": "실시간 시세 푸시를 위한 WebSocket 엔드포인트",
      "estimated_hours": 24,
      "resource_type": "백엔드 개발자",
      "deliverables": ["WebSocket 서버", "연결 관리 로직"],
      "predecessor_ids": ["TSK-005"]
    },
    {
      "id": "TSK-007",
      "work_package_id": "WP-002",
      "name": "Redis 캐싱 레이어",
      "description": "시세 데이터 캐싱 및 Pub/Sub 설정",
      "estimated_hours": 12,
      "resource_type": "백엔드 개발자",
      "deliverables": ["캐싱 로직", "Pub/Sub 구성"],
      "predecessor_ids": ["TSK-005"]
    }
  ]
}"""


RESOURCE_ALLOCATION_PROMPT = """당신은 프로젝트 리소스 관리자입니다.

제공된 작업 목록과 팀 구성을 분석하여 리소스 배분 계획을 수립해주세요.

## 고려사항
1. 작업별 필요 역량 (프론트엔드, 백엔드, 디자인, QA)
2. 병렬 작업 가능 여부
3. 리소스 가용성 (할당률 80% 권장, 100% 초과 금지)
4. 효율적인 배분 (한 사람이 유사 작업 연속 수행)

## 역할별 작업 유형
- **프론트엔드 개발자**: UI 컴포넌트, 화면 개발, 상태 관리
- **백엔드 개발자**: API, DB, 비즈니스 로직, 인프라
- **UI/UX 디자이너**: 와이어프레임, UI 디자인, 프로토타입
- **QA 엔지니어**: 테스트 계획, 테스트 실행, 버그 관리

### 입력 예시:
작업 목록:
- TSK-001: 사용자 DB 설계 (8h) - 백엔드
- TSK-002: 회원가입 API (16h) - 백엔드
- TSK-003: 로그인 화면 UI (12h) - 프론트엔드

팀 구성:
- 백엔드 개발자: 2명
- 프론트엔드 개발자: 1명

### 출력 예시:
{
  "allocations": [
    {
      "task_id": "TSK-001",
      "resource_type": "백엔드 개발자",
      "allocation_percentage": 100,
      "person_count": 1,
      "assigned_role": "Backend Dev #1"
    },
    {
      "task_id": "TSK-002",
      "resource_type": "백엔드 개발자",
      "allocation_percentage": 100,
      "person_count": 1,
      "assigned_role": "Backend Dev #1"
    },
    {
      "task_id": "TSK-003",
      "resource_type": "프론트엔드 개발자",
      "allocation_percentage": 100,
      "person_count": 1,
      "assigned_role": "Frontend Dev #1"
    }
  ],
  "resource_summary": [
    {
      "resource_type": "백엔드 개발자",
      "total_hours": 24,
      "total_days": 3,
      "peak_allocation": 1,
      "utilization": "75%"
    },
    {
      "resource_type": "프론트엔드 개발자",
      "total_hours": 12,
      "total_days": 1.5,
      "peak_allocation": 1,
      "utilization": "50%"
    }
  ],
  "bottlenecks": [],
  "recommendations": [
    "백엔드 개발자 2명 중 1명은 여유가 있어 추가 작업 할당 가능"
  ]
}"""


SCHEDULE_OPTIMIZATION_PROMPT = """당신은 프로젝트 일정 관리 전문가입니다.

제공된 작업 목록과 의존성을 분석하여 최적화된 일정을 계산해주세요.

## 최적화 원칙
1. 의존성 준수 (선행 작업 완료 후 후행 작업 시작)
2. 리소스 평준화 (특정 시기에 과부하 방지)
3. 크리티컬 패스 식별 (일정 지연 위험 경로)
4. 적절한 버퍼 확보 (10-20% 여유)

## 의존성 타입
- FS (Finish-to-Start): A 완료 후 B 시작 (기본)
- SS (Start-to-Start): A 시작 후 B 시작 가능
- FF (Finish-to-Finish): A 완료 시 B도 완료

### 입력 예시:
작업 목록:
- TSK-001: DB 설계 (8h), 선행작업 없음
- TSK-002: 회원가입 API (16h), 선행: TSK-001
- TSK-003: 로그인 API (16h), 선행: TSK-001
- TSK-004: 인증 테스트 (8h), 선행: TSK-002, TSK-003

일 8시간 기준

### 출력 예시:
{
  "schedule": [
    {
      "task_id": "TSK-001",
      "start_day": 1,
      "end_day": 1,
      "duration_days": 1,
      "is_critical": true,
      "slack_days": 0
    },
    {
      "task_id": "TSK-002",
      "start_day": 2,
      "end_day": 3,
      "duration_days": 2,
      "is_critical": true,
      "slack_days": 0
    },
    {
      "task_id": "TSK-003",
      "start_day": 2,
      "end_day": 3,
      "duration_days": 2,
      "is_critical": true,
      "slack_days": 0,
      "parallel_with": ["TSK-002"]
    },
    {
      "task_id": "TSK-004",
      "start_day": 4,
      "end_day": 4,
      "duration_days": 1,
      "is_critical": true,
      "slack_days": 0
    }
  ],
  "critical_path": ["TSK-001", "TSK-002", "TSK-004"],
  "total_duration_days": 4,
  "parallel_opportunities": [
    "TSK-002와 TSK-003은 동시 진행 가능 (같은 선행작업)"
  ],
  "risks": [
    "크리티컬 패스에 여유(slack)가 없어 지연 시 전체 일정에 영향"
  ]
}"""


ESTIMATION_PROMPT = """당신은 소프트웨어 공수 산정 전문가입니다.

제공된 기능 요구사항을 분석하여 개발 공수를 산정해주세요.

## 산정 기준
1. 기능 복잡도: 단순(8h) / 보통(16-24h) / 복잡(32-40h)
2. 기술적 난이도: 익숙한 기술(1.0x) / 학습 필요(1.3x) / 신기술(1.5x)
3. 연동/통합: 단독(1.0x) / 내부 연동(1.2x) / 외부 연동(1.5x)
4. 버퍼: 복잡도에 따라 10-20% 추가

## 복잡도 기준
- **단순**: CRUD 기본 기능, 단순 조회, 기본 UI
- **보통**: 비즈니스 로직 포함, 다중 테이블 연동, 상태 관리
- **복잡**: 실시간 처리, 외부 시스템 연동, 복잡한 알고리즘

## 배치 처리
여러 요구사항이 입력되면 각각에 대해 산정하여 하나의 JSON으로 반환하세요.

### 입력 예시:
요구사항 목록:
1. FR-001: 사용자 회원가입 (이메일/비밀번호 기반)
2. FR-002: 실시간 주식 시세 조회 (외부 API 연동)
3. FR-003: 가격 알림 설정 (조건 기반 푸시)

### 출력 예시:
{
  "estimations": [
    {
      "requirement_id": "FR-001",
      "requirement_title": "사용자 회원가입",
      "complexity": "보통",
      "tech_difficulty": 1.0,
      "integration_factor": 1.0,
      "base_hours": 24,
      "adjusted_hours": 24,
      "buffer_hours": 4,
      "total_hours": 28,
      "breakdown": {
        "설계": 4,
        "백엔드 개발": 12,
        "프론트엔드 개발": 8,
        "테스트": 4
      },
      "assumptions": ["소셜 로그인 미포함", "이메일 인증 포함"],
      "risks": []
    },
    {
      "requirement_id": "FR-002",
      "requirement_title": "실시간 주식 시세 조회",
      "complexity": "복잡",
      "tech_difficulty": 1.3,
      "integration_factor": 1.5,
      "base_hours": 40,
      "adjusted_hours": 78,
      "buffer_hours": 12,
      "total_hours": 90,
      "breakdown": {
        "설계": 8,
        "백엔드 개발": 40,
        "프론트엔드 개발": 24,
        "테스트": 18
      },
      "assumptions": ["외부 API 무료 플랜 사용", "WebSocket 구현"],
      "risks": ["외부 API 응답 지연 가능성", "API 호출 제한 대응 필요"]
    },
    {
      "requirement_id": "FR-003",
      "requirement_title": "가격 알림 설정",
      "complexity": "보통",
      "tech_difficulty": 1.2,
      "integration_factor": 1.2,
      "base_hours": 24,
      "adjusted_hours": 35,
      "buffer_hours": 5,
      "total_hours": 40,
      "breakdown": {
        "설계": 4,
        "백엔드 개발": 16,
        "프론트엔드 개발": 12,
        "테스트": 8
      },
      "assumptions": ["이메일/푸시 알림 지원", "알림 이력 저장"],
      "risks": ["푸시 알림 서비스 선정 필요"]
    }
  ],
  "summary": {
    "total_requirements": 3,
    "total_hours": 158,
    "total_man_days": 19.75,
    "complexity_distribution": {
      "단순": 0,
      "보통": 2,
      "복잡": 1
    }
  }
}"""
