"""Normalizer (Layer 2) unit tests.

Tests the pure/synchronous methods of the Normalizer without AI calls:
- _convert_to_requirement: converts a raw dict to NormalizedRequirement
- _extract_from_content: extracts raw requirement dicts from ParsedContent
"""

import pytest
from unittest.mock import AsyncMock

from app.layers.layer2_normalization.normalizer import Normalizer
from app.models import (
    ParsedContent,
    InputMetadata,
    RequirementType,
    Priority,
)


@pytest.fixture
def normalizer():
    """Normalizer instance with mocked claude_client."""
    mock_client = AsyncMock()
    return Normalizer(claude_client=mock_client)


def _make_raw_requirement(**overrides) -> dict:
    """Helper to build a raw requirement dict with sensible defaults."""
    defaults = dict(
        title="User Login",
        description="Users must log in with email and password",
        type="FR",
        priority="HIGH",
        confidence_score=0.85,
        user_story="As a user, I want to log in",
        acceptance_criteria=["Email validated", "Password min 8 chars"],
        section_name="Authentication",
        original_text="Users must log in with email and password",
        assumptions=["Email service available"],
        missing_info=["MFA requirements"],
    )
    defaults.update(overrides)
    return defaults


# ===================================================================
# _convert_to_requirement: type mapping
# ===================================================================

class TestConvertToRequirementTypeMapping:
    def test_fr_maps_to_functional(self, normalizer):
        raw = _make_raw_requirement(type="FR")
        req = normalizer._convert_to_requirement(raw, 1, "test.txt", "doc-001")
        assert req is not None
        assert req.type == RequirementType.FUNCTIONAL

    def test_nfr_maps_to_non_functional(self, normalizer):
        raw = _make_raw_requirement(type="NFR")
        req = normalizer._convert_to_requirement(raw, 2, "test.txt", "doc-001")
        assert req.type == RequirementType.NON_FUNCTIONAL

    def test_non_functional_string_maps_correctly(self, normalizer):
        raw = _make_raw_requirement(type="NON_FUNCTIONAL")
        req = normalizer._convert_to_requirement(raw, 3, "test.txt", "doc-001")
        assert req.type == RequirementType.NON_FUNCTIONAL

    def test_constraint_maps_to_constraint(self, normalizer):
        raw = _make_raw_requirement(type="CONSTRAINT")
        req = normalizer._convert_to_requirement(raw, 4, "test.txt", "doc-001")
        assert req.type == RequirementType.CONSTRAINT

    def test_unknown_type_defaults_to_functional(self, normalizer):
        raw = _make_raw_requirement(type="UNKNOWN")
        req = normalizer._convert_to_requirement(raw, 5, "test.txt", "doc-001")
        assert req.type == RequirementType.FUNCTIONAL


# ===================================================================
# _convert_to_requirement: priority mapping
# ===================================================================

class TestConvertToRequirementPriorityMapping:
    def test_high_priority(self, normalizer):
        raw = _make_raw_requirement(priority="HIGH")
        req = normalizer._convert_to_requirement(raw, 1, "test.txt", "doc-001")
        assert req.priority == Priority.HIGH

    def test_low_priority(self, normalizer):
        raw = _make_raw_requirement(priority="LOW")
        req = normalizer._convert_to_requirement(raw, 2, "test.txt", "doc-001")
        assert req.priority == Priority.LOW

    def test_unknown_priority_defaults_to_medium(self, normalizer):
        raw = _make_raw_requirement(priority="UNKNOWN")
        req = normalizer._convert_to_requirement(raw, 3, "test.txt", "doc-001")
        assert req.priority == Priority.MEDIUM

    def test_missing_priority_defaults_to_medium(self, normalizer):
        raw = _make_raw_requirement()
        del raw["priority"]
        req = normalizer._convert_to_requirement(raw, 4, "test.txt", "doc-001")
        assert req.priority == Priority.MEDIUM


# ===================================================================
# _convert_to_requirement: confidence_score clamping
# ===================================================================

class TestConvertToRequirementConfidenceScore:
    def test_normal_score_preserved(self, normalizer):
        raw = _make_raw_requirement(confidence_score=0.75)
        req = normalizer._convert_to_requirement(raw, 1, "test.txt", "doc-001")
        assert req.confidence_score == pytest.approx(0.75)

    def test_score_above_1_clamped(self, normalizer):
        raw = _make_raw_requirement(confidence_score=1.5)
        req = normalizer._convert_to_requirement(raw, 2, "test.txt", "doc-001")
        assert req.confidence_score == pytest.approx(1.0)

    def test_score_below_0_clamped(self, normalizer):
        raw = _make_raw_requirement(confidence_score=-0.5)
        req = normalizer._convert_to_requirement(raw, 3, "test.txt", "doc-001")
        assert req.confidence_score == pytest.approx(0.0)

    def test_invalid_score_string_defaults_to_0_7(self, normalizer):
        raw = _make_raw_requirement(confidence_score="invalid")
        req = normalizer._convert_to_requirement(raw, 4, "test.txt", "doc-001")
        assert req.confidence_score == pytest.approx(0.7)


# ===================================================================
# _convert_to_requirement: source_info and other fields
# ===================================================================

class TestConvertToRequirementFields:
    def test_source_info_populated(self, normalizer):
        raw = _make_raw_requirement(
            section_name="Auth Section",
            original_text="log in with email",
        )
        req = normalizer._convert_to_requirement(raw, 1, "spec.txt", "doc-42")
        assert req.source_info is not None
        assert req.source_info.document_id == "doc-42"
        assert req.source_info.filename == "spec.txt"
        assert req.source_info.section == "Auth Section"
        assert "log in with email" in req.source_info.excerpt

    def test_source_reference_includes_section_name(self, normalizer):
        raw = _make_raw_requirement(section_name="Login")
        req = normalizer._convert_to_requirement(raw, 1, "spec.txt", "doc-001")
        assert "spec.txt" in req.source_reference
        assert "[Login]" in req.source_reference

    def test_missing_fields_use_defaults(self, normalizer):
        raw = {"title": "Minimal", "description": "Minimal description"}
        req = normalizer._convert_to_requirement(raw, 1, "file.txt", "doc-001")
        assert req is not None
        assert req.type == RequirementType.FUNCTIONAL
        assert req.priority == Priority.MEDIUM
        assert req.confidence_score == pytest.approx(0.7)
        assert req.acceptance_criteria == []
        assert req.assumptions == []
        assert req.missing_info == []

    def test_id_format(self, normalizer):
        raw = _make_raw_requirement()
        req = normalizer._convert_to_requirement(raw, 42, "file.txt", "doc-001")
        assert req.id == "REQ-042"

    def test_title_truncated_to_50_chars(self, normalizer):
        long_title = "A" * 100
        raw = _make_raw_requirement(title=long_title)
        req = normalizer._convert_to_requirement(raw, 1, "file.txt", "doc-001")
        assert len(req.title) <= 50


# ===================================================================
# _extract_from_content tests
# ===================================================================

class TestExtractFromContent:
    def test_extracts_from_sections(self, normalizer):
        """Sections with meaningful content (>10 chars) become requirements."""
        parsed = ParsedContent(
            raw_text="Some raw text",
            metadata=InputMetadata(filename="test.txt"),
            sections=[
                {"title": "Login Feature", "content": "Users can log in with email and password system"},
                {"title": "Dashboard", "content": "Admin dashboard with analytics and reporting tools"},
            ],
        )
        result = normalizer._extract_from_content(parsed)
        assert len(result) == 2
        assert result[0]["title"] == "Login Feature"
        assert result[1]["title"] == "Dashboard"

    def test_skips_short_section_content(self, normalizer):
        """Sections with content <= 10 chars stripped should be skipped."""
        parsed = ParsedContent(
            raw_text="",
            metadata=InputMetadata(filename="test.txt"),
            sections=[
                {"title": "Empty", "content": "short"},
                {"title": "Valid", "content": "This is a valid content with more than 10 characters"},
            ],
        )
        result = normalizer._extract_from_content(parsed)
        assert len(result) == 1
        assert result[0]["title"] == "Valid"

    def test_extracts_from_raw_text_headers(self, normalizer):
        """When no sections, falls back to raw_text header detection."""
        raw_text = """# Login Feature
Users must be able to login with credentials
This is an important feature

# Dashboard
Admin dashboard for monitoring
"""
        parsed = ParsedContent(
            raw_text=raw_text,
            metadata=InputMetadata(filename="test.txt"),
            sections=[],
        )
        result = normalizer._extract_from_content(parsed)
        assert len(result) >= 1
        # The header-based extraction looks for lines starting with #
        assert any("Login Feature" in r.get("title", "") for r in result)

    def test_empty_content_returns_empty_list(self, normalizer):
        parsed = ParsedContent(
            raw_text="",
            metadata=InputMetadata(filename="test.txt"),
            sections=[],
        )
        result = normalizer._extract_from_content(parsed)
        assert result == []

    def test_section_with_list_content(self, normalizer):
        """Section content that is a list should be joined."""
        parsed = ParsedContent(
            raw_text="",
            metadata=InputMetadata(filename="test.txt"),
            sections=[
                {
                    "title": "Feature List",
                    "content": ["Login feature implementation", "Password reset", "Two factor auth"],
                },
            ],
        )
        result = normalizer._extract_from_content(parsed)
        assert len(result) == 1
        assert "Login feature" in result[0]["description"]
