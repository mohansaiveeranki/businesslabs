"""Turn a reviewed scope draft into plain proposal text."""


def render_proposal(project_id, requirements, questions, low, high, currency, hourly_rate):
    cost_low = low * hourly_rate
    cost_high = high * hourly_rate
    deliverables = "\n".join(
        f"- {item.description} ({item.kind}, {item.hours}h)" for item in requirements
    )
    questions_text = "\n".join(f"- {question}" for question in questions)
    if not questions_text:
        questions_text = "- No open questions were picked up automatically. Please review the scope before sharing it."
    return (
        f"## Project proposal: {project_id}\n\n"
        f"### What we plan to deliver\n{deliverables}\n\n"
        f"### Estimate\n{low}-{high} hours; {currency} {cost_low:,.0f}-{cost_high:,.0f}, "
        f"based on {currency} {hourly_rate:g} per hour. This is an estimate for planning, not a final quote.\n\n"
        f"### Questions to confirm\n{questions_text}\n\n"
        "### Next step\nA reviewer should approve the scope and estimate before this is sent to the client."
    )
