import { useState } from "react";
import { Setup } from "./components/Setup";
import { Shell } from "./components/Shell";
import { clearSession, loadSession, saveSession } from "./lib/storage";
import type { Session } from "./types";

export default function App() {
  const [session, setSession] = useState<Session | null>(() => loadSession());

  function enter(next: Session) {
    saveSession(next);
    setSession(next);
  }

  function leave() {
    clearSession();
    setSession(null);
  }

  if (!session) return <Setup onEnter={enter} />;
  return <Shell session={session} onLeave={leave} />;
}
