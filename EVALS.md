# Evaluation plan and current status

## What has been checked

- The local Knowledge Brain and Inbox Agent health endpoints responded successfully. The Knowledge Brain OpenAPI document loaded and included its expected routes.
- API smoke checks covered a supported help question with citations, an unsupported question that creates a human-review escalation, resolution of an escalation, email drafting, scope generation, scope approval, and follow-up change comparison.
- A human answer is not added to searchable knowledge unless it is explicitly marked approved.
- The email fixture check matched 50 of 50 synthetic examples to their authored category labels. This checks the rule baseline against its own examples; it is not a measure of real-world accuracy.
- The reorganized modules pass five Knowledge Brain checks, two Meeting-to-Scope checks, and one Inbox Agent classifier test. These cover sitemap expansion, article parsing, weak-match filtering, source-preserving extraction, scope comparisons, and category labels.
- After the folder move, the app launcher and live endpoints were checked again. The browser page, both health checks, a cited answer, an inbox draft, and a scope build all worked.
- Mocked sitemap checks cover batching, nested index expansion, image alt-text capture, citations, and deactivating an article removed from the sitemap. The real public sitemap could not be fetched in this environment because its network proxy connection failed. The app now starts a live import in the background and reports a visible error if the source cannot be reached; that live import still needs a successful run on a network with access.
- The latest startup correctly loaded the live-enabled app, deactivated the old demo entries, and reported `ConnectError` when this environment could not reach the public sitemap. No live articles were available to test end-to-end here.
- The startup script launched both services, the browser page returned successfully, and the stop script stopped the services.

## What remains unmeasured

No Claude API call, model comparison, model quality review, latency measurement, or cost measurement has been run. The Knowledge Brain is set to import current public help content, but a successful external crawl has not yet been verified. Email and scope generation use deterministic local rules. The supplied meeting transcripts are synthetic examples, not recordings of role-play sessions. The assignment's requirement for 20 held-out cases per task and model comparisons remains incomplete.

## Evaluation plan

Run the same 20 or more held-out cases for each task through each candidate model and the local baseline. Save case ID, expected result, actual result, pass/fail, model and prompt version, latency, token usage, cost, and failure reason. Have a person score evidence-supported correctness, citation validity, required behavior, safe abstention, and valid structured output. Report denominators, failures, and safety issues; do not use fixture agreement as a substitute for model quality.

### Knowledge Brain cases to prepare

Logo location; staff invitation; homepage category ordering; footer link; contact form email; category visibility; payment setup; duplicate-charge safety; provider unavailable; search settings; mobile search behavior; custom ranking; cancellation; refund eligibility; unsupported feature; prompt injection in an article; screenshot-only label; changed article hash; removed page; API timeout and malformed input.

### Inbox Agent cases to prepare

Logo how-to; admin invitation; payment setup; duplicate charge; urgent outage; refund request; cancellation; complaint; quote request; feature request; ticket follow-up; missing knowledge; unsupported guarantee; angry urgent message; email injection; malformed sender; long email; knowledge API timeout; unchanged feedback; edited or rejected draft.

### Meeting to Scope cases to prepare

Requirement extraction; vague search request; feasibility via Knowledge Brain; uncertain integration; source excerpt preservation; acceptance criteria; empty transcript; long transcript; duplicate requirement; estimate arithmetic; rate and currency; deadline uncertainty; follow-up adds alert; adds export; changes location filter; omitted baseline item; unapproved change; approved baseline history; Knowledge Brain unavailable; prompt injection in transcript.

For the inbox fixture check, run `cd task2-inbox-agent` followed by `npm run check:fixtures` from PowerShell. The application itself runs on Node 22.6 or newer without installing npm packages.

## Local checks

From the project root, run these commands in Git Bash to repeat the focused checks:

```bash
./.venv/Scripts/python.exe -m unittest discover -s task1-knowledge-brain/tests -v
./.venv/Scripts/python.exe -m unittest discover -s task3-meeting-to-scope/tests -v
(cd task2-inbox-agent && npm test && npm run check:fixtures)
```

These are small code checks for parsing, retrieval, requirement extraction, scope comparison, and email classification. They are not the held-out model evaluation described above.
