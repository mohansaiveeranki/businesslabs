"""Check each proposed requirement against the shared Knowledge Brain API."""
import httpx


async def check_feasibility(requirement, knowledge_api: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{knowledge_api}/query",
                json={"question": requirement.description, "top_k": 2},
            )
        if response.is_success:
            data = response.json()
            requirement.feasibility_status = "supported" if data.get("status") == "answered" else "not_found"
            requirement.knowledge_sources = data.get("sources", [])
            if data.get("status") == "answered" and requirement.kind == "unknown":
                requirement.kind = "configuration" if any(
                    "settings" in source["excerpt"].lower() or "configure" in source["excerpt"].lower()
                    for source in data.get("sources", [])
                ) else "custom"
    except Exception:
        requirement.feasibility_status = "unavailable"
    return requirement
