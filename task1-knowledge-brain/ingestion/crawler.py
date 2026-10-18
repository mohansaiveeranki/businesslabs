"""Fetch a sitemap and expand nested sitemap indexes into article URLs."""
from collections import deque

import httpx

from ingestion.parser import is_urlset, parse_sitemap


async def fetch_sitemap_urls(client: httpx.AsyncClient, sitemap_url: str, max_sitemaps: int = 100) -> tuple[list[str], bool]:
    pending = deque([sitemap_url])
    visited: set[str] = set()
    article_urls: list[str] = []
    saw_urlset = False

    while pending and len(visited) < max_sitemaps:
        url = pending.popleft()
        if url in visited:
            continue
        visited.add(url)
        response = await client.get(url)
        response.raise_for_status()
        xml = response.text
        locations = parse_sitemap(xml)
        if is_urlset(xml):
            saw_urlset = True
            article_urls.extend(locations)
        else:
            pending.extend(location for location in locations if location not in visited)

    if pending:
        raise ValueError(f"Sitemap index exceeds the limit of {max_sitemaps} files")
    return list(dict.fromkeys(article_urls)), saw_urlset
