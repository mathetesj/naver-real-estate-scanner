import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime

# --- 1. 페이지 설정 (반드시 최상단) ---
st.set_page_config(
    page_title="네이버 부동산 Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Professional UI/UX (White Theme 강제 적용 CSS) ---
st.markdown("""
    <style>
    /* 1. 기본 배경 및 폰트 설정 (화이트 테마 강제) */
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa; /* 아주 연한 회색 배경 */
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff; /* 사이드바 흰색 */
        border-right: 1px solid #e0e0e0;
    }
    
    /* 2. 텍스트 컬러 강제 (다크모드 사용자 대응) */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #1e293b !important; /* 진한 남색 계열 블랙 */
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 3. 카드 디자인 (토스/직방 스타일) */
    .property-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #f1f5f9;
        transition: all 0.2s ease-in-out;
    }
    .property-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #3b82f6;
    }
    
    /* 4. 뱃지 스타일 */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 8px;
    }
    .badge-trade { background-color: #fee2e2; color: #991b1b !important; } /* 매매 (Red) */
    .badge-jeonse { background-color: #dbeafe; color: #1e40af !important; } /* 전세 (Blue) */
    .badge-rent { background-color: #f3e8ff; color: #6b21a8 !important; } /* 월세 (Purple) */
    
    /* 5. 가격 텍스트 스타일 */
    .price-main {
        font-size: 22px;
        font-weight: 800;
        color: #0f172a !important;
        letter-spacing: -0.5px;
    }
    .price-sub {
        font-size: 14px;
        color: #64748b !important;
        margin-left: 4px;
    }
    
    /* 6. 환산가 하이라이트 */
    .converted-box {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0284c7 !important;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 15px;
        display: inline-block;
        margin-top: 8px;
    }
    
    /* 7. 상세 정보 텍스트 */
    .detail-info {
        color: #475569 !important;
        font-size: 14px;
        margin-top: 12px;
        display: flex;
        gap: 12px;
        align-items: center;
    }
    
    /* 8. 설명 박스 */
    .desc-box {
        background-color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #64748b !important;
        margin-top: 12px;
        line-height: 1.5;
    }
    
    /* Input & Button Customization */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #333;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
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

# --- 4. API 통신 함수 (핵심: UI 코드 완전 제거) ---
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://new.land.naver.com/",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br"
}

def search_complex_id(keyword):
    """단지 검색: 실패 시 None 반환"""
    try:
        url = "https://new.land.naver.com/api/search"
        params = {'keyword': keyword}
        time.sleep(0.5) # 짧은 딜레이
        res = requests.get(url, headers=COMMON_HEADERS, params=params, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            if data.get('suggests'):
                for item in data['suggests']:
                    if item.get('cortarType') == 'AptComplex':
                        return item.get('cortarName'), item.get('complexNo')
        return None, None
    except:
        return None, None

def fetch_complex_data(complex_id, complex_name):
    """
    개별 단지 데이터 수집
    *중요*: @st.cache_data를 제거하여 안전성 확보 (실시간성 우선)
    """
    url = f"https://new.land.naver.com/api/articles/complex/{complex_id}"
    params = {
        'realEstateType': 'APT',
        'tradeType': 'A1:B1:B2',
        'complexNo': complex_id,
    }
    
    # 네이버 차단 방지를 위한 헤더 설정
    headers = COMMON_HEADERS.copy()
    headers['Referer'] = f"https://new.land.naver.com/complexes/{complex_id}"
    
    try:
        # 랜덤 딜레이 (사람처럼 보이기)
        time.sleep(random.uniform(0.3, 1.0))
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            articles = data.get('articleList', [])
            parsed_list = []
            
            for art in articles:
                # 가격 파싱
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
            return "BLOCKED" # 차단됨
    except:
        return "ERROR" # 네트워크 에러

# --- 5. 데모 데이터 생성 (차단 시 Fallback) ---
def generate_demo_data(complex_list):
    dummy = []
    names = [c['name'] for c in complex_list] if complex_list else ['샘플단지A', '샘플단지B']
    for _ in range(15):
        c_name = random.choice(names)
        t_type = random.choice(['매매', '전세', '월세'])
        price = random.randint(100000, 300000)
        rent = 0
        if t_type == '월세':
            price = random.randint(10000, 100000)
            rent = random.randint(50, 400)
        elif t_type == '전세':
            price = random.randint(50000, 150000)
            
        dummy.append({
            '단지명': c_name,
            '거래유형': t_type,
            '가격(만원)': price,
            '월세(만원)': rent,
            '동': f"{random.randint(101, 110)}동",
            '층': "중/20",
            '면적': "84㎡",
            '설명': "데모 데이터입니다. 실제 매물이 아닙니다.",
            '확인일': datetime.now().strftime("%Y-%m-%d")
        })
    return pd.DataFrame(dummy)

# --- 6. 메인 앱 로직 ---

# 상태 초기화
if 'complex_list' not in st.session_state:
    st.session_state.complex_list = [{'name': '잠실엘스', 'id': '19772'}]
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

# === Sidebar ===
with st.sidebar:
    st.title("🛠️ 설정 (Settings)")
    
    st.markdown("### 1. 단지 추가")
    with st.form("search", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        keyword = col1.text_input("단지명", placeholder="예: 헬리오시티", label_visibility="collapsed")
        submit = col2.form_submit_button("검색")
        
        if submit and keyword:
            name, cid = search_complex_id(keyword)
            if cid:
                # 중복 체크
                if not any(c['id'] == cid for c in st.session_state.complex_list):
                    st.session_state.complex_list.append({'name': name, 'id': cid})
                    st.success(f"'{name}' 추가됨")
                else:
                    st.warning("이미 목록에 있습니다.")
            else:
                st.error("단지를 찾을 수 없습니다.")

    st.markdown("### 2. 관리 목록")
    if st.session_state.complex_list:
        for idx, c in enumerate(st.session_state.complex_list):
            c1, c2 = st.columns([4, 1])
            c1.caption(f"📍 {c['name']}")
            if c2.button("✖", key=f"del_{idx}"):
                st.session_state.complex_list.pop(idx)
                st.rerun()
    else:
        st.caption("등록된 단지가 없습니다.")

    st.markdown("---")
    st.markdown("### 3. 환산/모드 설정")
    rate = st.number_input("1억당 월세 (만원)", value=40, step=5)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.session_state.demo_mode = st.toggle("데모 모드 (차단 시 사용)", value=st.session_state.demo_mode)
    
    if st.button("🔄 데이터 새로고침", type="primary", use_container_width=True):
        st.rerun()

# === Main Content ===
st.title("Pro Real Estate Scanner")
st.markdown("##### 관심 단지의 최저가 매물을 실시간으로 분석합니다.")

# 데이터 수집 로직
final_df = pd.DataFrame()
error_occurred = False

if not st.session_state.complex_list:
    st.info("좌측 사이드바에서 단지를 검색하여 추가해주세요.")
else:
    # 1. 데모 모드일 경우
    if st.session_state.demo_mode:
        final_df = generate_demo_data(st.session_state.complex_list)
        st.toast("💡 데모 모드: 가상 데이터가 로드되었습니다.", icon="🧪")
    
    # 2. 실제 크롤링 모드
    else:
        all_results = []
        # Progress Bar (캐시 함수 밖에서 실행하므로 안전함)
        progress_text = st.empty()
        bar = st.progress(0)
        
        for idx, comp in enumerate(st.session_state.complex_list):
            progress_text.text(f"📡 {comp['name']} 데이터 수집 중...")
            
            result = fetch_complex_data(comp['id'], comp['name'])
            
            if result == "BLOCKED":
                st.toast(f"⚠️ {comp['name']}: 네이버 차단됨. 데모 모드를 켜주세요.", icon="🚫")
                error_occurred = True
            elif result == "ERROR":
                st.toast(f"❌ {comp['name']}: 네트워크 오류.", icon="⚠️")
            elif isinstance(result, list):
                all_results.extend(result)
            
            bar.progress((idx + 1) / len(st.session_state.complex_list))
        
        bar.empty()
        progress_text.empty()
        
        if all_results:
            final_df = pd.DataFrame(all_results)
        elif error_occurred:
            st.error("데이터 수집 중 문제가 발생했습니다. 사이드바의 '데모 모드'를 활성화하여 UI를 확인해보세요.")

# 데이터가 있으면 화면 표시
if not final_df.empty:
    # 1. 환산가 계산
    final_df['환산가(만원)'] = final_df.apply(
        lambda x: x['가격(만원)'] + (x['월세(만원)'] / rate * 10000) if x['월세(만원)'] > 0 else x['가격(만원)'], 
        axis=1
    )
    
    # 2. 상단 필터바
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        f_type = st.multiselect("거래 유형", final_df['거래유형'].unique(), default=final_df['거래유형'].unique())
    with c2:
        f_name = st.multiselect("단지 선택", final_df['단지명'].unique(), default=final_df['단지명'].unique())
    with c3:
        sort = st.selectbox("정렬 기준", ["환산가 낮은순", "환산가 높은순", "최신순"])

    # 필터링
    df_show = final_df[
        (final_df['거래유형'].isin(f_type)) & 
        (final_df['단지명'].isin(f_name))
    ].copy()

    # 정렬
    if sort == "환산가 낮은순":
        df_show = df_show.sort_values("환산가(만원)", ascending=True)
    elif sort == "환산가 높은순":
        df_show = df_show.sort_values("환산가(만원)", ascending=False)
    
    # 3. 결과 리스트 (카드 UI 렌더링)
    st.markdown(f"### 📊 검색 결과 ({len(df_show)}건)")
    
    for _, row in df_show.iterrows():
        # 스타일 결정
        b_cls = "badge-trade"
        if "전세" in row['거래유형']: b_cls = "badge-jeonse"
        elif "월세" in row['거래유형']: b_cls = "badge-rent"
        
        # 금액 포맷팅
        price_main = format_money(row['가격(만원)'])
        price_sub = ""
        if row['월세(만원)'] > 0:
            price_sub = f" / {row['월세(만원)']}"
        
        conv_price = format_money(int(row['환산가(만원)']))

        # HTML 카드 출력
        st.markdown(f"""
        <div class="property-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <span class="badge {b_cls}">{row['거래유형']}</span>
                    <span style="font-weight:700; font-size:18px; color:#334155;">{row['단지명']}</span>
                    <div style="margin-top:8px;">
                        <span class="price-main">{price_main}</span>
                        <span class="price-sub">{price_sub}</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div class="converted-box">환산 {conv_price}</div>
                </div>
            </div>
            
            <div class="detail-info">
                <span>🏢 {row['동']}</span>
                <span style="color:#cbd5e1;">|</span>
                <span>📐 {row['면적']}</span>
                <span style="color:#cbd5e1;">|</span>
                <span>⬆️ {row['층']}</span>
            </div>
            
            <div class="desc-box">
                {row['설명']}
            </div>
        </div>
        """, unsafe_allow_html=True)

elif not error_occurred and st.session_state.complex_list:
    st.info("조건에 맞는 매물이 없습니다.")
