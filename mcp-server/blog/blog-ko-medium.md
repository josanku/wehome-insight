# Claude에 한국 관광 데이터 연결하기 — K-STAY MCP 서버를 만든 이야기

> 한국 공공데이터를 LLM 시대의 표준 통합 방식인 MCP(Model Context Protocol)로 노출한 첫 한국형 사례. 외도민업 9,922곳·한옥체험업 2,522곳·축제 44개·외국인 통계까지 16개 도구로 자연어 호출.

---

## 왜 MCP인가?

ChatGPT·Claude·Gemini 같은 LLM이 빠르게 보급되면서, "LLM이 외부 도구를 어떻게 호출할 것인가"는 산업 표준 전쟁의 핵심이 되었습니다. 2024년 11월 Anthropic이 공개한 **MCP (Model Context Protocol)** 는 이 문제의 가장 깔끔한 답입니다.

**MCP의 핵심 아이디어**: 
- LLM 클라이언트(Claude Desktop·Cursor·Continue 등)와 외부 도구 서버 사이에 표준 프로토콜
- stdio·HTTP·SSE 등 다양한 전송 방식 지원
- 서버는 자기가 노출할 "도구(tool)" 목록과 입력 스키마를 선언
- LLM이 자연어 입력을 분석해 어떤 도구를 호출할지 자동 결정

OpenAI Function Calling이나 Anthropic Tool Use는 **모델별로 다른 인터페이스**였지만, MCP는 **클라이언트와 서버가 분리된 표준**이라 한 번 만들면 Claude·Cursor·Cline·Continue 모두에서 동작합니다.

## 왜 한국 관광 데이터인가?

위홈(wehome)을 운영하면서 본 풍경:
- 한국에는 **행정안전부 지방행정 인허가 데이터**라는 보석 같은 공공데이터가 있지만 일반인이 직접 활용하기 어려움
- 외국인 관광객 1,876만명 시대(2025년)인데 외국인 친화 데이터 인터페이스가 부족
- 공유숙박 호스트는 시장 정보가 없어 답답해함
- 개발자는 매번 정부 사이트에서 CSV 받아 파싱하는 반복 작업

→ 이 모든 걸 **하나의 LLM 도구**로 풀 수 있다는 발상.

## 만들기 — 3단계

### 1단계: 데이터 통합 (어려운 부분)

- **행정안전부 file.localdata.go.kr** — 5종 카테고리 CSV 매일 다운로드 (외도민업·한옥체험·관광숙박·농어촌·관광펜션)
- **EPSG:5174 → WGS84** 좌표 변환 (pyproj)
- **SQLite FTS5** 전문 검색
- 매일 04:00 KST cron 자동 갱신

### 2단계: REST API 노출

Flask로 21개 엔드포인트. CORS 허용해 누구나 쓸 수 있게:

```python
@app.after_request
def add_cors(response):
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response
```

`/api/hanok/stats`, `/api/tourism/inbound`, `/api/festivals` 등을 OpenAPI 3.0 스펙으로 문서화.

### 3단계: MCP 서버 래핑

TypeScript + `@modelcontextprotocol/sdk`로 REST API를 16개 도구로 래핑:

```typescript
const TOOLS = [
  {
    name: "get_hanok_stats",
    description: "한국 한옥체험업 종합 통계 (전국 2,522곳 영업중)",
    inputSchema: { type: "object", properties: {} },
  },
  // ... 15개 더
];

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name } = request.params;
  if (name === "get_hanok_stats") {
    const data = await fetch(`${API_BASE}/api/hanok/stats`).then(r => r.json());
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
  // ...
});
```

전체 코드: [github.com/josanku/wehome-insight/tree/main/mcp-server](https://github.com/josanku/wehome-insight/tree/main/mcp-server)

## 사용 예시

Claude Desktop 설정 파일에 5줄 추가하고:
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

이제 자연어로 물으면 Claude가 자동으로 도구를 호출합니다:

> **Me**: "10월에 한국 갈건데, 외국인이 좋아할 만한 축제 3개랑 그 근처 한옥숙박 추천해줘"
>
> **Claude**: (`get_festivals(month=10)` 호출 → 진주남강유등·안동탈춤·부산국제영화제 발견. 각 축제 인근 `search_hanok_listings` 호출 → 통합 답변)
> 
> 1️⃣ 진주남강유등축제 (10/1-15, 280만명) — 임진왜란 진주성 전투 기원
>    → 인근 한옥: 진주 OO한옥체험관
> 2️⃣ 안동국제탈춤페스티벌 (9/26-10/5, 150만명) — UNESCO 연계
>    → 인근 한옥: 안동 하회마을 충효당·양진당 종택
> ...

WebFetch나 수동 curl보다 3-4배 빠르고, URL을 기억할 필요도 없습니다.

## 배운 것 3가지

**1. MCP는 데이터 → LLM 어댑터의 표준이 될 것**

OpenAPI 스펙이 있다면 MCP 서버 작성은 1-2일이면 됩니다. Anthropic이 만들었지만 이미 Cursor·Cline·Continue 등이 모두 지원하면서 **사실상 표준**이 되어가는 중입니다.

**2. 자연어 인터페이스 = 데이터 활용 장벽 ↓↓**

저희 K-STAY 사이트의 가장 큰 사용성 장벽은 "복잡한 데이터를 어떻게 탐색할 것인가"였습니다. MCP로 자연어 인터페이스를 추가하니, 비개발자도 "광주 한옥 추천해줘"라고 물을 수 있게 됐습니다.

**3. 공공데이터 + LLM = 큰 기회**

한국 정부는 매년 수조원 규모의 공공데이터를 공개하지만 활용률은 낮습니다. **공공데이터를 MCP 서버로 노출하면** 정책 정보 검색·연구·언론·교육 등 모든 분야에서 사용이 폭발할 수 있습니다.

저희는 이를 K-STAY로 시작했지만, 다른 분들도 본인 도메인의 공공데이터를 MCP로 만들면 좋겠습니다. 코드는 MIT, 만드는 패턴도 단순합니다.

## 직접 사용해보기

- 🌐 https://k-stay.ai
- 📘 https://k-stay.ai/developer (5분 가이드)
- 📡 https://k-stay.ai/docs (REST API 인터랙티브 문서)
- 🐙 https://github.com/josanku/wehome-insight (GitHub Star 부탁드립니다!)

질문은 api@k-stay.ai 또는 GitHub Issues로.

---

*K-STAY는 위홈(wehome, Inc.)이 운영합니다. 위홈은 한국 최초의 합법 공유숙박 플랫폼으로, 외국인관광도시민박업(외도민업) 등록 호스트만 입점합니다.*

#mcp #claude #ai #공공데이터 #한국관광 #wehome
