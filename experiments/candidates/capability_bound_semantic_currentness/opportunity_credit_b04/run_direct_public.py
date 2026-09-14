"""One complete arm of CBSC public-stream opportunity-credit B01."""
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import sys
import time

import torch

from ..omrc_b01 import addressing, engine
from ..omrc_b01.b1_contract import B1_RUN_NAME
from ..omrc_b01.model import CommonRecurrentActorCritic
from .learner import OpportunityTrainer
from .snapshot import snapshot_readback
from .run import (
    ARMS, COST_LAW, fraction, fraction_record, write_read,
    pair_results, compare_rule, read_training_records,
)
from .direct_public import DirectPublicHost, project_panel, request_only, native_record

OBJECT = "CBSC-OPPORTUNITY-CREDIT-PUBLIC-STREAM-B01"
FORMAL_SEED = 2026091231
REPRESENTATION_PATH = "opportunity_credit_b04/direct_public.py"

def run_arm(*, arm, seed, output, launch_sha, raw_result=None, started=None):
    started = time.perf_counter() if started is None else started
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    updates, eval_episodes = 48, 32
    checkpoints = (0, 48)
    if seed != FORMAL_SEED or arm not in ARMS:
        raise ValueError("arm or seed differs from the selected direct-return profile")
    if (arm == ARMS[1]) != (raw_result is not None):
        raise ValueError("STRUCT requires the completed RAW result")
    object_name = OBJECT
    runtime = {"python_executable": sys.executable, "python_version": sys.version,
               "torch_version": str(torch.__version__)}
    host_start = time.perf_counter()
    host = DirectPublicHost(B1_RUN_NAME, seed)
    train_tapes = tuple(host.build_stochastic(addressing.TRAIN, e) for e in range(updates * 8))
    eval_tapes = tuple(host.build_stochastic(addressing.EVAL_STOCHASTIC, e) for e in range(eval_episodes))
    training_digest = engine._tape_primitive_digest(train_tapes)
    _, action_digest, _ = engine._training_action_uniforms(train_tapes, B1_RUN_NAME, seed)
    host_seconds = time.perf_counter() - host_start
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    trainer = OpportunityTrainer(model, run_name=B1_RUN_NAME, seed=seed, address_u64=addressing.u64)
    initial = torch.cat([p.detach().flatten() for p in model.parameters()]).clone()
    initial_norm = float(torch.linalg.vector_norm(initial))
    projection_start = time.perf_counter()
    eval_observations, eval_work = project_panel(eval_tapes, arm)
    eval_projection_seconds = time.perf_counter() - projection_start
    evaluations, curve, checkpoint_records, update_records = [], [], [], []
    context = {}
    if arm == ARMS[0]:
        for label, action in (("ALWAYS_REFRESH", "REFRESH"), ("ALWAYS_SAFE", "SAFE_FALLBACK")):
            context[label] = [native_record(tape, [action] * 24) for tape in eval_tapes]
        context["REQUEST_ONLY"] = [native_record(tape, request_only(tape.public_rows))
                                   for tape in eval_tapes]
    else:
        context = json.loads(Path(raw_result).read_text(encoding="utf-8"))["context"]
    for update in range(updates + 1):
        if update in checkpoints:
            evaluation_start = time.perf_counter()
            optimizer_before = engine._optimizer_digest(trainer)
            traces, state = engine._evaluate_heldout(eval_tapes, eval_observations, model)
            optimizer_after = engine._optimizer_digest(trainer)
            engine.assert_unchanged_state(optimizer_before, optimizer_after, label="evaluation optimizer")
            episodes = [native_record(tape, trace["decision_actions"])
                        for tape, trace in zip(eval_tapes, traces, strict=True)]
            actions = Counter()
            for episode in episodes:
                actions.update(episode["action_counts"])
            mean = sum((fraction(row["native_return"]) for row in episodes), Fraction()) / eval_episodes
            evaluations.append({"update": update, "episodes": episodes, "state": state,
                                "optimizer_before": optimizer_before, "optimizer_after": optimizer_after,
                                "action_counts": dict(actions), "wall_seconds": time.perf_counter() - evaluation_start})
            curve.append({"update": update, "mean_native_return": fraction_record(mean)})
            checkpoint_start = time.perf_counter()
            path = output / f"update-{update}.pt"
            reread = snapshot_readback(path, trainer, object_name=object_name,
                                       runtime=runtime, representation_path=REPRESENTATION_PATH,
                                       arm=arm, launch_sha=launch_sha,
                                       training_tape_digest=training_digest,
                                       action_uniform_digest=action_digest)
            checkpoint_records.append({"update": update, "path": path.name,
                                       "counters": reread["counters"], "wall_seconds": time.perf_counter() - checkpoint_start})
        if update == updates:
            break
        update_start = time.perf_counter()
        batch = train_tapes[8 * update:8 * update + 8]
        observations, work = project_panel(batch, arm)
        rollout, evidence, uniform_digest = engine._rollout_from_panel(
            batch, observations, model, run_name=B1_RUN_NAME, seed=seed)
        losses = trainer.train_rollout(rollout)
        record = {"update": update, "episode_ids": rollout.episode_ids.tolist(),
                  "adapter_work": asdict(work), "losses": [asdict(loss) for loss in losses],
                  "counters": asdict(trainer.counters), "actions": evidence["actions"],
                  "targets": trainer.last_targets.value_targets[:, 12::6].tolist(),
                  "old_decision_values": rollout.old_values[:, 12::6].tolist(),
                  "unnormalized_advantages": trainer.last_targets.advantages[:, 12::6].tolist(),
                  "normalized_advantages": trainer.last_targets.decision_advantages[:, 12::6].tolist(),
                  "reward_rows": evidence["rewards"], "action_uniform_digest": uniform_digest,
                  "observation_shape": list(observations.shape), "observation_dtype": str(observations.dtype),
                  "wall_seconds": time.perf_counter() - update_start}
        with (output / "updates.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        update_records.append({"update": update, "wall_seconds": record["wall_seconds"]})
    final = torch.cat([p.detach().flatten() for p in model.parameters()])
    movement = float(torch.linalg.vector_norm(final - initial))
    try:
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        peak_rss = None
    result = {"object": object_name, "arm": arm, "seed": seed, "rng_namespace": B1_RUN_NAME,
              "profile": "B/EXPLORE", "launch_sha": launch_sha,
              "configuration": asdict(trainer.config), "updates": updates, "eval_episodes": eval_episodes,
              "initialization_digest": model.initialization_digest, "training_tape_digest": training_digest,
              "evaluation_tape_digest": engine._tape_primitive_digest(eval_tapes),
              "representation_path": REPRESENTATION_PATH,
              "execution": {"torch_threads": torch.get_num_threads(), "dtype": str(initial.dtype),
                            "device": str(initial.device), **runtime},
              "parameter_count": model.active_parameter_count, "initial_parameter_l2": initial_norm,
              "final_parameter_l2": float(torch.linalg.vector_norm(final)),
              "parameter_movement_l2": movement, "relative_parameter_movement": movement / initial_norm,
              "changed_parameters": int(torch.count_nonzero(final != initial)),
              "minibatch_order_digest": trainer.minibatch_order_digest,
              "action_uniform_digest": action_digest,
              "counters": asdict(trainer.counters), "evaluation_executions": len(evaluations) * eval_episodes,
              "evaluation_transitions": len(evaluations) * eval_episodes * 152,
              "eval_adapter_work": asdict(eval_work), "evaluations": evaluations,
              "curve": curve, "checkpoints": checkpoint_records, "context": context,
              "cost": {"law": COST_LAW, "host_seconds": host_seconds,
                       "eval_projection_seconds": eval_projection_seconds, "updates": update_records,
                       "measured_seconds_per_update": sum(r["wall_seconds"] for r in update_records) / updates,
                       "peak_rss_bytes": peak_rss, "resources_unmeasured": peak_rss is None}}
    result["context_means"] = {
        label: fraction_record(sum((fraction(row["native_return"]) for row in rows), Fraction()) / len(rows))
        for label, rows in context.items()}
    result["request_only_comparison"] = compare_rule(evaluations[-1]["episodes"], context["REQUEST_ONLY"])
    result["training_action_counts"] = read_training_records(output / "updates.jsonl", updates)
    result = write_read(output / "summary.json", result)
    if arm == ARMS[1]:
        raw = json.loads(Path(raw_result).read_text(encoding="utf-8"))
        paired = pair_results(raw, result)
        reread = write_read(output / "paired_summary.json", paired)
        if reread["mean_difference"] != paired["mean_difference"]:
            raise ValueError("paired primary measurement readback differs")
    result["cost"]["wall_seconds_through_primary_readback"] = time.perf_counter() - started
    result = write_read(output / "summary.json", result)
    return result
