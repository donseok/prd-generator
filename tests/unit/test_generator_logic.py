"""BaseGenerator unit tests.

Tests the concrete (non-abstract) methods of BaseGenerator:
- _generate_id: produces IDs in the format {PREFIX}-{YYYYMMDD}-{4hex}
- _call_claude_json: returns {} on exception
- _call_claude_text: returns "" on exception
- _call_claude_json_with_fallback: returns fallback when result is empty
"""

import re
import pytest
from unittest.mock import AsyncMock

from app.layers.base_generator import BaseGenerator


class ConcreteGenerator(BaseGenerator):
    """Minimal concrete subclass for testing BaseGenerator."""

    _id_prefix = "TEST"
    _generator_name = "TestGen"

    async def _do_generate(self, input_doc, context):
        return input_doc  # passthrough


@pytest.fixture
def mock_claude_client():
    client = AsyncMock()
    client.complete = AsyncMock(return_value="mock text response")
    client.complete_json = AsyncMock(return_value={"key": "value"})
    return client


@pytest.fixture
def generator(mock_claude_client):
    return ConcreteGenerator(claude_client=mock_claude_client)


# ===================================================================
# _generate_id tests
# ===================================================================

class TestGenerateId:
    def test_id_matches_expected_format(self, generator):
        """ID should be {PREFIX}-{YYYYMMDD}-{4 hex chars}."""
        doc_id = generator._generate_id()
        pattern = r"^TEST-\d{8}-[0-9a-f]{4}$"
        assert re.match(pattern, doc_id), f"ID '{doc_id}' does not match pattern '{pattern}'"

    def test_id_starts_with_prefix(self, generator):
        doc_id = generator._generate_id()
        assert doc_id.startswith("TEST-")

    def test_id_contains_date_part(self, generator):
        from datetime import datetime
        doc_id = generator._generate_id()
        date_part = doc_id.split("-")[1]
        # Verify it is a valid date string YYYYMMDD
        parsed_date = datetime.strptime(date_part, "%Y%m%d")
        assert parsed_date.date() == datetime.now().date()

    def test_generates_unique_ids(self, generator):
        """Multiple calls should produce different IDs (UUID part differs)."""
        ids = {generator._generate_id() for _ in range(50)}
        assert len(ids) == 50, "Expected 50 unique IDs"

    def test_custom_prefix(self, mock_claude_client):
        """A subclass with a different prefix uses that prefix."""

        class PropGenerator(BaseGenerator):
            _id_prefix = "PROP"
            _generator_name = "PropGen"

            async def _do_generate(self, input_doc, context):
                return input_doc

        gen = PropGenerator(claude_client=mock_claude_client)
        doc_id = gen._generate_id()
        assert doc_id.startswith("PROP-")


# ===================================================================
# _call_claude_json tests
# ===================================================================

class TestCallClaudeJson:
    @pytest.mark.asyncio
    async def test_returns_result_on_success(self, generator, mock_claude_client):
        mock_claude_client.complete_json.return_value = {"requirements": []}
        result = await generator._call_claude_json("system", "user")
        assert result == {"requirements": []}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_exception(self, generator, mock_claude_client):
        mock_claude_client.complete_json.side_effect = RuntimeError("API failure")
        result = await generator._call_claude_json("system", "user")
        assert result == {}

    @pytest.mark.asyncio
    async def test_passes_temperature(self, generator, mock_claude_client):
        await generator._call_claude_json("sys", "usr", temperature=0.7)
        mock_claude_client.complete_json.assert_called_once()
        call_kwargs = mock_claude_client.complete_json.call_args
        assert call_kwargs.kwargs["temperature"] == 0.7


# ===================================================================
# _call_claude_text tests
# ===================================================================

class TestCallClaudeText:
    @pytest.mark.asyncio
    async def test_returns_stripped_result_on_success(self, generator, mock_claude_client):
        mock_claude_client.complete.return_value = "  Hello World  "
        result = await generator._call_claude_text("system", "user")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_returns_empty_string_on_exception(self, generator, mock_claude_client):
        mock_claude_client.complete.side_effect = RuntimeError("API failure")
        result = await generator._call_claude_text("system", "user")
        assert result == ""


# ===================================================================
# _call_claude_json_with_fallback tests
# ===================================================================

class TestCallClaudeJsonWithFallback:
    @pytest.mark.asyncio
    async def test_returns_result_when_non_empty(self, generator, mock_claude_client):
        mock_claude_client.complete_json.return_value = {"data": [1, 2, 3]}
        result = await generator._call_claude_json_with_fallback(
            "sys", "usr", fallback_value={"default": True}
        )
        assert result == {"data": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_returns_fallback_when_empty_dict(self, generator, mock_claude_client):
        """When _call_claude_json returns {}, the fallback should be used."""
        mock_claude_client.complete_json.return_value = {}
        # _call_claude_json returns {} on success with empty result
        # But the method checks `if result` which is falsy for {}
        result = await generator._call_claude_json_with_fallback(
            "sys", "usr", fallback_value={"default": True}
        )
        assert result == {"default": True}

    @pytest.mark.asyncio
    async def test_returns_fallback_on_exception(self, generator, mock_claude_client):
        """When _call_claude_json returns {} due to exception, fallback is used."""
        mock_claude_client.complete_json.side_effect = RuntimeError("fail")
        result = await generator._call_claude_json_with_fallback(
            "sys", "usr", fallback_value=["fallback_list"]
        )
        assert result == ["fallback_list"]
