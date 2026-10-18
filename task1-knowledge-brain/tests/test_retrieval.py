import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from retrieval.search import rank_sources


class RetrievalTests(unittest.TestCase):
    def test_relevant_article_ranks_first(self):
        rows = [
            {"title": "Changing your site logo", "url": "demo://logo", "body": "Update the site logo in design settings.", "query": ""},
            {"title": "Payment setup", "url": "demo://payments", "body": "Review provider settings.", "query": ""},
        ]
        ranked = rank_sources("How do I update my site logo?", rows, 3)
        self.assertEqual(ranked[0]["url"], "demo://logo")

    def test_weak_single_word_overlap_is_filtered(self):
        rows = [{"title": "Payments", "url": "demo://payments", "body": "Review the payment provider.", "query": ""}]
        self.assertEqual(rank_sources("Can I get a refund for a duplicate payment?", rows, 3), [])


if __name__ == "__main__":
    unittest.main()
