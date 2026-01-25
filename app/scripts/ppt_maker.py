"""PPT 제안서 생성 스크립트.

Usage:
    python -m app.scripts.ppt_maker

제안서(PROP-*.md)를 기반으로 다크 테마 PPT 생성.
"""

import json
import re
from datetime import datetime
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RgbColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    print("python-pptx 라이브러리가 설치되어 있지 않습니다.")
    print("설치: pip install python-pptx")


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


def hex_to_rgb(hex_color: str) -> RgbColor:
    """Hex 컬러를 RgbColor로 변환."""
    hex_color = hex_color.lstrip('#')
    return RgbColor(
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


def generate_ppt(proposal_path: Path, output_path: Path):
    """PPT 생성."""
    if not PPTX_AVAILABLE:
        print("python-pptx 설치 필요: pip install python-pptx")
        return None
    
    # 제안서 읽기
    md_content = proposal_path.read_text(encoding='utf-8')
    data = parse_proposal(md_content)
    
    # PPT 생성
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    
    # 1. 표지
    add_title_slide(
        prs, 
        data.get("title", "프로젝트 제안서"),
        f"{data.get('date', '')} | {data.get('client', '')}"
    )
    
    # 2. 목차
    add_content_slide(prs, "목차", [
        "경영진 요약",
        "현재 상황과 도전",
        "프로젝트 목표",
        "우리의 솔루션",
        "기술 접근법",
        "일정 계획",
        "투입 인력",
        "기대 효과",
        "다음 단계"
    ])
    
    # 3-4. 경영진 요약
    add_highlight_slide(prs, "핵심 메시지", "프로젝트의 가치를 한 문장으로")
    add_content_slide(prs, "경영진 요약", [
        "해결할 문제: [문제 정의]",
        "우리의 솔루션: [솔루션 개요]",
        "예상 기간: N개월",
        "기대 효과: [핵심 수치]"
    ])
    
    # 5-6. 현재 문제
    add_section_title_slide(prs, 1, "현재 상황")
    add_content_slide(prs, "현재의 도전과 과제", [
        "문제 1: [상세 설명]",
        "문제 2: [상세 설명]",
        "문제 3: [상세 설명]"
    ])
    
    # 7. 변화의 필요성
    add_highlight_slide(prs, "왜 지금 변화해야 하는가?", "기회 비용과 위험 분석")
    
    # 8. 목표
    add_section_title_slide(prs, 2, "프로젝트 목표")
    add_content_slide(prs, "목표 및 KPI", [
        "목표 1: [성공 기준]",
        "목표 2: [성공 기준]",
        "목표 3: [성공 기준]"
    ])
    
    # 10. 솔루션
    add_section_title_slide(prs, 3, "우리의 솔루션")
    add_content_slide(prs, "솔루션 개요", [
        "핵심 기능 1",
        "핵심 기능 2",
        "핵심 기능 3",
        "작업 범위"
    ])
    
    # 12. 아키텍처
    add_content_slide(prs, "시스템 아키텍처", [
        "[아키텍처 다이어그램은 별도 이미지로 교체]",
        "Frontend: React",
        "Backend: FastAPI",
        "Database: PostgreSQL",
        "Infrastructure: AWS"
    ])
    
    # 13-14. 일정
    add_section_title_slide(prs, 4, "일정 계획")
    add_content_slide(prs, "프로젝트 타임라인", [
        "Phase 1: 분석/설계 (N주)",
        "Phase 2: 개발 (N주)",
        "Phase 3: 테스트 (N주)",
        "Phase 4: 배포 (N주)"
    ])
    
    # 15-16. 인력
    add_section_title_slide(prs, 5, "투입 인력")
    add_content_slide(prs, "프로젝트 팀 구성", [
        "PM/PL: 1명",
        "백엔드 개발자: 2명",
        "프론트엔드 개발자: 1명",
        "DevOps/QA: 1명",
        "총 공수: N M/M"
    ])
    
    # 17. 리스크
    add_content_slide(prs, "리스크 관리", [
        "리스크 1 → 대응: [대응책]",
        "리스크 2 → 대응: [대응책]",
        "리스크 3 → 대응: [대응책]"
    ])
    
    # 18. 기대 효과
    add_section_title_slide(prs, 6, "기대 효과")
    add_highlight_slide(prs, "45분 → 20분", "처리 시간 56% 단축")
    
    # 19. 다음 단계
    add_content_slide(prs, "다음 단계", [
        "1. 제안서 검토 및 Q&A (1주)",
        "2. 세부 협의 및 조정 (1주)",
        "3. 계약 체결 (1주)",
        "4. 킥오프 미팅",
        "5. 프로젝트 착수"
    ])
    
    # 20. Q&A
    add_closing_slide(prs, "감사합니다", "Q&A | 연락처: [담당자 정보]")
    
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
        print(f"\n✅ PPT 생성 완료: {output_path}")
        print(f"   슬라이드 수: 20장")
    else:
        print("\n❌ PPT 생성 실패")


if __name__ == "__main__":
    main()
