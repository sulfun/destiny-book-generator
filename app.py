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

# === 앱 설정 ===
st.set_page_config(
    page_title="운명책 | The Book of Destiny",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 데이터 디렉토리 ===
DATA_DIR = Path("data")
ORDERS_DIR = DATA_DIR / "orders"
OUTPUT_DIR = DATA_DIR / "output"
for d in [DATA_DIR, ORDERS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

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


def save_order(order_data):
    """주문 저장"""
    order_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    order_data["order_id"] = order_id
    order_data["status"] = "pending"
    order_data["created_at"] = datetime.now().isoformat()

    order_path = ORDERS_DIR / f"{order_id}.json"
    with open(order_path, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, ensure_ascii=False, indent=2, default=str)

    return order_id


def load_orders():
    """모든 주문 불러오기"""
    orders = []
    for f in sorted(ORDERS_DIR.glob("*.json"), reverse=True):
        with open(f, 'r', encoding='utf-8') as fh:
            orders.append(json.load(fh))
    return orders


def update_order_status(order_id, new_status):
    """주문 상태 업데이트"""
    order_path = ORDERS_DIR / f"{order_id}.json"
    if order_path.exists():
        with open(order_path, 'r', encoding='utf-8') as f:
            order = json.load(f)
        order["status"] = new_status
        order["updated_at"] = datetime.now().isoformat()
        with open(order_path, 'w', encoding='utf-8') as f:
            json.dump(order, f, ensure_ascii=False, indent=2, default=str)


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

    st.markdown("""
    <div class="info-box">
    12가지 동서양 운명학 시스템을 통합 분석하여<br>
    당신만을 위한 운명의 책을 제작합니다.<br><br>
    사주명리 · 서양점성학 · 베딕점성학 · 수비학 · 휴먼디자인 · 주역 · 타로 · 카발라 외
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="price-tag">₩ 500,000</p>', unsafe_allow_html=True)

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
        notes = st.text_area("추가 메모 (선택)", placeholder="특별히 궁금한 점이나 참고사항이 있으면 적어주세요",
                            max_chars=500)

        submitted = st.form_submit_button("✨ 운명책 신청하기", use_container_width=True)

        if submitted:
            # 유효성 검사
            if not name_kr:
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
