"""
휴먼디자인 (Human Design) 계산 모듈
Human Design Chart Calculator

출생 데이터로부터 타입, 전략, 권위, 프로파일, 인카네이션 크로스,
정의된 센터, 게이트/채널 등을 계산

휴먼디자인 = 점성학(태양 위치) + 주역(I Ching 64괘) + 카발라 + 차크라 + 양자물리학
"""

import swisseph as swe
from datetime import datetime, timedelta
import math


# === 주역 64괘 → 휴먼디자인 게이트 매핑 ===
# 황도대 상의 게이트 순서 (0° 양자리부터 시작)
# 각 게이트는 360/64 = 5.625도씩 차지
GATE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63,  # 양자리~황소자리
    22, 36, 25, 17, 21, 51, 42, 3,   # 쌍둥이~게자리
    27, 24, 2, 23, 8, 20, 16, 35,    # 사자~처녀
    45, 12, 15, 52, 39, 53, 62, 56,  # 천칭~전갈
    31, 33, 7, 4, 29, 59, 40, 64,    # 궁수~염소
    47, 6, 46, 18, 48, 57, 32, 50,   # 물병~물고기
    28, 44, 1, 43, 14, 34, 9, 5,     # (계속)
    26, 11, 10, 58, 38, 54, 61, 60,  # (마지막)
]

# === 게이트 → 센터 매핑 ===
GATE_TO_CENTER = {
    # Head (머리)
    61: "Head", 63: "Head", 64: "Head",
    # Ajna (아즈나)
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    # Throat (목)
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat",
    12: "Throat", 45: "Throat", 33: "Throat", 8: "Throat",
    31: "Throat", 7: "Throat", 1: "Throat", 13: "Throat", 10: "Throat", 20: "Throat", 16: "Throat",
    # G Center (G 센터/자아)
    25: "G", 46: "G", 22: "G", 36: "G", 2: "G", 15: "G",
    # Heart/Will (심장/의지)
    21: "Heart", 51: "Heart", 26: "Heart", 40: "Heart",
    # Sacral (천골)
    5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral",
    9: "Sacral", 3: "Sacral", 42: "Sacral", 27: "Sacral",
    34: "Sacral",
    # Solar Plexus (태양신경총/감정)
    6: "SolarPlexus", 37: "SolarPlexus", 22: "SolarPlexus",
    36: "SolarPlexus", 49: "SolarPlexus", 55: "SolarPlexus", 30: "SolarPlexus",
    # Spleen (비장)
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen",
    32: "Spleen", 28: "Spleen", 18: "Spleen",
    # Root (루트)
    58: "Root", 38: "Root", 54: "Root", 53: "Root",
    60: "Root", 52: "Root", 19: "Root", 39: "Root", 41: "Root",
}

# === 채널 정의 (게이트 쌍 → 채널명) ===
CHANNELS = {
    (1, 8): "영감의 채널",
    (2, 14): "비트의 채널",
    (3, 60): "변이의 채널",
    (4, 63): "논리의 채널",
    (5, 15): "리듬의 채널",
    (6, 59): "친밀의 채널",
    (7, 31): "리더십의 채널",
    (9, 52): "집중의 채널",
    (10, 20): "각성의 채널",
    (10, 34): "탐험의 채널",
    (10, 57): "완벽한 형태의 채널",
    (11, 56): "호기심의 채널",
    (12, 22): "개방의 채널",
    (13, 33): "탕아의 채널",
    (16, 48): "재능의 채널",
    (17, 62): "수용의 채널",
    (18, 58): "판단의 채널",
    (19, 49): "통합의 채널",
    (20, 34): "카리스마의 채널",
    (20, 57): "뇌파의 채널",
    (21, 45): "돈의 채널",
    (23, 43): "구조화의 채널",
    (24, 61): "인식의 채널",
    (25, 51): "시작의 채널",
    (26, 44): "항복의 채널",
    (27, 50): "보존의 채널",
    (28, 38): "투쟁의 채널",
    (29, 46): "발견의 채널",
    (30, 41): "인식의 채널",
    (32, 54): "변환의 채널",
    (34, 57): "힘의 채널",
    (35, 36): "일시성의 채널",
    (37, 40): "공동체의 채널",
    (39, 55): "감정성의 채널",
    (42, 53): "성숙의 채널",
    (47, 64): "추상의 채널",
}

# === 게이트 이름 ===
GATE_NAMES = {
    1: "자기표현 (The Creative)", 2: "수용자의 방향 (The Receptive)",
    3: "질서 (Ordering)", 4: "공식화 (Formulization)",
    5: "기다림의 패턴 (Fixed Rhythms)", 6: "마찰 (Friction)",
    7: "자기 역할 (The Role of the Self)", 8: "기여 (Contribution)",
    9: "초점 (Focus)", 10: "자아의 행동 (Behavior of the Self)",
    11: "평화 (Peace)", 12: "정지 (Standstill)",
    13: "듣는 자 (The Listener)", 14: "풍요의 열쇠 (Power Skills)",
    15: "극단 (Extremes)", 16: "열정 (Enthusiasm)",
    17: "의견 (Opinions)", 18: "교정 (Correction)",
    19: "접근 (Approach)", 20: "현재 (The Now)",
    21: "사냥꾼 (The Hunter)", 22: "우아함 (Grace)",
    23: "분열 (Assimilation)", 24: "돌아옴 (Rationalization)",
    25: "무고함의 정신 (Spirit of the Self)", 26: "이기주의자 (The Taming Power)",
    27: "양육 (Nourishment)", 28: "위대함의 게임 (The Game Player)",
    29: "심연 (Perseverance)", 30: "불꽃 (Feelings)",
    31: "영향 (Influence)", 32: "지속 (Continuity)",
    33: "후퇴 (Privacy)", 34: "힘 (Power)",
    35: "변화 (Change)", 36: "위기 (Crisis)",
    37: "가족 (Friendship)", 38: "전투사 (The Fighter)",
    39: "도발 (Provocation)", 40: "전달 (Deliverance)",
    41: "감소 (Decrease)", 42: "증가 (Growth)",
    43: "통찰 (Insight)", 44: "경고 (Alertness)",
    45: "수집가 (The Gatherer)", 46: "몸의 사랑 (Determination)",
    47: "실현 (Realization)", 48: "깊이 (The Well)",
    49: "혁명 (Revolution)", 50: "가치 (Values)",
    51: "충격 (Shock)", 52: "정지 (Stillness)",
    53: "시작 (Beginnings)", 54: "야망 (Ambition)",
    55: "풍요 (Abundance)", 56: "자극 (Stimulation)",
    57: "직관 (Intuition)", 58: "기쁨 (Joy)",
    59: "분산 (Dispersion)", 60: "제한 (Limitation)",
    61: "내적 진실 (Inner Truth)", 62: "세부사항 (Details)",
    63: "의심 (After Completion)", 64: "완성 전 (Before Completion)",
}

# === 프로파일 매핑 ===
PROFILE_MEANINGS = {
    "1/3": "탐구자/순교자 (Investigator/Martyr)",
    "1/4": "탐구자/기회주의자 (Investigator/Opportunist)",
    "2/4": "은둔자/기회주의자 (Hermit/Opportunist)",
    "2/5": "은둔자/이단자 (Hermit/Heretic)",
    "3/5": "순교자/이단자 (Martyr/Heretic)",
    "3/6": "순교자/역할모델 (Martyr/Role Model)",
    "4/6": "기회주의자/역할모델 (Opportunist/Role Model)",
    "4/1": "기회주의자/탐구자 (Opportunist/Investigator)",
    "5/1": "이단자/탐구자 (Heretic/Investigator)",
    "5/2": "이단자/은둔자 (Heretic/Hermit)",
    "6/2": "역할모델/은둔자 (Role Model/Hermit)",
    "6/3": "역할모델/순교자 (Role Model/Martyr)",
}


def get_sun_position(year, month, day, hour, minute, lon=0, lat=0):
    """Swiss Ephemeris로 태양 위치(황경) 계산"""
    swe.set_ephe_path('')  # 기본 경로

    # 줄리안 데이 계산
    decimal_hour = hour + minute / 60.0
    jd = swe.julday(year, month, day, decimal_hour)

    # 태양 위치 계산
    sun_pos = swe.calc_ut(jd, swe.SUN)[0]
    return sun_pos[0]  # 황경 (longitude)


def get_planet_positions(year, month, day, hour, minute):
    """모든 주요 행성 위치 계산"""
    swe.set_ephe_path('')
    decimal_hour = hour + minute / 60.0
    jd = swe.julday(year, month, day, decimal_hour)

    planets = {
        "Sun": swe.SUN, "Earth": swe.SUN,  # Earth = Sun + 180
        "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS,
        "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
        "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
        "North_Node": swe.MEAN_NODE,
    }

    positions = {}
    for name, planet_id in planets.items():
        pos = swe.calc_ut(jd, planet_id)[0]
        if name == "Earth":
            positions[name] = (pos[0] + 180) % 360
        else:
            positions[name] = pos[0]

    return positions


def longitude_to_gate(longitude):
    """황경 → 휴먼디자인 게이트 변환"""
    # 각 게이트 = 5.625도
    gate_size = 360 / 64
    gate_idx = int(longitude / gate_size) % 64
    gate = GATE_ORDER[gate_idx]

    # 라인 계산 (각 게이트는 6라인)
    position_in_gate = (longitude % gate_size) / gate_size * 6
    line = int(position_in_gate) + 1
    if line > 6:
        line = 6

    return gate, line


def calculate_design_date(year, month, day, hour, minute):
    """
    디자인 날짜 계산 (출생 약 88일 전, 태양이 88도 뒤에 있는 시점)
    """
    swe.set_ephe_path('')

    # 출생 시점의 태양 위치
    decimal_hour = hour + minute / 60.0
    jd_birth = swe.julday(year, month, day, decimal_hour)
    sun_birth = swe.calc_ut(jd_birth, swe.SUN)[0][0]

    # 디자인 태양 위치 = 출생 태양 - 88도
    design_sun_target = (sun_birth - 88) % 360

    # 약 88일 전부터 탐색
    jd_search = jd_birth - 88
    for _ in range(30):  # 전후 30일 탐색
        sun_pos = swe.calc_ut(jd_search, swe.SUN)[0][0]
        diff = (design_sun_target - sun_pos) % 360
        if diff > 180:
            diff -= 360
        if abs(diff) < 0.01:
            break
        jd_search += diff  # 대략 1일당 1도
    else:
        jd_search = jd_birth - 88  # fallback

    # 줄리안 데이 → 날짜 변환
    design_date = swe.revjul(jd_search)
    return {
        "year": int(design_date[0]),
        "month": int(design_date[1]),
        "day": int(design_date[2]),
        "hour": int(design_date[3]),
        "minute": int((design_date[3] % 1) * 60),
        "jd": jd_search,
    }


def determine_type_and_authority(defined_centers, defined_channels):
    """타입과 권위 결정"""
    has_sacral = "Sacral" in defined_centers
    has_throat = "Throat" in defined_centers
    has_solar_plexus = "SolarPlexus" in defined_centers
    has_spleen = "Spleen" in defined_centers
    has_heart = "Heart" in defined_centers
    has_g = "G" in defined_centers

    # 천골과 목 연결 확인
    sacral_to_throat = False
    motor_to_throat = False

    # 간접 연결도 포함해야 하지만 간략화
    motor_centers = {"Sacral", "SolarPlexus", "Heart", "Root"}
    for ch_gates, ch_name in defined_channels.items():
        g1, g2 = ch_gates
        c1 = GATE_TO_CENTER.get(g1, "")
        c2 = GATE_TO_CENTER.get(g2, "")
        if ("Throat" in (c1, c2)) and (c1 in motor_centers or c2 in motor_centers):
            motor_to_throat = True
        if ("Throat" in (c1, c2)) and ("Sacral" in (c1, c2)):
            sacral_to_throat = True

    # 타입 결정
    if has_sacral and motor_to_throat:
        hd_type = "매니페스팅 제너레이터 (Manifesting Generator)"
        strategy = "반응하기 (To Respond)"
    elif has_sacral:
        hd_type = "제너레이터 (Generator)"
        strategy = "반응하기 (To Respond)"
    elif motor_to_throat and not has_sacral:
        hd_type = "매니페스터 (Manifestor)"
        strategy = "알리기 (To Inform)"
    elif not has_sacral and not motor_to_throat and defined_centers:
        hd_type = "프로젝터 (Projector)"
        strategy = "초대 기다리기 (Wait for the Invitation)"
    else:
        hd_type = "리플렉터 (Reflector)"
        strategy = "한 달 기다리기 (Wait a Lunar Cycle)"

    # 권위 결정
    if has_solar_plexus:
        authority = "감정 권위 (Emotional Authority)"
    elif has_sacral:
        authority = "천골 권위 (Sacral Authority)"
    elif has_spleen:
        authority = "비장 권위 (Splenic Authority)"
    elif has_heart:
        authority = "에고/의지 권위 (Ego Authority)"
    elif has_g:
        authority = "자아 권위 (Self-Projected Authority)"
    elif has_throat:
        authority = "환경 권위 (Mental/Environment Authority)"
    else:
        authority = "달 권위 (Lunar Authority)"

    return hd_type, strategy, authority


def calculate_human_design(year, month, day, hour, minute, city="Seoul", lat=37.5665, lon=126.978):
    """
    휴먼디자인 차트 전체 계산

    Parameters:
        year, month, day, hour, minute: 출생 정보
        city: 출생 도시
        lat, lon: 위도/경도

    Returns:
        dict: 휴먼디자인 차트 데이터
    """

    # 1. Personality (의식) - 출생 시점의 행성 위치
    personality_positions = get_planet_positions(year, month, day, hour, minute)

    # 2. Design (무의식) - 출생 약 88일 전
    design_date = calculate_design_date(year, month, day, hour, minute)
    design_positions = get_planet_positions(
        design_date["year"], design_date["month"], design_date["day"],
        design_date["hour"], design_date["minute"]
    )

    # 3. 게이트 계산
    personality_gates = {}
    design_gates = {}

    for planet, lng in personality_positions.items():
        gate, line = longitude_to_gate(lng)
        personality_gates[planet] = {"gate": gate, "line": line, "name": GATE_NAMES.get(gate, "")}

    for planet, lng in design_positions.items():
        gate, line = longitude_to_gate(lng)
        design_gates[planet] = {"gate": gate, "line": line, "name": GATE_NAMES.get(gate, "")}

    # 4. 활성화된 게이트 수집
    all_active_gates = set()
    for data in personality_gates.values():
        all_active_gates.add(data["gate"])
    for data in design_gates.values():
        all_active_gates.add(data["gate"])

    # 5. 채널 확인
    defined_channels = {}
    for (g1, g2), name in CHANNELS.items():
        if g1 in all_active_gates and g2 in all_active_gates:
            defined_channels[(g1, g2)] = name

    # 6. 정의된 센터 확인
    defined_centers = set()
    for (g1, g2) in defined_channels.keys():
        c1 = GATE_TO_CENTER.get(g1)
        c2 = GATE_TO_CENTER.get(g2)
        if c1:
            defined_centers.add(c1)
        if c2:
            defined_centers.add(c2)

    undefined_centers = {"Head", "Ajna", "Throat", "G", "Heart", "Sacral",
                         "SolarPlexus", "Spleen", "Root"} - defined_centers

    # 7. 타입, 전략, 권위 결정
    hd_type, strategy, authority = determine_type_and_authority(defined_centers, defined_channels)

    # 8. 프로파일 계산 (태양의 라인)
    sun_p_line = personality_gates.get("Sun", {}).get("line", 1)
    sun_d_line = design_gates.get("Sun", {}).get("line", 1)
    profile = f"{sun_p_line}/{sun_d_line}"
    profile_name = PROFILE_MEANINGS.get(profile, profile)

    # 9. 인카네이션 크로스
    sun_p_gate = personality_gates.get("Sun", {}).get("gate", 0)
    earth_p_gate = personality_gates.get("Earth", {}).get("gate", 0)
    sun_d_gate = design_gates.get("Sun", {}).get("gate", 0)
    earth_d_gate = design_gates.get("Earth", {}).get("gate", 0)
    incarnation_cross = f"태양 {sun_p_gate} / 지구 {earth_p_gate} | 태양 {sun_d_gate} / 지구 {earth_d_gate}"

    # 10. Not-Self 테마
    not_self_themes = {
        "매니페스터 (Manifestor)": "분노 (Anger)",
        "제너레이터 (Generator)": "좌절 (Frustration)",
        "매니페스팅 제너레이터 (Manifesting Generator)": "좌절 (Frustration)",
        "프로젝터 (Projector)": "쓴맛 (Bitterness)",
        "리플렉터 (Reflector)": "실망 (Disappointment)",
    }

    signature_themes = {
        "매니페스터 (Manifestor)": "평화 (Peace)",
        "제너레이터 (Generator)": "만족 (Satisfaction)",
        "매니페스팅 제너레이터 (Manifesting Generator)": "만족 (Satisfaction)",
        "프로젝터 (Projector)": "성공 (Success)",
        "리플렉터 (Reflector)": "놀라움 (Surprise)",
    }

    # 정의 유형 (단일 정의, 분리 정의 등) - 간략화
    num_defined = len(defined_centers)
    if num_defined <= 2:
        definition_type = "단일 정의 (Single Definition)"
    elif num_defined <= 4:
        definition_type = "분리 정의 (Split Definition)"
    elif num_defined <= 6:
        definition_type = "삼분 정의 (Triple Split)"
    else:
        definition_type = "사분 정의 (Quadruple Split)"

    if num_defined == 0:
        definition_type = "정의 없음 (No Definition)"

    return {
        "system": "휴먼디자인 (Human Design)",
        "birth_info": {
            "year": year, "month": month, "day": day,
            "hour": hour, "minute": minute, "city": city,
        },
        "design_date": design_date,
        "type": hd_type,
        "strategy": strategy,
        "authority": authority,
        "profile": profile,
        "profile_name": profile_name,
        "definition_type": definition_type,
        "incarnation_cross": incarnation_cross,
        "not_self_theme": not_self_themes.get(hd_type, ""),
        "signature": signature_themes.get(hd_type, ""),
        "defined_centers": list(defined_centers),
        "undefined_centers": list(undefined_centers),
        "defined_channels": {f"{g1}-{g2}": name for (g1, g2), name in defined_channels.items()},
        "personality_gates": personality_gates,
        "design_gates": design_gates,
        "all_active_gates": sorted(list(all_active_gates)),
        "summary": (
            f"타입: {hd_type}\n"
            f"전략: {strategy}\n"
            f"권위: {authority}\n"
            f"프로파일: {profile} ({profile_name})\n"
            f"정의: {definition_type}\n"
            f"인카네이션 크로스: {incarnation_cross}\n"
            f"정의된 센터: {', '.join(sorted(defined_centers)) or '없음'}\n"
            f"열린 센터: {', '.join(sorted(undefined_centers)) or '없음'}\n"
            f"활성 게이트: {len(all_active_gates)}개\n"
            f"정의된 채널: {len(defined_channels)}개"
        )
    }


if __name__ == "__main__":
    result = calculate_human_design(1990, 3, 15, 14, 30)
    print("=== 휴먼디자인 차트 ===")
    print(result["summary"])
    print(f"\n활성 게이트:")
    for g in result["all_active_gates"]:
        print(f"  Gate {g}: {GATE_NAMES.get(g, '')}")
