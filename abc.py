# -------------------------------------------------------------------
# 1. 대기오염물질배출시설 탭
# -------------------------------------------------------------------
with TAB1:
    st.subheader("대기오염물질배출시설 판별기준 [대기환경보전법 시행규칙 별표3]")

    st.markdown(
        """
### **보일러·흡수식 냉ᆞ온수기 및 가스열펌프 기준**

가스 또는 경질유만을 연료로 사용하는 시설의 경우에는  

- **시간당 증발량이 2톤 이상**, 또는  
- **시간당 열량이 1,238,000 kcal/h 이상**  

인 보일러와 흡수식 냉·온수기만 「대기오염물질배출시설」에 해당합니다.  

---

### **소형 보일러(환경표지 인증) 제외 기준**

단, 다음에 해당하는 보일러는 **총 규모 산정에서 제외될 수 있습니다.**

- 시간당 증발량 **0.1톤 미만**, 또는  
- 열량 **61,900 kcal/h 미만**인 보일러  
- 「환경기술 및 환경산업 지원법」 제17조에 따른 **환경표지 인증을 받은 보일러**

→ 유역환경청장, 지방환경청장, 수도권대기환경청장 또는 시ᆞ도지사가  
   **주변 환경여건을 고려하여 인정하는 경우에만 제외 가능함**

<br>

### <span style="color:red; font-weight:bold">
※ 환경표지인증을 받은 당사 난방 캐스케이드는 용량산정에서 제외될 수 있으나, 반드시 지자체 확인이 필요함.
</span>
""",
        unsafe_allow_html=True
    )

    st.markdown("### 1) 캐스케이드 용량 입력 (최대 가스소비량 기준)")

    # 모델별 용량
    NPW_CAP = 50_000      # NPW-48K(KD)
    NCB_CAP = 47_500      # NCB790-45LS
    NFB_CAP = 105_500     # NFB790-100LS

    colA, colB = st.columns([1, 1])

    with colA:
        # ① NCB 먼저 + 체크박스 추가
        ncb_count = st.number_input("NCB790-45LS 대수", min_value=0, step=1, value=0)
        ncb_exclude = st.checkbox("용량산정 제외 (지자체 허가 완료)", key="ncb_ex")

        # ② 그다음 NPW
        npw_count = st.number_input("NPW-48K(KD) 대수", min_value=0, step=1, value=0)

        # ③ 마지막 NFB
        nfb_count = st.number_input("NFB790-100LS 대수", min_value=0, step=1, value=0)

    with colB:
        st.markdown(
            f"""
            - NCB790-45LS: **{NCB_CAP:,.0f} kcal/h / 대**  
            - NPW-48K(KD): **{NPW_CAP:,.0f} kcal/h / 대**  
            - NFB790-100LS: **{NFB_CAP:,.0f} kcal/h / 대**
            """
        )

    # 체크박스 체크 시 NCB 용량 제외 처리
    if ncb_exclude:
        NCB_effective = 0
    else:
        NCB_effective = NCB_CAP

    # 계산
    cascade_capacity = (
        npw_count * NPW_CAP +
        ncb_count * NCB_effective +
        nfb_count * NFB_CAP
    )

    st.markdown("### 2) 타 장비 합산 용량 입력")
    other_capacity = st.number_input(
        "타 장비 합산용량 (kcal/h)",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        value=0.0,
    )

    st.markdown(
        """
**타장비 : 가스 보일러(보일러, 온수기), 흡수식 냉온수기, 가스 열펌프**
"""
    )

    THRESHOLD_AIR = 1_238_000  # 법 기준 열량

    if st.button("대기오염물질배출시설 판별", key="air_judge"):
        total_capacity = cascade_capacity + other_capacity

        st.markdown("#### 🔎 계산 결과")

        st.write(f"- 캐스케이드 합산 용량: **{cascade_capacity:,.0f} kcal/h**")
        if ncb_exclude:
            st.info("※ NCB790-45LS는 '용량산정 제외' 처리되었습니다.")

        st.write(f"- 타 장비 합산 용량: **{other_capacity:,.0f} kcal/h**")
        st.write(f"- 총 합산 용량: **{total_capacity:,.0f} kcal/h**")
        st.write(f"- 기준치: **{THRESHOLD_AIR:,.0f} kcal/h**")

        if total_capacity > THRESHOLD_AIR:
            st.error(
                f"✅ 총 용량 **{total_capacity:,.0f} kcal/h → 기준 초과**, "
                "**대기오염물질배출시설에 해당됩니다.**"
            )
        else:
            st.success(
                f"✅ 총 용량 **{total_capacity:,.0f} kcal/h → 기준 이하**, "
                "**대기오염물질배출시설에 해당되지 않습니다.**"
            )
