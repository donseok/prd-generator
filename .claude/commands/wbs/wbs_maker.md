# WBS Maker

최신 PRD JSON 파일을 기반으로 WBS (Work Breakdown Structure) 문서를 생성합니다.

## 실행 방법

다음 Python 스크립트를 실행하여 WBS를 생성합니다:

```bash
python -c "
import asyncio
import sys
import json
import time
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))

from app.models import PRDDocument
from app.layers.layer7_wbs import WBSGenerator, WBSContext


def find_latest_prd_json():
    \"\"\"최신 PRD JSON 파일 찾기.\"\"\"
    prd_dir = Path('workspace/outputs/prd')
    json_files = list(prd_dir.glob('PRD-*.json'))

    if not json_files:
        raise FileNotFoundError('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd_maker를 실행하세요.')

    # 가장 최근 파일
    latest = max(json_files, key=lambda x: x.stat().st_mtime)
    return latest


async def generate_wbs():
    print('\n' + '='*70)
    print('WBS 생성 시작')
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

    # WBS 컨텍스트 설정
    context = WBSContext(
        start_date=date.today(),
        team_size=5,
        methodology='agile',
        sprint_duration_weeks=2,
        working_hours_per_day=8,
        buffer_percentage=0.2,
        resource_types=['PM', '기획자', '프론트엔드 개발자', '백엔드 개발자', 'QA'],
    )

    # WBS 생성
    output_dir = Path('workspace/outputs/wbs')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    generator = WBSGenerator()
    wbs = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print('\n' + '='*70)
    print('WBS 생성 완료')
    print('='*70)
    print(f'\n  WBS ID: {wbs.id}')
    print(f'  제목: {wbs.title}')
    print(f'  총 단계: {wbs.summary.total_phases}개')
    print(f'  총 작업 패키지: {wbs.summary.total_work_packages}개')
    print(f'  총 작업: {wbs.summary.total_tasks}개')
    print(f'  총 예상 공수: {wbs.summary.total_hours:.0f}시간')
    print(f'  총 M/D: {wbs.summary.total_man_days:.1f}일')
    print(f'  총 M/M: {wbs.summary.total_man_months:.1f}개월')
    print(f'  예상 기간: {wbs.summary.estimated_duration_days}일')
    print(f'  크리티컬 패스: {len(wbs.summary.critical_path)}개 작업')
    print(f'  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)')

    # Markdown 저장
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = output_dir / f'WBS-{timestamp}.md'
    md_content = wbs.to_markdown()
    md_path.write_text(md_content, encoding='utf-8')
    print(f'\nMarkdown 저장: {md_path}')

    # JSON 저장
    json_path = output_dir / f'WBS-{timestamp}.json'
    json_content = wbs.to_json()
    json_path.write_text(json_content, encoding='utf-8')
    print(f'JSON 저장: {json_path}')

    return wbs


asyncio.run(generate_wbs())
"
```

## 입력

- **경로**: `workspace/outputs/prd/PRD-*.json` (최신 파일 자동 선택)
- **포맷**: JSON (PRDDocument 형식)

## 출력

- **Markdown**: `workspace/outputs/wbs/WBS-{timestamp}.md`
- **JSON**: `workspace/outputs/wbs/WBS-{timestamp}.json`

## WBS 컨텍스트 옵션

- `start_date`: 프로젝트 시작일 (기본: 오늘)
- `team_size`: 팀 규모 (기본: 5명)
- `methodology`: 개발 방법론 (agile, waterfall, hybrid)
- `sprint_duration_weeks`: 스프린트 주기 (기본: 2주)
- `working_hours_per_day`: 일일 작업 시간 (기본: 8시간)
- `buffer_percentage`: 버퍼 비율 (기본: 0.2 = 20%)
- `resource_types`: 리소스 유형 목록

## WBS 구조

```
프로젝트
└── Phase (단계)
    └── Work Package (작업 패키지)
        └── Task (세부 작업)
```

## 생성 항목

1. **WBS 요약**
   - 총 단계/작업 패키지/작업 수
   - 총 예상 공수 (시간, M/D, M/M)
   - 예상 기간
   - 리소스별 투입 계획
   - 크리티컬 패스

2. **단계별 작업 분해**
   - 단계 (Phase): 마일스톤, 주요 산출물
   - 작업 패키지 (Work Package): 관련 요구사항
   - 세부 작업 (Task): 예상 공수, 담당, 의존성, 산출물

3. **일정 개요**
   - 단계별 공수 시각화
   - 크리티컬 패스 표시

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다 (`/prd:prd_maker` 실행)
- Claude API 키가 `.env` 파일에 설정되어 있어야 합니다
- 생성 시간은 PRD 복잡도에 따라 달라질 수 있습니다
- 공수 산정은 참고용이며, 실제 프로젝트에서는 검토가 필요합니다
