from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[1] / ".research_core"
sys.path.insert(0, str(CORE))

from runtime.cli import main


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
