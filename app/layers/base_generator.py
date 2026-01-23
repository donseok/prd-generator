"""Base generator class for all document generators.

이 모듈은 PRD, Proposal, TRD, WBS 생성기들이 공통으로 사용하는
기본 기능을 제공하는 추상 베이스 클래스를 정의합니다.

주요 기능:
- 표준 ID 생성
- 템플릿 메서드 패턴을 통한 일관된 생성 흐름
- Claude API 호출 공통화 (JSON/텍스트)
- 로깅 및 에러 처리 표준화
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar, Generic, Optional, Any

from app.services import ClaudeClient, get_claude_client

# 제네릭 타입 변수
InputT = TypeVar('InputT')      # 입력 문서 타입 (PRDDocument 등)
OutputT = TypeVar('OutputT')    # 출력 문서 타입 (ProposalDocument 등)
ContextT = TypeVar('ContextT')  # 컨텍스트 타입 (ProposalContext 등)

logger = logging.getLogger(__name__)


class BaseGenerator(ABC, Generic[InputT, OutputT, ContextT]):
    """
    문서 생성기 추상 베이스 클래스.

    모든 Layer 4+ 생성기(PRDGenerator, ProposalGenerator, TRDGenerator,
    WBSGenerator)가 상속하는 기본 클래스입니다.

    Template Method 패턴을 사용하여 일관된 생성 흐름을 보장합니다:
    1. 시작 로깅
    2. ID 및 제목 생성
    3. 섹션별 생성 (서브클래스에서 구현)
    4. 메타데이터 생성
    5. 완료 로깅

    Attributes:
        claude_client: Claude API 호출을 위한 클라이언트
        _id_prefix: 생성되는 문서 ID의 접두어 (예: "PROP", "TRD", "WBS")
        _generator_name: 로깅에 사용되는 생성기 이름

    Example:
        class MyGenerator(BaseGenerator[PRDDocument, MyOutput, MyContext]):
            _id_prefix = "MY"
            _generator_name = "MyGenerator"

            async def _generate_sections(self, input_doc, context):
                # 섹션 생성 로직
                return sections
    """

    # 서브클래스에서 오버라이드해야 하는 클래스 속성
    _id_prefix: str = "DOC"
    _generator_name: str = "BaseGenerator"

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        생성기 초기화.

        Args:
            claude_client: Claude 클라이언트 인스턴스.
                          None이면 싱글톤 인스턴스 사용.
        """
        self.claude_client = claude_client or get_claude_client()

    def _generate_id(self) -> str:
        """
        표준 형식의 문서 ID 생성.

        형식: {PREFIX}-{YYYYMMDD}-{4자리 UUID}
        예시: PROP-20240115-a1b2, TRD-20240115-c3d4

        Returns:
            생성된 문서 ID 문자열
        """
        date_part = datetime.now().strftime('%Y%m%d')
        uuid_part = uuid.uuid4().hex[:4]
        return f"{self._id_prefix}-{date_part}-{uuid_part}"

    async def generate(
        self,
        input_doc: InputT,
        context: ContextT,
    ) -> OutputT:
        """
        문서 생성 템플릿 메서드.

        일관된 생성 흐름을 보장하는 템플릿 메서드입니다.
        서브클래스는 이 메서드를 직접 오버라이드하기보다
        _generate_sections()를 구현해야 합니다.

        처리 흐름:
        1. 시작 시간 기록 및 로깅
        2. _do_generate() 호출 (서브클래스 구현)
        3. 완료 시간 및 소요 시간 로깅

        Args:
            input_doc: 입력 문서 (예: PRDDocument)
            context: 생성 컨텍스트

        Returns:
            생성된 출력 문서

        Raises:
            Exception: 생성 중 발생한 모든 예외
        """
        doc_title = getattr(input_doc, 'title', 'Unknown')
        logger.info(f"[{self._generator_name}] 생성 시작: {doc_title}")
        start_time = datetime.now()

        try:
            result = await self._do_generate(input_doc, context)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{self._generator_name}] 생성 완료: {elapsed:.1f}초")

            return result

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{self._generator_name}] 생성 실패 ({elapsed:.1f}초): {e}")
            raise

    @abstractmethod
    async def _do_generate(
        self,
        input_doc: InputT,
        context: ContextT,
    ) -> OutputT:
        """
        실제 문서 생성 로직 (서브클래스에서 구현).

        Args:
            input_doc: 입력 문서
            context: 생성 컨텍스트

        Returns:
            생성된 출력 문서
        """
        pass

    async def _call_claude_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        section_name: str = "",
    ) -> dict:
        """
        Claude API JSON 호출 공통 메서드.

        JSON 형식의 응답을 요청하고 파싱하여 반환합니다.
        실패 시 기본값(빈 딕셔너리)을 반환하고 경고 로깅합니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            temperature: 샘플링 온도 (기본값 0.3)
            section_name: 로깅용 섹션 이름

        Returns:
            파싱된 JSON 딕셔너리. 실패 시 빈 딕셔너리.
        """
        log_prefix = f"[{self._generator_name}]"
        if section_name:
            log_prefix = f"[{self._generator_name}:{section_name}]"

        try:
            start = datetime.now()
            result = await self.claude_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )
            elapsed = (datetime.now() - start).total_seconds()
            logger.debug(f"{log_prefix} Claude JSON 호출 완료: {elapsed:.1f}초")
            return result

        except Exception as e:
            logger.warning(f"{log_prefix} Claude JSON 호출 실패: {e}")
            return {}

    async def _call_claude_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        section_name: str = "",
    ) -> str:
        """
        Claude API 텍스트 호출 공통 메서드.

        텍스트 형식의 응답을 요청하여 반환합니다.
        실패 시 빈 문자열을 반환하고 경고 로깅합니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            temperature: 샘플링 온도 (기본값 0.4)
            section_name: 로깅용 섹션 이름

        Returns:
            응답 텍스트. 실패 시 빈 문자열.
        """
        log_prefix = f"[{self._generator_name}]"
        if section_name:
            log_prefix = f"[{self._generator_name}:{section_name}]"

        try:
            start = datetime.now()
            result = await self.claude_client.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )
            elapsed = (datetime.now() - start).total_seconds()
            logger.debug(f"{log_prefix} Claude 텍스트 호출 완료: {elapsed:.1f}초")
            return result.strip()

        except Exception as e:
            logger.warning(f"{log_prefix} Claude 텍스트 호출 실패: {e}")
            return ""

    async def _call_claude_json_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback_value: Any,
        temperature: float = 0.3,
        section_name: str = "",
    ) -> Any:
        """
        Claude API JSON 호출 (실패 시 폴백 값 반환).

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            fallback_value: 실패 시 반환할 기본값
            temperature: 샘플링 온도
            section_name: 로깅용 섹션 이름

        Returns:
            파싱된 JSON 또는 폴백 값
        """
        result = await self._call_claude_json(
            system_prompt, user_prompt, temperature, section_name
        )
        return result if result else fallback_value
