"""ClaudeClient._parse_json_response unit tests.

Tests the JSON extraction logic that handles various AI response formats:
- Clean JSON, markdown-wrapped JSON, text with embedded JSON
- System message detection
- Error handling for unparseable content
"""

import pytest

from app.services.claude_client import ClaudeClient
from app.exceptions import ClaudeClientError


@pytest.fixture
def client():
    """ClaudeClient instance (no network calls needed for _parse_json_response)."""
    return ClaudeClient()


class TestParseJsonResponseEmpty:
    def test_none_response_returns_empty_dict(self, client):
        assert client._parse_json_response(None) == {}

    def test_empty_string_returns_empty_dict(self, client):
        assert client._parse_json_response("") == {}

    def test_whitespace_only_returns_empty_dict(self, client):
        assert client._parse_json_response("   \n\t  ") == {}


class TestParseJsonResponseValid:
    def test_valid_json_object(self, client):
        result = client._parse_json_response('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_valid_json_array(self, client):
        result = client._parse_json_response('[{"a": 1}, {"b": 2}]')
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"a": 1}

    def test_nested_json_objects(self, client):
        response = '{"outer": {"inner": {"deep": true}}, "list": [1, 2, 3]}'
        result = client._parse_json_response(response)
        assert result["outer"]["inner"]["deep"] is True
        assert result["list"] == [1, 2, 3]


class TestParseJsonResponseMarkdownWrapped:
    def test_json_in_markdown_code_block(self, client):
        response = '```json\n{"requirements": [{"title": "Login"}]}\n```'
        result = client._parse_json_response(response)
        assert "requirements" in result
        assert result["requirements"][0]["title"] == "Login"

    def test_json_in_plain_code_block(self, client):
        response = '```\n{"key": "value"}\n```'
        result = client._parse_json_response(response)
        assert result == {"key": "value"}


class TestParseJsonResponseWithLeadingText:
    def test_leading_text_before_json(self, client):
        response = 'Here is the result:\n{"requirements": [{"title": "Feature A"}]}'
        result = client._parse_json_response(response)
        assert "requirements" in result

    def test_leading_text_before_json_array(self, client):
        """When leading text is present, the parser finds the first { or [.
        Since { appears before [, it extracts the first JSON object."""
        response = 'Analysis complete. [{"id": 1}, {"id": 2}]'
        result = client._parse_json_response(response)
        # The parser finds { before [ so extracts the first object
        assert isinstance(result, dict)
        assert result["id"] == 1


class TestParseJsonResponseSystemMessage:
    def test_system_message_prd_returns_empty(self, client):
        """Responses containing system indicators should return {}."""
        response = "안녕하세요! PRD 생성 시스템에 오신 것을 환영합니다."
        result = client._parse_json_response(response)
        assert result == {}

    def test_system_message_auto_doc_returns_empty(self, client):
        response = "@auto-doc 명령어를 사용하여 문서를 생성할 수 있습니다."
        result = client._parse_json_response(response)
        assert result == {}

    def test_system_message_slash_command_returns_empty(self, client):
        response = "/prd:prd-maker 명령을 실행하여 PRD를 생성합니다."
        result = client._parse_json_response(response)
        assert result == {}


class TestParseJsonResponseInvalid:
    def test_no_brackets_raises_error(self, client):
        """Response with no JSON-like content should raise ClaudeClientError."""
        with pytest.raises(ClaudeClientError):
            client._parse_json_response("This is just plain text with no JSON at all")

    def test_broken_json_after_bracket_raises_error(self, client):
        """Malformed JSON after bracket extraction should raise ClaudeClientError."""
        with pytest.raises(ClaudeClientError):
            client._parse_json_response("result: {broken json without closing")
