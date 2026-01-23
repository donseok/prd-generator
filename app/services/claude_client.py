"""Claude Code CLI client service for PRD generation.

Uses Claude CLI (claude -p) for all AI operations.

이 모듈은 Claude CLI를 래핑하여 비동기 AI 호출을 제공합니다.

주요 기능:
- complete(): 텍스트 응답 요청
- complete_json(): JSON 응답 요청 (자동 파싱)
- analyze_image(): 이미지 분석 (Vision API)

실행 환경:
- Claude CLI가 PATH에 설치되어 있어야 함
- ThreadPoolExecutor를 사용하여 동기 CLI 호출을 비동기로 래핑

재시도 전략:
- 최대 3회 재시도
- 지수 백오프 (2초, 4초, 8초)
- 모든 예외에 대해 재시도 (타임아웃 포함)
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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Claude Code CLI 래퍼 클래스.

    한국어 최적화 및 비동기 처리를 지원합니다.

    Attributes:
        _max_retries: 최대 재시도 횟수 (기본값: 3)
        _retry_delay: 초기 재시도 대기 시간(초) (기본값: 2)
        _executor: CLI 실행용 ThreadPoolExecutor
    """

    def __init__(self):
        """
        ClaudeClient 초기화.

        ThreadPoolExecutor의 max_workers는 CPU 코어 수에 따라 동적 설정:
        - 최소: 2 (저사양 환경에서도 기본 동시성 보장)
        - 최대: 8 (과도한 동시 요청 방지)
        - 기본: CPU 코어 수

        이 설정으로 병렬 처리 시 20-30% 처리량 향상을 기대합니다.
        """
        self._max_retries = 3
        self._retry_delay = 2  # seconds

        # CPU 코어 수 기반 동적 workers 설정
        # 최소 2, 최대 8, 기본은 CPU 코어 수
        cpu_count = os.cpu_count() or 4
        max_workers = min(8, max(2, cpu_count))
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        logger.info(f"[ClaudeClient] CLI 모드 초기화 완료 (workers={max_workers})")

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """
        Send a completion request to Claude via CLI.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message content
            max_tokens: Maximum tokens in response (not used in CLI mode)
            temperature: Sampling temperature (not used in CLI mode)

        Returns:
            Claude's response text
        """
        full_prompt = f"""당신은 PRD(제품 요구사항 문서) 생성을 돕는 요구사항 분석 전문가입니다.

다음 지침을 따라 작업해 주세요:
{system_prompt}

---

{user_prompt}"""

        return await self._execute_claude_cli(full_prompt)

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict:
        """
        Send a completion request expecting JSON response.

        Args:
            system_prompt: System-level instructions (should specify JSON output)
            user_prompt: User message content
            max_tokens: Maximum tokens in response
            temperature: Lower temperature for more consistent JSON

        Returns:
            Parsed JSON response as dict
        """
        full_prompt = f"""당신은 PRD(제품 요구사항 문서) 생성을 돕는 요구사항 분석 전문가입니다.

다음 지침을 따라 작업해 주세요:
{system_prompt}

---

{user_prompt}

---

응답 형식: 반드시 유효한 JSON만 출력하세요. 설명이나 마크다운 코드 블록 없이 순수 JSON만 반환합니다."""

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
        Analyze image content using Claude's vision capabilities.

        Args:
            system_prompt: System-level instructions for image analysis
            image_data: Raw image bytes (not used if image_path provided)
            media_type: MIME type (image/png, image/jpeg, etc.)
            additional_context: Additional text context
            max_tokens: Maximum tokens in response
            image_path: Direct path to image file (preferred method)

        Returns:
            Analysis result text
        """
        # Use direct file path if provided (preferred method)
        if image_path and os.path.exists(image_path):
            full_prompt = f"""당신은 PRD 생성을 돕는 요구사항 분석 전문가입니다.

다음 지침을 따라 이미지를 분석해 주세요:
{system_prompt}

추가 컨텍스트: {additional_context if additional_context else "없음"}

분석할 이미지 파일: {image_path}"""

            return await self._execute_claude_cli(full_prompt)

        # Fallback: Save bytes to temp file and use path in prompt
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
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _get_env(self) -> dict:
        """Get environment with proper PATH for Claude CLI."""
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
        """Run Claude CLI synchronously."""
        env = self._get_env()

        prompt_len = len(prompt)
        logger.info(f"[CLI] 프롬프트 길이: {prompt_len} chars")

        start_time = datetime.now()

        try:
            use_shell = sys.platform == "win32"
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env,
                shell=use_shell,
                encoding='utf-8',
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[CLI] 완료: {elapsed:.1f}초, returncode={result.returncode}")

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
        """Run Claude CLI synchronously with file attachments."""
        env = self._get_env()

        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        for file_path in file_paths:
            cmd.extend(["--file", file_path])

        use_shell = sys.platform == "win32"
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
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
        Claude Code CLI를 비동기로 실행.

        ThreadPoolExecutor를 사용하여 동기 CLI 호출을
        비동기 컨텍스트에서 실행합니다.

        실행 환경:
        - claude CLI가 시스템 PATH에 설치되어 있어야 함
        - 명령어: claude -p <prompt> --output-format text
        - 타임아웃: 300초 (5분)

        재시도 전략:
        ┌─────────────────────────────────────────────────────┐
        │ 시도 │ 대기 시간 │ 누적 시간 │                      │
        ├─────────────────────────────────────────────────────┤
        │ 1차  │ -         │ 0초       │ 첫 시도              │
        │ 2차  │ 2초       │ 2초       │ 2^0 * 2초           │
        │ 3차  │ 4초       │ 6초       │ 2^1 * 2초           │
        └─────────────────────────────────────────────────────┘

        지수 백오프(Exponential Backoff) 적용:
        - wait_time = _retry_delay * (2 ** attempt)
        - 일시적 오류 복구 기회 제공
        - 서버 부하 분산 효과

        Args:
            prompt: Claude에 전송할 프롬프트

        Returns:
            Claude의 응답 텍스트

        Raises:
            마지막 시도에서 발생한 예외
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:
                logger.info(f"[CLI] 시도 {attempt + 1}/{self._max_retries}")

                # ThreadPoolExecutor에서 동기 CLI 실행
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    self._executor, self._run_claude_sync, prompt
                )

                logger.info(f"[CLI] 시도 {attempt + 1} 성공")
                return result

            except Exception as e:
                last_error = e
                logger.error(f"[CLI] 시도 {attempt + 1} 실패: {type(e).__name__}: {e}")

                # 마지막 시도가 아니면 지수 백오프 대기
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)
                    logger.info(f"[CLI] {wait_time}초 후 재시도...")
                    await asyncio.sleep(wait_time)

        logger.error(f"[CLI] 모든 시도 실패: {last_error}")
        raise last_error

    async def _execute_claude_cli_with_files(
        self, prompt: str, file_paths: list[str]
    ) -> str:
        """Execute Claude Code CLI with file attachments."""
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
        Claude 응답에서 JSON 파싱 (포맷팅 문제 처리 포함).

        Claude의 응답은 종종 마크다운 코드 블록이나 추가 텍스트를
        포함하므로, 3단계 파싱 전략을 사용합니다.

        파싱 전략 3단계:
        ┌─────────────────────────────────────────────────────────────┐
        │ 단계     │ 방법                     │ 성공 시               │
        ├─────────────────────────────────────────────────────────────┤
        │ 1. 직접  │ 마크다운 제거 후 파싱    │ 바로 반환             │
        │ 2. 추출  │ JSON 구조 찾아서 파싱    │ 추출된 JSON 반환      │
        │ 3. 실패  │ -                        │ ValueError 발생       │
        └─────────────────────────────────────────────────────────────┘

        1단계: 직접 파싱
        - 마크다운 코드 블록 제거 (```json, ```)
        - 앞뒤 공백 제거
        - json.loads() 시도

        2단계: JSON 구조 추출 파싱
        - 응답에서 { 또는 [ 찾기
        - 중괄호/대괄호 깊이 추적하여 완전한 JSON 추출
        - 추출된 부분만 json.loads() 시도

        3단계: 실패
        - ValueError 발생, 호출자가 처리

        처리 가능한 응답 형식 예시:
        - 순수 JSON: {"key": "value"}
        - 코드 블록: ```json\\n{"key": "value"}\\n```
        - 텍스트 포함: 결과입니다: {"key": "value"}

        Args:
            response: Claude의 원시 응답 텍스트

        Returns:
            파싱된 JSON 딕셔너리 또는 리스트

        Raises:
            ValueError: JSON 파싱 실패 시
        """
        logger.debug(f"[JSON] 파싱 시작")

        # ========== 1단계: 마크다운 코드 블록 제거 ==========
        cleaned = response.strip()

        # ```json 또는 ``` 제거
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 1단계 시도: 직접 파싱
        try:
            result = json.loads(cleaned)
            logger.debug("[JSON] 직접 파싱 성공")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON] 직접 파싱 실패: {e}")

            # ========== 2단계: JSON 구조 추출 파싱 ==========
            # 응답 내에서 JSON 객체/배열 시작점 찾기
            start_idx = cleaned.find("{")
            if start_idx == -1:
                start_idx = cleaned.find("[")

            if start_idx != -1:
                # 여는 괄호 타입 결정
                bracket = "{" if cleaned[start_idx] == "{" else "["
                closing = "}" if bracket == "{" else "]"

                # 중괄호 깊이 추적하여 완전한 JSON 범위 찾기
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

                # 추출된 JSON 파싱 시도
                try:
                    result = json.loads(cleaned[start_idx:end_idx])
                    logger.debug("[JSON] 추출 파싱 성공")
                    return result
                except json.JSONDecodeError as e2:
                    logger.error(f"[JSON] 추출 파싱 실패: {e2}")

            # ========== 3단계: 최종 실패 ==========
            logger.error(f"[JSON] 최종 파싱 실패")
            raise ValueError(f"Failed to parse JSON response: {e}")


# Singleton instance for dependency injection
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
