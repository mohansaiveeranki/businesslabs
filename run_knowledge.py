"""Load the Knowledge Brain from the assignment's hyphenated folder layout."""
import importlib.util
import sys
from pathlib import Path

module_path = Path(__file__).parent / "task1-knowledge-brain" / "app" / "main.py"
spec = importlib.util.spec_from_file_location("knowledge_brain_api", module_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load Knowledge Brain API from {module_path}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
app = module.app
