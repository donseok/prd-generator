"""Image file parser with OCR using Claude Vision."""

from pathlib import Path
from typing import Optional

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import IMAGE_PARSING_PROMPT


class ImageParser(BaseParser):
    """Parser for image files using Claude Vision for OCR and analysis."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.IMAGE]

    @property
    def supported_extensions(self) -> list[str]:
        return [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse image using Claude Vision API."""
        # Read image file
        with open(file_path, "rb") as f:
            image_data = f.read()

        # Determine media type
        ext = file_path.suffix.lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(ext, "image/png")

        # Get image dimensions
        dimensions = self._get_image_dimensions(image_data)

        # Build metadata
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.image_dimensions = dimensions

        # Use Claude Vision for analysis
        if self.claude_client:
            analysis = await self._analyze_with_vision(image_data, media_type, file_path)
        else:
            analysis = {
                "error": "Claude client not available for image analysis",
                "extracted_text": "",
                "ui_elements": [],
                "annotations": [],
            }

        # Build raw text from extracted content
        raw_text = self._build_raw_text(analysis)

        # Build sections
        sections = []
        if analysis.get("extracted_text"):
            sections.append({
                "title": "추출된 텍스트",
                "content": analysis["extracted_text"],
            })
        if analysis.get("ui_elements"):
            sections.append({
                "title": "UI 요소",
                "content": "\n".join([
                    f"- {elem.get('type', 'unknown')}: {elem.get('text', '')}"
                    for elem in analysis["ui_elements"]
                ]),
            })
        if analysis.get("inferred_requirements"):
            sections.append({
                "title": "추론된 요구사항",
                "content": "\n".join([
                    f"- {req.get('description', '')}"
                    for req in analysis["inferred_requirements"]
                ]),
            })

        return ParsedContent(
            raw_text=raw_text,
            structured_data=analysis,
            metadata=file_metadata,
            sections=sections,
        )

    def _get_image_dimensions(self, image_data: bytes) -> dict:
        """Get image dimensions without external dependencies."""
        # Try to extract from PNG header
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            width = int.from_bytes(image_data[16:20], 'big')
            height = int.from_bytes(image_data[20:24], 'big')
            return {"width": width, "height": height}

        # Try to extract from JPEG header
        if image_data[:2] == b'\xff\xd8':
            # Simplified JPEG dimension extraction
            # Full implementation would parse JPEG markers
            return {"width": 0, "height": 0}

        return {"width": 0, "height": 0}

    async def _analyze_with_vision(self, image_data: bytes, media_type: str, file_path: Path = None) -> dict:
        """Analyze image using Claude Vision API."""
        try:
            response = await self.claude_client.analyze_image(
                system_prompt=IMAGE_PARSING_PROMPT,
                image_data=image_data,
                media_type=media_type,
                additional_context="이 이미지에서 요구사항 관련 정보를 추출해주세요.",
                image_path=str(file_path) if file_path else None,
            )

            # Try to parse as JSON
            try:
                import json
                # Find JSON in response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

            # Return as text analysis
            return {
                "image_type": "unknown",
                "extracted_text": response,
                "ui_elements": [],
                "annotations": [],
                "inferred_requirements": [],
            }

        except Exception as e:
            return {
                "error": str(e),
                "extracted_text": "",
                "ui_elements": [],
                "annotations": [],
                "inferred_requirements": [],
            }

    def _build_raw_text(self, analysis: dict) -> str:
        """Build raw text from analysis results."""
        parts = []

        if analysis.get("image_type"):
            parts.append(f"이미지 유형: {analysis['image_type']}")

        if analysis.get("extracted_text"):
            parts.append("\n=== 추출된 텍스트 ===")
            text = analysis["extracted_text"]
            if isinstance(text, list):
                parts.append("\n".join(str(t) for t in text))
            else:
                parts.append(str(text))

        if analysis.get("ui_elements"):
            parts.append("\n=== UI 요소 ===")
            for elem in analysis["ui_elements"]:
                if isinstance(elem, dict):
                    parts.append(f"- {elem.get('type', 'unknown')}: {elem.get('text', '')}")
                else:
                    parts.append(f"- {str(elem)}")

        if analysis.get("annotations"):
            parts.append("\n=== 주석/마킹 ===")
            for ann in analysis["annotations"]:
                if isinstance(ann, dict):
                    parts.append(f"- {ann.get('type', '')}: {ann.get('description', '')}")
                else:
                    parts.append(f"- {str(ann)}")

        if analysis.get("inferred_requirements"):
            parts.append("\n=== 추론된 요구사항 ===")
            for req in analysis["inferred_requirements"]:
                if isinstance(req, dict):
                    conf = req.get("confidence", 0)
                    if isinstance(conf, (int, float)):
                        parts.append(f"- [{conf:.0%}] {req.get('description', '')}")
                    else:
                        parts.append(f"- {req.get('description', '')}")
                else:
                    parts.append(f"- {str(req)}")

        return "\n".join(parts)
