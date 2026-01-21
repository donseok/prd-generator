"""Main normalizer service for Layer 2."""

from typing import List, Optional
import uuid

from app.models import (
    ParsedContent,
    NormalizedRequirement,
    RequirementType,
    Priority,
)
from app.services import ClaudeClient, get_claude_client
from .prompts.normalization_prompts import (
    REQUIREMENT_EXTRACTION_PROMPT,
    USER_STORY_CONVERSION_PROMPT,
    CONFIDENCE_SCORING_PROMPT,
)


class Normalizer:
    """
    Layer 2: Intelligent normalization of parsed content into requirements.

    This is the core intelligence layer that:
    1. Extracts requirement candidates from parsed content
    2. Classifies them (FR/NFR/Constraint)
    3. Converts to user story format
    4. Scores confidence
    5. Identifies missing info and assumptions
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client or get_claude_client()

    async def normalize(
        self,
        parsed_contents: List[ParsedContent],
        context: dict = None
    ) -> List[NormalizedRequirement]:
        """
        Normalize multiple parsed contents into a unified list of requirements.

        Args:
            parsed_contents: List of parsed content from Layer 1
            context: Optional additional context

        Returns:
            List of normalized requirements
        """
        all_requirements = []
        requirement_counter = 1

        for parsed_content in parsed_contents:
            # Step 1: Extract requirement candidates using Claude
            candidates = await self._extract_candidates(parsed_content)

            for candidate in candidates:
                # Step 2: Classify and normalize
                requirement = await self._normalize_candidate(
                    candidate,
                    requirement_counter,
                    parsed_content.metadata.filename or "unknown"
                )

                if requirement:
                    all_requirements.append(requirement)
                    requirement_counter += 1

        # Step 3: Identify relationships between requirements
        if len(all_requirements) > 1:
            await self._identify_relationships(all_requirements)

        return all_requirements

    async def _extract_candidates(self, parsed_content: ParsedContent) -> List[dict]:
        """Extract requirement candidates from parsed content using Claude."""
        # Build context from parsed content
        content_text = parsed_content.raw_text
        sections_text = "\n".join([
            f"### {s.get('title', 'Section')}\n{s.get('content', '')}"
            for s in parsed_content.sections
        ])

        prompt = f"""다음 내용에서 요구사항 후보를 추출해주세요.

=== 원본 내용 ===
{content_text[:6000]}

=== 구조화된 섹션 ===
{sections_text[:2000]}

각 요구사항 후보에 대해 JSON 배열로 반환해주세요:
[
  {{
    "title": "짧은 제목",
    "description": "상세 설명",
    "original_text": "원본 텍스트",
    "type_hint": "FR/NFR/CONSTRAINT 중 추정",
    "priority_hint": "HIGH/MEDIUM/LOW 중 추정",
    "context": "발견된 맥락"
  }}
]

요구사항이 없으면 빈 배열 []을 반환하세요."""

        try:
            result = await self.claude_client.complete_json(
                system_prompt=REQUIREMENT_EXTRACTION_PROMPT,
                user_prompt=prompt,
                temperature=0.2,
            )

            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "requirements" in result:
                return result["requirements"]
            return []

        except Exception as e:
            print(f"Requirement extraction failed: {e}")
            return []

    async def _normalize_candidate(
        self,
        candidate: dict,
        counter: int,
        source_file: str
    ) -> Optional[NormalizedRequirement]:
        """Normalize a single requirement candidate."""
        try:
            # Determine requirement type
            type_hint = candidate.get("type_hint", "FR").upper()
            if "NFR" in type_hint or "NON" in type_hint:
                req_type = RequirementType.NON_FUNCTIONAL
            elif "CONSTRAINT" in type_hint:
                req_type = RequirementType.CONSTRAINT
            else:
                req_type = RequirementType.FUNCTIONAL

            # Determine priority
            priority_hint = candidate.get("priority_hint", "MEDIUM").upper()
            if "HIGH" in priority_hint:
                priority = Priority.HIGH
            elif "LOW" in priority_hint:
                priority = Priority.LOW
            else:
                priority = Priority.MEDIUM

            # Generate user story and acceptance criteria
            user_story, acceptance_criteria = await self._generate_user_story(
                candidate, req_type
            )

            # Calculate confidence score
            confidence_result = await self._calculate_confidence(
                candidate, user_story, acceptance_criteria
            )

            return NormalizedRequirement(
                id=f"REQ-{counter:03d}",
                type=req_type,
                title=candidate.get("title", f"요구사항 {counter}"),
                description=candidate.get("description", ""),
                user_story=user_story,
                acceptance_criteria=acceptance_criteria,
                priority=priority,
                confidence_score=confidence_result["score"],
                confidence_reason=confidence_result["reason"],
                source_reference=f"{source_file}: {candidate.get('context', '')}",
                assumptions=confidence_result.get("assumptions", []),
                missing_info=confidence_result.get("missing_info", []),
            )

        except Exception as e:
            print(f"Normalization failed for candidate: {e}")
            return None

    async def _generate_user_story(
        self,
        candidate: dict,
        req_type: RequirementType
    ) -> tuple[Optional[str], List[str]]:
        """Generate user story and acceptance criteria."""
        if req_type == RequirementType.CONSTRAINT:
            # Constraints don't need user stories
            return None, []

        prompt = f"""다음 요구사항을 User Story와 Acceptance Criteria로 변환해주세요.

요구사항:
제목: {candidate.get('title', '')}
설명: {candidate.get('description', '')}
원본: {candidate.get('original_text', '')}

JSON 형식으로 응답:
{{
  "user_story": "As a [사용자], I want [기능], so that [가치]",
  "acceptance_criteria": ["검증 조건 1", "검증 조건 2", ...]
}}"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt=USER_STORY_CONVERSION_PROMPT,
                user_prompt=prompt,
                temperature=0.3,
            )

            user_story = result.get("user_story")
            acceptance_criteria = result.get("acceptance_criteria", [])

            return user_story, acceptance_criteria

        except Exception as e:
            print(f"User story generation failed: {e}")
            return None, []

    async def _calculate_confidence(
        self,
        candidate: dict,
        user_story: Optional[str],
        acceptance_criteria: List[str]
    ) -> dict:
        """Calculate confidence score with detailed reasoning."""
        prompt = f"""다음 요구사항의 품질을 평가해주세요.

원본: {candidate.get('original_text', '')}
제목: {candidate.get('title', '')}
설명: {candidate.get('description', '')}
User Story: {user_story or '없음'}
Acceptance Criteria: {acceptance_criteria or '없음'}

JSON 형식으로 응답:
{{
  "score": 0.0~1.0 사이의 신뢰도 점수,
  "reason": "점수 부여 이유 (1-2문장)",
  "strengths": ["강점 1", "강점 2"],
  "weaknesses": ["약점 1", "약점 2"],
  "assumptions": ["추론한 가정 1", "추론한 가정 2"],
  "missing_info": ["누락된 정보 1", "누락된 정보 2"]
}}

평가 기준:
- 명확성: 모호하지 않고 명확한가?
- 완전성: 필요한 정보가 모두 있는가?
- 검증가능성: 테스트 가능한가?
- 추적가능성: 출처가 명확한가?"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt=CONFIDENCE_SCORING_PROMPT,
                user_prompt=prompt,
                temperature=0.1,
            )

            score = result.get("score", 0.5)
            # Ensure score is in valid range
            score = max(0.0, min(1.0, float(score)))

            return {
                "score": score,
                "reason": result.get("reason", ""),
                "assumptions": result.get("assumptions", []),
                "missing_info": result.get("missing_info", []),
            }

        except Exception as e:
            print(f"Confidence scoring failed: {e}")
            return {
                "score": 0.5,
                "reason": "신뢰도 계산 실패",
                "assumptions": [],
                "missing_info": [],
            }

    async def _identify_relationships(
        self,
        requirements: List[NormalizedRequirement]
    ) -> None:
        """Identify relationships between requirements."""
        if len(requirements) < 2:
            return

        # Build summary of all requirements
        req_summaries = "\n".join([
            f"{req.id}: {req.title}"
            for req in requirements
        ])

        prompt = f"""다음 요구사항들 간의 관계를 분석해주세요.

요구사항 목록:
{req_summaries}

JSON 형식으로 관계를 반환:
{{
  "relationships": [
    {{"from": "REQ-001", "to": "REQ-002", "type": "depends_on/related_to/conflicts_with"}}
  ]
}}

관계 유형:
- depends_on: A가 B에 의존
- related_to: A와 B가 관련됨
- conflicts_with: A와 B가 충돌"""

        try:
            result = await self.claude_client.complete_json(
                system_prompt="당신은 요구사항 간의 관계를 분석하는 전문가입니다.",
                user_prompt=prompt,
                temperature=0.2,
            )

            relationships = result.get("relationships", [])

            # Apply relationships to requirements
            for rel in relationships:
                from_id = rel.get("from")
                to_id = rel.get("to")

                for req in requirements:
                    if req.id == from_id and to_id:
                        if to_id not in req.related_requirements:
                            req.related_requirements.append(to_id)

        except Exception as e:
            print(f"Relationship identification failed: {e}")
