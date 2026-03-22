"""
프로젝트 관리 API입니다.
프로젝트 CRUD 및 프로젝트에 속한 문서 관리 기능을 제공합니다.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.project import Project, DocumentReference
from app.services import get_file_storage

router = APIRouter()


# ==================== 요청/응답 모델 ====================


class ProjectCreateRequest(BaseModel):
    """프로젝트 생성 요청"""

    name: str = Field(..., description="프로젝트 이름", min_length=1, max_length=200)
    description: str = Field(default="", description="프로젝트 설명")
    tags: list[str] = Field(default_factory=list, description="프로젝트 태그")


class ProjectUpdateRequest(BaseModel):
    """프로젝트 수정 요청"""

    name: Optional[str] = Field(default=None, description="프로젝트 이름", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="프로젝트 설명")
    status: Optional[str] = Field(default=None, description="프로젝트 상태: active, archived, completed")
    tags: Optional[list[str]] = Field(default=None, description="프로젝트 태그")


class DocumentAddRequest(BaseModel):
    """프로젝트에 문서 추가 요청"""

    doc_id: str = Field(..., description="문서 ID")
    doc_type: str = Field(..., description="문서 타입: PRD, TRD, WBS, Proposal, PPT")
    title: str = Field(default="", description="문서 제목")
    source_doc_id: Optional[str] = Field(default=None, description="원본 문서 ID")


class ProjectSummaryResponse(BaseModel):
    """프로젝트 목록 조회 시 요약 정보"""

    id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str
    document_count: int
    tags: list[str]


class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답"""

    total: int
    projects: list[ProjectSummaryResponse]


class DocumentGroupResponse(BaseModel):
    """타입별로 그룹핑된 문서 목록 응답"""

    doc_type: str
    documents: list[dict]
    count: int


class ProjectDocumentsResponse(BaseModel):
    """프로젝트 문서 목록 응답"""

    project_id: str
    project_name: str
    total_documents: int
    groups: list[DocumentGroupResponse]


# ==================== 프로젝트 CRUD 엔드포인트 ====================

VALID_STATUSES = {"active", "archived", "completed"}
VALID_DOC_TYPES = {"PRD", "TRD", "WBS", "Proposal", "PPT"}


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(default=0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(default=20, ge=1, le=100, description="조회할 항목 수"),
    status: Optional[str] = Query(default=None, description="프로젝트 상태 필터"),
):
    """프로젝트 목록을 페이지 단위로 조회합니다."""
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 상태입니다. 허용값: {', '.join(VALID_STATUSES)}",
        )

    storage = get_file_storage()
    total = await storage.count_projects(status=status)
    projects = await storage.list_projects(skip=skip, limit=limit, status=status)

    return ProjectListResponse(
        total=total,
        projects=[
            ProjectSummaryResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                status=p.status,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
                document_count=len(p.documents),
                tags=p.tags,
            )
            for p in projects
        ],
    )


@router.post("", status_code=201)
async def create_project(request: ProjectCreateRequest) -> dict:
    """새 프로젝트를 생성합니다."""
    storage = get_file_storage()

    project = Project(
        name=request.name,
        description=request.description,
        tags=request.tags,
    )

    project_id = await storage.save_project(project)

    return {
        "message": "프로젝트가 생성되었습니다",
        "project": project.model_dump(),
    }


@router.get("/{project_id}")
async def get_project(project_id: str) -> dict:
    """ID로 프로젝트 상세 내용을 조회합니다."""
    storage = get_file_storage()
    project = await storage.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    return project.model_dump()


@router.put("/{project_id}")
async def update_project(project_id: str, request: ProjectUpdateRequest) -> dict:
    """프로젝트 정보를 수정합니다."""
    storage = get_file_storage()
    project = await storage.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # 요청에 포함된 필드만 업데이트
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    if request.status is not None:
        if request.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 상태입니다. 허용값: {', '.join(VALID_STATUSES)}",
            )
        project.status = request.status
    if request.tags is not None:
        project.tags = request.tags

    updated = await storage.update_project(project)

    if not updated:
        raise HTTPException(status_code=500, detail="프로젝트 업데이트에 실패했습니다")

    return {
        "message": "프로젝트가 수정되었습니다",
        "project": project.model_dump(),
    }


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> dict:
    """프로젝트를 삭제합니다."""
    storage = get_file_storage()

    # 존재 여부 확인
    project = await storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    deleted = await storage.delete_project(project_id)

    if not deleted:
        raise HTTPException(status_code=500, detail="프로젝트 삭제에 실패했습니다")

    return {"message": "프로젝트가 삭제되었습니다", "id": project_id}


# ==================== 프로젝트 문서 관리 엔드포인트 ====================


@router.post("/{project_id}/documents", status_code=201)
async def add_document_to_project(
    project_id: str, request: DocumentAddRequest
) -> dict:
    """프로젝트에 문서 참조를 추가합니다."""
    if request.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 문서 타입입니다. 허용값: {', '.join(VALID_DOC_TYPES)}",
        )

    storage = get_file_storage()
    project = await storage.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # 중복 확인
    for doc in project.documents:
        if doc.doc_id == request.doc_id and doc.doc_type == request.doc_type:
            raise HTTPException(
                status_code=409,
                detail="이미 프로젝트에 등록된 문서입니다",
            )

    project.add_document(
        doc_id=request.doc_id,
        doc_type=request.doc_type,
        title=request.title,
        source_doc_id=request.source_doc_id,
    )

    await storage.update_project(project)

    return {
        "message": "문서가 프로젝트에 추가되었습니다",
        "project_id": project_id,
        "document": {
            "doc_id": request.doc_id,
            "doc_type": request.doc_type,
            "title": request.title,
        },
    }


@router.delete("/{project_id}/documents/{doc_id}")
async def remove_document_from_project(project_id: str, doc_id: str) -> dict:
    """프로젝트에서 문서 참조를 제거합니다."""
    storage = get_file_storage()
    project = await storage.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # 문서 존재 여부 확인
    doc_exists = any(d.doc_id == doc_id for d in project.documents)
    if not doc_exists:
        raise HTTPException(
            status_code=404,
            detail="프로젝트에 해당 문서가 존재하지 않습니다",
        )

    project.remove_document(doc_id)
    await storage.update_project(project)

    return {
        "message": "문서가 프로젝트에서 제거되었습니다",
        "project_id": project_id,
        "doc_id": doc_id,
    }


@router.get("/{project_id}/documents", response_model=ProjectDocumentsResponse)
async def list_project_documents(project_id: str):
    """프로젝트에 속한 문서 목록을 타입별로 그룹핑하여 조회합니다."""
    storage = get_file_storage()
    project = await storage.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # 타입별로 문서를 그룹핑
    groups_dict: dict[str, list[dict]] = {}
    for doc in project.documents:
        if doc.doc_type not in groups_dict:
            groups_dict[doc.doc_type] = []
        groups_dict[doc.doc_type].append({
            "doc_id": doc.doc_id,
            "title": doc.title,
            "created_at": doc.created_at.isoformat(),
            "source_doc_id": doc.source_doc_id,
        })

    # 문서 타입 순서 정의 (파이프라인 순서)
    type_order = ["PRD", "TRD", "WBS", "Proposal", "PPT"]
    groups = []
    for doc_type in type_order:
        if doc_type in groups_dict:
            groups.append(
                DocumentGroupResponse(
                    doc_type=doc_type,
                    documents=groups_dict[doc_type],
                    count=len(groups_dict[doc_type]),
                )
            )
    # 정의된 순서에 없는 타입도 포함
    for doc_type, docs in groups_dict.items():
        if doc_type not in type_order:
            groups.append(
                DocumentGroupResponse(
                    doc_type=doc_type,
                    documents=docs,
                    count=len(docs),
                )
            )

    return ProjectDocumentsResponse(
        project_id=project.id,
        project_name=project.name,
        total_documents=len(project.documents),
        groups=groups,
    )
