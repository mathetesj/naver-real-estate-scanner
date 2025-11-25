import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime

# --- 페이지 설정 (반드시 최상단) ---
st.set_page_config(
    page_title="네이버 부동산 스캐너 Pro",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 UI/UX 300% 업그레이드 (Custom CSS) ---
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 */
    .main {
        background-color: #f8f9fa;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 카드 스타일 (매물 리스트) */
    .property-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .property-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    /* 뱃지 스타일 */
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 6px;
    }
    .badge-trade { background-color: #ffe5e5; color: #d32f2f; } /* 매매 */
    .badge-jeonse { background-color: #e3f2fd; color: #1976d2; } /* 전세 */
    .badge-rent { background-color: #f3e5f5; color: #7b1fa2; } /* 월세 */
    
    /* 텍스트 스타일 */
    .price-text {
        font-size: 18px;
        font-weight: 800;
        color: #1a1a1a;
    }
    .converted-price {
        font-size: 15px;
        color: #3b82f6;
        font-weight: 700;
        background-color: #eff6ff;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 4px;
    }
    .info-text {
        color: #6c757d;
        font-size: 14px;
        margin-top: 4px;
    }
    .desc-text {
        color: #495057;
        font-size: 13px;
        margin-top: 8px;
        line-height: 1.4;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 6px;
    }
    
    /* 사이드바 스타일 개선 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eee;
    }
    
    /* 입력창 및 버튼 개선 */
    .stTextInput input {
        border-radius: 8px;
    }
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        border: none;
        transition: all 0.2s;
    }
    /* 주요 버튼 (파란색) */
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }
    </style>
""", unsafe_allow_html=True)

# --- 유틸리티 함수 ---
def format_money(val):
    """만원 단위 숫자를 '억 만원' 형태로 변환"""
    if val == 0: return "-"
    uk = val // 10000
    man = val % 10000
    if uk > 0 and man > 0: return f"{uk}억 {man.toLocaleString()}만"
    if uk > 0: return f"{uk}억"
    return f"{man.toLocaleString()}만"

# --- 0. 네이버 부동산 API 설정 ---
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://new.land.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://new.land.naver.com"
}

# --- 1. 단지 검색 함수 ---
def search_complex_id(keyword):
    """단지 이름으로 ID 검색 (예외처리 강화)"""
    url = "https://new.land.naver.com/api/search"
    params = {'keyword': keyword}
    try:
        time.sleep(random.uniform(0.5, 1.5)) # 랜덤 딜레이로 사람처럼 위장
        res = requests.get(url, headers=COMMON_HEADERS, params=params, timeout=5)
        
        if res.status_code == 429:
            return "BLOCKED", None
            
        res.raise_for_status()
        data = res.json()
        
        if data.get('suggests'):
            for item in data['suggests']:
                # 아파트(AptComplex)이면서 ID가 있는 경우
                if item.get('cortarType') == 'AptComplex' and item.get('complexNo'):
                    return item.get('cortarName'), item.get('complexNo')
        return None, None
    except Exception as e:
        return "ERROR", str(e)

# --- 2. 매물 데이터 수집 함수 ---
@st.cache_data(ttl=600) # 10분 캐시
def fetch_data(complex_list, demo_mode=False):
    """실제 데이터 수집 또는 데모 데이터 생성"""
    
    # [데모 모드] 네이버 차단 시 사용
    if demo_mode:
        dummy_data = []
        complexes = [c['name'] for c in complex_list] if complex_list else ['잠실엘스', '리센츠', '트리지움']
        types = ['매매', '전세', '월세']
        
        for i in range(20):
            c_name = random.choice(complexes)
            t_type = random.choice(types)
            price = random.randint(100000, 300000) # 10억~30억
            rent = 0
            if t_type == '월세':
                price = random.randint(10000, 100000) # 보증금 1억~10억
                rent = random.randint(50, 400) # 월세 50~400만
            elif t_type == '전세':
                price = random.randint(80000, 200000) # 8억~20억
                
            dummy_data.append({
                '단지명': c_name,
                '거래유형': t_type,
                '가격(만원)': price,
                '월세(만원)': rent,
                '동': f"{random.randint(101, 130)}동",
                '층': f"{random.choice(['저', '중', '고'])}/{random.randint(20, 35)}",
                '면적': f"{random.choice(['59', '84', '112'])}㎡",
                '설명': random.choice(['올수리, 한강뷰', '입주협의, 로얄동', '급매, 풀옵션', '세안고 매매']),
                '확인일': datetime.now().strftime("%Y-%m-%d")
            })
        return pd.DataFrame(dummy_data)

    # [실제 모드] 네이버 크롤링
    all_data = []
    url = "https://new.land.naver.com/api/articles/complex/{}"
    
    progress_text = st.empty()
    bar = st.progress(0)
    
    for idx, c_info in enumerate(complex_list):
        progress_text.text(f"📡 {c_info['name']} 데이터 스캔 중...")
        bar.progress((idx + 1) / len(complex_list))
        
        try:
            # 차단 방지: 랜덤 딜레이 (0.5초 ~ 2초)
            time.sleep(random.uniform(0.5, 2.0))
            
            headers = COMMON_HEADERS.copy()
            headers['Referer'] = f"https://new.land.naver.com/complexes/{c_info['id']}"
            
            params = {
                'realEstateType': 'APT',
                'tradeType': 'A1:B1:B2',
                'complexNo': c_info['id'],
            }
            
            res = requests.get(url.format(c_info['id']), headers=headers, params=params, timeout=10)
            
            if res.status_code == 429:
                st.toast(f"🚨 {c_info['name']}: 네이버 서버가 요청을 차단했습니다. 잠시 후 시도하세요.", icon="⚠️")
                continue
                
            data = res.json()
            articles = data.get('articleList', [])
            
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
                
                all_data.append({
                    '단지명': c_info['name'],
                    '거래유형': art.get('tradeTypeName'),
                    '가격(만원)': price,
                    '월세(만원)': rent,
                    '동': art.get('buildingName'),
                    '층': art.get('floorInfo'),
                    '면적': art.get('areaName'),
                    '설명': art.get('articleFeatureDesc'),
                    '확인일': art.get('confirmedDate')
                })
                
        except Exception as e:
            st.toast(f"{c_info['name']} 로딩 실패: {str(e)}", icon="❌")
            
    bar.empty()
    progress_text.empty()
    return pd.DataFrame(all_data)

# --- 3. 메인 앱 로직 ---

# 사이드바 상태 관리
if 'complex_list' not in st.session_state:
    st.session_state.complex_list = [
        {'name': '잠실엘스', 'id': '19772'},
        {'name': '리센츠', 'id': '19773'}
    ]
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

# === 사이드바 ===
with st.sidebar:
    st.title("🛠️ 스캐너 설정")
    
    # 1. 단지 검색/추가
    st.subheader("단지 추가")
    with st.form("search_form", clear_on_submit=True):
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_input = st.text_input("단지명", placeholder="예: 헬리오시티", label_visibility="collapsed")
        with col_s2:
            search_btn = st.form_submit_button("검색")
            
        if search_btn and search_input:
            name, cid = search_complex_id(search_input)
            if cid:
                # 중복 확인
                if not any(c['id'] == cid for c in st.session_state.complex_list):
                    st.session_state.complex_list.append({'name': name, 'id': cid})
                    st.toast(f"✅ '{name}' 추가 완료!", icon="🎉")
                else:
                    st.toast(f"⚠️ '{name}' 이미 목록에 있습니다.", icon="✋")
            elif name == "BLOCKED":
                st.error("🚫 검색 요청이 차단되었습니다. 잠시 후 다시 시도하거나 '데모 모드'를 사용하세요.")
            else:
                st.error("❌ 단지를 찾을 수 없습니다. 정확한 이름을 입력해주세요.")

    # 2. 현재 목록 관리
    st.subheader(f"관심 단지 ({len(st.session_state.complex_list)})")
    
    # 목록 삭제 기능
    for idx, c in enumerate(st.session_state.complex_list):
        col_del1, col_del2 = st.columns([4, 1])
        col_del1.text(f"• {c['name']}")
        if col_del2.button("X", key=f"del_{idx}", help="삭제"):
            st.session_state.complex_list.pop(idx)
            st.rerun()
            
    st.divider()
    
    # 3. 환산 설정
    st.subheader("💰 환산 기준")
    rate = st.number_input("1억 당 월세 (만원)", value=40, step=1)
    
    st.divider()
    
    # 4. 모드 설정
    st.subheader("⚙️ 모드 설정")
    st.session_state.demo_mode = st.toggle("데모 모드 (차단 시 사용)", value=st.session_state.demo_mode)
    
    if st.button("🔄 매물 새로고침", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# === 메인 화면 ===
st.title("🏡 네이버 부동산 실시간 스캐너 Pro")
st.markdown(f"""
<div style='background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 5px solid #2196f3; margin-bottom: 20px;'>
    <b>💡 팁:</b> 좌측 사이드바에서 단지를 검색해 추가하세요. 
    <b>네이버 서버 차단(429 Error)</b>이 발생하면 사이드바 하단의 <b>'데모 모드'</b>를 켜주세요.
</div>
""", unsafe_allow_html=True)

# 데이터 로딩
if not st.session_state.complex_list:
    st.info("👈 사이드바에서 관심 단지를 추가해주세요.")
else:
    df = fetch_data(st.session_state.complex_list, st.session_state.demo_mode)
    
    if df.empty:
        if st.session_state.demo_mode:
            st.warning("데이터가 없습니다.")
        else:
            st.error("데이터를 가져오지 못했습니다. 네이버 차단이 의심됩니다. 사이드바의 '데모 모드'를 켜서 기능을 체험해보세요.")
    else:
        # --- 데이터 가공 ---
        # 환산가 계산
        df['환산가(만원)'] = df.apply(
            lambda x: x['가격(만원)'] + (x['월세(만원)'] / rate * 10000) if x['월세(만원)'] > 0 else x['가격(만원)'], 
            axis=1
        )
        
        # --- 필터링 및 정렬 ---
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        
        with col_f1:
            filter_type = st.multiselect("거래 유형", df['거래유형'].unique(), default=df['거래유형'].unique())
        with col_f2:
            filter_complex = st.multiselect("단지", df['단지명'].unique(), default=df['단지명'].unique())
        with col_f3:
            sort_order = st.selectbox("정렬", ["환산가 낮은순", "환산가 높은순", "최신순"])
            
        # 필터 적용
        mask = (df['거래유형'].isin(filter_type)) & (df['단지명'].isin(filter_complex))
        filtered_df = df[mask].copy()
        
        # 정렬 적용
        if sort_order == "환산가 낮은순":
            filtered_df = filtered_df.sort_values("환산가(만원)", ascending=True)
        elif sort_order == "환산가 높은순":
            filtered_df = filtered_df.sort_values("환산가(만원)", ascending=False)
        else:
            filtered_df = filtered_df.sort_index(ascending=False) # 대략적 최신순
            
        # --- 결과 표시 (카드 UI) ---
        st.subheader(f"검색 결과 ({len(filtered_df)}건)")
        
        if len(filtered_df) == 0:
            st.info("조건에 맞는 매물이 없습니다.")
        else:
            # 그리드 레이아웃 (반응형)
            # 화면 크기에 따라 열 개수가 달라지지는 않지만, 시각적으로 정리됨
            for idx, row in filtered_df.iterrows():
                # 뱃지 클래스 결정
                badge_cls = "badge-trade"
                if "전세" in row['거래유형']: badge_cls = "badge-jeonse"
                elif "월세" in row['거래유형']: badge_cls = "badge-rent"
                
                # 가격 텍스트
                price_txt = format_money(row['가격(만원)'])
                if row['월세(만원)'] > 0:
                    price_txt += f" / {row['월세(만원)']}"
                
                # 환산가 텍스트
                conv_txt = format_money(int(row['환산가(만원)']))
                
                # HTML 카드 렌더링
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <span class="badge {badge_cls}">{row['거래유형']}</span>
                            <span style="font-weight: 600; color: #555;">{row['단지명']}</span>
                        </div>
                        <div style="text-align: right;">
                            <div class="price-text">{price_txt}</div>
                            <div class="converted-price">환산 {conv_txt}</div>
                        </div>
                    </div>
                    <div class="info-text">
                        {row['동']} • {row['층']} • {row['면적']}
                    </div>
                    <div class="desc-text">
                        {row['설명']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
