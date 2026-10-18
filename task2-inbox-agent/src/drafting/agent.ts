import { classify } from "../email/classify.ts";
import type { Draft, Email, KnowledgeResult } from "../email/types.ts";
import { queryKnowledge } from "../knowledge-client/client.ts";

export { classify } from "../email/classify.ts";
export { recordFeedback } from "../feedback/store.ts";
export type { Category, Draft, Email, KnowledgeResult } from "../email/types.ts";

export async function draft(raw: unknown): Promise<Draft> {
  if (!raw || typeof raw !== "object") throw new Error("Email must be an object");
  const input = raw as Record<string, unknown>;
  if (typeof input.id !== "string" || !input.id.trim()
      || typeof input.from !== "string" || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.from)
      || typeof input.subject !== "string" || !input.subject.trim() || input.subject.length > 300
      || typeof input.body !== "string" || input.body.trim().length < 3 || input.body.length > 8000) {
    throw new Error("Email fields are invalid or exceed their limits");
  }

  const email: Email = { id: input.id, from: input.from, subject: input.subject, body: input.body };
  const category = classify(`${email.subject}\n${email.body}`);
  let evidence: KnowledgeResult;
  try {
    evidence = await queryKnowledge(email.body);
  } catch {
    evidence = {
      answer: "Knowledge service is unavailable; no product facts were checked.",
      status: "insufficient_evidence",
      sources: [],
      needs_human: false,
    };
  }

  const highRisk = ["refund_cancellation", "complaint", "quote", "project_request"].includes(category);
  const reply = evidence.status === "answered"
    ? `Hi,\n\nThanks for reaching out. ${evidence.answer}\n\n${highRisk
      ? "Our team will need to confirm the account-specific details before making any changes or commitments."
      : "I hope that helps. Let us know if you have any questions."}\n\nBest,\nSupport`
    : `Hi,\n\nThanks for reaching out. I do not have enough verified information to answer safely yet. ${evidence.needs_human
      ? "I have flagged this for specialist review."
      : "A support specialist will need to review your request before we confirm details."}\n\nBest,\nSupport`;

  return {
    emailId: email.id,
    category,
    urgency: /urgent|today|down|outage/i.test(email.body) ? "high" : "normal",
    risk: highRisk ? "high" : category === "troubleshooting" ? "medium" : "low",
    reply,
    knowledge: evidence,
    requiresApproval: true,
    autoSendEligible: false,
  };
}
