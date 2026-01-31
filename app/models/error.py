"""에러 응답 모델."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """구조화된 API 에러 응답 모델."""

    error_code: str = Field(description="에러 코드 (예: ERR_INPUT_001)")
    message: str = Field(description="에러 메시지")
    details: Optional[Any] = Field(default=None, description="추가 에러 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시각")
