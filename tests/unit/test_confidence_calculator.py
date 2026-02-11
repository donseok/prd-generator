"""ConfidenceCalculator (Layer 2) 단위 테스트.

다층 신뢰도 계산기 ConfidenceCalculator의 각 메서드를 테스트합니다:
- calculate: 가중 평균 최종 점수 계산
- _calculate_source_credibility: 출처 유형별 기본 신뢰도
- _calculate_clarity_score: 모호 표현 감지 및 감점
- _calculate_completeness_score: 필수 필드 완전성
- _is_valid_user_story: User Story 형식 검증
- ConfidenceBreakdown.to_reason_string: 감점 사유 문자열
"""

import pytest
from app.layers.layer2_normalization.confidence_calculator import (
    ConfidenceCalculator,
    ConfidenceBreakdown,
    get_confidence_calculator,
)


@pytest.fixture
def calculator():
    return ConfidenceCalculator()


def _full_requirement(**overrides) -> dict:
    """모든 필수 필드를 갖춘 고품질 요구사항."""
    base = dict(
        title="사용자 인증 시스템 구현",
        description="이메일과 비밀번호 기반의 인증 시스템을 구현해야 합니다. 로그인, 로그아웃, 세션 관리 포함.",
        type="FR",
        priority="HIGH",
        user_story="As a user, I want to log in with my email and password, so that I can access my account securely",
        acceptance_criteria=[
            "Given a valid email and password, When the user submits the login form, Then the user is authenticated",
            "Given an invalid password, When the user submits the login form, Then an error message is displayed",
        ],
        section_name="Authentication",
        original_text="사용자 인증 시스템 구현이 필요합니다",
    )
    base.update(overrides)
    return base


# ===================================================================
# ConfidenceBreakdown
# ===================================================================

class TestConfidenceBreakdown:
    def test_to_reason_string_no_reasons(self):
        bd = ConfidenceBreakdown(
            source_credibility=1.0,
            clarity_score=1.0,
            completeness_score=1.0,
            ai_confidence=1.0,
            final_score=1.0,
            deduction_reasons=[],
        )
        assert bd.to_reason_string() == "모든 항목 충족"

    def test_to_reason_string_with_reasons(self):
        bd = ConfidenceBreakdown(
            source_credibility=0.7,
            clarity_score=0.8,
            completeness_score=0.5,
            ai_confidence=0.6,
            final_score=0.65,
            deduction_reasons=["출처 신뢰도 낮음", "인수조건 누락"],
        )
        result = bd.to_reason_string()
        assert "출처 신뢰도 낮음" in result
        assert "인수조건 누락" in result

    def test_to_reason_string_truncates_to_3(self):
        bd = ConfidenceBreakdown(
            source_credibility=0.5,
            clarity_score=0.5,
            completeness_score=0.5,
            ai_confidence=0.5,
            final_score=0.5,
            deduction_reasons=["이유1", "이유2", "이유3", "이유4", "이유5"],
        )
        parts = bd.to_reason_string().split("; ")
        assert len(parts) == 3


# ===================================================================
# _calculate_source_credibility
# ===================================================================

class TestSourceCredibility:
    @pytest.mark.parametrize("source_type,expected", [
        ("document", 1.0),
        ("excel", 0.95),
        ("csv", 0.90),
        ("text", 0.85),
        ("ppt", 0.85),
        ("email", 0.70),
        ("image", 0.60),
        ("chat", 0.50),
        ("unknown", 0.70),
    ])
    def test_known_source_types(self, calculator, source_type, expected):
        assert calculator._calculate_source_credibility(source_type) == expected

    def test_unknown_source_defaults_to_0_7(self, calculator):
        assert calculator._calculate_source_credibility("foobar") == 0.70

    def test_case_insensitive(self, calculator):
        assert calculator._calculate_source_credibility("DOCUMENT") == 1.0
        assert calculator._calculate_source_credibility("Email") == 0.70

    def test_none_defaults_to_unknown(self, calculator):
        assert calculator._calculate_source_credibility(None) == 0.70


# ===================================================================
# _calculate_clarity_score
# ===================================================================

class TestClarityScore:
    def test_no_ambiguous_patterns_returns_1(self, calculator):
        # 모호 표현이 없는 명확한 텍스트만 사용
        raw = {
            "title": "Login System",
            "description": "Implement email-based authentication with password validation.",
            "user_story": "As a registered member, I want to log in with my email and password, so that I can access my dashboard",
            "acceptance_criteria": [
                "Given a valid email, When the form is submitted, Then the session is created"
            ],
        }
        score, issues = calculator._calculate_clarity_score(raw)
        assert score == 1.0
        assert issues == []

    def test_ambiguous_patterns_reduce_score(self, calculator):
        raw = _full_requirement(
            description="적절한 방법으로 충분한 성능을 보장해야 합니다. 빠른 응답이 필요합니다."
        )
        score, issues = calculator._calculate_clarity_score(raw)
        assert score < 1.0
        assert len(issues) > 0

    def test_minimum_clarity_score_is_0_3(self, calculator):
        """매우 많은 모호 표현이 있어도 최소 0.3."""
        raw = _full_requirement(
            title="적절한 시스템",
            description="충분한 양의 많은 데이터를 빠르게 가끔 처리해야 한다",
            user_story="사용자로서 적절히 좋은 서비스를 원한다",
        )
        score, _ = calculator._calculate_clarity_score(raw)
        assert score >= 0.3

    def test_issues_limited_to_3(self, calculator):
        raw = _full_requirement(
            description="적절한 방법으로 충분한 성능을 빠른 시간 내에 좋은 품질로 나중에 처리"
        )
        _, issues = calculator._calculate_clarity_score(raw)
        assert len(issues) <= 3


# ===================================================================
# _calculate_completeness_score
# ===================================================================

class TestCompletenessScore:
    def test_full_requirement_high_score(self, calculator):
        raw = _full_requirement()
        score, issues = calculator._calculate_completeness_score(raw)
        assert score > 0.8
        assert len(issues) <= 1  # user_story형식 불완전 가능

    def test_minimal_requirement_low_score(self, calculator):
        raw = {"title": "짧음", "description": "짧은 설명"}
        score, issues = calculator._calculate_completeness_score(raw)
        assert score < 0.5
        assert any("누락" in i for i in issues)

    def test_constraint_skips_user_story(self, calculator):
        raw = _full_requirement(type="CONSTRAINT")
        del raw["user_story"]
        score, issues = calculator._calculate_completeness_score(raw)
        # user_story가 없어도 CONSTRAINT는 만점 처리
        assert score > 0.7

    def test_empty_acceptance_criteria_penalized(self, calculator):
        raw = _full_requirement(acceptance_criteria=[])
        score, issues = calculator._calculate_completeness_score(raw)
        assert any("인수조건" in i for i in issues)

    def test_short_acceptance_criteria_penalized(self, calculator):
        """10자 미만 인수조건은 부실로 처리."""
        raw = _full_requirement(acceptance_criteria=["짧은", "짧은것2"])
        score, issues = calculator._calculate_completeness_score(raw)
        assert any("부실" in i for i in issues)

    def test_short_title_penalized(self, calculator):
        raw = _full_requirement(title="짧")
        score, issues = calculator._calculate_completeness_score(raw)
        assert any("제목" in i for i in issues)

    def test_short_description_penalized(self, calculator):
        raw = _full_requirement(description="짧은 설명")
        score, issues = calculator._calculate_completeness_score(raw)
        assert any("설명" in i for i in issues)


# ===================================================================
# _is_valid_user_story
# ===================================================================

class TestIsValidUserStory:
    def test_english_format(self, calculator):
        assert calculator._is_valid_user_story(
            "As a user, I want to log in, so that I can access my account"
        )

    def test_korean_format(self, calculator):
        assert calculator._is_valid_user_story(
            "사용자로서 로그인 기능을 원합니다"
        )

    def test_long_enough_passes(self, calculator):
        assert calculator._is_valid_user_story(
            "비밀번호 재설정 페이지에서 새 비밀번호를 입력해서 계정을 복구할 수 있어야 합니다"
        )

    def test_empty_fails(self, calculator):
        assert not calculator._is_valid_user_story("")

    def test_too_short_fails(self, calculator):
        assert not calculator._is_valid_user_story("짧은 스토리")


# ===================================================================
# calculate (통합 계산)
# ===================================================================

class TestCalculate:
    def test_returns_confidence_breakdown(self, calculator):
        raw = _full_requirement()
        result = calculator.calculate(raw, "document", 0.9)
        assert isinstance(result, ConfidenceBreakdown)

    def test_final_score_between_0_and_1(self, calculator):
        raw = _full_requirement()
        result = calculator.calculate(raw, "document", 0.9)
        assert 0.0 <= result.final_score <= 1.0

    def test_document_source_higher_than_chat(self, calculator):
        raw = _full_requirement()
        doc_result = calculator.calculate(raw, "document", 0.9)
        chat_result = calculator.calculate(raw, "chat", 0.9)
        assert doc_result.final_score > chat_result.final_score

    def test_high_ai_confidence_improves_score(self, calculator):
        raw = _full_requirement()
        high = calculator.calculate(raw, "text", 0.95)
        low = calculator.calculate(raw, "text", 0.3)
        assert high.final_score > low.final_score

    def test_ai_confidence_clamped(self, calculator):
        raw = _full_requirement()
        result = calculator.calculate(raw, "text", 1.5)
        assert result.ai_confidence == 1.0

        result2 = calculator.calculate(raw, "text", -0.5)
        assert result2.ai_confidence == 0.0

    def test_weighted_average_formula(self, calculator):
        """가중치 합산 검증: source*0.15 + clarity*0.30 + completeness*0.35 + ai*0.20"""
        raw = _full_requirement()
        result = calculator.calculate(raw, "text", 0.8)
        expected = (
            result.source_credibility * 0.15 +
            result.clarity_score * 0.30 +
            result.completeness_score * 0.35 +
            result.ai_confidence * 0.20
        )
        assert result.final_score == pytest.approx(expected, abs=0.001)

    def test_low_quality_requirement_low_score(self, calculator):
        raw = {"title": "짧"}
        result = calculator.calculate(raw, "chat", 0.3)
        assert result.final_score < 0.5

    def test_deduction_reasons_populated(self, calculator):
        raw = {"title": "짧"}
        result = calculator.calculate(raw, "chat", 0.3)
        assert len(result.deduction_reasons) > 0


# ===================================================================
# get_confidence_calculator (싱글톤)
# ===================================================================

class TestSingleton:
    def test_returns_same_instance(self):
        c1 = get_confidence_calculator()
        c2 = get_confidence_calculator()
        assert c1 is c2
