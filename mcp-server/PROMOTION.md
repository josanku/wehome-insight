# K-STAY MCP 서버 보급 전략 (실행 가이드)

> **누구가 이 글을 읽나?** wehome 운영자 본인. K-STAY MCP를 어떻게 널리 알릴지 단계별 실행 매뉴얼.

---

## 핵심 메시지

> "한국 숙박·관광·문화 데이터를 LLM에 즉시 연결하는 첫 한국형 MCP 서버."

- **차별점**: 한국 공식 데이터(행정안전부·KTO·문화재청) + AI 친화 인터페이스
- **타깃**: ① LLM 도구 사용자(개발자·디자이너·연구자), ② 한국 여행 외국인, ③ 공유숙박 호스트
- **무료**: 인증·과금 없음, 출처표시만

---

## 1주 차: 즉시 실행 (오늘·내일)

### Day 1 — 공식 발견 채널 등록

#### ✅ Smithery.ai 등록 (MCP 디렉토리 1위)
1. https://smithery.ai 가입
2. "Submit a server" → GitHub URL: `https://github.com/josanku/wehome-insight`
3. 경로: `mcp-server/` 디렉토리 명시
4. 카테고리: "Travel & Tourism" + "Data"

#### ✅ mcp.so 등록
1. https://mcp.so 의 "Submit" 폼
2. 동일 정보 입력

#### ✅ Anthropic 공식 awesome-list PR
1. https://github.com/modelcontextprotocol/servers fork
2. README의 "Community Servers" 섹션에 추가:
   ```
   - [K-STAY](https://github.com/josanku/wehome-insight/tree/main/mcp-server) — Korean accommodation, tourism & culture data (외도민업·한옥·호텔·축제·외국인 통계). By Wehome.
   ```
3. PR 제출

#### ✅ GitHub 토픽·README 보강
- 메인 레포 `wehome-insight` Settings → Topics에 추가:
  `mcp`, `model-context-protocol`, `claude`, `korea`, `tourism`, `hanok`, `lodging`, `open-data`
- README.md 상단에 MCP 배지 추가

### Day 2 — 핵심 커뮤니티 알리기

#### ✅ Reddit 게시
**r/ClaudeAI** (250k+ members):
> 제목: "I built an MCP server for Korean tourism & lodging data (외도민업·한옥·축제)"
> 본문: K-STAY 소개 + Claude Desktop 설정 5초 가이드 + 사용 예시 GIF/스크린샷
> 링크: github.com/josanku/wehome-insight/tree/main/mcp-server

**r/LocalLLaMA** (250k+):
> "Free Korean accommodation & tourism MCP — 50,000+ legal lodging listings"

**r/korea** (150k+):
> "Claude에서 한국 숙박·관광 데이터 자연어로 쓰는 MCP 서버 만들었습니다"

**r/travel** (8M+):
> "Found Korean travel data tool that works with AI chat — 50k+ verified accommodations"

#### ✅ Hacker News 런치
- 제목: "Show HN: K-STAY — MCP server for Korean tourism & lodging (50,000+ listings)"
- 시간대: 한국시간 오후 10~11시 (미국 동부 오전)
- 본문: 핵심 가치 1줄 + 데모 GIF + GitHub 링크 + 출처(행정안전부)

#### ✅ Product Hunt 런치 준비
- https://producthunt.com 에서 Maker 계정 생성
- "K-STAY MCP Server" 등록 (런치는 Day 5에)
- 카피: "AI assistants now know Korean tourism — 50k+ accommodations, festivals, K-culture"

---

## 1주 차 후반: 콘텐츠 자산

### Day 3 — 데모 영상·GIF 제작

**도구**: Loom · QuickTime · OBS · ScreenToGif

**시나리오 영상 (각 30초)**:
1. Claude Desktop에서 "10월 한국 축제 추천" → 자동 답변
2. "서울 한옥 5개 알려줘" → 좌표·이름·설명
3. "외국인 방문객 국가별 추이" → 표·차트
4. "내 주소에서 외도민업 시작 가능?" → 진단

**호스팅**: YouTube + Twitter/X + 본문 임베드

### Day 4 — 블로그 포스트

#### 한국어 (Medium·velog·Tistory)
> 제목: "Claude에 한국 관광 데이터 연결하기 — K-STAY MCP 서버 만든 이야기"
> 내용:
> - 왜 MCP인가? (LLM 도구 표준)
> - 어떻게 만들었나? (Anthropic SDK + REST 래핑)
> - 어떤 데이터? (외도민업 9,922 + 한옥 2,522 + 축제 44 등)
> - 5분 설치 가이드

#### 영어 (dev.to · medium)
> 제목: "Building an MCP server for Korean tourism — 50,000+ data points for LLMs"
> 내용 동일 + 외국인 타깃

### Day 5 — Product Hunt 런치

- 화요일·수요일 오전 0시 (PT) 또는 한국시간 오후 5시
- 사전 알림 가입자 모집 (Twitter·이메일 리스트)
- 런치 당일 친구·동료 upvote 부탁

### Day 6 — Twitter/X 스레드

**한국어 (@wehome_kr 또는 신규 @kstay_ai):**
```
🇰🇷 한국 관광·숙박 데이터를 Claude·Cursor에 연결하는
K-STAY MCP 서버 출시!

📌 외도민업 9,922곳
📌 한옥체험 2,522곳
📌 한옥마을 51 / 명품고택 55
📌 템플스테이 130+
📌 K-Pop·Drama·축제·외국인 통계
📌 100% 무료, 인증 불필요

스레드 ⬇️ (1/8)
```

**영어 (@kstay_ai):**
```
🇰🇷 New MCP server for AI tools (Claude Desktop, Cursor, Continue):

K-STAY brings Korean tourism & lodging data to your LLM workflows.

50,000+ verified listings, hanok villages, K-pop sites, inbound tourism stats.

Free. No API key needed.

🧵 (1/n)
```

### Day 7 — 첫 주 회고 + 측정

- GitHub stars 카운트
- Smithery.ai 다운로드
- Reddit 댓글·질문 수집
- Twitter 멘션

---

## 2-4주 차: 확장

### Discord·Slack 커뮤니티
- **Anthropic Discord** (anthropic.com에서 초대 링크)
  → #showcase 채널에 데모 영상
- **MCP Discord** (https://discord.gg/modelcontextprotocol)
  → 신규 서버 소개
- **한국 IT 슬랙**: KakaoOpenChat 한국 개발자 채널
  → AI/ML 채널에 공유

### 한국 미디어
- **GeekNews** (news.hada.io) — 직접 작성 제출
- **44bits** — 기고 가능
- **Yozm.wishket** — Brunch 형식 글
- **techNeedle** — 기고

### 한국 IT 매체 보도자료
- 디지털타임스·전자신문·아이뉴스24·ZDNet Korea
- 보도자료 형식:
  > "위홈, 한국 관광 데이터를 AI에 연결하는 'K-STAY MCP' 오픈소스 공개"

### 카카오·네이버 기술 블로그 협업
- 네이버 D2 또는 카카오 tech blog 게스트 포스팅 제안
- 주제: "한국 공공데이터 + MCP 사례"

---

## 1-3개월: 깊은 보급

### Anthropic 공식 파트너십 시도
- partnerships@anthropic.com 메일
- 내용: "한국 최초의 정부 데이터 기반 MCP 서버 — Anthropic 한국 진출 시 협력 제안"
- 첨부: GitHub stars 수, Smithery 다운로드 수, 미디어 보도

### KTO (한국관광공사) 협력
- 데이터 정합성 검증 → KTO 공식 권장 도구 등재 시도
- KTO 한국관광 100선·명품고택 갱신 시 자동 연동 제안

### 학술·연구
- 한국관광학회·관광경영학회 학술대회 발표
- 논문: "공공데이터 기반 LLM 도구 통합 사례 — K-STAY MCP"

### 외국인 대상 채널
- **Visit Korea**: KTO 영문 사이트에 노출 요청
- **TimeOut Seoul**: AI 트래블 기사
- **r/korea·r/koreatravel·r/seoul** 정기 업데이트

---

## 측정 지표 (KPI)

| 지표 | 1주 후 목표 | 1개월 후 | 3개월 후 |
|---|---|---|---|
| GitHub Stars | 50 | 300 | 1,000 |
| Smithery 다운로드 | 100 | 1,000 | 5,000 |
| npm 다운로드/주 | - | 500 | 3,000 |
| Twitter Followers | 50 | 500 | 2,000 |
| 미디어 보도 | 1 | 3 | 10 |
| MCP API 호출/일 | 1,000 | 10,000 | 100,000 |

---

## 운영자 체크리스트 (실행할 때 표시)

### 즉시 (Day 1-2):
- [ ] npm publish (`cd mcp-server && npm publish --access public`)
- [ ] Smithery.ai 등록
- [ ] mcp.so 등록
- [ ] anthropic/servers PR
- [ ] GitHub Topics 추가
- [ ] Reddit r/ClaudeAI 게시
- [ ] Hacker News Show HN
- [ ] @kstay_ai Twitter 계정 개설

### 1주차:
- [ ] 데모 영상 4개 (YouTube + Twitter)
- [ ] 한국어 블로그 (Medium·velog)
- [ ] 영어 블로그 (dev.to)
- [ ] Product Hunt 런치

### 2-4주:
- [ ] Discord 커뮤니티 3곳
- [ ] 한국 미디어 보도자료 5곳
- [ ] 카카오·네이버 tech blog 협업 제안

### 1-3개월:
- [ ] Anthropic partnerships@ 메일
- [ ] KTO 협력 미팅
- [ ] 학술 발표 1건

---

## 첨부: 마케팅 카피 (복붙용)

### One-liner
- 한국어: "한국 관광·숙박 데이터를 Claude·Cursor에 즉시 연결하는 첫 한국형 MCP 서버"
- 영문: "The first MCP server connecting Korean tourism & lodging data to AI tools"

### 30초 엘리베이터 피치
> "K-STAY MCP는 한국 외도민업·한옥·호텔·템플스테이·축제·외국인 통계를 Claude나 Cursor 같은 LLM에 즉시 연결하는 오픈소스입니다. 50,000건 이상의 정부 공식 데이터를 16개 자연어 도구로 묶어, 여행자·호스트·연구자·개발자가 한 줄 설정으로 사용할 수 있습니다."

### 2분 데모 스크립트
1. "Claude Desktop을 열고…"
2. "10월 한국 외국인 방문객 통계 보여줘"
3. (Claude가 get_inbound_tourism 호출) — 차트·표 자동 생성
4. "그중 한옥 좋아할 만한 곳 추천해줘"
5. (search_hanok_listings 호출) — 좌표·이름·설명
6. "이거 우리 회사 슬랙봇에 붙이고 싶은데"
7. (Claude가 통합 코드 작성)
8. "끝. 1분 만에 한국 관광 데이터를 AI 워크플로에 통합."

---

## 라이선스·문의

- 이 문서: MIT
- 보도 문의: api@k-stay.ai
- 운영자: wehome, Inc.
