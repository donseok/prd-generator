#!/usr/bin/env python
"""슬랙 대화기록으로 PRD 생성 테스트."""

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


async def test_slack_document():
    """슬랙 대화기록 문서로 PRD 생성."""
    print("\n" + "="*60)
    print("슬랙 대화기록 PRD 생성 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    test_file = Path("workspace/inputs/samples/슬랙_대화기록.txt")
    if not test_file.exists():
        print(f"테스트 파일 없음: {test_file}")
        return

    client = get_claude_client()
    factory = ParserFactory(client)
    normalizer = Normalizer(client)
    validator = Validator(client)
    generator = PRDGenerator(client)

    total_start = time.time()

    # Layer 1: 파싱
    print("\n[Layer 1] 파싱 중...")
    start = time.time()
    parser = factory.get_parser(InputType.TEXT)
    parsed = await parser.parse(test_file)
    layer1_time = time.time() - start
    print(f"   완료: {layer1_time:.2f}초")
    print(f"   - 텍스트 길이: {len(parsed.raw_text)} chars")

    # Layer 2: 정규화
    print("\n[Layer 2] 정규화 중...")
    start = time.time()
    requirements = await normalizer.normalize([parsed], document_ids=["slack-001"])
    layer2_time = time.time() - start
    print(f"   완료: {layer2_time:.2f}초")
    print(f"   - 추출된 요구사항: {len(requirements)}개")

    # 요구사항 유형별 분류
    fr_count = len([r for r in requirements if r.type.value == "FR"])
    nfr_count = len([r for r in requirements if r.type.value == "NFR"])
    const_count = len([r for r in requirements if r.type.value == "CONSTRAINT"])
    print(f"   - FR: {fr_count}, NFR: {nfr_count}, CONSTRAINT: {const_count}")

    # Layer 3: 검증
    print("\n[Layer 3] 검증 중...")
    start = time.time()
    validated, review_items = await validator.validate(requirements, job_id="slack-test")
    layer3_time = time.time() - start
    print(f"   완료: {layer3_time:.2f}초")
    print(f"   - 승인: {len(validated)}개, PM검토: {len(review_items)}개")

    # Layer 4: PRD 생성
    print("\n[Layer 4] PRD 생성 중...")
    start = time.time()
    prd = await generator.generate(validated or requirements, source_documents=["슬랙_대화기록.txt"])
    layer4_time = time.time() - start
    print(f"   완료: {layer4_time:.2f}초")
    print(f"   - PRD ID: {prd.id}")
    print(f"   - 제목: {prd.title}")

    total_time = time.time() - total_start

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"\n소요 시간:")
    print(f"  Layer 1 (파싱):    {layer1_time:6.2f}초")
    print(f"  Layer 2 (정규화):  {layer2_time:6.2f}초")
    print(f"  Layer 3 (검증):    {layer3_time:6.2f}초")
    print(f"  Layer 4 (생성):    {layer4_time:6.2f}초")
    print(f"  ─────────────────────────")
    print(f"  총 소요시간:       {total_time:6.2f}초 ({total_time/60:.1f}분)")

    print(f"\nPRD 품질:")
    print(f"  - 기능 요구사항: {len(prd.functional_requirements)}개")
    print(f"  - 비기능 요구사항: {len(prd.non_functional_requirements)}개")
    print(f"  - 제약조건: {len(prd.constraints)}개")
    print(f"  - 전체 신뢰도: {prd.metadata.overall_confidence:.0%}")

    # 추출된 요구사항 출력
    print(f"\n추출된 요구사항 목록:")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. [{req.type.value}] {req.title} (신뢰도: {req.confidence_score:.0%})")

    # PRD 개요 출력
    print(f"\n생성된 PRD 개요:")
    print(f"  제목: {prd.title}")
    print(f"  배경: {prd.overview.background[:200]}...")
    print(f"\n  목표:")
    for goal in prd.overview.goals[:5]:
        print(f"    - {goal}")

    # 마크다운 출력
    print("\n" + "="*60)
    print("PRD 마크다운 출력")
    print("="*60)
    md_content = prd.to_markdown()
    print(md_content)

    return prd


if __name__ == "__main__":
    asyncio.run(test_slack_document())
