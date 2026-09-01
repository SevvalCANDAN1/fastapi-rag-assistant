# Mimari Rehber

Folio (bu repo) PDF’lerden soru-cevap üreten bir RAG asistanıdır. Sunucu FastAPI + Elasticsearch + LangChain; arayüz Vite + React. Gemini anahtarı sunucuya yazılmaz: istek başına header ile gelir (BYOK).

Bu dosya kodun *neden* böyle durduğunu özetler. Yeni bir oturumda önce buraya, sonra ilgili modüle bakın.

---

## Genel akış

```
Tarayıcı (Folio)
  Setup → Session (workspace + opsiyonel Gemini key)
       → Shell (sohbet / belgeler / talimatlar)
            │
            ├─ demo  → sahte ApiClient (ağ yok)
            └─ live  → fetch /rag/v1/*
                            │
FastAPI  main.py
  CORS + router’lar
       ├─ routers/rag.py        query, index, prompt
       ├─ routers/catalog.py    LLM / embedding listesi
       └─ /health               Elasticsearch ping
            │
services/
  loader.py          PDF → chunk
  elastic_rag.py     embed + indeksle + retrieve + LLM
            │
Elasticsearch
  rag-{workspace}              vektörler
  rag-workspace-settings       prompt + model seçimi
```

Canlı sorgu yolu: soru → workspace indeksinden `k=3` parça → sistem talimatı + `<context>` → Gemini → cevap + kaynak metadata (dosya adı, sayfa).

---

## Klasörler ne işe yarar

| Katman | Ne tutar | Neden ayrı |
| --- | --- | --- |
| `main.py` | Uygulama, CORS, health, router bağlama | Giriş noktası ince kalsın; iş kuralı buraya sızmasın |
| `core/config.py` | Ortam değişkenleri | Deploy (Render / local) `.env` ile değişsin, kod değişmesin |
| `core/model_catalog.py` | Desteklenen LLM / embedding ve eşleşmeleri | UI ve API aynı kaynaktan okusun; “hangi model hangi embed?” tek yerde dursun |
| `models/schemas.py` | İstek / yanıt sözleşmesi | FastAPI doğrulasın, frontend `types.ts` ile hizalansın |
| `routers/` | HTTP: header çözme, dosya limiti, hata kodu | Ağ kenarı servisten ayrı kalsın |
| `services/loader.py` | PDF yükle, parçala | İndeksleme pipeline’ı sorgudan bağımsız test edilebilsin |
| `services/elastic_rag.py` | ES client, workspace, prompt, RAG zinciri | Tek “beyin”; router sadece çağırır |
| `frontend/` | Folio UI | Backend’siz önizleme (demo) ve canlı bağlanma aynı ekranlardan geçsin |
| `docker-compose.yml` | Yerel Elasticsearch 9 | Cloud’a bağlanmadan geliştirme |
| `Procfile` | `uvicorn` | Render web process tanımı |

---

## İsteklerin izlediği yol

### 1. PDF indeksleme

1. `POST /rag/v1/documents/index` — `X-Workspace-Id` zorunlu, `X-Gemini-Api-Key` (veya sunucu `GEMINI_API_KEY`) embed için.
2. Yalnızca PDF, en fazla 10 MB; içerik geçici dosyaya yazılır, iş bitince silinir.
3. `load_and_split_pdf`: `RecursiveCharacterTextSplitter` (500 / 50 overlap) + `filename` / `workspace_id` metadata.
4. `ElasticRAGService.index_documents` Gemini embedding ile `rag-{workspace}` indeksine yazar.

### 2. Soru-cevap

1. `POST /rag/v1/query` — aynı header’lar; gövdede `question`, isteğe bağlı `system_prompt` (yalnızca bu istek).
2. Retriever `k=3`. Parçalar `[filename p.N]` başlığıyla birleştirilir.
3. Prompt yoksa workspace kaydı, o da yoksa `DEFAULT_SYSTEM_PROMPT`.
4. LangChain LCEL: talimat + context + soru → `gemini-2.5-flash` → düz metin.
5. Yanıtta `source_documents` ayrı döner; UI sağ rayda gösterir.

### 3. Workspace talimatı

`GET/PUT /rag/v1/prompt` Gemini istemez. Ayarlar `rag-workspace-settings` içinde workspace id ile saklanır. Boş string varsayılana döner.

### 4. Model kataloğu

`GET /rag/v1/catalog/llm-models` ve `.../embedding-models?llm_provider=&llm_model=` önerilen embedding’leri döner. Workspace belgesinde `llm_*` / `embedding_*` alanları da durur; **sorgu zinciri henüz bu alanları kullanmaz** (hâlâ Gemini sabit). Katalog, çok-sağlayıcılı geçiş için hazır sözleşmedir.

### 5. Sağlık

`GET /rag/v1/health` Elasticsearch `ping`. Ayağa kalkmamışsa `503` + `degraded`. Yük dengeleyici “uygulama ayakta ama vektör deposu yok” durumunu 200 ile yeşil sanmasın diye.

---

## Kararlar (neden böyle)

### ADR-1 — Katmanlı FastAPI, şişman `main` değil

Router HTTP’yi, `services` RAG’i, `core` yapılandırmayı tutar. Yeni endpoint veya yeni retriever eklerken dokunulacak yer belli olsun, CORS/health ile karışmasın diye.

### ADR-2 — BYOK: anahtar header’da, sunucuda saklanmaz

`X-Gemini-Api-Key` tercih edilir; `GEMINI_API_KEY` yalnızca opsiyonel yedek. Frontend anahtarı `sessionStorage`’da tutar (`folio.gemini`), `localStorage`’a workspace/mod yazar. Amaç: çok kiracılı demoda kullanıcı anahtarının diske veya log’a düşmemesi. CORS’ta bu header’ın açıkça izinli olması bu yüzden.

### ADR-3 — Workspace = ayrı Elasticsearch indeksi

İndeks adı `rag-{sanitized-id}`. Kullanıcılar aynı cluster’da birbirinin belgesini çekmesin. Id yalnızca alfanumerik / `-` / `_`; aksi 400. Ayarlar ayrı indeks (`rag-workspace-settings`) çünkü prompt/model vektör gövdesinden bağımsız ve id ile tek doküman yeter.

### ADR-4 — Elasticsearch hem vektör hem ayar deposu

Ayrı Postgres/Redis yok. Deploy yüzeyi küçük kalsın (Render + Elastic Cloud veya local compose). Bedel: ayar sorguları ES’e bağlı; health de bu yüzden ES’i ölçer.

### ADR-5 — LangChain LCEL, özel orkestratör yok

`ElasticsearchStore` + retriever + `ChatPromptTemplate` + `ChatGoogleGenerativeAI`. RAG’i çerçeve zaten biliyor; zinciri okunur tutmak, ileride streaming veya rerank eklemeyi kolaylaştırmak için.

### ADR-6 — PDF-only, küçük chunk, k=3

Yükleyici `PyPDFLoader`. Chunk 500 / overlap 50: embed maliyeti ve gürültü dengesi. `k=3`: context penceresini şişirmeden kaynak göstermeye yetecek kadar parça. 10 MB ve geçici dosya: bellek ve disk sızıntısını sınırlamak için.

### ADR-7 — Sistem talimatı workspace’te, istekte override

Varsayılan prompt “yalnızca context, uydurma, Türkçe soruya Türkçe.” Workspace kaydı kalıcı kişiselleştirme; `QueryRequest.system_prompt` tek seferlik deneme. Boş PUT = reset. Böylece UI “Talimatlar” paneli ile sohbet override’ı çakışmaz.

### ADR-8 — Tek paylaşılan ES client

`get_es_client` `lru_cache(maxsize=1)`. Cloud API key hem düz string hem base64 `id:secret` kabul eder (Elastic Cloud / self-hosted farkı). Her istekte yeni TCP oturumu açmamak ve Render’da auth header’ını doğru basmak için.

### ADR-9 — API öneki `/rag/v1`

Tüm RAG yolları versiyonlu. İleride kırıcı değişiklik (`v2`) eski istemciyi bozmasın. Frontend `liveApi.ts` bu öneki sabit kullanır.

### ADR-10 — Model kataloğu kodda, runtime’da keşif yok

`core/model_catalog.py` frozen dataclass listesi. LLM’ye göre önerilen embedding’ler (ör. Gemini→Gemini embed, Anthropic→Voyage sonra OpenAI). Query param’lar enum ile kısıtlı; bilinmeyen referans `RuntimeError`. Amaç: UI’nin uydurma model id’si göndermemesi. **Bilinen boşluk:** indeksleme ve sorgu hâlâ `gemini-embedding-001` + `gemini-2.5-flash`. Katalog + workspace alanları bir sonraki adımın kancası.

### ADR-11 — Folio: aynı `ApiClient`, demo veya live

`createClient(session)` demo’da ağ çağırmaz, live’da FastAPI’ye gider. Setup’ta önizleme, CORS/ES olmadan UI’yi gezdirmek için. Chat / docs / prompt aynı arayüzü kullanır; kaynak listesi sohbetten bağımsız sağ sütunda durur çünkü RAG’in değeri cevabın *nereden* geldiğini göstermek.

### ADR-12 — Frontend 3000, CORS allowlist

Vite `strictPort: 3000`; `ALLOWED_ORIGINS` varsayılanı `http://localhost:3000`. Tarayıcıdan gelen BYOK header’ı rastgele origin’den gitmesin. Prod API adresi yoksa canlı host’ta Render URL’sine düşülür (`storage.ts`).

### ADR-13 — Health 503, kök 200

`/` “süreç ayakta”; `/rag/v1/health` “ES de ayakta.” Compose veya Cloud kesilince UI kırmızı nokta göstersin, platform healthcheck’i yanıltmasın.

---

## Çalışma zamanı

- **Yerel vektör deposu:** `docker-compose` Elasticsearch 9, security kapalı, tek düğüm.
- **API:** `uvicorn main:app` (Procfile aynı komutu Render’da çalıştırır).
- **UI:** `frontend/` → `npm run dev` port 3000.
- **Gizli bilgiler:** `.env` git’te yok. Gerekli: `PROJECT_NAME`, `ELASTICSEARCH_URL`; cloud’da `ELASTICSEARCH_API_KEY`; CORS için `ALLOWED_ORIGINS`.

---

## Bilinçli sınırlar

- Çok sağlayıcılı LLM/embedding seçimi katalogda ve workspace belgesinde var, zincirde yok.
- `JWT_SECRET` config’de duruyor, auth akışı yok; kimlik workspace header’ı.
- İndekslenmiş dosya listesi sunucuda tutulmaz; Folio yalnızca oturum belleğindeki yüklemeleri gösterir.
- Streaming yok; cevap tek parça döner.
- PDF dışı format yok.

Bu sınırlar “unutulmuş borç” değil: önce BYOK + workspace izolasyonu + kaynaklı cevap oturdu, sağlayıcı soyutlaması ve streaming sonraki katman.
