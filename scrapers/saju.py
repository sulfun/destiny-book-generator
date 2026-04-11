"""
사주명리 (四柱命理) 계산 엔진 v2.0
Four Pillars of Destiny Calculator

korean-lunar-calendar 기반 정밀 간지 계산
+ 신살 / 12운성 / 용신 / 대운 / 세운 분석

Author: SULFUN (The Architect)
"""

from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar


# ============================================================
# 기초 데이터 테이블
# ============================================================

# === 천간 (Heavenly Stems) ===
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
CHEONGAN_ELEMENTS = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
CHEONGAN_YINYANG = ["양", "음", "양", "음", "양", "음", "양", "음", "양", "음"]

# === 지지 (Earthly Branches) ===
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIJI_ANIMALS = ["쥐", "소", "호랑이", "토끼", "용", "뱀",
                "말", "양", "원숭이", "닭", "개", "돼지"]
JIJI_ELEMENTS = ["수", "토", "목", "목", "토", "화",
                 "화", "토", "금", "금", "토", "수"]

# === 지지 지장간 (Hidden Stems in Branches) ===
JIJANGGAN = {
    "자": ["계"],
    "축": ["계", "신", "기"],
    "인": ["무", "병", "갑"],
    "묘": ["을"],
    "진": ["을", "계", "무"],
    "사": ["무", "경", "병"],
    "오": ["기", "정"],
    "미": ["정", "을", "기"],
    "신": ["무", "임", "경"],
    "유": ["신"],
    "술": ["신", "정", "무"],
    "해": ["무", "갑", "임"],
}

# === 오행 상생상극 ===
SANG_SAENG = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}  # 생
SANG_GEUK = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}  # 극

# === 십신 (Ten Gods) ===
SIPSIN_NAMES = {
    (True, True): "비견",     # 같은 오행, 같은 음양
    (True, False): "겁재",    # 같은 오행, 다른 음양
    (False, True, "생"): "식신",   # 내가 생, 같은 음양
    (False, False, "생"): "상관",  # 내가 생, 다른 음양
    (False, True, "극"): "편재",   # 내가 극, 같은 음양
    (False, False, "극"): "정재",  # 내가 극, 다른 음양
    (False, True, "극받"): "편관", # 나를 극, 같은 음양
    (False, False, "극받"): "정관",# 나를 극, 다른 음양
    (False, True, "생받"): "편인", # 나를 생, 같은 음양
    (False, False, "생받"): "정인",# 나를 생, 다른 음양
}

# === 12운성 (Twelve Growth Stages) ===
TWELVE_STAGES = ["장생", "목욕", "관대", "건록", "제왕", "쇠",
                 "병", "사", "묘", "절", "태", "양"]

# 일간별 12운성 시작 지지 인덱스 (장생 위치)
TWELVE_STAGE_START = {
    "갑": 2,   # 인
    "을": 5,   # 사 (역행: 오→사→진...)
    "병": 2,   # 인
    "정": 5,   # 사
    "무": 2,   # 인
    "기": 5,   # 사
    "경": 8,   # 신
    "신": 11,  # 해
    "임": 8,   # 신
    "계": 11,  # 해
}

# 음간은 역행
CHEONGAN_IS_YANG = {s: (i % 2 == 0) for i, s in enumerate(CHEONGAN)}


# ============================================================
# 60갑자 테이블 구축
# ============================================================

SIXTY_CYCLE = []
for i in range(60):
    si = i % 10
    bi = i % 12
    SIXTY_CYCLE.append({
        "index": i,
        "stem": CHEONGAN[si],
        "branch": JIJI[bi],
        "stem_hanja": CHEONGAN_HANJA[si],
        "branch_hanja": JIJI_HANJA[bi],
        "hanja": f"{CHEONGAN_HANJA[si]}{JIJI_HANJA[bi]}",
        "korean": f"{CHEONGAN[si]}{JIJI[bi]}",
        "full": f"{CHEONGAN[si]}({CHEONGAN_HANJA[si]}) {JIJI[bi]}({JIJI_HANJA[bi]})",
        "stem_idx": si,
        "branch_idx": bi,
        "stem_element": CHEONGAN_ELEMENTS[si],
        "branch_element": JIJI_ELEMENTS[bi],
        "stem_yinyang": CHEONGAN_YINYANG[si],
    })


def find_cycle(stem_idx, branch_idx):
    """60갑자에서 천간/지지 인덱스로 찾기"""
    for c in SIXTY_CYCLE:
        if c["stem_idx"] == stem_idx and c["branch_idx"] == branch_idx:
            return c
    return SIXTY_CYCLE[0]


# ============================================================
# 핵심 사주 계산 (korean-lunar-calendar 기반)
# ============================================================

def _parse_gapja_string(gapja_str):
    """
    korean-lunar-calendar의 getGapJaString() 결과 파싱
    예: '무진년 신유월 정해일' → [(무,진), (신,유), (정,해)]
    """
    parts = gapja_str.strip().split()
    result = []
    for part in parts:
        # '무진년', '신유월', '정해일' → 앞 두 글자만
        stem = part[0]
        branch = part[1]
        result.append((stem, branch))
    return result


def get_pillars_from_calendar(year, month, day):
    """
    korean-lunar-calendar로 연주/월주/일주 정밀 계산
    절기 기반 자동 처리됨
    """
    cal = KoreanLunarCalendar()
    cal.setSolarDate(year, month, day)
    gapja = cal.getGapJaString()
    parsed = _parse_gapja_string(gapja)

    pillars = []
    for stem, branch in parsed:
        si = CHEONGAN.index(stem)
        bi = JIJI.index(branch)
        pillars.append(find_cycle(si, bi))

    return pillars  # [연주, 월주, 일주]


def get_hour_pillar(hour, minute, day_stem_idx):
    """
    시주(時柱) 계산
    시간대별 지지 + 일간(日干)에 따른 시간 계산

    자시(子時) 23:00~00:59
    축시(丑時) 01:00~02:59
    인시(寅時) 03:00~04:59 ...
    """
    # 시간 → 지지 인덱스
    if hour == 23 or hour == 0:
        branch_idx = 0  # 자시
    else:
        branch_idx = (hour + 1) // 2

    # 시간 → 천간: 일간 기반 오호접기법(五虎遁起法)
    # 갑기일 → 甲子시부터, 을경일 → 丙子시부터...
    day_stem_group = day_stem_idx % 5
    hour_stem_start = (day_stem_group * 2) % 10
    stem_idx = (hour_stem_start + branch_idx) % 10

    return find_cycle(stem_idx, branch_idx)


# ============================================================
# 십신 (Ten Gods) 분석
# ============================================================

def get_sipsin(day_stem, target_stem):
    """일간 기준 대상 천간의 십신 판별"""
    ds_elem = CHEONGAN_ELEMENTS[CHEONGAN.index(day_stem)]
    ts_elem = CHEONGAN_ELEMENTS[CHEONGAN.index(target_stem)]
    ds_yy = CHEONGAN_IS_YANG[day_stem]
    ts_yy = CHEONGAN_IS_YANG[target_stem]
    same_yy = (ds_yy == ts_yy)

    if ds_elem == ts_elem:
        return "비견" if same_yy else "겁재"
    elif SANG_SAENG[ds_elem] == ts_elem:
        return "식신" if same_yy else "상관"
    elif SANG_GEUK[ds_elem] == ts_elem:
        return "편재" if same_yy else "정재"
    elif SANG_GEUK[ts_elem] == ds_elem:
        return "편관" if same_yy else "정관"
    elif SANG_SAENG[ts_elem] == ds_elem:
        return "편인" if same_yy else "정인"
    return "비견"


def analyze_ten_gods(day_stem, pillars):
    """사주 전체 십신 분석"""
    results = []
    for p in pillars:
        stem_sipsin = get_sipsin(day_stem, p["stem"])
        # 지지 지장간의 정기 십신
        jjg = JIJANGGAN[p["branch"]]
        branch_sipsin = get_sipsin(day_stem, jjg[-1])  # 정기 = 마지막
        results.append({
            "pillar": p["korean"],
            "stem_sipsin": stem_sipsin,
            "branch_sipsin": branch_sipsin,
            "jijanggan": jjg,
        })
    return results


# ============================================================
# 12운성 (Twelve Growth Stages)
# ============================================================

def get_twelve_stage(day_stem, branch):
    """일간 기준 지지의 12운성"""
    start = TWELVE_STAGE_START[day_stem]
    bi = JIJI.index(branch)
    is_yang = CHEONGAN_IS_YANG[day_stem]

    if is_yang:
        stage_idx = (bi - start) % 12
    else:
        stage_idx = (start - bi) % 12

    return TWELVE_STAGES[stage_idx]


def analyze_twelve_stages(day_stem, pillars):
    """사주 전체 12운성"""
    return [
        {"pillar": p["korean"], "stage": get_twelve_stage(day_stem, p["branch"])}
        for p in pillars
    ]


# ============================================================
# 오행 분석 + 용신 추정
# ============================================================

def analyze_five_elements(pillars):
    """오행 분포 분석 (천간 + 지지 + 지장간)"""
    elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}

    for p in pillars:
        elements[p["stem_element"]] += 1.0
        elements[p["branch_element"]] += 0.7  # 지지는 가중치 0.7
        # 지장간도 가중치 포함
        for jjg_stem in JIJANGGAN[p["branch"]]:
            elem = CHEONGAN_ELEMENTS[CHEONGAN.index(jjg_stem)]
            elements[elem] += 0.3

    # 소수점 정리
    elements = {k: round(v, 1) for k, v in elements.items()}
    return elements


def estimate_yongshin(day_stem, five_elements):
    """
    용신(用神) 추정 — 간략 자동 판정
    일간 오행의 강약을 판단하여 필요한 오행 추정

    실제로는 월령/통근/투출 등 복합 판단 필요하나,
    자동화 1차 버전으로 오행 분포 기반 추정
    """
    day_elem = CHEONGAN_ELEMENTS[CHEONGAN.index(day_stem)]

    # 일간을 돕는 오행: 비겁(같은 오행) + 인성(나를 생하는 오행)
    helping_elem = day_elem
    # 나를 생하는 오행 찾기
    for k, v in SANG_SAENG.items():
        if v == day_elem:
            parent_elem = k
            break
    else:
        parent_elem = day_elem

    strength = five_elements.get(day_elem, 0) + five_elements.get(parent_elem, 0)
    total = sum(five_elements.values())
    ratio = strength / total if total > 0 else 0.5

    if ratio > 0.45:
        # 신강(身強) → 설기/극: 식상, 재성, 관성이 용신
        yongshin_elem = SANG_SAENG[day_elem]  # 식상 (내가 생하는 것)
        body_strength = "신강(身強)"
        strategy = "설기(洩氣) — 에너지를 분출하고 활용하는 방향"
    elif ratio < 0.30:
        # 신약(身弱) → 생부/비겁: 인성, 비겁이 용신
        yongshin_elem = parent_elem  # 나를 생하는 오행
        body_strength = "신약(身弱)"
        strategy = "생부(生扶) — 자아를 강화하고 지지받는 방향"
    else:
        # 중화(中和) → 가장 약한 오행 보충
        weakest = min(five_elements, key=five_elements.get)
        yongshin_elem = weakest
        body_strength = "중화(中和)"
        strategy = "조후(調候) — 균형을 세밀하게 조율하는 방향"

    # 기신(忌神) = 용신을 극하는 오행
    for k, v in SANG_GEUK.items():
        if v == yongshin_elem:
            gishin_elem = k
            break
    else:
        gishin_elem = "토"

    return {
        "body_strength": body_strength,
        "day_element": day_elem,
        "strength_ratio": round(ratio, 2),
        "yongshin": yongshin_elem,
        "yongshin_desc": f"용신: {yongshin_elem}({SANG_SAENG.get(yongshin_elem, '')} 생)",
        "gishin": gishin_elem,
        "strategy": strategy,
    }


# ============================================================
# 신살 (Special Stars)
# ============================================================

def analyze_sinsal(pillars):
    """주요 신살 분석"""
    results = []
    year_branch = pillars[0]["branch"]
    day_branch = pillars[2]["branch"]
    ybi = JIJI.index(year_branch)
    dbi = JIJI.index(day_branch)

    # --- 역마살 (驛馬殺) ---
    yeokma_map = {"인": "신", "사": "해", "신": "인", "해": "사",
                  "자": "오", "오": "자", "묘": "유", "유": "묘",
                  "축": "미", "미": "축", "진": "술", "술": "진"}
    # 삼합 기준 역마: 인오술→신, 사유축→해, 신자진→인, 해묘미→사
    samhap_yeokma = {
        "인": "신", "오": "신", "술": "신",
        "사": "해", "유": "해", "축": "해",
        "신": "인", "자": "인", "진": "인",
        "해": "사", "묘": "사", "미": "사",
    }
    ym_target = samhap_yeokma.get(year_branch)
    for i, p in enumerate(pillars):
        if p["branch"] == ym_target:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "역마살(驛馬殺)", "position": pos,
                           "desc": "이동, 변화, 활동성이 강함. 해외운 좋음."})

    # --- 도화살 (桃花殺) ---
    samhap_dohwa = {
        "인": "묘", "오": "묘", "술": "묘",
        "사": "오", "유": "오", "축": "오",
        "신": "유", "자": "유", "진": "유",
        "해": "자", "묘": "자", "미": "자",
    }
    dh_target = samhap_dohwa.get(year_branch)
    for i, p in enumerate(pillars):
        if p["branch"] == dh_target:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "도화살(桃花殺)", "position": pos,
                           "desc": "매력, 예술적 감각, 이성운. 긍정적으로는 대중적 인기."})

    # --- 화개살 (華蓋殺) ---
    samhap_hwagae = {
        "인": "술", "오": "술", "술": "술",
        "사": "축", "유": "축", "축": "축",
        "신": "진", "자": "진", "진": "진",
        "해": "미", "묘": "미", "미": "미",
    }
    hg_target = samhap_hwagae.get(year_branch)
    for i, p in enumerate(pillars):
        if p["branch"] == hg_target:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "화개살(華蓋殺)", "position": pos,
                           "desc": "학문, 종교, 예술적 재능. 고독한 탐구자."})

    # --- 공망 (空亡) ---
    day_cycle_idx = pillars[2]["index"]
    group_start = (day_cycle_idx // 10) * 10
    empty_b1 = (group_start + 10) % 12
    empty_b2 = (group_start + 11) % 12
    for i, p in enumerate(pillars):
        if p["branch_idx"] in [empty_b1, empty_b2]:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "공망(空亡)", "position": pos,
                           "desc": "비어있는 에너지. 집착을 내려놓으면 영적 성장."})

    # --- 양인살 (羊刃殺) ---
    yangin_map = {"갑": "묘", "을": "인", "병": "오", "정": "사",
                  "무": "오", "기": "사", "경": "유", "신": "신",
                  "임": "자", "계": "해"}
    day_stem = pillars[2]["stem"]
    yi_target = yangin_map.get(day_stem)
    for i, p in enumerate(pillars):
        if p["branch"] == yi_target:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "양인살(羊刃殺)", "position": pos,
                           "desc": "강한 추진력과 결단력. 과하면 무모함."})

    # --- 귀문관살 (鬼門關殺) ---
    gwimun_map = {"자": "유", "축": "오", "인": "미", "묘": "사",
                  "진": "묘", "사": "인", "오": "축", "미": "자",
                  "신": "해", "유": "술", "술": "유", "해": "신"}
    gm_target = gwimun_map.get(day_branch)
    for i, p in enumerate(pillars):
        if i == 2:
            continue
        if p["branch"] == gm_target:
            pos = ["연", "월", "일", "시"][i]
            results.append({"name": "귀문관살(鬼門關殺)", "position": pos,
                           "desc": "영적 감수성, 직관력. 심리/영적 분야 적성."})

    return results


# ============================================================
# 대운 (Major Luck Cycles) — 정밀 계산
# ============================================================

def calculate_daeun(year, month, day, hour, gender, pillars):
    """
    대운 계산 (정밀)
    - 성별 + 연간 음양으로 순행/역행 결정
    - 대운 시작 나이: 절기까지 일수 / 3 (간략화)
    """
    year_stem_yang = CHEONGAN_IS_YANG[pillars[0]["stem"]]
    is_male = gender.lower() in ["m", "male", "남", "남자"]

    # 양남음녀 → 순행, 음남양녀 → 역행
    forward = (year_stem_yang and is_male) or (not year_stem_yang and not is_male)

    # 월주의 60갑자 인덱스
    month_cycle_idx = pillars[1]["index"]

    # 대운 시작 나이 (간략: 생일~절기 일수 / 3, 평균 3세)
    # TODO: 실제 절기 정밀 계산 추가
    start_age = 3

    daeun_list = []
    for i in range(1, 11):  # 10개 대운
        if forward:
            idx = (month_cycle_idx + i) % 60
        else:
            idx = (month_cycle_idx - i) % 60

        age = start_age + (i - 1) * 10
        cycle = SIXTY_CYCLE[idx]
        stage = get_twelve_stage(pillars[2]["stem"], cycle["branch"])

        daeun_list.append({
            "order": i,
            "age": age,
            "year_start": year + age,
            "year_end": year + age + 9,
            "pillar": cycle["korean"],
            "full": cycle["full"],
            "hanja": cycle["hanja"],
            "stem_element": cycle["stem_element"],
            "branch_element": cycle["branch_element"],
            "twelve_stage": stage,
        })

    return {
        "direction": "순행" if forward else "역행",
        "start_age": start_age,
        "cycles": daeun_list
    }


# ============================================================
# 세운 (Annual Luck) — 연운 분석
# ============================================================

def calculate_seun(pillars, start_year=2024, count=10):
    """세운(연운) 계산"""
    day_stem = pillars[2]["stem"]
    seun_list = []

    for y in range(start_year, start_year + count):
        idx = (y - 4) % 60
        cycle = SIXTY_CYCLE[idx]
        sipsin = get_sipsin(day_stem, cycle["stem"])
        stage = get_twelve_stage(day_stem, cycle["branch"])

        seun_list.append({
            "year": y,
            "pillar": cycle["korean"],
            "hanja": cycle["hanja"],
            "stem_sipsin": sipsin,
            "twelve_stage": stage,
            "stem_element": cycle["stem_element"],
        })

    return seun_list


# ============================================================
# 메인 함수
# ============================================================

def calculate_saju(year, month, day, hour, gender="female", minute=0):
    """
    사주 전체 계산 메인 함수 v2.0

    Parameters:
        year: 출생 연도 (양력)
        month: 출생 월
        day: 출생 일
        hour: 출생 시 (24시간제)
        gender: "male"/"female" 또는 "남"/"여"
        minute: 출생 분 (기본 0)

    Returns:
        dict: 사주 전체 분석 결과
    """
    # 1. 연주/월주/일주 — korean-lunar-calendar 정밀 계산
    base_pillars = get_pillars_from_calendar(year, month, day)
    year_pillar, month_pillar, day_pillar = base_pillars

    # 2. 시주 — 일간 기반 자체 계산
    hour_pillar = get_hour_pillar(hour, minute, day_pillar["stem_idx"])

    pillars = [year_pillar, month_pillar, day_pillar, hour_pillar]

    # 3. 일간 (Day Master)
    day_stem = day_pillar["stem"]
    day_elem = CHEONGAN_ELEMENTS[CHEONGAN.index(day_stem)]
    day_yy = "양" if CHEONGAN_IS_YANG[day_stem] else "음"

    # 4. 오행 분석
    five_elements = analyze_five_elements(pillars)

    # 5. 십신 분석
    ten_gods = analyze_ten_gods(day_stem, pillars)

    # 6. 12운성
    twelve_stages = analyze_twelve_stages(day_stem, pillars)

    # 7. 용신 추정
    yongshin = estimate_yongshin(day_stem, five_elements)

    # 8. 신살 분석
    sinsal = analyze_sinsal(pillars)

    # 9. 대운
    daeun = calculate_daeun(year, month, day, hour, gender, pillars)

    # 10. 세운 (2024~2033)
    current_year = datetime.now().year
    seun = calculate_seun(pillars, current_year, 10)

    # 11. 음력 정보
    cal = KoreanLunarCalendar()
    cal.setSolarDate(year, month, day)
    lunar_date = cal.LunarIsoFormat()

    # 띠
    animal = JIJI_ANIMALS[year_pillar["branch_idx"]]

    return {
        "system": "사주명리 (四柱命理)",
        "version": "2.0",
        "birth_info": {
            "solar": f"{year}-{month:02d}-{day:02d}",
            "lunar": lunar_date,
            "hour": hour,
            "minute": minute,
            "gender": gender,
        },
        "four_pillars": {
            "year": {
                "pillar": year_pillar["korean"],
                "full": year_pillar["full"],
                "hanja": year_pillar["hanja"],
                "stem_element": year_pillar["stem_element"],
                "branch_element": year_pillar["branch_element"],
            },
            "month": {
                "pillar": month_pillar["korean"],
                "full": month_pillar["full"],
                "hanja": month_pillar["hanja"],
                "stem_element": month_pillar["stem_element"],
                "branch_element": month_pillar["branch_element"],
            },
            "day": {
                "pillar": day_pillar["korean"],
                "full": day_pillar["full"],
                "hanja": day_pillar["hanja"],
                "stem_element": day_pillar["stem_element"],
                "branch_element": day_pillar["branch_element"],
            },
            "hour": {
                "pillar": hour_pillar["korean"],
                "full": hour_pillar["full"],
                "hanja": hour_pillar["hanja"],
                "stem_element": hour_pillar["stem_element"],
                "branch_element": hour_pillar["branch_element"],
            },
        },
        "day_master": {
            "stem": day_stem,
            "hanja": CHEONGAN_HANJA[CHEONGAN.index(day_stem)],
            "element": day_elem,
            "yinyang": day_yy,
            "description": f"{day_yy}{day_elem} ({day_stem})",
        },
        "animal_sign": animal,
        "five_elements": five_elements,
        "ten_gods": ten_gods,
        "twelve_stages": twelve_stages,
        "yongshin": yongshin,
        "sinsal": sinsal,
        "daeun": daeun,
        "seun": seun,
        "summary": (
            f"일간: {day_stem}({CHEONGAN_HANJA[CHEONGAN.index(day_stem)]}) "
            f"— {day_yy}{day_elem}\n"
            f"띠: {animal}\n"
            f"사주: {year_pillar['hanja']} {month_pillar['hanja']} "
            f"{day_pillar['hanja']} {hour_pillar['hanja']}\n"
            f"     {year_pillar['korean']} {month_pillar['korean']} "
            f"{day_pillar['korean']} {hour_pillar['korean']}\n"
            f"오행: {five_elements}\n"
            f"용신: {yongshin['yongshin']}({yongshin['body_strength']})\n"
            f"대운: {daeun['direction']}, {daeun['start_age']}세 시작\n"
            f"신살: {', '.join(s['name'] for s in sinsal) if sinsal else '없음'}"
        )
    }


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔮 사주명리 계산 엔진 v2.0 테스트")
    print("=" * 60)

    # 박선영: 1988-09-29, 23:25, 여성
    result = calculate_saju(1988, 9, 29, 23, "female", 25)
    print(f"\n{result['summary']}")

    print(f"\n[십신]")
    for tg in result['ten_gods']:
        print(f"  {tg['pillar']}: {tg['stem_sipsin']} / {tg['branch_sipsin']}")

    print(f"\n[12운성]")
    for ts in result['twelve_stages']:
        print(f"  {ts['pillar']}: {ts['stage']}")

    print(f"\n[신살]")
    for s in result['sinsal']:
        print(f"  {s['name']} ({s['position']}주): {s['desc']}")

    print(f"\n[대운] {result['daeun']['direction']}")
    for d in result['daeun']['cycles']:
        print(f"  {d['age']}~{d['age']+9}세 ({d['year_start']}~{d['year_end']}): "
              f"{d['full']} [{d['twelve_stage']}]")

    print(f"\n[세운]")
    for s in result['seun'][:5]:
        print(f"  {s['year']}: {s['pillar']} — {s['stem_sipsin']} [{s['twelve_stage']}]")
