"""CQC entrypoint for the r016 metadata-only audit."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from orientbench.r016.metadata_audit import main


if __name__ == "__main__":
    main()
