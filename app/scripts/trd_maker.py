#!/usr/bin/env python3
"""TRD maker script.

Usage:
    python -m app.scripts.trd_maker
"""

import asyncio
import sys
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    from app.models import PRDDocument
    from app.layers.layer6_trd import TRDGenerator, TRDContext

    print('\n' + '=' * 70)
    print('TRD 생성 시작')
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 최신 PRD 찾기
    prd_dir = Path('workspace/outputs/prd')
    json_files = list(prd_dir.glob('PRD-*.json'))

    if not json_files:
        print('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd_maker를 실행하세요.')
        return

    prd_path = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f'\n입력 PRD: {prd_path}')

    # PRD 로드
    with open(prd_path, 'r', encoding='utf-8') as f:
        prd_data = json.load(f)
    prd = PRDDocument(**prd_data)
    print(f'PRD 제목: {prd.title}')
    print(f'기능 요구사항: {len(prd.functional_requirements)}개')

    # TRD 컨텍스트
    context = TRDContext(
        target_environment='cloud',
        scalability_requirement='medium',
        security_level='standard',
    )

    output_dir = Path('workspace/outputs/trd')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    generator = TRDGenerator()
    trd = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '=' * 70)
    print('TRD 생성 완료')
    print('=' * 70)
    print(f'\n  TRD ID: {trd.id}')
    print(f'  제목: {trd.title}')
    print(f'  기술 스택: {len(trd.technology_stack)}개 카테고리')
    print(f'  아키텍처 레이어: {len(trd.system_architecture.layers)}개')
    print(f'  데이터베이스 엔티티: {len(trd.database_design.entities)}개')
    print(f'  API 엔드포인트: {len(trd.api_specification.endpoints)}개')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'TRD-{timestamp}.md'
    md_path.write_text(trd.to_markdown(), encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    json_path = output_dir / f'TRD-{timestamp}.json'
    json_path.write_text(trd.to_json(), encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return trd


if __name__ == "__main__":
    asyncio.run(main())
