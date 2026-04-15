#!/usr/bin/env python3
"""
build_briefing.py — ICBM2 대시보드 브리핑 데이터 수집기

데이터 소스:
  - 날씨: wttr.in/Seoul API (JSON)
  - 주식: 네이버 (KOSPI/KOSDAQ), Yahoo Finance (S&P500/NASDAQ)
  - 뉴스: Agent.News API (https://agent.news/api/v1/feed)
  - 자동화 상태: ~/.hermes/cron/jobs.json, ~/.hermes/memory/shiporslop.md
  - 블로그 히스토리: ~/.hermes/data/blog_history.json

사용법:
  python3 build_briefing.py              # JSON만 생성
  python3 build_briefing.py --inject     # JSON 생성 + dashboard/index.html 업데이트
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: 'requests' 모듈이 필요합니다. pip install requests")
    sys.exit(1)

# ─── 경로 설정 ───────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(REPO_DIR, "data")
DASHBOARD_DIR = os.path.join(REPO_DIR, "dashboard")
TEMPLATE_FILE = os.path.join(DASHBOARD_DIR, "index.html.template")
OUTPUT_HTML = os.path.join(DASHBOARD_DIR, "index.html")
OUTPUT_JSON = os.path.join(DATA_DIR, "briefing_latest.json")

HERMES_DIR = os.path.expanduser("~/.hermes")
CRON_JOBS_FILE = os.path.join(HERMES_DIR, "cron", "jobs.json")
SOS_STATE_FILE = os.path.join(HERMES_DIR, "memory", "shiporslop.md")
BLOG_HISTORY_FILE = os.path.join(HERMES_DIR, "data", "blog_history.json")
BOTMADANG_SECRET = os.path.join(HERMES_DIR, "secrets", "skillsmp")

KST = timezone(timedelta(hours=9))
TIMEOUT = 10
API_DELAY = 0.5  # API 호출 간 딜레이 (초)

os.makedirs(DATA_DIR, exist_ok=True)


# ─── 유틸리티 ───────────────────────────────────────────────
def safe_get(url, timeout=TIMEOUT, headers=None):
    """HTTP GET 요청, 실패 시 None 반환."""
    try:
        resp = requests.get(url, timeout=timeout, headers=headers or {})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [WARN] API 요청 실패: {url} → {e}")
        return None


def safe_read_json(filepath):
    """JSON 파일 읽기, 실패 시 None 반환."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [WARN] 파일 읽기 실패: {filepath} → {e}")
        return None


def safe_read_text(filepath):
    """텍스트 파일 읽기, 실패 시 None 반환."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"  [WARN] 파일 읽기 실패: {filepath} → {e}")
        return None


def now_kst() -> datetime:
    return datetime.now(KST)


def is_weekend() -> bool:
    """오늘이 주말인지 확인."""
    return now_kst().weekday() >= 5


def last_friday() -> str:
    """마지막 금요일 날짜 문자열 (YYYY-MM-DD)."""
    today = now_kst().date()
    days_back = (today.weekday() - 4) % 7
    if days_back == 0 and is_weekend():
        days_back = 2  # 토요일/일요일이면 이번 주 금요일
    elif days_back == 0:
        days_back = 7  # 평일이면 지난 주 금요일 (주말 전용)
    # 주말일 때만 사용하므로 단순 계산
    d = today
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")


# ─── 날씨 데이터 ─────────────────────────────────────────────
def fetch_weather():
    """wttr.in/Seoul에서 날씨 정보 수집."""
    print("🌤️  날씨 데이터 수집 중...")
    data = safe_get("https://wttr.in/Seoul?format=j1")
    if not data:
        return None

    try:
        current = data["current_condition"][0]
        today_weather = data["weather"][0]

        # 한국어 날씨 코드 매핑
        weather_code_map = {
            "113": "맑음", "116": "부분 흐림", "119": "흐림",
            "122": "흐림", "143": "안개", "176": "이슬비",
            "200": "뇌우", "227": "눈날림", "230": "눈",
            "248": "안개", "260": "짙은 안개", "263": "이슬비",
            "266": "이슬비", "281": "어는 이슬비", "284": "어는 이슬비",
            "293": "약한 이슬비", "296": "이슬비", "299": "이슬비",
            "302": "비", "305": "비", "308": "폭우",
            "311": "어는 비", "314": "어는 비", "317": "어는 비/눈",
            "320": "눈/비", "323": "약한 눈", "326": "눈",
            "329": "눈", "332": "폭설", "335": "폭설",
            "338": "폭설", "350": "진눈깨비", "353": "소나기",
            "356": "소나기", "359": "폭우", "362": "약한 진눈깨비",
            "365": "진눈깨비", "368": "약한 눈", "371": "보통 눈",
            "374": "약한 진눈깨비", "377": "어는 비",
            "386": "뇌우", "389": "뇌우", "392": "뇌우/눈", "395": "뇌우/폭설",
        }
        code = current.get("weatherCode", "113")
        desc_en = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        desc_ko = weather_code_map.get(code, desc_en)

        return {
            "location": "서울",
            "temp_c": int(current.get("temp_C", 0)),
            "feels_like_c": int(current.get("FeelsLikeC", 0)),
            "humidity": int(current.get("humidity", 0)),
            "wind_speed_kmph": int(current.get("windspeedKmph", 0)),
            "wind_dir": current.get("winddir16Point", ""),
            "weather_code": code,
            "weather_desc_en": desc_en,
            "weather_desc_ko": desc_ko,
            "uv_index": int(current.get("uvIndex", 0)),
            "visibility_km": int(current.get("visibility", 10)),
            "pressure_mb": int(current.get("pressure", 0)),
            "precip_mm": float(current.get("precipMM", 0)),
            "cloudcover": int(current.get("cloudcover", 0)),
            "sunrise": today_weather.get("astronomy", [{}])[0].get("sunrise", ""),
            "sunset": today_weather.get("astronomy", [{}])[0].get("sunset", ""),
            "max_temp_c": int(today_weather.get("maxtempC", 0)),
            "min_temp_c": int(today_weather.get("mintempC", 0)),
            "observed_at": current.get("localObsDateTime", ""),
        }
    except (KeyError, IndexError, ValueError, TypeError) as e:
        print(f"  [WARN] 날씨 데이터 파싱 오류: {e}")
        return None


# ─── 주식 데이터 ─────────────────────────────────────────────
def fetch_korean_stocks():
    """네이버 API에서 KOSPI/KOSDAQ 데이터 수집."""
    print("📈 한국 주식 데이터 수집 중...")
    result = {}

    for idx_name in ["KOSPI", "KOSDAQ"]:
        url = f"https://m.stock.naver.com/api/index/{idx_name}/basic"
        data = safe_get(url)
        if data:
            try:
                change_info = data.get("compareToPreviousPrice", {})
                result[idx_name] = {
                    "name": data.get("stockName", idx_name),
                    "close_price": data.get("closePrice", "0").replace(",", ""),
                    "change_value": data.get("compareToPreviousClosePrice", "0").replace(",", ""),
                    "change_code": change_info.get("code", "3"),
                    "change_text_ko": change_info.get("text", "보합"),
                    "fluctuation_ratio": data.get("fluctuationsRatio", "0"),
                    "market_status": data.get("marketStatus", "UNKNOWN"),
                    "local_traded_at": data.get("localTradedAt", ""),
                }
            except (KeyError, TypeError) as e:
                print(f"  [WARN] {idx_name} 파싱 오류: {e}")
                result[idx_name] = None
        else:
            result[idx_name] = None

        time.sleep(API_DELAY)

    return result


def fetch_us_stocks():
    """Yahoo Finance에서 S&P500, NASDAQ 데이터 수집."""
    print("🇺🇸 미국 주식 데이터 수집 중...")
    result = {}

    tickers = {
        "^GSPC": "S&P500",
        "^IXIC": "NASDAQ",
    }

    for ticker, name in tickers.items():
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?range=1d&interval=1d"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        data = safe_get(url, headers=headers)
        if data and "chart" in data:
            try:
                meta = data["chart"].get("result", [{}])[0].get("meta", {})
                prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0)
                current_price = meta.get("regularMarketPrice", 0)
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                if change > 0:
                    change_text = "상승"
                elif change < 0:
                    change_text = "하락"
                else:
                    change_text = "보합"

                result[name] = {
                    "name": name,
                    "ticker": ticker,
                    "price": round(current_price, 2),
                    "prev_close": round(prev_close, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "change_text_ko": change_text,
                    "market_status": meta.get("marketState", "UNKNOWN"),
                    "exchange": meta.get("exchangeName", ""),
                    "currency": meta.get("currency", "USD"),
                }
            except (KeyError, IndexError, TypeError) as e:
                print(f"  [WARN] {name} 파싱 오류: {e}")
                result[name] = None
        else:
            result[name] = None

        time.sleep(API_DELAY)

    return result


def fetch_stocks():
    """한국 + 미국 주식 데이터 통합 수집."""
    korean = fetch_korean_stocks()
    us = fetch_us_stocks()

    # 주말이면 시장 상태 메시지 추가
    weekend_note = None
    if is_weekend():
        weekend_note = f"주말입니다. 최근 거래일({last_friday()}) 기준 데이터입니다."

    return {
        "korean": korean,
        "us": us,
        "weekend_note": weekend_note,
        "is_weekend": is_weekend(),
        "fetched_at": now_kst().isoformat(),
    }


# ─── 뉴스 데이터 ─────────────────────────────────────────────
def fetch_news():
    """Agent.News API에서 최신 뉴스 수집."""
    print("📰 Agent.News 뉴스 수집 중...")
    data = safe_get("https://agent.news/api/v1/feed")
    if not data or "items" not in data:
        return {"items": [], "total": 0, "fetched_at": now_kst().isoformat()}

    items = []
    for item in data["items"][:20]:  # 최대 20개
        pub_date = item.get("published_at", item.get("created_at", ""))
        # ISO 날짜를 읽기 쉽게 변환
        pub_display = ""
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                pub_display = dt.astimezone(KST).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pub_display = pub_date[:16] if len(pub_date) >= 16 else pub_date

        items.append({
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "domain": item.get("domain", ""),
            "category": item.get("category", ""),
            "type": item.get("type", ""),
            "points": item.get("points", 0),
            "vote_count": item.get("vote_count", 0),
            "comment_count": item.get("comment_count", 0),
            "published_at": pub_display,
            "context_preview": (item.get("context") or "")[:200],
        })

    return {
        "items": items,
        "total": len(data["items"]),
        "fetched_at": now_kst().isoformat(),
    }


# ─── 크론잡 통계 ─────────────────────────────────────────────
def fetch_cron_stats():
    """~/.hermes/cron/jobs.json에서 크론잡 통계 수집."""
    print("⏰ 크론잡 통계 수집 중...")
    jobs_data = safe_read_json(CRON_JOBS_FILE)
    if not jobs_data or "jobs" not in jobs_data:
        return {
            "total_jobs": 0,
            "enabled_jobs": 0,
            "disabled_jobs": 0,
            "success_rate": 0,
            "last_errors": [],
            "jobs": [],
        }

    jobs = jobs_data["jobs"]
    total = len(jobs)
    enabled = sum(1 for j in jobs if j.get("enabled", False))
    disabled = total - enabled
    succeeded = sum(1 for j in jobs if j.get("last_status") == "ok")
    success_rate = round(succeeded / total * 100, 1) if total > 0 else 0

    # 실패한 잡 목록
    last_errors = []
    for j in jobs:
        if j.get("last_status") != "ok" and j.get("last_error"):
            last_errors.append({
                "name": j.get("name", ""),
                "last_error": j.get("last_error", ""),
                "last_run_at": j.get("last_run_at", ""),
            })

    # 각 잡 요약
    job_summaries = []
    for j in jobs:
        job_summaries.append({
            "name": j.get("name", ""),
            "enabled": j.get("enabled", False),
            "state": j.get("state", ""),
            "schedule": j.get("schedule_display", j.get("schedule", {}).get("display", "")),
            "completed": j.get("repeat", {}).get("completed", 0),
            "last_status": j.get("last_status", ""),
            "last_run_at": j.get("last_run_at", ""),
            "skill": j.get("skill", ""),
        })

    return {
        "total_jobs": total,
        "enabled_jobs": enabled,
        "disabled_jobs": disabled,
        "success_rate": success_rate,
        "last_errors": last_errors,
        "jobs": job_summaries,
    }


# ─── Ship or Slop 통계 ───────────────────────────────────────
def fetch_sos_stats():
    """~/.hermes/memory/shiporslop.md에서 SoS 통계 수집."""
    print("🚢 Ship or Slop 통계 수집 중...")
    content = safe_read_text(SOS_STATE_FILE)
    if not content:
        return {"framework_index": 0, "frameworks": [], "total_submissions": 0, "latest_activity": ""}

    # 프레임워크별 성과 파싱
    frameworks = []
    fw_pattern = re.compile(r'- (.+?)\((\d+)\): (.+)')
    total_ships = 0
    for match in fw_pattern.finditer(content):
        name = match.group(1)
        idx = int(match.group(2))
        status = match.group(3)
        ship_pct = 0
        ship_match = re.search(r'Ship률 (\d+)%', status)
        if ship_match:
            ship_pct = int(ship_match.group(1))
        frameworks.append({
            "name": name,
            "index": idx,
            "status": status,
            "ship_rate": ship_pct,
        })

    # 프레임워크 인덱스
    idx_match = re.search(r'\*\*프레임워크 인덱스:\*\*\s*(\d+)', content)
    framework_index = int(idx_match.group(1)) if idx_match else 0

    # 최근 활동 날짜 파싱 (마지막 ## 날짜 항목)
    date_entries = re.findall(r'## (\d{4}-\d{2}-\d{2})', content)
    latest_activity = date_entries[-1] if date_entries else ""

    # 제출 횟수 카운트 (✅ 마크 수)
    total_submissions = content.count("✅")

    return {
        "framework_index": framework_index,
        "frameworks": frameworks,
        "total_submissions": total_submissions,
        "latest_activity": latest_activity,
    }


# ─── 봇마당 통계 ─────────────────────────────────────────────
def fetch_botmadang_stats():
    """봇마당 API에서 게시글 통계 수집."""
    print("🤖 봇마당 통계 수집 중...")
    api_key = os.environ.get("BOTMADANG_API_KEY") or os.environ.get("SKILLSMP_API_KEY")
    if not api_key:
        secret_file = BOTMADANG_SECRET
        if os.path.exists(secret_file):
            try:
                with open(secret_file, "r") as f:
                    api_key = f.read().strip().split("\n")[0]
            except Exception:
                pass

    if not api_key:
        print("  [WARN] 봇마당 API 키 없음")
        return {"total_posts": 0, "recent_posts": [], "error": "API 키 없음"}

    # 봇마당 API 호출 (botmadang.org)
    url = "https://botmadang.org/api/v1/posts"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = safe_get(url, headers=headers)
    if not data:
        return {"total_posts": 0, "recent_posts": [], "error": "API 요청 실패"}

    try:
        posts = data if isinstance(data, list) else data.get("posts", data.get("data", []))
        return {
            "total_posts": len(posts) if isinstance(posts, list) else 0,
            "recent_posts": [
                {
                    "title": p.get("title", ""),
                    "url": p.get("url", ""),
                    "created_at": p.get("created_at", ""),
                }
                for p in (posts[:5] if isinstance(posts, list) else [])
            ],
        }
    except (KeyError, TypeError):
        return {"total_posts": 0, "recent_posts": [], "error": "파싱 오류"}


# ─── 블로그 히스토리 ─────────────────────────────────────────
def fetch_blog_stats():
    """~/.hermes/data/blog_history.json에서 블로그 통계 수집."""
    print("📝 블로그 통계 수집 중...")
    data = safe_read_json(BLOG_HISTORY_FILE)
    if not data or not isinstance(data, list):
        return {"total_posts": 0, "recent_posts": [], "by_grade": {}}

    # 등급별 카운트
    by_grade = {}
    for post in data:
        grade = post.get("grade", "N/A")
        by_grade[grade] = by_grade.get(grade, 0) + 1

    recent = [
        {
            "title": p.get("title", ""),
            "url": p.get("url", ""),
            "category": p.get("category", ""),
            "grade": p.get("grade", ""),
            "published_at": p.get("published_at", ""),
        }
        for p in data[-5:]
    ]

    return {
        "total_posts": len(data),
        "recent_posts": recent,
        "by_grade": by_grade,
    }


# ─── 자동화 종합 통계 ────────────────────────────────────────
def fetch_automation_stats():
    """모든 자동화 관련 데이터 종합."""
    cron = fetch_cron_stats()
    sos = fetch_sos_stats()
    botmadang = fetch_botmadang_stats()
    blog = fetch_blog_stats()

    return {
        "cron": cron,
        "sos": sos,
        "botmadang": botmadang,
        "blog": blog,
        "fetched_at": now_kst().isoformat(),
    }


# ─── 브리핑 데이터 통합 ──────────────────────────────────────
def build_briefing():
    """모든 소스에서 브리핑 데이터를 수집하여 통합."""
    print("=" * 50)
    print(f"ICBM2 브리핑 데이터 빌드 — {now_kst().strftime('%Y-%m-%d %H:%M:%S')} KST")
    print("=" * 50)

    briefing = {
        "generated_at": now_kst().isoformat(),
        "generated_at_display": now_kst().strftime("%Y-%m-%d %H:%M KST"),
        "day_of_week": ["월", "화", "수", "목", "금", "토", "일"][now_kst().weekday()],
        "is_weekend": is_weekend(),
        "weather": None,
        "stocks": None,
        "news": None,
        "automation": None,
    }

    # 1. 날씨
    briefing["weather"] = fetch_weather()
    time.sleep(API_DELAY)

    # 2. 주식
    briefing["stocks"] = fetch_stocks()
    time.sleep(API_DELAY)

    # 3. 뉴스
    briefing["news"] = fetch_news()
    time.sleep(API_DELAY)

    # 4. 자동화 통계
    briefing["automation"] = fetch_automation_stats()

    # JSON 파일 저장
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON 저장 완료: {OUTPUT_JSON}")

    return briefing


# ─── HTML 인젝션 ─────────────────────────────────────────────
def inject_into_dashboard(briefing):
    """dashboard/index.html.template에서 __BRIEFING_DATA__와 __BUILD_TIME__ 치환."""
    if not os.path.exists(TEMPLATE_FILE):
        # template이 없으면 dashboard/index.html을 직접 대상으로
        print(f"[WARN] 템플릿 파일 없음: {TEMPLATE_FILE}")
        if os.path.exists(OUTPUT_HTML):
            target = OUTPUT_HTML
            print(f"  대상 파일 사용: {target}")
        else:
            print("[ERROR] 대상 HTML 파일도 없습니다.")
            return False
    else:
        target = TEMPLATE_FILE

    print(f"📄 HTML 인젝션 중... (소스: {target})")
    try:
        with open(target, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"[ERROR] HTML 파일 읽기 실패: {e}")
        return False

    # JSON을 HTML에 안전하게 삽입 (JSON.stringify 스타일)
    briefing_json = json.dumps(briefing, ensure_ascii=False, separators=(",", ":"))

    # HTML 이스케이프: </script> 방지
    briefing_json = briefing_json.replace("</", r"<\/")

    # 플레이스홀더 치환
    if "__BRIEFING_DATA__" in html:
        html = html.replace("__BRIEFING_DATA__", briefing_json)
        print(f"  __BRIEFING_DATA__ 치환 완료 ({len(briefing_json):,} bytes)")
    else:
        print("  [WARN] __BRIEFING_DATA__ 플레이스홀더를 찾을 수 없습니다")

    build_time = now_kst().strftime("%Y-%m-%d %H:%M KST")
    if "__BUILD_TIME__" in html:
        html = html.replace("__BUILD_TIME__", build_time)
        print(f"  __BUILD_TIME__ 치환 완료: {build_time}")
    else:
        print("  [WARN] __BUILD_TIME__ 플레이스홀더를 찾을 수 없습니다")

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"💾 HTML 저장 완료: {OUTPUT_HTML}")
    return True


# ─── 메인 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ICBM2 브리핑 데이터 빌더")
    parser.add_argument("--inject", action="store_true", help="dashboard/index.html에 데이터 주입")
    parser.add_argument("--output", type=str, default=None, help="JSON 출력 경로 (기본값: 자동)")
    parser.add_argument("--quiet", action="store_true", help="출력 최소화")
    args = parser.parse_args()

    global OUTPUT_JSON, OUTPUT_HTML, TEMPLATE_FILE
    if args.output:
        OUTPUT_JSON = args.output

    if args.quiet:
        # stdout을 억제하지 않고 플래그만 설정 (향후 사용)
        pass

    briefing = build_briefing()

    if args.inject:
        print()
        success = inject_into_dashboard(briefing)
        if not success:
            sys.exit(1)

    print("\n✅ 브리핑 데이터 빌드 완료!")
    summary = {
        "weather": briefing["weather"] is not None,
        "stocks_korean": briefing["stocks"]["korean"].get("KOSPI") is not None if briefing["stocks"] else False,
        "stocks_us": briefing["stocks"]["us"].get("S&P500") is not None if briefing["stocks"] else False,
        "news": briefing["news"]["total"] if briefing["news"] else 0,
        "cron_jobs": briefing["automation"]["cron"]["total_jobs"] if briefing["automation"] else 0,
        "sos_submissions": briefing["automation"]["sos"]["total_submissions"] if briefing["automation"] else 0,
    }
    for k, v in summary.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {v}")

    return briefing


if __name__ == "__main__":
    main()
