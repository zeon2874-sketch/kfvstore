import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from preprocessor import load_and_preprocess_data
import koreanize_matplotlib

# 페이지 설정
st.set_page_config(
    page_title="한국민속촌 스토어 월간 성과 대시보드",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (프리미엄 디자인)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1e1e1e;
        font-family: 'Inter', sans-serif;
    }
    .st-emotion-cache-1kyxreq {
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드 (캐싱 적용)
@st.cache_data
def get_data():
    # 로컬 경로 대신 현재 작업 디렉토리 기준의 상대 경로 사용 (배포 시 필수)
    data_dir = os.path.join(os.getcwd(), "data")
    return load_and_preprocess_data(data_dir)

data = get_data()

# 사이드바 설정
st.sidebar.title("🏮 대시보드 필터")
months = sorted(data['master']['월'].unique(), reverse=True)
selected_month = st.sidebar.selectbox("조회 월 선택", months)

# 페이지 선택
page = st.sidebar.radio("페이지 이동", ["📈 경영 KPI 요약", "📦 상품/업체 분석"])

# 선택한 월의 데이터 필터링
master_month = data['master'][data['master']['월'] == selected_month].iloc[0]
target_month = data['monthly_targets'][data['monthly_targets']['월'] == selected_month]
if not target_month.empty:
    target_month = target_month.iloc[0]
else:
    target_month = None

# 전월 데이터 필터링 (증감률 계산용)
prev_month_idx = months.index(selected_month) + 1
if prev_month_idx < len(months):
    prev_month_name = months[prev_month_idx]
    prev_master = data['master'][data['master']['월'] == prev_month_name].iloc[0]
else:
    prev_master = None

# --- [페이지 1: 경영 KPI 요약] ---
if page == "📈 경영 KPI 요약":
    st.title(f"📊 {selected_month} 경영 성과 리포트")
    
    # 1. 상단 KPI 카드
    cols = st.columns(4)
    
    # 매출
    rev = master_month['매출']
    rev_delta = f"{((rev / prev_master['매출']) - 1) * 100:.1f}%" if prev_master is not None else None
    cols[0].metric("총 매출", f"{rev:,.0f}원", delta=rev_delta)
    
    # 영업이익
    op = master_month['영업이익']
    op_delta = f"{((op - prev_master['영업이익']) / abs(prev_master['영업이익'])) * 100:.1f}%" if prev_master is not None and prev_master['영업이익'] != 0 else None
    cols[1].metric("영업이익", f"{op:,.0f}원", delta=op_delta)
    
    # 회원수 (누적)
    mem = master_month['누적 회원수']
    mem_delta = f"+{master_month['회원수']:,.0f}명 (신규)"
    cols[2].metric("누적 회원수", f"{mem:,.0f}명", delta=mem_delta)
    
    # MAU
    mau = master_month['MAU']
    mau_delta = f"{((mau / prev_master['MAU']) - 1) * 100:.1f}%" if prev_master is not None else None
    cols[3].metric("MAU", f"{mau:,.0f}명", delta=mau_delta)
    
    st.markdown("---")
    
    # 2. 목표 달성률 KPI
    cols2 = st.columns(2)
    if target_month is not None:
        # 매출 달성률
        rev_target = target_month['목표 매출']
        rev_ratio = (rev / rev_target) * 100 if rev_target > 0 else 0
        
        fig_rev = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = rev_ratio,
            title = {'text': "매출 목표 달성률(%)"},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': "#ff6b6b"},
                'steps': [
                    {'range': [0, 80], 'color': "#f1f1f1"},
                    {'range': [80, 100], 'color': "#ffdada"},
                    {'range': [100, 150], 'color': "#ffc5c5"}]
            }
        ))
        fig_rev.update_layout(height=300)
        cols2[0].plotly_chart(fig_rev, use_container_width=True)
        
        # 회원 목표 달성률
        mem_target = target_month['목표 회원']
        new_mem = master_month['회원수']
        mem_ratio = (new_mem / mem_target) * 100 if mem_target > 0 else 0
        
        fig_mem = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = mem_ratio,
            title = {'text': "신규 회원 목표 달성률(%)"},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': "#4dabf7"},
                'steps': [
                    {'range': [0, 80], 'color': "#f1f1f1"},
                    {'range': [80, 100], 'color': "#d0ebff"},
                    {'range': [100, 150], 'color': "#a5d8ff"}]
            }
        ))
        fig_mem.update_layout(height=300)
        cols2[1].plotly_chart(fig_mem, use_container_width=True)
        
    # 3. 추이 차트
    st.subheader("📈 월별 주요 지표 추이")
    
    # 매출 & 영업이익 추이
    df_trend = data['master'].copy().sort_values('월')
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=df_trend['월'], y=df_trend['매출'], name="매출", marker_color="#ff6b6b"))
    fig_trend.add_trace(go.Scatter(x=df_trend['월'], y=df_trend['영업이익'], name="영업이익", line=dict(color="#212529", width=3)))
    fig_trend.update_layout(title="월별 매출 및 영업이익 추이", barmode='group', height=400)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 마케팅비 & ROAS
    col4_1, col4_2 = st.columns([2, 1])
    
    with col4_1:
        fig_roas = go.Figure()
        total_mkt = df_trend['매체 광고비'] + df_trend['기타 마케팅비']
        fig_roas.add_trace(go.Bar(x=df_trend['월'], y=total_mkt, name="마케팅비 계", marker_color="#adb5bd"))
        fig_roas.add_trace(go.Scatter(x=df_trend['월'], y=df_trend['ROAS'], name="ROAS", yaxis="y2", line=dict(color="#f06595", width=3)))
        
        fig_roas.update_layout(
            title="마케팅비 vs ROAS 추이",
            yaxis=dict(title="마케팅비(원)"),
            yaxis2=dict(title="ROAS", overlaying="y", side="right"),
            legend=dict(x=0, y=1.1, orientation="h"),
            height=400
        )
        st.plotly_chart(fig_roas, use_container_width=True)
        
    with col4_2:
        st.metric("현재 ROAS", f"{master_month['ROAS']:.2f}")
        st.info(f"💡 전체 매출 중 굿즈 비중: {(master_month['굿즈 매출']/master_month['매출']*100):.1f}%")

# --- [페이지 2: 상품/업체 분석] ---
elif page == "📦 상품/업체 분석":
    st.title(f"🛒 {selected_month} 상품 및 업체 상세 분석")
    
    # 1. 카테고리 분석
    st.subheader("🗂️ 카테고리별 판매 성과")
    df_orders_month = data['orders'][data['orders']['월'] == selected_month]
    
    col_cat1, col_cat2 = st.columns(2)
    
    with col_cat1:
        cat_revenue = df_orders_month.groupby('카테고리')['총 매출'].sum().reset_index().sort_values('총 매출', ascending=False)
        fig_cat_pie = px.pie(cat_revenue, values='총 매출', names='카테고리', title="카테고리별 매출 비중", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_cat_pie, use_container_width=True)
        
    with col_cat2:
        cat_qty = df_orders_month.groupby('카테고리')['수량'].sum().reset_index().sort_values('수량', ascending=False)
        fig_cat_bar = px.bar(cat_qty, x='수량', y='카테고리', orientation='h', title="카테고리별 판매 수량",
                             color='수량', color_continuous_scale='Blues')
        fig_cat_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cat_bar, use_container_width=True)
        
    st.markdown("---")
    
    # 2. 업체(파트너) 분석
    st.subheader("🏢 TOP 3 매출 업체")
    df_rank_month = data['ranking'][data['ranking']['월'] == selected_month].sort_values('순위')
    
    rank_cols = st.columns(3)
    for i, (_, row) in enumerate(df_rank_month.iterrows()):
        if i < 3:
            with rank_cols[i]:
                st.markdown(f"### {row['순위']}")
                st.markdown(f"**{row['업체명']}**")
                st.markdown(f"매출액: **{row['매출']:,.0f}원**")
                st.progress(1.0 - (i * 0.2))
                
    st.markdown("---")
    
    # 3. 상품 분석
    st.subheader("🏆 가장 많이 팔린 상품 TOP 5")
    top_products = df_orders_month.groupby(['상품명', '파트너']).agg({
        '수량': 'sum',
        '총 매출': 'sum'
    }).reset_index().sort_values('수량', ascending=False).head(5)
    
    top_products.columns = ['상품명', '업체명', '판매수량', '매출액']
    st.table(top_products.style.format({'판매수량': '{:,.0f}', '매출액': '{:,.0f}원'}))
    
    # 상품별 매출 기여도 기포 차트
    fig_bubble = px.scatter(top_products, x="판매수량", y="매출액", size="매출액", color="상품명",
                            hover_name="상품명", log_x=False, size_max=60, title="TOP 5 상품 기여도 분석")
    st.plotly_chart(fig_bubble, use_container_width=True)

# 푸터
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>한국민속촌 스토어 데이터 분석 시스템 v1.0</p>", unsafe_allow_html=True)
