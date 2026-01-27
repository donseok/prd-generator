"""
API 라우터 설정 파일입니다.
각 기능별로 나누어진 API 주소들을 하나로 모으는 역할을 합니다.
"""

from fastapi import APIRouter

from app.api.endpoints import health, documents, processing, prd, review

# 메인 API 라우터 생성
api_router = APIRouter()

# 헬스 체크 엔드포인트: 서버 상태 확인용 (/health)
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# 문서 관리 엔드포인트: 파일 업로드 및 관리 (/documents)
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# 처리 파이프라인 엔드포인트: AI 처리 작업 시작 및 상태 확인 (/processing)
api_router.include_router(
    processing.router,
    prefix="/processing",
    tags=["processing"]
)

# PRD 문서 엔드포인트: 생성된 PRD 조회 (/prd)
api_router.include_router(
    prd.router,
    prefix="/prd",
    tags=["prd"]
)

# PM 리뷰 엔드포인트: 기획자 검토 기능 (/review)
api_router.include_router(
    review.router,
    prefix="/review",
    tags=["review"]
)