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

    # 모델 용량값
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
<h2 style="font-size:20px; font-weight:700;">특정가스사용시설</h2>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
🔹 **특정가스사용시설**

- 산업통상자원부장관이 정하는 기준에 따라 산정된  
  **월사용 예정량 2,000㎥ 이상(제1종 보호시설은 1,000㎥ 이상)** 가스사용시설  
- 시·도지사가 안전관리를 위하여 필요하다고 인정하여 지정하는 시설  
  *(예: 경기지역 학원, 유치원, 유아원, 놀이방, 어린이집 등)*

---

🔹 **월사용 예정량 산출식  
(도시가스사업법 시행규칙 【별표7】)**

- Q = [(A × 240) + (B × 90)] ÷ 11,000 kcal/m³  
- Q : 월사용 예정량 (m³)  
- A : 산업용 연소기 가스소비량 합계 (kcal/h)  
- B : 비산업용 연소기 가스소비량 합계 (kcal/h)

---

🔹 **제1종 보호시설 예시**
- 학교, 유치원, 보육시설, 어린이집, 놀이방, 어린이놀이터, 노인정  
- 학원, 병원, 도서관, 시장, 공중목욕탕, 호텔, 여관, 청소년수련시설  
- 사실상 독립된 부분의 연면적 1,000㎡ 이상 건축물  
- 극장·교회·공회당 등 수용능력 300인 이상 시설  
- 아동·노인·장애인 등 사회복지시설 20인 이상 수용

---

※ 월사용 예정량 계산 안내  
- 산업용 : (입력값) × 240시간 ÷ 11,000  
- 일반용 : (입력값) × 90시간 ÷ 11,000  
"""
    )

    st.markdown("### 1) 명판 소비량 입력")

    col1, col2 = st.columns(2)
    with col1:
        A = st.number_input(
            "A : 산업용 가스소비량 합계 (kcal/h)",
            min_value=0.0,
            step=10_000.0,
            format="%.0f",
            value=0.0,
        )
    with col2:
        B = st.number_input(
            "B : 일반용 가스소비량 합계 (kcal/h)",
            min_value=0.0,
            step=10_000.0,
            format="%.0f",
            value=0.0,
        )

    st.markdown("### 2) 시설 유형 선택")
    facility_type = st.radio(
        "시설 유형을 선택하세요.",
        ["일반 시설", "제1종 보호시설"],
        horizontal=True,
    )

    if st.button("특정가스사용시설 판별", key="gas_judge"):
        Q_industrial = A * 240 / 11_000
        Q_general = B * 90 / 11_000
        Q_total = Q_industrial + Q_general

        threshold = 1_000 if facility_type == "제1종 보호시설" else 2_000

        st.markdown("#### 🔎 계산 결과")

        st.write(f"- 산업용 사용량 : **{Q_industrial:,.1f} m³/월**")
        st.write(f"- 일반용 사용량 : **{Q_general:,.1f} m³/월**")
        st.write(f"- 월사용 예정량 Q : **{Q_total:,.1f} m³/월**")
        st.write(f"- 적용 기준 : **{threshold:,} m³/월 이상이면 해당**")

        if Q_total >= threshold:
            st.error("→ 기준 이상 : **특정가스사용시설 해당**")
        else:
            st.success("→ 기준 미만 : **특정가스사용시설 아님**")
