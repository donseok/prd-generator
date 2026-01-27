"""
처리 파이프라인 관련 데이터 모델입니다.
작업(Job)의 상태, 진행률, 이벤트 등을 정의합니다.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid


class ProcessingStatus(str, Enum):
    """
    작업 진행 상태 단계입니다.
    """

    PENDING = "pending"         # 대기 중
    PARSING = "parsing"         # 1단계: 파싱 중
    NORMALIZING = "normalizing" # 2단계: 정규화 중
    VALIDATING = "validating"   # 3단계: 검증 중
    GENERATING = "generating"   # 4단계: 문서 생성 중
    PM_REVIEW = "pm_review"     # 기획자 검토 대기 중
    COMPLETED = "completed"     # 완료됨
    FAILED = "failed"           # 실패함


class LayerResult(BaseModel):
    """각 단계(Layer)별 처리 결과 정보입니다."""

    layer_name: str
    status: str = Field(
        ..., description="상태: success(성공), partial(부분성공), failed(실패)"
    )
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None # 소요 시간 (밀리초)
    output_data: Optional[Any] = None # 결과 데이터
    errors: list[str] = Field(default_factory=list) # 에러 목록
    warnings: list[str] = Field(default_factory=list) # 경고 목록

    def complete(self, output_data: Any = None, errors: list[str] = None):
        """작업을 완료 상태로 표시하는 함수"""
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
    """검토가 필요한 이유(유형)입니다."""

    LOW_CONFIDENCE = "low_confidence" # 확신도 낮음
    MISSING_INFO = "missing_info"     # 정보 부족
    CONFLICT = "conflict"             # 내용 충돌
    AMBIGUOUS = "ambiguous"           # 모호함


class ReviewItem(BaseModel):
    """
    기획자의 검토가 필요한 개별 항목입니다.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    job_id: str
    requirement_id: str
    issue_type: ReviewItemType
    description: str # 왜 검토가 필요한지 설명
    original_text: str = "" # 원본 내용
    suggested_resolution: Optional[str] = None # AI의 제안
    pm_decision: Optional[str] = Field(
        default=None, description="기획자의 결정: approve, reject, modify"
    )
    pm_notes: Optional[str] = None # 기획자 메모
    modified_content: Optional[dict] = Field(
        default=None, description="수정 시 변경된 데이터"
    )
    resolved: bool = False # 해결 여부
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def resolve(self, decision: str, notes: str = None, modified_content: dict = None):
        """기획자의 결정으로 항목을 해결 처리합니다."""
        self.pm_decision = decision
        self.pm_notes = notes
        self.modified_content = modified_content
        self.resolved = True
        self.resolved_at = datetime.now()


class ProcessingJob(BaseModel):
    """
    전체 처리 작업(Job)을 나타내는 클래스입니다.
    하나의 PRD 생성 요청이 하나의 Job이 됩니다.
    """

    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="작업 고유 ID"
    )
    status: ProcessingStatus = ProcessingStatus.PENDING # 현재 상태
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 입력 정보
    input_document_ids: list[str] = Field(default_factory=list)
    input_filenames: list[str] = Field(default_factory=list)

    # 단계별 결과
    layer_results: dict[str, LayerResult] = Field(default_factory=dict)

    # 결과물 (PRD ID)
    prd_id: Optional[str] = None

    # 검토 관리
    requires_pm_review: bool = False
    review_items: list[ReviewItem] = Field(default_factory=list)

    # 에러 관리
    error_message: Optional[str] = None
    retry_count: int = 0

    def update_status(self, status: ProcessingStatus):
        """작업 상태 업데이트"""
        self.status = status
        self.updated_at = datetime.now()

    def add_layer_result(self, layer_name: str, result: LayerResult):
        """단계별 결과 저장"""
        self.layer_results[layer_name] = result
        self.updated_at = datetime.now()

    def add_review_item(self, item: ReviewItem):
        """검토 항목 추가"""
        self.review_items.append(item)
        self.requires_pm_review = True
        self.updated_at = datetime.now()

    def get_progress(self) -> dict:
        """현재 진행률 정보를 계산하여 반환합니다."""
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
    """
    실시간 진행 상황을 클라이언트에 알리기 위한 이벤트 모델입니다.
    """

    job_id: str
    event_type: str = Field(
        ..., description="이벤트 종류: 상태변경, 단계시작, 단계완료, 에러 등"
    )
    layer: Optional[str] = None
    message: str
    progress_percent: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[dict] = None