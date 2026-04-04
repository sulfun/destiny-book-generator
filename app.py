"""
운명책 자동 생성기 - Streamlit 웹앱
Destiny Book Generator Web App

고객용: 출생 정보 입력 폼
관리자용: 주문 관리 대시보드
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

# 모듈 경로
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CITY_DATABASE
from scrapers.saju import calculate_saju
from scrapers.astrology import calculate_astrology
from scrapers.numerology import calculate_numerology
from scrapers.human_design import calculate_human_design
from interpreter import generate_all_chapters, generate_all_chapters_offline
from pdf_generator import generate_pdf

try:
    from notion_client import Client as NotionClient
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

# === 앱 설정 ===
st.set_page_config(
    page_title="운명책 | The Book of Destiny",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 데이터 디렉토리 (로컬 폴백용) ===
OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Notion 연결 ===
NOTION_DB_ID = "231274d036864a249614327bb9fdeed9"

@st.cache_resource(ttl=300)
def get_notion_client():
    """Notion 클라이언트 생성"""
    if not NOTION_AVAILABLE:
        return None
    try:
        token = st.secrets.get("notion_token", "")
        if not token:
            return None
        return NotionClient(auth=token)
    except Exception as e:
        st.sidebar.warning(f"Notion 연결 실패: {e}")
        return None

# === 스타일 ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&display=swap');

    .main-title {
        font-family: 'Noto Serif KR', serif;
        text-align: center;
        color: #1a1a2e;
        font-size: 2.5rem;
        margin-bottom: 0;
    }
    .sub-title {
        text-align: center;
        color: #c9a96e;
        font-size: 1.1rem;
        margin-top: 0;
        letter-spacing: 3px;
    }
    .gold-divider {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #c9a96e, transparent);
        margin: 20px 0;
    }
    .info-box {
        background: #f8f6f0;
        border-left: 3px solid #c9a96e;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
    }
    .price-tag {
        font-family: 'Noto Serif KR', serif;
        text-align: center;
        font-size: 1.8rem;
        color: #1a1a2e;
        margin: 20px 0;
    }
    .status-pending { color: #e67e22; font-weight: bold; }
    .status-processing { color: #3498db; font-weight: bold; }
    .status-complete { color: #27ae60; font-weight: bold; }
    .status-delivered { color: #8e44ad; font-weight: bold; }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: #1a1a2e;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# === 도시 목록 ===
CITY_OPTIONS = {
    "서울": ("서울", 37.5665, 126.9780, "Asia/Seoul"),
    "부산": ("부산", 35.1796, 129.0756, "Asia/Seoul"),
    "대구": ("대구", 35.8714, 128.6014, "Asia/Seoul"),
    "인천": ("인천", 37.4563, 126.7052, "Asia/Seoul"),
    "대전": ("대전", 36.3504, 127.3845, "Asia/Seoul"),
    "광주": ("광주", 35.1595, 126.8526, "Asia/Seoul"),
    "수원": ("수원", 37.2636, 127.0286, "Asia/Seoul"),
    "제주": ("제주", 33.4996, 126.5312, "Asia/Seoul"),
    "New York": ("New York", 40.7128, -74.0060, "America/New_York"),
    "Los Angeles": ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    "Tokyo": ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    "London": ("London", 51.5074, -0.1278, "Europe/London"),
    "Paris": ("Paris", 48.8566, 2.3522, "Europe/Paris"),
    "기타 (직접 입력)": None,
}


def _notion_status_map(status):
    """내부 상태 → Notion 상태 매핑"""
    mapping = {
        "pending": "접수완료",
        "processing": "차트계산중",
        "interpreting": "해석생성중",
        "pdf_generating": "PDF생성중",
        "complete": "완료",
        "delivered": "완료",
        "error": "오류",
    }
    return mapping.get(status, "접수완료")


def _notion_status_reverse(notion_status):
    """Notion 상태 → 내부 상태 매핑"""
    mapping = {
        "접수완료": "pending",
        "차트계산중": "processing",
        "해석생성중": "processing",
        "PDF생성중": "processing",
        "완료": "complete",
        "오류": "error",
    }
    return mapping.get(notion_status, "pending")


def save_order(order_data):
    """주문 저장 → Notion"""
    order_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    order_data["order_id"] = order_id

    notion = get_notion_client()
    if notion:
        try:
            gender_kr = "여성" if order_data.get("gender") in ["여", "여성"] else "남성"
            properties = {
                "주문번호": {"title": [{"text": {"content": order_id}}]},
                "상태": {"select": {"name": "접수완료"}},
                "이름(한글)": {"rich_text": [{"text": {"content": order_data.get("name_kr", "")}}]},
                "이름(영문)": {"rich_text": [{"text": {"content": order_data.get("name_en", "")}}]},
                "이메일": {"email": order_data.get("email", "") or None},
                "전화번호": {"phone_number": order_data.get("phone", "") or None},
                "성별": {"select": {"name": gender_kr}},
                "생년": {"number": int(order_data.get("year", 0))},
                "생월": {"number": int(order_data.get("month", 0))},
                "생일": {"number": int(order_data.get("day", 0))},
                "생시": {"number": int(order_data.get("hour", 0))},
                "생분": {"number": int(order_data.get("minute", 0))},
                "출생도시": {"rich_text": [{"text": {"content": order_data.get("city", "")}}]},
                "메모": {"rich_text": [{"text": {"content": order_data.get("notes", "")}}]},
            }
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties=properties
            )
        except Exception as e:
            st.warning(f"Notion 저장 실패: {e}")
    return order_id


def load_orders():
    """모든 주문 불러오기 ← Notion"""
    notion = get_notion_client()
    if notion is None:
        return []
    try:
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            sorts=[{"property": "접수일시", "direction": "descending"}]
        )
        orders = []
        for page in results.get("results", []):
            props = page["properties"]
            order = {
                "page_id": page["id"],
                "order_id": _get_title(props.get("주문번호", {})),
                "status": _notion_status_reverse(
                    _get_select(props.get("상태", {}))
                ),
                "status_kr": _get_select(props.get("상태", {})),
                "name_kr": _get_rich_text(props.get("이름(한글)", {})),
                "name_en": _get_rich_text(props.get("이름(영문)", {})),
                "email": props.get("이메일", {}).get("email", ""),
                "phone": props.get("전화번호", {}).get("phone_number", ""),
                "gender": _get_select(props.get("성별", {})),
                "year": int(props.get("생년", {}).get("number", 0) or 0),
                "month": int(props.get("생월", {}).get("number", 0) or 0),
                "day": int(props.get("생일", {}).get("number", 0) or 0),
                "hour": int(props.get("생시", {}).get("number", 0) or 0),
                "minute": int(props.get("생분", {}).get("number", 0) or 0),
                "city": _get_rich_text(props.get("출생도시", {})),
                "notes": _get_rich_text(props.get("메모", {})),
                "created_at": page.get("created_time", ""),
            }
            orders.append(order)
        return orders
    except Exception as e:
        st.warning(f"주문 로드 실패: {e}")
        return []


def _get_title(prop):
    """Notion title 속성에서 텍스트 추출"""
    try:
        return prop["title"][0]["plain_text"]
    except (KeyError, IndexError):
        return ""

def _get_rich_text(prop):
    """Notion rich_text 속성에서 텍스트 추출"""
    try:
        return prop["rich_text"][0]["plain_text"]
    except (KeyError, IndexError):
        return ""

def _get_select(prop):
    """Notion select 속성에서 값 추출"""
    try:
        return prop["select"]["name"]
    except (KeyError, TypeError):
        return ""


def update_order_status(order_id, new_status):
    """주문 상태 업데이트 → Notion"""
    notion = get_notion_client()
    if notion is None:
        return
    try:
        # order_id로 페이지 찾기
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "주문번호", "title": {"equals": str(order_id)}}
        )
        pages = results.get("results", [])
        if pages:
            page_id = pages[0]["id"]
            notion.pages.update(
                page_id=page_id,
                properties={
                    "상태": {"select": {"name": _notion_status_map(new_status)}}
                }
            )
    except Exception as e:
        st.warning(f"상태 업데이트 실패: {e}")


def save_chart_data(order_id, chart_data_json):
    """차트 데이터를 Notion에 저장"""
    notion = get_notion_client()
    if notion is None:
        return
    try:
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "주문번호", "title": {"equals": str(order_id)}}
        )
        pages = results.get("results", [])
        if pages:
            page_id = pages[0]["id"]
            # Notion rich_text 최대 2000자이므로 필요시 잘라서 저장
            truncated = chart_data_json[:2000] if len(chart_data_json) > 2000 else chart_data_json
            notion.pages.update(
                page_id=page_id,
                properties={
                    "차트데이터": {"rich_text": [{"text": {"content": truncated}}]}
                }
            )
    except Exception as e:
        st.warning(f"차트 데이터 저장 실패: {e}")


def collect_charts(data):
    """차트 데이터 수집"""
    city_info = CITY_OPTIONS.get(data["city"])
    if city_info:
        city_name, lat, lon, tz = city_info
    else:
        lat, lon, tz = data.get("lat", 37.5665), data.get("lon", 126.978), data.get("tz", "Asia/Seoul")
        city_name = data.get("city_custom", "Unknown")

    all_data = {}

    # 사주
    try:
        all_data["saju"] = calculate_saju(
            data["year"], data["month"], data["day"], data["hour"], data["gender"]
        )
    except Exception as e:
        all_data["saju"] = {"error": str(e)}

    # 점성학
    try:
        all_data["astrology"] = calculate_astrology(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], city_name, lat, lon, tz
        )
    except Exception as e:
        all_data["astrology"] = {"error": str(e)}

    # 수비학
    try:
        all_data["numerology"] = calculate_numerology(
            data["year"], data["month"], data["day"], data.get("name_en", "")
        )
    except Exception as e:
        all_data["numerology"] = {"error": str(e)}

    # 휴먼디자인
    try:
        all_data["humandesign"] = calculate_human_design(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], city_name, lat, lon
        )
    except Exception as e:
        all_data["humandesign"] = {"error": str(e)}

    return all_data


# ========================================
# 페이지 라우팅
# ========================================

def page_customer():
    """고객 주문 페이지"""
    st.markdown('<h1 class="main-title">운명책</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">THE BOOK OF DESTINY</p>', unsafe_allow_html=True)
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === HERO SECTION ===
    st.markdown("""
    <div style="text-align: center; margin: 10px 0 30px 0;">
        <p style="font-family: 'Noto Serif KR', serif; font-size: 1.15rem; color: #555;
                  line-height: 1.9; max-width: 600px; margin: 0 auto;">
        세상에 단 하나뿐인,<br>
        <strong style="color: #1a1a2e;">나로 살기 위한 책</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === WHAT IT IS ===
    st.markdown("""
    <div style="max-width: 640px; margin: 0 auto; line-height: 2; color: #333; font-size: 0.95rem;">

    <p>이 책은 <strong>"언제 돈이 들어온다, 언제 결혼한다"</strong> 같은 운세책이 아닙니다.</p>

    <p>동서양 12종 운명학 시스템과 AI 분석을 결합하여<br>
    <em style="color: #1a1a2e; font-weight: 600;">"한 인간의 구조와 가능성을 해석하는 운명 설계 보고서"</em>를 제작합니다.</p>

    <p style="color: #888; font-size: 0.88rem; letter-spacing: 0.5px;">
    사주명리 · 서양점성학 · 베딕점성학 · 수비학 · 휴먼디자인 · 자미두수 · 타로 · 카발라 외</p>

    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === QUESTIONS THIS BOOK ANSWERS ===
    st.markdown("""
    <div style="max-width: 640px; margin: 0 auto; padding: 20px 0;">
        <p style="font-family: 'Noto Serif KR', serif; text-align: center;
                  font-size: 1.05rem; color: #1a1a2e; margin-bottom: 20px;">
                  이 책이 다루는 질문들</p>
        <div style="line-height: 2.2; color: #444; font-size: 0.93rem;">
            <p style="margin: 8px 0;">나는 왜 이런 삶을 살고 있는가</p>
            <p style="margin: 8px 0;">나의 타고난 성향과 재능은 무엇인가</p>
            <p style="margin: 8px 0;">나에게 반복되는 패턴은 무엇인가</p>
            <p style="margin: 8px 0;">어떤 선택을 할 때 인생이 크게 확장되는가</p>
            <p style="margin: 8px 0;">앞으로의 3~5년은 어떤 흐름으로 전개되는가</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === BETA TESTER FEEDBACK ===
    st.markdown("### 베타 리더들의 이야기")

    # --- 장세진 ---
    st.markdown("""
> *"운명책은 감동적이었습니다. 점을 볼 때처럼 잘 맞거나 명료한 감상을 예상했는데, 그와는 전혀 다른 벅찬 감동과 울림이 있었습니다."*

> *"모든 챕터가 설명은 다르지만 한 가지 이야기를 하고 있었고, 저라는 사람에 대해 다시금 돌아보고 앞날을 결심하는 계기가 되었습니다."*

> *"책에서는 제 안의 모순을 모두 담으면서도 그것의 통합을 말하더라고요. 그 지점에서 의문이 풀리는 기분이었습니다."*

— 199x년 익산 장\*진
""")

    st.markdown("---")

    # --- 이경은 ---
    st.markdown("""
> *"위의 문구들을 읽자 가슴이 뛰었습니다. 맞다 이게 나였지.. 하는 두근거림, 오랫동안 잊고 살던 꿈을 다시금 떠올린 기분이었습니다. 창문으로 피터팬이 찾아오는 그 순간처럼요."*

> *"이 내용들에서는 놀라기도 했고, 반성도 했습니다. 제 커리어가 제대로 된 게 없고 그때그때 종구난방으로 살아오면서도 달리 방법이 없던 것을 최근 들어 정비의 필요성을 느끼던 중이었거든요."*

> *"감정의 기복을 따라 결정하는 습관을 멈추고, 감정이 최대 무기가 될 것이지만 그만큼 감정 상태를 안정적으로 잘 다스려야한다는 것을 알았습니다. 잘 해낸다면 그것이 저의 가장 정확한 나침반이 될 것을 믿습니다."*

— 199x년 서울 이\*은
""")

    st.markdown("---")

    # --- 김소연 ---
    st.markdown("""
> *"가장 집중해서 읽은 곳은 12장 통합해석과 14장 결론입니다. 이런 멋진 말만 가득해도 되나 싶을 정도로 감동적이었고 모든 설명이 마음에 깊이 닿았습니다."*

> *"본질을 보고, 이원성을 통합하고, 감정을 잘 다뤄 나침반이 되게 하고, 진리를 세상에 나누는 삶. 이것들은 제가 꿈꾸는 너무나 멋진 삶이자 최대 숙제입니다."*

> *"28p 맺음말의 문구에서는 눈물을 참을 수가 없었습니다. 제 운명은 이미 아름답게 설계되었다니.. 태어나 처음 들어본 말입니다."*

— 198x년 전주 김\*연
""")


    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === WHAT MAKES IT DIFFERENT ===
    st.markdown("""
    <div style="max-width: 640px; margin: 0 auto; padding: 20px 0;
                line-height: 2; color: #333; font-size: 0.93rem;">

    <p style="font-family: 'Noto Serif KR', serif; text-align: center;
              font-size: 1.05rem; color: #1a1a2e; margin-bottom: 20px;">
              기존 서비스와 무엇이 다른가</p>

    <p>대부분의 운세 앱은 DB에 입력된 경우의 수 조합으로 결과를 출력합니다.
    같은 생년월일이면 같은 답이 나옵니다.</p>

    <p>이 책은 다릅니다. 12종의 운명학 체계를 교차 분석하고,
    20년 이상의 실전 해석 경험을 학습한 AI가
    <strong>단 한 사람만을 위한 해석</strong>을 생성합니다.</p>

    <p>인간이 태어나기 전 설계한 사명은 물질세계에서 단 하나의 직업으로만
    성취되는 것이 아닙니다. 힐러로 태어난 사람은 의사, 상담가, 교육자,
    무엇이든 될 수 있습니다. 이 책은 표면적 직업이 아니라
    <em>당신이라는 존재의 구조와 방향성</em>을 읽어냅니다.</p>

    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === PROCESS ===
    st.markdown("""
    <div style="max-width: 640px; margin: 0 auto; padding: 20px 0;">
        <p style="font-family: 'Noto Serif KR', serif; text-align: center;
                  font-size: 1.05rem; color: #1a1a2e; margin-bottom: 20px;">
                  진행 방식</p>
        <div style="display: flex; justify-content: center; gap: 30px; text-align: center;
                    color: #555; font-size: 0.88rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 140px;">
                <p style="font-size: 1.5rem; margin-bottom: 5px;">01</p>
                <p style="color: #c9a96e; font-weight: 600;">신청서 작성</p>
                <p>출생 정보 입력 및 제출</p>
            </div>
            <div style="flex: 1; min-width: 140px;">
                <p style="font-size: 1.5rem; margin-bottom: 5px;">02</p>
                <p style="color: #c9a96e; font-weight: 600;">제작 (1~3일)</p>
                <p>12종 차트 분석 + AI 해석 생성</p>
            </div>
            <div style="flex: 1; min-width: 140px;">
                <p style="font-size: 1.5rem; margin-bottom: 5px;">03</p>
                <p style="color: #c9a96e; font-weight: 600;">운명책 수령</p>
                <p>PDF 이메일 발송</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === PRICING ===
    st.markdown("""
    <div style="text-align: center; margin: 25px 0;">
        <p style="font-family: 'Noto Serif KR', serif; font-size: 1rem; color: #999;
                  text-decoration: line-through; margin-bottom: 2px;">₩ 199,000</p>
        <p style="font-family: 'Noto Serif KR', serif; font-size: 2.2rem; color: #1a1a2e;
                  margin: 0; font-weight: 700;">₩ 119,000</p>
        <p style="font-size: 0.85rem; color: #c9a96e; letter-spacing: 1px; margin-top: 4px;">
            한정 33권 · BETA EDITION</p>
        <p style="font-size: 0.78rem; color: #aaa; margin-top: 8px;">
            정가 출시 후에는 이 가격으로 구매할 수 없습니다</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === NOTES ===
    st.markdown("""
    <div style="max-width: 640px; margin: 0 auto; padding: 15px 0;
                color: #888; font-size: 0.82rem; line-height: 1.9;">
    <p><strong style="color: #666;">참고사항</strong></p>
    <p>· 태어난 시간과 장소를 정확히 아는 것이 매우 중요합니다</p>
    <p>· 영문 이름은 수비학 분석에 사용됩니다 (선택사항)</p>
    <p>· 제작은 신청 + 입금 순으로 진행됩니다</p>
    <p>· 현재 수작업 검증을 병행하고 있어 제작 기간이 다소 소요될 수 있습니다</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # === 입력 폼 ===
    st.subheader("📋 출생 정보 입력")

    with st.form("birth_info_form"):
        col1, col2 = st.columns(2)

        with col1:
            name_kr = st.text_input("이름 (한국어) *", placeholder="홍길동")
            name_en = st.text_input("이름 (영문)", placeholder="Gildong Hong", help="수비학 분석에 사용")
            email = st.text_input("이메일 *", placeholder="you@email.com", help="완성된 운명책을 보내드립니다")

        with col2:
            gender = st.selectbox("성별 *", ["여성", "남성"])
            phone = st.text_input("연락처", placeholder="010-0000-0000")

        st.markdown("---")
        st.subheader("🗓️ 출생 일시")

        col3, col4, col5 = st.columns(3)
        with col3:
            birth_date = st.date_input(
                "출생일 *",
                value=date(1990, 1, 1),
                min_value=date(1920, 1, 1),
                max_value=date(2010, 12, 31)
            )
        with col4:
            birth_hour = st.selectbox("출생 시 *", list(range(0, 24)),
                                       format_func=lambda x: f"{x:02d}시")
        with col5:
            birth_minute = st.selectbox("출생 분 *", [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
                                         format_func=lambda x: f"{x:02d}분")

        st.subheader("📍 출생지")
        city = st.selectbox("출생 도시 *", list(CITY_OPTIONS.keys()))

        if city == "기타 (직접 입력)":
            col6, col7, col8 = st.columns(3)
            with col6:
                city_custom = st.text_input("도시명", placeholder="Beijing")
            with col7:
                lat_custom = st.number_input("위도", value=37.5665, format="%.4f")
            with col8:
                lon_custom = st.number_input("경도", value=126.9780, format="%.4f")
            tz_custom = st.text_input("타임존", value="Asia/Seoul",
                                       help="예: Asia/Seoul, America/New_York, Europe/London")

        st.markdown("---")
        notes = st.text_area(
            "추가 메모 (선택)",
            placeholder="일, 직업, 소명, 원가족, 파트너 문제 등 현재의 고민을 상세히 기술해 주십시오.",
            help="정보가 상세할수록 해석의 깊이가 달라집니다. 과거-현재의 직업/경력/이력은 미래의 향방을 예측하고 조언을 출력하는 데 큰 정보가 됩니다.",
            max_chars=2000
        )

        st.markdown("---")

        privacy_agreed = st.checkbox("개인정보 수집 및 이용에 동의합니다.")

        st.markdown("""
<details style="font-size: 0.82rem; color: #888; margin-top: -8px; margin-bottom: 12px;">
<summary style="cursor: pointer; color: #c9a96e;">개인정보 수집·이용 동의 안내 (자세히 보기)</summary>

**수집 항목**: 이름, 이메일, 전화번호, 성별, 생년월일 및 출생시간, 출생지
**수집 목적**: 운명책 제작 및 배송, 주문 확인 연락, 고객 문의 응대
**보유 기간**: 주문 완료 후 **1년** 또는 동의 철회 시까지
**동의 거부 시**: 운명책 신청이 불가합니다.

수집된 개인정보는 상기 목적 외에 사용되지 않으며, 제3자에게 제공되지 않습니다.
동의 철회를 원하시면 **help@sulfun.com**으로 연락해 주세요.
</details>
""", unsafe_allow_html=True)

        submitted = st.form_submit_button("✨ 운명책 신청하기", use_container_width=True)

        if submitted:
            # 유효성 검사
            if not privacy_agreed:
                st.error("개인정보 수집 및 이용에 동의해 주세요.")
            elif not name_kr:
                st.error("이름을 입력해주세요.")
            elif not email:
                st.error("이메일을 입력해주세요.")
            else:
                order_data = {
                    "name_kr": name_kr,
                    "name_en": name_en,
                    "email": email,
                    "phone": phone,
                    "gender": "여" if gender == "여성" else "남",
                    "year": birth_date.year,
                    "month": birth_date.month,
                    "day": birth_date.day,
                    "hour": birth_hour,
                    "minute": birth_minute,
                    "city": city,
                    "notes": notes,
                }

                if city == "기타 (직접 입력)":
                    order_data["city_custom"] = city_custom
                    order_data["lat"] = lat_custom
                    order_data["lon"] = lon_custom
                    order_data["tz"] = tz_custom

                order_id = save_order(order_data)

                st.success(f"""
                ✅ **주문이 접수되었습니다!**

                주문번호: `{order_id}`

                운명책은 입금 확인 후 7일 이내에 이메일로 전달됩니다.
                문의: help@sulfun.com
                """)

    # 하단 안내
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
    이수진 | 20년 이상의 동서양 운명학 연구 · AI 통합 분석 시스템 설계<br>
    Produced by SULFUN | © 2026 All rights reserved<br>
    문의: help@sulfun.com
    </div>
    """, unsafe_allow_html=True)


def page_admin():
    """관리자 대시보드"""
    st.title("🔐 관리자 대시보드")

    # API 키 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        api_key = st.text_input("Anthropic API Key", type="password",
                                value=os.environ.get("ANTHROPIC_API_KEY", ""))
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            st.success("API 키 설정됨")

    # 주문 목록
    orders = load_orders()

    if not orders:
        st.info("아직 주문이 없습니다.")
        return

    # 상태별 필터
    status_filter = st.selectbox(
        "상태 필터",
        ["전체", "pending", "processing", "complete", "delivered"],
        format_func=lambda x: {
            "전체": "📋 전체", "pending": "⏳ 대기중", "processing": "🔄 생성중",
            "complete": "✅ 완료", "delivered": "📨 전달완료"
        }.get(x, x)
    )

    filtered = orders if status_filter == "전체" else [o for o in orders if o.get("status") == status_filter]

    # 통계
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 주문", len(orders))
    with col2:
        st.metric("대기중", len([o for o in orders if o.get("status") == "pending"]))
    with col3:
        st.metric("생성중", len([o for o in orders if o.get("status") == "processing"]))
    with col4:
        st.metric("완료", len([o for o in orders if o.get("status") in ["complete", "delivered"]]))

    st.markdown("---")

    # 주문 상세
    for order in filtered:
        oid = order.get("order_id", "?")
        name = order.get("name_kr", "?")
        status = order.get("status", "pending")
        created = order.get("created_at", "")[:16]

        status_emoji = {"pending": "⏳", "processing": "🔄", "complete": "✅", "delivered": "📨"}.get(status, "❓")

        with st.expander(f"{status_emoji} [{oid}] {name} — {created}"):
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.markdown(f"""
                **이름:** {name} ({order.get('name_en', '-')})
                **이메일:** {order.get('email', '-')}
                **연락처:** {order.get('phone', '-')}
                **출생:** {order.get('year')}년 {order.get('month')}월 {order.get('day')}일 {order.get('hour')}시 {order.get('minute')}분
                **출생지:** {order.get('city', '-')}
                **성별:** {order.get('gender', '-')}
                **메모:** {order.get('notes', '-')}
                """)

            with col_b:
                # 상태 변경
                new_status = st.selectbox(
                    "상태 변경", ["pending", "processing", "complete", "delivered"],
                    index=["pending", "processing", "complete", "delivered"].index(status),
                    key=f"status_{oid}",
                    format_func=lambda x: {"pending": "⏳ 대기중", "processing": "🔄 생성중",
                                           "complete": "✅ 완료", "delivered": "📨 전달완료"}.get(x, x)
                )
                if st.button("상태 업데이트", key=f"update_{oid}"):
                    update_order_status(oid, new_status)
                    st.success(f"상태 → {new_status}")
                    st.rerun()

            st.markdown("---")

            # 차트 계산 + 운명책 생성 버튼
            col_c1, col_c2, col_c3 = st.columns(3)

            with col_c1:
                if st.button("📊 차트 계산", key=f"chart_{oid}"):
                    with st.spinner("차트 데이터 수집 중..."):
                        chart_data = collect_charts(order)

                    # 차트 데이터 저장
                    chart_path = OUTPUT_DIR / f"{oid}_charts.json"
                    with open(chart_path, 'w', encoding='utf-8') as f:
                        json.dump(chart_data, f, ensure_ascii=False, indent=2, default=str)

                    st.success("차트 계산 완료!")

                    # 요약 표시
                    for system, data in chart_data.items():
                        if isinstance(data, dict) and "summary" in data:
                            st.text_area(f"{system} 요약", data["summary"],
                                        height=100, key=f"summary_{oid}_{system}")

            with col_c2:
                if st.button("📖 운명책 생성 (API)", key=f"generate_{oid}"):
                    chart_path = OUTPUT_DIR / f"{oid}_charts.json"
                    if not chart_path.exists():
                        st.warning("먼저 차트를 계산해주세요.")
                    elif not os.environ.get("ANTHROPIC_API_KEY"):
                        st.warning("사이드바에서 API 키를 입력해주세요.")
                    else:
                        with open(chart_path, 'r', encoding='utf-8') as f:
                            chart_data = json.load(f)

                        with st.spinner("Claude API로 운명책 생성 중... (약 5-10분 소요)"):
                            book_data = generate_all_chapters(
                                chart_data, name, os.environ["ANTHROPIC_API_KEY"]
                            )
                            book_data["birth_info"] = {
                                "year": order["year"], "month": order["month"],
                                "day": order["day"], "hour": order["hour"],
                                "minute": order["minute"], "city": order.get("city", ""),
                            }

                            pdf_path = generate_pdf(book_data, str(OUTPUT_DIR))

                        st.success(f"운명책 생성 완료: {pdf_path}")
                        update_order_status(oid, "complete")

            with col_c3:
                if st.button("📖 테스트 생성 (오프라인)", key=f"offline_{oid}"):
                    chart_path = OUTPUT_DIR / f"{oid}_charts.json"
                    if not chart_path.exists():
                        st.warning("먼저 차트를 계산해주세요.")
                    else:
                        with open(chart_path, 'r', encoding='utf-8') as f:
                            chart_data = json.load(f)

                        with st.spinner("테스트 PDF 생성 중..."):
                            book_data = generate_all_chapters_offline(chart_data, name)
                            book_data["birth_info"] = {
                                "year": order["year"], "month": order["month"],
                                "day": order["day"], "hour": order["hour"],
                                "minute": order["minute"], "city": order.get("city", ""),
                            }
                            pdf_path = generate_pdf(book_data, str(OUTPUT_DIR))

                        st.success("테스트 PDF 생성 완료!")

            # PDF 다운로드
            safe_name = name.replace(" ", "_")
            pdf_file = OUTPUT_DIR / f"{safe_name}_운명책.pdf"
            if pdf_file.exists():
                with open(pdf_file, 'rb') as f:
                    st.download_button(
                        "📥 운명책 PDF 다운로드",
                        f.read(),
                        file_name=f"{name}_운명책.pdf",
                        mime="application/pdf",
                        key=f"download_{oid}"
                    )


def page_quick_generate():
    """빠른 생성 (관리자용)"""
    st.title("⚡ 빠른 생성")
    st.markdown("차트 계산 + PDF 생성을 한 번에 실행합니다.")

    col1, col2 = st.columns(2)

    with col1:
        name_kr = st.text_input("이름 (한국어)", value="테스트")
        name_en = st.text_input("이름 (영문)", value="Test")
        gender = st.selectbox("성별", ["여", "남"])

    with col2:
        birth_date = st.date_input("출생일", value=date(1990, 1, 1))
        birth_hour = st.number_input("출생 시", min_value=0, max_value=23, value=14)
        birth_minute = st.number_input("출생 분", min_value=0, max_value=59, value=30)
        city = st.selectbox("출생지", list(CITY_OPTIONS.keys()))

    use_api = st.checkbox("Claude API 사용 (해석 포함)", value=False)

    if st.button("🚀 차트 계산 + PDF 생성", use_container_width=True):
        data = {
            "name_kr": name_kr, "name_en": name_en, "gender": gender,
            "year": birth_date.year, "month": birth_date.month, "day": birth_date.day,
            "hour": birth_hour, "minute": birth_minute, "city": city,
        }

        # 차트 수집
        with st.spinner("🔮 차트 데이터 수집 중..."):
            chart_data = collect_charts(data)

        # 결과 표시
        tabs = st.tabs(["사주명리", "점성학", "수비학", "휴먼디자인"])
        for tab, (system, sdata) in zip(tabs, chart_data.items()):
            with tab:
                if isinstance(sdata, dict) and "summary" in sdata:
                    st.text(sdata["summary"])
                elif isinstance(sdata, dict) and "error" in sdata:
                    st.error(sdata["error"])

        # PDF 생성
        with st.spinner("📄 PDF 생성 중..."):
            if use_api and os.environ.get("ANTHROPIC_API_KEY"):
                book_data = generate_all_chapters(chart_data, name_kr, os.environ["ANTHROPIC_API_KEY"])
            else:
                book_data = generate_all_chapters_offline(chart_data, name_kr)

            book_data["birth_info"] = {
                "year": data["year"], "month": data["month"], "day": data["day"],
                "hour": data["hour"], "minute": data["minute"], "city": city,
            }
            pdf_path = generate_pdf(book_data, str(OUTPUT_DIR))

        st.success("✅ 운명책 생성 완료!")

        with open(pdf_path, 'rb') as f:
            st.download_button(
                "📥 운명책 PDF 다운로드",
                f.read(),
                file_name=f"{name_kr}_운명책.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# ========================================
# 메인 라우터
# ========================================

def main():
    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("## 🔮 운명책")
        st.markdown("---")

        page = st.radio(
            "메뉴",
            ["🌟 주문하기", "⚡ 빠른 생성", "🔐 관리자"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("""
        <div style="color: #888; font-size: 0.8rem;">
        Produced by SULFUN<br>
        운명학 종합 분석 시스템<br>
        v1.0
        </div>
        """, unsafe_allow_html=True)

    # 페이지 렌더링
    if page == "🌟 주문하기":
        page_customer()
    elif page == "⚡ 빠른 생성":
        page_quick_generate()
    elif page == "🔐 관리자":
        page_admin()


if __name__ == "__main__":
    main()
