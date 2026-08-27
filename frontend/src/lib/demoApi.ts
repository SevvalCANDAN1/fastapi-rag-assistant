import type { ApiClient, PromptResponse } from "../types";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

const DEFAULT_PROMPT = `You are a RAG assistant. Answer using ONLY the text inside <context>.
If the context is empty or does not contain the answer, say that this information is not in the uploaded documents. Do not invent facts.
If the question is in Turkish, answer in Turkish.
When you use a passage, mention the filename or page if that metadata appears in the context.`;

let promptState: PromptResponse = {
  system_prompt: DEFAULT_PROMPT,
  is_default: true,
};

export function createDemoClient(): ApiClient {
  return {
    async query(question) {
      await wait(900);
      const q = question.toLowerCase();
      const aboutMissing = /yok|bulunmuyor|eksik/.test(q);

      if (aboutMissing) {
        return {
          answer:
            "Yüklenen belgelerde bu bilgiye rastlamadım. Soruyu başka bir ifadeyle deneyebilir veya ilgili PDF’i bu çalışma alanına ekleyebilirsiniz.",
          source_documents: [],
        };
      }

      return {
        answer:
          "Önizleme yanıtı: scikit-learn belgelerine göre bir tahminleyici `fit` ile eğitilir, `predict` ile etiket üretir. Pipeline, dönüştürücüleri ve modeli tek bir nesnede birleştirir; böylece sızıntı riski azalır.\n\nBu cevap sahte veridir. Canlı API’ye geçince yanıtlar Elasticsearch’ten çekilen parçalara dayanır.",
        source_documents: [
          {
            filename: "sklearn-user-guide.pdf",
            page: 12,
            text: "Estimators are the building blocks of scikit-learn. An estimator is an object that implements fit and predict. Pipelines chain transformers with a final estimator so preprocessing is applied consistently.",
          },
          {
            filename: "sklearn-user-guide.pdf",
            page: 18,
            text: "Cross-validation splits the data into folds. Each fold is held out once while the remaining folds train the model. This estimates generalization without a separate test set for every experiment.",
          },
        ],
      };
    },

    async indexPdf(file) {
      await wait(700);
      const chunks = Math.max(8, Math.round(file.size / 18000));
      return {
        status: "success",
        workspace_id: "demo",
        filename: file.name,
        chunks,
      };
    },

    async getPrompt() {
      await wait(180);
      return promptState;
    },

    async setPrompt(systemPrompt) {
      await wait(280);
      const text = systemPrompt.trim();
      promptState = text
        ? { system_prompt: text, is_default: false }
        : { system_prompt: DEFAULT_PROMPT, is_default: true };
      return promptState;
    },

    async health() {
      await wait(120);
      return { status: "ok", elasticsearch: true };
    },
  };
}
