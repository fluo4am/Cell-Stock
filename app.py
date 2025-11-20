import streamlit as st
import re

st.set_page_config(page_title="세포 뱅킹 계산 프로그램", page_icon="🧬", layout="wide")

st.title("🧬 세포 뱅킹 계산 프로그램")

# 사이드바 입력
with st.sidebar:
    st.header("입력 정보")
    
    cell_type = st.selectbox(
        "세포 타입",
        ["간세포 (100,000개 × 6웰)", "담관세포 (20,000개 × 6웰)"],
        index=0
    )
    
    total_cells_input = st.text_input(
        "총 세포 수 (X.XX E 6 형식 또는 숫자)",
        placeholder="예: 5.5 E 6 또는 5500000"
    )
    
    suspension_vol = st.number_input(
        "서스펜션 볼륨 (mL)",
        min_value=0.1,
        value=5.0,
        step=0.1
    )
    
    calculate_btn = st.button("계산하기", type="primary", use_container_width=True)

# 세포 수 파싱 함수
def parse_cell_count(input_str):
    # X.XX E 6 형식 파싱
    match = re.match(r'([0-9.]+)\s*[eE]\s*([0-9]+)', input_str.strip())
    if match:
        base = float(match.group(1))
        exponent = int(match.group(2))
        return base * (10 ** exponent)
    else:
        # 일반 숫자
        try:
            return float(input_str.replace(',', ''))
        except:
            return None

# 계산 로직
if calculate_btn:
    total_cells = parse_cell_count(total_cells_input)
    
    if total_cells is None or total_cells <= 0:
        st.error("올바른 세포 수를 입력해주세요.")
    elif suspension_vol <= 0:
        st.error("올바른 서스펜션 볼륨을 입력해주세요.")
    else:
        # 오가노이드 시딩 세포 수
        if "간세포" in cell_type:
            org_cells = 100000 * 6
        else:
            org_cells = 20000 * 6
        
        # 오가노이드 후 남은 세포
        remaining = total_cells - org_cells
        
        if remaining <= 0:
            st.error("세포 수가 부족합니다. 오가노이드 시딩에 필요한 세포 수보다 많아야 합니다.")
        else:
            # 70%는 셀 스탁, 30%는 셀 펠렛
            stock_cells = remaining * 0.7
            pellet_cells = remaining * 0.3
            
            # 셀 스탁 전략: 바이알 수가 5~6개 정도가 되도록 선택
            vials_at_2m = stock_cells / 2000000
            vials_at_1m = stock_cells / 1000000
            vials_at_500k = stock_cells / 500000
            
            # 5~6개 범위 내에 있는 옵션 우선 선택
            if 4 <= vials_at_2m <= 7:
                stock_per_vial = 2000000
            elif 4 <= vials_at_1m <= 7:
                stock_per_vial = 1000000
            elif 4 <= vials_at_500k <= 7:
                stock_per_vial = 500000
            # 범위 밖이면 5.5에 가장 가까운 것 선택
            elif abs(vials_at_2m - 5.5) <= abs(vials_at_1m - 5.5) and abs(vials_at_2m - 5.5) <= abs(vials_at_500k - 5.5):
                stock_per_vial = 2000000
            elif abs(vials_at_1m - 5.5) <= abs(vials_at_500k - 5.5):
                stock_per_vial = 1000000
            else:
                stock_per_vial = 500000
            
            stock_vials = int(stock_cells / stock_per_vial)
            stock_cryo_vol = stock_vials * 1.0
            
            # 셀 펠렛 전략: Stock과 짝 맞추기
            if stock_per_vial == 2000000:
                pellet_per_vial = 1000000
            elif stock_per_vial == 1000000:
                pellet_per_vial = 500000
            else:
                pellet_per_vial = 200000
            
            pellet_vials = int(pellet_cells / pellet_per_vial)
            
            # 부피 계산
            cell_concentration = total_cells / suspension_vol
            org_vol = org_cells / cell_concentration
            stock_vol = stock_cells / cell_concentration
            pellet_vol = pellet_cells / cell_concentration
            pellet_vol_per_tube = pellet_vol / pellet_vials if pellet_vials > 0 else 0
            
            # 결과 출력
            st.success("✅ 계산 완료!")
            
            st.markdown("---")
            st.header("📋 작업 프로토콜")
            
            # 1단계
            st.markdown("### 1️⃣ 서스펜션")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("전체 세포를 서스펜션하세요", f"{suspension_vol:.2f} mL")
            with col2:
                st.metric("세포 농도", f"{cell_concentration:,.0f} cells/mL")
            
            st.markdown("---")
            
            # 2단계
            st.markdown("### 2️⃣ 오가노이드 시딩")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("튜브 1개에 원심분리", f"{org_vol:.2f} mL")
            with col2:
                st.metric("세포 수", f"{org_cells:,}개")
            st.info("6웰에 오가노이드 시딩하세요")
            
            st.markdown("---")
            
            # 3단계
            st.markdown("### 3️⃣ 셀 스탁 (Stock)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("튜브 1개에 원심분리", f"{stock_vol:.2f} mL")
            with col2:
                st.metric("동결액 추가", f"{stock_cryo_vol:.1f} mL")
            with col3:
                st.metric("Cryovial 개수", f"{stock_vials}개")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("바이알당 세포 수", f"{stock_per_vial:,}개")
            with col2:
                st.metric("총 세포 수", f"{int(stock_cells):,}개")
            
            st.markdown("---")
            
            # 4단계
            st.markdown("### 4️⃣ 셀 펠렛 (Pellet)")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("튜브 개수", f"{pellet_vials}개")
            with col2:
                st.metric("튜브당 분주량", f"{pellet_vol_per_tube:.2f} mL")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("바이알당 세포 수", f"{pellet_per_vial:,}개")
            with col2:
                st.metric("총 세포 수", f"{int(pellet_cells):,}개")
            
            st.warning("원심분리 후 상등액은 제거하세요")

# 참고사항
with st.expander("📌 참고사항"):
    st.markdown("""
    - **세포 수 입력**: "5.5 E 6" (=5.5×10⁶) 또는 "1.2 E 7" (=1.2×10⁷) 형식 사용 가능
    - **분배 비율**: 오가노이드 시딩 후 남은 세포의 70%는 Stock, 30%는 Pellet
    - **Stock 전략**: 바이알 수가 5~6개 정도가 되도록 200만개/100만개/50만개 중 자동 선택
    - **Pellet 전략**: Stock과 짝을 맞춤
        - Stock 200만개 → Pellet 100만개
        - Stock 100만개 → Pellet 50만개
        - Stock 50만개 → Pellet 20만개
    """)
