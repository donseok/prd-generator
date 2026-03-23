"""
워크스페이스 출력 문서 조회 API입니다.
/workspace/outputs/ 폴더에 저장된 CLI 생성 문서를 조회합니다.
"""

import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 워크스페이스 출력 폴더 경로
WORKSPACE_OUTPUTS_PATH = Path(__file__).parent.parent.parent.parent / "workspace" / "outputs"

# 문서 타입별 폴더 매핑
DOCUMENT_FOLDERS = {
    "prd": "PRD",
    "trd": "TRD",
    "wbs": "WBS",
    "proposals": "Proposal",
    "ppt": "PPT",
}

# doc_id에 허용되는 문자 패턴 (경로 탐색 방지)
SAFE_DOC_ID_PATTERN = re.compile(r'^[A-Za-z0-9가-힣_\-]+$')


def _validate_doc_id(doc_id: str) -> str:
    """doc_id 경로 탐색 방지 검증"""
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise HTTPException(status_code=400, detail=f"유효하지 않은 문서 ID입니다: {doc_id}")
    return doc_id


class OutputDocument(BaseModel):
    """출력 문서 정보"""
    id: str
    title: str
    doc_type: str  # PRD, TRD, WBS, Proposal, PPT
    file_path: str
    created_at: str
    has_json: bool
    has_md: bool
    has_pptx: bool


class OutputDocumentsResponse(BaseModel):
    """문서 목록 응답"""
    total: int
    documents: List[OutputDocument]


def parse_document_id_timestamp(doc_id: str) -> Optional[datetime]:
    """문서 ID에서 타임스탬프 추출 (예: PRD-20260206-093046)"""
    try:
        parts = doc_id.split("-")
        if len(parts) >= 3:
            date_str = parts[1]
            time_str = parts[2]
            return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
    except (ValueError, IndexError):
        pass
    return None


def scan_folder(folder_path: Path, doc_type: str) -> List[OutputDocument]:
    """폴더를 스캔하여 문서 목록 반환"""
    documents = []
    
    if not folder_path.exists():
        return documents
    
    # JSON 파일 먼저 스캔 (메타데이터 소스)
    json_files = {}
    md_files = set()
    pptx_files = set()
    
    for file_path in folder_path.iterdir():
        if file_path.name.startswith("."):
            continue
            
        stem = file_path.stem
        suffix = file_path.suffix.lower()
        
        if suffix == ".json":
            json_files[stem] = file_path
        elif suffix == ".md":
            md_files.add(stem)
        elif suffix == ".pptx":
            pptx_files.add(stem)
    
    # JSON 파일에서 문서 정보 추출
    for stem, json_path in json_files.items():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 파일명(stem)을 ID로 사용 (파일 검색에 사용되므로 일관성 유지)
            doc_id = stem
            title = data.get("title", stem)
            
            # 타임스탬프 추출
            created_at = None
            if "metadata" in data and "created_at" in data["metadata"]:
                created_at = data["metadata"]["created_at"]
            elif "created_at" in data:
                created_at = data["created_at"]
            else:
                ts = parse_document_id_timestamp(doc_id)
                if ts:
                    created_at = ts.isoformat()
                else:
                    # 파일 수정 시간 사용
                    created_at = datetime.fromtimestamp(json_path.stat().st_mtime).isoformat()
            
            documents.append(OutputDocument(
                id=doc_id,
                title=title,
                doc_type=doc_type,
                file_path=str(json_path),
                created_at=created_at,
                has_json=True,
                has_md=stem in md_files,
                has_pptx=stem in pptx_files,
            ))
            
        except Exception as e:
            logger.warning(f"Failed to parse {json_path}: {e}")
            continue
    
    # JSON 없이 MD만 있는 경우도 처리
    for stem in md_files:
        if stem not in json_files:
            md_path = folder_path / f"{stem}.md"
            ts = parse_document_id_timestamp(stem)
            created_at = ts.isoformat() if ts else datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
            
            documents.append(OutputDocument(
                id=stem,
                title=stem,
                doc_type=doc_type,
                file_path=str(md_path),
                created_at=created_at,
                has_json=False,
                has_md=True,
                has_pptx=stem in pptx_files,
            ))
    
    # PPTX만 있는 경우도 처리
    for stem in pptx_files:
        if stem not in json_files and stem not in md_files:
            pptx_path = folder_path / f"{stem}.pptx"
            ts = parse_document_id_timestamp(stem)
            created_at = ts.isoformat() if ts else datetime.fromtimestamp(pptx_path.stat().st_mtime).isoformat()
            
            documents.append(OutputDocument(
                id=stem,
                title=stem,
                doc_type=doc_type,
                file_path=str(pptx_path),
                created_at=created_at,
                has_json=False,
                has_md=False,
                has_pptx=True,
            ))
    
    return documents


@router.get("/documents", response_model=OutputDocumentsResponse)
async def list_output_documents(
    doc_type: Optional[str] = None,
    limit: int = 50,
) -> OutputDocumentsResponse:
    """
    워크스페이스 출력 폴더의 문서 목록을 반환합니다.
    
    - doc_type: 특정 문서 타입만 필터링 (prd, trd, wbs, proposals, ppt)
    - limit: 반환할 최대 문서 수
    """
    all_documents = []
    
    # 지정된 타입만 또는 전체 스캔
    folders_to_scan = {}
    if doc_type and doc_type.lower() in DOCUMENT_FOLDERS:
        folders_to_scan[doc_type.lower()] = DOCUMENT_FOLDERS[doc_type.lower()]
    else:
        folders_to_scan = DOCUMENT_FOLDERS
    
    for folder_name, doc_type_label in folders_to_scan.items():
        folder_path = WORKSPACE_OUTPUTS_PATH / folder_name
        documents = scan_folder(folder_path, doc_type_label)
        all_documents.extend(documents)
    
    # 날짜순 정렬 (최신순)
    all_documents.sort(key=lambda d: d.created_at, reverse=True)
    
    # 제한 적용
    limited_documents = all_documents[:limit]
    
    return OutputDocumentsResponse(
        total=len(all_documents),
        documents=limited_documents,
    )


class DeleteAllResponse(BaseModel):
    """문서 삭제 응답"""
    success: bool
    message: str
    deleted_count: int
    details: dict


class OpenPptxResponse(BaseModel):
    """PPTX 파일 열기 응답"""
    success: bool
    message: str
    file_path: str


# 주의: DELETE /documents/all은 GET /documents/{doc_id}보다 먼저 등록해야 합니다.
# FastAPI는 등록 순서대로 라우트를 매칭하므로, {doc_id}가 "all"을 캡처하는 것을 방지합니다.
@router.delete("/documents/all", response_model=DeleteAllResponse)
async def delete_all_documents() -> DeleteAllResponse:
    """
    모든 생성된 문서를 삭제합니다.
    workspace/outputs/ 폴더 내의 모든 문서를 삭제합니다.
    .gitkeep 파일은 보존됩니다.
    """
    folders = ["prd", "trd", "wbs", "proposals", "ppt", "doc", "diagrams", "agent-team"]
    total_deleted = 0
    details = {}

    for folder_name in folders:
        folder_path = WORKSPACE_OUTPUTS_PATH / folder_name
        deleted_in_folder = 0

        if not folder_path.exists():
            details[folder_name] = 0
            continue

        for file_path in folder_path.iterdir():
            # .gitkeep 파일과 숨김 파일은 제외
            if file_path.name == ".gitkeep" or file_path.name.startswith("."):
                continue

            if file_path.is_file():
                try:
                    os.remove(file_path)
                    deleted_in_folder += 1
                    logger.info(f"삭제됨: {file_path}")
                except Exception as e:
                    logger.error(f"삭제 실패: {file_path} - {e}")

        details[folder_name] = deleted_in_folder
        total_deleted += deleted_in_folder

    return DeleteAllResponse(
        success=True,
        message=f"총 {total_deleted}개 파일이 삭제되었습니다.",
        deleted_count=total_deleted,
        details=details,
    )


@router.get("/documents/{doc_id}")
async def get_output_document(doc_id: str, format: Optional[str] = None) -> dict:
    """
    특정 문서의 상세 내용을 반환합니다.

    - format: 'json' 또는 'md'를 지정하면 해당 형식만 반환
    """
    _validate_doc_id(doc_id)

    # 모든 폴더에서 문서 검색
    for folder_name, doc_type_label in DOCUMENT_FOLDERS.items():
        folder_path = WORKSPACE_OUTPUTS_PATH / folder_name

        if not folder_path.exists():
            continue

        json_path = folder_path / f"{doc_id}.json"
        md_path = folder_path / f"{doc_id}.md"

        json_exists = json_path.exists()
        md_exists = md_path.exists()

        if not json_exists and not md_exists:
            continue

        result = {
            "id": doc_id,
            "doc_type": doc_type_label,
        }

        # format이 지정된 경우 해당 형식만 반환
        if format == "json":
            if json_exists:
                with open(json_path, "r", encoding="utf-8") as f:
                    result["content_json"] = json.load(f)
                return result
            else:
                raise HTTPException(status_code=404, detail=f"JSON 파일이 없습니다: {doc_id}")

        elif format == "md":
            if md_exists:
                with open(md_path, "r", encoding="utf-8") as f:
                    result["content_md"] = f.read()
                return result
            else:
                raise HTTPException(status_code=404, detail=f"Markdown 파일이 없습니다: {doc_id}")

        # format이 없으면 둘 다 반환
        if json_exists:
            with open(json_path, "r", encoding="utf-8") as f:
                result["content_json"] = json.load(f)

        if md_exists:
            with open(md_path, "r", encoding="utf-8") as f:
                result["content_md"] = f.read()

        return result

    raise HTTPException(status_code=404, detail=f"문서를 찾을 수 없습니다: {doc_id}")


@router.post("/documents/{doc_id}/open-pptx", response_model=OpenPptxResponse)
async def open_pptx_file(doc_id: str) -> OpenPptxResponse:
    """
    PPTX 파일을 시스템 기본 프로그램(PowerPoint)으로 엽니다.

    - doc_id: 문서 ID
    """
    import subprocess
    import platform

    _validate_doc_id(doc_id)

    # 모든 폴더에서 PPTX 파일 검색
    for folder_name in DOCUMENT_FOLDERS.keys():
        folder_path = WORKSPACE_OUTPUTS_PATH / folder_name

        if not folder_path.exists():
            continue

        pptx_path = folder_path / f"{doc_id}.pptx"

        if pptx_path.exists():
            # 경로가 워크스페이스 내에 있는지 최종 확인
            resolved = pptx_path.resolve()
            if not str(resolved).startswith(str(WORKSPACE_OUTPUTS_PATH.resolve())):
                raise HTTPException(status_code=400, detail="유효하지 않은 문서 ID입니다")

            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(resolved))
                elif system == "Darwin":
                    subprocess.Popen(["open", str(resolved)])
                else:
                    subprocess.Popen(["xdg-open", str(resolved)])

                logger.info(f"PPTX 파일 열기: {resolved}")
                return OpenPptxResponse(
                    success=True,
                    message=f"PPTX 파일을 열었습니다: {pptx_path.name}",
                    file_path=str(pptx_path.name)
                )
            except Exception as e:
                logger.error(f"PPTX 파일 열기 실패: {pptx_path} - {e}")
                raise HTTPException(status_code=500, detail=f"PPTX 파일을 열 수 없습니다: {str(e)}")

    raise HTTPException(status_code=404, detail=f"PPTX 파일을 찾을 수 없습니다: {doc_id}")
