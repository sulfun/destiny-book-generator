"""
수비학 (Numerology) 계산 모듈
Numerology Calculator

생년월일과 이름으로 주요 수비학 수 계산
마스터넘버 11, 22 보존
"""


# === 피타고라스 수비학 문자-숫자 매핑 ===
PYTHAGOREAN_MAP = {
    'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
    'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
    's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8,
}

VOWELS = set('aeiou')
CONSONANTS = set('bcdfghjklmnpqrstvwxyz')

# === 마스터 넘버 ===
MASTER_NUMBERS = {11, 22, 33}

# === 수 의미 해석 ===
NUMBER_MEANINGS = {
    1: {
        "keyword": "리더십, 독립, 개척",
        "description": "독립적이고 창의적인 리더. 새로운 시작과 개척의 에너지.",
        "strength": "자기 확신, 결단력, 독창성",
        "challenge": "독선, 고립, 타인과의 협력 부족",
    },
    2: {
        "keyword": "조화, 협력, 직관",
        "description": "조화와 균형을 추구하는 외교관. 섬세한 감수성과 직관력.",
        "strength": "공감, 중재, 세심함",
        "challenge": "우유부단, 의존성, 자기 주장 부족",
    },
    3: {
        "keyword": "창조, 표현, 소통",
        "description": "창조적 자기표현의 달인. 예술적 재능과 소통 능력.",
        "strength": "표현력, 낙관, 사교성",
        "challenge": "산만함, 감정 기복, 에너지 분산",
    },
    4: {
        "keyword": "안정, 체계, 근면",
        "description": "안정적 구조를 만드는 건축가. 체계적이고 실용적.",
        "strength": "성실함, 조직력, 인내",
        "challenge": "경직, 완고함, 변화 거부",
    },
    5: {
        "keyword": "자유, 변화, 모험",
        "description": "자유와 변화를 추구하는 모험가. 다재다능하고 적응력 뛰어남.",
        "strength": "적응력, 다재다능, 호기심",
        "challenge": "불안정, 산만, 책임 회피",
    },
    6: {
        "keyword": "책임, 돌봄, 조화",
        "description": "사랑과 책임의 수호자. 가정과 공동체에 헌신.",
        "strength": "책임감, 양육, 미적 감각",
        "challenge": "과잉 간섭, 완벽주의, 자기 희생",
    },
    7: {
        "keyword": "탐구, 지혜, 영성",
        "description": "진리를 탐구하는 철학자. 깊은 분석력과 영적 성장.",
        "strength": "분석력, 직관, 깊은 사고",
        "challenge": "고립, 냉소, 불신",
    },
    8: {
        "keyword": "권력, 풍요, 성취",
        "description": "물질적 세계의 마스터. 비즈니스 감각과 실행력.",
        "strength": "리더십, 비전, 물질적 성취",
        "challenge": "물질 집착, 권위주의, 워커홀릭",
    },
    9: {
        "keyword": "완성, 봉사, 인도주의",
        "description": "인류를 위한 봉사자. 넓은 시야과 자비심.",
        "strength": "자비, 이상주의, 창조성",
        "challenge": "과도한 이상, 감정 소모, 집착",
    },
    11: {
        "keyword": "영적 각성, 직관, 영감 [마스터넘버]",
        "description": "영적 메신저. 높은 직관력과 영감으로 타인을 이끄는 힘.",
        "strength": "직관, 영적 비전, 영감",
        "challenge": "불안, 자기 의심, 과민함",
    },
    22: {
        "keyword": "마스터 빌더, 대업, 실현 [마스터넘버]",
        "description": "비전을 현실로 만드는 마스터 빌더. 대규모 프로젝트의 실현자.",
        "strength": "실현력, 대규모 비전, 실용적 이상주의",
        "challenge": "자기 파괴, 압도감, 비현실적 기대",
    },
    33: {
        "keyword": "마스터 티처, 치유, 봉사 [마스터넘버]",
        "description": "우주적 사랑의 교사. 치유와 봉사를 통한 인류 상승.",
        "strength": "무조건적 사랑, 치유, 영적 가르침",
        "challenge": "자기 희생, 순교자 컴플렉스",
    },
}


def reduce_to_single(n, preserve_master=True):
    """
    숫자를 단일 자릿수로 환원
    마스터넘버(11, 22, 33)는 보존
    """
    while n > 9:
        if preserve_master and n in MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def life_path_number(year, month, day):
    """
    생명수 (Life Path Number) 계산
    생년월일 각 부분을 별도로 환원 후 합산
    """
    # 각 부분 별도 환원
    y = reduce_to_single(sum(int(d) for d in str(year)))
    m = reduce_to_single(sum(int(d) for d in str(month)))
    d = reduce_to_single(sum(int(d) for d in str(day)))

    total = y + m + d
    return reduce_to_single(total)


def birthday_number(day):
    """생일수 (Birthday Number) - 태어난 날만"""
    return reduce_to_single(day)


def expression_number(full_name):
    """
    표현수 (Expression/Destiny Number)
    이름의 모든 글자를 수로 변환하여 합산
    """
    if not full_name:
        return None

    total = 0
    for char in full_name.lower():
        if char in PYTHAGOREAN_MAP:
            total += PYTHAGOREAN_MAP[char]

    if total == 0:
        return None
    return reduce_to_single(total)


def soul_urge_number(full_name):
    """
    영혼수 (Soul Urge/Heart's Desire Number)
    이름의 모음만 합산
    """
    if not full_name:
        return None

    total = 0
    for char in full_name.lower():
        if char in VOWELS and char in PYTHAGOREAN_MAP:
            total += PYTHAGOREAN_MAP[char]

    if total == 0:
        return None
    return reduce_to_single(total)


def personality_number(full_name):
    """
    성격수 (Personality Number)
    이름의 자음만 합산
    """
    if not full_name:
        return None

    total = 0
    for char in full_name.lower():
        if char in CONSONANTS and char in PYTHAGOREAN_MAP:
            total += PYTHAGOREAN_MAP[char]

    if total == 0:
        return None
    return reduce_to_single(total)


def maturity_number(life_path, expression):
    """성숙수 (Maturity Number) = 생명수 + 표현수"""
    if life_path is None or expression is None:
        return None
    return reduce_to_single(life_path + expression)


def personal_year(year, month, day, current_year):
    """개인년수 (Personal Year Number)"""
    m = reduce_to_single(month)
    d = reduce_to_single(day)
    y = reduce_to_single(sum(int(x) for x in str(current_year)))
    return reduce_to_single(m + d + y)


def karmic_debt_numbers(year, month, day):
    """카르마 부채 수 확인 (13, 14, 16, 19)"""
    karmic_debts = []

    # 생일에서 확인
    if day in [13, 14, 16, 19]:
        karmic_debts.append(day)

    # 생명수 계산 중간값 확인
    total = sum(int(d) for d in str(year)) + month + day
    while total > 9 and total not in MASTER_NUMBERS:
        if total in [13, 14, 16, 19]:
            karmic_debts.append(total)
        total = sum(int(d) for d in str(total))

    return list(set(karmic_debts))


def pinnacle_numbers(life_path, month, day, year):
    """피너클 수 (Pinnacle Numbers) - 인생의 4단계"""
    m = reduce_to_single(month)
    d = reduce_to_single(day)
    y = reduce_to_single(sum(int(x) for x in str(year)))

    p1 = reduce_to_single(m + d)
    p2 = reduce_to_single(d + y)
    p3 = reduce_to_single(p1 + p2)
    p4 = reduce_to_single(m + y)

    # 피너클 기간 계산
    first_end = 36 - life_path
    if first_end < 27:
        first_end = 27

    return [
        {"pinnacle": 1, "number": p1, "period": f"출생 ~ {first_end}세"},
        {"pinnacle": 2, "number": p2, "period": f"{first_end+1} ~ {first_end+9}세"},
        {"pinnacle": 3, "number": p3, "period": f"{first_end+10} ~ {first_end+18}세"},
        {"pinnacle": 4, "number": p4, "period": f"{first_end+19}세 이후"},
    ]


def challenge_numbers(month, day, year):
    """도전수 (Challenge Numbers)"""
    m = reduce_to_single(month)
    d = reduce_to_single(day)
    y = reduce_to_single(sum(int(x) for x in str(year)))

    c1 = abs(m - d)
    c2 = abs(d - y)
    c3 = abs(c1 - c2)
    c4 = abs(m - y)

    return [
        reduce_to_single(c1, preserve_master=False),
        reduce_to_single(c2, preserve_master=False),
        reduce_to_single(c3, preserve_master=False),
        reduce_to_single(c4, preserve_master=False),
    ]


def calculate_numerology(year, month, day, full_name_en="", current_year=2026):
    """
    수비학 전체 계산 메인 함수

    Parameters:
        year, month, day: 출생일
        full_name_en: 영문 전체 이름 (선택)
        current_year: 개인년수 계산용 현재 연도

    Returns:
        dict: 수비학 분석 결과
    """
    lp = life_path_number(year, month, day)
    bd = birthday_number(day)
    expr = expression_number(full_name_en) if full_name_en else None
    soul = soul_urge_number(full_name_en) if full_name_en else None
    pers = personality_number(full_name_en) if full_name_en else None
    mat = maturity_number(lp, expr) if expr else None
    py = personal_year(year, month, day, current_year)
    karmic = karmic_debt_numbers(year, month, day)
    pinnacles = pinnacle_numbers(lp, month, day, year)
    challenges = challenge_numbers(month, day, year)

    # 개인년 5년 전망
    personal_years = []
    for y in range(current_year, current_year + 5):
        py_num = personal_year(year, month, day, y)
        personal_years.append({
            "year": y,
            "number": py_num,
            "meaning": NUMBER_MEANINGS.get(py_num, {}).get("keyword", "")
        })

    result = {
        "system": "수비학 (Numerology)",
        "birth_info": {"year": year, "month": month, "day": day, "name": full_name_en},
        "core_numbers": {
            "life_path": {
                "number": lp,
                "meaning": NUMBER_MEANINGS.get(lp, {}),
                "description": f"생명수 {lp} - {NUMBER_MEANINGS.get(lp, {}).get('keyword', '')}"
            },
            "birthday": {
                "number": bd,
                "meaning": NUMBER_MEANINGS.get(bd, {}),
            },
        },
        "personal_year": {
            "current": py,
            "year": current_year,
            "meaning": NUMBER_MEANINGS.get(py, {}).get("keyword", ""),
            "forecast": personal_years,
        },
        "karmic_debt": karmic,
        "pinnacles": pinnacles,
        "challenges": challenges,
    }

    # 이름 기반 수 (영문 이름 있을 때만)
    if full_name_en:
        result["name_numbers"] = {
            "expression": {"number": expr, "meaning": NUMBER_MEANINGS.get(expr, {})},
            "soul_urge": {"number": soul, "meaning": NUMBER_MEANINGS.get(soul, {})},
            "personality": {"number": pers, "meaning": NUMBER_MEANINGS.get(pers, {})},
            "maturity": {"number": mat, "meaning": NUMBER_MEANINGS.get(mat, {})},
        }

    result["summary"] = (
        f"생명수(Life Path): {lp} - {NUMBER_MEANINGS.get(lp, {}).get('keyword', '')}\n"
        f"생일수(Birthday): {bd}\n"
        f"개인년수 {current_year}: {py} - {NUMBER_MEANINGS.get(py, {}).get('keyword', '')}\n"
        f"카르마 부채: {karmic if karmic else '없음'}\n"
        + (f"표현수(Expression): {expr}\n영혼수(Soul Urge): {soul}\n" if full_name_en else "")
    )

    return result


if __name__ == "__main__":
    result = calculate_numerology(1990, 3, 15, "Sujin Lee")
    print("=== 수비학 계산 결과 ===")
    print(result["summary"])
    print(f"\n피너클:")
    for p in result["pinnacles"]:
        print(f"  {p['period']}: {p['number']}")
