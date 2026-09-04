"""Thin one-shot CLI for the frozen VSP05-A4 blind DTO admission audit."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_05.blind_portable_locator_dto_retained_field_admission import main


if __name__ == "__main__":
    raise SystemExit(main())
