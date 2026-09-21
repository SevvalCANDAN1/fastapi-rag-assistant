# FastAPI RAG Assistant

Production-oriented RAG API: PDF upload, Elasticsearch vector search, Gemini answers (BYOK via header).

Deploy the API yourself (for example Render) and set the frontend `VITE_API_URL` to that origin. Do not commit live hostnames.

## Stack

- FastAPI, LangChain, Elasticsearch Cloud, Google Gemini
- Per-workspace PDF indexes and customizable system prompts
- Gemini API key via `X-Gemini-Api-Key` (not stored in the database)

## API (`/rag/v1`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | App + Elasticsearch ping |
| POST | `/documents/index` | Upload PDF (multipart) |
| POST | `/query` | RAG question |
| GET | `/prompt` | Current workspace system prompt |
| PUT | `/prompt` | Save workspace system prompt |

### Headers

- `X-Workspace-Id` — isolates documents and prompt per workspace (e.g. UUID in `sessionStorage`)
- `X-Gemini-Api-Key` — user's Gemini key (required for index/query)

### Quick test

```bash
# Health
curl http://localhost:8000/rag/v1/health

# Index PDF
curl -X POST .../rag/v1/documents/index \
  -H "X-Gemini-Api-Key: YOUR_KEY" \
  -H "X-Workspace-Id: my-workspace-001" \
  -F "file=@document.pdf"

# Query (omit system_prompt to use saved/default prompt)
curl -X POST .../rag/v1/query \
  -H "Content-Type: application/json" \
  -H "X-Gemini-Api-Key: YOUR_KEY" \
  -H "X-Workspace-Id: my-workspace-001" \
  -d '{"question":"What topics are in the documents?"}'
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PROJECT_NAME` | yes | App title |
| `ELASTICSEARCH_URL` | yes | Elastic Cloud endpoint |
| `ELASTICSEARCH_API_KEY` | yes (cloud) | Cluster API key |
| `ALLOWED_ORIGINS` | optional | CORS origins (comma-separated) |
| `GEMINI_API_KEY` | optional | Server fallback; BYOK uses header |

Local: copy values into `.env` (never commit).

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Docker Elasticsearch (optional): `docker compose up -d`

## Development workflow

Feature branches → push → Pull Request → merge `main` → delete branch.

```bash
git checkout main && git pull
git checkout -b feat/my-feature
# ... changes ...
git commit -m "feat: description"
git push -u origin feat/my-feature
# Open PR on GitHub, merge, then delete branch
```
