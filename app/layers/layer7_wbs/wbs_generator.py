"""WBS generator - converts PRD to Work Breakdown Structure."""

import asyncio
import logging
import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from app.models import PRDDocument
from app.services import ClaudeClient, get_claude_client

from .models import (
    WBSDocument,
    WBSContext,
    WBSMetadata,
    TaskStatus,
    DependencyType,
    ResourceAllocation,
    TaskDependency,
    WBSTask,
    WorkPackage,
    WBSPhase,
    ResourceSummary,
    WBSSummary,
)
from .prompts import (
    PHASE_GENERATION_PROMPT,
    WORK_PACKAGE_PROMPT,
    TASK_GENERATION_PROMPT,
    RESOURCE_ALLOCATION_PROMPT,
    ESTIMATION_PROMPT,
)

logger = logging.getLogger(__name__)


class WBSGenerator:
    """PRD를 기반으로 WBS(Work Breakdown Structure) 생성."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()

    async def generate(
        self,
        prd: PRDDocument,
        context: WBSContext,
    ) -> WBSDocument:
        """
        PRD를 기반으로 WBS 생성.

        Args:
            prd: 원본 PRD 문서
            context: WBS 생성 컨텍스트

        Returns:
            WBSDocument: 생성된 WBS
        """
        logger.info(f"[WBSGenerator] WBS 생성 시작: {prd.title}")
        start_time = datetime.now()

        # WBS ID 생성
        wbs_id = f"WBS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"

        # 제목 설정
        title = f"{prd.title} - 작업분해구조 (WBS)"

        # 1. 프로젝트 단계 생성
        phases = await self._generate_phases(prd, context)
        logger.info(f"[WBSGenerator] 프로젝트 단계 생성 완료: {len(phases)}개")

        # 2. 작업 패키지 생성 (병렬 처리)
        wp_tasks = [
            self._generate_work_packages(prd, phase, context)
            for phase in phases
        ]
        wp_results = await asyncio.gather(*wp_tasks)
        for phase, work_packages in zip(phases, wp_results):
            phase.work_packages = work_packages
            logger.info(f"[WBSGenerator] {phase.name} 작업 패키지 생성 완료: {len(work_packages)}개")

        # 3. 세부 작업 생성 (병렬 처리)
        all_wps = [(phase, wp) for phase in phases for wp in phase.work_packages]
        task_coroutines = [
            self._generate_tasks(prd, wp, context)
            for _, wp in all_wps
        ]
        task_results = await asyncio.gather(*task_coroutines)
        for (_, wp), tasks in zip(all_wps, task_results):
            wp.tasks = tasks
        logger.info("[WBSGenerator] 세부 작업 생성 완료")

        # 4. 요구사항 매핑
        self._map_requirements_to_tasks(prd, phases)
        logger.info("[WBSGenerator] 요구사항 매핑 완료")

        # 5. 의존성 설정
        self._set_dependencies(phases)
        logger.info("[WBSGenerator] 의존성 설정 완료")

        # 6. 리소스 배분
        self._allocate_resources(phases, context)
        logger.info("[WBSGenerator] 리소스 배분 완료")

        # 7. 일정 계산
        self._calculate_schedule(phases, context)
        logger.info("[WBSGenerator] 일정 계산 완료")

        # 8. 크리티컬 패스 계산
        critical_path = self._calculate_critical_path(phases)
        logger.info(f"[WBSGenerator] 크리티컬 패스: {len(critical_path)}개 작업")

        # 9. 요약 생성
        summary = self._generate_summary(phases, critical_path, context)
        logger.info("[WBSGenerator] 요약 생성 완료")

        # 메타데이터
        metadata = WBSMetadata(
            source_prd_id=prd.id,
            source_prd_title=prd.title,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[WBSGenerator] WBS 생성 완료: {elapsed:.1f}초")

        return WBSDocument(
            id=wbs_id,
            title=title,
            phases=phases,
            summary=summary,
            metadata=metadata,
        )

    async def _generate_phases(
        self, prd: PRDDocument, context: WBSContext
    ) -> list[WBSPhase]:
        """프로젝트 단계 생성 (Claude)."""
        fr_summary = "\n".join([f"- {r.title}" for r in prd.functional_requirements[:15]])
        milestone_summary = "\n".join([f"- {m.name}: {m.description}" for m in prd.milestones[:5]])

        prompt = f"""{PHASE_GENERATION_PROMPT}

프로젝트: {prd.title}

개발 방법론: {context.methodology}

주요 기능 요구사항:
{fr_summary}

마일스톤:
{milestone_summary if milestone_summary else "정의되지 않음"}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="프로젝트 관리 전문가(PMP)로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            phases = []
            for i, phase_data in enumerate(result.get("phases", [])):
                phases.append(WBSPhase(
                    id=phase_data.get("id", f"PH-{i+1:03d}"),
                    name=phase_data.get("name", f"Phase {i+1}"),
                    description=phase_data.get("description", ""),
                    order=phase_data.get("order", i + 1),
                    milestone=phase_data.get("milestone", ""),
                    deliverables=phase_data.get("deliverables", []),
                ))
            return phases

        except Exception as e:
            logger.warning(f"[WBSGenerator] 프로젝트 단계 생성 실패: {e}")
            # 기본 단계 반환
            if context.methodology == "waterfall":
                return [
                    WBSPhase(id="PH-001", name="요구사항 분석", order=1, milestone="요구사항 확정",
                             deliverables=["요구사항 정의서"]),
                    WBSPhase(id="PH-002", name="설계", order=2, milestone="설계 완료",
                             deliverables=["시스템 설계서", "DB 설계서"]),
                    WBSPhase(id="PH-003", name="개발", order=3, milestone="개발 완료",
                             deliverables=["소스 코드"]),
                    WBSPhase(id="PH-004", name="테스트", order=4, milestone="테스트 완료",
                             deliverables=["테스트 결과서"]),
                    WBSPhase(id="PH-005", name="배포/오픈", order=5, milestone="서비스 오픈",
                             deliverables=["운영 매뉴얼"]),
                ]
            else:  # agile
                return [
                    WBSPhase(id="PH-001", name="프로젝트 준비", order=1, milestone="킥오프",
                             deliverables=["프로젝트 계획서"]),
                    WBSPhase(id="PH-002", name="Sprint 1: 핵심 기능", order=2, milestone="MVP",
                             deliverables=["핵심 기능 구현"]),
                    WBSPhase(id="PH-003", name="Sprint 2-3: 추가 기능", order=3, milestone="베타 버전",
                             deliverables=["추가 기능 구현"]),
                    WBSPhase(id="PH-004", name="Sprint 4: 안정화", order=4, milestone="릴리즈 준비",
                             deliverables=["버그 수정", "문서화"]),
                    WBSPhase(id="PH-005", name="릴리즈", order=5, milestone="서비스 오픈",
                             deliverables=["운영 환경 배포"]),
                ]

    async def _generate_work_packages(
        self, prd: PRDDocument, phase: WBSPhase, context: WBSContext
    ) -> list[WorkPackage]:
        """작업 패키지 생성 (Claude)."""
        # 단계에 맞는 요구사항 필터링
        fr_summary = "\n".join([
            f"- {r.id}: {r.title}"
            for r in prd.functional_requirements[:20]
        ])

        prompt = f"""{WORK_PACKAGE_PROMPT}

프로젝트: {prd.title}

현재 단계: {phase.name}
단계 설명: {phase.description}

기능 요구사항:
{fr_summary}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="프로젝트 관리 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            work_packages = []
            for i, wp_data in enumerate(result.get("work_packages", [])):
                work_packages.append(WorkPackage(
                    id=wp_data.get("id", f"{phase.id}-WP-{i+1:03d}"),
                    name=wp_data.get("name", f"Work Package {i+1}"),
                    description=wp_data.get("description", ""),
                ))
            return work_packages

        except Exception as e:
            logger.warning(f"[WBSGenerator] 작업 패키지 생성 실패 ({phase.name}): {e}")
            # 기본 작업 패키지
            return [
                WorkPackage(
                    id=f"{phase.id}-WP-001",
                    name=f"{phase.name} 작업",
                    description=f"{phase.name} 단계의 주요 작업",
                ),
            ]

    async def _generate_tasks(
        self, prd: PRDDocument, work_package: WorkPackage, context: WBSContext
    ) -> list[WBSTask]:
        """세부 작업 생성 (Claude)."""
        prompt = f"""{TASK_GENERATION_PROMPT}

프로젝트: {prd.title}

작업 패키지: {work_package.name}
설명: {work_package.description}

리소스 유형: {', '.join(context.resource_types)}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="프로젝트 관리 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            tasks = []
            for i, task_data in enumerate(result.get("tasks", [])):
                task_id = task_data.get("id", f"{work_package.id}-T-{i+1:03d}")
                resources = []
                resource_type = task_data.get("resource_type", "개발자")
                if resource_type:
                    resources.append(ResourceAllocation(
                        resource_type=resource_type,
                        allocation_percentage=100.0,
                        person_count=1,
                    ))

                dependencies = []
                for pred_id in task_data.get("predecessor_ids", []):
                    dependencies.append(TaskDependency(
                        predecessor_id=pred_id,
                        dependency_type=DependencyType.FINISH_TO_START,
                    ))

                tasks.append(WBSTask(
                    id=task_id,
                    name=task_data.get("name", f"Task {i+1}"),
                    description=task_data.get("description", ""),
                    estimated_hours=float(task_data.get("estimated_hours", 8)),
                    resources=resources,
                    dependencies=dependencies,
                    deliverables=task_data.get("deliverables", []),
                ))
            return tasks

        except Exception as e:
            logger.warning(f"[WBSGenerator] 세부 작업 생성 실패 ({work_package.name}): {e}")
            # 기본 작업
            return [
                WBSTask(
                    id=f"{work_package.id}-T-001",
                    name=f"{work_package.name} 수행",
                    description="작업 패키지 주요 작업 수행",
                    estimated_hours=16.0,
                    resources=[ResourceAllocation(resource_type="개발자", allocation_percentage=100.0, person_count=1)],
                ),
            ]

    def _map_requirements_to_tasks(self, prd: PRDDocument, phases: list[WBSPhase]) -> None:
        """요구사항을 작업에 매핑."""
        # 개발 단계 찾기
        dev_phases = [p for p in phases if "개발" in p.name.lower() or "sprint" in p.name.lower()]

        if not dev_phases:
            return

        # 요구사항을 개발 단계 작업들에 분배
        all_tasks = []
        for phase in dev_phases:
            for wp in phase.work_packages:
                all_tasks.extend(wp.tasks)

        if not all_tasks:
            return

        # 라운드 로빈 방식으로 요구사항 할당
        for i, req in enumerate(prd.functional_requirements):
            task_idx = i % len(all_tasks)
            if req.id not in all_tasks[task_idx].related_requirement_ids:
                all_tasks[task_idx].related_requirement_ids.append(req.id)

    def _set_dependencies(self, phases: list[WBSPhase]) -> None:
        """작업 간 의존성 설정."""
        prev_phase_last_task = None

        for phase in sorted(phases, key=lambda x: x.order):
            phase_tasks = []
            for wp in phase.work_packages:
                phase_tasks.extend(wp.tasks)

            if not phase_tasks:
                continue

            # 단계의 첫 작업은 이전 단계 마지막 작업에 의존
            if prev_phase_last_task and phase_tasks:
                first_task = phase_tasks[0]
                if not any(d.predecessor_id == prev_phase_last_task.id for d in first_task.dependencies):
                    first_task.dependencies.append(TaskDependency(
                        predecessor_id=prev_phase_last_task.id,
                        dependency_type=DependencyType.FINISH_TO_START,
                    ))

            # 단계 내 작업들은 순차 의존성 (이미 설정되지 않은 경우)
            for i in range(1, len(phase_tasks)):
                current_task = phase_tasks[i]
                prev_task = phase_tasks[i - 1]
                if not current_task.dependencies:
                    current_task.dependencies.append(TaskDependency(
                        predecessor_id=prev_task.id,
                        dependency_type=DependencyType.FINISH_TO_START,
                    ))

            if phase_tasks:
                prev_phase_last_task = phase_tasks[-1]

    def _allocate_resources(self, phases: list[WBSPhase], context: WBSContext) -> None:
        """리소스 배분."""
        # 이미 할당된 리소스가 없는 작업에 기본 리소스 할당
        for phase in phases:
            for wp in phase.work_packages:
                for task in wp.tasks:
                    if not task.resources:
                        # 작업명에서 리소스 유형 추론
                        resource_type = "개발자"
                        if any(kw in task.name.lower() for kw in ["설계", "기획", "분석"]):
                            resource_type = "기획자/분석가"
                        elif any(kw in task.name.lower() for kw in ["디자인", "ui", "ux"]):
                            resource_type = "디자이너"
                        elif any(kw in task.name.lower() for kw in ["테스트", "qa", "검증"]):
                            resource_type = "QA"
                        elif any(kw in task.name.lower() for kw in ["pm", "관리", "조정"]):
                            resource_type = "PM"

                        task.resources.append(ResourceAllocation(
                            resource_type=resource_type,
                            allocation_percentage=100.0,
                            person_count=1,
                        ))

    def _calculate_schedule(self, phases: list[WBSPhase], context: WBSContext) -> None:
        """일정 계산."""
        start_date = context.start_date or date.today()
        current_date = start_date

        for phase in sorted(phases, key=lambda x: x.order):
            phase.start_date = current_date
            phase_end_date = current_date

            for wp in phase.work_packages:
                wp.start_date = current_date
                wp_end_date = current_date

                for task in wp.tasks:
                    task.start_date = current_date
                    # 작업 일수 계산 (8시간/일 기준)
                    task_days = max(1, int(task.estimated_hours / context.working_hours_per_day))
                    task.end_date = current_date + timedelta(days=task_days - 1)

                    if task.end_date > wp_end_date:
                        wp_end_date = task.end_date

                    # 순차 작업인 경우 다음 작업 시작일 업데이트
                    current_date = task.end_date + timedelta(days=1)

                wp.end_date = wp_end_date

            phase.end_date = wp_end_date if phase.work_packages else current_date

    def _calculate_critical_path(self, phases: list[WBSPhase]) -> list[str]:
        """크리티컬 패스 계산 (위상 정렬 기반 최적화 버전)."""
        # 모든 작업 수집
        all_tasks = []
        for phase in phases:
            for wp in phase.work_packages:
                all_tasks.extend(wp.tasks)

        if not all_tasks:
            return []

        # 작업 ID → 작업 매핑
        task_dict = {t.id: t for t in all_tasks}

        # 동적 프로그래밍: 각 작업까지의 최장 경로 거리와 이전 작업 기록
        dist: dict[str, float] = {t.id: 0.0 for t in all_tasks}
        prev: dict[str, str | None] = {t.id: None for t in all_tasks}

        # 후속 작업 매핑 (역방향 그래프)
        successors: dict[str, list[str]] = {t.id: [] for t in all_tasks}
        for task in all_tasks:
            for dep in task.dependencies:
                if dep.predecessor_id in successors:
                    successors[dep.predecessor_id].append(task.id)

        # 위상 정렬 순서로 처리 (단순히 단계/작업패키지 순서 사용)
        for task in all_tasks:
            task_hours = task.estimated_hours
            for dep in task.dependencies:
                pred_id = dep.predecessor_id
                if pred_id in dist:
                    new_dist = dist[pred_id] + task_dict[pred_id].estimated_hours
                    if new_dist > dist[task.id]:
                        dist[task.id] = new_dist
                        prev[task.id] = pred_id

        # 가장 긴 경로의 끝점 찾기
        end_task_id = max(dist.keys(), key=lambda x: dist[x] + task_dict[x].estimated_hours)

        # 경로 역추적
        critical_path = []
        current = end_task_id
        while current is not None:
            critical_path.append(current)
            current = prev[current]

        critical_path.reverse()
        return critical_path

    def _generate_summary(
        self, phases: list[WBSPhase], critical_path: list[str], context: WBSContext
    ) -> WBSSummary:
        """WBS 요약 생성."""
        total_phases = len(phases)
        total_work_packages = sum(len(p.work_packages) for p in phases)
        total_tasks = sum(p.total_tasks for p in phases)
        total_hours = sum(p.total_hours for p in phases)

        # 버퍼 적용
        total_hours_with_buffer = total_hours * (1 + context.buffer_percentage)

        # M/D, M/M 계산
        total_man_days = total_hours_with_buffer / context.working_hours_per_day
        total_man_months = total_man_days / 22  # 월 22일 기준

        # 기간 계산 (팀 규모 고려)
        effective_team_size = max(1, context.team_size * 0.7)  # 70% 효율
        estimated_duration_days = int(total_man_days / effective_team_size)

        # 리소스별 요약
        resource_hours: dict[str, float] = {}
        for phase in phases:
            for wp in phase.work_packages:
                for task in wp.tasks:
                    for resource in task.resources:
                        resource_type = resource.resource_type
                        hours = task.estimated_hours * (resource.allocation_percentage / 100)
                        resource_hours[resource_type] = resource_hours.get(resource_type, 0) + hours

        resource_summary = [
            ResourceSummary(
                resource_type=rt,
                total_hours=hours,
                total_days=hours / context.working_hours_per_day,
            )
            for rt, hours in resource_hours.items()
        ]

        return WBSSummary(
            total_phases=total_phases,
            total_work_packages=total_work_packages,
            total_tasks=total_tasks,
            total_hours=total_hours_with_buffer,
            total_man_days=total_man_days,
            total_man_months=total_man_months,
            estimated_duration_days=estimated_duration_days,
            critical_path=critical_path,
            resource_summary=resource_summary,
        )
