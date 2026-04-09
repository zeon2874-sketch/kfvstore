import pandas as pd
import os

def load_and_preprocess_data(data_dir):
    files = {
        "ranking": "TOP3 매출 업체.xlsx",
        "targets": "목표 달성률.xlsx",
        "master": "브랜드사업본부_월간결산_루커.xlsx",
        "orders": "정식몰 주문집계(9_1~).xlsx",
        "members": "정식몰 회원집계(9_1~).xlsx"
    }
    
    data = {}
    
    # 1. Master Data (경영지표)
    master_path = os.path.join(data_dir, files["master"])
    df_master = pd.read_excel(master_path)
    df_master['날짜'] = pd.to_datetime(df_master['날짜'])
    df_master['월'] = df_master['날짜'].dt.strftime('%Y-%m')
    data['master'] = df_master
    
    # 2. Target Data
    target_path = os.path.join(data_dir, files["targets"])
    df_targets = pd.read_excel(target_path)
    df_targets['날짜'] = pd.to_datetime(df_targets['날짜'])
    df_targets['월'] = df_targets['날짜'].dt.strftime('%Y-%m')
    # 월별 목표값 추출 (월초 1일에만 값이 있는 경우 고려)
    monthly_targets = df_targets.groupby('월').agg({
        '목표 매출': 'max',
        '목표 회원': 'max'
    }).reset_index()
    data['monthly_targets'] = monthly_targets
    
    # 3. Order Data (Fact Table)
    order_path = os.path.join(data_dir, files["orders"])
    df_orders = pd.read_excel(order_path)
    df_orders['결제 완료일자'] = pd.to_datetime(df_orders['결제 완료일자'])
    df_orders['월'] = df_orders['결제 완료일자'].dt.strftime('%Y-%m')
    # 클레임 상태가 취소/환불인 데이터는 제외 또는 필터링 가능하게 유지 (요청사항: 트렌드 분석용)
    data['orders'] = df_orders
    
    # 4. Ranking Data (상위 3개 업체)
    ranking_path = os.path.join(data_dir, files["ranking"])
    df_ranking = pd.read_excel(ranking_path)
    df_ranking['날짜'] = pd.to_datetime(df_ranking['날짜'])
    df_ranking['월'] = df_ranking['날짜'].dt.strftime('%Y-%m')
    data['ranking'] = df_ranking
    
    # 5. Member Data (추가 분석용)
    member_path = os.path.join(data_dir, files["members"])
    if os.path.exists(member_path):
        df_members = pd.read_excel(member_path)
        if '회원가입일' in df_members.columns:
            df_members['회원가입일'] = pd.to_datetime(df_members['회원가입일'], errors='coerce')
            df_members = df_members.dropna(subset=['회원가입일'])
            df_members['월'] = df_members['회원가입일'].dt.strftime('%Y-%m')
        data['members'] = df_members
        
    return data

if __name__ == "__main__":
    data_dir = r"c:\Users\Designer_2\Documents\jeon\dashboard\data"
    processed_data = load_and_preprocess_data(data_dir)
    print("Preprocessing complete.")
    for key, df in processed_data.items():
        print(f"{key}: {df.shape}")
