"""
Layer 4: PRD 문서 생성 서비스입니다.
검증된 요구사항들을 바탕으로 최종 PRD 문서(PRDDocument)를 생성합니다.
"""

from typing import List, Optional
from datetime import datetime
import logging

from app.models import (
    NormalizedRequirement,
    RequirementType,
    PRDDocument,
    PRDOverview,
    PRDMetadata,
    Milestone,
    UnresolvedItem,
)
from app.services.claude_client import ClaudeClient, get_claude_client
from app.layers.base_generator import BaseGenerator
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PRDContext:
    """PRD 생성에 필요한 추가 정보들"""
    title: Optional[str] = None
    source_documents: Optional[List[str]] = None
    additional_context: Optional[dict] = None


class PRDGenerator(BaseGenerator[List[NormalizedRequirement], PRDDocument, PRDContext]):
    """
    PRD 생성기 클래스입니다.
    BaseGenerator를 상속받아 표준화된 문서 생성 흐름을 따릅니다.
    """

    _id_prefix = "PRD"  # 생성될 문서 ID의 접두어
    _generator_name = "PRDGenerator"

    async def _do_generate(
        self,
        requirements: List[NormalizedRequirement],
        context: PRDContext,
    ) -> PRDDocument:
        """
        실제 PRD 생성을 수행하는 내부 함수입니다.
        """
        # 1. 요구사항을 종류별로 분류 (기능 / 비기능 / 제약조건)
        functional = [r for r in requirements if r.type == RequirementType.FUNCTIONAL]
        non_functional = [r for r in requirements if r.type == RequirementType.NON_FUNCTIONAL]
        constraints = [r for r in requirements if r.type == RequirementType.CONSTRAINT]

        # 2. AI를 사용하여 프로젝트 개요(Overview) 작성
        overview = await self._generate_overview(requirements, context)

        # 3. 우선순위에 따라 마일스톤 자동 생성
        milestones = await self._generate_milestones(requirements)

        # 4. 미해결 항목(질문, 가정) 수집
        unresolved = self._collect_unresolved_items(requirements)

        # 5. 전체 신뢰도 점수 계산 (평균)
        overall_confidence = self._calculate_overall_confidence(requirements)

        # 6. 메타데이터 생성
        source_docs = context.source_documents or []
        metadata = PRDMetadata(
            version="1.0",
            status="draft",
            author="PRD Generator",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_documents=source_docs,
            overall_confidence=overall_confidence,
            requires_pm_review=overall_confidence < 0.8,
            pm_review_reasons=self._get_review_reasons(requirements),
        )

        # 문서 ID 생성
        prd_id = self._generate_id()

        # 제목 생성 (로컬 처리)
        title = self._generate_title(requirements, context)

        # 최종 PRD 객체 반환
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

    async def generate(
        self,
        requirements: List[NormalizedRequirement],
        source_documents: List[str] = None,
        context: dict = None
    ) -> PRDDocument:
        """
        외부에서 호출하는 메인 함수입니다. (호환성 유지용)
        입력받은 파라미터를 정리해서 내부 생성 함수(_do_generate)를 호출합니다.
        """
        # 컨텍스트 객체 생성
        prd_context = PRDContext(
            title=context.get("title") if context else None,
            source_documents=source_documents,
            additional_context=context,
        )

        logger.info(f"[{self._generator_name}] PRD 생성 시작")
        start_time = datetime.now()

        try:
            result = await self._do_generate(requirements, prd_context)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{self._generator_name}] PRD 생성 완료: {elapsed:.1f}초")

            return result

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{self._generator_name}] PRD 생성 실패 ({elapsed:.1f}초): {e}")
            raise

    async def _generate_overview(
        self,
        requirements: List[NormalizedRequirement],
        context: PRDContext
    ) -> PRDOverview:
        """PRD의 개요 섹션을 생성합니다. AI 호출 실패 시 요구사항에서 직접 추출."""
        # 먼저 요구사항에서 기본 정보 추출 (AI 없이)
        goals = []
        for req in requirements[:10]:
            if req.type == RequirementType.FUNCTIONAL and req.title:
                goal = req.title
                if ':' in goal:
                    goal = goal.split(':', 1)[1].strip()
                if len(goal) > 5 and goal not in goals:
                    goals.append(goal[:80])
                if len(goals) >= 5:
                    break

        # 배경 정보 추출 (첫 번째 요구사항 설명에서)
        background = "시스템 개선 및 신규 기능 개발 프로젝트"
        if requirements and requirements[0].description:
            desc = requirements[0].description
            if len(desc) > 20:
                background = desc[:300]

        # AI 호출 시도 (선택적)
        try:
            req_summary = "\n".join([
                f"- {req.title}"
                for req in requirements[:10]
            ])

            prompt = f"""요구사항 기반 PRD 개요를 JSON으로 작성:

요구사항:
{req_summary}

JSON형식(background, goals[], scope, out_of_scope[], target_users[], success_metrics[]):"""

            result = await self._call_claude_json(
                system_prompt="PRD 개요 작성 전문가. 간결하게 JSON만 반환.",
                user_prompt=prompt,
                section_name="overview",
            )

            if result and result.get("background"):
                return PRDOverview(
                    background=result.get("background", background),
                    goals=result.get("goals", goals) or goals,
                    scope=result.get("scope", "프로젝트 범위 정의 필요"),
                    out_of_scope=result.get("out_of_scope", []),
                    target_users=result.get("target_users", ["시스템 사용자"]),
                    success_metrics=result.get("success_metrics", []),
                )
        except Exception as e:
            logger.warning(f"[PRDGenerator] Overview AI 생성 실패, 로컬 폴백 사용: {e}")

        # 로컬 폴백 (AI 실패 시)
        return PRDOverview(
            background=background,
            goals=goals or ["프로젝트 목표 정의 필요"],
            scope="문서에서 정의된 기능 범위",
            out_of_scope=[],
            target_users=["시스템 사용자", "관리자"],
            success_metrics=[],
        )

    async def _generate_milestones(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[Milestone]:
        """요구사항의 우선순위를 기반으로 마일스톤(단계별 목표)을 생성합니다."""
        if not requirements:
            return []

        # 우선순위별로 분류
        high_priority = [r for r in requirements if r.priority.value == "HIGH"]
        medium_priority = [r for r in requirements if r.priority.value == "MEDIUM"]
        low_priority = [r for r in requirements if r.priority.value == "LOW"]

        milestones = []

        # 1단계: MVP (필수 기능)
        if high_priority:
            milestones.append(Milestone(
                id="MS-001",
                name="MVP (Minimum Viable Product)",
                description="핵심 기능 구현",
                deliverables=[r.title for r in high_priority[:5]],
                dependencies=[],
                order=1,
            ))

        # 2단계: 기능 확장
        if medium_priority:
            milestones.append(Milestone(
                id="MS-002",
                name="Phase 2 - 기능 확장",
                description="추가 기능 구현",
                deliverables=[r.title for r in medium_priority[:5]],
                dependencies=["MS-001"] if high_priority else [],
                order=2,
            ))

        # 3단계: 개선 및 부가 기능
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

    def _generate_title(
        self,
        requirements: List[NormalizedRequirement],
        context: PRDContext
    ) -> str:
        """PRD 제목을 생성합니다. (AI 호출 없이 로컬 처리)"""
        # 이미 제목이 있으면 그것 사용
        if context.title:
            return context.title

        # 소스 문서에서 제목 추출 시도
        if context.source_documents:
            for doc_name in context.source_documents:
                # 파일명에서 확장자 제거하고 제목으로 사용
                if doc_name and doc_name != "unknown":
                    title = doc_name.rsplit('.', 1)[0]  # 확장자 제거
                    # 불필요한 접미사 제거
                    for suffix in [' - 수행계획서', ' 수행계획서', ' 계획서', ' 제안서']:
                        title = title.replace(suffix, '')
                    if title and len(title) > 3:
                        return title

        # 첫 번째 요구사항 제목에서 추출
        if requirements:
            first_title = requirements[0].title
            # "슬라이드 X: " 같은 접두사 제거
            if ':' in first_title:
                first_title = first_title.split(':', 1)[1].strip()
            if first_title and len(first_title) > 5:
                return first_title[:50]

        return f"PRD - {datetime.now().strftime('%Y년 %m월')}"

    def _collect_unresolved_items(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[UnresolvedItem]:
        """요구사항에서 미해결 항목(누락 정보, 가정사항)을 수집하여 별도 목록으로 만듭니다."""
        items = []
        item_counter = 1

        for req in requirements:
            # 누락 정보를 질문으로 변환
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

            # 가정사항을 확인 필요 항목으로 변환
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

        return items[:20]  # 너무 많으면 잘라냄

    def _calculate_overall_confidence(
        self,
        requirements: List[NormalizedRequirement]
    ) -> float:
        """전체 요구사항의 평균 신뢰도를 계산합니다."""
        if not requirements:
            return 0.0

        scores = [r.confidence_score for r in requirements]
        return sum(scores) / len(scores)

    def _get_review_reasons(
        self,
        requirements: List[NormalizedRequirement]
    ) -> List[str]:
        """PM 검토가 필요한 이유들을 정리합니다."""
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