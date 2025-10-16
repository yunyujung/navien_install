# -*- coding: utf-8 -*-
# KD Navien 설치/교체현장 제출 서류 양식 (단일 페이지) 생성 앱 - 8컷(4x2) 사진 버전

import io
import os
import re
import unicodedata
from datetime import date
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image

# ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ────────────────────────────────────────────────
# 페이지 설정 (제목 변경 반영)
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식",
    layout="wide"
)

# ────────────────────────────────────────────────
# 폰트 등록
# ────────────────────────────────────────────────
def try_register_font() -> str:
    candidates = [
        ("NanumGothic", "NanumGothic.ttf"),
        ("MalgunGothic", "C:\\Windows\\Fonts\\malgun.ttf"),
        ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),
    ]
    for family, path in candidates:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(family, path))
                return family
        except Exception:
            pass
    return "Helvetica"

BASE_FONT = try_register_font()

ss = getSampleStyleSheet()
styles = {
    "title": ParagraphStyle(
        name="title", parent=ss["Heading1"], fontName=BASE_FONT,
        fontSize=16, leading=20, alignment=1, spaceAfter=8
    ),
    "cell": ParagraphStyle(
        name="cell", parent=ss["Normal"], fontName=BASE_FONT,
        fontSize=9, leading=12
    ),
    "small_center": ParagraphStyle(
        name="small_center", parent=ss["Normal"], fontName=BASE_FONT,
        fontSize=8, leading=11, alignment=1
    ),
}

# ────────────────────────────────────────────────
# 유틸
# ────────────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[\\/:*?\"<>|]", "_", name).strip().strip(".")
    return name or "output"

def format_kr_phone(s: str) -> str:
    digits = re.sub(r"\D", "", s)
    if digits.startswith("02") and len(digits) in (9, 10):
        return f"02-{digits[2:-4]}-{digits[-4:]}"
    if digits.startswith(("010", "011", "016", "017", "018", "019")) and len(digits) in (10, 11):
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        else:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    m = re.match(r"^0\d{1,2}", digits)
    if m and len(digits) >= 9:
        area = m.group()
        rest = digits[len(area):]
        return f"{area}-{rest[:-4]}-{rest[-4:]}"
    return s

def validate_capacity(s: str) -> bool:
    return bool(re.search(r"\d", s))

def _pick_image(file_uploader, camera_input) -> Optional[Image.Image]:
    # 우선순위: 촬영 > 앨범선택 (원하시면 반대로 바꿔도 됩니다)
    if camera_input is not None:
        return Image.open(camera_input).convert("RGB")
    if file_uploader is not None:
        return Image.open(file_uploader).convert("RGB")
    return None

def _resize_for_pdf(img: Image.Image, max_px: int = 1400) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_px:
        return img
    if w >= h:
        new_w = max_px
        new_h = int(h * (max_px / w))
    else:
        new_h = max_px
        new_w = int(w * (max_px / h))
    return img.resize((new_w, new_h))

def _pil_to_bytesio(img: Image.Image, quality=85) -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return buf

# ────────────────────────────────────────────────
# PDF 빌더 (제목/8컷 4x2 레이아웃)
# ────────────────────────────────────────────────
def build_pdf(meta: dict, titled_images: List[Tuple[str, Optional[Image.Image]]]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=20, bottomMargin=20,
        leftMargin=20, rightMargin=20,
        title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식"
    )
    story = []

    # 제목 (변경)
    story.append(Paragraph("경동나비엔 가스보일러 설치/교체현장 제출 서류 양식", styles["title"]))
    story.append(Spacer(1, 4))

    # 메타 정보 표
    meta_rows = [
        [Paragraph("현장명", styles["cell"]), Paragraph(meta["site"], styles["cell"])],
        [Paragraph("설치모델", styles["cell"]), Paragraph(meta["model"], styles["cell"])],
        [Paragraph("용량 (kcal/h, kg/h)", styles["cell"]), Paragraph(meta["capacity"], styles["cell"])],
        [Paragraph("급배기방식", styles["cell"]), Paragraph(meta["flue"], styles["cell"])],
        [Paragraph("설치대리점", styles["cell"]), Paragraph(meta["dealer"], styles["cell"])],
        [Paragraph("시공자 (이름/전화번호)", styles["cell"]), Paragraph(meta["installer"], styles["cell"])],
        [Paragraph("시공연월일", styles["cell"]), Paragraph(meta["date"], styles["cell"])],
    ]
    meta_tbl = Table(meta_rows, colWidths=[85, 420])
    meta_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8))

    # 사진 그리드 4x2 (총 8컷)
    PAGE_W, _ = A4
    col_count = 4
    gap_total = 6 * (col_count - 1)  # 약간의 컬럼 간격 6pt
    col_width = (PAGE_W - 40 - gap_total) / col_count

    cells = []
    for title, pil_img in titled_images:
        if pil_img is None:
            cell = Table(
                [[Paragraph("(사진 없음)", styles["small_center"])],
                 [Paragraph(title, styles["small_center"])]],
                colWidths=[col_width]
            )
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
        else:
            img_resized = _resize_for_pdf(pil_img, max_px=1400)
            bio = _pil_to_bytesio(img_resized, quality=85)
            rl_img = RLImage(bio, width=col_width-8)
            rl_img.hAlign = "CENTER"
            cell = Table([[rl_img], [Paragraph(title, styles["small_center"])]], colWidths=[col_width])
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
        cells.append(cell)

    # 8장 고정 (4x2)
    while len(cells) < 8:
        cells.append(Table(
            [[Paragraph("(사진 없음)", styles["small_center"])],
             [Paragraph("추가 사진", styles["small_center"])]],
            colWidths=[col_width]
        ))

    grid_rows = [cells[0:4], cells[4:8]]
    grid_tbl = Table(
        grid_rows, colWidths=[col_width]*4,
        hAlign="CENTER", spaceBefore=0, spaceAfter=0
    )
    grid_tbl.setStyle(TableStyle([
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(grid_tbl)

    doc.build(story)
    return buf.getvalue()

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.markdown("### 경동나비엔 가스보일러 설치/교체현장 제출 서류 양식")
st.info("모바일에서는 각 항목에서 **촬영(카메라 사용)** 또는 **사진/갤러리 선택**으로 업로드 가능합니다.")

# 세션 상태
if "meta_locked" not in st.session_state:
    st.session_state.meta_locked = False
if "meta_data" not in st.session_state:
    st.session_state.meta_data = {}

# 메타정보 폼
with st.form("meta_form_v2", clear_on_submit=False):
    disabled = st.session_state.meta_locked
    colA, colB = st.columns(2)
    with colA:
        site = st.text_input("현장명", value=st.session_state.meta_data.get("site",""), disabled=disabled)
        model = st.text_input("설치모델", value=st.session_state.meta_data.get("model",""), disabled=disabled)
        capacity = st.text_input("용량 (kcal/h, kg/h)", value=st.session_state.meta_data.get("capacity",""), disabled=disabled)
        flue = st.selectbox(
            "급배기방식", ["FF", "FE"],
            index=(["FF","FE"].index(st.session_state.meta_data.get("flue","FF"))
                   if st.session_state.meta_data.get("flue") in ["FF","FE"] else 0),
            disabled=disabled
        )
    with colB:
        dealer = st.text_input("설치대리점", value=st.session_state.meta_data.get("dealer",""), disabled=disabled)
        installer_name = st.text_input("시공자 이름", value=st.session_state.meta_data.get("installer_name",""), disabled=disabled)
        installer_phone = st.text_input("시공자 전화번호", value=st.session_state.meta_data.get("installer_phone",""), disabled=disabled)
        work_date = st.date_input("시공연월일", value=st.session_state.meta_data.get("work_date", date.today()), format="YYYY-MM-DD", disabled=disabled)

    c1, c2 = st.columns([1,1])
    with c1:
        submitted_meta = st.form_submit_button("✅ 기본정보 저장", disabled=disabled)
    with c2:
        unlock = st.form_submit_button("🔓 기본정보 수정", disabled=not disabled)

# 메타 저장/잠금 토글
if submitted_meta:
    installer_phone_fmt = format_kr_phone(installer_phone)

    missing = []
    checks = [
        ("현장명", site.strip()),
        ("설치모델", model.strip()),
        ("용량", capacity.strip()),
        ("설치대리점", dealer.strip()),
        ("시공자 이름", installer_name.strip()),
        ("시공자 전화번호", installer_phone_fmt.strip()),
    ]
    for k, v in checks:
        if not v:
            missing.append(k)
    if not validate_capacity(capacity):
        missing.append("용량(숫자 포함)")

    if missing:
        st.error("필수 항목 누락: " + ", ".join(missing))
    else:
        st.session_state.meta_data = {
            "site": site.strip(),
            "model": model.strip(),
            "capacity": capacity.strip(),
            "flue": flue,
            "dealer": dealer.strip(),
            "installer_name": installer_name.strip(),
            "installer_phone": installer_phone_fmt,
            "work_date": work_date,
        }
        st.session_state.meta_locked = True
        st.success("기본정보를 저장했고 입력칸을 잠갔습니다. 필요하면 '🔓 기본정보 수정'을 눌러 변경하세요.")

if unlock:
    st.session_state.meta_locked = False
    st.info("기본정보를 다시 수정할 수 있습니다.")

# ────────────────────────────────────────────────
# 현장 사진 섹션 (문구/항목 변경, 8개 고정)
# ────────────────────────────────────────────────
st.markdown("#### 현장 사진")

photo_labels = [
    "1. 가스보일러 전면사진",
    "2. 배기통 (실내)",
    "3. 배기통 (실외)",
    "4. 일산화탄소 경보기",
    "5. 시공표지판",
    "6. 명판",
    "7. 플랙시블호스/가스밸브",
    "8. 기타",
]

# 4열 x 2행로 화면 배치(표기는 '현장 사진'만, 3x2 문구 노출 없음)
uploads = []
for row_idx in range(2):
    cols = st.columns(4)
    for col_idx in range(4):
        i = row_idx*4 + col_idx
        with cols[col_idx]:
            st.caption(photo_labels[i])
            cam = st.camera_input("📷 촬영", key=f"cam_{i}")
            fu = st.file_uploader("사진/갤러리 선택", type=["jpg","jpeg","png"], key=f"fu_{i}")
            uploads.append((fu, cam))

# 제출 버튼
submitted = st.button("📄 제출서류 생성")

if submitted:
    if not st.session_state.meta_data:
        st.error("먼저 상단의 '✅ 기본정보 저장'을 눌러 정보를 저장해 주세요.")
    else:
        try:
            images: List[Tuple[str, Optional[Image.Image]]] = []
            for (fu, cam), label in zip(uploads, photo_labels):
                pil_img = _pick_image(fu, cam)
                images.append((label, pil_img))

            md = st.session_state.meta_data
            meta = {
                "site": md["site"],
                "model": md["model"],
                "capacity": md["capacity"],
                "flue": md["flue"],
                "dealer": md["dealer"],
                "installer": f"{md['installer_name']} / {md['installer_phone']}",
                "date": str(md["work_date"]),
            }

            pdf_bytes = build_pdf(meta, images)
            safe_site = sanitize_filename(meta['site'])
            st.success("PDF 생성 완료! 아래 버튼으로 다운로드하세요.")
            st.download_button(
                label="⬇️ 설치·시공 현장 제출 서류(PDF) 다운로드",
                data=pdf_bytes,
                file_name=f"{safe_site}_설치교체현장_제출서류.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error("PDF 생성 중 오류가 발생했습니다. 아래 상세 오류를 확인하세요.")
            st.exception(e)

with st.expander("도움말 / 안내"):
    st.markdown(
        """
- **촬영이 안 뜨면**: 브라우저 *카메라 권한*을 허용해 주세요.
- **한글이 깨질 때**: 실행 폴더에 `NanumGothic.ttf`를 두거나(권장), 윈도우는 자동으로 `맑은 고딕`을 시도합니다.
- **사진 권장 크기**: 1~3MB 내외 (앱에서 자동 리사이즈/압축)
- **전화번호**: 자동으로 `010-1234-5678` 형식으로 정리됩니다.
        """
    )
