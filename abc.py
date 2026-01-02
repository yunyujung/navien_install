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
# 메인 제목 + 버전 표시
# ----------------------------------------
st.markdown(
    """
<h1 style="font-size:30px; text-align:center; margin-bottom:5px; font-weight:900;">
대기오염물질배출시설·특정가스사용시설 판별
</h1>
<p style="text-align:center; font-size:13px; color:gray; margin-top:0;">
버전: <b>v2026-01-02-3 (디버그용)</b>
</p>
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

    # -------------------------------
    # 구분선
    # -------------------------------
    st.write("---")

    # =========================================
    # 🔹 캐스케이드 용량 입력 (최대 가스소비량 기준)
    # =========================================
    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">🔹 캐스케이드 용량 입력 (최대 가스소비량 기준)</h2>
""",
        unsafe_allow_html=True
    )

    # 설비별 용량
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

    # NCB 제외 여부 반영
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

    # ✅ 디버그용 문구 (이게 보여야 '새 코드' 맞음)
    st.markdown(
        """
<p style="color:red; font-weight:700;">
※ 이 문구(빨간 글씨)가 보이면, 특정가스사용시설 탭은 최신 버전 코드가 적용된 상태입니다.
</p>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
<h2 style="font-size:20px; font-weight:700;">특정가스사용시설 판별</h2>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
🔹 **특정가스사용시설 [도시가스사업법 시행규칙 【별표7】]**

1) 산업통상부령으로 정하는 가스사용시설로 월사용 예정량 **2,000㎥ 이상**
   (제1종 보호시설은 **1,000㎥ 이상**)  

2) 월 사용예정량이 기준 미만이라도 해당되는 시설  
   ① 내관 및 부속시설이 바닥·벽 등에 매립 또는 매몰 설치되는 가스사용시설(가정용 제외)  
   ② 많은 사람이 이용하는 시설로서 시·도지사가 안전관리를 위하여 지정한 가스사용시설

---

🔹 **월사용 예정량 산출식 (도시가스사업법 시행규칙 【별표7】)**

- Q = [(A × 240) + (B × 90)] ÷ 11,000 kcal/m³  
- Q : 월사용 예정량 (m³)  
- A(산업용) : 산업용 연소기 명판 가스소비량 합계 (㎉/h)  
- B(비산업용) : 산업용이 아닌 연소기 명판 가스소비량 합계 (㎉/h)  

※ 가정용 연소기 가스소비량은 제외  
※ A 산업용 : 해당 연소기를 통해 직접 제품을 생산, 판매하는 경우 
※ B 비산업용 : 그 외 모든 연소기 → 대부분 현장에 해당 

---

🔹 **제1종 보호시설 [도시가스사업법 시행규칙 【별표1】]**

- 학교·유치원·어린이집·노인시설·청소년수련시설  
- 병원·학원·도서관·전통시장·숙박업·목욕시설  
- 영화관·종교시설·장례식장 등  
- 사실상 독립된 부분의 연면적 1,000㎡ 이상 건축물  
- 공연장·예식장·전시장(수용능력 300명 이상)  
- 사회복지시설 20명 이상 수용  

---
""",
        unsafe_allow_html=True
    )

    st.markdown("### ※ 월사용 예정량 계산 안내")
    st.write("사용량을 입력하면 월사용 예정량을 편리하게 계산할 수 있습니다.")
    st.write("---")

    colA, colB = st.columns([1, 2])

    with colA:
        # 🔹 A/B 라벨 변경 (요청하신 그대로)
        industrial = st.number_input(
            "산업용 (A) kcal/h",
            min_value=0.0,
            step=10000.0,
            format="%.0f",
            value=0.0
        )
        general = st.number_input(
            "비산업용 (B) kcal/h",
            min_value=0.0,
            step=10000.0,
            format="%.0f",
            value=0.0
        )

    with colB:
        # 🔹 안내 문구 변경
        st.write("상업용 : A kcal/h × 240시간 ÷ 11,000 kcal/m³")
        st.write("비산업용 : B kcal/h × 90시간 ÷ 11,000 kcal/m³")

    is_protect = st.checkbox("제1종 보호시설인 경우 (1,000㎥ 이상 기준 적용)")

    # 월사용량 계산
    Q_industrial = industrial * 240 / 11000
    Q_general = general * 90 / 11000
    Q_total = Q_industrial + Q_general

    st.write("---")

    c1, c2, c3 = st.columns(3)
    c1.metric("산업용(A) 사용량", f"{Q_industrial:,.2f} m³/월")
    c2.metric("비산업용(B) 사용량", f"{Q_general:,.2f} m³/월")
    c3.metric("월사용 예정량 합계", f"{Q_total:,.2f} m³/월")

    st.write("---")

    # 특정가스사용시설 기본 판별 기준
    threshold = 1000 if is_protect else 2000
    st.write(f"✔ 적용 기준 : **{threshold:,} m³/월 이상이면 특정가스사용시설 해당**")

    if st.button("특정가스사용시설 판별하기"):
        st.markdown("#### 🔎 판정 결과")

        # ① 특정가스사용시설 여부
        if Q_total >= threshold:
            st.error("👉 기준 이상 : **특정가스사용시설 해당**")
        else:
            st.success("👉 기준 미만 : **특정가스사용시설 아님**")

        # ② 안전관리자 선임 안내
        st.markdown("##### 📌 안전관리자 선임 안내")

        # 4,000 m³/월 초과 → 총괄자 + 책임자
        if Q_total > 4000:
            st.warning(
                "월사용 예정량 합계가 **4,000 m³/월 초과**이므로,  \n"
                "**→ 안전관리총괄자 + 안전관리책임자 선임 필요**"
            )
        else:
            # 제1종 보호시설인 경우 (1,000 ~ 4,000 m³/월 이하)
            if is_protect and Q_total >= 1000:
                st.info(
                    "제1종 보호시설이며 월사용 예정량이 **1,000 ~ 4,000 m³/월 이하** 구간에 해당하므로,  \n"
                    "**→ 안전관리총괄자 선임 필요**"
                )
            # 일반 시설 (2,000 ~ 4,000 m³/월 이하)
            elif (not is_protect) and Q_total >= 2000:
                st.info(
                    "월사용 예정량이 **2,000 ~ 4,000 m³/월 이하** 구간에 해당하므로,  \n"
                    "**→ 안전관리총괄자 선임 필요**"
                )
            # 그 외 구간 → 선임 대상 아님
            else:
                st.success(
                    "월사용 예정량 합계 기준에 따라  \n"
                    "**→ 안전관리총괄자·안전관리책임자 선임 대상 구간에 해당하지 않습니다.**"
                )

