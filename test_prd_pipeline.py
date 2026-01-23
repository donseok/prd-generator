#!/usr/bin/env python
"""PRD 생성 파이프라인 테스트 스크립트."""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.models import (
    InputDocument,
    InputType,
    ParsedContent,
    ProcessingJob,
)
from app.services.claude_client import get_claude_client
from app.layers.layer1_parsing import ParserFactory
from app.layers.layer2_normalization import Normalizer
from app.layers.layer3_validation import Validator
from app.layers.layer4_generation import PRDGenerator


async def test_layer1_parsing():
    """Layer 1: 파싱 테스트."""
    print("\n" + "="*60)
    print("Layer 1: 파싱 테스트")
    print("="*60)

    client = get_claude_client()
    factory = ParserFactory(client)

    # 테스트 파일 경로
    test_file = Path("data/uploads/20fc347a/test_requirements.txt")

    if not test_file.exists():
        print(f"❌ 테스트 파일 없음: {test_file}")
        return None

    start = time.time()
    try:
        parser = factory.get_parser(InputType.TEXT)
        parsed = await parser.parse(test_file)
        elapsed = time.time() - start

        print(f"✅ 파싱 성공: {elapsed:.2f}초")
        print(f"   - 원본 텍스트 길이: {len(parsed.raw_text)} chars")
        print(f"   - 섹션 수: {len(parsed.sections)}")
        print(f"   - 파일명: {parsed.metadata.filename}")

        return parsed
    except Exception as e:
        print(f"❌ 파싱 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_layer2_normalization(parsed_content: ParsedContent):
    """Layer 2: 정규화 테스트."""
    print("\n" + "="*60)
    print("Layer 2: 정규화 테스트")
    print("="*60)

    if not parsed_content:
        print("❌ 파싱된 콘텐츠 없음, 테스트 스킵")
        return None

    client = get_claude_client()
    normalizer = Normalizer(client)

    start = time.time()
    try:
        requirements = await normalizer.normalize(
            [parsed_content],
            document_ids=["test-doc-001"]
        )
        elapsed = time.time() - start

        print(f"✅ 정규화 성공: {elapsed:.2f}초")
        print(f"   - 추출된 요구사항 수: {len(requirements)}")

        for req in requirements[:5]:  # 처음 5개만 출력
            print(f"\n   [{req.id}] {req.title}")
            print(f"       유형: {req.type.value}")
            print(f"       우선순위: {req.priority.value}")
            print(f"       신뢰도: {req.confidence_score:.0%}")
            if req.user_story:
                print(f"       User Story: {req.user_story[:80]}...")

        if len(requirements) > 5:
            print(f"\n   ... 외 {len(requirements) - 5}개")

        return requirements
    except Exception as e:
        print(f"❌ 정규화 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_layer3_validation(requirements):
    """Layer 3: 검증 테스트."""
    print("\n" + "="*60)
    print("Layer 3: 검증 테스트")
    print("="*60)

    if not requirements:
        print("❌ 요구사항 없음, 테스트 스킵")
        return None

    client = get_claude_client()
    validator = Validator(client)

    start = time.time()
    try:
        validated, review_items = await validator.validate(
            requirements,
            job_id="test-job-001"
        )
        elapsed = time.time() - start

        print(f"✅ 검증 성공: {elapsed:.2f}초")
        print(f"   - 승인된 요구사항: {len(validated)}개")
        print(f"   - PM 검토 필요: {len(review_items)}개")

        # 신뢰도 분포
        high_conf = len([r for r in requirements if r.confidence_score >= 0.8])
        med_conf = len([r for r in requirements if 0.5 <= r.confidence_score < 0.8])
        low_conf = len([r for r in requirements if r.confidence_score < 0.5])

        print(f"\n   신뢰도 분포:")
        print(f"   - 높음 (≥80%): {high_conf}개")
        print(f"   - 중간 (50-80%): {med_conf}개")
        print(f"   - 낮음 (<50%): {low_conf}개")

        return validated
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_layer4_generation(requirements):
    """Layer 4: PRD 생성 테스트."""
    print("\n" + "="*60)
    print("Layer 4: PRD 생성 테스트")
    print("="*60)

    if not requirements:
        print("❌ 요구사항 없음, 테스트 스킵")
        return None

    client = get_claude_client()
    generator = PRDGenerator(client)

    start = time.time()
    try:
        prd = await generator.generate(
            requirements,
            source_documents=["test_requirements.txt"]
        )
        elapsed = time.time() - start

        print(f"✅ PRD 생성 성공: {elapsed:.2f}초")
        print(f"   - PRD ID: {prd.id}")
        print(f"   - 제목: {prd.title}")
        print(f"   - 기능 요구사항: {len(prd.functional_requirements)}개")
        print(f"   - 비기능 요구사항: {len(prd.non_functional_requirements)}개")
        print(f"   - 제약조건: {len(prd.constraints)}개")
        print(f"   - 마일스톤: {len(prd.milestones)}개")
        print(f"   - 미해결 항목: {len(prd.unresolved_items)}개")
        print(f"   - 전체 신뢰도: {prd.metadata.overall_confidence:.0%}")

        print(f"\n   개요:")
        print(f"   - 배경: {prd.overview.background[:100]}...")
        print(f"   - 목표: {prd.overview.goals[:3]}")

        return prd
    except Exception as e:
        print(f"❌ PRD 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_full_test():
    """전체 파이프라인 테스트 실행."""
    print("\n" + "="*60)
    print("PRD 생성 파이프라인 전체 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    total_start = time.time()

    # Layer 1: 파싱
    parsed = await test_layer1_parsing()

    # Layer 2: 정규화
    requirements = await test_layer2_normalization(parsed)

    # Layer 3: 검증
    validated = await test_layer3_validation(requirements)

    # Layer 4: PRD 생성
    prd = await test_layer4_generation(validated or requirements)

    total_elapsed = time.time() - total_start

    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"총 소요 시간: {total_elapsed:.2f}초 ({total_elapsed/60:.1f}분)")
    print(f"Layer 1 (파싱): {'✅ 성공' if parsed else '❌ 실패'}")
    print(f"Layer 2 (정규화): {'✅ 성공' if requirements else '❌ 실패'}")
    print(f"Layer 3 (검증): {'✅ 성공' if validated is not None else '❌ 실패'}")
    print(f"Layer 4 (생성): {'✅ 성공' if prd else '❌ 실패'}")

    if prd:
        print(f"\n최종 PRD: {prd.id}")
        print(f"제목: {prd.title}")


if __name__ == "__main__":
    asyncio.run(run_full_test())
