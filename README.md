# FastAPI RAG Assistant

PDF yükleme, Elasticsearch vektör arama ve BYOK (kendi API anahtarın) ile soru-cevap. Sunucu FastAPI; arayüz Vite + React (`frontend/`).

## Stack

- FastAPI, LangChain, Elasticsearch, çoklu LLM / embedding sağlayıcıları
- Workspace başına indeksler ve sistem talimatı
- API anahtarları istek header’ı ile gelir; veritabanına yazılmaz

## API (`/rag/v1`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Uygulama + Elasticsearch ping |
| POST | `/documents/index` | PDF yükle (multipart) |
| POST | `/query` | RAG sorusu |
| GET | `/prompt` | Workspace sistem talimatı |
| PUT | `/prompt` | Workspace sistem talimatı kaydet |

### Headers

- `X-Workspace-Id` — belgeler ve talimatı ayırır
- `X-Llm-Api-Key` / `X-Embedding-Api-Key` — sağlayıcı anahtarları (index/query için)

### Yerel deneme

```bash
# Health
curl http://localhost:8000/rag/v1/health
```

Deploy örneği: API URL’ini kendi host’unla değiştir (`https://YOUR-SERVICE.onrender.com`). Canlı adresleri bu repoya yazma.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PROJECT_NAME` | yes | Uygulama başlığı |
| `ELASTICSEARCH_URL` | yes | Elasticsearch endpoint |
| `ELASTICSEARCH_API_KEY` | yes (cloud) | Cluster API key |
| `ALLOWED_ORIGINS` | optional | CORS origin’leri (virgülle) |

Yerel: değerleri `.env` içine koy (asla commit etme). Frontend için `frontend/.env.example` dosyasına bak.

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Docker Elasticsearch (opsiyonel): `docker compose up -d`

## License

[MIT](LICENSE)
