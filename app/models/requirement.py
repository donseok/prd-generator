"""
요구사항(Requirement) 데이터 모델입니다.
PRD의 핵심이 되는 개별 요구사항을 정의합니다.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """
    요구사항의 출처 정보입니다.
    어떤 파일의 어디서(섹션, 줄 번호) 나왔는지 추적할 수 있게 해줍니다.
    """

    document_id: str = Field(..., description="문서 ID")
    filename: str = Field(..., description="파일명")
    section: Optional[str] = Field(default=None, description="섹션 이름")
    line_start: Optional[int] = Field(default=None, description="시작 줄 번호")
    line_end: Optional[int] = Field(default=None, description="끝 줄 번호")
    excerpt: Optional[str] = Field(default=None, description="원문 발췌 (최대 200자)")

    def to_display_string(self) -> str:
        """사람이 읽기 좋은 형태로 변환합니다."""
        parts = [self.filename]
        if self.section:
            parts.append(f"[{self.section}]")
        if self.line_start:
            if self.line_end and self.line_end != self.line_start:
                parts.append(f"(L{self.line_start}-{self.line_end})")
            else:
                parts.append(f"(L{self.line_start})")
        return " ".join(parts)


class RequirementType(str, Enum):
    """요구사항 종류입니다."""

    FUNCTIONAL = "FR"  # 기능 요구사항 (시스템이 해야 할 일)
    NON_FUNCTIONAL = "NFR"  # 비기능 요구사항 (성능, 보안 등 품질 속성)
    CONSTRAINT = "CONSTRAINT"  # 제약사항 (반드시 지켜야 할 규칙)


class Priority(str, Enum):
    """우선순위입니다."""

    HIGH = "HIGH"    # 높음 (필수)
    MEDIUM = "MEDIUM" # 중간 (중요)
    LOW = "LOW"      # 낮음 (선택)


class NormalizedRequirement(BaseModel):
    """
    정규화된 요구사항입니다.
    다양한 형태의 입력에서 추출하여 표준화된 형태로 정리한 것입니다.
    """

    id: str = Field(..., description="요구사항 ID (예: REQ-001)")
    type: RequirementType
    title: str = Field(..., description="요구사항 제목 (요약)")
    description: str = Field(..., description="상세 설명")
    user_story: Optional[str] = Field(
        default=None,
        description="사용자 스토리 형식: [사용자]로서 [목표]를 위해 [기능]을 원한다",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="인수 기준 (완료 조건)"
    )
    priority: Priority = Field(default=Priority.MEDIUM)
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="AI의 확신도 (0.0 ~ 1.0)"
    )
    confidence_reason: str = Field(
        default="", description="확신도에 대한 이유 설명"
    )
    source_reference: str = Field(
        default="", description="출처 위치 (문자열 형태, 구버전 호환용)"
    )
    source_info: Optional[SourceReference] = Field(
        default=None, description="구조화된 출처 정보"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="이 요구사항을 도출하며 가정한 내용들"
    )
    missing_info: list[str] = Field(
        default_factory=list, description="부족하거나 불명확한 정보"
    )
    related_requirements: list[str] = Field(
        default_factory=list, description="관련된 다른 요구사항들의 ID"
    )


class ValidationResult(BaseModel):
    """
    요구사항 검증 결과입니다.
    """

    requirement_id: str
    is_valid: bool # 유효성 여부
    completeness_score: float = Field(ge=0.0, le=1.0) # 완전성 점수
    consistency_issues: list[str] = Field(default_factory=list) # 일관성 위배 사항
    traceability_score: float = Field(ge=0.0, le=1.0) # 추적 가능성 점수
    needs_pm_review: bool = False # 기획자 검토 필요 여부
    review_reasons: list[str] = Field(default_factory=list) # 검토 필요한 이유