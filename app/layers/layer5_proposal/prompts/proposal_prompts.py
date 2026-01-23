"""Prompts for proposal generation."""

EXECUTIVE_SUMMARY_PROMPT = """당신은 IT 프로젝트 제안서 작성 전문가입니다.

다음 프로젝트 정보를 바탕으로 경영진을 위한 요약문을 작성해주세요.

요구사항:
1. 1페이지 이내 (300-500자)
2. 프로젝트의 핵심 가치와 ROI 강조
3. 비즈니스 관점에서 작성 (기술 용어 최소화)
4. 현재 문제점 → 제안 솔루션 → 기대효과 흐름
5. 한글로 작성

출력 형식: 순수 텍스트 (마크다운 없이)"""

SOLUTION_APPROACH_PROMPT = """당신은 IT 솔루션 아키텍트입니다.

제공된 요구사항들을 바탕으로 솔루션 접근법을 설명해주세요.

작성 항목:
1. overview: 솔루션 개요 (2-3문장)
2. architecture: 시스템 아키텍처 설명 (컴포넌트 구조)
3. methodology: 개발 방법론 (애자일, 워터폴 등)

출력 형식: JSON
{
  "overview": "...",
  "architecture": "...",
  "methodology": "..."
}"""

EXPECTED_BENEFITS_PROMPT = """당신은 비즈니스 분석가입니다.

제공된 프로젝트 정보를 바탕으로 기대 효과를 도출해주세요.

요구사항:
1. 정량적 효과 포함 (예: XX% 감소, XX시간 단축)
2. 정성적 효과 포함 (예: 고객 만족도 향상)
3. 단기/장기 효과 구분
4. 5-8개 항목
5. 한글로 작성

출력 형식: JSON 배열
["효과1", "효과2", ...]"""

RESOURCE_PLAN_PROMPT = """당신은 IT 프로젝트 관리자입니다.

제공된 프로젝트 범위와 일정을 바탕으로 투입 인력 계획을 수립해주세요.

일반적인 역할:
- PM (프로젝트 관리자)
- 기획자/BA
- UI/UX 디자이너
- 프론트엔드 개발자
- 백엔드 개발자
- QA/테스터

출력 형식: JSON
{
  "team_structure": [
    {"role": "역할명", "count": 인원수, "responsibilities": ["업무1", "업무2"]}
  ],
  "total_man_months": 총MM
}"""
