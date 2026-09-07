"""Run exactly one frozen native-return seed, or its distinct technical profile."""

import time

STARTED = time.perf_counter()

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def publish(path, summary):
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    updates, eval_episodes, cap = (2, 16, 60.) if args.profile == "technical" else (1024, 4096, 600.)
    summary = dict(object_id="UCOPE-NATIVE-RETURN-ACQUISITION-B01", seed=args.seed,
                   profile=args.profile, status="INCOMPLETE", batch_branch="INCOMPLETE",
                   joint_optimizer_steps=0, tail_active_batches=0, evaluation={},
                   selected_updates=updates, selected_eval_episodes_per_context_per_policy=eval_episodes,
                   cost_law="T_init + 1024*T_batch256 + 32768*T_eval_pair + T_publish",
                   resources_status="resources_unmeasured")
    actor = initial = None

    def check_time():
        if time.perf_counter() - STARTED >= cap:
            raise TimeoutError(f"complete invocation wall cap {cap:g}s reached")

    try:
        import torch
        from experiments.candidates.ucope.native_return_acquisition_b01.learner import (
            Actor, collect_batch, movement, new_counts, parameter_vectors,
        )
        from experiments.candidates.ucope.native_return_acquisition_b01.evaluation import evaluate

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        summary["launch_sha"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip()
        summary["runtime"] = dict(torch=torch.__version__, python=sys.version, device="cpu",
                                  dtype="float32", intraop_threads=torch.get_num_threads(),
                                  interop_threads=torch.get_num_interop_threads())
        summary["training_counts"] = new_counts()
        check_time()
        actor = Actor(args.seed)
        initial = parameter_vectors(actor)
        optimizer = torch.optim.Adam(actor.parameters(), lr=.003, betas=(.9, .999), eps=1e-8,
                                     weight_decay=0, amsgrad=False, foreach=False)
        root_rng = torch.Generator(device="cpu").manual_seed(args.seed + 1_000_000)
        tail_rng = torch.Generator(device="cpu").manual_seed(args.seed + 2_000_000)
        summary["initialization_wall_seconds"] = time.perf_counter() - STARTED
        training_start = time.perf_counter()
        with (out / "training.jsonl").open("w", encoding="utf-8") as log:
            for update in range(updates):
                check_time()
                loss, returns, probes = collect_batch(actor, args.seed, update, root_rng, tail_rng,
                                                      summary["training_counts"])
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                summary["joint_optimizer_steps"] += 1
                summary["tail_active_batches"] += int(probes > 0)
                log.write(json.dumps(dict(update=update + 1, mean_native_return=float(returns.mean()),
                                          probe_count=probes, **summary["training_counts"])) + "\n")
                log.flush()
        summary["training_wall_seconds"] = time.perf_counter() - training_start
        check_time()
        torch.save(actor.state_dict(), out / "final_parameters.pt")
        summary["final_parameters"] = "final_parameters.pt"
        evaluation_start = time.perf_counter()
        evaluate(actor, args.seed, eval_episodes, summary["evaluation"], check_time)
        summary["evaluation_wall_seconds"] = time.perf_counter() - evaluation_start
        check_time()
        summary["status"] = "TECHNICAL_COMPLETE" if args.profile == "technical" else "COMPLETE"
    except Exception as exc:
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["status"] = "INCOMPLETE"
    finally:
        if actor is not None and initial is not None:
            summary["exposure"] = movement(actor, initial, summary["joint_optimizer_steps"])
        summary["wall_seconds"] = time.perf_counter() - STARTED
        publish(out / "summary.json", summary)
        summary["wall_seconds"] = time.perf_counter() - STARTED
        if summary["wall_seconds"] >= cap:
            summary.update(status="INCOMPLETE", error=f"complete invocation wall cap {cap:g}s reached")
        publish(out / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("seed", "profile", "status", "wall_seconds")}))
    return 1 if summary["status"] == "INCOMPLETE" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--profile", choices=("science", "technical"), default="science")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    allowed = (9006301,) if args.profile == "technical" else (6301, 6302)
    if args.seed not in allowed:
        parser.error(f"{args.profile} profile requires seed in {allowed}")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
