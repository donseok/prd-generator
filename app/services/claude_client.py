"""Claude Code CLI client service for PRD generation."""

import json
import subprocess
import tempfile
import os
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor


# Thread pool for running sync subprocess in async context
_executor = ThreadPoolExecutor(max_workers=4)


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
        full_prompt = f"""[시스템 지시사항]
{system_prompt}

[사용자 요청]
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
        json_system_prompt = f"""{system_prompt}

중요: 반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트나 설명 없이 JSON만 반환합니다."""

        full_prompt = f"""[시스템 지시사항]
{json_system_prompt}

[사용자 요청]
{user_prompt}"""

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
            full_prompt = f"""[시스템 지시사항]
{system_prompt}

[추가 컨텍스트]
{additional_context if additional_context else "없음"}

이미지 파일을 분석해주세요: {tmp_path}"""

            # Use claude CLI with image file
            result = await self._execute_claude_cli_with_files(full_prompt, [tmp_path])
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _run_claude_sync(self, prompt: str) -> str:
        """Run Claude CLI synchronously."""
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        return result.stdout.strip()

    def _run_claude_sync_with_files(self, prompt: str, file_paths: list[str]) -> str:
        """Run Claude CLI synchronously with file attachments."""
        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        for file_path in file_paths:
            cmd.extend(["--file", file_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        return result.stdout.strip()

    async def _execute_claude_cli(self, prompt: str) -> str:
        """Execute Claude Code CLI with the given prompt."""
        import functools
        last_error = None
        loop = asyncio.get_event_loop()

        for attempt in range(self._max_retries):
            try:
                # Run sync subprocess in thread pool using functools.partial
                func = functools.partial(self._run_claude_sync, prompt)
                result = await loop.run_in_executor(_executor, func)
                return result

            except Exception as e:
                last_error = e
                print(f"Claude CLI attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
                continue

        raise last_error

    async def _execute_claude_cli_with_files(
        self, prompt: str, file_paths: list[str]
    ) -> str:
        """Execute Claude Code CLI with file attachments."""
        import functools
        last_error = None
        loop = asyncio.get_event_loop()

        for attempt in range(self._max_retries):
            try:
                # Run sync subprocess in thread pool using functools.partial
                func = functools.partial(self._run_claude_sync_with_files, prompt, file_paths)
                result = await loop.run_in_executor(_executor, func)
                return result

            except Exception as e:
                last_error = e
                print(f"Claude CLI with files attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
                continue

        raise last_error

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from Claude's response, handling common formatting issues."""
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
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Try to find JSON object/array in the response
            start_idx = cleaned.find("{")
            if start_idx == -1:
                start_idx = cleaned.find("[")

            if start_idx != -1:
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
                    return json.loads(cleaned[start_idx:end_idx])
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"Failed to parse JSON response: {e}")


# Singleton instance for dependency injection
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
