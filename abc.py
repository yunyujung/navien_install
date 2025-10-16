# -*- coding: utf-8 -*-
# KD Navien 설치/교체현장 제출 서류 양식 (단일 페이지) 생성 앱 - 8컷(4x2) 사진 버전

import io
import os
import re
import unicodedata
from datetime import date
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image, ImageOps

# ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ────────────────────────────────────────────────
# 페이지 설정 (제목 반영)
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식",
    layout="wide"
)

# ────────────────────────────────────────────────
# 폰트 등록 (한글 깨짐 방지)
# ────────────────────────────────────────────────
def try_register_font() -> Tuple[str, bool]:
    """
    사용 가능 폰트 등록 후 (font_name, is_custom) 반환
    is_custom: True면 한글 TTF 임베드 성공, False면 Helvetica 대체
    """
    candidates = [
        ("NanumGothic", "NanumGothic.ttf"),                       # 실행 폴더 최우선
        ("MalgunGothic", "C:\\Windows\\Fonts\\malgun.ttf"),       # 윈도우 경로 1
        ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),          # 윈도우 경로 2
    ]
    for family, path in candidates:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(family, path))
                # 본문/볼드/이탤릭 등 패밀리 매핑(볼드/이탤릭 없으면 동일 폰트로 매핑)
                from reportlab.pdfbase.ttfonts import TTFont
                try:
                    pdfmetrics.registerFont(TTFont(f"{family}-Bold", path))
                    pdfmetrics.registerFont(TTFont(f"{family}-Italic", path))
                    pdfmetrics.registerFont(TTFont(f"{family}-BoldItalic", path))
                except Exception:
                    pass
                return family, True
        except Exception:
            pass
    return "Helvetica", False

BASE_FONT, FONT_OK = try_register_font()
if not FONT_OK:
    st.warning("⚠️ 한글 폰트를 임베드하지 못했습니다. 실행 폴더에 `NanumGothic.ttf`를 두면 PDF 한글이 깨지지 않습니다.")

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
    # 우선순위: 촬영 > 앨범선택
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

def enforce_aspect_pad(img: Image.Image, target_ratio: float = 4/3) -> Image.Image:
    """
    이미지의 비율을 target_ratio(기본 4:3)에 맞추기 위해 여백(PAD)을 추가.
    중앙 정렬, 배경은 흰색.
    """
    w, h = img.size
    cur_ratio = w / h
    if abs(cur_ratio - target_ratio) < 1e-3:
        return img

    # 새 캔버스 크기 계산 (둘 중 큰 쪽을 확장)
    if cur_ratio > target_ratio:
        # 가로가 더 길다 -> 세로 확장
        new_h = int(round(w / target_ratio))
        new_w = w
    else:
        # 세로가 더 길다 -> 가로 확장
        new_w = int(round(h * target_ratio))
        new_h = h

    canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    paste_x = (new_w - w) // 2
    paste_y = (new_h - h) // 2
    canvas.paste(img, (paste_x, paste_y))
    return canvas

# ────────────────────────────────────────────────
# PDF 빌더 (제목/8컷 4x2 레이아웃, 1페이지 고정)
# ────────────────────────────────────────────────
def build_pdf(meta: dict, titled_images: List[Tuple[str, Optional[Image.Image]]]) -> bytes:
    buf = io.BytesIO()
    # A4: 595 x 842 pt
    PAGE_W, PAGE_H = A4
    LEFT_RIGHT_MARGIN = 20
    TOP_BOTTOM_MARGIN = 20

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=TOP_BOTTOM_MARGIN, bottomMargin=TOP_BOTTOM_MARGIN,
        leftMargin=LEFT_RIGHT_MARGIN, rightMargin=LEFT_RIGHT_MARGIN,
        title="경동나비엔 가스보일러 설치/교체현장 제출 서류 양식"
    )
    story = []

    # 제목
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
    meta_tbl = Table(meta_rows, colWidths=[85, PAGE_W - 2*LEFT_RIGHT_MARGIN - 85])
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

    # ── 사진 그리드 4x2 (총 8컷), 1페이지 고정 레이아웃 ──
    col_count = 4
    # 표 전체 폭: 페이지 폭 - 좌우 마진
    usable_width = PAGE_W - 2*LEFT_RIGHT_MARGIN
    gap_total = 6 * (col_count - 1)  # 컬럼 간격(테이블 내부 패딩으로 대체, 실제 gap 없이 colWidth만 주어도 안정)
    col_width = (usable_width - gap_total) / col_count

    # 1페이지에 안정적으로 들어가도록 행 높이/캡션 높이 지정
    ROW_HEIGHT = 240   # 각 행 총 높이
    CAPTION_HEIGHT = 24
    IMAGE_MAX_H = ROW_HEIGHT - CAPTION_HEIGHT - 8  # 상하 패딩 감안
    IMAGE_MAX_W = col_width - 8

    cells = []
    for title, pil_img in titled_images:
        if pil_img is not None:
            # 4:3 비율 맞추기(패딩), 리사이즈
            pil_img = enforce_aspect_pad(pil_img, 4/3)
            img_resized = _resize_for_pdf(pil_img, max_px=1400)
            bio = _pil_to_bytesio(img_resized, quality=85)

            # RLImage 생성 후 4:3 유지한 채 셀 안으로 맞추기
            # 4:3 기준 크기 계산
            # (우선 가로 기준으로 맞추고, 높이를 초과하면 높이 기준으로 재조정)
            target_w = IMAGE_MAX_W
            target_h = target_w * 3 / 4  # 4:3
            if target_h > IMAGE_MAX_H:
                target_h = IMAGE_MAX_H
                target_w = target_h * 4 / 3

            rl_img = RLImage(bio, width=target_w, height=target_h)
            rl_img.hAlign = "CENTER"

            cell = Table(
                [[rl_img],
                 [Paragraph(title, styles["small_center"])]],
                colWidths=[col_width],
                rowHeights=[ROW_HEIGHT - CAPTION_HEIGHT, CAPTION_HEIGHT]
            )
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("TOPPADDING", (0,0), (-1,0), 2),
                ("BOTTOMPADDING", (0,0), (-1,0), 2),
                ("TOPPADDING", (0,1), (-1,1), 0),
                ("BOTTOMPADDING", (0,1), (-1,1), 0),
            ]))
        else:
            cell = Table(
                [[Paragraph("(사진 없음)", styles["small_center"])],
                 [Paragraph(title, styles["small_center"])]],
                colWidths=[col_width],
                rowHeights=[ROW_HEIGHT - CAPTION_HEIGHT, CAPTION_HEIGHT]
            )
            cell.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 0.3, colors.grey),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))
        cells.append(cell)

    # 부족하면 공백 셀 채우기
    while len(cells) < 8:
        cells.append(
            Table(
                [[Paragraph("(사진 없음)", styles["small_center"])],
                 [Paragraph("추가 사진", styles["small_center"])]],
                colWidths=[col_width],
                rowHeights=[ROW_HEIGHT - CAPTION_HEIGHT, CAPTION_HEIGHT]
            )
        )

    grid_rows = [cells[0:4], cells[4:8]]
    grid_tbl = Table(
        grid_rows,
        colWidths=[col_width]*4,
        rowHeights=[ROW_HEIGHT, ROW_HEIGHT],
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

    # 1페이지 내에 수렴하도록 상단 요소 크기를 튜닝했으므로 추가 제약 없이 build
    doc.build(story)
    return buf.getvalue()

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.markdown("### 경동나비엔 가스보일러 설치/교체현장 제출 서류 양식")
st.info("모바일에서는 각 항목에서 **촬영(카메라 사용)** 또는 **사진/갤러리 선택**으로 업로드 가능합니다. 모든 사진은 4:3 비율로 자동 보정됩니다.")

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
# 현장 사진 섹션 (8개 고정, 4:3 자동 보정)
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
                if pil_img is not None:
                    # 4:3 비율로 패딩 보정
                    pil_img = enforce_aspect_pad(pil_img, 4/3)
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
- **촬영 버튼이 안 보이면**: 브라우저 *카메라 권한*을 허용해 주세요.
- **한글이 깨질 때**: 실행 폴더에 `NanumGothic.ttf`를 두면 PDF에 폰트가 임베드되어 해결됩니다(윈도우는 자동으로 `맑은 고딕` 시도).
- **사진 비율**: 모든 사진은 자동으로 **4:3 비율(패딩 방식)** 로 맞춰집니다.
- **사진 권장 크기**: 1~3MB 내외 (앱에서 자동 리사이즈/압축)
- **전화번호**: 자동으로 `010-1234-5678` 형식으로 정리됩니다.
        """
    )
