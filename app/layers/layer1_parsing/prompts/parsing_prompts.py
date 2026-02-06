"""Claude prompts for parsing different input types (Korean) - Enhanced with Few-shot examples."""

EMAIL_PARSING_PROMPT = """당신은 이메일 스레드를 분석하여 요구사항 정보를 추출하는 전문가입니다.

주어진 이메일에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. thread_summary: 이메일 전체 요약 (1-2문장)
2. participants: 참여자 목록
   - email: 이메일 주소
   - inferred_role: 추론된 역할 (PM, 개발자, 디자이너, 고객, 경영진 등)
3. decisions: 확정된 결정 사항들 (문자열 배열, 최대 10개)
4. open_discussions: 아직 결정되지 않은 논의 사항들 (문자열 배열, 최대 10개)
5. requirement_candidates: 요구사항으로 볼 수 있는 항목들 (최대 20개)
   - text: 원본 텍스트 (200자 이내)
   - context: 맥락 설명 (100자 이내)
   - confidence: 신뢰도 (0.0~1.0)
   - type: FR(기능)/NFR(비기능)/CONSTRAINT(제약) 중 추정
6. priority_signals: 우선순위 관련 키워드 (긴급, ASAP, 필수 등)
7. action_items: 후속 조치 필요 사항 (최대 10개)

### 입력 예시:
Subject: RE: 주문 시스템 개선 요청
From: kim.pm@company.com
To: lee.dev@company.com, park.designer@company.com

안녕하세요, 김PM입니다.

지난 회의에서 논의된 내용 정리합니다.

1. 결제 모듈은 반드시 PG사 연동으로 진행 (확정)
2. 주문 완료 후 SMS 알림 기능 추가 필요 - ASAP
3. 관리자 대시보드는 다음 버전에서 검토

응답시간은 3초 이내로 유지해주세요.

박디자이너님, UI 목업 금요일까지 부탁드립니다.

### 출력 예시:
{
  "thread_summary": "주문 시스템 개선을 위한 결제 모듈 PG 연동과 SMS 알림 기능 추가 논의",
  "participants": [
    {"email": "kim.pm@company.com", "inferred_role": "PM"},
    {"email": "lee.dev@company.com", "inferred_role": "개발자"},
    {"email": "park.designer@company.com", "inferred_role": "디자이너"}
  ],
  "decisions": [
    "결제 모듈은 PG사 연동으로 진행"
  ],
  "open_discussions": [
    "관리자 대시보드는 다음 버전에서 검토 예정"
  ],
  "requirement_candidates": [
    {
      "text": "결제 모듈은 반드시 PG사 연동으로 진행",
      "context": "결제 기능 구현 방식 결정",
      "confidence": 0.95,
      "type": "FR"
    },
    {
      "text": "주문 완료 후 SMS 알림 기능 추가",
      "context": "사용자 알림 기능 요청",
      "confidence": 0.9,
      "type": "FR"
    },
    {
      "text": "응답시간은 3초 이내로 유지",
      "context": "성능 요구사항",
      "confidence": 0.85,
      "type": "NFR"
    }
  ],
  "priority_signals": ["반드시", "ASAP"],
  "action_items": [
    "UI 목업 금요일까지 완료 (담당: 박디자이너)"
  ]
}

이제 다음 이메일을 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


EXCEL_PARSING_PROMPT = """당신은 엑셀/CSV 데이터를 분석하여 요구사항 정보를 추출하는 전문가입니다.

주어진 데이터에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. data_summary: 데이터 전체 요약 (2-3문장)
2. column_analysis: 컬럼별 분석 (최대 20개 컬럼)
   - column_name: 컬럼명
   - data_type: 데이터 유형 (text, number, date, category 등)
   - purpose: 추정되는 용도 (requirement_title, description, priority 등)
   - sample_values: 샘플 값 (최대 3개)
3. requirement_mapping: 요구사항으로 매핑 가능한 행들 (최대 30개)
   - row_reference: 행 번호 또는 식별자
   - title: 추출된 제목 (50자 이내)
   - description: 추출된 설명 (200자 이내)
   - priority: 추출된 우선순위 (HIGH/MEDIUM/LOW)
   - confidence: 매핑 신뢰도 (0.0~1.0)
4. data_quality_issues: 데이터 품질 문제 (빈 값, 중복, 불일치 등)
5. suggested_normalization: 정규화 제안

### 입력 예시:
| 기능ID | 기능명 | 설명 | 우선순위 | 담당자 |
|--------|--------|------|----------|--------|
| F001 | 로그인 | 사용자 인증 기능 | 높음 | 김개발 |
| F002 | 대시보드 | 메인 화면 표시 | 중간 | 박개발 |
| F003 | 결제 | | 높음 | |

### 출력 예시:
{
  "data_summary": "기능 요구사항 목록으로, 3개의 기능이 정의되어 있으며 우선순위와 담당자 정보를 포함",
  "column_analysis": [
    {"column_name": "기능ID", "data_type": "text", "purpose": "requirement_id", "sample_values": ["F001", "F002", "F003"]},
    {"column_name": "기능명", "data_type": "text", "purpose": "requirement_title", "sample_values": ["로그인", "대시보드", "결제"]},
    {"column_name": "설명", "data_type": "text", "purpose": "description", "sample_values": ["사용자 인증 기능", "메인 화면 표시"]},
    {"column_name": "우선순위", "data_type": "category", "purpose": "priority", "sample_values": ["높음", "중간"]},
    {"column_name": "담당자", "data_type": "text", "purpose": "assignee", "sample_values": ["김개발", "박개발"]}
  ],
  "requirement_mapping": [
    {"row_reference": "F001", "title": "로그인", "description": "사용자 인증 기능", "priority": "HIGH", "confidence": 0.95},
    {"row_reference": "F002", "title": "대시보드", "description": "메인 화면 표시", "priority": "MEDIUM", "confidence": 0.9},
    {"row_reference": "F003", "title": "결제", "description": "", "priority": "HIGH", "confidence": 0.6}
  ],
  "data_quality_issues": [
    "F003 행의 설명이 비어있음",
    "F003 행의 담당자가 지정되지 않음"
  ],
  "suggested_normalization": {
    "priority_mapping": {"높음": "HIGH", "중간": "MEDIUM", "낮음": "LOW"}
  }
}

이제 다음 데이터를 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


PPT_PARSING_PROMPT = """당신은 PPT 프레젠테이션을 분석하여 요구사항 정보를 추출하는 전문가입니다.

주어진 PPT 내용에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. presentation_summary: 프레젠테이션 전체 요약 (2-3문장)
2. slide_analysis: 슬라이드별 분석 (최대 30개)
   - slide_number: 슬라이드 번호
   - purpose: 슬라이드 목적 (개요, 기능설명, 일정, 비용 등)
   - key_points: 핵심 포인트들 (각 100자 이내, 최대 5개)
3. requirement_candidates: 요구사항 후보들 (최대 30개)
   - text: 원본 텍스트 (200자 이내)
   - source_slide: 출처 슬라이드 번호
   - type: FR/NFR/CONSTRAINT 추정
   - confidence: 신뢰도 (0.0~1.0)
4. visual_references: 시각 자료 참조 (다이어그램, 와이어프레임 등의 설명)
5. timeline_info: 일정 관련 정보
6. stakeholder_notes: 이해관계자 관련 정보

### 입력 예시:
슬라이드 1: 프로젝트 개요
- 고객사: ABC Corporation
- 프로젝트: ERP 시스템 구축

슬라이드 2: 주요 기능
- 재고 관리: 입출고 관리, 재고 현황 조회
- 주문 관리: 주문 등록, 주문 상태 추적
- 보고서: 일별/월별 통계

슬라이드 3: 일정
- 1단계 (3개월): 분석/설계
- 2단계 (4개월): 개발
- 3단계 (1개월): 테스트/오픈

### 출력 예시:
{
  "presentation_summary": "ABC Corporation의 ERP 시스템 구축 제안서로, 재고/주문 관리 및 보고서 기능을 8개월간 개발하는 프로젝트",
  "slide_analysis": [
    {"slide_number": 1, "purpose": "개요", "key_points": ["고객사: ABC Corporation", "프로젝트: ERP 시스템 구축"]},
    {"slide_number": 2, "purpose": "기능설명", "key_points": ["재고 관리 기능", "주문 관리 기능", "보고서 기능"]},
    {"slide_number": 3, "purpose": "일정", "key_points": ["총 8개월 소요", "3단계로 구성"]}
  ],
  "requirement_candidates": [
    {"text": "입출고 관리, 재고 현황 조회", "source_slide": 2, "type": "FR", "confidence": 0.9},
    {"text": "주문 등록, 주문 상태 추적", "source_slide": 2, "type": "FR", "confidence": 0.9},
    {"text": "일별/월별 통계 보고서", "source_slide": 2, "type": "FR", "confidence": 0.85}
  ],
  "visual_references": [],
  "timeline_info": {
    "milestones": ["분석/설계 완료", "개발 완료", "오픈"],
    "total_duration": "8개월"
  },
  "stakeholder_notes": ["고객사: ABC Corporation"]
}

이제 다음 PPT 내용을 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


IMAGE_PARSING_PROMPT = """당신은 UI 스크린샷과 이미지를 분석하여 요구사항을 추출하는 전문가입니다.

이미지에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. image_type: 이미지 유형
   - screenshot: UI 스크린샷
   - mockup: 디자인 목업
   - wireframe: 와이어프레임
   - diagram: 다이어그램/플로우차트
   - annotation: 주석이 있는 이미지
   - photo: 일반 사진
   - other: 기타

2. extracted_text: 이미지에서 추출된 모든 텍스트 (OCR, 500자 이내)

3. ui_elements: 식별된 UI 요소들 (최대 20개)
   - type: 요소 유형 (button, input, menu, header, list, table, card, modal 등)
   - text: 요소에 포함된 텍스트
   - location: 위치 설명 (상단, 좌측 사이드바 등)

4. annotations: 마킹/주석 정보 (최대 10개)
   - type: 주석 유형 (circle, arrow, highlight, text_note 등)
   - description: 주석이 가리키는 내용
   - target: 대상 UI 요소

5. inferred_requirements: 추론된 요구사항들 (최대 15개)
   - description: 요구사항 설명 (200자 이내)
   - confidence: 신뢰도 (0.0~1.0)
   - source: 추론 근거 (annotation, ui_element, text 등)
   - type: FR/NFR/CONSTRAINT 추정

6. change_requests: 변경 요청 사항 (Before/After 패턴, 수정/삭제/추가 요청)

### 입력 예시:
[대시보드 화면 스크린샷]
- 상단에 "주문 관리" 헤더
- 좌측 사이드바에 메뉴 (대시보드, 주문목록, 설정)
- 중앙에 주문 테이블
- 우측 상단에 "새 주문" 버튼
- 빨간 동그라미로 "새 주문" 버튼 마킹
- 화살표와 함께 메모: "버튼을 더 크게"

### 출력 예시:
{
  "image_type": "annotation",
  "extracted_text": "주문 관리, 대시보드, 주문목록, 설정, 새 주문",
  "ui_elements": [
    {"type": "header", "text": "주문 관리", "location": "상단"},
    {"type": "menu", "text": "대시보드, 주문목록, 설정", "location": "좌측 사이드바"},
    {"type": "table", "text": "주문 테이블", "location": "중앙"},
    {"type": "button", "text": "새 주문", "location": "우측 상단"}
  ],
  "annotations": [
    {"type": "circle", "description": "버튼 강조", "target": "새 주문 버튼"},
    {"type": "text_note", "description": "버튼을 더 크게 요청", "target": "새 주문 버튼"}
  ],
  "inferred_requirements": [
    {"description": "주문 관리 대시보드 화면 구현", "confidence": 0.9, "source": "ui_element", "type": "FR"},
    {"description": "새 주문 버튼 크기 확대", "confidence": 0.95, "source": "annotation", "type": "FR"},
    {"description": "좌측 사이드바 메뉴 구현", "confidence": 0.85, "source": "ui_element", "type": "FR"}
  ],
  "change_requests": [
    {"type": "modify", "target": "새 주문 버튼", "request": "버튼 크기 확대"}
  ]
}

이제 다음 이미지를 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


CHAT_PARSING_PROMPT = """당신은 메신저/채팅 대화를 분석하여 요구사항 정보를 추출하는 전문가입니다.

대화 내용에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. conversation_summary: 대화 전체 요약 (2-3문장)
2. topic_segments: 주제별 대화 구분 (최대 10개)
   - topic: 주제
   - start_message: 시작 메시지 인덱스
   - key_points: 핵심 내용 (각 100자 이내)
3. participants_analysis: 참여자 분석 (최대 10명)
   - name: 이름/닉네임
   - inferred_role: 추론된 역할
   - contribution: 주요 기여 내용
4. requirement_candidates: 요구사항 후보 (최대 20개)
   - text: 원본 텍스트 (줄임말, 이모지 해석 포함, 200자 이내)
   - speaker: 발화자
   - context: 맥락
   - confidence: 신뢰도 (0.0~1.0)
   - type: FR/NFR/CONSTRAINT 추정
5. decisions_made: 합의된 결정 사항 (최대 10개)
6. action_items: 후속 조치 필요 사항
7. unclear_items: 불명확하여 확인 필요한 사항
8. slang_translations: 줄임말/은어 해석

### 입력 예시:
[10:30] 김PM: 오늘 회의 안건 공유드립니다
[10:31] 김PM: 1. 로그인 방식 결정 2. API 응답시간 기준
[10:35] 이개발: 로그인은 소셜로그인 ㄱㄱ요 카카오 네이버 구글
[10:36] 박기획: +1 소셜로그인 찬성이요
[10:40] 이개발: API는 2초 이내면 될듯요?
[10:42] 김PM: ㅇㅋ 소셜로그인으로 확정, API 2초 이내로 가시죠
[10:43] 이개발: 넵 ㅎㅎ

### 출력 예시:
{
  "conversation_summary": "로그인 방식을 소셜로그인(카카오, 네이버, 구글)으로 확정하고, API 응답시간 기준을 2초 이내로 결정한 회의",
  "topic_segments": [
    {"topic": "회의 안건 공유", "start_message": 0, "key_points": ["로그인 방식 결정", "API 응답시간 기준"]},
    {"topic": "로그인 방식 논의", "start_message": 2, "key_points": ["소셜로그인 제안", "카카오/네이버/구글"]},
    {"topic": "API 응답시간 논의", "start_message": 4, "key_points": ["2초 이내 제안", "합의 완료"]}
  ],
  "participants_analysis": [
    {"name": "김PM", "inferred_role": "PM", "contribution": "회의 진행 및 의사결정"},
    {"name": "이개발", "inferred_role": "개발자", "contribution": "기술적 제안"},
    {"name": "박기획", "inferred_role": "기획자", "contribution": "제안 동의"}
  ],
  "requirement_candidates": [
    {"text": "소셜로그인 지원 (카카오, 네이버, 구글)", "speaker": "이개발", "context": "로그인 방식 논의", "confidence": 0.95, "type": "FR"},
    {"text": "API 응답시간 2초 이내", "speaker": "이개발", "context": "성능 기준 논의", "confidence": 0.9, "type": "NFR"}
  ],
  "decisions_made": [
    "소셜로그인으로 확정 (카카오, 네이버, 구글)",
    "API 응답시간 2초 이내로 확정"
  ],
  "action_items": [],
  "unclear_items": [],
  "slang_translations": [
    {"original": "ㄱㄱ요", "interpreted": "가요/진행하자"},
    {"original": "+1", "interpreted": "동의"},
    {"original": "ㅇㅋ", "interpreted": "오케이/확인"},
    {"original": "넵 ㅎㅎ", "interpreted": "네, 알겠습니다"}
  ]
}

이제 다음 대화를 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""


DOCUMENT_PARSING_PROMPT = """당신은 기존 문서(Word, PDF)를 분석하여 요구사항 정보를 추출하는 전문가입니다.

문서 내용에서 다음을 식별하고 JSON 형식으로 반환해주세요:

1. document_summary: 문서 전체 요약 (2-3문장)
2. document_type: 문서 유형 추정
   - requirement_spec: 요구사항 명세서
   - proposal: 제안서
   - meeting_minutes: 회의록
   - technical_doc: 기술 문서
   - contract: 계약서
   - other: 기타
3. structure_analysis: 문서 구조 분석
   - sections: 섹션 목록 (제목, 요약)
   - has_table_of_contents: 목차 여부
   - has_appendix: 부록 여부
4. existing_requirements: 기존 요구사항들 (최대 50개)
   - id: 기존 ID (있는 경우)
   - title: 제목 (50자 이내)
   - description: 설명 (200자 이내)
   - type: FR/NFR/CONSTRAINT
   - confidence: 신뢰도 (0.0~1.0)
5. change_candidates: 변경이 필요해 보이는 항목
6. references: 참조 정보 (internal: 내부 문서, external: 외부 참조)
7. stakeholders: 문서에 언급된 이해관계자

### 입력 예시:
# ABC 프로젝트 요구사항 정의서

## 1. 개요
본 문서는 ABC 쇼핑몰 시스템의 요구사항을 정의합니다.

## 2. 기능 요구사항
### REQ-001: 회원 가입
사용자는 이메일과 비밀번호로 회원가입할 수 있어야 한다.
우선순위: 높음

### REQ-002: 상품 검색
사용자는 키워드로 상품을 검색할 수 있어야 한다.
우선순위: 높음

## 3. 비기능 요구사항
### NFR-001: 응답 시간
모든 페이지는 3초 이내에 로드되어야 한다.

## 4. 참고자료
- 기존 쇼핑몰 분석 보고서 (내부)
- PCI DSS 규정 (외부)

### 출력 예시:
{
  "document_summary": "ABC 쇼핑몰 시스템의 요구사항 정의서로, 회원가입/상품검색 등 기능 요구사항과 성능 요구사항을 포함",
  "document_type": "requirement_spec",
  "structure_analysis": {
    "sections": [
      {"title": "1. 개요", "summary": "문서 목적 설명"},
      {"title": "2. 기능 요구사항", "summary": "회원가입, 상품검색 기능 정의"},
      {"title": "3. 비기능 요구사항", "summary": "응답시간 등 성능 기준"},
      {"title": "4. 참고자료", "summary": "내부/외부 참조 문서"}
    ],
    "has_table_of_contents": false,
    "has_appendix": false
  },
  "existing_requirements": [
    {"id": "REQ-001", "title": "회원 가입", "description": "사용자는 이메일과 비밀번호로 회원가입할 수 있어야 한다", "type": "FR", "confidence": 0.95},
    {"id": "REQ-002", "title": "상품 검색", "description": "사용자는 키워드로 상품을 검색할 수 있어야 한다", "type": "FR", "confidence": 0.95},
    {"id": "NFR-001", "title": "응답 시간", "description": "모든 페이지는 3초 이내에 로드되어야 한다", "type": "NFR", "confidence": 0.9}
  ],
  "change_candidates": [],
  "references": {
    "internal": ["기존 쇼핑몰 분석 보고서"],
    "external": ["PCI DSS 규정"]
  },
  "stakeholders": []
}

이제 다음 문서를 분석해주세요. 응답은 반드시 유효한 JSON 형식이어야 합니다."""
