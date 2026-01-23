"""Main normalizer service for Layer 2 - Optimized version.

Layer 2: 정규화 서비스
파싱된 문서 내용을 구조화된 요구사항으로 변환합니다.

최적화 전략:
- 단일 Claude 호출로 문서당 모든 요구사항 추출 (기존 다중 호출 대비 개선)
- 다중 문서 병렬 처리: asyncio.gather() + Semaphore(3)
- 예상 효과: 5개 문서 기준 80% 시간 단축

처리 흐름:
1. 각 ParsedContent에서 텍스트 추출
2. Claude에 요구사항 추출 요청 (JSON 응답)
3. JSON 결과를 NormalizedRequirement 객체로 변환
4. 전체 요구사항 목록 반환
"""

import asyncio
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
        다중 문서를 통합 요구사항 목록으로 정규화 (병렬 처리).

        최적화 전략:
        - 문서당 단일 Claude 호출로 모든 요구사항 추출
        - 다중 문서 병렬 처리 (Semaphore(3)으로 동시 처리 제한)

        Args:
            parsed_contents: 파싱된 컨텐츠 목록
            context: 추가 컨텍스트 (사용하지 않음)
            document_ids: 문서 ID 목록 (없으면 자동 생성)

        Returns:
            정규화된 요구사항 목록
        """
        logger.info(f"[Normalizer] ===== 정규화 시작 (병렬 처리 버전) =====")
        logger.info(f"[Normalizer] 처리할 문서 수: {len(parsed_contents)}")
        start_time = datetime.now()

        # 문서 ID 생성
        if document_ids is None:
            document_ids = [f"doc-{i}" for i in range(len(parsed_contents))]

        # 동시 정규화 수 제한 (최대 3개)
        # Claude API 호출이 포함되므로 파싱보다 낮은 동시성 사용
        semaphore = asyncio.Semaphore(3)

        async def process_document(
            idx: int,
            parsed_content: ParsedContent,
            doc_id: str,
            start_counter: int
        ) -> tuple[List[NormalizedRequirement], int]:
            """
            단일 문서 정규화 (세마포어 적용).

            Returns:
                (요구사항 목록, 다음 카운터 시작값)
            """
            async with semaphore:
                filename = parsed_content.metadata.filename or "unknown"
                logger.info(f"[Normalizer] [{idx}] 문서 처리 시작: {filename}")

                requirements = await self._extract_and_normalize_all(
                    parsed_content,
                    start_counter,
                    filename,
                    doc_id
                )

                logger.info(f"[Normalizer] [{idx}] {len(requirements)}개 요구사항 추출 완료")
                return requirements, len(requirements)

        # 요구사항 ID 카운터 계산을 위한 예비 할당
        # 각 문서에 예상 요구사항 수(10개)만큼 ID 범위 할당
        estimated_reqs_per_doc = 10
        tasks = []

        for idx, (parsed_content, doc_id) in enumerate(
            zip(parsed_contents, document_ids), 1
        ):
            start_counter = 1 + (idx - 1) * estimated_reqs_per_doc
            tasks.append(process_document(idx, parsed_content, doc_id, start_counter))

        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 병합 및 ID 재할당
        all_requirements = []
        requirement_counter = 1

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[Normalizer] 문서 처리 실패: {result}")
                continue

            requirements, _ = result
            # ID 재할당으로 연속성 보장
            for req in requirements:
                req.id = f"REQ-{requirement_counter:03d}"
                all_requirements.append(req)
                requirement_counter += 1

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
        단일 Claude 호출로 문서의 모든 요구사항을 추출하고 정규화.

        이 메서드는 기존의 다중 Claude 호출 방식을 대체하여
        성능을 크게 향상시킵니다.

        처리 흐름:
        1. 문서 내용 준비 (raw_text + sections, 최대 6000자)
        2. JSON 응답 요청 프롬프트 구성
        3. Claude 호출 (complete_json)
        4. JSON 결과를 NormalizedRequirement 객체로 변환

        요청 JSON 구조:
        ```json
        [{
            "title": "요구사항 제목",
            "description": "상세 설명",
            "type": "FR|NFR|CONSTRAINT",
            "priority": "HIGH|MEDIUM|LOW",
            "user_story": "As a X, I want Y, so that Z",
            "acceptance_criteria": ["조건1", "조건2"],
            "confidence_score": 0.8,
            "confidence_reason": "신뢰도 판단 이유",
            "assumptions": ["가정1"],
            "missing_info": ["누락 정보"],
            "original_text": "원본 텍스트",
            "section_name": "출처 섹션"
        }]
        ```

        타입 분류 기준:
        - FR (Functional): 시스템이 수행해야 하는 기능
        - NFR (Non-Functional): 성능, 보안, 확장성 등 품질 속성
        - CONSTRAINT: 기술 스택, 환경 제약 등 제한 조건

        confidence_score 기준 (0.0 ~ 1.0):
        - 1.0: 명확한 요구사항, 측정 가능한 기준 포함
        - 0.8: 대부분 명확하나 일부 세부사항 부족
        - 0.6: 모호한 표현 포함, 추가 확인 필요
        - 0.4 이하: 매우 모호하거나 불완전

        Args:
            parsed_content: 파싱된 문서 내용
            start_counter: 요구사항 ID 시작 번호
            source_file: 원본 파일명
            document_id: 문서 ID

        Returns:
            NormalizedRequirement 객체 목록

        Raises:
            예외 발생 시 빈 목록 반환 (로깅 후 계속 진행)
        """
        filename = parsed_content.metadata.filename or "unknown"
        logger.info(f"[extract_all] 통합 추출 시작: {filename}")

        # Build context from parsed content (optimized size)
        content_text = parsed_content.raw_text[:6000]  # Reduced for faster processing

        def get_section_content(s):
            """Safely extract section content as string."""
            content = s.get('content', '')
            if isinstance(content, list):
                content = "\n".join(str(c) for c in content)
            return str(content)[:300]

        sections_text = "\n".join([
            f"[{s.get('title', 'Section')}] {get_section_content(s)}"
            for s in parsed_content.sections[:8]
        ]) if parsed_content.sections else ""

        # Optimized prompt - shorter and more focused
        prompt = f"""문서에서 소프트웨어 요구사항을 추출하세요.

문서:
{content_text}

{f"섹션: {sections_text}" if sections_text else ""}

JSON 배열로 반환:
[{{"title":"제목","description":"설명","type":"FR|NFR|CONSTRAINT","priority":"HIGH|MEDIUM|LOW","user_story":"As a X, I want Y, so that Z","acceptance_criteria":["조건1"],"confidence_score":0.8,"confidence_reason":"이유","assumptions":[],"missing_info":[],"original_text":"원문","section_name":"섹션"}}]

- FR: 기능 요구사항
- NFR: 비기능(성능/보안)
- CONSTRAINT: 제약조건
- confidence_score: 0.0~1.0 (명확할수록 높음)

요구사항 없으면 []반환. JSON만 출력."""

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
