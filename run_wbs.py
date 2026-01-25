"""WBS 생성 스크립트 (PRD + TRD 기반)."""

import asyncio
import json
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from app.models import PRDDocument
from app.layers.layer7_wbs import WBSGenerator, WBSContext


def find_latest_json(directory: str, prefix: str) -> Optional[Path]:
    """최신 JSON 파일 찾기."""
    dir_path = Path(directory)
    json_files = list(dir_path.glob(f"{prefix}-*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda x: x.stat().st_mtime)


def load_trd_context(trd_path: Path) -> dict:
    """TRD에서 WBS 생성에 필요한 컨텍스트 추출."""
    with open(trd_path, "r", encoding="utf-8") as f:
        trd_data = json.load(f)

    context = {
        "technology_stack": [],
        "api_count": 0,
        "entity_count": 0,
        "security_requirements": [],
        "infrastructure_requirements": [],
        "technical_risks": [],
    }

    # 기술 스택 추출
    for stack in trd_data.get("technology_stack", []):
        context["technology_stack"].extend(stack.get("technologies", []))

    # API 엔드포인트 수
    api_spec = trd_data.get("api_specification", {})
    context["api_count"] = len(api_spec.get("endpoints", []))

    # DB 엔티티 수
    db_design = trd_data.get("database_design", {})
    context["entity_count"] = len(db_design.get("entities", []))

    # 보안 요구사항
    context["security_requirements"] = [
        req.get("requirement", "") for req in trd_data.get("security_requirements", [])
    ]

    # 인프라 요구사항
    context["infrastructure_requirements"] = [
        req.get("specification", "")
        for req in trd_data.get("infrastructure_requirements", [])
    ]

    # 기술 리스크
    context["technical_risks"] = [
        risk.get("description", "") for risk in trd_data.get("technical_risks", [])
    ]

    return context


async def generate_wbs():
    print("\n" + "=" * 70)
    print("WBS 생성 시작 (PRD + TRD 기반)")
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print("=" * 70)

    # 최신 PRD 찾기
    prd_path = find_latest_json("workspace/outputs/prd", "PRD")
    if not prd_path:
        raise FileNotFoundError(
            "PRD JSON 파일을 찾을 수 없습니다. 먼저 /prd:prd-maker를 실행하세요."
        )
    print(f"\n[입력] PRD: {prd_path}")

    # PRD 로드
    with open(prd_path, "r", encoding="utf-8") as f:
        prd_data = json.load(f)
    prd = PRDDocument(**prd_data)
    print(f"  - 제목: {prd.title}")
    print(f"  - 기능 요구사항: {len(prd.functional_requirements)}개")
    print(f"  - 비기능 요구사항: {len(prd.non_functional_requirements)}개")
    print(f"  - 마일스톤: {len(prd.milestones)}개")

    # 최신 TRD 찾기 (선택적)
    trd_path = find_latest_json("workspace/outputs/trd", "TRD")
    trd_context = None
    if trd_path:
        print(f"\n[입력] TRD: {trd_path}")
        trd_context = load_trd_context(trd_path)
        print(f'  - 기술 스택: {len(trd_context["technology_stack"])}개')
        print(f'  - API 엔드포인트: {trd_context["api_count"]}개')
        print(f'  - DB 엔티티: {trd_context["entity_count"]}개')
        print(f'  - 보안 요구사항: {len(trd_context["security_requirements"])}개')
        print(f'  - 인프라 요구사항: {len(trd_context["infrastructure_requirements"])}개')
        print(f'  - 기술 리스크: {len(trd_context["technical_risks"])}개')
    else:
        print("\n[참고] TRD 파일이 없습니다. PRD만으로 WBS를 생성합니다.")
        print("       더 정확한 공수 산정을 위해 /trd:trd-maker를 먼저 실행하세요.")

    # WBS 컨텍스트 설정 (TRD 기반 리소스 타입 조정)
    resource_types = ["PM", "기획자", "프론트엔드 개발자", "백엔드 개발자", "QA"]
    if trd_context:
        tech_stack = " ".join(trd_context["technology_stack"]).lower()
        if any(
            kw in tech_stack
            for kw in ["kubernetes", "docker", "aws", "gcp", "azure", "terraform"]
        ):
            resource_types.append("DevOps/인프라")
        if any(kw in tech_stack for kw in ["security", "oauth", "jwt", "encryption"]):
            resource_types.append("보안 전문가")
        if trd_context["entity_count"] > 10:
            resource_types.append("DBA")

    context = WBSContext(
        start_date=date.today(),
        team_size=5,
        methodology="agile",
        sprint_duration_weeks=2,
        working_hours_per_day=8,
        buffer_percentage=0.2,
        resource_types=resource_types,
    )

    print(f"\n[설정] WBS 컨텍스트")
    print(f"  - 시작일: {context.start_date}")
    print(f"  - 팀 규모: {context.team_size}명")
    print(f"  - 개발 방법론: {context.methodology}")
    print(f"  - 스프린트 주기: {context.sprint_duration_weeks}주")
    print(f"  - 버퍼 비율: {context.buffer_percentage:.0%}")
    print(f"  - 리소스 유형: {len(context.resource_types)}개")

    # WBS 생성
    output_dir = Path("workspace/outputs/wbs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 70)
    print("[Layer 7] WBS 생성")
    print("-" * 70)

    total_start = time.time()

    generator = WBSGenerator()
    wbs = await generator.generate(prd, context)

    total_time = time.time() - total_start

    # 결과 요약
    print("\n" + "=" * 70)
    print("WBS 생성 완료")
    print("=" * 70)
    print(f"\n  WBS ID: {wbs.id}")
    print(f"  제목: {wbs.title}")
    print(f"  총 단계: {wbs.summary.total_phases}개")
    print(f"  총 작업 패키지: {wbs.summary.total_work_packages}개")
    print(f"  총 작업: {wbs.summary.total_tasks}개")
    print(f"  총 예상 공수: {wbs.summary.total_hours:.0f}시간")
    print(f"  총 M/D: {wbs.summary.total_man_days:.1f}일")
    print(f"  총 M/M: {wbs.summary.total_man_months:.1f}개월")
    print(f"  예상 기간: {wbs.summary.estimated_duration_days}일")
    print(f"  크리티컬 패스: {len(wbs.summary.critical_path)}개 작업")
    print(f"  총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)")

    # Markdown 저장
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = output_dir / f"WBS-{timestamp}.md"
    md_content = wbs.to_markdown()
    md_path.write_text(md_content, encoding="utf-8")
    print(f"\nMarkdown 저장: {md_path}")

    # JSON 저장
    json_path = output_dir / f"WBS-{timestamp}.json"
    json_content = wbs.to_json()
    json_path.write_text(json_content, encoding="utf-8")
    print(f"JSON 저장: {json_path}")

    # TRD 참조 정보 출력
    if trd_context:
        print(f"\n[TRD 반영 정보]")
        print(f"  - TRD 기반 리소스 유형 조정: {resource_types}")
        if trd_context["api_count"] > 0:
            print(f'  - API 개발 작업 반영: {trd_context["api_count"]}개 엔드포인트')
        if trd_context["entity_count"] > 0:
            print(f'  - DB 설계/개발 작업 반영: {trd_context["entity_count"]}개 엔티티')

    return wbs


if __name__ == "__main__":
    asyncio.run(generate_wbs())
