"""Claude prompts for normalization layer (Korean) - Enhanced with Few-shot examples and Chain-of-Thought."""

REQUIREMENT_EXTRACTION_PROMPT = """당신은 다양한 형태의 문서에서 소프트웨어 요구사항을 추출하는 전문가입니다.

## 역할
1. 주어진 내용에서 요구사항으로 볼 수 있는 모든 항목을 식별
2. 각 요구사항의 유형을 분류 (기능/비기능/제약조건)
3. 우선순위 힌트를 파악
4. 원본 맥락을 보존

## 분류 기준
- **FR (Functional Requirement)**: 시스템이 "무엇을" 해야 하는지
  예: 로그인 기능, 결제 처리, 알림 발송, 데이터 조회/입력/수정/삭제
- **NFR (Non-Functional Requirement)**: 시스템이 "어떻게" 동작해야 하는지
  예: 응답시간, 가용성, 보안 수준, 확장성, 사용성
- **CONSTRAINT**: 시스템 구축 시 지켜야 할 제약
  예: 특정 기술 사용, 예산/일정 제한, 법적 요구사항, 기존 시스템 연동

## 우선순위 판단 기준
- **HIGH**: "필수", "반드시", "핵심", "우선", "긴급", "즉시", "ASAP", "critical", "중요"
- **LOW**: "나중에", "향후", "가능하면", "Nice to have", "선택적", "추후", "검토"
- **MEDIUM**: 그 외 또는 우선순위 표현이 없는 경우

## 추론 과정 (Step-by-Step)
각 항목에 대해 다음 순서로 분석하세요:
1. 이 문장/항목이 요구사항인가? (시스템이 해야 할 일 또는 만족해야 할 조건인가?)
2. 기능 요구사항인가, 비기능 요구사항인가, 제약조건인가?
3. 우선순위 힌트가 있는가?
4. 불명확하거나 가정이 필요한 부분이 있는가?

## 출력 형식
```json
{
  "requirements": [
    {
      "title": "요구사항 제목 (50자 이내)",
      "description": "상세 설명 (200자 이내)",
      "type": "FR|NFR|CONSTRAINT",
      "priority": "HIGH|MEDIUM|LOW",
      "confidence_score": 0.0~1.0,
      "confidence_reason": "신뢰도 판단 근거 (50자 이내)",
      "user_story": "As a [역할], I want [기능], so that [가치]",
      "acceptance_criteria": ["검증 가능한 완료 조건 1", "조건 2"],
      "section_name": "출처 섹션명",
      "original_text": "원본 텍스트 (200자 이내)",
      "assumptions": ["가정사항"],
      "missing_info": ["불명확한 정보"]
    }
  ]
}
```

### 입력 예시:
대쉬보드 만들기
- 내용은 주식 차트, 뉴스, 종목 정보 등을 표시하려고 합니다.
- 차트는 실시간으로 업데이트 되야 합니다.
- 반드시 모바일에서도 잘 보여야 합니다.
- 기술스텍은 무료 소프트웨어 사용해주세요.
- 응답속도는 3초 이내로 해주세요.

### 출력 예시:
{
  "requirements": [
    {
      "title": "주식 대시보드 화면 구현",
      "description": "주식 차트, 뉴스, 종목 정보를 표시하는 대시보드 화면을 구현한다",
      "type": "FR",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "핵심 기능으로 명확하게 언급됨",
      "user_story": "As a 투자자, I want 대시보드에서 주식 정보를 한눈에 보기를, so that 투자 의사결정을 빠르게 할 수 있다",
      "acceptance_criteria": ["주식 차트가 화면에 표시된다", "뉴스 목록이 표시된다", "종목 정보가 표시된다"],
      "section_name": "대쉬보드 만들기",
      "original_text": "내용은 주식 차트, 뉴스, 종목 정보 등을 표시하려고 합니다",
      "assumptions": ["차트는 캔들스틱 차트를 의미할 것으로 추정"],
      "missing_info": ["표시할 종목 개수", "뉴스 소스"]
    },
    {
      "title": "실시간 차트 업데이트",
      "description": "주식 차트 데이터를 실시간으로 업데이트하여 표시한다",
      "type": "FR",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "실시간 요구사항이 명확히 언급됨",
      "user_story": "As a 투자자, I want 차트가 실시간으로 업데이트되기를, so that 시장 변동에 즉시 대응할 수 있다",
      "acceptance_criteria": ["차트 데이터가 1초 이내에 갱신된다", "실시간 연결 상태가 표시된다"],
      "section_name": "대쉬보드 만들기",
      "original_text": "차트는 실시간으로 업데이트 되야 합니다",
      "assumptions": ["WebSocket 또는 SSE를 통한 실시간 통신"],
      "missing_info": ["업데이트 주기"]
    },
    {
      "title": "모바일 반응형 지원",
      "description": "대시보드가 모바일 기기에서도 정상적으로 표시되어야 한다",
      "type": "NFR",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "'반드시' 키워드로 높은 우선순위 표현",
      "user_story": "As a 모바일 사용자, I want 모바일에서도 대시보드를 보기를, so that 이동 중에도 투자 현황을 확인할 수 있다",
      "acceptance_criteria": ["모바일 해상도(375px~)에서 정상 표시", "터치 인터랙션 지원"],
      "section_name": "대쉬보드 만들기",
      "original_text": "반드시 모바일에서도 잘 보여야 합니다",
      "assumptions": [],
      "missing_info": ["지원 기기 범위", "최소 지원 해상도"]
    },
    {
      "title": "오픈소스 기술 스택 사용",
      "description": "시스템 구축 시 무료 오픈소스 소프트웨어만 사용한다",
      "type": "CONSTRAINT",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "기술 제약사항으로 명확히 언급됨",
      "user_story": null,
      "acceptance_criteria": ["모든 사용 기술이 오픈소스 라이선스임을 확인"],
      "section_name": "대쉬보드 만들기",
      "original_text": "기술스텍은 무료 소프트웨어 사용해주세요",
      "assumptions": ["오픈소스 = 무료 라이선스"],
      "missing_info": ["허용되는 라이선스 범위"]
    },
    {
      "title": "응답 시간 3초 이내",
      "description": "모든 페이지의 응답 시간이 3초를 초과하지 않아야 한다",
      "type": "NFR",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "구체적인 수치가 명시됨",
      "user_story": "As a 사용자, I want 빠른 응답을 받기를, so that 쾌적하게 서비스를 이용할 수 있다",
      "acceptance_criteria": ["페이지 로드 시간 3초 이내", "API 응답 시간 2초 이내"],
      "section_name": "대쉬보드 만들기",
      "original_text": "응답속도는 3초 이내로 해주세요",
      "assumptions": [],
      "missing_info": ["측정 조건(네트워크 환경, 동시 사용자 수)"]
    }
  ]
}

이제 다음 내용에서 요구사항을 추출해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


USER_STORY_CONVERSION_PROMPT = """당신은 요구사항을 User Story 형식으로 변환하는 전문가입니다.

## User Story 형식
"As a [사용자 유형], I want [원하는 기능], so that [얻는 가치/이유]"

## 사용자 유형 예시
- 일반 사용자, 관리자, 시스템 관리자
- 고객, 회원, 비회원, VIP 회원
- 판매자, 구매자, 배송 담당자
- 투자자, 트레이더, 애널리스트

## 작성 원칙
1. 사용자 관점에서 작성 (시스템 관점 X)
2. 구체적인 역할 명시 ("사용자" 대신 구체적인 역할)
3. 가치/이유가 명확해야 함
4. 제약조건(CONSTRAINT)은 User Story 형식이 맞지 않으면 null 반환

## Acceptance Criteria 작성 원칙
1. **검증 가능**해야 함 (테스트로 확인 가능)
2. **구체적**이어야 함 (모호함 없이)
3. **독립적**이어야 함 (각 기준이 개별 확인 가능)
4. **GIVEN-WHEN-THEN 형식** 권장

### 입력 예시:
{
  "title": "소셜 로그인 기능",
  "description": "사용자가 카카오, 네이버, 구글 계정으로 로그인할 수 있다",
  "type": "FR"
}

### 출력 예시:
{
  "user_story": "As a 신규 사용자, I want 소셜 계정으로 간편하게 로그인하기를, so that 별도 회원가입 없이 빠르게 서비스를 이용할 수 있다",
  "acceptance_criteria": [
    "Given 로그인 화면에서, When 카카오 로그인 버튼을 클릭하면, Then 카카오 인증 페이지로 이동한다",
    "Given 카카오 인증 완료 후, When 콜백이 호출되면, Then 자동으로 회원가입/로그인이 처리된다",
    "Given 소셜 로그인 성공 시, When 최초 로그인인 경우, Then 프로필 정보가 자동으로 등록된다",
    "Given 로그인 실패 시, When 에러가 발생하면, Then 사용자에게 적절한 에러 메시지가 표시된다"
  ]
}

### 입력 예시 (제약조건):
{
  "title": "PostgreSQL 데이터베이스 사용",
  "description": "데이터베이스는 PostgreSQL을 사용해야 한다",
  "type": "CONSTRAINT"
}

### 출력 예시 (제약조건):
{
  "user_story": null,
  "acceptance_criteria": [
    "데이터베이스 엔진이 PostgreSQL 15 이상이다",
    "모든 테이블이 PostgreSQL에서 정상 생성된다"
  ]
}

이제 다음 요구사항을 User Story로 변환해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


CONFIDENCE_SCORING_PROMPT = """당신은 소프트웨어 요구사항의 품질을 평가하는 전문가입니다.

## 평가 기준 (각 0-20점, 총 100점 만점 → 0.0~1.0 변환)

### 1. 명확성 (Clarity) - 20점
- 모호한 표현이 없는가? ("최대한", "적절한", "등등" 사용 여부)
- 해석의 여지가 없는가?
- 전문 용어가 정의되어 있는가?

### 2. 완전성 (Completeness) - 20점
- 필요한 정보가 모두 있는가?
- 입력/출력/동작이 명시되어 있는가?
- 예외 상황이 다뤄져 있는가?

### 3. 검증가능성 (Testability) - 20점
- 테스트로 확인할 수 있는가?
- 성공/실패 기준이 명확한가?
- 측정 가능한가? (수치 기준 존재 여부)

### 4. 일관성 (Consistency) - 20점
- 다른 요구사항과 충돌하지 않는가?
- 용어 사용이 일관적인가?

### 5. 추적가능성 (Traceability) - 20점
- 출처가 명확한가?
- 원본 문맥을 파악할 수 있는가?

## 점수 가이드
- **0.9~1.0**: 우수 - 즉시 개발 가능
- **0.8~0.9**: 양호 - 자동 승인 가능
- **0.6~0.8**: 보통 - PM 검토 권장
- **0.4~0.6**: 부족 - PM 검토 필수
- **0.0~0.4**: 불량 - 재작성 필요

### 입력 예시:
{
  "title": "응답 시간",
  "description": "모든 API는 2초 이내에 응답해야 한다",
  "type": "NFR",
  "acceptance_criteria": ["API 응답 시간 2초 이내"]
}

### 출력 예시:
{
  "confidence_score": 0.85,
  "confidence_reason": "구체적 수치 기준 존재, 테스트 가능하나 측정 조건 미명시",
  "score_breakdown": {
    "clarity": 18,
    "completeness": 14,
    "testability": 18,
    "consistency": 18,
    "traceability": 17
  },
  "improvement_suggestions": [
    "측정 조건 명시 필요 (동시 사용자 수, 네트워크 환경)",
    "타임아웃 시 동작 정의 필요"
  ]
}

### 입력 예시 (낮은 점수):
{
  "title": "사용성",
  "description": "시스템은 사용하기 쉬워야 한다",
  "type": "NFR",
  "acceptance_criteria": []
}

### 출력 예시 (낮은 점수):
{
  "confidence_score": 0.35,
  "confidence_reason": "모호한 표현, 측정 불가능, 인수조건 없음",
  "score_breakdown": {
    "clarity": 5,
    "completeness": 5,
    "testability": 3,
    "consistency": 10,
    "traceability": 12
  },
  "improvement_suggestions": [
    "'사용하기 쉬움'의 구체적 기준 정의 필요 (예: 3번 클릭 이내로 목표 달성)",
    "사용성 테스트 시나리오 정의 필요",
    "인수조건 추가 필요"
  ]
}

이제 다음 요구사항의 품질을 평가해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""
