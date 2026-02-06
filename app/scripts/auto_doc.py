#!/usr/bin/env python3
"""Auto-doc script for generating all 5 documents.

Usage:
    python -m app.scripts.auto_doc

Generates: PRD → TRD → WBS → Proposal → PPT
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Windows 콘솔 코드 페이지를 UTF-8로 변경
    os.system('chcp 65001 > nul 2>&1')

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    parser = argparse.ArgumentParser(
        description="PRD, TRD, WBS, 제안서, PPT 5종 자동 생성"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="workspace/inputs/projects",
        help="입력 파일 디렉토리"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="workspace/outputs",
        help="출력 기본 디렉토리"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="상세 로그 숨기기"
    )

    args = parser.parse_args()

    from app.services.document_orchestrator import DocumentOrchestrator

    orchestrator = DocumentOrchestrator(
        input_dir=Path(args.input_dir),
        output_base_dir=Path(args.output_dir),
    )

    bundle = await orchestrator.generate_all(
        verbose=not args.quiet,
    )

    # 종료 코드: 에러가 있으면 1
    return 1 if bundle.errors else 0


def run_auto_doc():
    """CLI 진입점."""
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


if __name__ == "__main__":
    run_auto_doc()
