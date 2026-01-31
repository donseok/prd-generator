"""
AI 처리 파이프라인 제어 API입니다.
PRD 생성 작업을 시작하고, 진행 상황을 확인하거나 취소할 수 있습니다.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models import ProcessingJob, ProcessingStatus
from app.services import get_file_storage

logger = logging.getLogger(__name__)

router = APIRouter()


class StartProcessingRequest(BaseModel):
    """작업 시작 요청에 사용할 데이터 모델 (문서 ID 목록)"""
    document_ids: List[str]


@router.post("/start")
async def start_processing(
    request: StartProcessingRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    PRD 생성 파이프라인을 시작하는 API입니다.
    
    파이프라인 단계:
    1. 파싱(Parsing): 문서 내용 읽기
    2. 정규화(Normalization): 요구사항 정리
    3. 검증(Validation): 품질 체크
    4. 생성(Generation): PRD 문서 작성
    """
    storage = get_file_storage()

    # 요청된 문서 ID들이 실제로 존재하는지 확인
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

    # 새로운 처리 작업(Job) 생성
    job = ProcessingJob(
        input_document_ids=request.document_ids,
        input_filenames=filenames,
    )

    # 작업 정보를 저장소에 기록
    await storage.save_job(job)

    # 백그라운드에서 AI 처리 작업 시작 (사용자는 기다리지 않고 바로 응답을 받음)
    import asyncio
    asyncio.create_task(run_pipeline(job.job_id))

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": f"{len(documents)}개 문서 처리 시작",
        "documents": filenames,
    }


async def run_pipeline(job_id: str):
    """실제 파이프라인을 실행하는 백그라운드 함수"""
    from app.services import get_orchestrator

    logger.info(f"[Pipeline] 작업 시작 ID: {job_id}")

    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        logger.error(f"[Pipeline] 작업을 찾을 수 없음: {job_id}")
        return

    try:
        # 처리할 문서 정보 가져오기
        documents = []
        for doc_id in job.input_document_ids:
            doc = await storage.get_input_document(doc_id)
            if doc:
                documents.append(doc)

        if not documents:
            raise ValueError("입력 문서를 찾을 수 없습니다")

        logger.info(f"[Pipeline] {len(documents)}개 문서 처리 중")

        # 오케스트레이터에게 작업을 맡김
        orchestrator = get_orchestrator()
        prd = await orchestrator.process(job, documents)

        logger.info(f"[Pipeline] 파이프라인 완료. 결과: {prd.id if prd else '없음 (PM 검토 대기)'}")

        # 만약 prd가 None이면, 중간에 검토가 필요해서 멈춘 상태임
        # (상태 업데이트는 orchestrator 안에서 이미 수행됨)

    except Exception as e:
        # 에러 발생 시 로그 출력 및 상태 실패로 변경
        logger.error(f"[Pipeline] 에러 발생: {e}", exc_info=True)
        job.update_status(ProcessingStatus.FAILED)
        job.error_message = str(e)
        await storage.update_job(job)


@router.get("/status/{job_id}")
async def get_processing_status(job_id: str) -> dict:
    """
    현재 작업 진행 상태를 확인하는 API.
    
    반환 정보:
    - 현재 단계 (예: 파싱 중, 검증 중)
    - 진행률 (%)
    - 에러 메시지 (있을 경우)
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
    """진행 중인 작업을 취소하는 API"""
    storage = get_file_storage()
    job = await storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    # 이미 끝난 작업은 취소 불가
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
    """전체 작업 목록 조회 API"""
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