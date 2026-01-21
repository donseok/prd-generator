"""Document parser for Word and PDF files."""

from pathlib import Path
from typing import Optional

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import DOCUMENT_PARSING_PROMPT


class DocumentParser(BaseParser):
    """Parser for Word and PDF documents."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.DOCUMENT]

    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf", ".docx", ".doc"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse document file."""
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            raw_text, pages = self._parse_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            raw_text, pages = self._parse_word(file_path)
        else:
            raise ValueError(f"Unsupported document type: {ext}")

        # Build metadata
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.page_count = len(pages)

        # Build sections from pages
        sections = [
            {
                "title": f"페이지 {i+1}",
                "content": page,
            }
            for i, page in enumerate(pages)
        ]

        # Build structured data
        structured_data = {
            "page_count": len(pages),
            "char_count": len(raw_text),
            "document_type": ext[1:].upper(),
        }

        # Use Claude for analysis if available
        if self.claude_client:
            try:
                analysis = await self._analyze_with_claude(raw_text)
                structured_data["ai_analysis"] = analysis
            except Exception as e:
                print(f"Claude document analysis failed: {e}")

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=file_metadata,
            sections=sections,
        )

    def _parse_pdf(self, file_path: Path) -> tuple[str, list]:
        """Parse PDF file using PyPDF2."""
        from PyPDF2 import PdfReader

        reader = PdfReader(str(file_path))
        pages = []
        all_text = []

        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
            all_text.append(text)

        return "\n\n".join(all_text), pages

    def _parse_word(self, file_path: Path) -> tuple[str, list]:
        """Parse Word document using python-docx."""
        from docx import Document

        doc = Document(str(file_path))

        # Extract paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)

        # Extract tables
        tables_text = []
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(" | ".join(cells))
            tables_text.append("\n".join(table_rows))

        # Combine all text
        all_text = "\n\n".join(paragraphs)
        if tables_text:
            all_text += "\n\n=== 표 ===\n" + "\n\n".join(tables_text)

        # For Word docs, treat the whole document as one "page"
        # Could split by section breaks if needed
        return all_text, [all_text]

    async def _analyze_with_claude(self, raw_text: str) -> dict:
        """Use Claude to analyze document content."""
        result = await self.claude_client.complete_json(
            system_prompt=DOCUMENT_PARSING_PROMPT,
            user_prompt=f"다음 문서를 분석해주세요:\n\n{raw_text[:8000]}",
            temperature=0.2,
        )
        return result
