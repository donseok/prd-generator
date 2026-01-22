"""Main normalizer service for Layer 2 - Optimized version."""

from typing import List, Optional
import uuid
import logging
from datetime import datetime

from app.models import (
    ParsedContent,
    NormalizedRequirement,
    RequirementType,
    Priority,
    SourceReference,
)
from app.services import ClaudeClient, get_claude_client
from .prompts.normalization_prompts import (
    REQUIREMENT_EXTRACTION_PROMPT,
    USER_STORY_CONVERSION_PROMPT,
    CONFIDENCE_SCORING_PROMPT,
)

logger = logging.getLogger(__name__)


class Normalizer:
    """
    Layer 2: Intelligent normalization of parsed content into requirements.

    Optimized version: Single Claude call extracts all requirement data at once.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()

    async def normalize(
        self,
        parsed_contents: List[ParsedContent],
        context: dict = None,
        document_ids: List[str] = None
    ) -> List[NormalizedRequirement]:
        """
        Normalize multiple parsed contents into a unified list of requirements.

        Optimized: Single Claude call per document extracts complete requirements.
        """
        logger.info(f"[Normalizer] ===== 정규화 시작 (최적화 버전) =====")
        logger.info(f"[Normalizer] 처리할 문서 수: {len(parsed_contents)}")
        start_time = datetime.now()

        all_requirements = []
        requirement_counter = 1

        # Generate document IDs if not provided
        if document_ids is None:
            document_ids = [f"doc-{i}" for i in range(len(parsed_contents))]

        for idx, parsed_content in enumerate(parsed_contents, 1):
            filename = parsed_content.metadata.filename or "unknown"
            doc_id = document_ids[idx - 1] if idx <= len(document_ids) else f"doc-{idx}"
            logger.info(f"[Normalizer] [{idx}/{len(parsed_contents)}] 문서 처리 시작: {filename}")

            # Single Claude call to extract all requirements with full details
            requirements = await self._extract_and_normalize_all(
                parsed_content,
                requirement_counter,
                filename,
                doc_id
            )

            logger.info(f"[Normalizer] [{idx}] {len(requirements)}개 요구사항 추출 완료")

            all_requirements.extend(requirements)
            requirement_counter += len(requirements)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[Normalizer] ===== 정규화 완료 =====")
        logger.info(f"[Normalizer] 총 요구사항: {len(all_requirements)}개, 소요시간: {elapsed:.1f}초")

        return all_requirements

    async def _extract_and_normalize_all(
        self,
        parsed_content: ParsedContent,
        start_counter: int,
        source_file: str,
        document_id: str
    ) -> List[NormalizedRequirement]:
        """
        Extract and normalize all requirements in a single Claude call.

        This is the optimized method that replaces multiple Claude calls.
        """
        filename = parsed_content.metadata.filename or "unknown"
        logger.info(f"[extract_all] 통합 추출 시작: {filename}")

        # Build context from parsed content
        content_text = parsed_content.raw_text[:8000]  # Limit content size
        sections_text = "\n".join([
            f"### {s.get('title', 'Section')}\n{s.get('content', '')[:500]}"
            for s in parsed_content.sections[:10]  # Limit sections
        ])

        # Single comprehensive prompt
        prompt = f"""다음 문서에서 소프트웨어 요구사항을 추출하고 완전한 형식으로 정규화해주세요.

=== 문서 내용 ===
{content_text}

=== 구조화된 섹션 ===
{sections_text}

각 요구사항에 대해 완전한 정보를 포함한 JSON 배열로 반환해주세요:

[
  {{
    "title": "짧고 명확한 제목 (15자 이내)",
    "description": "요구사항 상세 설명",
    "type": "FR|NFR|CONSTRAINT",
    "priority": "HIGH|MEDIUM|LOW",
    "user_story": "As a [사용자], I want [기능], so that [가치]",
    "acceptance_criteria": ["검증 조건 1", "검증 조건 2"],
    "confidence_score": 0.0~1.0,
    "confidence_reason": "신뢰도 점수 부여 이유",
    "assumptions": ["가정사항 1"],
    "missing_info": ["누락 정보 1"],
    "original_text": "원본 텍스트 발췌 (100자 이내)",
    "section_name": "발견된 섹션명"
  }}
]

분류 기준:
- FR (Functional): 시스템이 해야 하는 기능
- NFR (Non-Functional): 성능, 보안, 가용성 등
- CONSTRAINT: 기술적/법적/비즈니스 제약

우선순위 기준:
- HIGH: 필수, 핵심, 긴급
- MEDIUM: 중요하지만 필수는 아님
- LOW: 선택적, 향후 구현

신뢰도 기준:
- 0.9+: 명확하고 완전
- 0.7-0.9: 양호
- 0.5-0.7: 일부 불명확
- 0.5 미만: 많이 불명확

요구사항이 없으면 빈 배열 []을 반환하세요.
JSON만 출력하세요."""

        try:
            start = datetime.now()
            result = await self.claude_client.complete_json(
                system_prompt=REQUIREMENT_EXTRACTION_PROMPT,
                user_prompt=prompt,
                temperature=0.2,
            )
            elapsed = (datetime.now() - start).total_seconds()
            logger.info(f"[extract_all] Claude 응답: {elapsed:.1f}초 소요")

            # Parse results
            if isinstance(result, dict) and "requirements" in result:
                raw_reqs = result["requirements"]
            elif isinstance(result, list):
                raw_reqs = result
            else:
                logger.warning(f"[extract_all] 예상치 못한 결과 타입: {type(result)}")
                return []

            # Convert to NormalizedRequirement objects
            requirements = []
            for idx, raw in enumerate(raw_reqs):
                try:
                    req = self._convert_to_requirement(
                        raw,
                        start_counter + idx,
                        source_file,
                        document_id
                    )
                    if req:
                        requirements.append(req)
                except Exception as e:
                    logger.warning(f"[extract_all] 요구사항 변환 실패: {e}")
                    continue

            return requirements

        except Exception as e:
            logger.error(f"[extract_all] 추출 실패: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _convert_to_requirement(
        self,
        raw: dict,
        counter: int,
        source_file: str,
        document_id: str
    ) -> Optional[NormalizedRequirement]:
        """Convert raw dict from Claude to NormalizedRequirement."""
        try:
            # Parse type
            type_str = raw.get("type", "FR").upper()
            if "NFR" in type_str or "NON" in type_str:
                req_type = RequirementType.NON_FUNCTIONAL
            elif "CONSTRAINT" in type_str:
                req_type = RequirementType.CONSTRAINT
            else:
                req_type = RequirementType.FUNCTIONAL

            # Parse priority
            priority_str = raw.get("priority", "MEDIUM").upper()
            if "HIGH" in priority_str:
                priority = Priority.HIGH
            elif "LOW" in priority_str:
                priority = Priority.LOW
            else:
                priority = Priority.MEDIUM

            # Parse confidence score
            score = raw.get("confidence_score", 0.7)
            try:
                score = max(0.0, min(1.0, float(score)))
            except (ValueError, TypeError):
                score = 0.7

            # Build source reference
            source_info = SourceReference(
                document_id=document_id,
                filename=source_file,
                section=raw.get("section_name"),
                excerpt=raw.get("original_text", "")[:200]
            )

            # Legacy source reference
            section_name = raw.get("section_name", "")
            legacy_source = source_file
            if section_name:
                legacy_source += f" [{section_name}]"

            return NormalizedRequirement(
                id=f"REQ-{counter:03d}",
                type=req_type,
                title=raw.get("title", f"요구사항 {counter}")[:50],
                description=raw.get("description", ""),
                user_story=raw.get("user_story") if req_type != RequirementType.CONSTRAINT else None,
                acceptance_criteria=raw.get("acceptance_criteria", []),
                priority=priority,
                confidence_score=score,
                confidence_reason=raw.get("confidence_reason", ""),
                source_reference=legacy_source,
                source_info=source_info,
                assumptions=raw.get("assumptions", []),
                missing_info=raw.get("missing_info", []),
            )

        except Exception as e:
            logger.error(f"[convert] 변환 실패: {e}")
            return None

    # Keep legacy methods for compatibility but they won't be used
    async def _extract_candidates(self, parsed_content: ParsedContent) -> List[dict]:
        """Legacy method - kept for compatibility."""
        return []

    async def _normalize_candidate(
        self,
        candidate: dict,
        counter: int,
        source_file: str,
        document_id: str = None
    ) -> Optional[NormalizedRequirement]:
        """Legacy method - kept for compatibility."""
        return None

    async def _generate_user_story(
        self,
        candidate: dict,
        req_type: RequirementType
    ) -> tuple[Optional[str], List[str]]:
        """Legacy method - kept for compatibility."""
        return None, []

    async def _calculate_confidence(
        self,
        candidate: dict,
        user_story: Optional[str],
        acceptance_criteria: List[str]
    ) -> dict:
        """Legacy method - kept for compatibility."""
        return {"score": 0.5, "reason": "", "assumptions": [], "missing_info": []}

    async def _identify_relationships(
        self,
        requirements: List[NormalizedRequirement]
    ) -> None:
        """Legacy method - skipped for performance."""
        pass
