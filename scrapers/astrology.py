"""
점성학 차트 계산 모듈
Astrology Chart Calculator using Kerykeion

서양 점성학 (Modern/Placidus), 베딕, 헬레니스틱 차트 데이터 생성
"""

from kerykeion import AstrologicalSubject
from datetime import datetime
import json


# === 행성 한국어 매핑 ===
PLANET_KR = {
    "Sun": "태양 ☉",
    "Moon": "달 ☽",
    "Mercury": "수성 ☿",
    "Venus": "금성 ♀",
    "Mars": "화성 ♂",
    "Jupiter": "목성 ♃",
    "Saturn": "토성 ♄",
    "Uranus": "천왕성 ♅",
    "Neptune": "해왕성 ♆",
    "Pluto": "명왕성 ♇",
    "Mean_Node": "북교점 ☊",
    "True_Node": "북교점 ☊",
    "Chiron": "키론 ⚷",
}

# === 별자리 한국어 매핑 ===
SIGN_KR = {
    "Ari": "양자리 ♈", "Tau": "황소자리 ♉", "Gem": "쌍둥이자리 ♊",
    "Can": "게자리 ♋", "Leo": "사자자리 ♌", "Vir": "처녀자리 ♍",
    "Lib": "천칭자리 ♎", "Sco": "전갈자리 ♏", "Sag": "궁수자리 ♐",
    "Cap": "염소자리 ♑", "Aqu": "물병자리 ♒", "Pis": "물고기자리 ♓",
}

SIGN_FULL_KR = {
    "Ari": "양자리", "Tau": "황소자리", "Gem": "쌍둥이자리",
    "Can": "게자리", "Leo": "사자자리", "Vir": "처녀자리",
    "Lib": "천칭자리", "Sco": "전갈자리", "Sag": "궁수자리",
    "Cap": "염소자리", "Aqu": "물병자리", "Pis": "물고기자리",
}

# === 하우스 의미 ===
HOUSE_MEANINGS = {
    1: "자아, 외모, 첫인상",
    2: "재산, 가치관, 자기가치",
    3: "소통, 학습, 형제",
    4: "가정, 뿌리, 내면",
    5: "창조, 로맨스, 자녀",
    6: "건강, 일상, 봉사",
    7: "파트너십, 결혼, 계약",
    8: "변환, 공유자원, 심층심리",
    9: "철학, 해외, 고등교육",
    10: "커리어, 사회적 지위",
    11: "친구, 커뮤니티, 희망",
    12: "잠재의식, 은둔, 영성",
}

# === 원소/모드 매핑 ===
ELEMENT_MAP = {
    "Ari": "불(Fire)", "Leo": "불(Fire)", "Sag": "불(Fire)",
    "Tau": "흙(Earth)", "Vir": "흙(Earth)", "Cap": "흙(Earth)",
    "Gem": "바람(Air)", "Lib": "바람(Air)", "Aqu": "바람(Air)",
    "Can": "물(Water)", "Sco": "물(Water)", "Pis": "물(Water)",
}

MODE_MAP = {
    "Ari": "카디널", "Can": "카디널", "Lib": "카디널", "Cap": "카디널",
    "Tau": "고정", "Leo": "고정", "Sco": "고정", "Aqu": "고정",
    "Gem": "변통", "Vir": "변통", "Sag": "변통", "Pis": "변통",
}

# === 주요 애스펙트 ===
ASPECT_NAMES = {
    "conjunction": "합(0°)",
    "opposition": "충(180°)",
    "trine": "삼합(120°)",
    "square": "각(90°)",
    "sextile": "육합(60°)",
}


def get_planet_data(subject, planet_name):
    """행성 객체에서 데이터 추출"""
    planet = getattr(subject, planet_name.lower(), None)
    if planet is None:
        return None

    try:
        return {
            "name": PLANET_KR.get(planet_name, planet_name),
            "sign": SIGN_KR.get(planet.sign, planet.sign),
            "sign_code": planet.sign,
            "degree": round(planet.position, 2),
            "abs_degree": round(planet.abs_pos, 2) if hasattr(planet, 'abs_pos') else None,
            "house": planet.house if hasattr(planet, 'house') else None,
            "retrograde": getattr(planet, 'retrograde', False),
            "element": ELEMENT_MAP.get(planet.sign, ""),
        }
    except Exception:
        return None


def calculate_aspects(subject):
    """주요 애스펙트 계산"""
    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars",
               "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

    aspects = []
    orbs = {
        "conjunction": 8, "opposition": 8, "trine": 8,
        "square": 7, "sextile": 6
    }
    aspect_angles = {
        "conjunction": 0, "opposition": 180, "trine": 120,
        "square": 90, "sextile": 60
    }

    for i, p1_name in enumerate(planets):
        p1 = getattr(subject, p1_name.lower(), None)
        if p1 is None:
            continue
        for j, p2_name in enumerate(planets):
            if j <= i:
                continue
            p2 = getattr(subject, p2_name.lower(), None)
            if p2 is None:
                continue

            try:
                diff = abs(p1.abs_pos - p2.abs_pos)
                if diff > 180:
                    diff = 360 - diff

                for asp_name, angle in aspect_angles.items():
                    orb = abs(diff - angle)
                    if orb <= orbs[asp_name]:
                        aspects.append({
                            "planet1": PLANET_KR.get(p1_name, p1_name),
                            "planet2": PLANET_KR.get(p2_name, p2_name),
                            "aspect": ASPECT_NAMES.get(asp_name, asp_name),
                            "orb": round(orb, 2),
                            "exact": orb < 1
                        })
            except Exception:
                continue

    return aspects


def analyze_element_balance(planet_data_list):
    """원소 균형 분석"""
    elements = {"불(Fire)": 0, "흙(Earth)": 0, "바람(Air)": 0, "물(Water)": 0}
    modes = {"카디널": 0, "고정": 0, "변통": 0}

    for pd in planet_data_list:
        if pd and pd.get("element"):
            elements[pd["element"]] = elements.get(pd["element"], 0) + 1
        if pd and pd.get("sign_code"):
            mode = MODE_MAP.get(pd["sign_code"], "")
            if mode in modes:
                modes[mode] += 1

    return {"elements": elements, "modes": modes}


def calculate_astrology(year, month, day, hour, minute, city, lat, lon, tz_str):
    """
    점성학 차트 전체 계산

    Parameters:
        year, month, day: 출생일
        hour, minute: 출생 시간
        city: 출생 도시명
        lat, lon: 위도/경도
        tz_str: 타임존 문자열

    Returns:
        dict: 점성학 차트 데이터
    """
    try:
        subject = AstrologicalSubject(
            name="Client",
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            city=city,
            nation="",
            lat=lat,
            lng=lon,
            tz_str=tz_str,
            online=False,
        )
    except Exception as e:
        return {"error": f"점성학 차트 계산 실패: {str(e)}"}

    # 행성 데이터 수집
    planet_names = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

    planets = {}
    planet_data_list = []
    for name in planet_names:
        data = get_planet_data(subject, name)
        if data:
            planets[name] = data
            planet_data_list.append(data)

    # 노드 데이터
    for node_name in ["Mean_Node", "True_Node"]:
        data = get_planet_data(subject, node_name)
        if data:
            planets[node_name] = data

    # 하우스 데이터
    HOUSE_ATTR_NAMES = [
        "first_house", "second_house", "third_house", "fourth_house",
        "fifth_house", "sixth_house", "seventh_house", "eighth_house",
        "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
    ]
    houses = {}
    for i, attr_name in enumerate(HOUSE_ATTR_NAMES, 1):
        try:
            h = getattr(subject, attr_name, None)
            if h:
                houses[i] = {
                    "sign": SIGN_KR.get(h.sign, h.sign) if hasattr(h, 'sign') else "",
                    "degree": round(h.position, 2) if hasattr(h, 'position') else 0,
                    "meaning": HOUSE_MEANINGS.get(i, ""),
                }
            else:
                houses[i] = {"sign": "", "degree": 0, "meaning": HOUSE_MEANINGS.get(i, "")}
        except Exception:
            houses[i] = {"sign": "", "degree": 0, "meaning": HOUSE_MEANINGS.get(i, "")}

    # 애스펙트 계산
    aspects = calculate_aspects(subject)

    # 원소/모드 밸런스
    balance = analyze_element_balance(planet_data_list)

    # Big Three 요약
    sun_data = planets.get("Sun", {})
    moon_data = planets.get("Moon", {})

    # ASC (Ascendant)
    asc_sign = ""
    if houses.get(1):
        asc_sign = houses[1].get("sign", "")

    # 베딕 차트용 사이드리얼 오프셋 (아야남사 약 -24도)
    AYANAMSA = 24.11  # 라히리 아야남사 (대략값)
    vedic_planets = {}
    for name, data in planets.items():
        if data.get("abs_degree") is not None:
            vedic_deg = (data["abs_degree"] - AYANAMSA) % 360
            vedic_sign_idx = int(vedic_deg / 30)
            signs_list = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                         "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
            vedic_sign = signs_list[vedic_sign_idx]
            vedic_planets[name] = {
                "name": data["name"],
                "sign": SIGN_KR.get(vedic_sign, vedic_sign),
                "degree": round(vedic_deg % 30, 2),
                "nakshatra": get_nakshatra(vedic_deg),
            }

    return {
        "system": "서양 점성학 (Western Astrology)",
        "birth_info": {
            "year": year, "month": month, "day": day,
            "hour": hour, "minute": minute,
            "city": city, "lat": lat, "lon": lon,
        },
        "big_three": {
            "sun": sun_data.get("sign", ""),
            "moon": moon_data.get("sign", ""),
            "ascendant": asc_sign,
        },
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "element_balance": balance,
        "vedic_planets": vedic_planets,
        "summary": (
            f"태양: {sun_data.get('sign', '?')} {sun_data.get('degree', '')}°\n"
            f"달: {moon_data.get('sign', '?')} {moon_data.get('degree', '')}°\n"
            f"ASC: {asc_sign}\n"
            f"원소 균형: {balance['elements']}\n"
            f"주요 애스펙트: {len(aspects)}개"
        )
    }


def get_nakshatra(sidereal_degree):
    """베딕 점성학 낙샤트라 계산"""
    nakshatras = [
        "아슈비니(Ashwini)", "바라니(Bharani)", "크리티카(Krittika)",
        "로히니(Rohini)", "므리가시르샤(Mrigashirsha)", "아르드라(Ardra)",
        "푸나르바수(Punarvasu)", "푸시야(Pushya)", "아슐레샤(Ashlesha)",
        "마가(Magha)", "푸르바 팔구니(Purva Phalguni)", "우타라 팔구니(Uttara Phalguni)",
        "하스타(Hasta)", "치트라(Chitra)", "스바티(Swati)",
        "비샤카(Vishakha)", "아누라다(Anuradha)", "예슈타(Jyeshtha)",
        "물라(Mula)", "푸르바샤다(Purva Ashadha)", "우타라샤다(Uttara Ashadha)",
        "슈라바나(Shravana)", "다니슈타(Dhanishta)", "샤타비샤(Shatabhisha)",
        "푸르바 바드라파다(Purva Bhadrapada)", "우타라 바드라파다(Uttara Bhadrapada)",
        "레바티(Revati)"
    ]

    nak_size = 360 / 27
    idx = int(sidereal_degree / nak_size)
    return nakshatras[idx % 27]


if __name__ == "__main__":
    result = calculate_astrology(1990, 3, 15, 14, 30, "Seoul", 37.5665, 126.978, "Asia/Seoul")
    if "error" not in result:
        print("=== 점성학 차트 ===")
        print(f"Big Three: {result['big_three']}")
        print(f"\n행성:")
        for name, data in result['planets'].items():
            print(f"  {data['name']}: {data['sign']} {data['degree']}°")
        print(f"\n애스펙트: {len(result['aspects'])}개")
    else:
        print(result["error"])
