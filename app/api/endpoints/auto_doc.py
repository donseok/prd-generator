"""
Auto-Doc 문서 생성 API입니다.
로컬 폴더의 파일을 읽어 PRD, TRD, WBS, 제안서, PPT 5종 문서를 생성합니다.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# PYTHONPATH 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)

router = APIRouter()

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUTS_PATH = PROJECT_ROOT / "workspace" / "inputs" / "projects"
OUTPUTS_PATH = PROJECT_ROOT / "workspace" / "outputs"


class InputFile(BaseModel):
    """입력 파일 정보"""
    name: str
    path: str
    size: int
    extension: str


class InputFilesResponse(BaseModel):
    """입력 파일 목록 응답"""
    total: int
    folder_path: str
    files: List[InputFile]


class GenerateRequest(BaseModel):
    """문서 생성 요청"""
    doc_types: List[str] = ["prd", "trd", "wbs", "proposal", "ppt"]


class GenerateResponse(BaseModel):
    """문서 생성 응답"""
    job_id: str
    status: str
    message: str
    doc_types: List[str]


# 생성 작업 상태 저장 (간단한 인메모리 저장)
generation_jobs = {}


@router.get("/inputs", response_model=InputFilesResponse)
async def list_input_files() -> InputFilesResponse:
    """
    workspace/inputs/projects 폴더의 파일 목록을 반환합니다.
    """
    files = []
    
    if INPUTS_PATH.exists():
        for file_path in INPUTS_PATH.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                files.append(InputFile(
                    name=file_path.name,
                    path=str(file_path),
                    size=file_path.stat().st_size,
                    extension=file_path.suffix.lower(),
                ))
    
    # 이름순 정렬
    files.sort(key=lambda f: f.name)
    
    return InputFilesResponse(
        total=len(files),
        folder_path=str(INPUTS_PATH),
        files=files,
    )


async def run_generation(job_id: str, doc_types: List[str]):
    """백그라운드에서 DocumentOrchestrator를 사용하여 5종 문서 생성 실행"""
    from app.services.document_orchestrator import DocumentOrchestrator

    try:
        generation_jobs[job_id]["status"] = "processing"
        generation_jobs[job_id]["started_at"] = datetime.now().isoformat()

        def on_step(step_name: str, current: int, total: int):
            """단계별 진행 상황을 job 상태에 업데이트"""
            generation_jobs[job_id]["current_step"] = step_name
            generation_jobs[job_id]["current_step_number"] = current
            generation_jobs[job_id]["total_steps"] = total

        orchestrator = DocumentOrchestrator(
            input_dir=INPUTS_PATH,
            output_base_dir=OUTPUTS_PATH,
        )

        bundle = await orchestrator.generate_all(
            verbose=True,
            on_step=on_step,
        )

        # 결과 정리
        results = []
        if bundle.prd_path:
            results.append({"type": "prd", "path": str(bundle.prd_path)})
        if bundle.trd_path:
            results.append({"type": "trd", "path": str(bundle.trd_path)})
        if bundle.wbs_path:
            results.append({"type": "wbs", "path": str(bundle.wbs_path)})
        if bundle.proposal_path:
            results.append({"type": "proposal", "path": str(bundle.proposal_path)})
        if bundle.ppt_path:
            results.append({"type": "ppt", "path": str(bundle.ppt_path)})

        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["results"] = results
        generation_jobs[job_id]["errors"] = bundle.errors
        generation_jobs[job_id]["total_time_seconds"] = bundle.total_time_seconds
        generation_jobs[job_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        logger.error(f"문서 생성 실패: {e}")
        generation_jobs[job_id]["status"] = "failed"
        generation_jobs[job_id]["error"] = str(e)


@router.post("/generate", response_model=GenerateResponse)
async def generate_documents(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    """
    문서 생성을 시작합니다.
    백그라운드에서 비동기로 실행되며, job_id로 상태를 조회할 수 있습니다.
    """
    # 입력 파일 확인
    if not INPUTS_PATH.exists():
        raise HTTPException(status_code=400, detail="입력 폴더가 존재하지 않습니다")
    
    files = [f for f in INPUTS_PATH.iterdir() if f.is_file() and not f.name.startswith('.')]
    if not files:
        raise HTTPException(status_code=400, detail="입력 폴더에 파일이 없습니다. workspace/inputs/projects/에 요구사항 파일을 배치해주세요.")
    
    # 지원하는 문서 타입 확인
    valid_types = ["prd", "trd", "wbs", "proposal", "ppt"]
    for doc_type in request.doc_types:
        if doc_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 문서 타입: {doc_type}")
    
    # 작업 ID 생성
    job_id = f"auto-doc-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 작업 상태 저장
    generation_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "doc_types": request.doc_types,
        "created_at": datetime.now().isoformat(),
        "input_files": len(files),
    }
    
    # 백그라운드 작업 시작
    background_tasks.add_task(run_generation, job_id, request.doc_types)
    
    return GenerateResponse(
        job_id=job_id,
        status="started",
        message=f"문서 생성이 시작되었습니다. {len(files)}개의 입력 파일을 처리합니다.",
        doc_types=request.doc_types,
    )


@router.get("/status/{job_id}")
async def get_generation_status(job_id: str) -> dict:
    """
    문서 생성 작업의 상태를 조회합니다.
    """
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    return generation_jobs[job_id]
