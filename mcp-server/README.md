# @k-stay/mcp-server

> K-STAY MCP server — Claude Desktop / Claude Code / Cursor에서 한국 숙박·관광·문화 데이터를 **native 도구**처럼 사용하세요.

[![MCP](https://img.shields.io/badge/MCP-1.0-blue.svg)](https://modelcontextprotocol.io)
[![Node](https://img.shields.io/badge/node-%3E%3D18-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-orange.svg)]()

K-STAY API([k-stay.ai](https://k-stay.ai))의 21개 엔드포인트를 LLM이 직접 호출할 수 있는 16개의 도구로 노출합니다. WebFetch보다 빠르고, 응답이 LLM 컨텍스트에 곧장 들어가며, 인자 검증·타입 안전이 자동 처리됩니다.

## 제공 도구

| 도구 | 설명 |
|---|---|
| `get_stats` | 외국인관광도시민박업(외도민업) 종합 통계 |
| `get_categories_overview` | 5종 합법 숙박 카테고리 요약 |
| `get_registrations_monthly` | 지역별 월간 신규 등록 추이 |
| `get_hanok_stats` | 한옥체험업 통계 (2,522곳 영업중) |
| `search_hanok_listings` | 한옥체험업 영업장 검색 (좌표 포함) |
| `get_hanok_villages` | 한옥마을 51곳 |
| `get_meongpum_gotaek` | KTO 명품고택 55곳 |
| `get_temple_stays` | 템플스테이 사찰 130+곳 |
| `search_lodging` | 호텔·호스텔·농어촌·펜션 검색 |
| `get_lodging_stats` | 카테고리별 통계 |
| `get_inbound_tourism` | 외국인 관광객 통계 (월별·국가별·목적) |
| `get_kculture_hotspots` | K-Pop·Drama·Food·Beauty 명소 |
| `get_korea100` | 한국관광공사 한국관광 100선 |
| `get_festivals` | 전국 축제 캘린더 (월 필터) |
| `get_data_sources` | 데이터 출처 카탈로그 |
| `get_monthly_report` | 월간 시장 리포트 |

## 설치

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 또는
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) 에 추가:

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

Claude Desktop을 재시작하면 메시지 입력란 옆에 🔌 아이콘이 표시되고 K-STAY 도구가 활성화됩니다.

### Claude Code (CLI)

```bash
claude mcp add k-stay -- npx -y @k-stay/mcp-server
```

또는 프로젝트 `.mcp.json`:
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

### 로컬 개발

```bash
git clone https://github.com/josanku/wehome-insight.git
cd wehome-insight/mcp-server
npm install
npm run build
node dist/index.js   # stdio 서버 기동 (Ctrl-C로 종료)
```

Claude Desktop 설정에서 `"command": "node", "args": ["/path/to/dist/index.js"]` 로 가리키세요.

## 환경 변수

- `K_STAY_API_BASE` (선택) — API base URL. 기본 `https://k-stay.ai`. 자체 미러나 스테이징 환경 사용 시 변경.

## 사용 예시

Claude Desktop에서 자연어로 호출:

```
사용자: "한옥체험업 영업장이 가장 많은 시군구 5곳 알려줘"
Claude: (도구 호출: get_hanok_stats)
        경주시 363곳, 종로구 332곳, 전주시 298곳, 안동시 184곳, 순천시 74곳입니다.

사용자: "2026년 1~5월 사이 서울 부산 신규 외도민업 등록 비교"
Claude: (도구 호출: get_registrations_monthly with year="2026")
        서울 1,314건, 부산 166건으로 서울이 부산의 7.9배.
        ...

사용자: "10월에 외국인 관광객이 가장 많이 오는 축제는?"
Claude: (도구 호출: get_festivals with month=10)
        진주남강유등축제 280만명, 안동탈춤 150만명, 부산국제영화제 20만명 등.
```

## 데이터 출처

- DB 데이터: 행정안전부 지방행정 인허가 데이터 (매일 04:00 KST 자동 갱신)
- 큐레이션: 한국관광공사·문화재청·한국불교문화사업단·각 운영사 공개 자료
- 모든 데이터 출처는 `get_data_sources` 도구로 즉시 조회 가능

## 라이선스

MIT License — wehome, Inc.

## 문의

- 📧 [api@k-stay.ai](mailto:api@k-stay.ai)
- 🌐 [k-stay.ai/docs](https://k-stay.ai/docs)
- 🐛 [GitHub Issues](https://github.com/josanku/wehome-insight/issues)
