"""Auto-Doc API 통합 테스트.

/api/v1/auto-doc 엔드포인트의 입력 파일 목록, 문서 생성, 상태 조회를 테스트합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from pathlib import Path
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ===================================================================
# GET /api/v1/auto-doc/inputs
# ===================================================================

class TestListInputFiles:
    async def test_returns_file_list(self, client: AsyncClient, tmp_path):
        """입력 폴더에 파일이 있으면 목록을 반환한다."""
        # 임시 입력 폴더 생성
        fake_inputs = tmp_path / "projects"
        fake_inputs.mkdir()
        (fake_inputs / "requirements.txt").write_text("test content")
        (fake_inputs / "spec.md").write_text("# Spec\ntest")

        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.get("/api/v1/auto-doc/inputs")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "files" in data
        assert data["total"] == 2

    async def test_returns_empty_when_no_folder(self, client: AsyncClient, tmp_path):
        """입력 폴더가 없어도 빈 목록을 반환한다."""
        fake_inputs = tmp_path / "nonexistent"
        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.get("/api/v1/auto-doc/inputs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["files"] == []

    async def test_excludes_hidden_files(self, client: AsyncClient, tmp_path):
        """숨김 파일(.)은 목록에 포함하지 않는다."""
        fake_inputs = tmp_path / "projects"
        fake_inputs.mkdir()
        (fake_inputs / ".hidden").write_text("hidden")
        (fake_inputs / "visible.txt").write_text("visible")

        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.get("/api/v1/auto-doc/inputs")

        data = response.json()
        assert data["total"] == 1
        assert data["files"][0]["name"] == "visible.txt"


# ===================================================================
# POST /api/v1/auto-doc/generate
# ===================================================================

class TestGenerateDocuments:
    async def test_generate_no_input_folder(self, client: AsyncClient, tmp_path):
        """입력 폴더가 없으면 400 반환."""
        fake_inputs = tmp_path / "nonexistent"
        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.post(
                "/api/v1/auto-doc/generate",
                json={"doc_types": ["prd"]},
            )
        assert response.status_code == 400

    async def test_generate_empty_input_folder(self, client: AsyncClient, tmp_path):
        """입력 폴더가 비어있으면 400 반환."""
        fake_inputs = tmp_path / "empty_projects"
        fake_inputs.mkdir()
        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.post(
                "/api/v1/auto-doc/generate",
                json={"doc_types": ["prd"]},
            )
        assert response.status_code == 400

    async def test_generate_invalid_doc_type(self, client: AsyncClient, tmp_path):
        """잘못된 문서 타입이면 400 반환."""
        fake_inputs = tmp_path / "projects"
        fake_inputs.mkdir()
        (fake_inputs / "test.txt").write_text("content")
        with patch("app.api.endpoints.auto_doc.INPUTS_PATH", fake_inputs):
            response = await client.post(
                "/api/v1/auto-doc/generate",
                json={"doc_types": ["invalid_type"]},
            )
        assert response.status_code == 400


# ===================================================================
# GET /api/v1/auto-doc/status/{job_id}
# ===================================================================

class TestGenerationStatus:
    async def test_status_nonexistent_job(self, client: AsyncClient):
        """존재하지 않는 작업 ID는 404 반환."""
        response = await client.get("/api/v1/auto-doc/status/nonexistent-job")
        assert response.status_code == 404
