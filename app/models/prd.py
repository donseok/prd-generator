"""PRD document data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .requirement import NormalizedRequirement


class PRDOverview(BaseModel):
    """PRD document overview section."""

    background: str = Field(..., description="Project background")
    goals: list[str] = Field(..., description="Project goals")
    scope: str = Field(..., description="Project scope")
    out_of_scope: list[str] = Field(default_factory=list, description="Out of scope items")
    target_users: list[str] = Field(default_factory=list, description="Target user groups")
    success_metrics: list[str] = Field(default_factory=list, description="Success metrics/KPIs")


class Milestone(BaseModel):
    """Project milestone."""

    id: str
    name: str
    description: str
    deliverables: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    order: int = 0


class UnresolvedItem(BaseModel):
    """Unresolved item requiring attention."""

    id: str
    type: str = Field(..., description="Type: question, decision, risk, dependency")
    description: str
    related_requirement_ids: list[str] = Field(default_factory=list)
    priority: str = "MEDIUM"
    suggested_action: Optional[str] = None


class PRDMetadata(BaseModel):
    """PRD document metadata."""

    version: str = "1.0"
    status: str = "draft"  # draft, review, approved
    author: str = "PRD Generator"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_documents: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    requires_pm_review: bool = False
    pm_review_reasons: list[str] = Field(default_factory=list)


class PRDDocument(BaseModel):
    """Complete PRD document."""

    id: str = Field(..., description="PRD document ID")
    title: str = Field(..., description="PRD title")
    overview: PRDOverview
    functional_requirements: list[NormalizedRequirement] = Field(default_factory=list)
    non_functional_requirements: list[NormalizedRequirement] = Field(default_factory=list)
    constraints: list[NormalizedRequirement] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = Field(default_factory=list)
    metadata: PRDMetadata = Field(default_factory=PRDMetadata)

    def to_markdown(self) -> str:
        """Convert PRD to Markdown format."""
        lines = []

        # Title and metadata
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**버전**: {self.metadata.version} | **상태**: {self.metadata.status} | **신뢰도**: {self.metadata.overall_confidence:.0%}")
        lines.append(f"**생성일**: {self.metadata.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # Overview
        lines.append("## 1. 개요")
        lines.append("")
        lines.append("### 배경")
        lines.append(self.overview.background)
        lines.append("")

        lines.append("### 목표")
        for goal in self.overview.goals:
            lines.append(f"- {goal}")
        lines.append("")

        lines.append("### 범위")
        lines.append(self.overview.scope)
        lines.append("")

        if self.overview.out_of_scope:
            lines.append("### 범위 외")
            for item in self.overview.out_of_scope:
                lines.append(f"- {item}")
            lines.append("")

        if self.overview.target_users:
            lines.append("### 대상 사용자")
            for user in self.overview.target_users:
                lines.append(f"- {user}")
            lines.append("")

        if self.overview.success_metrics:
            lines.append("### 성공 지표")
            for metric in self.overview.success_metrics:
                lines.append(f"- {metric}")
            lines.append("")

        # Functional Requirements
        if self.functional_requirements:
            lines.append("## 2. 기능 요구사항 (FR)")
            lines.append("")
            for req in self.functional_requirements:
                lines.append(f"### {req.id}: {req.title}")
                lines.append(f"**우선순위**: {req.priority.value} | **신뢰도**: {req.confidence_score:.0%}")
                if req.source_reference:
                    lines.append(f" | **출처**: {req.source_reference}")
                lines.append("")
                lines.append(req.description)
                lines.append("")
                if req.user_story:
                    lines.append(f"**User Story**: {req.user_story}")
                    lines.append("")
                if req.acceptance_criteria:
                    lines.append("**Acceptance Criteria**:")
                    for ac in req.acceptance_criteria:
                        lines.append(f"- [ ] {ac}")
                    lines.append("")

        # Non-Functional Requirements
        if self.non_functional_requirements:
            lines.append("## 3. 비기능 요구사항 (NFR)")
            lines.append("")
            for req in self.non_functional_requirements:
                lines.append(f"### {req.id}: {req.title}")
                lines.append(f"**우선순위**: {req.priority.value} | **신뢰도**: {req.confidence_score:.0%}")
                if req.source_reference:
                    lines.append(f" | **출처**: {req.source_reference}")
                lines.append("")
                lines.append(req.description)
                lines.append("")

        # Constraints
        if self.constraints:
            lines.append("## 4. 제약조건")
            lines.append("")
            for req in self.constraints:
                lines.append(f"### {req.id}: {req.title}")
                if req.source_reference:
                    lines.append(f"**출처**: {req.source_reference}")
                lines.append(req.description)
                lines.append("")

        # Milestones
        if self.milestones:
            lines.append("## 5. 마일스톤")
            lines.append("")
            for ms in sorted(self.milestones, key=lambda x: x.order):
                lines.append(f"### {ms.name}")
                lines.append(ms.description)
                if ms.deliverables:
                    lines.append("**산출물**:")
                    for d in ms.deliverables:
                        lines.append(f"- {d}")
                lines.append("")

        # Unresolved Items
        if self.unresolved_items:
            lines.append("## 6. 미해결 사항")
            lines.append("")
            for item in self.unresolved_items:
                lines.append(f"- **[{item.type.upper()}]** {item.description}")
                if item.suggested_action:
                    lines.append(f"  - 제안: {item.suggested_action}")
            lines.append("")

        # Source Documents
        if self.metadata.source_documents:
            lines.append("## 출처 문서")
            lines.append("")
            lines.append("이 PRD는 다음 문서들을 기반으로 생성되었습니다:")
            lines.append("")
            for idx, doc in enumerate(self.metadata.source_documents, 1):
                lines.append(f"{idx}. {doc}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*이 문서는 PRD 자동 생성 시스템에 의해 작성되었습니다.*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Convert PRD to JSON format."""
        return self.model_dump_json(indent=2)
