"""Proposal generator - converts PRD to customer proposal."""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.models import PRDDocument, RequirementType
from app.services import ClaudeClient, get_claude_client

from .models import (
    ProposalDocument,
    ProposalContext,
    ProposalMetadata,
    ProjectOverview,
    ScopeOfWork,
    SolutionApproach,
    Timeline,
    TimelinePhase,
    Deliverable,
    ResourcePlan,
    TeamMember,
    Risk,
    RiskLevel,
)
from .prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    SOLUTION_APPROACH_PROMPT,
    EXPECTED_BENEFITS_PROMPT,
    RESOURCE_PLAN_PROMPT,
)

logger = logging.getLogger(__name__)


class ProposalGenerator:
    """PRD를 기반으로 고객 제안서 생성."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()

    async def generate(
        self,
        prd: PRDDocument,
        context: ProposalContext,
    ) -> ProposalDocument:
        """
        PRD를 기반으로 제안서 생성.

        Args:
            prd: 원본 PRD 문서
            context: 제안서 컨텍스트 (고객사명 등)

        Returns:
            ProposalDocument: 생성된 제안서
        """
        logger.info(f"[ProposalGenerator] 제안서 생성 시작: {prd.title}")
        start_time = datetime.now()

        # 제안서 ID 생성
        proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

        # 제목 설정
        project_name = context.project_name or prd.title
        title = f"{context.client_name} {project_name} 제안서"

        # 1. 프로젝트 개요 추출
        project_overview = self._extract_project_overview(prd)
        logger.info("[ProposalGenerator] 프로젝트 개요 추출 완료")

        # 2. 작업 범위 추출
        scope_of_work = self._extract_scope_of_work(prd)
        logger.info("[ProposalGenerator] 작업 범위 추출 완료")

        # 3. 솔루션 접근법 생성 (Claude)
        solution_approach = await self._generate_solution_approach(prd)
        logger.info("[ProposalGenerator] 솔루션 접근법 생성 완료")

        # 4. 일정 계획 변환
        timeline = self._convert_milestones_to_timeline(prd, context)
        logger.info("[ProposalGenerator] 일정 계획 변환 완료")

        # 5. 산출물 목록 생성
        deliverables = self._generate_deliverables(prd)
        logger.info("[ProposalGenerator] 산출물 목록 생성 완료")

        # 6. 투입 인력 계획 생성 (Claude)
        resource_plan = await self._generate_resource_plan(prd, context)
        logger.info("[ProposalGenerator] 투입 인력 계획 생성 완료")

        # 7. 리스크 평가
        risks = self._assess_risks(prd)
        logger.info("[ProposalGenerator] 리스크 평가 완료")

        # 8. 전제 조건 추출
        assumptions = self._extract_assumptions(prd)
        logger.info("[ProposalGenerator] 전제 조건 추출 완료")

        # 9. 기대 효과 생성 (Claude)
        expected_benefits = await self._generate_expected_benefits(prd)
        logger.info("[ProposalGenerator] 기대 효과 생성 완료")

        # 10. 경영진 요약 생성 (Claude) - 마지막에 생성
        executive_summary = await self._generate_executive_summary(
            prd, context, project_overview, expected_benefits
        )
        logger.info("[ProposalGenerator] 경영진 요약 생성 완료")

        # 11. 후속 절차
        next_steps = self._generate_next_steps()

        # 메타데이터
        metadata = ProposalMetadata(
            source_prd_id=prd.id,
            source_prd_title=prd.title,
            overall_confidence=prd.metadata.overall_confidence,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[ProposalGenerator] 제안서 생성 완료: {elapsed:.1f}초")

        return ProposalDocument(
            id=proposal_id,
            title=title,
            client_name=context.client_name,
            executive_summary=executive_summary,
            project_overview=project_overview,
            scope_of_work=scope_of_work,
            solution_approach=solution_approach,
            timeline=timeline,
            deliverables=deliverables,
            resource_plan=resource_plan,
            risks=risks,
            assumptions=assumptions,
            expected_benefits=expected_benefits,
            next_steps=next_steps,
            metadata=metadata,
        )

    def _extract_project_overview(self, prd: PRDDocument) -> ProjectOverview:
        """PRD에서 프로젝트 개요 추출."""
        return ProjectOverview(
            background=prd.overview.background,
            objectives=prd.overview.goals,
            success_criteria=prd.overview.success_metrics or [],
        )

    def _extract_scope_of_work(self, prd: PRDDocument) -> ScopeOfWork:
        """PRD에서 작업 범위 추출."""
        # 포함 범위: scope + 주요 기능 카테고리
        in_scope = []
        if prd.overview.scope:
            in_scope.append(prd.overview.scope)

        # 기능 요구사항을 카테고리별로 그룹화
        key_features = []

        # FR 그룹화
        fr_titles = [r.title for r in prd.functional_requirements[:10]]
        if fr_titles:
            key_features.append({
                "name": "기능 요구사항",
                "description": "핵심 비즈니스 기능 구현",
                "count": len(prd.functional_requirements),
            })
            in_scope.extend(fr_titles[:5])

        # NFR 그룹화
        if prd.non_functional_requirements:
            key_features.append({
                "name": "비기능 요구사항",
                "description": "성능, 보안, 확장성 등",
                "count": len(prd.non_functional_requirements),
            })

        # 제약조건
        if prd.constraints:
            key_features.append({
                "name": "기술 제약사항",
                "description": "기술 스택 및 환경 요구사항",
                "count": len(prd.constraints),
            })

        return ScopeOfWork(
            in_scope=in_scope,
            out_of_scope=prd.overview.out_of_scope or [],
            key_features=key_features,
        )

    async def _generate_solution_approach(self, prd: PRDDocument) -> SolutionApproach:
        """솔루션 접근법 생성 (Claude)."""
        # 제약조건에서 기술 스택 추출
        tech_stack = []
        for constraint in prd.constraints:
            if any(kw in constraint.title.lower() for kw in ["기술", "스택", "프레임워크", "언어"]):
                tech_stack.append(constraint.title)

        # 요구사항 요약 생성
        fr_summary = "\n".join([f"- {r.title}" for r in prd.functional_requirements[:10]])
        nfr_summary = "\n".join([f"- {r.title}" for r in prd.non_functional_requirements[:5]])

        prompt = f"""{SOLUTION_APPROACH_PROMPT}

프로젝트: {prd.title}

주요 기능 요구사항:
{fr_summary}

비기능 요구사항:
{nfr_summary}

기술 제약사항:
{chr(10).join([f'- {c.title}' for c in prd.constraints[:5]])}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="IT 솔루션 아키텍트로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            return SolutionApproach(
                overview=result.get("overview", ""),
                architecture=result.get("architecture", ""),
                technology_stack=tech_stack or result.get("technology_stack", []),
                methodology=result.get("methodology", "애자일 방법론 기반 개발"),
            )
        except Exception as e:
            logger.warning(f"[ProposalGenerator] 솔루션 접근법 생성 실패: {e}")
            return SolutionApproach(
                overview="요구사항 기반 맞춤형 솔루션 제공",
                architecture="클라우드 기반 웹/모바일 시스템",
                technology_stack=tech_stack,
                methodology="애자일 방법론 기반 개발",
            )

    def _convert_milestones_to_timeline(
        self, prd: PRDDocument, context: ProposalContext
    ) -> Timeline:
        """마일스톤을 일정 계획으로 변환."""
        phases = []

        # 기본 단계 정의
        default_phases = [
            ("요구사항 분석", "1개월"),
            ("설계", "1개월"),
            ("개발", "3개월"),
            ("테스트", "1개월"),
            ("오픈", "0.5개월"),
        ]

        if prd.milestones:
            for ms in sorted(prd.milestones, key=lambda x: x.order):
                phases.append(TimelinePhase(
                    phase_name=ms.name,
                    duration=f"{len(ms.deliverables)}주" if ms.deliverables else "2주",
                    deliverables=ms.deliverables,
                    description=ms.description,
                ))
        else:
            for name, duration in default_phases:
                phases.append(TimelinePhase(
                    phase_name=name,
                    duration=duration,
                    deliverables=[],
                ))

        total_duration = f"{context.project_duration_months or 6}개월"

        return Timeline(
            total_duration=total_duration,
            phases=phases,
        )

    def _generate_deliverables(self, prd: PRDDocument) -> list[Deliverable]:
        """산출물 목록 생성."""
        deliverables = [
            Deliverable(name="요구사항 정의서", description="상세 요구사항 문서", phase="분석"),
            Deliverable(name="시스템 설계서", description="아키텍처 및 상세 설계", phase="설계"),
            Deliverable(name="UI/UX 설계서", description="화면 설계 및 프로토타입", phase="설계"),
            Deliverable(name="소스 코드", description="개발된 시스템 코드", phase="개발"),
            Deliverable(name="테스트 결과서", description="테스트 수행 결과", phase="테스트"),
            Deliverable(name="사용자 매뉴얼", description="시스템 사용 가이드", phase="오픈"),
            Deliverable(name="운영 매뉴얼", description="시스템 운영 가이드", phase="오픈"),
        ]

        return deliverables

    async def _generate_resource_plan(
        self, prd: PRDDocument, context: ProposalContext
    ) -> ResourcePlan:
        """투입 인력 계획 생성."""
        # 기본 팀 구성
        team_structure = [
            TeamMember(role="PM", count=1, responsibilities=["프로젝트 관리", "일정 관리", "이해관계자 커뮤니케이션"]),
            TeamMember(role="기획자", count=1, responsibilities=["요구사항 분석", "기능 정의"]),
            TeamMember(role="UI/UX 디자이너", count=1, responsibilities=["화면 설계", "프로토타입 제작"]),
            TeamMember(role="프론트엔드 개발자", count=2, responsibilities=["웹/앱 UI 개발"]),
            TeamMember(role="백엔드 개발자", count=2, responsibilities=["서버 개발", "API 개발"]),
            TeamMember(role="QA", count=1, responsibilities=["테스트 수행", "품질 관리"]),
        ]

        # 규모에 따라 인원 조정
        total_reqs = (
            len(prd.functional_requirements)
            + len(prd.non_functional_requirements)
            + len(prd.constraints)
        )

        if total_reqs > 100:
            team_structure[3].count = 3  # 프론트엔드 +1
            team_structure[4].count = 3  # 백엔드 +1

        # M/M 계산 (대략적)
        duration_months = context.project_duration_months or 6
        total_members = sum(m.count for m in team_structure)
        total_mm = total_members * duration_months * 0.8  # 80% 효율

        return ResourcePlan(
            team_structure=team_structure,
            total_man_months=round(total_mm, 1),
        )

    def _assess_risks(self, prd: PRDDocument) -> list[Risk]:
        """리스크 평가."""
        risks = []

        # 1. 낮은 신뢰도 요구사항 → 리스크
        low_confidence_reqs = [
            r for r in prd.functional_requirements + prd.non_functional_requirements
            if r.confidence_score < 0.7
        ]

        if low_confidence_reqs:
            risks.append(Risk(
                description="요구사항 명확성 부족",
                level=RiskLevel.MEDIUM,
                impact="요구사항 변경으로 인한 일정 지연 가능",
                mitigation="요구사항 확정 미팅 및 문서화 강화",
                source_requirement_id=low_confidence_reqs[0].id if low_confidence_reqs else None,
            ))

        # 2. 미해결 사항 → 리스크
        if prd.unresolved_items:
            high_priority_unresolved = [
                u for u in prd.unresolved_items if u.priority == "HIGH"
            ]
            if high_priority_unresolved:
                risks.append(Risk(
                    description="미확정 의사결정 사항 존재",
                    level=RiskLevel.HIGH,
                    impact="프로젝트 방향성 및 일정에 영향",
                    mitigation="착수 전 주요 사항 의사결정 완료",
                ))

        # 3. 기술적 복잡성 (연동 요구사항)
        integration_reqs = [
            r for r in prd.functional_requirements + prd.constraints
            if any(kw in r.title.lower() for kw in ["연동", "통합", "인터페이스", "api"])
        ]
        if integration_reqs:
            risks.append(Risk(
                description="외부 시스템 연동 복잡성",
                level=RiskLevel.MEDIUM,
                impact="연동 인터페이스 변경 시 추가 개발 필요",
                mitigation="사전 인터페이스 정의 및 테스트 환경 확보",
            ))

        # 4. 일정 리스크
        if prd.milestones and len(prd.milestones) > 3:
            risks.append(Risk(
                description="다단계 프로젝트 일정 관리",
                level=RiskLevel.LOW,
                impact="단계 간 의존성으로 인한 일정 조정",
                mitigation="주간 진척 관리 및 버퍼 일정 확보",
            ))

        # 기본 리스크 추가
        if not risks:
            risks.append(Risk(
                description="일반적인 프로젝트 리스크",
                level=RiskLevel.LOW,
                impact="일정 또는 비용 변동 가능",
                mitigation="정기 리스크 모니터링 및 대응",
            ))

        return risks

    def _extract_assumptions(self, prd: PRDDocument) -> list[str]:
        """전제 조건 추출."""
        assumptions = []

        # 요구사항에서 가정사항 수집
        for req in prd.functional_requirements + prd.non_functional_requirements:
            if req.assumptions:
                assumptions.extend(req.assumptions[:2])

        # 기본 전제조건 추가
        default_assumptions = [
            "고객사 담당자의 적시 의사결정 지원",
            "필요 자료 및 정보의 적시 제공",
            "개발/테스트 환경 접근 권한 제공",
            "주요 이해관계자의 정기 미팅 참석",
        ]

        assumptions.extend(default_assumptions)

        # 중복 제거 및 제한
        return list(dict.fromkeys(assumptions))[:10]

    async def _generate_expected_benefits(self, prd: PRDDocument) -> list[str]:
        """기대 효과 생성 (Claude)."""
        # 먼저 NFR에서 정량적 효과 추출
        benefits = []
        for nfr in prd.non_functional_requirements:
            if any(kw in nfr.title for kw in ["감소", "단축", "향상", "개선", "%"]):
                benefits.append(nfr.title)

        if len(benefits) >= 5:
            return benefits[:8]

        # Claude로 추가 생성
        fr_summary = "\n".join([f"- {r.title}" for r in prd.functional_requirements[:10]])

        prompt = f"""{EXPECTED_BENEFITS_PROMPT}

프로젝트: {prd.title}

배경: {prd.overview.background[:500]}

주요 기능:
{fr_summary}

기존 추출된 효과:
{chr(10).join([f'- {b}' for b in benefits])}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="비즈니스 분석가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.4,
            )

            if isinstance(result, list):
                benefits.extend(result)
            elif isinstance(result, dict) and "benefits" in result:
                benefits.extend(result["benefits"])

        except Exception as e:
            logger.warning(f"[ProposalGenerator] 기대효과 생성 실패: {e}")
            # 기본 효과 추가
            benefits.extend([
                "업무 효율성 향상",
                "사용자 만족도 개선",
                "데이터 기반 의사결정 지원",
            ])

        return list(dict.fromkeys(benefits))[:8]

    async def _generate_executive_summary(
        self,
        prd: PRDDocument,
        context: ProposalContext,
        overview: ProjectOverview,
        benefits: list[str],
    ) -> str:
        """경영진 요약 생성 (Claude)."""
        prompt = f"""{EXECUTIVE_SUMMARY_PROMPT}

고객사: {context.client_name}
프로젝트: {prd.title}

배경:
{overview.background}

목표:
{chr(10).join([f'- {g}' for g in overview.objectives[:5]])}

주요 기대효과:
{chr(10).join([f'- {b}' for b in benefits[:5]])}

전체 요구사항 수: 기능 {len(prd.functional_requirements)}건, 비기능 {len(prd.non_functional_requirements)}건
"""

        try:
            result = await self.claude_client.complete(
                system_prompt="IT 프로젝트 제안서 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.4,
            )
            return result.strip()

        except Exception as e:
            logger.warning(f"[ProposalGenerator] 경영진 요약 생성 실패: {e}")
            return f"""{context.client_name}의 {prd.title} 프로젝트는 {overview.background[:200]}

본 제안서는 {len(prd.functional_requirements)}개의 기능 요구사항과 {len(prd.non_functional_requirements)}개의 비기능 요구사항을 기반으로 최적의 솔루션을 제안합니다."""

    def _generate_next_steps(self) -> list[str]:
        """후속 절차 생성."""
        return [
            "제안서 검토 및 Q&A 세션",
            "상세 범위 및 일정 협의",
            "계약 조건 협의",
            "계약 체결",
            "킥오프 미팅 및 프로젝트 착수",
        ]
