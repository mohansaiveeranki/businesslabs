import type { KnowledgeResult } from "../email/types.ts";

const API = process.env.KNOWLEDGE_API_URL ?? "http://127.0.0.1:8000";

export async function queryKnowledge(question: string): Promise<KnowledgeResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`${API}/query`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, top_k: 3 }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Knowledge API returned ${response.status}`);
    return await response.json() as KnowledgeResult;
  } finally {
    clearTimeout(timer);
  }
}
