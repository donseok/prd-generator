#!/usr/bin/env python3
"""Auto-doc script for generating all documents.

Usage:
    python -m app.scripts.auto_doc
    python -m app.scripts.auto_doc --proposal
    python -m app.scripts.auto_doc --proposal --client "ABC Corporation"
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    parser = argparse.ArgumentParser(
        description="PRD, TRD, WBS, 제안서 자동 생성"
    )
    parser.add_argument(
        "--proposal",
        action="store_true",
        help="제안서까지 생성"
    )
    parser.add_argument(
        "--client",
        type=str,
        default="귀사",
        help="고객사명 (제안서 생성 시 사용)"
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
        include_proposal=args.proposal,
        client_name=args.client,
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
