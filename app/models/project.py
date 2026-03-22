"""
프로젝트 모델입니다.
여러 문서(PRD, TRD, WBS, 제안서, PPT)를 하나의 프로젝트로 묶어 관리합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
import uuid


class DocumentReference(BaseModel):
    """프로젝트에 속한 문서 참조 정보"""

    doc_id: str = Field(..., description="문서 ID (파일명 또는 UUID)")
    doc_type: str = Field(..., description="문서 타입: PRD, TRD, WBS, Proposal, PPT")
    title: str = Field(default="", description="문서 제목")
    created_at: datetime = Field(default_factory=datetime.now)
    source_doc_id: Optional[str] = Field(
        default=None, description="이 문서의 원본 문서 ID (예: TRD의 원본 PRD)"
    )


class Project(BaseModel):
    """프로젝트 모델 - 관련 문서들을 하나로 묶는 컨테이너"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., description="프로젝트 이름")
    description: str = Field(default="", description="프로젝트 설명")
    status: str = Field(
        default="active", description="프로젝트 상태: active, archived, completed"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    documents: list[DocumentReference] = Field(
        default_factory=list, description="프로젝트에 속한 문서 목록"
    )
    tags: list[str] = Field(default_factory=list, description="프로젝트 태그")

    def add_document(
        self,
        doc_id: str,
        doc_type: str,
        title: str = "",
        source_doc_id: Optional[str] = None,
    ):
        """프로젝트에 문서를 추가합니다."""
        # 중복 방지
        for doc in self.documents:
            if doc.doc_id == doc_id and doc.doc_type == doc_type:
                return
        self.documents.append(
            DocumentReference(
                doc_id=doc_id,
                doc_type=doc_type,
                title=title,
                source_doc_id=source_doc_id,
            )
        )
        self.updated_at = datetime.now()

    def remove_document(self, doc_id: str):
        """프로젝트에서 문서를 제거합니다."""
        self.documents = [d for d in self.documents if d.doc_id != doc_id]
        self.updated_at = datetime.now()

    def get_documents_by_type(self, doc_type: str) -> list[DocumentReference]:
        """타입별 문서 목록을 반환합니다."""
        return [d for d in self.documents if d.doc_type == doc_type]

    def get_latest_document(self, doc_type: str) -> Optional[DocumentReference]:
        """특정 타입의 최신 문서를 반환합니다."""
        docs = self.get_documents_by_type(doc_type)
        if not docs:
            return None
        return max(docs, key=lambda d: d.created_at)
