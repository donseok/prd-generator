"""FileStorage unit tests.

Tests all CRUD operations for PRD documents, processing jobs,
uploads, and input documents using a temporary directory.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.file_storage import FileStorage
from app.models import (
    PRDDocument,
    PRDOverview,
    PRDMetadata,
    ProcessingJob,
    ProcessingStatus,
    InputDocument,
    InputType,
    ParsedContent,
    InputMetadata,
)
from app.exceptions import StorageError


def _make_prd(prd_id: str = "PRD-20240101-abcd") -> PRDDocument:
    """Helper to create a minimal PRDDocument."""
    return PRDDocument(
        id=prd_id,
        title="Test PRD",
        overview=PRDOverview(
            background="Test background",
            goals=["Goal 1"],
            scope="Test scope",
        ),
        metadata=PRDMetadata(
            version="1.0",
            status="draft",
            overall_confidence=0.85,
        ),
    )


def _make_job(job_id: str = "test-job-001") -> ProcessingJob:
    """Helper to create a minimal ProcessingJob."""
    return ProcessingJob(
        job_id=job_id,
        status=ProcessingStatus.PENDING,
        input_document_ids=["doc-001"],
        input_filenames=["test.txt"],
    )


def _make_input_document(doc_id: str = "doc-001") -> InputDocument:
    """Helper to create a minimal InputDocument."""
    return InputDocument(
        id=doc_id,
        input_type=InputType.TEXT,
        content=ParsedContent(
            raw_text="Sample input text",
            metadata=InputMetadata(filename="test.txt"),
        ),
    )


# ===================================================================
# PRD CRUD tests
# ===================================================================

class TestPRDStorage:
    @pytest.mark.asyncio
    async def test_save_and_get_prd_roundtrip(self, temp_storage):
        """Save a PRD, then retrieve it and verify fields match."""
        prd = _make_prd("PRD-roundtrip-001")
        saved_id = await temp_storage.save_prd(prd)
        assert saved_id == "PRD-roundtrip-001"

        loaded = await temp_storage.get_prd("PRD-roundtrip-001")
        assert loaded is not None
        assert loaded.id == prd.id
        assert loaded.title == prd.title
        assert loaded.overview.background == prd.overview.background

    @pytest.mark.asyncio
    async def test_get_prd_returns_none_for_nonexistent(self, temp_storage):
        result = await temp_storage.get_prd("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_prds_returns_saved_prds(self, temp_storage):
        await temp_storage.save_prd(_make_prd("PRD-list-001"))
        await temp_storage.save_prd(_make_prd("PRD-list-002"))

        prds = await temp_storage.list_prds()
        assert len(prds) == 2
        prd_ids = {p.id for p in prds}
        assert "PRD-list-001" in prd_ids
        assert "PRD-list-002" in prd_ids

    @pytest.mark.asyncio
    async def test_delete_prd_removes_file(self, temp_storage):
        await temp_storage.save_prd(_make_prd("PRD-delete-001"))
        result = await temp_storage.delete_prd("PRD-delete-001")
        assert result is True

        loaded = await temp_storage.get_prd("PRD-delete-001")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_prd_returns_false(self, temp_storage):
        result = await temp_storage.delete_prd("nonexistent")
        assert result is False


# ===================================================================
# Job CRUD tests
# ===================================================================

class TestJobStorage:
    @pytest.mark.asyncio
    async def test_save_and_get_job_roundtrip(self, temp_storage):
        job = _make_job("job-roundtrip-001")
        saved_id = await temp_storage.save_job(job)
        assert saved_id == "job-roundtrip-001"

        loaded = await temp_storage.get_job("job-roundtrip-001")
        assert loaded is not None
        assert loaded.job_id == job.job_id
        assert loaded.status == ProcessingStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_job_returns_none_for_nonexistent(self, temp_storage):
        result = await temp_storage.get_job("nonexistent-job")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_job_updates_timestamp(self, temp_storage):
        job = _make_job("job-update-001")
        await temp_storage.save_job(job)

        original_time = job.updated_at
        result = await temp_storage.update_job(job)
        assert result is True

        loaded = await temp_storage.get_job("job-update-001")
        assert loaded is not None
        # updated_at should be at least as recent as the original
        assert loaded.updated_at >= original_time

    @pytest.mark.asyncio
    async def test_list_jobs_returns_saved_jobs(self, temp_storage):
        await temp_storage.save_job(_make_job("job-list-001"))
        await temp_storage.save_job(_make_job("job-list-002"))

        jobs = await temp_storage.list_jobs()
        assert len(jobs) == 2
        job_ids = {j.job_id for j in jobs}
        assert "job-list-001" in job_ids
        assert "job-list-002" in job_ids


# ===================================================================
# Upload CRUD tests
# ===================================================================

class TestUploadStorage:
    @pytest.mark.asyncio
    async def test_save_and_get_upload_roundtrip(self, temp_storage):
        content = b"Hello, this is test content"
        path = await temp_storage.save_upload(content, "test.txt", "upload-doc-001")
        assert "test.txt" in path

        loaded = await temp_storage.get_upload("upload-doc-001", "test.txt")
        assert loaded == content

    @pytest.mark.asyncio
    async def test_get_upload_returns_none_for_nonexistent(self, temp_storage):
        result = await temp_storage.get_upload("nonexistent-doc", "nonexistent.txt")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_upload_removes_directory(self, temp_storage):
        await temp_storage.save_upload(b"data", "file.txt", "upload-del-001")
        result = await temp_storage.delete_upload("upload-del-001")
        assert result is True

        loaded = await temp_storage.get_upload("upload-del-001", "file.txt")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_upload_returns_false(self, temp_storage):
        result = await temp_storage.delete_upload("nonexistent-upload")
        assert result is False


# ===================================================================
# InputDocument CRUD tests
# ===================================================================

class TestInputDocumentStorage:
    @pytest.mark.asyncio
    async def test_save_and_get_input_document_roundtrip(self, temp_storage):
        doc = _make_input_document("input-doc-001")
        saved_id = await temp_storage.save_input_document(doc)
        assert saved_id == "input-doc-001"

        loaded = await temp_storage.get_input_document("input-doc-001")
        assert loaded is not None
        assert loaded.id == "input-doc-001"
        assert loaded.input_type == InputType.TEXT
        assert loaded.content.raw_text == "Sample input text"

    @pytest.mark.asyncio
    async def test_get_input_document_returns_none_for_nonexistent(self, temp_storage):
        result = await temp_storage.get_input_document("nonexistent-doc")
        assert result is None


# ===================================================================
# _save_model error handling
# ===================================================================

class TestSaveModelError:
    @pytest.mark.asyncio
    async def test_save_model_raises_storage_error_on_write_failure(self, temp_storage):
        """When the underlying file write fails, StorageError should be raised."""
        prd = _make_prd("PRD-error-001")

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(StorageError):
                await temp_storage.save_prd(prd)
