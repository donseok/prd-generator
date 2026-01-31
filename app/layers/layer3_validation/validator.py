"""Layer 3: 검증(Validation) 서비스입니다.
추출된 요구사항의 품질을 검사하고, 문제가 있거나 AI가 확신하지 못하는 항목을 찾아냅니다.
"""

import logging
from typing import List, Tuple, Optional

from app.models import (
    NormalizedRequirement,
    ValidationResult,
    ReviewItem,
    ReviewItemType,
)
from app.services import ClaudeClient, get_claude_client
from app.config import get_settings

logger = logging.getLogger(__name__)


class Validator:
    """
    요구사항 검증기 클래스입니다.
    
    주요 기능:
    1. 개별 요구사항 품질 체크 (완전성, 일관성 등)
    2. 기획자(PM)의 검토가 필요한 항목 분류
    3. 요구사항 간의 충돌 감지
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()
        self.settings = get_settings()

    async def validate(
        self,
        requirements: List[NormalizedRequirement],
        job_id: str = ""
    ) -> Tuple[List[NormalizedRequirement], List[ReviewItem]]:
        """
        요구사항 목록 전체를 검증합니다.

        Returns:
            (자동 승인된 요구사항 목록, 검토가 필요한 항목 목록)
        """
        validated = []
        review_items = []

        for req in requirements:
            # 개별 요구사항 검증 수행
            validation_result = await self._validate_requirement(req, requirements)

            # 검증 결과에 따라 승인 또는 검토 대기로 분류
            if self._needs_pm_review(req, validation_result):
                review_item = self._create_review_item(req, validation_result, job_id)
                review_items.append(review_item)
            else:
                validated.append(req)

        # 요구사항 간의 충돌 감지 (AI 활용)
        conflicts = await self._detect_conflicts(requirements)
        for conflict in conflicts:
            conflict.job_id = job_id
            review_items.append(conflict)

        return validated, review_items

    async def _validate_requirement(
        self,
        requirement: NormalizedRequirement,
        all_requirements: List[NormalizedRequirement]
    ) -> ValidationResult:
        """단일 요구사항에 대한 종합 검증을 수행합니다."""
        # 1. 내용이 충분한지 체크 (완전성)
        completeness = self._check_completeness(requirement)

        # 2. 내용에 문제가 없는지 체크 (일관성)
        consistency_issues = self._check_consistency(requirement)

        # 3. 출처가 명확한지 체크 (추적성)
        traceability = self._check_traceability(requirement)

        # 유효성 판단 기준: 완전성이 70% 이상이고 일관성 문제가 없으며 신뢰도가 기준치 이상이어야 함
        is_valid = (
            completeness > 0.7 and
            not consistency_issues and
            requirement.confidence_score >= self.settings.auto_approve_threshold
        )

        return ValidationResult(
            requirement_id=requirement.id,
            is_valid=is_valid,
            completeness_score=completeness,
            consistency_issues=consistency_issues,
            traceability_score=traceability,
            needs_pm_review=not is_valid,
            review_reasons=self._compile_review_reasons(
                requirement, completeness, consistency_issues
            ),
        )

    def _check_completeness(self, req: NormalizedRequirement) -> float:
        """
        요구사항이 얼마나 구체적으로 작성되었는지 점수를 매깁니다. (0.0 ~ 1.0)
        
        평가 항목 (각 20점):
        1. 제목 길이
        2. 설명 길이
        3. 사용자 스토리 존재 여부
        4. 인수 조건(완료 기준) 존재 여부
        5. 우선순위 설정 여부
        """
        score = 0.0
        max_score = 5.0

        # 1. 제목 검사: 4자 이상의 의미 있는 제목
        if req.title and len(req.title) > 3:
            score += 1.0

        # 2. 설명 검사: 11자 이상의 상세 설명
        if req.description and len(req.description) > 10:
            score += 1.0

        # 3. 사용자 스토리 검사: 기능 요구사항은 필수
        if req.user_story or req.type.value == "CONSTRAINT":
            score += 1.0

        # 4. 인수 조건 검사: 최소 1개 이상
        if req.acceptance_criteria and len(req.acceptance_criteria) > 0:
            score += 1.0

        # 5. 우선순위 검사: 설정되어 있어야 함
        if req.priority:
            score += 1.0

        return score / max_score

    def _check_consistency(self, req: NormalizedRequirement) -> List[str]:
        """표현이 모호하거나 정보가 누락되었는지 확인합니다."""
        issues = []

        # 모호한 표현 사용 여부 검사
        vague_terms = ["등", "기타", "필요시", "적절한", "합리적인", "etc", "등등"]
        for term in vague_terms:
            if term in req.description.lower():
                issues.append(f"모호한 표현 사용: '{term}'")

        # AI가 감지한 누락 정보가 있는지 확인
        if req.missing_info:
            for info in req.missing_info[:2]:  # 최대 2개까지만 표시
                issues.append(f"누락된 정보: {info}")

        return issues

    def _check_traceability(self, req: NormalizedRequirement) -> float:
        """출처가 명확한지 점수를 매깁니다."""
        score = 0.0

        # 출처 정보가 있는지
        if req.source_reference:
            score += 0.5

        # AI 신뢰도가 높은지
        if req.confidence_score > 0.5:
            score += 0.3

        # 신뢰도 이유가 명시되어 있는지
        if req.confidence_reason:
            score += 0.2

        return min(1.0, score)

    def _needs_pm_review(
        self,
        requirement: NormalizedRequirement,
        validation: ValidationResult
    ) -> bool:
        """
        기획자(PM)의 검토가 필요한지 최종 판단하는 함수입니다.
        설정된 조건 중 하나라도 만족하면 검토가 필요하다고 판단합니다.
        """
        # PM 검토 기능이 꺼져있으면 무조건 통과
        if not self.settings.enable_pm_review:
            return False

        threshold = self.settings.auto_approve_threshold

        # 1. 신뢰도가 기준치 미만인 경우
        if requirement.confidence_score < threshold:
            return True

        # 2. 내용이 충분하지 않은 경우
        if validation.completeness_score < 0.7:
            return True

        # 3. 모호한 표현 등 문제가 있는 경우
        if validation.consistency_issues:
            return True

        # 4. 누락된 정보가 있는 경우
        if requirement.missing_info:
            return True

        return False

    def _compile_review_reasons(
        self,
        requirement: NormalizedRequirement,
        completeness: float,
        consistency_issues: List[str]
    ) -> List[str]:
        """왜 검토가 필요한지 이유 목록을 작성합니다."""
        reasons = []

        threshold = self.settings.auto_approve_threshold

        if requirement.confidence_score < threshold:
            reasons.append(
                f"신뢰도 {requirement.confidence_score:.0%} < 기준 {threshold:.0%}"
            )

        if completeness < 0.7:
            reasons.append(f"완전성 점수 {completeness:.0%} 부족")

        for issue in consistency_issues[:2]:
            reasons.append(issue)

        if requirement.assumptions:
            reasons.append(f"가정사항 {len(requirement.assumptions)}개 확인 필요")

        return reasons

    def _create_review_item(
        self,
        requirement: NormalizedRequirement,
        validation: ValidationResult,
        job_id: str
    ) -> ReviewItem:
        """검토 항목 객체를 생성합니다."""
        # 검토 유형 분류
        if requirement.confidence_score < 0.5:
            issue_type = ReviewItemType.LOW_CONFIDENCE
        elif requirement.missing_info:
            issue_type = ReviewItemType.MISSING_INFO
        else:
            issue_type = ReviewItemType.AMBIGUOUS

        # 설명 작성
        reasons = validation.review_reasons or ["검토 필요"]
        description = "; ".join(reasons)

        return ReviewItem(
            job_id=job_id,
            requirement_id=requirement.id,
            issue_type=issue_type,
            description=description,
            original_text=requirement.description[:500],
            suggested_resolution=requirement.confidence_reason,
        )

    async def _detect_conflicts(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[ReviewItem]:
        """
        AI를 사용하여 요구사항 간의 충돌을 감지합니다.
        (예: '비용 최소화' vs '최고 성능' 같은 모순)
        """
        # 충돌 감지 기능이 꺼져있으면 건너뜀
        if not self.settings.enable_conflict_detection:
            return []

        # 비교할 요구사항이 2개 미만이면 건너뜀
        if len(requirements) < 2:
            return []

        # AI에게 보낼 요약 정보 생성 (최대 20개로 제한)
        req_summaries = "\n".join([
            f"{req.id}: {req.title} - {req.description[:100]}"
            for req in requirements[:20]
        ])

        prompt = f"""다음 요구사항들 중 서로 충돌하는 항목을 찾아주세요.

요구사항 목록:
{req_summaries}

충돌 유형:
1. 직접적 모순: A와 B가 서로 반대되는 요구
2. 자원 충돌: 같은 자원을 다르게 사용
3. 우선순위 충돌: 동시에 만족 불가능

JSON 형식으로 응답:
{{
  "conflicts": [
    {{
      "req1_id": "REQ-001",
      "req2_id": "REQ-002",
      "conflict_type": "직접적 모순/자원 충돌/우선순위 충돌",
      "description": "충돌 설명"
    }}
  ]
}}

충돌이 없으면 {{'conflicts': []}}를 반환하세요."""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="당신은 요구사항 충돌을 탐지하는 전문가입니다.",
                user_prompt=prompt,
                temperature=0.2,
            )

            conflicts = result.get("conflicts", [])
            review_items = []

            for conflict in conflicts:
                review_items.append(ReviewItem(
                    job_id="",  # 호출자가 나중에 설정함
                    requirement_id=conflict.get("req1_id", ""),
                    issue_type=ReviewItemType.CONFLICT,
                    description=f"충돌 발견: {conflict.get('description', '')}",
                    original_text=f"{conflict.get('req1_id')} vs {conflict.get('req2_id')}",
                    suggested_resolution=f"두 요구사항 검토 필요: {conflict.get('conflict_type', '')}",
                ))

            return review_items

        except Exception as e:
            logger.error(f"충돌 감지 실패: {e}", exc_info=True)
            return []