export type ConnectionMode = "demo" | "live";
export type AppView = "chat" | "docs" | "prompt";

export interface Session {
  workspaceId: string;
  geminiKey: string;
  apiUrl: string;
  mode: ConnectionMode;
}

export interface SourceChunk {
  text: string;
  filename: string | null;
  page: number | null;
}

export interface QueryResponse {
  answer: string;
  source_documents: SourceChunk[];
}

export interface IndexResponse {
  status: string;
  workspace_id: string;
  filename: string;
  chunks: number;
}

export interface PromptResponse {
  system_prompt: string;
  is_default: boolean;
}

export interface HealthResponse {
  status: string;
  elasticsearch: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  error?: boolean;
}

export interface IndexedFile {
  id: string;
  filename: string;
  chunks: number;
  at: number;
}

export interface ApiClient {
  query(question: string, systemPrompt?: string): Promise<QueryResponse>;
  indexPdf(file: File): Promise<IndexResponse>;
  getPrompt(): Promise<PromptResponse>;
  setPrompt(systemPrompt: string): Promise<PromptResponse>;
  health(): Promise<HealthResponse>;
}
