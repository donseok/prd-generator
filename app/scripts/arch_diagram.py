"""시스템 아키텍처 다이어그램 생성 스크립트.

Usage:
    python -m app.scripts.arch_diagram

TRD JSON의 system_architecture를 읽어 시각적 아키텍처 다이어그램 PNG를 생성.
PPT 슬라이드 삽입 및 독립 실행 모두 지원.
"""

import json
import math
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# 디자인 상수
# ============================================================
IMG_W = 1920
IMG_H = 1080
BG_COLOR = "#FFFFFF"
CARD_RADIUS = 16

# 컬러 팔레트 (2026 모던 디자인)
LAYER_COLORS = {
    "Presentation Layer": {"bg": "#EEF2FF", "border": "#818CF8", "accent": "#6366F1", "icon": "#4F46E5"},
    "API Layer":          {"bg": "#ECFDF5", "border": "#6EE7B7", "accent": "#10B981", "icon": "#059669"},
    "Service Layer":      {"bg": "#FFF7ED", "border": "#FDBA74", "accent": "#F97316", "icon": "#EA580C"},
    "Data Layer":         {"bg": "#FEF2F2", "border": "#FCA5A5", "accent": "#EF4444", "icon": "#DC2626"},
    "Infrastructure":     {"bg": "#F0F9FF", "border": "#7DD3FC", "accent": "#0EA5E9", "icon": "#0284C7"},
}
DEFAULT_LAYER = {"bg": "#F8FAFC", "border": "#94A3B8", "accent": "#64748B", "icon": "#475569"}

COMP_COLORS = ["#6366F1", "#0EA5E9", "#10B981", "#F97316", "#EC4899", "#8B5CF6"]

TEXT_DARK = "#0F172A"
TEXT_MID = "#334155"
TEXT_LIGHT = "#64748B"
ARROW_COLOR = "#94A3B8"


def _get_font(size, bold=False):
    """시스템 폰트 로드."""
    font_paths = [
        # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Windows
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _rounded_rect(draw, xy, fill, outline=None, radius=16, width=2):
    """둥근 사각형 그리기."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_arrow(draw, x1, y1, x2, y2, color=ARROW_COLOR, width=3):
    """화살표 그리기."""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # 화살촉
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 12
    arrow_angle = math.pi / 6
    lx = x2 - arrow_len * math.cos(angle - arrow_angle)
    ly = y2 - arrow_len * math.sin(angle - arrow_angle)
    rx = x2 - arrow_len * math.cos(angle + arrow_angle)
    ry = y2 - arrow_len * math.sin(angle + arrow_angle)
    draw.polygon([(x2, y2), (lx, ly), (rx, ry)], fill=color)


def _draw_circle_icon(draw, cx, cy, r, color, text="", font=None):
    """원형 아이콘."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    if text and font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2 - 2), text, fill="#FFFFFF", font=font)


def generate_arch_diagram(trd_data: dict, output_path: Path) -> Path:
    """TRD 데이터에서 아키텍처 다이어그램 PNG 생성."""
    arch = trd_data.get("system_architecture", {})
    layers = arch.get("layers", [])
    data_flow = arch.get("data_flow", "")
    arch_style = arch.get("architecture_style", "")
    overview = arch.get("overview", "")

    img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_title = _get_font(28, bold=True)
    font_subtitle = _get_font(16)
    font_layer = _get_font(20, bold=True)
    font_comp = _get_font(14, bold=True)
    font_comp_desc = _get_font(11)
    font_small = _get_font(10)
    font_icon = _get_font(12, bold=True)
    font_flow = _get_font(12)

    # ---- 상단 헤더 ----
    # 얇은 액센트 바
    draw.rectangle([0, 0, IMG_W, 5], fill="#2563EB")

    # 제목
    title = trd_data.get("title", "System Architecture")
    draw.text((40, 20), title, fill=TEXT_DARK, font=font_title)

    # 부제 (아키텍처 스타일)
    if arch_style:
        draw.text((40, 55), arch_style, fill=TEXT_LIGHT, font=font_subtitle)

    # 우측 뱃지
    badge_text = f"Layers: {len(layers)}"
    _rounded_rect(draw, (IMG_W - 180, 20, IMG_W - 30, 52), fill="#2563EB", radius=12)
    bbox = draw.textbbox((0, 0), badge_text, font=font_subtitle)
    draw.text((IMG_W - 180 + (150 - (bbox[2] - bbox[0])) / 2, 24), badge_text,
              fill="#FFFFFF", font=font_subtitle)

    # ---- 레이어 영역 ----
    margin_x = 40
    margin_top = 85
    gap_y = 15
    available_h = IMG_H - margin_top - 120  # 하단 데이터 플로우 공간
    n_layers = max(len(layers), 1)
    layer_h = min(280, (available_h - (n_layers - 1) * gap_y) / n_layers)

    for li, layer in enumerate(layers):
        layer_name = layer.get("name", f"Layer {li+1}")
        layer_desc = layer.get("description", "")
        components = layer.get("components", [])

        colors = LAYER_COLORS.get(layer_name, DEFAULT_LAYER)
        y_top = margin_top + li * (layer_h + gap_y)
        layer_w = IMG_W - 2 * margin_x

        # 레이어 배경 카드
        _rounded_rect(draw, (margin_x, y_top, margin_x + layer_w, y_top + layer_h),
                       fill=colors["bg"], outline=colors["border"], radius=CARD_RADIUS, width=2)

        # 좌측 레이어 라벨 (세로 배치)
        label_w = 140
        _rounded_rect(draw, (margin_x + 8, y_top + 8, margin_x + label_w, y_top + layer_h - 8),
                       fill=colors["accent"], radius=12)

        # 라벨 텍스트 (세로 중앙)
        parts = layer_name.split(" ")
        label_y = y_top + (layer_h - len(parts) * 28) / 2
        for part in parts:
            bbox = draw.textbbox((0, 0), part, font=font_layer)
            tw = bbox[2] - bbox[0]
            draw.text((margin_x + 8 + (label_w - 8 - tw) / 2, label_y),
                      part, fill="#FFFFFF", font=font_layer)
            label_y += 28

        # 레이어 설명
        if layer_desc:
            draw.text((margin_x + label_w + 15, y_top + 10),
                      layer_desc[:80], fill=TEXT_LIGHT, font=font_small)

        # ---- 컴포넌트 카드 ----
        comp_area_x = margin_x + label_w + 15
        comp_area_w = layer_w - label_w - 30
        comp_area_y = y_top + 30
        comp_area_h = layer_h - 42

        n_comps = len(components)
        if n_comps == 0:
            continue

        # 동적 레이아웃
        max_cols = min(n_comps, 5)
        cols = max_cols
        rows = math.ceil(n_comps / cols)
        gap_cx = 12
        gap_cy = 10
        comp_w = (comp_area_w - (cols - 1) * gap_cx) / cols
        comp_h = min(110, (comp_area_h - (rows - 1) * gap_cy) / max(rows, 1))

        for ci, comp in enumerate(components):
            col = ci % cols
            row = ci // cols
            cx = comp_area_x + col * (comp_w + gap_cx)
            cy = comp_area_y + row * (comp_h + gap_cy)

            comp_color = COMP_COLORS[ci % len(COMP_COLORS)]

            # 컴포넌트 카드
            _rounded_rect(draw, (cx, cy, cx + comp_w, cy + comp_h),
                           fill="#FFFFFF", outline=colors["border"], radius=10, width=1)

            # 아이콘
            icon_r = 12
            icon_cx = cx + 18
            icon_cy = cy + 20
            _draw_circle_icon(draw, icon_cx, icon_cy, icon_r, comp_color,
                              comp.get("name", "?")[:1].upper(), font_icon)

            # 컴포넌트 이름
            comp_name = comp.get("name", "")
            draw.text((cx + 36, cy + 8), comp_name[:20], fill=TEXT_DARK, font=font_comp)

            # 타입 뱃지
            comp_type = comp.get("type", "")
            if comp_type:
                badge_x = cx + 36
                badge_y = cy + 30
                bbox = draw.textbbox((0, 0), comp_type, font=font_small)
                bw = bbox[2] - bbox[0] + 10
                _rounded_rect(draw, (badge_x, badge_y, badge_x + bw, badge_y + 16),
                               fill=colors["bg"], radius=6)
                draw.text((badge_x + 5, badge_y + 1), comp_type, fill=colors["accent"],
                          font=font_small)

            # 설명 (줄 제한)
            desc = comp.get("description", "")
            if desc and comp_h > 60:
                max_chars = int(comp_w / 7)
                desc_lines = [desc[i:i+max_chars] for i in range(0, min(len(desc), max_chars * 2), max_chars)]
                dy = cy + 52
                for line in desc_lines[:2]:
                    draw.text((cx + 10, dy), line, fill=TEXT_LIGHT, font=font_comp_desc)
                    dy += 15

            # 인터페이스 표시
            interfaces = comp.get("interfaces", [])
            if interfaces and comp_h > 85:
                iface_text = interfaces[0][:30] if interfaces else ""
                draw.text((cx + 10, cy + comp_h - 18), iface_text,
                          fill=TEXT_LIGHT, font=font_small)

    # ---- 레이어 간 화살표 ----
    for li in range(len(layers) - 1):
        y1 = margin_top + li * (layer_h + gap_y) + layer_h
        y2 = margin_top + (li + 1) * (layer_h + gap_y)
        mid_x = IMG_W / 2
        _draw_arrow(draw, mid_x, y1 + 2, mid_x, y2 - 2, color="#94A3B8", width=2)

    # ---- 하단 데이터 플로우 ----
    flow_y = IMG_H - 80
    _rounded_rect(draw, (margin_x, flow_y - 10, IMG_W - margin_x, IMG_H - 15),
                   fill="#F8FAFC", outline="#E2E8F0", radius=10, width=1)

    draw.text((margin_x + 12, flow_y - 2), "Data Flow:", fill="#2563EB", font=font_comp)

    if data_flow:
        # 화살표 스타일로 표시
        flow_parts = [p.strip() for p in data_flow.split("→")]
        fx = margin_x + 100
        for i, part in enumerate(flow_parts[:8]):
            text = part[:18]
            bbox = draw.textbbox((0, 0), text, font=font_flow)
            tw = bbox[2] - bbox[0]

            _rounded_rect(draw, (fx, flow_y, fx + tw + 14, flow_y + 22),
                           fill="#EEF2FF", radius=8)
            draw.text((fx + 7, flow_y + 3), text, fill=TEXT_MID, font=font_flow)

            fx += tw + 20
            if i < len(flow_parts) - 1 and fx < IMG_W - 80:
                # 화살표
                draw.text((fx - 8, flow_y + 2), "->", fill=ARROW_COLOR, font=font_flow)
                fx += 16

            if fx > IMG_W - 120:
                break

    # ---- 하단 액센트 바 ----
    draw.rectangle([0, IMG_H - 4, IMG_W, IMG_H], fill="#7C3AED")

    img.save(str(output_path), "PNG", quality=95)
    return output_path


def generate_from_trd_file(trd_path: Path, output_dir: Path = None) -> Path:
    """TRD 파일에서 아키텍처 다이어그램 생성."""
    with open(trd_path, 'r', encoding='utf-8') as f:
        trd_data = json.load(f)

    if output_dir is None:
        output_dir = Path("workspace/outputs/diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"ARCH-{timestamp}.png"

    return generate_arch_diagram(trd_data, output_path)


def main():
    print("\n" + "=" * 70)
    print("시스템 아키텍처 다이어그램 생성")
    print(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print("=" * 70)

    trd_dir = Path("workspace/outputs/trd")
    json_files = list(trd_dir.glob("TRD-*.json"))

    if not json_files:
        print("TRD JSON 파일을 찾을 수 없습니다.")
        print("먼저 /trd:trd-maker를 실행하세요.")
        return

    trd_path = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"\n[입력] TRD: {trd_path}")

    result = generate_from_trd_file(trd_path)
    print(f"\n[완료] 다이어그램 생성: {result}")


if __name__ == "__main__":
    main()
