import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime

# --- 1. 페이지 설정 (브라우저 탭 이름 등) ---
st.set_page_config(
    page_title="네이버 부동산 Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UI/UX 디자인 (완벽한 가독성 테마) ---
st.markdown("""
    <style>
    /* 1. 글로벌 폰트 및 컬러 리셋 */
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
        color: #1e293b; /* 진한 남색 텍스트 */
    }
    
    /* 2. 배경색 설정 */
    .stApp {
        background-color: #f1f5f9; /* 아주 연한 회색 배경 */
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* 3. 제목 및 헤더 스타일 */
    h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }
    h2, h3 {
        color: #334155 !important;
        font-weight: 700 !important;
    }
    
    /* 4. 프로페셔널 매물 카드 디자인 */
    .property-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    .property-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #3b82f6; /* 호버 시 파란 테두리 */
    }
    
    /* 5. 뱃지 스타일 (가독성 강화) */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 8px;
        vertical-align: middle;
    }
    .badge-trade { background-color: #fee2e2; color: #b91c1c !important; border: 1px solid #fecaca; } /* 매매 (Red) */
    .badge-jeonse { background-color: #dbeafe; color: #1d4ed8 !important; border: 1px solid #bfdbfe; } /* 전세 (Blue) */
    .badge-rent { background-color: #f3e8ff; color: #7e22ce !important; border: 1px solid #e9d5ff; } /* 월세 (Purple) */
    
    /* 6. 가격 텍스트 디자인 */
    .price-main {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .price-sub {
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
        margin-left: 4px;
    }
    
    /* 7. 환산가 강조 박스 */
    .converted-box {
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
        border: 1px solid #bfdbfe;
        color: #0369a1 !important;
        font-weight: 700;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 15px;
        display: inline-block;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* 8. 상세 정보 및 설명 */
    .detail-row {
        margin-top: 12px;
        font-size: 14px;
        color: #475569;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .divider {
        color: #cbd5e1;
    }
    .desc-box {
        margin-top: 12px;
        background-color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #64748b;
        line-height: 1.5;
        border: 1px solid #f1f5f9;
    }

    /* 9. 데모 모드 배너 */
    .demo-banner {
        background-color: #fff7ed;
        border: 1px solid #fed7aa;
        color: #9a3412;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Streamlit 기본 위젯 커스텀 */
    .stTextInput input {
        background-color: white;
        color: #333;
        border: 1px solid #cbd5e1;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: white;
        color: #333;
        border-color: #cbd5e1;
    }
    /* 버튼 스타일 */
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    div.stButton > button[kind="secondary"] {
        background-color: white;
        color: #475569;
        border: 1px solid #cbd5e1;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 유틸리티 함수 (숫자 포맷팅) ---
def format_money(val):
    if val == 0: return "-"
    uk = val // 10000
    man = val % 10000
    
    # Python f-string {:,} 문법 사용 (천단위 콤마)
    if uk > 0 and man > 0: return f"{uk}억 {man:,}"
    if uk > 0: return f"{uk}억"
    return f"{man:,}만"

# --- 4. API 통신 및 데이터 로직 ---
def get_headers(referer_url="https://new.land.naver.com/"):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Referer": referer_url,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://new.land.naver.com"
    }

def search_complex_id(keyword):
    """단지 검색 로직"""
    url = "https://new.land.naver.com/api/search"
    params = {'keyword': keyword}
    try:
        time.sleep(random.uniform(0.3, 0.8))
        res = requests.get(url, headers=get_headers(), params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('suggests'):
                for item in data['suggests']:
                    if item.get('cortarType') == 'AptComplex':
                        return item.get('cortarName'), item.get('complexNo')
            return "NOT_FOUND", None
        return f"BLOCKED_{res.status_code}", None
    except Exception as e:
        return f"ERROR_{str(e)}", None

def fetch_complex_data(complex_id, complex_name):
    """실제 매물 데이터 크롤링"""
    url = f"https://new.land.naver.com/api/articles/complex/{complex_id}"
    params = {'realEstateType': 'APT', 'tradeType': 'A1:B1:B2', 'complexNo': complex_id}
    try:
        time.sleep(random.uniform(0.5, 1.2))
        res = requests.get(url, headers=get_headers(f"https://new.land.naver.com/complexes/{complex_id}"), params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            articles = data.get('articleList', [])
            parsed_list = []
            for art in articles:
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
        return "BLOCKED"
    except:
        return "ERROR"

def generate_demo_data(complex_list):
    """데모용 가상 데이터 생성"""
    dummy = []
    names = [c['name'] for c in complex_list] if complex_list else ['예시단지A', '예시단지B']
    
    # 데이터 다양성 확보
    for _ in range(20):
        c_name = random.choice(names)
        t_type = random.choices(['매매', '전세', '월세'], weights=[0.4, 0.4, 0.2])[0]
        
        price = 0
        rent = 0
        area = random.choice(["59㎡", "84㎡", "114㎡"])
        
        if t_type == '매매':
            price = random.randint(180000, 250000) if area == "84㎡" else random.randint(130000, 170000)
        elif t_type == '전세':
            price = random.randint(90000, 130000) if area == "84㎡" else random.randint(70000, 90000)
        else: # 월세
            price = random.randint(10000, 50000)
            rent = random.randint(100, 400)

        dummy.append({
            '단지명': c_name, '거래유형': t_type, '가격(만원)': price, '월세(만원)': rent,
            '동': f"{random.randint(101, 112)}동", 
            '층': random.choice(["저/25", "중/25", "고/25", "5/25", "20/25"]), 
            '면적': area, 
            '설명': random.choice(["올수리, 입주협의", "한강뷰 로얄동", "급매, 풀옵션", "주인거주 깨끗함", "세안고 갭투자"]), 
            '확인일': datetime.now().strftime("%Y-%m-%d")
        })
    return pd.DataFrame(dummy)

# --- 5. 메인 앱 실행 로직 ---

# 세션 상태 초기화
if 'complex_list' not in st.session_state:
    st.session_state.complex_list = [{'name': '잠실엘스', 'id': '19772'}]
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

# [사이드바] 설정 패널
with st.sidebar:
    st.header("🛠️ 스캐너 설정")
    
    st.subheader("1. 단지 관리")
    with st.form("search", clear_on_submit=False):
        col1, col2 = st.columns([3, 1])
        keyword = col1.text_input("단지명 검색", placeholder="예: 헬리오시티", label_visibility="collapsed")
        submit = col2.form_submit_button("검색")
        
        if submit and keyword:
            name, cid = search_complex_id(keyword)
            if cid:
                if not any(c['id'] == cid for c in st.session_state.complex_list):
                    st.session_state.complex_list.append({'name': name, 'id': cid})
                    st.success(f"✅ '{name}' 추가됨")
                    time.sleep(1) # 메시지 확인용 딜레이
                    st.rerun()
                else:
                    st.warning("⚠️ 이미 목록에 있습니다.")
            elif name and "BLOCKED" in name:
                st.error("🚫 네이버 접속 차단됨. 하단의 '데모 모드'를 켜주세요.")
            elif name and "ERROR" in name:
                st.error("❌ 네트워크 오류")
            else:
                st.error("🔍 단지를 찾을 수 없습니다.")

    # 단지 목록 표시
    if st.session_state.complex_list:
        st.markdown("---")
        st.caption(f"등록된 단지 ({len(st.session_state.complex_list)})")
        for idx, c in enumerate(st.session_state.complex_list):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{c['name']}**")
            if c2.button("🗑️", key=f"del_{idx}", help="삭제"):
                st.session_state.complex_list.pop(idx)
                st.rerun()
    else:
        st.info("단지를 추가해주세요.")
                
    st.markdown("---")
    st.subheader("2. 환산 기준")
    rate = st.number_input("1억당 월세 (만원)", value=40, step=5, help="월세를 전세로 환산할 때 적용할 비율입니다.")
    
    st.markdown("---")
    st.subheader("3. 시스템 모드")
    st.session_state.demo_mode = st.toggle("데모 모드 (차단 시 사용)", value=st.session_state.demo_mode)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 데이터 새로고침", type="primary", use_container_width=True):
        st.rerun()

# [메인 화면] 콘텐츠
st.title("Pro Real Estate Scanner")
st.markdown("관심 단지의 최저가 매물을 **실시간 환산가** 기준으로 비교 분석합니다.")

# 데모 모드 배너
if st.session_state.demo_mode:
    st.markdown("""
        <div class="demo-banner">
            <span>🚧</span>
            <span><b>데모 모드 실행 중:</b> 실제 네이버 데이터가 아닌, 테스트용 가상 데이터를 보여줍니다.</span>
        </div>
    """, unsafe_allow_html=True)
    df = generate_demo_data(st.session_state.complex_list)

# 실제 데이터 로딩
else:
    all_data = []
    blocked = False
    
    # 프로그레스 바 UI
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, c in enumerate(st.session_state.complex_list):
        status_text.text(f"📡 {c['name']} 매물 데이터 수신 중...")
        res = fetch_complex_data(c['id'], c['name'])
        
        if res == "BLOCKED":
            st.toast(f"🚫 {c['name']}: 네이버 서버 접근이 차단되었습니다.", icon="⚠️")
            blocked = True
        elif res == "ERROR":
            st.toast(f"❌ {c['name']}: 통신 오류 발생", icon="💥")
        elif isinstance(res, list):
            all_data.extend(res)
        
        progress_bar.progress((idx + 1) / len(st.session_state.complex_list))
    
    # 로딩 종료
    progress_bar.empty()
    status_text.empty()
    
    if blocked and not all_data:
        st.error("""
            **🚨 네이버 부동산 서버 접근이 차단되었습니다.**
            
            너무 많은 요청이 발생하여 네이버 보안 정책에 의해 일시적으로 차단된 상태입니다.
            좌측 사이드바의 **'데모 모드'**를 켜서 기능을 확인하시거나, 잠시 후 다시 시도해주세요.
        """)
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(all_data)

# 결과 렌더링
if not df.empty:
    # 1. 환산가 계산
    df['환산가(만원)'] = df.apply(
        lambda x: x['가격(만원)'] + (x['월세(만원)'] / rate * 10000) if x['월세(만원)'] > 0 else x['가격(만원)'], 
        axis=1
    )
    
    # 2. 필터 및 정렬 옵션 (카드 위에 배치)
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        f_type = st.multiselect("거래 유형", df['거래유형'].unique(), default=df['거래유형'].unique())
    with col_f2:
        f_sort = st.selectbox("정렬 기준", ["환산가 낮은순", "환산가 높은순", "최신 등록순"])
    
    # 데이터 필터링
    filtered_df = df[df['거래유형'].isin(f_type)].copy()
    
    # 정렬 로직
    if f_sort == "환산가 낮은순":
        filtered_df = filtered_df.sort_values("환산가(만원)", ascending=True)
    elif f_sort == "환산가 높은순":
        filtered_df = filtered_df.sort_values("환산가(만원)", ascending=False)
    else: # 최신 등록순 (확인일 기준)
        filtered_df = filtered_df.sort_values("확인일", ascending=False)
    
    # 3. 매물 카드 리스트 출력
    st.markdown(f"##### 📊 검색 결과 ({len(filtered_df)}건)")
    
    if len(filtered_df) == 0:
        st.info("조건에 맞는 매물이 없습니다.")
    
    for _, row in filtered_df.iterrows():
        # 뱃지 클래스 결정
        badge_class = "badge-trade"
        if "전세" in row['거래유형']: badge_class = "badge-jeonse"
        elif "월세" in row['거래유형']: badge_class = "badge-rent"
        
        # 가격 텍스트 생성
        price_txt = format_money(row['가격(만원)'])
        if row['월세(만원)'] > 0:
            price_txt += f" / {row['월세(만원)']}"
            
        conv_txt = format_money(int(row['환산가(만원)']))
        
        # HTML 렌더링
        st.markdown(f"""
        <div class="property-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="margin-bottom: 6px;">
                        <span class="badge {badge_class}">{row['거래유형']}</span>
                        <span style="font-weight: 700; font-size: 18px; color: #1e293b;">{row['단지명']}</span>
                    </div>
                    <div>
                        <span class="price-main">{price_txt}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="converted-box">환산 {conv_txt}</div>
                </div>
            </div>
            
            <div class="detail-row">
                <span>🏢 {row['동']}</span>
                <span class="divider">|</span>
                <span>📐 {row['면적']}</span>
                <span class="divider">|</span>
                <span>⬆️ {row['층']}</span>
                <span class="divider">|</span>
                <span style="color: #94a3b8; font-size: 13px;">{row['확인일']} 확인</span>
            </div>
            
            <div class="desc-box">
                {row['설명']}
            </div>
        </div>
        """, unsafe_allow_html=True)

elif not blocked and st.session_state.complex_list:
    st.info("검색된 매물이 없습니다. 필터를 확인하거나 단지를 추가해보세요.")
