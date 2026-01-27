"""
입력 문서 관련 데이터 모델입니다.
사용자가 업로드하는 파일이나 텍스트 등의 형식을 정의합니다.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """지원하는 입력 파일의 종류입니다."""

    TEXT = "text"
    EMAIL = "email"
    EXCEL = "excel"
    CSV = "csv"
    POWERPOINT = "ppt"
    IMAGE = "image"
    CHAT = "chat"
    DOCUMENT = "document"  # Word, PDF 등
    # AUDIO = "audio"  # 추후 오디오 지원 예정


class InputMetadata(BaseModel):
    """
    입력 문서에서 추출한 부가 정보(메타데이터)입니다.
    파일 종류에 따라 다른 정보가 담길 수 있습니다.
    """

    filename: Optional[str] = None  # 파일명
    author: Optional[str] = None    # 작성자
    created_at: Optional[datetime] = None  # 생성일
    modified_at: Optional[datetime] = None # 수정일
    subject: Optional[str] = None  # 이메일 제목
    sheet_names: Optional[list[str]] = None  # 엑셀 시트 이름들
    slide_count: Optional[int] = None  # 파워포인트 슬라이드 수
    page_count: Optional[int] = None  # 문서 페이지 수
    image_dimensions: Optional[dict] = None  # 이미지 크기 (가로, 세로)
    participants: Optional[list[str]] = None  # 채팅 참여자 목록


class ParsedContent(BaseModel):
    """
    파일에서 읽어들인 실제 내용입니다.
    """

    raw_text: str = Field(..., description="파일에서 추출한 순수한 텍스트 내용")
    structured_data: Optional[dict] = Field(
        default=None, description="구조화된 데이터 (엑셀/CSV인 경우 사용)"
    )
    metadata: InputMetadata = Field(default_factory=InputMetadata)
    sections: list[dict] = Field(
        default_factory=list, description="문서의 목차나 섹션 정보"
    )


class InputDocument(BaseModel):
    """
    PRD 생성을 위해 입력된 하나의 문서 단위를 나타냅니다.
    """

    id: str = Field(..., description="문서 고유 ID")
    input_type: InputType  # 문서 종류
    content: ParsedContent # 문서 내용
    source_path: Optional[str] = None # 원본 파일 저장 경로
    uploaded_at: datetime = Field(default_factory=datetime.now) # 업로드 시간