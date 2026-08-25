import type { FormEvent } from "react";
import { useState } from "react";
import { defaultApiUrl } from "../lib/storage";
import type { ConnectionMode, Session } from "../types";

interface Props {
  onEnter: (session: Session) => void;
}

export function Setup({ onEnter }: Props) {
  const [workspaceId, setWorkspaceId] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [apiUrl, setApiUrl] = useState(defaultApiUrl());
  const [mode, setMode] = useState<ConnectionMode>("demo");
  const [error, setError] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const ws = workspaceId.trim();
    if (!ws) {
      setError("Çalışma alanı adı gerekli.");
      return;
    }
    if (mode === "live" && !geminiKey.trim()) {
      setError("Canlı API için Gemini anahtarı gerekli.");
      return;
    }
    if (mode === "live" && !apiUrl.trim()) {
      setError("API adresi gerekli.");
      return;
    }
    onEnter({
      workspaceId: ws,
      geminiKey: geminiKey.trim(),
      apiUrl: apiUrl.trim().replace(/\/$/, ""),
      mode,
    });
  }

  return (
    <div className="setup">
      <section className="setup-hero">
        <div>
          <div className="brand">
            <BrandMark />
            Folio
          </div>
          <h1>Belgelerinize sorun.</h1>
          <p className="lede">
            PDF yükleyin, çalışma alanınızda sorun. Gemini anahtarınız tarayıcı oturumunda kalır;
            sunucuya yazılmaz.
          </p>
        </div>
        <div className="hero-meta">
          <div>
            <strong>BYOK</strong>
            X-Gemini-Api-Key
          </div>
          <div>
            <strong>Workspace</strong>
            X-Workspace-Id
          </div>
          <div>
            <strong>Kaynak</strong>
            sayfa + dosya adı
          </div>
        </div>
      </section>

      <section className="setup-panel">
        <form className="setup-card" onSubmit={submit}>
          <h2>Çalışma alanına gir</h2>
          <p className="hint">
            Önizleme tasarımı sahte veriyle açar. Bağlamak istediğinizde canlı API’ye geçin.
          </p>

          <div className="mode-toggle">
            <button
              type="button"
              className={mode === "demo" ? "active" : ""}
              onClick={() => setMode("demo")}
            >
              <strong>Önizleme</strong>
              <span>Sahte yanıtlar, bağlanmaz</span>
            </button>
            <button
              type="button"
              className={mode === "live" ? "active" : ""}
              onClick={() => setMode("live")}
            >
              <strong>Canlı API</strong>
              <span>FastAPI + Elasticsearch</span>
            </button>
          </div>

          <div className="field">
            <label htmlFor="workspace">Çalışma alanı</label>
            <input
              id="workspace"
              autoComplete="off"
              placeholder="ornek-proje"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
            />
          </div>

          {mode === "live" && (
            <>
              <div className="field">
                <label htmlFor="api">API adresi</label>
                <input
                  id="api"
                  placeholder="http://localhost:8000"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="key">Gemini API anahtarı</label>
                <input
                  id="key"
                  type="password"
                  autoComplete="off"
                  placeholder="AIza…"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                />
              </div>
            </>
          )}

          {error ? <p className="error-text">{error}</p> : null}

          <button className="btn btn-block" type="submit">
            Devam et
          </button>
          <p className="live-note">
            Anahtar sessionStorage’da tutulur; sekme kapanınca silinir. CORS origin:
            localhost:3000.
          </p>
        </form>
      </section>
    </div>
  );
}

export function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 32 32" fill="none" aria-hidden>
      <rect width="32" height="32" rx="8" fill="#171512" />
      <path
        d="M9 8.5h10.5a3.5 3.5 0 0 1 3.5 3.5v11H12.5A3.5 3.5 0 0 1 9 19.5v-11z"
        stroke="#e07a3d"
        strokeWidth="1.6"
      />
      <path d="M12 13h8M12 17h5" stroke="#ece6d9" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
