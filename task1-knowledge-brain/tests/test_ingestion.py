import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from ingestion.parser import article_text, is_urlset, parse_sitemap
from ingestion.crawler import fetch_sitemap_urls


class IngestionParserTests(unittest.TestCase):
    def test_sitemap_keeps_unique_https_locations(self):
        xml = """<urlset><url><loc>https://example.com/a</loc></url><url><loc>https://example.com/a</loc></url><url><loc>http://example.com/b</loc></url></urlset>"""
        self.assertEqual(parse_sitemap(xml), ["https://example.com/a"])
        self.assertTrue(is_urlset(xml))

    def test_article_parser_keeps_text_and_image_alt_context(self):
        html = '<html><head><title>Help</title></head><body><nav>Ignore</nav><main><h1>Logo</h1><p>Upload a square image.</p><img src="/logo.png" alt="Logo upload button"></main></body></html>'
        title, body = article_text(html, "https://example.com/help")
        self.assertEqual(title, "Help")
        self.assertIn("Upload a square image", body)
        self.assertIn("Logo upload button", body)
        self.assertIn("https://example.com/logo.png", body)
        self.assertNotIn("Ignore", body)


class SitemapCrawlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_expands_nested_sitemap_indexes(self):
        pages = {
            "https://example.com/sitemap.xml": '<sitemapindex><sitemap><loc>https://example.com/articles.xml</loc></sitemap></sitemapindex>',
            "https://example.com/articles.xml": '<urlset><url><loc>https://example.com/help/a</loc></url><url><loc>https://example.com/help/b</loc></url></urlset>',
        }

        class Response:
            def __init__(self, text):
                self.text = text

            def raise_for_status(self):
                pass

        class Client:
            async def get(self, url):
                return Response(pages[url])

        urls, complete = await fetch_sitemap_urls(Client(), "https://example.com/sitemap.xml")
        self.assertEqual(urls, ["https://example.com/help/a", "https://example.com/help/b"])
        self.assertTrue(complete)


if __name__ == "__main__":
    unittest.main()
