import { createDemoClient } from "./demoApi";
import { createLiveClient } from "./liveApi";
import type { ApiClient, Session } from "../types";

export function createClient(session: Session): ApiClient {
  return session.mode === "live" ? createLiveClient(session) : createDemoClient();
}
