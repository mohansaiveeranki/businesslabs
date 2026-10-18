# Business Labs: AI Tech Consultant

This project brings three small-business workflows into one local app: searching live help content, preparing a customer email, and turning meeting notes into a project plan. On startup, the Knowledge Brain begins importing current public Brilliant Directories help articles from the configured sitemap. Inbox and Scope use those indexed articles. Replies and plans stay drafts for a person to review; the app does not send customer email.

## Run it from Git Bash

The project is in `D:\businesslabs`. In Git Bash, run:

```bash
cd /d/businesslabs
powershell.exe -ExecutionPolicy Bypass -File 'D:\businesslabs\scripts\start.ps1'
```

The start script opens the app in your browser. If it does not, visit <http://127.0.0.1:8000>.

When you are finished, stop the services from Git Bash:

```bash
powershell.exe -ExecutionPolicy Bypass -File 'D:\businesslabs\scripts\stop.ps1'
```

The first start creates a Python environment in `.venv` and installs the packages in `requirements.txt`. It needs Python 3.11 or newer, Node.js 22.6 or newer, and internet access for package installation and the live help-center import. If startup fails, check `data/logs/knowledge-error.log` and `data/logs/inbox-error.log`.

## Try the app

- **Knowledge Brain:** the app starts a live help-center import automatically. You can also click **Sync public help center** to import the next batch. Each batch contains up to 20 articles; more batches run daily. The source site must be reachable from your computer.
- **Inbox Agent:** review the example email, draft a reply, check its source, and record your review. Nothing is sent.
- **Meeting to Scope:** prepare a plan from the example notes, review it, and try the follow-up box to compare changes.

The Knowledge Brain API docs are at <http://127.0.0.1:8000/docs>. The Inbox Agent health check is at <http://127.0.0.1:8001/health>.

## Project folders

- `task1-knowledge-brain/` contains the Knowledge Brain API, sitemap and article parsing, retrieval, image metadata handling, and focused tests.
- `task2-inbox-agent/` contains email classification, the Knowledge Brain client, reply drafting, feedback storage, and fixture checks.
- `task3-meeting-to-scope/` contains the scope API, requirement extraction, meeting transcripts, and follow-up comparison.
- `shared-docs/` contains notes used across the three workflows. The root folder holds the main setup and design documents.

## Current project status

Help articles are fetched live and cached locally so search remains fast. The email and meeting examples are synthetic, and reply and scope generation are rule-based. The app does not call Claude, send email, or connect to a private Brilliant Directories customer account. A private account API needs its own domain and API key; never put that key in the browser. The required model comparison and cost and quality evaluation are still outstanding. See [DESIGN.md](DESIGN.md), [EVALS.md](EVALS.md), and [AI_LOG.md](AI_LOG.md) for details.
