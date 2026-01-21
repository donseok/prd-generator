# User Stories - 마이페이지 개선

## Epic: 마이페이지 UX 개선

### US-001: 프로필 사진 변경
**As a** 등록된 사용자  
**I want** 내 프로필 사진을 쉽게 변경할 수  
**So that** 다른 사용자들이 나를 쉽게 알아볼 수 있다

**Acceptance Criteria:**
- [ ] 갤러리에서 사진 선택 가능
- [ ] 카메라로 직접 촬영 가능
- [ ] 이미지 크롭 기능 제공
- [ ] 프로필 사진 삭제 후 기본 이미지로 변경 가능
- [ ] 지원 포맷: JPG, PNG (최대 5MB)

**Story Points:** 3  
**Priority:** Should Have

---

### US-002: 회원 등급 확인
**As a** 쇼핑몰 회원  
**I want** 현재 회원 등급과 다음 등급까지 남은 구매 금액을 확인할 수  
**So that** 등급 혜택을 위한 구매 계획을 세울 수 있다

**Acceptance Criteria:**
- [ ] 현재 등급 및 아이콘 표시
- [ ] 다음 등급까지 필요한 구매 금액 표시
- [ ] 프로그레스 바로 진행률 시각화
- [ ] 등급별 혜택 목록 확인 가능
- [ ] 등급 산정 기준 안내 툴팁

**Story Points:** 5  
**Priority:** Must Have

---

### US-003: 1:1 문의 내역 조회
**As a** 고객  
**I want** 이전에 문의한 내역과 답변을 확인할 수  
**So that** 반복 문의를 피하고 이전 상담 내용을 참고할 수 있다

**Acceptance Criteria:**
- [ ] 문의 내역 목록 조회 (최신순)
- [ ] 답변 완료/대기 상태 필터링
- [ ] 문의 상세 내용 및 답변 확인
- [ ] 문의 내역 삭제 기능
- [ ] 추가 문의 작성 기능

**Story Points:** 5  
**Priority:** Must Have

---

### US-004: 알림 설정 관리
**As a** 앱 사용자  
**I want** 받고 싶은 알림 종류를 선택할 수  
**So that** 불필요한 알림으로 인한 피로감을 줄일 수 있다

**Acceptance Criteria:**
- [ ] 푸시 알림 ON/OFF 토글
- [ ] 카테고리별 알림 설정 (주문, 배송, 프로모션, 이벤트)
- [ ] 야간 알림 수신 설정 (22시~08시)
- [ ] 이메일 수신 동의 설정
- [ ] SMS 수신 동의 설정

**Story Points:** 3  
**Priority:** Could Have

---

## Technical Notes
- 모든 API는 RESTful 규격 준수
- 응답 시간 1초 이내 목표
- 오프라인 상태에서 캐시된 데이터 표시
