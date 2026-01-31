"""
문서 업로드 및 관리 API 통합 테스트.
파일 업로드, 조회, 삭제, 유효성 검증 등을 확인합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_upload_text_file(client: AsyncClient):
    """POST /api/v1/documents/upload 으로 .txt 파일을 업로드하면 200과 문서 정보를 반환해야 한다."""
    response = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("test.txt", b"hello world", "text/plain"))],
    )

    assert response.status_code == 200

    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) == 1

    doc = data["documents"][0]
    assert "id" in doc
    assert doc["filename"] == "test.txt"
    assert doc["input_type"] == "text"
    assert doc["size_bytes"] == len(b"hello world")


async def test_upload_multiple_files(client: AsyncClient):
    """두 개의 파일을 동시에 업로드하면 2개의 문서 정보를 반환해야 한다."""
    response = await client.post(
        "/api/v1/documents/upload",
        files=[
            ("files", ("file1.txt", b"content one", "text/plain")),
            ("files", ("file2.md", b"content two", "text/markdown")),
        ],
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data["documents"]) == 2

    filenames = [doc["filename"] for doc in data["documents"]]
    assert "file1.txt" in filenames
    assert "file2.md" in filenames


async def test_upload_invalid_extension(client: AsyncClient):
    """허용되지 않는 확장자(.exe)를 업로드하면 400 에러를 반환해야 한다."""
    response = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("malware.exe", b"MZ\x90\x00", "application/octet-stream"))],
    )

    assert response.status_code == 400

    data = response.json()
    assert "error_code" in data
    assert data["error_code"] == "ERR_INPUT_001"


async def test_upload_empty_filename(client: AsyncClient):
    """빈 파일명으로 업로드하면 400 또는 422 에러를 반환해야 한다."""
    response = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("", b"some content", "text/plain"))],
    )

    # FastAPI가 빈 파일명을 422(Unprocessable Entity)로 거부하거나
    # validate_filename이 InputValidationError(400)을 발생시킬 수 있다
    assert response.status_code in (400, 422)


async def test_upload_path_traversal(client: AsyncClient):
    """경로 순회 공격 파일명(../../../etc/passwd)은 400 에러를 반환해야 한다."""
    response = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("../../../etc/passwd", b"root:x:0:0", "text/plain"))],
    )

    assert response.status_code == 400

    data = response.json()
    assert "error_code" in data
    assert data["error_code"] == "ERR_INPUT_001"


async def test_get_document_not_found(client: AsyncClient):
    """존재하지 않는 문서 ID로 조회하면 404를 반환해야 한다."""
    response = await client.get("/api/v1/documents/nonexistent")

    assert response.status_code == 404


async def test_delete_document_not_found(client: AsyncClient):
    """존재하지 않는 문서 ID로 삭제하면 404를 반환해야 한다."""
    response = await client.delete("/api/v1/documents/nonexistent")

    assert response.status_code == 404


async def test_list_documents(client: AsyncClient):
    """GET /api/v1/documents 는 200과 total, documents 필드를 반환해야 한다."""
    response = await client.get("/api/v1/documents")

    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)
