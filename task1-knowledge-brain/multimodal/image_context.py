"""Capture image context available in HTML; this is not vision-model analysis."""
from urllib.parse import urljoin


def describe_image_reference(alt: str, source: str, page_url: str) -> str:
    return f"Image context: {alt.strip()} | Image URL: {urljoin(page_url, source)}"
