# CLAUDE.md — 운명책 (Destiny Book) Generator

## Project Overview

자동화된 운명책(Destiny Book) 생성 시스템. 고객의 출생 데이터를 기반으로 동서양 12개 운명학 시스템을 교차 분석하여 개인화된 운명책 PDF를 생성하고, 이메일로 발송한다.

**핵심 파이프라인:** Notion 주문 → 차트 계산 → Claude API 해석 (15챕터) → PDF 생성 → 이메일 발송 → Notion 상태 업데이트

## Architecture

```
app.py (Streamlit UI) → Notion DB (주문 접수)
batch_generator.py (배치 CLI) → Notion DB (주문 조회)
  ↓
main.py:collect_all_charts() → scrapers/{saju,astrology,numerology,human_design}.py
  ↓
interpreter.py:generate_all_chapters() → Claude API (15챕터 생성)
  ↓
pdf_generator.py:generate_pdf() → PDF (A4, 한글 폰트, gold/navy 테마)
  ↓
batch_generator.py:send_destiny_book_email() → Gmail SMTP
```

## Key Files

| File | Purpose |
|------|---------|
| `config.py` | CHAPTERS (15개), CITY_DATABASE, Claude/PDF 설정 |
| `main.py` | `collect_all_charts()`, `run_pipeline()` — 전체 오케스트레이션 |
| `interpreter.py` | `generate_all_chapters()` — Claude API로 15챕터 해석 생성 |
| `pdf_generator.py` | `generate_pdf()` — ReportLab 기반 PDF 생성 |
| `batch_generator.py` | Notion 연동 배치 처리 CLI |
| `app.py` | Streamlit 고객 신청폼 + 관리자 대시보드 |
| `scrapers/saju.py` | 사주명리 엔진 v2.0 (korean-lunar-calendar 기반) |
| `scrapers/astrology.py` | 서양 점성학 (Kerykeion 기반) |
| `scrapers/numerology.py` | 수비학 (피타고라스 체계) |
| `scrapers/human_design.py` | 휴먼디자인 |

## Commands

```bash
# 단일 실행 (대화형)
python main.py

# 빠른 실행
python main.py --quick 1990 3 15 14 30 서울 여 홍길동 "Hong Gildong"

# 차트만 계산 (해석/PDF 생략)
python main.py --charts-only --quick 1990 3 15 14 30 서울 여 홍길동 ""

# 배치: 선정완료 주문 전부 처리
python batch_generator.py

# 배치: 특정 이름만
python batch_generator.py --name 홍길동

# 배치: 드라이런 (대상만 확인)
python batch_generator.py --dry-run

# 배치: 입금완료 상태 처리
python batch_generator.py --status 입금완료

# 배치: 이메일 없이
python batch_generator.py --no-email

# Streamlit 앱
streamlit run app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API 키 |
| `NOTION_TOKEN` | Yes | Notion API 토큰 |
| `GMAIL_APP_PASSWORD` | For email | Gmail 앱 비밀번호 |
| `GMAIL_SENDER` | Optional | 발신자 (기본: societyalef@gmail.com) |

## Notion DB Schema

**DB ID:** `231274d036864a249614327bb9fdeed9`

**상태 플로우:**
접수완료 → 선정완료 → (입금안내 발송) → 입금완료 → 차트계산중 → 해석생성중 → PDF생성중 → 완료 → 발송완료

**주요 속성:** 주문번호(title), 이름(한글), 이름(영문), 이메일, 전화번호, 성별, 생년/생월/생일/생시/생분, 출생도시, 상태, 메모, 차트데이터

## 15 Chapter Systems

1. 사주명리 (Four Pillars)
2. 서양 점성학 (Western Astrology)
3. 베딕 점성학 (Vedic)
4. 헬레니스틱 점성학 (Hellenistic)
5. 수비학 (Numerology)
6. 구성기학 (Nine Star Ki)
7. 휴먼디자인 (Human Design)
8. 주역 (I Ching)
9. 타로 (Tarot)
10. 카발라 (Kabbalah)
11. 육임 (Liuren)
12. 기문둔갑 (Qimen Dunjia)
13. 통합 해석 (Synthesis)
14. 로드맵 (Roadmap)
15. 운명 원칙 (Principles)

## Dependencies

- `kerykeion>=5.0.0` — 점성학 차트 계산 (Swiss Ephemeris)
- `korean-lunar-calendar>=0.3.1` — 만세력/간지 계산 (정확한 절기 기반)
- `anthropic>=0.80.0` — Claude API
- `reportlab>=4.0` — PDF 생성
- `notion-client>=2.0.0` — Notion API
- `streamlit>=1.30.0` — Web UI

## Key Design Decisions

- **사주 연주/월주/일주:** `korean-lunar-calendar`의 `getGapJaString()` 사용 (수동 절기 계산 대신)
- **시주:** 오호접기법(五虎遁起法) 직접 구현
- **점성학 ASC:** Kerykeion v5+ `first_house` attribute 사용 (`houses_list` deprecated)
- **베딕 차트:** 라히리 아야남사(24.11°) 사이드리얼 오프셋 적용
- **PDF 폰트:** HYGothic-Medium (제목), HYSMyeongJo-Medium (본문) — CID 한글 폰트
- **배치 처리:** Notion 상태 기반 필터링, 오류 시 자동 상태 롤백
