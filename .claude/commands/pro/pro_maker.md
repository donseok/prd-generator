# Proposal Maker

최신 PRD JSON 파일을 기반으로 고객 제안서(Proposal)를 생성합니다.

## 실행 방법

다음 Python 스크립트를 실행하여 제안서를 생성합니다:

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
from app.layers.layer5_proposal import ProposalGenerator, ProposalContext


def find_latest_prd_json():
    \"\"\"최신 PRD JSON 파일 찾기.\"\"\"
    prd_dir = Path('workspace/outputs/prd')
    json_files = list(prd_dir.glob('PRD-*.json'))

    if not json_files:
        raise FileNotFoundError('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd_maker를 실행하세요.')

    # 가장 최근 파일
    latest = max(json_files, key=lambda x: x.stat().st_mtime)
    return latest


async def generate_proposal():
    print('\n' + '='*70)
    print('제안서 생성 시작')
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
    print(f'비기능 요구사항: {len(prd.non_functional_requirements)}개')

    # 제안서 컨텍스트 설정
    # 고객사명은 PRD 제목에서 추출하거나 기본값 사용
    client_name = input('\n고객사명을 입력하세요 (기본: 귀사): ').strip() or '귀사'
    
    context = ProposalContext(
        client_name=client_name,
        project_name=prd.title,
        project_duration_months=6,
    )

    # 제안서 생성
    output_dir = Path('workspace/outputs/proposals')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    print('\n' + '-'*70)
    print('[Layer 5] 제안서 생성')
    print('-'*70)

    generator = ProposalGenerator()
    proposal = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '='*70)
    print('제안서 생성 완료')
    print('='*70)
    print(f'\n  제안서 ID: {proposal.id}')
    print(f'  제목: {proposal.title}')
    print(f'  고객사: {proposal.client_name}')
    print(f'  프로젝트 기간: {proposal.timeline.total_duration}')
    print(f'  투입 공수: {proposal.resource_plan.total_man_months:.1f} M/M')
    print(f'  리스크: {len(proposal.risks)}건')
    print(f'  문서 신뢰도: {proposal.metadata.overall_confidence:.0%}')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # Markdown 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'PROP-{timestamp}.md'
    md_content = proposal.to_markdown()
    md_path.write_text(md_content, encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    # JSON 저장
    json_path = output_dir / f'PROP-{timestamp}.json'
    json_content = proposal.to_json()
    json_path.write_text(json_content, encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return proposal


asyncio.run(generate_proposal())
"
```

## 입력

- **경로**: `workspace/outputs/prd/PRD-*.json` (최신 파일 자동 선택)
- **포맷**: JSON (PRDDocument 형식)

## 출력

- **Markdown**: `workspace/outputs/proposals/PROP-{timestamp}.md`
- **JSON**: `workspace/outputs/proposals/PROP-{timestamp}.json`

## 제안서 생성 항목

1. **경영진 요약**: 프로젝트 개요 및 핵심 가치 제안
2. **프로젝트 개요**: 배경, 목표, 성공 기준
3. **작업 범위**: 포함/제외 범위, 주요 기능
4. **솔루션 접근법**: 아키텍처, 기술 스택, 개발 방법론
5. **일정 계획**: 마일스톤 기반 단계별 계획
6. **산출물**: 단계별 산출물 목록
7. **투입 인력**: 역할별 인원 및 총 공수(M/M)
8. **리스크 및 대응방안**: 프로젝트 리스크 평가
9. **전제 조건**: 프로젝트 수행 전제조건
10. **기대 효과**: 정량적/정성적 기대효과
11. **후속 절차**: 계약 및 착수 절차

## 컨텍스트 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `client_name` | 고객사명 | 귀사 |
| `project_name` | 프로젝트명 | PRD 제목 사용 |
| `project_duration_months` | 프로젝트 기간 (월) | 6개월 |

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다 (`/prd:prd_maker` 실행)
- Claude API 키가 `.env` 파일에 설정되어 있어야 합니다
- 생성 시간은 PRD 복잡도에 따라 2-5분 소요됩니다
- 고객사명 입력 시 Enter를 누르면 기본값(귀사)이 사용됩니다

## 권장 실행 순서

```
1. /prd:prd_maker     # PRD 생성
2. /trd:trd_maker     # TRD 생성 (선택)
3. /wbs:wbs_maker     # WBS 생성 (선택)
4. /pro:pro-maker     # 제안서 생성
```

또는 @auto-doc --proposal 으로 한번에 생성 가능합니다.
