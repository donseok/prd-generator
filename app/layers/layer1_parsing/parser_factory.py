"""
파서 팩토리(Parser Factory) 모듈입니다.
입력된 파일의 종류에 맞는 적절한 파서를 찾아서 생성해주는 역할을 합니다.
"""

from typing import Dict, Type, Optional
from pathlib import Path

from app.models import InputType
from app.services.claude_client import ClaudeClient, get_claude_client
from .base_parser import BaseParser


class ParserFactory:
    """
    적절한 파서를 생성하는 공장 클래스입니다.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        초기화 함수.
        사용할 파서들을 등록합니다.
        """
        self.claude_client = claude_client or get_claude_client()
        self._parsers: Dict[InputType, BaseParser] = {}
        self._parser_classes: Dict[InputType, Type[BaseParser]] = {}

        # 사용 가능한 파서 등록
        self._register_parsers()

    def _register_parsers(self):
        """모든 종류의 파서 클래스를 등록하는 내부 함수"""
        from .parsers.text_parser import TextParser
        from .parsers.email_parser import EmailParser
        from .parsers.excel_parser import ExcelParser
        from .parsers.ppt_parser import PPTParser
        from .parsers.image_parser import ImageParser
        from .parsers.chat_parser import ChatParser
        from .parsers.document_parser import DocumentParser

        self._parser_classes = {
            InputType.TEXT: TextParser, # 텍스트/마크다운
            InputType.EMAIL: EmailParser, # 이메일 (.eml)
            InputType.EXCEL: ExcelParser, # 엑셀 (.xlsx)
            InputType.CSV: ExcelParser,  # CSV도 엑셀 파서 사용
            InputType.POWERPOINT: PPTParser, # 파워포인트 (.pptx)
            InputType.IMAGE: ImageParser, # 이미지 (.png, .jpg)
            InputType.CHAT: ChatParser, # 채팅 로그
            InputType.DOCUMENT: DocumentParser, # 워드/PDF
        }

    def get_parser(self, input_type: InputType) -> BaseParser:
        """
        입력 타입에 맞는 파서 인스턴스를 반환합니다.
        이미 생성된 인스턴스가 있으면 재사용합니다 (Singleton 패턴 유사).
        """
        if input_type not in self._parsers:
            parser_class = self._parser_classes.get(input_type)
            if not parser_class:
                raise ValueError(f"지원하지 않는 입력 타입입니다: {input_type}")
            self._parsers[input_type] = parser_class(self.claude_client)

        return self._parsers[input_type]

    def detect_type(self, filename: str, content_type: str = None) -> InputType:
        """
        파일명(확장자)이나 컨텐츠 타입을 보고 입력 타입을 자동으로 추측합니다.
        """
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        extension_map = {
            # 텍스트
            "txt": InputType.TEXT,
            "md": InputType.TEXT,
            "markdown": InputType.TEXT,
            # 이메일
            "eml": InputType.EMAIL,
            "msg": InputType.EMAIL,
            # 엑셀/CSV
            "xlsx": InputType.EXCEL,
            "xls": InputType.EXCEL,
            "csv": InputType.CSV,
            # 파워포인트
            "pptx": InputType.POWERPOINT,
            "ppt": InputType.POWERPOINT,
            # 이미지
            "png": InputType.IMAGE,
            "jpg": InputType.IMAGE,
            "jpeg": InputType.IMAGE,
            "gif": InputType.IMAGE,
            "bmp": InputType.IMAGE,
            "webp": InputType.IMAGE,
            # 일반 문서
            "pdf": InputType.DOCUMENT,
            "docx": InputType.DOCUMENT,
            "doc": InputType.DOCUMENT,
            # 채팅 (보통 JSON으로 내보냄)
            "json": InputType.CHAT,
        }

        # 컨텐츠 타입(MIME Type) 힌트가 있으면 우선 확인
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
        파일을 파싱하는 편리한 함수입니다.
        타입을 지정하지 않으면 자동으로 알아내서 파싱합니다.
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
        바이트 데이터를 파싱하는 편리한 함수입니다.
        """
        if input_type is None:
            input_type = self.detect_type(filename)

        parser = self.get_parser(input_type)
        return await parser.parse_bytes(content, filename)