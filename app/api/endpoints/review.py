"""
PM(기획자) 검토 API입니다.
AI가 100% 확신하지 못하는 요구사항들에 대해 사람이 직접 확인하고 결정(승인/수정/반려)하는 기능을 제공합니다.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import ProcessingStatus
from app.services import get_file_storage

router = APIRouter()


class ReviewDecision(BaseModel):
    """검토 결정 데이터 모델"""
    job_id: str
    review_item_id: str
    decision: str  # approve(승인), reject(반려), modify(수정)
    notes: Optional[str] = None
    modified_content: Optional[dict] = None


class BulkReviewDecision(BaseModel):
    """일괄 검토 데이터 모델"""
    decisions: list[ReviewDecision]


@router.get("/pending/{job_id}")
async def get_pending_reviews(job_id: str) -> dict:
    """
    검토 대기 중인 항목들을 조회합니다.
    
    검토 대상이 되는 경우:
    - AI의 확신도가 80% 미만일 때
    - 중요 정보가 빠져있을 때
    - 서로 다른 요구사항이 충돌할 때
    - 내용이 애매할 때
    """
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    # 아직 처리되지 않은 항목들
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

    # 이미 처리된 항목들
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
    개별 항목에 대한 검토 결정을 저장합니다.
    
    옵션:
    - approve: 그대로 승인
    - reject: 요구사항 삭제 (PRD에 포함 안 함)
    - modify: 내용 수정 후 승인
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

    # 해당 검토 항목 찾기
    review_item = None
    for item in job.review_items:
        if item.id == decision.review_item_id:
            review_item = item
            break

    if not review_item:
        raise HTTPException(status_code=404, detail="검토 항목을 찾을 수 없습니다")

    if review_item.resolved:
        raise HTTPException(status_code=400, detail="이미 처리된 항목입니다")

    # 결정 적용
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
    """여러 항목을 한 번에 검토 처리합니다 (일괄 승인 등)."""
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
    모든 검토가 끝났을 때 호출하여 파이프라인을 재개합니다.
    남은 검토 항목이 없어야 합니다.
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

    # 미해결 항목 확인
    pending_items = [item for item in job.review_items if not item.resolved]
    if pending_items:
        raise HTTPException(
            status_code=400,
            detail=f"{len(pending_items)}개 항목이 아직 검토되지 않았습니다"
        )

    # 오케스트레이터를 통해 작업 재개 (PRD 생성 단계로 이동)
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
    """검토 현황 통계를 조회합니다 (승인/반려 건수 등)."""
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    # 이슈 유형별 카운트
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