"""Entry point for the frozen FRRIE contact-active R128 object."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import main


if __name__ == "__main__":
    raise SystemExit(main())
