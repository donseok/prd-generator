"""Claude API client service for PRD generation."""

import json
import asyncio
import base64
from typing import Optional, Any
from anthropic import AsyncAnthropic, APIError, RateLimitError

from app.config import get_settings


class ClaudeClient:
    """Wrapper for Anthropic Claude API with Korean language optimization."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
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
        Send a completion request to Claude.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message content
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Claude's response text
        """
        return await self._complete_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

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
        # Enhance system prompt for JSON output
        json_system_prompt = f"""{system_prompt}

중요: 반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트나 설명 없이 JSON만 반환합니다."""

        response = await self._complete_with_retry(
            system_prompt=json_system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

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
        base64_image = base64.standard_b64encode(image_data).decode("utf-8")

        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_image,
                },
            }
        ]

        if additional_context:
            content.append({
                "type": "text",
                "text": additional_context,
            })

        return await self._complete_with_retry(
            system_prompt=system_prompt,
            content=content,
            max_tokens=max_tokens,
            temperature=0.3,
        )

    async def _complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str = None,
        content: list = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Execute completion with retry logic for transient failures."""
        messages = []

        if content:
            messages = [{"role": "user", "content": content}]
        elif user_prompt:
            messages = [{"role": "user", "content": user_prompt}]
        else:
            raise ValueError("Either user_prompt or content must be provided")

        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages,
                    temperature=temperature,
                )
                return response.content[0].text

            except RateLimitError as e:
                last_error = e
                wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(wait_time)

            except APIError as e:
                last_error = e
                if e.status_code >= 500:  # Server error, retry
                    wait_time = self._retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    raise  # Client error, don't retry

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
