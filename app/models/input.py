"""Input document data models."""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Supported input types."""

    TEXT = "text"
    EMAIL = "email"
    EXCEL = "excel"
    CSV = "csv"
    POWERPOINT = "ppt"
    IMAGE = "image"
    CHAT = "chat"
    DOCUMENT = "document"  # Word, PDF 등 기존 문서
    # AUDIO = "audio"  # 추후 구현 예정


class InputMetadata(BaseModel):
    """Metadata extracted from input document."""

    filename: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    subject: Optional[str] = None  # For emails
    sheet_names: Optional[list[str]] = None  # For Excel
    slide_count: Optional[int] = None  # For PowerPoint
    page_count: Optional[int] = None  # For PDF/Word
    image_dimensions: Optional[dict] = None  # For images: {"width": int, "height": int}
    participants: Optional[list[str]] = None  # For chat/messenger


class ParsedContent(BaseModel):
    """Parsed content from a document."""

    raw_text: str = Field(..., description="Extracted raw text content")
    structured_data: Optional[dict] = Field(
        default=None, description="Structured data (for Excel/CSV)"
    )
    metadata: InputMetadata = Field(default_factory=InputMetadata)
    sections: list[dict] = Field(
        default_factory=list, description="Identified sections/headers"
    )


class InputDocument(BaseModel):
    """Input document for PRD generation."""

    id: str = Field(..., description="Unique document identifier")
    input_type: InputType
    content: ParsedContent
    source_path: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.now)
