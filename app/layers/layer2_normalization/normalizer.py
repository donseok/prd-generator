"""Layer 2: 정규화(Normalization) 서비스입니다.
파싱된 문서 내용을 AI(Claude)를 통해 구조화된 요구사항으로 변환하는 역할을 합니다.

주요 기능:
1. AI에게 문서 내용을 주고 요구사항 추출 요청
2. 여러 문서를 동시에 처리하여 속도 향상 (병렬 처리)
3. 추출된 요구사항을 표준 형식(NormalizedRequirement)으로 변환
4. 다층 신뢰도 계산 (출처/명확성/완전성/AI 신뢰도 종합)
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
from .confidence_calculator import get_confidence_calculator, ConfidenceBreakdown

logger = logging.getLogger(__name__)


class Normalizer:
    """
    정규화 담당 클래스입니다.
    최적화된 방식(한 번의 AI 호출로 모든 정보 추출)을 사용합니다.
    다층 신뢰도 계산을 통해 요구사항 품질을 정밀하게 평가합니다.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """AI 클라이언트 및 신뢰도 계산기 초기화"""
        self.claude_client = claude_client or get_claude_client()
        self.confidence_calculator = get_confidence_calculator()

    async def normalize(
        self,
        parsed_contents: List[ParsedContent],
        context: dict = None,
        document_ids: List[str] = None
    ) -> List[NormalizedRequirement]:
        """
        여러 문서를 한꺼번에 처리하여 요구사항 목록을 만듭니다.
        문서가 많을 경우 3개씩 동시에 처리하여 시간을 단축합니다.

        Args:
            parsed_contents: 파싱된 문서 목록
            context: 추가 컨텍스트 정보
                - source_types: 문서별 출처 유형 리스트 (text, email, chat 등)
            document_ids: 문서 ID 목록
        """
        logger.info(f"[Normalizer] ===== 정규화 시작 (병렬 처리 + 다층 신뢰도) =====")
        logger.info(f"[Normalizer] 처리할 문서 수: {len(parsed_contents)}")
        start_time = datetime.now()

        # 문서 ID가 없으면 임의로 생성
        if document_ids is None:
            document_ids = [f"doc-{i}" for i in range(len(parsed_contents))]

        # context에서 source_types 추출 (없으면 파일명에서 추론)
        context = context or {}
        source_types = context.get("source_types", [])

        # 동시에 실행할 AI 요청 수 제한 (최대 3개)
        # 너무 많이 동시에 요청하면 API 제한에 걸릴 수 있음
        semaphore = asyncio.Semaphore(3)

        async def process_document(
            idx: int,
            parsed_content: ParsedContent,
            doc_id: str,
            start_counter: int,
            source_type: str
        ) -> tuple[List[NormalizedRequirement], int]:
            """내부 함수: 하나의 문서를 처리"""
            async with semaphore:
                filename = parsed_content.metadata.filename or "unknown"
                logger.info(f"[Normalizer] [{idx}] 문서 처리 시작: {filename} (출처: {source_type})")

                # AI를 통해 요구사항 추출 실행 (다층 신뢰도 계산 포함)
                requirements = await self._extract_and_normalize_all(
                    parsed_content,
                    start_counter,
                    filename,
                    doc_id,
                    source_type
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

            # source_type 결정 (context에서 가져오거나 파일명에서 추론)
            if idx - 1 < len(source_types):
                source_type = source_types[idx - 1]
            else:
                source_type = self._infer_source_type(parsed_content)

            tasks.append(process_document(idx, parsed_content, doc_id, start_counter, source_type))

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

    def _infer_source_type(self, parsed_content: ParsedContent) -> str:
        """
        파일명이나 메타데이터에서 문서 유형을 추론합니다.
        """
        filename = (parsed_content.metadata.filename or "").lower()

        # 확장자 기반 추론
        if filename.endswith(('.docx', '.doc', '.pdf')):
            return "document"
        elif filename.endswith(('.xlsx', '.xls')):
            return "excel"
        elif filename.endswith('.csv'):
            return "csv"
        elif filename.endswith(('.pptx', '.ppt')):
            return "ppt"
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return "image"
        elif filename.endswith(('.eml', '.msg')) or 'email' in filename:
            return "email"
        elif 'chat' in filename or 'slack' in filename or 'kakao' in filename:
            return "chat"
        elif filename.endswith(('.txt', '.md')):
            return "text"

        # 메타데이터 기반 추론
        if parsed_content.metadata.subject:  # 이메일 제목이 있으면
            return "email"
        if parsed_content.metadata.slide_count:  # 슬라이드 수가 있으면
            return "ppt"
        if parsed_content.metadata.sheet_names:  # 시트 이름이 있으면
            return "excel"
        if parsed_content.metadata.participants:  # 참여자가 있으면
            return "chat"
        if parsed_content.metadata.image_dimensions:  # 이미지 크기가 있으면
            return "image"

        return "text"  # 기본값

    async def _extract_and_normalize_all(
        self,
        parsed_content: ParsedContent,
        start_counter: int,
        source_file: str,
        document_id: str,
        source_type: str = "text"
    ) -> List[NormalizedRequirement]:
        """
        AI(Claude)에게 문서 전체 내용을 주고 요구사항을 뽑아달라고 요청하는 함수입니다.
        JSON 형식으로 결과를 받아서 프로그램에서 쓸 수 있는 객체로 변환합니다.
        다층 신뢰도 계산을 적용합니다.
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

        # 문서 유형 힌트 생성
        doc_type_hint = self._get_doc_type_hint(source_type, content_text)

        # AI에게 보낼 프롬프트(명령어) 구성
        prompt = f"""다음 문서에서 **실제 소프트웨어 요구사항만** 추출하세요. JSON으로 반환.

## 문서 유형: {doc_type_hint}

## ⛔ 필터링 규칙
참석자/서기/장소/날짜/인사말/목차/섹션제목만 있는 항목/소개글은 절대 추출하지 마세요.

## 문서 내용:
{content_text[:6000]}

{f"## 섹션 구조:{chr(10)}{sections_text[:1500]}" if sections_text else ""}

## 출력 형식:
{{"requirements": [{{"title":"동사형 제목","description":"상세 설명","type":"FR|NFR|CONSTRAINT","module":"기능 모듈명","priority":"HIGH|MEDIUM|LOW","confidence_score":0.0~1.0,"confidence_reason":"근거","user_story":"As a [역할], I want [기능], so that [가치]","acceptance_criteria":["Given ..., When ..., Then ..."],"section_name":"출처","original_text":"원문","assumptions":[],"missing_info":[]}}]}}

FR=기능, NFR=비기능(수치 정량화 필수), CONSTRAINT=제약. JSON만 반환."""

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

            # 추출된 데이터를 정규화된 객체로 변환 (다층 신뢰도 적용)
            requirements = []
            for idx, raw in enumerate(raw_reqs):
                try:
                    req = self._convert_to_requirement(
                        raw,
                        start_counter + idx,
                        source_file,
                        document_id,
                        source_type
                    )
                    if req:
                        requirements.append(req)
                except Exception as e:
                    logger.warning(f"[extract_all] 요구사항 변환 실패: {e}")
                    continue

            return requirements

        except Exception as e:
            logger.error(f"[extract_all] 추출 실패: {type(e).__name__}: {e}", exc_info=True)
            # 예외 발생 시에도 문서 내용에서 직접 추출 시도
            return self._extract_from_parsed_content(parsed_content, start_counter, source_file, document_id, source_type)

    def _convert_to_requirement(
        self,
        raw: dict,
        counter: int,
        source_file: str,
        document_id: str,
        source_type: str = "text"
    ) -> Optional[NormalizedRequirement]:
        """
        AI가 준 딕셔너리 데이터를 NormalizedRequirement 객체로 변환하는 함수입니다.
        다층 신뢰도 계산을 적용하여 정밀한 품질 평가를 수행합니다.
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

            # AI 신뢰도 추출 (기본값 0.7)
            ai_confidence = raw.get("confidence_score", 0.7)
            try:
                ai_confidence = max(0.0, min(1.0, float(ai_confidence)))
            except (ValueError, TypeError):
                ai_confidence = 0.7

            # 다층 신뢰도 계산
            confidence_breakdown = self.confidence_calculator.calculate(
                raw_requirement=raw,
                source_type=source_type,
                ai_confidence=ai_confidence
            )

            # 최종 신뢰도와 상세 사유
            final_score = confidence_breakdown.final_score
            confidence_reason = self._build_confidence_reason(confidence_breakdown, raw)

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

            # 모듈 정보 추출
            feature_module = raw.get("module") or raw.get("feature_module")

            # 객체 생성 및 반환
            return NormalizedRequirement(
                id=f"REQ-{counter:03d}",
                type=req_type,
                title=raw.get("title", f"요구사항 {counter}")[:50],
                description=raw.get("description", ""),
                user_story=raw.get("user_story") if req_type != RequirementType.CONSTRAINT else None,
                acceptance_criteria=raw.get("acceptance_criteria", []),
                priority=priority,
                confidence_score=final_score,
                confidence_reason=confidence_reason,
                source_reference=legacy_source,
                source_info=source_info,
                assumptions=raw.get("assumptions", []),
                missing_info=raw.get("missing_info", []),
                feature_module=feature_module,
            )

        except Exception as e:
            logger.error(f"[convert] 변환 실패: {e}")
            return None

    def _build_confidence_reason(self, breakdown: ConfidenceBreakdown, raw: dict) -> str:
        """
        신뢰도 계산 결과를 사람이 읽기 좋은 문자열로 변환합니다.
        """
        parts = []

        # 점수 요약 (높은 신뢰도면 간략히, 낮으면 상세히)
        if breakdown.final_score >= 0.8:
            parts.append(f"신뢰도 양호 ({breakdown.final_score:.0%})")
        else:
            # 상세 점수 표시
            parts.append(
                f"출처:{breakdown.source_credibility:.0%} "
                f"명확성:{breakdown.clarity_score:.0%} "
                f"완전성:{breakdown.completeness_score:.0%}"
            )

        # 감점 사유 추가
        if breakdown.deduction_reasons:
            parts.append(breakdown.to_reason_string())

        # AI가 제공한 원본 사유도 포함 (있으면)
        ai_reason = raw.get("confidence_reason", "")
        if ai_reason and len(ai_reason) > 5:
            parts.append(f"AI: {ai_reason[:50]}")

        return " | ".join(parts)

    def _get_doc_type_hint(self, source_type: str, content_text: str) -> str:
        """문서 유형에 따른 추출 전략 힌트를 생성합니다."""
        content_lower = content_text[:2000].lower()

        # 내용 기반 자동 감지 (source_type보다 우선)
        meeting_keywords = ["회의록", "참석자", "서기", "결정사항", "action item", "합의", "논의"]
        interview_keywords = ["인터뷰", "면담", "현장", "불편", "pain point"]
        rfp_keywords = ["rfp", "제안요청", "요구사항정의", "요구사항 명세"]

        meeting_score = sum(1 for kw in meeting_keywords if kw in content_lower)
        interview_score = sum(1 for kw in interview_keywords if kw in content_lower)
        rfp_score = sum(1 for kw in rfp_keywords if kw in content_lower)

        if meeting_score >= 2:
            return "회의록/회의 기록 → 결정사항, Action Item, 합의된 요구사항에 집중. 참석자/장소/인사말 제외"
        elif interview_score >= 2:
            return "인터뷰/현장 메모 → Pain Point에서 요구사항 도출. 사용자 발언에서 핵심 니즈 추출"
        elif rfp_score >= 1:
            return "정형 문서(RFP/요구사항정의서) → 항목별 체계적 추출"
        elif source_type == "email":
            return "이메일 → 요청사항, 결정사항, 작업 지시에 집중"
        elif source_type == "chat":
            return "채팅/메시지 → 요청, 합의, 결정에 해당하는 내용만 추출"
        elif source_type in ("ppt", "excel"):
            return f"{source_type.upper()} 문서 → 슬라이드/시트별 핵심 요구사항 추출. 장식적 텍스트 제외"
        else:
            return "일반 문서 → 시스템 기능, 성능, 제약사항에 해당하는 내용 추출"

    # 폴백 시 필터링할 비-요구사항 키워드
    _SKIP_TITLES = {
        "introduction", "서론", "개요", "목차", "배경", "참석자", "서기",
        "agenda", "table of contents", "appendix", "부록", "약어",
        "용어 정의", "감사합니다", "다음 회의", "next meeting",
        "참고 자료", "references", "회의 정보", "meeting info",
    }

    _SKIP_CONTENT_PATTERNS = [
        "참석자:", "서기:", "장소:", "일시:", "작성자:", "작성일:",
        "발표자:", "회의 일시", "회의 장소", "date:", "location:",
        "attendees:", "minutes by:", "감사합니다",
    ]

    def _is_non_requirement(self, title: str, content: str) -> bool:
        """섹션이 비-요구사항인지 판별합니다."""
        title_lower = title.lower().strip()

        # 제목 기반 필터링
        for skip in self._SKIP_TITLES:
            if skip in title_lower:
                return True

        # 내용 기반 필터링
        content_lower = content.lower().strip() if content else ""
        for pattern in self._SKIP_CONTENT_PATTERNS:
            if content_lower.startswith(pattern.lower()):
                return True

        # 내용이 너무 짧으면 의미 없는 섹션
        if len(content.strip()) < 15:
            return True

        return False

    def _extract_from_content(self, parsed_content: ParsedContent) -> List[dict]:
        """
        AI 응답이 없을 때 문서 내용에서 직접 요구사항을 추출합니다.
        비-요구사항 필터링을 적용하여 품질을 보장합니다.
        """
        raw_reqs = []

        # 섹션이 있으면 섹션 기반으로 추출
        if parsed_content.sections:
            for idx, section in enumerate(parsed_content.sections[:20]):
                title = section.get('title', f'요구사항 {idx + 1}')
                content = section.get('content', '')
                if isinstance(content, list):
                    content = "\n".join(str(c) for c in content)

                # 비-요구사항 필터링
                if self._is_non_requirement(title, content):
                    logger.debug(f"[extract_from_content] 비-요구사항 스킵: {title}")
                    continue

                if content and len(content.strip()) > 15:
                    raw_reqs.append({
                        "title": title[:50] if title else f"요구사항 {idx + 1}",
                        "description": content[:500] if content else title,
                        "type": "FR",
                        "priority": "MEDIUM",
                        "acceptance_criteria": [],
                        "confidence_score": 0.4,
                        "confidence_reason": "AI 실패, 문서에서 직접 추출 (낮은 품질)",
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
                        content_text = "\n".join(current_content)
                        if not self._is_non_requirement(current_title, content_text):
                            raw_reqs.append({
                                "title": current_title[:50],
                                "description": content_text[:500],
                                "type": "FR",
                                "priority": "MEDIUM",
                                "confidence_score": 0.4,
                                "confidence_reason": "AI 실패, 문서에서 직접 추출 (낮은 품질)",
                            })
                    current_title = line.strip('=- #')
                    current_content = []
                else:
                    current_content.append(line)

            # 마지막 섹션 처리
            if current_title and current_content:
                content_text = "\n".join(current_content)
                if not self._is_non_requirement(current_title, content_text):
                    raw_reqs.append({
                        "title": current_title[:50],
                        "description": content_text[:500],
                        "type": "FR",
                        "priority": "MEDIUM",
                        "confidence_score": 0.4,
                        "confidence_reason": "AI 실패, 문서에서 직접 추출 (낮은 품질)",
                    })

        logger.info(f"[extract_from_content] 직접 추출된 요구사항: {len(raw_reqs)}개")
        return raw_reqs

    def _extract_from_parsed_content(
        self,
        parsed_content: ParsedContent,
        start_counter: int,
        source_file: str,
        document_id: str,
        source_type: str = "text"
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
                    document_id,
                    source_type
                )
                if req:
                    requirements.append(req)
            except Exception as e:
                logger.warning(f"[extract_from_parsed] 변환 실패: {e}")
                continue

        return requirements