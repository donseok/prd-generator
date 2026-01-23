"""Base parser interface for all input type parsers.

모든 입력 타입 파서가 상속하는 추상 베이스 클래스와
공통 기능을 제공하는 Mixin들을 정의합니다.

Mixin 사용:
- ClaudeAnalysisMixin: Claude 기반 문서 분석
- MetadataExtractionMixin: 파일 메타데이터 추출
- StructureDetectionMixin: 문서 구조 감지
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pathlib import Path

from app.models import InputType, ParsedContent, InputMetadata
from .mixins import ClaudeAnalysisMixin, MetadataExtractionMixin, StructureDetectionMixin


class BaseParser(ABC, ClaudeAnalysisMixin, MetadataExtractionMixin, StructureDetectionMixin):
    """
    모든 입력 파서의 추상 베이스 클래스.

    Mixin 클래스들을 상속하여 다음 기능을 제공:
    - Claude를 사용한 문서 분석 (ClaudeAnalysisMixin)
    - 파일 메타데이터 추출 (MetadataExtractionMixin)
    - 문서 구조 감지 (StructureDetectionMixin)

    서브클래스에서 구현해야 하는 메서드:
    - supported_types: 지원하는 입력 타입 목록
    - supported_extensions: 지원하는 파일 확장자 목록
    - parse: 파일 파싱 로직
    """

    def __init__(self, claude_client=None):
        """
        파서 초기화.

        Args:
            claude_client: Claude API 호출용 클라이언트.
                          AI 기반 파싱/분석에 사용됩니다.
        """
        self.claude_client = claude_client

    @property
    @abstractmethod
    def supported_types(self) -> list[InputType]:
        """Return list of supported input types."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions (with dot)."""
        pass

    @abstractmethod
    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """
        Parse the input file and return structured content.

        Args:
            file_path: Path to the file to parse
            metadata: Optional additional metadata

        Returns:
            ParsedContent with raw_text, structured_data, metadata, sections
        """
        pass

    async def parse_bytes(
        self,
        content: bytes,
        filename: str,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """
        Parse from bytes content.

        Default implementation writes to temp file and calls parse().
        Override for direct byte parsing.
        """
        import tempfile
        import os

        ext = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            return await self.parse(tmp_path, metadata)
        finally:
            os.unlink(tmp_path)

    async def extract_metadata(
        self,
        file_path: Path,
    ) -> InputMetadata:
        """
        Extract metadata from file.

        Override in subclasses for format-specific metadata extraction.
        """
        import os
        from datetime import datetime

        stat = file_path.stat()
        return InputMetadata(
            filename=file_path.name,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    async def detect_structure(self, content: str) -> dict:
        """
        Detect document structure (headers, sections, lists).

        Override for type-specific structure detection.
        """
        lines = content.split("\n")
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Simple heuristic: lines that look like headers
            if stripped and len(stripped) < 100:
                # Check if it looks like a header
                if (stripped.endswith(":") or
                    stripped.isupper() or
                    stripped.startswith("#") or
                    (i > 0 and not lines[i-1].strip())):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "title": stripped.rstrip(":").strip("#").strip(),
                        "start_line": i,
                        "content": []
                    }
                elif current_section:
                    current_section["content"].append(line)

        if current_section:
            sections.append(current_section)

        return {
            "sections": sections,
            "line_count": len(lines),
            "char_count": len(content),
        }

    def can_parse(self, filename: str) -> bool:
        """Check if this parser can handle the given file."""
        ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
        return ext in self.supported_extensions
