# K-STAY MCP Server · 개발자 가이드 (완전판)

> **0부터 시작하는 단계별 가이드.** Claude Desktop·Claude Code·Cursor에서 한국 숙박·관광·문화 데이터를 자연어로 사용하세요.

---

## 목차

1. [MCP가 뭐고 왜 쓰나?](#1-mcp가-뭐고-왜-쓰나)
2. [사전 준비 (Node.js 설치)](#2-사전-준비)
3. [Claude Desktop에 K-STAY 연결](#3-claude-desktop에-k-stay-연결-가장-쉬움)
4. [Claude Code (CLI)에 K-STAY 연결](#4-claude-code-cli에-k-stay-연결)
5. [Cursor·기타 도구에 연결](#5-cursor기타-도구에-연결)
6. [실제 사용 시나리오 7가지](#6-실제-사용-시나리오-7가지)
7. [도구 16개 상세 레퍼런스](#7-도구-16개-상세-레퍼런스)
8. [트러블슈팅](#8-트러블슈팅)
9. [개발자 기여 가이드](#9-개발자-기여-가이드)

---

## 1. MCP가 뭐고 왜 쓰나?

**MCP (Model Context Protocol)** 는 Anthropic이 2024년 11월에 공개한 오픈 표준입니다. LLM이 외부 데이터·도구를 **native 함수처럼** 호출할 수 있게 해줍니다.

### MCP 없이 vs MCP 있을 때

**❌ MCP 없이** (WebFetch / 수동 curl)
```
사용자: "한옥체험업 통계 알려줘"
Claude: (WebFetch로 https://k-stay.ai/api/hanok/stats 가져옴)
        → 응답을 파싱하고 분석
        → 비효율적, 매번 URL 입력 필요
```

**✅ MCP 있을 때**
```
사용자: "한옥체험업 통계 알려줘"
Claude: get_hanok_stats() 호출 (자동, 0.5초)
        → 결과를 직접 분석
        → URL·인자·파싱 모두 자동
```

### 누가 써야 하나?

- ✨ **여행자**: "10월 한국 가는데 좋은 축제 알려줘" → 즉시 매칭 답변
- 🏠 **공유숙박 호스트**: "내 주소 주변 경쟁 호스트 수" → 진단 즉시
- 📊 **연구자·기자**: "외국인 방문객 국가별 추이" → 데이터 즉시 분석
- 💻 **개발자**: 본인 앱에서 K-STAY 데이터 사용. CLI·API 모두 가능

---

## 2. 사전 준비

### Node.js 설치 (한 번만)

K-STAY MCP는 Node.js로 동작합니다. **Node.js 18 이상** 필요.

**macOS:**
```bash
# Homebrew 있으면
brew install node

# 없으면 https://nodejs.org 에서 LTS 다운로드
```

**Windows:**
- https://nodejs.org 에서 LTS 인스톨러 다운로드 → 실행
- 또는 PowerShell에서:
  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**설치 확인:**
```bash
node --version   # v20.x 또는 v18.x 이상이어야 함
npm --version
```

---

## 3. Claude Desktop에 K-STAY 연결 (가장 쉬움)

### 3-1. Claude Desktop 다운로드
https://claude.ai/download 에서 macOS·Windows용 앱 설치.

### 3-2. 설정 파일 열기

**macOS:**
```bash
# 터미널에서:
open ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 파일이 없으면:
mkdir -p ~/Library/Application\ Support/Claude
echo '{"mcpServers":{}}' > ~/Library/Application\ Support/Claude/claude_desktop_config.json
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
- 탐색기 주소창에 `%APPDATA%\Claude\` 입력 → Enter
- `claude_desktop_config.json` 파일 메모장으로 열기 (없으면 새로 만들기)

### 3-3. K-STAY 추가

방법 A — **npm 패키지 사용** (publish 완료 후):
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

방법 B — **로컬 빌드** (현재 권장):
```bash
# 터미널에서:
git clone https://github.com/josanku/wehome-insight.git ~/k-stay
cd ~/k-stay/mcp-server
npm install
npm run build
pwd   # 이 경로 복사
```

설정 파일에:
```json
{
  "mcpServers": {
    "k-stay": {
      "command": "node",
      "args": ["/Users/YOUR_NAME/k-stay/mcp-server/dist/index.js"]
    }
  }
}
```

> ⚠️ Windows의 경우 백슬래시는 두 번: `"C:\\Users\\YOU\\k-stay\\..."`

### 3-4. Claude Desktop 재시작

완전 종료 (Cmd+Q 또는 작업관리자에서 종료) → 다시 실행.

### 3-5. 연결 확인

채팅 입력란 옆에 🔌 **MCP 아이콘**이 생겼다면 성공. 클릭하면 K-STAY 도구 16개 목록 표시.

테스트:
```
한국 한옥체험업이 가장 많은 시군구 5곳 알려줘
```
Claude가 자동으로 `get_hanok_stats` 호출 → 결과 표시.

---

## 4. Claude Code (CLI)에 K-STAY 연결

### 4-1. Claude Code 설치
```bash
npm install -g @anthropic-ai/claude-code
```

### 4-2. MCP 서버 추가

방법 A — **사용자 전역 (모든 프로젝트)**:
```bash
claude mcp add k-stay -- npx -y @k-stay/mcp-server
```

방법 B — **프로젝트 단위** (`.mcp.json` 만들기):
```bash
cd my-project
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "k-stay": {
      "command": "npx",
      "args": ["-y", "@k-stay/mcp-server"]
    }
  }
}
EOF
```

방법 C — **로컬 빌드**:
```bash
claude mcp add k-stay -- node ~/k-stay/mcp-server/dist/index.js
```

### 4-3. 사용
```bash
claude
> 서울 한옥체험업 영업장 10개 알려줘. 그중 종로구만 따로 표시
```
Claude Code가 `search_hanok_listings` 호출 → 결과 표시.

### 4-4. 도구 활성화 확인
```bash
claude
> /mcp
```
K-STAY 16개 도구가 리스트에 나오면 OK.

---

## 5. Cursor·기타 도구에 연결

### Cursor
**Settings → Features → MCP Servers**에서 "Add new MCP server":
- Name: `k-stay`
- Type: `command`
- Command: `npx -y @k-stay/mcp-server`

### Cline (VS Code)
`.vscode/cline_mcp_settings.json`:
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

### Continue.dev
config에 `mcpServers` 추가, 위와 동일 형식.

---

## 6. 실제 사용 시나리오 7가지

### 🧳 시나리오 1: 한국 여행자
> "10월에 한국 갈건데, 외국인이 좋아할 만한 축제 3개랑 그 근처 한옥숙박 추천해줘"

**Claude의 동작:**
1. `get_festivals(month=10)` → 진주남강유등 280만명, 안동탈춤 150만명, 부산국제영화제 20만명
2. 각 축제 위치 인근 한옥체험업 검색:
   - `search_hanok_listings(sido='경상북도', sigungu='안동시', limit=5)`
   - `search_hanok_listings(sido='경상남도', sigungu='진주시', limit=5)`
3. 통합 답변 생성

**결과 미리보기:**
```
🎊 10월 한국 외국인 추천 축제 3선:
1. 진주남강유등축제 (10/1-15, 280만명) — 임진왜란 진주성 전투 기원
   → 인근 한옥: 진주 OO한옥체험관 (위치 좌표)
2. 안동국제탈춤페스티벌 (9/26-10/5, 150만명) — UNESCO 연계
   → 인근 한옥: 안동 하회마을 충효당 종택, 양진당 종택
3. 부산국제영화제 (10/2-11, 20만명) — 아시아 최대
   → 부산 한옥은 적음, 대신 해운대·광안리 호텔 추천
```

### 🏠 시나리오 2: 예비 공유숙박 호스트
> "내가 마포구에서 외도민업 시작하려는데, 현재 영업중 호스트가 몇 명이고 신규 등록 추이는?"

**Claude의 동작:**
1. `get_stats(sido='서울특별시')` → 마포구 영업 호스트 수
2. `get_registrations_monthly(year='2026', sidos='서울특별시')` → 월별 추이
3. 시장 포화도·기회 분석

### 📊 시나리오 3: 데이터 저널리스트
> "코로나 이전과 비교해서 외국인 관광객 회복률을 국가별로 분석해줘"

**Claude의 동작:**
1. `get_inbound_tourism()` → 2019-2025 연간 + 국가별 yoy
2. 회복률 계산 (2025/2019)
3. CSV 또는 마크다운 표로 출력

**결과 미리보기:**
```
2019년 대비 2025년 회복률:
- 중국: 472만/602만 = 78% 회복 (정치 영향)
- 일본: 345만/327만 = 105% 회복 ✅
- 베트남: 62만/55만 = 113% 회복 ✅ (K-pop 효과)
- 미국: 129만/104만 = 124% 회복 ✅
- 인도: 18만/14만 = 129% 회복 ✅✅
```

### 🏯 시나리오 4: 한옥 마니아
> "보물로 지정된 한옥 종택만 알려줘. 종부가 직접 운영하는 곳 우선"

**Claude의 동작:**
1. `get_meongpum_gotaek()` → 55곳 명품고택
2. `cultural_property` 필드에서 "보물 제..." 필터
3. `experiences`에 "종부 이야기" 있는 곳 우선 정렬

### 🎬 시나리오 5: K-Pop 팬 (외국인)
> "I'm a BTS fan visiting Seoul. Where should I go?"

**Claude의 동작:**
1. `get_kculture_hotspots()` → HYBE 사옥·BTS 마이크드롭 신촌·제주 BTS 인 더 숲 등
2. K-Pop fandom=ARMY 필터
3. 동선 추천

### 💻 시나리오 6: 개발자 (앱 빌딩)
> "Next.js 프로젝트에서 한옥 지도 만들고 싶어. API 호출 코드 짜줘"

**Claude의 동작:**
1. `get_hanok_villages()` 호출해 데이터 구조 파악
2. `search_hanok_listings(limit=500)` 호출해 좌표 확인
3. Next.js + Kakao Maps 통합 코드 생성:
```javascript
// app/hanok/page.tsx
export default async function HanokPage() {
  const villages = await fetch('https://k-stay.ai/api/hanok/villages').then(r=>r.json());
  return <Map markers={villages.villages} />;
}
```

### 📚 시나리오 7: 연구자 (학술 논문)
> "한옥체험업의 연도별 등록 추이를 그래프로 그릴 수 있는 데이터 줘"

**Claude의 동작:**
1. `get_hanok_stats()` → `by_year` 필드에서 2018-2026 연간 등록
2. Python pandas/matplotlib 코드 또는 CSV 출력
3. 학술 인용 형식: "Data from K-STAY (k-stay.ai) · 행정안전부 인허가 데이터, 2026"

---

## 7. 도구 16개 상세 레퍼런스

### 메타·통계 (5개)

#### `get_stats`
**용도**: 외도민업 종합 통계
**인자**: `sido` (선택), `category` (선택, default: foreigner_city_homestays)
**예시**: `get_stats(sido="서울특별시")` → 서울 외도민업 6,161곳 영업중

#### `get_categories_overview`
**용도**: 5종 합법 숙박 카테고리 통계 일괄
**인자**: 없음
**반환**: 외도민업·한옥체험·관광숙박·농어촌·관광펜션 영업 개수

#### `get_registrations_monthly`
**용도**: 월간 신규 등록 추이
**인자**: `year` (default: 2026), `sidos` (default: '서울특별시,부산광역시')

#### `get_data_sources`
**용도**: 모든 데이터 출처·갱신 주기·대체 후보 카탈로그
**인자**: 없음

#### `get_monthly_report`
**용도**: 월간 시장 리포트
**인자**: `ym` (YYYY-MM, 없으면 최신)

### 한옥 (4개)

#### `get_hanok_stats`
**용도**: 한옥체험업 통계 (2,522곳 영업중)

#### `search_hanok_listings`
**용도**: 한옥체험업 영업장 검색
**인자**: `sido`, `sigungu`, `limit` (max 5000, default 100)

#### `get_hanok_villages`
**용도**: 한옥마을 51곳 (UNESCO·민속마을·보존지구)

#### `get_meongpum_gotaek`
**용도**: KTO 명품고택 55곳

### 숙박 카테고리 (3개)

#### `get_temple_stays`
**용도**: 템플스테이 사찰 130+곳

#### `search_lodging`
**용도**: 호텔/호스텔/농어촌/펜션 영업장 검색
**인자**: `kind` (필수), `sido`, `sigungu`, `limit`

#### `get_lodging_stats`
**용도**: 카테고리별 통계
**인자**: `kind` (필수)

### 관광·문화 (4개)

#### `get_inbound_tourism`
**용도**: 외국인 관광객 통계 (월별·연도별·국가별·목적·연령)

#### `get_kculture_hotspots`
**용도**: K-Culture 핫스팟 35곳

#### `get_korea100`
**용도**: 한국관광 100선 (연도별)

#### `get_festivals`
**용도**: 전국 축제 캘린더 44개
**인자**: `month` (1~12, 없으면 전체)

---

## 8. 트러블슈팅

### Claude Desktop에 🔌 아이콘이 안 보임
1. 설정 파일 JSON 문법 검사: https://jsonlint.com
2. Claude Desktop 완전 종료 (Cmd+Q) 후 재시작
3. 로그 확인: `~/Library/Logs/Claude/mcp*.log`

### "Cannot find module" 오류
- `npm install`이 실패했을 수 있음
- `cd mcp-server && npm install && npm run build` 재실행

### Korean 응답이 깨짐
- 터미널 encoding 확인: `export LANG=ko_KR.UTF-8`

### API가 느림
- 첫 호출은 cold start. 이후 5분간 캐시 (Cache-Control: max-age=300)

### 데이터가 오래됨
- DB 데이터는 매일 04:00 KST 자동 갱신 (D-2 기준)
- 즉시 최신화 필요 시: `curl https://k-stay.ai/api/data-sources`로 last_update 확인

---

## 9. 개발자 기여 가이드

### 신규 도구 추가
1. `src/index.ts`의 `TOOLS` 배열에 도구 정의 추가
2. `setRequestHandler(CallToolRequestSchema, ...)`에 핸들러 추가
3. `npm run build`
4. PR 제출

### 새 K-STAY API 엔드포인트 노출
1. K-STAY 본 레포(`server.py`)에 엔드포인트 추가
2. `openapi.json`에 스펙 추가
3. MCP 도구 추가 (위)

### 버그 신고
GitHub Issues: https://github.com/josanku/wehome-insight/issues

---

## 라이선스 · 문의

- 라이선스: MIT (코드) / 공공누리 제4유형 (데이터)
- 이메일: api@k-stay.ai
- GitHub: https://github.com/josanku/wehome-insight
- 공식 문서: https://k-stay.ai/docs
