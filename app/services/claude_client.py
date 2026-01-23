"""Claude Code CLI client service for PRD generation.

Uses Claude CLI (claude -p) for all AI operations.
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
    """Wrapper for Claude Code CLI with Korean language optimization."""

    def __init__(self):
        self._max_retries = 3
        self._retry_delay = 2  # seconds
        self._executor = ThreadPoolExecutor(max_workers=2)
        logger.info("[ClaudeClient] CLI 모드 초기화 완료")

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
        """Execute Claude Code CLI with the given prompt."""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                logger.info(f"[CLI] 시도 {attempt + 1}/{self._max_retries}")

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    self._executor, self._run_claude_sync, prompt
                )

                logger.info(f"[CLI] 시도 {attempt + 1} 성공")
                return result

            except Exception as e:
                last_error = e
                logger.error(f"[CLI] 시도 {attempt + 1} 실패: {type(e).__name__}: {e}")
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
        """Parse JSON from Claude's response, handling common formatting issues."""
        logger.debug(f"[JSON] 파싱 시작")

        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
            logger.debug("[JSON] 직접 파싱 성공")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON] 직접 파싱 실패: {e}")

            # Try to find JSON object/array in the response
            start_idx = cleaned.find("{")
            if start_idx == -1:
                start_idx = cleaned.find("[")

            if start_idx != -1:
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
            raise ValueError(f"Failed to parse JSON response: {e}")


# Singleton instance for dependency injection
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
