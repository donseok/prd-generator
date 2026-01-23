#!/usr/bin/env python3
"""PRD maker script.

Usage:
    python -m app.scripts.prd_maker
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    from app.models import InputType
    from app.services.claude_client import get_claude_client
    from app.layers.layer1_parsing import ParserFactory
    from app.layers.layer2_normalization import Normalizer
    from app.layers.layer3_validation import Validator
    from app.layers.layer4_generation import PRDGenerator

    print('\n' + '=' * 70)
    print('PRD 생성 시작 - workspace/inputs/projects')
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    input_dir = Path('workspace/inputs/projects')
    output_dir = Path('workspace/outputs/prd')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파일 수집
    files = [f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    files = sorted(files, key=lambda x: x.name)

    print(f'\n처리할 파일 수: {len(files)}개')
    for i, f in enumerate(files, 1):
        print(f'  {i:2}. {f.name}')

    client = get_claude_client()
    factory = ParserFactory(client)
    normalizer = Normalizer(client)
    validator = Validator(client)
    generator = PRDGenerator(client)

    total_start = time.time()

    # Layer 1: 파싱
    print('\n' + '-' * 70)
    print('[Layer 1] 파싱')
    print('-' * 70)

    parsed_contents = []
    document_ids = []

    def get_input_type(file_path: Path) -> InputType:
        suffix = file_path.suffix.lower()
        type_map = {
            '.txt': InputType.TEXT, '.md': InputType.TEXT, '.json': InputType.TEXT,
            '.csv': InputType.CSV, '.xlsx': InputType.EXCEL, '.xls': InputType.EXCEL,
            '.pptx': InputType.POWERPOINT, '.ppt': InputType.POWERPOINT,
            '.docx': InputType.DOCUMENT, '.doc': InputType.DOCUMENT,
            '.png': InputType.IMAGE, '.jpg': InputType.IMAGE, '.jpeg': InputType.IMAGE,
        }
        return type_map.get(suffix, InputType.TEXT)

    for i, file_path in enumerate(files, 1):
        input_type = get_input_type(file_path)
        print(f'\n  [{i}/{len(files)}] {file_path.name} ({input_type.value})')

        try:
            parser = factory.get_parser(input_type)
            parsed = await parser.parse(file_path)
            parsed_contents.append(parsed)
            document_ids.append(f'doc-{i:03d}')
            text_len = len(parsed.raw_text) if parsed.raw_text else 0
            sections = len(parsed.sections) if parsed.sections else 0
            print(f'      완료: 텍스트 {text_len} chars, 섹션 {sections}개')
        except Exception as e:
            print(f'      실패: {e}')

    if not parsed_contents:
        print('\n파싱된 콘텐츠가 없어 종료합니다.')
        return

    # Layer 2: 정규화
    print('\n' + '-' * 70)
    print('[Layer 2] 정규화 (요구사항 추출)')
    print('-' * 70)

    requirements = await normalizer.normalize(parsed_contents, document_ids=document_ids)
    print(f'\n  추출된 요구사항: {len(requirements)}개')

    # Layer 3: 검증
    print('\n' + '-' * 70)
    print('[Layer 3] 검증')
    print('-' * 70)

    validated, review_items = await validator.validate(requirements, job_id='prd-maker')
    print(f'\n  승인: {len(validated)}개, PM검토 필요: {len(review_items)}개')

    # Layer 4: PRD 생성
    print('\n' + '-' * 70)
    print('[Layer 4] PRD 생성')
    print('-' * 70)

    source_docs = [f.name for f in files]
    prd = await generator.generate(validated or requirements, source_documents=source_docs)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '=' * 70)
    print('PRD 생성 완료')
    print('=' * 70)
    print(f'\n  PRD ID: {prd.id}')
    print(f'  제목: {prd.title}')
    print(f'  기능 요구사항: {len(prd.functional_requirements)}개')
    print(f'  비기능 요구사항: {len(prd.non_functional_requirements)}개')
    print(f'  제약조건: {len(prd.constraints)}개')
    print(f'  마일스톤: {len(prd.milestones)}개')
    print(f'  전체 신뢰도: {prd.metadata.overall_confidence:.0%}')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'PRD-{timestamp}.md'
    md_content = prd.to_markdown()
    md_path.write_text(md_content, encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    json_path = output_dir / f'PRD-{timestamp}.json'
    json_content = prd.to_json()
    json_path.write_text(json_content, encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return prd


if __name__ == "__main__":
    asyncio.run(main())
