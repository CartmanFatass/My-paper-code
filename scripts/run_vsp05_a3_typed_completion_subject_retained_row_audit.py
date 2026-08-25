"""Thin one-shot CLI for the frozen VSP05-A3 retained-row offline audit."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_05.typed_completion_subject_retained_row_audit import main


if __name__ == "__main__":
    raise SystemExit(main())
