"""One fixed shared-data seed; admission and whole-process timeout are external."""

import time

STARTED = time.perf_counter()

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.candidates.ucope.shared_data_return_model_b02.model import (
    BATCHES, EVAL_EPISODES, OBJECT_ID, SEED, ReturnModel, collect,
)
from experiments.candidates.ucope.shared_data_return_model_b02.evaluation import evaluate, reading_rule


def publish(out, summary):
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(out, seed=SEED, object_id=OBJECT_ID):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    model = ReturnModel()
    summary = dict(object_id=object_id, seed=seed, independent_datasets=1, status="INCOMPLETE",
                   branch="INCOMPLETE", training={}, evaluation={},
                   selected_batches=BATCHES, selected_eval_episodes_per_context_policy=EVAL_EPISODES,
                   cost_law="T_init + 1024*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish",
                   resources_status="resources_unmeasured")

    def check_time():
        if time.perf_counter() - STARTED >= 600:
            raise TimeoutError("complete invocation 600s wall cap reached")

    try:
        summary["launch_sha"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip()
        summary["runtime"] = dict(python=sys.version, float_mantissa_bits=sys.float_info.mant_dig,
                                  device="cpu", compute_threads=1)
        check_time()
        collect(model, summary["training"], check_time, batches=BATCHES, seed=seed)
        check_time()
        summary["final_policies"] = model.final_policies()
        evaluate(summary["final_policies"], EVAL_EPISODES, summary["evaluation"], check_time, seed=seed)
        check_time()
        differences = summary["evaluation"]["differences"]
        rule = reading_rule(differences["delta_native"]["mean"], differences["delta_information"]["mean"],
                            summary["evaluation"]["counts"]["FULL"]["probe_episodes"])
        summary.update(rule)
        summary["status"] = "INCOMPLETE" if rule["branch"] == "INCOMPLETE" else "COMPLETE"
    except (Exception, KeyboardInterrupt) as exc:
        summary.update(status="INCOMPLETE", branch="INCOMPLETE", error=f"{type(exc).__name__}: {exc}")
    finally:
        summary["exposure"] = model.exposure()
        summary["learned_values_and_counts"] = vars(model)
        summary["wall_seconds"] = time.perf_counter() - STARTED
        publish(out, summary)
        summary["wall_seconds"] = time.perf_counter() - STARTED
        if summary["wall_seconds"] >= 600:
            summary.update(status="INCOMPLETE", branch="INCOMPLETE", error="complete invocation 600s wall cap reached")
        publish(out, summary)
    print(json.dumps({key: summary[key] for key in ("seed", "status", "branch", "wall_seconds")}))
    return 0 if summary["status"] == "COMPLETE" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, choices=(SEED,))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    return run(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
