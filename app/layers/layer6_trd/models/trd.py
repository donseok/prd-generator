"""TRD (Technical Requirements Document) models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TRDContext(BaseModel):
    """TRD 생성 컨텍스트."""
    target_environment: str = Field("cloud", description="배포 환경 (cloud, on-premise, hybrid)")
    preferred_stack: Optional[list[str]] = Field(None, description="선호 기술 스택")
    scalability_requirement: str = Field("medium", description="확장성 요구수준 (low, medium, high)")
    security_level: str = Field("standard", description="보안 수준 (basic, standard, high)")
    integration_systems: list[str] = Field(default_factory=list, description="연동 대상 시스템")
    additional_constraints: list[str] = Field(default_factory=list, description="추가 제약사항")


class TRDMetadata(BaseModel):
    """TRD 메타데이터."""
    version: str = "1.0"
    status: str = "DRAFT"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    source_prd_id: str = Field(..., description="원본 PRD ID")
    source_prd_title: str = Field(..., description="원본 PRD 제목")


class TechnologyStack(BaseModel):
    """기술 스택 정의."""
    category: str = Field(..., description="카테고리 (Frontend, Backend, Database, Infrastructure 등)")
    technologies: list[str] = Field(default_factory=list, description="기술 목록")
    rationale: str = Field("", description="선정 이유")


class SystemComponent(BaseModel):
    """시스템 컴포넌트."""
    name: str = Field(..., description="컴포넌트명")
    type: str = Field(..., description="타입 (service, module, library 등)")
    description: str = Field("", description="설명")
    responsibilities: list[str] = Field(default_factory=list, description="책임")
    dependencies: list[str] = Field(default_factory=list, description="의존성")
    interfaces: list[str] = Field(default_factory=list, description="인터페이스")


class ArchitectureLayer(BaseModel):
    """아키텍처 레이어."""
    name: str = Field(..., description="레이어명")
    description: str = Field("", description="레이어 설명")
    components: list[SystemComponent] = Field(default_factory=list, description="컴포넌트 목록")


class SystemArchitecture(BaseModel):
    """시스템 아키텍처."""
    overview: str = Field("", description="아키텍처 개요")
    architecture_style: str = Field("", description="아키텍처 스타일 (Microservices, Monolithic, Layered 등)")
    layers: list[ArchitectureLayer] = Field(default_factory=list, description="아키텍처 레이어")
    data_flow: str = Field("", description="데이터 흐름 설명")
    deployment_diagram: str = Field("", description="배포 다이어그램 설명")


class DatabaseEntity(BaseModel):
    """데이터베이스 엔티티."""
    name: str = Field(..., description="엔티티명")
    description: str = Field("", description="설명")
    attributes: list[str] = Field(default_factory=list, description="속성 목록")
    primary_key: str = Field("", description="기본 키")
    relationships: list[str] = Field(default_factory=list, description="관계")


class DatabaseDesign(BaseModel):
    """데이터베이스 설계."""
    database_type: str = Field("", description="데이터베이스 유형 (RDBMS, NoSQL, etc.)")
    recommended_engine: str = Field("", description="권장 엔진")
    entities: list[DatabaseEntity] = Field(default_factory=list, description="엔티티 목록")
    indexing_strategy: str = Field("", description="인덱싱 전략")
    partitioning_strategy: str = Field("", description="파티셔닝 전략")


class HTTPMethod(str, Enum):
    """HTTP 메서드."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class APIEndpoint(BaseModel):
    """API 엔드포인트."""
    path: str = Field(..., description="API 경로")
    method: HTTPMethod = Field(..., description="HTTP 메서드")
    description: str = Field("", description="설명")
    request_body: Optional[str] = Field(None, description="요청 바디 스키마")
    response_body: Optional[str] = Field(None, description="응답 바디 스키마")
    authentication: bool = Field(True, description="인증 필요 여부")
    related_requirement_id: Optional[str] = Field(None, description="관련 요구사항 ID")


class APISpecification(BaseModel):
    """API 명세."""
    base_url: str = Field("/api/v1", description="기본 URL")
    authentication_method: str = Field("JWT", description="인증 방식")
    endpoints: list[APIEndpoint] = Field(default_factory=list, description="엔드포인트 목록")
    common_headers: dict[str, str] = Field(default_factory=dict, description="공통 헤더")
    error_handling: str = Field("", description="에러 처리 방식")


class SecurityRequirement(BaseModel):
    """보안 요구사항."""
    category: str = Field(..., description="카테고리 (Authentication, Authorization, Data Protection 등)")
    requirement: str = Field(..., description="요구사항 내용")
    implementation: str = Field("", description="구현 방안")
    priority: str = Field("HIGH", description="우선순위")


class PerformanceRequirement(BaseModel):
    """성능 요구사항."""
    metric: str = Field(..., description="성능 지표")
    target_value: str = Field(..., description="목표 값")
    measurement_method: str = Field("", description="측정 방법")
    related_component: Optional[str] = Field(None, description="관련 컴포넌트")


class InfrastructureRequirement(BaseModel):
    """인프라 요구사항."""
    category: str = Field(..., description="카테고리 (Compute, Storage, Network, etc.)")
    specification: str = Field(..., description="사양")
    quantity: Optional[str] = Field(None, description="수량")
    purpose: str = Field("", description="용도")
    estimated_cost: Optional[str] = Field(None, description="예상 비용")


class RiskLevel(str, Enum):
    """리스크 수준."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TechnicalRisk(BaseModel):
    """기술 리스크."""
    description: str = Field(..., description="리스크 설명")
    level: RiskLevel = Field(RiskLevel.MEDIUM, description="위험도")
    impact: str = Field("", description="영향")
    mitigation: str = Field("", description="대응방안")
    contingency: str = Field("", description="비상 계획")


class TRDDocument(BaseModel):
    """TRD (Technical Requirements Document) 문서."""

    # 기본 정보
    id: str = Field(..., description="TRD ID")
    title: str = Field(..., description="TRD 제목")

    # TRD 섹션
    executive_summary: str = Field("", description="기술 요약")
    technology_stack: list[TechnologyStack] = Field(default_factory=list, description="기술 스택")
    system_architecture: SystemArchitecture = Field(default_factory=SystemArchitecture, description="시스템 아키텍처")
    database_design: DatabaseDesign = Field(default_factory=DatabaseDesign, description="데이터베이스 설계")
    api_specification: APISpecification = Field(default_factory=APISpecification, description="API 명세")
    security_requirements: list[SecurityRequirement] = Field(default_factory=list, description="보안 요구사항")
    performance_requirements: list[PerformanceRequirement] = Field(default_factory=list, description="성능 요구사항")
    infrastructure_requirements: list[InfrastructureRequirement] = Field(default_factory=list, description="인프라 요구사항")
    technical_risks: list[TechnicalRisk] = Field(default_factory=list, description="기술 리스크")

    # 메타데이터
    metadata: TRDMetadata

    def to_markdown(self) -> str:
        """마크다운 형식의 TRD 생성."""
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

        # 1. 기술 요약
        if self.executive_summary:
            lines.append("## 1. 기술 요약")
            lines.append("")
            lines.append(self.executive_summary)
            lines.append("")

        # 2. 기술 스택
        if self.technology_stack:
            lines.append("## 2. 기술 스택")
            lines.append("")
            for stack in self.technology_stack:
                lines.append(f"### {stack.category}")
                lines.append("")
                for tech in stack.technologies:
                    lines.append(f"- {tech}")
                if stack.rationale:
                    lines.append(f"\n**선정 이유**: {stack.rationale}")
                lines.append("")

        # 3. 시스템 아키텍처
        lines.append("## 3. 시스템 아키텍처")
        lines.append("")

        if self.system_architecture.overview:
            lines.append("### 3.1 아키텍처 개요")
            lines.append("")
            lines.append(self.system_architecture.overview)
            lines.append("")

        if self.system_architecture.architecture_style:
            lines.append(f"**아키텍처 스타일**: {self.system_architecture.architecture_style}")
            lines.append("")

        if self.system_architecture.layers:
            lines.append("### 3.2 아키텍처 레이어")
            lines.append("")
            for layer in self.system_architecture.layers:
                lines.append(f"#### {layer.name}")
                if layer.description:
                    lines.append(layer.description)
                lines.append("")
                if layer.components:
                    lines.append("| 컴포넌트 | 타입 | 설명 |")
                    lines.append("|----------|------|------|")
                    for comp in layer.components:
                        lines.append(f"| {comp.name} | {comp.type} | {comp.description} |")
                    lines.append("")

        if self.system_architecture.data_flow:
            lines.append("### 3.3 데이터 흐름")
            lines.append("")
            lines.append(self.system_architecture.data_flow)
            lines.append("")

        # 4. 데이터베이스 설계
        if self.database_design.entities:
            lines.append("## 4. 데이터베이스 설계")
            lines.append("")

            if self.database_design.database_type:
                lines.append(f"**데이터베이스 유형**: {self.database_design.database_type}")
            if self.database_design.recommended_engine:
                lines.append(f"**권장 엔진**: {self.database_design.recommended_engine}")
            lines.append("")

            lines.append("### 4.1 엔티티 정의")
            lines.append("")
            for entity in self.database_design.entities:
                lines.append(f"#### {entity.name}")
                if entity.description:
                    lines.append(entity.description)
                lines.append("")
                if entity.attributes:
                    lines.append("**속성**:")
                    for attr in entity.attributes:
                        lines.append(f"- {attr}")
                if entity.primary_key:
                    lines.append(f"\n**기본 키**: {entity.primary_key}")
                if entity.relationships:
                    lines.append("\n**관계**:")
                    for rel in entity.relationships:
                        lines.append(f"- {rel}")
                lines.append("")

            if self.database_design.indexing_strategy:
                lines.append("### 4.2 인덱싱 전략")
                lines.append("")
                lines.append(self.database_design.indexing_strategy)
                lines.append("")

        # 5. API 명세
        if self.api_specification.endpoints:
            lines.append("## 5. API 명세")
            lines.append("")
            lines.append(f"**Base URL**: `{self.api_specification.base_url}`")
            lines.append(f"**인증 방식**: {self.api_specification.authentication_method}")
            lines.append("")

            lines.append("### 5.1 엔드포인트 목록")
            lines.append("")
            lines.append("| 메서드 | 경로 | 설명 | 인증 |")
            lines.append("|--------|------|------|------|")
            for endpoint in self.api_specification.endpoints:
                auth_str = "O" if endpoint.authentication else "X"
                lines.append(f"| {endpoint.method.value} | `{endpoint.path}` | {endpoint.description} | {auth_str} |")
            lines.append("")

            if self.api_specification.error_handling:
                lines.append("### 5.2 에러 처리")
                lines.append("")
                lines.append(self.api_specification.error_handling)
                lines.append("")

        # 6. 보안 요구사항
        if self.security_requirements:
            lines.append("## 6. 보안 요구사항")
            lines.append("")
            lines.append("| 카테고리 | 요구사항 | 구현 방안 | 우선순위 |")
            lines.append("|----------|----------|----------|----------|")
            for sec in self.security_requirements:
                lines.append(f"| {sec.category} | {sec.requirement} | {sec.implementation} | {sec.priority} |")
            lines.append("")

        # 7. 성능 요구사항
        if self.performance_requirements:
            lines.append("## 7. 성능 요구사항")
            lines.append("")
            lines.append("| 성능 지표 | 목표 값 | 측정 방법 |")
            lines.append("|----------|---------|----------|")
            for perf in self.performance_requirements:
                lines.append(f"| {perf.metric} | {perf.target_value} | {perf.measurement_method} |")
            lines.append("")

        # 8. 인프라 요구사항
        if self.infrastructure_requirements:
            lines.append("## 8. 인프라 요구사항")
            lines.append("")
            lines.append("| 카테고리 | 사양 | 수량 | 용도 |")
            lines.append("|----------|------|------|------|")
            for infra in self.infrastructure_requirements:
                qty = infra.quantity or "-"
                lines.append(f"| {infra.category} | {infra.specification} | {qty} | {infra.purpose} |")
            lines.append("")

        # 9. 기술 리스크
        if self.technical_risks:
            lines.append("## 9. 기술 리스크")
            lines.append("")
            lines.append("| 리스크 | 위험도 | 영향 | 대응방안 |")
            lines.append("|--------|--------|------|----------|")
            for risk in self.technical_risks:
                level_emoji = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}.get(risk.level.value, "")
                lines.append(f"| {risk.description} | {level_emoji} | {risk.impact} | {risk.mitigation} |")
            lines.append("")

        # 푸터
        lines.append("---")
        lines.append("")
        lines.append(f"*본 TRD는 '{self.metadata.source_prd_title}' PRD를 기반으로 자동 생성되었습니다.*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """JSON 형식으로 변환."""
        return self.model_dump_json(indent=2)
