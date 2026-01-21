"""Text and markdown file parser."""

from pathlib import Path
from typing import Optional

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser


class TextParser(BaseParser):
    """Parser for plain text and markdown files."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.TEXT]

    @property
    def supported_extensions(self) -> list[str]:
        return [".txt", ".md", ".markdown", ".text"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse text file and extract content."""
        # Read file content
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        # Extract metadata
        file_metadata = await self.extract_metadata(file_path)
        if metadata:
            for key, value in metadata.items():
                if hasattr(file_metadata, key):
                    setattr(file_metadata, key, value)

        # Detect structure
        structure = await self.detect_structure(raw_text)

        # Build sections from structure
        sections = []
        for sec in structure.get("sections", []):
            sections.append({
                "title": sec["title"],
                "content": "\n".join(sec.get("content", [])),
            })

        return ParsedContent(
            raw_text=raw_text,
            structured_data={
                "line_count": structure.get("line_count", 0),
                "char_count": structure.get("char_count", 0),
                "is_markdown": file_path.suffix.lower() in [".md", ".markdown"],
            },
            metadata=file_metadata,
            sections=sections,
        )

    async def detect_structure(self, content: str) -> dict:
        """Detect text structure with markdown awareness."""
        lines = content.split("\n")
        sections = []
        current_section = None
        in_code_block = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                if current_section:
                    current_section["content"].append(line)
                continue

            # Detect markdown headers
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                title = stripped.lstrip("#").strip()
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": title,
                    "level": level,
                    "start_line": i,
                    "content": []
                }
            # Detect underline-style headers
            elif i > 0 and stripped and set(stripped) in [{"="}, {"-"}]:
                prev_line = lines[i-1].strip()
                if prev_line and len(prev_line) < 100:
                    if current_section:
                        # Remove the header from content
                        if current_section["content"]:
                            current_section["content"].pop()
                        sections.append(current_section)
                    current_section = {
                        "title": prev_line,
                        "level": 1 if "=" in stripped else 2,
                        "start_line": i - 1,
                        "content": []
                    }
            elif current_section:
                current_section["content"].append(line)
            elif stripped:
                # Start implicit first section
                current_section = {
                    "title": "Introduction",
                    "level": 1,
                    "start_line": i,
                    "content": [line]
                }

        if current_section:
            sections.append(current_section)

        return {
            "sections": sections,
            "line_count": len(lines),
            "char_count": len(content),
        }
