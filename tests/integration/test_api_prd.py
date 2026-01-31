"""
PRD 문서 조회 및 내보내기 API 통합 테스트.
PRD 조회, 목록, 내보내기, 삭제 등을 확인합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_get_prd_not_found(client: AsyncClient):
    """존재하지 않는 PRD ID로 조회하면 404를 반환해야 한다."""
    response = await client.get("/api/v1/prd/nonexistent")

    assert response.status_code == 404


async def test_export_prd_not_found(client: AsyncClient):
    """존재하지 않는 PRD ID를 마크다운으로 내보내기 하면 404를 반환해야 한다."""
    response = await client.get("/api/v1/prd/nonexistent/export?format=markdown")

    assert response.status_code == 404


async def test_list_prds(client: AsyncClient):
    """GET /api/v1/prd 는 200과 total, prds 필드를 반환해야 한다."""
    response = await client.get("/api/v1/prd")

    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "prds" in data
    assert isinstance(data["prds"], list)


async def test_export_invalid_format(client: AsyncClient):
    """지원하지 않는 형식(xml)으로 내보내기 하면 400 또는 404를 반환해야 한다."""
    response = await client.get("/api/v1/prd/nonexistent/export?format=xml")

    # PRD가 존재하지 않으면 404가 먼저 발생하고,
    # PRD가 존재하더라도 지원하지 않는 format이면 400이 발생한다.
    # 현재 로직은 PRD 존재 여부를 먼저 확인하므로 404가 반환된다.
    assert response.status_code in (400, 404)


async def test_delete_prd_not_found(client: AsyncClient):
    """존재하지 않는 PRD ID를 삭제하면 404를 반환해야 한다."""
    response = await client.delete("/api/v1/prd/nonexistent")

    assert response.status_code == 404
