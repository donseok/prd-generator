"""WBS (Work Breakdown Structure) models."""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WBSContext(BaseModel):
    """WBS 생성 컨텍스트.

    버퍼 비율 사용 예시:
    - buffer_percentage=0.15 또는 buffer_percentage=15 → 15% 버퍼
    - 1보다 크면 자동으로 100으로 나눔

    스프린트 기간:
    - sprint_duration: 일 단위 (기본값 14일 = 2주)
    - sprint_duration_weeks: 주 단위 (legacy, sprint_duration 우선)
    """
    start_date: Optional[date] = Field(None, description="프로젝트 시작일")
    team_size: int = Field(5, description="팀 규모")
    methodology: str = Field("agile", description="개발 방법론 (agile, waterfall, hybrid)")
    sprint_duration: int = Field(14, description="스프린트 기간 (일)")
    sprint_duration_weeks: int = Field(2, description="스프린트 주기 (주) - legacy")
    working_hours_per_day: int = Field(8, description="일일 작업 시간")
    buffer_percentage: float = Field(0.15, description="버퍼 비율 (0.15 또는 15 둘 다 15%로 처리)")
    resource_types: list[str] = Field(
        default_factory=lambda: ["PM", "개발자", "디자이너", "QA"],
        description="리소스 유형"
    )

    @property
    def normalized_buffer(self) -> float:
        """정규화된 버퍼 비율 (0.0~1.0)."""
        if self.buffer_percentage > 1.0:
            return self.buffer_percentage / 100.0
        return self.buffer_percentage


class WBSMetadata(BaseModel):
    """WBS 메타데이터."""
    version: str = "1.0"
    status: str = "DRAFT"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    source_prd_id: str = Field(..., description="원본 PRD ID")
    source_prd_title: str = Field(..., description="원본 PRD 제목")


class TaskStatus(str, Enum):
    """작업 상태."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class DependencyType(str, Enum):
    """의존성 유형."""
    FINISH_TO_START = "FS"  # 선행 완료 후 시작
    START_TO_START = "SS"  # 선행 시작과 동시 시작
    FINISH_TO_FINISH = "FF"  # 선행 완료와 동시 완료
    START_TO_FINISH = "SF"  # 선행 시작 후 완료


class ResourceAllocation(BaseModel):
    """리소스 배분."""
    resource_type: str = Field(..., description="리소스 유형")
    allocation_percentage: float = Field(100.0, description="배분율 (%)")
    person_count: int = Field(1, description="인원 수")


class TaskDependency(BaseModel):
    """작업 의존성."""
    predecessor_id: str = Field(..., description="선행 작업 ID")
    dependency_type: DependencyType = Field(DependencyType.FINISH_TO_START, description="의존성 유형")
    lag_days: int = Field(0, description="지연 일수")


class WBSTask(BaseModel):
    """WBS 최하위 작업 단위."""
    id: str = Field(..., description="작업 ID")
    name: str = Field(..., description="작업명")
    description: str = Field("", description="작업 설명")
    estimated_hours: float = Field(0.0, description="예상 공수 (시간)")
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="작업 상태")
    resources: list[ResourceAllocation] = Field(default_factory=list, description="리소스 배분")
    dependencies: list[TaskDependency] = Field(default_factory=list, description="의존성")
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    related_requirement_ids: list[str] = Field(default_factory=list, description="관련 요구사항 ID")
    deliverables: list[str] = Field(default_factory=list, description="산출물")
    notes: str = Field("", description="비고")


class WorkPackage(BaseModel):
    """작업 패키지 (중간 수준)."""
    id: str = Field(..., description="작업 패키지 ID")
    name: str = Field(..., description="작업 패키지명")
    description: str = Field("", description="설명")
    tasks: list[WBSTask] = Field(default_factory=list, description="하위 작업 목록")
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")

    @property
    def total_hours(self) -> float:
        """총 예상 공수."""
        return sum(task.estimated_hours for task in self.tasks)

    @property
    def completion_percentage(self) -> float:
        """완료율."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100


class WBSPhase(BaseModel):
    """프로젝트 단계 (최상위 수준)."""
    id: str = Field(..., description="단계 ID")
    name: str = Field(..., description="단계명")
    description: str = Field("", description="단계 설명")
    order: int = Field(0, description="순서")
    work_packages: list[WorkPackage] = Field(default_factory=list, description="작업 패키지 목록")
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    milestone: str = Field("", description="마일스톤")
    deliverables: list[str] = Field(default_factory=list, description="주요 산출물")

    @property
    def total_hours(self) -> float:
        """총 예상 공수."""
        return sum(wp.total_hours for wp in self.work_packages)

    @property
    def total_tasks(self) -> int:
        """총 작업 수."""
        return sum(len(wp.tasks) for wp in self.work_packages)


class ResourceSummary(BaseModel):
    """리소스 요약."""
    resource_type: str = Field(..., description="리소스 유형")
    total_hours: float = Field(0.0, description="총 공수 (시간)")
    total_days: float = Field(0.0, description="총 공수 (일)")
    peak_allocation: int = Field(0, description="최대 동시 투입 인원")


class WBSSummary(BaseModel):
    """WBS 요약."""
    total_phases: int = Field(0, description="총 단계 수")
    total_work_packages: int = Field(0, description="총 작업 패키지 수")
    total_tasks: int = Field(0, description="총 작업 수")
    total_hours: float = Field(0.0, description="총 예상 공수 (시간)")
    total_man_days: float = Field(0.0, description="총 M/D")
    total_man_months: float = Field(0.0, description="총 M/M")
    estimated_duration_days: int = Field(0, description="예상 기간 (일)")
    critical_path: list[str] = Field(default_factory=list, description="크리티컬 패스 작업 ID")
    resource_summary: list[ResourceSummary] = Field(default_factory=list, description="리소스 요약")


class WBSDocument(BaseModel):
    """WBS (Work Breakdown Structure) 문서."""

    # 기본 정보
    id: str = Field(..., description="WBS ID")
    title: str = Field(..., description="WBS 제목")

    # WBS 구조
    phases: list[WBSPhase] = Field(default_factory=list, description="프로젝트 단계")
    summary: WBSSummary = Field(default_factory=WBSSummary, description="WBS 요약")

    # 메타데이터
    metadata: WBSMetadata

    def to_markdown(self) -> str:
        """마크다운 형식의 WBS 생성."""
        lines = []

        # 헤더
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**버전**: {self.metadata.version} | **상태**: {self.metadata.status}")
        lines.append(f"**생성일**: {self.metadata.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**원본 PRD**: {self.metadata.source_prd_title} ({self.metadata.source_prd_id})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. 요약
        lines.append("## 1. WBS 요약")
        lines.append("")
        lines.append(f"| 항목 | 값 |")
        lines.append("|------|-----|")
        lines.append(f"| 총 단계 | {self.summary.total_phases}개 |")
        lines.append(f"| 총 작업 패키지 | {self.summary.total_work_packages}개 |")
        lines.append(f"| 총 작업 | {self.summary.total_tasks}개 |")
        lines.append(f"| 총 예상 공수 | {self.summary.total_hours:.0f}시간 ({self.summary.total_man_days:.1f} M/D, {self.summary.total_man_months:.1f} M/M) |")
        lines.append(f"| 예상 기간 | {self.summary.estimated_duration_days}일 |")
        lines.append("")

        # 리소스 요약
        if self.summary.resource_summary:
            lines.append("### 리소스 투입 계획")
            lines.append("")
            lines.append("| 리소스 유형 | 총 공수 (시간) | 총 공수 (일) |")
            lines.append("|------------|---------------|-------------|")
            for rs in self.summary.resource_summary:
                lines.append(f"| {rs.resource_type} | {rs.total_hours:.0f}h | {rs.total_days:.1f}d |")
            lines.append("")

        # 크리티컬 패스
        if self.summary.critical_path:
            lines.append("### 크리티컬 패스")
            lines.append("")
            lines.append(" → ".join(self.summary.critical_path))
            lines.append("")

        # 2. 단계별 상세
        lines.append("## 2. 단계별 작업 분해")
        lines.append("")

        for phase in sorted(self.phases, key=lambda x: x.order):
            lines.append(f"### {phase.order}. {phase.name}")
            lines.append("")
            if phase.description:
                lines.append(phase.description)
                lines.append("")

            if phase.milestone:
                lines.append(f"**마일스톤**: {phase.milestone}")

            date_str = ""
            if phase.start_date and phase.end_date:
                date_str = f" ({phase.start_date} ~ {phase.end_date})"
            lines.append(f"**예상 공수**: {phase.total_hours:.0f}시간{date_str}")
            lines.append("")

            if phase.deliverables:
                lines.append("**주요 산출물**:")
                for d in phase.deliverables:
                    lines.append(f"- {d}")
                lines.append("")

            # 작업 패키지
            for wp in phase.work_packages:
                lines.append(f"#### {wp.name}")
                lines.append("")
                if wp.description:
                    lines.append(wp.description)
                    lines.append("")

                if wp.tasks:
                    lines.append("| ID | 작업명 | 예상 공수 | 담당 | 산출물 |")
                    lines.append("|----|--------|----------|------|--------|")
                    for task in wp.tasks:
                        resource_str = ", ".join([r.resource_type for r in task.resources[:2]]) if task.resources else "-"
                        deliverable_str = ", ".join(task.deliverables[:2]) if task.deliverables else "-"
                        lines.append(f"| {task.id} | {task.name} | {task.estimated_hours:.0f}h | {resource_str} | {deliverable_str} |")
                    lines.append("")

        # 3. 간트 차트 개요 (텍스트 기반)
        lines.append("## 3. 일정 개요")
        lines.append("")
        lines.append("```")
        for phase in sorted(self.phases, key=lambda x: x.order):
            phase_bar = "=" * min(int(phase.total_hours / 8), 50)  # 일 단위로 변환하여 표시
            lines.append(f"{phase.name[:20]:<20} |{phase_bar}| {phase.total_hours:.0f}h")
        lines.append("```")
        lines.append("")

        # 푸터
        lines.append("---")
        lines.append("")
        lines.append(f"*본 WBS는 '{self.metadata.source_prd_title}' PRD를 기반으로 자동 생성되었습니다.*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """JSON 형식으로 변환."""
        return self.model_dump_json(indent=2)
