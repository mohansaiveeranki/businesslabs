export const categories = [
  "how_to", "troubleshooting", "project_request", "refund_cancellation",
  "complaint", "quote", "follow_up", "other",
] as const;

export type Category = typeof categories[number];
export type Email = { id: string; from: string; subject: string; body: string };
export type KnowledgeResult = {
  answer: string;
  status: "answered" | "insufficient_evidence";
  sources: { title: string; url: string; relevance: number; excerpt: string }[];
  needs_human: boolean;
  escalation_id?: string | null;
};
export type Draft = {
  emailId: string;
  category: Category;
  urgency: "low" | "normal" | "high";
  risk: "low" | "medium" | "high";
  reply: string;
  knowledge: KnowledgeResult;
  requiresApproval: true;
  autoSendEligible: boolean;
};
