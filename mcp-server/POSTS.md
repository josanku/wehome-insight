# 📣 게시물 모음 — 복붙해서 즉시 사용

각 플랫폼별 게시물 초안. 그대로 복사해서 게시하세요.

---

## 1. Hacker News (Show HN)

**제목** (80자 이내):
```
Show HN: K-STAY MCP – Korean tourism & lodging data in Claude/Cursor (50k+ items)
```

**본문**:
```
Hi HN! I built an open-source MCP server that gives Claude Desktop, Cursor, and other AI tools native access to Korean tourism data:

• 9,922 legal Korean homestays (외도민업)
• 2,522 hanok (traditional house) experiences
• 130+ temple stays
• 44 major festivals
• 35 K-Culture hotspots (K-Pop, K-Drama sites)
• Inbound tourism stats by country/month
• ~50,000 verified data points total

All from Korean government open data (행정안전부), refreshed daily.

It exposes 16 typed tools to LLMs:
- get_hanok_stats, search_hanok_listings
- get_festivals, get_temple_stays
- get_inbound_tourism, get_kculture_hotspots
- ... and more

Install in 30 seconds:
{
  "mcpServers": {
    "k-stay": {
      "command": "npx",
      "args": ["-y", "@k-stay/mcp-server"]
    }
  }
}

Then ask Claude naturally: "Recommend October festivals in Korea + nearby hanok stays"

Free, MIT license, no API key required.

Source: https://github.com/josanku/wehome-insight/tree/main/mcp-server
Live site: https://k-stay.ai
Dev guide: https://k-stay.ai/developer
REST API docs: https://k-stay.ai/docs

Built this because Korean public data is rich but underutilized — wrapping it as MCP makes it instantly usable in any LLM workflow.

Feedback welcome!
```

---

## 2. Reddit · r/ClaudeAI

**제목**:
```
[Show] K-STAY MCP server — Korean tourism & accommodation data for Claude (50k+ verified listings, free)
```

**본문**:
```
Hey r/ClaudeAI! Built an MCP server that gives Claude Desktop instant access to Korean tourism data.

**What it does**:
Ask Claude things like:
- "Recommend October festivals in Korea + nearby hanok stays"
- "Which sigungu has the most hanok? Top 5"
- "Chinese tourist recovery rate vs 2019"

Claude automatically calls the right tool (no URL fetching, no JSON parsing) and gives you the answer.

**Data**:
- 9,922 legal homestays · 2,522 hanok experiences
- 130+ temple stays · 44 festivals · 35 K-Culture spots
- Inbound tourism stats (KTO + Ministry of Justice)
- All from Korean government open data, refreshed daily

**Install (Claude Desktop)**:
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
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

Restart Claude. Done.

**Links**:
- GitHub: https://github.com/josanku/wehome-insight (please star ⭐)
- Live site: https://k-stay.ai
- Dev guide: https://k-stay.ai/developer
- Demo: https://k-stay.ai/developer (try the "Try it" buttons)

Free, MIT license. No API key. Built with Anthropic MCP SDK.

Happy to answer questions!
```

---

## 3. Reddit · r/LocalLLaMA

**제목**:
```
Free MCP server for Korean tourism — 50,000+ verified listings, works with any MCP client
```

**본문**: (위 r/ClaudeAI 본문과 동일, 단 "Claude Desktop" 외에 "Cursor, Continue, Cline, OpenWebUI" 등도 작동한다고 명시)

---

## 4. Reddit · r/korea

**제목**:
```
Claude·Cursor에서 한국 관광·숙박 데이터 자연어로 쓰는 MCP 서버 만들었습니다 (오픈소스)
```

**본문**:
```
안녕하세요. 외도민업·한옥체험업·호텔·템플스테이·축제 등 한국 관광 데이터를 Claude나 Cursor 같은 LLM 도구에서 자연어로 쓸 수 있게 해주는 오픈소스 MCP 서버를 만들었습니다.

**데이터**:
- 외도민업 9,922곳 영업중
- 한옥체험 2,522곳 + 한옥마을 51곳 + 명품고택 55곳
- 템플스테이 130+곳
- 전국 축제 44개
- K-Pop·Drama·Food·Beauty 명소
- 외국인 관광객 통계 (월별·국가별)

모두 행정안전부 공공데이터 + KTO·문화재청 자료 기반, 매일 자동 갱신.

**Claude Desktop에 설치 (30초)**:
설정 파일에 5줄 추가하면 끝. 자세한 가이드: https://k-stay.ai/developer

**예시**:
> "10월에 한국 외국인 가는 축제 + 근처 한옥 추천"
→ Claude가 자동으로 도구 호출 → 진주남강유등·안동탈춤 + 인근 한옥 추천

무료, 인증 불필요, MIT 라이선스.

링크:
- 사이트: https://k-stay.ai
- GitHub: https://github.com/josanku/wehome-insight
- 개발자 가이드: https://k-stay.ai/developer

피드백 환영합니다!
```

---

## 5. Twitter/X — 한국어 스레드

**1/8**:
```
🇰🇷 한국 관광·숙박 데이터를 Claude·Cursor에 연결하는 K-STAY MCP 서버 출시!

📌 외도민업 9,922곳
📌 한옥체험 2,522곳
📌 한옥마을 51 / 명품고택 55
📌 템플스테이 130+
📌 축제 44개·외국인 통계
📌 100% 무료, 인증 불필요

스레드 ⬇️ (1/8)

🔗 https://k-stay.ai/developer
```

**2/8**:
```
MCP는 Anthropic이 2024년 11월 공개한 표준입니다.

LLM과 외부 데이터·도구를 연결하는 방식인데, OpenAI Function Calling과 달리 한 번 만들면 Claude·Cursor·Cline·Continue 등 모든 클라이언트에서 작동합니다.

사실상 LLM 도구 표준이 되어가는 중. (2/8)
```

**3/8**:
```
Claude Desktop에 5줄 추가:

{
  "mcpServers": {
    "k-stay": {
      "command": "npx",
      "args": ["-y", "@k-stay/mcp-server"]
    }
  }
}

재시작 → 끝. (3/8)
```

**4/8**:
```
이제 자연어로 물으면 Claude가 알아서 도구를 호출합니다.

👤 "10월에 한국 갈건데, 외국인 좋아할 축제 + 근처 한옥 추천"
🤖 (get_festivals + search_hanok_listings 자동 호출)
→ 진주남강유등 + 인근 한옥 / 안동탈춤 + 하회마을 종택 / ... (4/8)
```

**5/8**:
```
👤 "보물로 지정된 한옥 종택, 종부가 직접 운영하는 곳"
🤖 (get_meongpum_gotaek 호출)
→ 임청각(보물 182호) · 양진당(306호) · 향단(412호) ...

👤 "중국 관광객 코로나 이전 대비 회복률"
🤖 (get_inbound_tourism)
→ "78% 회복. 일본 105%, 베트남 113%..." (5/8)
```

**6/8**:
```
🏠 호스트도 유용:
👤 "마포구 외도민업 시작하려는데 시장 어떤가?"
🤖 (get_stats + get_registrations_monthly)
→ "마포구 1,752곳, 월평균 신규 60건"

💻 개발자도:
👤 "Next.js로 한옥 지도 만들어줘"
🤖 → 완성된 컴포넌트 코드 + 카카오 SDK (6/8)
```

**7/8**:
```
모든 데이터는 정부 공식 출처:
• 행정안전부 인허가 데이터 (매일 04:00 갱신)
• 한국관광공사·문화재청·한국불교문화사업단
• 법무부 출입국 통계

출처가 명확해서 학술·언론 인용도 가능. (7/8)
```

**8/8**:
```
오픈소스 MIT, 무료, API 키 불필요.

📘 5분 가이드: https://k-stay.ai/developer
📡 REST API: https://k-stay.ai/docs
🐙 GitHub: https://github.com/josanku/wehome-insight

⭐ Star 부탁드립니다. 한국 공공데이터가 LLM 시대에 더 잘 쓰이게 함께해주세요. (8/8)

#mcp #claude #공공데이터 #한국관광
```

---

## 6. Twitter/X — English thread

**1/6**:
```
🇰🇷 New MCP server for AI tools (Claude Desktop, Cursor):

K-STAY brings Korean tourism & lodging data to your LLM workflows.

✅ 50,000+ verified listings
✅ Hanok villages, K-Pop sites, festivals
✅ Inbound tourism stats
✅ Free, no API key

🧵 (1/6)

https://k-stay.ai/developer
```

**2/6**:
```
What's MCP?

Anthropic's Model Context Protocol — standard way for LLMs to call external tools.

Write once, works in Claude Desktop / Cursor / Continue / Cline / etc.

Game-changer for connecting public data to AI. (2/6)
```

**3/6**:
```
Install in 30 seconds:

Add to claude_desktop_config.json:

{"mcpServers":{"k-stay":{"command":"npx","args":["-y","@k-stay/mcp-server"]}}}

Restart Claude. Done. (3/6)
```

**4/6**:
```
Now ask naturally:

👤 "Recommend October festivals in Korea + nearby hanok stays"
🤖 (calls get_festivals + search_hanok_listings)
→ Top 3 festivals + matched hanok with coordinates

👤 "Chinese tourist recovery vs 2019"
🤖 (get_inbound_tourism)
→ "78%. Japan 105%, Vietnam 113%..." (4/6)
```

**5/6**:
```
Data sources (all official):
• Korean Government Open Data (행정안전부)
• Korea Tourism Organization (KTO)
• Cultural Heritage Administration
• Ministry of Justice (immigration stats)

Refreshed daily 4 AM KST. (5/6)
```

**6/6**:
```
MIT license, no API key.

📘 https://k-stay.ai/developer
📡 https://k-stay.ai/docs
🐙 https://github.com/josanku/wehome-insight

⭐ Stars and shares appreciated. Let's make Korean public data more useful in the AI era. (6/6)

#MCP #Claude #OpenData #Korea
```

---

## 7. Anthropic Discord (#showcase)

```
🇰🇷 Built an MCP server for Korean tourism & lodging data — wanted to share!

**K-STAY MCP** exposes 16 tools to Claude Desktop / Code / Cursor for accessing:
- 9,922 legal Korean homestays
- 2,522 hanok experiences  
- 130+ temple stays
- 44 festivals
- Inbound tourism stats
- ~50,000 total verified data points

All from Korean government open data, refreshed daily. Free, MIT, no API key.

🔗 https://k-stay.ai/developer
📦 npm: @k-stay/mcp-server (publishing soon)
🐙 GitHub: https://github.com/josanku/wehome-insight

Built this to make Korean public data accessible to AI assistants. Demo conversations and full code linked. Feedback welcome!
```

---

## 8. LinkedIn

```
🚀 위홈에서 K-STAY MCP 서버를 오픈소스로 공개했습니다.

Anthropic의 Model Context Protocol(MCP)을 사용해 한국 관광·숙박 데이터(외도민업·한옥·호텔·축제·외국인 통계 등 약 50,000건)를 Claude·Cursor 같은 AI 도구에 자연어로 연결합니다.

🎯 핵심:
• 한국 공공데이터 + LLM 표준 통합 첫 사례
• 16개 도구로 자연어 호출
• 100% 무료, MIT 라이선스, API 키 불필요

🔗 한 줄 가이드: https://k-stay.ai/developer
📡 REST API 문서: https://k-stay.ai/docs
🐙 GitHub: https://github.com/josanku/wehome-insight

공공데이터 + AI 통합에 관심 있는 분, 한국 진출 외국 기업 분, 여행 관련 서비스 만드시는 분 — 자유롭게 사용·공유해주세요.

함께 일하실 분, 협업 제안은 api@k-stay.ai

#MCP #Claude #공공데이터 #한국관광 #wehome #AI
```

---

## 9. GeekNews (news.hada.io)

**제목**:
```
K-STAY MCP - 한국 관광·숙박 데이터를 Claude·Cursor에 연결하는 첫 한국형 MCP 서버 [오픈소스]
```

**본문** (마크다운):
```markdown
한국 공공데이터(행정안전부 인허가 데이터·KTO·문화재청)를 Anthropic MCP로 노출한 첫 한국 사례입니다.

## 데이터
- 외도민업 9,922곳 · 한옥체험 2,522곳 · 템플스테이 130+
- 한옥마을 51 · 명품고택 55 · 축제 44 · K-Culture 35
- 외국인 관광객 통계 (월·국가·연령·목적)
- 총 ~50,000건 검증 데이터, 매일 04:00 자동 갱신

## 사용
Claude Desktop config에 5줄 추가:
```json
{"mcpServers":{"k-stay":{"command":"npx","args":["-y","@k-stay/mcp-server"]}}}
```
재시작하면 자연어로 한국 관광 데이터 호출 가능.

## 의의
- 한국 정부 공공데이터의 LLM 통합 첫 사례
- MIT 라이선스, API 키 불필요, CORS 허용
- REST API + MCP + OpenAPI 3.0 모두 제공

링크:
- 개발자 가이드: https://k-stay.ai/developer
- REST API: https://k-stay.ai/docs
- GitHub: https://github.com/josanku/wehome-insight
- 보급 전략: https://github.com/josanku/wehome-insight/blob/main/mcp-server/PROMOTION.md
```

---

## 10. Product Hunt 등록

**Tagline** (60자 이내):
```
Korean tourism & lodging data for any AI tool
```

**Description**:
```
K-STAY connects 50,000+ verified Korean accommodations, festivals, and tourism stats to Claude, Cursor, and any MCP-compatible AI tool.

Ask AI naturally:
"Recommend October festivals in Korea + nearby hanok"
"Chinese tourist recovery rate vs 2019"
"Hanok types I should consider as a host in Mapo-gu"

→ Your AI calls the right tool, returns structured data.

Free, open-source MIT, no API key required.

Built on Korean government open data (행정안전부, KTO, Ministry of Justice), refreshed daily.

For travelers, hosts, journalists, researchers, and developers.
```

**Maker Comment**:
```
👋 Hi PH! Maker here.

I built K-STAY because Korean public data is rich but hard to access — every researcher and traveler ends up parsing CSVs or scraping government sites.

The MCP standard (Anthropic, Nov 2024) made it possible to wrap this once and have it work everywhere — Claude Desktop, Cursor, Continue, Cline, etc.

Highlights:
✅ 16 tools (statistics, search, details)
✅ ~50K data points across 11 lodging/culture categories  
✅ Updated daily 4 AM KST
✅ MIT, no API key, CORS-enabled REST API too

Try it: https://k-stay.ai/developer

Happy to answer any questions about MCP, Korean tourism data, or implementation details!
```

---

## 사용 가이드

1. **순서**: HN → Reddit → Twitter → Product Hunt → LinkedIn → GeekNews
2. **시간대**:
   - HN: 한국시간 오후 10~11시 (미 동부 오전 9시)
   - Reddit: 미 동부 오전 8~10시
   - Twitter: 화/수 한국시간 오후 8시
   - PH: 화/수 0시 PT
3. **간격**: HN 후 24시간 대기 → Reddit, 이후 매일 1개 플랫폼
4. **반응 모니터링**: 댓글·DM 1시간 내 응답
