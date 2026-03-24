"""
Auto-Doc 문서 생성 API.
workspace/inputs/projects 폴더의 문서를 기반으로 선택한 생성기를 서버에서 실행한다.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

# 프로젝트 루트가 import path에 없을 수 있어 명시적으로 추가한다.
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUTS_PATH = PROJECT_ROOT / "workspace" / "inputs" / "projects"
OUTPUTS_PATH = PROJECT_ROOT / "workspace" / "outputs"
VALID_DOC_TYPES = ["prd", "trd", "wbs", "proposal", "ppt"]


class InputFile(BaseModel):
    name: str
    path: str
    size: int
    extension: str


class InputFilesResponse(BaseModel):
    total: int
    folder_path: str
    files: list[InputFile]


class GenerateRequest(BaseModel):
    doc_types: list[str] = Field(default_factory=lambda: VALID_DOC_TYPES.copy())


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str
    doc_types: list[str]


generation_jobs: dict[str, dict[str, Any]] = {}

_JOB_TTL_SECONDS = 3600  # 1시간


def _cleanup_old_jobs() -> None:
    """1시간 이상 된 작업 항목을 제거하여 메모리 누수를 방지합니다."""
    now = datetime.now()
    expired_ids = [
        job_id
        for job_id, job_data in generation_jobs.items()
        if (now - datetime.fromisoformat(job_data["created_at"])).total_seconds() > _JOB_TTL_SECONDS
    ]
    for job_id in expired_ids:
        del generation_jobs[job_id]
    if expired_ids:
        logger.info("만료된 작업 %d건 정리 완료", len(expired_ids))


@router.get("/inputs", response_model=InputFilesResponse)
async def list_input_files() -> InputFilesResponse:
    files: list[InputFile] = []

    if INPUTS_PATH.exists():
        for file_path in INPUTS_PATH.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                files.append(
                    InputFile(
                        name=file_path.name,
                        path=str(file_path),
                        size=file_path.stat().st_size,
                        extension=file_path.suffix.lower(),
                    )
                )

    files.sort(key=lambda item: item.name)

    return InputFilesResponse(total=len(files), folder_path=str(INPUTS_PATH), files=files)


def _bundle_results(bundle: Any, requested_doc_types: list[str]) -> list[dict[str, str]]:
    result_map = {
        "prd": getattr(bundle, "prd_path", None),
        "trd": getattr(bundle, "trd_path", None),
        "wbs": getattr(bundle, "wbs_path", None),
        "proposal": getattr(bundle, "proposal_path", None),
        "ppt": getattr(bundle, "ppt_path", None),
    }
    results: list[dict[str, str]] = []
    for doc_type in requested_doc_types:
        path = result_map.get(doc_type)
        if path:
          results.append({"type": doc_type, "path": str(path)})
    return results


async def run_generation(job_id: str, doc_types: list[str]) -> None:
    from app.services.document_orchestrator import DocumentOrchestrator

    try:
        generation_jobs[job_id]["status"] = "processing"
        generation_jobs[job_id]["started_at"] = datetime.now().isoformat()

        def on_step(step_name: str, current: int, total: int) -> None:
            generation_jobs[job_id]["current_step"] = step_name
            generation_jobs[job_id]["current_step_number"] = current
            generation_jobs[job_id]["total_steps"] = total
            generation_jobs[job_id]["progress_percent"] = round((current / max(total, 1)) * 100)

        orchestrator = DocumentOrchestrator(input_dir=INPUTS_PATH, output_base_dir=OUTPUTS_PATH)
        bundle = await orchestrator.generate_selected(doc_types=doc_types, verbose=True, on_step=on_step)

        generation_jobs[job_id]["status"] = "completed" if not bundle.errors else "completed_with_errors"
        generation_jobs[job_id]["results"] = _bundle_results(bundle, doc_types)
        generation_jobs[job_id]["errors"] = bundle.errors
        generation_jobs[job_id]["total_time_seconds"] = bundle.total_time_seconds
        generation_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        generation_jobs[job_id]["progress_percent"] = 100
    except Exception as exc:  # pragma: no cover - defensive path
        logger.error("문서 생성 실패: %s", exc, exc_info=True)
        generation_jobs[job_id]["status"] = "failed"
        generation_jobs[job_id]["error"] = str(exc)
        generation_jobs[job_id]["completed_at"] = datetime.now().isoformat()


@router.post("/generate", response_model=GenerateResponse)
async def generate_documents(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    if not INPUTS_PATH.exists():
        raise HTTPException(status_code=400, detail="입력 폴더가 존재하지 않습니다.")

    files = [path for path in INPUTS_PATH.iterdir() if path.is_file() and not path.name.startswith(".")]
    if not files:
        raise HTTPException(
            status_code=400,
            detail="입력 폴더에 파일이 없습니다. workspace/inputs/projects 에 문서를 먼저 넣어 주세요.",
        )

    requested = request.doc_types or VALID_DOC_TYPES.copy()
    if not requested:
        raise HTTPException(status_code=400, detail="doc_types must not be empty")
    invalid = [doc_type for doc_type in requested if doc_type not in VALID_DOC_TYPES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 문서 타입입니다: {', '.join(invalid)}")

    _cleanup_old_jobs()

    job_id = f"auto-doc-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    generation_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "doc_types": requested,
        "created_at": datetime.now().isoformat(),
        "input_files": len(files),
        "current_step": None,
        "current_step_number": 0,
        "total_steps": len(requested),
        "progress_percent": 0,
        "results": [],
        "errors": [],
    }

    background_tasks.add_task(run_generation, job_id, requested)

    return GenerateResponse(
        job_id=job_id,
        status="started",
        message=f"문서 생성 작업을 시작했습니다. 입력 파일 {len(files)}개를 기준으로 처리합니다.",
        doc_types=requested,
    )


@router.get("/status/{job_id}")
async def get_generation_status(job_id: str) -> dict[str, Any]:
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return generation_jobs[job_id]
