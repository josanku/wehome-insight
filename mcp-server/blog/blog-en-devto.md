---
title: "Building an MCP server for Korean tourism — 50,000+ data points for LLMs"
published: false
description: "How we wrapped Korean public data into an MCP server so Claude, Cursor, and other AI tools can natively access tourism, lodging, and culture data with natural language."
tags: mcp, claude, opendata, korea
canonical_url: https://k-stay.ai/developer
cover_image: https://k-stay.ai/og-image.png
---

# Building an MCP server for Korean tourism — 50,000+ data points for LLMs

> Free, open-source MCP server connecting Korean accommodation, tourism, and culture data to Claude Desktop, Cursor, and any MCP-compatible AI tool. No API key needed.

## TL;DR

We built [@k-stay/mcp-server](https://github.com/josanku/wehome-insight/tree/main/mcp-server) — an open-source [Model Context Protocol](https://modelcontextprotocol.io) server that gives LLMs native access to:

- **9,922** legal Korean homestays
- **2,522** hanok (traditional house) experiences  
- **130+** temple stays
- **44** major festivals
- **35** K-Culture hotspots (K-Pop, K-Drama, K-Food, K-Beauty)
- **Inbound tourism stats** by country/month/purpose (KTO + Ministry of Justice)
- And more — total ~50,000+ verified data points

All from Korean government open data, refreshed daily. 16 tools, fully typed.

## Why MCP?

LLM clients (Claude, Cursor, Continue, Cline) needed a standard way to call external tools. [MCP](https://modelcontextprotocol.io), released by Anthropic in Nov 2024, has quickly become that standard. Write once → works everywhere.

Korean public data is a goldmine but underutilized:
- The [Korean Government Open Data Portal](https://www.localdata.go.kr) publishes daily-updated CSVs of every legal lodging in Korea
- Yet AI assistants can't access this directly because of CORS, encoding, and parsing barriers

→ Solve this with one MCP server, and Claude/Cursor instantly know Korean tourism.

## Architecture

```
User: "Recommend October festivals in Korea + nearby hanok stays"
   ↓
Claude Desktop
   ↓ MCP stdio
@k-stay/mcp-server (TypeScript)
   ↓ HTTP fetch
k-stay.ai REST API (Python/Flask)
   ↓
SQLite + Curated JSON (refreshed daily)
   ↓
Korean Government Open Data
```

## Code

The whole MCP server is ~250 lines of TypeScript. Highlights:

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const TOOLS = [
  {
    name: "get_hanok_stats",
    description: "Korean hanok (traditional house) experience industry stats (2,522 active)",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "search_hanok_listings",
    description: "Search Korean hanok experience businesses with coordinates (for maps)",
    inputSchema: {
      type: "object",
      properties: {
        sido: { type: "string", description: "Province filter" },
        sigungu: { type: "string", description: "City/county filter" },
        limit: { type: "integer", default: 100 },
      },
    },
  },
  // ... 14 more
];

const server = new Server(
  { name: "k-stay", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // Map tool name → REST endpoint
  const data = await fetch(`https://k-stay.ai/api/${routeFor(name)}`, { ... });
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

await server.connect(new StdioServerTransport());
```

[Full source on GitHub](https://github.com/josanku/wehome-insight/blob/main/mcp-server/src/index.ts)

## Installation (5 min)

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

Restart Claude Desktop. Done.

### Claude Code
```bash
claude mcp add k-stay -- npx -y @k-stay/mcp-server
```

### Cursor / Cline / Continue
Same pattern with their respective MCP config files.

## Example Conversations

> **User**: "Which sigungu (district) has the most hanok experiences? Top 5"
>
> **Claude**: *calls `get_hanok_stats`* → Gyeongju 363, Jongno-gu (Bukchon) 332, Jeonju 298, Andong 184, Suncheon 74

> **User**: "I'm visiting Korea in October. Recommend foreigner-friendly festivals and hanok nearby"
>
> **Claude**: *calls `get_festivals(month=10)`* + `search_hanok_listings(sido='경상북도', sigungu='안동시')` → produces ranked list with coordinates and descriptions

> **User**: "Recovery rate of Chinese tourists vs 2019"
>
> **Claude**: *calls `get_inbound_tourism`* → "China is at 78% of pre-COVID levels, while Japan recovered to 105%..."

## Why this matters

**For developers**: Build apps using Korean travel data without parsing CSVs. Type-safe, cached, free.

**For travelers**: Ask Claude naturally — "Where should I go for cherry blossoms next April?" instead of clicking through 5 government websites.

**For researchers**: Pull tourism data in 1 second instead of 1 hour.

**For Korea**: Public data finally usable by AI.

## What I learned

1. **MCP is becoming the standard for LLM tool integration.** OpenAI's function calling and Anthropic's tool use were each model-specific. MCP is client-server, so the same server works across Claude, Cursor, Cline, Continue, etc.

2. **Wrapping REST → MCP is trivial.** If you have OpenAPI 3.0 spec, you can generate the MCP server in 1-2 days. Way easier than I expected.

3. **Public data + LLM = huge unlock.** Government open data has been around for a decade but few people use it. MCP servers make it accessible to anyone who can use Claude.

## Try it

- 🌐 [https://k-stay.ai](https://k-stay.ai)
- 📘 [Developer guide](https://k-stay.ai/developer)
- 📡 [REST API docs](https://k-stay.ai/docs)
- 🐙 [GitHub (please star!)](https://github.com/josanku/wehome-insight)

K-STAY is operated by Wehome — Korea's first certified legal home sharing platform.

---

**If you build MCP servers for your own public data**, share with me at [api@k-stay.ai](mailto:api@k-stay.ai). I'd love to learn from your approach.
