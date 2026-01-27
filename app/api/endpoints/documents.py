"""
문서 업로드 및 관리 API입니다.
사용자가 PRD 생성을 위해 업로드한 파일들을 저장하고 목록을 보여줍니다.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from app.models import InputDocument, InputType, ParsedContent, InputMetadata
from app.services import get_file_storage

router = APIRouter()


# 파일 확장자에 따라 문서 종류를 자동으로 분류하기 위한 맵
EXTENSION_MAP = {
    ".txt": InputType.TEXT,
    ".md": InputType.TEXT,
    ".eml": InputType.EMAIL,  # 이메일
    ".msg": InputType.EMAIL,
    ".xlsx": InputType.EXCEL, # 엑셀
    ".xls": InputType.EXCEL,
    ".csv": InputType.CSV,
    ".pptx": InputType.POWERPOINT, # 파워포인트
    ".ppt": InputType.POWERPOINT,
    ".png": InputType.IMAGE,  # 이미지
    ".jpg": InputType.IMAGE,
    ".jpeg": InputType.IMAGE,
    ".gif": InputType.IMAGE,
    ".pdf": InputType.DOCUMENT, # 일반 문서
    ".docx": InputType.DOCUMENT,
    ".doc": InputType.DOCUMENT,
}


def detect_input_type(filename: str) -> InputType:
    """파일 이름(확장자)을 보고 문서 종류를 판단하는 함수"""
    ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
    return EXTENSION_MAP.get(ext, InputType.TEXT)


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
) -> dict:
    """
    파일 업로드 API.
    한 번에 여러 개의 파일을 업로드할 수 있습니다.
    
    지원 형식: 텍스트(txt, md), 엑셀(xlsx, csv), 파워포인트(pptx), 이미지(png, jpg), 워드(docx) 등
    """
    storage = get_file_storage()
    uploaded_documents = []

    for file in files:
        # 파일별로 고유 ID 생성 (UUID의 앞 8자리만 사용)
        doc_id = str(uuid.uuid4())[:8]

        # 파일 내용을 읽음
        content = await file.read()

        # 저장소(FileStorage)에 파일 저장
        file_path = await storage.save_upload(content, file.filename, doc_id)

        # 문서 종류 판단
        input_type = detect_input_type(file.filename)

        # 입력 문서 정보 생성 (내용 파싱은 나중에 함)
        input_doc = InputDocument(
            id=doc_id,
            input_type=input_type,
            content=ParsedContent(
                raw_text="",  # 파싱 전이라 아직 비어있음
                metadata=InputMetadata(filename=file.filename),
            ),
            source_path=file_path,
        )

        # 메타데이터 저장
        await storage.save_input_document(input_doc)

        uploaded_documents.append({
            "id": doc_id,
            "filename": file.filename,
            "input_type": input_type.value,
            "size_bytes": len(content),
        })

    return {
        "message": f"{len(uploaded_documents)}개 파일 업로드 완료",
        "documents": uploaded_documents,
    }


@router.get("/{document_id}")
async def get_document(document_id: str) -> dict:
    """특정 문서의 상세 정보를 조회하는 API"""
    storage = get_file_storage()
    doc = await storage.get_input_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return {
        "id": doc.id,
        "input_type": doc.input_type.value,
        "filename": doc.content.metadata.filename,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict:
    """업로드된 문서를 삭제하는 API"""
    storage = get_file_storage()

    # 파일과 정보 모두 삭제
    deleted = await storage.delete_upload(document_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return {"message": "문서가 삭제되었습니다", "id": document_id}


@router.get("")
async def list_documents(skip: int = 0, limit: int = 20) -> dict:
    """전체 업로드 문서 목록을 조회하는 API (페이지네이션 지원)"""
    storage = get_file_storage()

    # 폴더 목록을 읽어서 문서 정보 수집
    import os
    docs = []
    uploads_path = storage.uploads_path

    if uploads_path.exists():
        for doc_id in os.listdir(uploads_path):
            doc = await storage.get_input_document(doc_id)
            if doc:
                docs.append({
                    "id": doc.id,
                    "input_type": doc.input_type.value,
                    "filename": doc.content.metadata.filename,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                })

    # 최신 순으로 정렬하고 페이지 크기만큼 자르기
    docs.sort(key=lambda x: x["uploaded_at"], reverse=True)

    return {
        "total": len(docs),
        "documents": docs[skip:skip + limit],
    }