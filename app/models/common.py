"""Common models and enums used across multiple layers.

This module consolidates shared types to avoid code duplication
and ensure consistency across proposal, TRD, and WBS generators.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """
    리스크 수준 정의.

    프로젝트 리스크를 3단계로 분류:
    - HIGH: 즉각적인 대응 필요, 프로젝트 일정/비용에 심각한 영향
    - MEDIUM: 모니터링 필요, 적절한 대응 시 관리 가능
    - LOW: 일반적인 프로젝트 리스크, 정기 점검으로 관리
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BaseDocumentMetadata(BaseModel):
    """
    문서 메타데이터 베이스 클래스.

    모든 생성 문서(Proposal, TRD, WBS)에서 공통으로 사용되는
    메타데이터 필드를 정의합니다.

    Attributes:
        version: 문서 버전 (semantic versioning)
        status: 문서 상태 (DRAFT, REVIEW, APPROVED, FINAL)
        created_at: 문서 생성 시간
        updated_at: 마지막 수정 시간
        source_prd_id: 원본 PRD 문서 ID
        source_prd_title: 원본 PRD 문서 제목
    """
    version: str = Field(default="1.0", description="문서 버전")
    status: str = Field(default="DRAFT", description="문서 상태")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: Optional[datetime] = Field(default=None, description="수정 시간")
    source_prd_id: str = Field(..., description="원본 PRD ID")
    source_prd_title: str = Field(..., description="원본 PRD 제목")


class BaseRisk(BaseModel):
    """
    리스크 베이스 클래스.

    프로젝트/기술 리스크를 표현하는 공통 속성을 정의합니다.

    Attributes:
        description: 리스크 설명
        level: 위험도 수준
        impact: 영향 범위 및 정도
        mitigation: 대응/완화 방안
    """
    description: str = Field(..., description="리스크 설명")
    level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="위험도")
    impact: str = Field(default="", description="영향")
    mitigation: str = Field(default="", description="대응방안")
