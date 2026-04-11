#!/usr/bin/env python3
"""
운명책 배치 생성기 (Destiny Book Batch Generator)
================================================

노션 DB에서 '선정완료' 상태인 주문만 가져와서
차트 계산 → Claude API 해석 → PDF 생성 → 이메일 발송 → 노션 상태 업데이트

사용법:
    python batch_generator.py                    # 선정완료 건 전부 처리
    python batch_generator.py --dry-run          # 처리 대상만 확인 (실행 안함)
    python batch_generator.py --name 안혜라       # 특정 이름만 처리
    python batch_generator.py --no-email         # 이메일 발송 안함
    python batch_generator.py --status 접수완료   # 다른 상태도 처리 가능

환경변수:
    ANTHROPIC_API_KEY   Claude API 키 (필수)
    NOTION_TOKEN        Notion API 토큰 (필수)
    GMAIL_APP_PASSWORD  Gmail 앱 비밀번호 (이메일 발송 시)
    GMAIL_SENDER        발신자 이메일 (기본: societyalef@gmail.com)

Author: SULFUN (The Architect)
"""

import argparse
import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path

# 모듈 경로
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CITY_DATABASE, CHAPTERS
from main import collect_all_charts, run_pipeline


# ============================================================
# 노션 연동
# ============================================================

NOTION_DB_ID = "231274d036864a249614327bb9fdeed9"

# 결제 정보
PAYMENT_AMOUNT = "119,000원"
PAYMENT_BANK = "국민은행"
PAYMENT_ACCOUNT = "642002-04-036645"
PAYMENT_HOLDER = "이수진"

def get_notion_client():
    """Notion 클라이언트 생성"""
    try:
        from notion_client import Client as NotionClient
    except ImportError:
        print("❌ notion-client 패키지가 필요합니다: pip install notion-client")
        sys.exit(1)

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("❌ NOTION_TOKEN 환경변수를 설정하세요")
        sys.exit(1)

    return NotionClient(auth=token)


def fetch_orders_by_status(notion, status="선정완료"):
    """노션에서 특정 상태의 주문 조회"""
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={
            "property": "상태",
            "select": {"equals": status}
        },
        sorts=[{"property": "접수일시", "direction": "ascending"}]
    )

    orders = []
    for page in results.get("results", []):
        props = page["properties"]
        order = {
            "page_id": page["id"],
            "order_id": _get_title(props.get("주문번호", {})),
            "name_kr": _get_text(props.get("이름(한글)", {})),
            "name_en": _get_text(props.get("이름(영문)", {})),
            "email": props.get("이메일", {}).get("email", ""),
            "phone": props.get("전화번호", {}).get("phone_number", ""),
            "gender": _get_select(props.get("성별", {})),
            "year": int(props.get("생년", {}).get("number", 0) or 0),
            "month": int(props.get("생월", {}).get("number", 0) or 0),
            "day": int(props.get("생일", {}).get("number", 0) or 0),
            "hour": int(props.get("생시", {}).get("number", 0) or 0),
            "minute": int(props.get("생분", {}).get("number", 0) or 0),
            "city": _get_text(props.get("출생도시", {})),
            "memo": _get_text(props.get("메모", {})),
            "status": _get_select(props.get("상태", {})),
        }
        orders.append(order)

    return orders


def _get_title(prop):
    items = prop.get("title", [])
    return items[0]["plain_text"] if items else ""

def _get_text(prop):
    items = prop.get("rich_text", [])
    return items[0]["plain_text"] if items else ""

def _get_select(prop):
    sel = prop.get("select")
    return sel["name"] if sel else ""


def update_notion_status(notion, page_id, status, chart_data_json=""):
    """노션 주문 상태 업데이트"""
    properties = {
        "상태": {"select": {"name": status}}
    }
    if chart_data_json:
        # 차트 데이터 요약 저장 (2000자 제한)
        properties["차트데이터"] = {
            "rich_text": [{"text": {"content": chart_data_json[:2000]}}]
        }
    notion.pages.update(page_id=page_id, properties=properties)


# ============================================================
# 도시 → 좌표 변환
# ============================================================

def resolve_city(city_name):
    """도시명으로 좌표/타임존 조회"""
    city_lower = city_name.lower().strip()

    # config.py의 CITY_DATABASE 사용
    if city_lower in CITY_DATABASE:
        return CITY_DATABASE[city_lower]

    # 한국어 키로 검색
    for name, data in CITY_DATABASE.items():
        if city_name.strip() == name:
            return data

    # 기본값: 서울
    print(f"  ⚠️  '{city_name}' 좌표 미확인 → 서울로 대체")
    return (37.5665, 126.9780, "Asia/Seoul")


# ============================================================
# 이메일 발송
# ============================================================

def send_destiny_book_email(to_email, client_name, pdf_path, order_id):
    """운명책 PDF를 이메일로 발송"""
    sender = os.environ.get("GMAIL_SENDER", "societyalef@gmail.com")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not password:
        print(f"  ⚠️  GMAIL_APP_PASSWORD 미설정 → 이메일 발송 생략")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"The Architect <{sender}>"
    msg["To"] = to_email
    msg["Subject"] = f"[운명책 #{order_id}] {client_name}님의 운명책이 도착했습니다"

    body = f"""안녕하세요, {client_name}님.

요청하신 운명책이 완성되었습니다.

첨부된 PDF 파일을 확인해 주세요.
이 운명책은 {client_name}님의 출생 데이터를 기반으로
동서양 12개 운명학 시스템을 교차 분석하여 작성되었습니다.

문의사항이 있으시면 이 메일로 회신해 주세요.

감사합니다.

—
The Architect
Produced by The Architect
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # PDF 첨부
    with open(pdf_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        filename = f"{client_name}_운명책.pdf"
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        print(f"  ✅ 이메일 발송 완료 → {to_email}")
        return True
    except Exception as e:
        print(f"  ❌ 이메일 발송 실패: {e}")
        return False


def send_payment_notice_email(to_email, client_name, order_id):
    """선정 완료 후 입금 안내 이메일 발송"""
    sender = os.environ.get("GMAIL_SENDER", "societyalef@gmail.com")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not password:
        print(f"  ⚠️  GMAIL_APP_PASSWORD 미설정 → 이메일 발송 생략")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"세계대예언가이자 인간운명판독기 <{sender}>"
    msg["To"] = to_email
    msg["Subject"] = f"[세계대예언가] 운명책 입금 안내 — {client_name}님"

    body = f"""{client_name}님, 안녕하세요.

세계대예언가이자 인간운명판독기입니다.

{client_name}님의 운명책 신청이 선정되었습니다.
축하드립니다.

아래 계좌로 입금 확인 후, 운명책 제작이 시작됩니다.

━━━━━━━━━━━━━━━━━━━━━
금액: {PAYMENT_AMOUNT}
입금 계좌: {PAYMENT_BANK} {PAYMENT_ACCOUNT}
예금주: {PAYMENT_HOLDER}
━━━━━━━━━━━━━━━━━━━━━

※ 입금자명을 신청자 본인 이름으로 해주세요.
※ 입금 확인 후 영업일 기준 3~5일 내 운명책이 이메일로 발송됩니다.

감사합니다.

—
세계대예언가이자 인간운명판독기 드림
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        print(f"  ✅ 입금 안내 발송 완료 → {to_email}")
        return True
    except Exception as e:
        print(f"  ❌ 입금 안내 발송 실패: {e}")
        return False


def send_payment_notice_sms(phone, client_name):
    """솔라피(Solapi) API로 입금 안내 문자 발송"""
    api_key = os.environ.get("SOLAPI_API_KEY")
    api_secret = os.environ.get("SOLAPI_API_SECRET")
    sender_phone = os.environ.get("SOLAPI_SENDER", "")

    if not api_key or not api_secret or not sender_phone:
        print(f"  ⚠️  SOLAPI 환경변수 미설정 → 문자 발송 생략")
        return False

    try:
        from solapi import SolapiMessageService
    except ImportError:
        print("  ⚠️  solapi 패키지 미설치 → pip install solapi-sms")
        return False

    text = (
        f"[세계대예언가] {client_name}님, 운명책 신청이 선정되었습니다. "
        f"입금안내: {PAYMENT_BANK} {PAYMENT_ACCOUNT} ({PAYMENT_HOLDER}) "
        f"{PAYMENT_AMOUNT}. 입금자명은 본인 이름으로 부탁드립니다."
    )

    try:
        messaging = SolapiMessageService(api_key, api_secret)
        result = messaging.send_one({
            "to": phone.replace("-", ""),
            "from": sender_phone,
            "text": text,
        })
        print(f"  ✅ 문자 발송 완료 → {phone}")
        return True
    except Exception as e:
        print(f"  ❌ 문자 발송 실패: {e}")
        return False


# ============================================================
# 단일 주문 처리
# ============================================================

def process_order(order, notion, output_dir="output", api_key=None,
                  send_email=True, offline=False):
    """단일 주문 전체 처리"""
    name = order["name_kr"] or "의뢰인"
    order_id = order["order_id"]

    print(f"\n{'='*60}")
    print(f"📖 주문 처리: {name} ({order_id})")
    print(f"   출생: {order['year']}-{order['month']:02d}-{order['day']:02d} "
          f"{order['hour']:02d}:{order['minute']:02d}")
    print(f"   출생지: {order['city']}, 성별: {order['gender']}")
    print(f"{'='*60}")

    # 데이터 유효성 검증
    if not all([order["year"], order["month"], order["day"]]):
        print(f"  ❌ 출생 데이터 불완전 → 건너뜀")
        update_notion_status(notion, order["page_id"], "오류")
        return None

    try:
        # 1. 상태: 차트계산중
        update_notion_status(notion, order["page_id"], "차트계산중")

        # 2. 차트 데이터 수집
        lat, lon, tz = resolve_city(order["city"])
        gender_code = "여" if order["gender"] in ["여성", "여", "female"] else "남"

        all_charts = collect_all_charts(
            order["year"], order["month"], order["day"],
            order["hour"], order["minute"],
            order["city"], gender_code,
            order["name_kr"], order["name_en"]
        )

        # 차트 요약 저장
        chart_summary = json.dumps({
            k: v.get("summary", "")[:200] if isinstance(v, dict) else ""
            for k, v in all_charts.items()
        }, ensure_ascii=False)
        update_notion_status(notion, order["page_id"], "해석생성중", chart_summary)

        # 3. 해석 생성 (Claude API)
        from interpreter import generate_all_chapters, generate_all_chapters_offline

        if offline or not api_key:
            print("  📖 오프라인 모드 → 차트 데이터만 포함")
            book_data = generate_all_chapters_offline(all_charts, name)
        else:
            print("  📖 Claude API로 운명책 해석 생성 중...")
            book_data = generate_all_chapters(all_charts, name, api_key)
            if "error" in book_data:
                print(f"  ⚠️  API 오류 → 오프라인 모드 전환: {book_data['error']}")
                book_data = generate_all_chapters_offline(all_charts, name)

        book_data["birth_info"] = {
            "year": order["year"], "month": order["month"],
            "day": order["day"], "hour": order["hour"],
            "minute": order["minute"], "city": order["city"],
        }

        # 4. PDF 생성
        update_notion_status(notion, order["page_id"], "PDF생성중")
        from pdf_generator import generate_pdf

        safe_name = name.replace(" ", "_")
        order_output_dir = os.path.join(output_dir, safe_name)
        os.makedirs(order_output_dir, exist_ok=True)

        # book_data JSON 저장
        json_path = os.path.join(order_output_dir, f"{safe_name}_book_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2, default=str)

        pdf_path = generate_pdf(book_data, order_output_dir)
        print(f"  ✅ PDF 생성 완료: {pdf_path}")

        # 5. 상태: 완료
        update_notion_status(notion, order["page_id"], "완료")

        # 6. 이메일 발송
        if send_email and order["email"]:
            email_sent = send_destiny_book_email(
                order["email"], name, pdf_path, order_id
            )
            if email_sent:
                update_notion_status(notion, order["page_id"], "발송완료")
        else:
            if not order["email"]:
                print(f"  ⚠️  이메일 주소 없음 → 발송 생략")
            else:
                print(f"  ℹ️  이메일 발송 비활성화 (--no-email)")

        return pdf_path

    except Exception as e:
        print(f"  ❌ 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        update_notion_status(notion, order["page_id"], "오류")
        return None


# ============================================================
# 메인 배치 실행
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="운명책 배치 생성기")
    parser.add_argument("--status", default="선정완료",
                        help="처리할 노션 상태 (기본: 선정완료)")
    parser.add_argument("--name", type=str,
                        help="특정 이름만 처리")
    parser.add_argument("--dry-run", action="store_true",
                        help="처리 대상만 확인 (실행 안함)")
    parser.add_argument("--no-email", action="store_true",
                        help="이메일 발송 안함")
    parser.add_argument("--offline", action="store_true",
                        help="오프라인 모드 (API 없이)")
    parser.add_argument("--api-key", type=str,
                        help="Anthropic API 키 (환경변수 대체)")
    parser.add_argument("--output", default="output",
                        help="출력 디렉토리 (기본: output)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")

    print("=" * 60)
    print("📚 운명책 배치 생성기 v1.0")
    print("   by The Architect")
    print("=" * 60)

    # 노션 연결
    notion = get_notion_client()
    print(f"✅ Notion 연결 완료")

    # 주문 조회
    print(f"\n🔍 '{args.status}' 상태 주문 조회 중...")
    orders = fetch_orders_by_status(notion, args.status)

    # 이름 필터
    if args.name:
        orders = [o for o in orders if args.name in (o["name_kr"] or "")]
        print(f"  → '{args.name}' 필터 적용")

    if not orders:
        print(f"\n📭 처리할 주문이 없습니다.")
        return

    # 대상 목록 표시
    print(f"\n📋 처리 대상: {len(orders)}건")
    print("-" * 60)
    for i, o in enumerate(orders, 1):
        print(f"  {i}. {o['name_kr']} ({o['order_id']}) "
              f"— {o['year']}-{o['month']:02d}-{o['day']:02d} "
              f"{o['hour']:02d}:{o['minute']:02d} {o['city']}")
    print("-" * 60)

    if args.dry_run:
        print("\n🔍 Dry run 모드 — 실행하지 않고 종료합니다.")
        return

    if not api_key and not args.offline:
        print("\n⚠️  ANTHROPIC_API_KEY가 없습니다. --offline 모드로 전환합니다.")
        args.offline = True

    # 배치 처리
    results = {"success": [], "failed": []}
    for order in orders:
        pdf_path = process_order(
            order, notion,
            output_dir=args.output,
            api_key=api_key,
            send_email=not args.no_email,
            offline=args.offline
        )
        if pdf_path:
            results["success"].append(order["name_kr"])
        else:
            results["failed"].append(order["name_kr"])

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"📊 배치 처리 결과")
    print(f"{'='*60}")
    print(f"  ✅ 성공: {len(results['success'])}건 — {', '.join(results['success']) or '-'}")
    print(f"  ❌ 실패: {len(results['failed'])}건 — {', '.join(results['failed']) or '-'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
