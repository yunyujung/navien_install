# -*- coding: utf-8 -*-
# KD Navien 설치/교체현장 제출 서류 양식 (1페이지, 8컷 4x2) - 파일 업로드 전용(카메라 제거, 버튼 문구: 사진/앨범)

import io, os, re, unicodedata
from pathlib import Path
from datetime import date
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage
)
    # noqa
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식",
    layout="wide"
)

# ─────────────────────────────────────────
# 폰트 등록 (안정화: 실제 폰트명 반환)
# ─────────────────────────────────────────
def register_korean_font_stable() -> Tuple[str, str, bool]:
    fonts_dir = (Path(__file__).parent if "__file__" in globals() else Path(os.getcwd())) / "fonts"
    reg_candidates  = ["NanumGothic.ttf", "NanumGothic-Regular.ttf", "NanumGothic.ttf.ttf"]
    bold_candidates = ["NanumGothicBold.ttf", "NanumGothic-Bold.ttf", "NanumGothicBold.ttf.ttf"]

    reg_path  = next((fonts_dir / n for n in reg_candidates  if (fonts_dir / n).exists()), None)
    bold_path = next((fonts_dir / n for n in bold_candidates if (fonts_dir / n).exists()), None)

    if reg_path and bold_path:
        try:
            REG_NAME  = "KFont-Regular"
            BOLD_NAME = "KFont-Bold"
            pdfmetrics.registerFont(TTFont(REG_NAME,  str(reg_path)))
            pdfmetrics.registerFont(TTFont(BOLD_NAME, str(bold_path)))
            return REG_NAME, BOLD_NAME, True
        except Exception as e:
            st.error(f"폰트 등록 오류: {e}")
            return "Helvetica", "Helvetica-Bold", False
    return "Helvetica", "Helvetica-Bold", False

REG_FONT, BOLD_FONT, FONT_OK = register_korean_font_stable()
if not FONT_OK:
    st.error("❗ PDF 한글 폰트를 찾지 못했습니다. 'fonts' 폴더에 "
             "NanumGothic.ttf / NanumGothicBold.ttf (또는 -Regular/-Bold, .ttf.ttf) 파일을 넣어주세요.")
    st.stop()

# ─────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────
ss = getSampleStyleSheet()
styles = {
    "title": ParagraphStyle(
        name="title", parent=ss["Heading1"], fontName=REG_FONT,
        fontSize=16, leading=20, alignment=1, spaceAfter=8
    ),
    "cell": ParagraphStyle(
        name="cell", parent=ss["Normal"], fontName=REG_FONT,
        fontSize=9, leading=12
    ),
    "photo_caption": ParagraphStyle(
        name="photo_caption", parent=ss["Normal"], fontName=BOLD_FONT,
        fontSize=11, leading=14, alignment=1
    ),
    "small_center": ParagraphStyle(
        name="small_center", parent=ss["Normal"], fontName=REG_FONT,
        fontSize=8, leading=11, alignment=1
    ),
}

# ─────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip().strip(".")
    return name or "output"

def format_kr_phone(s: str) -> str:
    digits = re.sub(r"\D", "", s)
    if digits.startswith("02") and len(digits) in (9, 10):
        return f"02-{digits[2:-4]}-{digits[-4:]}"
    if digits.startswith(("010","011","016","017","018","019")) and len(digits) in (10, 11):
        return f"{digits[:3]}-{digits[3:-4]}-{digits[-4:]}"
    m = re.match(r"^0\d{1,2}", digits)
    if m and len(digits) >= 9:
        area = m.group(); rest = digits[len(area):]
        return f"{area}-{rest[:-4]}-{rest[-4:]}"
    return s

def validate_has_digit(s: str) -> bool:
    return bool(re.search(r"\d", s))

def _resize_for_pdf(img: Image.Image, max_px: int = 1400) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_px:
        return img
    if w >= h:
        return img.resize((max_px, int(h * (max_px / w))))
    else:
        return img.resize((int(w * (max_px / h)), max_px))

def _pil_to_bytesio(img: Image.Image, quality=85) -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return buf

def enforce_aspect_pad(img: Image.Image, target_ratio: float = 4/3) -> Image.Image:
    w, h = img.size
    cur = w / h
    if abs(cur - target_ratio) < 1e-3:
        return img
    if cur > target_ratio:
        new_h = int(round(w / target_ratio)); new_w = w
    else:
        new_w = int(round(h * target_ratio)); new_h = h
    canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    canvas.paste(img, ((new_w - w)//2, (new_h - h)//2))
    return canvas

# ─────────────────────────────────────────
# PDF 빌더
# ─────────────────────────────────────────
def build_pdf(meta: dict, titled_images: List[Tuple[str, Optional[Image.Image]]]) -> bytes:
    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MLR, MTB = 20, 20

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=MTB, bottomMargin=MTB, leftMargin=MLR, rightMargin=MLR,
        title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식"
    )
    story = []
    story.append(Paragraph("경동나비엔 가스보일러 설치/교체현장 제출 서류 양식", styles["title"]))
    story.append(Spacer(1, 4))

    rows = [
        [Paragraph("설치장소(주소)", styles["cell"]), Paragraph(meta["site_addr"], styles["cell"])],
        [Paragraph("모델명", styles["cell"]), Paragraph(meta["model_name"], styles["cell"])],
        [Paragraph("최대가스소비량(kcal/h)", styles["cell"]), Paragraph(meta["max_gas"], styles["cell"])],
        [Paragraph("급배기방식", styles["cell"]), Paragraph(meta["flue"], styles["cell"])],
        [Paragraph("설치업체명", styles["cell"]), Paragraph(meta["installer_company"], styles["cell"])],
        [Paragraph("시공자 (이름/연락처)", styles["cell"]), Paragraph(meta["installer"], styles["cell"])],
        [Paragraph("시공연월일", styles["cell"]), Paragraph(meta["date"], styles["cell"])],
    ]
    tbl = Table(rows, colWidths=[105, PAGE_W - 2*MLR - 105])
    tbl.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.9, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(tbl); story.append(Spacer(1, 8))

    col_count = 4
    usable_w = PAGE_W - 2*MLR
    col_w = (usable_w - 6*(col_count-1)) / col_count
    ROW_H, CAP_H = 240, 28
    IMG_MAX_H = ROW_H - CAP_H - 8
    IMG_MAX_W = col_w - 8

    cells = []
    for title, pil_img in titled_images:
        if pil_img is not None:
            pil_img = enforce_aspect_pad(pil_img, 4/3)
            bio = _pil_to_bytesio(_resize_for_pdf(pil_img, 1400), quality=85)
            tw = IMG_MAX_W; th = tw * 3/4
            if th > IMG_MAX_H:
                th = IMG_MAX_H; tw = th * 4/3
            rim = RLImage(bio, width=tw, height=th); rim.hAlign = "CENTER"
            cell = Table([[rim], [Paragraph(title, styles["photo_caption"])]],
                         colWidths=[col_w], rowHeights=[ROW_H-CAP_H, CAP_H])
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))
        else:
            cell = Table([[Paragraph("(사진 없음)", styles["small_center"])],
                          [Paragraph(title, styles["photo_caption"])]],
                         colWidths=[col_w], rowHeights=[ROW_H-CAP_H, CAP_H])
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))
        cells.append(cell)

    while len(cells) < 8:
        cells.append(Table([[Paragraph("(사진 없음)", styles["small_center"])],
                            [Paragraph("추가 사진", styles["photo_caption"])]],
                           colWidths=[col_w], rowHeights=[ROW_H-CAP_H, CAP_H]))

    grid = Table([cells[0:4], cells[4:8]],
                 colWidths=[col_w]*4, rowHeights=[ROW_H, ROW_H],
                 hAlign="CENTER")
    grid.setStyle(TableStyle([
        ("LEFTPADDING",(0,0),(-1,-1),2),
        ("RIGHTPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    story.append(grid)
    doc.build(story)
    return buf.getvalue()

# ─────────────────────────────────────────
# UI
# ─────────────────────────────────────────
st.markdown("### 경동나비엔 가스보일러 설치/교체현장 제출 서류 양식")
st.info("모바일/PC에서 **사진/앨범** 버튼만 사용합니다. 모든 사진은 4:3 비율로 자동 보정됩니다.")

if "meta_locked" not in st.session_state:
    st.session_state.meta_locked = False
if "meta_data" not in st.session_state:
    st.session_state.meta_data = {}

# 메타 정보
with st.form("meta", clear_on_submit=False):
    disabled = st.session_state.meta_locked
    c1, c2 = st.columns(2)
    with c1:
        site_addr  = st.text_input("설치장소(주소)", value=st.session_state.meta_data.get("site_addr",""), disabled=disabled)
        model_name = st.text_input("모델명", value=st.session_state.meta_data.get("model_name",""), disabled=disabled)
        max_gas    = st.text_input("최대가스소비량(kcal/h)", value=st.session_state.meta_data.get("max_gas",""), disabled=disabled)
        flue       = st.selectbox("급배기방식", ["FF","FE"],
                                  index=(["FF","FE"].index(st.session_state.meta_data.get("flue","FF"))
                                         if st.session_state.meta_data.get("flue") in ["FF","FE"] else 0),
                                  disabled=disabled)
    with c2:
        installer_company = st.text_input("설치업체명", value=st.session_state.meta_data.get("installer_company",""), disabled=disabled)
        installer_name    = st.text_input("시공자 이름", value=st.session_state.meta_data.get("installer_name",""), disabled=disabled)
        installer_phone   = st.text_input("시공자 연락처", value=st.session_state.meta_data.get("installer_phone",""), disabled=disabled)
        work_date         = st.date_input("시공연월일", value=st.session_state.meta_data.get("work_date", date.today()),
                                          format="YYYY-MM-DD", disabled=disabled)
    b1, b2 = st.columns(2)
    with b1:
        submitted_meta = st.form_submit_button("✅ 기본정보 저장", disabled=disabled)
    with b2:
        unlock = st.form_submit_button("🔓 기본정보 수정", disabled=not disabled)

if submitted_meta:
    installer_phone_fmt = format_kr_phone(installer_phone)
    missing = []
    for k, v in [
        ("설치장소(주소)", site_addr.strip()),
        ("모델명", model_name.strip()),
        ("최대가스소비량(kcal/h)", max_gas.strip()),
        ("설치업체명", installer_company.strip()),
        ("시공자 이름", installer_name.strip()),
        ("시공자 연락처", installer_phone_fmt.strip()),
    ]:
        if not v:
            missing.append(k)
    if not validate_has_digit(max_gas):
        missing.append("최대가스소비량(숫자 포함)")

    if missing:
        st.error("필수 항목 누락: " + ", ".join(missing))
    else:
        st.session_state.meta_data = {
            "site_addr": site_addr.strip(),
            "model_name": model_name.strip(),
            "max_gas": max_gas.strip(),
            "flue": flue,
            "installer_company": installer_company.strip(),
            "installer_name": installer_name.strip(),
            "installer_phone": installer_phone_fmt,
            "work_date": work_date,
        }
        st.session_state.meta_locked = True
        st.success("저장 완료! 입력칸을 잠궜습니다. '🔓 기본정보 수정'으로 다시 수정할 수 있어요.")

if "unlock" in locals() and unlock:
    st.session_state.meta_locked = False
    st.info("기본정보를 다시 수정할 수 있습니다.")

# 현장 사진 (파일 업로드만)
st.markdown("#### 현장 사진")

labels = [
    "1. 가스보일러 전면사진",
    "2. 배기통(실내)",
    "3. 배기통(실외)",
    "4. 일산화탄소 경보기",
    "5. 시공표지판",
    "6. 명판",
    "7. 플랙시블호스/가스밸브",
    "8. 기타",
]

uploads: list[Optional[Image.Image]] = [None] * 8
for r in range(2):
    cols = st.columns(4)
    for c in range(4):
        i = r*4 + c
        with cols[c]:
            st.markdown(f"**{labels[i]}**")
            fu = st.file_uploader("사진/앨범", type=["jpg","jpeg","png"], key=f"fu_{i}")
            if fu is not None:
                img = Image.open(fu).convert("RGB")
                uploads[i] = enforce_aspect_pad(img, 4/3)
                st.image(uploads[i], use_container_width=True)

# PDF 생성
if st.button("📄 제출서류 생성"):
    if not st.session_state.meta_data:
        st.error("먼저 '✅ 기본정보 저장'을 눌러 주세요.")
    else:
        try:
            images: List[Tuple[str, Optional[Image.Image]]] = [(labels[i], uploads[i]) for i in range(8)]
            md = st.session_state.meta_data
            meta = {
                "site_addr": md["site_addr"],
                "model_name": md["model_name"],
                "max_gas": md["max_gas"],
                "flue": md["flue"],
                "installer_company": md["installer_company"],
                "installer": f"{md['installer_name']} / {md['installer_phone']}",
                "date": str(md["work_date"]),
            }
            pdf_bytes = build_pdf(meta, images)
            safe_site = sanitize_filename(md["site_addr"])
            st.success("PDF 생성 완료! 아래 버튼으로 다운로드하세요.")
            st.download_button(
                "⬇️ 설치·시공 현장 제출 서류(PDF) 다운로드",
                data=pdf_bytes,
                file_name=f"{safe_site}_설치교체현장_제출서류.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error("PDF 생성 중 오류가 발생했습니다.")
            st.exception(e)

with st.expander("도움말 / 안내"):
    st.markdown("""
- **한글 깨짐**: `fonts` 폴더에 `NanumGothic.ttf` + `NanumGothicBold.ttf`(또는 이름 변형)가 있어야 하며, 이 앱은 자동으로 감지해 등록합니다.
- **사진 업로드**: **사진/앨범** 버튼만 사용합니다. (카메라 입력 없음)
- **사진 비율**: 모든 사진은 자동으로 4:3으로 패딩 보정됩니다.
- **연락처**: `010-1234-5678` 형태로 자동 정리됩니다.
""")
