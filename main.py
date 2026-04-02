#!/usr/bin/env python3
"""
운명책 자동 생성기 (Destiny Book Auto Generator)
==============================================

생년월일+출생시간+출생지만 입력하면
사주명리 / 점성학 / 수비학 / 휴먼디자인 차트를 자동 계산하고
Claude API로 해석하여 PDF 운명책을 생성합니다.

사용법:
    python main.py                          # 대화형 입력
    python main.py --test                   # 테스트 모드 (API 없이)
    python main.py --json client.json       # JSON 파일로 입력
    python main.py --quick 1990 3 15 14 30 서울 여 "김수진" "Sujin Kim"

Author: SULFUN
"""

import argparse
import json
import os
import sys

# 모듈 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CITY_DATABASE, DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE
from scrapers.saju import calculate_saju
from scrapers.astrology import calculate_astrology
from scrapers.numerology import calculate_numerology
from scrapers.human_design import calculate_human_design
from interpreter import generate_all_chapters, generate_all_chapters_offline
from pdf_generator import generate_pdf


def resolve_city(city_input):
    """도시명으로 위도/경도/타임존 조회"""
    city_lower = city_input.lower().strip()

    if city_lower in CITY_DATABASE:
        lat, lon, tz = CITY_DATABASE[city_lower]
        return lat, lon, tz

    # 한국어 도시명도 검색
    for name, (lat, lon, tz) in CITY_DATABASE.items():
        if city_input.strip() == name:
            return lat, lon, tz

    # 찾지 못한 경우 기본값 (서울)
    print(f"⚠️  '{city_input}'을(를) 찾을 수 없습니다. 서울로 기본 설정합니다.")
    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE


def collect_all_charts(year, month, day, hour, minute, city, gender,
                       name_kr="", name_en=""):
    """모든 차트 데이터 수집"""
    lat, lon, tz = resolve_city(city)

    print("\n" + "=" * 60)
    print("🔮 운명책 차트 데이터 수집")
    print("=" * 60)
    print(f"   출생: {year}년 {month}월 {day}일 {hour}시 {minute}분")
    print(f"   출생지: {city} ({lat}, {lon})")
    print(f"   성별: {gender}")
    if name_kr:
        print(f"   이름: {name_kr}")
    print("=" * 60)

    all_data = {}

    # 1. 사주명리
    print("\n🏛️  사주명리 계산 중...")
    try:
        saju = calculate_saju(year, month, day, hour, gender)
        all_data["saju"] = saju
        print(f"   ✅ 일간: {saju['day_master']}, 띠: {saju['animal_sign']}")
    except Exception as e:
        print(f"   ❌ 사주 계산 오류: {e}")
        all_data["saju"] = {"error": str(e)}

    # 2. 점성학
    print("\n⭐ 점성학 차트 계산 중...")
    try:
        astro = calculate_astrology(year, month, day, hour, minute, city, lat, lon, tz)
        all_data["astrology"] = astro
        if "error" not in astro:
            big3 = astro.get("big_three", {})
            print(f"   ✅ 태양: {big3.get('sun', '?')}, 달: {big3.get('moon', '?')}, ASC: {big3.get('ascendant', '?')}")
        else:
            print(f"   ⚠️  {astro['error']}")
    except Exception as e:
        print(f"   ❌ 점성학 계산 오류: {e}")
        all_data["astrology"] = {"error": str(e)}

    # 3. 수비학
    print("\n🔢 수비학 계산 중...")
    try:
        numerology = calculate_numerology(year, month, day, name_en)
        all_data["numerology"] = numerology
        lp = numerology["core_numbers"]["life_path"]["number"]
        print(f"   ✅ 생명수: {lp}")
    except Exception as e:
        print(f"   ❌ 수비학 계산 오류: {e}")
        all_data["numerology"] = {"error": str(e)}

    # 4. 휴먼디자인
    print("\n🧬 휴먼디자인 차트 계산 중...")
    try:
        hd = calculate_human_design(year, month, day, hour, minute, city, lat, lon)
        all_data["humandesign"] = hd
        print(f"   ✅ 타입: {hd['type']}, 프로파일: {hd['profile']}")
    except Exception as e:
        print(f"   ❌ 휴먼디자인 계산 오류: {e}")
        all_data["humandesign"] = {"error": str(e)}

    print("\n" + "=" * 60)
    print("✅ 차트 데이터 수집 완료!")
    print("=" * 60)

    return all_data


def interactive_input():
    """대화형 입력"""
    print("\n" + "=" * 60)
    print("🔮 운명책 자동 생성기 (Destiny Book Generator)")
    print("   by SULFUN")
    print("=" * 60)

    name_kr = input("\n📝 의뢰인 이름 (한국어): ").strip()
    name_en = input("📝 의뢰인 이름 (영문, 수비학용 - 없으면 Enter): ").strip()

    print("\n📅 출생 정보를 입력하세요:")
    year = int(input("   출생 연도 (예: 1990): "))
    month = int(input("   출생 월 (1-12): "))
    day = int(input("   출생 일 (1-31): "))
    hour = int(input("   출생 시 (0-23, 24시간제): "))
    minute = int(input("   출생 분 (0-59): "))
    city = input("   출생 도시 (예: 서울, Seoul, Tokyo): ").strip()
    gender = input("   성별 (남/여 또는 male/female): ").strip()

    return {
        "name_kr": name_kr,
        "name_en": name_en,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "city": city or "서울",
        "gender": gender or "여",
    }


def run_pipeline(input_data, output_dir="output", api_key=None, offline=False):
    """전체 파이프라인 실행"""
    # 1. 차트 데이터 수집
    all_data = collect_all_charts(
        input_data["year"], input_data["month"], input_data["day"],
        input_data["hour"], input_data["minute"],
        input_data["city"], input_data["gender"],
        input_data.get("name_kr", ""),
        input_data.get("name_en", ""),
    )

    # 중간 데이터 저장
    os.makedirs(output_dir, exist_ok=True)
    safe_name = input_data.get("name_kr", "client").replace(" ", "_")
    json_path = os.path.join(output_dir, f"{safe_name}_chart_data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 차트 데이터 저장: {json_path}")

    # 2. 텍스트 해석 생성
    client_name = input_data.get("name_kr", "의뢰인")

    if offline:
        print("\n📖 오프라인 모드 - 차트 데이터만 포함하여 PDF 생성")
        book_data = generate_all_chapters_offline(all_data, client_name)
    else:
        print("\n📖 Claude API로 운명책 텍스트 생성 중...")
        book_data = generate_all_chapters(all_data, client_name, api_key)

        if "error" in book_data:
            print(f"\n❌ {book_data['error']}")
            print("   → 오프라인 모드로 전환합니다.")
            book_data = generate_all_chapters_offline(all_data, client_name)

    # birth_info 추가
    book_data["birth_info"] = {
        "year": input_data["year"],
        "month": input_data["month"],
        "day": input_data["day"],
        "hour": input_data["hour"],
        "minute": input_data["minute"],
        "city": input_data["city"],
    }

    # 3. PDF 생성
    print("\n📄 PDF 운명책 생성 중...")
    pdf_path = generate_pdf(book_data, output_dir)

    print("\n" + "=" * 60)
    print(f"🎉 운명책 생성 완료!")
    print(f"   📁 PDF: {pdf_path}")
    print(f"   📁 차트 데이터: {json_path}")
    print("=" * 60)

    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="운명책 자동 생성기")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (API 없이)")
    parser.add_argument("--json", type=str, help="JSON 입력 파일 경로")
    parser.add_argument("--api-key", type=str, help="Anthropic API 키")
    parser.add_argument("--output", type=str, default="output", help="출력 디렉토리")
    parser.add_argument("--quick", nargs=9, metavar=(
        "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "CITY", "GENDER", "NAME_KR", "NAME_EN"
    ), help="빠른 입력: 연 월 일 시 분 도시 성별 이름_한글 이름_영문")
    parser.add_argument("--charts-only", action="store_true",
                        help="차트 데이터만 수집 (해석/PDF 생성 안함)")

    args = parser.parse_args()

    # 입력 데이터 결정
    if args.quick:
        input_data = {
            "year": int(args.quick[0]),
            "month": int(args.quick[1]),
            "day": int(args.quick[2]),
            "hour": int(args.quick[3]),
            "minute": int(args.quick[4]),
            "city": args.quick[5],
            "gender": args.quick[6],
            "name_kr": args.quick[7],
            "name_en": args.quick[8],
        }
    elif args.json:
        with open(args.json, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    else:
        input_data = interactive_input()

    # 차트 데이터만 수집 모드
    if args.charts_only:
        all_data = collect_all_charts(
            input_data["year"], input_data["month"], input_data["day"],
            input_data["hour"], input_data["minute"],
            input_data["city"], input_data["gender"],
            input_data.get("name_kr", ""),
            input_data.get("name_en", ""),
        )
        os.makedirs(args.output, exist_ok=True)
        safe_name = input_data.get("name_kr", "client").replace(" ", "_")
        json_path = os.path.join(args.output, f"{safe_name}_chart_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n✅ 차트 데이터 저장: {json_path}")

        # 요약 출력
        print("\n=== 차트 요약 ===")
        for system, data in all_data.items():
            print(f"\n[{system}]")
            if isinstance(data, dict) and "summary" in data:
                print(data["summary"])
        return

    # 전체 파이프라인 실행
    offline = args.test or not (args.api_key or os.environ.get("ANTHROPIC_API_KEY"))
    run_pipeline(input_data, args.output, args.api_key, offline)


if __name__ == "__main__":
    main()
