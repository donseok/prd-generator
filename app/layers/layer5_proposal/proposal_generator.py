"""
Layer 5: 제안서(Proposal) 생성기입니다.
생성된 PRD 문서를 바탕으로 고객에게 보낼 제안서 문서를 자동으로 작성합니다.

주요 기능:
- 프로젝트 개요 및 범위 정의
- 솔루션 접근법 및 아키텍처 제안
- 일정 및 인력 계획 수립
- 기대 효과 및 리스크 분석
- 현재 방식 vs 제안 솔루션 비교 분석
- 투자 수익(ROI) 요약

개선 사항 (v3):
- PRDContextExtractor를 통한 풍부한 PRD 정보 활용
- 리스크 지표 자동 추출 및 반영
- 프로젝트 특성 기반 동적 산출물 생성
- 시간 기반 후속 절차 생성
- 경쟁 분석 섹션 추가
- 투자 요약 자동 산출
"""

import logging
from datetime import datetime
from typing import Optional

from app.models import PRDDocument, RequirementType
from app.services import ClaudeClient, get_claude_client
from app.layers.base_generator import BaseGenerator
from app.layers.prd_context_extractor import get_prd_context_extractor

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
    InvestmentSummary,
)
from .prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    SOLUTION_APPROACH_PROMPT,
    EXPECTED_BENEFITS_PROMPT,
    RESOURCE_PLAN_PROMPT,
    COMPETITIVE_ANALYSIS_PROMPT,
)

logger = logging.getLogger(__name__)

# 인건비 단가 상수 (M/M 당 평균 비용, 만원 단위)
COST_PER_MAN_MONTH = 1200  # 1,200만원/M/M


class ProposalGenerator(BaseGenerator[PRDDocument, ProposalDocument, ProposalContext]):
    """
    제안서 생성기 클래스입니다.
    여러 작업을 병렬로 처리하여 빠르게 제안서를 만듭니다.
    """

    _id_prefix = "PROP"
    _generator_name = "ProposalGenerator"

    async def _do_generate(
        self,
        prd: PRDDocument,
        context: ProposalContext,
    ) -> ProposalDocument:
        """
        제안서 생성 메인 로직입니다.

        효율을 위해 다음 3단계로 진행됩니다:
        1. 로컬 처리 (PRD 내용 그대로 가져오기) - 빠름
        2. AI 병렬 처리 (솔루션, 인력, 기대효과, 경쟁 분석 등 창작이 필요한 부분) - 동시에 진행
        3. 마무리 처리 (요약문 작성, 투자 요약 산출)
        """
        import asyncio

        # 문서 ID 생성
        proposal_id = self._generate_id()

        # 제목 설정
        project_name = context.project_name or prd.title
        title = f"{context.client_name} {project_name} 제안서"

        # ========== 1단계: 로컬 처리 (빠른 작업) ==========
        # PRD 내용을 그대로 옮겨오거나 간단한 규칙으로 변환하는 작업들입니다.

        project_overview = self._extract_project_overview(prd)
        logger.info("[ProposalGenerator] 프로젝트 개요 추출 완료")

        scope_of_work = self._extract_scope_of_work(prd)
        logger.info("[ProposalGenerator] 작업 범위 추출 완료")

        timeline = self._convert_milestones_to_timeline(prd, context)
        logger.info("[ProposalGenerator] 일정 계획 변환 완료")

        deliverables = self._generate_deliverables(prd)
        logger.info("[ProposalGenerator] 산출물 목록 생성 완료")

        risks = self._assess_risks(prd)
        logger.info("[ProposalGenerator] 리스크 평가 완료")

        assumptions = self._extract_assumptions(prd)
        logger.info("[ProposalGenerator] 전제 조건 추출 완료")

        next_steps = self._generate_next_steps(context)

        # ========== 2단계: AI 병렬 처리 (창작 작업) ==========
        # AI의 도움이 필요한 부분들을 동시에 요청하여 시간을 절약합니다.
        logger.info("[ProposalGenerator] AI 병렬 처리 시작")

        # 네 가지 작업을 동시에 실행 (비동기)
        solution_task = self._generate_solution_approach(prd)
        resource_task = self._generate_resource_plan(prd, context)
        benefits_task = self._generate_expected_benefits(prd)
        competitive_task = self._generate_competitive_analysis(prd)

        # 결과가 다 나올 때까지 기다림
        solution_approach, resource_plan, expected_benefits, competitive_analysis = await asyncio.gather(
            solution_task,
            resource_task,
            benefits_task,
            competitive_task,
        )

        logger.info("[ProposalGenerator] AI 병렬 처리 완료")

        # ========== 3단계: 마무리 처리 ==========
        # 앞선 결과물들을 종합하여 경영진용 요약문을 작성합니다.
        executive_summary = await self._generate_executive_summary(
            prd, context, project_overview, expected_benefits
        )
        logger.info("[ProposalGenerator] 경영진 요약 생성 완료")

        # 투자 요약 산출
        investment_summary = self._calculate_investment_summary(
            resource_plan, expected_benefits, context
        )
        logger.info("[ProposalGenerator] 투자 요약 산출 완료")

        # 메타데이터 생성
        metadata = ProposalMetadata(
            source_prd_id=prd.id,
            source_prd_title=prd.title,
            overall_confidence=prd.metadata.overall_confidence,
        )

        # 최종 제안서 객체 반환
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
            competitive_analysis=competitive_analysis,
            investment_summary=investment_summary,
            metadata=metadata,
        )

    def _extract_project_overview(self, prd: PRDDocument) -> ProjectOverview:
        """PRD의 내용을 바탕으로 프로젝트 개요를 작성합니다."""
        return ProjectOverview(
            background=prd.overview.background,
            objectives=prd.overview.goals,
            success_criteria=prd.overview.success_metrics or [],
        )

    def _extract_scope_of_work(self, prd: PRDDocument) -> ScopeOfWork:
        """할 일(범위)과 안 할 일(범위 제외)을 정리합니다."""
        in_scope = []
        if prd.overview.scope:
            in_scope.append(prd.overview.scope)

        # 주요 기능들을 카테고리별로 묶어서 보여줍니다.
        key_features = []

        # 기능 요구사항 (FR)
        fr_titles = [r.title for r in prd.functional_requirements[:10]]
        if fr_titles:
            key_features.append({
                "name": "기능 요구사항",
                "description": "핵심 비즈니스 기능 구현",
                "count": len(prd.functional_requirements),
            })
            in_scope.extend(fr_titles[:5])

        # 비기능 요구사항 (NFR)
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
        """AI를 사용하여 어떻게 개발할지(솔루션 접근법)를 작성합니다. (개선: PRD 컨텍스트 활용)"""
        # PRD 컨텍스트 추출기 활용
        extractor = get_prd_context_extractor()
        prd_text = extractor.to_prompt_text(prd, include_details=False)
        risk_indicators = extractor.get_risk_indicators(prd)

        # 기술 제약조건이 있으면 기술 스택 힌트로 사용
        tech_stack = []
        for constraint in prd.constraints:
            if any(kw in constraint.title.lower() for kw in ["기술", "스택", "프레임워크", "언어"]):
                tech_stack.append(constraint.title)

        # 아키텍처 결정에 영향을 주는 특수 요구사항
        special_considerations = []
        if risk_indicators["real_time_requirements"]:
            special_considerations.append("실시간 데이터 처리 필요 - WebSocket/이벤트 기반 아키텍처 고려")
        if risk_indicators["integration_requirements"]:
            special_considerations.append("외부 시스템 연동 필요 - API Gateway/어댑터 패턴 고려")
        if len(prd.functional_requirements) > 20:
            special_considerations.append("대규모 기능 - 마이크로서비스/모듈러 아키텍처 고려")
        if risk_indicators["security_requirements"]:
            special_considerations.append("보안 요구사항 존재 - OAuth2/JWT 인증, RBAC 권한 관리 고려")

        prompt = f"""{SOLUTION_APPROACH_PROMPT}

{prd_text}

## 기술 제약사항
{chr(10).join([f'- {c.title}: {c.description[:100]}' for c in prd.constraints[:8]]) if prd.constraints else '특별한 제약 없음'}

## 아키텍처 고려사항
{chr(10).join([f'- {s}' for s in special_considerations]) if special_considerations else '일반적인 웹 애플리케이션 아키텍처 적용'}
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
                key_differentiators=result.get("key_differentiators", []),
            )
        except Exception as e:
            logger.warning(f"[ProposalGenerator] 솔루션 접근법 생성 실패: {e}")
            return SolutionApproach(
                overview="요구사항 기반 맞춤형 솔루션 제공",
                architecture="클라우드 기반 웹/모바일 시스템",
                technology_stack=tech_stack,
                methodology="애자일 방법론 기반 개발",
                key_differentiators=[],
            )

    def _convert_milestones_to_timeline(
        self,
        prd: PRDDocument,
        context: ProposalContext,
    ) -> Timeline:
        """PRD의 마일스톤을 일정표(Timeline)로 변환합니다."""
        phases = []

        # 마일스톤이 없으면 기본 일정 템플릿 사용
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
                    deliverables=[]
                ))

        total_duration = f"{context.project_duration_months or 6}개월"

        return Timeline(
            total_duration=total_duration,
            phases=phases,
        )

    def _generate_deliverables(self, prd: PRDDocument) -> list[Deliverable]:
        """프로젝트 특성에 맞춰 산출물 목록을 동적으로 생성합니다."""
        # 기본 산출물 (항상 포함)
        deliverables = [
            Deliverable(name="요구사항 정의서", description="상세 요구사항 문서", phase="분석"),
            Deliverable(name="시스템 설계서", description="아키텍처 및 상세 설계", phase="설계"),
            Deliverable(name="소스 코드", description="개발된 시스템 코드", phase="개발"),
            Deliverable(name="테스트 결과서", description="테스트 수행 결과 및 품질 보고서", phase="테스트"),
        ]

        # PRD 컨텍스트에서 리스크 지표 추출
        extractor = get_prd_context_extractor()
        risk_indicators = extractor.get_risk_indicators(prd)

        # 프로젝트 특성 기반 추가 산출물
        added_specific = set()

        # UI/UX 관련 요구사항이 있는지 확인
        has_ui_requirements = any(
            any(kw in r.title.lower() for kw in ["화면", "ui", "ux", "디자인", "대시보드", "인터페이스", "프론트", "웹", "앱", "모바일"])
            for r in prd.functional_requirements
        )
        if has_ui_requirements and "ui" not in added_specific:
            deliverables.append(Deliverable(
                name="UI/UX 설계서", description="화면 설계 및 사용자 경험 프로토타입", phase="설계"
            ))
            added_specific.add("ui")

        # 실시간 처리 요구사항
        if risk_indicators["real_time_requirements"] and "realtime" not in added_specific:
            deliverables.append(Deliverable(
                name="실시간 모니터링 대시보드 설계서",
                description="실시간 데이터 처리 아키텍처 및 모니터링 화면 설계",
                phase="설계",
            ))
            added_specific.add("realtime")

        # 외부 시스템 연동
        if risk_indicators["integration_requirements"] and "integration" not in added_specific:
            deliverables.append(Deliverable(
                name="인터페이스 정의서",
                description="외부 시스템 연동 인터페이스 규격 및 테스트 시나리오",
                phase="설계",
            ))
            added_specific.add("integration")

        # 보안 요구사항
        if risk_indicators["security_requirements"] and "security" not in added_specific:
            deliverables.append(Deliverable(
                name="보안 점검 보고서",
                description="보안 취약점 점검 및 대응 결과",
                phase="테스트",
            ))
            added_specific.add("security")

        # 데이터 관련 요구사항 확인
        has_data_requirements = any(
            any(kw in r.title.lower() for kw in ["데이터", "마이그레이션", "이관", "db", "데이터베이스", "분석", "리포트", "보고서"])
            for r in prd.functional_requirements
        )
        if has_data_requirements and "data" not in added_specific:
            deliverables.append(Deliverable(
                name="데이터베이스 설계서",
                description="데이터 모델링 및 마이그레이션 계획",
                phase="설계",
            ))
            added_specific.add("data")

        # 기본적으로 사용자 매뉴얼은 항상 포함
        deliverables.append(Deliverable(name="사용자 매뉴얼", description="시스템 사용 가이드", phase="오픈"))
        deliverables.append(Deliverable(name="운영 매뉴얼", description="시스템 운영 및 장애 대응 가이드", phase="오픈"))

        return deliverables

    async def _generate_resource_plan(
        self,
        prd: PRDDocument,
        context: ProposalContext,
    ) -> ResourcePlan:
        """프로젝트 규모에 맞춰 필요한 인력 구성을 계획합니다."""
        # 기본 팀 구성
        team_structure = [
            TeamMember(role="PM", count=1, responsibilities=["프로젝트 관리", "일정 관리", "이해관계자 커뮤니케이션"]),
            TeamMember(role="기획자", count=1, responsibilities=["요구사항 분석", "기능 정의"]),
            TeamMember(role="UI/UX 디자이너", count=1, responsibilities=["화면 설계", "프로토타입 제작"]),
            TeamMember(role="프론트엔드 개발자", count=2, responsibilities=["웹/앱 UI 개발"]),
            TeamMember(role="백엔드 개발자", count=2, responsibilities=["서버 개발", "API 개발"]),
            TeamMember(role="QA", count=1, responsibilities=["테스트 수행", "품질 관리"]),
        ]

        # 요구사항이 많으면 개발자를 더 추가합니다.
        total_reqs = (
            len(prd.functional_requirements)
            + len(prd.non_functional_requirements)
            + len(prd.constraints)
        )

        if total_reqs > 100:
            team_structure[3].count = 3  # 프론트엔드 +1
            team_structure[4].count = 3  # 백엔드 +1

        # 총 투입 공수(M/M) 계산 (대략적인 추정)
        duration_months = context.project_duration_months or 6
        total_members = sum(m.count for m in team_structure)
        total_mm = total_members * duration_months * 0.8  # 휴가 등 고려하여 80% 효율 가정

        return ResourcePlan(
            team_structure=team_structure,
            total_man_months=round(total_mm, 1),
        )

    def _assess_risks(self, prd: PRDDocument) -> list[Risk]:
        """프로젝트의 잠재적 위험 요소를 분석합니다. (개선: PRD 컨텍스트 활용)"""
        risks = []

        # PRD 컨텍스트에서 리스크 지표 추출
        extractor = get_prd_context_extractor()
        risk_indicators = extractor.get_risk_indicators(prd)

        # 1. 신뢰도 낮은 요구사항 (불명확성 리스크)
        low_conf_reqs = risk_indicators["low_confidence_requirements"]
        if low_conf_reqs:
            sample_titles = ", ".join([r["title"][:20] for r in low_conf_reqs[:3]])
            risks.append(Risk(
                description=f"요구사항 명확성 부족 ({len(low_conf_reqs)}건)",
                level=RiskLevel.MEDIUM if len(low_conf_reqs) < 5 else RiskLevel.HIGH,
                impact="요구사항 변경으로 인한 일정 지연 가능",
                mitigation="요구사항 확정 미팅 및 문서화 강화",
                source_requirement_id=low_conf_reqs[0]["id"] if low_conf_reqs else None,
            ))

        # 2. 불명확 정보 존재 (정보 부족 리스크)
        missing_info = risk_indicators["missing_info_items"]
        if missing_info:
            risks.append(Risk(
                description=f"불명확한 정보 존재 ({len(missing_info)}건)",
                level=RiskLevel.MEDIUM,
                impact="추가 분석 및 확인 작업으로 일정 지연 가능",
                mitigation=f"착수 전 확인 필요: {', '.join(missing_info[:3])}",
            ))

        # 3. 미해결 사항 (의사결정 리스크)
        unresolved = risk_indicators["unresolved_items"]
        high_priority_unresolved = [u for u in unresolved if u.get("priority") == "HIGH"]
        if high_priority_unresolved:
            risks.append(Risk(
                description=f"미확정 의사결정 사항 ({len(high_priority_unresolved)}건)",
                level=RiskLevel.HIGH,
                impact="프로젝트 방향성 및 일정에 영향",
                mitigation="착수 전 주요 사항 의사결정 완료 필요",
            ))

        # 4. 외부 연동 (기술적 복잡성 리스크)
        integration_ids = risk_indicators["integration_requirements"]
        if integration_ids:
            risks.append(Risk(
                description=f"외부 시스템 연동 복잡성 ({len(integration_ids)}건)",
                level=RiskLevel.MEDIUM,
                impact="연동 인터페이스 변경 시 추가 개발 필요",
                mitigation="사전 인터페이스 정의 및 테스트 환경 확보",
            ))

        # 5. 실시간 처리 (기술적 난이도 리스크)
        realtime_ids = risk_indicators["real_time_requirements"]
        if realtime_ids:
            risks.append(Risk(
                description=f"실시간 처리 요구사항 ({len(realtime_ids)}건)",
                level=RiskLevel.MEDIUM,
                impact="실시간 아키텍처 구현 복잡성",
                mitigation="WebSocket/SSE 기반 아키텍처 PoC 선행",
            ))

        # 6. 보안 요구사항 (컴플라이언스 리스크)
        security_ids = risk_indicators["security_requirements"]
        if security_ids:
            risks.append(Risk(
                description=f"보안 요구사항 ({len(security_ids)}건)",
                level=RiskLevel.MEDIUM,
                impact="보안 검토 및 테스트로 일정 영향 가능",
                mitigation="보안 전문가 참여 및 보안 테스트 계획 수립",
            ))

        # 7. 일정 복잡성
        if prd.milestones and len(prd.milestones) > 3:
            risks.append(Risk(
                description="다단계 프로젝트 일정 관리",
                level=RiskLevel.LOW,
                impact="단계 간 의존성으로 인한 일정 조정",
                mitigation="주간 진척 관리 및 버퍼 일정 확보",
            ))

        # 리스크가 없으면 일반적인 리스크 추가
        if not risks:
            risks.append(Risk(
                description="일반적인 프로젝트 리스크",
                level=RiskLevel.LOW,
                impact="일정 또는 비용 변동 가능",
                mitigation="정기 리스크 모니터링 및 대응",
            ))

        return risks

    def _extract_assumptions(self, prd: PRDDocument) -> list[str]:
        """프로젝트 수행을 위한 전제 조건들을 정리합니다."""
        assumptions = []

        # 요구사항에 명시된 가정사항들 수집
        for req in prd.functional_requirements + prd.non_functional_requirements:
            if req.assumptions:
                assumptions.extend(req.assumptions[:2])

        # 제약조건에서 전제 조건 추출
        for constraint in prd.constraints:
            desc = constraint.description or ""
            title = constraint.title or ""
            # 기술/환경 관련 제약조건을 전제 조건으로 변환
            if any(kw in title.lower() for kw in ["기술", "환경", "인프라", "서버", "클라우드", "네트워크"]):
                assumptions.append(f"{title}에 대한 사전 준비 완료")
            elif any(kw in title.lower() for kw in ["데이터", "마이그레이션", "이관"]):
                assumptions.append(f"기존 {title} 관련 데이터 접근 권한 확보")

        # 기능 요구사항에서 외부 연동 관련 전제 조건 추출
        extractor = get_prd_context_extractor()
        risk_indicators = extractor.get_risk_indicators(prd)

        if risk_indicators["integration_requirements"]:
            assumptions.append("외부 연동 시스템의 API 문서 및 테스트 환경 제공")

        if risk_indicators["security_requirements"]:
            assumptions.append("보안 정책 및 컴플라이언스 요구사항 사전 공유")

        # 기본 전제조건 추가 (최소한만)
        default_assumptions = [
            "고객사 담당자의 적시 의사결정 지원",
            "필요 자료 및 정보의 적시 제공",
        ]

        # 기본 전제조건은 프로젝트 특성 전제조건이 적을 때만 추가
        if len(assumptions) < 4:
            assumptions.extend(default_assumptions)
        else:
            # 최소 1개는 추가
            assumptions.append(default_assumptions[0])

        # 중복 제거 및 10개로 제한
        return list(dict.fromkeys(assumptions))[:10]

    async def _generate_expected_benefits(self, prd: PRDDocument) -> list[str]:
        """프로젝트 완료 시 기대되는 효과를 작성합니다."""
        # 1. 비기능 요구사항에서 힌트 찾기 (성능 향상, 비용 절감 등)
        benefits = []
        for nfr in prd.non_functional_requirements:
            if any(kw in nfr.title for kw in ["감소", "단축", "향상", "개선", "%"]):
                benefits.append(nfr.title)

        if len(benefits) >= 5:
            return benefits[:8]

        # 2. 부족하면 AI에게 추가 작성을 요청
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
            # 실패 시 기본 효과 추가
            benefits.extend([
                "업무 효율성 향상",
                "사용자 만족도 개선",
                "데이터 기반 의사결정 지원",
            ])

        # benefits에 dict 객체가 포함될 수 있으므로 문자열로 정규화 후 중복 제거
        normalized = []
        seen = set()
        for b in benefits:
            text = b if isinstance(b, str) else (b.get("benefit") or b.get("title") or str(b))
            if text not in seen:
                seen.add(text)
                normalized.append(text)
        return normalized[:8]

    async def _generate_competitive_analysis(self, prd: PRDDocument) -> list[dict]:
        """현재 방식 vs 제안 솔루션 비교 분석을 생성합니다."""
        extractor = get_prd_context_extractor()
        prd_text = extractor.to_prompt_text(prd, include_details=False)

        fr_summary = "\n".join([f"- {r.title}" for r in prd.functional_requirements[:10]])
        nfr_summary = "\n".join([f"- {r.title}" for r in prd.non_functional_requirements[:5]])

        prompt = f"""{COMPETITIVE_ANALYSIS_PROMPT}

프로젝트: {prd.title}

배경: {prd.overview.background[:500]}

주요 기능 요구사항:
{fr_summary}

비기능 요구사항:
{nfr_summary}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="IT 전략 컨설턴트로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            if isinstance(result, dict) and "categories" in result:
                return result["categories"]
            elif isinstance(result, list):
                return result
            else:
                return []

        except Exception as e:
            logger.warning(f"[ProposalGenerator] 경쟁 분석 생성 실패: {e}")
            return []

    async def _generate_executive_summary(
        self,
        prd: PRDDocument,
        context: ProposalContext,
        overview: ProjectOverview,
        benefits: list[str],
    ) -> str:
        """경영진을 위한 한 페이지 요약문을 작성합니다."""
        prompt = f"""{EXECUTIVE_SUMMARY_PROMPT}

고객사: {context.client_name}
프로젝트: {prd.title}
프로젝트 기간: {context.project_duration_months or 6}개월

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
            return f"{context.client_name}의 {prd.title} 프로젝트는 {overview.background[:200]}. 본 제안서는 {len(prd.functional_requirements)}개의 기능 요구사항과 {len(prd.non_functional_requirements)}개의 비기능 요구사항을 기반으로 최적의 솔루션을 제안합니다."

    def _generate_next_steps(self, context: ProposalContext) -> list[str]:
        """제안서 제출 이후의 진행 절차를 시간 기반으로 안내합니다."""
        duration = context.project_duration_months or 6

        steps = [
            "제안서 검토 및 Q&A 세션 (제안서 수령 후 1주 이내)",
            "상세 범위 확정 및 일정 협의 (Q&A 후 1주 이내)",
            "계약 조건 협의 및 계약 체결 (협의 후 2주 이내)",
            f"프로젝트 착수 미팅 및 킥오프 (계약 후 1주 이내)",
            f"요구사항 상세화 및 설계 착수 (킥오프 후 즉시)",
        ]

        # 프로젝트 기간이 짧으면 긴급성 강조
        if duration <= 3:
            steps.append(f"** 프로젝트 기간이 {duration}개월로 촉박하므로, 신속한 의사결정이 프로젝트 성공의 핵심입니다.")
        elif duration <= 6:
            steps.append(f"원활한 프로젝트 수행을 위해 착수 후 2주 이내 핵심 요구사항 확정이 필요합니다.")

        return steps

    def _calculate_investment_summary(
        self,
        resource_plan: ResourcePlan,
        expected_benefits: list[str],
        context: ProposalContext,
    ) -> InvestmentSummary:
        """투입 공수와 기대효과를 기반으로 투자 요약을 산출합니다."""
        total_mm = resource_plan.total_man_months or 0
        total_cost = total_mm * COST_PER_MAN_MONTH  # 만원 단위

        # 비용 포맷팅
        if total_cost >= 10000:
            cost_str = f"약 {total_cost / 10000:.1f}억원"
        elif total_cost >= 1000:
            cost_str = f"약 {total_cost / 1000:.1f}천만원"
        else:
            cost_str = f"약 {total_cost:.0f}만원"

        # 연간 절감액 추정 (총 비용의 30-50% 수준으로 보수적 추정)
        estimated_savings = total_cost * 0.35
        if estimated_savings >= 10000:
            savings_str = f"약 {estimated_savings / 10000:.1f}억원 (보수적 추정)"
        elif estimated_savings >= 1000:
            savings_str = f"약 {estimated_savings / 1000:.1f}천만원 (보수적 추정)"
        else:
            savings_str = f"약 {estimated_savings:.0f}만원 (보수적 추정)"

        # 투자 회수 기간 계산
        if estimated_savings > 0:
            payback_years = total_cost / estimated_savings
            if payback_years <= 1:
                payback_str = f"약 {payback_years * 12:.0f}개월"
            else:
                payback_str = f"약 {payback_years:.1f}년"
        else:
            payback_str = "산정 불가"

        return InvestmentSummary(
            total_cost_estimate=f"{cost_str} ({total_mm} M/M 기준, 단가 {COST_PER_MAN_MONTH}만원/M/M)",
            expected_annual_savings=savings_str,
            payback_period=payback_str,
        )
