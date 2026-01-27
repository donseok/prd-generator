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

        # 제목 생성 (AI 활용)
        title = await self._generate_title(requirements, context)

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
        """AI를 사용하여 PRD의 개요 섹션(배경, 목표, 범위 등)을 작성합니다."""
        # 요구사항 일부를 요약해서 AI에게 전달
        req_summary = "\n".join([
            f"- {req.title}: {req.description[:100]}"
            for req in requirements[:15]
        ])

        additional = context.additional_context or {}

        prompt = f"""
다음 요구사항들을 기반으로 PRD 개요를 작성해주세요.

요구사항 요약:
{req_summary}

추가 컨텍스트:
{additional or '없음'}

JSON 형식으로 응답:
{{
  "background": "프로젝트 배경 (2-3문장)",
  "goals": ["목표 1", "목표 2", "목표 3"],
  "scope": "프로젝트 범위 설명",
  "out_of_scope": ["범위 외 항목 1", "범위 외 항목 2"],
  "target_users": ["대상 사용자 1", "대상 사용자 2"],
  "success_metrics": ["성공 지표 1", "성공 지표 2"]
}}"""

        result = await self._call_claude_json(
            system_prompt="당신은 PRD 문서 작성 전문가입니다. 주어진 요구사항을 분석하여 명확하고 실행 가능한 개요를 작성합니다.",
            user_prompt=prompt,
            section_name="overview",
        )

        if result:
            return PRDOverview(
                background=result.get("background", "프로젝트 배경 정보가 필요합니다."),
                goals=result.get("goals", ["목표 정의 필요"]),
                scope=result.get("scope", "범위 정의 필요"),
                out_of_scope=result.get("out_of_scope", []),
                target_users=result.get("target_users", ["대상 사용자 정의 필요"]),
                success_metrics=result.get("success_metrics", []),
            )
        else:
            return PRDOverview(
                background="자동 생성 실패 - 수동 입력 필요",
                goals=["목표 정의 필요"],
                scope="범위 정의 필요",
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

    async def _generate_title(
        self,
        requirements: List[NormalizedRequirement],
        context: PRDContext
    ) -> str:
        """PRD 제목을 생성합니다."""
        # 이미 제목이 있으면 그것 사용
        if context.title:
            return context.title

        req_titles = ", ".join([r.title for r in requirements[:5]])

        # AI에게 제목 추천 요청
        title = await self._call_claude_text(
            system_prompt="당신은 PRD 제목을 생성하는 전문가입니다. 간결하고 명확한 제목을 생성합니다.",
            user_prompt=f"다음 요구사항들을 포괄하는 PRD 제목을 한 줄로 작성해주세요 (20자 이내):\n{req_titles}",
            temperature=0.5,
            section_name="title",
        )

        if title:
            return title.strip().strip('"').strip("'")
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