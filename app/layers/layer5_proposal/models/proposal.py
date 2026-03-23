"""Proposal document models for customer proposals."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.common import RiskLevel, BaseDocumentMetadata


class ProposalContext(BaseModel):
    """제안서 생성 컨텍스트."""
    client_name: str = Field(..., description="고객사명")
    project_name: Optional[str] = Field(None, description="프로젝트명 (없으면 PRD 제목 사용)")
    submission_date: Optional[str] = Field(None, description="제출 예정일")
    project_start_date: Optional[str] = Field(None, description="프로젝트 시작 예정일")
    project_duration_months: Optional[int] = Field(None, description="프로젝트 기간 (개월)")
    include_pricing: bool = Field(False, description="견적 포함 여부")
    additional_notes: Optional[str] = Field(None, description="추가 참고사항")


class ProposalMetadata(BaseModel):
    """제안서 메타데이터."""
    version: str = "1.0"
    status: str = "DRAFT"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    source_prd_id: str = Field(..., description="원본 PRD ID")
    source_prd_title: str = Field(..., description="원본 PRD 제목")
    overall_confidence: float = Field(0.0, description="전체 신뢰도")


class ProjectOverview(BaseModel):
    """프로젝트 개요."""
    background: str = Field(..., description="프로젝트 배경")
    objectives: list[str] = Field(default_factory=list, description="프로젝트 목표")
    success_criteria: list[str] = Field(default_factory=list, description="성공 기준")


class ScopeOfWork(BaseModel):
    """작업 범위."""
    in_scope: list[str] = Field(default_factory=list, description="포함 범위")
    out_of_scope: list[str] = Field(default_factory=list, description="제외 범위")
    key_features: list[dict] = Field(default_factory=list, description="주요 기능 목록")


class SolutionApproach(BaseModel):
    """솔루션 접근법."""
    overview: str = Field("", description="솔루션 개요")
    architecture: str = Field("", description="시스템 아키텍처 설명")
    technology_stack: list[str] = Field(default_factory=list, description="기술 스택")
    methodology: str = Field("", description="개발 방법론")
    key_differentiators: list[str] = Field(default_factory=list, description="차별화 요소")


class TimelinePhase(BaseModel):
    """일정 단계."""
    phase_name: str = Field(..., description="단계명")
    duration: str = Field(..., description="기간")
    start_date: Optional[str] = Field(None, description="시작일")
    end_date: Optional[str] = Field(None, description="종료일")
    deliverables: list[str] = Field(default_factory=list, description="산출물")
    description: str = Field("", description="단계 설명")


class Timeline(BaseModel):
    """일정 계획."""
    total_duration: str = Field("", description="전체 기간")
    phases: list[TimelinePhase] = Field(default_factory=list, description="단계별 일정")


class Deliverable(BaseModel):
    """산출물."""
    name: str = Field(..., description="산출물명")
    description: str = Field("", description="설명")
    phase: str = Field("", description="해당 단계")


class TeamMember(BaseModel):
    """팀원."""
    role: str = Field(..., description="역할")
    count: int = Field(1, description="인원수")
    responsibilities: list[str] = Field(default_factory=list, description="담당 업무")


class ResourcePlan(BaseModel):
    """투입 인력 계획."""
    team_structure: list[TeamMember] = Field(default_factory=list, description="팀 구성")
    total_man_months: Optional[float] = Field(None, description="총 M/M")


class Risk(BaseModel):
    """리스크."""
    description: str = Field(..., description="리스크 설명")
    level: RiskLevel = Field(RiskLevel.MEDIUM, description="위험도")
    impact: str = Field("", description="영향")
    mitigation: str = Field("", description="대응방안")
    source_requirement_id: Optional[str] = Field(None, description="관련 요구사항 ID")


class InvestmentSummary(BaseModel):
    """투자 요약."""
    total_cost_estimate: str = Field("", description="총 투자 비용 추정")
    expected_annual_savings: str = Field("", description="연간 예상 절감액")
    payback_period: str = Field("", description="투자 회수 기간")


class ProposalDocument(BaseModel):
    """고객 제안서 문서."""

    # 기본 정보
    id: str = Field(..., description="제안서 ID")
    title: str = Field(..., description="제안서 제목")
    client_name: str = Field(..., description="고객사명")

    # 제안서 섹션
    executive_summary: str = Field("", description="경영진 요약")
    project_overview: ProjectOverview = Field(default_factory=ProjectOverview)
    scope_of_work: ScopeOfWork = Field(default_factory=ScopeOfWork)
    solution_approach: SolutionApproach = Field(default_factory=SolutionApproach)
    timeline: Timeline = Field(default_factory=Timeline)
    deliverables: list[Deliverable] = Field(default_factory=list)
    resource_plan: ResourcePlan = Field(default_factory=ResourcePlan)
    risks: list[Risk] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    expected_benefits: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)

    # 신규 섹션 (backward compatible with defaults)
    competitive_analysis: Optional[list[dict]] = Field(default=None, description="현재 방식 vs 제안 솔루션 비교")
    investment_summary: Optional[InvestmentSummary] = Field(default=None, description="투자 요약")

    # 메타데이터
    metadata: ProposalMetadata

    def to_markdown(self) -> str:
        """마크다운 형식의 제안서 생성."""
        lines = []

        # 헤더
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**고객사**: {self.client_name}")
        lines.append(f"**제출일**: {self.metadata.created_at.strftime('%Y-%m-%d')}")
        lines.append(f"**버전**: {self.metadata.version}")
        lines.append(f"**문서 신뢰도**: {self.metadata.overall_confidence:.0%}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. 경영진 요약
        if self.executive_summary:
            lines.append("## 1. 경영진 요약")
            lines.append("")
            lines.append(self.executive_summary)
            lines.append("")

            # 투자 요약 박스 (경영진 요약 바로 뒤)
            if self.investment_summary:
                lines.append("### 투자 수익 요약")
                lines.append("")
                lines.append("> | 항목 | 내용 |")
                lines.append("> |------|------|")
                lines.append(f"> | **총 투자 비용 (추정)** | {self.investment_summary.total_cost_estimate} |")
                lines.append(f"> | **연간 예상 절감액** | {self.investment_summary.expected_annual_savings} |")
                lines.append(f"> | **투자 회수 기간** | {self.investment_summary.payback_period} |")
                lines.append("")

        # 2. 프로젝트 개요
        lines.append("## 2. 프로젝트 개요")
        lines.append("")

        lines.append("### 2.1 배경")
        lines.append("")
        lines.append(self.project_overview.background)
        lines.append("")

        if self.project_overview.objectives:
            lines.append("### 2.2 목표")
            lines.append("")
            for obj in self.project_overview.objectives:
                lines.append(f"- {obj}")
            lines.append("")

        if self.project_overview.success_criteria:
            lines.append("### 2.3 성공 기준")
            lines.append("")
            for criteria in self.project_overview.success_criteria:
                lines.append(f"- {criteria}")
            lines.append("")

        # 3. 작업 범위
        lines.append("## 3. 작업 범위")
        lines.append("")

        if self.scope_of_work.in_scope:
            lines.append("### 3.1 포함 범위")
            lines.append("")
            for item in self.scope_of_work.in_scope:
                lines.append(f"- {item}")
            lines.append("")

        if self.scope_of_work.out_of_scope:
            lines.append("### 3.2 제외 범위")
            lines.append("")
            for item in self.scope_of_work.out_of_scope:
                lines.append(f"- {item}")
            lines.append("")

        if self.scope_of_work.key_features:
            lines.append("### 3.3 주요 기능")
            lines.append("")
            for feature in self.scope_of_work.key_features:
                name = feature.get("name", "")
                desc = feature.get("description", "")
                count = feature.get("count", 0)
                lines.append(f"#### {name}")
                if desc:
                    lines.append(f"{desc}")
                if count:
                    lines.append(f"- 관련 요구사항: {count}건")
                lines.append("")

        # 4. 솔루션 접근법
        lines.append("## 4. 솔루션 접근법")
        lines.append("")

        if self.solution_approach.overview:
            lines.append("### 4.1 솔루션 개요")
            lines.append("")
            lines.append(self.solution_approach.overview)
            lines.append("")

        if self.solution_approach.architecture:
            lines.append("### 4.2 시스템 아키텍처")
            lines.append("")
            lines.append(self.solution_approach.architecture)
            lines.append("")

        if self.solution_approach.technology_stack:
            lines.append("### 4.3 기술 스택")
            lines.append("")
            for tech in self.solution_approach.technology_stack:
                lines.append(f"- {tech}")
            lines.append("")

        if self.solution_approach.methodology:
            lines.append("### 4.4 개발 방법론")
            lines.append("")
            lines.append(self.solution_approach.methodology)
            lines.append("")

        if self.solution_approach.key_differentiators:
            lines.append("### 4.5 차별화 요소")
            lines.append("")
            for diff in self.solution_approach.key_differentiators:
                lines.append(f"- {diff}")
            lines.append("")

        # 5. 현재 방식 vs 제안 솔루션 (신규 섹션)
        if self.competitive_analysis:
            lines.append("## 5. 현재 방식 vs 제안 솔루션")
            lines.append("")
            lines.append("| 비교 항목 | 현재 방식 | 제안 솔루션 | 개선 효과 |")
            lines.append("|-----------|-----------|-------------|-----------|")
            for item in self.competitive_analysis:
                cat = item.get("category_name", "")
                current = item.get("current_method", "")
                proposed = item.get("proposed_method", "")
                improvement = item.get("improvement_description", "")
                lines.append(f"| {cat} | {current} | {proposed} | {improvement} |")
            lines.append("")

        # 6. 일정 계획 (번호 동적 조정)
        section_num = 6 if self.competitive_analysis else 5
        lines.append(f"## {section_num}. 일정 계획")
        lines.append("")

        if self.timeline.total_duration:
            lines.append(f"**전체 기간**: {self.timeline.total_duration}")
            lines.append("")

        if self.timeline.phases:
            lines.append("| 단계 | 기간 | 주요 산출물 |")
            lines.append("|------|------|-------------|")
            for phase in self.timeline.phases:
                deliverables_str = ", ".join(phase.deliverables[:3]) if phase.deliverables else "-"
                lines.append(f"| {phase.phase_name} | {phase.duration} | {deliverables_str} |")
            lines.append("")

        # 7. 산출물
        if self.deliverables:
            section_num += 1
            lines.append(f"## {section_num}. 산출물")
            lines.append("")
            lines.append("| 산출물 | 설명 | 단계 |")
            lines.append("|--------|------|------|")
            for d in self.deliverables:
                lines.append(f"| {d.name} | {d.description} | {d.phase} |")
            lines.append("")

        # 8. 투입 인력
        if self.resource_plan.team_structure:
            section_num += 1
            lines.append(f"## {section_num}. 투입 인력")
            lines.append("")
            lines.append("| 역할 | 인원 | 주요 업무 |")
            lines.append("|------|------|----------|")
            for member in self.resource_plan.team_structure:
                responsibilities = ", ".join(member.responsibilities[:2]) if member.responsibilities else "-"
                lines.append(f"| {member.role} | {member.count}명 | {responsibilities} |")
            lines.append("")
            if self.resource_plan.total_man_months:
                lines.append(f"**총 투입 공수**: {self.resource_plan.total_man_months} M/M")
                lines.append("")

        # 9. 리스크 및 대응방안
        if self.risks:
            section_num += 1
            lines.append(f"## {section_num}. 리스크 및 대응방안")
            lines.append("")
            lines.append("| 리스크 | 위험도 | 영향 | 대응방안 |")
            lines.append("|--------|--------|------|----------|")
            for risk in self.risks:
                level_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk.level.value, "")
                lines.append(f"| {risk.description} | {level_emoji} {risk.level.value} | {risk.impact} | {risk.mitigation} |")
            lines.append("")

        # 10. 전제 조건
        if self.assumptions:
            section_num += 1
            lines.append(f"## {section_num}. 전제 조건")
            lines.append("")
            for assumption in self.assumptions:
                lines.append(f"- {assumption}")
            lines.append("")

        # 11. 기대 효과
        if self.expected_benefits:
            section_num += 1
            lines.append(f"## {section_num}. 기대 효과")
            lines.append("")
            for benefit in self.expected_benefits:
                lines.append(f"- {benefit}")
            lines.append("")

        # 12. 후속 절차
        section_num += 1
        if self.next_steps:
            lines.append(f"## {section_num}. 후속 절차")
            lines.append("")
            for i, step in enumerate(self.next_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # 푸터
        lines.append("---")
        lines.append("")
        lines.append(f"*본 제안서는 '{self.metadata.source_prd_title}' PRD를 기반으로 자동 생성되었습니다.*")
        lines.append("")
        lines.append(f"*PRD ID: {self.metadata.source_prd_id}*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """JSON 형식으로 변환."""
        return self.model_dump_json(indent=2)
