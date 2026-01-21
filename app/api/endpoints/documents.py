"""Document upload and management endpoints."""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from app.models import InputDocument, InputType, ParsedContent, InputMetadata
from app.services import get_file_storage

router = APIRouter()


# File extension to InputType mapping
EXTENSION_MAP = {
    ".txt": InputType.TEXT,
    ".md": InputType.TEXT,
    ".eml": InputType.EMAIL,
    ".msg": InputType.EMAIL,
    ".xlsx": InputType.EXCEL,
    ".xls": InputType.EXCEL,
    ".csv": InputType.CSV,
    ".pptx": InputType.POWERPOINT,
    ".ppt": InputType.POWERPOINT,
    ".png": InputType.IMAGE,
    ".jpg": InputType.IMAGE,
    ".jpeg": InputType.IMAGE,
    ".gif": InputType.IMAGE,
    ".pdf": InputType.DOCUMENT,
    ".docx": InputType.DOCUMENT,
    ".doc": InputType.DOCUMENT,
}


def detect_input_type(filename: str) -> InputType:
    """Detect input type from filename extension."""
    ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
    return EXTENSION_MAP.get(ext, InputType.TEXT)


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
) -> dict:
    """
    Upload one or more documents for PRD generation.

    Supports: txt, md, eml, xlsx, csv, pptx, png, jpg, pdf, docx
    """
    storage = get_file_storage()
    uploaded_documents = []

    for file in files:
        # Generate document ID
        doc_id = str(uuid.uuid4())[:8]

        # Read file content
        content = await file.read()

        # Save file to storage
        file_path = await storage.save_upload(content, file.filename, doc_id)

        # Detect input type
        input_type = detect_input_type(file.filename)

        # Create input document (content will be parsed later)
        input_doc = InputDocument(
            id=doc_id,
            input_type=input_type,
            content=ParsedContent(
                raw_text="",  # Will be filled during parsing
                metadata=InputMetadata(filename=file.filename),
            ),
            source_path=file_path,
        )

        # Save document metadata
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
    """Get document details by ID."""
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
    """Delete an uploaded document."""
    storage = get_file_storage()

    # Delete upload files
    deleted = await storage.delete_upload(document_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return {"message": "문서가 삭제되었습니다", "id": document_id}


@router.get("")
async def list_documents(skip: int = 0, limit: int = 20) -> dict:
    """List all uploaded documents."""
    storage = get_file_storage()

    # List document directories
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

    # Sort by upload time (newest first) and paginate
    docs.sort(key=lambda x: x["uploaded_at"], reverse=True)

    return {
        "total": len(docs),
        "documents": docs[skip:skip + limit],
    }
