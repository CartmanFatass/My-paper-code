"""Replay all three frozen endpoints on each block's common endpoint mixture."""

from __future__ import annotations

import json
import resource
import time
from pathlib import Path

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import initialization_fingerprint, make_config, optimizer_steps, preserved_rng, seed_everything, sha256_file
from .auxiliary import B03AuxiliaryReplay
from .facts import replay_facts
from .native import B03Spec, OBJECT_ID, _write_json, production_spec


def verify_run(root: Path, summary_sha256: str, *, arm: str, seed: int,
               expected_spec: B03Spec, training_sha: str, training_device: str):
    root = Path(root)
    if sha256_file(root / "summary.json") != summary_sha256:
        raise ValueError(f"{arm} summary identity mismatch")
    summary = json.loads((root / "summary.json").read_text())
    if (summary["object_id"], summary["status"], summary["arm"], summary["seed"]) != (OBJECT_ID, "COMPLETE", arm, seed):
        raise ValueError(f"{arm} source run identity/status mismatch")
    if summary["launch_sha"] != training_sha:
        raise ValueError(f"{arm} source launch SHA mismatch")
    expected = {"config.json": summary["config_sha256"], "facts.npz": summary["facts_sha256"],
                "calibration.json": summary["calibration_sha256"],
                "endpoint_facts.npz": summary["endpoint_facts_sha256"]}
    expected.update({f"checkpoint_final/{name}": digest for name, digest in summary["checkpoint_sha256"].items()})
    for name, digest in expected.items():
        if sha256_file(root / name) != digest:
            raise ValueError(f"{arm} artifact identity mismatch: {name}")
    config = json.loads((root / "config.json").read_text())
    values = dict(config["spec"])
    for key in ("eval_seeds", "fact_seeds", "endpoint_fact_seeds", "final_seeds", "eval_rollouts"):
        values[key] = tuple(values[key])
    spec = B03Spec(**values)
    if config["arm"] != arm or spec.seed != seed:
        raise ValueError(f"{arm} source config identity mismatch")
    if spec != expected_spec:
        raise ValueError(f"{arm} source is not the fixed B03 production specification")
    if summary["device"] != training_device or summary["torch_threads"] != expected_spec.threads:
        raise ValueError(f"{arm} training device/thread contract mismatch")
    if summary["counts"]["transitions"] != spec.transitions or summary["counts"]["rollouts"] != spec.rollouts:
        raise ValueError(f"{arm} source training exposure mismatch")
    expected_rollouts = {str(index) for index in (*spec.eval_rollouts, spec.rollouts)}
    if set(summary["evaluations"]) != expected_rollouts:
        raise ValueError(f"{arm} development checkpoint panel mismatch")
    evaluation_steps = 0
    evaluation_worlds = 0
    panels = [(summary["evaluations"][index]["native"], spec.eval_seeds) for index in expected_rollouts]
    panels.append((summary["final_evaluation"], spec.final_seeds))
    for panel, expected_seeds in panels:
        if tuple(world["seed"] for world in panel["worlds"]) != tuple(expected_seeds):
            raise ValueError(f"{arm} native evaluation world panel mismatch")
        lengths = [world["actual_length"] for world in panel["worlds"]]
        if any(not isinstance(length, int) or not 0 < length <= spec.episode_length for length in lengths):
            raise ValueError(f"{arm} native evaluation length mismatch")
        if sum(lengths) != panel["actual_transitions"]:
            raise ValueError(f"{arm} native panel transition count mismatch")
        evaluation_steps += sum(lengths)
        evaluation_worlds += len(lengths)
    if (evaluation_steps, evaluation_worlds) != (summary["counts"]["evaluation_transitions"], summary["counts"]["evaluations"]):
        raise ValueError(f"{arm} native evaluation totals mismatch")
    return summary, spec


def run_replay(*, inputs: dict[str, tuple[Path, str]], seed: int, out: Path,
               launch_sha: str, training_sha: str, device_name: str = "cuda", threads: int = 4,
               spec: B03Spec | None = None):
    if set(inputs) != {"D", "S", "G"}:
        raise ValueError("all three endpoints are required")
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json")):
        raise FileExistsError("endpoint replay output already exists")
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    summary = {"object_id": "UAV-SERVICE-AUXILIARY-B03-ENDPOINT-REPLAY", "status": "INCOMPLETE",
               "seed": seed, "launch_sha": launch_sha, "failure": None,
               "new_fits": 0, "new_optimizer_updates": 0, "new_environment_transitions": 0,
               "arms": {}, "replay_agent_rows": 0}
    _write_json(out / "summary.json", summary)
    try:
        expected_spec = production_spec(seed) if spec is None else spec
        checked = {arm: verify_run(root, digest, arm=arm, seed=seed,
                                   expected_spec=expected_spec, training_sha=training_sha,
                                   training_device=device_name)
                   for arm, (root, digest) in inputs.items()}
        reference_spec = checked["D"][1]
        for arm, (source, spec) in checked.items():
            if spec != reference_spec or source["initialization_sha256"] != checked["D"][0]["initialization_sha256"]:
                raise ValueError(f"{arm} block configuration/initialization mismatch")
            if source["calibration_sha256"] != checked["D"][0]["calibration_sha256"]:
                raise ValueError(f"{arm} common calibration mismatch")
        _write_json(out / "config.json", {
            "inputs": {arm: {"root": str(root), "summary_sha256": digest} for arm, (root, digest) in inputs.items()},
            "training_sha": training_sha,
            "device": device_name, "threads": threads, "weighting": "episode equal; source arm strata retained",
        })
        device = torch.device(device_name)
        torch.set_num_threads(threads)
        if device.type == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA requested but unavailable")
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
        with preserved_rng():
            for arm in ("D", "S", "G"):
                source, spec = checked[arm]
                seed_everything(seed, device)
                config = make_config(spec)
                agent = HMASDAgent(config, log_dir=str(out / f"{arm}_loader"), device=device)
                agent.load_model(inputs[arm][0] / "checkpoint_final/agent.pt")
                agent.train(False)
                auxiliary = B03AuxiliaryReplay(
                    agent.skill_discoverer.actor, arm, initialization_seed=seed + spec.head_seed_offset,
                    generic_initialization_seed=seed + spec.generic_head_seed_offset,
                    observation_dim=config.obs_dim, action_dim=config.action_dim, window=spec.window,
                )
                auxiliary.load_checkpoint_state(torch.load(inputs[arm][0] / "checkpoint_final/auxiliary.pt", map_location=device, weights_only=False))
                before = initialization_fingerprint(agent)
                steps_before = optimizer_steps(agent)
                if before != source["final_policy_sha256"]:
                    raise ValueError(f"{arm} restored policy identity mismatch")
                strata = {}
                episodes = []
                for source_arm in ("D", "S", "G"):
                    result = replay_facts(auxiliary, agent, inputs[source_arm][0] / "endpoint_facts.npz",
                                          save_arrays=out / f"{arm}_on_{source_arm}_predictions.npz")
                    if (result["source"]["kind"], result["source"]["source_arm"], result["source"]["block_seed"]) != ("endpoint", source_arm, seed):
                        raise ValueError("endpoint facts source mismatch")
                    if result["source"]["policy_sha256"] != checked[source_arm][0]["final_policy_sha256"]:
                        raise ValueError("endpoint facts policy fingerprint mismatch")
                    if tuple(result["source"]["seeds"]) != spec.endpoint_fact_seeds:
                        raise ValueError("endpoint fact world panel mismatch")
                    strata[source_arm] = result
                    episodes.extend([{**row, "source_arm": source_arm} for row in result["episodes"]])
                    summary["replay_agent_rows"] += result["valid_agent_rows"]
                if before != initialization_fingerprint(agent) or steps_before != optimizer_steps(agent):
                    raise RuntimeError("fixed-policy replay changed a learner")
                aggregate = {}
                for key in ("service_mse", "observation_mse", "persistence_mse", "training_mean_mse", "service_training_mean_mse"):
                    values = [row[key] for row in episodes if row[key] is not None]
                    aggregate[key] = float(np.mean(values)) if values else None
                    aggregate[f"{key}_episodes"] = len(values)
                summary["arms"][arm] = {"source_strata": strata, "episodes": episodes, "aggregate": aggregate,
                                         "policy_sha256_before_after": before, "new_optimizer_updates": 0}
                _write_json(out / "summary.json", summary)
                del auxiliary, agent
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update({"wall_seconds": time.time() - started,
                        "cpu_user_seconds": usage.ru_utime - cpu_start.ru_utime,
                        "cpu_system_seconds": usage.ru_stime - cpu_start.ru_stime,
                        "peak_rss_kib": int(usage.ru_maxrss), "rss_scope": "replay runner process high-water mark"})
        _write_json(out / "summary.json", summary)
