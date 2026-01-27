from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    애플리케이션의 설정을 관리하는 클래스입니다.
    환경 변수(.env 파일)에서 설정값을 읽어옵니다.
    """

    # API 설정: AI 모델 사용을 위한 키와 모델 이름
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"  # 사용할 Claude AI 모델 버전

    # 검증 및 처리 로직 설정
    auto_approve_threshold: float = 0.8  # 자동 승인 점수 기준 (이 점수 이상이면 자동 통과)
    enable_pm_review: bool = False  # PM(기획자) 검토 단계를 켤지 끌지 결정
    enable_conflict_detection: bool = False  # 요구사항 간의 충돌을 감지하는 기능을 켤지 결정

    # 서버 설정: 서버가 실행될 주소와 포트 번호
    host: str = "0.0.0.0"  # 모든 외부 접속 허용
    port: int = 8000

    class Config:
        # 설정을 읽어올 파일 지정
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    설정을 가져오는 함수입니다.
    @lru_cache를 사용하여 한 번 읽은 설정은 메모리에 저장해두고 재사용합니다.
    (매번 파일을 다시 읽지 않아 효율적입니다)
    """
    return Settings()