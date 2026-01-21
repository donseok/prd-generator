"""Base parser interface for all input type parsers."""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pathlib import Path

from app.models import InputType, ParsedContent, InputMetadata


class BaseParser(ABC):
    """Abstract base class for all input parsers."""

    def __init__(self, claude_client=None):
        """
        Initialize parser with optional Claude client.

        Args:
            claude_client: ClaudeClient instance for AI-powered parsing
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
