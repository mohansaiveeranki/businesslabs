"""Compare requirements from a follow-up transcript with the approved baseline."""
from difflib import SequenceMatcher


def match_score(left: str, right: str) -> float:
    score = SequenceMatcher(None, left.lower(), right.lower()).ratio()
    anchors = ("location", "mobile", "search", "saved search", "alert", "export", "booking", "payment", "logo", "integration", "member")
    if any(anchor in left.lower() and anchor in right.lower() for anchor in anchors):
        score = max(score, 0.70)
    return score


def compare_requirements(baseline, follow_up) -> list[dict]:
    changes = []
    for item in follow_up:
        match = max(baseline, key=lambda old: match_score(item.description, old.description), default=None)
        ratio = match_score(item.description, match.description) if match else 0
        if ratio < 0.65:
            changes.append({"type": "added_out_of_scope", "requirement": item.model_dump()})
        elif ratio < 0.92:
            changes.append({"type": "modified", "baseline_id": match.id, "requirement": item.model_dump()})
    for old in baseline:
        if not any(match_score(old.description, new.description) >= 0.65 for new in follow_up):
            changes.append({"type": "not_repeated_in_follow_up", "baseline_id": old.id, "description": old.description})
    return changes
