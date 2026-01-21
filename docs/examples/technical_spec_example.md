# Technical Specification: 알림 시스템 구축

## 1. 개요

### 1.1 목적
사용자에게 실시간으로 주문, 배송, 프로모션 알림을 전달하는 통합 알림 시스템 구축

### 1.2 범위
- 푸시 알림 (FCM/APNs)
- 인앱 알림
- 이메일 알림
- SMS 알림 (외부 연동)

---

## 2. 기능 요구사항

### 2.1 알림 발송
| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| NTF-001 | 푸시 알림 발송 | P0 |
| NTF-002 | 인앱 알림 목록 조회 | P0 |
| NTF-003 | 알림 읽음 처리 | P0 |
| NTF-004 | 알림 일괄 삭제 | P1 |
| NTF-005 | 알림 타입별 필터링 | P1 |

### 2.2 알림 설정
| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| NTF-010 | 알림 수신 ON/OFF | P0 |
| NTF-011 | 카테고리별 설정 | P1 |
| NTF-012 | 야간 알림 차단 | P2 |
| NTF-013 | 알림 빈도 설정 | P2 |

---

## 3. 비기능 요구사항

### 3.1 성능
- **처리량**: 초당 10,000건 알림 발송 가능
- **지연시간**: 알림 발송 후 3초 이내 도달
- **가용성**: 99.9% uptime

### 3.2 확장성
- 수평 확장 가능한 아키텍처
- 메시지 큐 기반 비동기 처리

### 3.3 보안
- 알림 내용 암호화 (전송 중)
- 사용자 토큰 안전한 관리
- 알림 이력 90일 보관 후 자동 삭제

---

## 4. 시스템 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│   API GW     │────▶│  Notif.     │
│   (App)     │     │              │     │  Service    │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌───────────────────────────┼───────┐
                    ▼                           ▼       ▼
              ┌──────────┐              ┌───────┐  ┌────────┐
              │  Redis   │              │ FCM/  │  │ Email  │
              │  Queue   │              │ APNs  │  │ Sender │
              └──────────┘              └───────┘  └────────┘
```

---

## 5. API 명세

### 5.1 알림 목록 조회
```
GET /api/v1/notifications
Authorization: Bearer {token}

Query Parameters:
- page: integer (default: 1)
- limit: integer (default: 20, max: 100)
- type: string (order|delivery|promotion|all)
- read: boolean (optional)

Response:
{
  "notifications": [...],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

### 5.2 알림 읽음 처리
```
PATCH /api/v1/notifications/{id}/read
Authorization: Bearer {token}

Response: 204 No Content
```

---

## 6. 데이터 모델

### notifications 테이블
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | UUID | PK |
| user_id | UUID | FK to users |
| type | ENUM | 알림 유형 |
| title | VARCHAR(100) | 알림 제목 |
| body | TEXT | 알림 본문 |
| data | JSONB | 추가 데이터 |
| is_read | BOOLEAN | 읽음 여부 |
| created_at | TIMESTAMP | 생성 시각 |

---

## 7. 의존성
- Firebase Cloud Messaging (FCM)
- Apple Push Notification service (APNs)
- Redis (메시지 큐)
- PostgreSQL (데이터 저장)

## 8. 일정
| 마일스톤 | 예상 완료일 |
|---------|-----------|
| 설계 완료 | 2026-01-25 |
| 개발 완료 | 2026-02-15 |
| QA 완료 | 2026-02-25 |
| 배포 | 2026-03-01 |
