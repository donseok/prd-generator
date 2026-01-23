#!/usr/bin/env python
"""복잡한 문서로 PRD 생성 테스트."""

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


async def test_complex_document():
    """복잡한 이메일 스레드 문서로 테스트."""
    print("\n" + "="*60)
    print("복잡한 문서 테스트: 이메일_스레드.txt")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    test_file = Path("data/uploads/a649bd2c/이메일_스레드.txt")
    if not test_file.exists():
        print(f"❌ 테스트 파일 없음: {test_file}")
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
    print(f"   ✅ 완료: {layer1_time:.2f}초")
    print(f"   - 텍스트 길이: {len(parsed.raw_text)} chars")

    # Layer 2: 정규화
    print("\n[Layer 2] 정규화 중... (시간이 걸릴 수 있습니다)")
    start = time.time()
    requirements = await normalizer.normalize([parsed], document_ids=["email-001"])
    layer2_time = time.time() - start
    print(f"   ✅ 완료: {layer2_time:.2f}초")
    print(f"   - 추출된 요구사항: {len(requirements)}개")

    # 요구사항 유형별 분류
    fr_count = len([r for r in requirements if r.type.value == "FR"])
    nfr_count = len([r for r in requirements if r.type.value == "NFR"])
    const_count = len([r for r in requirements if r.type.value == "CONSTRAINT"])
    print(f"   - FR: {fr_count}, NFR: {nfr_count}, CONSTRAINT: {const_count}")

    # Layer 3: 검증
    print("\n[Layer 3] 검증 중...")
    start = time.time()
    validated, review_items = await validator.validate(requirements, job_id="test-002")
    layer3_time = time.time() - start
    print(f"   ✅ 완료: {layer3_time:.2f}초")
    print(f"   - 승인: {len(validated)}개, PM검토: {len(review_items)}개")

    # Layer 4: PRD 생성
    print("\n[Layer 4] PRD 생성 중...")
    start = time.time()
    prd = await generator.generate(validated or requirements, source_documents=["이메일_스레드.txt"])
    layer4_time = time.time() - start
    print(f"   ✅ 완료: {layer4_time:.2f}초")
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

    # 일부 요구사항 출력
    print(f"\n추출된 요구사항 샘플:")
    for req in requirements[:5]:
        print(f"  [{req.id}] {req.title} ({req.type.value}, {req.confidence_score:.0%})")


if __name__ == "__main__":
    asyncio.run(test_complex_document())
