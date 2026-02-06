"""
Auto-Doc 문서 생성 API입니다.
로컬 폴더의 파일을 읽어 PRD, TRD, WBS, 제안서를 생성합니다.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
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
    doc_types: List[str] = ["prd"]  # prd, trd, wbs, proposal


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


async def run_prd_maker():
    """PRD 생성 스크립트 실행"""
    from app.models import InputType
    from app.services.claude_client import get_claude_client
    from app.layers.layer1_parsing import ParserFactory
    from app.layers.layer2_normalization import Normalizer
    from app.layers.layer3_validation import Validator
    from app.layers.layer4_generation import PRDGenerator
    
    logger.info("PRD 생성 시작")
    
    input_dir = INPUTS_PATH
    output_dir = OUTPUTS_PATH / "prd"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일 수집
    files = [f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    files = sorted(files, key=lambda x: x.name)
    
    if not files:
        raise Exception("입력 파일이 없습니다")
    
    client = get_claude_client()
    factory = ParserFactory(client)
    normalizer = Normalizer(client)
    validator = Validator(client)
    generator = PRDGenerator(client)
    
    # Layer 1: 파싱
    def get_input_type(file_path: Path):
        from app.models import InputType
        suffix = file_path.suffix.lower()
        type_map = {
            '.txt': InputType.TEXT, '.md': InputType.TEXT, '.json': InputType.TEXT,
            '.csv': InputType.CSV, '.xlsx': InputType.EXCEL, '.xls': InputType.EXCEL,
            '.pptx': InputType.POWERPOINT, '.ppt': InputType.POWERPOINT,
            '.docx': InputType.DOCUMENT, '.doc': InputType.DOCUMENT,
            '.png': InputType.IMAGE, '.jpg': InputType.IMAGE, '.jpeg': InputType.IMAGE,
        }
        return type_map.get(suffix, InputType.TEXT)
    
    parsed_contents = []
    document_ids = []
    
    for i, file_path in enumerate(files, 1):
        input_type = get_input_type(file_path)
        try:
            parser = factory.get_parser(input_type)
            parsed = await parser.parse(file_path)
            parsed_contents.append(parsed)
            document_ids.append(f'doc-{i:03d}')
        except Exception as e:
            logger.warning(f"파일 파싱 실패: {file_path.name} - {e}")
    
    if not parsed_contents:
        raise Exception("파싱된 콘텐츠가 없습니다")
    
    # Layer 2-4: 정규화 → 검증 → 생성
    requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
    validated, review_items = await validator.validate(requirements, job_id='auto-doc')
    source_docs = [f.name for f in files]
    prd = await generator.generate(validated or requirements, source_documents=source_docs)
    
    # 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'PRD-{timestamp}.md'
    md_path.write_text(prd.to_markdown(), encoding='utf-8')
    
    json_path = output_dir / f'PRD-{timestamp}.json'
    json_path.write_text(prd.to_json(), encoding='utf-8')
    
    logger.info(f"PRD 생성 완료: {prd.id}")
    return prd.id


async def run_generation(job_id: str, doc_types: List[str]):
    """백그라운드에서 문서 생성 실행"""
    try:
        generation_jobs[job_id]["status"] = "processing"
        generation_jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        results = []
        
        for doc_type in doc_types:
            generation_jobs[job_id]["current_step"] = doc_type
            
            if doc_type == "prd":
                prd_id = await run_prd_maker()
                results.append({"type": "prd", "id": prd_id})
            # trd, wbs, proposal은 추후 구현 가능
            
        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["results"] = results
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
    valid_types = ["prd", "trd", "wbs", "proposal"]
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
