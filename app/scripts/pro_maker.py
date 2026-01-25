#!/usr/bin/env python3
"""Proposal maker script.

Usage:
    python -m app.scripts.pro_maker
    python -m app.scripts.pro_maker --client "ABC Corporation"
"""

import asyncio
import argparse
import sys
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    parser = argparse.ArgumentParser(description="제안서 생성")
    parser.add_argument("--client", type=str, default="귀사", help="고객사명")
    args = parser.parse_args()

    from app.models import PRDDocument
    from app.layers.layer5_proposal import ProposalGenerator, ProposalContext

    print('\n' + '=' * 70)
    print('제안서 생성 시작')
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
    print(f'고객사: {args.client}')

    # 제안서 컨텍스트
    context = ProposalContext(
        client_name=args.client,
        project_name=prd.title,
        project_duration_months=6,
    )

    output_dir = Path('workspace/outputs/proposals')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    generator = ProposalGenerator()
    proposal = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '=' * 70)
    print('제안서 생성 완료')
    print('=' * 70)
    print(f'\n  제안서 ID: {proposal.id}')
    print(f'  제목: {proposal.title}')
    print(f'  고객사: {proposal.client_name}')
    print(f'  프로젝트 기간: {proposal.timeline.total_duration}')
    print(f'  투입 공수: {proposal.resource_plan.total_man_months:.1f} M/M')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'PROP-{timestamp}.md'
    md_path.write_text(proposal.to_markdown(), encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    json_path = output_dir / f'PROP-{timestamp}.json'
    json_path.write_text(proposal.to_json(), encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return proposal


if __name__ == "__main__":
    asyncio.run(main())
