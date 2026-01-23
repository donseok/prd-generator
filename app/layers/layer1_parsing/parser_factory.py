"""Parser factory for creating appropriate parsers based on input type."""

from typing import Dict, Type, Optional
from pathlib import Path

from app.models import InputType
from app.services.claude_client import ClaudeClient, get_claude_client
from .base_parser import BaseParser


class ParserFactory:
    """Factory for creating appropriate parsers based on input type."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Initialize factory with Claude client.

        Args:
            claude_client: ClaudeClient instance, or None to use default
        """
        self.claude_client = claude_client or get_claude_client()
        self._parsers: Dict[InputType, BaseParser] = {}
        self._parser_classes: Dict[InputType, Type[BaseParser]] = {}

        # Register parsers
        self._register_parsers()

    def _register_parsers(self):
        """Register all available parsers."""
        from .parsers.text_parser import TextParser
        from .parsers.email_parser import EmailParser
        from .parsers.excel_parser import ExcelParser
        from .parsers.ppt_parser import PPTParser
        from .parsers.image_parser import ImageParser
        from .parsers.chat_parser import ChatParser
        from .parsers.document_parser import DocumentParser

        self._parser_classes = {
            InputType.TEXT: TextParser,
            InputType.EMAIL: EmailParser,
            InputType.EXCEL: ExcelParser,
            InputType.CSV: ExcelParser,  # Reuse for CSV
            InputType.POWERPOINT: PPTParser,
            InputType.IMAGE: ImageParser,
            InputType.CHAT: ChatParser,
            InputType.DOCUMENT: DocumentParser,
        }

    def get_parser(self, input_type: InputType) -> BaseParser:
        """
        Get or create a parser instance for the given input type.

        Args:
            input_type: The type of input to parse

        Returns:
            Parser instance for the input type

        Raises:
            ValueError: If no parser is available for the type
        """
        if input_type not in self._parsers:
            parser_class = self._parser_classes.get(input_type)
            if not parser_class:
                raise ValueError(f"No parser available for type: {input_type}")
            self._parsers[input_type] = parser_class(self.claude_client)

        return self._parsers[input_type]

    def detect_type(self, filename: str, content_type: str = None) -> InputType:
        """
        Auto-detect input type from filename and optional content type.

        Args:
            filename: Name of the file
            content_type: Optional MIME content type

        Returns:
            Detected InputType
        """
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        extension_map = {
            # Text
            "txt": InputType.TEXT,
            "md": InputType.TEXT,
            "markdown": InputType.TEXT,
            # Email
            "eml": InputType.EMAIL,
            "msg": InputType.EMAIL,
            # Excel/CSV
            "xlsx": InputType.EXCEL,
            "xls": InputType.EXCEL,
            "csv": InputType.CSV,
            # PowerPoint
            "pptx": InputType.POWERPOINT,
            "ppt": InputType.POWERPOINT,
            # Image
            "png": InputType.IMAGE,
            "jpg": InputType.IMAGE,
            "jpeg": InputType.IMAGE,
            "gif": InputType.IMAGE,
            "bmp": InputType.IMAGE,
            "webp": InputType.IMAGE,
            # Document
            "pdf": InputType.DOCUMENT,
            "docx": InputType.DOCUMENT,
            "doc": InputType.DOCUMENT,
            # Chat (common export formats)
            "json": InputType.CHAT,  # Many chat exports are JSON
        }

        # Check content type hints
        if content_type:
            content_type_map = {
                "text/plain": InputType.TEXT,
                "message/rfc822": InputType.EMAIL,
                "application/vnd.ms-excel": InputType.EXCEL,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": InputType.EXCEL,
                "text/csv": InputType.CSV,
                "application/vnd.ms-powerpoint": InputType.POWERPOINT,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": InputType.POWERPOINT,
                "image/": InputType.IMAGE,
                "application/pdf": InputType.DOCUMENT,
            }
            for mime, itype in content_type_map.items():
                if content_type.startswith(mime):
                    return itype

        return extension_map.get(ext, InputType.TEXT)

    async def parse_file(
        self,
        file_path: Path,
        input_type: Optional[InputType] = None
    ):
        """
        Parse a file, auto-detecting type if not specified.

        Args:
            file_path: Path to the file
            input_type: Optional explicit input type

        Returns:
            ParsedContent from the appropriate parser
        """
        if input_type is None:
            input_type = self.detect_type(file_path.name)

        parser = self.get_parser(input_type)
        return await parser.parse(file_path)

    async def parse_bytes(
        self,
        content: bytes,
        filename: str,
        input_type: Optional[InputType] = None
    ):
        """
        Parse from bytes content.

        Args:
            content: File content as bytes
            filename: Original filename
            input_type: Optional explicit input type

        Returns:
            ParsedContent from the appropriate parser
        """
        if input_type is None:
            input_type = self.detect_type(filename)

        parser = self.get_parser(input_type)
        return await parser.parse_bytes(content, filename)
