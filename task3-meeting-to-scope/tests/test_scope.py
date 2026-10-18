import importlib.util
import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))
APP_PATH = TASK_ROOT / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("meeting_scope_test_app", APP_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ScopeWorkflowTests(unittest.TestCase):
    def test_extracts_requirement_with_source_text(self):
        text = "We need to add a location filter for members."
        requirements, _ = MODULE.extract(text)
        self.assertTrue(requirements)
        self.assertIn("location filter", requirements[0].description)
        self.assertTrue(requirements[0].source_excerpt)

    def test_follow_up_helper_marks_new_requirement(self):
        requirements, _ = MODULE.extract("We need to add a location filter for members.")
        new, _ = MODULE.extract("Please add a CSV export for account owners.")
        changes = MODULE.compare_requirements(requirements, new)
        self.assertTrue(any(change["type"] == "added_out_of_scope" for change in changes))


if __name__ == "__main__":
    unittest.main()
