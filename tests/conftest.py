"""공유 pytest fixture 모음."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models import (
    NormalizedRequirement,
    RequirementType,
    Priority,
    SourceReference,
    ValidationResult,
    PRDDocument,
    PRDOverview,
    PRDMetadata,
    Milestone,
    ParsedContent,
    InputMetadata,
    InputDocument,
    InputType,
    ProcessingJob,
    ProcessingStatus,
    LayerResult,
)


@pytest.fixture
def mock_claude_client():
    """ClaudeClient mock fixture."""
    client = AsyncMock()
    client.complete = AsyncMock(return_value="mocked response")
    client.complete_json = AsyncMock(return_value={"requirements": []})
    client.analyze_image = AsyncMock(return_value="mocked image analysis")
    return client


@pytest.fixture
def sample_requirement():
    """단일 NormalizedRequirement fixture."""
    return NormalizedRequirement(
        id="REQ-001",
        type=RequirementType.FUNCTIONAL,
        title="사용자 로그인 기능",
        description="사용자는 이메일과 비밀번호로 로그인할 수 있어야 한다",
        user_story="사용자로서, 이메일과 비밀번호로 로그인하여 서비스를 이용할 수 있다",
        acceptance_criteria=["이메일 형식 검증", "비밀번호 최소 8자"],
        priority=Priority.HIGH,
        confidence_score=0.9,
        confidence_reason="명확한 기능 요구사항",
        source_reference="test.txt",
        source_info=SourceReference(
            document_id="doc-001",
            filename="test.txt",
            section="로그인",
            excerpt="사용자는 이메일과 비밀번호로 로그인",
        ),
    )


@pytest.fixture
def sample_requirements(sample_requirement):
    """복수 NormalizedRequirement fixture."""
    req2 = NormalizedRequirement(
        id="REQ-002",
        type=RequirementType.NON_FUNCTIONAL,
        title="응답 시간 제한",
        description="모든 API 응답은 3초 이내에 완료되어야 한다",
        priority=Priority.MEDIUM,
        confidence_score=0.85,
        source_reference="test.txt",
    )
    req3 = NormalizedRequirement(
        id="REQ-003",
        type=RequirementType.CONSTRAINT,
        title="데이터베이스 제약",
        description="PostgreSQL 14 이상을 사용해야 한다",
        priority=Priority.HIGH,
        confidence_score=0.95,
        source_reference="spec.md",
    )
    return [sample_requirement, req2, req3]


@pytest.fixture
def sample_prd(sample_requirements):
    """PRDDocument fixture."""
    return PRDDocument(
        id="PRD-20240101-abcd",
        title="테스트 프로젝트 PRD",
        overview=PRDOverview(
            background="테스트를 위한 샘플 프로젝트입니다",
            goals=["기능 구현", "테스트 작성"],
            scope="사용자 인증 시스템",
            out_of_scope=["결제 시스템"],
            target_users=["일반 사용자", "관리자"],
            success_metrics=["사용자 만족도 90% 이상"],
        ),
        functional_requirements=[r for r in sample_requirements if r.type == RequirementType.FUNCTIONAL],
        non_functional_requirements=[r for r in sample_requirements if r.type == RequirementType.NON_FUNCTIONAL],
        constraints=[r for r in sample_requirements if r.type == RequirementType.CONSTRAINT],
        milestones=[
            Milestone(id="MS-001", name="Phase 1", description="기본 구현", order=1),
            Milestone(id="MS-002", name="Phase 2", description="고급 기능", order=2),
        ],
        metadata=PRDMetadata(
            version="1.0",
            status="draft",
            source_documents=["test.txt", "spec.md"],
            overall_confidence=0.85,
        ),
    )


@pytest.fixture
def sample_parsed_content():
    """ParsedContent fixture."""
    return ParsedContent(
        raw_text="사용자 로그인 기능이 필요합니다.\n관리자 대시보드 기능이 필요합니다.",
        metadata=InputMetadata(filename="test.txt"),
        sections=[
            {"title": "로그인", "content": "이메일과 비밀번호로 로그인"},
            {"title": "대시보드", "content": "관리자 대시보드 기능 구현"},
        ],
    )


@pytest.fixture
def sample_input_document(sample_parsed_content):
    """InputDocument fixture."""
    return InputDocument(
        id="doc-001",
        input_type=InputType.TEXT,
        content=sample_parsed_content,
        source_path="/tmp/test.txt",
    )


@pytest.fixture
def sample_job():
    """ProcessingJob fixture."""
    return ProcessingJob(
        job_id="test-job-001",
        input_document_ids=["doc-001"],
        input_filenames=["test.txt"],
    )


@pytest.fixture
def temp_storage(tmp_path):
    """임시 디렉토리 기반 FileStorage fixture."""
    from app.services.file_storage import FileStorage
    return FileStorage(base_path=str(tmp_path))


@pytest.fixture
def async_client():
    """httpx AsyncClient fixture (FastAPI 테스트용)."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
