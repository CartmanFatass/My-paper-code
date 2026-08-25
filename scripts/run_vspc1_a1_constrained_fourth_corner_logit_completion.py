"""Thin one-shot CLI for the frozen VSPC1-A1 fourth-corner audit."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_c1.constrained_fourth_corner_logit_completion import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
