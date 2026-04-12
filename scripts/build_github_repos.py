#!/usr/bin/env python3
"""Build GitHub repos dashboard page with live data from GitHub API."""
import json
import subprocess
import os

REPO_DIR = "/Users/hjshin/icbm2-knowledge-graph"
TEMPLATE = os.path.join(REPO_DIR, "dashboard", "github-repos.html")
OUTPUT = os.path.join(REPO_DIR, "dashboard", "github-repos.html")

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

# Fetch repos
print("Fetching repos from GitHub...")
result = subprocess.run(
    ['gh', 'repo', 'list', '--limit', '100', '--json',
     'name,description,url,stargazerCount,forkCount,primaryLanguage,updatedAt,createdAt,isPrivate,homepageUrl'],
    capture_output=True, text=True
)
repos = json.loads(result.stdout)

# Add category
for repo in repos:
    repo['language'] = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else None
    repo['category'] = CATEGORY_MAP.get(repo['name'], "📋 기타")
    # Remove primaryLanguage to keep data clean
    del repo['primaryLanguage']

# Sort: by category then by stars desc
repos.sort(key=lambda r: (r['category'], -r['stargazerCount'], r['name']))

print(f"Total: {len(repos)} repos")

# Read template and inject data
with open(TEMPLATE, 'r') as f:
    html = f.read()

repos_json = json.dumps(repos, ensure_ascii=False, indent=2)
html = html.replace('__REPOS_PLACEHOLDER__', repos_json)

with open(OUTPUT, 'w') as f:
    f.write(html)

print(f"Built: {OUTPUT}")
