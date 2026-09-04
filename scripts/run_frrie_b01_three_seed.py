"""Entry point for one FRRIE B01 three-seed panel root."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.three_seed import main


if __name__ == "__main__":
    raise SystemExit(main())
