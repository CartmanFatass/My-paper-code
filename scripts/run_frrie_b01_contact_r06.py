"""Entry point for the frozen FRRIE contact-active R128 LR003 R06 object."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import main


if __name__ == "__main__":
    raise SystemExit(main(
        adam_lr=0.003,
        object_id="FRRIE-B01-CONTACT-ACTIVE-R128-LR003-R06-20260904",
        branch_prefix="R06",
    ))
