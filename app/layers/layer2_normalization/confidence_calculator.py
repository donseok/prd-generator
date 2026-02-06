"""다층 신뢰도 계산 모듈입니다.

여러 요소를 종합하여 요구사항의 최종 신뢰도를 계산합니다:
1. 출처 신뢰도 (source_credibility): 문서 유형에 따른 기본 신뢰도
2. 명확성 점수 (clarity_score): 모호 표현 감지 기반
3. 완전성 점수 (completeness_score): 필수 필드 존재 여부
4. AI 신뢰도 (ai_confidence): Claude가 반환한 신뢰도
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceBreakdown:
    """신뢰도 계산 상세 내역"""
    source_credibility: float  # 출처 신뢰도 (0.0~1.0)
    clarity_score: float       # 명확성 점수 (0.0~1.0)
    completeness_score: float  # 완전성 점수 (0.0~1.0)
    ai_confidence: float       # AI 신뢰도 (0.0~1.0)
    final_score: float         # 최종 점수 (0.0~1.0)
    deduction_reasons: list[str]  # 감점 사유

    def to_reason_string(self) -> str:
        """감점 사유를 문자열로 변환"""
        if not self.deduction_reasons:
            return "모든 항목 충족"
        return "; ".join(self.deduction_reasons[:3])  # 최대 3개


class ConfidenceCalculator:
    """다층 신뢰도 계산기"""

    # 출처 유형별 기본 신뢰도
    SOURCE_CREDIBILITY = {
        "text": 0.85,       # 일반 텍스트
        "document": 1.0,    # 명세서/문서 (Word, PDF)
        "excel": 0.95,      # 엑셀 (구조화된 데이터)
        "csv": 0.90,        # CSV
        "ppt": 0.85,        # 파워포인트
        "email": 0.70,      # 이메일 (비공식적)
        "chat": 0.50,       # 채팅 (매우 비공식적)
        "image": 0.60,      # 이미지 (OCR 불확실성)
        "unknown": 0.70,    # 알 수 없음
    }

    # 모호 표현 패턴 (30개+)
    AMBIGUOUS_PATTERNS = [
        # 정도/범위 모호
        (r"적절한|적절히|적절하게", "적절한 → 구체적 기준 필요"),
        (r"최대한|가능한\s*한", "최대한 → 구체적 수치 필요"),
        (r"등등|등\s*$|기타\s*등", "등등 → 명시적 나열 필요"),
        (r"충분한|충분히", "충분한 → 정량적 기준 필요"),
        (r"빠른|빠르게|신속한|신속히", "빠른 → 응답시간 명시 필요"),
        (r"좋은|좋게|우수한", "좋은 → 품질 기준 명시 필요"),
        (r"많은|많이|대량", "많은 → 구체적 수량 필요"),
        (r"일부|몇몇|몇\s*개", "일부 → 정확한 범위 필요"),

        # 시점 모호
        (r"가끔|때때로|종종", "가끔 → 빈도 명시 필요"),
        (r"나중에|추후|향후", "나중에 → 구체적 일정 필요"),
        (r"곧|조만간|빠른\s*시일", "곧 → 명확한 기한 필요"),
        (r"필요시|필요에\s*따라|상황에\s*따라", "필요시 → 조건 명시 필요"),

        # 범위 모호
        (r"대부분|대다수|거의", "대부분 → 구체적 비율 필요"),
        (r"약간|조금|다소", "약간 → 정량화 필요"),
        (r"어느\s*정도|웬만큼", "어느 정도 → 수치화 필요"),
        (r"평균적|일반적|보통", "평균적 → 기준값 명시 필요"),

        # 조건 모호
        (r"가능하면|되도록|되도록이면", "가능하면 → 필수/선택 구분 필요"),
        (r"원활한|원활하게|원활히", "원활한 → 성능 기준 필요"),
        (r"안정적|안정적으로", "안정적 → 가용성 수치 필요"),
        (r"효율적|효율적으로", "효율적 → 효율성 지표 필요"),

        # 주체 모호
        (r"누군가|어떤\s*사람", "누군가 → 역할 명시 필요"),
        (r"사용자들?(?!로서|가|는|의)", "사용자 → 구체적 역할 명시 권장"),

        # 범위 한정 모호
        (r"정도|쯤|가량", "정도 → 정확한 값 필요"),
        (r"여러|다양한|각종", "여러 → 구체적 항목 나열 필요"),
        (r"전반적|전체적", "전반적 → 구체적 범위 필요"),

        # 수동태/불명확 주체
        (r"되어야\s*한다|되어야\s*함", "수동태 → 주체 명시 권장"),
        (r"처리된다|수행된다", "수동태 → 수행 주체 명시 필요"),

        # 불완전 조건
        (r"경우에\s*따라|상황에\s*따라", "경우에 따라 → 조건 명시 필요"),
        (r"문제\s*없이|오류\s*없이", "문제없이 → 허용 기준 명시 필요"),
        (r"쉽게|간단히|편리하게", "쉽게 → 사용성 기준 필요"),
    ]

    # 필수 필드 및 가중치
    REQUIRED_FIELDS = {
        "title": 0.15,
        "description": 0.25,
        "type": 0.10,
        "priority": 0.10,
        "acceptance_criteria": 0.25,
        "user_story": 0.15,  # CONSTRAINT 타입은 예외
    }

    # 가중치 설정
    WEIGHTS = {
        "source_credibility": 0.15,
        "clarity_score": 0.30,
        "completeness_score": 0.35,
        "ai_confidence": 0.20,
    }

    def calculate(
        self,
        raw_requirement: dict,
        source_type: str = "unknown",
        ai_confidence: float = 0.7
    ) -> ConfidenceBreakdown:
        """
        다층 신뢰도를 계산합니다.

        Args:
            raw_requirement: AI가 추출한 원시 요구사항 딕셔너리
            source_type: 문서 출처 유형 (text, email, chat 등)
            ai_confidence: AI가 반환한 신뢰도 (0.0~1.0)

        Returns:
            ConfidenceBreakdown: 상세 신뢰도 내역
        """
        deduction_reasons = []

        # 1. 출처 신뢰도
        source_credibility = self._calculate_source_credibility(source_type)
        if source_credibility < 0.8:
            deduction_reasons.append(f"출처 신뢰도 낮음 ({source_type})")

        # 2. 명확성 점수
        clarity_score, clarity_issues = self._calculate_clarity_score(raw_requirement)
        deduction_reasons.extend(clarity_issues)

        # 3. 완전성 점수
        completeness_score, completeness_issues = self._calculate_completeness_score(raw_requirement)
        deduction_reasons.extend(completeness_issues)

        # 4. AI 신뢰도 (유효 범위로 클램핑)
        ai_confidence = max(0.0, min(1.0, ai_confidence))

        # 5. 최종 점수 계산 (가중 평균)
        final_score = (
            source_credibility * self.WEIGHTS["source_credibility"] +
            clarity_score * self.WEIGHTS["clarity_score"] +
            completeness_score * self.WEIGHTS["completeness_score"] +
            ai_confidence * self.WEIGHTS["ai_confidence"]
        )

        # 최종 점수 클램핑
        final_score = max(0.0, min(1.0, final_score))

        logger.debug(
            f"[ConfidenceCalc] source={source_credibility:.2f}, "
            f"clarity={clarity_score:.2f}, completeness={completeness_score:.2f}, "
            f"ai={ai_confidence:.2f} → final={final_score:.2f}"
        )

        return ConfidenceBreakdown(
            source_credibility=source_credibility,
            clarity_score=clarity_score,
            completeness_score=completeness_score,
            ai_confidence=ai_confidence,
            final_score=final_score,
            deduction_reasons=deduction_reasons
        )

    def _calculate_source_credibility(self, source_type: str) -> float:
        """출처 유형에 따른 기본 신뢰도 반환"""
        source_type = source_type.lower() if source_type else "unknown"
        return self.SOURCE_CREDIBILITY.get(source_type, 0.70)

    def _calculate_clarity_score(self, raw_requirement: dict) -> tuple[float, list[str]]:
        """
        명확성 점수를 계산합니다.
        모호 표현이 많을수록 점수가 낮아집니다.
        """
        issues = []

        # 검사할 텍스트 결합
        texts_to_check = [
            raw_requirement.get("title", ""),
            raw_requirement.get("description", ""),
            raw_requirement.get("user_story", ""),
        ]

        # acceptance_criteria도 검사
        criteria = raw_requirement.get("acceptance_criteria", [])
        if isinstance(criteria, list):
            texts_to_check.extend(str(c) for c in criteria)

        combined_text = " ".join(str(t) for t in texts_to_check if t)

        # 모호 표현 감지
        ambiguous_count = 0
        detected_patterns = set()

        for pattern, issue_msg in self.AMBIGUOUS_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                ambiguous_count += 1
                # 같은 유형의 이슈는 한 번만 기록
                issue_key = issue_msg.split("→")[0].strip()
                if issue_key not in detected_patterns:
                    detected_patterns.add(issue_key)
                    if len(issues) < 3:  # 최대 3개까지만 기록
                        issues.append(issue_msg)

        # 점수 계산: 모호 표현 1개당 0.1점 감점 (최소 0.3)
        clarity_score = max(0.3, 1.0 - (ambiguous_count * 0.1))

        return clarity_score, issues

    def _calculate_completeness_score(self, raw_requirement: dict) -> tuple[float, list[str]]:
        """
        완전성 점수를 계산합니다.
        필수 필드의 존재 여부와 내용 충실도를 평가합니다.
        """
        issues = []
        score = 0.0

        req_type = raw_requirement.get("type", "FR").upper()
        is_constraint = "CONSTRAINT" in req_type

        for field, weight in self.REQUIRED_FIELDS.items():
            # CONSTRAINT 타입은 user_story가 필수가 아님
            if field == "user_story" and is_constraint:
                score += weight  # 만점 부여
                continue

            value = raw_requirement.get(field)

            if field == "acceptance_criteria":
                # acceptance_criteria는 리스트이며 최소 1개 이상 필요
                if isinstance(value, list) and len(value) > 0:
                    # 각 기준의 품질도 평가
                    valid_criteria = [c for c in value if c and len(str(c)) > 10]
                    ratio = len(valid_criteria) / max(len(value), 1)
                    score += weight * ratio
                    if ratio < 1.0:
                        issues.append("인수조건 내용 부실")
                else:
                    issues.append("인수조건 누락")
            elif value:
                # 내용이 있는 경우
                str_value = str(value)
                if field == "title" and len(str_value) < 5:
                    score += weight * 0.5
                    issues.append("제목 너무 짧음")
                elif field == "description" and len(str_value) < 20:
                    score += weight * 0.5
                    issues.append("설명 부족")
                elif field == "user_story" and not self._is_valid_user_story(str_value):
                    score += weight * 0.7
                    issues.append("User Story 형식 불완전")
                else:
                    score += weight
            else:
                # 필드 누락
                if field in ["title", "description"]:
                    issues.append(f"{field} 누락")

        return score, issues[:3]  # 최대 3개 이슈만 반환

    def _is_valid_user_story(self, user_story: str) -> bool:
        """User Story가 올바른 형식인지 검사"""
        if not user_story:
            return False

        # "As a ... I want ... so that ..." 패턴 또는 한글 패턴 검사
        patterns = [
            r"As a .+, I want .+, so that .+",  # 영문
            r".*로서.*원한다|원합니다",  # 한글 간략
            r".*사용자.*위해.*기능",  # 한글 변형
        ]

        for pattern in patterns:
            if re.search(pattern, user_story, re.IGNORECASE):
                return True

        # 최소 길이 충족 여부
        return len(user_story) > 30


# 싱글톤 인스턴스
_calculator_instance: Optional[ConfidenceCalculator] = None


def get_confidence_calculator() -> ConfidenceCalculator:
    """ConfidenceCalculator 싱글톤 인스턴스 반환"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = ConfidenceCalculator()
    return _calculator_instance
