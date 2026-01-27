"""
공통 데이터 모델 모듈입니다.
PRD, TRD, WBS 등 여러 문서 생성기에서 공통으로 사용되는 데이터 구조를 정의합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """
    리스크(위험) 수준을 정의하는 열거형 클래스입니다.
    
    분류:
    - HIGH: 매우 위험. 즉시 조치 필요. 프로젝트 실패 가능성 있음.
    - MEDIUM: 중간 위험. 지속적인 관찰 필요.
    - LOW: 낮은 위험. 주기적인 점검으로 충분함.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BaseDocumentMetadata(BaseModel):
    """
    모든 문서(PRD, TRD, WBS 등)가 공통으로 가지는 기본 정보입니다.
    
    포함 정보:
    - 버전 (예: 1.0)
    - 상태 (초안, 검토중, 승인됨 등)
    - 생성일 및 수정일
    - 원본 PRD 정보 (추적성을 위함)
    """
    version: str = Field(default="1.0", description="문서 버전")
    status: str = Field(default="DRAFT", description="문서 상태")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: Optional[datetime] = Field(default=None, description="마지막 수정 시간")
    source_prd_id: str = Field(..., description="이 문서의 기반이 된 PRD ID")
    source_prd_title: str = Field(..., description="이 문서의 기반이 된 PRD 제목")


class BaseRisk(BaseModel):
    """
    리스크 정보를 표현하는 기본 클래스입니다.
    프로젝트나 기술적 위험요소를 기록할 때 사용합니다.
    """
    description: str = Field(..., description="무엇이 위험한지 설명")
    level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="위험한 정도")
    impact: str = Field(default="", description="발생했을 때 미치는 영향")
    mitigation: str = Field(default="", description="어떻게 해결하거나 완화할 것인지")