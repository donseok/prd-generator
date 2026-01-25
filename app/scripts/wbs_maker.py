#!/usr/bin/env python3
"""WBS maker script.

Usage:
    python -m app.scripts.wbs_maker
"""

import asyncio
import sys
import json
import time
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    from app.models import PRDDocument
    from app.layers.layer7_wbs import WBSGenerator, WBSContext

    print('\n' + '=' * 70)
    print('WBS 생성 시작')
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 최신 PRD 찾기
    prd_dir = Path('workspace/outputs/prd')
    json_files = list(prd_dir.glob('PRD-*.json'))

    if not json_files:
        print('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd-maker를 실행하세요.')
        return

    prd_path = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f'\n입력 PRD: {prd_path}')

    # PRD 로드
    with open(prd_path, 'r', encoding='utf-8') as f:
        prd_data = json.load(f)
    prd = PRDDocument(**prd_data)
    print(f'PRD 제목: {prd.title}')
    print(f'기능 요구사항: {len(prd.functional_requirements)}개')

    # WBS 컨텍스트
    context = WBSContext(
        start_date=date.today(),
        team_size=5,
        methodology='agile',
        sprint_duration_weeks=2,
        working_hours_per_day=8,
        buffer_percentage=0.2,
    )

    output_dir = Path('workspace/outputs/wbs')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    generator = WBSGenerator()
    wbs = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '=' * 70)
    print('WBS 생성 완료')
    print('=' * 70)
    print(f'\n  WBS ID: {wbs.id}')
    print(f'  제목: {wbs.title}')
    print(f'  총 단계: {wbs.summary.total_phases}개')
    print(f'  총 작업 패키지: {wbs.summary.total_work_packages}개')
    print(f'  총 작업: {wbs.summary.total_tasks}개')
    print(f'  총 M/M: {wbs.summary.total_man_months:.1f}개월')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'WBS-{timestamp}.md'
    md_path.write_text(wbs.to_markdown(), encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    json_path = output_dir / f'WBS-{timestamp}.json'
    json_path.write_text(wbs.to_json(), encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return wbs


if __name__ == "__main__":
    asyncio.run(main())
