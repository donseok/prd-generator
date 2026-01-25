"""Document orchestrator for generating all documents in sequence.

전체 문서 생성 파이프라인:
1. PRD 생성 (Layer 1-4)
2. TRD 생성 (Layer 6)
3. WBS 생성 (Layer 7)
4. 제안서 생성 (Layer 5) - 선택적

이 오케스트레이터는 @auto-doc 에이전트에서 사용됩니다.
"""

import asyncio
import json
import time
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


def safe_print(text: str):
    """Windows cp949 안전 출력."""
    try:
        print(text)
    except UnicodeEncodeError:
        # 이모지 및 특수 문자 대체
        replacements = {
            "📋": "[DOC]",
            "✅": "[OK]",
            "❌": "[X]",
            "⚠️": "[!]",
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'replace').decode('ascii'))


@dataclass
class DocumentBundle:
    """생성된 문서 번들."""
    prd_path: Optional[Path] = None
    trd_path: Optional[Path] = None
    wbs_path: Optional[Path] = None
    proposal_path: Optional[Path] = None
    
    total_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """PRD, TRD, WBS가 모두 생성되었는지 확인."""
        return all([self.prd_path, self.trd_path, self.wbs_path])


class DocumentOrchestrator:
    """
    전체 문서 생성 파이프라인 오케스트레이터.
    
    PRD → TRD → WBS → Proposal 순서로 문서를 생성합니다.
    각 단계는 이전 단계의 결과를 입력으로 사용합니다.
    """
    
    def __init__(
        self,
        input_dir: Path = None,
        output_base_dir: Path = None,
    ):
        """
        오케스트레이터 초기화.
        
        Args:
            input_dir: 입력 파일 디렉토리 (기본: workspace/inputs/projects)
            output_base_dir: 출력 기본 디렉토리 (기본: workspace/outputs)
        """
        self.input_dir = input_dir or Path("workspace/inputs/projects")
        self.output_base_dir = output_base_dir or Path("workspace/outputs")
        
        # 출력 디렉토리 설정
        self.prd_dir = self.output_base_dir / "prd"
        self.trd_dir = self.output_base_dir / "trd"
        self.wbs_dir = self.output_base_dir / "wbs"
        self.proposal_dir = self.output_base_dir / "proposals"
    
    async def generate_all(
        self,
        include_proposal: bool = False,
        client_name: str = "귀사",
        verbose: bool = True,
    ) -> DocumentBundle:
        """
        전체 문서 세트 생성.
        
        Args:
            include_proposal: 제안서 포함 여부
            client_name: 고객사명 (제안서 생성 시 사용)
            verbose: 상세 로그 출력 여부
            
        Returns:
            DocumentBundle: 생성된 문서 경로 번들
        """
        bundle = DocumentBundle()
        total_start = time.time()
        
        if verbose:
            safe_print("\n" + "=" * 70)
            safe_print("📋 전체 문서 생성 시작")
            safe_print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            safe_print("=" * 70)
        
        try:
            # Step 1: PRD 생성
            if verbose:
                safe_print("\n[1/4] PRD 생성 중...")
            bundle.prd_path = await self._generate_prd(verbose)
            
            if not bundle.prd_path:
                bundle.errors.append("PRD 생성 실패")
                return bundle
            
            # Step 2: TRD 생성
            if verbose:
                safe_print("\n[2/4] TRD 생성 중...")
            bundle.trd_path = await self._generate_trd(bundle.prd_path, verbose)
            
            if not bundle.trd_path:
                bundle.errors.append("TRD 생성 실패")
            
            # Step 3: WBS 생성
            if verbose:
                safe_print("\n[3/4] WBS 생성 중...")
            bundle.wbs_path = await self._generate_wbs(bundle.prd_path, verbose)
            
            if not bundle.wbs_path:
                bundle.errors.append("WBS 생성 실패")
            
            # Step 4: 제안서 생성 (선택적)
            if include_proposal:
                if verbose:
                    safe_print("\n[4/4] 제안서 생성 중...")
                bundle.proposal_path = await self._generate_proposal(
                    bundle.prd_path, client_name, verbose
                )
                
                if not bundle.proposal_path:
                    bundle.errors.append("제안서 생성 실패")
            
        except Exception as e:
            logger.error(f"문서 생성 중 오류: {e}")
            bundle.errors.append(str(e))
        
        bundle.total_time_seconds = time.time() - total_start
        
        if verbose:
            self._print_summary(bundle, include_proposal)
        
        return bundle
    
    async def _generate_prd(self, verbose: bool) -> Optional[Path]:
        """PRD 생성."""
        from app.models import InputType
        from app.services.claude_client import get_claude_client
        from app.layers.layer1_parsing import ParserFactory
        from app.layers.layer2_normalization import Normalizer
        from app.layers.layer3_validation import Validator
        from app.layers.layer4_generation import PRDGenerator
        
        try:
            self.prd_dir.mkdir(parents=True, exist_ok=True)
            
            # 입력 파일 수집
            files = self._get_input_files()
            if not files:
                logger.warning("입력 파일이 없습니다.")
                return None
            
            if verbose:
                safe_print(f"  - 입력 파일: {len(files)}개")
            
            client = get_claude_client()
            factory = ParserFactory(client)
            normalizer = Normalizer(client)
            validator = Validator(client)
            generator = PRDGenerator(client)
            
            # Layer 1: 파싱
            parsed_contents = []
            for file_path in files:
                try:
                    input_type = self._get_input_type(file_path)
                    parser = factory.get_parser(input_type)
                    parsed = await parser.parse(file_path)
                    parsed_contents.append(parsed)
                except Exception as e:
                    logger.warning(f"파싱 실패 ({file_path.name}): {e}")
            
            if not parsed_contents:
                return None
            
            # Layer 2: 정규화
            document_ids = [f"doc-{i:03d}" for i in range(1, len(files) + 1)]
            requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
            
            if verbose:
                safe_print(f"  - 요구사항 추출: {len(requirements)}개")
            
            # Layer 3: 검증
            validated, review_items = await validator.validate(requirements, job_id="auto-doc")
            
            # Layer 4: PRD 생성
            source_docs = [f.name for f in files]
            prd = await generator.generate(validated or requirements, source_documents=source_docs)
            
            # 저장
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            md_path = self.prd_dir / f"PRD-{timestamp}.md"
            json_path = self.prd_dir / f"PRD-{timestamp}.json"
            
            md_path.write_text(prd.to_markdown(), encoding="utf-8")
            json_path.write_text(prd.to_json(), encoding="utf-8")
            
            if verbose:
                safe_print(f"  ✅ PRD 저장: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"PRD 생성 오류: {e}")
            return None
    
    async def _generate_trd(self, prd_path: Path, verbose: bool) -> Optional[Path]:
        """TRD 생성."""
        from app.models import PRDDocument
        from app.layers.layer6_trd import TRDGenerator, TRDContext
        
        try:
            self.trd_dir.mkdir(parents=True, exist_ok=True)
            
            # PRD 로드
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # TRD 컨텍스트
            context = TRDContext(
                target_environment="cloud",
                scalability_requirement="medium",
                security_level="standard",
            )
            
            # 생성
            generator = TRDGenerator()
            trd = await generator.generate(prd, context)
            
            # 저장
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            md_path = self.trd_dir / f"TRD-{timestamp}.md"
            json_path = self.trd_dir / f"TRD-{timestamp}.json"
            
            md_path.write_text(trd.to_markdown(), encoding="utf-8")
            json_path.write_text(trd.to_json(), encoding="utf-8")
            
            if verbose:
                safe_print(f"  ✅ TRD 저장: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"TRD 생성 오류: {e}")
            return None
    
    async def _generate_wbs(self, prd_path: Path, verbose: bool) -> Optional[Path]:
        """WBS 생성."""
        from app.models import PRDDocument
        from app.layers.layer7_wbs import WBSGenerator, WBSContext
        
        try:
            self.wbs_dir.mkdir(parents=True, exist_ok=True)
            
            # PRD 로드
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # WBS 컨텍스트
            context = WBSContext(
                start_date=date.today(),
                team_size=5,
                methodology="agile",
                sprint_duration_weeks=2,
            )
            
            # 생성
            generator = WBSGenerator()
            wbs = await generator.generate(prd, context)
            
            # 저장
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            md_path = self.wbs_dir / f"WBS-{timestamp}.md"
            json_path = self.wbs_dir / f"WBS-{timestamp}.json"
            
            md_path.write_text(wbs.to_markdown(), encoding="utf-8")
            json_path.write_text(wbs.to_json(), encoding="utf-8")
            
            if verbose:
                safe_print(f"  ✅ WBS 저장: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"WBS 생성 오류: {e}")
            return None
    
    async def _generate_proposal(
        self, prd_path: Path, client_name: str, verbose: bool
    ) -> Optional[Path]:
        """제안서 생성."""
        from app.models import PRDDocument
        from app.layers.layer5_proposal import ProposalGenerator, ProposalContext
        
        try:
            self.proposal_dir.mkdir(parents=True, exist_ok=True)
            
            # PRD 로드
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # 제안서 컨텍스트
            context = ProposalContext(
                client_name=client_name,
                project_name=prd.title,
                project_duration_months=6,
            )
            
            # 생성
            generator = ProposalGenerator()
            proposal = await generator.generate(prd, context)
            
            # 저장
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            md_path = self.proposal_dir / f"PROP-{timestamp}.md"
            json_path = self.proposal_dir / f"PROP-{timestamp}.json"
            
            md_path.write_text(proposal.to_markdown(), encoding="utf-8")
            json_path.write_text(proposal.to_json(), encoding="utf-8")
            
            if verbose:
                safe_print(f"  ✅ 제안서 저장: {md_path.name}")
            
            return md_path
            
        except Exception as e:
            logger.error(f"제안서 생성 오류: {e}")
            return None
    
    def _get_input_files(self) -> List[Path]:
        """입력 파일 목록 조회."""
        if not self.input_dir.exists():
            return []
        
        files = [
            f for f in self.input_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
        return sorted(files, key=lambda x: x.name)
    
    def _get_input_type(self, file_path: Path):
        """파일 확장자로 입력 타입 결정."""
        from app.models import InputType
        
        suffix = file_path.suffix.lower()
        type_map = {
            ".txt": InputType.TEXT,
            ".md": InputType.TEXT,
            ".json": InputType.TEXT,
            ".csv": InputType.CSV,
            ".xlsx": InputType.EXCEL,
            ".xls": InputType.EXCEL,
            ".pptx": InputType.POWERPOINT,
            ".ppt": InputType.POWERPOINT,
            ".docx": InputType.DOCUMENT,
            ".doc": InputType.DOCUMENT,
            ".png": InputType.IMAGE,
            ".jpg": InputType.IMAGE,
            ".jpeg": InputType.IMAGE,
        }
        return type_map.get(suffix, InputType.TEXT)
    
    def _print_summary(self, bundle: DocumentBundle, include_proposal: bool):
        """결과 요약 출력."""
        safe_print("\n" + "=" * 70)
        safe_print("📋 문서 생성 완료")
        safe_print("=" * 70)
        
        docs = [
            ("PRD", bundle.prd_path),
            ("TRD", bundle.trd_path),
            ("WBS", bundle.wbs_path),
        ]
        if include_proposal:
            docs.append(("제안서", bundle.proposal_path))
        
        for name, path in docs:
            status = "✅" if path else "❌"
            filename = path.name if path else "생성 실패"
            safe_print(f"  {status} {name}: {filename}")
        
        safe_print(f"\n  총 소요시간: {bundle.total_time_seconds:.1f}초 ({bundle.total_time_seconds/60:.1f}분)")
        
        if bundle.errors:
            safe_print(f"\n  ⚠️ 오류: {len(bundle.errors)}건")
            for err in bundle.errors:
                safe_print(f"    - {err}")


# 싱글톤 인스턴스
_document_orchestrator: Optional[DocumentOrchestrator] = None


def get_document_orchestrator() -> DocumentOrchestrator:
    """DocumentOrchestrator 싱글톤 반환."""
    global _document_orchestrator
    if _document_orchestrator is None:
        _document_orchestrator = DocumentOrchestrator()
    return _document_orchestrator
