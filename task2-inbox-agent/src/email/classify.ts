import type { Category } from "./types.ts";

export function classify(text: string): Category {
  const s = text.toLowerCase();
  if (/follow.?up|checking (in|whether|if)|checking on|did you receive|status of/.test(s)) return "follow_up";
  if (/refund|cancel|cancellation|chargeback/.test(s)) return "refund_cancellation";
  if (/complaint|unacceptable|disappointed|angry|broke our|still no update|hours cleaning|promised/.test(s)) return "complaint";
  if (/quote|price|cost|estimate|how much/.test(s)) return "quote";
  if (/broken|error|failed|fails|not working|issue|bug|blank screen|stopped arriving|stopped working|disappeared|security warning|charged twice|missing listings|does not reach|never reaches|notification|cannot sign|can't sign|unable to/i.test(s)) return "troubleshooting";
  if (/how (do|can) i\b|where (can|do) i\b|can you explain how|can you tell me where|can i (change|update|upload|edit|add)|steps to|configure/.test(s)) return "how_to";
  if (/could we|we'd like|we would like|build|add a (booking|feature|private|referral|second language|approval|custom)|feature|custom|integrat|project/.test(s)) return "project_request";
  return "other";
}
