# K-STAY MCP 보급 실행 액션 플랜

> **사용자(운영자)가 직접 해야 할 일을 우선순위별로 정리.** 각 액션의 예상 시간·임팩트·필요 권한 명시.

---

## 🟢 이미 완료된 작업 (제가 처리함)

- ✅ MCP 서버 코드 + 빌드 + 테스트
- ✅ 개발자 허브 페이지 (https://k-stay.ai/developer)
- ✅ REST API 문서 (https://k-stay.ai/docs)
- ✅ 개발자 가이드 + 보급 전략 + 게시물 초안 10개 + 블로그 초안 2개
- ✅ GitHub repo: description · homepage · 14개 topics
- ✅ GitHub Release v1.0.0
- ✅ GitHub Discussions 활성화 + 공지 게시 (#1)
- ✅ sitemap.xml에 신규 페이지 41개 등록
- ✅ MCP Registry 설정 (mcpName · server.json)
- ✅ mcp-publisher CLI 설치
- ✅ OG 이미지 SVG 작성

---

## 🔴 사용자(운영자)가 직접 해야 할 작업

### 🥇 TOP 3 — 가장 큰 임팩트 (오늘 안에)

#### 1. npm publish (소요 15분 · 임팩트 ★★★★★)

사용자 설치 마찰 80% 감소. `npx -y @k-stay/mcp-server` 한 줄 사용 가능.

```bash
# 1) npm 계정 만들기 (한 번)
# https://www.npmjs.com/signup → "wehome" 또는 "k-stay" 사용자 생성

# 2) @k-stay 조직 만들기 (Free)
# https://www.npmjs.com/org/create → "k-stay" 입력

# 3) 로컬에서 로그인 & 배포
cd /Users/skyblue/urbanstay/mcp-server
npm login            # 브라우저 인증
npm publish --access public

# 4) 검증 (15초)
npx -y @k-stay/mcp-server < /dev/null
# 'K-STAY MCP server running · API base: https://k-stay.ai' 출력 확인
```

#### 2. MCP Registry 등록 (소요 10분 · 임팩트 ★★★★★)

Anthropic 공식 디렉토리. 모든 MCP 클라이언트가 자동 발견.

> ⚠️ npm publish 완료 후에 진행

```bash
cd /Users/skyblue/urbanstay/mcp-server

# 이미 server.json 작성됨. 인증 후 publish만 하면 됨.
mcp-publisher login github
# 브라우저 열림 → 코드 입력

mcp-publisher publish

# 검증
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=k-stay"
```

#### 3. Hacker News Show HN (소요 5분 · 임팩트 ★★★★★)

잘 되면 24시간 내 GitHub stars 100-500개 가능.

**시간**: 한국시간 화/수 **오후 10-11시** (미 동부 오전 9-10시) — 트래픽 최대 시간

**제출**: https://news.ycombinator.com/submit

**제목**:
```
Show HN: K-STAY MCP – Korean tourism & lodging data in Claude/Cursor (50k+ items)
```

**본문**: `mcp-server/POSTS.md` 의 "1. Hacker News (Show HN)" 섹션 복붙

**팁**: 게시 후 1-2시간 댓글에 빠르게 답변하면 frontpage 도달 확률↑

---

### 🥈 1주차 — 콘텐츠 자산 + 커뮤니티 (총 2-3시간)

#### 4. Smithery.ai 등록 (소요 10분 · 임팩트 ★★★★)
- https://smithery.ai/signup → GitHub 로그인
- "Submit Server" → GitHub URL: `https://github.com/josanku/wehome-insight`, Path: `mcp-server/`
- 1-2일 후 승인 → 매주 자동 다운로드 발생

#### 5. mcp.so 등록 (소요 5분 · 임팩트 ★★★)
- https://mcp.so/submit → 동일 정보 입력

#### 6. Reddit r/ClaudeAI 게시 (소요 5분 · 임팩트 ★★★★)
- POSTS.md의 "2. Reddit · r/ClaudeAI" 섹션 복붙
- **시간**: 미 동부 오전 8-10시 (한국시간 저녁 9-11시)
- 250k 멤버 노출

#### 7. Reddit r/korea 게시 (소요 5분 · 임팩트 ★★★)
- POSTS.md의 "4. Reddit · r/korea" 섹션 복붙
- 한국 사용자·개발자 노출

#### 8. Twitter/X 스레드 (소요 20분 · 임팩트 ★★★★)
- 한국어 8개 + 영문 6개 스레드 POSTS.md에 있음
- @k-stay_ai 또는 @wehome 계정으로 게시
- Anthropic 공식 (@anthropicai) 멘션하면 RT 가능성

#### 9. Anthropic MCP Discord (소요 5분 · 임팩트 ★★★)
- https://discord.gg/modelcontextprotocol 가입
- #showcase 채널에 POSTS.md "7. Anthropic Discord" 섹션 복붙

#### 10. 블로그 게시 (소요 15분 × 2 · 임팩트 ★★★)
- 한국어: `mcp-server/blog/blog-ko-medium.md` → Medium 또는 velog
- 영문: `mcp-server/blog/blog-en-devto.md` → dev.to

#### 11. OG 이미지 PNG 변환 (소요 5분)
SVG 그대로도 작동하지만 일부 플랫폼은 PNG만 인식:
```bash
# Inkscape 또는 온라인 변환 도구로 og-image.svg → og-image.png 변환
# https://cloudconvert.com/svg-to-png
# 또는: brew install librsvg && rsvg-convert -w 1200 og-image.svg > og-image.png
```
완성된 PNG를 프로젝트 루트에 저장 후 commit.

---

### 🥉 2-4주차 — 확장 (선택)

#### 12. Product Hunt 런치 (소요 1시간 준비 + 24시간 모니터링)
- 화/수 0시 PT (한국시간 오후 5시)
- POSTS.md "10. Product Hunt 등록" 섹션 참고
- 친구·동료 upvote 부탁 (사전 알림 가입자)

#### 13. LinkedIn (소요 5분)
- POSTS.md "8. LinkedIn" 섹션 복붙
- 한국 IT/관광 업계 노출

#### 14. GeekNews (소요 5분)
- https://news.hada.io 가입 → POSTS.md "9. GeekNews" 섹션 복붙

#### 15. 한국 미디어 보도자료 (소요 1시간)
- 디지털타임스·전자신문·아이뉴스24·ZDNet Korea·테크니들
- 보도자료 형식 + 위홈 공식 입장

#### 16. Anthropic 파트너십 메일 (소요 30분)
- partnerships@anthropic.com
- 1-2주 후 GitHub stars 수·다운로드 수 모일 때 보내야 효과적
- 메일 내용: PROMOTION.md "Anthropic 파트너십 시도" 섹션 참조

#### 17. KTO (한국관광공사) 협력 (소요 1시간)
- KTO 데이터랩 담당자에게 협력 제안 메일
- "한국 관광 데이터의 AI 인터페이스 첫 사례 — 공식 협력 제안"

---

## 📊 측정 지표 (체크)

매주 일요일 점검:

| 지표 | 1주 목표 | 1개월 | 3개월 |
|---|---|---|---|
| GitHub Stars | 50 | 300 | 1,000 |
| npm 다운로드/주 | 50 | 500 | 3,000 |
| MCP Registry 노출 | ✓ | ✓ | ✓ |
| Smithery 다운로드 | 100 | 1,000 | 5,000 |
| 미디어 보도 | 1 | 3 | 10 |
| API 호출/일 | 1,000 | 10,000 | 100,000 |

확인 명령어:
```bash
# GitHub stars
gh api repos/josanku/wehome-insight --jq .stargazers_count

# npm 다운로드 (publish 후)
curl https://api.npmjs.org/downloads/point/last-week/@k-stay/mcp-server
```

---

## 🚨 막힐 때 대처

### "npm publish 실패: 402 Payment Required"
조직 패키지(@k-stay/...)는 무료 계정에서 **public**으로만 가능. `--access public` 플래그 필수.

### "mcp-publisher publish 실패: name mismatch"
`package.json`의 `mcpName`과 `server.json`의 `name`이 정확히 일치하지 않을 때.
이미 둘 다 `io.github.josanku/k-stay`로 설정되어 있으니 문제 없을 것.

### "Smithery 승인 거부"
README 부족. 이미 DEVELOPER_GUIDE.md가 풍부하니 README 첫 단락만 강화해 재제출.

### "HN frontpage 못 감"
첫 1-2시간 댓글 활동이 중요. 게시 직후 1시간 동안 모니터링 + 빠른 답변.

### "Reddit 자동 삭제"
스팸 필터에 걸릴 수 있음. 게시 30분 후 표시 안 되면 mod에게 메시지.

---

## 💡 가장 효과적인 순서 (오늘 시작 가능)

**오늘 (1시간):**
1. npm 계정 + 조직 생성 (10분)
2. `npm publish --access public` (5분)
3. MCP Registry `mcp-publisher publish` (10분)
4. Smithery 제출 (10분)
5. Hacker News 게시 — 한국시간 오후 10시 (5분)

**1일 후 (1시간):**
- Reddit r/ClaudeAI + r/korea
- Twitter 스레드 한·영
- Anthropic Discord

**1주 후:**
- 블로그 2개
- Product Hunt
- 결과 측정

---

## 📞 도움 요청

각 단계에서 막히는 부분이 있으면:
1. `mcp-server/PUBLISH_GUIDE.md` 문제 해결 섹션 참조
2. `mcp-server/DEVELOPER_GUIDE.md` 트러블슈팅 참조
3. 또는 Claude Code에서 "[액션명] 실행 중 [오류 메시지] 발생" 입력 → 도움 받기

**한 시간만 투자하면 v1.0.0의 인지도가 완전히 달라집니다.**
