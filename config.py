"""
운명책 자동 생성기 - 설정 파일
Destiny Book Auto Generator - Configuration
"""

# === 기본 설정 ===
DEFAULT_BIRTH_LOCATION = "Seoul, South Korea"
DEFAULT_LATITUDE = 37.5665
DEFAULT_LONGITUDE = 126.9780
DEFAULT_TIMEZONE = "Asia/Seoul"

# === Claude API 설정 ===
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 8000

# === PDF 설정 ===
PDF_TITLE_FONT = "HYGothic-Medium"
PDF_BODY_FONT = "HYSMyeongJo-Medium"
PDF_LINE_SPACING = 19
PDF_PAGE_WIDTH = 210  # mm (A4)
PDF_PAGE_HEIGHT = 297  # mm (A4)
PDF_MARGIN = 20  # mm

# === 운명책 챕터 구조 ===
CHAPTERS = [
    {"id": 1, "title": "사주명리 (四柱命理)", "system": "saju"},
    {"id": 2, "title": "서양 점성학 (Western Astrology)", "system": "astrology"},
    {"id": 3, "title": "베딕 점성학 (Vedic Astrology)", "system": "vedic"},
    {"id": 4, "title": "헬레니스틱 점성학 (Hellenistic Astrology)", "system": "hellenistic"},
    {"id": 5, "title": "수비학 (Numerology)", "system": "numerology"},
    {"id": 6, "title": "구성학 (Nine Star Ki)", "system": "ninestarki"},
    {"id": 7, "title": "휴먼디자인 (Human Design)", "system": "humandesign"},
    {"id": 8, "title": "주역 (I Ching)", "system": "iching"},
    {"id": 9, "title": "타로 (Tarot)", "system": "tarot"},
    {"id": 10, "title": "카발라 (Kabbalah)", "system": "kabbalah"},
    {"id": 11, "title": "육임 (Da Liu Ren)", "system": "liuren"},
    {"id": 12, "title": "기문둔갑 (Qi Men Dun Jia)", "system": "qimen"},
    {"id": 13, "title": "시스템 통합 해석 (Cross-System Synthesis)", "system": "synthesis"},
    {"id": 14, "title": "운명 로드맵 2026-2030", "system": "roadmap"},
    {"id": 15, "title": "삶의 10대 원칙 (10 Life Principles)", "system": "principles"},
]

# === 주요 도시 좌표 데이터베이스 ===
CITY_DATABASE = {
    # 한국
    "서울": (37.5665, 126.9780, "Asia/Seoul"),
    "seoul": (37.5665, 126.9780, "Asia/Seoul"),
    "부산": (35.1796, 129.0756, "Asia/Seoul"),
    "busan": (35.1796, 129.0756, "Asia/Seoul"),
    "대구": (35.8714, 128.6014, "Asia/Seoul"),
    "daegu": (35.8714, 128.6014, "Asia/Seoul"),
    "인천": (37.4563, 126.7052, "Asia/Seoul"),
    "incheon": (37.4563, 126.7052, "Asia/Seoul"),
    "대전": (36.3504, 127.3845, "Asia/Seoul"),
    "daejeon": (36.3504, 127.3845, "Asia/Seoul"),
    "광주": (35.1595, 126.8526, "Asia/Seoul"),
    "gwangju": (35.1595, 126.8526, "Asia/Seoul"),
    "수원": (37.2636, 127.0286, "Asia/Seoul"),
    "suwon": (37.2636, 127.0286, "Asia/Seoul"),
    "제주": (33.4996, 126.5312, "Asia/Seoul"),
    "jeju": (33.4996, 126.5312, "Asia/Seoul"),
    # 미국
    "new york": (40.7128, -74.0060, "America/New_York"),
    "los angeles": (34.0522, -118.2437, "America/Los_Angeles"),
    "chicago": (41.8781, -87.6298, "America/Chicago"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
    # 일본
    "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
    "도쿄": (35.6762, 139.6503, "Asia/Tokyo"),
    "osaka": (34.6937, 135.5023, "Asia/Tokyo"),
    # 중국
    "beijing": (39.9042, 116.4074, "Asia/Shanghai"),
    "shanghai": (31.2304, 121.4737, "Asia/Shanghai"),
    # 유럽
    "london": (51.5074, -0.1278, "Europe/London"),
    "paris": (48.8566, 2.3522, "Europe/Paris"),
    "berlin": (52.5200, 13.4050, "Europe/Berlin"),
}
