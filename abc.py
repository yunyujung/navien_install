import streamlit as st

# ----------------------------------------
# 페이지 설정
# ----------------------------------------
st.set_page_config(
    page_title="대기오염물질배출시설·특정가스사용시설 판별",
    page_icon="🏭",
    layout="centered"
)

# ----------------------------------------
# 메인 제목
# ----------------------------------------
st.markdown(
    """
<h1 style="font-size:30px; text-align:center; margin-bottom:10px; font-weight:900;">
대기오염물질배출시설·특정가스사용시설 판별
</h1>
""",
    unsafe_allow_html=True
)

# ----------------------------------------
# 탭
# ----------------------------------------
TAB1, TAB2 = st.tabs(["대기오염물질배출시설", "특정가스사용시설"])


# =====================================================================
# TAB 1 — 대기오염물질배출시설
# =====================================================================
with TAB1:

    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">
대기오염물질배출시설 판별기준 [대기환경보전법 시행규칙 별표3]
</h2>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
<h3 style="font-size:18px; font-weight:600;">🔹 1) 보일러 + 흡수식 냉ᆞ온수기</h3>

- 시간당 증발량 2톤 이상, 또는 시간당 열량 1,238,000 kcal/h 이상인 보일러와 흡수식 냉·온수기만 해당  
  → 대기오염물질배출시설 해당

<br>

<h3 style="font-size:18px; font-weight:600;">🔹 2) 가스열펌프</h3>
※ 단, 아래에 해당되는 경우 제외됨  

- 가스열펌프에서 배출되는 대기오염물질이 배출허용기준의 30% 미만인 경우  
- 기후에너지환경부장관 고시 기준에 따라 인증받은 저감장치를 부착한 경우  

<br>

<h3 style="font-size:18px; font-weight:700;">
※ 용량산정에서 제외범위 (단, 지자체 인정하는 경우)
</h3>

시간당 증발량이 0.1톤 미만이거나 열량이 61,900 kcal/h 미만인 보일러로서  
「환경기술 및 환경산업 지원법」 제17조에 따른 환경표지 인증 보일러

<br>

<h2 style="color:red; font-weight:700; font-size:18px;">
※ "지자체(환경청 또는 시·도지사)가 인정하는 경우에만" 용량 산정에서 제외 가능
</h2>
""",
        unsafe_allow_html=True
    )

    # =========================================
    # 캐스케이드 용량 입력
    # =========================================
    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">🔹 캐스케이드 용량 입력 (최대 가스소비량 기준)</h2>
""",
        unsafe_allow_html=True
    )

    NPW_CAP = 50_000
    NCB_CAP = 47_500
    NFB_CAP = 105_500

    colA, colB = st.columns([1, 1])

    with colA:
        ncb_count = st.number_input("NCB790-45LS 대수", min_value=0, step=1, value=0)
        ncb_exclude = st.checkbox("용량산정 제외 (지자체 승인 완료)", key="ncb_ex")

        npw_count = st.number_input("NPW-48K(KD) 대수", min_value=0, step=1, value=0)
        nfb_count = st.number_input("NFB790-100LS 대수", min_value=0, step=1, value=0)

    with colB:
        st.markdown(
            f"""
- NCB790-45LS : **{NCB_CAP:,} kcal/h / 대**  
- NPW-48K(KD) : **{NPW_CAP:,} kcal/h / 대**  
- NFB790-100LS : **{NFB_CAP:,} kcal/h / 대**  
"""
        )

    NCB_effective = 0 if ncb_exclude else NCB_CAP

    cascade_capacity = (
        ncb_count * NCB_effective +
        npw_count * NPW_CAP +
        nfb_count * NFB_CAP
    )

    # =========================================
    # 타 장비 입력
    # =========================================
    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">🔹 타 장비 합산 용량 입력</h2>
""",
        unsafe_allow_html=True
    )

    other_capacity = st.number_input(
        "타 장비 합산용량 (kcal/h)",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        value=0.0,
    )

    THRESHOLD_AIR = 1_238_000

    if st.button("대기오염물질배출시설 판별", key="air_judge"):
        total_capacity = cascade_capacity + other_capacity

        st.markdown("#### 🔎 계산 결과")
        st.write(f"- 캐스케이드 합산 용량 : **{cascade_capacity:,} kcal/h**")
        if ncb_exclude:
            st.info("※ NCB790-45LS : 용량산정 제외 처리됨 (지자체 승인 완료)")
        st.write(f"- 타 장비 합산 용량 : **{other_capacity:,} kcal/h**")
        st.write(f"- 총 용량 : **{total_capacity:,} kcal/h**")
        st.write(f"- 기준치 : **{THRESHOLD_AIR:,} kcal/h**")

        if total_capacity >= THRESHOLD_AIR:
            st.error("→ 기준 이상 : **대기오염물질배출시설 해당**")
        else:
            st.success("→ 기준 미만 : **대기오염물질배출시설 아님**")



# =====================================================================
# TAB 2 — 특정가스사용시설
# =====================================================================
with TAB2:

    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">특정가스사용시설 판별</h2>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
🔹 <b>특정가스사용시설 [도시가스사업법 시행규칙 【별표7】]</b>

1) 산업통상부령으로 정하는 가스사용시설로서  
&nbsp;&nbsp;&nbsp;&nbsp;→ <b>월사용 예정량 2,000㎥ 이상(제1종 보호시설은 1,000㎥ 이상)</b>

2) 월 사용예정량이 기준 미만이더라도 해당되는 경우  
&nbsp;&nbsp;&nbsp;&nbsp;① 내관 및 부속시설이 매립·매몰 설치되는 가스사용시설(가정용 제외)  
&nbsp;&nbsp;&nbsp;&nbsp;② 많은 사람이 이용하는 시설로서 시·도지사가 지정한 시설  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(학원·유치원·유아원·놀이방·어린이집 등)

---

🔹 <b>월사용 예정량 산출식  
(도시가스사업법 시행규칙 【별표7】)</b>

- <b>Q = [(A × 240) + (B × 90)] ÷ 11,000 kcal/m³</b><br>
- Q : 월사용 예정량 (m³)<br>
- A : 산업용으로 사용하는 연소기의 명판에 기재된 가스소비량의 합계 (kcal/h)<br>
- B : 산업용이 아닌 연소기의 명판에 기재된 가스소비량의 합계 (kcal/h)<br>
※ 단, 가정용으로 사용하는 연소 기의 가스소비량은 합산 대상에서 제외 
※ 산업용 : 판매를 목적으로 하는 제품을 생산하는데 사용되는 가스 연소기 
※ 비산업용 : 산업용 이 외의 모든 가스 연소기

---

🔹 <b>제1종 보호시설 [도시가스사업법 시행규칙 【별표1】]</b>

- 학교, 유치원, 어린이집, 어린이놀이시설, 경로당, 청소년수련시설  
- 병원 및 의료기관, 학원, 도서관, 전통시장, 숙박업, 목욕시설  
- 영화상영관, 종교시설, 장례식장 등  
- 사실상 독립된 부분 연면적 1,000㎡ 이상 건축물  
- 공연장·예식장·전시장 등 수용능력 300인 이상  
- 사회복지시설 20인 이상 수용

---
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
### ※ 월사용 예정량 계산 안내
사용량을 입력하면 월사용 예정량을 편리하게 계산할 수 있습니다.
"""
    )

    st.write("---")

    # ================= 입력 영역 =================
    colA, colB = st.columns([1, 2])

    with colA:
        industrial = st.number_input(
            "상업용 (A) kcal/h",
            min_value=0.0,
            step=1000.0,
            format="%.0f",
            value=0.0
        )
        general = st.number_input(
            "일반용 (B) kcal/h",
            min_value=0.0,
            step=1000.0,
            format="%.0f",
            value=0.0
        )

    with colB:
        st.write("상업용 : kcal/h × 240시간 ÷ 11,000 kcal/m³")
        st.write("일반용 : kcal/h × 90시간 ÷ 11,000 kcal/m³")

    # ================= 계산 =================
    Q_industrial = industrial * 240 / 11000
    Q_general = general * 90 / 11000
    Q_total = Q_industrial + Q_general

    st.write("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("상업용 사용량", f"{Q_industrial:,.2f} m³/월")
    with c2:
        st.metric("일반용 사용량", f"{Q_general:,.2f} m³/월")
    with c3:
        st.metric("월사용 예정량 합계", f"{Q_total:,.2f} m³/월")

    st.write("---")

    # ================= 시설 유형 선택 =================
    st.markdown("### 시설 유형 선택")
    facility_type = st.radio(
        "시설 유형을 선택하세요.",
        ["일반 시설", "제1종 보호시설"],
        horizontal=True,
    )

    threshold = 1000 if facility_type == "제1종 보호시설" else 2000
    st.write(f"✔ 적용 기준 : **{threshold:,} m³/월 이상이면 특정가스사용시설 해당**")

    # ================= 판정 =================
    if st.button("특정가스사용시설 판별하기"):
        st.markdown("#### 🔎 판정 결과")

        if Q_total >= threshold:
            st.error("👉 기준 이상 : **특정가스사용시설 해당**")
        else:
            st.success("👉 기준 미만 : **특정가스사용시설 아님**")

