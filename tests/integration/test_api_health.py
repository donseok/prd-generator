"""
API 헬스 체크 및 루트 엔드포인트 통합 테스트.
서버의 기본 응답과 문서 페이지 접근을 확인합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_root_endpoint(client: AsyncClient):
    """GET / 는 서버 기본 정보(name, version, docs)를 200으로 반환해야 한다."""
    response = await client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


async def test_docs_endpoint(client: AsyncClient):
    """GET /docs 는 Swagger UI 페이지를 200으로 반환해야 한다."""
    response = await client.get("/docs")

    assert response.status_code == 200
