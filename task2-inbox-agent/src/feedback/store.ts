import { appendFile, readFile } from "node:fs/promises";
import { categories, type Category } from "../email/types.ts";

const STORE = new URL("../../data/feedback.jsonl", import.meta.url);
type Outcome = "sent_unchanged" | "edited" | "rejected" | "unsafe";
type Event = { category: Category; outcome: Outcome; timestamp: string; draftText?: string; finalText?: string };

export async function recordFeedback(
  category: Category,
  outcome: Outcome,
  draftText?: string,
  finalText?: string,
): Promise<{ streak: number; eligible: boolean }> {
  if (!categories.includes(category)) throw new Error("Unknown category");
  let lines: string[] = [];
  try { lines = (await readFile(STORE, "utf8")).trim().split("\n").filter(Boolean); }
  catch { /* The first review has no previous journal yet. */ }

  const event: Event = {
    category,
    outcome,
    timestamp: new Date().toISOString(),
    ...(draftText ? { draftText } : {}),
    ...(finalText ? { finalText } : {}),
  };
  await appendFile(STORE, JSON.stringify(event) + "\n", "utf8");
  if (outcome !== "sent_unchanged") return { streak: 0, eligible: false };

  let streak = 0;
  for (const line of [...lines].reverse()) {
    const old = JSON.parse(line) as Event;
    if (old.category !== category || old.outcome !== "sent_unchanged") break;
    streak++;
  }
  streak++;
  return { streak, eligible: category === "how_to" && streak >= 20 };
}
