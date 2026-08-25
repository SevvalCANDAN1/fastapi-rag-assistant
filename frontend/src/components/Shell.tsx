import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createClient } from "../lib/api";
import type {
  ApiClient,
  AppView,
  ChatMessage,
  HealthResponse,
  IndexedFile,
  Session,
  SourceChunk,
} from "../types";
import { BrandMark } from "./Setup";

const SUGGESTIONS = [
  "Bu belgede ana yöntem nedir?",
  "Pipeline neden kullanılır?",
  "Bu konuda bilgi yok mu?",
];

interface Props {
  session: Session;
  onLeave: () => void;
}

export function Shell({ session, onLeave }: Props) {
  const client = useMemo(() => createClient(session), [session]);
  const [view, setView] = useState<AppView>("chat");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sources, setSources] = useState<SourceChunk[]>([]);
  const [busy, setBusy] = useState(false);
  const [files, setFiles] = useState<IndexedFile[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function ping() {
      try {
        const h = await client.health();
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth({ status: "down", elasticsearch: false });
      }
    }
    void ping();
    const id = window.setInterval(ping, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [client]);

  async function ask(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setView("chat");
    const user: ChatMessage = { id: crypto.randomUUID(), role: "user", content: q };
    setMessages((m) => [...m, user]);
    try {
      const res = await client.query(q);
      setSources(res.source_documents);
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.answer,
          sources: res.source_documents,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: err instanceof Error ? err.message : "Sorgu başarısız.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-left">
          <BrandMark />
          <strong>Folio</strong>
          <span className={`pill ${session.mode}`}>{session.mode === "demo" ? "Önizleme" : "Canlı"}</span>
        </div>
        <div className="topbar-right">
          <div className="health" title="API / Elasticsearch">
            <span
              className={`dot ${
                health == null
                  ? ""
                  : health.elasticsearch && health.status === "ok"
                    ? "ok"
                    : "degraded"
              }`}
            />
            {health == null
              ? "Kontrol ediliyor"
              : health.elasticsearch
                ? "Elasticsearch bağlı"
                : "Elasticsearch yok"}
          </div>
          <button className="btn btn-ghost" type="button" onClick={onLeave}>
            Çıkış
          </button>
        </div>
      </header>

      <nav className="sidebar">
        <NavItem active={view === "chat"} onClick={() => setView("chat")} icon={ChatIcon} label="Sohbet" />
        <NavItem active={view === "docs"} onClick={() => setView("docs")} icon={DocIcon} label="Belgeler" />
        <NavItem
          active={view === "prompt"}
          onClick={() => setView("prompt")}
          icon={PromptIcon}
          label="Talimatlar"
        />
        <div className="sidebar-foot">
          <div className="workspace-label">Çalışma alanı</div>
          <div className="workspace-id">{session.workspaceId}</div>
        </div>
      </nav>

      <main className="main">
        {view === "chat" && (
          <ChatPane messages={messages} busy={busy} onAsk={ask} />
        )}
        {view === "docs" && (
          <DocsPane client={client} files={files} onIndexed={(f) => setFiles((prev) => [f, ...prev])} />
        )}
        {view === "prompt" && <PromptPane client={client} />}
      </main>

      <aside className="rail">
        <h3>Kaynaklar</h3>
        <div className="sources">
          {sources.length === 0 ? (
            <p className="muted" style={{ padding: "0 4px" }}>
              Yanıt geldiğinde Elasticsearch’ten çekilen parçalar burada görünür.
            </p>
          ) : (
            sources.map((s, i) => (
              <article className="source-card" key={`${s.filename}-${s.page}-${i}`}>
                <header>
                  <span>{s.filename ?? "belge"}</span>
                  <span>{s.page != null ? `s.${s.page}` : ""}</span>
                </header>
                <p>{s.text}</p>
              </article>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}

function NavItem({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: () => ReactNode;
  label: string;
}) {
  return (
    <button className={`nav-btn ${active ? "active" : ""}`} type="button" onClick={onClick}>
      <Icon />
      {label}
    </button>
  );
}

function ChatPane({
  messages,
  busy,
  onAsk,
}: {
  messages: ChatMessage[];
  busy: boolean;
  onAsk: (q: string) => void;
}) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  function send() {
    const q = draft;
    setDraft("");
    void onAsk(q);
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <h2>Arşiv açık.</h2>
            <p>Yüklediğiniz PDF’lerden yanıt alın. Kaynak parçaları sağda durur.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" onClick={() => onAsk(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div className={`msg ${m.role}${m.error ? " error" : ""}`} key={m.id}>
              <span className="who">{m.role === "user" ? "Siz" : "Folio"}</span>
              <div className="bubble">{m.content}</div>
            </div>
          ))
        )}
        {busy ? (
          <div className="msg assistant">
            <span className="who">Folio</span>
            <div className="bubble typing" aria-label="yazıyor">
              <i />
              <i />
              <i />
            </div>
          </div>
        ) : null}
        <div ref={endRef} />
      </div>
      <div className="composer">
        <div className="composer-box">
          <textarea
            rows={1}
            placeholder="Belgeniz hakkında sorun…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="send" type="button" disabled={busy || !draft.trim()} onClick={send}>
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}

function DocsPane({
  client,
  files,
  onIndexed,
}: {
  client: ApiClient;
  files: IndexedFile[];
  onIndexed: (file: IndexedFile) => void;
}) {
  const [over, setOver] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function upload(file: File) {
    setError("");
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Yalnızca PDF kabul edilir.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("En fazla 10 MB.");
      return;
    }
    setBusy(true);
    try {
      const res = await client.indexPdf(file);
      onIndexed({
        id: crypto.randomUUID(),
        filename: res.filename,
        chunks: res.chunks,
        at: Date.now(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yükleme başarısız.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pane">
      <p className="pane-title">Belgeler</p>
      <label
        className={`drop ${over ? "over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const file = e.dataTransfer.files[0];
          if (file) void upload(file);
        }}
      >
        {busy ? "İndeksleniyor…" : "PDF bırakın veya seçin · en fazla 10 MB"}
        <input
          type="file"
          accept="application/pdf"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void upload(file);
            e.target.value = "";
          }}
        />
      </label>
      {error ? <p className="error-text" style={{ marginTop: 12 }}>{error}</p> : null}
      <div className="file-list">
        {files.length === 0 ? (
          <p className="muted">Bu oturumda henüz belge yok. Her workspace kendi indeksini kullanır.</p>
        ) : (
          files.map((f) => (
            <div className="file-row" key={f.id}>
              <div>
                <div>{f.filename}</div>
                <small>{new Date(f.at).toLocaleString("tr-TR")}</small>
              </div>
              <small>{f.chunks} parça</small>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function PromptPane({ client }: { client: ApiClient }) {
  const [text, setText] = useState("");
  const [isDefault, setIsDefault] = useState(true);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    client
      .getPrompt()
      .then((p) => {
        if (cancelled) return;
        setText(p.system_prompt);
        setIsDefault(p.is_default);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Prompt alınamadı.");
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  async function save() {
    setError("");
    try {
      const p = await client.setPrompt(text);
      setText(p.system_prompt);
      setIsDefault(p.is_default);
      setStatus("Kaydedildi.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kayıt başarısız.");
    }
  }

  async function reset() {
    setError("");
    try {
      const p = await client.setPrompt("");
      setText(p.system_prompt);
      setIsDefault(p.is_default);
      setStatus("Varsayılana döndü.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sıfırlama başarısız.");
    }
  }

  return (
    <div className="pane prompt-box">
      <p className="pane-title">Sistem talimatı {isDefault ? "· varsayılan" : "· özel"}</p>
      <p className="muted" style={{ margin: "0 0 12px" }}>
        Model yalnızca belgedeki bağlama göre cevaplar. Boş kaydetmek varsayılana döner.
      </p>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <div className="prompt-actions">
        <button className="btn" type="button" onClick={() => void save()}>
          Kaydet
        </button>
        <button className="btn btn-ghost" type="button" onClick={() => void reset()}>
          Varsayılan
        </button>
        {status ? <span className="muted">{status}</span> : null}
      </div>
      {error ? <p className="error-text">{error}</p> : null}
    </div>
  );
}

function ChatIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3 3.5h10v7H6l-3 2v-9z" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

function DocIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M5 2.5h5l3 3V13.5H5v-11z" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10 2.5V6h3" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

function PromptIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3.5 4h9M3.5 8h9M3.5 12h6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
