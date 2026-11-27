import { type NextRequest } from "next/server";

// FastAPI backend that /api/* is forwarded to (server-side; the browser never sees this address).
const API_URL = (process.env.API_URL || "http://localhost:8010").replace(/\/+$/, "");

const STRIP_RESPONSE_HEADERS = new Set([
  "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
  "transfer-encoding", "upgrade", "content-encoding", "content-length",
]);

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const target = `${API_URL}/api/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`;

  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");

  const init: RequestInit = { method: req.method, headers, redirect: "manual" };
  if (req.method !== "GET" && req.method !== "HEAD") init.body = await req.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    return Response.json({ detail: `SRMS API unreachable at ${API_URL}` }, { status: 502 });
  }

  const out = new Headers();
  upstream.headers.forEach((v, k) => { if (!STRIP_RESPONSE_HEADERS.has(k.toLowerCase())) out.set(k, v); });
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE };
