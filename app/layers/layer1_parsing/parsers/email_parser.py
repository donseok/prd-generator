"""이메일 파일(.eml, .msg) 파서입니다.
외부 라이브러리(mailparser)를 사용하여 이메일 헤더, 본문, 첨부파일 정보를 추출합니다.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import EMAIL_PARSING_PROMPT


class EmailParser(BaseParser):
    """이메일 및 스레드를 처리하는 파서입니다."""

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
        """이메일 파일을 읽어서 내용을 추출합니다."""
        import mailparser

        # 이메일 파싱
        mail = mailparser.parse_from_file(str(file_path))

        # 텍스트 형태의 통합 본문 생성
        raw_text = self._build_raw_text(mail)

        # 메타데이터 생성
        email_metadata = InputMetadata(
            filename=file_path.name,
            author=mail.from_[0][1] if mail.from_ else None,
            created_at=mail.date if mail.date else None,
            subject=mail.subject,
        )

        # AI(Claude) 분석 (가능한 경우)
        structured_data = await self._analyze_email(raw_text)

        # 섹션 구성 (헤더, 본문, 첨부파일)
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
        """전체 이메일 내용을 하나의 텍스트로 합칩니다."""
        parts = []

        # 헤더 정보
        parts.append(f"제목: {mail.subject or '(없음)'}")
        parts.append(f"발신자: {mail.from_}")
        parts.append(f"수신자: {mail.to}")
        if mail.cc:
            parts.append(f"참조: {mail.cc}")
        parts.append(f"날짜: {mail.date}")
        parts.append("")

        # 본문
        parts.append("=== 본문 ===")
        parts.append(mail.body or "(본문 없음)")

        return "\n".join(parts)

    def _format_headers(self, mail) -> str:
        """헤더 정보만 따로 텍스트로 만듭니다."""
        headers = []
        headers.append(f"제목: {mail.subject or '(없음)'}")
        headers.append(f"발신자: {mail.from_}")
        headers.append(f"수신자: {mail.to}")
        if mail.cc:
            headers.append(f"참조: {mail.cc}")
        headers.append(f"날짜: {mail.date}")
        return "\n".join(headers)

    async def _analyze_email(self, raw_text: str) -> dict:
        """Claude에게 이메일 내용 분석을 요청합니다 (요구사항 추출 용도)."""
        if not self.claude_client:
            return self._basic_analysis(raw_text)

        try:
            result = await self.claude_client.complete_json(
                system_prompt=EMAIL_PARSING_PROMPT,
                user_prompt=f"다음 이메일을 분석해주세요:\n\n{raw_text[:8000]}",  # 길이 제한
                temperature=0.2,
            )
            return result
        except Exception as e:
            print(f"Claude 이메일 분석 실패: {e}")
            return self._basic_analysis(raw_text)

    def _basic_analysis(self, raw_text: str) -> dict:
        """AI가 없을 때 사용하는 기본 분석 함수"""
        lines = raw_text.split("\n")

        # 기본 정보 추출
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