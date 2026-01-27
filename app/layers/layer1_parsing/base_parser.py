"""모든 입력 파일 파서(Parser)들이 상속받는 기본 클래스입니다.
공통적으로 필요한 기능들(AI 분석, 메타데이터 추출, 구조 감지)을 모아두었습니다.

Mixin 클래스:
- ClaudeAnalysisMixin: Claude AI를 사용해서 내용을 분석하는 기능
- MetadataExtractionMixin: 파일의 생성일, 크기 등 정보를 뽑아내는 기능
- StructureDetectionMixin: 문서의 목차나 문단 구조를 파악하는 기능
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pathlib import Path

from app.models import InputType, ParsedContent, InputMetadata
from .mixins import ClaudeAnalysisMixin, MetadataExtractionMixin, StructureDetectionMixin


class BaseParser(ABC, ClaudeAnalysisMixin, MetadataExtractionMixin, StructureDetectionMixin):
    """
    모든 파서의 부모(Base) 클래스입니다.

    모든 파서는 이 클래스를 상속받아 `parse` 메서드를 구현해야 합니다.
    """

    def __init__(self, claude_client=None):
        """
        초기화 함수.
        AI 분석 기능이 필요할 때 사용할 Claude 클라이언트를 받습니다.
        """
        self.claude_client = claude_client

    @property
    @abstractmethod
    def supported_types(self) -> list[InputType]:
        """이 파서가 처리할 수 있는 입력 타입 목록 (예: [InputType.TEXT])"""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """이 파서가 처리할 수 있는 파일 확장자 목록 (예: ['.txt', '.md'])"""
        pass

    @abstractmethod
    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """
        파일을 실제로 파싱하는 함수. (자식 클래스에서 반드시 구현해야 함)

        Args:
            file_path: 파일 경로
            metadata: 추가 정보

        Returns:
            ParsedContent: 파싱된 결과물 (텍스트, 구조 정보 등)
        """
        pass

    async def parse_bytes(
        self,
        content: bytes,
        filename: str,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """
        파일 경로가 아니라 바이너리 데이터(bytes)를 바로 파싱할 때 사용하는 함수.
        기본적으로는 임시 파일을 만들어서 `parse` 함수를 호출하는 방식으로 동작합니다.
        """
        import tempfile
        import os

        ext = Path(filename).suffix
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            return await self.parse(tmp_path, metadata)
        finally:
            # 작업 후 임시 파일 삭제
            os.unlink(tmp_path)

    async def extract_metadata(
        self,
        file_path: Path,
    ) -> InputMetadata:
        """
        파일에서 기본적인 메타데이터(파일명, 생성일, 수정일)를 추출하는 함수.
        """
        import os
        from datetime import datetime

        stat = file_path.stat()
        return InputMetadata(
            filename=file_path.name,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    async def detect_structure(self, content: str) -> dict:
        """
        텍스트 내용에서 문서 구조(섹션, 헤더)를 자동으로 감지하는 함수.
        기본적으로는 간단한 규칙(짧은 줄, #으로 시작 등)을 사용하여 헤더를 찾습니다.
        """
        lines = content.split("\n")
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 헤더 감지 로직 (단순 규칙)
            if stripped and len(stripped) < 100:
                # :로 끝나거나, 모두 대문자거나, #으로 시작하거나, 빈 줄 다음인 경우
                if (
                    stripped.endswith(":")
                    or stripped.isupper()
                    or stripped.startswith("#")
                    or (i > 0 and not lines[i-1].strip())
                ):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "title": stripped.rstrip(":").strip("#").strip(),
                        "start_line": i,
                        "content": [],
                    }
                elif current_section:
                    current_section["content"].append(line)

        if current_section:
            sections.append(current_section)

        return {
            "sections": sections,
            "line_count": len(lines),
            "char_count": len(content),
        }

    def can_parse(self, filename: str) -> bool:
        """주어진 파일명을 이 파서가 처리할 수 있는지 확인하는 함수"""
        ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
        return ext in self.supported_extensions