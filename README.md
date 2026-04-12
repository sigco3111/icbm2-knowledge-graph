# 🚀 ICBM2 Command Center

> ICBM2 자동화 AI 에이전트의 모든 활동을 한눈에 볼 수 있는 웹 대시보드

**🌐 Live Demo:** [https://sigco3111.github.io/icbm2-knowledge-graph/](https://sigco3111.github.io/icbm2-knowledge-graph/)

## 📸 섹션

| 섹션 | 설명 |
|------|------|
| 🧠 Knowledge Graph | D3.js 기반 인터랙티브 지식 그래프 (671 노드, 9,781 연결) |
| 📦 GitHub Repos | 124개 저장소 대시보드 — 언어/카테고리 분포, 히트맵, 상세 모달 |

## 📦 GitHub Repos 대시보드

124개 GitHub 저장소를 6개 카테고리로 분류한 종합 대시보드입니다.

**기능:**
- 📊 언어 분포 도넛 차트, 월별 생성 트렌드, 카테고리별 비중, 활동 히트맵
- 🔍 검색, 카테고리/공개여부 필터, 정렬 (이름/Stars/Forks/업데이트)
- 📋 저장소 상세 모달 (README 미리보기, 최근 커밋, Topics, 메타 정보)
- 🏆 인기 저장소 TOP 5
- ⚠️ 미관리 저장소 식별 (6개월+ 미활동)
- 🆕 신규 저장소 자동 감지 + 카테고리 추천
- 📱 모바일 반응형 최적화 (4단계 브레이크포인트)

**카테고리 분류:**
| 카테고리 | 저장소 수 | 예시 |
|----------|-----------|------|
| 🎮 게임 | 56개 | 2048, wordle, candy-crush-saga, mount-and-blade |
| 📊 데이터 시각화 | 27개 | github-board, steam-board, commodity-dashboard |
| 🌐 웹 프로젝트 | 10개 | KakaoSplit, DevCanvas, astrocartography |
| 🔧 ICBM/에이전트 | 4개 | hermes_bot, icbm2-knowledge-graph |
| 🛠 개발 도구 | 3개 | prompt-advisor, ccusage-json |
| 📖 재무 | 1개 | bookk |

## 🛠 기술 스택

- **D3.js v7** — 지식 그래프 시각화
- **Canvas API** — 저장소 대시보드 차트 (도넛, 바, 히트맵)
- **Vanilla JS** — 탭 네비게이션, 인터랙션, 모달
- **GitHub REST API** — 저장소 데이터 수집 + 페이지네이션
- **GitHub Pages** — 자동 배포 (main 브랜치)
- **Python** — 데이터 수집/빌드 스크립트

## 📁 프로젝트 구조

```
icbm2-knowledge-graph/
├── index.html                              # 메인 대시보드 (지식그래프 + GitHub Repos 탭)
├── README.md                               # 이 파일
├── dashboard/
│   ├── github-repos-template.html          # GitHub Repos HTML 템플릿
│   ├── github-repos.html                   # GitHub Repos 빌드 결과 (자동 생성)
│   └── index.html                          # 대시보드 진입점
├── data/
│   ├── nodes.json                          # 지식 그래프 노드 (671개)
│   ├── links.json                          # 지식 그래프 연결 (9,781개)
│   ├── github_repos_cache.json             # GitHub 저장소 캐시
│   └── github_repos_new.json               # 신규 저장소 목록
└── scripts/
    └── build_github_repos.py               # GitHub 대시보드 빌드 스크립트
```

## 🔄 자동 업데이트

| 작업 | 스케줄 | 설명 |
|------|--------|------|
| 지식 그래프 | 매일 21:00 KST | Notion DB에서 노드/연결 데이터 갱신 |
| GitHub Repos | 매주 일요일 04:00 KST | 전체 저장소 데이터 수집 + 배포 |

### GitHub Repos 빌드

```bash
# 전체 빌드 (커밋/README 포함, ~2분)
python3 scripts/build_github_repos.py

# 빠른 빌드 (캐시 활용, ~3초)
python3 scripts/build_github_repos.py --fast
```

## 📝 라이선스

MIT

---
*Last updated: 2026-04-12*
