# WBS Maker

최신 PRD 및 TRD JSON 파일을 기반으로 WBS (Work Breakdown Structure) 문서를 생성합니다.

TRD의 기술 스택, API 엔드포인트, 데이터베이스 엔티티, 인프라 요구사항 정보를 활용하여 더 정확한 작업 분해와 공수 산정을 수행합니다.

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


def find_latest_json(directory: str, prefix: str) -> Path:
    \"\"\"최신 JSON 파일 찾기.\"\"\"
    dir_path = Path(directory)
    json_files = list(dir_path.glob(f'{prefix}-*.json'))

    if not json_files:
        return None

    # 가장 최근 파일
    return max(json_files, key=lambda x: x.stat().st_mtime)


def load_trd_context(trd_path: Path) -> dict:
    \"\"\"TRD에서 WBS 생성에 필요한 컨텍스트 추출.\"\"\"
    with open(trd_path, 'r', encoding='utf-8') as f:
        trd_data = json.load(f)

    context = {
        'technology_stack': [],
        'api_count': 0,
        'entity_count': 0,
        'security_requirements': [],
        'infrastructure_requirements': [],
        'technical_risks': [],
    }

    # 기술 스택 추출
    for stack in trd_data.get('technology_stack', []):
        context['technology_stack'].extend(stack.get('technologies', []))

    # API 엔드포인트 수
    api_spec = trd_data.get('api_specification', {})
    context['api_count'] = len(api_spec.get('endpoints', []))

    # DB 엔티티 수
    db_design = trd_data.get('database_design', {})
    context['entity_count'] = len(db_design.get('entities', []))

    # 보안 요구사항
    context['security_requirements'] = [
        req.get('requirement', '')
        for req in trd_data.get('security_requirements', [])
    ]

    # 인프라 요구사항
    context['infrastructure_requirements'] = [
        req.get('specification', '')
        for req in trd_data.get('infrastructure_requirements', [])
    ]

    # 기술 리스크
    context['technical_risks'] = [
        risk.get('description', '')
        for risk in trd_data.get('technical_risks', [])
    ]

    return context


async def generate_wbs():
    print('\n' + '='*70)
    print('WBS 생성 시작 (PRD + TRD 기반)')
    print(f'시작 시간: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('='*70)

    # 최신 PRD 찾기
    prd_path = find_latest_json('workspace/outputs/prd', 'PRD')
    if not prd_path:
        raise FileNotFoundError('PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd_maker를 실행하세요.')
    print(f'\n[입력] PRD: {prd_path}')

    # PRD 로드
    with open(prd_path, 'r', encoding='utf-8') as f:
        prd_data = json.load(f)
    prd = PRDDocument(**prd_data)
    print(f'  - 제목: {prd.title}')
    print(f'  - 기능 요구사항: {len(prd.functional_requirements)}개')
    print(f'  - 비기능 요구사항: {len(prd.non_functional_requirements)}개')
    print(f'  - 마일스톤: {len(prd.milestones)}개')

    # 최신 TRD 찾기 (선택적)
    trd_path = find_latest_json('workspace/outputs/trd', 'TRD')
    trd_context = None
    if trd_path:
        print(f'\n[입력] TRD: {trd_path}')
        trd_context = load_trd_context(trd_path)
        print(f'  - 기술 스택: {len(trd_context[\"technology_stack\"])}개')
        print(f'  - API 엔드포인트: {trd_context[\"api_count\"]}개')
        print(f'  - DB 엔티티: {trd_context[\"entity_count\"]}개')
        print(f'  - 보안 요구사항: {len(trd_context[\"security_requirements\"])}개')
        print(f'  - 인프라 요구사항: {len(trd_context[\"infrastructure_requirements\"])}개')
        print(f'  - 기술 리스크: {len(trd_context[\"technical_risks\"])}개')
    else:
        print('\n[참고] TRD 파일이 없습니다. PRD만으로 WBS를 생성합니다.')
        print('       더 정확한 공수 산정을 위해 /trd:trd_maker를 먼저 실행하세요.')

    # WBS 컨텍스트 설정 (TRD 기반 리소스 타입 조정)
    resource_types = ['PM', '기획자', '프론트엔드 개발자', '백엔드 개발자', 'QA']

    if trd_context:
        tech_stack = ' '.join(trd_context['technology_stack']).lower()
        # TRD 기술 스택에 따라 리소스 타입 조정
        if any(kw in tech_stack for kw in ['kubernetes', 'docker', 'aws', 'gcp', 'azure', 'terraform']):
            resource_types.append('DevOps/인프라')
        if any(kw in tech_stack for kw in ['security', 'oauth', 'jwt', 'encryption']):
            resource_types.append('보안 전문가')
        if trd_context['entity_count'] > 10:
            resource_types.append('DBA')

    context = WBSContext(
        start_date=date.today(),
        team_size=5,
        methodology='agile',
        sprint_duration_weeks=2,
        working_hours_per_day=8,
        buffer_percentage=0.2,
        resource_types=resource_types,
    )

    print(f'\n[설정] WBS 컨텍스트')
    print(f'  - 시작일: {context.start_date}')
    print(f'  - 팀 규모: {context.team_size}명')
    print(f'  - 개발 방법론: {context.methodology}')
    print(f'  - 스프린트 주기: {context.sprint_duration_weeks}주')
    print(f'  - 버퍼 비율: {context.buffer_percentage:.0%}')
    print(f'  - 리소스 유형: {len(context.resource_types)}개')

    # WBS 생성
    output_dir = Path('workspace/outputs/wbs')
    output_dir.mkdir(parents=True, exist_ok=True)

    print('\n' + '-'*70)
    print('[Layer 7] WBS 생성')
    print('-'*70)

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

    # TRD 참조 정보 출력
    if trd_context:
        print(f'\n[TRD 반영 정보]')
        print(f'  - TRD 기반 리소스 유형 조정: {resource_types}')
        if trd_context['api_count'] > 0:
            print(f'  - API 개발 작업 반영: {trd_context[\"api_count\"]}개 엔드포인트')
        if trd_context['entity_count'] > 0:
            print(f'  - DB 설계/개발 작업 반영: {trd_context[\"entity_count\"]}개 엔티티')

    return wbs


asyncio.run(generate_wbs())
"
```

## 입력

### 필수 입력
- **PRD**: `workspace/outputs/prd/PRD-*.json` (최신 파일 자동 선택)
  - 기능 요구사항, 비기능 요구사항, 마일스톤 정보 활용
  - PRDDocument 형식의 JSON

### 선택 입력 (권장)
- **TRD**: `workspace/outputs/trd/TRD-*.json` (최신 파일 자동 선택)
  - 기술 스택, API 엔드포인트, DB 엔티티 정보 활용
  - 더 정확한 공수 산정을 위해 TRD 생성 후 WBS 생성 권장

## 출력

- **Markdown**: `workspace/outputs/wbs/WBS-{timestamp}.md`
- **JSON**: `workspace/outputs/wbs/WBS-{timestamp}.json`

## 처리 파이프라인

```
PRD (Layer 4) ─────────────────────────┐
                                       ├──▶ [Layer 7: WBS 생성] ──▶ WBS 문서
TRD (Layer 6, 선택) ───────────────────┘
```

1. **PRD 분석**: 기능 요구사항, 비기능 요구사항, 마일스톤 추출
2. **TRD 분석** (선택): 기술 스택, API 수, DB 엔티티 수, 인프라 요구사항 추출
3. **단계 생성**: 개발 방법론에 따른 프로젝트 단계(Phase) 정의
4. **작업 패키지 생성**: 각 단계별 작업 패키지(Work Package) 분해
5. **세부 작업 생성**: 작업 패키지별 세부 작업(Task) 정의 및 공수 산정
6. **의존성 설정**: 작업 간 선후행 관계 정의
7. **리소스 배분**: 작업별 담당 리소스 할당
8. **일정 계산**: 시작일/종료일 산정
9. **크리티컬 패스 분석**: 프로젝트 최장 경로 식별

## WBS 컨텍스트 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `start_date` | 프로젝트 시작일 | 오늘 |
| `team_size` | 팀 규모 | 5명 |
| `methodology` | 개발 방법론 (agile, waterfall, hybrid) | agile |
| `sprint_duration_weeks` | 스프린트 주기 | 2주 |
| `working_hours_per_day` | 일일 작업 시간 | 8시간 |
| `buffer_percentage` | 버퍼 비율 (0.0~1.0) | 0.2 (20%) |
| `resource_types` | 리소스 유형 목록 | PM, 기획자, 개발자, QA |

### TRD 기반 리소스 자동 조정

TRD가 있는 경우 기술 스택에 따라 리소스 유형이 자동으로 추가됩니다:

| TRD 기술 스택 | 추가 리소스 |
|--------------|------------|
| Kubernetes, Docker, AWS, GCP, Terraform | DevOps/인프라 |
| OAuth, JWT, Security 관련 | 보안 전문가 |
| DB 엔티티 10개 이상 | DBA |

## WBS 구조

```
프로젝트
└── Phase (단계)
    ├── 마일스톤
    ├── 주요 산출물
    └── Work Package (작업 패키지)
        ├── 설명
        └── Task (세부 작업)
            ├── 예상 공수 (시간)
            ├── 담당 리소스
            ├── 의존성
            ├── 시작일/종료일
            ├── 산출물
            └── 관련 요구사항 ID
```

## 생성 항목

### 1. WBS 요약
- 총 단계/작업 패키지/작업 수
- 총 예상 공수 (시간, M/D, M/M)
- 예상 기간 (일)
- 리소스별 투입 계획
- 크리티컬 패스

### 2. 단계별 작업 분해

| 개발 방법론 | 기본 단계 |
|------------|----------|
| **Agile** | 프로젝트 준비 → Sprint 1 (MVP) → Sprint 2-3 (추가 기능) → Sprint 4 (안정화) → 릴리즈 |
| **Waterfall** | 요구사항 분석 → 설계 → 개발 → 테스트 → 배포/오픈 |

각 단계에는 다음 정보가 포함됩니다:
- **Phase**: 마일스톤, 주요 산출물
- **Work Package**: 작업 범위, 관련 요구사항
- **Task**: 예상 공수, 담당, 의존성, 산출물

### 3. 일정 개요
- 단계별 공수 시각화 (텍스트 기반 차트)
- 크리티컬 패스 표시

### 4. TRD 연계 작업 (TRD 입력 시)
- **API 개발**: TRD의 API 엔드포인트별 개발 작업
- **DB 구축**: TRD의 엔티티별 테이블 설계/구현 작업
- **인프라 구축**: TRD의 인프라 요구사항 기반 작업
- **보안 구현**: TRD의 보안 요구사항 기반 작업

## 공수 산정 기준

| 작업 유형 | 기본 공수 | 비고 |
|----------|----------|------|
| 기획/분석 | 8~16h | 요구사항 복잡도에 따라 조정 |
| 화면 설계 | 8h/화면 | UI/UX 복잡도에 따라 조정 |
| API 개발 | 4~8h/엔드포인트 | CRUD 기준, 복잡 로직은 추가 |
| DB 설계 | 4h/엔티티 | 관계 복잡도에 따라 조정 |
| 단위 테스트 | 개발 공수의 30% | 테스트 커버리지 목표에 따라 조정 |
| 통합 테스트 | 개발 공수의 20% | |
| 문서화 | 개발 공수의 10% | |

## 주의사항

- PRD JSON 파일이 먼저 생성되어 있어야 합니다 (`/prd:prd_maker` 실행)
- 더 정확한 공수 산정을 위해 TRD 생성 후 WBS를 생성하세요 (`/trd:trd_maker` 실행)
- Claude API 키가 `.env` 파일에 설정되어 있어야 합니다
- 생성 시간은 PRD/TRD 복잡도에 따라 달라질 수 있습니다
- **공수 산정은 참고용**이며, 실제 프로젝트에서는 팀 역량/경험에 따른 검토가 필요합니다
- 버퍼 비율은 프로젝트 리스크 수준에 따라 조정하세요 (신규 기술 도입 시 30% 이상 권장)

## 권장 실행 순서

```
1. /prd:prd_maker   # PRD 생성
2. /trd:trd_maker   # TRD 생성 (기술 설계)
3. /wbs:wbs_maker   # WBS 생성 (PRD + TRD 기반)
```
