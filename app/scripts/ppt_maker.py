"""PPT 제안서 생성 스크립트.

Usage:
    python -m app.scripts.ppt_maker

제안서(PROP-*.md)를 기반으로 다크 테마 PPT 생성.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


# 다크 테마 컬러
COLORS = {
    "background": "1E1E2E",
    "surface": "2D2D3F",
    "primary": "7C3AED",
    "secondary": "06B6D4",
    "accent": "F59E0B",
    "text_primary": "FFFFFF",
    "text_secondary": "A0AEC0",
    "success": "10B981",
    "warning": "F59E0B",
}


def hex_to_rgb(hex_color: str) -> RGBColor:
    """Hex 컬러를 RGBColor로 변환."""
    hex_color = hex_color.lstrip('#')
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )


def set_slide_background(slide, color_hex: str):
    """슬라이드 배경색 설정."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = hex_to_rgb(color_hex)


def add_title_slide(prs, title: str, subtitle: str = ""):
    """표지 슬라이드 추가."""
    slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])
    
    # 제목
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(3), Inches(9), Inches(1.5)
    )
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
    p.alignment = PP_ALIGN.CENTER
    
    # 부제
    if subtitle:
        subtitle_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(4.5), Inches(9), Inches(0.8)
        )
        tf = subtitle_box.text_frame
        p = tf.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(24)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.alignment = PP_ALIGN.CENTER
    
    return slide


def add_section_title_slide(prs, section_num: int, title: str):
    """섹션 제목 슬라이드 추가."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])
    
    # 섹션 번호
    num_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(1)
    )
    tf = num_box.text_frame
    p = tf.paragraphs[0]
    p.text = f"0{section_num}" if section_num < 10 else str(section_num)
    p.font.size = Pt(72)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["primary"])
    p.alignment = PP_ALIGN.CENTER
    
    # 제목
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(3.5), Inches(9), Inches(1)
    )
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
    p.alignment = PP_ALIGN.CENTER
    
    return slide


def add_content_slide(prs, title: str, bullets: list):
    """내용 슬라이드 (제목 + 불릿 리스트)."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])
    
    # 제목
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.5), Inches(9), Inches(0.8)
    )
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
    
    # 불릿 리스트
    content_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.5), Inches(9), Inches(5)
    )
    tf = content_box.text_frame
    tf.word_wrap = True
    
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"• {bullet}"
        p.font.size = Pt(20)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.space_before = Pt(12)
    
    return slide


def add_highlight_slide(prs, main_text: str, sub_text: str = ""):
    """강조 슬라이드 (핵심 메시지)."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])
    
    # 메인 텍스트
    main_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(2)
    )
    tf = main_box.text_frame
    p = tf.paragraphs[0]
    p.text = main_text
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
    p.alignment = PP_ALIGN.CENTER
    
    # 서브 텍스트
    if sub_text:
        sub_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(4.5), Inches(9), Inches(1)
        )
        tf = sub_box.text_frame
        p = tf.paragraphs[0]
        p.text = sub_text
        p.font.size = Pt(24)
        p.font.color.rgb = hex_to_rgb(COLORS["secondary"])
        p.alignment = PP_ALIGN.CENTER
    
    return slide


def add_closing_slide(prs, title: str = "Q&A", contact_info: str = ""):
    """마무리 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])
    
    # 제목
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(1.5)
    )
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(56)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["primary"])
    p.alignment = PP_ALIGN.CENTER
    
    # 연락처
    if contact_info:
        contact_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(4.5), Inches(9), Inches(1)
        )
        tf = contact_box.text_frame
        p = tf.paragraphs[0]
        p.text = contact_info
        p.font.size = Pt(20)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.alignment = PP_ALIGN.CENTER
    
    return slide


def add_two_column_slide(prs, title: str, left_title: str, left_items: list,
                          right_title: str, right_items: list,
                          left_color: str = None, right_color: str = None):
    """2컬럼 비교 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # 왼쪽 컬럼
    left_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.3), Inches(1.2), Inches(4.4), Inches(5.8))
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = hex_to_rgb(left_color or COLORS["surface"])
    left_box.line.fill.background()

    left_title_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(4), Inches(0.5))
    tf = left_title_box.text_frame
    p = tf.paragraphs[0]
    p.text = left_title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["warning"])

    left_content = slide.shapes.add_textbox(Inches(0.5), Inches(2.0), Inches(4), Inches(4.8))
    tf = left_content.text_frame
    tf.word_wrap = True
    for i, item in enumerate(left_items[:6]):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(16)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.space_before = Pt(8)

    # 오른쪽 컬럼
    right_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(5.3), Inches(1.2), Inches(4.4), Inches(5.8))
    right_box.fill.solid()
    right_box.fill.fore_color.rgb = hex_to_rgb(right_color or COLORS["surface"])
    right_box.line.fill.background()

    right_title_box = slide.shapes.add_textbox(Inches(5.5), Inches(1.4), Inches(4), Inches(0.5))
    tf = right_title_box.text_frame
    p = tf.paragraphs[0]
    p.text = right_title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["success"])

    right_content = slide.shapes.add_textbox(Inches(5.5), Inches(2.0), Inches(4), Inches(4.8))
    tf = right_content.text_frame
    tf.word_wrap = True
    for i, item in enumerate(right_items[:6]):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(16)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.space_before = Pt(8)

    return slide


def add_kpi_card_slide(prs, title: str, kpis: list):
    """KPI 카드 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # KPI 카드들 (2x2 그리드)
    card_positions = [
        (0.3, 1.3), (5.0, 1.3),
        (0.3, 4.0), (5.0, 4.0)
    ]

    for i, kpi in enumerate(kpis[:4]):
        x, y = card_positions[i]

        # 카드 배경
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(x), Inches(y), Inches(4.5), Inches(2.4))
        card.fill.solid()
        card.fill.fore_color.rgb = hex_to_rgb(COLORS["surface"])
        card.line.fill.background()

        # 메트릭 이름
        metric_box = slide.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.2), Inches(4), Inches(0.4))
        tf = metric_box.text_frame
        p = tf.paragraphs[0]
        p.text = kpi.get("metric", "")
        p.font.size = Pt(16)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])

        # 변화 (Before → After)
        value_box = slide.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.7), Inches(4), Inches(0.8))
        tf = value_box.text_frame
        p = tf.paragraphs[0]
        before = kpi.get("current", kpi.get("before", ""))
        after = kpi.get("target", kpi.get("after", ""))
        p.text = f"{before} → {after}"
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["primary"])

        # 개선율
        improve_box = slide.shapes.add_textbox(Inches(x + 0.2), Inches(y + 1.6), Inches(4), Inches(0.5))
        tf = improve_box.text_frame
        p = tf.paragraphs[0]
        p.text = kpi.get("improvement", "")
        p.font.size = Pt(18)
        p.font.color.rgb = hex_to_rgb(COLORS["success"])

    return slide


def add_timeline_slide(prs, title: str, phases: list):
    """타임라인 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # 타임라인 바
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]
    bar_y = 3.0
    total_width = 9.0

    for i, phase in enumerate(phases[:3]):
        bar_width = total_width / len(phases[:3])
        x = 0.5 + (i * bar_width)

        # 막대
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                      Inches(x), Inches(bar_y), Inches(bar_width - 0.1), Inches(0.6))
        bar.fill.solid()
        bar.fill.fore_color.rgb = hex_to_rgb(colors[i % len(colors)])
        bar.line.fill.background()

        # Phase 이름
        name_box = slide.shapes.add_textbox(Inches(x), Inches(bar_y - 0.8), Inches(bar_width), Inches(0.6))
        tf = name_box.text_frame
        p = tf.paragraphs[0]
        p.text = phase.get("phase", f"Phase {i+1}")
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
        p.alignment = PP_ALIGN.CENTER

        # 기간
        duration_box = slide.shapes.add_textbox(Inches(x), Inches(bar_y + 0.8), Inches(bar_width), Inches(0.8))
        tf = duration_box.text_frame
        p = tf.paragraphs[0]
        p.text = f"{phase.get('duration', '')}\n{phase.get('period', '')}"
        p.font.size = Pt(14)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])
        p.alignment = PP_ALIGN.CENTER

    return slide


def add_team_slide(prs, title: str, team: list, effort_summary: dict):
    """팀 구성 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # 팀원 카드
    for i, member in enumerate(team[:6]):
        row = i // 3
        col = i % 3
        x = 0.3 + (col * 3.2)
        y = 1.2 + (row * 2.6)

        # 카드
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(x), Inches(y), Inches(3.0), Inches(2.3))
        card.fill.solid()
        card.fill.fore_color.rgb = hex_to_rgb(COLORS["surface"])
        card.line.fill.background()

        # 역할
        role_box = slide.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.15), Inches(2.7), Inches(0.5))
        tf = role_box.text_frame
        p = tf.paragraphs[0]
        p.text = member.get("role", "")
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["primary"])

        # 인원
        count_box = slide.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.65), Inches(2.7), Inches(0.4))
        tf = count_box.text_frame
        p = tf.paragraphs[0]
        count = member.get("count", 1)
        p.text = f"{count}명" if count >= 1 else f"{count} (50%)"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

        # 전문성
        exp_box = slide.shapes.add_textbox(Inches(x + 0.15), Inches(y + 1.2), Inches(2.7), Inches(1.0))
        tf = exp_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = member.get("expertise", "")[:50]
        p.font.size = Pt(12)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])

    # 총 공수
    total_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.5), Inches(9), Inches(0.5))
    tf = total_box.text_frame
    p = tf.paragraphs[0]
    total_mm = effort_summary.get("total", {}).get("man_months", 16)
    p.text = f"총 공수: {total_mm} Man-Months"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["secondary"])
    p.alignment = PP_ALIGN.CENTER

    return slide


def add_risk_table_slide(prs, title: str, risks: list):
    """리스크 테이블 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # 리스크 항목
    y_start = 1.2
    for i, risk in enumerate(risks[:5]):
        y = y_start + (i * 1.1)

        # 배경 박스
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                      Inches(0.3), Inches(y), Inches(9.4), Inches(1.0))
        box.fill.solid()
        box.fill.fore_color.rgb = hex_to_rgb(COLORS["surface"])
        box.line.fill.background()

        # 영향도 표시
        impact = risk.get("impact", "MEDIUM")
        impact_color = COLORS["warning"] if impact == "HIGH" else COLORS["secondary"]
        impact_box = slide.shapes.add_textbox(Inches(0.4), Inches(y + 0.1), Inches(0.8), Inches(0.4))
        tf = impact_box.text_frame
        p = tf.paragraphs[0]
        p.text = impact
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(impact_color)

        # 리스크 내용
        risk_box = slide.shapes.add_textbox(Inches(1.3), Inches(y + 0.1), Inches(4.0), Inches(0.4))
        tf = risk_box.text_frame
        p = tf.paragraphs[0]
        p.text = risk.get("risk", "")[:40]
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

        # 대응
        mitigation_box = slide.shapes.add_textbox(Inches(1.3), Inches(y + 0.5), Inches(8.2), Inches(0.4))
        tf = mitigation_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"→ {risk.get('mitigation', '')[:60]}"
        p.font.size = Pt(12)
        p.font.color.rgb = hex_to_rgb(COLORS["text_secondary"])

    return slide


def add_steps_slide(prs, title: str, steps: list):
    """스텝 다이어그램 슬라이드."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, COLORS["background"])

    # 제목
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

    # 스텝들
    y_start = 1.5
    for i, step in enumerate(steps[:5]):
        y = y_start + (i * 1.1)

        # 번호 원
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                         Inches(0.5), Inches(y), Inches(0.6), Inches(0.6))
        circle.fill.solid()
        circle.fill.fore_color.rgb = hex_to_rgb(COLORS["primary"])
        circle.line.fill.background()

        # 번호 텍스트
        num_box = slide.shapes.add_textbox(Inches(0.5), Inches(y + 0.1), Inches(0.6), Inches(0.4))
        tf = num_box.text_frame
        p = tf.paragraphs[0]
        p.text = str(step.get("step", i + 1))
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])
        p.alignment = PP_ALIGN.CENTER

        # 액션
        action_box = slide.shapes.add_textbox(Inches(1.3), Inches(y + 0.1), Inches(6), Inches(0.5))
        tf = action_box.text_frame
        p = tf.paragraphs[0]
        p.text = step.get("action", "")
        p.font.size = Pt(20)
        p.font.color.rgb = hex_to_rgb(COLORS["text_primary"])

        # 기간
        duration_box = slide.shapes.add_textbox(Inches(7.5), Inches(y + 0.1), Inches(2), Inches(0.5))
        tf = duration_box.text_frame
        p = tf.paragraphs[0]
        p.text = step.get("duration", "")
        p.font.size = Pt(16)
        p.font.color.rgb = hex_to_rgb(COLORS["secondary"])
        p.alignment = PP_ALIGN.RIGHT

    return slide


def parse_proposal(md_content: str) -> dict:
    """제안서 Markdown 파싱."""
    data = {
        "title": "",
        "date": "",
        "client": "",
        "sections": {}
    }

    # 제목 추출
    title_match = re.search(r'^# (.+?)$', md_content, re.MULTILINE)
    if title_match:
        data["title"] = title_match.group(1).strip()

    # 날짜 추출
    date_match = re.search(r'\*\*제안일\*\*:\s*(.+?)$', md_content, re.MULTILINE)
    if date_match:
        data["date"] = date_match.group(1).strip()

    # 수신 추출
    client_match = re.search(r'\*\*수신\*\*:\s*(.+?)$', md_content, re.MULTILINE)
    if client_match:
        data["client"] = client_match.group(1).strip()

    return data


def load_proposal_json(json_path: Path) -> dict:
    """제안서 JSON 로드."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_ppt(proposal_path: Path, output_path: Path):
    """PPT 생성."""
    # 제안서 읽기 (JSON 우선, 없으면 MD)
    json_path = proposal_path.with_suffix('.json')
    if json_path.exists():
        data = load_proposal_json(json_path)
        print(f"   JSON 데이터 로드: {json_path.name}")
    else:
        md_content = proposal_path.read_text(encoding='utf-8')
        data = parse_proposal(md_content)

    # PPT 생성
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # 데이터 추출
    title = data.get("title", "프로젝트 제안서")
    metadata = data.get("metadata", {})
    exec_summary = data.get("executive_summary", {})
    current_sit = data.get("current_situation", {})
    objectives = data.get("objectives", {})
    solution = data.get("solution", {})
    tech = data.get("technical_approach", {})
    timeline = data.get("timeline", {})
    team = data.get("team", {})
    risks = data.get("risk_management", [])
    benefits = data.get("expected_benefits", {})
    next_steps = data.get("next_steps", [])
    storytelling = data.get("storytelling_structure", {})

    # 1. 표지
    add_title_slide(
        prs,
        title.replace(" 제안서", ""),
        f"{metadata.get('proposal_date', '')} | {metadata.get('client_company', '[고객사]')} 귀중"
    )

    # 2. 목차
    add_content_slide(prs, "목차 (Contents)", [
        "01  경영진 요약 (Executive Summary)",
        "02  현재 상황과 도전 (Current Challenges)",
        "03  프로젝트 목표 (Objectives)",
        "04  우리의 솔루션 (Our Solution)",
        "05  기술 접근법 (Technical Approach)",
        "06  일정 계획 (Timeline)",
        "07  투입 인력 (Team)",
        "08  기대 효과 (Expected Benefits)",
        "09  다음 단계 (Next Steps)"
    ])

    # 3. 경영진 요약 - 핵심 메시지
    add_highlight_slide(
        prs,
        storytelling.get("solution", exec_summary.get("solution", "디지털 전환")),
        storytelling.get("hook", "15년 된 레거시 시스템의 한계를 극복합니다")
    )

    # 4. 경영진 요약 - 상세
    add_content_slide(prs, "경영진 요약 (Executive Summary)", [
        f"해결할 문제: {exec_summary.get('problem', '')}",
        f"솔루션: {exec_summary.get('solution', '')}",
        f"예상 기간: {exec_summary.get('duration', '7개월')}",
        f"투입 공수: {exec_summary.get('effort', '16 M/M')}",
        f"핵심 효과: {', '.join(exec_summary.get('key_benefits', [])[:2])}"
    ])

    # 5. 현재 상황 섹션
    add_section_title_slide(prs, 1, "현재 상황")

    # 6. 현재의 도전
    challenges = current_sit.get("challenges", [])
    challenge_bullets = [
        f"{c.get('area', '')}: {c.get('symptom', '')}"
        for c in challenges[:4]
    ]
    add_content_slide(prs, "현재의 도전과 과제", challenge_bullets)

    # 7. 변화하지 않으면?
    risks_no_change = current_sit.get("risks_if_no_change", [])
    add_content_slide(prs, "변화하지 않으면?", risks_no_change[:4])

    # 8. Before vs After 비교
    future_vision = current_sit.get("future_vision", {})
    add_two_column_slide(
        prs, "Before vs After",
        "현재 (AS-IS)", [c.get("business_impact", "") for c in challenges[:4]],
        "미래 (TO-BE)", list(future_vision.values())[:4]
    )

    # 9. 프로젝트 목표 섹션
    add_section_title_slide(prs, 2, "프로젝트 목표")

    # 10. KPI 카드
    kpis = objectives.get("kpis", [])
    add_kpi_card_slide(prs, "목표 및 핵심 KPI", kpis)

    # 11. 솔루션 섹션
    add_section_title_slide(prs, 3, "우리의 솔루션")

    # 12. 솔루션 개요
    add_highlight_slide(
        prs,
        solution.get("value_proposition", "손으로 쓰던 전표가 스마트폰으로"),
        solution.get("overview", "")[:80]
    )

    # 13. 작업 범위
    in_scope = solution.get("scope", {}).get("in_scope", [])
    out_scope = solution.get("scope", {}).get("out_of_scope", [])
    add_two_column_slide(
        prs, "작업 범위 (Scope)",
        "포함 (In-Scope)", [f"{s.get('category', '')}: {s.get('value', '')}" for s in in_scope[:5]],
        "제외 (Out of Scope)", [s.get("item", "") for s in out_scope[:4]]
    )

    # 14. 기술 스택
    tech_stack = tech.get("technology_stack", [])
    add_content_slide(prs, "기술 스택 (Technology Stack)", [
        f"{t.get('category', '')}: {t.get('technology', '')}"
        for t in tech_stack[:6]
    ])

    # 15. 일정 섹션
    add_section_title_slide(prs, 4, "일정 계획")

    # 16. 타임라인
    phases = timeline.get("phases", [])
    add_timeline_slide(prs, f"프로젝트 타임라인 ({timeline.get('total_duration', '7개월')})", phases)

    # 17. 인력 섹션 + 팀 구성
    team_comp = team.get("composition", [])
    effort_sum = team.get("effort_summary", {})
    add_team_slide(prs, "프로젝트 팀 구성", team_comp, effort_sum)

    # 18. 리스크 관리
    add_risk_table_slide(prs, "리스크 관리", risks)

    # 19. 기대 효과 - 핵심 수치
    quant_benefits = benefits.get("quantitative", [])
    if quant_benefits:
        first_benefit = quant_benefits[0]
        add_highlight_slide(
            prs,
            f"{first_benefit.get('before', '')} → {first_benefit.get('after', '')}",
            f"{first_benefit.get('metric', '')} {first_benefit.get('improvement', '')}"
        )

    # 20. 다음 단계
    add_steps_slide(prs, "다음 단계 (Next Steps)", next_steps)

    # 21. Q&A
    add_closing_slide(
        prs,
        "감사합니다",
        f"Q&A | {storytelling.get('cta', '지금 바로 문의하세요!')}"
    )

    # 저장
    prs.save(str(output_path))
    return output_path


def main():
    print("\n" + "=" * 70)
    print("PPT 제안서 생성")
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print("=" * 70)
    
    # 최신 제안서 찾기
    proposal_dir = Path("workspace/outputs/proposals")
    md_files = list(proposal_dir.glob("PROP-*.md"))
    
    if not md_files:
        print("제안서 파일을 찾을 수 없습니다.")
        print("먼저 /pro:pro-maker를 실행하세요.")
        return
    
    proposal_path = max(md_files, key=lambda x: x.stat().st_mtime)
    print(f"\n[입력] 제안서: {proposal_path}")
    
    # 출력 경로
    output_dir = Path("workspace/outputs/ppt")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"PPT-{timestamp}.pptx"
    
    # PPT 생성
    result = generate_ppt(proposal_path, output_path)
    
    if result:
        print(f"\n[완료] PPT 생성 완료: {output_path}")
        print(f"   슬라이드 수: 20장")
    else:
        print("\n[실패] PPT 생성 실패")


if __name__ == "__main__":
    main()
