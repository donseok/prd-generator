"""
PRD 생성 시스템 커스텀 예외 계층입니다.
각 레이어/서비스별 구조화된 에러 코드와 메시지를 제공합니다.
"""

from typing import Optional, Any


class PRDGeneratorError(Exception):
    """PRD 생성 시스템 기본 예외 클래스."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_UNKNOWN",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ParsingError(PRDGeneratorError):
    """Layer 1: 파싱 단계 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_PARSE_001", details=details)


class NormalizationError(PRDGeneratorError):
    """Layer 2: 정규화 단계 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_NORM_001", details=details)


class ValidationError(PRDGeneratorError):
    """Layer 3: 검증 단계 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_VALID_001", details=details)


class GenerationError(PRDGeneratorError):
    """Layer 4+: 문서 생성 단계 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_GEN_001", details=details)


class StorageError(PRDGeneratorError):
    """파일 저장소 관련 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_STORE_001", details=details)


class ClaudeClientError(PRDGeneratorError):
    """Claude AI 클라이언트 통신 에러."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_CLAUDE_001", details=details)


class InputValidationError(PRDGeneratorError):
    """입력 유효성 검증 에러 (400 응답)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, error_code="ERR_INPUT_001", details=details)
