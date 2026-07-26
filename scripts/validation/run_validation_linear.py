import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.common import run_family_suite


if __name__ == "__main__":
    raise SystemExit(run_family_suite("linear"))
