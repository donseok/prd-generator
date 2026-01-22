"""Requirement data models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Structured source reference for traceability."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    section: Optional[str] = Field(default=None, description="Section name where found")
    line_start: Optional[int] = Field(default=None, description="Starting line number")
    line_end: Optional[int] = Field(default=None, description="Ending line number")
    excerpt: Optional[str] = Field(default=None, description="Original text excerpt (max 200 chars)")

    def to_display_string(self) -> str:
        """Convert to human-readable display string."""
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
    """Requirement classification types."""

    FUNCTIONAL = "FR"  # Functional Requirement
    NON_FUNCTIONAL = "NFR"  # Non-Functional Requirement
    CONSTRAINT = "CONSTRAINT"  # Constraint


class Priority(str, Enum):
    """Requirement priority levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class NormalizedRequirement(BaseModel):
    """A normalized requirement extracted from input."""

    id: str = Field(..., description="Requirement ID (e.g., REQ-001)")
    type: RequirementType
    title: str = Field(..., description="Short requirement title")
    description: str = Field(..., description="Detailed description")
    user_story: Optional[str] = Field(
        default=None,
        description="User story format: As a [user], I want [goal], so that [benefit]",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="List of acceptance criteria"
    )
    priority: Priority = Field(default=Priority.MEDIUM)
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0 ~ 1.0)"
    )
    confidence_reason: str = Field(
        default="", description="Reason for the confidence score"
    )
    source_reference: str = Field(
        default="", description="Reference to original source location (legacy)"
    )
    source_info: Optional[SourceReference] = Field(
        default=None, description="Structured source reference for detailed traceability"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Assumptions made during extraction"
    )
    missing_info: list[str] = Field(
        default_factory=list, description="Information that is missing or unclear"
    )
    related_requirements: list[str] = Field(
        default_factory=list, description="IDs of related requirements"
    )


class ValidationResult(BaseModel):
    """Result of requirement validation."""

    requirement_id: str
    is_valid: bool
    completeness_score: float = Field(ge=0.0, le=1.0)
    consistency_issues: list[str] = Field(default_factory=list)
    traceability_score: float = Field(ge=0.0, le=1.0)
    needs_pm_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
