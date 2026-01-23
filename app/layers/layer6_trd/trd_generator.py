"""TRD generator - converts PRD to Technical Requirements Document.

Layer 6: 기술 요구사항 문서 생성기
PRDDocument를 기반으로 TRD(Technical Requirements Document)를 생성합니다.

처리 순서:
1. 기술 스택 추천 (Claude 호출) - 요구사항 기반 기술 선정
2. 시스템 아키텍처 설계 (Claude 호출) - 레이어별 컴포넌트 정의
3. 데이터베이스 설계 (Claude 호출) - 엔티티 및 관계 정의
4. API 명세 생성 (Claude 호출) - 엔드포인트 및 스키마 정의
5. 보안 요구사항 추출 (NFR 기반 + 기본 요구사항)
6. 성능 요구사항 추출 (NFR 기반 + 기본 요구사항)
7. 인프라 요구사항 생성 (환경별 기본 템플릿)
8. 기술 리스크 평가 (연동/기술/성능/보안 기반)
9. 기술 요약 생성 (Claude 호출, 마지막에 생성)

병렬화 가능 섹션:
- 1, 2, 3, 4번은 의존성이 없어 병렬 실행 가능
- 5, 6, 7, 8번은 로컬 처리로 빠름
- 9번은 1, 2번 결과가 필요하여 마지막 순차 실행
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
    PRD를 기반으로 TRD(Technical Requirements Document) 생성.

    BaseGenerator를 상속하여 일관된 생성 흐름과
    공통 유틸리티 메서드를 활용합니다.
    """

    _id_prefix = "TRD"
    _generator_name = "TRDGenerator"

    async def _do_generate(
        self,
        prd: PRDDocument,
        context: TRDContext,
    ) -> TRDDocument:
        """
        실제 TRD 생성 로직 (병렬 처리 최적화).

        병렬화 전략:
        - Phase 1: 독립 Claude 호출 병렬 (tech_stack, database, api_spec)
        - Phase 2: 의존성 있는 Claude 호출 병렬 (architecture, security)
        - Phase 3: 로컬 처리 (performance, infrastructure, risks)
        - Phase 4: 최종 요약 (순차, 이전 결과 의존)

        예상 효과: 50-60% 시간 단축

        Args:
            prd: 원본 PRD 문서
            context: TRD 생성 컨텍스트

        Returns:
            TRDDocument: 생성된 TRD
        """
        import asyncio

        # TRD ID 생성 (베이스 클래스 메서드 사용)
        trd_id = self._generate_id()

        # 제목 설정
        title = f"{prd.title} - 기술 요구사항 문서 (TRD)"

        # ========== Phase 1: 독립 Claude 호출 병렬 ==========
        # tech_stack, database_design, api_specification은 서로 독립적
        logger.info("[TRDGenerator] Phase 1: 독립 Claude 호출 병렬 시작")

        tech_task = self._generate_technology_stack(prd, context)
        db_task = self._generate_database_design(prd)
        api_task = self._generate_api_specification(prd)

        technology_stack, database_design, api_specification = await asyncio.gather(
            tech_task,
            db_task,
            api_task
        )

        logger.info("[TRDGenerator] 기술 스택 추천 완료")
        logger.info("[TRDGenerator] 데이터베이스 설계 완료")
        logger.info("[TRDGenerator] API 명세 생성 완료")

        # ========== Phase 2: 의존성 있는 Claude 호출 병렬 ==========
        # system_architecture는 technology_stack 필요
        # security_requirements는 context만 필요
        logger.info("[TRDGenerator] Phase 2: 의존 Claude 호출 병렬 시작")

        arch_task = self._generate_system_architecture(prd, technology_stack)
        security_task = self._extract_security_requirements(prd, context)

        system_architecture, security_requirements = await asyncio.gather(
            arch_task,
            security_task
        )

        logger.info("[TRDGenerator] 시스템 아키텍처 설계 완료")
        logger.info("[TRDGenerator] 보안 요구사항 추출 완료")

        # ========== Phase 3: 로컬 처리 ==========
        # 6. 성능 요구사항 추출
        performance_requirements = self._extract_performance_requirements(prd)
        logger.info("[TRDGenerator] 성능 요구사항 추출 완료")

        # 7. 인프라 요구사항 생성 (technology_stack 필요하지만 로컬 처리)
        infrastructure_requirements = await self._generate_infrastructure(prd, technology_stack, context)
        logger.info("[TRDGenerator] 인프라 요구사항 생성 완료")

        # 8. 기술 리스크 평가 (technology_stack 필요)
        technical_risks = self._assess_technical_risks(prd, technology_stack)
        logger.info("[TRDGenerator] 기술 리스크 평가 완료")

        # ========== Phase 4: 최종 요약 (순차) ==========
        # technology_stack과 system_architecture 결과가 필요
        executive_summary = await self._generate_executive_summary(
            prd, technology_stack, system_architecture
        )
        logger.info("[TRDGenerator] 기술 요약 생성 완료")

        # 메타데이터
        metadata = TRDMetadata(
            source_prd_id=prd.id,
            source_prd_title=prd.title,
        )

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
        """기술 스택 추천 (Claude)."""
        # 요구사항 요약
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
            # 기본 스택 반환
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
        """시스템 아키텍처 설계 (Claude)."""
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
        """데이터베이스 설계 (Claude)."""
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
        """API 명세 생성 (Claude)."""
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
        """보안 요구사항 추출."""
        # NFR에서 보안 관련 항목 추출
        security_reqs = []

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
        """성능 요구사항 추출."""
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
        """인프라 요구사항 생성."""
        infra_reqs = []

        # 기본 인프라 구성
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
        else:  # on-premise or hybrid
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

        # 확장성 요구에 따른 조정
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
        """기술 리스크 평가."""
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

        # 2. 기술 스택 성숙도 리스크
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

        # 3. 성능 관련 리스크
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

        # 4. 보안 리스크
        risks.append(TechnicalRisk(
            description="보안 취약점 발생 가능성",
            level=RiskLevel.HIGH,
            impact="데이터 유출 및 서비스 중단",
            mitigation="보안 코드 리뷰 및 취약점 스캔 정기 수행",
            contingency="보안 패치 즉시 적용 체계 구축",
        ))

        # 기본 리스크가 없으면 추가
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
        """기술 요약 생성 (Claude)."""
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
