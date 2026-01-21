"""PowerPoint file parser."""

from pathlib import Path
from typing import Optional

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import PPT_PARSING_PROMPT


class PPTParser(BaseParser):
    """Parser for PowerPoint presentations."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.POWERPOINT]

    @property
    def supported_extensions(self) -> list[str]:
        return [".pptx", ".ppt"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse PowerPoint file and extract content."""
        from pptx import Presentation

        # Load presentation
        prs = Presentation(str(file_path))

        # Extract slides
        slides_data = []
        for i, slide in enumerate(prs.slides, 1):
            slide_info = self._extract_slide_content(slide, i)
            slides_data.append(slide_info)

        # Build raw text
        raw_text = self._build_raw_text(slides_data)

        # Build metadata
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.slide_count = len(prs.slides)

        # Build sections (one per slide)
        sections = [
            {
                "title": f"슬라이드 {s['number']}: {s['title']}",
                "content": s["content"],
            }
            for s in slides_data
        ]

        # Structured data
        structured_data = {
            "slide_count": len(prs.slides),
            "slides": slides_data,
        }

        # Use Claude for analysis if available
        if self.claude_client:
            try:
                analysis = await self._analyze_with_claude(raw_text)
                structured_data["ai_analysis"] = analysis
            except Exception as e:
                print(f"Claude PPT analysis failed: {e}")

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=file_metadata,
            sections=sections,
        )

    def _extract_slide_content(self, slide, slide_number: int) -> dict:
        """Extract content from a single slide."""
        title = ""
        content_parts = []
        notes = ""

        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text_frame.text.strip()
                if text:
                    # First substantial text is usually the title
                    if not title and shape.is_placeholder:
                        if hasattr(shape, 'placeholder_format'):
                            ph_type = shape.placeholder_format.type
                            # Title placeholder types
                            if ph_type in [1, 3]:  # TITLE, CENTER_TITLE
                                title = text
                                continue
                    content_parts.append(text)

            # Handle tables
            if shape.has_table:
                table_text = self._extract_table(shape.table)
                content_parts.append(table_text)

        # Extract speaker notes
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame:
                notes = notes_frame.text.strip()

        return {
            "number": slide_number,
            "title": title or f"슬라이드 {slide_number}",
            "content": "\n".join(content_parts),
            "notes": notes,
            "has_images": any(
                shape.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE
                for shape in slide.shapes
                if hasattr(shape, 'shape_type')
            ),
        }

    def _extract_table(self, table) -> str:
        """Extract table content as text."""
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(" | ".join(cells))
        return "\n".join(rows)

    def _build_raw_text(self, slides_data: list) -> str:
        """Build raw text from slides data."""
        parts = []

        for slide in slides_data:
            parts.append(f"=== 슬라이드 {slide['number']}: {slide['title']} ===")
            if slide['content']:
                parts.append(slide['content'])
            if slide['notes']:
                parts.append(f"\n[발표자 노트]\n{slide['notes']}")
            parts.append("")

        return "\n".join(parts)

    async def _analyze_with_claude(self, raw_text: str) -> dict:
        """Use Claude to analyze PPT content."""
        result = await self.claude_client.complete_json(
            system_prompt=PPT_PARSING_PROMPT,
            user_prompt=f"다음 PPT 내용을 분석해주세요:\n\n{raw_text[:8000]}",
            temperature=0.2,
        )
        return result
