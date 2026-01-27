"""
Layer 6: TRD (기술 요구사항 문서) 생성기입니다.
PRD 내용을 바탕으로 구체적인 기술 스택, 아키텍처, DB 설계 등을 자동으로 제안합니다.

주요 기능:
- 기술 스택 추천 (언어, 프레임워크, DB 등)
- 시스템 아키텍처 설계
- 데이터베이스 모델링 및 API 명세
- 보안 및 인프라 요구사항 정의
"""

import logging
from datetime import datetime
from typing import Optional

from app.models import PRDDocument, RequirementType
from app.models.common import RiskLevel
from app.services import ClaudeClient, get_claude_client
from app.layers.base_generator import BaseGenerator

from .models import (
    TRDDocument,
    TRDContext,
    TRDMetadata,
    TechnologyStack,
    SystemComponent,
    ArchitectureLayer,
    SystemArchitecture,
    DatabaseEntity,
    DatabaseDesign,
    HTTPMethod,
    APIEndpoint,
    APISpecification,
    SecurityRequirement,
    PerformanceRequirement,
    InfrastructureRequirement,
    TechnicalRisk,
)
from .prompts import (
    TECHNOLOGY_STACK_PROMPT,
    SYSTEM_ARCHITECTURE_PROMPT,
    DATABASE_DESIGN_PROMPT,
    API_SPECIFICATION_PROMPT,
    TRD_SUMMARY_PROMPT,
    SECURITY_REQUIREMENTS_PROMPT,
    INFRASTRUCTURE_PROMPT,
)

logger = logging.getLogger(__name__)


class TRDGenerator(BaseGenerator[PRDDocument, TRDDocument, TRDContext]):
    """
    TRD 생성기 클래스입니다.
    여러 AI 작업을 병렬로 수행하여 복잡한 기술 문서를 빠르게 작성합니다.
    """

    _id_prefix = "TRD"
    _generator_name = "TRDGenerator"

    async def _do_generate(
        self,
        prd: PRDDocument,
        context: TRDContext,
    ) -> TRDDocument:
        """
        TRD 생성 메인 로직입니다.
        
        효율을 위해 작업을 4단계로 나누어 진행합니다:
        1. 독립적 AI 작업 (기술스택, DB, API) -> 동시에 실행
        2. 의존적 AI 작업 (아키텍처, 보안) -> 1번 완료 후 실행
        3. 로컬 작업 (성능, 인프라, 리스크) -> 계산만 하면 되므로 빠름
        4. 최종 요약 -> 모든 결과 종합
        """
        import asyncio

        trd_id = self._generate_id()
        title = f"{prd.title} - 기술 요구사항 문서 (TRD)"

        # ========== 1단계: 독립적 AI 작업 (병렬 처리) ==========
        # 서로 상관없는 작업들을 동시에 요청합니다.
        logger.info("[TRDGenerator] Phase 1: 독립 AI 작업 시작")

        tech_task = self._generate_technology_stack(prd, context)
        db_task = self._generate_database_design(prd)
        api_task = self._generate_api_specification(prd)

        # 3가지 작업 동시 실행
        technology_stack, database_design, api_specification = await asyncio.gather(
            tech_task,
            db_task,
            api_task
        )

        logger.info("[TRDGenerator] 기술스택/DB/API 생성 완료")

        # ========== 2단계: 의존적 AI 작업 (병렬 처리) ==========
        # 기술 스택이 결정되어야 아키텍처를 설계할 수 있습니다.
        logger.info("[TRDGenerator] Phase 2: 의존 AI 작업 시작")

        arch_task = self._generate_system_architecture(prd, technology_stack)
        security_task = self._extract_security_requirements(prd, context)

        system_architecture, security_requirements = await asyncio.gather(
            arch_task,
            security_task
        )

        logger.info("[TRDGenerator] 아키텍처/보안 생성 완료")

        # ========== 3단계: 로컬 처리 ==========
        # AI 없이 규칙 기반으로 처리할 수 있는 작업들입니다.
        
        # 성능 요구사항
        performance_requirements = self._extract_performance_requirements(prd)
        logger.info("[TRDGenerator] 성능 요구사항 추출 완료")

        # 인프라 요구사항 (기술 스택 참조)
        infrastructure_requirements = await self._generate_infrastructure(prd, technology_stack, context)
        logger.info("[TRDGenerator] 인프라 요구사항 생성 완료")

        # 기술 리스크 분석
        technical_risks = self._assess_technical_risks(prd, technology_stack)
        logger.info("[TRDGenerator] 기술 리스크 평가 완료")

        # ========== 4단계: 최종 요약 ==========
        # 모든 내용을 종합하여 요약문을 작성합니다.
        executive_summary = await self._generate_executive_summary(
            prd, technology_stack, system_architecture
        )
        logger.info("[TRDGenerator] 기술 요약 생성 완료")

        # 메타데이터 생성
        metadata = TRDMetadata(
            source_prd_id=prd.id,
            source_prd_title=prd.title,
        )

        # 최종 TRD 객체 반환
        return TRDDocument(
            id=trd_id,
            title=title,
            executive_summary=executive_summary,
            technology_stack=technology_stack,
            system_architecture=system_architecture,
            database_design=database_design,
            api_specification=api_specification,
            security_requirements=security_requirements,
            performance_requirements=performance_requirements,
            infrastructure_requirements=infrastructure_requirements,
            technical_risks=technical_risks,
            metadata=metadata,
        )

    async def _generate_technology_stack(
        self, prd: PRDDocument, context: TRDContext
    ) -> list[TechnologyStack]:
        """AI에게 적절한 기술 스택(언어, 프레임워크 등) 추천을 요청합니다."""
        # AI에게 줄 정보 요약
        fr_summary = "\n".join([f"- {r.title}: {r.description[:100]}" for r in prd.functional_requirements[:15]])
        nfr_summary = "\n".join([f"- {r.title}" for r in prd.non_functional_requirements[:10]])
        constraints_summary = "\n".join([f"- {c.title}" for c in prd.constraints[:5]])

        preferred_stack = ""
        if context.preferred_stack:
            preferred_stack = f"\n선호 기술 스택: {', '.join(context.preferred_stack)}"

        prompt = f"""{TECHNOLOGY_STACK_PROMPT}

프로젝트: {prd.title}

기능 요구사항:
{fr_summary}

비기능 요구사항:
{nfr_summary}

제약사항:
{constraints_summary}

배포 환경: {context.target_environment}
확장성 요구수준: {context.scalability_requirement}
보안 수준: {context.security_level}
{preferred_stack}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="시니어 솔루션 아키텍트로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            stacks = []
            raw_stacks = result.get("stacks", [])
            for stack_data in raw_stacks:
                stacks.append(TechnologyStack(
                    category=stack_data.get("category", ""),
                    technologies=stack_data.get("technologies", []),
                    rationale=stack_data.get("rationale", ""),
                ))
            return stacks

        except Exception as e:
            logger.warning(f"[TRDGenerator] 기술 스택 생성 실패: {e}")
            # 실패 시 기본값 반환
            return [
                TechnologyStack(
                    category="Frontend",
                    technologies=["React", "TypeScript"],
                    rationale="널리 사용되는 프론트엔드 스택",
                ),
                TechnologyStack(
                    category="Backend",
                    technologies=["Python", "FastAPI"],
                    rationale="빠른 개발과 높은 성능",
                ),
                TechnologyStack(
                    category="Database",
                    technologies=["PostgreSQL"],
                    rationale="안정적인 관계형 데이터베이스",
                ),
            ]

    async def _generate_system_architecture(
        self, prd: PRDDocument, tech_stack: list[TechnologyStack]
    ) -> SystemArchitecture:
        """시스템 구조(아키텍처)를 설계합니다."""
        fr_summary = "\n".join([f"- {r.title}" for r in prd.functional_requirements[:10]])
        tech_summary = "\n".join([f"- {s.category}: {', '.join(s.technologies)}" for s in tech_stack])

        prompt = f"""{SYSTEM_ARCHITECTURE_PROMPT}

프로젝트: {prd.title}

주요 기능 요구사항:
{fr_summary}

기술 스택:
{tech_summary}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="시스템 아키텍트로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            layers = []
            for layer_data in result.get("layers", []):
                components = []
                for comp_data in layer_data.get("components", []):
                    components.append(SystemComponent(
                        name=comp_data.get("name", ""),
                        type=comp_data.get("type", "service"),
                        description=comp_data.get("description", ""),
                        responsibilities=comp_data.get("responsibilities", []),
                        dependencies=comp_data.get("dependencies", []),
                        interfaces=comp_data.get("interfaces", []),
                    ))

                layers.append(ArchitectureLayer(
                    name=layer_data.get("name", ""),
                    description=layer_data.get("description", ""),
                    components=components,
                ))

            return SystemArchitecture(
                overview=result.get("overview", ""),
                architecture_style=result.get("architecture_style", "Layered Architecture"),
                layers=layers,
                data_flow=result.get("data_flow", ""),
            )

        except Exception as e:
            logger.warning(f"[TRDGenerator] 시스템 아키텍처 생성 실패: {e}")
            return SystemArchitecture(
                overview="표준 웹 애플리케이션 아키텍처",
                architecture_style="Layered Architecture",
                layers=[
                    ArchitectureLayer(
                        name="Presentation Layer",
                        description="사용자 인터페이스",
                        components=[SystemComponent(name="Web App", type="application", description="웹 프론트엔드")],
                    ),
                    ArchitectureLayer(
                        name="Application Layer",
                        description="비즈니스 로직",
                        components=[SystemComponent(name="API Server", type="service", description="백엔드 API 서버")],
                    ),
                    ArchitectureLayer(
                        name="Data Layer",
                        description="데이터 저장",
                        components=[SystemComponent(name="Database", type="database", description="주 데이터베이스")],
                    ),
                ],
            )

    async def _generate_database_design(self, prd: PRDDocument) -> DatabaseDesign:
        """데이터베이스 구조(테이블)를 설계합니다."""
        fr_summary = "\n".join([f"- {r.title}: {r.description[:150]}" for r in prd.functional_requirements[:15]])

        prompt = f"""{DATABASE_DESIGN_PROMPT}

프로젝트: {prd.title}

기능 요구사항:
{fr_summary}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="데이터베이스 설계 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            entities = []
            for entity_data in result.get("entities", []):
                entities.append(DatabaseEntity(
                    name=entity_data.get("name", ""),
                    description=entity_data.get("description", ""),
                    attributes=entity_data.get("attributes", []),
                    primary_key=entity_data.get("primary_key", "id"),
                    relationships=entity_data.get("relationships", []),
                ))

            return DatabaseDesign(
                database_type=result.get("database_type", "RDBMS"),
                recommended_engine=result.get("recommended_engine", "PostgreSQL"),
                entities=entities,
                indexing_strategy=result.get("indexing_strategy", ""),
                partitioning_strategy=result.get("partitioning_strategy", ""),
            )

        except Exception as e:
            logger.warning(f"[TRDGenerator] 데이터베이스 설계 실패: {e}")
            return DatabaseDesign(
                database_type="RDBMS",
                recommended_engine="PostgreSQL",
                entities=[],
            )

    async def _generate_api_specification(self, prd: PRDDocument) -> APISpecification:
        """주요 API 명세를 설계합니다."""
        fr_summary = "\n".join([
            f"- {r.id}: {r.title} - {r.description[:100]}"
            for r in prd.functional_requirements[:20]
        ])

        prompt = f"""{API_SPECIFICATION_PROMPT}

프로젝트: {prd.title}

기능 요구사항:
{fr_summary}
"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="API 설계 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.3,
            )

            endpoints = []
            for ep_data in result.get("endpoints", []):
                method_str = ep_data.get("method", "GET").upper()
                try:
                    method = HTTPMethod(method_str)
                except ValueError:
                    method = HTTPMethod.GET

                endpoints.append(APIEndpoint(
                    path=ep_data.get("path", "/"),
                    method=method,
                    description=ep_data.get("description", ""),
                    request_body=ep_data.get("request_body"),
                    response_body=ep_data.get("response_body"),
                    authentication=ep_data.get("authentication", True),
                    related_requirement_id=ep_data.get("related_requirement_id"),
                ))

            return APISpecification(
                base_url=result.get("base_url", "/api/v1"),
                authentication_method=result.get("authentication_method", "JWT"),
                endpoints=endpoints,
                error_handling=result.get("error_handling", "표준 HTTP 상태 코드 및 JSON 에러 응답 사용"),
            )

        except Exception as e:
            logger.warning(f"[TRDGenerator] API 명세 생성 실패: {e}")
            return APISpecification(
                base_url="/api/v1",
                authentication_method="JWT",
                endpoints=[],
            )

    async def _extract_security_requirements(
        self, prd: PRDDocument, context: TRDContext
    ) -> list[SecurityRequirement]:
        """보안 요구사항을 정리합니다."""
        security_reqs = []

        # NFR에서 보안 관련 항목 찾기
        security_keywords = ["보안", "인증", "권한", "암호화", "security", "auth", "encryption"]
        for nfr in prd.non_functional_requirements:
            if any(kw in nfr.title.lower() or kw in nfr.description.lower() for kw in security_keywords):
                security_reqs.append(SecurityRequirement(
                    category="NFR-Based",
                    requirement=nfr.title,
                    implementation=nfr.description[:200] if nfr.description else "",
                    priority="HIGH",
                ))

        # 기본 보안 요구사항 추가
        if context.security_level in ["standard", "high"]:
            default_reqs = [
                SecurityRequirement(
                    category="Authentication",
                    requirement="사용자 인증 체계 구축",
                    implementation="JWT 기반 토큰 인증",
                    priority="HIGH",
                ),
                SecurityRequirement(
                    category="Authorization",
                    requirement="역할 기반 접근 제어(RBAC)",
                    implementation="사용자 역할별 권한 관리",
                    priority="HIGH",
                ),
                SecurityRequirement(
                    category="Data Protection",
                    requirement="민감 데이터 암호화",
                    implementation="AES-256 암호화 적용",
                    priority="HIGH",
                ),
            ]
            security_reqs.extend(default_reqs)

        if context.security_level == "high":
            security_reqs.append(SecurityRequirement(
                category="Audit",
                requirement="감사 로깅",
                implementation="모든 주요 작업에 대한 감사 로그 기록",
                priority="MEDIUM",
            ))

        return security_reqs

    def _extract_performance_requirements(self, prd: PRDDocument) -> list[PerformanceRequirement]:
        """성능 요구사항을 정리합니다."""
        perf_reqs = []

        perf_keywords = ["성능", "응답", "처리량", "지연", "performance", "latency", "throughput"]
        for nfr in prd.non_functional_requirements:
            if any(kw in nfr.title.lower() or kw in nfr.description.lower() for kw in perf_keywords):
                perf_reqs.append(PerformanceRequirement(
                    metric=nfr.title,
                    target_value=nfr.description[:100] if nfr.description else "정의 필요",
                    measurement_method="성능 테스트 도구 활용",
                ))

        # 기본 성능 요구사항 추가
        if not perf_reqs:
            perf_reqs = [
                PerformanceRequirement(
                    metric="API 응답 시간",
                    target_value="평균 200ms 이하",
                    measurement_method="APM 도구 모니터링",
                ),
                PerformanceRequirement(
                    metric="동시 사용자 처리",
                    target_value="100명 이상",
                    measurement_method="부하 테스트",
                ),
                PerformanceRequirement(
                    metric="시스템 가용성",
                    target_value="99.9% 이상",
                    measurement_method="업타임 모니터링",
                ),
            ]

        return perf_reqs

    async def _generate_infrastructure(
        self, prd: PRDDocument, tech_stack: list[TechnologyStack], context: TRDContext
    ) -> list[InfrastructureRequirement]:
        """서버 및 인프라 요구사항을 정의합니다."""
        infra_reqs = []

        # 클라우드 vs 온프레미스 환경에 따른 기본 구성
        if context.target_environment == "cloud":
            infra_reqs = [
                InfrastructureRequirement(
                    category="Compute",
                    specification="Application Server (4 vCPU, 16GB RAM)",
                    quantity="2",
                    purpose="웹 애플리케이션 서버",
                ),
                InfrastructureRequirement(
                    category="Database",
                    specification="Managed Database (8 vCPU, 32GB RAM, 500GB SSD)",
                    quantity="1 (Primary-Replica)",
                    purpose="주 데이터베이스",
                ),
                InfrastructureRequirement(
                    category="Storage",
                    specification="Object Storage (S3/GCS)",
                    quantity="500GB",
                    purpose="파일 저장소",
                ),
                InfrastructureRequirement(
                    category="Network",
                    specification="Load Balancer + CDN",
                    quantity="1",
                    purpose="트래픽 분산 및 정적 콘텐츠 배포",
                ),
            ]
        else:  # 온프레미스 또는 하이브리드
            infra_reqs = [
                InfrastructureRequirement(
                    category="Compute",
                    specification="Physical/VM Server (8 Core, 32GB RAM)",
                    quantity="2",
                    purpose="애플리케이션 서버",
                ),
                InfrastructureRequirement(
                    category="Database",
                    specification="Database Server (16 Core, 64GB RAM, 1TB SSD)",
                    quantity="2 (Active-Standby)",
                    purpose="데이터베이스 서버",
                ),
            ]

        # 확장성이 많이 필요하면 캐시나 메시지 큐 추가
        if context.scalability_requirement == "high":
            infra_reqs.append(InfrastructureRequirement(
                category="Cache",
                specification="In-Memory Cache (Redis Cluster)",
                quantity="3 nodes",
                purpose="캐싱 및 세션 관리",
            ))
            infra_reqs.append(InfrastructureRequirement(
                category="Message Queue",
                specification="Message Broker (RabbitMQ/Kafka)",
                quantity="3 nodes",
                purpose="비동기 메시지 처리",
            ))

        return infra_reqs

    def _assess_technical_risks(
        self, prd: PRDDocument, tech_stack: list[TechnologyStack]
    ) -> list[TechnicalRisk]:
        """기술적인 위험 요소를 분석합니다."""
        risks = []

        # 1. 연동 복잡성 리스크
        integration_reqs = [
            r for r in prd.functional_requirements + prd.constraints
            if any(kw in r.title.lower() for kw in ["연동", "통합", "api", "interface"])
        ]
        if integration_reqs:
            risks.append(TechnicalRisk(
                description="외부 시스템 연동 복잡성",
                level=RiskLevel.MEDIUM,
                impact="연동 인터페이스 변경 시 추가 개발 필요",
                mitigation="사전 인터페이스 정의 및 Mock 서버 활용",
                contingency="연동 범위 축소 또는 단계별 구현",
            ))

        # 2. 신기술 사용 리스크
        new_tech_keywords = ["beta", "preview", "experimental"]
        for stack in tech_stack:
            if any(kw in " ".join(stack.technologies).lower() for kw in new_tech_keywords):
                risks.append(TechnicalRisk(
                    description=f"신규/미성숙 기술 사용 ({stack.category})",
                    level=RiskLevel.MEDIUM,
                    impact="기술 지원 부족 및 예상치 못한 이슈 발생",
                    mitigation="PoC 수행 및 대안 기술 검토",
                    contingency="안정적인 대체 기술로 전환",
                ))

        # 3. 대용량 처리 리스크
        large_data_reqs = [
            r for r in prd.functional_requirements + prd.non_functional_requirements
            if any(kw in r.title.lower() or kw in r.description.lower()
                   for kw in ["대용량", "대규모", "실시간", "대량"])
        ]
        if large_data_reqs:
            risks.append(TechnicalRisk(
                description="대용량 데이터 처리 성능",
                level=RiskLevel.MEDIUM,
                impact="응답 시간 지연 및 시스템 과부하",
                mitigation="캐싱 전략 및 비동기 처리 적용",
                contingency="데이터 처리 범위 조정",
            ))

        # 4. 보안 리스크 (항상 포함)
        risks.append(TechnicalRisk(
            description="보안 취약점 발생 가능성",
            level=RiskLevel.HIGH,
            impact="데이터 유출 및 서비스 중단",
            mitigation="보안 코드 리뷰 및 취약점 스캔 정기 수행",
            contingency="보안 패치 즉시 적용 체계 구축",
        ))

        # 리스크가 너무 적으면 일반 리스크 추가
        if len(risks) < 2:
            risks.append(TechnicalRisk(
                description="일정 내 기술 구현 난이도",
                level=RiskLevel.LOW,
                impact="일정 지연 가능성",
                mitigation="기술 검증(PoC) 선행 및 버퍼 일정 확보",
                contingency="기능 우선순위 조정",
            ))

        return risks

    async def _generate_executive_summary(
        self,
        prd: PRDDocument,
        tech_stack: list[TechnologyStack],
        architecture: SystemArchitecture,
    ) -> str:
        """TRD의 핵심 내용을 요약합니다."""
        tech_summary = ", ".join([
            f"{s.category}: {', '.join(s.technologies[:2])}"
            for s in tech_stack[:4]
        ])

        prompt = f"""{TRD_SUMMARY_PROMPT}

프로젝트: {prd.title}

프로젝트 배경:
{prd.overview.background[:300]}

기술 스택:
{tech_summary}

아키텍처 스타일: {architecture.architecture_style}

아키텍처 개요:
{architecture.overview}

주요 기능 수: {len(prd.functional_requirements)}개
비기능 요구사항 수: {len(prd.non_functional_requirements)}개
"""

        try:
            result = await self.claude_client.complete(
                system_prompt="기술 문서 작성 전문가로서 응답하세요.",
                user_prompt=prompt,
                temperature=0.4,
            )
            return result.strip()

        except Exception as e:
            logger.warning(f"[TRDGenerator] 기술 요약 생성 실패: {e}")
            return f"""본 TRD는 '{prd.title}' 프로젝트의 기술 요구사항을 정의합니다.

시스템은 {architecture.architecture_style} 아키텍처를 기반으로 설계되었으며, {tech_summary} 등의 기술 스택을 활용합니다.

총 {len(prd.functional_requirements)}개의 기능 요구사항과 {len(prd.non_functional_requirements)}개의 비기능 요구사항을 충족하기 위한 기술 명세를 포함합니다."""