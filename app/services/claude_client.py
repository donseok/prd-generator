"""Claude Code CLI client service for PRD generation."""

import json
import subprocess
import tempfile
import os
import asyncio
import logging
from typing import Optional
from datetime import datetime

# 상세 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """Wrapper for Claude Code CLI with Korean language optimization."""

    def __init__(self):
        self._max_retries = 3
        self._retry_delay = 2  # seconds

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
        # Claude Code CLI에 맞는 자연스러운 프롬프트 형식
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
        # Claude Code CLI에 맞는 자연스러운 프롬프트 형식
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
    ) -> str:
        """
        Analyze image content using Claude's vision capabilities.

        Args:
            system_prompt: System-level instructions for image analysis
            image_data: Raw image bytes
            media_type: MIME type (image/png, image/jpeg, etc.)
            additional_context: Additional text context
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result text
        """
        # Save image to temporary file
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

첨부된 이미지 파일을 분석해주세요."""

            # Use claude CLI with image file
            result = await self._execute_claude_cli_with_files(full_prompt, [tmp_path])
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _run_claude_sync(self, prompt: str) -> str:
        """Run Claude CLI synchronously."""
        # Get current environment and ensure PATH includes common locations
        env = os.environ.copy()
        extra_paths = [
            os.path.expanduser("~/.npm-global/bin"),
            "/usr/local/bin",
            "/opt/homebrew/bin",
        ]
        env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "")

        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
        logger.info(f"[CLI] 프롬프트 길이: {len(prompt)} chars")
        logger.debug(f"[CLI] 프롬프트 미리보기: {prompt_preview}")

        start_time = datetime.now()
        logger.info(f"[CLI] subprocess 시작: {start_time.strftime('%H:%M:%S')}")

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env,
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[CLI] subprocess 완료: {elapsed:.1f}초 소요, returncode={result.returncode}")

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"[CLI] 에러 발생: {error_msg}")
                logger.error(f"[CLI] stdout: {result.stdout[:500] if result.stdout else 'empty'}")
                raise RuntimeError(f"Claude CLI error: {error_msg}")

            response_preview = result.stdout[:300] if result.stdout else "empty"
            logger.info(f"[CLI] 응답 길이: {len(result.stdout)} chars")
            logger.debug(f"[CLI] 응답 미리보기: {response_preview}...")

            return result.stdout.strip()

        except subprocess.TimeoutExpired as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"[CLI] 타임아웃! {elapsed:.1f}초 후 타임아웃")
            raise

    def _run_claude_sync_with_files(self, prompt: str, file_paths: list[str]) -> str:
        """Run Claude CLI synchronously with file attachments."""
        # Get current environment and ensure PATH includes common locations
        env = os.environ.copy()
        extra_paths = [
            os.path.expanduser("~/.npm-global/bin"),
            "/usr/local/bin",
            "/opt/homebrew/bin",
        ]
        env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "")

        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        for file_path in file_paths:
            cmd.extend(["--file", file_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
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
                logger.info(f"[execute] 시도 {attempt + 1}/{self._max_retries} 시작")
                result = await asyncio.to_thread(self._run_claude_sync, prompt)
                logger.info(f"[execute] 시도 {attempt + 1} 성공!")
                return result

            except Exception as e:
                last_error = e
                logger.error(f"[execute] 시도 {attempt + 1} 실패: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)
                    logger.info(f"[execute] {wait_time}초 후 재시도...")
                    await asyncio.sleep(wait_time)
                continue

        logger.error(f"[execute] 모든 시도 실패! 마지막 에러: {last_error}")
        raise last_error

    async def _execute_claude_cli_with_files(
        self, prompt: str, file_paths: list[str]
    ) -> str:
        """Execute Claude Code CLI with file attachments."""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                print(f"[ClaudeClient] Executing CLI with files (attempt {attempt + 1})...")
                result = await asyncio.to_thread(
                    self._run_claude_sync_with_files, prompt, file_paths
                )
                print(f"[ClaudeClient] CLI with files completed successfully")
                return result

            except Exception as e:
                last_error = e
                print(f"[ClaudeClient] CLI with files attempt {attempt + 1} failed: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
                continue

        raise last_error

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from Claude's response, handling common formatting issues."""
        logger.info(f"[JSON] 파싱 시작, 응답 길이: {len(response)} chars")

        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
            logger.debug("[JSON] ```json 제거")
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
            logger.debug("[JSON] ``` 제거")
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            logger.debug("[JSON] 끝 ``` 제거")
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
            logger.info(f"[JSON] 직접 파싱 성공! 타입: {type(result).__name__}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON] 직접 파싱 실패: {e}")
            logger.debug(f"[JSON] 정리된 응답 미리보기: {cleaned[:300]}...")

            # Try to find JSON object/array in the response
            start_idx = cleaned.find("{")
            if start_idx == -1:
                start_idx = cleaned.find("[")

            if start_idx != -1:
                logger.info(f"[JSON] JSON 시작 위치 발견: {start_idx}")
                # Find matching closing bracket
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
                    logger.info(f"[JSON] 추출 파싱 성공! 타입: {type(result).__name__}")
                    return result
                except json.JSONDecodeError as e2:
                    logger.error(f"[JSON] 추출 파싱도 실패: {e2}")
                    logger.error(f"[JSON] 추출된 부분: {cleaned[start_idx:end_idx][:200]}...")

            logger.error(f"[JSON] 최종 파싱 실패! 원본 응답: {response[:500]}...")
            raise ValueError(f"Failed to parse JSON response: {e}")


# Singleton instance for dependency injection
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
