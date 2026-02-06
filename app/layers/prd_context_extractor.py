"""PRD 컨텍스트 추출 유틸리티입니다.

PRD 문서에서 TRD, WBS, Proposal 생성에 필요한 풍부한 컨텍스트를 추출합니다.
이전에는 각 생성기에서 제한적인 정보만 사용했지만,
이 모듈을 통해 PRD의 모든 유용한 정보를 일관되게 활용할 수 있습니다.

개선 포인트:
- 요구사항 제목뿐만 아니라 설명, 인수조건, 사용자 스토리까지 포함
- missing_info, assumptions를 통한 리스크 사전 파악
- 신뢰도 기반 우선순위화
- 카테고리별 그룹화로 구조화된 정보 제공
"""

from typing import Optional
from dataclasses import dataclass, field

from app.models import PRDDocument, RequirementType


@dataclass
class RequirementSummary:
    """요구사항 요약 정보"""
    id: str
    title: str
    description: str
    type: str
    priority: str
    confidence: float
    user_story: Optional[str] = None
    acceptance_criteria: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)


@dataclass
class PRDContext:
    """PRD에서 추출한 풍부한 컨텍스트"""

    # 기본 정보
    title: str
    background: str
    scope: str
    goals: list[str]
    success_metrics: list[str]
    out_of_scope: list[str]

    # 요구사항 요약 (구조화)
    functional_requirements: list[RequirementSummary]
    non_functional_requirements: list[RequirementSummary]
    constraints: list[RequirementSummary]

    # 통계
    total_requirements: int
    high_priority_count: int
    low_confidence_count: int
    avg_confidence: float

    # 특수 정보
    all_assumptions: list[str]  # 모든 요구사항의 가정사항 통합
    all_missing_info: list[str]  # 모든 불명확 정보 통합
    all_acceptance_criteria: list[str]  # 주요 인수조건 통합

    # 마일스톤
    milestones: list[dict]

    # 미해결 사항
    unresolved_items: list[dict]


class PRDContextExtractor:
    """PRD에서 생성기용 컨텍스트를 추출하는 클래스"""

    def __init__(self, max_text_length: int = 300):
        """
        Args:
            max_text_length: 텍스트 필드 최대 길이 (AI 프롬프트 크기 제한용)
        """
        self.max_text_length = max_text_length

    def extract(self, prd: PRDDocument) -> PRDContext:
        """PRD에서 풍부한 컨텍스트를 추출합니다."""

        # 요구사항 변환
        fr_summaries = self._convert_requirements(prd.functional_requirements, "FR")
        nfr_summaries = self._convert_requirements(prd.non_functional_requirements, "NFR")
        constraint_summaries = self._convert_requirements(prd.constraints, "CONSTRAINT")

        all_reqs = prd.functional_requirements + prd.non_functional_requirements + prd.constraints

        # 통계 계산
        total = len(all_reqs)
        high_priority = sum(1 for r in all_reqs if r.priority.value == "HIGH")
        low_confidence = sum(1 for r in all_reqs if r.confidence_score < 0.7)
        avg_confidence = sum(r.confidence_score for r in all_reqs) / max(total, 1)

        # 통합 정보 수집
        all_assumptions = []
        all_missing = []
        all_criteria = []

        for req in all_reqs:
            all_assumptions.extend(req.assumptions[:2])
            all_missing.extend(req.missing_info[:2])
            all_criteria.extend(req.acceptance_criteria[:2])

        # 중복 제거 및 제한
        all_assumptions = list(dict.fromkeys(all_assumptions))[:20]
        all_missing = list(dict.fromkeys(all_missing))[:20]
        all_criteria = list(dict.fromkeys(all_criteria))[:30]

        # 마일스톤 변환
        milestones = [
            {
                "name": m.name,
                "description": m.description,
                "order": m.order,
                "deliverables": m.deliverables[:5],
            }
            for m in prd.milestones
        ]

        # 미해결 사항 변환
        unresolved = [
            {
                "issue": u.issue,
                "priority": u.priority,
                "suggested_solution": u.suggested_solution,
            }
            for u in prd.unresolved_items[:10]
        ]

        return PRDContext(
            title=prd.title,
            background=self._truncate(prd.overview.background),
            scope=self._truncate(prd.overview.scope) if prd.overview.scope else "",
            goals=prd.overview.goals[:10],
            success_metrics=prd.overview.success_metrics[:10] if prd.overview.success_metrics else [],
            out_of_scope=prd.overview.out_of_scope[:10] if prd.overview.out_of_scope else [],
            functional_requirements=fr_summaries,
            non_functional_requirements=nfr_summaries,
            constraints=constraint_summaries,
            total_requirements=total,
            high_priority_count=high_priority,
            low_confidence_count=low_confidence,
            avg_confidence=round(avg_confidence, 2),
            all_assumptions=all_assumptions,
            all_missing_info=all_missing,
            all_acceptance_criteria=all_criteria,
            milestones=milestones,
            unresolved_items=unresolved,
        )

    def _convert_requirements(self, requirements, req_type: str) -> list[RequirementSummary]:
        """요구사항을 요약 형태로 변환합니다."""
        summaries = []

        for req in requirements:
            summaries.append(RequirementSummary(
                id=req.id,
                title=req.title,
                description=self._truncate(req.description),
                type=req_type,
                priority=req.priority.value,
                confidence=req.confidence_score,
                user_story=req.user_story,
                acceptance_criteria=req.acceptance_criteria[:5],
                assumptions=req.assumptions[:3],
                missing_info=req.missing_info[:3],
            ))

        return summaries

    def _truncate(self, text: str) -> str:
        """텍스트를 최대 길이로 자릅니다."""
        if not text:
            return ""
        if len(text) <= self.max_text_length:
            return text
        return text[:self.max_text_length - 3] + "..."

    def to_prompt_text(self, prd: PRDDocument, include_details: bool = False) -> str:
        """
        AI 프롬프트에 사용할 수 있는 텍스트 형식으로 변환합니다.

        Args:
            prd: PRD 문서
            include_details: True면 인수조건, 가정사항 등 상세 정보 포함

        Returns:
            프롬프트용 텍스트
        """
        ctx = self.extract(prd)

        lines = [
            f"# 프로젝트: {ctx.title}",
            "",
            "## 배경",
            ctx.background,
            "",
            "## 목표",
        ]

        for goal in ctx.goals[:5]:
            lines.append(f"- {goal}")

        # 기능 요구사항
        lines.extend([
            "",
            f"## 기능 요구사항 (총 {len(ctx.functional_requirements)}개)",
        ])

        for req in ctx.functional_requirements[:20]:
            priority_mark = "★" if req.priority == "HIGH" else ""
            lines.append(f"- [{req.id}] {req.title} {priority_mark}")
            if include_details and req.description:
                lines.append(f"  설명: {req.description[:150]}")
            if include_details and req.acceptance_criteria:
                for ac in req.acceptance_criteria[:2]:
                    lines.append(f"  ✓ {ac}")

        # 비기능 요구사항
        lines.extend([
            "",
            f"## 비기능 요구사항 (총 {len(ctx.non_functional_requirements)}개)",
        ])

        for req in ctx.non_functional_requirements[:10]:
            lines.append(f"- [{req.id}] {req.title}")
            if include_details and req.description:
                lines.append(f"  {req.description[:100]}")

        # 제약사항
        if ctx.constraints:
            lines.extend([
                "",
                f"## 제약사항 (총 {len(ctx.constraints)}개)",
            ])
            for req in ctx.constraints[:5]:
                lines.append(f"- [{req.id}] {req.title}")

        # 통계 정보
        lines.extend([
            "",
            "## 통계",
            f"- 총 요구사항: {ctx.total_requirements}개",
            f"- HIGH 우선순위: {ctx.high_priority_count}개",
            f"- 평균 신뢰도: {ctx.avg_confidence:.0%}",
        ])

        # 상세 정보 (옵션)
        if include_details:
            if ctx.all_missing_info:
                lines.extend([
                    "",
                    "## 불명확한 정보 (리스크)",
                ])
                for info in ctx.all_missing_info[:10]:
                    lines.append(f"- {info}")

            if ctx.all_assumptions:
                lines.extend([
                    "",
                    "## 가정사항",
                ])
                for assumption in ctx.all_assumptions[:10]:
                    lines.append(f"- {assumption}")

        return "\n".join(lines)

    def get_risk_indicators(self, prd: PRDDocument) -> dict:
        """
        PRD에서 리스크 지표를 추출합니다.
        TRD 리스크 분석이나 Proposal 리스크 섹션에 활용됩니다.
        """
        ctx = self.extract(prd)

        indicators = {
            "low_confidence_requirements": [],
            "missing_info_items": ctx.all_missing_info,
            "unresolved_items": ctx.unresolved_items,
            "integration_requirements": [],
            "real_time_requirements": [],
            "security_requirements": [],
        }

        # 신뢰도 낮은 요구사항
        for req in ctx.functional_requirements + ctx.non_functional_requirements:
            if req.confidence < 0.7:
                indicators["low_confidence_requirements"].append({
                    "id": req.id,
                    "title": req.title,
                    "confidence": req.confidence,
                })

        # 키워드 기반 분류
        all_reqs = ctx.functional_requirements + ctx.non_functional_requirements + ctx.constraints

        for req in all_reqs:
            text = f"{req.title} {req.description}".lower()

            if any(kw in text for kw in ["연동", "통합", "api", "인터페이스", "외부"]):
                indicators["integration_requirements"].append(req.id)

            if any(kw in text for kw in ["실시간", "real-time", "즉시", "push", "websocket"]):
                indicators["real_time_requirements"].append(req.id)

            if any(kw in text for kw in ["보안", "인증", "권한", "암호화", "security"]):
                indicators["security_requirements"].append(req.id)

        return indicators


# 싱글톤 인스턴스
_extractor_instance: Optional[PRDContextExtractor] = None


def get_prd_context_extractor() -> PRDContextExtractor:
    """PRDContextExtractor 싱글톤 인스턴스 반환"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = PRDContextExtractor()
    return _extractor_instance
