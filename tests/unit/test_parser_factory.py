"""ParserFactory unit tests.

ParserFactory is responsible for:
- Selecting the correct parser based on InputType
- Caching parser instances (singleton-like per type)
- Detecting InputType from filenames and MIME content types
"""

import pytest
from unittest.mock import AsyncMock

from app.models import InputType
from app.layers.layer1_parsing.parser_factory import ParserFactory
from app.layers.layer1_parsing.parsers.text_parser import TextParser
from app.layers.layer1_parsing.parsers.email_parser import EmailParser
from app.layers.layer1_parsing.parsers.excel_parser import ExcelParser
from app.layers.layer1_parsing.parsers.ppt_parser import PPTParser
from app.layers.layer1_parsing.parsers.image_parser import ImageParser
from app.layers.layer1_parsing.parsers.chat_parser import ChatParser
from app.layers.layer1_parsing.parsers.document_parser import DocumentParser


@pytest.fixture
def factory():
    """ParserFactory with a mock claude_client."""
    mock_client = AsyncMock()
    return ParserFactory(claude_client=mock_client)


# ---- get_parser returns correct parser type for each InputType ----

class TestGetParserReturnsCorrectType:
    def test_text_returns_text_parser(self, factory):
        parser = factory.get_parser(InputType.TEXT)
        assert isinstance(parser, TextParser)

    def test_email_returns_email_parser(self, factory):
        parser = factory.get_parser(InputType.EMAIL)
        assert isinstance(parser, EmailParser)

    def test_excel_returns_excel_parser(self, factory):
        parser = factory.get_parser(InputType.EXCEL)
        assert isinstance(parser, ExcelParser)

    def test_csv_returns_excel_parser(self, factory):
        # CSV reuses the ExcelParser
        parser = factory.get_parser(InputType.CSV)
        assert isinstance(parser, ExcelParser)

    def test_powerpoint_returns_ppt_parser(self, factory):
        parser = factory.get_parser(InputType.POWERPOINT)
        assert isinstance(parser, PPTParser)

    def test_image_returns_image_parser(self, factory):
        parser = factory.get_parser(InputType.IMAGE)
        assert isinstance(parser, ImageParser)

    def test_document_returns_document_parser(self, factory):
        parser = factory.get_parser(InputType.DOCUMENT)
        assert isinstance(parser, DocumentParser)

    def test_chat_returns_chat_parser(self, factory):
        parser = factory.get_parser(InputType.CHAT)
        assert isinstance(parser, ChatParser)


# ---- get_parser raises ValueError for unsupported type ----

class TestGetParserUnsupportedType:
    def test_raises_value_error_for_unknown_type(self, factory):
        """Passing an unregistered type should raise ValueError."""
        # Remove all registered parser classes to simulate an unsupported type
        factory._parser_classes.clear()
        with pytest.raises(ValueError, match="지원하지 않는 입력 타입"):
            factory.get_parser(InputType.TEXT)


# ---- get_parser returns cached instance on second call ----

class TestGetParserCaching:
    def test_returns_same_instance_on_second_call(self, factory):
        parser_first = factory.get_parser(InputType.TEXT)
        parser_second = factory.get_parser(InputType.TEXT)
        assert parser_first is parser_second

    def test_different_types_return_different_instances(self, factory):
        text_parser = factory.get_parser(InputType.TEXT)
        email_parser = factory.get_parser(InputType.EMAIL)
        assert text_parser is not email_parser


# ---- detect_type correctly maps file extensions ----

class TestDetectTypeByExtension:
    @pytest.mark.parametrize("filename,expected", [
        ("readme.txt", InputType.TEXT),
        ("notes.md", InputType.TEXT),
        ("data.xlsx", InputType.EXCEL),
        ("data.csv", InputType.CSV),
        ("slides.pptx", InputType.POWERPOINT),
        ("photo.png", InputType.IMAGE),
        ("photo.jpg", InputType.IMAGE),
        ("report.pdf", InputType.DOCUMENT),
        ("message.eml", InputType.EMAIL),
        ("chat_log.json", InputType.CHAT),
    ])
    def test_extension_mapping(self, factory, filename, expected):
        assert factory.detect_type(filename) == expected

    def test_unknown_extension_defaults_to_text(self, factory):
        assert factory.detect_type("file.xyz") == InputType.TEXT

    def test_no_extension_defaults_to_text(self, factory):
        assert factory.detect_type("noext") == InputType.TEXT


# ---- detect_type with content_type MIME hints ----

class TestDetectTypeByContentType:
    def test_text_plain_mime(self, factory):
        assert factory.detect_type("file.bin", content_type="text/plain") == InputType.TEXT

    def test_rfc822_mime(self, factory):
        assert factory.detect_type("file.bin", content_type="message/rfc822") == InputType.EMAIL

    def test_excel_openxml_mime(self, factory):
        result = factory.detect_type(
            "file.bin",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        assert result == InputType.EXCEL

    def test_csv_mime(self, factory):
        assert factory.detect_type("file.bin", content_type="text/csv") == InputType.CSV

    def test_powerpoint_openxml_mime(self, factory):
        result = factory.detect_type(
            "file.bin",
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        assert result == InputType.POWERPOINT

    def test_image_mime_prefix(self, factory):
        assert factory.detect_type("file.bin", content_type="image/png") == InputType.IMAGE
        assert factory.detect_type("file.bin", content_type="image/jpeg") == InputType.IMAGE

    def test_pdf_mime(self, factory):
        assert factory.detect_type("file.bin", content_type="application/pdf") == InputType.DOCUMENT

    def test_mime_takes_priority_over_extension(self, factory):
        """When content_type is provided and matches, it should override extension."""
        result = factory.detect_type("data.txt", content_type="application/pdf")
        assert result == InputType.DOCUMENT
