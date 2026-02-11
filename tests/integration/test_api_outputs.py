"""출력 문서 API 통합 테스트.

/api/v1/outputs/documents 엔드포인트의 문서 목록 조회, 상세 조회, 삭제를 테스트합니다.
"""

import json
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


@pytest.fixture
def fake_outputs(tmp_path):
    """테스트용 출력 문서 구조 생성 (소문자 폴더명)."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()

    # prd 폴더 (소문자)
    prd_dir = outputs / "prd"
    prd_dir.mkdir()
    prd_doc = prd_dir / "PRD-20260101-120000.json"
    prd_doc.write_text(json.dumps({
        "id": "PRD-20260101-120000",
        "title": "테스트 PRD",
        "overview": {"background": "테스트"},
        "metadata": {"version": "1.0", "status": "draft"},
    }, ensure_ascii=False))

    prd_md = prd_dir / "PRD-20260101-120000.md"
    prd_md.write_text("# 테스트 PRD\n테스트 내용")

    # trd 폴더
    trd_dir = outputs / "trd"
    trd_dir.mkdir()

    # wbs 폴더
    wbs_dir = outputs / "wbs"
    wbs_dir.mkdir()

    # proposals 폴더
    proposals_dir = outputs / "proposals"
    proposals_dir.mkdir()

    # ppt 폴더
    ppt_dir = outputs / "ppt"
    ppt_dir.mkdir()

    return outputs


# ===================================================================
# GET /api/v1/outputs/documents
# ===================================================================

class TestListOutputDocuments:
    async def test_list_returns_documents(self, client: AsyncClient, fake_outputs):
        """출력 폴더에 문서가 있으면 목록 반환."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.get("/api/v1/outputs/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert data["total"] >= 1

    async def test_list_empty_folder(self, client: AsyncClient, tmp_path):
        """빈 출력 폴더는 빈 목록 반환."""
        empty_out = tmp_path / "empty_outputs"
        empty_out.mkdir()
        # 소문자 폴더 생성
        for f in ["prd", "trd", "wbs", "proposals", "ppt"]:
            (empty_out / f).mkdir()

        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", empty_out):
            response = await client.get("/api/v1/outputs/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_filter_by_doc_type(self, client: AsyncClient, fake_outputs):
        """doc_type 파라미터로 필터링."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.get("/api/v1/outputs/documents?doc_type=prd")

        assert response.status_code == 200
        data = response.json()
        for doc in data["documents"]:
            assert doc["doc_type"] == "PRD"

    async def test_limit_parameter(self, client: AsyncClient, fake_outputs):
        """limit 파라미터로 결과 수 제한."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.get("/api/v1/outputs/documents?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) <= 1


# ===================================================================
# GET /api/v1/outputs/documents/{doc_id}
# ===================================================================

class TestGetOutputDocument:
    async def test_get_existing_document(self, client: AsyncClient, fake_outputs):
        """존재하는 문서 ID로 상세 조회."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.get("/api/v1/outputs/documents/PRD-20260101-120000")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "PRD-20260101-120000"

    async def test_get_nonexistent_document(self, client: AsyncClient, fake_outputs):
        """존재하지 않는 문서 ID는 404 반환."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.get("/api/v1/outputs/documents/NONEXIST-DOC")

        assert response.status_code == 404


# ===================================================================
# DELETE /api/v1/outputs/documents/all
# ===================================================================

class TestDeleteAllDocuments:
    async def test_delete_all(self, client: AsyncClient, fake_outputs):
        """모든 문서 삭제."""
        with patch("app.api.endpoints.outputs.WORKSPACE_OUTPUTS_PATH", fake_outputs):
            response = await client.delete("/api/v1/outputs/documents/all")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
