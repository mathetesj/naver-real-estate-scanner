import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="네이버 부동산 Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS 스타일 (화이트 테마) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    h1, h2, h3, h4, h5, h6, p, span, div { color: #1e293b !important; font-family: 'Pretendard', sans-serif; }
    .property-card {
        background-color: #ffffff; border-radius: 16px; padding: 24px; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #f1f5f9;
    }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700; margin-right: 8px; }
    .badge-trade { background-color: #fee2e2; color: #991b1b !important; }
    .badge-jeonse { background-color: #dbeafe; color: #1e40af !important; }
    .badge-rent { background-color: #f3e8ff; color: #6b21a8 !important; }
    .price-main { font-size: 22px; font-weight: 800; color: #0f172a !important; }
    .converted-box {
        background-color: #f0f9ff; border: 1px solid #bae6fd; color: #0284c7 !important;
        font-weight: 700; padding: 6px 12px; border-radius: 8px; font-size: 15px; display: inline-block;
    }
    .stTextInput input { background-color: #fff; color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 유틸리티 함수 ---
def format_money(val):
    if val == 0: return "-"
    uk = val // 10000
    man = val % 10000
    if uk > 0 and man > 0: return f"{uk}억 {man.toLocaleString()}"
    if uk > 0: return f"{uk}억"
    return f"{man.toLocaleString()}만"

# --- 4. API 통신 함수 (차단 회피 강화) ---
def get_headers(referer_url="https://new.land.naver.com/"):
    """네이버 봇 차단을 피하기 위한 랜덤 헤더 생성"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Referer": referer_url,
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://new.land.naver.com",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

def search_complex_id(keyword):
    """단지 검색 및 디버깅"""
    url = "https://new.land.naver.com/api/search"
    params = {'keyword': keyword}
    try:
        time.sleep(random.uniform(0.5, 1.5))
        res = requests.get(url, headers=get_headers(), params=params, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            if data.get('suggests'):
                for item in data['suggests']:
                    if item.get('cortarType') == 'AptComplex':
                        return item.get('cortarName'), item.get('complexNo')
            return "NOT_FOUND", None # 결과 없음
        else:
            return f"BLOCKED_{res.status_code}", None # 차단됨 (예: 429)
    except Exception as e:
        return f"ERROR_{str(e)}", None

def fetch_complex_data(complex_id, complex_name):
    url = f"https://new.land.naver.com/api/articles/complex/{complex_id}"
    params = {
        'realEstateType': 'APT',
        'tradeType': 'A1:B1:B2',
        'complexNo': complex_id,
    }
    try:
        time.sleep(random.uniform(0.5, 2.0))
        res = requests.get(url, headers=get_headers(f"https://new.land.naver.com/complexes/{complex_id}"), params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            articles = data.get('articleList', [])
            parsed_list = []
            for art in articles:
                # 가격 파싱 로직
                p_str = art.get('dealOrWarrantPrc', '0').replace(',', '')
                r_str = art.get('rentPrc', '0').replace(',', '')
                price = 0
                if '억' in p_str:
                    parts = p_str.split('억')
                    uk = int(parts[0]) * 10000
                    man = int(parts[1]) if len(parts) > 1 and parts[1].strip() else 0
                    price = uk + man
                else:
                    price = int(p_str)
                rent = int(r_str) if r_str else 0
                
                parsed_list.append({
                    '단지명': complex_name,
                    '거래유형': art.get('tradeTypeName'),
                    '가격(만원)': price,
                    '월세(만원)': rent,
                    '동': art.get('buildingName'),
                    '층': art.get('floorInfo'),
                    '면적': art.get('areaName'),
                    '설명': art.get('articleFeatureDesc'),
                    '확인일': art.get('confirmedDate')
                })
            return parsed_list
        else:
            return "BLOCKED"
    except:
        return "ERROR"

# --- 5. 데모 데이터 생성 ---
def generate_demo_data(complex_list):
    dummy = []
    names = [c['name'] for c in complex_list] if complex_list else ['예시단지A', '예시단지B']
    for _ in range(10):
        c_name = random.choice(names)
        t_type = random.choice(['매매', '전세', '월세'])
        price = random.randint(100000, 250000)
        rent = 0
        if t_type == '월세':
            price = random.randint(10000, 80000); rent = random.randint(50, 300)
        elif t_type == '전세':
            price = random.randint(50000, 150000)
            
        dummy.append({
            '단지명': c_name, '거래유형': t_type, '가격(만원)': price, '월세(만원)': rent,
            '동': f"{random.randint(101, 105)}동", '층': "고/25", '면적': "84㎡", '설명': "데모 데이터", '확인일': "2024-03-20"
        })
    return pd.DataFrame(dummy)

# --- 6. 메인 로직 ---
if 'complex_list' not in st.session_state:
    st.session_state.complex_list = [{'name': '잠실엘스', 'id': '19772'}]
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

# Sidebar
with st.sidebar:
    st.title("🛠️ 설정")
    st.markdown("### 1. 단지 추가")
    with st.form("search", clear_on_submit=False): # 엔터키 이슈 방지
        col1, col2 = st.columns([3, 1])
        keyword = col1.text_input("단지명", placeholder="예: 헬리오시티", label_visibility="collapsed")
        submit = col2.form_submit_button("검색")
        
        if submit and keyword:
            name, cid = search_complex_id(keyword)
            if cid:
                if not any(c['id'] == cid for c in st.session_state.complex_list):
                    st.session_state.complex_list.append({'name': name, 'id': cid})
                    st.success(f"✅ '{name}' 추가됨")
                else:
                    st.warning("⚠️ 이미 목록에 있습니다.")
            elif name and "BLOCKED" in name:
                st.error(f"🚫 네이버 차단됨 ({name}). 데모 모드를 켜주세요.")
            elif name and "ERROR" in name:
                st.error(f"❌ 오류 발생: {name}")
            else:
                st.error("🔍 단지를 찾을 수 없습니다. (정확한 아파트명 입력)")

    st.markdown("### 2. 관리 목록")
    if st.session_state.complex_list:
        for idx, c in enumerate(st.session_state.complex_list):
            c1, c2 = st.columns([4, 1])
            c1.caption(f"📍 {c['name']}")
            if c2.button("✖", key=f"del_{idx}"):
                st.session_state.complex_list.pop(idx); st.rerun()
                
    st.divider()
    rate = st.number_input("1억당 월세 (만원)", value=40, step=5)
    st.divider()
    st.session_state.demo_mode = st.toggle("데모 모드 (차단 시 사용)", value=st.session_state.demo_mode)
    if st.button("🔄 데이터 새로고침", type="primary"): st.rerun()

# Main
st.title("Pro Real Estate Scanner")
st.markdown("관심 단지의 최저가 매물을 실시간으로 분석합니다.")

if st.session_state.demo_mode:
    st.info("💡 데모 모드: 실제 데이터가 아닌 가상 데이터입니다.")
    df = generate_demo_data(st.session_state.complex_list)
else:
    all_data = []
    blocked = False
    
    # 캐시 없이 UI 표시하며 진행
    progress_text = st.empty()
    bar = st.progress(0)
    
    for idx, c in enumerate(st.session_state.complex_list):
        progress_text.text(f"📡 {c['name']} 스캔 중...")
        res = fetch_complex_data(c['id'], c['name'])
        
        if res == "BLOCKED":
            st.toast(f"🚫 {c['name']} 차단됨", icon="⚠️"); blocked = True
        elif res == "ERROR":
            st.toast(f"❌ {c['name']} 오류", icon="⚠️")
        elif isinstance(res, list):
            all_data.extend(res)
        bar.progress((idx + 1) / len(st.session_state.complex_list))
    
    bar.empty(); progress_text.empty()
    
    if blocked and not all_data:
        st.error("🚨 네이버가 서버 접근을 차단했습니다. 사이드바의 '데모 모드'를 켜서 UI를 확인하거나, 잠시 후 다시 시도해주세요.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(all_data)

if not df.empty:
    df['환산가(만원)'] = df.apply(lambda x: x['가격(만원)'] + (x['월세(만원)']/rate*10000) if x['월세(만원)']>0 else x['가격(만원)'], axis=1)
    
    c1, c2 = st.columns(2)
    with c1: f_type = st.multiselect("유형", df['거래유형'].unique(), default=df['거래유형'].unique())
    with c2: sort = st.selectbox("정렬", ["환산가 낮은순", "높은순"])
    
    df = df[df['거래유형'].isin(f_type)]
    if sort == "환산가 낮은순": df = df.sort_values("환산가(만원)")
    else: df = df.sort_values("환산가(만원)", ascending=False)
    
    for _, row in df.iterrows():
        b_cls = "badge-trade" if "매매" in row['거래유형'] else "badge-jeonse" if "전세" in row['거래유형'] else "badge-rent"
        price = format_money(row['가격(만원)'])
        if row['월세(만원)'] > 0: price += f" / {row['월세(만원)']}"
        conv = format_money(int(row['환산가(만원)']))
        
        st.markdown(f"""
        <div class="property-card">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <span class="badge {b_cls}">{row['거래유형']}</span>
                    <span style="font-weight:700; font-size:18px;">{row['단지명']}</span>
                    <div class="price-main">{price}</div>
                </div>
                <div style="text-align:right;"><div class="converted-box">환산 {conv}</div></div>
            </div>
            <div style="margin-top:12px; color:#64748b; font-size:14px;">
                {row['동']} • {row['층']} • {row['면적']}
            </div>
            <div style="margin-top:8px; background:#f8fafc; padding:10px; border-radius:8px; font-size:13px; color:#475569;">
                {row['설명']}
            </div>
        </div>
        """, unsafe_allow_html=True)
elif not blocked and st.session_state.complex_list:
    st.info("조건에 맞는 매물이 없습니다.")
