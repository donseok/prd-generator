"""File-based storage service for PRD generation system."""

import json
import os
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar, Type
from pydantic import BaseModel

from app.models import PRDDocument, ProcessingJob, InputDocument


T = TypeVar("T", bound=BaseModel)


class FileStorage:
    """JSON file-based storage for PRDs, jobs, and uploads."""

    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.prd_path = self.base_path / "prd"
        self.jobs_path = self.base_path / "jobs"
        self.uploads_path = self.base_path / "uploads"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        for path in [self.prd_path, self.jobs_path, self.uploads_path]:
            path.mkdir(parents=True, exist_ok=True)

    # ==================== PRD Operations ====================

    async def save_prd(self, prd: PRDDocument) -> str:
        """Save PRD document to file."""
        file_path = self.prd_path / f"{prd.id}.json"
        await self._save_model(file_path, prd)
        return prd.id

    async def get_prd(self, prd_id: str) -> Optional[PRDDocument]:
        """Get PRD document by ID."""
        file_path = self.prd_path / f"{prd_id}.json"
        return await self._load_model(file_path, PRDDocument)

    async def list_prds(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> list[PRDDocument]:
        """List PRD documents with pagination."""
        prds = []
        files = sorted(
            self.prd_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for file_path in files:
            prd = await self._load_model(file_path, PRDDocument)
            if prd:
                if status is None or prd.metadata.status == status:
                    prds.append(prd)

        return prds[skip:skip + limit]

    async def delete_prd(self, prd_id: str) -> bool:
        """Delete PRD document."""
        file_path = self.prd_path / f"{prd_id}.json"
        return self._delete_file(file_path)

    async def update_prd(self, prd: PRDDocument) -> bool:
        """Update existing PRD document."""
        file_path = self.prd_path / f"{prd.id}.json"
        if not file_path.exists():
            return False
        prd.metadata.updated_at = datetime.now()
        await self._save_model(file_path, prd)
        return True

    # ==================== Job Operations ====================

    async def save_job(self, job: ProcessingJob) -> str:
        """Save processing job to file."""
        file_path = self.jobs_path / f"{job.job_id}.json"
        await self._save_model(file_path, job)
        return job.job_id

    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get processing job by ID."""
        file_path = self.jobs_path / f"{job_id}.json"
        return await self._load_model(file_path, ProcessingJob)

    async def update_job(self, job: ProcessingJob) -> bool:
        """Update existing processing job."""
        file_path = self.jobs_path / f"{job.job_id}.json"
        job.updated_at = datetime.now()
        await self._save_model(file_path, job)
        return True

    async def list_jobs(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> list[ProcessingJob]:
        """List processing jobs with pagination."""
        jobs = []
        files = sorted(
            self.jobs_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for file_path in files:
            job = await self._load_model(file_path, ProcessingJob)
            if job:
                if status is None or job.status.value == status:
                    jobs.append(job)

        return jobs[skip:skip + limit]

    async def delete_job(self, job_id: str) -> bool:
        """Delete processing job."""
        file_path = self.jobs_path / f"{job_id}.json"
        return self._delete_file(file_path)

    # ==================== Upload Operations ====================

    async def save_upload(
        self,
        file_content: bytes,
        filename: str,
        document_id: str
    ) -> str:
        """Save uploaded file and return path."""
        # Create document-specific directory
        doc_dir = self.uploads_path / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        file_path = doc_dir / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        return str(file_path)

    async def get_upload(self, document_id: str, filename: str) -> Optional[bytes]:
        """Get uploaded file content."""
        file_path = self.uploads_path / document_id / filename
        if not file_path.exists():
            return None

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_upload(self, document_id: str) -> bool:
        """Delete all uploaded files for a document."""
        doc_dir = self.uploads_path / document_id
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
            return True
        return False

    def get_upload_path(self, document_id: str, filename: str) -> Path:
        """Get path to uploaded file."""
        return self.uploads_path / document_id / filename

    # ==================== Input Document Operations ====================

    async def save_input_document(self, doc: InputDocument) -> str:
        """Save input document metadata."""
        doc_dir = self.uploads_path / doc.id
        doc_dir.mkdir(parents=True, exist_ok=True)
        file_path = doc_dir / "metadata.json"
        await self._save_model(file_path, doc)
        return doc.id

    async def get_input_document(self, document_id: str) -> Optional[InputDocument]:
        """Get input document by ID."""
        file_path = self.uploads_path / document_id / "metadata.json"
        return await self._load_model(file_path, InputDocument)

    # ==================== Helper Methods ====================

    async def _save_model(self, file_path: Path, model: BaseModel):
        """Save Pydantic model to JSON file."""
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(model.model_dump_json(indent=2))

    async def _load_model(self, file_path: Path, model_class: Type[T]) -> Optional[T]:
        """Load Pydantic model from JSON file."""
        if not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return model_class.model_validate_json(content)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def _delete_file(self, file_path: Path) -> bool:
        """Delete a file if it exists."""
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Singleton instance
_file_storage: Optional[FileStorage] = None


def get_file_storage() -> FileStorage:
    """Get or create file storage singleton."""
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorage()
    return _file_storage
