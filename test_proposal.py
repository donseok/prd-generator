#!/usr/bin/env python
"""PRD 기반 제안서 생성 테스트."""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.models import InputType
from app.services.claude_client import get_claude_client
from app.layers.layer1_parsing import ParserFactory
from app.layers.layer2_normalization import Normalizer
from app.layers.layer3_validation import Validator
from app.layers.layer4_generation import PRDGenerator
from app.layers.layer5_proposal import ProposalGenerator, ProposalContext


def get_input_type(file_path: Path) -> InputType:
    """파일 확장자로 InputType 결정."""
    suffix = file_path.suffix.lower()
    type_map = {
        '.txt': InputType.TEXT,
        '.md': InputType.TEXT,
        '.json': InputType.TEXT,
        '.csv': InputType.CSV,
        '.xlsx': InputType.EXCEL,
        '.xls': InputType.EXCEL,
        '.pptx': InputType.POWERPOINT,
        '.ppt': InputType.POWERPOINT,
        '.docx': InputType.DOCUMENT,
        '.doc': InputType.DOCUMENT,
        '.png': InputType.IMAGE,
        '.jpg': InputType.IMAGE,
        '.jpeg': InputType.IMAGE,
    }
    return type_map.get(suffix, InputType.TEXT)


async def generate_prd(files: list[Path], client) -> "PRDDocument":
    """Layer 1-4: PRD 생성."""
    factory = ParserFactory(client)
    normalizer = Normalizer(client)
    validator = Validator(client)
    generator = PRDGenerator(client)

    # Layer 1: 파싱
    print("\n[Layer 1] 파싱...")
    parsed_contents = []
    document_ids = []

    for i, file_path in enumerate(files, 1):
        input_type = get_input_type(file_path)
        try:
            parser = factory.get_parser(input_type)
            parsed = await parser.parse(file_path)
            parsed_contents.append(parsed)
            document_ids.append(f"doc-{i:03d}")
            print(f"  ✓ {file_path.name}")
        except Exception as e:
            print(f"  ✗ {file_path.name}: {e}")

    print(f"  파싱 완료: {len(parsed_contents)}/{len(files)}개")

    if not parsed_contents:
        raise ValueError("파싱된 콘텐츠 없음")

    # Layer 2: 정규화
    print("\n[Layer 2] 정규화...")
    requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
    print(f"  요구사항 추출: {len(requirements)}개")

    # Layer 3: 검증
    print("\n[Layer 3] 검증...")
    validated, review_items = await validator.validate(requirements, job_id="proposal-test")
    print(f"  승인: {len(validated)}개, PM검토: {len(review_items)}개")

    # Layer 4: PRD 생성
    print("\n[Layer 4] PRD 생성...")
    source_docs = [f.name for f in files]
    prd = await generator.generate(validated or requirements, source_documents=source_docs)
    print(f"  PRD 생성 완료: {prd.id}")

    return prd


async def test_proposal_generation():
    """제안서 생성 테스트."""
    print("\n" + "="*70)
    print("PRD → 제안서 생성 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    examples_dir = Path("workspace/inputs/samples")

    # 테스트용으로 일부 파일만 사용 (빠른 테스트)
    # 전체 테스트는 아래 주석 해제
    files = [f for f in examples_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    files = sorted(files, key=lambda x: x.name)[:5]  # 처음 5개만

    # files = [f for f in examples_dir.iterdir() if f.is_file() and not f.name.startswith('.')]

    print(f"\n테스트 파일: {len(files)}개")
    for f in files:
        print(f"  - {f.name}")

    client = get_claude_client()
    total_start = time.time()

    # Layer 1-4: PRD 생성
    print("\n" + "-"*70)
    print("Phase 1: PRD 생성 (Layer 1-4)")
    print("-"*70)

    prd_start = time.time()
    prd = await generate_prd(files, client)
    prd_time = time.time() - prd_start

    print(f"\nPRD 생성 완료: {prd_time:.1f}초")
    print(f"  - 기능 요구사항: {len(prd.functional_requirements)}개")
    print(f"  - 비기능 요구사항: {len(prd.non_functional_requirements)}개")
    print(f"  - 제약조건: {len(prd.constraints)}개")
    print(f"  - 전체 신뢰도: {prd.metadata.overall_confidence:.0%}")

    # Layer 5: 제안서 생성
    print("\n" + "-"*70)
    print("Phase 2: 제안서 생성 (Layer 5)")
    print("-"*70)

    proposal_generator = ProposalGenerator(client)

    # 제안서 컨텍스트 설정
    context = ProposalContext(
        client_name="ABC Corporation",
        project_name="통합 시스템 구축",
        project_duration_months=6,
        include_pricing=False,
        additional_notes="POC 프로젝트로 시작하여 확장 예정",
    )

    print(f"\n고객사: {context.client_name}")
    print(f"프로젝트명: {context.project_name}")
    print(f"예상 기간: {context.project_duration_months}개월")

    proposal_start = time.time()
    proposal = await proposal_generator.generate(prd, context)
    proposal_time = time.time() - proposal_start

    print(f"\n제안서 생성 완료: {proposal_time:.1f}초")
    print(f"  - 제안서 ID: {proposal.id}")
    print(f"  - 제목: {proposal.title}")

    total_time = time.time() - total_start

    # 결과 요약
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)

    print(f"\n소요 시간:")
    print(f"  PRD 생성 (Layer 1-4):   {prd_time:7.1f}초")
    print(f"  제안서 생성 (Layer 5):  {proposal_time:7.1f}초")
    print(f"  ─────────────────────────────────")
    print(f"  총 소요시간:            {total_time:7.1f}초 ({total_time/60:.1f}분)")

    print(f"\n제안서 구성:")
    print(f"  - 경영진 요약: {len(proposal.executive_summary)} chars")
    print(f"  - 프로젝트 목표: {len(proposal.project_overview.objectives)}개")
    print(f"  - 작업 범위 (포함): {len(proposal.scope_of_work.in_scope)}개")
    print(f"  - 주요 기능: {len(proposal.scope_of_work.key_features)}개")
    print(f"  - 일정 단계: {len(proposal.timeline.phases)}개")
    print(f"  - 산출물: {len(proposal.deliverables)}개")
    print(f"  - 투입 인원: {len(proposal.resource_plan.team_structure)}개 역할")
    print(f"  - 리스크: {len(proposal.risks)}개")
    print(f"  - 전제 조건: {len(proposal.assumptions)}개")
    print(f"  - 기대 효과: {len(proposal.expected_benefits)}개")

    # 마크다운 저장
    print("\n" + "="*70)
    print("제안서 저장")
    print("="*70)

    md_content = proposal.to_markdown()
    output_path = Path("workspace/outputs/proposals")
    output_path.mkdir(parents=True, exist_ok=True)

    proposal_file = output_path / f"{proposal.id}.md"
    proposal_file.write_text(md_content, encoding='utf-8')
    print(f"\n저장 완료: {proposal_file}")

    # 마크다운 출력
    print("\n" + "="*70)
    print("제안서 마크다운")
    print("="*70)
    print(md_content)

    return proposal


if __name__ == "__main__":
    asyncio.run(test_proposal_generation())
