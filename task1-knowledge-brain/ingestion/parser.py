"""Parse sitemap locations and readable article text for ingestion."""
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from multimodal.image_context import describe_image_reference


def parse_sitemap(xml: str) -> list[str]:
    root = ET.fromstring(xml)
    locations = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "loc" or not node.text:
            continue
        url = node.text.strip()
        if urlparse(url).scheme == "https":
            locations.append(url)
    return list(dict.fromkeys(locations))


def is_urlset(xml: str) -> bool:
    root = ET.fromstring(xml)
    return root.tag.rsplit("}", 1)[-1] == "urlset"


def article_text(html: str, base_url: str = "") -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script,style,nav,footer,header,aside"):
        node.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    title = (soup.title.get_text(" ", strip=True) if soup.title else "Untitled article")[:300]
    chunks = []
    for node in main.select("h1,h2,h3,p,li,td,th,img[alt]"):
        if node.name == "img":
            value = describe_image_reference(node.get("alt", ""), node.get("src", ""), base_url)
        else:
            value = node.get_text(" ", strip=True)
        if value:
            chunks.append(value)
    return title, "\n".join(chunks)[:50000]
