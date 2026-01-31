"""Validator (Layer 3) unit tests.

Tests the pure/synchronous validation logic without AI calls:
- _check_completeness: scores requirement content quality (0.0-1.0)
- _check_consistency: detects vague terms and missing info
- _check_traceability: scores source tracing quality (0.0-1.0)
- _needs_pm_review: decides whether PM review is needed
- _create_review_item: creates a ReviewItem with correct issue_type
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.layers.layer3_validation.validator import Validator
from app.models import (
    NormalizedRequirement,
    RequirementType,
    Priority,
    ValidationResult,
    ReviewItemType,
    SourceReference,
)


@pytest.fixture
def mock_settings():
    """Return a mock settings object with default values."""
    settings = MagicMock()
    settings.enable_pm_review = True
    settings.auto_approve_threshold = 0.8
    settings.enable_conflict_detection = False
    return settings


@pytest.fixture
def validator(mock_settings):
    """Validator instance with mocked claude_client and settings."""
    mock_client = AsyncMock()
    with patch("app.layers.layer3_validation.validator.get_settings", return_value=mock_settings):
        v = Validator(claude_client=mock_client)
    return v


def _make_requirement(**overrides) -> NormalizedRequirement:
    """Helper to build a NormalizedRequirement with sensible defaults."""
    defaults = dict(
        id="REQ-001",
        type=RequirementType.FUNCTIONAL,
        title="User login feature",
        description="Users must be able to log in with email and password",
        user_story="As a user, I want to log in to access the service",
        acceptance_criteria=["Email format validated", "Password min 8 chars"],
        priority=Priority.HIGH,
        confidence_score=0.9,
        confidence_reason="Clear functional requirement",
        source_reference="spec.txt",
        source_info=SourceReference(
            document_id="doc-001",
            filename="spec.txt",
            section="Login",
            excerpt="Users must be able to log in",
        ),
    )
    defaults.update(overrides)
    return NormalizedRequirement(**defaults)


# ===================================================================
# _check_completeness tests
# ===================================================================

class TestCheckCompleteness:
    def test_full_requirement_scores_1(self, validator):
        """A requirement with all fields populated should score 1.0."""
        req = _make_requirement()
        score = validator._check_completeness(req)
        assert score == pytest.approx(1.0)

    def test_missing_title_reduces_score(self, validator):
        """A title of 3 chars or fewer does not earn the title point."""
        req = _make_requirement(title="abc")  # len == 3, not > 3
        score = validator._check_completeness(req)
        assert score == pytest.approx(4.0 / 5.0)

    def test_empty_title_reduces_score(self, validator):
        req = _make_requirement(title="")
        score = validator._check_completeness(req)
        assert score == pytest.approx(4.0 / 5.0)

    def test_short_description_reduces_score(self, validator):
        """A description of 10 chars or fewer does not earn the description point."""
        req = _make_requirement(description="short")  # len == 5
        score = validator._check_completeness(req)
        assert score == pytest.approx(4.0 / 5.0)

    def test_no_user_story_reduces_score(self, validator):
        """Missing user_story for non-CONSTRAINT type loses one point."""
        req = _make_requirement(user_story=None)
        score = validator._check_completeness(req)
        assert score == pytest.approx(4.0 / 5.0)

    def test_constraint_type_gets_user_story_point_without_story(self, validator):
        """CONSTRAINT type gets the user_story point even without a user_story."""
        req = _make_requirement(
            type=RequirementType.CONSTRAINT,
            user_story=None,
        )
        score = validator._check_completeness(req)
        assert score == pytest.approx(1.0)

    def test_empty_acceptance_criteria_reduces_score(self, validator):
        req = _make_requirement(acceptance_criteria=[])
        score = validator._check_completeness(req)
        assert score == pytest.approx(4.0 / 5.0)

    def test_minimal_requirement_scores_low(self, validator):
        """A requirement with minimal content should have a low score."""
        req = _make_requirement(
            title="",
            description="",
            user_story=None,
            acceptance_criteria=[],
            # priority is still set, so +1 point
        )
        score = validator._check_completeness(req)
        assert score == pytest.approx(1.0 / 5.0)


# ===================================================================
# _check_consistency tests
# ===================================================================

class TestCheckConsistency:
    def test_clean_description_has_no_issues(self, validator):
        req = _make_requirement(description="Users must log in with email and password")
        issues = validator._check_consistency(req)
        assert issues == []

    @pytest.mark.parametrize("vague_term", [
        "등", "기타", "필요시", "적절한", "합리적인", "etc", "등등",
    ])
    def test_vague_term_detected(self, validator, vague_term):
        req = _make_requirement(description=f"이 기능은 {vague_term} 포함한다")
        issues = validator._check_consistency(req)
        assert any(vague_term in issue for issue in issues)

    def test_missing_info_adds_issues(self, validator):
        req = _make_requirement(missing_info=["구체적인 응답 시간 기준", "대상 사용자 수"])
        issues = validator._check_consistency(req)
        assert len(issues) == 2
        assert all("누락된 정보" in issue for issue in issues)

    def test_missing_info_capped_at_two(self, validator):
        """At most 2 missing_info items are reported."""
        req = _make_requirement(
            missing_info=["info1", "info2", "info3", "info4"],
        )
        issues = validator._check_consistency(req)
        missing_issues = [i for i in issues if "누락된 정보" in i]
        assert len(missing_issues) == 2

    def test_vague_term_and_missing_info_combined(self, validator):
        req = _make_requirement(
            description="적절한 시간 내에 처리해야 한다",
            missing_info=["처리 시간 기준"],
        )
        issues = validator._check_consistency(req)
        assert len(issues) >= 2  # at least one vague + one missing


# ===================================================================
# _check_traceability tests
# ===================================================================

class TestCheckTraceability:
    def test_full_traceability_scores_1(self, validator):
        req = _make_requirement(
            source_reference="spec.txt",
            confidence_score=0.9,  # > 0.5
            confidence_reason="Clearly stated in spec",
        )
        score = validator._check_traceability(req)
        assert score == pytest.approx(1.0)

    def test_no_source_reference_loses_half(self, validator):
        req = _make_requirement(
            source_reference="",
            confidence_score=0.9,
            confidence_reason="reason",
        )
        score = validator._check_traceability(req)
        assert score == pytest.approx(0.5)  # 0 + 0.3 + 0.2

    def test_low_confidence_loses_0_3(self, validator):
        req = _make_requirement(
            source_reference="file.txt",
            confidence_score=0.3,  # <= 0.5
            confidence_reason="reason",
        )
        score = validator._check_traceability(req)
        assert score == pytest.approx(0.7)  # 0.5 + 0 + 0.2

    def test_no_confidence_reason_loses_0_2(self, validator):
        req = _make_requirement(
            source_reference="file.txt",
            confidence_score=0.9,
            confidence_reason="",
        )
        score = validator._check_traceability(req)
        assert score == pytest.approx(0.8)  # 0.5 + 0.3 + 0

    def test_nothing_scores_zero(self, validator):
        req = _make_requirement(
            source_reference="",
            confidence_score=0.3,
            confidence_reason="",
        )
        score = validator._check_traceability(req)
        assert score == pytest.approx(0.0)


# ===================================================================
# _needs_pm_review tests
# ===================================================================

class TestNeedsPmReview:
    def _make_validation(self, **overrides) -> ValidationResult:
        defaults = dict(
            requirement_id="REQ-001",
            is_valid=True,
            completeness_score=0.9,
            consistency_issues=[],
            traceability_score=0.9,
            needs_pm_review=False,
        )
        defaults.update(overrides)
        return ValidationResult(**defaults)

    def test_pm_review_disabled_always_returns_false(self, validator, mock_settings):
        """When enable_pm_review is False, never needs review."""
        mock_settings.enable_pm_review = False
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.1)  # low confidence
        validation = self._make_validation(completeness_score=0.3)
        assert validator._needs_pm_review(req, validation) is False

    def test_low_confidence_needs_review(self, validator, mock_settings):
        """confidence_score < threshold triggers review."""
        mock_settings.auto_approve_threshold = 0.8
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.5)
        validation = self._make_validation()
        assert validator._needs_pm_review(req, validation) is True

    def test_high_confidence_no_issues_no_review(self, validator, mock_settings):
        mock_settings.auto_approve_threshold = 0.8
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.9, missing_info=[])
        validation = self._make_validation(completeness_score=0.9, consistency_issues=[])
        assert validator._needs_pm_review(req, validation) is False

    def test_low_completeness_needs_review(self, validator, mock_settings):
        mock_settings.auto_approve_threshold = 0.8
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.9)
        validation = self._make_validation(completeness_score=0.5)
        assert validator._needs_pm_review(req, validation) is True

    def test_consistency_issues_need_review(self, validator, mock_settings):
        mock_settings.auto_approve_threshold = 0.8
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.9)
        validation = self._make_validation(
            completeness_score=0.9,
            consistency_issues=["vague term found"],
        )
        assert validator._needs_pm_review(req, validation) is True

    def test_missing_info_needs_review(self, validator, mock_settings):
        mock_settings.auto_approve_threshold = 0.8
        validator.settings = mock_settings

        req = _make_requirement(confidence_score=0.9, missing_info=["some info missing"])
        validation = self._make_validation(completeness_score=0.9)
        assert validator._needs_pm_review(req, validation) is True


# ===================================================================
# _create_review_item tests
# ===================================================================

class TestCreateReviewItem:
    def _make_validation(self, **overrides) -> ValidationResult:
        defaults = dict(
            requirement_id="REQ-001",
            is_valid=False,
            completeness_score=0.5,
            consistency_issues=[],
            traceability_score=0.5,
            needs_pm_review=True,
            review_reasons=["Low confidence"],
        )
        defaults.update(overrides)
        return ValidationResult(**defaults)

    def test_low_confidence_creates_low_confidence_type(self, validator):
        req = _make_requirement(confidence_score=0.3)
        validation = self._make_validation()
        item = validator._create_review_item(req, validation, "job-1")

        assert item.issue_type == ReviewItemType.LOW_CONFIDENCE
        assert item.job_id == "job-1"
        assert item.requirement_id == "REQ-001"

    def test_missing_info_creates_missing_info_type(self, validator):
        req = _make_requirement(
            confidence_score=0.7,  # >= 0.5, so not LOW_CONFIDENCE
            missing_info=["database schema"],
        )
        validation = self._make_validation()
        item = validator._create_review_item(req, validation, "job-2")

        assert item.issue_type == ReviewItemType.MISSING_INFO

    def test_ambiguous_fallback(self, validator):
        """When confidence >= 0.5 and no missing_info, issue_type is AMBIGUOUS."""
        req = _make_requirement(
            confidence_score=0.7,
            missing_info=[],
        )
        validation = self._make_validation(
            review_reasons=["Vague terms detected"],
        )
        item = validator._create_review_item(req, validation, "job-3")

        assert item.issue_type == ReviewItemType.AMBIGUOUS

    def test_description_includes_review_reasons(self, validator):
        req = _make_requirement(confidence_score=0.3)
        validation = self._make_validation(review_reasons=["reason A", "reason B"])
        item = validator._create_review_item(req, validation, "job-4")

        assert "reason A" in item.description
        assert "reason B" in item.description

    def test_original_text_from_requirement_description(self, validator):
        long_desc = "x" * 600
        req = _make_requirement(confidence_score=0.3, description=long_desc)
        validation = self._make_validation()
        item = validator._create_review_item(req, validation, "job-5")

        # original_text should be description[:500]
        assert len(item.original_text) == 500

    def test_suggested_resolution_from_confidence_reason(self, validator):
        req = _make_requirement(
            confidence_score=0.3,
            confidence_reason="Needs clarification from stakeholder",
        )
        validation = self._make_validation()
        item = validator._create_review_item(req, validation, "job-6")

        assert item.suggested_resolution == "Needs clarification from stakeholder"
