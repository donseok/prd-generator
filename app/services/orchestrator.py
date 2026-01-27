"""
PRD 생성 파이프라인의 전체 흐름을 관리하는 '지휘자' 역할을 하는 오케스트레이터입니다.

처리 단계(파이프라인):
1. 파싱 (Parsing): 입력된 파일들을 읽고 내용을 추출합니다.
2. 정규화 (Normalization): 추출된 내용을 표준 요구사항 형태로 정리합니다.
3. 검증 (Validation): 요구사항의 품질을 확인하고 문제가 없는지 검사합니다.
4. 생성 (Generation): 최종 PRD 문서를 생성합니다.
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
# 순환 참조(서로를 계속 참조하는 문제)를 피하기 위해 일부는 함수 안에서 import 합니다.


class PipelineOrchestrator:
    """
    4단계 PRD 생성 과정을 조율하는 클래스입니다.
    각 단계별 처리기를 실행하고 결과를 다음 단계로 전달합니다.
    """

    def __init__(self):
        self.claude_client = get_claude_client()
        self.storage = get_file_storage()

        # 각 단계를 담당할 처리기들을 나중에 불러옵니다.
        from app.layers.layer1_parsing import ParserFactory
        from app.layers.layer2_normalization import Normalizer
        from app.layers.layer3_validation import Validator
        from app.layers.layer4_generation import PRDGenerator

        # 각 단계별 처리기 초기화
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
        전체 파이프라인을 실행하는 메인 함수입니다.

        Args:
            job: 현재 작업 정보
            documents: 처리할 입력 문서들
            on_progress: 진행 상황을 알려줄 콜백 함수

        Returns:
            생성된 PRD 문서 (검토가 필요한 경우 None 반환)
        """
        try:
            # ========== 1단계: 파싱 (Parsing) ==========
            # 문서 내용을 읽어서 텍스트로 변환합니다.
            job.update_status(ProcessingStatus.PARSING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "parsing", "파싱 시작")

            parsed_contents = await self._execute_parsing(job, documents)

            await self._emit_event(
                on_progress, job, "layer_complete", "parsing",
                f"{len(parsed_contents)}개 문서 파싱 완료"
            )

            # ========== 2단계: 정규화 (Normalization) ==========
            # 텍스트에서 명확한 요구사항들을 뽑아냅니다.
            job.update_status(ProcessingStatus.NORMALIZING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "normalizing", "정규화 시작")

            # 문서 ID 목록 준비
            document_ids = [doc.id for doc in documents]
            requirements = await self._execute_normalization(
                job, parsed_contents, document_ids=document_ids
            )

            await self._emit_event(
                on_progress, job, "layer_complete", "normalizing",
                f"{len(requirements)}개 요구사항 추출 완료"
            )

            # ========== 3단계: 검증 (Validation) ==========
            # 뽑아낸 요구사항이 타당한지 검사합니다.
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

            # PM(기획자)의 검토가 필요한 항목이 있으면 여기서 멈추고 검토를 요청합니다.
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

                # 검토 대기 상태이므로 문서를 반환하지 않고 종료
                return None

            # ========== 4단계: 생성 (Generation) ==========
            # 최종 PRD 문서를 작성합니다.
            job.update_status(ProcessingStatus.GENERATING)
            await self.storage.update_job(job)
            await self._emit_event(on_progress, job, "layer_start", "generating", "PRD 생성 시작")

            prd = await self._execute_generation(
                job, validated_requirements, documents
            )

            # 결과 저장
            await self.storage.save_prd(prd)

            # 작업 완료 처리
            job.update_status(ProcessingStatus.COMPLETED)
            job.prd_id = prd.id
            await self.storage.update_job(job)

            await self._emit_event(
                on_progress, job, "layer_complete", "generating",
                f"PRD 생성 완료: {prd.id}"
            )

            return prd

        except Exception as e:
            # 오류 발생 시 실패 상태로 변경하고 에러 메시지 저장
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
        PM 검토가 끝난 후 작업을 재개하는 함수입니다.
        검토된 내용을 반영하여 최종 문서를 생성합니다.
        """
        # 원본 문서를 다시 불러옵니다.
        documents = []
        for doc_id in job.input_document_ids:
            doc = await self.storage.get_input_document(doc_id)
            if doc:
                documents.append(doc)

        # 파싱과 정규화를 다시 실행하여 최신 상태 확인 (캐시 활용됨)
        parsed_contents = await self._execute_parsing(job, documents)
        document_ids = [doc.id for doc in documents]
        requirements = await self._execute_normalization(
            job, parsed_contents, document_ids=document_ids
        )

        # 검토 결과(수정/거절 등)를 요구사항에 반영합니다.
        final_requirements = self._apply_review_decisions(requirements, job.review_items)

        # PRD 생성 단계 실행
        job.update_status(ProcessingStatus.GENERATING)
        await self.storage.update_job(job)

        prd = await self._execute_generation(job, final_requirements, documents)

        # 저장 및 완료
        await self.storage.save_prd(prd)

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
        1단계: 파싱 실행 (병렬 처리)
        
        여러 파일을 동시에 읽어서 속도를 높입니다. (최대 4개 동시)
        """
        layer_start = datetime.now()

        # 동시 실행 제한 설정 (최대 4개)
        semaphore = asyncio.Semaphore(4)

        async def parse_document(doc: InputDocument) -> Optional[ParsedContent]:
            """개별 문서를 파싱하는 내부 함수"""
            async with semaphore:
                try:
                    parser = self.parser_factory.get_parser(doc.input_type)

                    # 파일 경로가 있으면 해당 파일을 읽음
                    if doc.source_path:
                        from pathlib import Path
                        source_path = Path(doc.source_path)

                        # 상대 경로를 절대 경로로 변환
                        if not source_path.is_absolute():
                            project_root = Path(__file__).parent.parent.parent
                            source_path = project_root / source_path

                        if not source_path.exists():
                            print(f"[Parsing] 경고: 파일을 찾을 수 없음: {source_path}")
                            return None

                        return await parser.parse(source_path)
                    else:
                        # 이미 내용이 있으면 그대로 사용
                        return doc.content

                except Exception as e:
                    print(f"파싱 실패 ({doc.id}): {e}")
                    import traceback
                    traceback.print_exc()
                    return None

        # 모든 문서에 대해 파싱 작업을 동시에 시작하고 결과를 기다림
        results = await asyncio.gather(
            *[parse_document(doc) for doc in documents],
            return_exceptions=False
        )

        # 성공한 결과만 모으기
        parsed_contents = [r for r in results if r is not None]

        # 결과 기록
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
        """2단계: 정규화 실행 - AI를 통해 요구사항 구조화"""
        layer_start = datetime.now()

        requirements = await self.normalizer.normalize(
            parsed_contents,
            document_ids=document_ids
        )

        # 결과 기록
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
        """3단계: 검증 실행 - 품질 체크 및 리뷰 필요 항목 식별"""
        layer_start = datetime.now()

        validated, review_items = await self.validator.validate(
            requirements, job.job_id
        )

        # 결과 기록
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
        """4단계: 생성 실행 - 최종 문서 작성"""
        layer_start = datetime.now()

        source_docs = [
            doc.content.metadata.filename or doc.id
            for doc in documents
        ]

        prd = await self.generator.generate(
            requirements,
            source_documents=source_docs,
        )

        # 결과 기록
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
        """PM 검토 결과를 요구사항에 반영하는 내부 함수"""
        final_requirements = []

        # 검토된 항목들을 찾기 쉽게 정리
        decisions = {
            item.requirement_id: item
            for item in review_items
            if item.resolved
        }

        for req in requirements:
            if req.id in decisions:
                decision = decisions[req.id]
                if decision.pm_decision == "reject":
                    # 거절된 요구사항은 제외
                    continue
                elif decision.pm_decision == "modify" and decision.modified_content:
                    # 수정된 내용 반영
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
        """진행 상황 알림 이벤트를 발생시키는 함수"""
        if callback:
            event = ProcessingEvent(
                job_id=job.job_id,
                event_type=event_type,
                layer=layer,
                message=message,
                progress_percent=job.get_progress()["progress_percent"],
            )
            await callback(event) if callable(callback) else None


# 싱글톤 인스턴스 (프로그램 전체에서 하나만 생성됨)
_orchestrator: Optional[PipelineOrchestrator] = None


def get_orchestrator() -> PipelineOrchestrator:
    """오케스트레이터 인스턴스를 가져오거나 생성하는 함수"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator