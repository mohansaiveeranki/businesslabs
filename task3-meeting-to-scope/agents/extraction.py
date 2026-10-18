"""Rule-based requirement extraction with source text preserved for review."""
import re
from difflib import SequenceMatcher


def extract_requirements(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    chunks = [text[index:index + 5000] for index in range(0, len(text), 4500)]
    pattern = re.compile(
        r"(?:we need(?: to)?|we want(?: to)?|we'd like|we would like|please|add|build|change|make|also need|want(?:s| to)?|our team wants|marketing team wants|we decided)\s+([^.!?\n]{8,220})",
        re.I,
    )
    raw = []
    for chunk in chunks:
        raw.extend((match.group(1).strip(), match.group(0).strip()) for match in pattern.finditer(chunk))

    unique: list[tuple[str, str]] = []
    for description, excerpt in raw:
        if not any(SequenceMatcher(None, description.lower(), old[0].lower()).ratio() > 0.86 for old in unique):
            unique.append((description, excerpt))

    questions = []
    if not unique:
        questions.append("No actionable requirement was extracted; clarify the desired outcome and user workflow.")
    if re.search(r"better|fast|easy|improve|seamless", text, re.I):
        questions.append("Define measurable acceptance criteria for subjective terms such as better, faster or easier.")
    if re.search(r"integrat|payment|crm|api", text, re.I):
        questions.append("Confirm vendor, access, data fields and failure behavior for the integration.")
    return unique, questions
