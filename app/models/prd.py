"""
PRD (제품 요구사항 정의서) 데이터 모델입니다.
최종적으로 생성되는 문서의 구조를 정의합니다.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .requirement import NormalizedRequirement


class PRDOverview(BaseModel):
    """PRD의 개요 섹션입니다. 프로젝트의 전반적인 내용을 담습니다."""

    background: str = Field(..., description="프로젝트 추진 배경")
    goals: list[str] = Field(..., description="프로젝트 목표 목록")
    scope: str = Field(..., description="프로젝트 범위 (할 것)")
    out_of_scope: list[str] = Field(default_factory=list, description="범위 제외 사항 (안 할 것)")
    target_users: list[str] = Field(default_factory=list, description="주요 타겟 사용자 그룹")
    success_metrics: list[str] = Field(default_factory=list, description="성공 판단 기준 (KPI)")


class Milestone(BaseModel):
    """프로젝트 주요 마일스톤(단계별 목표)입니다."""

    id: str
    name: str = "마일스톤 이름"
    description: str = "설명"
    deliverables: list[str] = Field(default_factory=list) # 산출물 목록
    dependencies: list[str] = Field(default_factory=list) # 의존성 (선행 작업 등)
    order: int = 0  # 순서


class UnresolvedItem(BaseModel):
    """아직 해결되지 않은 이슈나 질문 사항입니다."""

    id: str
    type: str = Field(..., description="유형: 질문(question), 결정필요(decision), 위험(risk) 등")
    description: str
    related_requirement_ids: list[str] = Field(default_factory=list) # 관련된 요구사항 ID들
    priority: str = "MEDIUM" # 중요도
    suggested_action: Optional[str] = None # 제안하는 해결 방안


class PRDMetadata(BaseModel):
    """PRD 문서의 메타데이터입니다."""

    version: str = "1.0"
    status: str = "draft"  # draft(초안), review(검토중), approved(승인됨)
    author: str = "PRD Generator"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_documents: list[str] = Field(default_factory=list) # 참고한 원본 문서들
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0) # AI의 전체 확신도 (0~1)
    requires_pm_review: bool = False # 기획자 검토 필요 여부
    pm_review_reasons: list[str] = Field(default_factory=list) # 검토가 필요한 이유들


class PRDDocument(BaseModel):
    """
    완성된 PRD 문서를 나타내는 메인 클래스입니다.
    """

    id: str = Field(..., description="PRD 문서 ID")
    title: str = Field(..., description="프로젝트 제목")
    overview: PRDOverview # 개요
    functional_requirements: list[NormalizedRequirement] = Field(default_factory=list) # 기능 요구사항
    non_functional_requirements: list[NormalizedRequirement] = Field(default_factory=list) # 비기능 요구사항
    constraints: list[NormalizedRequirement] = Field(default_factory=list) # 제약사항
    milestones: list[Milestone] = Field(default_factory=list) # 마일스톤
    unresolved_items: list[UnresolvedItem] = Field(default_factory=list) # 미해결 항목
    metadata: PRDMetadata = Field(default_factory=PRDMetadata) # 메타데이터

    def to_markdown(self) -> str:
        """PRD 내용을 마크다운(Markdown) 텍스트로 변환하는 함수"""
        lines = []

        # 제목 및 메타정보
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**버전**: {self.metadata.version} | **상태**: {self.metadata.status} | **신뢰도**: {self.metadata.overall_confidence:.0%}")
        lines.append(f"**생성일**: {self.metadata.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # 1. 개요
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

        # 2. 기능 요구사항 (FR)
        if self.functional_requirements:
            lines.append("## 2. 기능 요구사항 (FR)")
            lines.append("")
            for req in self.functional_requirements:
                lines.append(f"### {req.id}: {req.title}")
                
                # 출처 표시 문자열 생성
                source_display = ""
                if req.source_info:
                    source_display = req.source_info.to_display_string()
                elif req.source_reference:
                    source_display = req.source_reference

                lines.append(f"**우선순위**: {req.priority.value} | **신뢰도**: {req.confidence_score:.0%}")
                if source_display:
                    lines.append(f"**출처**: {source_display}")
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
                # 원문 발췌가 있으면 표시
                if req.source_info and req.source_info.excerpt:
                    lines.append(f"> 원문: \"{req.source_info.excerpt}\"")
                    lines.append("")

        # 3. 비기능 요구사항 (NFR)
        if self.non_functional_requirements:
            lines.append("## 3. 비기능 요구사항 (NFR)")
            lines.append("")
            for req in self.non_functional_requirements:
                lines.append(f"### {req.id}: {req.title}")
                source_display = ""
                if req.source_info:
                    source_display = req.source_info.to_display_string()
                elif req.source_reference:
                    source_display = req.source_reference

                lines.append(f"**우선순위**: {req.priority.value} | **신뢰도**: {req.confidence_score:.0%}")
                if source_display:
                    lines.append(f"**출처**: {source_display}")
                lines.append("")
                lines.append(req.description)
                lines.append("")
                if req.source_info and req.source_info.excerpt:
                    lines.append(f"> 원문: \"{req.source_info.excerpt}\"")
                    lines.append("")

        # 4. 제약조건
        if self.constraints:
            lines.append("## 4. 제약조건")
            lines.append("")
            for req in self.constraints:
                lines.append(f"### {req.id}: {req.title}")
                source_display = ""
                if req.source_info:
                    source_display = req.source_info.to_display_string()
                elif req.source_reference:
                    source_display = req.source_reference

                if source_display:
                    lines.append(f"**출처**: {source_display}")
                lines.append(req.description)
                lines.append("")
                if req.source_info and req.source_info.excerpt:
                    lines.append(f"> 원문: \"{req.source_info.excerpt}\"")
                    lines.append("")

        # 5. 마일스톤
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

        # 6. 미해결 사항
        if self.unresolved_items:
            lines.append("## 6. 미해결 사항")
            lines.append("")
            for item in self.unresolved_items:
                lines.append(f"- **[{item.type.upper()}]** {item.description}")
                if item.suggested_action:
                    lines.append(f"  - 제안: {item.suggested_action}")
            lines.append("")

        # 출처 문서 목록
        if self.metadata.source_documents:
            lines.append("## 출처 문서")
            lines.append("")
            lines.append("이 PRD는 다음 문서들을 기반으로 생성되었습니다:")
            lines.append("")
            for idx, doc in enumerate(self.metadata.source_documents, 1):
                lines.append(f"{idx}. {doc}")
            lines.append("")

        # 바닥글
        lines.append("---")
        lines.append("*이 문서는 PRD 자동 생성 시스템에 의해 작성되었습니다.*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """JSON 포맷으로 변환하는 함수"""
        return self.model_dump_json(indent=2)