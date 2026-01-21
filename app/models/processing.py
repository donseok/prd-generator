"""Processing pipeline data models."""

from enum import Enum
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid


class ProcessingStatus(str, Enum):
    """Pipeline processing status."""

    PENDING = "pending"
    PARSING = "parsing"
    NORMALIZING = "normalizing"
    VALIDATING = "validating"
    GENERATING = "generating"
    PM_REVIEW = "pm_review"
    COMPLETED = "completed"
    FAILED = "failed"


class LayerResult(BaseModel):
    """Result from a single layer processing."""

    layer_name: str
    status: str = Field(
        ..., description="Layer status: success, partial, failed"
    )
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output_data: Optional[Any] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def complete(self, output_data: Any = None, errors: list[str] = None):
        """Mark layer as completed."""
        self.completed_at = datetime.now()
        self.duration_ms = int(
            (self.completed_at - self.started_at).total_seconds() * 1000
        )
        if output_data:
            self.output_data = output_data
        if errors:
            self.errors = errors
            self.status = "failed" if errors else "success"
        else:
            self.status = "success"


class ReviewItemType(str, Enum):
    """Types of review items."""

    LOW_CONFIDENCE = "low_confidence"
    MISSING_INFO = "missing_info"
    CONFLICT = "conflict"
    AMBIGUOUS = "ambiguous"


class ReviewItem(BaseModel):
    """Item requiring PM review."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    job_id: str
    requirement_id: str
    issue_type: ReviewItemType
    description: str
    original_text: str = ""
    suggested_resolution: Optional[str] = None
    pm_decision: Optional[str] = Field(
        default=None, description="PM decision: approve, reject, modify"
    )
    pm_notes: Optional[str] = None
    modified_content: Optional[dict] = Field(
        default=None, description="Modified requirement data if pm_decision is modify"
    )
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def resolve(self, decision: str, notes: str = None, modified_content: dict = None):
        """Resolve review item with PM decision."""
        self.pm_decision = decision
        self.pm_notes = notes
        self.modified_content = modified_content
        self.resolved = True
        self.resolved_at = datetime.now()


class ProcessingJob(BaseModel):
    """Represents a complete processing job."""

    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique job identifier"
    )
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Input tracking
    input_document_ids: list[str] = Field(default_factory=list)
    input_filenames: list[str] = Field(default_factory=list)

    # Layer results
    layer_results: dict[str, LayerResult] = Field(default_factory=dict)

    # Output
    prd_id: Optional[str] = None

    # Review tracking
    requires_pm_review: bool = False
    review_items: list[ReviewItem] = Field(default_factory=list)

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0

    def update_status(self, status: ProcessingStatus):
        """Update job status."""
        self.status = status
        self.updated_at = datetime.now()

    def add_layer_result(self, layer_name: str, result: LayerResult):
        """Add layer result."""
        self.layer_results[layer_name] = result
        self.updated_at = datetime.now()

    def add_review_item(self, item: ReviewItem):
        """Add review item."""
        self.review_items.append(item)
        self.requires_pm_review = True
        self.updated_at = datetime.now()

    def get_progress(self) -> dict:
        """Get processing progress info."""
        layer_order = ["parsing", "normalizing", "validating", "generating"]
        completed_layers = sum(
            1 for layer in layer_order
            if layer in self.layer_results and self.layer_results[layer].status == "success"
        )
        return {
            "status": self.status.value,
            "current_layer": self.status.value if self.status != ProcessingStatus.COMPLETED else "done",
            "completed_layers": completed_layers,
            "total_layers": len(layer_order),
            "progress_percent": int((completed_layers / len(layer_order)) * 100),
            "requires_pm_review": self.requires_pm_review,
            "pending_reviews": sum(1 for item in self.review_items if not item.resolved),
        }


class ProcessingEvent(BaseModel):
    """Event for real-time processing updates."""

    job_id: str
    event_type: str = Field(
        ..., description="Event type: status_change, layer_start, layer_complete, error, review_required"
    )
    layer: Optional[str] = None
    message: str
    progress_percent: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[dict] = None
