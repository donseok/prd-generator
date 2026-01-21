"""PRD document generator for Layer 4."""

from typing import List, Optional
from datetime import datetime
import uuid

from app.models import (
    NormalizedRequirement,
    RequirementType,
    PRDDocument,
    PRDOverview,
    PRDMetadata,
    Milestone,
    UnresolvedItem,
)
from app.services import ClaudeClient, get_claude_client


class PRDGenerator:
    """
    Layer 4: PRD document generation.

    Generates complete PRD documents from validated requirements.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()

    async def generate(
        self,
        requirements: List[NormalizedRequirement],
        source_documents: List[str] = None,
        context: dict = None
    ) -> PRDDocument:
        """
        Generate complete PRD document from validated requirements.

        Args:
            requirements: List of validated requirements
            source_documents: List of source document names
            context: Optional additional context

        Returns:
            Complete PRDDocument
        """
        # Categorize requirements
        functional = [r for r in requirements if r.type == RequirementType.FUNCTIONAL]
        non_functional = [r for r in requirements if r.type == RequirementType.NON_FUNCTIONAL]
        constraints = [r for r in requirements if r.type == RequirementType.CONSTRAINT]

        # Generate overview using Claude
        overview = await self._generate_overview(requirements, context)

        # Generate milestones
        milestones = await self._generate_milestones(requirements)

        # Collect unresolved items
        unresolved = self._collect_unresolved_items(requirements)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(requirements)

        # Build metadata
        metadata = PRDMetadata(
            version="1.0",
            status="draft",
            author="PRD Generator",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_documents=source_documents or [],
            overall_confidence=overall_confidence,
            requires_pm_review=overall_confidence < 0.8,
            pm_review_reasons=self._get_review_reasons(requirements),
        )

        # Generate PRD ID
        prd_id = f"PRD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"

        # Generate title
        title = await self._generate_title(requirements, context)

        return PRDDocument(
            id=prd_id,
            title=title,
            overview=overview,
            functional_requirements=functional,
            non_functional_requirements=non_functional,
            constraints=constraints,
            milestones=milestones,
            unresolved_items=unresolved,
            metadata=metadata,
        )

    async def _generate_overview(
        self,
        requirements: List[NormalizedRequirement],
        context: dict = None
    ) -> PRDOverview:
        """Generate PRD overview section using Claude."""
        # Build requirements summary
        req_summary = "\n".join([
            f"- {req.title}: {req.description[:100]}"
            for req in requirements[:15]
        ])

        prompt = f"""다음 요구사항들을 기반으로 PRD 개요를 작성해주세요.

요구사항 요약:
{req_summary}

추가 컨텍스트:
{context or '없음'}

JSON 형식으로 응답:
{{
  "background": "프로젝트 배경 (2-3문장)",
  "goals": ["목표 1", "목표 2", "목표 3"],
  "scope": "프로젝트 범위 설명",
  "out_of_scope": ["범위 외 항목 1", "범위 외 항목 2"],
  "target_users": ["대상 사용자 1", "대상 사용자 2"],
  "success_metrics": ["성공 지표 1", "성공 지표 2"]
}}"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="당신은 PRD 문서 작성 전문가입니다. 주어진 요구사항을 분석하여 명확하고 실행 가능한 개요를 작성합니다.",
                user_prompt=prompt,
                temperature=0.3,
            )

            return PRDOverview(
                background=result.get("background", "프로젝트 배경 정보가 필요합니다."),
                goals=result.get("goals", ["목표 정의 필요"]),
                scope=result.get("scope", "범위 정의 필요"),
                out_of_scope=result.get("out_of_scope", []),
                target_users=result.get("target_users", ["대상 사용자 정의 필요"]),
                success_metrics=result.get("success_metrics", []),
            )

        except Exception as e:
            print(f"Overview generation failed: {e}")
            return PRDOverview(
                background="자동 생성 실패 - 수동 입력 필요",
                goals=["목표 정의 필요"],
                scope="범위 정의 필요",
            )

    async def _generate_milestones(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[Milestone]:
        """Generate project milestones based on requirements."""
        if not requirements:
            return []

        # Group by priority
        high_priority = [r for r in requirements if r.priority.value == "HIGH"]
        medium_priority = [r for r in requirements if r.priority.value == "MEDIUM"]
        low_priority = [r for r in requirements if r.priority.value == "LOW"]

        milestones = []

        # MVP milestone (high priority)
        if high_priority:
            milestones.append(Milestone(
                id="MS-001",
                name="MVP (Minimum Viable Product)",
                description="핵심 기능 구현",
                deliverables=[r.title for r in high_priority[:5]],
                dependencies=[],
                order=1,
            ))

        # Phase 2 (medium priority)
        if medium_priority:
            milestones.append(Milestone(
                id="MS-002",
                name="Phase 2 - 기능 확장",
                description="추가 기능 구현",
                deliverables=[r.title for r in medium_priority[:5]],
                dependencies=["MS-001"] if high_priority else [],
                order=2,
            ))

        # Phase 3 (low priority)
        if low_priority:
            milestones.append(Milestone(
                id="MS-003",
                name="Phase 3 - 개선",
                description="부가 기능 및 개선",
                deliverables=[r.title for r in low_priority[:5]],
                dependencies=["MS-002"] if medium_priority else ["MS-001"] if high_priority else [],
                order=3,
            ))

        return milestones

    async def _generate_title(
        self,
        requirements: List[NormalizedRequirement],
        context: dict = None
    ) -> str:
        """Generate PRD title."""
        if context and context.get("title"):
            return context["title"]

        # Use Claude to generate title
        req_titles = ", ".join([r.title for r in requirements[:5]])

        try:
            result = await self.claude_client.complete(
                system_prompt="당신은 PRD 제목을 생성하는 전문가입니다. 간결하고 명확한 제목을 생성합니다.",
                user_prompt=f"다음 요구사항들을 포괄하는 PRD 제목을 한 줄로 작성해주세요 (20자 이내):\n{req_titles}",
                temperature=0.5,
                max_tokens=50,
            )
            return result.strip().strip('"').strip("'")
        except:
            return f"PRD - {datetime.now().strftime('%Y년 %m월')}"

    def _collect_unresolved_items(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[UnresolvedItem]:
        """Collect unresolved items from requirements."""
        items = []
        item_counter = 1

        for req in requirements:
            # Missing info becomes questions
            for missing in req.missing_info:
                items.append(UnresolvedItem(
                    id=f"UNR-{item_counter:03d}",
                    type="question",
                    description=missing,
                    related_requirement_ids=[req.id],
                    priority="MEDIUM",
                    suggested_action="PM에게 확인 필요",
                ))
                item_counter += 1

            # Assumptions become items to verify
            for assumption in req.assumptions:
                items.append(UnresolvedItem(
                    id=f"UNR-{item_counter:03d}",
                    type="decision",
                    description=f"가정 확인 필요: {assumption}",
                    related_requirement_ids=[req.id],
                    priority="LOW",
                    suggested_action="이해관계자와 확인",
                ))
                item_counter += 1

        return items[:20]  # Limit to 20 items

    def _calculate_overall_confidence(
        self,
        requirements: List[NormalizedRequirement]
    ) -> float:
        """Calculate overall PRD confidence score."""
        if not requirements:
            return 0.0

        scores = [r.confidence_score for r in requirements]
        return sum(scores) / len(scores)

    def _get_review_reasons(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[str]:
        """Get reasons why PM review might be needed."""
        reasons = []

        low_confidence = [r for r in requirements if r.confidence_score < 0.8]
        if low_confidence:
            reasons.append(f"{len(low_confidence)}개 요구사항의 신뢰도가 80% 미만")

        with_missing = [r for r in requirements if r.missing_info]
        if with_missing:
            reasons.append(f"{len(with_missing)}개 요구사항에 누락 정보 존재")

        with_assumptions = [r for r in requirements if r.assumptions]
        if with_assumptions:
            reasons.append(f"{len(with_assumptions)}개 요구사항에 확인 필요한 가정 존재")

        return reasons
