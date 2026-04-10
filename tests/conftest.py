from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = REPO_ROOT / "examples" / "hello_regression"

for path in (str(REPO_ROOT), str(EXAMPLE_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)
