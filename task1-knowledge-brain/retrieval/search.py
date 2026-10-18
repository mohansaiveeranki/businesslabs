"""Small lexical retrieval baseline used by the local demo."""
from collections.abc import Iterable, Mapping


def terms(text: str) -> set[str]:
    return {word.lower().strip(".,!?;:'\"()") for word in text.split() if len(word) > 2}


def rank_sources(question: str, rows: Iterable[Mapping[str, object]], top_k: int) -> list[dict[str, object]]:
    query_terms = terms(question)
    ranked: list[dict[str, object]] = []
    for row in rows:
        content = terms(f"{row['title']} {row['query']} {row['body']}")
        score = len(query_terms & content) / max(1, len(query_terms))
        # A single shared word is not enough evidence for a support answer.
        if score >= 0.34:
            ranked.append({
                "title": row["title"],
                "url": row["url"],
                "relevance": round(min(0.99, score), 3),
                "excerpt": str(row["body"])[:700],
            })
    return sorted(ranked, key=lambda source: source["relevance"], reverse=True)[:top_k]
