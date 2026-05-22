#!/usr/bin/env node
/**
 * K-STAY MCP Server
 *
 * Claude Desktop / Claude Code에서 한국 숙박·관광·문화 데이터를
 * native 도구처럼 호출할 수 있게 해주는 MCP 서버.
 *
 * Base API: https://k-stay.ai/api
 * Docs:     https://k-stay.ai/docs
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

const API_BASE = process.env.K_STAY_API_BASE || "https://k-stay.ai";

// ─── 도구 정의 ────────────────────────────────────────────────
const TOOLS = [
  {
    name: "get_stats",
    description:
      "한국 외국인관광도시민박업(외도민업) 종합 통계 — 영업/휴업/폐업 개수, 시군구 분포, 마지막 갱신일. 시도·카테고리 필터 가능.",
    inputSchema: {
      type: "object",
      properties: {
        sido: { type: "string", description: "시도명 (예: 서울특별시, 부산광역시)" },
        category: {
          type: "string",
          description: "카테고리 코드 — foreigner_city_homestays(default) / hanok_experience / tourist_accommodations / rural_homestays / tourist_pensions / all",
        },
      },
    },
  },
  {
    name: "get_categories_overview",
    description: "한국 5종 합법 숙박 카테고리(외도민업·한옥체험업·관광숙박업·농어촌민박·관광펜션업) 통계 요약을 한 번에.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_registrations_monthly",
    description: "지역별 월간 신규 외도민업 등록 추이. 서울·부산 등 비교용.",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "string", description: "4자리 연도 (default: 2026)" },
        sidos: { type: "string", description: "콤마구분 시도 (default: '서울특별시,부산광역시')" },
      },
    },
  },
  {
    name: "get_hanok_stats",
    description: "한국 한옥체험업 종합 통계 (전국 2,522곳 영업중). 시도별/시군구별 분포 + 연도별 신규 등록 추이.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "search_hanok_listings",
    description: "한국 한옥체험업 영업장 검색 — 좌표·이름·주소 반환. 시도/시군구 필터, 카카오맵 마커 생성에 적합.",
    inputSchema: {
      type: "object",
      properties: {
        sido: { type: "string", description: "시도 필터 (예: 경상북도)" },
        sigungu: { type: "string", description: "시군구 필터 (예: 경주시)" },
        limit: { type: "integer", description: "최대 5000, 기본 100", default: 100 },
      },
    },
  },
  {
    name: "get_hanok_villages",
    description: "한국 한옥마을 51곳 큐레이션 — 북촌·전주·안동 하회·경주 양동 등 보존지구·민속마을·UNESCO 유산.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_meongpum_gotaek",
    description: "한국관광공사 명품고택 55곳 — 임청각·운조루·선교장 등 보물·국가민속문화재 등급 종택.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_temple_stays",
    description: "한국 템플스테이 운영 사찰 130+곳 — 통도사·해인사·송광사 등 조계종 본사 + 비구니 본사 + 주요 사찰.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "search_lodging",
    description: "한국 숙박 카테고리별 영업장 검색 — 호텔/호스텔/농어촌민박/관광펜션. 좌표 포함 카카오맵 마커용.",
    inputSchema: {
      type: "object",
      properties: {
        kind: { type: "string", enum: ["hotel", "hostel", "rural", "pension"], description: "카테고리" },
        sido: { type: "string" },
        sigungu: { type: "string" },
        limit: { type: "integer", default: 100, description: "최대 5000" },
      },
      required: ["kind"],
    },
  },
  {
    name: "get_lodging_stats",
    description: "한국 숙박 카테고리별 통계 — 호텔/호스텔/농어촌/관광펜션의 영업중 개수·시도 분포.",
    inputSchema: {
      type: "object",
      properties: {
        kind: { type: "string", enum: ["hotel", "hostel", "rural", "pension"] },
      },
      required: ["kind"],
    },
  },
  {
    name: "get_inbound_tourism",
    description:
      "한국 외국인 관광객 통계 — 2025년 1,876만명, 월별·연도별·국가별·목적별·연령·체류기간. KTO 데이터랩 + 법무부 출입국 통계 기반.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_kculture_hotspots",
    description:
      "K-Culture 핫스팟 35곳 — K-Pop(HYBE·SM·JYP·YG 사옥)·K-Drama 촬영지·K-Food(광장시장·명동)·K-Beauty(강남·명동).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_korea100",
    description: "한국관광공사 한국관광 100선 (연도별) — KTO 격년 발표 공식 명단.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_festivals",
    description: "전국 주요 축제 캘린더 44개 — 진해 군항제·보령머드·부산국제영화제·서울 불꽃축제 등. 월별·카테고리별 분류.",
    inputSchema: {
      type: "object",
      properties: {
        month: { type: "integer", description: "1~12 월. 없으면 전체", minimum: 1, maximum: 12 },
      },
    },
  },
  {
    name: "get_data_sources",
    description:
      "K-STAY의 모든 데이터 출처·갱신 주기·대체 후보 카탈로그. 데이터 신뢰도 확인용.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_monthly_report",
    description: "한국 공유숙박 월간 시장 리포트 — 매월 25일 발행. ym 인자가 없으면 최신 호.",
    inputSchema: {
      type: "object",
      properties: {
        ym: { type: "string", description: "YYYY-MM 형식 (예: 2026-05). 없으면 최신" },
      },
    },
  },
];

// ─── 헬퍼 ─────────────────────────────────────────────────────
async function fetchJson(path: string, params?: Record<string, string | number | undefined>): Promise<unknown> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString(), {
    headers: { "User-Agent": "k-stay-mcp/1.0", Accept: "application/json" },
  });
  if (!res.ok) {
    throw new McpError(ErrorCode.InternalError, `K-STAY API ${path} → HTTP ${res.status}`);
  }
  return res.json();
}

function asText(data: unknown): { type: "text"; text: string } {
  return { type: "text", text: JSON.stringify(data, null, 2) };
}

// ─── MCP 서버 ─────────────────────────────────────────────────
const server = new Server(
  { name: "k-stay", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = (args ?? {}) as Record<string, unknown>;

  try {
    switch (name) {
      case "get_stats":
        return { content: [asText(await fetchJson("/api/stats", { sido: a.sido as string, category: a.category as string }))] };

      case "get_categories_overview":
        return { content: [asText(await fetchJson("/api/categories"))] };

      case "get_registrations_monthly":
        return { content: [asText(await fetchJson("/api/registrations/monthly", { year: a.year as string, sidos: a.sidos as string }))] };

      case "get_hanok_stats":
        return { content: [asText(await fetchJson("/api/hanok/stats"))] };

      case "search_hanok_listings":
        return { content: [asText(await fetchJson("/api/hanok/listings", { sido: a.sido as string, sigungu: a.sigungu as string, limit: (a.limit as number) ?? 100 }))] };

      case "get_hanok_villages":
        return { content: [asText(await fetchJson("/api/hanok/villages"))] };

      case "get_meongpum_gotaek":
        return { content: [asText(await fetchJson("/api/hanok/meongpum"))] };

      case "get_temple_stays":
        return { content: [asText(await fetchJson("/api/temple"))] };

      case "search_lodging":
        return { content: [asText(await fetchJson("/api/lodging/listings", { kind: a.kind as string, sido: a.sido as string, sigungu: a.sigungu as string, limit: (a.limit as number) ?? 100 }))] };

      case "get_lodging_stats":
        return { content: [asText(await fetchJson("/api/lodging/stats", { kind: a.kind as string }))] };

      case "get_inbound_tourism":
        return { content: [asText(await fetchJson("/api/tourism/inbound"))] };

      case "get_kculture_hotspots":
        return { content: [asText(await fetchJson("/api/culture/hotspots"))] };

      case "get_korea100":
        return { content: [asText(await fetchJson("/api/korea100"))] };

      case "get_festivals": {
        const data = (await fetchJson("/api/festivals")) as { festivals: Array<{ period_start?: string }> };
        if (a.month && data.festivals) {
          const m = Number(a.month);
          data.festivals = data.festivals.filter((f) => Number((f.period_start ?? "").split("-")[0]) === m);
        }
        return { content: [asText(data)] };
      }

      case "get_data_sources":
        return { content: [asText(await fetchJson("/api/data-sources"))] };

      case "get_monthly_report": {
        const ym = a.ym as string | undefined;
        const path = ym ? `/api/report/${ym}` : "/api/report/latest";
        return { content: [asText(await fetchJson(path))] };
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (err) {
    if (err instanceof McpError) throw err;
    const msg = err instanceof Error ? err.message : String(err);
    throw new McpError(ErrorCode.InternalError, `K-STAY tool error: ${msg}`);
  }
});

// ─── 기동 ─────────────────────────────────────────────────────
async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // stderr로 안내 (stdout은 MCP 프로토콜 전용)
  process.stderr.write(`K-STAY MCP server running · API base: ${API_BASE}\n`);
}

main().catch((err: unknown) => {
  process.stderr.write(`Fatal: ${String(err)}\n`);
  process.exit(1);
});
