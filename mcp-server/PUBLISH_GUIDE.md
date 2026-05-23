# K-STAY MCP 서버 배포 가이드 (npm + MCP Registry + Smithery)

> 실제 사용자가 `npx -y @k-stay/mcp-server` 한 줄로 설치할 수 있게 만드는 단계별 명령어 모음.

---

## 사전 준비 (각각 한 번씩)

### 1. npm 계정
1. https://www.npmjs.com/signup 에서 계정 생성 (예: `wehome` 또는 `k-stay`)
2. 이메일 인증
3. 2FA 활성화 (선택이지만 권장)

### 2. npm 조직 생성 (`@k-stay` 스코프용)
```bash
# 옵션 A: npm 웹사이트에서
# https://www.npmjs.com/org/create → "k-stay" 입력 (Free)

# 옵션 B: 터미널에서
npm org create k-stay
```

### 3. 로컬에서 npm 로그인
```bash
cd /Users/skyblue/urbanstay/mcp-server
npm login
# 또는: npm adduser
```
브라우저가 열리며 npm 계정 인증.

---

## A. npm 패키지 배포

### 첫 배포
```bash
cd /Users/skyblue/urbanstay/mcp-server
npm install
npm run build

# 최종 확인
ls dist/  # index.js가 있어야 함
node dist/index.js < /dev/null  # 'K-STAY MCP server running' 출력 확인 (Ctrl+C로 종료)

# 배포 (공개)
npm publish --access public
```

성공 시:
```
+ @k-stay/mcp-server@1.0.0
```

이제 누구나 `npx -y @k-stay/mcp-server`로 사용 가능 🎉

### 업데이트 배포
```bash
cd /Users/skyblue/urbanstay/mcp-server
# 1) package.json의 version 수정 (예: 1.0.0 → 1.0.1)
# 또는 자동:
npm version patch   # 1.0.0 → 1.0.1
npm version minor   # 1.0.0 → 1.1.0
npm version major   # 1.0.0 → 2.0.0

npm run build
npm publish
```

---

## B. MCP Server Registry 등록 (공식)

Anthropic이 운영하는 공식 디렉토리. 등록하면 모든 MCP 클라이언트가 자동 발견.

### 1단계: package.json에 mcpName 추가
이미 등록되어 있는지 확인:
```bash
cd mcp-server
cat package.json | grep mcpName
```

없다면 추가 (다음 PR 또는 직접):
```json
{
  "name": "@k-stay/mcp-server",
  "mcpName": "io.github.josanku/k-stay",
  ...
}
```

> 주의: `io.github.<username>/<name>` 형식. GitHub 인증을 위해 일치 필요.

### 2단계: mcp-publisher CLI 설치
```bash
# macOS (Homebrew)
brew install mcp-publisher

# Linux/macOS (수동)
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m).tar.gz" | tar xz
sudo mv mcp-publisher /usr/local/bin/
```

### 3단계: server.json 생성
```bash
cd mcp-server
mcp-publisher init
```
생성된 `server.json`을 수정:
```json
{
  "name": "io.github.josanku/k-stay",
  "description": "Korean tourism, accommodation, and culture data — 50,000+ verified listings (legal homestays, hanok, hotels, festivals, K-Culture, inbound tourism stats)",
  "version": "1.0.0",
  "packages": [{
    "registryType": "npm",
    "identifier": "@k-stay/mcp-server",
    "version": "1.0.0",
    "transport": {"type": "stdio"}
  }],
  "repository": {
    "url": "https://github.com/josanku/wehome-insight",
    "source": "github",
    "subfolder": "mcp-server"
  }
}
```

### 4단계: GitHub 인증
```bash
mcp-publisher login github
```
표시된 코드를 https://github.com/login/device 에 입력.

### 5단계: 배포
```bash
mcp-publisher publish
```

### 6단계: 검증
```bash
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=k-stay"
```

성공 시 등록 확인. 이제 https://registry.modelcontextprotocol.io 에서 검색 가능.

---

## C. Smithery.ai 등록 (커뮤니티 1위 디렉토리)

1. https://smithery.ai/signup → GitHub 로그인
2. 우상단 "Submit Server" 클릭
3. 입력:
   - **GitHub URL**: `https://github.com/josanku/wehome-insight`
   - **Path**: `mcp-server/`
   - **Categories**: `Travel & Tourism`, `Data`, `Open Data`
   - **Tags**: `korea`, `tourism`, `hanok`, `lodging`, `open-data`
   - **Description**: README의 첫 단락 복붙
4. Submit

심사 1-2일 → 승인되면 https://smithery.ai/server/@k-stay/mcp-server 에 등록.

승인 후 본인 페이지에서:
- README 자동 동기화
- 다운로드 통계 확인
- "Install with Smithery CLI" 버튼 자동 활성화

---

## D. mcp.so 등록 (커뮤니티 2위)

1. https://mcp.so/submit
2. GitHub 로그인
3. 동일 정보 입력 (B의 내용과 동일)
4. Submit

---

## E. Anthropic MCP Discord

https://discord.gg/modelcontextprotocol 가입 후 #showcase 채널에 게시:

```
🇰🇷 K-STAY MCP server — Korean tourism data for Claude/Cursor

I just published @k-stay/mcp-server — 50,000+ Korean lodging/tourism/culture data points via 16 native tools.

Try it:
```json
{"mcpServers":{"k-stay":{"command":"npx","args":["-y","@k-stay/mcp-server"]}}}
```

GitHub: github.com/josanku/wehome-insight
Demo: k-stay.ai/developer

Feedback welcome!
```

---

## F. Hacker News Show

준비된 게시물: [POSTS.md](POSTS.md) 의 1번 섹션 참고. 시간대: 한국시간 오후 10-11시 (미 동부 오전 9-10시) 화요일·수요일.

---

## 체크리스트

- [ ] npm 계정 생성 + 2FA
- [ ] `@k-stay` npm 조직 생성
- [ ] `npm login` → `npm publish --access public`
- [ ] `npx -y @k-stay/mcp-server` 외부 환경에서 테스트
- [ ] MCP Registry 등록 (`mcp-publisher publish`)
- [ ] Smithery.ai submit
- [ ] mcp.so submit
- [ ] Anthropic Discord #showcase 게시
- [ ] HN Show HN
- [ ] Reddit r/ClaudeAI
- [ ] Twitter/X 스레드

---

## 문제 해결

### `npm publish` 실패: "402 Payment Required"
조직 패키지(`@k-stay/`)는 무료 계정에서 공개로만 가능. `--access public` 플래그 필수.

### `mcp-publisher publish` 실패: "name mismatch"
`package.json`의 `mcpName`과 `server.json`의 `name`이 정확히 일치해야 합니다.

### Smithery 승인 거부
README가 부족할 수 있음. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)로 보완 → 재제출.

### `npx -y @k-stay/mcp-server` 너무 느림
첫 호출은 다운로드 5-10초. 이후 캐시됨. Claude Desktop의 timeout 늘리려면 `args`에 `--timeout 30000` 추가 가능 (구성에 따라).
