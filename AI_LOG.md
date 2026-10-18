# AI coding notes

I used Codex to help build and review this assignment in the local project workspace. The main request was to complete the assignment, improve the app and its writing, check the APIs, and make the project easier for a beginner to run.

This file is a short account of the work, not an exported chat transcript. The workspace did not provide a record of five exact prompts or a Claude Code/Cursor session, so I have not made one up. If the evaluator requires those records, add the genuine prompts or export before submission.

## Changes made after review

The first sitemap removal check could have marked articles as removed before the whole sitemap had been read. Removal is now reconciled only after a complete scan. The inbox feedback streak also needed to stop when a different kind of review happened; it now resets on intervening events and records the generated reply alongside the final edited reply.

During the last retrieval check, an unsupported refund question matched unrelated sample articles. I raised the minimum evidence score so weak matches go to human review. The fabricated knowledge entries are now disabled by default; the app imports public help articles from the live sitemap instead.

The code is now arranged by responsibility under the three task folders: ingestion and retrieval, email classification and drafting, and meeting extraction and scope comparison. I ran the focused tests and checked the launcher and main API handoffs after the move.

## What still needs real project evidence

The local app now imports public help articles from a live sitemap, but this environment could not verify a successful external crawl. It does not call Claude, and there are no retained model-comparison results. The example emails and meeting transcripts are synthetic. Add real model runs, human-reviewed results, and any required role-play records before describing those parts as completed.
