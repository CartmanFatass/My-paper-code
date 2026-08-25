"""Thin CLI for the frozen VSP05-B0 candidate-independent support map."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_05.support_map import main


if __name__ == "__main__":
    raise SystemExit(main())
