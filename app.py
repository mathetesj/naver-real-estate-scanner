"""
네이버 부동산 매물 검색기 v3.0
- HTTP 429 에러 해결 (지수 백오프, 세션 유지, 요청 간격 증가)
- 완전히 새로운 UI/UX
- 확장된 프리셋 단지
"""

import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="부동산 매물 검색기",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# 프리셋 단지 데이터 (확장)
# ============================================================
PRESET_COMPLEXES = {
    # 송파구
    "잠실엘스": "19772",
    "헬리오시티": "114743",
    "트리지움": "19764",
    "리센츠": "19765",
    "파크리오": "19763",
    "잠실래미안아이파크": "137980",
    "잠실주공5단지": "8540",
    "올림픽선수촌": "8628",
    # 강남구
    "은마아파트": "8928",
    "대치래미안": "8918",
    "도곡렉슬": "8977",
    "타워팰리스": "8981",
    "개포주공1단지": "8867",
    "래미안대치팰리스": "8918",
    # 서초구
    "래미안퍼스티지": "8894",
    "반포자이": "100078",
    "아크로리버파크": "100096",
    "래미안원베일리": "136068",
    "반포래미안아이파크": "137979",
    "서초그랑자이": "124797",
    # 용산구
    "래미안용산더센트럴": "140927",
    "이촌동LG한강자이": "7853",
    # 마포/영등포
    "마포래미안푸르지오": "102378",
    "여의도자이": "18584",
    # 성동구
    "트리마제": "106811",
    "서울숲리버뷰자이": "114591",
    # 광진구
    "현대프라임": "8684",
    "자양래미안": "8688",
}

# ============================================================
# CSS 스타일 (완전히 새로운 디자인)
# ============================================================
st.markdown("""
<style>
    /* 폰트 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    /* 메인 컨테이너 */
    .main > div {
        padding: 2rem 3rem;
    }
    
    /* 헤더 스타일 */
    .main-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #64748b;
        font-size: 1.1rem;
    }
    
    /* 단지 선택 그리드 */
    .complex-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 10px;
        margin: 1.5rem 0;
    }
    .complex-chip {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
        color: #475569;
    }
    .complex-chip:hover {
        border-color: #818cf8;
        background: #f5f3ff;
    }
    .complex-chip.selected {
        border-color: #6366f1;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 섹션 카드 */
    .section-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* 매물 카드 (새 디자인) */
    .listing-card {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #f1f5f9;
        transition: all 0.25s ease;
    }
    .listing-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-color: #e0e7ff;
    }
    
    /* 거래 유형 태그 */
    .trade-tag {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .trade-sale { background: #fef2f2; color: #dc2626; }
    .trade-jeonse { background: #eff6ff; color: #2563eb; }
    .trade-rent { background: #faf5ff; color: #9333ea; }
    
    /* 가격 */
    .price-text {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin: 8px 0;
    }
    .converted-price {
        display: inline-block;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        color: #0369a1;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
    }
    
    /* 상세 정보 */
    .detail-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-top: 12px;
        font-size: 13px;
        color: #64748b;
    }
    .detail-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* 설명 */
    .desc-box {
        background: #f8fafc;
        border-radius: 10px;
        padding: 12px 14px;
        margin-top: 12px;
        font-size: 13px;
        color: #475569;
        line-height: 1.5;
    }
    
    /* 통계 카드 */
    .stat-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin: 1.5rem 0;
    }
    .stat-box {
        background: white;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .stat-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #1e293b;
    }
    .stat-label {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }
    
    /* 알림 박스 */
    .alert-box {
        padding: 16px 20px;
        border-radius: 12px;
        margin: 1rem 0;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }
    .alert-info {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
    }
    .alert-warning {
        background: #fffbeb;
        border: 1px solid #fcd34d;
        color: #92400e;
    }
    .alert-error {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
    }
    .alert-success {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #16a34a;
    }
    
    /* 선택된 단지 표시 */
    .selected-complex-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #6366f1;
        color: white;
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        margin: 4px;
    }
    .selected-complex-tag .remove {
        cursor: pointer;
        opacity: 0.8;
    }
    .selected-complex-tag .remove:hover {
        opacity: 1;
    }
    
    /* 로딩 상태 */
    .loading-box {
        text-align: center;
        padding: 3rem;
        color: #64748b;
    }
    .loading-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid #e2e8f0;
        border-top: 3px solid #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 빈 상태 */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #94a3b8;
    }
    .empty-state .icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    /* 필터 컨테이너 */
    .filter-container {
        background: white;
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    
    /* Streamlit 기본 요소 커스텀 */
    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    div[data-testid="stMetric"] {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# API 클래스 (세션 유지, 재시도 로직)
# ============================================================
class NaverLandAPI:
    """네이버 부동산 API 클라이언트"""
    
    BASE_URL = "https://new.land.naver.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())
        self.last_request_time = 0
        self.min_interval = 3.0  # 최소 요청 간격 (초)
    
    def _get_headers(self) -> dict:
        """브라우저와 유사한 헤더 생성"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://new.land.naver.com/complexes",
            "Origin": "https://new.land.naver.com",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
    
    def _wait_for_rate_limit(self):
        """요청 간격 조절"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed + random.uniform(0.5, 1.5)
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _request_with_retry(self, url: str, params: dict = None, max_retries: int = 3) -> Optional[dict]:
        """지수 백오프를 사용한 재시도 로직"""
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # 429 에러 시 대기 시간 증가
                    wait = (2 ** attempt) * 5 + random.uniform(1, 3)
                    time.sleep(wait)
                    continue
                else:
                    return None
                    
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        return None
    
    def search_complex(self, keyword: str) -> Tuple[bool, Optional[dict], str]:
        """단지 검색"""
        # 프리셋에서 먼저 검색
        for name, complex_id in PRESET_COMPLEXES.items():
            if keyword in name or name in keyword:
                return True, {"name": name, "id": complex_id}, ""
        
        # API 검색
        url = f"{self.BASE_URL}/search"
        params = {"keyword": keyword}
        
        data = self._request_with_retry(url, params)
        
        if data is None:
            return False, None, "검색 실패 (네트워크 오류 또는 차단)"
        
        suggests = data.get("suggests", [])
        
        for item in suggests:
            if item.get("cortarType") == "AptComplex":
                return True, {
                    "name": item.get("cortarName", keyword),
                    "id": item.get("complexNo") or item.get("cortarNo")
                }, ""
        
        # 다른 형식 시도
        for item in suggests:
            complex_no = item.get("complexNo") or item.get("cortarNo")
            if complex_no:
                return True, {
                    "name": item.get("cortarName", keyword),
                    "id": complex_no
                }, ""
        
        return False, None, "검색 결과가 없습니다"
    
    def get_listings(self, complex_id: str, complex_name: str) -> Tuple[bool, List[dict], str]:
        """매물 목록 조회"""
        url = f"{self.BASE_URL}/articles/complex/{complex_id}"
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
            "complexNo": complex_id
        }
        
        # Referer 업데이트
        self.session.headers["Referer"] = f"https://new.land.naver.com/complexes/{complex_id}"
        
        data = self._request_with_retry(url, params)
        
        if data is None:
            return False, [], "조회 실패"
        
        articles = data.get("articleList", [])
        parsed = [self._parse_article(art, complex_name) for art in articles]
        
        return True, parsed, ""
    
    def _parse_article(self, art: dict, complex_name: str) -> dict:
        """매물 데이터 파싱"""
        # 가격 파싱
        price_str = str(art.get("dealOrWarrantPrc", "0")).replace(",", "").replace(" ", "")
        price = 0
        
        if "억" in price_str:
            parts = price_str.split("억")
            try:
                uk = int(parts[0]) * 10000
                man = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                price = uk + man
            except:
                price = 0
        else:
            try:
                price = int(price_str) if price_str else 0
            except:
                price = 0
        
        # 월세 파싱
        rent_str = str(art.get("rentPrc", "0")).replace(",", "")
        try:
            rent = int(rent_str) if rent_str else 0
        except:
            rent = 0
        
        return {
            "단지명": complex_name,
            "거래유형": art.get("tradeTypeName", ""),
            "가격": price,
            "월세": rent,
            "동": art.get("buildingName", "-"),
            "층": art.get("floorInfo", "-"),
            "면적": art.get("areaName", "-"),
            "방향": art.get("direction", "-"),
            "설명": art.get("articleFeatureDesc", ""),
            "확인일": art.get("articleConfirmYmd", ""),
        }


# ============================================================
# 유틸리티 함수
# ============================================================

def format_price(val: int) -> str:
    """가격 포맷팅"""
    if val == 0:
        return "-"
    uk = val // 10000
    man = val % 10000
    if uk > 0 and man > 0:
        return f"{uk}억 {man:,}"
    elif uk > 0:
        return f"{uk}억"
    return f"{man:,}만원"


def calc_converted(price: int, rent: int, rate: int) -> int:
    """환산가 계산"""
    if rent > 0:
        return int(price + (rent / rate) * 10000)
    return price


def generate_demo_data(names: List[str]) -> pd.DataFrame:
    """데모 데이터 생성"""
    if not names:
        names = ["샘플단지"]
    
    data = []
    for _ in range(30):
        name = random.choice(names)
        trade = random.choices(["매매", "전세", "월세"], weights=[0.4, 0.4, 0.2])[0]
        area = random.choice(["59㎡", "74㎡", "84㎡", "102㎡"])
        area_num = int(area.replace("㎡", ""))
        
        if trade == "매매":
            price = random.randint(140000 + area_num * 1500, 180000 + area_num * 2000)
            rent = 0
        elif trade == "전세":
            price = random.randint(70000 + area_num * 800, 100000 + area_num * 1000)
            rent = 0
        else:
            price = random.randint(10000, 50000)
            rent = random.randint(80, 300)
        
        data.append({
            "단지명": name,
            "거래유형": trade,
            "가격": price,
            "월세": rent,
            "동": f"{random.randint(101, 115)}동",
            "층": f"{random.choice(['저','중','고'])}/{random.randint(20,35)}",
            "면적": area,
            "방향": random.choice(["남향", "남동향", "동향"]),
            "설명": random.choice(["올수리", "로얄층", "급매", "깨끗함", "역세권"]),
            "확인일": datetime.now().strftime("%Y-%m-%d"),
        })
    
    return pd.DataFrame(data)


# ============================================================
# 세션 상태 초기화
# ============================================================

if "selected_complexes" not in st.session_state:
    st.session_state.selected_complexes = {}  # {name: id}

if "listings_data" not in st.session_state:
    st.session_state.listings_data = None

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

if "api_client" not in st.session_state:
    st.session_state.api_client = NaverLandAPI()

if "fetch_errors" not in st.session_state:
    st.session_state.fetch_errors = []


# ============================================================
# 메인 UI
# ============================================================

# 헤더
st.markdown("""
<div class="main-header">
    <h1>🏢 부동산 매물 검색기</h1>
    <p>관심 단지를 선택하고 매물을 환산가 기준으로 비교해보세요</p>
</div>
""", unsafe_allow_html=True)

# 단지 선택 섹션
st.markdown("### 📍 단지 선택")

# 지역별 탭
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 송파구", "💎 강남구", "🌟 서초구", "🔍 기타 지역", "✏️ 직접 검색"])

preset_by_region = {
    "송파구": ["잠실엘스", "헬리오시티", "트리지움", "리센츠", "파크리오", "올림픽선수촌"],
    "강남구": ["은마아파트", "대치래미안", "도곡렉슬", "타워팰리스", "개포주공1단지"],
    "서초구": ["래미안퍼스티지", "반포자이", "아크로리버파크", "래미안원베일리", "서초그랑자이"],
    "기타": ["마포래미안푸르지오", "여의도자이", "트리마제", "현대프라임"]
}

def render_preset_buttons(region_name: str, presets: List[str]):
    cols = st.columns(min(len(presets), 4))
    for i, name in enumerate(presets):
        with cols[i % 4]:
            is_selected = name in st.session_state.selected_complexes
            btn_type = "primary" if is_selected else "secondary"
            if st.button(
                f"{'✓ ' if is_selected else ''}{name}",
                key=f"preset_{region_name}_{name}",
                type=btn_type,
                use_container_width=True
            ):
                if is_selected:
                    del st.session_state.selected_complexes[name]
                else:
                    st.session_state.selected_complexes[name] = PRESET_COMPLEXES.get(name, "")
                st.session_state.listings_data = None
                st.rerun()

with tab1:
    render_preset_buttons("송파", preset_by_region["송파구"])

with tab2:
    render_preset_buttons("강남", preset_by_region["강남구"])

with tab3:
    render_preset_buttons("서초", preset_by_region["서초구"])

with tab4:
    render_preset_buttons("기타", preset_by_region["기타"])

with tab5:
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        search_input = st.text_input(
            "단지명 검색",
            placeholder="예: 잠실엘스, 헬리오시티...",
            label_visibility="collapsed"
        )
    with search_col2:
        search_btn = st.button("검색", use_container_width=True)
    
    if search_btn and search_input:
        with st.spinner("검색 중..."):
            api = st.session_state.api_client
            success, data, error = api.search_complex(search_input)
            
            if success and data:
                if data["name"] not in st.session_state.selected_complexes:
                    st.session_state.selected_complexes[data["name"]] = data["id"]
                    st.session_state.listings_data = None
                    st.success(f"✓ {data['name']} 추가됨")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("이미 선택된 단지입니다")
            else:
                st.error(f"❌ {error}")

# 선택된 단지 표시
if st.session_state.selected_complexes:
    st.markdown("#### 선택된 단지")
    
    selected_html = ""
    for name in st.session_state.selected_complexes.keys():
        selected_html += f'<span class="selected-complex-tag">{name}</span>'
    st.markdown(selected_html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 매물 조회", type="primary", use_container_width=True):
            st.session_state.listings_data = None
            st.session_state.fetch_errors = []
            st.rerun()
    with col2:
        if st.button("🗑️ 전체 삭제", use_container_width=True):
            st.session_state.selected_complexes = {}
            st.session_state.listings_data = None
            st.rerun()

st.markdown("---")

# 설정
with st.expander("⚙️ 설정", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        conversion_rate = st.slider(
            "환산 비율 (1억당 월세)",
            min_value=30, max_value=60, value=40, step=5,
            help="월세를 전세로 환산하는 비율 (기본: 1억당 40만원)"
        )
    with col2:
        st.session_state.demo_mode = st.toggle(
            "데모 모드",
            value=st.session_state.demo_mode,
            help="네이버 차단 시 샘플 데이터로 기능 확인"
        )

# 데모 모드 알림
if st.session_state.demo_mode:
    st.markdown("""
    <div class="alert-box alert-warning">
        <span>⚠️</span>
        <div><strong>데모 모드</strong> - 샘플 데이터를 표시합니다. 실제 데이터는 데모 모드를 끄세요.</div>
    </div>
    """, unsafe_allow_html=True)

# 단지 미선택 시
if not st.session_state.selected_complexes:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🏠</div>
        <h3>단지를 선택해주세요</h3>
        <p>위에서 관심 단지를 클릭하거나 직접 검색하세요</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 데이터 로딩
df = None

if st.session_state.demo_mode:
    names = list(st.session_state.selected_complexes.keys())
    df = generate_demo_data(names)
else:
    if st.session_state.listings_data is not None:
        df = st.session_state.listings_data
    else:
        all_data = []
        errors = []
        api = st.session_state.api_client
        
        progress_container = st.empty()
        status_container = st.empty()
        
        complexes = list(st.session_state.selected_complexes.items())
        total = len(complexes)
        
        for i, (name, cid) in enumerate(complexes):
            progress_container.progress((i + 1) / total, text=f"📡 {name} 조회 중... ({i+1}/{total})")
            status_container.caption(f"⏳ 요청 간격 준수 중 (3초+)")
            
            success, listings, error = api.get_listings(cid, name)
            
            if success:
                all_data.extend(listings)
            else:
                errors.append(f"{name}: {error}")
        
        progress_container.empty()
        status_container.empty()
        
        st.session_state.fetch_errors = errors
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.session_state.listings_data = df

# 에러 표시
if st.session_state.fetch_errors:
    st.markdown(f"""
    <div class="alert-box alert-error">
        <span>⚠️</span>
        <div>
            <strong>일부 조회 실패</strong><br>
            {', '.join(st.session_state.fetch_errors)}<br>
            <small>네이버 서버 차단일 수 있습니다. 잠시 후 다시 시도하거나 데모 모드를 사용하세요.</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 데이터 없음
if df is None or df.empty:
    st.markdown("""
    <div class="alert-box alert-info">
        <span>ℹ️</span>
        <div>조회된 매물이 없습니다. '매물 조회' 버튼을 눌러주세요.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 환산가 계산
df["환산가"] = df.apply(lambda x: calc_converted(x["가격"], x["월세"], conversion_rate), axis=1)

# 필터
st.markdown("### 🔍 필터 및 정렬")

fcol1, fcol2, fcol3, fcol4 = st.columns(4)

with fcol1:
    trade_opts = df["거래유형"].unique().tolist()
    selected_trades = st.multiselect("거래유형", trade_opts, default=trade_opts)

with fcol2:
    complex_opts = df["단지명"].unique().tolist()
    selected_names = st.multiselect("단지", complex_opts, default=complex_opts)

with fcol3:
    area_opts = df["면적"].unique().tolist()
    selected_areas = st.multiselect("면적", area_opts, default=area_opts)

with fcol4:
    sort_by = st.selectbox("정렬", ["환산가 낮은순", "환산가 높은순", "가격 낮은순", "가격 높은순"])

# 필터 적용
filtered = df[
    (df["거래유형"].isin(selected_trades)) &
    (df["단지명"].isin(selected_names)) &
    (df["면적"].isin(selected_areas))
].copy()

# 정렬
sort_col = "환산가" if "환산가" in sort_by else "가격"
sort_asc = "낮은순" in sort_by
filtered = filtered.sort_values(sort_col, ascending=sort_asc)

# 통계
st.markdown("### 📊 통계")

stat_cols = st.columns(4)
with stat_cols[0]:
    st.metric("총 매물", f"{len(filtered)}건")
with stat_cols[1]:
    if len(filtered) > 0:
        st.metric("최저 환산가", format_price(int(filtered["환산가"].min())))
    else:
        st.metric("최저 환산가", "-")
with stat_cols[2]:
    if len(filtered) > 0:
        st.metric("평균 환산가", format_price(int(filtered["환산가"].mean())))
    else:
        st.metric("평균 환산가", "-")
with stat_cols[3]:
    sale_n = len(filtered[filtered["거래유형"] == "매매"])
    jeonse_n = len(filtered[filtered["거래유형"] == "전세"])
    rent_n = len(filtered[filtered["거래유형"] == "월세"])
    st.metric("유형별", f"매매 {sale_n} | 전세 {jeonse_n} | 월세 {rent_n}")

# 매물 목록
st.markdown(f"### 🏠 매물 목록 ({len(filtered)}건)")

# 보기 모드 선택
view_mode = st.radio("보기 모드", ["카드", "테이블"], horizontal=True, label_visibility="collapsed")

if len(filtered) == 0:
    st.info("조건에 맞는 매물이 없습니다.")
elif view_mode == "테이블":
    display_df = filtered.copy()
    display_df["가격표시"] = display_df.apply(
        lambda x: f"{format_price(x['가격'])}" + (f" / {int(x['월세']):,}" if x['월세'] > 0 else ""),
        axis=1
    )
    display_df["환산가표시"] = display_df["환산가"].apply(lambda x: format_price(int(x)))
    
    st.dataframe(
        display_df[["단지명", "거래유형", "가격표시", "환산가표시", "동", "층", "면적", "방향", "설명"]].rename(
            columns={"가격표시": "가격", "환산가표시": "환산가"}
        ),
        use_container_width=True,
        hide_index=True,
        height=500
    )
else:
    for _, row in filtered.iterrows():
        # 거래유형 태그
        trade_class = "trade-sale" if row["거래유형"] == "매매" else ("trade-jeonse" if row["거래유형"] == "전세" else "trade-rent")
        
        # 가격 텍스트
        price_txt = format_price(row["가격"])
        if row["월세"] > 0:
            price_txt += f" / {int(row['월세']):,}"
        
        converted_txt = format_price(int(row["환산가"]))
        
        st.markdown(f"""
        <div class="listing-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span class="trade-tag {trade_class}">{row["거래유형"]}</span>
                    <span style="font-weight: 600; margin-left: 8px;">{row["단지명"]}</span>
                    <div class="price-text">{price_txt}</div>
                </div>
                <div>
                    <span class="converted-price">환산 {converted_txt}</span>
                </div>
            </div>
            <div class="detail-row">
                <span class="detail-item">🏢 {row["동"]}</span>
                <span class="detail-item">📐 {row["면적"]}</span>
                <span class="detail-item">⬆️ {row["층"]}</span>
                <span class="detail-item">🧭 {row["방향"]}</span>
                <span class="detail-item" style="color: #94a3b8;">📅 {row["확인일"]}</span>
            </div>
            <div class="desc-box">{row["설명"] if row["설명"] else "설명 없음"}</div>
        </div>
        """, unsafe_allow_html=True)

# 다운로드
st.markdown("---")
csv_data = filtered.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    "📥 CSV 다운로드",
    csv_data,
    f"매물_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    "text/csv"
)

# 푸터
st.caption("""
💡 **Tip**: 환산가는 월세를 전세로 환산한 가격입니다 (기본 1억당 월40만원) | 
네이버 서버가 요청을 차단할 경우 '데모 모드'를 사용하세요 | 
요청 간격은 차단 방지를 위해 3초 이상으로 설정됩니다
""")
