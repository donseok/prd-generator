"""
AI 처리 파이프라인 API 통합 테스트.
작업 시작, 상태 조회, 취소, 목록 조회 등을 확인합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_start_processing_no_documents(client: AsyncClient):
    """존재하지 않는 문서 ID로 처리를 시작하면 404를 반환해야 한다."""
    response = await client.post(
        "/api/v1/processing/start",
        json={"document_ids": ["nonexistent-doc-id"]},
    )

    assert response.status_code == 404


async def test_get_status_not_found(client: AsyncClient):
    """존재하지 않는 작업 ID로 상태를 조회하면 404를 반환해야 한다."""
    response = await client.get("/api/v1/processing/status/nonexistent")

    assert response.status_code == 404


async def test_cancel_not_found(client: AsyncClient):
    """존재하지 않는 작업 ID를 취소하면 404를 반환해야 한다."""
    response = await client.post("/api/v1/processing/cancel/nonexistent")

    assert response.status_code == 404


async def test_list_jobs(client: AsyncClient):
    """GET /api/v1/processing 은 200과 jobs 배열을 반환해야 한다."""
    response = await client.get("/api/v1/processing")

    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


async def test_start_processing_empty_list(client: AsyncClient):
    """빈 document_ids 목록으로 처리를 시작하면 작업이 생성되지만 백그라운드에서 실패한다.

    현재 구현에서는 빈 목록이 검증을 통과하고 200을 반환한 뒤
    백그라운드 파이프라인에서 '입력 문서를 찾을 수 없습니다' 에러가 발생한다.
    """
    response = await client.post(
        "/api/v1/processing/start",
        json={"document_ids": []},
    )

    # 빈 목록은 for 루프를 건너뛰므로 job이 생성되고 200이 반환됨
    # 실제 에러는 백그라운드 파이프라인에서 발생
    assert response.status_code == 200

    data = response.json()
    assert "job_id" in data
    assert data["message"] == "0개 문서 처리 시작"
