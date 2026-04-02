"""
사주명리 (四柱命理) 계산 엔진
Four Pillars of Destiny Calculator

생년월일시로부터 천간지지, 사주팔자, 대운, 오행 분석을 자동 계산
"""

from datetime import datetime, timedelta
import math


# === 천간 (Heavenly Stems) ===
CHEONGAN = ["갑(甲)", "을(乙)", "병(丙)", "정(丁)", "무(戊)",
            "기(己)", "경(庚)", "신(辛)", "임(壬)", "계(癸)"]
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
CHEONGAN_ELEMENTS = ["목(木)", "목(木)", "화(火)", "화(火)", "토(土)",
                     "토(土)", "금(金)", "금(金)", "수(水)", "수(水)"]
CHEONGAN_YINYANG = ["양", "음", "양", "음", "양", "음", "양", "음", "양", "음"]

# === 지지 (Earthly Branches) ===
JIJI = ["자(子)", "축(丑)", "인(寅)", "묘(卯)", "진(辰)", "사(巳)",
        "오(午)", "미(未)", "신(申)", "유(酉)", "술(戌)", "해(亥)"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIJI_ANIMALS = ["쥐", "소", "호랑이", "토끼", "용", "뱀",
                "말", "양", "원숭이", "닭", "개", "돼지"]
JIJI_ELEMENTS = ["수(水)", "토(土)", "목(木)", "목(木)", "토(土)", "화(火)",
                 "화(火)", "토(土)", "금(金)", "금(金)", "토(土)", "수(水)"]

# === 60갑자 (Sexagenary Cycle) ===
SIXTY_CYCLE = []
for i in range(60):
    stem = CHEONGAN_HANJA[i % 10]
    branch = JIJI_HANJA[i % 12]
    stem_kr = CHEONGAN[i % 10]
    branch_kr = JIJI[i % 12]
    SIXTY_CYCLE.append({
        "hanja": f"{stem}{branch}",
        "korean": f"{stem_kr.split('(')[0]}{branch_kr.split('(')[0]}",
        "full": f"{stem_kr} {branch_kr}",
        "stem_idx": i % 10,
        "branch_idx": i % 12
    })

# === 절기 (Solar Terms) - 월주 계산용 ===
# 각 월의 절입일 (평균값, 실제로는 매년 다름)
SOLAR_TERMS_APPROX = {
    1: (2, 4),    # 입춘 (2/4 전후)
    2: (3, 6),    # 경칩
    3: (4, 5),    # 청명
    4: (5, 6),    # 입하
    5: (6, 6),    # 망종
    6: (7, 7),    # 소서
    7: (8, 7),    # 입추
    8: (9, 8),    # 백로
    9: (10, 8),   # 한로
    10: (11, 7),  # 입동
    11: (12, 7),  # 대설
    12: (1, 6),   # 소한 (다음해 1월)
}


def get_year_pillar(year, month, day):
    """
    연주(年柱) 계산
    입춘(2/4경) 이전이면 전년도 기준
    """
    # 입춘 이전 체크 (대략 2월 4일)
    if month < 2 or (month == 2 and day < 4):
        year -= 1

    # 1984년 = 갑자(甲子)년 기준
    idx = (year - 4) % 60
    return SIXTY_CYCLE[idx]


def get_month_pillar(year, month, day, year_stem_idx):
    """
    월주(月柱) 계산
    절기 기준으로 월 결정, 연간(年干)에 따라 월간(月干) 결정
    """
    # 절기 기반 월 결정
    saju_month = None
    for m in range(1, 13):
        term_month, term_day = SOLAR_TERMS_APPROX[m]
        if m == 12:  # 소한은 다음해 1월
            if month == 1 and day < term_day:
                saju_month = 12
                break
            elif month == 12 and day >= 7:
                saju_month = 12
                break
        else:
            next_m = m + 1
            next_term_month, next_term_day = SOLAR_TERMS_APPROX[next_m]

            if month == term_month and day >= term_day:
                if next_m <= 11:
                    if month < next_term_month or (month == next_term_month and day < next_term_day):
                        saju_month = m
                        break
                else:
                    saju_month = m
                    break
            elif month > term_month and month < next_term_month:
                saju_month = m
                break

    if saju_month is None:
        # 기본값: 양력 월 기반 추정
        saju_month = ((month + 9) % 12) + 1

    # 월간 계산: 연간(年干)에 따른 월간 공식
    # 갑기년 - 병인월 시작, 을경년 - 무인월 시작 등
    year_stem_group = year_stem_idx % 5
    month_stem_start = (year_stem_group * 2 + 2) % 10
    month_stem_idx = (month_stem_start + saju_month - 1) % 10

    # 월지는 인(寅)월부터 시작 (1월=인, 2월=묘...)
    month_branch_idx = (saju_month + 1) % 12

    # 60갑자에서 찾기
    for cycle in SIXTY_CYCLE:
        if cycle["stem_idx"] == month_stem_idx and cycle["branch_idx"] == month_branch_idx:
            return cycle

    return SIXTY_CYCLE[0]  # fallback


def get_day_pillar(year, month, day):
    """
    일주(日柱) 계산
    기준일(2000-01-07 = 갑자일)로부터 일수 차이로 계산
    """
    base_date = datetime(2000, 1, 7)  # 갑자일 기준
    target_date = datetime(year, month, day)
    diff = (target_date - base_date).days
    idx = diff % 60
    return SIXTY_CYCLE[idx]


def get_hour_pillar(hour, day_stem_idx):
    """
    시주(時柱) 계산
    시간대별 지지 + 일간(日干)에 따른 시간 계산
    """
    # 시간대별 지지 (자시: 23-01, 축시: 01-03, ...)
    hour_branches = [
        (23, 1, 0),   # 자시 子
        (1, 3, 1),    # 축시 丑
        (3, 5, 2),    # 인시 寅
        (5, 7, 3),    # 묘시 卯
        (7, 9, 4),    # 진시 辰
        (9, 11, 5),   # 사시 巳
        (11, 13, 6),  # 오시 午
        (13, 15, 7),  # 미시 未
        (15, 17, 8),  # 신시 申
        (17, 19, 9),  # 유시 酉
        (19, 21, 10), # 술시 戌
        (21, 23, 11), # 해시 亥
    ]

    hour_branch_idx = 0
    for start, end, idx in hour_branches:
        if start == 23:
            if hour >= 23 or hour < 1:
                hour_branch_idx = idx
                break
        elif start <= hour < end:
            hour_branch_idx = idx
            break

    # 시간 계산: 일간에 따른 시간 공식
    day_stem_group = day_stem_idx % 5
    hour_stem_start = (day_stem_group * 2) % 10
    hour_stem_idx = (hour_stem_start + hour_branch_idx) % 10

    for cycle in SIXTY_CYCLE:
        if cycle["stem_idx"] == hour_stem_idx and cycle["branch_idx"] == hour_branch_idx:
            return cycle

    return SIXTY_CYCLE[0]


def analyze_five_elements(pillars):
    """오행(五行) 분석 - 목화토금수 비율"""
    elements = {"목(木)": 0, "화(火)": 0, "토(土)": 0, "금(金)": 0, "수(水)": 0}

    for pillar in pillars:
        stem_elem = CHEONGAN_ELEMENTS[pillar["stem_idx"]]
        branch_elem = JIJI_ELEMENTS[pillar["branch_idx"]]
        elements[stem_elem] += 1
        elements[branch_elem] += 1

    return elements


def get_ten_gods(day_stem_idx, pillars):
    """십신(十神) 분석"""
    ten_gods_map = {
        0: "비견", 1: "겁재", 2: "식신", 3: "상관", 4: "편재",
        5: "정재", 6: "편관", 7: "정관", 8: "편인", 9: "정인"
    }

    results = []
    for pillar in pillars:
        diff = (pillar["stem_idx"] - day_stem_idx) % 10
        results.append({
            "pillar": pillar["full"],
            "ten_god": ten_gods_map[diff]
        })

    return results


def calculate_daeun(year, month, day, hour, gender):
    """
    대운(大運) 계산
    성별과 연간 음양에 따라 순행/역행 결정
    """
    year_pillar = get_year_pillar(year, month, day)
    year_stem_yang = CHEONGAN_YINYANG[year_pillar["stem_idx"]] == "양"
    is_male = gender.lower() in ["m", "male", "남", "남자"]

    # 양남음녀 → 순행, 음남양녀 → 역행
    forward = (year_stem_yang and is_male) or (not year_stem_yang and not is_male)

    month_pillar = get_month_pillar(year, month, day, year_pillar["stem_idx"])

    # 대운 시작 나이 계산 (간략화: 평균 3-4세)
    start_age = 3  # 실제로는 절기까지 일수로 계산해야 하나 간략화

    daeun_list = []
    month_cycle_idx = None
    for i, cycle in enumerate(SIXTY_CYCLE):
        if cycle["stem_idx"] == month_pillar["stem_idx"] and cycle["branch_idx"] == month_pillar["branch_idx"]:
            month_cycle_idx = i
            break

    if month_cycle_idx is None:
        month_cycle_idx = 0

    for i in range(1, 11):  # 10개 대운
        if forward:
            idx = (month_cycle_idx + i) % 60
        else:
            idx = (month_cycle_idx - i) % 60

        age = start_age + (i - 1) * 10
        cycle = SIXTY_CYCLE[idx]
        daeun_list.append({
            "age": age,
            "year": year + age,
            "pillar": cycle["full"],
            "hanja": cycle["hanja"],
            "element": CHEONGAN_ELEMENTS[cycle["stem_idx"]]
        })

    return daeun_list


def calculate_saju(year, month, day, hour, gender="female"):
    """
    사주 전체 계산 메인 함수

    Parameters:
        year: 출생 연도 (양력)
        month: 출생 월
        day: 출생 일
        hour: 출생 시 (24시간제)
        gender: "male"/"female" 또는 "남"/"여"

    Returns:
        dict: 사주 전체 분석 결과
    """
    # 사주 팔자 계산
    year_pillar = get_year_pillar(year, month, day)
    month_pillar = get_month_pillar(year, month, day, year_pillar["stem_idx"])
    day_pillar = get_day_pillar(year, month, day)
    hour_pillar = get_hour_pillar(hour, day_pillar["stem_idx"])

    pillars = [year_pillar, month_pillar, day_pillar, hour_pillar]

    # 오행 분석
    five_elements = analyze_five_elements(pillars)

    # 일간(日干) = 나를 대표하는 글자
    day_master = CHEONGAN[day_pillar["stem_idx"]]
    day_master_element = CHEONGAN_ELEMENTS[day_pillar["stem_idx"]]

    # 십신 분석
    ten_gods = get_ten_gods(day_pillar["stem_idx"], pillars)

    # 대운 계산
    daeun = calculate_daeun(year, month, day, hour, gender)

    # 띠
    animal = JIJI_ANIMALS[year_pillar["branch_idx"]]

    return {
        "system": "사주명리 (四柱命理)",
        "birth_info": {
            "year": year, "month": month, "day": day, "hour": hour,
            "gender": gender
        },
        "four_pillars": {
            "year": {"pillar": year_pillar["full"], "hanja": year_pillar["hanja"]},
            "month": {"pillar": month_pillar["full"], "hanja": month_pillar["hanja"]},
            "day": {"pillar": day_pillar["full"], "hanja": day_pillar["hanja"]},
            "hour": {"pillar": hour_pillar["full"], "hanja": hour_pillar["hanja"]},
        },
        "day_master": day_master,
        "day_master_element": day_master_element,
        "animal_sign": animal,
        "five_elements": five_elements,
        "ten_gods": ten_gods,
        "daeun": daeun,
        "summary": (
            f"일간: {day_master} ({day_master_element})\n"
            f"띠: {animal}\n"
            f"연주: {year_pillar['full']}\n"
            f"월주: {month_pillar['full']}\n"
            f"일주: {day_pillar['full']}\n"
            f"시주: {hour_pillar['full']}\n"
            f"오행분포: {five_elements}"
        )
    }


if __name__ == "__main__":
    # 테스트
    result = calculate_saju(1990, 3, 15, 14, "female")
    print("=== 사주명리 계산 결과 ===")
    print(f"사주: {result['four_pillars']}")
    print(f"일간: {result['day_master']}")
    print(f"띠: {result['animal_sign']}")
    print(f"오행: {result['five_elements']}")
    print(f"\n대운:")
    for d in result['daeun']:
        print(f"  {d['age']}세 ({d['year']}): {d['pillar']}")
