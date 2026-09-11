"""Fresh paired recurrent PPO with direct native-return measurement."""
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import time

import torch

from .omrc_b01 import addressing, engine
from .omrc_b01.b1_contract import B1_RUN_NAME
from .omrc_b01.checkpoint import capture_checkpoint, load_checkpoint, save_checkpoint
from .omrc_b01.contract import Action
from .omrc_b01.evaluator import evaluate_episode
from .omrc_b01.host import DynamicHost
from .omrc_b01.model import CommonRecurrentActorCritic
from .omrc_b01.ppo import PPOConfig, RecurrentPPOTrainer

OBJECT = "CBSC-DIRECT-RETURN-B02"
B03_OBJECT = "CBSC-DIRECT-RETURN-B03"
ARMS = ("RAW-GRU", "STRUCT-CURRENTNESS-GRU")
COST_LAW = (
    "startup + host_generation + sum_updates(project8 + rollout8 + PPO4x4) "
    "+ sum_checkpoints(eval_panel + checkpoint_io) + context_RAW "
    "+ publication_readback + pairing_STRUCT + process_finish"
)


def expected_seed(object_id=OBJECT, engineering=False):
    if object_id == OBJECT:
        return 21201 if engineering else 21203
    if object_id == B03_OBJECT and not engineering:
        return 21209
    raise ValueError("unknown direct-return object or engineering profile")


def fraction(value):
    return Fraction(value["numerator"], value["denominator"])


def fraction_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator,
            "float": float(value)}


def native_record(tape, names):
    """Only the evaluator receives truth; the policy supplied action names."""
    result = evaluate_episode(tape, [Action[name] for name in names])
    decision = sum((fraction(row["decision_reward"]) for row in result["decisions"]), Fraction())
    settlement = sum((fraction(row["settlement_reward"]) for row in result["decisions"]), Fraction())
    if decision + settlement != fraction(result["return"]):
        raise ValueError("native return omitted a decision or settlement contribution")
    return {"identity": result["identity"], "actions": names,
            "native_return": result["return"], "decision_sum": fraction_record(decision),
            "settlement_sum": fraction_record(settlement), "action_counts": result["action_counts"]}


def write_read(path, value):
    path.write_text(json.dumps(value, allow_nan=False, indent=2) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def pair_results(raw, structured):
    for key in ("object", "seed", "rng_namespace", "profile", "configuration",
                "initialization_digest", "training_tape_digest", "evaluation_tape_digest",
                "launch_sha", "updates", "eval_episodes", "counters"):
        if raw[key] != structured[key]:
            raise ValueError(f"paired primary measurement identity differs: {key}")
    if (raw["arm"], structured["arm"]) != ARMS:
        raise ValueError("paired comparison requires RAW then STRUCT")
    if any(arm["evaluations"][-1]["update"] != arm["updates"] for arm in (raw, structured)):
        raise ValueError("paired measurement must use the declared final update")
    raw_rows = raw["evaluations"][-1]["episodes"]
    struct_rows = structured["evaluations"][-1]["episodes"]
    if len(raw_rows) != raw["eval_episodes"] or len(struct_rows) != len(raw_rows):
        raise ValueError("paired endpoint episode coverage differs")
    differences = []
    for left, right in zip(raw_rows, struct_rows, strict=True):
        if left["identity"] != right["identity"]:
            raise ValueError("paired endpoint tapes differ")
        difference = fraction(right["native_return"]) - fraction(left["native_return"])
        differences.append({"identity": left["identity"], "raw_return": left["native_return"],
                            "struct_return": right["native_return"], "difference": fraction_record(difference)})
    mean = sum((fraction(row["difference"]) for row in differences), Fraction()) / len(differences)
    return {"object": raw["object"], "seed": raw["seed"], "profile": raw["profile"],
            "independent_training_seeds": 1, "endpoint_update": raw["updates"],
            "differences": differences, "mean_difference": fraction_record(mean),
            "curves": {arm["arm"]: arm["curve"] for arm in (raw, structured)},
            "context": raw["context"], "launch_shas": [raw["launch_sha"], structured["launch_sha"]]}


def run_arm(*, arm, seed, output, launch_sha, raw_result=None, engineering=False, started=None,
            object_id=OBJECT):
    started = time.perf_counter() if started is None else started
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    updates, eval_episodes = (1, 1) if engineering else (48, 32)
    checkpoints = (0, 1) if engineering else (0, 12, 24, 48)
    if seed != expected_seed(object_id, engineering) or arm not in ARMS:
        raise ValueError("arm or seed differs from the selected direct-return profile")
    if (arm == ARMS[1]) != (raw_result is not None):
        raise ValueError("STRUCT requires the completed RAW result")
    host_start = time.perf_counter()
    host = DynamicHost(B1_RUN_NAME, seed)
    train_tapes = tuple(host.build_stochastic(addressing.TRAIN, e) for e in range(updates * 8))
    eval_tapes = tuple(host.build_stochastic(addressing.EVAL_STOCHASTIC, e) for e in range(eval_episodes))
    training_digest = engine._tape_primitive_digest(train_tapes)
    _, action_digest, _ = engine._training_action_uniforms(train_tapes, B1_RUN_NAME, seed)
    host_seconds = time.perf_counter() - host_start
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    trainer = RecurrentPPOTrainer(model, run_name=B1_RUN_NAME, seed=seed, address_u64=addressing.u64)
    initial = torch.cat([p.detach().flatten() for p in model.parameters()]).clone()
    initial_norm = float(torch.linalg.vector_norm(initial))
    projection_start = time.perf_counter()
    eval_observations, eval_work = engine._project_panel(eval_tapes, engine._ADAPTERS[arm])
    eval_projection_seconds = time.perf_counter() - projection_start
    evaluations, curve, checkpoint_records, update_records = [], [], [], []
    context = {}
    if arm == ARMS[0]:
        for label, action in (("ALWAYS_REFRESH", "REFRESH"), ("ALWAYS_SAFE", "SAFE_FALLBACK")):
            context[label] = [native_record(tape, [action] * 24) for tape in eval_tapes]
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
            payload = capture_checkpoint(trainer, arm=arm, training_tape_digest=training_digest,
                                         action_uniform_digest=action_digest)
            save_checkpoint(path, payload)
            reread = load_checkpoint(path)
            if reread["counters"] != asdict(trainer.counters):
                raise ValueError("checkpoint readback lost actual counters")
            checkpoint_records.append({"update": update, "path": path.name,
                                       "counters": reread["counters"], "wall_seconds": time.perf_counter() - checkpoint_start})
        if update == updates:
            break
        update_start = time.perf_counter()
        batch = train_tapes[8 * update:8 * update + 8]
        observations, work = engine._project_panel(batch, engine._ADAPTERS[arm])
        rollout, evidence, uniform_digest = engine._rollout_from_panel(
            batch, observations, model, run_name=B1_RUN_NAME, seed=seed)
        losses = trainer.train_rollout(rollout)
        record = {"update": update, "episode_ids": rollout.episode_ids.tolist(),
                  "adapter_work": asdict(work), "losses": [asdict(loss) for loss in losses],
                  "counters": asdict(trainer.counters), "actions": evidence["actions"],
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
    result = {"object": object_id, "arm": arm, "seed": seed, "rng_namespace": B1_RUN_NAME,
              "profile": "ENGINEERING_ONLY" if engineering else "B/EXPLORE", "launch_sha": launch_sha,
              "configuration": asdict(PPOConfig()), "updates": updates, "eval_episodes": eval_episodes,
              "initialization_digest": model.initialization_digest, "training_tape_digest": training_digest,
              "evaluation_tape_digest": engine._tape_primitive_digest(eval_tapes),
              "execution": {"torch_threads": torch.get_num_threads(), "dtype": str(initial.dtype),
                            "device": str(initial.device)},
              "parameter_count": model.active_parameter_count, "initial_parameter_l2": initial_norm,
              "parameter_movement_l2": movement, "relative_parameter_movement": movement / initial_norm,
              "changed_parameters": int(torch.count_nonzero(final != initial)),
              "counters": asdict(trainer.counters), "evaluation_executions": len(evaluations) * eval_episodes,
              "evaluation_transitions": len(evaluations) * eval_episodes * 152,
              "eval_adapter_work": asdict(eval_work), "evaluations": evaluations,
              "curve": curve, "checkpoints": checkpoint_records, "context": context,
              "cost": {"law": COST_LAW, "host_seconds": host_seconds,
                       "eval_projection_seconds": eval_projection_seconds, "updates": update_records,
                       "measured_seconds_per_update": sum(r["wall_seconds"] for r in update_records) / updates,
                       "peak_rss_bytes": peak_rss, "resources_unmeasured": peak_rss is None}}
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
