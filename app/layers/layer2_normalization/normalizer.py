"""Layer 2: 정규화(Normalization) 서비스입니다.
파싱된 문서 내용을 AI(Claude)를 통해 구조화된 요구사항으로 변환하는 역할을 합니다.

주요 기능:
1. AI에게 문서 내용을 주고 요구사항 추출 요청
2. 여러 문서를 동시에 처리하여 속도 향상 (병렬 처리)
3. 추출된 요구사항을 표준 형식(NormalizedRequirement)으로 변환
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
    정규화 담당 클래스입니다.
    최적화된 방식(한 번의 AI 호출로 모든 정보 추출)을 사용합니다.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """AI 클라이언트 초기화"""
        self.claude_client = claude_client or get_claude_client()

    async def normalize(
        self,
        parsed_contents: List[ParsedContent],
        context: dict = None,
        document_ids: List[str] = None
    ) -> List[NormalizedRequirement]:
        """
        여러 문서를 한꺼번에 처리하여 요구사항 목록을 만듭니다.
        문서가 많을 경우 3개씩 동시에 처리하여 시간을 단축합니다.
        """
        logger.info(f"[Normalizer] ===== 정규화 시작 (병렬 처리 버전) =====")
        logger.info(f"[Normalizer] 처리할 문서 수: {len(parsed_contents)}")
        start_time = datetime.now()

        # 문서 ID가 없으면 임의로 생성
        if document_ids is None:
            document_ids = [f"doc-{i}" for i in range(len(parsed_contents))]

        # 동시에 실행할 AI 요청 수 제한 (최대 3개)
        # 너무 많이 동시에 요청하면 API 제한에 걸릴 수 있음
        semaphore = asyncio.Semaphore(3)

        async def process_document(
            idx: int,
            parsed_content: ParsedContent,
            doc_id: str,
            start_counter: int
        ) -> tuple[List[NormalizedRequirement], int]:
            """내부 함수: 하나의 문서를 처리"""
            async with semaphore:
                filename = parsed_content.metadata.filename or "unknown"
                logger.info(f"[Normalizer] [{idx}] 문서 처리 시작: {filename}")

                # AI를 통해 요구사항 추출 실행
                requirements = await self._extract_and_normalize_all(
                    parsed_content,
                    start_counter,
                    filename,
                    doc_id
                )

                logger.info(f"[Normalizer] [{idx}] {len(requirements)}개 요구사항 추출 완료")
                return requirements, len(requirements)

        # 병렬 작업을 위한 태스크 목록 준비
        estimated_reqs_per_doc = 10
        tasks = []

        for idx, (parsed_content, doc_id) in enumerate(
            zip(parsed_contents, document_ids), 1
        ):
            # ID가 겹치지 않게 시작 번호를 다르게 설정
            start_counter = 1 + (idx - 1) * estimated_reqs_per_doc
            tasks.append(process_document(idx, parsed_content, doc_id, start_counter))

        # 모든 태스크 동시 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 합치기
        all_requirements = []
        requirement_counter = 1

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[Normalizer] 문서 처리 실패: {result}")
                continue

            requirements, _ = result
            # ID를 깔끔하게 1번부터 다시 매김 (REQ-001, REQ-002...)
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
        AI(Claude)에게 문서 전체 내용을 주고 요구사항을 뽑아달라고 요청하는 함수입니다.
        JSON 형식으로 결과를 받아서 프로그램에서 쓸 수 있는 객체로 변환합니다.
        """
        filename = parsed_content.metadata.filename or "unknown"
        logger.info(f"[extract_all] 통합 추출 시작: {filename}")

        # 문서 내용이 너무 길면 앞부분만 자름 (비용 및 속도 최적화)
        content_text = parsed_content.raw_text[:6000]

        # 섹션 정보 문자열로 변환
        def get_section_content(s):
            content = s.get('content', '')
            if isinstance(content, list):
                content = "\n".join(str(c) for c in content)
            return str(content)[:300]

        sections_text = "\n".join([
            f"[{s.get('title', 'Section')}] {get_section_content(s)}"
            for s in parsed_content.sections[:8]
        ]) if parsed_content.sections else ""

        # AI에게 보낼 프롬프트(명령어) 구성 - 간결하게
        prompt = f"""문서에서 요구사항 추출. JSON배열만 반환:

문서 내용:
{content_text[:4000]}

{f"섹션: {sections_text[:1000]}" if sections_text else ""}

형식: [{{"title":"제목","description":"설명","type":"FR|NFR|CONSTRAINT","priority":"HIGH|MEDIUM|LOW","confidence_score":0.8}}]
FR=기능, NFR=비기능, CONSTRAINT=제약. JSON만."""

        try:
            start = datetime.now()
            # AI 호출 (JSON 응답 요청)
            result = await self.claude_client.complete_json(
                system_prompt=REQUIREMENT_EXTRACTION_PROMPT,
                user_prompt=prompt,
                temperature=0.2,
            )
            elapsed = (datetime.now() - start).total_seconds()
            logger.info(f"[extract_all] Claude 응답: {elapsed:.1f}초 소요")

            # 응답 결과 파싱
            if isinstance(result, dict) and "requirements" in result:
                raw_reqs = result["requirements"]
            elif isinstance(result, list):
                raw_reqs = result
            elif isinstance(result, dict) and not result:
                # 빈 딕셔너리인 경우 - AI가 JSON을 반환하지 않음
                logger.warning(f"[extract_all] AI 응답 없음, 문서에서 직접 추출 시도")
                raw_reqs = self._extract_from_content(parsed_content)
            else:
                logger.warning(f"[extract_all] 예상치 못한 결과 타입: {type(result)}")
                raw_reqs = self._extract_from_content(parsed_content)

            # 추출된 데이터를 정규화된 객체로 변환
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
            # 예외 발생 시에도 문서 내용에서 직접 추출 시도
            return self._extract_from_parsed_content(parsed_content, start_counter, source_file, document_id)

    def _convert_to_requirement(
        self,
        raw: dict,
        counter: int,
        source_file: str,
        document_id: str
    ) -> Optional[NormalizedRequirement]:
        """
        AI가 준 딕셔너리 데이터를 NormalizedRequirement 객체로 변환하는 함수입니다.
        데이터 타입을 맞추고 기본값을 채워넣습니다.
        """
        try:
            # 요구사항 타입 결정 (FR/NFR/CONSTRAINT)
            type_str = raw.get("type", "FR").upper()
            if "NFR" in type_str or "NON" in type_str:
                req_type = RequirementType.NON_FUNCTIONAL
            elif "CONSTRAINT" in type_str:
                req_type = RequirementType.CONSTRAINT
            else:
                req_type = RequirementType.FUNCTIONAL

            # 우선순위 결정
            priority_str = raw.get("priority", "MEDIUM").upper()
            if "HIGH" in priority_str:
                priority = Priority.HIGH
            elif "LOW" in priority_str:
                priority = Priority.LOW
            else:
                priority = Priority.MEDIUM

            # 신뢰도 점수 변환 (0~1 사이 값)
            score = raw.get("confidence_score", 0.7)
            try:
                score = max(0.0, min(1.0, float(score)))
            except (ValueError, TypeError):
                score = 0.7

            # 출처 정보 생성
            source_info = SourceReference(
                document_id=document_id,
                filename=source_file,
                section=raw.get("section_name"),
                excerpt=raw.get("original_text", "")[:200]
            )

            # 구버전 호환용 출처 문자열
            section_name = raw.get("section_name", "")
            legacy_source = source_file
            if section_name:
                legacy_source += f" [{section_name}]"

            # 객체 생성 및 반환
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

    def _extract_from_content(self, parsed_content: ParsedContent) -> List[dict]:
        """
        AI 응답이 없을 때 문서 내용에서 직접 요구사항을 추출합니다.
        섹션별로 분석하여 기본적인 요구사항 구조를 생성합니다.
        """
        raw_reqs = []

        # 섹션이 있으면 섹션 기반으로 추출
        if parsed_content.sections:
            for idx, section in enumerate(parsed_content.sections[:20]):  # 최대 20개
                title = section.get('title', f'요구사항 {idx + 1}')
                content = section.get('content', '')
                if isinstance(content, list):
                    content = "\n".join(str(c) for c in content)

                # 제목이 슬라이드 번호만 있으면 스킵
                if content and len(content.strip()) > 10:
                    raw_reqs.append({
                        "title": title[:50] if title else f"요구사항 {idx + 1}",
                        "description": content[:500] if content else title,
                        "type": "FR",
                        "priority": "MEDIUM",
                        "user_story": f"사용자로서, {title}을(를) 원합니다.",
                        "acceptance_criteria": [f"{title} 기능이 정상 동작해야 한다"],
                        "confidence_score": 0.6,
                        "confidence_reason": "문서 내용에서 직접 추출됨",
                        "section_name": title,
                        "original_text": content[:200] if content else "",
                    })

        # 섹션이 없으면 raw_text에서 추출
        if not raw_reqs and parsed_content.raw_text:
            lines = parsed_content.raw_text.split('\n')
            current_title = ""
            current_content = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 제목 패턴 감지 (===, ---, # 등)
                if line.startswith('===') or line.startswith('---') or line.startswith('#'):
                    if current_title and current_content:
                        raw_reqs.append({
                            "title": current_title[:50],
                            "description": "\n".join(current_content)[:500],
                            "type": "FR",
                            "priority": "MEDIUM",
                            "confidence_score": 0.5,
                        })
                    current_title = line.strip('=- #')
                    current_content = []
                else:
                    current_content.append(line)

            # 마지막 섹션 처리
            if current_title and current_content:
                raw_reqs.append({
                    "title": current_title[:50],
                    "description": "\n".join(current_content)[:500],
                    "type": "FR",
                    "priority": "MEDIUM",
                    "confidence_score": 0.5,
                })

        logger.info(f"[extract_from_content] 직접 추출된 요구사항: {len(raw_reqs)}개")
        return raw_reqs

    def _extract_from_parsed_content(
        self,
        parsed_content: ParsedContent,
        start_counter: int,
        source_file: str,
        document_id: str
    ) -> List[NormalizedRequirement]:
        """
        파싱된 콘텐츠에서 직접 요구사항 객체를 생성합니다.
        예외 발생 시 폴백으로 사용됩니다.
        """
        raw_reqs = self._extract_from_content(parsed_content)
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
                logger.warning(f"[extract_from_parsed] 변환 실패: {e}")
                continue

        return requirements