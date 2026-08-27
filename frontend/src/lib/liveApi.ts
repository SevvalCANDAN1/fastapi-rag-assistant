import type {
  ApiClient,
  HealthResponse,
  IndexResponse,
  PromptResponse,
  QueryResponse,
  Session,
} from "../types";

function headers(session: Session, extra?: Record<string, string>): HeadersInit {
  return {
    "X-Workspace-Id": session.workspaceId,
    ...(session.geminiKey ? { "X-Gemini-Api-Key": session.geminiKey } : {}),
    ...extra,
  };
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  if (res.status === 401) return "Gemini anahtarı veya workspace kimliği eksik.";
  if (res.status === 503) return "Elasticsearch şu an ulaşılamıyor.";
  return `İstek başarısız (${res.status}).`;
}

export function createLiveClient(session: Session): ApiClient {
  const base = session.apiUrl.replace(/\/$/, "");

  return {
    async query(question, systemPrompt) {
      const res = await fetch(`${base}/rag/v1/query`, {
        method: "POST",
        headers: headers(session, { "Content-Type": "application/json" }),
        body: JSON.stringify({
          question,
          ...(systemPrompt ? { system_prompt: systemPrompt } : {}),
        }),
      });
      if (!res.ok) throw new Error(await readError(res));
      return (await res.json()) as QueryResponse;
    },

    async indexPdf(file) {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${base}/rag/v1/documents/index`, {
        method: "POST",
        headers: headers(session),
        body: form,
      });
      if (!res.ok) throw new Error(await readError(res));
      return (await res.json()) as IndexResponse;
    },

    async getPrompt() {
      const res = await fetch(`${base}/rag/v1/prompt`, {
        headers: headers(session),
      });
      if (!res.ok) throw new Error(await readError(res));
      return (await res.json()) as PromptResponse;
    },

    async setPrompt(systemPrompt) {
      const res = await fetch(`${base}/rag/v1/prompt`, {
        method: "PUT",
        headers: headers(session, { "Content-Type": "application/json" }),
        body: JSON.stringify({ system_prompt: systemPrompt }),
      });
      if (!res.ok) throw new Error(await readError(res));
      return (await res.json()) as PromptResponse;
    },

    async health() {
      const res = await fetch(`${base}/rag/v1/health`);
      const body = (await res.json()) as HealthResponse;
      if (!res.ok && res.status !== 503) throw new Error("API sağlık kontrolü başarısız.");
      return body;
    },
  };
}
