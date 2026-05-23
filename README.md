# K-STAY

[![Live](https://img.shields.io/badge/live-k--stay.ai-FF6B35)](https://k-stay.ai)
[![MCP](https://img.shields.io/badge/MCP-1.0-blue)](https://k-stay.ai/developer)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open Data](https://img.shields.io/badge/data-공공누리%20제4유형-orange)](https://www.kogl.or.kr/info/license.do)

> **K-STAY** · Get the best stay for you in Korea. Powered by Wehome, certified home sharing of Korea.

한국을 여행하는 모든 분(내국인·외국인)이 꼭 찾는 숙소 종합 가이드. AI 비서가 내게 최적의 숙소를 추천하며, 외도민업·한옥·호텔·호스텔·템플스테이·축제까지 한국 숙박 정보의 가장 최신·정확한 출처입니다.

🌐 **Live**: [https://k-stay.ai](https://k-stay.ai)  ·  📘 **개발자**: [k-stay.ai/developer](https://k-stay.ai/developer)  ·  📡 **API**: [k-stay.ai/docs](https://k-stay.ai/docs)

---

## 🎯 무엇을 제공하나

| 카테고리 | 데이터 규모 | 출처 |
|---|---|---|
| 외국인관광도시민박업 (외도민업) | 9,922 영업중 | 행정안전부 (매일 갱신) |
| 한옥체험업 | 2,522 영업중 | 행정안전부 (매일 갱신) |
| 관광호텔 / 호스텔 | 1,229 + 397 | 행정안전부 |
| 농어촌민박 | 36,361 영업중 | 행정안전부 |
| 관광펜션업 | 1,300 영업중 | 행정안전부 |
| 한옥마을 | 51곳 큐레이션 | UNESCO·문화재청·KTO |
| 한국관광공사 명품고택 | 55곳 큐레이션 | KTO·문화재청 |
| 템플스테이 사찰 | 130+ 큐레이션 | 한국불교문화사업단 |
| K-Culture 핫스팟 | 35곳 (K-Pop·Drama·Food·Beauty) | K-STAY 큐레이션 |
| 한국관광 100선 | 75곳 (2025-2026) + 아카이브 | KTO 격년 발표 |
| 전국 축제 | 44개 (월별·카테고리) | KTO·문체부 |
| 외국인 관광객 통계 | 월별·연도별·국가별 | KTO 데이터랩 + 법무부 |
| **합계** | **~50,000+ 영업장 + 큐레이션 350+** | |

---

## 🚀 즉시 사용 (3가지 방법)

### 1️⃣ 웹사이트 (가장 쉬움)
브라우저에서 [https://k-stay.ai](https://k-stay.ai) 접속.

### 2️⃣ Open REST API
```bash
curl https://k-stay.ai/api/hanok/stats
curl https://k-stay.ai/api/festivals
curl https://k-stay.ai/api/tourism/inbound
```
- 인증 불필요, CORS 허용, JSON 응답
- 21개 엔드포인트 · [전체 문서](https://k-stay.ai/docs) · [OpenAPI 3.0 스펙](https://k-stay.ai/openapi.json)

### 3️⃣ MCP Server (Claude·Cursor 네이티브 통합)
Claude Desktop 또는 Claude Code에서 자연어로 K-STAY 데이터 사용. [전체 가이드](https://k-stay.ai/developer)

**Claude Desktop:** `claude_desktop_config.json`에 추가:
```json
{
  "mcpServers": {
    "k-stay": {
      "command": "npx",
      "args": ["-y", "@k-stay/mcp-server"]
    }
  }
}
```

**Claude Code:**
```bash
claude mcp add k-stay -- npx -y @k-stay/mcp-server
```

이제 자연어로:
```
한옥체험업이 가장 많은 시군구 5곳 알려줘
10월 외국인이 좋아할 만한 축제 + 근처 한옥 추천
중국 방문객 코로나 이전 대비 회복률
```

→ Claude가 16개 도구 중 적절한 것 자동 호출.

[📘 MCP 개발자 가이드 (전체)](mcp-server/DEVELOPER_GUIDE.md) · [📦 MCP 서버 README](mcp-server/README.md)

---

## 🏗️ 아키텍처

```
Browser / Claude / Cursor / 외부 앱
            ↓
┌──────────────────────────────────────┐
│  K-STAY.AI (lounge 사이트)            │
│  - 21 페이지 (한옥/숙박/문화/통계)     │
│  - 21 REST API (CORS 허용)            │
│  - OpenAPI 3.0 spec                  │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│  K-STAY MCP Server                   │
│  - 16 native tools                   │
│  - stdio transport                   │
│  - Anthropic MCP SDK 1.0             │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│  Flask + SQLite + pyproj             │
│  - 5종 카테고리 매일 04:00 갱신       │
│  - 큐레이션 JSON (data/)              │
│  - data-sources.json 카탈로그         │
└──────────────────────────────────────┘
```

---

## 📂 디렉토리 구조

```
wehome-insight/
├── server.py              # Flask 메인 서버 (라우트 + API)
├── *.html                 # 페이지 (studio·analysis·hanok·tourism·docs·developer 등 28개)
├── data/
│   ├── urbanstay.db       # SQLite 영업장 데이터 (172MB, gitignored)
│   ├── hanok/             # 한옥마을·명품고택 JSON
│   ├── temple/            # 템플스테이 JSON
│   ├── lodging/           # 코리빙·레지던스·글램핑·외국인 통계
│   ├── culture/           # K-Culture·관광100선·축제
│   └── data-sources.json  # 데이터 소스 카탈로그
├── mcp-server/            # K-STAY MCP 서버 (Node.js/TypeScript)
│   ├── src/index.ts
│   ├── README.md
│   ├── DEVELOPER_GUIDE.md # 개발자 매뉴얼 (9 섹션)
│   └── PROMOTION.md       # 보급 전략 가이드
├── fetch_data.py          # 매일 04:00 cron - 5종 CSV 갱신
├── publish_report.py      # 매월 25일 cron - 월간 리포트
├── news_monitor.py        # 매일 06:00 cron - 뉴스 모니터
└── aws/                   # AWS 배포 자산 (App Runner / CloudFormation)
```

---

## 🤖 자동화

- **매일 04:00** — `fetch_data.py` 행정안전부 CSV 5종 자동 다운로드 + 서비스 재시작
- **매일 06:00** — `news_monitor.py` 공유숙박 관련 뉴스 수집
- **매주 일요일 03:30** — 큐레이션 JSON 변경 감지
- **매월 25일 00:05** — `publish_report.py` 월간 시장 리포트 스냅샷
- **GitHub Actions** — main push 시 EC2 SSH 자동 배포

---

## 🔓 라이선스 · 출처

- **코드**: MIT License
- **DB 데이터**: 행정안전부 공공누리 제4유형 (출처표시·상업적이용금지·변경금지)
- **큐레이션**: KTO·문화재청·한국불교문화사업단 등 공개 자료 기반
- **인용 시**: "Data from K-STAY (k-stay.ai) · 행정안전부 인허가 데이터"

---

## 🤝 기여 · 문의

- 📧 [api@k-stay.ai](mailto:api@k-stay.ai)
- 🐛 [Issues](https://github.com/josanku/wehome-insight/issues)
- ⭐ Star 부탁드립니다 — 한국 공공데이터의 LLM 통합을 함께 발전시켜요
- 📣 [MCP 보급 도와주세요](mcp-server/PROMOTION.md)

---

**Made by [wehome, Inc.](https://wehome.me)** · 한국 최초 인증 합법 공유숙박 플랫폼  ·  Built on public open data from 행정안전부 / KTO / 문화재청
