"""Email file parser (.eml, .msg)."""

from pathlib import Path
from typing import Optional
from datetime import datetime

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import EMAIL_PARSING_PROMPT


class EmailParser(BaseParser):
    """Parser for email files and threads."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.EMAIL]

    @property
    def supported_extensions(self) -> list[str]:
        return [".eml", ".msg"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse email file and extract structured content."""
        import mailparser

        # Parse email
        mail = mailparser.parse_from_file(str(file_path))

        # Build raw text representation
        raw_text = self._build_raw_text(mail)

        # Extract metadata
        email_metadata = InputMetadata(
            filename=file_path.name,
            author=mail.from_[0][1] if mail.from_ else None,
            created_at=mail.date if mail.date else None,
            subject=mail.subject,
        )

        # Use Claude to analyze email structure if available
        structured_data = await self._analyze_email(raw_text)

        # Build sections
        sections = [
            {"title": "헤더 정보", "content": self._format_headers(mail)},
            {"title": "본문", "content": mail.body or ""},
        ]

        if mail.attachments:
            sections.append({
                "title": "첨부파일",
                "content": "\n".join([att.get("filename", "unknown") for att in mail.attachments])
            })

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=email_metadata,
            sections=sections,
        )

    def _build_raw_text(self, mail) -> str:
        """Build raw text representation of email."""
        parts = []

        # Headers
        parts.append(f"제목: {mail.subject or '(없음)'}")
        parts.append(f"발신자: {mail.from_}")
        parts.append(f"수신자: {mail.to}")
        if mail.cc:
            parts.append(f"참조: {mail.cc}")
        parts.append(f"날짜: {mail.date}")
        parts.append("")

        # Body
        parts.append("=== 본문 ===")
        parts.append(mail.body or "(본문 없음)")

        return "\n".join(parts)

    def _format_headers(self, mail) -> str:
        """Format email headers as text."""
        headers = []
        headers.append(f"제목: {mail.subject or '(없음)'}")
        headers.append(f"발신자: {mail.from_}")
        headers.append(f"수신자: {mail.to}")
        if mail.cc:
            headers.append(f"참조: {mail.cc}")
        headers.append(f"날짜: {mail.date}")
        return "\n".join(headers)

    async def _analyze_email(self, raw_text: str) -> dict:
        """Use Claude to analyze email thread structure."""
        if not self.claude_client:
            return self._basic_analysis(raw_text)

        try:
            result = await self.claude_client.complete_json(
                system_prompt=EMAIL_PARSING_PROMPT,
                user_prompt=f"다음 이메일을 분석해주세요:\n\n{raw_text[:8000]}",  # Limit size
                temperature=0.2,
            )
            return result
        except Exception as e:
            print(f"Claude email analysis failed: {e}")
            return self._basic_analysis(raw_text)

    def _basic_analysis(self, raw_text: str) -> dict:
        """Basic email analysis without AI."""
        lines = raw_text.split("\n")

        # Extract basic info
        subject = ""
        sender = ""
        for line in lines:
            if line.startswith("제목:"):
                subject = line[3:].strip()
            elif line.startswith("발신자:"):
                sender = line[4:].strip()

        return {
            "thread_summary": subject,
            "participants": [{"email": sender, "inferred_role": "unknown"}] if sender else [],
            "decisions": [],
            "open_discussions": [],
            "requirement_candidates": [],
            "priority_signals": [],
        }
