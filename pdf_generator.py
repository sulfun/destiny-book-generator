"""
PDF 생성기 - 운명책
Destiny Book PDF Generator

ReportLab + pypdf, 한국어 CID 폰트 사용
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from pypdf import PdfReader, PdfWriter
import json


# === 색상 팔레트 ===
COLORS = {
    "primary": HexColor("#1a1a2e"),     # 남색 배경
    "secondary": HexColor("#16213e"),   # 진남색
    "accent": HexColor("#c9a96e"),      # 골드
    "text": HexColor("#2c2c2c"),        # 본문 텍스트
    "text_light": HexColor("#666666"),  # 연한 텍스트
    "bg_light": HexColor("#f8f6f0"),    # 크림색 배경
    "divider": HexColor("#d4c5a0"),     # 구분선
    "chapter_bg": HexColor("#1a1a2e"),  # 챕터 타이틀 배경
}

# === CID 폰트 이름 ===
FONT_GOTHIC = "HYGothic-Medium"  # 고딕 (제목용)
FONT_MYEONGJO = "HYSMyeongJo-Medium"  # 명조 (본문용)

# === 페이지 설정 ===
PAGE_W, PAGE_H = A4
MARGIN_LEFT = 25 * mm
MARGIN_RIGHT = 25 * mm
MARGIN_TOP = 30 * mm
MARGIN_BOTTOM = 25 * mm
CONTENT_WIDTH = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT


def create_cover_page(output_path, client_name, core_theme, birth_info):
    """표지 페이지 생성"""
    c = canvas.Canvas(output_path, pagesize=A4)

    # 배경
    c.setFillColor(COLORS["primary"])
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1)

    # 상단 장식선
    c.setStrokeColor(COLORS["accent"])
    c.setLineWidth(0.5)
    y_top = PAGE_H - 60 * mm
    c.line(50 * mm, y_top, PAGE_W - 50 * mm, y_top)

    # "운명책" 타이틀
    c.setFillColor(COLORS["accent"])
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase import pdfmetrics
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_GOTHIC))
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_MYEONGJO))

    c.setFont(FONT_GOTHIC, 14)
    c.drawCentredString(PAGE_W / 2, y_top + 10 * mm, "運 命 冊")

    c.setFont(FONT_GOTHIC, 36)
    c.drawCentredString(PAGE_W / 2, y_top - 25 * mm, "운명책")

    # 영문 서브타이틀
    c.setFont(FONT_GOTHIC, 11)
    c.setFillColor(HexColor("#8a8a8a"))
    c.drawCentredString(PAGE_W / 2, y_top - 40 * mm, "THE BOOK OF DESTINY")

    # 구분선
    c.setStrokeColor(COLORS["accent"])
    c.setLineWidth(0.3)
    y_mid = y_top - 55 * mm
    c.line(70 * mm, y_mid, PAGE_W - 70 * mm, y_mid)

    # 의뢰인 이름
    c.setFillColor(white)
    c.setFont(FONT_GOTHIC, 28)
    c.drawCentredString(PAGE_W / 2, y_mid - 25 * mm, client_name)

    # 코어 테마
    c.setFillColor(COLORS["accent"])
    c.setFont(FONT_MYEONGJO, 14)
    c.drawCentredString(PAGE_W / 2, y_mid - 50 * mm, f"「{core_theme}」")

    # 출생 정보
    c.setFillColor(HexColor("#8a8a8a"))
    c.setFont(FONT_MYEONGJO, 10)
    birth_text = f"{birth_info.get('year', '')}년 {birth_info.get('month', '')}월 {birth_info.get('day', '')}일 {birth_info.get('hour', '')}시 {birth_info.get('minute', '00')}분"
    c.drawCentredString(PAGE_W / 2, y_mid - 70 * mm, birth_text)

    city = birth_info.get('city', '')
    if city:
        c.drawCentredString(PAGE_W / 2, y_mid - 80 * mm, city)

    # 하단 장식선
    y_bottom = 40 * mm
    c.setStrokeColor(COLORS["accent"])
    c.setLineWidth(0.5)
    c.line(50 * mm, y_bottom, PAGE_W - 50 * mm, y_bottom)

    # 하단 크레딧
    c.setFillColor(HexColor("#666666"))
    c.setFont(FONT_GOTHIC, 8)
    c.drawCentredString(PAGE_W / 2, y_bottom - 10 * mm, "Produced by SULFUN | 운명학 종합 분석 시스템")

    c.save()


def create_chapter_title_page(c, chapter_num, chapter_title):
    """챕터 타이틀 페이지 생성 (canvas에 직접 그리기)"""
    # 배경
    c.setFillColor(COLORS["secondary"])
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1)

    # 챕터 번호
    c.setFillColor(COLORS["accent"])
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase import pdfmetrics
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_GOTHIC))
    except:
        pass

    c.setFont(FONT_GOTHIC, 12)
    y_center = PAGE_H / 2 + 20 * mm
    c.drawCentredString(PAGE_W / 2, y_center + 15 * mm, f"CHAPTER {chapter_num}")

    # 장식선
    c.setStrokeColor(COLORS["accent"])
    c.setLineWidth(0.5)
    c.line(70 * mm, y_center + 10 * mm, PAGE_W - 70 * mm, y_center + 10 * mm)

    # 챕터 제목
    c.setFillColor(white)
    c.setFont(FONT_GOTHIC, 22)
    c.drawCentredString(PAGE_W / 2, y_center - 10 * mm, chapter_title)

    c.showPage()


def get_body_styles():
    """본문 스타일 정의"""
    styles = {
        "heading1": ParagraphStyle(
            name="Heading1",
            fontName=FONT_GOTHIC,
            fontSize=16,
            leading=24,
            spaceAfter=12 * mm,
            spaceBefore=8 * mm,
            textColor=COLORS["primary"],
        ),
        "heading2": ParagraphStyle(
            name="Heading2",
            fontName=FONT_GOTHIC,
            fontSize=13,
            leading=20,
            spaceAfter=6 * mm,
            spaceBefore=6 * mm,
            textColor=COLORS["secondary"],
        ),
        "body": ParagraphStyle(
            name="Body",
            fontName=FONT_MYEONGJO,
            fontSize=10.5,
            leading=19,
            spaceAfter=3 * mm,
            alignment=TA_JUSTIFY,
            textColor=COLORS["text"],
        ),
        "quote": ParagraphStyle(
            name="Quote",
            fontName=FONT_MYEONGJO,
            fontSize=11,
            leading=20,
            spaceAfter=5 * mm,
            spaceBefore=5 * mm,
            leftIndent=15 * mm,
            rightIndent=15 * mm,
            alignment=TA_CENTER,
            textColor=COLORS["accent"],
        ),
        "small": ParagraphStyle(
            name="Small",
            fontName=FONT_MYEONGJO,
            fontSize=9,
            leading=15,
            textColor=COLORS["text_light"],
        ),
    }
    return styles


class GoldDivider(Flowable):
    """골드 구분선 Flowable"""
    def __init__(self, width=None):
        super().__init__()
        self.width = width or CONTENT_WIDTH
        self.height = 5 * mm

    def draw(self):
        self.canv.setStrokeColor(COLORS["divider"])
        self.canv.setLineWidth(0.5)
        self.canv.line(20 * mm, self.height / 2, self.width - 20 * mm, self.height / 2)


def text_to_flowables(text, styles):
    """마크다운 유사 텍스트 → ReportLab Flowables 변환"""
    flowables = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            flowables.append(Spacer(1, 3 * mm))
            continue

        # XML 특수문자 이스케이프
        safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # 마크다운 헤딩
        if line.startswith('## '):
            text_content = safe_line[3:].strip()
            flowables.append(Spacer(1, 4 * mm))
            flowables.append(Paragraph(text_content, styles["heading2"]))
            flowables.append(GoldDivider())
        elif line.startswith('# '):
            text_content = safe_line[2:].strip()
            flowables.append(Paragraph(text_content, styles["heading1"]))
        elif line.startswith('**') and line.endswith('**'):
            text_content = safe_line[2:-2].strip()
            flowables.append(Paragraph(f"<b>{text_content}</b>", styles["body"]))
        elif line.startswith('> '):
            text_content = safe_line[2:].strip()
            flowables.append(Paragraph(text_content, styles["quote"]))
        elif line.startswith('- ') or line.startswith('• '):
            text_content = safe_line[2:].strip()
            bullet_text = f"  • {text_content}"
            flowables.append(Paragraph(bullet_text, styles["body"]))
        elif line.startswith(tuple(f"{i}." for i in range(1, 20))):
            flowables.append(Paragraph(f"  {safe_line}", styles["body"]))
        else:
            # 볼드 마크다운 인라인 처리
            processed = safe_line
            # **text** → <b>text</b>
            import re
            processed = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', processed)
            flowables.append(Paragraph(processed, styles["body"]))

    return flowables


def add_page_numbers(input_path, output_path, start_page=1):
    """PDF에 페이지 번호 추가"""
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        # 임시 캔버스로 페이지 번호 오버레이
        import io
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase import pdfmetrics
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(FONT_MYEONGJO))
        except:
            pass

        page_num = start_page + i
        c.setFont(FONT_MYEONGJO, 8)
        c.setFillColor(HexColor("#999999"))
        c.drawCentredString(PAGE_W / 2, 15 * mm, str(page_num))
        c.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)


def generate_pdf(book_data, output_dir="output"):
    """
    운명책 전체 PDF 생성

    Parameters:
        book_data: interpreter에서 생성한 {core_theme, preface, chapters, client_name}
        output_dir: 출력 디렉토리

    Returns:
        str: 생성된 PDF 파일 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    client_name = book_data.get("client_name", "Client")
    core_theme = book_data.get("core_theme", "")
    safe_name = client_name.replace(" ", "_")

    # 파일 경로
    cover_path = os.path.join(output_dir, f"{safe_name}_cover.pdf")
    body_path = os.path.join(output_dir, f"{safe_name}_body.pdf")
    merged_path = os.path.join(output_dir, f"{safe_name}_운명책.pdf")

    # 출생 정보 (book_data에 포함되어야 함)
    birth_info = book_data.get("birth_info", {})

    # === 1. 표지 생성 ===
    print("📄 표지 생성 중...")
    create_cover_page(cover_path, client_name, core_theme, birth_info)

    # === 2. 본문 생성 ===
    print("📄 본문 생성 중...")
    styles = get_body_styles()

    doc = SimpleDocTemplate(
        body_path,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = []

    # 목차 페이지
    story.append(Paragraph("목 차", styles["heading1"]))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("서문 — 이름과 운명", styles["body"]))
    story.append(Spacer(1, 2 * mm))

    for ch in book_data.get("chapters", []):
        toc_line = f"Chapter {ch['id']}  —  {ch['title']}"
        story.append(Paragraph(toc_line, styles["body"]))
        story.append(Spacer(1, 1.5 * mm))

    story.append(PageBreak())

    # 서문
    story.append(Paragraph("서 문", styles["heading1"]))
    story.append(GoldDivider())
    story.append(Spacer(1, 3 * mm))
    preface_text = book_data.get("preface", "")
    story.extend(text_to_flowables(preface_text, styles))
    story.append(PageBreak())

    # 각 챕터
    for ch in book_data.get("chapters", []):
        # 챕터 타이틀
        story.append(Spacer(1, 30 * mm))
        story.append(Paragraph(f"Chapter {ch['id']}", styles["small"]))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(ch["title"], styles["heading1"]))
        story.append(GoldDivider())
        story.append(Spacer(1, 5 * mm))

        # 챕터 본문
        story.extend(text_to_flowables(ch.get("text", ""), styles))

        # 챕터 끝 구분
        story.append(Spacer(1, 10 * mm))
        story.append(GoldDivider())
        story.append(PageBreak())

    # === 3. 본문 빌드 ===
    doc.build(story)

    # === 4. 표지 + 본문 합치기 ===
    print("📄 PDF 합치기...")
    writer = PdfWriter()

    # 표지
    cover_reader = PdfReader(cover_path)
    for page in cover_reader.pages:
        writer.add_page(page)

    # 본문
    body_reader = PdfReader(body_path)
    for page in body_reader.pages:
        writer.add_page(page)

    with open(merged_path, 'wb') as f:
        writer.write(f)

    # 임시 파일 정리
    try:
        os.remove(cover_path)
        os.remove(body_path)
    except:
        pass

    print(f"\n✅ 운명책 PDF 생성 완료: {merged_path}")
    return merged_path
