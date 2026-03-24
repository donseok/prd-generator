"""PM 검토 API 통합 테스트.

/api/v1/review 엔드포인트의 검토 대기 조회, 결정 제출, 통계 조회를 테스트합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ===================================================================
# GET /api/v1/review/pending/{job_id}
# ===================================================================

class TestGetPendingReviews:
    async def test_nonexistent_job_returns_404(self, client: AsyncClient):
        """존재하지 않는 작업 ID는 404 반환."""
        response = await client.get("/api/v1/review/pending/nonexistent-job")
        assert response.status_code == 404

    async def test_existing_job_returns_review_data(self, client: AsyncClient, sample_job):
        """존재하는 작업이 있으면 검토 데이터를 반환한다."""
        from unittest.mock import patch, AsyncMock
        from app.services import file_storage

        mock_storage = AsyncMock()
        mock_storage.get_job = AsyncMock(return_value=sample_job)

        with patch("app.api.endpoints.review.get_file_storage", return_value=mock_storage):
            response = await client.get(f"/api/v1/review/pending/{sample_job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "pending_count" in data
        assert "total_items" in data


# ===================================================================
# POST /api/v1/review/decision
# ===================================================================

class TestSubmitReviewDecision:
    async def test_invalid_job_returns_404(self, client: AsyncClient):
        """존재하지 않는 작업 ID로 결정 제출 시 404."""
        response = await client.post("/api/v1/review/decision", json={
            "job_id": "nonexistent",
            "review_item_id": "item-1",
            "decision": "approve",
        })
        assert response.status_code == 404

    async def test_invalid_decision_returns_400(self, client: AsyncClient, sample_job):
        """잘못된 결정 값(approve/reject/modify 외)은 400 반환."""
        from unittest.mock import patch, AsyncMock

        mock_storage = AsyncMock()
        mock_storage.get_job = AsyncMock(return_value=sample_job)

        with patch("app.api.endpoints.review.get_file_storage", return_value=mock_storage):
            response = await client.post("/api/v1/review/decision", json={
                "job_id": sample_job.job_id,
                "review_item_id": "item-1",
                "decision": "invalid_decision",
            })

        assert response.status_code == 400


# ===================================================================
# POST /api/v1/review/complete/{job_id}
# ===================================================================

class TestCompleteReview:
    async def test_nonexistent_job_returns_404(self, client: AsyncClient):
        """존재하지 않는 작업 ID는 404 반환."""
        response = await client.post("/api/v1/review/complete/nonexistent-job")
        assert response.status_code == 404

    async def test_non_review_status_returns_400(self, client: AsyncClient, sample_job):
        """PM_REVIEW 상태가 아니면 400 반환."""
        from unittest.mock import patch, AsyncMock
        from app.models import ProcessingStatus

        # 기본 상태는 PENDING (PM_REVIEW가 아님)
        mock_storage = AsyncMock()
        mock_storage.get_job = AsyncMock(return_value=sample_job)

        with patch("app.api.endpoints.review.get_file_storage", return_value=mock_storage):
            response = await client.post(f"/api/v1/review/complete/{sample_job.job_id}")

        assert response.status_code == 400


# ===================================================================
# GET /api/v1/review/stats/{job_id}
# ===================================================================

class TestReviewStats:
    async def test_nonexistent_job_returns_404(self, client: AsyncClient):
        """존재하지 않는 작업 ID는 404 반환."""
        response = await client.get("/api/v1/review/stats/nonexistent-job")
        assert response.status_code == 404

    async def test_returns_stats_for_existing_job(self, client: AsyncClient, sample_job):
        """존재하는 작업의 통계를 반환한다."""
        from unittest.mock import patch, AsyncMock

        mock_storage = AsyncMock()
        mock_storage.get_job = AsyncMock(return_value=sample_job)

        with patch("app.api.endpoints.review.get_file_storage", return_value=mock_storage):
            response = await client.get(f"/api/v1/review/stats/{sample_job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "pending" in data
        assert "resolved" in data
        assert "by_decision" in data
