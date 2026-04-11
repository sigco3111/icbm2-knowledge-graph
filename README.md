# 🚀 ICBM2 Command Center

> ICBM2 자동화 AI 에이전트의 모든 활동을 한눈에 볼 수 있는 웹 대시보드

**🌐 Live Demo:** [https://sigco3111.github.io/icbm2-knowledge-graph/](https://sigco3111.github.io/icbm2-knowledge-graph/)

## 📸 미리보기

| 섹션 | 설명 |
|------|------|
| 🧠 Knowledge Graph | D3.js 기반 인터랙티브 지식 그래프 (671 노드, 9,781 연결) |
| 📊 Dashboard | 크론잡 상태, 성과 통계, 데이터 소스 분포 |
| 🤖 Skills | 104개 스킬을 22 카테고리로 분류 |
| 📈 AI Models | 12개 AI 모델 릴리즈 트래커 |

## 🛠 기술 스택

- **D3.js v7** — 지식 그래프 시각화
- **Vanilla JS** — 탭 네비게이션, 인터랙션
- **GitHub Pages** — 자동 배포 (main 브랜치)
- **Notion API** — 데이터 수집 (iOS Trend, AI Model Tracker, 투자 메모 등)

## 📁 프로젝트 구조

```
icbm2-knowledge-graph/
├── index.html          # 메인 대시보드 (4섹션 SPA)
├── README.md           # 이 파일 (자동 갱신)
├── data/
│   ├── nodes.json      # 지식 그래프 노드 데이터 (671개)
│   └── links.json      # 지식 그래프 연결 데이터 (9,781개)
```

## 🔄 자동 업데이트

지식 그래프 데이터는 매일 21:00 KST에 자동으로 갱신됩니다.

## 📝 라이선스

MIT

---
*Last updated: 2026-04-11 22:31 KST*
