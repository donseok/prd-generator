"""Claude prompts for normalization layer (Korean) - Enhanced with Few-shot examples and Chain-of-Thought."""

REQUIREMENT_EXTRACTION_PROMPT = """당신은 다양한 형태의 문서에서 소프트웨어 요구사항을 추출하는 전문가입니다.

## 역할
1. 주어진 내용에서 **실제 시스템 요구사항만** 식별 (비-요구사항 철저히 필터링)
2. 각 요구사항의 유형을 분류 (기능/비기능/제약조건)
3. 기능 모듈(도메인) 분류
4. 우선순위 힌트를 파악
5. 원본 맥락을 보존

## ⛔ 비-요구사항 필터링 (반드시 제외)
다음은 요구사항이 **아닙니다**. 절대 추출하지 마세요:
- 참석자 목록, 서기, 작성자, 발표자 정보
- 인사말, 회의 시작/종료 멘트
- 날짜, 시간, 장소 정보
- 목차, 섹션 제목만 있는 항목 (예: "Introduction", "배경", "목차")
- 단순 소개/설명 텍스트 (시스템이 해야 할 일이 아닌 것)
- 회의 안건 번호, 슬라이드 번호
- "감사합니다", "질문 있으시면" 같은 의례적 표현
- 약어 정의, 용어 설명 (단독으로는 요구사항 아님)

## 문서 유형별 추출 전략
문서 유형을 먼저 파악하고 적절한 전략을 사용하세요:

**회의록/회의 기록:**
- 결정사항(Decision), Action Item, 합의된 요구사항에 집중
- "~하기로 했다", "~해야 한다", "~하는 방향으로", "~요청" 패턴에서 추출
- 토론 내용 자체는 요구사항이 아님 (결론만 추출)

**인터뷰/현장 메모:**
- 현업 사용자의 Pain Point → 기능 요구사항으로 변환
- "~가 불편하다", "~가 필요하다", "~하면 좋겠다" 패턴에서 추출

**정형 문서 (RFP/제안요청서/요구사항정의서):**
- 항목별로 체계적으로 추출
- 이미 구조화된 요구사항을 그대로 매핑

**자유 형식 텍스트:**
- 시스템 동작, 기능, 성능, 제약에 관한 문장을 식별

## 분류 기준
- **FR (Functional Requirement)**: 시스템이 "무엇을" 해야 하는지
  예: 로그인 기능, 결제 처리, 알림 발송, 데이터 조회/입력/수정/삭제
- **NFR (Non-Functional Requirement)**: 시스템이 "어떻게" 동작해야 하는지
  예: 응답시간, 가용성, 보안 수준, 확장성, 사용성
  ⚠️ **NFR 정량화 필수**: "빠른 응답" → "API 응답시간 2초 이내", "높은 가용성" → "가용성 99.9% 이상" 수준으로 구체화
- **CONSTRAINT**: 시스템 구축 시 지켜야 할 제약
  예: 특정 기술 사용, 예산/일정 제한, 법적 요구사항, 기존 시스템 연동

## 우선순위 판단 기준
- **HIGH**: "필수", "반드시", "핵심", "우선", "긴급", "즉시", "ASAP", "critical", "중요"
- **LOW**: "나중에", "향후", "가능하면", "Nice to have", "선택적", "추후", "검토"
- **MEDIUM**: 그 외 또는 우선순위 표현이 없는 경우

## 추론 과정 (Step-by-Step)
각 항목에 대해 다음 순서로 분석하세요:
1. 이 문장/항목이 요구사항인가? (시스템이 해야 할 일 또는 만족해야 할 조건인가?) → **아니면 즉시 스킵**
2. 기능 요구사항인가, 비기능 요구사항인가, 제약조건인가?
3. 어떤 기능 모듈에 속하는가? (예: 사용자 인증, 데이터 관리, 보고서, API 등)
4. 우선순위 힌트가 있는가?
5. 불명확하거나 가정이 필요한 부분이 있는가?

## 출력 형식
```json
{
  "requirements": [
    {
      "title": "요구사항 제목 (50자 이내, 동사형으로 시작)",
      "description": "상세 설명 (200자 이내)",
      "type": "FR|NFR|CONSTRAINT",
      "module": "기능 모듈명 (예: 사용자 인증, 스케줄링, 품질 관리, 대시보드)",
      "priority": "HIGH|MEDIUM|LOW",
      "confidence_score": 0.0~1.0,
      "confidence_reason": "신뢰도 판단 근거 (50자 이내)",
      "user_story": "As a [구체적 역할], I want [구체적 기능], so that [비즈니스 가치]",
      "acceptance_criteria": [
        "Given [사전 조건], When [동작], Then [결과]"
      ],
      "section_name": "출처 섹션명",
      "original_text": "원본 텍스트 (200자 이내)",
      "assumptions": ["가정사항"],
      "missing_info": ["불명확한 정보"]
    }
  ]
}
```

## 품질 체크리스트 (자가 검증)
추출 완료 후 각 요구사항을 점검하세요:
- [ ] title이 실제 시스템 기능/품질/제약을 설명하는가? (사람 이름, 장소, 날짜가 아닌가?)
- [ ] user_story가 실제 사용자 관점의 의미 있는 스토리인가?
- [ ] acceptance_criteria가 테스트 가능한 조건인가?
- [ ] module이 의미 있는 기능 도메인인가?

---

### 예시 1: 정형 입력
**입력:**
대쉬보드 만들기
- 내용은 주식 차트, 뉴스, 종목 정보 등을 표시하려고 합니다.
- 차트는 실시간으로 업데이트 되야 합니다.
- 반드시 모바일에서도 잘 보여야 합니다.
- 기술스텍은 무료 소프트웨어 사용해주세요.
- 응답속도는 3초 이내로 해주세요.

**출력:**
{
  "requirements": [
    {
      "title": "주식 대시보드 화면 구현",
      "description": "주식 차트, 뉴스, 종목 정보를 표시하는 대시보드 화면을 구현한다",
      "type": "FR",
      "module": "대시보드",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "핵심 기능으로 명확하게 언급됨",
      "user_story": "As a 투자자, I want 대시보드에서 주식 차트/뉴스/종목 정보를 한눈에 보기를, so that 투자 의사결정을 빠르게 할 수 있다",
      "acceptance_criteria": [
        "Given 대시보드 페이지 접속 시, When 로딩이 완료되면, Then 주식 차트/뉴스/종목 정보가 모두 표시된다",
        "Given 종목 검색 시, When 종목명을 입력하면, Then 해당 종목의 차트와 정보가 표시된다"
      ],
      "section_name": "대쉬보드 만들기",
      "original_text": "내용은 주식 차트, 뉴스, 종목 정보 등을 표시하려고 합니다",
      "assumptions": ["차트는 캔들스틱 차트를 의미할 것으로 추정"],
      "missing_info": ["표시할 종목 개수", "뉴스 소스"]
    },
    {
      "title": "실시간 차트 데이터 업데이트",
      "description": "주식 차트 데이터를 실시간으로 업데이트하여 표시한다",
      "type": "FR",
      "module": "대시보드",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "실시간 요구사항이 명확히 언급됨",
      "user_story": "As a 투자자, I want 차트가 실시간으로 업데이트되기를, so that 시장 변동에 즉시 대응할 수 있다",
      "acceptance_criteria": [
        "Given 대시보드가 열려 있을 때, When 시장 데이터가 변경되면, Then 1초 이내에 차트가 갱신된다",
        "Given 네트워크 연결이 끊어졌을 때, When 재연결되면, Then 자동으로 최신 데이터를 동기화한다"
      ],
      "section_name": "대쉬보드 만들기",
      "original_text": "차트는 실시간으로 업데이트 되야 합니다",
      "assumptions": ["WebSocket 또는 SSE를 통한 실시간 통신"],
      "missing_info": ["업데이트 주기"]
    },
    {
      "title": "모바일 반응형 UI 지원",
      "description": "대시보드가 모바일 기기에서도 정상적으로 표시되어야 한다",
      "type": "NFR",
      "module": "UI/UX",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "'반드시' 키워드로 높은 우선순위 표현",
      "user_story": "As a 모바일 사용자, I want 모바일에서도 대시보드를 보기를, so that 이동 중에도 투자 현황을 확인할 수 있다",
      "acceptance_criteria": [
        "Given 모바일 기기(375px 이상)에서, When 대시보드에 접속하면, Then 모든 콘텐츠가 잘림 없이 표시된다",
        "Given 모바일 기기에서, When 차트를 터치하면, Then 확대/축소 인터랙션이 동작한다"
      ],
      "section_name": "대쉬보드 만들기",
      "original_text": "반드시 모바일에서도 잘 보여야 합니다",
      "assumptions": [],
      "missing_info": ["지원 기기 범위", "최소 지원 해상도"]
    },
    {
      "title": "오픈소스 기술 스택 사용",
      "description": "시스템 구축 시 무료 오픈소스 소프트웨어만 사용한다",
      "type": "CONSTRAINT",
      "module": "기술 제약",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "기술 제약사항으로 명확히 언급됨",
      "user_story": null,
      "acceptance_criteria": [
        "Given 기술 스택 선정 시, When 라이선스를 확인하면, Then 모든 소프트웨어가 OSS 라이선스이다"
      ],
      "section_name": "대쉬보드 만들기",
      "original_text": "기술스텍은 무료 소프트웨어 사용해주세요",
      "assumptions": ["오픈소스 = 무료 라이선스"],
      "missing_info": ["허용되는 라이선스 범위"]
    },
    {
      "title": "페이지 응답 시간 3초 이내 보장",
      "description": "모든 페이지의 응답 시간이 3초를 초과하지 않아야 한다. API 응답은 2초 이내",
      "type": "NFR",
      "module": "성능",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "구체적인 수치가 명시됨",
      "user_story": "As a 사용자, I want 3초 이내에 페이지가 로드되기를, so that 쾌적하게 서비스를 이용할 수 있다",
      "acceptance_criteria": [
        "Given 일반 네트워크 환경에서, When 페이지를 요청하면, Then 3초 이내에 렌더링이 완료된다",
        "Given 동시 사용자 100명 환경에서, When API를 호출하면, Then 2초 이내에 응답한다"
      ],
      "section_name": "대쉬보드 만들기",
      "original_text": "응답속도는 3초 이내로 해주세요",
      "assumptions": [],
      "missing_info": ["측정 조건(네트워크 환경, 동시 사용자 수)"]
    }
  ]
}

---

### 예시 2: 회의록 입력
**입력:**
## 제2차 MES 구축 프로젝트 킥오프 회의록

일시: 2024-03-15 14:00~16:00
장소: 본사 3층 대회의실
참석자: 김부장(PI추진팀), 이과장(PI추진팀/서기), 박팀장(생산관리), 최대리(품질관리), 외부 컨설턴트 2명
서기: PI추진팀 이정민 과장

### 1. 프로젝트 개요 소개
김부장이 프로젝트 배경과 목적을 설명함.

### 2. 현장 요구사항 논의
- 박팀장: "현재 APS에서 두께 점프 제한이 안 되고 있어서 품질 문제가 발생합니다. 반드시 반영해야 합니다."
- 박팀장: "코일 이송 시간도 스케줄링에 반영되어야 합니다. 현재는 수작업으로 보정하고 있습니다."
- 최대리: "RFID 기반 코일 추적 시스템이 필요합니다. 현재 바코드는 오류율이 높아요."
- 최대리: "품질 검사 데이터 자동 수집 기능도 추가해 주세요."

### 3. 결정사항
- APS 스케줄링에 두께 점프 제약조건 반영하기로 함 (1차 개발 포함)
- 코일 이송 시간 파라미터 추가 (1차 개발 포함)
- RFID 추적은 2차에서 검토 (예산 확보 필요)
- 품질 데이터 자동 수집은 1차에 포함

### 4. 다음 회의 일정
- 3월 29일 같은 장소에서 상세 설계 검토 예정
- 감사합니다.

**출력:**
{
  "requirements": [
    {
      "title": "APS 두께 점프 제한 규칙 적용",
      "description": "APS 스케줄링 시 두께 점프 제한 규칙을 적용하여, 허용 범위를 벗어나는 두께 변경이 연속 배치되지 않도록 제약조건을 반영한다",
      "type": "FR",
      "module": "APS 스케줄링",
      "priority": "HIGH",
      "confidence_score": 0.95,
      "confidence_reason": "결정사항에서 1차 개발 포함으로 확정됨",
      "user_story": "As a 생산관리 담당자, I want APS가 두께 점프 제한을 자동 적용하기를, so that 두께 변경에 의한 품질 불량을 예방할 수 있다",
      "acceptance_criteria": [
        "Given 스케줄링 실행 시, When 연속 코일의 두께 차이가 허용치를 초과하면, Then 해당 배치 순서가 자동 조정된다",
        "Given 두께 점프 제한 규칙 설정 화면에서, When 허용 범위를 입력하면, Then 스케줄링에 즉시 반영된다"
      ],
      "section_name": "결정사항",
      "original_text": "APS 스케줄링에 두께 점프 제약조건 반영하기로 함",
      "assumptions": ["두께 점프 허용 범위는 별도 정의 필요"],
      "missing_info": ["두께 점프 허용 범위 수치", "예외 처리 규칙"]
    },
    {
      "title": "코일 이송 시간 스케줄링 반영",
      "description": "APS 스케줄링 시 공정 간 코일 이송 시간을 파라미터로 반영하여, 현실적인 생산 계획을 수립한다",
      "type": "FR",
      "module": "APS 스케줄링",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "결정사항에서 1차 개발 포함으로 확정됨",
      "user_story": "As a 생산관리 담당자, I want 코일 이송 시간이 스케줄에 반영되기를, so that 수작업 보정 없이 정확한 생산 계획을 세울 수 있다",
      "acceptance_criteria": [
        "Given 스케줄링 파라미터 설정 시, When 공정 간 이송 시간을 입력하면, Then 생산 계획에 이송 시간이 반영된다",
        "Given 스케줄 조회 시, When 간트차트를 확인하면, Then 이송 시간이 별도 구간으로 표시된다"
      ],
      "section_name": "결정사항",
      "original_text": "코일 이송 시간도 스케줄링에 반영되어야 합니다",
      "assumptions": ["이송 시간은 공정 간 고정값 또는 거리 기반 계산"],
      "missing_info": ["공정별 이송 시간 데이터", "이송 경로 정보"]
    },
    {
      "title": "RFID 기반 코일 실시간 추적",
      "description": "RFID 태그를 이용하여 코일의 현재 위치와 이동 이력을 실시간으로 추적하는 시스템을 구축한다",
      "type": "FR",
      "module": "코일 추적",
      "priority": "LOW",
      "confidence_score": 0.75,
      "confidence_reason": "2차 검토 대상으로 결정됨, 예산 확보 필요",
      "user_story": "As a 품질관리 담당자, I want RFID로 코일 위치를 실시간 추적하기를, so that 바코드 오류 없이 정확한 추적이 가능하다",
      "acceptance_criteria": [
        "Given RFID 리더기가 설치된 구간에서, When 코일이 통과하면, Then 위치 정보가 1초 이내에 시스템에 기록된다",
        "Given 코일 추적 화면에서, When 코일 번호를 조회하면, Then 현재 위치와 이동 이력이 표시된다"
      ],
      "section_name": "현장 요구사항 논의",
      "original_text": "RFID 기반 코일 추적 시스템이 필요합니다",
      "assumptions": ["RFID 인프라(리더기, 태그) 별도 구매 필요"],
      "missing_info": ["RFID 장비 사양", "설치 위치", "2차 개발 시점"]
    },
    {
      "title": "품질 검사 데이터 자동 수집",
      "description": "품질 검사 장비에서 측정 데이터를 자동으로 수집하여 시스템에 저장한다",
      "type": "FR",
      "module": "품질 관리",
      "priority": "HIGH",
      "confidence_score": 0.9,
      "confidence_reason": "1차 개발에 포함으로 결정됨",
      "user_story": "As a 품질관리 담당자, I want 검사 데이터가 자동 수집되기를, so that 수작업 입력 오류를 제거하고 실시간 품질 모니터링이 가능하다",
      "acceptance_criteria": [
        "Given 품질 검사 완료 시, When 측정 장비에서 데이터가 생성되면, Then 시스템에 자동으로 저장된다",
        "Given 자동 수집된 데이터 조회 시, When 기간/검사항목으로 검색하면, Then 수집된 데이터 목록이 표시된다"
      ],
      "section_name": "결정사항",
      "original_text": "품질 검사 데이터 자동 수집 기능도 추가해 주세요",
      "assumptions": ["검사 장비가 데이터 출력 인터페이스를 제공"],
      "missing_info": ["검사 장비 종류 및 인터페이스 규격", "데이터 항목 목록"]
    }
  ]
}

⚠️ 위 회의록에서 "참석자 목록", "서기 정보", "장소", "다음 회의 일정", "감사합니다", "프로젝트 개요 소개" 등은 요구사항이 아니므로 추출하지 않았습니다.

---

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
