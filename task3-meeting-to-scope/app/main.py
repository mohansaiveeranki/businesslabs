"""API routes for preparing and reviewing a project scope."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

TASK_ROOT = Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))
from agents.extraction import extract_requirements
from agents.feasibility import check_feasibility
from agents.proposal import render_proposal

# The folder follows the assignment's hyphenated name, which cannot be a
# regular Python import. Load its comparison helper directly from its path.
_diff_path = TASK_ROOT / "scope-diff" / "compare.py"
_diff_spec = importlib.util.spec_from_file_location("scope_diff_compare", _diff_path)
if _diff_spec is None or _diff_spec.loader is None:
    raise ImportError(f"Could not load scope comparison helper from {_diff_path}")
_diff_module = importlib.util.module_from_spec(_diff_spec)
sys.modules[_diff_spec.name] = _diff_module
_diff_spec.loader.exec_module(_diff_module)
compare_requirements = _diff_module.compare_requirements

router = APIRouter(prefix="/scope", tags=["meeting-to-scope"])
KB = "http://127.0.0.1:8000"


class BuildRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=100)
    transcript: str = Field(min_length=30, max_length=100000)
    hourly_rate: float = Field(default=100, gt=0, le=10000)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class Requirement(BaseModel):
    id: str
    description: str
    acceptance_criteria: list[str]
    source_excerpt: str
    hours: int = Field(ge=1)
    kind: Literal["configuration", "custom", "unknown"]
    feasibility_status: Literal["unverified", "supported", "not_found", "unavailable"] = "unverified"
    knowledge_sources: list[dict[str, str | float]] = Field(default_factory=list)


class ScopeResult(BaseModel):
    project_id: str
    requirements: list[Requirement]
    open_questions: list[str]
    total_hours: int
    estimate_range: tuple[int, int]
    proposal: str
    approved: bool = False


class Approval(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    approved: bool


class FollowUpRequest(BaseModel):
    transcript: str = Field(min_length=20, max_length=100000)


BASELINES: dict[str, ScopeResult] = {}
APPROVALS: dict[str, str] = {}


def extract(text: str) -> tuple[list[Requirement], list[str]]:
    extracted, questions = extract_requirements(text)
    requirements = []
    for index, (description, excerpt) in enumerate(extracted, 1):
        configuration = bool(re.search(r"setting|enable|turn on|configure|existing|filter", description, re.I))
        hours = 4 if configuration else 12
        requirements.append(Requirement(
            id=f"REQ-{index:02}",
            description=description,
            acceptance_criteria=[f"Client and reviewer can verify: {description.rstrip('.')} .".replace(" .", ".")],
            source_excerpt=excerpt,
            hours=hours,
            kind="configuration" if configuration else "unknown",
        ))
    return requirements, questions


@router.post("/build", response_model=ScopeResult)
async def build(request: BuildRequest):
    requirements, questions = extract(request.transcript)
    requirements = [await check_feasibility(item, KB) for item in requirements]
    total = sum(item.hours for item in requirements)
    low = max(1, round(total * 0.8))
    high = max(total, round(total * 1.4))
    proposal = render_proposal(request.project_id, requirements, questions, low, high, request.currency, request.hourly_rate)
    result = ScopeResult(
        project_id=request.project_id,
        requirements=requirements,
        open_questions=questions,
        total_hours=total,
        estimate_range=(low, high),
        proposal=proposal,
    )
    BASELINES[request.project_id] = result
    return result


@router.post("/{project_id}/follow-up")
async def follow_up(project_id: str, request: FollowUpRequest):
    baseline = BASELINES.get(project_id)
    if not baseline:
        raise HTTPException(404, "Project baseline not found")
    new_requirements, _ = extract(request.transcript)
    changes = compare_requirements(baseline.requirements, new_requirements)
    return {
        "project_id": project_id,
        "changes": changes,
        "baseline_approved": project_id in APPROVALS,
        "requires_human_approval": True,
    }


@router.post("/{project_id}/approve")
def approve(project_id: str, request: Approval):
    if project_id not in BASELINES:
        raise HTTPException(404, "Project baseline not found")
    if request.approved:
        APPROVALS[project_id] = request.reviewer
    else:
        APPROVALS.pop(project_id, None)
    return {"project_id": project_id, "approved": request.approved, "reviewer": request.reviewer}
