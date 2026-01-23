"""Main validator service for Layer 3."""

from typing import List, Tuple, Optional

from app.models import (
    NormalizedRequirement,
    ValidationResult,
    ReviewItem,
    ReviewItemType,
)
from app.services import ClaudeClient, get_claude_client
from app.config import get_settings


class Validator:
    """
    Layer 3: Quality validation and PM review routing.

    Validates requirements and routes low-confidence items for PM review.
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
        Validate requirements and route low-confidence items for PM review.

        Args:
            requirements: List of normalized requirements
            job_id: Processing job ID for review items

        Returns:
            Tuple of (validated_requirements, review_items)
        """
        validated = []
        review_items = []

        for req in requirements:
            # Perform validation checks
            validation_result = await self._validate_requirement(req, requirements)

            # Decide routing based on confidence and validation
            if self._needs_pm_review(req, validation_result):
                review_item = self._create_review_item(req, validation_result, job_id)
                review_items.append(review_item)
            else:
                validated.append(req)

        # Cross-requirement validation (conflicts)
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
        """Perform comprehensive validation on a single requirement."""
        # Completeness check
        completeness = self._check_completeness(requirement)

        # Consistency check
        consistency_issues = self._check_consistency(requirement)

        # Traceability check
        traceability = self._check_traceability(requirement)

        # Determine if valid
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
        요구사항 완전성 점수 계산.

        5가지 항목을 검사하여 0.0 ~ 1.0 사이의 점수를 반환합니다.
        각 항목은 1점씩이며, 총점 5점을 기준으로 정규화됩니다.

        점수 산정 기준 (5점 만점):
        ┌─────────────────────────────────────────────────────┐
        │ 항목               │ 조건                    │ 점수 │
        ├─────────────────────────────────────────────────────┤
        │ 1. 제목            │ 4자 이상               │ 1.0  │
        │ 2. 설명            │ 11자 이상              │ 1.0  │
        │ 3. 사용자 스토리   │ 있음 또는 CONSTRAINT   │ 1.0  │
        │ 4. 인수 조건       │ 1개 이상               │ 1.0  │
        │ 5. 우선순위        │ 설정됨                 │ 1.0  │
        └─────────────────────────────────────────────────────┘

        결과 해석:
        - 1.0 (100%): 완벽하게 정의된 요구사항
        - 0.8 (80%): 대부분 완전, 일부 보완 필요
        - 0.6 (60%): 기본 정보만 있음, 보완 필요
        - 0.4 이하: 불완전, PM 검토 필요

        Args:
            req: 검사할 요구사항

        Returns:
            0.0 ~ 1.0 사이의 완전성 점수
        """
        score = 0.0
        max_score = 5.0

        # 1. 제목 검사: 4자 이상의 의미 있는 제목
        if req.title and len(req.title) > 3:
            score += 1.0

        # 2. 설명 검사: 11자 이상의 상세 설명
        if req.description and len(req.description) > 10:
            score += 1.0

        # 3. 사용자 스토리 검사: FR/NFR은 필수, CONSTRAINT는 면제
        if req.user_story or req.type.value == "CONSTRAINT":
            score += 1.0

        # 4. 인수 조건 검사: 최소 1개 이상
        if req.acceptance_criteria and len(req.acceptance_criteria) > 0:
            score += 1.0

        # 5. 우선순위 검사: HIGH/MEDIUM/LOW 중 하나 설정
        if req.priority:
            score += 1.0

        return score / max_score

    def _check_consistency(self, req: NormalizedRequirement) -> List[str]:
        """Check for consistency issues."""
        issues = []

        # Check for vague terms
        vague_terms = ["등", "기타", "필요시", "적절한", "합리적인", "etc", "등등"]
        for term in vague_terms:
            if term in req.description.lower():
                issues.append(f"모호한 표현 사용: '{term}'")

        # Check for missing info flags
        if req.missing_info:
            for info in req.missing_info[:2]:  # Limit to 2
                issues.append(f"누락된 정보: {info}")

        return issues

    def _check_traceability(self, req: NormalizedRequirement) -> float:
        """Check requirement traceability."""
        score = 0.0

        # Has source reference
        if req.source_reference:
            score += 0.5

        # Has reasonable confidence
        if req.confidence_score > 0.5:
            score += 0.3

        # Has confidence reason
        if req.confidence_reason:
            score += 0.2

        return min(1.0, score)

    def _needs_pm_review(
        self,
        requirement: NormalizedRequirement,
        validation: ValidationResult
    ) -> bool:
        """
        요구사항의 PM 검토 필요 여부 판단.

        4가지 조건 중 하나라도 해당하면 PM 검토가 필요합니다.
        이 메서드는 자동 승인과 수동 검토를 구분하는 핵심 로직입니다.

        PM 검토 조건 4가지:
        ┌─────────────────────────────────────────────────────────────┐
        │ 조건                        │ 기준값                        │
        ├─────────────────────────────────────────────────────────────┤
        │ 1. 낮은 신뢰도              │ confidence < threshold (0.8)  │
        │ 2. 불완전한 요구사항        │ completeness < 0.7 (70%)      │
        │ 3. 일관성 문제              │ consistency_issues 존재       │
        │ 4. 누락 정보                │ missing_info 목록 존재        │
        └─────────────────────────────────────────────────────────────┘

        설정 제어:
        - enable_pm_review=False: PM 검토 비활성화 (모두 자동 승인)
        - auto_approve_threshold: 신뢰도 기준 (기본값 0.8)

        처리 흐름:
        1. PM 검토 기능 활성화 여부 확인
        2. 4가지 조건 순차 검사
        3. 하나라도 해당하면 True 반환

        Args:
            requirement: 검사할 요구사항
            validation: 검증 결과 (completeness, consistency 등)

        Returns:
            PM 검토 필요 여부
        """
        # 설정에서 PM 검토 기능 비활성화 시 항상 False
        if not self.settings.enable_pm_review:
            return False

        threshold = self.settings.auto_approve_threshold

        # 조건 1: 신뢰도가 기준 미만
        if requirement.confidence_score < threshold:
            return True

        # 조건 2: 완전성 점수 70% 미만
        if validation.completeness_score < 0.7:
            return True

        # 조건 3: 일관성 문제 발견
        if validation.consistency_issues:
            return True

        # 조건 4: 누락된 정보 존재
        if requirement.missing_info:
            return True

        return False

    def _compile_review_reasons(
        self,
        requirement: NormalizedRequirement,
        completeness: float,
        consistency_issues: List[str]
    ) -> List[str]:
        """Compile reasons why PM review is needed."""
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
        """Create a review item for PM review."""
        # Determine issue type
        if requirement.confidence_score < 0.5:
            issue_type = ReviewItemType.LOW_CONFIDENCE
        elif requirement.missing_info:
            issue_type = ReviewItemType.MISSING_INFO
        else:
            issue_type = ReviewItemType.AMBIGUOUS

        # Build description
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
        Claude를 사용하여 요구사항 간 충돌 감지.

        서로 상충되거나 동시에 만족할 수 없는 요구사항 쌍을 찾습니다.
        이 기능은 설정으로 활성화/비활성화할 수 있습니다.

        충돌 유형 3가지:
        ┌─────────────────────────────────────────────────────────────────┐
        │ 유형              │ 설명                    │ 예시              │
        ├─────────────────────────────────────────────────────────────────┤
        │ 1. 직접적 모순    │ A와 B가 서로 반대       │ "오프라인 전용" vs│
        │                   │                         │ "실시간 동기화"   │
        ├─────────────────────────────────────────────────────────────────┤
        │ 2. 자원 충돌      │ 같은 자원을 다르게 사용 │ "DB를 MySQL"로 vs │
        │                   │                         │ "DB를 PostgreSQL" │
        ├─────────────────────────────────────────────────────────────────┤
        │ 3. 우선순위 충돌  │ 동시에 만족 불가능      │ "최소 비용" vs    │
        │                   │                         │ "최고 성능"       │
        └─────────────────────────────────────────────────────────────────┘

        처리 흐름:
        1. 충돌 감지 기능 활성화 여부 확인
        2. 요구사항 목록 요약 생성 (최대 20개)
        3. Claude에 충돌 분석 요청
        4. JSON 응답에서 충돌 목록 추출
        5. ReviewItem 객체로 변환

        Args:
            requirements: 검사할 요구사항 목록

        Returns:
            충돌이 발견된 ReviewItem 목록

        Note:
            - 요구사항이 2개 미만이면 빈 목록 반환
            - Claude 호출 실패 시 빈 목록 반환
            - 최대 20개 요구사항만 분석 (성능 최적화)
        """
        # 설정에서 충돌 감지 기능 비활성화 시 건너뛰기
        if not self.settings.enable_conflict_detection:
            return []

        # 요구사항이 2개 미만이면 충돌 불가능
        if len(requirements) < 2:
            return []

        # 요구사항 요약 생성 (Claude 프롬프트용)
        req_summaries = "\n".join([
            f"{req.id}: {req.title} - {req.description[:100]}"
            for req in requirements[:20]  # 성능을 위해 최대 20개로 제한
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

충돌이 없으면 {{"conflicts": []}}를 반환하세요."""

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
                    job_id="",  # Will be set by caller
                    requirement_id=conflict.get("req1_id", ""),
                    issue_type=ReviewItemType.CONFLICT,
                    description=f"충돌 발견: {conflict.get('description', '')}",
                    original_text=f"{conflict.get('req1_id')} vs {conflict.get('req2_id')}",
                    suggested_resolution=f"두 요구사항 검토 필요: {conflict.get('conflict_type', '')}",
                ))

            return review_items

        except Exception as e:
            print(f"Conflict detection failed: {e}")
            return []
