"""
네이버 부동산 매물 검색기 Pro v2.0
- 인기 단지 프리셋 지원
- 깔끔한 UI/UX
- 검증된 API 구조
- 환산가 기반 매물 비교
"""

import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime
import json

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="네이버 부동산 검색기",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 인기 단지 데이터 (검색 없이 바로 사용 가능)
# ============================================================
POPULAR_COMPLEXES = {
    "잠실엘스": {"id": "19772", "address": "서울시 송파구 잠실동"},
    "헬리오시티": {"id": "114743", "address": "서울시 송파구 가락동"},
    "래미안퍼스티지": {"id": "8894", "address": "서울시 서초구 반포동"},
    "반포자이": {"id": "100078", "address": "서울시 서초구 반포동"},
    "트리지움": {"id": "19764", "address": "서울시 송파구 잠실동"},
    "리센츠": {"id": "19765", "address": "서울시 송파구 잠실동"},
    "파크리오": {"id": "19763", "address": "서울시 송파구 잠실동"},
    "아크로리버파크": {"id": "100096", "address": "서울시 서초구 반포동"},
    "은마아파트": {"id": "8928", "address": "서울시 강남구 대치동"},
    "마포래미안푸르지오": {"id": "102378", "address": "서울시 마포구 아현동"},
    "래미안대치팰리스": {"id": "8918", "address": "서울시 강남구 대치동"},
    "도곡렉슬": {"id": "8977", "address": "서울시 강남구 도곡동"},
    "타워팰리스": {"id": "8981", "address": "서울시 강남구 도곡동"},
    "래미안원베일리": {"id": "136068", "address": "서울시 서초구 반포동"},
}

# ============================================================
# CSS 스타일
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* 매물 카드 */
    .listing-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease;
    }
    .listing-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #3b82f6;
    }
    
    /* 거래유형 뱃지 */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-sale { background: #fee2e2; color: #dc2626; }
    .badge-jeonse { background: #dbeafe; color: #2563eb; }
    .badge-rent { background: #f3e8ff; color: #9333ea; }
    
    /* 가격 표시 */
    .price-main {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
    }
    .price-converted {
        background: linear-gradient(135deg, #eff6ff, #f0f9ff);
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
    }
    
    /* 상세 정보 */
    .detail-info {
        color: #6b7280;
        font-size: 14px;
        margin-top: 10px;
    }
    .detail-info span {
        margin-right: 12px;
    }
    
    /* 설명 박스 */
    .desc-text {
        background: #f9fafb;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 13px;
        color: #4b5563;
        margin-top: 10px;
        line-height: 1.5;
    }
    
    /* 메시지 박스 */
    .error-box {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    .warning-box {
        background: #fffbeb;
        border: 1px solid #fcd34d;
        color: #92400e;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    .info-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# API 함수들
# ============================================================

def get_headers(referer="https://new.land.naver.com/", use_mobile=False):
    """API 요청에 필요한 헤더 생성"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    if use_mobile:
        referer = "https://m.land.naver.com/"
    
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "Host": "new.land.naver.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Connection": "keep-alive",
    }


def search_complex(keyword: str) -> dict:
    """아파트 단지 검색"""
    # 1. 프리셋에서 먼저 찾기
    for name, data in POPULAR_COMPLEXES.items():
        if keyword in name or name in keyword:
            return {
                "success": True,
                "data": {
                    "name": name,
                    "complexNo": data["id"],
                    "address": data["address"]
                },
                "error": None
            }
    
    # 2. API 검색
    url = "https://new.land.naver.com/api/search"
    params = {"keyword": keyword}
    
    try:
        time.sleep(random.uniform(0.3, 0.7))
        response = requests.get(
            url, 
            headers=get_headers(use_mobile=True), 
            params=params, 
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            suggests = data.get("suggests", [])
            
            for item in suggests:
                if item.get("cortarType") == "AptComplex":
                    return {
                        "success": True,
                        "data": {
                            "name": item.get("cortarName", keyword),
                            "complexNo": item.get("complexNo") or item.get("cortarNo"),
                            "address": item.get("cortarAddress", "")
                        },
                        "error": None
                    }
            
            for item in suggests:
                complexes = item.get("complexes", [])
                if complexes:
                    first = complexes[0]
                    return {
                        "success": True,
                        "data": {
                            "name": first.get("complexName", keyword),
                            "complexNo": first.get("complexNo"),
                            "address": first.get("address", "")
                        },
                        "error": None
                    }
            
            if suggests:
                first_item = suggests[0]
                complex_no = first_item.get("complexNo") or first_item.get("cortarNo")
                if complex_no:
                    return {
                        "success": True,
                        "data": {
                            "name": first_item.get("cortarName", keyword),
                            "complexNo": complex_no,
                            "address": first_item.get("cortarAddress", "")
                        },
                        "error": None
                    }
            
            return {"success": False, "data": None, "error": "검색 결과가 없습니다"}
            
        elif response.status_code == 403:
            return {"success": False, "data": None, "error": "접근 차단됨 (403). 프리셋 단지를 이용하세요."}
        else:
            return {"success": False, "data": None, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "data": None, "error": "시간 초과. 프리셋 단지를 이용하세요."}
    except Exception as e:
        return {"success": False, "data": None, "error": f"오류: {str(e)[:50]}"}


def fetch_listings(complex_no: str, complex_name: str) -> dict:
    """단지의 매물 목록 조회"""
    url = f"https://new.land.naver.com/api/articles/complex/{complex_no}"
    params = {
        "realEstateType": "APT",
        "tradeType": "A1:B1:B2",
        "tag": ":::::::::",
        "rentPriceMin": "0",
        "rentPriceMax": "900000000",
        "priceMin": "0",
        "priceMax": "900000000",
        "areaMin": "0",
        "areaMax": "900000000",
        "showArticle": "false",
        "sameAddressGroup": "true",
        "page": "1",
        "complexNo": complex_no
    }
    
    referer = f"https://new.land.naver.com/complexes/{complex_no}?ms=37.5,127,16&a=APT&b=A1:B1:B2"
    
    try:
        time.sleep(random.uniform(0.5, 1.0))
        response = requests.get(
            url, 
            headers=get_headers(referer, use_mobile=True), 
            params=params, 
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articleList", [])
            
            if not articles:
                return {"success": True, "data": [], "error": None}
            
            parsed = [parse_article(art, complex_name) for art in articles]
            return {"success": True, "data": parsed, "error": None}
            
        elif response.status_code == 403:
            return {"success": False, "data": None, "error": "접근 차단됨"}
        else:
            return {"success": False, "data": None, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "data": None, "error": "시간 초과"}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)[:50]}


def parse_article(art: dict, complex_name: str) -> dict:
    """매물 데이터 파싱"""
    price_str = str(art.get("dealOrWarrantPrc", "0")).replace(",", "").replace(" ", "")
    price = 0
    
    if "억" in price_str:
        parts = price_str.split("억")
        uk = int(parts[0]) * 10000
        man = 0
        if len(parts) > 1 and parts[1]:
            try:
                man = int(parts[1])
            except:
                pass
        price = uk + man
    else:
        try:
            price = int(price_str) if price_str else 0
        except:
            price = 0
    
    rent_str = str(art.get("rentPrc", "0")).replace(",", "")
    try:
        rent = int(rent_str) if rent_str else 0
    except:
        rent = 0
    
    return {
        "단지명": complex_name,
        "거래유형": art.get("tradeTypeName", ""),
        "가격(만원)": price,
        "월세(만원)": rent,
        "동": art.get("buildingName", "-"),
        "층": art.get("floorInfo", "-"),
        "면적": art.get("areaName", "-"),
        "방향": art.get("direction", "-"),
        "설명": art.get("articleFeatureDesc", ""),
        "확인일": art.get("articleConfirmYmd", ""),
        "매물번호": str(art.get("articleNo", "")),
    }


# ============================================================
# 유틸리티 함수
# ============================================================

def format_price(val: int, include_unit: bool = True) -> str:
    """가격을 읽기 쉬운 형식으로 변환"""
    if val == 0:
        return "-"
    
    uk = val // 10000
    man = val % 10000
    
    if uk > 0 and man > 0:
        result = f"{uk}억 {man:,}"
    elif uk > 0:
        result = f"{uk}억"
    else:
        result = f"{man:,}"
    
    if include_unit and val < 10000:
        result += "만원"
    
    return result


def calculate_converted_price(price: int, rent: int, rate: int) -> int:
    """환산가 계산"""
    if rent > 0:
        converted_rent = (rent / rate) * 10000
        return int(price + converted_rent)
    return price


def generate_demo_data(complexes: list) -> list:
    """데모 데이터 생성"""
    names = [c["name"] for c in complexes] if complexes else ["샘플단지A", "샘플단지B"]
    demo = []
    
    areas = ["59㎡", "74㎡", "84㎡", "102㎡", "114㎡"]
    descs = [
        "올수리 완료, 즉시입주",
        "로얄층, 조망 우수",
        "급매물, 실입주자 환영",
        "주인직접거래",
        "풀옵션, 깨끗한 상태",
        "학군우수, 역세권",
        "세입자 거주중",
    ]
    
    for _ in range(25):
        name = random.choice(names)
        trade = random.choices(["매매", "전세", "월세"], weights=[0.4, 0.4, 0.2])[0]
        area = random.choice(areas)
        area_num = int(area.replace("㎡", ""))
        
        if trade == "매매":
            base = 150000 + (area_num - 59) * 2000
            price = random.randint(int(base * 0.9), int(base * 1.1))
            rent = 0
        elif trade == "전세":
            base = 80000 + (area_num - 59) * 1000
            price = random.randint(int(base * 0.85), int(base * 1.05))
            rent = 0
        else:
            price = random.randint(10000, 50000)
            rent = random.randint(80, 350)
        
        demo.append({
            "단지명": name,
            "거래유형": trade,
            "가격(만원)": price,
            "월세(만원)": rent,
            "동": f"{random.randint(101, 115)}동",
            "층": f"{random.choice(['저', '중', '고', str(random.randint(3,20))])}/{random.randint(20,35)}",
            "면적": area,
            "방향": random.choice(["남향", "남동향", "동향", "남서향"]),
            "설명": random.choice(descs),
            "확인일": datetime.now().strftime("%Y-%m-%d"),
            "매물번호": str(random.randint(2400000000, 2500000000)),
        })
    
    return demo


# ============================================================
# 세션 상태 초기화
# ============================================================

if "complexes" not in st.session_state:
    st.session_state.complexes = []

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

if "cached_data" not in st.session_state:
    st.session_state.cached_data = None

if "fetch_errors" not in st.session_state:
    st.session_state.fetch_errors = []

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "card"


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    # 인기 단지 프리셋
    st.markdown("##### 🔥 인기 단지 (클릭하여 추가)")
    preset_names = list(POPULAR_COMPLEXES.keys())[:8]
    
    cols = st.columns(2)
    for i, name in enumerate(preset_names):
        with cols[i % 2]:
            if st.button(name, key=f"preset_{name}", use_container_width=True):
                existing_ids = [c["id"] for c in st.session_state.complexes]
                preset = POPULAR_COMPLEXES[name]
                if preset["id"] not in existing_ids:
                    st.session_state.complexes.append({
                        "name": name,
                        "id": preset["id"],
                        "address": preset["address"]
                    })
                    st.session_state.cached_data = None
                    st.rerun()
    
    # 단지 검색
    st.markdown("---")
    st.markdown("##### 🔍 단지 검색")
    
    search_keyword = st.text_input(
        "단지명 입력",
        placeholder="예: 헬리오시티, 은마아파트",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        search_btn = st.button("검색", use_container_width=True)
    with col2:
        if st.button("전체삭제", use_container_width=True):
            st.session_state.complexes = []
            st.session_state.cached_data = None
            st.rerun()
    
    if search_btn and search_keyword:
        with st.spinner("검색 중..."):
            result = search_complex(search_keyword)
            
            if result["success"]:
                data = result["data"]
                existing_ids = [c["id"] for c in st.session_state.complexes]
                if data["complexNo"] not in existing_ids:
                    st.session_state.complexes.append({
                        "name": data["name"],
                        "id": data["complexNo"],
                        "address": data.get("address", "")
                    })
                    st.session_state.cached_data = None
                    st.success(f"✓ {data['name']} 추가됨")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("이미 추가된 단지입니다")
            else:
                st.error(f"❌ {result['error']}")
    
    # 등록된 단지 목록
    st.markdown("---")
    st.markdown(f"##### 📋 등록된 단지 ({len(st.session_state.complexes)})")
    
    if st.session_state.complexes:
        for i, c in enumerate(st.session_state.complexes):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{c['name']}**")
            with col2:
                if st.button("✕", key=f"del_{i}", help="삭제"):
                    st.session_state.complexes.pop(i)
                    st.session_state.cached_data = None
                    st.rerun()
    else:
        st.info("위 버튼으로 단지를 추가하세요")
    
    # 환산 기준
    st.markdown("---")
    st.markdown("##### 💰 환산 기준")
    conversion_rate = st.slider(
        "1억당 월세 (만원)",
        min_value=30, max_value=60, value=40, step=5,
        help="월세를 전세로 환산하는 비율"
    )
    
    # 보기 모드
    st.markdown("---")
    st.markdown("##### 👁️ 보기 모드")
    view_mode = st.radio(
        "표시 방식",
        ["카드", "테이블"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.view_mode = "card" if view_mode == "카드" else "table"
    
    # 시스템 모드
    st.markdown("---")
    st.markdown("##### 🔧 시스템")
    st.session_state.demo_mode = st.toggle(
        "데모 모드 (차단 시 사용)",
        value=st.session_state.demo_mode
    )
    
    st.markdown("---")
    if st.button("🔄 매물 조회", type="primary", use_container_width=True):
        st.session_state.cached_data = None
        st.session_state.fetch_errors = []
        st.rerun()


# ============================================================
# 메인 화면
# ============================================================

st.markdown("# 🏠 네이버 부동산 검색기")
st.markdown("관심 단지의 매물을 **환산가** 기준으로 비교합니다.")

# 데모 모드 알림
if st.session_state.demo_mode:
    st.markdown("""
    <div class="warning-box">
        <strong>📌 데모 모드</strong> - 샘플 데이터를 표시합니다. 실제 매물 조회는 데모 모드를 끄세요.
    </div>
    """, unsafe_allow_html=True)

# 단지가 없는 경우
if not st.session_state.complexes:
    st.markdown("""
    <div class="info-box">
        <strong>🚀 시작하기</strong><br>
        왼쪽 사이드바에서 인기 단지를 클릭하거나 단지명을 검색하세요.
    </div>
    """, unsafe_allow_html=True)
    
    # 빠른 추가 버튼
    st.markdown("### 👆 빠른 추가")
    quick_cols = st.columns(4)
    for i, (name, data) in enumerate(list(POPULAR_COMPLEXES.items())[:4]):
        with quick_cols[i]:
            if st.button(f"➕ {name}", key=f"quick_{name}", use_container_width=True):
                st.session_state.complexes.append({
                    "name": name,
                    "id": data["id"],
                    "address": data["address"]
                })
                st.rerun()
    
    st.stop()

# 데이터 로딩
df = None

if st.session_state.demo_mode:
    data = generate_demo_data(st.session_state.complexes)
    df = pd.DataFrame(data)
else:
    if st.session_state.cached_data is not None:
        df = st.session_state.cached_data
    else:
        all_data = []
        errors = []
        
        progress = st.progress(0, text="매물 정보를 불러오는 중...")
        
        for i, c in enumerate(st.session_state.complexes):
            progress.progress(
                (i + 1) / len(st.session_state.complexes),
                text=f"📡 {c['name']} 조회 중..."
            )
            
            result = fetch_listings(c["id"], c["name"])
            
            if result["success"]:
                all_data.extend(result["data"])
            else:
                errors.append(f"{c['name']}: {result['error']}")
        
        progress.empty()
        
        if errors:
            st.session_state.fetch_errors = errors
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.session_state.cached_data = df
        else:
            df = pd.DataFrame()

# 에러 표시
if st.session_state.fetch_errors:
    error_text = "<br>".join(st.session_state.fetch_errors)
    st.markdown(f"""
    <div class="error-box">
        <strong>⚠️ 일부 조회 실패</strong><br>{error_text}<br><br>
        네이버 서버 차단일 수 있습니다. '데모 모드'를 켜거나 잠시 후 다시 시도하세요.
    </div>
    """, unsafe_allow_html=True)

# 데이터가 없는 경우
if df is None or df.empty:
    st.markdown("""
    <div class="info-box">
        조회된 매물이 없습니다. '매물 조회' 버튼을 눌러주세요.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
# 데이터 처리
# ============================================================

df["환산가(만원)"] = df.apply(
    lambda x: calculate_converted_price(x["가격(만원)"], x["월세(만원)"], conversion_rate),
    axis=1
)

# 필터
st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    trade_types = df["거래유형"].unique().tolist()
    selected_trades = st.multiselect("거래유형", options=trade_types, default=trade_types)

with col2:
    complexes = df["단지명"].unique().tolist()
    selected_complexes = st.multiselect("단지", options=complexes, default=complexes)

with col3:
    sort_options = ["환산가 낮은순", "환산가 높은순", "가격 낮은순", "가격 높은순"]
    sort_by = st.selectbox("정렬", options=sort_options)

with col4:
    areas = df["면적"].unique().tolist()
    selected_areas = st.multiselect("면적", options=areas, default=areas)

# 필터 적용
filtered_df = df[
    (df["거래유형"].isin(selected_trades)) &
    (df["단지명"].isin(selected_complexes)) &
    (df["면적"].isin(selected_areas))
].copy()

# 정렬
if sort_by == "환산가 낮은순":
    filtered_df = filtered_df.sort_values("환산가(만원)", ascending=True)
elif sort_by == "환산가 높은순":
    filtered_df = filtered_df.sort_values("환산가(만원)", ascending=False)
elif sort_by == "가격 낮은순":
    filtered_df = filtered_df.sort_values("가격(만원)", ascending=True)
else:
    filtered_df = filtered_df.sort_values("가격(만원)", ascending=False)

# 통계
st.markdown("---")
stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

with stats_col1:
    st.metric("검색된 매물", f"{len(filtered_df)}건")

with stats_col2:
    if len(filtered_df) > 0:
        st.metric("최저 환산가", format_price(int(filtered_df["환산가(만원)"].min()), False))
    else:
        st.metric("최저 환산가", "-")

with stats_col3:
    if len(filtered_df) > 0:
        st.metric("평균 환산가", format_price(int(filtered_df["환산가(만원)"].mean()), False))
    else:
        st.metric("평균 환산가", "-")

with stats_col4:
    sale = len(filtered_df[filtered_df["거래유형"] == "매매"])
    jeonse = len(filtered_df[filtered_df["거래유형"] == "전세"])
    rent = len(filtered_df[filtered_df["거래유형"] == "월세"])
    st.metric("유형 분포", f"매매{sale} / 전세{jeonse} / 월세{rent}")

# 매물 표시
st.markdown("---")
st.markdown(f"### 📊 매물 목록 ({len(filtered_df)}건)")

if len(filtered_df) == 0:
    st.info("선택한 조건에 맞는 매물이 없습니다.")
elif st.session_state.view_mode == "table":
    # 테이블 뷰
    display_df = filtered_df.copy()
    display_df["가격"] = display_df.apply(
        lambda x: f"{format_price(x['가격(만원)'], False)}" + (f" / {int(x['월세(만원)']):,}" if x['월세(만원)'] > 0 else ""),
        axis=1
    )
    display_df["환산가"] = display_df["환산가(만원)"].apply(lambda x: format_price(int(x), False))
    
    st.dataframe(
        display_df[["단지명", "거래유형", "가격", "환산가", "동", "층", "면적", "방향", "설명", "확인일"]],
        use_container_width=True,
        hide_index=True,
        height=600
    )
else:
    # 카드 뷰
    for _, row in filtered_df.iterrows():
        badge_class = "badge-sale" if row["거래유형"] == "매매" else ("badge-jeonse" if row["거래유형"] == "전세" else "badge-rent")
        
        price_text = format_price(row["가격(만원)"], include_unit=False)
        if row["월세(만원)"] > 0:
            price_text += f" / {int(row['월세(만원)']):,}"
        
        converted_text = format_price(int(row["환산가(만원)"]), include_unit=False)
        
        st.markdown(f"""
        <div class="listing-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="badge {badge_class}">{row['거래유형']}</span>
                    <span style="font-weight: 600; font-size: 16px;">{row['단지명']}</span>
                    <div class="price-main" style="margin-top: 8px;">{price_text}</div>
                </div>
                <div style="text-align: right;">
                    <span class="price-converted">환산 {converted_text}</span>
                </div>
            </div>
            <div class="detail-info">
                <span>🏢 {row['동']}</span>
                <span>📐 {row['면적']}</span>
                <span>⬆️ {row['층']}</span>
                <span>🧭 {row['방향']}</span>
                <span style="color: #9ca3af;">📅 {row['확인일']}</span>
            </div>
            <div class="desc-text">{row['설명'] if row['설명'] else '설명 없음'}</div>
        </div>
        """, unsafe_allow_html=True)

# 다운로드
st.markdown("---")
csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="📥 CSV 다운로드",
    data=csv,
    file_name=f"매물목록_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)

st.caption("""
💡 **사용 팁** | 환산가: 월세를 전세로 환산한 가격 (기본 1억당 월 40만원) | 
네이버 서버 차단 시 '데모 모드' 사용 | 인기 단지는 검색 없이 바로 추가 가능
""")
