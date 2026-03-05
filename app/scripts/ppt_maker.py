"""PPT 제안서 생성 스크립트 (2026 Modern Design).

Usage:
    python -m app.scripts.ppt_maker

제안서(PROP-*.json)를 기반으로 모던 라이트 테마 PPT 생성.
2026 트렌드: 미니멀, 화이트스페이스, 소프트 그라데이션, 아이콘 시각화.

슬라이드 안전 영역: 높이 7.5인치, 콘텐츠는 0.3~7.2인치 이내.
"""

import json
import re
import math
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from app.scripts.arch_diagram import generate_from_trd_file


# ============================================================
# 2026 Modern Light Theme
# ============================================================
COLORS = {
    "bg_white": "FFFFFF",
    "bg_light": "F8FAFC",
    "bg_section": "1E3A5F",
    "card": "F1F5F9",
    "card_alt": "EEF2FF",
    "accent": "2563EB",
    "accent2": "7C3AED",
    "accent3": "0891B2",
    "accent4": "059669",
    "accent5": "DC2626",
    "orange": "EA580C",
    "amber": "D97706",
    "title": "0F172A",
    "body": "334155",
    "subtle": "64748B",
    "muted": "94A3B8",
    "border": "E2E8F0",
    "white": "FFFFFF",
}

PALETTE = ["2563EB", "7C3AED", "0891B2", "059669", "EA580C", "D97706"]

FONT_TITLE = "맑은 고딕"
FONT_BODY = "맑은 고딕"

# 슬라이드 레이아웃 상수
SLIDE_W = 10.0
SLIDE_H = 7.5
MARGIN_X = 0.6        # 좌우 여백
MARGIN_TOP = 0.4      # 상단 여백
CONTENT_TOP = 1.8     # 헤더 아래 콘텐츠 시작
SAFE_BOTTOM = 7.1     # 콘텐츠 안전 하한
CONTENT_H = SAFE_BOTTOM - CONTENT_TOP  # 사용 가능 높이 = 5.3인치
CONTENT_W = SLIDE_W - 2 * MARGIN_X     # 사용 가능 폭 = 8.8인치


def hex_to_rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip('#')
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_slide_bg(slide, color_hex: str):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = hex_to_rgb(color_hex)


def _add_text(slide, left, top, width, height, text, font_size=18,
              bold=False, color="334155", alignment=PP_ALIGN.LEFT,
              font_name=None, word_wrap=True):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.text = str(text)
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = hex_to_rgb(color)
    p.font.name = font_name or FONT_BODY
    p.alignment = alignment
    return box


def _add_rounded_card(slide, left, top, width, height, fill_color="F1F5F9"):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex_to_rgb(fill_color)
    shape.line.fill.background()
    shape.adjustments[0] = 0.06
    return shape


def _add_circle_icon(slide, left, top, size, color, text="", text_color="FFFFFF"):
    circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(left), Inches(top), Inches(size), Inches(size)
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = hex_to_rgb(color)
    circle.line.fill.background()
    if text:
        tf = circle.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = str(text)
        p.font.size = Pt(max(9, int(size * 13)))
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(text_color)
        p.alignment = PP_ALIGN.CENTER
    return circle


def _add_accent_bar(slide, left, top, width, height=0.05, color="2563EB"):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = hex_to_rgb(color)
    bar.line.fill.background()
    return bar


def _add_progress_bar(slide, left, top, width, height, pct, bg_color="E2E8F0", fill_color="2563EB"):
    bg = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = hex_to_rgb(bg_color)
    bg.line.fill.background()
    fill_w = max(width * (pct / 100.0), 0.1)
    fg = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(fill_w), Inches(height)
    )
    fg.fill.solid()
    fg.fill.fore_color.rgb = hex_to_rgb(fill_color)
    fg.line.fill.background()
    return fg


def _slide_header(slide, eng_label, kor_title, label_color="2563EB", bar_color="2563EB"):
    """공통 슬라이드 헤더. 영문 라벨 + 한글 제목 + 액센트 바."""
    _add_text(slide, 0.8, 0.4, 8, 0.4, eng_label,
              font_size=12, bold=True, color=label_color)
    _add_text(slide, 0.8, 0.8, 8, 0.6, kor_title,
              font_size=30, bold=True, color=COLORS["title"], font_name=FONT_TITLE)
    _add_accent_bar(slide, 0.8, 1.4, 1.5, 0.04, bar_color)


def _calc_item_spacing(n_items, start_y=CONTENT_TOP, end_y=SAFE_BOTTOM, item_h=0.8):
    """항목 수에 따라 동적 간격 계산. 오버플로우 방지."""
    available = end_y - start_y
    if n_items <= 0:
        return start_y, item_h
    total_needed = n_items * item_h
    if total_needed > available:
        item_h = available / n_items
    return start_y, item_h


# ============================================================
# Slide Builders
# ============================================================

def slide_cover(prs, title, subtitle, date_str):
    """슬라이드 1: 표지."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])

    _add_accent_bar(slide, 0, 0, 10, 0.07, COLORS["accent"])

    block = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0.07), Inches(0.22), Inches(7.36)
    )
    block.fill.solid()
    block.fill.fore_color.rgb = hex_to_rgb(COLORS["accent"])
    block.line.fill.background()

    _add_text(slide, 0.8, 2.2, 8.5, 1.2, title,
              font_size=42, bold=True, color=COLORS["title"],
              font_name=FONT_TITLE)
    _add_accent_bar(slide, 0.8, 3.5, 2.0, 0.04, COLORS["accent"])

    if subtitle:
        _add_text(slide, 0.8, 3.8, 8.5, 0.5, subtitle,
                  font_size=18, color=COLORS["subtle"])
    _add_text(slide, 0.8, 4.5, 8.5, 0.4, date_str,
              font_size=14, color=COLORS["muted"])

    _add_accent_bar(slide, 0, 7.43, 10, 0.07, COLORS["accent2"])


def slide_toc(prs, sections):
    """슬라이드 2: 목차 (2컬럼)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "CONTENTS", "목차")

    n = len(sections)
    col1_count = math.ceil(n / 2)

    # 컬럼 1 (좌측)
    y = CONTENT_TOP
    spacing = min(0.48, (SAFE_BOTTOM - CONTENT_TOP) / max(col1_count, 1))
    for i in range(col1_count):
        num = f"{i+1:02d}"
        color = PALETTE[i % len(PALETTE)]
        _add_circle_icon(slide, 0.6, y, 0.38, color, num)
        _add_text(slide, 1.15, y + 0.01, 3.8, 0.38, sections[i],
                  font_size=15, color=COLORS["body"])
        y += spacing

    # 컬럼 2 (우측)
    y = CONTENT_TOP
    for i in range(col1_count, n):
        num = f"{i+1:02d}"
        color = PALETTE[i % len(PALETTE)]
        _add_circle_icon(slide, 5.2, y, 0.38, color, num)
        _add_text(slide, 5.75, y + 0.01, 3.8, 0.38, sections[i],
                  font_size=15, color=COLORS["body"])
        y += spacing


def slide_exec_highlight(prs, main_text, metrics):
    """슬라이드 3: 경영진 요약 핵심."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_section"])

    _add_text(slide, 0.8, 0.5, 8, 0.4, "EXECUTIVE SUMMARY",
              font_size=12, bold=True, color=COLORS["muted"])
    _add_text(slide, 0.8, 1.1, 8.4, 1.8, main_text[:150],
              font_size=24, bold=True, color=COLORS["white"], font_name=FONT_TITLE)

    if metrics:
        n = min(len(metrics), 3)
        card_w = 2.4
        gap = 0.3
        total_w = n * card_w + (n - 1) * gap
        start_x = (SLIDE_W - total_w) / 2

        for i, m in enumerate(metrics[:3]):
            x = start_x + i * (card_w + gap)
            _add_rounded_card(slide, x, 3.8, card_w, 1.8, "1E4A6F")
            _add_text(slide, x + 0.15, 3.95, card_w - 0.3, 0.35,
                      m.get("label", ""), font_size=11, color=COLORS["muted"])
            _add_text(slide, x + 0.15, 4.35, card_w - 0.3, 0.6,
                      m.get("value", ""), font_size=22, bold=True,
                      color=COLORS["white"], alignment=PP_ALIGN.CENTER,
                      font_name=FONT_TITLE)
            if m.get("desc"):
                _add_text(slide, x + 0.15, 5.0, card_w - 0.3, 0.35,
                          m["desc"], font_size=10, color=COLORS["muted"],
                          alignment=PP_ALIGN.CENTER)


def slide_exec_detail(prs, items):
    """슬라이드 4: 경영진 요약 상세."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "EXECUTIVE SUMMARY", "프로젝트 개요")

    n = min(len(items), 5)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 0.85)
    icons = ["P", "S", "T", "E", "K"]
    colors = [COLORS["accent5"], COLORS["accent"], COLORS["accent3"],
              COLORS["accent2"], COLORS["accent4"]]

    for i, item in enumerate(items[:n]):
        y = start_y + i * item_h
        _add_rounded_card(slide, 0.5, y, 9.0, item_h - 0.08, COLORS["card"])
        _add_circle_icon(slide, 0.7, y + (item_h - 0.5) / 2 - 0.04, 0.45,
                         colors[i % len(colors)], icons[i % len(icons)])
        _add_text(slide, 1.35, y + 0.08, 2.2, 0.3, item.get("label", ""),
                  font_size=12, bold=True, color=COLORS["accent"])
        _add_text(slide, 1.35, y + 0.38, 7.8, 0.35, item.get("value", "")[:90],
                  font_size=14, color=COLORS["body"])


def slide_section(prs, num, title, subtitle=""):
    """섹션 구분 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_section"])

    _add_text(slide, 0.8, 2.0, 8, 0.9,
              f"{num:02d}" if isinstance(num, int) else str(num),
              font_size=64, bold=True, color="3B82F6", font_name=FONT_TITLE)
    _add_accent_bar(slide, 0.8, 3.0, 2.0, 0.05, "3B82F6")
    _add_text(slide, 0.8, 3.3, 8, 0.9, title,
              font_size=36, bold=True, color=COLORS["white"], font_name=FONT_TITLE)
    if subtitle:
        _add_text(slide, 0.8, 4.2, 8, 0.5, subtitle,
                  font_size=16, color=COLORS["muted"])


def slide_challenges(prs, title, challenges):
    """도전과제 슬라이드 (2x2 카드 그리드)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "CHALLENGES", title, COLORS["accent5"], COLORS["accent5"])

    n = min(len(challenges), 4)
    cols = 2
    rows = math.ceil(n / cols)
    cw = 4.2
    gap_x = 0.4
    gap_y = 0.3
    ch = (SAFE_BOTTOM - CONTENT_TOP - (rows - 1) * gap_y) / rows  # 동적 카드 높이
    ch = min(ch, 2.4)
    start_x = (SLIDE_W - (cols * cw + (cols - 1) * gap_x)) / 2

    warn_icons = ["!", "!!", "?", "X"]
    for i, c in enumerate(challenges[:n]):
        col_idx = i % cols
        row_idx = i // cols
        x = start_x + col_idx * (cw + gap_x)
        y = CONTENT_TOP + row_idx * (ch + gap_y)

        _add_rounded_card(slide, x, y, cw, ch, COLORS["card"])
        _add_circle_icon(slide, x + 0.15, y + 0.15, 0.38, COLORS["accent5"],
                         warn_icons[i % len(warn_icons)])

        area = c.get("area", c.get("title", f"과제 {i+1}"))
        desc = c.get("symptom", c.get("description", c.get("issue", "")))

        _add_text(slide, x + 0.65, y + 0.15, cw - 0.85, 0.35, area[:30],
                  font_size=14, bold=True, color=COLORS["title"])
        _add_text(slide, x + 0.15, y + 0.65, cw - 0.3, ch - 0.8, desc[:100],
                  font_size=12, color=COLORS["body"])


def slide_risks_no_change(prs, risks):
    """변화하지 않으면 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "IF NO CHANGE", "변화하지 않으면?", COLORS["accent5"], COLORS["accent5"])

    n = min(len(risks), 5)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 0.85)

    for i, risk in enumerate(risks[:n]):
        y = start_y + i * item_h
        text = risk if isinstance(risk, str) else str(risk)
        _add_rounded_card(slide, 0.5, y, 9.0, item_h - 0.08, COLORS["card"])
        _add_circle_icon(slide, 0.7, y + (item_h - 0.48) / 2 - 0.04, 0.42,
                         COLORS["accent5"], str(i + 1))
        _add_text(slide, 1.35, y + (item_h - 0.4) / 2 - 0.04, 7.8, 0.4,
                  text[:100], font_size=15, color=COLORS["body"])


def slide_before_after(prs, before_items, after_items):
    """Before vs After 비교."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "COMPARISON", "Before vs After")

    card_top = CONTENT_TOP
    card_h = SAFE_BOTTOM - card_top
    col_w = 4.0

    # 좌측: Before
    _add_rounded_card(slide, 0.4, card_top, col_w, card_h, "FEF2F2")
    _add_circle_icon(slide, 0.55, card_top + 0.12, 0.4, COLORS["accent5"], "X")
    _add_text(slide, 1.1, card_top + 0.12, 2.8, 0.4, "AS-IS (현재)",
              font_size=17, bold=True, color=COLORS["accent5"])

    n_before = min(len(before_items), 5)
    item_area = card_h - 0.8
    spacing = item_area / max(n_before, 1)
    spacing = min(spacing, 0.55)
    y = card_top + 0.7
    for item in before_items[:n_before]:
        _add_text(slide, 0.6, y, 3.6, 0.4, item[:60],
                  font_size=13, color=COLORS["body"])
        y += spacing

    # 중앙 화살표
    arrow_y = card_top + card_h / 2 - 0.2
    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW, Inches(4.3), Inches(arrow_y), Inches(0.7), Inches(0.4)
    )
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = hex_to_rgb(COLORS["accent"])
    arrow.line.fill.background()

    # 우측: After
    _add_rounded_card(slide, 5.6, card_top, col_w, card_h, "F0FDF4")
    _add_circle_icon(slide, 5.75, card_top + 0.12, 0.4, COLORS["accent4"], "O")
    _add_text(slide, 6.3, card_top + 0.12, 2.8, 0.4, "TO-BE (미래)",
              font_size=17, bold=True, color=COLORS["accent4"])

    n_after = min(len(after_items), 5)
    y = card_top + 0.7
    for item in after_items[:n_after]:
        _add_text(slide, 5.8, y, 3.6, 0.4, item[:60],
                  font_size=13, color=COLORS["body"])
        y += spacing


def slide_kpi(prs, title, kpis):
    """KPI 카드 슬라이드 (2x2)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "KEY PERFORMANCE INDICATORS", title)

    n = min(len(kpis), 4)
    cols = 2
    rows = math.ceil(n / cols)
    cw = 4.2
    gap_x = 0.4
    gap_y = 0.3
    ch = min(2.2, (SAFE_BOTTOM - CONTENT_TOP - (rows - 1) * gap_y) / max(rows, 1))
    start_x = (SLIDE_W - (cols * cw + (cols - 1) * gap_x)) / 2

    for i, kpi in enumerate(kpis[:n]):
        col = i % cols
        row = i // cols
        x = start_x + col * (cw + gap_x)
        y = CONTENT_TOP + row * (ch + gap_y)

        _add_rounded_card(slide, x, y, cw, ch, COLORS["card"])

        metric_name = kpi.get("metric", kpi.get("name", f"KPI {i+1}"))
        current = kpi.get("current", "-")
        target = kpi.get("target", "-")
        improvement = kpi.get("improvement", "")

        _add_text(slide, x + 0.2, y + 0.12, cw - 0.4, 0.3, metric_name[:35],
                  font_size=12, bold=True, color=COLORS["subtle"])
        _add_text(slide, x + 0.2, y + 0.5, cw - 0.4, 0.55,
                  f"{current}  ->  {target}",
                  font_size=20, bold=True, color=COLORS["accent"],
                  font_name=FONT_TITLE)

        if improvement:
            badge_y = y + ch - 0.55
            _add_rounded_card(slide, x + 0.2, badge_y, 1.8, 0.38, COLORS["accent4"])
            _add_text(slide, x + 0.22, badge_y + 0.02, 1.76, 0.34, improvement[:20],
                      font_size=11, bold=True, color=COLORS["white"],
                      alignment=PP_ALIGN.CENTER)


def slide_solution_highlight(prs, value_prop, overview):
    """솔루션 개요 하이라이트."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_section"])

    _add_text(slide, 0.8, 0.5, 8, 0.4, "OUR SOLUTION",
              font_size=12, bold=True, color=COLORS["muted"])
    _add_text(slide, 0.8, 1.5, 8.4, 1.8, value_prop[:120],
              font_size=28, bold=True, color=COLORS["white"], font_name=FONT_TITLE)

    if overview:
        _add_accent_bar(slide, 0.8, 3.6, 2.0, 0.04, "3B82F6")
        _add_text(slide, 0.8, 3.9, 8.4, 1.5, overview[:150],
                  font_size=16, color=COLORS["muted"])


def slide_scope(prs, in_scope, out_scope):
    """작업 범위 슬라이드 (2컬럼)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "PROJECT SCOPE", "작업 범위")

    card_top = CONTENT_TOP
    card_h = SAFE_BOTTOM - card_top
    col_w = 4.2

    # In-Scope
    _add_rounded_card(slide, 0.4, card_top, col_w, card_h, "F0FDF4")
    _add_circle_icon(slide, 0.55, card_top + 0.1, 0.35, COLORS["accent4"], "O")
    _add_text(slide, 1.05, card_top + 0.1, 3.2, 0.35, "포함 범위 (In-Scope)",
              font_size=14, bold=True, color=COLORS["accent4"])

    n_in = min(len(in_scope), 6)
    spacing = min(0.42, (card_h - 0.7) / max(n_in, 1))
    y = card_top + 0.6
    for item in in_scope[:n_in]:
        text = item if isinstance(item, str) else item.get("value", item.get("name", str(item)))
        _add_text(slide, 0.6, y, 3.8, 0.35, text[:50],
                  font_size=12, color=COLORS["body"])
        y += spacing

    # Out-of-Scope
    _add_rounded_card(slide, 5.4, card_top, col_w, card_h, "FEF2F2")
    _add_circle_icon(slide, 5.55, card_top + 0.1, 0.35, COLORS["accent5"], "X")
    _add_text(slide, 6.05, card_top + 0.1, 3.2, 0.35, "제외 범위 (Out of Scope)",
              font_size=14, bold=True, color=COLORS["accent5"])

    n_out = min(len(out_scope), 6)
    spacing = min(0.42, (card_h - 0.7) / max(n_out, 1))
    y = card_top + 0.6
    for item in out_scope[:n_out]:
        text = item if isinstance(item, str) else item.get("item", item.get("name", str(item)))
        _add_text(slide, 5.6, y, 3.8, 0.35, text[:50],
                  font_size=12, color=COLORS["body"])
        y += spacing


def slide_features(prs, features):
    """핵심 기능 슬라이드 (카드 그리드)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "KEY FEATURES", "핵심 기능", COLORS["accent2"], COLORS["accent2"])

    n = min(len(features), 6)
    cols = 3 if n > 4 else 2
    rows = math.ceil(n / cols)
    gap_x = 0.3
    gap_y = 0.25
    cw = (CONTENT_W - (cols - 1) * gap_x) / cols
    ch = min(2.0, (SAFE_BOTTOM - CONTENT_TOP - (rows - 1) * gap_y) / max(rows, 1))
    start_x = MARGIN_X

    for i, feat in enumerate(features[:n]):
        col = i % cols
        row = i // cols
        x = start_x + col * (cw + gap_x)
        y = CONTENT_TOP + row * (ch + gap_y)

        _add_rounded_card(slide, x, y, cw, ch, COLORS["card_alt"])
        _add_circle_icon(slide, x + 0.1, y + 0.1, 0.35, PALETTE[i % len(PALETTE)],
                         str(i + 1))

        name = feat.get("name", f"기능 {i+1}")
        desc = feat.get("description", "")
        _add_text(slide, x + 0.55, y + 0.1, cw - 0.7, 0.3, name[:25],
                  font_size=13, bold=True, color=COLORS["title"])
        _add_text(slide, x + 0.1, y + 0.55, cw - 0.2, ch - 0.65, desc[:70],
                  font_size=10, color=COLORS["body"])


def slide_tech_stack(prs, tech_items):
    """기술 스택 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "TECHNOLOGY STACK", "기술 스택", COLORS["accent3"], COLORS["accent3"])

    n = min(len(tech_items), 6)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 0.78)

    for i, item in enumerate(tech_items[:n]):
        y = start_y + i * item_h
        cat = item.get("category", "")
        tech = item.get("technology", item.get("tech", ""))

        _add_rounded_card(slide, 0.5, y, 9.0, item_h - 0.06, COLORS["card"])
        _add_circle_icon(slide, 0.7, y + (item_h - 0.42) / 2 - 0.03, 0.4,
                         PALETTE[i % len(PALETTE)], cat[:1].upper() if cat else "T")
        _add_text(slide, 1.3, y + 0.06, 2.5, 0.28, cat[:20],
                  font_size=12, bold=True, color=COLORS["accent"])
        _add_text(slide, 1.3, y + 0.35, 7.8, 0.3, tech[:80],
                  font_size=13, color=COLORS["body"])


def slide_architecture(prs, diagram_path):
    """시스템 아키텍처 다이어그램 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "SYSTEM ARCHITECTURE", "시스템 아키텍처", COLORS["accent3"], COLORS["accent3"])

    # 이미지를 콘텐츠 영역에 꽉 차게 삽입
    img_top = CONTENT_TOP
    img_h = SAFE_BOTTOM - img_top
    img_w = CONTENT_W

    # 이미지 비율 유지하면서 최대 크기 계산 (원본 1920x1080 = 16:9)
    aspect = 1920 / 1080
    fit_w = img_h * aspect
    if fit_w > img_w:
        fit_w = img_w
        fit_h = img_w / aspect
    else:
        fit_h = img_h

    img_left = MARGIN_X + (img_w - fit_w) / 2
    img_top_adj = img_top + (img_h - fit_h) / 2

    slide.shapes.add_picture(
        str(diagram_path),
        Inches(img_left), Inches(img_top_adj),
        Inches(fit_w), Inches(fit_h)
    )


def slide_timeline(prs, total_duration, phases):
    """타임라인 슬라이드 (컴팩트)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "PROJECT TIMELINE", "프로젝트 일정")

    # 총 기간 뱃지
    if total_duration:
        _add_rounded_card(slide, 7.2, 0.8, 2.2, 0.45, COLORS["accent"])
        _add_text(slide, 7.25, 0.83, 2.1, 0.4, total_duration,
                  font_size=14, bold=True, color=COLORS["white"],
                  alignment=PP_ALIGN.CENTER)

    n = min(len(phases), 5)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 0.95)

    for i, phase in enumerate(phases[:n]):
        y = start_y + i * item_h
        color = PALETTE[i % len(PALETTE)]
        name = phase.get("phase", phase.get("name", phase.get("phase_name", f"Phase {i+1}")))
        duration = phase.get("duration", phase.get("period", ""))
        desc = phase.get("period", phase.get("description", ""))

        _add_circle_icon(slide, 0.6, y + 0.02, 0.38, color, str(i + 1))
        _add_text(slide, 1.15, y, 4.5, 0.35, name[:35],
                  font_size=15, bold=True, color=COLORS["title"])
        _add_text(slide, 6.5, y, 3.0, 0.35, duration[:20],
                  font_size=13, color=COLORS["subtle"], alignment=PP_ALIGN.RIGHT)

        # 프로그레스 바
        bar_y = y + 0.4
        pct = min(100, ((i + 1) / n) * 100)
        _add_progress_bar(slide, 1.15, bar_y, 7.0, 0.15, pct, COLORS["border"], color)

        # 설명 (겹침 방지: 공간 있을 때만)
        if desc and desc != duration and item_h >= 0.85:
            _add_text(slide, 1.15, bar_y + 0.2, 7.0, 0.25, desc[:60],
                      font_size=10, color=COLORS["muted"])


def slide_team(prs, team_comp, total_mm):
    """팀 구성 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "PROJECT TEAM", "투입 인력", COLORS["accent2"], COLORS["accent2"])

    n = min(len(team_comp), 6)
    cols = 3 if n > 3 else n
    rows = math.ceil(n / cols)
    gap_x = 0.3
    gap_y = 0.25
    cw = (CONTENT_W - (cols - 1) * gap_x) / cols

    # 총 공수 뱃지 높이 확보
    badge_h = 0.5
    badge_gap = 0.2
    available_h = SAFE_BOTTOM - CONTENT_TOP - badge_h - badge_gap
    ch = min(2.2, (available_h - (rows - 1) * gap_y) / max(rows, 1))
    start_x = MARGIN_X

    role_icons = ["PM", "BE", "FE", "UX", "QA", "DV"]

    for i, member in enumerate(team_comp[:n]):
        col = i % cols
        row = i // cols
        x = start_x + col * (cw + gap_x)
        y = CONTENT_TOP + row * (ch + gap_y)

        _add_rounded_card(slide, x, y, cw, ch, COLORS["card"])

        role = member.get("role", f"역할 {i+1}")
        count = member.get("count", 1)
        expertise = member.get("expertise", member.get("skills", ""))

        icon_text = role_icons[i] if i < len(role_icons) else role[:2]
        _add_circle_icon(slide, x + (cw - 0.5) / 2, y + 0.12, 0.5,
                         PALETTE[i % len(PALETTE)], icon_text)

        _add_text(slide, x + 0.05, y + 0.72, cw - 0.1, 0.3, role[:15],
                  font_size=14, bold=True, color=COLORS["title"],
                  alignment=PP_ALIGN.CENTER)

        count_str = f"{count}명" if count >= 1 else f"{count} (파트타임)"
        _add_text(slide, x + 0.05, y + 1.02, cw - 0.1, 0.3, count_str,
                  font_size=18, bold=True, color=COLORS["accent"],
                  alignment=PP_ALIGN.CENTER, font_name=FONT_TITLE)

        if expertise and ch >= 1.8:
            _add_text(slide, x + 0.05, y + 1.35, cw - 0.1, 0.5,
                      str(expertise)[:40], font_size=9, color=COLORS["subtle"],
                      alignment=PP_ALIGN.CENTER)

    # 총 공수 하단 (카드 아래에 배치)
    badge_y = CONTENT_TOP + rows * (ch + gap_y) + 0.1
    badge_y = min(badge_y, SAFE_BOTTOM - badge_h)
    _add_rounded_card(slide, 2.5, badge_y, 5.0, badge_h, COLORS["accent"])
    _add_text(slide, 2.55, badge_y + 0.05, 4.9, 0.4,
              f"총 공수: {total_mm} Man-Months",
              font_size=16, bold=True, color=COLORS["white"],
              alignment=PP_ALIGN.CENTER, font_name=FONT_TITLE)


def slide_risks(prs, risks):
    """리스크 관리 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "RISK MANAGEMENT", "리스크 관리", COLORS["orange"], COLORS["orange"])

    n = min(len(risks), 4)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 1.15)

    for i, risk in enumerate(risks[:n]):
        y = start_y + i * item_h
        risk_text = risk.get("risk", risk.get("description", ""))
        impact = risk.get("impact", risk.get("level", "MEDIUM"))
        mitigation = risk.get("mitigation", "")

        if impact == "HIGH":
            level_color = COLORS["accent5"]
        elif impact == "LOW":
            level_color = COLORS["accent4"]
        else:
            level_color = COLORS["amber"]

        _add_rounded_card(slide, 0.5, y, 9.0, item_h - 0.08, COLORS["card"])

        # 영향도 뱃지
        _add_rounded_card(slide, 0.65, y + 0.12, 0.8, 0.3, level_color)
        _add_text(slide, 0.67, y + 0.13, 0.76, 0.28, impact,
                  font_size=10, bold=True, color=COLORS["white"],
                  alignment=PP_ALIGN.CENTER)

        _add_text(slide, 1.65, y + 0.08, 7.5, 0.35, risk_text[:55],
                  font_size=14, bold=True, color=COLORS["title"])

        if mitigation and item_h >= 0.85:
            _add_text(slide, 1.65, y + 0.5, 7.5, 0.4, f"-> {mitigation[:65]}",
                      font_size=11, color=COLORS["subtle"])


def slide_benefits(prs, quant_benefits, qual_benefits):
    """기대 효과 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "EXPECTED BENEFITS", "기대 효과", COLORS["accent4"], COLORS["accent4"])

    has_quant = bool(quant_benefits)
    has_qual = bool(qual_benefits)

    if has_quant:
        n_q = min(len(quant_benefits), 3)
        cw = 2.6
        gap = 0.3
        total_w = n_q * cw + (n_q - 1) * gap
        start_x = (SLIDE_W - total_w) / 2
        card_h = 1.6

        for i, b in enumerate(quant_benefits[:n_q]):
            x = start_x + i * (cw + gap)
            _add_rounded_card(slide, x, CONTENT_TOP, cw, card_h, COLORS["card"])

            metric = b.get("metric", "")
            before = b.get("before", "-")
            after = b.get("after", "-")

            _add_text(slide, x + 0.12, CONTENT_TOP + 0.1, cw - 0.24, 0.25,
                      metric[:30], font_size=11, bold=True, color=COLORS["subtle"])
            _add_text(slide, x + 0.12, CONTENT_TOP + 0.45, cw - 0.24, 0.5,
                      f"{before} -> {after}",
                      font_size=17, bold=True, color=COLORS["accent4"],
                      alignment=PP_ALIGN.CENTER, font_name=FONT_TITLE)
            _add_circle_icon(slide, x + (cw - 0.3) / 2, CONTENT_TOP + card_h - 0.45,
                             0.3, COLORS["accent4"], "^")

    qual_start_y = CONTENT_TOP + (1.9 if has_quant else 0)
    if has_qual:
        n_qual = min(len(qual_benefits), 5)
        spacing = min(0.42, (SAFE_BOTTOM - qual_start_y) / max(n_qual, 1))
        y = qual_start_y
        for i, qual in enumerate(qual_benefits[:n_qual]):
            text = qual if isinstance(qual, str) else str(qual)
            _add_text(slide, 0.8, y, 8.4, 0.35, f"  {text[:80]}",
                      font_size=14, color=COLORS["body"])
            y += spacing


def slide_next_steps(prs, steps):
    """다음 단계 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_white"])
    _slide_header(slide, "NEXT STEPS", "다음 단계")

    n = min(len(steps), 5)
    start_y, item_h = _calc_item_spacing(n, CONTENT_TOP, SAFE_BOTTOM, 0.9)

    for i, step in enumerate(steps[:n]):
        y = start_y + i * item_h
        action = step.get("action", step) if isinstance(step, dict) else str(step)
        duration = step.get("duration", "") if isinstance(step, dict) else ""

        _add_rounded_card(slide, 0.5, y, 9.0, item_h - 0.12, COLORS["card"])
        _add_circle_icon(slide, 0.7, y + (item_h - 0.45) / 2 - 0.06, 0.42,
                         PALETTE[i % len(PALETTE)], str(i + 1))
        _add_text(slide, 1.35, y + (item_h - 0.4) / 2 - 0.06, 5.8, 0.4,
                  action[:60], font_size=15, color=COLORS["body"])
        if duration:
            _add_text(slide, 7.5, y + (item_h - 0.35) / 2 - 0.06, 1.8, 0.35,
                      duration[:15], font_size=12, color=COLORS["subtle"],
                      alignment=PP_ALIGN.RIGHT)

        # 연결선 (마지막 항목 제외)
        if i < n - 1:
            conn_y = y + item_h - 0.12
            conn = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0.9), Inches(conn_y), Inches(0.03), Inches(0.12)
            )
            conn.fill.solid()
            conn.fill.fore_color.rgb = hex_to_rgb(COLORS["border"])
            conn.line.fill.background()


def slide_closing(prs, title_text, cta):
    """마무리 슬라이드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, COLORS["bg_section"])

    _add_text(slide, 0.5, 2.2, 9, 1.2, title_text,
              font_size=44, bold=True, color=COLORS["white"],
              alignment=PP_ALIGN.CENTER, font_name=FONT_TITLE)
    _add_accent_bar(slide, 3.5, 3.6, 3.0, 0.05, "3B82F6")
    _add_text(slide, 0.5, 4.0, 9, 0.6, cta,
              font_size=18, color=COLORS["muted"], alignment=PP_ALIGN.CENTER)
    _add_text(slide, 0.5, 5.2, 9, 0.5, "Q & A",
              font_size=26, bold=True, color="3B82F6",
              alignment=PP_ALIGN.CENTER, font_name=FONT_TITLE)


# ============================================================
# Validation
# ============================================================

def validate_ppt(prs):
    """PPT 슬라이드별 레이아웃 검증. 오버플로우/겹침 검출."""
    slide_w = prs.slide_width
    slide_h = prs.slide_height
    issues = []

    for idx, slide in enumerate(prs.slides):
        slide_num = idx + 1
        shapes_info = []

        for shape in slide.shapes:
            left = shape.left / 914400  # EMU to inches
            top = shape.top / 914400
            width = shape.width / 914400
            height = shape.height / 914400
            right = left + width
            bottom = top + height

            shapes_info.append({
                "name": shape.shape_id,
                "left": round(left, 2),
                "top": round(top, 2),
                "right": round(right, 2),
                "bottom": round(bottom, 2),
            })

            # 슬라이드 경계 초과 검사
            slide_w_in = slide_w / 914400
            slide_h_in = slide_h / 914400

            if right > slide_w_in + 0.1:
                issues.append(f"  슬라이드 {slide_num}: 요소가 우측 경계 초과 "
                              f"(right={right:.2f} > {slide_w_in:.1f})")
            if bottom > slide_h_in + 0.1:
                issues.append(f"  슬라이드 {slide_num}: 요소가 하단 경계 초과 "
                              f"(bottom={bottom:.2f} > {slide_h_in:.1f})")

        # 동일 위치 텍스트 겹침 검사 (같은 좌표에 같은 크기 텍스트가 중복 배치된 경우)
        # 의도적 레이어링(카드+텍스트, 그리드 레이아웃)은 제외
        for i, a in enumerate(shapes_info):
            for j, b in enumerate(shapes_info):
                if i >= j:
                    continue
                # 거의 동일 위치(0.05인치 이내)에 동일 크기 요소가 겹치면 문제
                same_pos = abs(a["left"] - b["left"]) < 0.05 and abs(a["top"] - b["top"]) < 0.05
                same_size = abs(a["right"] - a["left"] - (b["right"] - b["left"])) < 0.1 and \
                            abs(a["bottom"] - a["top"] - (b["bottom"] - b["top"])) < 0.1
                if same_pos and same_size:
                    a_area = (a["right"] - a["left"]) * (a["bottom"] - a["top"])
                    if a_area > 1.0:  # 큰 요소만 (작은 뱃지/바 제외)
                        issues.append(
                            f"  슬라이드 {slide_num}: 동일 위치 중복 요소 "
                            f"(top={a['top']:.1f}, left={a['left']:.1f})"
                        )

    return issues


# ============================================================
# Data Normalization
# ============================================================

def normalize_proposal_data(data: dict) -> dict:
    """제안서 JSON을 PPT 데이터로 정규화."""
    if "storytelling_structure" in data:
        return data
    if "current_challenges" in data:
        return _normalize_new_format(data)
    return _normalize_legacy_format(data)


def _normalize_new_format(data: dict) -> dict:
    """새 제안서 JSON 포맷 정규화."""
    exec_summary = data.get("executive_summary", {})
    core_msg = exec_summary.get("core_message", "")
    invest = exec_summary.get("investment_overview", {})
    key_metrics = exec_summary.get("key_metrics", {})
    title = data.get("title", "프로젝트 제안서")

    normalized = {
        "title": title,
        "metadata": {
            "proposal_date": data.get("created_at", ""),
            "client_company": data.get("client_name", ""),
            "proposer": data.get("proposer", ""),
        },
        "storytelling_structure": {
            "hook": core_msg[:60] if core_msg else title,
            "solution": core_msg[:80] if core_msg else title,
            "cta": "함께 시작하겠습니다",
        },
    }

    normalized["executive_summary"] = {
        "problem": core_msg,
        "solution": core_msg,
        "duration": invest.get("project_period", ""),
        "effort": invest.get("total_effort_with_buffer", invest.get("total_effort", "")),
        "key_benefits": list(key_metrics.values())[:2] if key_metrics else [],
    }

    challenges_raw = data.get("current_challenges", [])
    challenges = [{"area": ch.get("title", ""), "symptom": ch.get("description", ""),
                    "business_impact": ch.get("description", "")} for ch in challenges_raw]

    goals = data.get("project_goals", [])
    future_vision = {f"vision_{i+1}": f"{g.get('title', '')}: {g.get('description', '')}"
                     for i, g in enumerate(goals[:4])}

    normalized["current_situation"] = {
        "challenges": challenges,
        "risks_if_no_change": [ch.get("description", "") for ch in challenges_raw[:4]],
        "future_vision": future_vision,
    }

    kpis = [{"metric": k.get("name", ""), "current": k.get("current", "-"),
             "target": k.get("target", ""), "improvement": k.get("measurement", "")}
            for k in data.get("kpi", [])[:4]]
    normalized["objectives"] = {"kpis": kpis, "goals": [g.get("description", "") for g in goals]}

    scope_data = data.get("scope", {})
    in_scope = [{"value": s} if isinstance(s, str) else s for s in scope_data.get("in_scope", [])]
    out_scope = [{"item": s} if isinstance(s, str) else s for s in scope_data.get("out_of_scope", [])]
    modules = data.get("solution", {}).get("modules", [])

    normalized["solution"] = {
        "value_proposition": core_msg[:60] if core_msg else title,
        "overview": ", ".join(m.get("name", "") for m in modules[:3]),
        "scope": {"in_scope": in_scope, "out_of_scope": out_scope},
    }

    tech_data = data.get("technology_stack", {})
    tech_list = [{"category": k, "technology": ", ".join(v.values()) if isinstance(v, dict) else str(v)}
                 for k, v in tech_data.items() if isinstance(v, dict)]
    normalized["technical_approach"] = {"technology_stack": tech_list}

    timeline_data = data.get("timeline", {})
    normalized["timeline"] = {
        "total_duration": timeline_data.get("total_duration", ""),
        "phases": [{"phase": p.get("name", ""), "duration": p.get("period", ""),
                     "period": p.get("dates", "")} for p in timeline_data.get("phases", [])],
    }

    resource = data.get("resource_plan", {})
    normalized["team"] = {
        "composition": [{"role": m.get("role", ""), "count": m.get("count", 1),
                          "expertise": m.get("period", "")}
                         for m in resource.get("team", [])],
        "effort_summary": {"total": {"man_months": resource.get("total_man_months_with_buffer",
                                                                  resource.get("total_man_months", 0))}},
    }

    normalized["risk_management"] = [{"risk": r.get("title", r.get("description", "")),
                                       "impact": r.get("impact", "MEDIUM"),
                                       "mitigation": r.get("mitigation", "")}
                                      for r in data.get("risks", [])]

    benefits = data.get("expected_benefits", {})
    if isinstance(benefits, dict):
        quant = [{"metric": b.get("item", ""), "before": b.get("before", ""),
                  "after": b.get("after", ""), "improvement": "개선"}
                 for b in benefits.get("quantitative", [])[:4]]
        normalized["expected_benefits"] = {"quantitative": quant, "qualitative": benefits.get("qualitative", [])}
    else:
        normalized["expected_benefits"] = {"quantitative": [], "qualitative": []}

    milestones = timeline_data.get("milestones", [])
    normalized["next_steps"] = [{"step": i + 1, "action": ms.get("name", ""), "duration": ms.get("date", "")}
                                 for i, ms in enumerate(milestones[:5])]
    return normalized


def _normalize_legacy_format(data: dict) -> dict:
    """기존 ProposalDocument 모델 JSON 정규화. 동적 데이터 추출."""
    title = data.get("title", "프로젝트 제안서")
    exec_str = data.get("executive_summary", "")
    overview = data.get("project_overview", {})
    timeline_data = data.get("timeline", {})
    resource = data.get("resource_plan", {})
    total_duration = timeline_data.get("total_duration", "")
    total_mm = resource.get("total_man_months", "")

    normalized = {
        "title": title,
        "metadata": data.get("metadata", {}),
        "storytelling_structure": {
            "hook": exec_str[:60] if isinstance(exec_str, str) and exec_str else title,
            "solution": exec_str[:80] if isinstance(exec_str, str) and exec_str else title,
            "cta": "함께 시작하겠습니다",
        },
    }

    if isinstance(exec_str, str):
        normalized["executive_summary"] = {
            "problem": exec_str,
            "solution": exec_str,
            "duration": total_duration,
            "effort": f"{total_mm} M/M" if total_mm else "",
            "key_benefits": data.get("expected_benefits", [])[:2]
                            if isinstance(data.get("expected_benefits"), list) else []
        }
    else:
        normalized["executive_summary"] = exec_str

    background = overview.get("background", "")
    objectives = overview.get("objectives", [])
    success_criteria = overview.get("success_criteria", [])

    challenges = []
    if background:
        sentences = [s.strip() for s in background.replace('. ', '.\n').split('\n') if s.strip()]
        for i, sent in enumerate(sentences[:4]):
            challenges.append({"area": f"현황 {i+1}", "symptom": sent[:80], "business_impact": sent[:80]})

    risks_if_no = [f"{obj} 미달성 시 서비스 품질 저하" for obj in objectives[:4] if isinstance(obj, str)]
    future_vision = {f"vision_{i+1}": c for i, c in enumerate(success_criteria[:4])}

    normalized["current_situation"] = {
        "challenges": challenges,
        "risks_if_no_change": risks_if_no if risks_if_no else ["현재 방식 유지 시 비효율 지속"],
        "future_vision": future_vision,
    }

    kpis = [{"metric": c[:30], "current": "-", "target": c, "improvement": ""}
            for c in success_criteria[:4]]
    normalized["objectives"] = {"kpis": kpis, "goals": objectives}

    scope = data.get("scope_of_work", {})
    solution_approach = data.get("solution_approach", {})
    in_scope_list = scope.get("in_scope", [])
    out_scope_list = scope.get("out_of_scope", [])
    key_features = scope.get("key_features", [])

    in_scope_converted = [{"value": i} if isinstance(i, str) else i for i in in_scope_list]
    out_scope_converted = [{"item": i} if isinstance(i, str) else i for i in out_scope_list]

    normalized["solution"] = {
        "value_proposition": solution_approach.get("overview", title),
        "overview": solution_approach.get("architecture", ""),
        "scope": {"in_scope": in_scope_converted, "out_of_scope": out_scope_converted},
        "key_features": key_features,
    }

    tech_stack = solution_approach.get("technology_stack", [])
    tech_converted = []
    for item in tech_stack:
        if isinstance(item, str):
            parts = item.split("(", 1)
            cat = parts[1].rstrip(")") if len(parts) > 1 else ""
            tech_converted.append({"category": cat, "technology": parts[0].strip()})
        else:
            tech_converted.append(item)
    normalized["technical_approach"] = {"technology_stack": tech_converted}

    phases = timeline_data.get("phases", [])
    normalized["timeline"] = {
        "total_duration": total_duration,
        "phases": [{"phase": p.get("phase_name", ""), "duration": p.get("duration", ""),
                     "period": p.get("description", "")} for p in phases],
    }

    team_structure = resource.get("team_structure", [])
    normalized["team"] = {
        "composition": [{"role": m.get("role", ""), "count": m.get("count", 1),
                          "expertise": ", ".join(m.get("responsibilities", [])[:2])}
                         for m in team_structure],
        "effort_summary": {"total": {"man_months": total_mm}},
    }

    normalized["risk_management"] = [{"risk": r.get("description", ""),
                                       "impact": r.get("level", "MEDIUM"),
                                       "mitigation": r.get("mitigation", "")}
                                      for r in data.get("risks", [])]

    benefits = data.get("expected_benefits", [])
    if isinstance(benefits, list):
        quant = [{"metric": b[:40], "before": "", "after": "", "improvement": ""}
                 for b in benefits[:4] if isinstance(b, str)]
        normalized["expected_benefits"] = {"quantitative": quant, "qualitative": benefits}
    else:
        normalized["expected_benefits"] = benefits

    steps = data.get("next_steps", [])
    normalized["next_steps"] = [{"step": i + 1, "action": s, "duration": ""}
                                 if isinstance(s, str) else s for i, s in enumerate(steps)]
    return normalized


# ============================================================
# Main Generator
# ============================================================

def _get_or_generate_arch_diagram() -> Path | None:
    """아키텍처 다이어그램 PNG 가져오기 또는 TRD에서 자동 생성."""
    diagram_dir = Path("workspace/outputs/diagrams")
    existing = list(diagram_dir.glob("ARCH-*.png")) if diagram_dir.exists() else []
    if existing:
        return max(existing, key=lambda x: x.stat().st_mtime)

    # TRD JSON에서 자동 생성
    trd_dir = Path("workspace/outputs/trd")
    trd_files = list(trd_dir.glob("TRD-*.json")) if trd_dir.exists() else []
    if not trd_files:
        return None

    trd_path = max(trd_files, key=lambda x: x.stat().st_mtime)
    try:
        print(f"   아키텍처 다이어그램 자동 생성 중... ({trd_path.name})")
        result = generate_from_trd_file(trd_path, diagram_dir)
        print(f"   다이어그램 생성 완료: {result.name}")
        return result
    except Exception as e:
        print(f"   [경고] 다이어그램 생성 실패: {e}")
        return None


def load_proposal_json(json_path: Path) -> dict:
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_ppt(proposal_path: Path, output_path: Path):
    """PPT 생성 메인."""
    json_path = proposal_path.with_suffix('.json')
    if json_path.exists():
        raw_data = load_proposal_json(json_path)
        print(f"   JSON 데이터 로드: {json_path.name}")
    else:
        raw_data = {"title": "프로젝트 제안서"}

    data = normalize_proposal_data(raw_data)

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    title = data.get("title", "프로젝트 제안서").replace(" 제안서", "")
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
    key_features = solution.get("key_features", [])

    client = metadata.get("client_company", data.get("client_name", ""))
    date_str = metadata.get("proposal_date", metadata.get("created_at", ""))
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    subtitle = f"{client} 귀중" if client else ""

    total_duration = timeline.get("total_duration", "")
    total_mm = team.get("effort_summary", {}).get("total", {}).get("man_months", "")

    # ---- 슬라이드 생성 ----

    slide_cover(prs, title, subtitle, date_str)

    toc_items = [
        "경영진 요약 (Executive Summary)",
        "현재 상황과 도전 (Challenges)",
        "프로젝트 목표 (Objectives)",
        "우리의 솔루션 (Solution)",
        "핵심 기능 (Features)",
        "기술 스택 (Tech Stack)",
        "시스템 아키텍처 (Architecture)",
        "프로젝트 일정 (Timeline)",
        "투입 인력 (Team)",
        "리스크 관리 (Risks)",
        "기대 효과 (Benefits)",
        "다음 단계 (Next Steps)",
    ]
    slide_toc(prs, toc_items)

    # 경영진 요약 - 핵심
    exec_problem = exec_summary.get("problem", "") if isinstance(exec_summary, dict) else str(exec_summary)
    exec_metrics = []
    if total_duration:
        exec_metrics.append({"label": "프로젝트 기간", "value": total_duration, "desc": ""})
    if total_mm:
        exec_metrics.append({"label": "투입 공수", "value": f"{total_mm} M/M", "desc": ""})
    key_benefits = exec_summary.get("key_benefits", []) if isinstance(exec_summary, dict) else []
    if key_benefits:
        exec_metrics.append({"label": "핵심 효과", "value": str(key_benefits[0])[:20], "desc": ""})
    slide_exec_highlight(prs, exec_problem[:150], exec_metrics)

    # 경영진 요약 - 상세
    detail_items = []
    if isinstance(exec_summary, dict):
        if exec_summary.get("problem"):
            detail_items.append({"label": "해결할 문제", "value": exec_summary["problem"][:80]})
        if exec_summary.get("solution") and exec_summary["solution"] != exec_summary.get("problem"):
            detail_items.append({"label": "솔루션", "value": exec_summary["solution"][:80]})
        if total_duration:
            detail_items.append({"label": "예상 기간", "value": total_duration})
        if exec_summary.get("effort"):
            detail_items.append({"label": "투입 공수", "value": str(exec_summary["effort"])})
        for b in key_benefits[:2]:
            detail_items.append({"label": "핵심 효과", "value": str(b)[:60]})
    slide_exec_detail(prs, detail_items)

    # 섹션: 현재 상황
    slide_section(prs, 1, "현재 상황", "Current Challenges")

    challenges = current_sit.get("challenges", [])
    slide_challenges(prs, "현재의 도전과 과제", challenges)

    risks_no_change = current_sit.get("risks_if_no_change", [])
    slide_risks_no_change(prs, risks_no_change)

    before_items = [c.get("business_impact", c.get("symptom", "")) for c in challenges[:5]]
    after_items = list(current_sit.get("future_vision", {}).values())[:5]
    slide_before_after(prs, before_items, after_items)

    # 섹션: 프로젝트 목표
    slide_section(prs, 2, "프로젝트 목표", "Objectives & KPI")
    kpis = objectives.get("kpis", [])
    slide_kpi(prs, "핵심 성과 지표 (KPI)", kpis)

    # 섹션: 솔루션
    slide_section(prs, 3, "우리의 솔루션", "Our Solution")
    slide_solution_highlight(prs, solution.get("value_proposition", title), solution.get("overview", "")[:120])

    in_scope = solution.get("scope", {}).get("in_scope", [])
    out_scope = solution.get("scope", {}).get("out_of_scope", [])
    slide_scope(prs, in_scope, out_scope)

    if key_features:
        slide_features(prs, key_features)

    # 기술 스택
    tech_stack = tech.get("technology_stack", [])
    slide_tech_stack(prs, tech_stack)

    # 시스템 아키텍처 다이어그램
    arch_diagram_path = _get_or_generate_arch_diagram()
    if arch_diagram_path:
        slide_architecture(prs, arch_diagram_path)

    # 섹션: 일정
    slide_section(prs, 4, "프로젝트 일정", "Timeline & Milestones")
    phases = timeline.get("phases", [])
    slide_timeline(prs, total_duration, phases)

    # 팀 구성
    team_comp = team.get("composition", [])
    slide_team(prs, team_comp, total_mm)

    # 리스크
    slide_risks(prs, risks)

    # 기대 효과
    quant = benefits.get("quantitative", []) if isinstance(benefits, dict) else []
    qual = benefits.get("qualitative", []) if isinstance(benefits, dict) else (
        benefits if isinstance(benefits, list) else [])
    slide_benefits(prs, quant, qual)

    # 다음 단계
    slide_next_steps(prs, next_steps)

    # Q&A
    slide_closing(prs, "감사합니다", storytelling.get("cta", "함께 시작하겠습니다"))

    # ---- 최종 검증 ----
    print("\n[검증] 슬라이드 레이아웃 검증 중...")
    issues = validate_ppt(prs)
    if issues:
        print(f"  [주의] {len(issues)}건의 레이아웃 이슈 발견:")
        for issue in issues[:10]:
            print(f"    {issue}")
    else:
        print("  [통과] 모든 슬라이드 레이아웃 정상")

    prs.save(str(output_path))
    slide_count = len(prs.slides)
    return output_path, slide_count


def main():
    print("\n" + "=" * 70)
    print("PPT 제안서 생성 (2026 Modern Design)")
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print("=" * 70)

    proposal_dir = Path("workspace/outputs/proposals")
    md_files = list(proposal_dir.glob("PROP-*.md"))

    if not md_files:
        print("제안서 파일을 찾을 수 없습니다.")
        print("먼저 /pro:pro-maker를 실행하세요.")
        return

    proposal_path = max(md_files, key=lambda x: x.stat().st_mtime)
    print(f"\n[입력] 제안서: {proposal_path}")

    output_dir = Path("workspace/outputs/ppt")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"PPT-{timestamp}.pptx"

    result, slide_count = generate_ppt(proposal_path, output_path)

    if result:
        print(f"\n[완료] PPT 생성 완료: {output_path}")
        print(f"   슬라이드 수: {slide_count}장")
        print(f"   테마: 2026 Modern Light")
    else:
        print("\n[실패] PPT 생성 실패")


if __name__ == "__main__":
    main()
