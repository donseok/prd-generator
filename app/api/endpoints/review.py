"""PM review endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import ProcessingStatus
from app.services import get_file_storage

router = APIRouter()


class ReviewDecision(BaseModel):
    """Review decision from PM."""
    job_id: str
    review_item_id: str
    decision: str  # approve, reject, modify
    notes: Optional[str] = None
    modified_content: Optional[dict] = None


class BulkReviewDecision(BaseModel):
    """Bulk review decisions."""
    decisions: list[ReviewDecision]


@router.get("/pending/{job_id}")
async def get_pending_reviews(job_id: str) -> dict:
    """
    Get all items pending PM review for a job.

    Items are flagged for review when:
    - Confidence score < 80%
    - Missing critical information
    - Conflicting requirements detected
    - Ambiguous interpretations
    """
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    pending_items = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "issue_type": item.issue_type.value,
            "description": item.description,
            "original_text": item.original_text,
            "suggested_resolution": item.suggested_resolution,
            "created_at": item.created_at.isoformat(),
        }
        for item in job.review_items
        if not item.resolved
    ]

    resolved_items = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "decision": item.pm_decision,
            "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        }
        for item in job.review_items
        if item.resolved
    ]

    return {
        "job_id": job_id,
        "status": job.status.value,
        "total_items": len(job.review_items),
        "pending_count": len(pending_items),
        "resolved_count": len(resolved_items),
        "pending_items": pending_items,
        "resolved_items": resolved_items,
    }


@router.post("/decision")
async def submit_review_decision(decision: ReviewDecision) -> dict:
    """
    Submit PM decision for a review item.

    Decision options:
    - approve: Accept the requirement as-is
    - reject: Remove the requirement from PRD
    - modify: Accept with modifications (provide modified_content)
    """
    storage = get_file_storage()
    job = await storage.get_job(decision.job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    if decision.decision not in ["approve", "reject", "modify"]:
        raise HTTPException(
            status_code=400,
            detail="결정은 approve, reject, modify 중 하나여야 합니다"
        )

    # Find the review item
    review_item = None
    for item in job.review_items:
        if item.id == decision.review_item_id:
            review_item = item
            break

    if not review_item:
        raise HTTPException(status_code=404, detail="검토 항목을 찾을 수 없습니다")

    if review_item.resolved:
        raise HTTPException(status_code=400, detail="이미 처리된 항목입니다")

    # Apply decision
    review_item.resolve(
        decision=decision.decision,
        notes=decision.notes,
        modified_content=decision.modified_content,
    )

    await storage.update_job(job)

    return {
        "message": "검토 결정이 저장되었습니다",
        "item_id": decision.review_item_id,
        "decision": decision.decision,
    }


@router.post("/bulk-decision")
async def submit_bulk_decisions(request: BulkReviewDecision) -> dict:
    """Submit multiple review decisions at once."""
    results = []

    for decision in request.decisions:
        try:
            result = await submit_review_decision(decision)
            results.append({"success": True, **result})
        except HTTPException as e:
            results.append({
                "success": False,
                "item_id": decision.review_item_id,
                "error": e.detail,
            })

    success_count = sum(1 for r in results if r["success"])

    return {
        "message": f"{success_count}/{len(results)}개 결정 처리 완료",
        "results": results,
    }


@router.post("/complete/{job_id}")
async def complete_review(job_id: str) -> dict:
    """
    Mark review as complete and resume pipeline.

    All pending items must be resolved before completing.
    """
    from app.services import get_orchestrator

    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    if job.status != ProcessingStatus.PM_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"PM 검토 상태가 아닙니다: {job.status.value}"
        )

    # Check all items are resolved
    pending_items = [item for item in job.review_items if not item.resolved]
    if pending_items:
        raise HTTPException(
            status_code=400,
            detail=f"{len(pending_items)}개 항목이 아직 검토되지 않았습니다"
        )

    # Resume pipeline through orchestrator
    try:
        orchestrator = get_orchestrator()
        prd = await orchestrator.resume_after_review(job)

        return {
            "message": "검토 완료, PRD 생성 완료",
            "job_id": job_id,
            "prd_id": prd.id,
            "status": job.status.value,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PRD 생성 실패: {str(e)}"
        )


@router.get("/stats/{job_id}")
async def get_review_stats(job_id: str) -> dict:
    """Get review statistics for a job."""
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    # Count by issue type
    issue_type_counts = {}
    decision_counts = {"approve": 0, "reject": 0, "modify": 0}

    for item in job.review_items:
        issue_type = item.issue_type.value
        issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1

        if item.resolved and item.pm_decision:
            decision_counts[item.pm_decision] += 1

    return {
        "job_id": job_id,
        "total_items": len(job.review_items),
        "pending": sum(1 for item in job.review_items if not item.resolved),
        "resolved": sum(1 for item in job.review_items if item.resolved),
        "by_issue_type": issue_type_counts,
        "by_decision": decision_counts,
    }
