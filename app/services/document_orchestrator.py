"""
문서 생성 통합 오케스트레이터 서비스입니다.
PRD뿐만 아니라 TRD, WBS, 제안서까지 모든 문서 생성 과정을 순서대로 관리합니다.

생성 순서:
1. PRD (제품 요구사항) 생성
2. TRD (기술 요구사항) 생성
3. WBS (작업 분해) 생성
4. 제안서 생성 (옵션)
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
    """
    윈도우 환경(cp949)에서 이모지 출력 시 에러가 나지 않도록 안전하게 출력하는 함수입니다.
    이모지를 텍스트(예: [OK])로 변환하여 출력합니다.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # 이모지 및 특수 문자 대체 맵
        replacements = {
            "📋": "[문서]",
            "✅": "[완료]",
            "❌": "[실패]",
            "⚠️": "[주의]",
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        try:
            print(text)
        except UnicodeEncodeError:
            # 그래도 안 되면 문자 자체를 무시하거나 대체 문자로 변경
            print(text.encode('ascii', 'replace').decode('ascii'))


@dataclass
class DocumentBundle:
    """생성된 모든 문서의 경로를 담고 있는 데이터 클래스입니다."""
    prd_path: Optional[Path] = None  # PRD 파일 경로
    trd_path: Optional[Path] = None  # TRD 파일 경로
    wbs_path: Optional[Path] = None  # WBS 파일 경로
    proposal_path: Optional[Path] = None  # 제안서 파일 경로
    
    total_time_seconds: float = 0.0  # 총 소요 시간
    errors: List[str] = field(default_factory=list)  # 발생한 에러 목록
    
    def is_complete(self) -> bool:
        """필수 문서 3종(PRD, TRD, WBS)이 모두 생성되었는지 확인합니다."""
        return all([self.prd_path, self.trd_path, self.wbs_path])


class DocumentOrchestrator:
    """
    전체 문서 생성 파이프라인 관리자 클래스입니다.
    하나의 입력으로 여러 종류의 문서를 연쇄적으로 생성합니다.
    """
    
    def __init__(
        self,
        input_dir: Path = None,
        output_base_dir: Path = None,
    ):
        """
        초기화 함수. 
        
        Args:
            input_dir: 입력 파일을 읽어올 폴더 (기본값: workspace/inputs/projects)
            output_base_dir: 결과물을 저장할 기본 폴더 (기본값: workspace/outputs)
        """
        self.input_dir = input_dir or Path("workspace/inputs/projects")
        self.output_base_dir = output_base_dir or Path("workspace/outputs")
        
        # 각 문서 종류별로 저장할 하위 폴더 설정
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
        모든 문서를 순서대로 생성하는 메인 함수입니다.
        
        Args:
            include_proposal: 제안서도 만들지 여부
            client_name: 제안서에 들어갈 고객사 이름
            verbose: 진행 상황을 화면에 출력할지 여부
            
        Returns:
            생성된 문서들의 정보가 담긴 DocumentBundle 객체
        """
        bundle = DocumentBundle()
        total_start = time.time()
        
        if verbose:
            safe_print("\n" + "=" * 70)
            safe_print("📋 전체 문서 생성 시작")
            safe_print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            safe_print("=" * 70)
        
        try:
            # 1단계: PRD 생성
            if verbose:
                safe_print("\n[1/4] PRD (제품 요구사항 정의서) 생성 중...")
            bundle.prd_path = await self._generate_prd(verbose)
            
            if not bundle.prd_path:
                bundle.errors.append("PRD 생성 실패")
                return bundle  # PRD가 없으면 나머지도 못 만드므로 중단
            
            # 2단계: TRD 생성
            if verbose:
                safe_print("\n[2/4] TRD (기술 요구사항 정의서) 생성 중...")
            bundle.trd_path = await self._generate_trd(bundle.prd_path, verbose)
            
            if not bundle.trd_path:
                bundle.errors.append("TRD 생성 실패")
            
            # 3단계: WBS 생성
            if verbose:
                safe_print("\n[3/4] WBS (작업 분해 구조) 생성 중...")
            bundle.wbs_path = await self._generate_wbs(bundle.prd_path, verbose)
            
            if not bundle.wbs_path:
                bundle.errors.append("WBS 생성 실패")
            
            # 4단계: 제안서 생성 (선택)
            if include_proposal:
                if verbose:
                    safe_print("\n[4/4] 프로젝트 제안서 생성 중...")
                bundle.proposal_path = await self._generate_proposal(
                    bundle.prd_path, client_name, verbose
                )
                
                if not bundle.proposal_path:
                    bundle.errors.append("제안서 생성 실패")
            
        except Exception as e:
            logger.error(f"문서 생성 중 오류: {e}", exc_info=True)
            bundle.errors.append(str(e))
        
        bundle.total_time_seconds = time.time() - total_start
        
        if verbose:
            self._print_summary(bundle, include_proposal)
        
        return bundle
    
    async def _generate_prd(self, verbose: bool) -> Optional[Path]:
        """PRD 생성 내부 함수."""
        # 필요한 모듈들을 안에서 불러옵니다.
        from app.models import InputType
        from app.services.claude_client import get_claude_client
        from app.layers.layer1_parsing import ParserFactory
        from app.layers.layer2_normalization import Normalizer
        from app.layers.layer3_validation import Validator
        from app.layers.layer4_generation import PRDGenerator
        
        try:
            self.prd_dir.mkdir(parents=True, exist_ok=True)
            
            # 폴더에서 입력 파일들 찾기
            files = self._get_input_files()
            if not files:
                logger.warning("입력 파일이 없습니다.")
                return None
            
            if verbose:
                safe_print(f"  - 입력 파일: {len(files)}개 발견")
            
            client = get_claude_client()
            factory = ParserFactory(client)
            normalizer = Normalizer(client)
            validator = Validator(client)
            generator = PRDGenerator(client)
            
            # Layer 1: 파싱 (파일 읽기)
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
            
            # Layer 2: 정규화 (요구사항 추출)
            document_ids = [f"doc-{i:03d}" for i in range(1, len(files) + 1)]
            requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
            
            if verbose:
                safe_print(f"  - 요구사항 추출 완료: {len(requirements)}개")
            
            # Layer 3: 검증 (품질 체크)
            validated, review_items = await validator.validate(requirements, job_id="auto-doc")
            
            # Layer 4: PRD 생성
            source_docs = [f.name for f in files]
            prd = await generator.generate(validated or requirements, source_documents=source_docs)
            
            # 파일로 저장 (Markdown과 JSON 두 가지 형식)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            md_path = self.prd_dir / f"PRD-{timestamp}.md"
            json_path = self.prd_dir / f"PRD-{timestamp}.json"
            
            md_path.write_text(prd.to_markdown(), encoding="utf-8")
            json_path.write_text(prd.to_json(), encoding="utf-8")
            
            if verbose:
                safe_print(f"  ✅ PRD 저장 완료: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"PRD 생성 오류: {e}", exc_info=True)
            return None
    
    async def _generate_trd(self, prd_path: Path, verbose: bool) -> Optional[Path]:
        """TRD (기술 요구사항) 생성 내부 함수."""
        from app.models import PRDDocument
        from app.layers.layer6_trd import TRDGenerator, TRDContext
        
        try:
            self.trd_dir.mkdir(parents=True, exist_ok=True)
            
            # 앞서 생성한 PRD 파일을 불러옵니다.
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # TRD 생성 설정 (기본값 사용)
            context = TRDContext(
                target_environment="cloud",  # 클라우드 환경 타겟
                scalability_requirement="medium", # 중간 수준의 확장성
                security_level="standard", # 표준 보안 수준
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
                safe_print(f"  ✅ TRD 저장 완료: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"TRD 생성 오류: {e}", exc_info=True)
            return None
    
    async def _generate_wbs(self, prd_path: Path, verbose: bool) -> Optional[Path]:
        """WBS (작업 분해 구조) 생성 내부 함수."""
        from app.models import PRDDocument
        from app.layers.layer7_wbs import WBSGenerator, WBSContext
        
        try:
            self.wbs_dir.mkdir(parents=True, exist_ok=True)
            
            # PRD 로드
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # WBS 생성 설정
            context = WBSContext(
                start_date=date.today(), # 오늘부터 시작
                team_size=5, # 팀원 5명 가정
                methodology="agile", # 애자일 방법론
                sprint_duration_weeks=2, # 스프린트 기간 2주
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
                safe_print(f"  ✅ WBS 저장 완료: {md_path.name}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"WBS 생성 오류: {e}", exc_info=True)
            return None
    
    async def _generate_proposal(
        self, prd_path: Path, client_name: str, verbose: bool
    ) -> Optional[Path]:
        """제안서 생성 내부 함수."""
        from app.models import PRDDocument
        from app.layers.layer5_proposal import ProposalGenerator, ProposalContext
        
        try:
            self.proposal_dir.mkdir(parents=True, exist_ok=True)
            
            # PRD 로드
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
            prd = PRDDocument(**prd_data)
            
            # 제안서 설정
            context = ProposalContext(
                client_name=client_name,
                project_name=prd.title,
                project_duration_months=6, # 기간 6개월 가정
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
                safe_print(f"  ✅ 제안서 저장 완료: {md_path.name}")
            
            return md_path
            
        except Exception as e:
            logger.error(f"제안서 생성 오류: {e}", exc_info=True)
            return None
    
    def _get_input_files(self) -> List[Path]:
        """입력 폴더에서 처리할 파일들을 찾아서 반환합니다."""
        if not self.input_dir.exists():
            return []
        
        # 점(.)으로 시작하는 숨김 파일은 제외
        files = [
            f for f in self.input_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
        return sorted(files, key=lambda x: x.name)
    
    def _get_input_type(self, file_path: Path):
        """파일 확장자를 보고 어떤 종류의 파일인지 판단합니다."""
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
        """작업 결과를 요약해서 출력합니다."""
        safe_print("\n" + "=" * 70)
        safe_print("📋 문서 생성 작업 완료")
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


# 싱글톤 인스턴스 저장소
_document_orchestrator: Optional[DocumentOrchestrator] = None


def get_document_orchestrator() -> DocumentOrchestrator:
    """오케스트레이터 인스턴스를 하나만 생성하여 반환합니다."""
    global _document_orchestrator
    if _document_orchestrator is None:
        _document_orchestrator = DocumentOrchestrator()
    return _document_orchestrator