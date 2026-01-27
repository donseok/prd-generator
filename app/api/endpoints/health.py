"""
헬스 체크(Health Check) 엔드포인트입니다.
서버가 살아서 정상적으로 응답하는지 확인하는 용도입니다.
"""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("")
async def health_check():
    """
    기본 상태 확인 함수.
    서버가 켜져 있으면 {"status": "healthy"}를 반환합니다.
    """
    return {"status": "healthy"}


@router.get("/detail")
async def health_check_detail():
    """
    상세 상태 확인 함수.
    현재 설정 정보(어떤 AI 모델을 쓰는지 등)도 같이 보여줍니다.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "config": {
            "claude_model": settings.claude_model,  # 사용 중인 AI 모델
            "auto_approve_threshold": settings.auto_approve_threshold,  # 자동 승인 점수 기준
            "api_key_configured": bool(settings.anthropic_api_key),  # API 키 설정 여부
        }
    }