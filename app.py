import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# --- 페이지 설정 ---
st.set_page_config(
    page_title="네이버 부동산 실시간 분석기",
    page_icon="🏠",
    layout="wide"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    .stDataFrame { width: 100%; }
    /* 버튼 배경색 설정 */
    div.stButton > button {
        background-color: #f0f2f6; 
        color: #1f77b4;
        border: 1px solid #1f77b4;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 0. 네이버 부동산 API 접근을 위한 보안 헤더 ---
# 실제 사용자처럼 위장하여 차단 회피 시도
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Referer": "https://new.land.naver.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "application/json, text/plain, */*"
}

# --- 1. 단지 이름으로 ID를 찾는 함수 (새로운 기능) ---
def search_complex_id(complex_name):
    search_url = "https://new.land.naver.com/api/search"
    params = {'keyword': complex_name}
    
    try:
        response = requests.get(search_url, headers=COMMON_HEADERS, params=params, timeout=5)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()
        
        # 검색 결과 중 'APT' 유형의 첫 번째 결과를 찾음
        if data.get('suggests'):
            for item in data['suggests']:
                if item.get('cortarType') == 'AptComplex' and item.get('complexNo'):
                    return item.get('cortarName'), item.get('complexNo')
        return None, None
    except Exception as e:
        st.error(f"단지 검색 중 오류 발생: {e}")
        return None, None

# --- 2. 데이터 수집 함수 (Backend Logic) ---
@st.cache_data(ttl=300) # 5분마다 캐시 초기화 
def fetch_naver_land_data(complex_list):
    url_base = "https://new.land.naver.com/api/articles/complex/{}"
    all_data = []
    
    for complex_info in complex_list:
        complex_no = complex_info['id']
        complex_name = complex_info['name']
        
        params = {
            'realEstateType': 'APT',  
            'tradeType': 'A1:B1:B2', 
            'complexNo': complex_no,
        }
        
        try:
            # 헤더에 단지 정보 URL을 Referer로 넣어 차단 회피 시도
            headers = COMMON_HEADERS.copy()
            headers['Referer'] = f"https://new.land.naver.com/complexes/{complex_no}"

            response = requests.get(url_base.format(complex_no), headers=headers, params=params, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()
            articles = data.get('articleList', [])
            
            for article in articles:
                price_str = article.get('dealOrWarrantPrc', '0')
                rent_str = article.get('rentPrc', '0')
                
                # 네이버 가격 문자열 파싱 (예: 15억 5,000)
                def parse_price(p_str):
                    if not p_str: return 0
                    p_str = p_str.replace(',', '')
                    total = 0
                    if '억' in p_str:
                        parts = p_str.split('억')
                        uk = int(parts[0]) * 10000
                        man = int(parts[1]) if len(parts) > 1 and parts[1] and parts[1].strip() else 0
                        total = uk + man
                    else:
                        total = int(p_str)
                    return total

                price_val = parse_price(price_str)
                rent_val = int(rent_str.replace(',', '')) if rent_str else 0
                
                item = {
                    '단지명': complex_name,
                    '거래유형': article.get('tradeTypeName'),
                    '가격(화면용)': f"{price_str}{f' / {rent_str}' if rent_val > 0 else ''}",
                    '보증금/매매가(만원)': price_val,
                    '월세(만원)': rent_val,
                    '층': article.get('floorInfo'),
                    '면적': article.get('areaName'),
                    '설명': article.get('articleFeatureDesc'),
                }
                all_data.append(item)
                
        except requests.exceptions.RequestException as req_err:
            st.warning(f"⚠️ {complex_name} 데이터 로딩 실패: 네트워크 오류 또는 서버 차단됨 ({req_err})")
        except Exception as e:
             st.warning(f"⚠️ {complex_name} 데이터 처리 중 오류: {e}")
            
    return pd.DataFrame(all_data)

# --- 3. 웹 화면 구성 (Frontend Logic) ---

st.title("🏠 네이버 부동산 실시간 스캐너")
st.markdown("관심 단지의 **최저가 매물**을 실시간으로 가져와 **전세 환산가**로 비교합니다.")

# 세션 상태 초기화 및 관리 (단지 목록 유지를 위해 필수)
if 'complex_list_text' not in st.session_state:
    st.session_state.complex_list_text = "잠실엘스,19772\n리센츠,19773\n트리지움,19774"

# 사이드바: 설정 영역
with st.sidebar:
    st.header("🛠️ 설정")

    # --- 단지 이름 검색 기능 (새로운 UX) ---
    st.subheader("🔍 단지 이름으로 추가")
    
    col_search, col_button = st.columns([3, 1])
    with col_search:
        search_name = st.text_input("단지 이름 입력", key="search_input", placeholder="예: 헬리오시티")
    with col_button:
        # 검색 버튼
        if st.button("검색 & 추가", use_container_width=True):
            if search_name:
                st.info(f"'{search_name}' 단지 코드를 찾는 중...")
                found_name, found_id = search_complex_id(search_name)
                
                if found_id:
                    new_entry = f"{found_name},{found_id}"
                    
                    # 이미 목록에 있는지 확인
                    if new_entry in st.session_state.complex_list_text:
                        st.warning(f"'{found_name}' 단지는 이미 목록에 있습니다.")
                    else:
                        # 목록에 추가하고 텍스트 영역 업데이트
                        st.session_state.complex_list_text += f"\n{new_entry}"
                        st.success(f"'{found_name}' ({found_id}) 단지 추가 완료!")
                else:
                    st.error(f"'{search_name}'에 대한 정확한 단지 코드를 찾지 못했습니다. 이름을 다시 확인해주세요.")
            else:
                st.warning("단지 이름을 입력해 주세요.")
            
    st.markdown("---")

    # --- 기존 단지 목록 텍스트 영역 ---
    st.subheader("📝 현재 스캔 단지 목록")
    user_complex_input = st.text_area(
        "단지 목록 (이름,번호 형식으로 줄바꿈)",
        value=st.session_state.complex_list_text,
        key="complex_text_area",
        height=150,
        help="이름과 번호를 콤마(,)로 구분하고 줄바꿈으로 단지를 구분합니다."
    )
    
    st.markdown("---")
    st.subheader("💰 환산 기준")
    conversion_rate = st.number_input("1억 당 월세 (만원)", value=40, step=1, help="예: 40만원 = 1억으로 계산")

    if st.button("🔄 데이터 새로고침 (5분 캐시)", type="primary", use_container_width=True):
        st.cache_data.clear() # 캐시 삭제하여 강제 재로딩
        st.rerun()

# 입력값 파싱 (텍스트 영역이 변경될 때마다 실행)
try:
    target_complexes = []
    for line in user_complex_input.split('\n'):
        if ',' in line:
            name, cid = line.split(',')
            # 이름과 ID가 모두 공백이 아닌 경우만 추가
            if name.strip() and cid.strip():
                target_complexes.append({'name': name.strip(), 'id': cid.strip()})
except Exception:
    st.error("단지 목록 형식이 올바르지 않습니다. '이름,번호' 형식인지 확인해 주세요.")
    target_complexes = []


# 메인 로직
if not target_complexes:
    st.warning("좌측 사이드바에 스캔할 단지 정보를 입력해주세요.")
else:
    with st.spinner(f'{len(target_complexes)}개 단지의 실시간 매물을 가져오는 중...'):
        df = fetch_naver_land_data(target_complexes)

    if not df.empty:
        # --- 4. 데이터 가공 (환산가 계산) ---
        df['환산전세(만원)'] = df.apply(
            lambda x: x['보증금/매매가(만원)'] + (x['월세(만원)'] / conversion_rate * 10000) if x['월세(만원)'] > 0 else x['보증금/매매가(만원)'], 
            axis=1
        )
        df['환산전세(만원)'] = df['환산전세(만원)'].astype(int)

        # 보기 좋게 포맷팅 함수
        def format_money(val):
            uk = val // 10000
            man = val % 10000
            if uk > 0 and man > 0: return f"{uk}억 {man}만"
            if uk > 0: return f"{uk}억"
            return f"{man}만"

        df['환산가(보기)'] = df['환산전세(만원)'].apply(format_money)

        # --- 5. 필터링 UI ---
        # 전체 단지명 리스트를 가져와서 필터링 옵션으로 사용
        complex_names = df['단지명'].unique().tolist()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_type = st.multiselect("거래 유형 필터", df['거래유형'].unique(), default=df['거래유형'].unique())
        with col2:
            selected_complex = st.multiselect("단지별 필터", complex_names, default=complex_names)
        with col3:
            sort_option = st.radio("정렬 기준", ["낮은 환산가순", "높은 환산가순"], horizontal=True)

        # 필터 적용
        mask = (df['거래유형'].isin(selected_type)) & (df['단지명'].isin(selected_complex))
        filtered_df = df[mask].copy()

        # 정렬 적용
        ascending = True if sort_option == "낮은 환산가순" else False
        filtered_df = filtered_df.sort_values(by='환산전세(만원)', ascending=ascending)

        # --- 6. 결과 출력 ---
        st.subheader(f"📊 분석 결과 ({len(filtered_df)}건)")
        
        # 중요 컬럼만 선택해서 보여주기
        display_cols = ['단지명', '거래유형', '가격(화면용)', '환산가(보기)', '층', '면적', '설명']
        
        st.dataframe(
            filtered_df[display_cols],
            hide_index=True,
            column_config={
                "환산가(보기)": st.column_config.TextColumn(
                    "전세 환산가 (기준 적용)",
                    help=f"월세 {conversion_rate}만원 = 1억 기준 환산",
                ),
                "가격(화면용)": "원래 가격 (보증금/월세)"
            },
            use_container_width=True
        )

    else:
        st.error("데이터를 가져오지 못했습니다. 네이버의 크롤링 방지 시스템이 작동했을 수 있습니다. 잠시 후 '데이터 새로고침' 버튼을 눌러 다시 시도해주세요.")
