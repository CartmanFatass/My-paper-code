"""Thin CLI for the frozen VSP05-A2 lifecycle-phase treatment."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_05.lifecycle_phase_support_discrimination import main


if __name__ == "__main__":
    raise SystemExit(main())
