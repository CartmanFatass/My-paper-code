"""One Linux synthetic cost measurement; never loads scientific coefficients."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.acvc.history_upper_prefix_assessment_r03.arithmetic import (
    prefix_bound, structural_counts, synthetic_inputs,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true", help="Only the one toy publication test")
    args = parser.parse_args()
    import resource
    rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    started = time.perf_counter()

    def check():
        if time.perf_counter() - started >= 40 or rss() >= 0.75 * 1024**3:
            raise TimeoutError("synthetic cost cap")

    contexts, prefix = (1, 2) if args.smoke else (12, 4)
    status = "complete"
    try:
        inputs = synthetic_inputs(contexts=contexts, check=check)
        prefix_bound(*inputs, prefix=prefix, check=check)  # Discard all objective/action values.
    except TimeoutError:
        status = "cost_cap_reached"
    summary = {"status": status, "wall_seconds": time.perf_counter() - started,
               "peak_rss_bytes": rss(),
               "static_counts": structural_counts(2 * contexts, contexts, 3, prefix)}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if status == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
