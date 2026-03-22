#!/usr/bin/env python3
"""Agent Team maker script.

PRD, TRD, WBS 문서를 분석하여 프로젝트 수행에 최적화된 에이전트 팀 구성 문서를 생성합니다.

Usage:
    python -m app.scripts.team_maker
    python -m app.scripts.team_maker --team-size 7
"""

import asyncio
import sys
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _find_latest_json(directory: Path, prefix: str) -> Path | None:
    """지정 폴더에서 prefix로 시작하는 최신 JSON 파일을 찾습니다."""
    json_files = list(directory.glob(f"{prefix}-*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda x: x.stat().st_mtime)


def _load_json(path: Path) -> dict:
    """JSON 파일을 읽어 딕셔너리로 반환합니다."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_prd_summary(prd: dict) -> str:
    """PRD에서 에이전트 팀 생성에 필요한 핵심 정보를 추출합니다."""
    lines = []
    lines.append(f"프로젝트명: {prd.get('title', 'N/A')}")

    overview = prd.get("overview", prd.get("project_overview", ""))
    if overview:
        lines.append(f"프로젝트 개요: {overview[:500]}")

    goals = prd.get("goals", prd.get("project_goals", []))
    if goals:
        if isinstance(goals, list):
            lines.append(f"프로젝트 목표: {', '.join(str(g) for g in goals[:5])}")
        else:
            lines.append(f"프로젝트 목표: {str(goals)[:300]}")

    fr = prd.get("functional_requirements", [])
    lines.append(f"기능 요구사항 수: {len(fr)}개")
    for req in fr[:10]:
        if isinstance(req, dict):
            lines.append(f"  - {req.get('title', req.get('name', req.get('id', '')))}: {req.get('description', '')[:100]}")
        else:
            lines.append(f"  - {str(req)[:120]}")

    nfr = prd.get("non_functional_requirements", [])
    if nfr:
        lines.append(f"비기능 요구사항 수: {len(nfr)}개")

    constraints = prd.get("constraints", [])
    if constraints:
        lines.append(f"제약조건: {len(constraints)}개")

    return "\n".join(lines)


def _extract_trd_summary(trd: dict) -> str:
    """TRD에서 에이전트 팀 생성에 필요한 기술 정보를 추출합니다."""
    lines = []

    tech_stack = trd.get("technology_stack", [])
    if tech_stack:
        lines.append("기술 스택:")
        for stack in tech_stack:
            if isinstance(stack, dict):
                cat = stack.get("category", "")
                techs = stack.get("technologies", [])
                lines.append(f"  - {cat}: {', '.join(techs) if isinstance(techs, list) else techs}")

    arch = trd.get("system_architecture", {})
    if arch:
        style = arch.get("architecture_style", "")
        if style:
            lines.append(f"아키텍처 스타일: {style}")
        layers = arch.get("layers", [])
        if layers:
            lines.append(f"시스템 레이어: {len(layers)}개")
            for layer in layers:
                if isinstance(layer, dict):
                    components = layer.get("components", [])
                    lines.append(f"  - {layer.get('name', '')}: 컴포넌트 {len(components)}개")

    db = trd.get("database_design", {})
    if db:
        entities = db.get("entities", [])
        lines.append(f"데이터베이스 엔티티: {len(entities)}개")
        engine = db.get("recommended_engine", db.get("database_type", ""))
        if engine:
            lines.append(f"DB 엔진: {engine}")

    api = trd.get("api_specification", {})
    if api:
        endpoints = api.get("endpoints", [])
        lines.append(f"API 엔드포인트: {len(endpoints)}개")

    security = trd.get("security_requirements", [])
    if security:
        lines.append(f"보안 요구사항: {len(security)}개")

    risks = trd.get("technical_risks", [])
    if risks:
        lines.append(f"기술 리스크: {len(risks)}개")

    return "\n".join(lines)


def _extract_wbs_summary(wbs: dict) -> str:
    """WBS에서 에이전트 팀 구성에 필요한 작업/역할 정보를 추출합니다."""
    lines = []

    summary = wbs.get("summary", {})
    if summary:
        lines.append(f"총 공수: {summary.get('total_hours', 'N/A')}시간")
        lines.append(f"M/M: {summary.get('man_months', 'N/A')}")
        lines.append(f"총 태스크: {summary.get('total_tasks', 'N/A')}개")
        critical_path = summary.get("critical_path", [])
        if critical_path:
            lines.append(f"크리티컬 패스: {' -> '.join(str(cp) for cp in critical_path)}")

    context = wbs.get("context", {})
    if context:
        lines.append(f"팀 규모: {context.get('team_size', 'N/A')}명")
        lines.append(f"방법론: {context.get('methodology', 'N/A')}")
        lines.append(f"스프린트 기간: {context.get('sprint_duration_weeks', 'N/A')}주")

    phases = wbs.get("phases", [])
    if phases:
        lines.append(f"\n페이즈: {len(phases)}개")
        for phase in phases:
            if isinstance(phase, dict):
                name = phase.get("name", phase.get("phase_name", ""))
                work_packages = phase.get("work_packages", [])
                total_tasks = sum(
                    len(wp.get("tasks", [])) for wp in work_packages if isinstance(wp, dict)
                )
                total_hours = sum(
                    sum(t.get("estimated_hours", 0) for t in wp.get("tasks", []) if isinstance(t, dict))
                    for wp in work_packages if isinstance(wp, dict)
                )
                lines.append(f"  - {name}: 작업패키지 {len(work_packages)}개, 태스크 {total_tasks}개, {total_hours}시간")

    # 역할별 공수 추출
    role_hours: dict[str, float] = {}
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        for wp in phase.get("work_packages", []):
            if not isinstance(wp, dict):
                continue
            for task in wp.get("tasks", []):
                if not isinstance(task, dict):
                    continue
                role = task.get("role", task.get("assigned_role", "Unknown"))
                hours = task.get("estimated_hours", 0)
                role_hours[role] = role_hours.get(role, 0) + hours

    if role_hours:
        lines.append("\n역할별 공수 배분:")
        for role, hours in sorted(role_hours.items(), key=lambda x: -x[1]):
            lines.append(f"  - {role}: {hours:.0f}시간")

    return "\n".join(lines)


def _build_prompt(prd_summary: str, trd_summary: str, wbs_summary: str, team_size: int) -> str:
    """에이전트 팀 생성을 위한 Claude 프롬프트를 구성합니다."""
    return f"""당신은 소프트웨어 프로젝트의 에이전트 팀을 설계하는 전문가입니다.
아래 PRD(제품 요구사항), TRD(기술 요구사항), WBS(작업 분해 구조) 분석 결과를 기반으로
이 프로젝트를 수행하기에 최적화된 AI 에이전트 팀 구성을 Markdown 문서로 작성하세요.

---

## 입력 데이터

### PRD 요약
{prd_summary}

### TRD 요약
{trd_summary}

### WBS 요약
{wbs_summary}

---

## 작성 규칙

1. **팀 규모**: {team_size}명의 에이전트로 구성
2. **역할 최적화**: WBS의 역할별 공수 배분과 TRD의 기술 스택을 기반으로 역할 설계
3. **기술 매칭**: TRD의 기술 스택에 맞는 전문성을 각 에이전트에 부여
4. **작업 커버리지**: WBS의 모든 페이즈와 태스크를 팀이 커버할 수 있도록 구성
5. **한국어 작성**: 모든 내용을 한국어로 작성

## 출력 형식 (정확히 이 구조를 따라주세요)

```markdown
# [프로젝트명] 에이전트 팀 구성

> 이 문서는 PRD, TRD, WBS 분석을 기반으로 자동 생성된 프로젝트 수행 최적화 에이전트 팀 구성입니다.

**생성일**: [오늘 날짜]
**기반 문서**: PRD, TRD, WBS
**팀 규모**: {team_size}명

---

## 프로젝트 개요

[PRD 기반 프로젝트 요약 2~3문장]

---

## 기술 환경

[TRD 기반 기술 스택 요약 테이블]

---

## 팀 구성

### [역할명] - [에이전트 이름]

**전문 분야**: [기술 영역]
**담당 페이즈**: [WBS 페이즈]
**핵심 역량**:
- [역량 1]
- [역량 2]
- [역량 3]

**담당 업무**:
- [업무 1]
- [업무 2]

**시스템 프롬프트**:
> 당신은 [역할] 전문가입니다. [프로젝트명] 프로젝트에서 [담당 영역]을 책임집니다.
> [구체적 기술 스택과 작업 범위에 대한 상세 프롬프트]
> [품질 기준과 산출물 형식에 대한 지침]

(위 형식을 {team_size}명 모두에 대해 반복)

---

## 팀 협업 구조

### 커뮤니케이션 매트릭스
[어떤 에이전트가 어떤 에이전트와 주로 소통하는지 표로 정리]

### 작업 흐름
[WBS 페이즈별로 어떤 에이전트가 주도하고 어떤 에이전트가 지원하는지]

### 의존성 관리
[에이전트 간 작업 의존성과 핸드오프 포인트]

---

## 품질 관리

### 코드 리뷰 체계
[리뷰 프로세스]

### 산출물 검증
[각 페이즈별 산출물과 검증 기준]

---

## 리스크 대응

[TRD 기술 리스크 기반 팀 차원의 대응 전략]

---

## 실행 가이드

### 에이전트 활성화 순서
[어떤 순서로 에이전트를 배치/활성화하는지]

### 마일스톤별 체크포인트
[WBS 기반 주요 마일스톤과 팀 체크포인트]
```

위 형식에 맞춰 작성하되, 프로젝트의 실제 데이터를 반영하여 구체적이고 실용적인 팀 구성을 만드세요.
특히 각 에이전트의 '시스템 프롬프트'는 해당 에이전트가 Claude Code에서 바로 사용할 수 있을 정도로 구체적으로 작성하세요."""


async def main():
    from app.services.claude_client import get_claude_client

    import argparse
    parser = argparse.ArgumentParser(description="프로젝트 최적화 에이전트 팀 생성")
    parser.add_argument("--team-size", type=int, default=5, help="에이전트 팀 인원 수 (기본: 5)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("에이전트 팀 구성 문서 생성 시작")
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print("=" * 70)

    # 1. 최신 PRD/TRD/WBS JSON 파일 탐색
    prd_dir = Path("workspace/outputs/prd")
    trd_dir = Path("workspace/outputs/trd")
    wbs_dir = Path("workspace/outputs/wbs")

    prd_path = _find_latest_json(prd_dir, "PRD")
    trd_path = _find_latest_json(trd_dir, "TRD")
    wbs_path = _find_latest_json(wbs_dir, "WBS")

    if not prd_path:
        print("PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd-maker를 실행하세요.")
        return

    print(f"\n입력 PRD: {prd_path.name}")
    prd_data = _load_json(prd_path)
    prd_summary = _extract_prd_summary(prd_data)
    print(f"  - 프로젝트: {prd_data.get('title', 'N/A')}")

    trd_summary = ""
    if trd_path:
        print(f"입력 TRD: {trd_path.name}")
        trd_data = _load_json(trd_path)
        trd_summary = _extract_trd_summary(trd_data)
    else:
        print("TRD 파일 없음 - PRD 기반으로 생성합니다.")

    wbs_summary = ""
    if wbs_path:
        print(f"입력 WBS: {wbs_path.name}")
        wbs_data = _load_json(wbs_path)
        wbs_summary = _extract_wbs_summary(wbs_data)
    else:
        print("WBS 파일 없음 - PRD 기반으로 생성합니다.")

    # 2. Claude CLI를 사용하여 에이전트 팀 문서 생성
    print(f"\n에이전트 팀 구성 생성 중 (팀 규모: {args.team_size}명)...")
    total_start = time.time()

    client = get_claude_client()
    prompt = _build_prompt(prd_summary, trd_summary, wbs_summary, args.team_size)

    result = await client.complete(
        system_prompt="프로젝트 에이전트 팀 구성 문서를 Markdown 형식으로 생성하세요. 코드 블록 없이 순수 Markdown만 출력하세요.",
        user_prompt=prompt,
    )

    total_time = time.time() - total_start

    # 3. 결과 저장
    output_dir = Path("workspace/outputs/agent-team")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = output_dir / f"TEAM-{timestamp}.md"
    md_path.write_text(result, encoding="utf-8")

    print("\n" + "=" * 70)
    print("에이전트 팀 구성 문서 생성 완료")
    print("=" * 70)
    print(f"\n  팀 규모: {args.team_size}명")
    print(f"  저장 위치: {md_path}")
    print(f"  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)")

    return md_path


if __name__ == "__main__":
    asyncio.run(main())
