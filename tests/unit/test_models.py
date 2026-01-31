"""Unit tests for Pydantic data models.

Tests creation, validation, serialization, and methods of all core models
used in the PRD generation system.
"""

import json
import pytest
from datetime import datetime, timedelta

from app.models import (
    NormalizedRequirement,
    RequirementType,
    Priority,
    SourceReference,
    ValidationResult,
    PRDDocument,
    PRDOverview,
    PRDMetadata,
    Milestone,
    UnresolvedItem,
    ParsedContent,
    InputMetadata,
    InputDocument,
    InputType,
    ProcessingJob,
    ProcessingStatus,
    LayerResult,
    ReviewItem,
    ReviewItemType,
    ProcessingEvent,
)


# ---------------------------------------------------------------------------
# SourceReference
# ---------------------------------------------------------------------------

class TestSourceReference:
    def test_creation_with_required_fields(self):
        ref = SourceReference(document_id="doc-001", filename="spec.txt")
        assert ref.document_id == "doc-001"
        assert ref.filename == "spec.txt"
        assert ref.section is None
        assert ref.line_start is None
        assert ref.line_end is None
        assert ref.excerpt is None

    def test_to_display_string_filename_only(self):
        ref = SourceReference(document_id="doc-001", filename="spec.txt")
        assert ref.to_display_string() == "spec.txt"

    def test_to_display_string_with_section(self):
        ref = SourceReference(
            document_id="doc-001", filename="spec.txt", section="Overview"
        )
        assert ref.to_display_string() == "spec.txt [Overview]"

    def test_to_display_string_with_single_line(self):
        ref = SourceReference(
            document_id="doc-001", filename="spec.txt", line_start=10
        )
        assert ref.to_display_string() == "spec.txt (L10)"

    def test_to_display_string_with_line_range(self):
        ref = SourceReference(
            document_id="doc-001",
            filename="spec.txt",
            section="Auth",
            line_start=5,
            line_end=12,
        )
        assert ref.to_display_string() == "spec.txt [Auth] (L5-12)"

    def test_to_display_string_same_start_end_line(self):
        ref = SourceReference(
            document_id="doc-001", filename="spec.txt", line_start=7, line_end=7
        )
        assert ref.to_display_string() == "spec.txt (L7)"


# ---------------------------------------------------------------------------
# NormalizedRequirement
# ---------------------------------------------------------------------------

class TestNormalizedRequirement:
    def test_creation_with_required_fields(self):
        req = NormalizedRequirement(
            id="REQ-001",
            type=RequirementType.FUNCTIONAL,
            title="Login Feature",
            description="Users can log in",
            confidence_score=0.85,
        )
        assert req.id == "REQ-001"
        assert req.type == RequirementType.FUNCTIONAL
        assert req.priority == Priority.MEDIUM  # default
        assert req.acceptance_criteria == []
        assert req.user_story is None
        assert req.source_info is None

    def test_default_values(self):
        req = NormalizedRequirement(
            id="REQ-002",
            type=RequirementType.NON_FUNCTIONAL,
            title="Performance",
            description="API < 3s",
            confidence_score=0.5,
        )
        assert req.priority == Priority.MEDIUM
        assert req.acceptance_criteria == []
        assert req.confidence_reason == ""
        assert req.source_reference == ""
        assert req.assumptions == []
        assert req.missing_info == []
        assert req.related_requirements == []

    def test_confidence_score_lower_bound(self):
        req = NormalizedRequirement(
            id="REQ-010",
            type=RequirementType.FUNCTIONAL,
            title="Edge",
            description="Lower bound",
            confidence_score=0.0,
        )
        assert req.confidence_score == 0.0

    def test_confidence_score_upper_bound(self):
        req = NormalizedRequirement(
            id="REQ-011",
            type=RequirementType.FUNCTIONAL,
            title="Edge",
            description="Upper bound",
            confidence_score=1.0,
        )
        assert req.confidence_score == 1.0

    def test_confidence_score_below_zero_rejected(self):
        with pytest.raises(Exception):
            NormalizedRequirement(
                id="REQ-012",
                type=RequirementType.FUNCTIONAL,
                title="Bad",
                description="Invalid",
                confidence_score=-0.1,
            )

    def test_confidence_score_above_one_rejected(self):
        with pytest.raises(Exception):
            NormalizedRequirement(
                id="REQ-013",
                type=RequirementType.FUNCTIONAL,
                title="Bad",
                description="Invalid",
                confidence_score=1.1,
            )

    def test_serialization_roundtrip(self):
        req = NormalizedRequirement(
            id="REQ-020",
            type=RequirementType.CONSTRAINT,
            title="DB Constraint",
            description="Must use PostgreSQL",
            confidence_score=0.95,
            priority=Priority.HIGH,
            acceptance_criteria=["PostgreSQL 14+"],
        )
        data = req.model_dump()
        restored = NormalizedRequirement(**data)
        assert restored.id == req.id
        assert restored.type == req.type
        assert restored.confidence_score == req.confidence_score
        assert restored.acceptance_criteria == req.acceptance_criteria


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_creation(self):
        result = ValidationResult(
            requirement_id="REQ-001",
            is_valid=True,
            completeness_score=0.9,
            traceability_score=0.8,
        )
        assert result.is_valid is True
        assert result.consistency_issues == []
        assert result.needs_pm_review is False
        assert result.review_reasons == []

    def test_invalid_result_with_issues(self):
        result = ValidationResult(
            requirement_id="REQ-002",
            is_valid=False,
            completeness_score=0.3,
            traceability_score=0.2,
            consistency_issues=["Conflicting with REQ-001"],
            needs_pm_review=True,
            review_reasons=["Low completeness"],
        )
        assert result.is_valid is False
        assert len(result.consistency_issues) == 1
        assert result.needs_pm_review is True


# ---------------------------------------------------------------------------
# PRDOverview
# ---------------------------------------------------------------------------

class TestPRDOverview:
    def test_creation_with_required_fields(self):
        overview = PRDOverview(
            background="Project background",
            goals=["Goal 1", "Goal 2"],
            scope="Authentication system",
        )
        assert overview.background == "Project background"
        assert len(overview.goals) == 2
        assert overview.scope == "Authentication system"
        assert overview.out_of_scope == []
        assert overview.target_users == []
        assert overview.success_metrics == []


# ---------------------------------------------------------------------------
# Milestone
# ---------------------------------------------------------------------------

class TestMilestone:
    def test_creation(self):
        ms = Milestone(id="MS-001", name="Phase 1", description="Initial build")
        assert ms.id == "MS-001"
        assert ms.order == 0  # default
        assert ms.deliverables == []
        assert ms.dependencies == []

    def test_ordering(self):
        ms1 = Milestone(id="MS-001", name="Phase 1", description="First", order=1)
        ms2 = Milestone(id="MS-002", name="Phase 2", description="Second", order=2)
        ms3 = Milestone(id="MS-003", name="Phase 3", description="Third", order=3)
        sorted_milestones = sorted([ms3, ms1, ms2], key=lambda m: m.order)
        assert [m.id for m in sorted_milestones] == ["MS-001", "MS-002", "MS-003"]


# ---------------------------------------------------------------------------
# PRDDocument
# ---------------------------------------------------------------------------

class TestPRDDocument:
    @pytest.fixture
    def minimal_prd(self):
        return PRDDocument(
            id="PRD-001",
            title="Test Project",
            overview=PRDOverview(
                background="Background",
                goals=["Goal 1"],
                scope="Full scope",
            ),
        )

    @pytest.fixture
    def full_prd(self):
        fr = NormalizedRequirement(
            id="FR-001",
            type=RequirementType.FUNCTIONAL,
            title="Login",
            description="Users can log in",
            confidence_score=0.9,
            priority=Priority.HIGH,
        )
        nfr = NormalizedRequirement(
            id="NFR-001",
            type=RequirementType.NON_FUNCTIONAL,
            title="Performance",
            description="API < 3s",
            confidence_score=0.85,
        )
        return PRDDocument(
            id="PRD-002",
            title="Full Project",
            overview=PRDOverview(
                background="Full background",
                goals=["Goal A"],
                scope="All features",
                target_users=["End users"],
                success_metrics=["KPI 1"],
            ),
            functional_requirements=[fr],
            non_functional_requirements=[nfr],
            milestones=[
                Milestone(id="MS-001", name="Phase 1", description="Build", order=1),
            ],
            metadata=PRDMetadata(
                version="1.0",
                status="draft",
                overall_confidence=0.87,
                source_documents=["input.txt"],
            ),
        )

    def test_creation_minimal(self, minimal_prd):
        assert minimal_prd.id == "PRD-001"
        assert minimal_prd.title == "Test Project"
        assert minimal_prd.functional_requirements == []
        assert minimal_prd.milestones == []

    def test_to_markdown_contains_title(self, full_prd):
        md = full_prd.to_markdown()
        assert "# Full Project" in md

    def test_to_markdown_contains_sections(self, full_prd):
        md = full_prd.to_markdown()
        assert "## 1." in md  # overview section header
        assert "FR-001" in md
        assert "NFR-001" in md

    def test_to_json_is_valid_json(self, full_prd):
        json_str = full_prd.to_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == "PRD-002"
        assert parsed["title"] == "Full Project"
        assert len(parsed["functional_requirements"]) == 1


# ---------------------------------------------------------------------------
# InputDocument, ParsedContent, InputMetadata
# ---------------------------------------------------------------------------

class TestInputModels:
    def test_input_metadata_defaults(self):
        meta = InputMetadata()
        assert meta.filename is None
        assert meta.author is None
        assert meta.sheet_names is None

    def test_parsed_content_creation(self):
        content = ParsedContent(raw_text="Hello world")
        assert content.raw_text == "Hello world"
        assert content.structured_data is None
        assert content.sections == []

    def test_input_document_creation(self):
        content = ParsedContent(raw_text="Some text")
        doc = InputDocument(
            id="doc-001",
            input_type=InputType.TEXT,
            content=content,
        )
        assert doc.id == "doc-001"
        assert doc.input_type == InputType.TEXT
        assert doc.source_path is None
        assert isinstance(doc.uploaded_at, datetime)


# ---------------------------------------------------------------------------
# ProcessingJob
# ---------------------------------------------------------------------------

class TestProcessingJob:
    def test_creation_defaults(self):
        job = ProcessingJob(job_id="job-001")
        assert job.status == ProcessingStatus.PENDING
        assert job.input_document_ids == []
        assert job.layer_results == {}
        assert job.prd_id is None
        assert job.requires_pm_review is False
        assert job.retry_count == 0

    def test_update_status(self):
        job = ProcessingJob(job_id="job-002")
        before = job.updated_at
        job.update_status(ProcessingStatus.PARSING)
        assert job.status == ProcessingStatus.PARSING
        assert job.updated_at >= before

    def test_add_layer_result(self):
        job = ProcessingJob(job_id="job-003")
        result = LayerResult(layer_name="parsing", status="success")
        job.add_layer_result("parsing", result)
        assert "parsing" in job.layer_results
        assert job.layer_results["parsing"].status == "success"

    def test_get_progress_empty(self):
        job = ProcessingJob(job_id="job-004")
        progress = job.get_progress()
        assert progress["completed_layers"] == 0
        assert progress["total_layers"] == 4
        assert progress["progress_percent"] == 0
        assert progress["status"] == "pending"

    def test_get_progress_partial(self):
        job = ProcessingJob(job_id="job-005")
        job.add_layer_result("parsing", LayerResult(layer_name="parsing", status="success"))
        job.add_layer_result("normalizing", LayerResult(layer_name="normalizing", status="success"))
        progress = job.get_progress()
        assert progress["completed_layers"] == 2
        assert progress["progress_percent"] == 50

    def test_get_progress_full(self):
        job = ProcessingJob(job_id="job-006")
        job.update_status(ProcessingStatus.COMPLETED)
        for layer in ["parsing", "normalizing", "validating", "generating"]:
            job.add_layer_result(layer, LayerResult(layer_name=layer, status="success"))
        progress = job.get_progress()
        assert progress["completed_layers"] == 4
        assert progress["progress_percent"] == 100
        assert progress["current_layer"] == "done"


# ---------------------------------------------------------------------------
# LayerResult
# ---------------------------------------------------------------------------

class TestLayerResult:
    def test_creation(self):
        lr = LayerResult(layer_name="parsing", status="pending")
        assert lr.layer_name == "parsing"
        assert lr.status == "pending"
        assert lr.completed_at is None
        assert lr.duration_ms is None
        assert lr.output_data is None
        assert lr.errors == []
        assert lr.warnings == []

    def test_complete_sets_fields(self):
        lr = LayerResult(layer_name="parsing", status="pending")
        lr.complete(output_data={"items": 5})
        assert lr.status == "success"
        assert lr.completed_at is not None
        assert lr.duration_ms is not None
        assert lr.duration_ms >= 0
        assert lr.output_data == {"items": 5}

    def test_complete_with_errors(self):
        lr = LayerResult(layer_name="normalizing", status="pending")
        lr.complete(errors=["Something went wrong"])
        assert lr.status == "failed"
        assert lr.errors == ["Something went wrong"]


# ---------------------------------------------------------------------------
# ReviewItem
# ---------------------------------------------------------------------------

class TestReviewItem:
    def test_creation(self):
        item = ReviewItem(
            job_id="job-001",
            requirement_id="REQ-001",
            issue_type=ReviewItemType.LOW_CONFIDENCE,
            description="Score is too low",
        )
        assert item.job_id == "job-001"
        assert item.requirement_id == "REQ-001"
        assert item.issue_type == ReviewItemType.LOW_CONFIDENCE
        assert item.resolved is False
        assert item.pm_decision is None

    def test_resolve(self):
        item = ReviewItem(
            job_id="job-002",
            requirement_id="REQ-002",
            issue_type=ReviewItemType.MISSING_INFO,
            description="Need clarification",
        )
        item.resolve(decision="approve", notes="Looks fine after review")
        assert item.resolved is True
        assert item.pm_decision == "approve"
        assert item.pm_notes == "Looks fine after review"
        assert item.resolved_at is not None

    def test_resolve_with_modification(self):
        item = ReviewItem(
            job_id="job-003",
            requirement_id="REQ-003",
            issue_type=ReviewItemType.AMBIGUOUS,
            description="Ambiguous requirement",
        )
        modified = {"title": "Updated Title", "description": "Clearer description"}
        item.resolve(decision="modify", modified_content=modified)
        assert item.pm_decision == "modify"
        assert item.modified_content == modified
        assert item.resolved is True


# ---------------------------------------------------------------------------
# ProcessingEvent
# ---------------------------------------------------------------------------

class TestProcessingEvent:
    def test_creation(self):
        event = ProcessingEvent(
            job_id="job-001",
            event_type="status_change",
            message="Started parsing",
        )
        assert event.job_id == "job-001"
        assert event.event_type == "status_change"
        assert event.progress_percent == 0
        assert event.layer is None
        assert event.data is None
        assert isinstance(event.timestamp, datetime)
