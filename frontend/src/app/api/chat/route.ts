/** Proxy SSE chat stream from the internal backend to the browser. */
import { auth } from "../../../../auth";

function getApiBaseUrl(): string {
  return (
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}

export async function POST(request: Request): Promise<Response> {
  const session = await auth();

  if (!session?.user) {
    return new Response("Unauthorized", { status: 401 });
  }

  if (session.error === "RefreshTokenError") {
    return new Response("Session expired", { status: 401 });
  }

  if (!session.idToken) {
    return new Response("Missing ID token", { status: 401 });
  }

  let body: string;
  try {
    const json: unknown = await request.json();
    body = JSON.stringify(json);
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const upstream = await fetch(`${getApiBaseUrl()}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.idToken}`,
    },
    body,
    signal: request.signal,
  });

  if (!upstream.ok) {
    const text = await upstream.text();
    return new Response(text, { status: upstream.status });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
