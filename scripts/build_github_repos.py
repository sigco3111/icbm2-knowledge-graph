#!/usr/bin/env python3
"""Build GitHub repos dashboard page with live data from GitHub API."""
import json
import subprocess
import os
import sys
import base64
import time
from datetime import datetime, timedelta

REPO_DIR = "/Users/hjshin/icbm2-knowledge-graph"
TEMPLATE = os.path.join(REPO_DIR, "dashboard", "github-repos-template.html")
OUTPUT = os.path.join(REPO_DIR, "dashboard", "github-repos.html")
DATA_DIR = os.path.join(REPO_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "github_repos_cache.json")
NEW_REPOS_FILE = os.path.join(DATA_DIR, "github_repos_new.json")

os.makedirs(DATA_DIR, exist_ok=True)

# Category mapping
CATEGORY_MAP = {}
cat_items = {
    "🔧 ICBM/에이전트": ["hermes_bot", "icbm2-workspace", "icbm-workspace", "icbm2-knowledge-graph"],
    "📖 재무": ["bookk"],
    "🛠 개발 도구": ["prompt-advisor", "ccusage-json", "yt-download"],
    "📊 데이터 시각화": [
        "github-board", "github-board2", "cli-board", "hitel-board", "sys8-board",
        "win11-board", "winxp-board", "ubuntu-board", "mac-board", "steam-board",
        "space-board", "commodity-dashboard", "air-management", "world-bank-board",
        "satellite-board", "co2-board", "ip-board", "youtube-board", "token-meter",
        "tech-stack", "tech-toolkit-hub", "code-map", "json-flow", "ai-flowchart",
        "codeviz-ai", "insight-pick", "fire-tribe-base"
    ],
    "🎮 게임": [
        "2048", "candy-crush-saga", "gostop", "one-card-game", "poker-king", "liquid-sort",
        "number-connect", "number-link-merge", "wordle", "ladder-game", "watermelon",
        "sand-blast", "castle-breaker", "core-breaker", "wobbly-tower", "diablock",
        "kingdoms3-tradewar", "age-of-exploration-lite", "xcom-lite", "democracy4-lite",
        "block-simCity", "gamedev-lite", "rpg-adv-at", "rpg-adv-bt", "rpg-script-editor",
        "terrarium", "world-box", "mount-and-blade", "department-tycoon", "pixel-farm-story",
        "dungeon-story", "real-estate-king", "capitalism-web", "grand-prix", "convenience24",
        "juice-tycoon", "3d-physics-lab", "predator", "iron-dome", "lightning-strike",
        "earthquake", "stonks-9800", "ai-buy-sell", "decision-genie", "core-video-editor",
        "pixedit", "3d-fractal", "svg-converter", "core-image-converter", "text-sync-check",
        "make-app-wiz", "google-script-wizard", "speech-recognition", "appscript_board",
        "core-markdown-editor", "relationship-visualizer"
    ],
    "🌐 웹 프로젝트": ["ubobtest", "KakaoSplit", "keyword_fighter", "DevCanvas", "pages", "blog",
                        "astrocartography", "terrain", "world-data-map"]
}
for cat, names in cat_items.items():
    for name in names:
        CATEGORY_MAP[name] = cat

# Keyword-based auto category recommendation
KEYWORD_MAP = {
    "🎮 게임": ["game", "게임"],
    "📊 데이터 시각화": ["board", "dashboard", "chart", "시각화", "visualization"],
    "🛠 개발 도구": ["tool", "editor", "converter", "도구"],
    "🔧 ICBM/에이전트": ["icbm", "hermes", "agent", "에이전트"],
    "📖 재무": ["bookk", "finance", "accounting", "재무"],
}

def suggest_category(repo_name, repo_desc=""):
    """Suggest category based on keywords for uncategorized repos."""
    text = (repo_name + " " + (repo_desc or "")).lower()
    for cat, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                return cat
    return "📋 기타"

def run_gh_json(args):
    """Run gh CLI command and return parsed JSON."""
    result = subprocess.run(
        ['gh', 'api'] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def run_gh_raw(args):
    """Run gh CLI command and return raw stdout."""
    result = subprocess.run(
        ['gh', 'api'] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

# ─── Step 1: Fetch ALL repos via REST API ───
print("📦 Fetching repos from GitHub API...")
repos_raw = []
page = 1
while True:
    batch = run_gh_json([f'user/repos?per_page=100&sort=updated&page={page}'])
    if not batch or not isinstance(batch, list) or len(batch) == 0:
        break
    repos_raw.extend(batch)
    print(f"  Page {page}: {len(batch)} repos")
    page += 1
    if len(batch) < 100:
        break

print(f"Total repos fetched: {len(repos_raw)}")

# ─── Step 2: Normalize repo data ───
repos = []
for r in repos_raw:
    repo = {
        'name': r.get('name'),
        'description': r.get('description'),
        'url': r.get('html_url', ''),
        'homepageUrl': r.get('homepage', ''),
        'stargazerCount': r.get('stargazers_count', 0),
        'forkCount': r.get('forks_count', 0),
        'isPrivate': r.get('private', False),
        'createdAt': r.get('created_at'),
        'updatedAt': r.get('updated_at'),
        'pushed_at': r.get('pushed_at'),
        'open_issues_count': r.get('open_issues_count', 0),
        'has_pages': r.get('has_pages', False),
        'size': r.get('size', 0),
        'visibility': r.get('visibility', 'private'),
        'default_branch': r.get('default_branch', 'main'),
        'topics': r.get('topics', []),
        'license_spdx_id': r.get('license', {}).get('spdx_id') if r.get('license') else None,
        'language': r.get('language'),  # REST API returns string directly
    }
    repos.append(repo)

# ─── Step 3: Detect stale repos (pushed_at > 6 months ago) ───
six_months_ago = datetime.now() - timedelta(days=180)
for repo in repos:
    pushed = repo.get('pushed_at')
    if pushed:
        try:
            pushed_date = datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ")
            repo['is_stale'] = pushed_date < six_months_ago
        except ValueError:
            repo['is_stale'] = False
    else:
        repo['is_stale'] = True

# ─── Step 4: Fetch recent commit + README for each repo ───
# Support --fast flag to skip commit/README fetching (use cached data)
FAST_MODE = '--fast' in sys.argv

if FAST_MODE and os.path.exists(CACHE_FILE):
    print("⚡ Fast mode: loading commits/READMEs from cache...")
    try:
        with open(CACHE_FILE, 'r') as f:
            cached_repos = {r['name']: r for r in json.load(f)}
        for repo in repos:
            cached = cached_repos.get(repo['name'])
            if cached:
                repo['last_commit_sha'] = cached.get('last_commit_sha')
                repo['last_commit_msg'] = cached.get('last_commit_msg')
                repo['last_commit_date'] = cached.get('last_commit_date')
                repo['readme_preview'] = cached.get('readme_preview')
            else:
                repo['last_commit_sha'] = None
                repo['last_commit_msg'] = None
                repo['last_commit_date'] = None
                repo['readme_preview'] = None
        print(f"  Loaded from cache ({len(cached_repos)} repos)")
    except Exception as e:
        print(f"  Cache error: {e}, falling back to full fetch")
        FAST_MODE = False

if not FAST_MODE:
    print("🔄 Fetching commits and READMEs...")
    for i, repo in enumerate(repos):
        name = repo['name']
        full_name = f"repos/sigco3111/{name}"

        # Fetch latest commit
        commit_data = run_gh_json([f"{full_name}/commits?per_page=1"])
        if commit_data and isinstance(commit_data, list) and len(commit_data) > 0:
            c = commit_data[0]
            repo['last_commit_sha'] = c['sha'][:7]
            repo['last_commit_msg'] = c['commit']['message'].split('\n')[0]
            repo['last_commit_date'] = c['commit']['committer']['date']
        else:
            repo['last_commit_sha'] = None
            repo['last_commit_msg'] = None
            repo['last_commit_date'] = None

        # Fetch README
        readme_raw = run_gh_raw([f"{full_name}/readme", '--jq', '.content'])
        if readme_raw:
            try:
                readme_text = base64.b64decode(readme_raw).decode('utf-8', errors='replace')
                repo['readme_preview'] = readme_text[:500]
            except Exception:
                repo['readme_preview'] = None
        else:
            repo['readme_preview'] = None

        if (i + 1) % 10 == 0 or i == len(repos) - 1:
            print(f"  Progress: {i+1}/{len(repos)} repos")

        time.sleep(0.5)  # Rate limit safety

    print("✅ Commits and READMEs fetched")

# ─── Step 5: Load previous cache and detect new repos ───
prev_names = set()
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            prev_cache = json.load(f)
            prev_names = {r['name'] for r in prev_cache}
        print(f"📋 Previous cache: {len(prev_names)} repos")
    except Exception as e:
        print(f"  WARNING: Could not load cache: {e}")

new_repos = []
for repo in repos:
    is_new = repo['name'] not in prev_names
    repo['new_repo'] = is_new
    if is_new:
        suggested = suggest_category(repo['name'], repo.get('description', ''))
        if repo['name'] in CATEGORY_MAP:
            repo['suggested_category'] = CATEGORY_MAP[repo['name']]
        else:
            repo['suggested_category'] = suggested
        new_repos.append({
            'name': repo['name'],
            'description': repo.get('description'),
            'url': repo['url'],
            'suggested_category': repo['suggested_category'],
            'isPrivate': repo.get('isPrivate'),
            'language': repo.get('language'),
        })

if new_repos:
    print(f"🆕 New repos detected: {len(new_repos)}")
    for nr in new_repos:
        print(f"  + {nr['name']} → {nr['suggested_category']}")
else:
    print("ℹ️ No new repos detected")

# ─── Step 6: Assign categories ───
for repo in repos:
    if repo['name'] in CATEGORY_MAP:
        repo['category'] = CATEGORY_MAP[repo['name']]
    elif repo.get('new_repo'):
        repo['category'] = repo.get('suggested_category', '📋 기타')
    else:
        repo['category'] = suggest_category(repo['name'], repo.get('description', ''))

# Sort by category then stars
repos.sort(key=lambda r: (r['category'], -(r['stargazerCount'] or 0), r['name']))

# ─── Step 7: Save cache ───
cache_data = []
for repo in repos:
    cache_data.append({
        'name': repo['name'],
        'description': repo.get('description'),
        'url': repo['url'],
        'homepageUrl': repo.get('homepageUrl'),
        'stargazerCount': repo.get('stargazerCount', 0),
        'forkCount': repo.get('forkCount', 0),
        'isPrivate': repo.get('isPrivate', False),
        'createdAt': repo.get('createdAt'),
        'updatedAt': repo.get('updatedAt'),
        'pushed_at': repo.get('pushed_at'),
        'language': repo.get('language'),
        'category': repo['category'],
    })

with open(CACHE_FILE, 'w') as f:
    json.dump(cache_data, f, ensure_ascii=False)
print(f"💾 Cache saved: {CACHE_FILE}")

# Save new repos list
with open(NEW_REPOS_FILE, 'w') as f:
    json.dump(new_repos, f, ensure_ascii=False, indent=2)
print(f"💾 New repos saved: {NEW_REPOS_FILE}")

# ─── Step 8: Build output HTML ───
print("🏗️ Building dashboard HTML...")

with open(TEMPLATE, 'r') as f:
    html = f.read()

if '__REPOS_PLACEHOLDER__' not in html:
    print("ERROR: __REPOS_PLACEHOLDER__ not found in template!")
    sys.exit(1)

# Use separators to minimize JSON (no newlines that could break inline JS)
repos_json = json.dumps(repos, ensure_ascii=False, separators=(',', ':'))
html = html.replace('__REPOS_PLACEHOLDER__', repos_json)

# Inject build timestamp
build_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html = html.replace('__BUILD_TIME__', build_time)

with open(OUTPUT, 'w') as f:
    f.write(html)

# Verify placeholder is gone
with open(OUTPUT, 'r') as f:
    output = f.read()
if '__REPOS_PLACEHOLDER__' in output:
    print("ERROR: Placeholder still present in output!")
    sys.exit(1)

print(f"✅ Built: {OUTPUT}")
print(f"   Output size: {len(output):,} bytes")
print(f"   Repos injected: {len(repos)}")
print(f"   New repos: {len(new_repos)}")
print(f"   Stale repos: {sum(1 for r in repos if r.get('is_stale'))}")
print("🎉 Done!")
