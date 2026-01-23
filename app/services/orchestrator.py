"""Pipeline orchestrator for coordinating 4-layer processing.

파이프라인 처리 흐름:
1. Layer 1 (Parsing): 다양한 형식의 문서 파싱 - 병렬 처리 지원
2. Layer 2 (Normalization): 구조화된 요구사항으로 변환
3. Layer 3 (Validation): 품질 검증 및 PM 리뷰 라우팅
4. Layer 4 (Generation): PRD 문서 생성

성능 최적화:
- Layer 1: asyncio.gather() + Semaphore(4)로 최대 4개 파일 동시 파싱
- 예상 효과: 5개 파일 기준 80% 시간 단축
"""

import asyncio
from typing import List, Optional, Callable
from datetime import datetime

from app.models import (
    InputDocument,
    ParsedContent,
    NormalizedRequirement,
    PRDDocument,
    ProcessingJob,
    ProcessingStatus,
    LayerResult,
    ProcessingEvent,
)
from app.services.claude_client import get_claude_client
from app.services.file_storage import get_file_storage
# Layer imports are lazy to avoid circular imports


class PipelineOrchestrator:
    """
    Orchestrates the 4-layer PRD generation pipeline.

    Coordinates:
    1. Layer 1: Parsing - Extract content from various formats
    2. Layer 2: Normalization - Convert to structured requirements
    3. Layer 3: Validation - Quality checks and PM review routing
    4. Layer 4: Generation - Create PRD document
    """

    def __init__(self):
        self.claude_client = get_claude_client()
        self.storage = get_file_storage()

        # 순환 임포트 방지를 위해 지연 임포트
        from app.layers.layer1_parsing import ParserFactory
        from app.layers.layer2_normalization import Normalizer
        from app.layers.layer3_validation import Validator
        from app.layers.layer4_generation import PRDGenerator

        # Initialize layers
        self.parser_factory = ParserFactory(self.claude_client)
        self.normalizer = Normalizer(self.claude_client)
        self.validator = Validator(self.claude_client)
        self.generator = PRDGenerator(self.claude_client)

    async def process(
        self,
        job: ProcessingJob,
        documents: List[InputDocument],
        on_progress: Optional[Callable[[ProcessingEvent], None]] = None
    ) -> Optional[PRDDocument]:
        """
        Execute the full pipeline.

        Args:
            job: Processing job to track progress
            documents: Input documents to process
            on_progress: Optional callback for progress updates

        Returns:
            Generated PRDDocument or None if PM review is needed
        """
        try:
            # ========== Layer 1: Parsing ==========
            job.update_status(ProcessingStatus.PARSING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "parsing", "파싱 시작")

            parsed_contents = await self._execute_parsing(job, documents)

            await self._emit_event(
                on_progress, job, "layer_complete", "parsing",
                f"{len(parsed_contents)}개 문서 파싱 완료"
            )

            # ========== Layer 2: Normalization ==========
            job.update_status(ProcessingStatus.NORMALIZING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "normalizing", "정규화 시작")

            # Pass document IDs for source tracking
            document_ids = [doc.id for doc in documents]
            requirements = await self._execute_normalization(
                job, parsed_contents, document_ids=document_ids
            )

            await self._emit_event(
                on_progress, job, "layer_complete", "normalizing",
                f"{len(requirements)}개 요구사항 추출 완료"
            )

            # ========== Layer 3: Validation ==========
            job.update_status(ProcessingStatus.VALIDATING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "validating", "검증 시작")

            validated_requirements, review_items = await self._execute_validation(
                job, requirements
            )

            await self._emit_event(
                on_progress, job, "layer_complete", "validating",
                f"검증 완료: {len(validated_requirements)}개 승인, {len(review_items)}개 검토 필요"
            )

            # Check if PM review is needed
            if review_items:
                job.update_status(ProcessingStatus.PM_REVIEW)
                job.requires_pm_review = True
                for item in review_items:
                    job.add_review_item(item)
                await self.storage.update_job(job)

                await self._emit_event(
                    on_progress, job, "review_required", None,
                    f"{len(review_items)}개 항목 PM 검토 필요"
                )

                # Return None to indicate waiting for review
                return None

            # ========== Layer 4: Generation ==========
            job.update_status(ProcessingStatus.GENERATING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "generating", "PRD 생성 시작")

            prd = await self._execute_generation(
                job, validated_requirements, documents
            )

            # Save PRD
            await self.storage.save_prd(prd)

            # Update job
            job.update_status(ProcessingStatus.COMPLETED)
            job.prd_id = prd.id
            await self.storage.update_job(job)

            await self._emit_event(
                on_progress, job, "layer_complete", "generating",
                f"PRD 생성 완료: {prd.id}"
            )

            return prd

        except Exception as e:
            job.update_status(ProcessingStatus.FAILED)
            job.error_message = str(e)
            await self.storage.update_job(job)

            await self._emit_event(
                on_progress, job, "error", None,
                f"처리 실패: {str(e)}"
            )
            raise

    async def resume_after_review(
        self,
        job: ProcessingJob,
        on_progress: Optional[Callable[[ProcessingEvent], None]] = None
    ) -> PRDDocument:
        """
        Resume pipeline after PM review is complete.

        Args:
            job: Processing job with completed reviews
            on_progress: Optional callback for progress updates

        Returns:
            Generated PRDDocument
        """
        # Get validated requirements from storage
        # In a real implementation, we'd store intermediate results
        # For now, we'll regenerate from the stored documents

        # Get documents
        documents = []
        for doc_id in job.input_document_ids:
            doc = await self.storage.get_input_document(doc_id)
            if doc:
                documents.append(doc)

        # Re-run parsing and normalization
        parsed_contents = await self._execute_parsing(job, documents)
        document_ids = [doc.id for doc in documents]
        requirements = await self._execute_normalization(
            job, parsed_contents, document_ids=document_ids
        )

        # Apply review decisions
        final_requirements = self._apply_review_decisions(requirements, job.review_items)

        # Generate PRD
        job.update_status(ProcessingStatus.GENERATING)
        await self.storage.update_job(job)

        prd = await self._execute_generation(job, final_requirements, documents)

        # Save PRD
        await self.storage.save_prd(prd)

        # Update job
        job.update_status(ProcessingStatus.COMPLETED)
        job.prd_id = prd.id
        await self.storage.update_job(job)

        return prd

    async def _execute_parsing(
        self,
        job: ProcessingJob,
        documents: List[InputDocument]
    ) -> List[ParsedContent]:
        """
        Execute Layer 1: Parsing (병렬 처리).

        최대 4개 파일을 동시에 파싱하여 처리 시간을 단축합니다.
        Semaphore를 사용하여 동시 파싱 수를 제한합니다.

        Args:
            job: 처리 작업 정보
            documents: 파싱할 문서 목록

        Returns:
            파싱된 컨텐츠 목록

        처리 흐름:
        1. 각 문서에 대해 비동기 파싱 태스크 생성
        2. Semaphore(4)로 동시 실행 수 제한
        3. asyncio.gather()로 병렬 실행
        4. None 결과 필터링하여 반환
        """
        layer_start = datetime.now()

        # 동시 파싱 수 제한 (최대 4개)
        semaphore = asyncio.Semaphore(4)

        async def parse_document(doc: InputDocument) -> Optional[ParsedContent]:
            """단일 문서 파싱 (세마포어 적용)."""
            async with semaphore:
                try:
                    parser = self.parser_factory.get_parser(doc.input_type)

                    if doc.source_path:
                        from pathlib import Path
                        source_path = Path(doc.source_path)

                        # 상대 경로인 경우 절대 경로로 변환 (기존 문서 호환성)
                        if not source_path.is_absolute():
                            project_root = Path(__file__).parent.parent.parent
                            source_path = project_root / source_path

                        if not source_path.exists():
                            print(f"[Parsing] WARNING: File not found: {source_path}")
                            return None

                        return await parser.parse(source_path)
                    else:
                        return doc.content

                except Exception as e:
                    print(f"Parsing failed for {doc.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    return None

        # 병렬 파싱 실행
        results = await asyncio.gather(
            *[parse_document(doc) for doc in documents],
            return_exceptions=False
        )

        # None 결과 필터링
        parsed_contents = [r for r in results if r is not None]

        # 레이어 결과 기록
        layer_result = LayerResult(
            layer_name="parsing",
            status="success" if parsed_contents else "failed",
            started_at=layer_start,
        )
        layer_result.complete(output_data={"parsed_count": len(parsed_contents)})
        job.add_layer_result("parsing", layer_result)

        return parsed_contents

    async def _execute_normalization(
        self,
        job: ProcessingJob,
        parsed_contents: List[ParsedContent],
        document_ids: List[str] = None
    ) -> List[NormalizedRequirement]:
        """Execute Layer 2: Normalization."""
        layer_start = datetime.now()

        requirements = await self.normalizer.normalize(
            parsed_contents,
            document_ids=document_ids
        )

        # Record layer result
        layer_result = LayerResult(
            layer_name="normalizing",
            status="success",
            started_at=layer_start,
        )
        layer_result.complete(output_data={"requirement_count": len(requirements)})
        job.add_layer_result("normalizing", layer_result)

        return requirements

    async def _execute_validation(
        self,
        job: ProcessingJob,
        requirements: List[NormalizedRequirement]
    ) -> tuple[List[NormalizedRequirement], list]:
        """Execute Layer 3: Validation."""
        layer_start = datetime.now()

        validated, review_items = await self.validator.validate(
            requirements, job.job_id
        )

        # Record layer result
        layer_result = LayerResult(
            layer_name="validating",
            status="success",
            started_at=layer_start,
        )
        layer_result.complete(output_data={
            "validated_count": len(validated),
            "review_count": len(review_items),
        })
        job.add_layer_result("validating", layer_result)

        return validated, review_items

    async def _execute_generation(
        self,
        job: ProcessingJob,
        requirements: List[NormalizedRequirement],
        documents: List[InputDocument]
    ) -> PRDDocument:
        """Execute Layer 4: Generation."""
        layer_start = datetime.now()

        source_docs = [
            doc.content.metadata.filename or doc.id
            for doc in documents
        ]

        prd = await self.generator.generate(
            requirements,
            source_documents=source_docs,
        )

        # Record layer result
        layer_result = LayerResult(
            layer_name="generating",
            status="success",
            started_at=layer_start,
        )
        layer_result.complete(output_data={"prd_id": prd.id})
        job.add_layer_result("generating", layer_result)

        return prd

    def _apply_review_decisions(
        self,
        requirements: List[NormalizedRequirement],
        review_items: list
    ) -> List[NormalizedRequirement]:
        """Apply PM review decisions to requirements."""
        final_requirements = []

        # Build lookup of review decisions
        decisions = {
            item.requirement_id: item
            for item in review_items
            if item.resolved
        }

        for req in requirements:
            if req.id in decisions:
                decision = decisions[req.id]
                if decision.pm_decision == "reject":
                    # Skip rejected requirements
                    continue
                elif decision.pm_decision == "modify" and decision.modified_content:
                    # Apply modifications
                    for key, value in decision.modified_content.items():
                        if hasattr(req, key):
                            setattr(req, key, value)

            final_requirements.append(req)

        return final_requirements

    async def _emit_event(
        self,
        callback: Optional[Callable],
        job: ProcessingJob,
        event_type: str,
        layer: Optional[str],
        message: str
    ):
        """Emit a processing event."""
        if callback:
            event = ProcessingEvent(
                job_id=job.job_id,
                event_type=event_type,
                layer=layer,
                message=message,
                progress_percent=job.get_progress()["progress_percent"],
            )
            await callback(event) if callable(callback) else None


# Singleton instance
_orchestrator: Optional[PipelineOrchestrator] = None


def get_orchestrator() -> PipelineOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator
