"""Parser Mixin classes for shared functionality.

이 모듈은 Layer 1 파서들이 공통으로 사용할 수 있는
Mixin 클래스들을 정의합니다.

주요 Mixin:
- ClaudeAnalysisMixin: Claude를 사용한 문서 분석 기능
- MetadataExtractionMixin: 파일 메타데이터 추출 기능
- StructureDetectionMixin: 문서 구조 감지 기능
"""

import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.models import InputMetadata

logger = logging.getLogger(__name__)


class ClaudeAnalysisMixin:
    """
    Claude를 사용한 문서 분석 Mixin.

    파서에서 Claude API를 사용하여 문서를 분석하는
    공통 기능을 제공합니다.

    Requires:
        - self.claude_client: ClaudeClient 인스턴스
    """

    async def analyze_with_claude(
        self,
        content: str,
        analysis_prompt: str,
        system_prompt: str = "문서 분석 전문가로서 응답하세요.",
        temperature: float = 0.2,
        max_content_length: int = 6000,
    ) -> dict:
        """
        Claude를 사용하여 문서 내용 분석.

        Args:
            content: 분석할 문서 내용
            analysis_prompt: 분석 프롬프트 템플릿 ({content} 플레이스홀더 사용)
            system_prompt: 시스템 프롬프트
            temperature: 샘플링 온도
            max_content_length: 최대 내용 길이 (초과 시 잘림)

        Returns:
            분석 결과 딕셔너리. 실패 시 빈 딕셔너리.
        """
        if not hasattr(self, 'claude_client') or self.claude_client is None:
            logger.warning("[ClaudeAnalysisMixin] claude_client가 설정되지 않음")
            return {}

        # 내용 길이 제한
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            logger.debug(f"[ClaudeAnalysisMixin] 내용 잘림: {len(content)} -> {max_content_length}")

        # 프롬프트 생성
        formatted_prompt = analysis_prompt.format(content=truncated_content)

        try:
            start = datetime.now()
            result = await self.claude_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=formatted_prompt,
                temperature=temperature,
            )
            elapsed = (datetime.now() - start).total_seconds()
            logger.debug(f"[ClaudeAnalysisMixin] 분석 완료: {elapsed:.1f}초")
            return result

        except Exception as e:
            logger.warning(f"[ClaudeAnalysisMixin] 분석 실패: {e}")
            return {}

    async def extract_requirements_with_claude(
        self,
        content: str,
        additional_context: str = "",
    ) -> List[dict]:
        """
        Claude를 사용하여 문서에서 요구사항 추출.

        Args:
            content: 문서 내용
            additional_context: 추가 컨텍스트 정보

        Returns:
            추출된 요구사항 목록
        """
        prompt = """문서에서 소프트웨어 요구사항을 추출하세요.

문서:
{content}

{context}

JSON 배열로 반환:
[{{"title":"제목","description":"설명","type":"FR|NFR|CONSTRAINT","priority":"HIGH|MEDIUM|LOW"}}]

요구사항 없으면 []반환. JSON만 출력."""

        formatted_prompt = prompt.format(
            content=content[:5000],
            context=f"추가 컨텍스트: {additional_context}" if additional_context else ""
        )

        result = await self.analyze_with_claude(
            content=content,
            analysis_prompt=formatted_prompt,
            system_prompt="소프트웨어 요구사항 분석 전문가로서 응답하세요.",
        )

        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "requirements" in result:
            return result["requirements"]
        return []


class MetadataExtractionMixin:
    """
    파일 메타데이터 추출 Mixin.

    파일에서 메타데이터를 추출하는 공통 기능을 제공합니다.
    """

    def extract_file_metadata(
        self,
        file_path: Path,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> InputMetadata:
        """
        파일에서 기본 메타데이터 추출.

        Args:
            file_path: 파일 경로
            additional_metadata: 추가 메타데이터

        Returns:
            InputMetadata 인스턴스
        """
        stat = file_path.stat()

        metadata = InputMetadata(
            filename=file_path.name,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

        # 추가 메타데이터가 있으면 병합
        if additional_metadata:
            for key, value in additional_metadata.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)

        return metadata

    def calculate_file_hash(
        self,
        file_path: Path,
        algorithm: str = "md5",
    ) -> str:
        """
        파일의 해시값 계산.

        캐싱에서 변경 감지용으로 사용됩니다.

        Args:
            file_path: 파일 경로
            algorithm: 해시 알고리즘 (md5, sha256 등)

        Returns:
            해시 문자열
        """
        hasher = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()


class StructureDetectionMixin:
    """
    문서 구조 감지 Mixin.

    문서의 섹션, 헤더, 목록 등 구조를 감지하는 기능을 제공합니다.
    """

    def detect_sections(
        self,
        content: str,
        header_patterns: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        텍스트에서 섹션 구조 감지.

        기본 헤더 패턴:
        - 콜론으로 끝나는 줄 (예: "요구사항:")
        - 대문자만 있는 줄
        - # 또는 ## 마크다운 헤더
        - 빈 줄 다음의 짧은 줄

        Args:
            content: 문서 내용
            header_patterns: 추가 헤더 패턴 (정규식)

        Returns:
            섹션 목록 [{title, start_line, content: []}]
        """
        lines = content.split("\n")
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            is_header = self._is_header_line(stripped, i, lines)

            if is_header:
                if current_section:
                    sections.append(current_section)

                current_section = {
                    "title": stripped.rstrip(":").strip("#").strip(),
                    "start_line": i,
                    "content": []
                }
            elif current_section:
                current_section["content"].append(line)

        if current_section:
            sections.append(current_section)

        return sections

    def _is_header_line(
        self,
        line: str,
        line_index: int,
        all_lines: List[str],
    ) -> bool:
        """
        줄이 헤더인지 판단.

        Args:
            line: 검사할 줄
            line_index: 줄 인덱스
            all_lines: 전체 줄 목록

        Returns:
            헤더 여부
        """
        # 너무 긴 줄은 헤더가 아님
        if len(line) > 100:
            return False

        # 마크다운 헤더
        if line.startswith("#"):
            return True

        # 콜론으로 끝나는 짧은 줄
        if line.endswith(":") and len(line) < 50:
            return True

        # 대문자만 있는 줄
        if line.isupper() and len(line) > 3:
            return True

        # 빈 줄 다음의 짧은 줄
        if line_index > 0:
            prev_line = all_lines[line_index - 1].strip()
            if not prev_line and len(line) < 60:
                return True

        return False

    def detect_lists(
        self,
        content: str,
    ) -> List[dict]:
        """
        텍스트에서 목록 구조 감지.

        Args:
            content: 문서 내용

        Returns:
            목록 구조 [{type: 'bullet'|'numbered', items: [...]}]
        """
        lines = content.split("\n")
        lists = []
        current_list = None

        bullet_markers = ["-", "*", "•", "·"]
        numbered_pattern = lambda x: (
            len(x) > 2 and
            (x[0].isdigit() or x[:2].isdigit()) and
            (x[1] in ".)" or (x[1].isdigit() and x[2] in ".)"))
        )

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if current_list:
                    lists.append(current_list)
                    current_list = None
                continue

            is_bullet = any(stripped.startswith(m + " ") for m in bullet_markers)
            is_numbered = numbered_pattern(stripped)

            if is_bullet or is_numbered:
                list_type = "bullet" if is_bullet else "numbered"

                if current_list and current_list["type"] == list_type:
                    # 같은 유형의 목록 계속
                    item_text = stripped.lstrip("-*•·0123456789.)")
                    current_list["items"].append(item_text.strip())
                else:
                    # 새 목록 시작
                    if current_list:
                        lists.append(current_list)

                    item_text = stripped.lstrip("-*•·0123456789.)")
                    current_list = {
                        "type": list_type,
                        "items": [item_text.strip()]
                    }
            elif current_list:
                # 목록 종료
                lists.append(current_list)
                current_list = None

        if current_list:
            lists.append(current_list)

        return lists
