#!/usr/bin/env python
"""workspace/inputs/samples 폴더 전체 파일로 통합 PRD 생성."""

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


async def test_all_examples():
    """workspace/inputs/samples 폴더 전체 파일 처리."""
    print("\n" + "="*70)
    print("workspace/inputs/samples 전체 파일 통합 PRD 생성")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    examples_dir = Path("workspace/inputs/samples")

    # output 폴더 제외하고 파일만 수집
    files = [f for f in examples_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    files = sorted(files, key=lambda x: x.name)

    print(f"\n처리할 파일 수: {len(files)}개")
    for i, f in enumerate(files, 1):
        print(f"  {i:2}. {f.name} ({get_input_type(f).value})")

    client = get_claude_client()
    factory = ParserFactory(client)
    normalizer = Normalizer(client)
    validator = Validator(client)
    generator = PRDGenerator(client)

    total_start = time.time()

    # Layer 1: 파싱
    print("\n" + "-"*70)
    print("[Layer 1] 파싱")
    print("-"*70)

    parsed_contents = []
    document_ids = []
    parse_times = []

    for i, file_path in enumerate(files, 1):
        input_type = get_input_type(file_path)
        print(f"\n  [{i}/{len(files)}] {file_path.name} ({input_type.value})")

        start = time.time()
        try:
            parser = factory.get_parser(input_type)
            parsed = await parser.parse(file_path)
            elapsed = time.time() - start
            parse_times.append(elapsed)

            parsed_contents.append(parsed)
            document_ids.append(f"doc-{i:03d}")

            text_len = len(parsed.raw_text) if parsed.raw_text else 0
            sections = len(parsed.sections) if parsed.sections else 0
            print(f"      완료: {elapsed:.2f}초, 텍스트: {text_len} chars, 섹션: {sections}개")

        except Exception as e:
            elapsed = time.time() - start
            parse_times.append(elapsed)
            print(f"      실패: {e}")

    layer1_time = sum(parse_times)
    print(f"\n  Layer 1 총 소요: {layer1_time:.2f}초")
    print(f"  파싱 성공: {len(parsed_contents)}/{len(files)}개")

    if not parsed_contents:
        print("\n파싱된 콘텐츠가 없어 종료합니다.")
        return

    # Layer 2: 정규화
    print("\n" + "-"*70)
    print("[Layer 2] 정규화 (요구사항 추출)")
    print("-"*70)

    start = time.time()
    requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
    layer2_time = time.time() - start

    print(f"\n  완료: {layer2_time:.2f}초")
    print(f"  추출된 요구사항: {len(requirements)}개")

    # 유형별 분류
    fr_count = len([r for r in requirements if r.type.value == "FR"])
    nfr_count = len([r for r in requirements if r.type.value == "NFR"])
    const_count = len([r for r in requirements if r.type.value == "CONSTRAINT"])
    print(f"  - FR: {fr_count}, NFR: {nfr_count}, CONSTRAINT: {const_count}")

    # Layer 3: 검증
    print("\n" + "-"*70)
    print("[Layer 3] 검증")
    print("-"*70)

    start = time.time()
    validated, review_items = await validator.validate(requirements, job_id="all-examples")
    layer3_time = time.time() - start

    print(f"\n  완료: {layer3_time:.2f}초")
    print(f"  승인: {len(validated)}개, PM검토: {len(review_items)}개")

    # Layer 4: PRD 생성
    print("\n" + "-"*70)
    print("[Layer 4] PRD 생성")
    print("-"*70)

    source_docs = [f.name for f in files]

    start = time.time()
    prd = await generator.generate(validated or requirements, source_documents=source_docs)
    layer4_time = time.time() - start

    print(f"\n  완료: {layer4_time:.2f}초")
    print(f"  PRD ID: {prd.id}")
    print(f"  제목: {prd.title}")

    total_time = time.time() - total_start

    # 결과 요약
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)

    print(f"\n소요 시간:")
    print(f"  Layer 1 (파싱):    {layer1_time:7.2f}초")
    print(f"  Layer 2 (정규화):  {layer2_time:7.2f}초")
    print(f"  Layer 3 (검증):    {layer3_time:7.2f}초")
    print(f"  Layer 4 (생성):    {layer4_time:7.2f}초")
    print(f"  ─────────────────────────────")
    print(f"  총 소요시간:       {total_time:7.2f}초 ({total_time/60:.1f}분)")

    print(f"\nPRD 품질:")
    print(f"  - 입력 문서: {len(files)}개")
    print(f"  - 기능 요구사항: {len(prd.functional_requirements)}개")
    print(f"  - 비기능 요구사항: {len(prd.non_functional_requirements)}개")
    print(f"  - 제약조건: {len(prd.constraints)}개")
    print(f"  - 마일스톤: {len(prd.milestones)}개")
    print(f"  - 미해결 항목: {len(prd.unresolved_items)}개")
    print(f"  - 전체 신뢰도: {prd.metadata.overall_confidence:.0%}")

    # 요구사항 목록
    print(f"\n추출된 요구사항 ({len(requirements)}개):")
    for i, req in enumerate(requirements, 1):
        print(f"  {i:2}. [{req.type.value:10}] {req.title} ({req.confidence_score:.0%})")

    # PRD 개요
    print(f"\n생성된 PRD 개요:")
    print(f"  제목: {prd.title}")
    print(f"  배경: {prd.overview.background[:300]}...")

    print(f"\n  목표:")
    for goal in prd.overview.goals[:5]:
        print(f"    - {goal}")

    # 마크다운 저장
    print("\n" + "="*70)
    print("PRD 저장")
    print("="*70)

    md_content = prd.to_markdown()
    output_path = Path("workspace/outputs/prd/PRD-통합_전체문서.md")
    output_path.write_text(md_content, encoding='utf-8')
    print(f"\n저장 완료: {output_path}")

    # 마크다운 출력
    print("\n" + "="*70)
    print("PRD 마크다운")
    print("="*70)
    print(md_content)

    return prd


if __name__ == "__main__":
    asyncio.run(test_all_examples())
