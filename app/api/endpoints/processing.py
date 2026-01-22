"""Processing pipeline endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models import ProcessingJob, ProcessingStatus
from app.services import get_file_storage

router = APIRouter()


class StartProcessingRequest(BaseModel):
    """Request body for starting processing."""
    document_ids: List[str]


@router.post("/start")
async def start_processing(
    request: StartProcessingRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Start the PRD generation pipeline for given documents.

    The pipeline processes documents through 4 layers:
    1. Parsing - Extract text and structure
    2. Normalization - Convert to requirements
    3. Validation - Quality checks
    4. Generation - Create PRD document
    """
    storage = get_file_storage()

    # Validate document IDs
    documents = []
    filenames = []
    for doc_id in request.document_ids:
        doc = await storage.get_input_document(doc_id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"문서를 찾을 수 없습니다: {doc_id}"
            )
        documents.append(doc)
        filenames.append(doc.content.metadata.filename or doc_id)

    # Create processing job
    job = ProcessingJob(
        input_document_ids=request.document_ids,
        input_filenames=filenames,
    )

    # Save job
    await storage.save_job(job)

    # Start background processing using asyncio.create_task
    import asyncio
    asyncio.create_task(run_pipeline(job.job_id))

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": f"{len(documents)}개 문서 처리 시작",
        "documents": filenames,
    }


async def run_pipeline(job_id: str):
    """Background task to run the processing pipeline."""
    import traceback
    from app.services import get_orchestrator

    print(f"[Pipeline] Starting pipeline for job: {job_id}")

    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        print(f"[Pipeline] Job not found: {job_id}")
        return

    try:
        # Get input documents
        documents = []
        for doc_id in job.input_document_ids:
            doc = await storage.get_input_document(doc_id)
            if doc:
                documents.append(doc)

        if not documents:
            raise ValueError("입력 문서를 찾을 수 없습니다")

        print(f"[Pipeline] Processing {len(documents)} documents")

        # Run pipeline through orchestrator
        orchestrator = get_orchestrator()
        prd = await orchestrator.process(job, documents)

        print(f"[Pipeline] Pipeline completed. PRD: {prd.id if prd else 'None (PM review required)'}")

        # If prd is None, it means PM review is required
        # The orchestrator already updated the job status

    except Exception as e:
        print(f"[Pipeline] ERROR: {e}")
        traceback.print_exc()
        job.update_status(ProcessingStatus.FAILED)
        job.error_message = str(e)
        await storage.update_job(job)


@router.get("/status/{job_id}")
async def get_processing_status(job_id: str) -> dict:
    """
    Get current processing status and progress.

    Returns progress through 4-layer pipeline.
    """
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    progress = job.get_progress()

    return {
        "job_id": job.job_id,
        **progress,
        "documents": job.input_filenames,
        "prd_id": job.prd_id,
        "error": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


@router.post("/cancel/{job_id}")
async def cancel_processing(job_id: str) -> dict:
    """Cancel an in-progress processing job."""
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    if job.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"이미 완료된 작업입니다: {job.status.value}"
        )

    job.update_status(ProcessingStatus.FAILED)
    job.error_message = "사용자에 의해 취소됨"
    await storage.update_job(job)

    return {"message": "작업이 취소되었습니다", "job_id": job_id}


@router.get("")
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    status: str = None
) -> dict:
    """List all processing jobs."""
    storage = get_file_storage()
    jobs = await storage.list_jobs(skip=skip, limit=limit, status=status)

    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "documents": job.input_filenames,
                "prd_id": job.prd_id,
                "requires_pm_review": job.requires_pm_review,
                "created_at": job.created_at.isoformat(),
            }
            for job in jobs
        ],
    }
