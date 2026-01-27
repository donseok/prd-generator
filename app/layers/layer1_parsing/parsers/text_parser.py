"""
텍스트 파일(.txt)과 마크다운 파일(.md) 파서입니다.
"""

from pathlib import Path
from typing import Optional

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser


class TextParser(BaseParser):
    """일반 텍스트 및 마크다운 문서를 처리하는 파서입니다."""

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
        """텍스트 파일을 읽어서 내용을 추출합니다."""
        # 파일 읽기 (UTF-8 인코딩)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        # 메타데이터 추출
        file_metadata = await self.extract_metadata(file_path)
        if metadata:
            for key, value in metadata.items():
                if hasattr(file_metadata, key):
                    setattr(file_metadata, key, value)

        # 문서 구조 감지 (헤더 등)
        structure = await self.detect_structure(raw_text)

        # 구조 정보를 바탕으로 섹션 나누기
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
        """
        마크다운 문법을 고려하여 문서 구조를 파악합니다.
        (예: # 헤더, 코드 블록 ``` 등)
        """
        lines = content.split("\n")
        sections = []
        current_section = None
        in_code_block = False # 코드 블록 안인지 여부 체크

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 코드 블록 감지 (```)
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            # 코드 블록 안 내용은 헤더로 인식하지 않음
            if in_code_block:
                if current_section:
                    current_section["content"].append(line)
                continue

            # 마크다운 헤더 감지 (#, ##, ...)
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
            # 밑줄 스타일 헤더 감지 (===, ---)
            elif i > 0 and stripped and set(stripped) in [{"="}, {"-"}]:
                prev_line = lines[i-1].strip()
                if prev_line and len(prev_line) < 100:
                    if current_section:
                        # 이전 줄은 내용이 아니라 제목이었으므로 내용에서 제거
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
                # 첫 헤더가 나오기 전의 내용은 'Introduction' 섹션으로 간주
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