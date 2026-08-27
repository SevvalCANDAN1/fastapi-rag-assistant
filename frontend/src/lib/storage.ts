import type { Session } from "../types";

const KEY = "folio.session";

export function loadSession(): Session | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Session>;
    if (!parsed.workspaceId) return null;
    const geminiKey = sessionStorage.getItem("folio.gemini") ?? parsed.geminiKey ?? "";
    return {
      workspaceId: parsed.workspaceId,
      geminiKey,
      apiUrl: parsed.apiUrl || import.meta.env.VITE_API_URL || "http://localhost:8000",
      mode: parsed.mode === "live" ? "live" : "demo",
    };
  } catch {
    return null;
  }
}

export function saveSession(session: Session): void {
  localStorage.setItem(
    KEY,
    JSON.stringify({
      workspaceId: session.workspaceId,
      apiUrl: session.apiUrl,
      mode: session.mode,
    } satisfies Omit<Session, "geminiKey">),
  );
  if (session.geminiKey) {
    sessionStorage.setItem("folio.gemini", session.geminiKey);
  } else {
    sessionStorage.removeItem("folio.gemini");
  }
}

export function clearSession(): void {
  localStorage.removeItem(KEY);
  sessionStorage.removeItem("folio.gemini");
}

export function defaultApiUrl(): string {
  return import.meta.env.VITE_API_URL || "http://localhost:8000";
}
