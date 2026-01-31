"""
PRD(제품 요구사항 정의서) 생성 시스템의 메인 진입점 파일입니다.
웹 서버 애플리케이션을 생성하고 설정하는 역할을 담당합니다.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.router import api_router
from app.exceptions import PRDGeneratorError, InputValidationError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션의 생명주기(시작과 종료)를 관리하는 함수입니다.
    
    서버가 시작될 때:
    1. 필요한 설정들을 불러옵니다.
    2. 시작 로그를 출력합니다.
    
    서버가 종료될 때:
    1. 정리 작업이나 종료 로그를 출력합니다.
    """
    # 시작 시: 서비스 초기화
    settings = get_settings()
    logger.info(f"PRD 생성기가 다음 주소에서 시작됩니다: {settings.host}:{settings.port}")
    logger.info("AI 처리를 위해 Claude Code CLI를 사용합니다")

    yield

    # 종료 시: 리소스 정리
    logger.info("PRD 생성기가 종료됩니다")


def create_app() -> FastAPI:
    """
    FastAPI 웹 애플리케이션을 생성하고 설정하는 함수입니다.
    
    주요 기능:
    1. 기본 앱 정보 설정 (제목, 설명 등)
    2. CORS 설정 (프론트엔드와의 통신 허용 설정)
    3. API 라우터 연결 (기능별 주소 연결)
    """
    settings = get_settings()

    app = FastAPI(
        title="PRD 자동 생성 시스템",
        description="다양한 입력 형식을 표준 PRD로 변환하는 4단계 AI 파이프라인",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",  # 개발자용 문서 주소
        redoc_url="/redoc",
    )

    # CORS 미들웨어 설정: 프론트엔드 웹페이지가 이 서버에 접속할 수 있도록 허용하는 설정입니다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],  # 모든 통신 방식 허용 (GET, POST 등)
        allow_headers=["*"],  # 모든 헤더 정보 허용
    )

    # 글로벌 예외 핸들러: 커스텀 예외를 구조화된 JSON 응답으로 변환
    @app.exception_handler(PRDGeneratorError)
    async def prd_error_handler(request: Request, exc: PRDGeneratorError):
        status_code = 400 if isinstance(exc, InputValidationError) else 500
        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.error(f"처리되지 않은 예외: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "ERR_INTERNAL",
                "message": "내부 서버 오류가 발생했습니다",
                "details": None,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # API 라우터 포함: /api/v1 주소 아래에 모든 기능을 연결합니다.
    app.include_router(api_router, prefix="/api/v1")

    return app


# 애플리케이션 인스턴스 생성
app = create_app()


@app.get("/")
async def root():
    """
    루트 엔드포인트: 서버가 정상적으로 동작하는지 확인하는 기본 주소입니다.
    접속 시 서버의 기본 정보를 반환합니다.
    """
    return {
        "name": "PRD 자동 생성 시스템",
        "version": "1.0.0",
        "description": "다양한 입력 형식을 표준 PRD로 변환",
        "docs": "/docs",
        "api": "/api/v1",
    }


# 이 파일을 직접 실행했을 때 서버를 구동시키는 코드입니다.
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    # uvicorn 웹 서버를 실행합니다.
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # 코드가 변경되면 자동으로 재시작 (개발 모드)
    )