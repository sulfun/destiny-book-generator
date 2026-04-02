"""
Claude API 해석 엔진
Destiny Book Interpretation Engine

차트 데이터를 기반으로 Claude API를 호출하여 15챕터 운명책 텍스트 생성
"""

import json
import os
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from config import CHAPTERS, CLAUDE_MODEL, CLAUDE_MAX_TOKENS


# === 시스템 프롬프트 ===
SYSTEM_PROMPT = """당신은 세계적 수준의 운명학 전문가이자 운명책(Destiny Book) 저자입니다.

전문 분야:
- 사주명리(四柱命理), 서양 점성학(Modern/Placidus), 베딕 점성학(Jyotish), 헬레니스틱 점성학
- 수비학(Numerology), 구성학(Nine Star Ki), 휴먼디자인(Human Design)
- 주역(I Ching), 타로(Tarot), 카발라(Kabbalah)
- 육임(Da Liu Ren), 기문둔갑(Qi Men Dun Jia)

작성 원칙:
1. 각 시스템의 데이터를 정확하게 해석하되, 읽는 사람이 이해할 수 있는 언어로 풀어쓸 것
2. 추상적 미사여구 대신 구체적 분석과 실용적 조언을 포함할 것
3. 시스템 간 교차 검증과 공명하는 패턴을 발견하여 언급할 것
4. 글의 톤: 깊이 있지만 따뜻하고, 전문적이지만 접근 가능한 문체
5. 한국어로 작성하되, 원어 용어를 병기할 것 (예: "태양 물병자리 ♒")
6. 각 챕터는 최소 1500자 이상으로 충실하게 작성할 것
7. 데이터에 없는 내용을 지어내지 말 것 - 제공된 차트 데이터 기반으로만 해석"""


# === 챕터별 프롬프트 템플릿 ===
CHAPTER_PROMPTS = {
    "saju": """## 챕터: 사주명리 (四柱命理)

다음 사주 데이터를 기반으로 깊이 있는 사주 해석을 작성해주세요.

{chart_data}

포함할 내용:
1. 일간(日干) 성격 분석 - 이 사람의 본질적 에너지
2. 사주 구조 해석 - 연주/월주/일주/시주의 의미
3. 오행 균형 분석 - 과잉/부족 원소와 그 영향
4. 십신(十神) 분석 - 대인관계, 재물, 직업적 특성
5. 대운(大運) 흐름 - 인생의 큰 흐름과 주요 전환점
6. 종합 해석 - 이 사주가 가진 핵심 메시지""",

    "astrology": """## 챕터: 서양 점성학 (Western Astrology - Placidus)

다음 출생 차트(네이탈 차트) 데이터를 기반으로 해석해주세요.

{chart_data}

포함할 내용:
1. Big Three 분석 - 태양/달/ASC의 조합이 만드는 성격 초상화
2. 행성 배치 분석 - 각 행성의 별자리와 하우스 위치 의미
3. 원소/모드 균형 - 불/흙/바람/물, 카디널/고정/변통
4. 주요 애스펙트 - 긴장(스퀘어/오포지션)과 조화(트라인/섹스타일)
5. 리트로그레이드 행성의 의미
6. 인생 테마와 성장 방향""",

    "vedic": """## 챕터: 베딕 점성학 (Vedic/Jyotish Astrology)

사이드리얼 좌표계 기반의 베딕 차트 데이터입니다.

{chart_data}

포함할 내용:
1. 라시(Rashi) 분석 - 사이드리얼 태양/달 별자리
2. 낙샤트라(Nakshatra) 분석 - 달의 별자리 분할
3. 서양 차트와의 비교 - 트로피컬 vs 사이드리얼 차이가 주는 추가 통찰
4. 다샤(Dasha) 주기적 관점에서의 인생 흐름
5. 카르마적 의미 - 전생의 과제와 이생의 목적""",

    "hellenistic": """## 챕터: 헬레니스틱 점성학 (Hellenistic Astrology)

고전 점성학 관점에서 다음 차트를 해석해주세요.

{chart_data}

포함할 내용:
1. 종파(Sect) 분석 - 주간/야간 차트의 의미
2. 도미사일/엑절테이션/디트리먼트/폴 - 행성 품위
3. 로트(Lot) - 포르투나, 스피릿, 에로스
4. 바운드 주인(Bound Lord)의 의미
5. 프로펙션(Profection) 기법으로 본 현재 시기
6. 전통적 해석의 지혜가 현대 삶에 주는 조언""",

    "numerology": """## 챕터: 수비학 (Numerology)

다음 수비학 데이터를 기반으로 해석해주세요.

{chart_data}

포함할 내용:
1. 생명수(Life Path Number) 깊이 분석 - 인생의 주제와 목적
2. 생일수(Birthday Number) - 타고난 재능
3. 이름 기반 수(있는 경우) - 표현수, 영혼수, 성격수
4. 개인년수(Personal Year) - 2026년 에너지와 활용법
5. 피너클과 도전수 - 인생 4단계의 흐름
6. 카르마 부채수(있는 경우) - 해소해야 할 과제
7. 5년 전망 (2026-2030)""",

    "ninestarki": """## 챕터: 구성학 (Nine Star Ki)

출생년/월/일 기반으로 구성학(九星気学) 해석을 작성해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 본명성(本命星) - 기본 성격과 에너지
2. 월명성(月命星) - 감정과 내면
3. 경향성(傾斜) - 잠재된 성향
4. 동적/정적 상성
5. 2026년 운세와 방위""",

    "humandesign": """## 챕터: 휴먼디자인 (Human Design)

다음 휴먼디자인 차트를 기반으로 깊이 있는 해석을 작성해주세요.

{chart_data}

포함할 내용:
1. 타입과 전략 - 에너지를 올바르게 사용하는 법
2. 권위(Authority) - 올바른 의사결정 방법
3. 프로파일 - 인생에서의 역할
4. 인카네이션 크로스 - 인생의 목적
5. 정의된 센터 vs 열린 센터 - 일관된 에너지 vs 배울 영역
6. 주요 게이트와 채널 - 타고난 재능과 에너지 흐름
7. Not-Self 테마와 시그니처 - 올바른 길의 신호""",

    "iching": """## 챕터: 주역 (I Ching / 易經)

출생 데이터 기반으로 주역 해석을 제공해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 출생 시점의 본괘(本卦) 해석
2. 효변과 지괘(之卦)
3. 괘의 상(象)과 인생에의 적용
4. 대상전(大象傳)의 지혜
5. 현재 시기에 주는 조언""",

    "tarot": """## 챕터: 타로 (Tarot)

수비학 데이터를 기반으로 타로 해석을 연결해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 생명수 기반 소울 카드 / 성격 카드
2. 출생년 카드
3. 각 카드의 상징과 인생 테마 연결
4. 그림자 카드 - 성장의 과제
5. 현재 시기의 타로 에너지""",

    "kabbalah": """## 챕터: 카발라 (Kabbalah)

출생 데이터와 수비학을 연결한 카발라 해석을 작성해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 생명나무(Tree of Life) 위의 경로
2. 생명수와 세피로트 연결
3. 히브리 문자와 의미
4. 영적 성장의 경로
5. 티쿤(Tikkun) - 영혼의 수정 과제""",

    "liuren": """## 챕터: 육임 (大六壬 / Da Liu Ren)

출생 데이터 기반으로 육임 해석을 제공해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 일간/월장/시간 기반 과식(課式) 설정
2. 사과(四課) 해석
3. 삼전(三傳) 분석
4. 천장(天將) 배치
5. 인생 전반에 대한 육임적 관점""",

    "qimen": """## 챕터: 기문둔갑 (奇門遁甲 / Qi Men Dun Jia)

출생 데이터 기반으로 기문둔갑 해석을 제공해주세요.

기본 데이터:
{chart_data}

포함할 내용:
1. 출생 시점의 국(局) 설정
2. 팔문(八門) 배치와 의미
3. 구성(九星)과 팔신(八神) 해석
4. 기(奇)와 의(儀)의 배치
5. 인생 전략적 관점에서의 기문둔갑 조언""",

    "synthesis": """## 챕터: 시스템 통합 해석 (Cross-System Synthesis)

지금까지의 모든 시스템 데이터를 종합하여 통합 해석을 작성해주세요.

전체 데이터:
{chart_data}

포함할 내용:
1. 공명 패턴 - 여러 시스템에서 반복되는 핵심 테마 (최소 3가지)
2. 상충과 긴장 - 시스템 간 모순되는 지점과 그 의미
3. 종합 인물 초상화 - 모든 시스템을 관통하는 이 사람의 본질
4. 타고난 재능의 교차점
5. 핵심 과제의 교차점
6. 인생의 통합 메시지 - 한 문장으로 표현한다면""",

    "roadmap": """## 챕터: 운명 로드맵 2026-2030

모든 시스템의 데이터를 종합하여 5년간의 운명 로드맵을 작성해주세요.

전체 데이터:
{chart_data}

포함할 내용:
1. 2026년 상세 전망 - 월별 에너지 흐름 (12개월)
2. 2027년 전망 - 주요 전환점
3. 2028년 전망 - 성장 기회
4. 2029년 전망 - 도약 포인트
5. 2030년 전망 - 장기 비전
6. 각 연도별 행동 지침과 주의사항
7. 대운/트랜싯/개인년수를 교차 참조한 타이밍""",

    "principles": """## 챕터: 삶의 10대 원칙 (10 Life Principles)

모든 운명학 시스템을 종합하여 이 사람만을 위한 10가지 삶의 원칙을 작성해주세요.

전체 데이터:
{chart_data}

작성 방식:
- 각 원칙은 한 줄 제목 + 3-5줄 설명
- 어떤 시스템에서 도출된 원칙인지 근거를 밝힐 것
- 추상적 격언이 아닌, 이 사람의 차트에서만 나올 수 있는 구체적 원칙
- 실용적으로 일상에서 적용할 수 있는 행동 지침 포함""",
}


def get_chapter_data(chapter_system, all_data):
    """챕터별로 필요한 데이터 선택"""
    if chapter_system in ["synthesis", "roadmap", "principles"]:
        # 통합 챕터는 모든 데이터
        return json.dumps(all_data, ensure_ascii=False, indent=2, default=str)

    system_map = {
        "saju": "saju",
        "astrology": "astrology",
        "vedic": "astrology",  # 점성학 데이터의 vedic 부분 사용
        "hellenistic": "astrology",
        "numerology": "numerology",
        "ninestarki": "saju",  # 사주 데이터 기반
        "humandesign": "humandesign",
        "iching": "humandesign",  # 휴먼디자인의 게이트(주역) 데이터
        "tarot": "numerology",  # 수비학 기반 타로
        "kabbalah": "numerology",
        "liuren": "saju",
        "qimen": "saju",
    }

    data_key = system_map.get(chapter_system, "")
    if data_key and data_key in all_data:
        return json.dumps(all_data[data_key], ensure_ascii=False, indent=2, default=str)
    return json.dumps(all_data, ensure_ascii=False, indent=2, default=str)


def generate_chapter(client, chapter_id, chapter_title, chapter_system,
                     all_data, client_name="", previous_chapters=None):
    """단일 챕터 생성"""
    prompt_template = CHAPTER_PROMPTS.get(chapter_system, "")
    if not prompt_template:
        return f"[{chapter_title}] - 프롬프트 템플릿 없음"

    chart_data = get_chapter_data(chapter_system, all_data)
    prompt = prompt_template.format(chart_data=chart_data)

    # 이전 챕터 컨텍스트 추가 (통합 챕터용)
    if previous_chapters and chapter_system in ["synthesis", "roadmap", "principles"]:
        context = "\n\n=== 이전 챕터 핵심 요약 ===\n"
        for ch_title, ch_text in previous_chapters.items():
            # 각 챕터의 첫 500자만 컨텍스트로 전달
            context += f"\n[{ch_title}]: {ch_text[:500]}...\n"
        prompt = context + "\n\n" + prompt

    if client_name:
        prompt = f"[의뢰인: {client_name}]\n\n" + prompt

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"[API 오류] {chapter_title}: {str(e)}"


def generate_core_theme(client, all_data, client_name=""):
    """운명책 표지의 핵심 메시지(코어 테마) 생성"""
    prompt = f"""다음 운명학 데이터를 종합하여, 이 사람의 인생을 관통하는 핵심 메시지를 한 문장으로 작성해주세요.

의뢰인: {client_name}

데이터:
{json.dumps(all_data, ensure_ascii=False, indent=2, default=str)[:3000]}

요구사항:
- 15-30자 내외의 한국어 한 문장
- 시적이지만 구체적
- 이 사람의 차트에서만 나올 수 있는 고유한 메시지
- 예시 톤: "물의 지혜로 세상을 비추는 빛", "불꽃이 된 대지의 노래"

핵심 메시지만 출력하세요 (설명 없이):"""

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip().strip('"\'')
    except Exception as e:
        return "운명의 길을 밝히는 빛"


def generate_preface(client, all_data, client_name=""):
    """서문(이름 어원학) 생성"""
    prompt = f"""운명책의 서문을 작성해주세요.

의뢰인: {client_name}

이름의 의미와 어원을 분석하고, 이름이 운명학 차트와 어떻게 공명하는지 해석해주세요.

차트 요약:
- 사주: {all_data.get('saju', {}).get('summary', 'N/A')}
- 점성학: {all_data.get('astrology', {}).get('summary', 'N/A')}
- 수비학: {all_data.get('numerology', {}).get('summary', 'N/A')}
- 휴먼디자인: {all_data.get('humandesign', {}).get('summary', 'N/A')}

포함할 내용:
1. 이름의 한자/의미 분석 (가능한 경우)
2. 이름과 차트의 공명점
3. 이 운명책의 목적과 활용법
4. 의뢰인에게 보내는 따뜻한 인사

약 800자로 작성해주세요."""

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"[서문 생성 오류: {str(e)}]"


def generate_all_chapters(all_data, client_name="", api_key=None):
    """
    전체 운명책 텍스트 생성 (15챕터 + 서문 + 표지 테마)

    Parameters:
        all_data: 모든 차트 데이터 dict
        client_name: 의뢰인 이름
        api_key: Anthropic API 키

    Returns:
        dict: {core_theme, preface, chapters: [{title, text}]}
    """
    if Anthropic is None:
        return {"error": "anthropic 패키지가 설치되어 있지 않습니다. pip install anthropic"}

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY가 설정되지 않았습니다."}

    client = Anthropic(api_key=api_key)

    print("📖 운명책 생성을 시작합니다...")
    print(f"   의뢰인: {client_name}")

    # 1. 코어 테마 생성
    print("\n🎯 코어 테마 생성 중...")
    core_theme = generate_core_theme(client, all_data, client_name)
    print(f"   → {core_theme}")

    # 2. 서문 생성
    print("\n📝 서문 생성 중...")
    preface = generate_preface(client, all_data, client_name)

    # 3. 15챕터 순차 생성
    chapters = []
    previous_chapters = {}

    for ch in CHAPTERS:
        print(f"\n📖 챕터 {ch['id']}: {ch['title']} 생성 중...")
        text = generate_chapter(
            client,
            ch["id"], ch["title"], ch["system"],
            all_data, client_name,
            previous_chapters if ch["id"] >= 13 else None
        )
        chapters.append({"id": ch["id"], "title": ch["title"], "text": text})
        previous_chapters[ch["title"]] = text
        print(f"   → {len(text)}자 생성 완료")

    print("\n✅ 운명책 텍스트 생성 완료!")

    return {
        "core_theme": core_theme,
        "preface": preface,
        "chapters": chapters,
        "client_name": client_name,
    }


def generate_all_chapters_offline(all_data, client_name=""):
    """
    오프라인 모드 (API 없이) - 차트 데이터만 구조화하여 반환
    API 키 없이 테스트할 때 사용
    """
    chapters = []
    for ch in CHAPTERS:
        chart_data = get_chapter_data(ch["system"], all_data)
        chapters.append({
            "id": ch["id"],
            "title": ch["title"],
            "text": f"[{ch['title']}]\n\n차트 데이터:\n{chart_data[:2000]}...\n\n"
                    f"(Claude API로 해석 생성 필요)",
        })

    return {
        "core_theme": "운명의 별이 밝히는 길",
        "preface": f"이 운명책은 {client_name}님을 위해 작성되었습니다.",
        "chapters": chapters,
        "client_name": client_name,
        "mode": "offline",
    }
