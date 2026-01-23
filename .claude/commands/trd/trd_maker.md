# TRD Maker

최신 PRD JSON 파일을 기반으로 TRD (Technical Requirements Document) 문서를 생성합니다.

## 실행 방법

다음 Python 스크립트를 실행하여 TRD를 생성합니다:

```bash
python -c "
import asyncio
import sys
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))

from app.models import PRDDocument
from app.layers.layer6_trd import TRDGenerator, TRDContext


def find_latest_prd_json():
    \"\"\"최신 PRD JSON 파일 찾기.\"\"\"
    prd_dir = Path('workspace/outputs/prd')
    json_files = list(prd_dir.glob('PRD-*.json'))

    if not json_files:
        raise FileNotFoundError('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd_maker를 실행하세요.')

    # 가장 최근 파일
    latest = max(json_files, key=lambda x: x.stat().st_mtime)
    return latest


async def generate_trd():
    print('\n' + '='*70)
    print('TRD 생성 시작')
    print(f'시작 시간: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('='*70)

    # 최신 PRD 찾기
    prd_path = find_latest_prd_json()
    print(f'\n입력 PRD: {prd_path}')

    # PRD 로드
    with open(prd_path, 'r', encoding='utf-8') as f:
        prd_data = json.load(f)
    prd = PRDDocument(**prd_data)
    print(f'PRD 제목: {prd.title}')
    print(f'기능 요구사항: {len(prd.functional_requirements)}개')

    # TRD 컨텍스트 설정
    context = TRDContext(
        target_environment='cloud',
        scalability_requirement='medium',
        security_level='standard',
    )

    # TRD 생성
    output_dir = Path('workspace/outputs/trd')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    generator = TRDGenerator()
    trd = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '='*70)
    print('TRD 생성 완료')
    print('='*70)
    print(f'\n  TRD ID: {trd.id}')
    print(f'  제목: {trd.title}')
    print(f'  기술 스택: {len(trd.technology_stack)}개 카테고리')
    print(f'  아키텍처 레이어: {len(trd.system_architecture.layers)}개')
    print(f'  데이터베이스 엔티티: {len(trd.database_design.entities)}개')
    print(f'  API 엔드포인트: {len(trd.api_specification.endpoints)}개')
    print(f'  보안 요구사항: {len(trd.security_requirements)}개')
    print(f'  성능 요구사항: {len(trd.performance_requirements)}개')
    print(f'  인프라 요구사항: {len(trd.infrastructure_requirements)}개')
    print(f'  기술 리스크: {len(trd.technical_risks)}개')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # Markdown 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'TRD-{timestamp}.md'
    md_content = trd.to_markdown()
    md_path.write_text(md_content, encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    # JSON 저장
    json_path = output_dir / f'TRD-{timestamp}.json'
    json_content = trd.to_json()
    json_path.write_text(json_content, encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return trd


asyncio.run(generate_trd())
"
```

## 입력

- **경로**: `workspace/outputs/prd/PRD-*.json` (최신 파일 자동 선택)
- **포맷**: JSON (PRDDocument 형식)

## 출력

- **Markdown**: `workspace/outputs/trd/TRD-{timestamp}.md`
- **JSON**: `workspace/outputs/trd/TRD-{timestamp}.json`

## TRD 컨텍스트 옵션

- `target_environment`: 배포 환경 (cloud, on-premise, hybrid)
- `scalability_requirement`: 확장성 요구 수준 (low, medium, high)
- `security_level`: 보안 수준 (basic, standard, high)
- `preferred_stack`: 선호 기술 스택 (선택)

## 생성 항목

1. **기술 요약**: 경영진/기술팀용 기술 개요
2. **기술 스택**: Frontend, Backend, Database, Infrastructure 별 추천 기술
3. **시스템 아키텍처**: 아키텍처 스타일, 레이어, 컴포넌트 정의
4. **데이터베이스 설계**: 엔티티, 속성, 관계 정의
5. **API 명세**: RESTful API 엔드포인트 정의
6. **보안 요구사항**: 인증, 인가, 데이터 보호 요구사항
7. **성능 요구사항**: 응답 시간, 처리량 등 성능 지표
8. **인프라 요구사항**: 컴퓨팅, 스토리지, 네트워크 사양
9. **기술 리스크**: 기술적 위험 요소 및 대응방안

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다 (`/prd:prd_maker` 실행)
- Claude API 키가 `.env` 파일에 설정되어 있어야 합니다
- 생성 시간은 PRD 복잡도에 따라 달라질 수 있습니다
