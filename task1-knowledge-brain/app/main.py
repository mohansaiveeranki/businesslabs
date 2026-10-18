"""Shared Knowledge Brain API. Local retrieval is deliberately transparent and inspectable."""
from __future__ import annotations

import hashlib
import asyncio
import importlib.util
import logging
import os
import sqlite3
import sys
import uuid
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from apscheduler.schedulers.asyncio import AsyncIOScheduler

ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "task1-knowledge-brain"
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))
from ingestion.crawler import fetch_sitemap_urls
from ingestion.parser import article_text
from retrieval.search import rank_sources

DB_PATH = Path(os.getenv("KB_DB_PATH", ROOT / "data" / "knowledge.db"))
SITEMAP = os.getenv("KB_SITEMAP_URL", "https://support.brilliantdirectories.com/support/sitemap.xml")
log=logging.getLogger(__name__)

# The assignment uses hyphenated folder names, which Python cannot import as
# package names. Load the scope router by file path while keeping that layout.
_scope_path = ROOT / "task3-meeting-to-scope" / "app" / "main.py"
_scope_spec = importlib.util.spec_from_file_location("meeting_scope_pipeline", _scope_path)
if _scope_spec is None or _scope_spec.loader is None:
    raise ImportError(f"Could not load scope API from {_scope_path}")
_scope_module = importlib.util.module_from_spec(_scope_spec)
sys.modules[_scope_spec.name] = _scope_module
_scope_spec.loader.exec_module(_scope_module)
scope_router = _scope_module.router
DEMO_SEED = [
    ("Changing your site logo", "demo://help/site-logo", "In this example, open the site admin dashboard, choose Design, then Logo & Branding. Upload an image and save. The screenshot reference is an illustration created for this demo."),
    ("Payment setup overview", "demo://help/payments", "Payment options can depend on the account and region. In this example, check Settings, then Payments. Ask support if a provider is missing."),
    ("Troubleshooting a failed payment", "demo://help/payment-troubleshooting", "Before retrying a charge, check that the provider is connected and confirm the transaction status in its dashboard."),
    ("Website search settings", "demo://help/search-settings", "Search options can depend on site settings and enabled modules. Ask support to confirm whether custom ranking is available."),
    ("Account cancellation requests", "demo://help/cancellation", "Cancellation and refund eligibility depend on the account terms. Ask support to confirm account-specific details before making a change."),
]

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    context: str | None = Field(default=None, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)

class Source(BaseModel):
    title: str
    url: str
    relevance: float
    excerpt: str

class QueryResponse(BaseModel):
    answer: str
    status: Literal["answered", "insufficient_evidence"]
    sources: list[Source]
    confidence: float | None = None
    needs_human: bool
    escalation_id: str | None = None

class EscalationRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    reason: str = Field(min_length=3, max_length=1000)

class ResolutionRequest(BaseModel):
    answer: str = Field(min_length=3, max_length=4000)
    reviewer: str = Field(min_length=1, max_length=120)
    approved_for_knowledge: bool = False
    expires_at: datetime | None = None

class IngestRequest(BaseModel):
    sitemap_url: HttpUrl = SITEMAP
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS articles(url TEXT PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,content_hash TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS escalations(id TEXT PRIMARY KEY,question TEXT NOT NULL,reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS expert_answers(id TEXT PRIMARY KEY,question TEXT,answer TEXT,reviewer TEXT,expires_at TEXT,approved INTEGER NOT NULL DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS ingestion(url TEXT PRIMARY KEY,status TEXT,attempts INTEGER DEFAULT 0,error TEXT,content_hash TEXT,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        """)
        expert_columns={row["name"] for row in db.execute("PRAGMA table_info(expert_answers)")}
        if "approved" not in expert_columns:
            db.execute("ALTER TABLE expert_answers ADD COLUMN approved INTEGER NOT NULL DEFAULT 0")
        if os.getenv("KB_DEMO_SEED", "false").lower() == "true" and db.execute("SELECT count(*) FROM articles").fetchone()[0] == 0:
            for title, url, body in DEMO_SEED:
                db.execute("INSERT OR IGNORE INTO articles(url,title,body,content_hash) VALUES(?,?,?,?)", (url,title,body,hashlib.sha256(body.encode()).hexdigest()))
        else:
            # Example entries must never be presented as current product help.
            db.execute("UPDATE articles SET active=0 WHERE url LIKE 'demo://%'")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler=AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_scheduled_ingestion,"cron",hour=3,minute=30,id="daily-sitemap-check",replace_existing=True)
    scheduler.start()
    with connect() as db:
        live_count = db.execute("SELECT count(*) FROM articles WHERE active=1 AND url NOT LIKE 'demo://%'").fetchone()[0]
    if live_count == 0:
        asyncio.create_task(run_scheduled_ingestion())
    yield
    scheduler.shutdown(wait=False)

async def run_scheduled_ingestion() -> None:
    try:
        limit=max(1,min(100,int(os.getenv("KB_DAILY_CRAWL_LIMIT","20"))))
        with connect() as db:
            row=db.execute("SELECT value FROM settings WHERE key='daily_offset'").fetchone()
        offset=int(row[0]) if row else 0
        await ingest(IngestRequest(limit=limit,offset=offset))
    except Exception:
        with connect() as db:
            current=db.execute("SELECT value FROM settings WHERE key='last_sync_error'").fetchone()
            if not current or not current[0]:
                db.execute("INSERT INTO settings(key,value) VALUES('last_sync_error','Sync failed; check the Knowledge API logs.') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
        log.exception("Daily Knowledge Brain ingestion failed")

app = FastAPI(title="AI Tech Consultant Knowledge Brain", version="1.0.0", lifespan=lifespan)
app.include_router(scope_router)

def retrieve(question: str, top_k: int) -> list[Source]:
    with connect() as db:
        rows = db.execute("SELECT title,url,body,'' AS query FROM articles WHERE active=1 UNION ALL SELECT 'Reviewed expert answer', 'expert://' || id, answer AS body, question FROM expert_answers WHERE approved=1 AND (expires_at IS NULL OR julianday(expires_at) > julianday('now'))").fetchall()
    return [Source(**source) for source in rank_sources(question, rows, top_k)]

@app.get("/health")
def health():
    with connect() as db:
        count = db.execute("SELECT count(*) FROM articles WHERE active=1 AND url NOT LIKE 'demo://%'").fetchone()[0]
    return {"status":"ok","active_articles":count,"retrieval":"lexical"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    sources = retrieve(req.question + (" " + req.context if req.context else ""), req.top_k)
    if not sources:
        eid = str(uuid.uuid4())
        with connect() as db:
            db.execute("INSERT INTO escalations(id,question,reason) VALUES(?,?,?)",(eid,req.question,"No sufficiently relevant active evidence"))
        return QueryResponse(answer="I could not find enough verified information to answer safely. I have created a human review task.",status="insufficient_evidence",sources=[],needs_human=True,escalation_id=eid)
    answer="The matching help content says: "+sources[0].excerpt
    return QueryResponse(answer=answer,status="answered",sources=sources,confidence=None,needs_human=False)

@app.post("/escalations")
def create_escalation(req: EscalationRequest):
    eid=str(uuid.uuid4())
    with connect() as db: db.execute("INSERT INTO escalations(id,question,reason) VALUES(?,?,?)",(eid,req.question,req.reason))
    return {"id":eid,"status":"open"}

@app.get("/escalations")
def list_escalations():
    with connect() as db: return [dict(r) for r in db.execute("SELECT * FROM escalations ORDER BY created_at DESC")]

@app.post("/escalations/{escalation_id}/resolve")
def resolve(escalation_id: str, req: ResolutionRequest):
    with connect() as db:
        row=db.execute("SELECT question,status FROM escalations WHERE id=?",(escalation_id,)).fetchone()
        if row is None: raise HTTPException(404,"Escalation not found")
        if row["status"] != "open": raise HTTPException(409,"Escalation is already resolved")
        db.execute("INSERT INTO expert_answers(id,question,answer,reviewer,expires_at,approved) VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),row["question"],req.answer,req.reviewer,req.expires_at.isoformat() if req.expires_at else None,int(req.approved_for_knowledge)))
        db.execute("UPDATE escalations SET status='resolved' WHERE id=?",(escalation_id,))
    return {"id":escalation_id,"status":"resolved","added_to_knowledge":req.approved_for_knowledge}

@app.post("/ingestion/run")
async def ingest(req: IngestRequest):
    # Fetches are deliberately sequential and rate-limited; run with a small limit first.
    async with httpx.AsyncClient(timeout=20,follow_redirects=True,headers={"User-Agent":"AI-Tech-Consultant-Student/1.0 (polite demo crawler)"}) as client:
        try:
            all_urls,can_reconcile=await fetch_sitemap_urls(client,str(req.sitemap_url))
        except (httpx.RequestError,httpx.HTTPStatusError,ET.ParseError,ValueError) as exc:
            with connect() as db:
                db.execute("INSERT INTO settings(key,value) VALUES('last_sync_error',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(f"{type(exc).__name__}: {exc}"[:500],))
            raise HTTPException(status_code=502,detail=f"Could not read the sitemap ({type(exc).__name__}). Check the URL and network, then retry.") from exc
        start=min(req.offset,len(all_urls))
        urls=all_urls[start:start+req.limit]
        next_offset=0 if start+len(urls)>=len(all_urls) else start+len(urls)
        counts={"added":0,"updated":0,"unchanged":0,"failed":0,"removed":0}
        with connect() as db:
            old={r["url"]:r["content_hash"] for r in db.execute("SELECT url,content_hash FROM articles")}
        for url in urls:
            try:
                page=None
                for attempt in range(1,4):
                    with connect() as db: db.execute("INSERT INTO ingestion(url,status,attempts,error) VALUES(?,'fetching',1,NULL) ON CONFLICT(url) DO UPDATE SET status='fetching',attempts=attempts+1,error=NULL",(url,))
                    try:
                        page=await client.get(url); page.raise_for_status(); break
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code < 500: raise
                        if attempt == 3: raise
                    except (httpx.TimeoutException,httpx.NetworkError):
                        if attempt == 3: raise
                    await asyncio.sleep(.5 * (2 ** (attempt-1)))
                if page is None: raise RuntimeError("Page fetch did not complete")
                title,body=article_text(page.text,str(page.url))
                if not body.strip(): raise ValueError("No article text extracted")
                digest=hashlib.sha256((title+"\n"+body).encode()).hexdigest()
                if old.get(url)==digest:
                    counts["unchanged"]+=1
                    with connect() as db: db.execute("UPDATE articles SET active=1,title=?,updated_at=CURRENT_TIMESTAMP WHERE url=?",(title,url))
                else:
                    counts["updated" if url in old else "added"]+=1
                    with connect() as db:
                        db.execute("INSERT INTO articles(url,title,body,content_hash,active) VALUES(?,?,?,?,1) ON CONFLICT(url) DO UPDATE SET title=excluded.title,body=excluded.body,content_hash=excluded.content_hash,active=1,updated_at=CURRENT_TIMESTAMP",(url,title,body,digest))
                with connect() as db: db.execute("UPDATE ingestion SET status='complete',content_hash=?,updated_at=CURRENT_TIMESTAMP WHERE url=?",(digest,url))
            except Exception as exc:
                counts["failed"]+=1
                with connect() as db: db.execute("UPDATE ingestion SET status='failed',error=?,updated_at=CURRENT_TIMESTAMP WHERE url=?",(str(exc)[:500],url))
            await asyncio.sleep(.25)
        # Compare against the full sitemap listing, never only the current article batch.
        removed=(set(old)-set(all_urls)) if can_reconcile else set()
        if removed:
            with connect() as db:
                db.executemany("UPDATE articles SET active=0,updated_at=CURRENT_TIMESTAMP WHERE url=?",[(u,) for u in removed])
            counts["removed"]=len(removed)
        with connect() as db:
            db.execute("INSERT INTO settings(key,value) VALUES('daily_offset',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(next_offset),))
            db.execute("INSERT INTO settings(key,value) VALUES('last_sync_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(datetime.now().isoformat(timespec="seconds"),))
            db.execute("INSERT INTO settings(key,value) VALUES('last_sync_error','') ON CONFLICT(key) DO UPDATE SET value='' ")
        return {"processed":len(urls),"offset":start,"next_offset":next_offset,"reconciled_removals":can_reconcile,**counts,"note":"Article fetches are bounded by request.limit and rotate daily. Nested sitemap indexes are expanded before removal checks."}

@app.get("/ingestion/status")
def ingestion_status():
    with connect() as db:
        rows=[dict(r) for r in db.execute("SELECT status,count(*) AS count FROM ingestion GROUP BY status")]
        active=db.execute("SELECT count(*) FROM articles WHERE active=1 AND url NOT LIKE 'demo://%'").fetchone()[0]
        offset=db.execute("SELECT value FROM settings WHERE key='daily_offset'").fetchone()
        settings={row["key"]:row["value"] for row in db.execute("SELECT key,value FROM settings WHERE key IN ('last_sync_at','last_sync_error')")}
    return {"source":SITEMAP,"active_articles":active,"daily_offset":int(offset[0]) if offset else 0,"last_sync_at":settings.get("last_sync_at"),"last_sync_error":settings.get("last_sync_error"),"pages":rows}

@app.get("/",include_in_schema=False)
def home():
    from fastapi.responses import HTMLResponse
    return HTMLResponse((ROOT / "web" / "index.html").read_text(encoding="utf-8"))

