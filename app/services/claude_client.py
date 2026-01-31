"""
Claude Code CLI 클라이언트 서비스입니다.
AI(Claude)와의 통신을 담당하는 모듈입니다.

주요 기능:
1. Claude AI에게 질문하고 답변 받기 (텍스트/JSON)
2. 이미지 분석 요청
3. 오류 발생 시 자동으로 재시도하는 기능
"""

import json
import subprocess
import tempfile
import os
import sys
import asyncio
import logging
from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.exceptions import ClaudeClientError

# 로깅 설정: 시스템의 동작 상태를 기록합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Claude AI와 통신하는 도구입니다.
    터미널 명령어(CLI)를 통해 Claude를 실행하고 결과를 받아옵니다.

    주요 특징:
    - 한국어 처리에 최적화되어 있습니다.
    - 여러 요청을 동시에 처리할 수 있습니다 (비동기 처리).
    - 요청이 실패하면 자동으로 재시도합니다.
    """

    def __init__(self):
        """
        ClaudeClient 초기화 함수입니다.
        
        컴퓨터의 성능(CPU 코어 수)에 맞춰서 동시에 처리할 수 있는 작업 수를 자동으로 조절합니다.
        (너무 많이 실행하면 컴퓨터가 느려지는 것을 방지합니다)
        """
        self._max_retries = 2  # 최대 2번까지 재시도 (빠른 실패)
        self._retry_delay = 1  # 재시도 전 1초 대기

        # CPU 코어 수 확인 후 작업자(Worker) 수 설정
        cpu_count = os.cpu_count() or 4
        # 최소 2개, 최대 8개 사이로 설정
        max_workers = min(8, max(2, cpu_count))
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        logger.info(f"[ClaudeClient] CLI 모드 초기화 완료 (작업자 수={max_workers})")

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """
        Claude에게 텍스트 답변을 요청하는 함수입니다.

        Args:
            system_prompt: AI에게 부여할 역할이나 지침 (예: "당신은 전문 번역가입니다")
            user_prompt: 실제 질문 내용
            max_tokens: 답변의 최대 길이 (CLI 모드에서는 자동 처리됨)
            temperature: 창의성 조절 (낮을수록 정확하고 일관된 답변)

        Returns:
            AI의 답변 텍스트
        """
        full_prompt = f"""[중요: 이 요청은 프로그램 API 호출입니다. 시스템 안내 메시지나 대화형 응답을 출력하지 마세요.]

역할: 요구사항 분석 전문가
작업: {system_prompt}

입력 데이터:
{user_prompt}

[필수] 요청된 내용만 직접 응답하세요. 인사말이나 안내 메시지 없이 결과만 출력합니다."""

        return await self._execute_claude_cli(full_prompt)

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict:
        """
        Claude에게 JSON 형식(구조화된 데이터)의 답변을 요청하는 함수입니다.
        결과를 프로그램에서 바로 사용할 수 있는 형태(Dictionary)로 변환해줍니다.

        Args:
            system_prompt: JSON 형식으로 답하라는 지침이 포함되어야 함
            user_prompt: 질문 내용

        Returns:
            파싱된 데이터 (딕셔너리 형태)
        """
        full_prompt = f"""[중요: 이 요청은 프로그램 API 호출입니다. 시스템 안내 메시지나 대화형 응답을 출력하지 마세요.]

역할: 요구사항 분석 전문가
작업: {system_prompt}

입력 데이터:
{user_prompt}

[필수 응답 형식]
- 반드시 유효한 JSON만 출력
- 설명, 인사말, 마크다운 없이 순수 JSON만 반환
- {{ 또는 [ 로 시작하여 }} 또는 ] 로 끝나야 함"""

        response = await self._execute_claude_cli(full_prompt)
        return self._parse_json_response(response)

    async def analyze_image(
        self,
        system_prompt: str,
        image_data: bytes,
        media_type: str,
        additional_context: str = "",
        max_tokens: int = 4096,
        image_path: str = None,
    ) -> str:
        """
        Claude의 시각(Vision) 기능을 사용하여 이미지를 분석하는 함수입니다.
        이미지 파일 경로나 데이터 자체를 입력받아 분석 결과를 텍스트로 반환합니다.

        Args:
            system_prompt: 이미지 분석 지침
            image_data: 이미지 파일의 바이너리 데이터 (image_path가 없을 때 사용)
            media_type: 이미지 종류 (예: image/png)
            additional_context: 추가 설명 텍스트
            image_path: 이미지 파일의 경로 (권장됨)
        """
        # 파일 경로가 있으면 직접 사용 (더 효율적)
        if image_path and os.path.exists(image_path):
            full_prompt = f"""당신은 PRD 생성을 돕는 요구사항 분석 전문가입니다.

다음 지침을 따라 이미지를 분석해 주세요:
{system_prompt}

추가 컨텍스트: {additional_context if additional_context else "없음"}

분석할 이미지 파일: {image_path}"""

            return await self._execute_claude_cli(full_prompt)

        # 파일 경로가 없으면 임시 파일을 만들어서 처리
        extension = media_type.split("/")[-1]
        if extension == "jpeg":
            extension = "jpg"

        with tempfile.NamedTemporaryFile(
            suffix=f".{extension}", delete=False
        ) as tmp_file:
            tmp_file.write(image_data)
            tmp_path = tmp_file.name

        try:
            full_prompt = f"""당신은 PRD 생성을 돕는 요구사항 분석 전문가입니다.

다음 지침을 따라 이미지를 분석해 주세요:
{system_prompt}

추가 컨텍스트: {additional_context if additional_context else "없음"}

분석할 이미지 파일: {tmp_path}"""

            result = await self._execute_claude_cli(full_prompt)
            return result
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _get_env(self) -> dict:
        """Claude CLI 실행을 위한 환경 변수 설정 (명령어 경로 등)"""
        env = os.environ.copy()

        if sys.platform == "win32":
            extra_paths = [
                os.path.expanduser("~\\AppData\\Roaming\\npm"),
            ]
            path_separator = ";"
        else:
            extra_paths = [
                os.path.expanduser("~/.npm-global/bin"),
                "/usr/local/bin",
                "/opt/homebrew/bin",
            ]
            path_separator = ":"

        env["PATH"] = path_separator.join(extra_paths) + path_separator + env.get("PATH", "")
        return env

    def _run_claude_sync(self, prompt: str) -> str:
        """실제로 Claude CLI 명령어를 실행하는 함수 (동기 방식)"""
        env = self._get_env()

        prompt_len = len(prompt)
        logger.info(f"[CLI] 프롬프트 길이: {prompt_len} chars")

        start_time = datetime.now()

        try:
            use_shell = sys.platform == "win32"
            # 임시 디렉토리에서 실행하여 프로젝트 컨텍스트 분리
            temp_dir = tempfile.gettempdir()

            # 속도 최적화 옵션:
            # --dangerously-skip-permissions: 권한 체크 스킵
            # --setting-sources user: 프로젝트 설정(CLAUDE.md) 무시
            # --no-session-persistence: 세션 저장 안함
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text",
                 "--dangerously-skip-permissions", "--setting-sources", "user",
                 "--no-session-persistence"],
                capture_output=True,
                text=True,
                timeout=120,  # 2분 제한 (빠른 실패)
                env=env,
                shell=use_shell,
                encoding='utf-8',
                cwd=temp_dir,  # 임시 디렉토리에서 실행
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[CLI] 완료: {elapsed:.1f}초, 상태코드={result.returncode}")

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"[CLI] 에러: {error_msg}")
                raise RuntimeError(f"Claude CLI error: {error_msg}")

            logger.info(f"[CLI] 응답 길이: {len(result.stdout)} chars")
            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"[CLI] 타임아웃! {elapsed:.1f}초")
            raise

    def _run_claude_sync_with_files(self, prompt: str, file_paths: list[str]) -> str:
        """파일 첨부와 함께 Claude CLI 실행"""
        env = self._get_env()

        cmd = ["claude", "-p", prompt, "--output-format", "text",
               "--dangerously-skip-permissions", "--setting-sources", "user",
               "--no-session-persistence"]
        for file_path in file_paths:
            cmd.extend(["--file", file_path])

        use_shell = sys.platform == "win32"
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2분 제한
            env=env,
            shell=use_shell,
            encoding='utf-8',
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        return result.stdout.strip()

    async def _execute_claude_cli(self, prompt: str) -> str:
        """
        Claude CLI를 비동기로 실행하고 재시도 로직을 적용하는 함수.
        
        재시도 전략 (지수 백오프):
        - 1차 시도: 실패 시 바로 다음 단계
        - 2차 시도: 2초 대기
        - 3차 시도: 4초 대기
        - 모두 실패하면 에러 발생
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:
                logger.info(f"[CLI] 시도 {attempt + 1}/{self._max_retries}")

                # 별도의 스레드에서 실행하여 메인 프로그램이 멈추지 않게 함
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    self._executor, self._run_claude_sync, prompt
                )

                logger.info(f"[CLI] 시도 {attempt + 1} 성공")
                return result

            except Exception as e:
                last_error = e
                logger.error(f"[CLI] 시도 {attempt + 1} 실패: {type(e).__name__}: {e}")

                # 마지막 시도가 아니면 잠시 대기
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)
                    logger.info(f"[CLI] {wait_time}초 후 재시도...")
                    await asyncio.sleep(wait_time)

        logger.error(f"[CLI] 모든 시도 실패: {last_error}")
        raise last_error

    async def _execute_claude_cli_with_files(
        self,
        prompt: str,
        file_paths: list[str]
    ) -> str:
        """파일 첨부 CLI 실행 (비동기 + 재시도)"""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                logger.info(f"[CLI] 파일 첨부 요청 (시도 {attempt + 1})")

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    self._run_claude_sync_with_files,
                    prompt,
                    file_paths
                )

                return result

            except Exception as e:
                last_error = e
                logger.error(f"[CLI] 파일 첨부 요청 실패: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))

        raise last_error

    def _parse_json_response(self, response: str) -> dict:
        """
        AI의 응답 텍스트에서 JSON 데이터를 추출하는 함수입니다.
        AI가 가끔 설명이나 마크다운 기호(```json 등)를 붙여서 주는데, 이를 깨끗하게 정리해서 데이터만 뽑아냅니다.
        """
        logger.debug(f"[JSON] 파싱 시작")

        # 응답이 비어있으면 빈 딕셔너리 반환
        if not response or not response.strip():
            logger.warning("[JSON] 응답이 비어있음, 빈 딕셔너리 반환")
            return {}

        # 1. 앞뒤 공백 및 마크다운 기호 제거
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 2. PRD 시스템 안내 메시지인지 확인 (Claude Code 프로젝트 컨텍스트로 인한 응답)
        system_indicators = [
            "안녕하세요! PRD",
            "PRD 생성 시스템",
            "/prd:prd-maker",
            "/trd:trd-maker",
            "@auto-doc",
            "어떤 작업을 도와드릴까요",
        ]
        if any(indicator in cleaned for indicator in system_indicators):
            logger.warning("[JSON] Claude Code 시스템 응답 감지, 빈 결과 반환")
            return {}

        # 3. JSON 변환 시도
        try:
            result = json.loads(cleaned)
            logger.debug("[JSON] 직접 파싱 성공")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON] 직접 파싱 실패: {e}")

            # 4. 실패 시 텍스트 내에서 중괄호({})
            # 또는 대괄호([])를 찾아서 추출 시도
            start_idx = cleaned.find("{")
            if start_idx == -1:
                start_idx = cleaned.find("[")

            if start_idx != -1:
                # 괄호 짝 맞추기 로직
                bracket = "{" if cleaned[start_idx] == "{" else "["
                closing = "}" if bracket == "{" else "]"

                depth = 0
                end_idx = start_idx

                for i, char in enumerate(cleaned[start_idx:], start_idx):
                    if char == bracket:
                        depth += 1
                    elif char == closing:
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break

                try:
                    result = json.loads(cleaned[start_idx:end_idx])
                    logger.debug("[JSON] 추출 파싱 성공")
                    return result
                except json.JSONDecodeError as e2:
                    logger.error(f"[JSON] 추출 파싱 실패: {e2}")

            logger.error(f"[JSON] 최종 파싱 실패")
            raise ClaudeClientError(
                "Claude 응답에서 유효한 JSON을 추출할 수 없습니다",
                details={"response_preview": cleaned[:200]},
            )


# 전역 변수로 클라이언트 인스턴스 저장 (싱글톤 패턴)
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """ClaudeClient 인스턴스를 가져오거나 생성하는 함수"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client