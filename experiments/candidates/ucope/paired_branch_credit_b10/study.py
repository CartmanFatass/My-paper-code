"""Prospective B10 package comparison; no native effects without admission."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import statistics
import time
import traceback

import numpy as np
import torch

from ..frozen_mean_gate_b08 import engine
from ..frozen_mean_gate_b08 import study as inherited
from ..normalized_distance_gate_b09.gate import Gate as ScalarGate
from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
from .collection import collect_pair, schedule
from .learning import update_pairs
from .storage import save_pair


OBJECT = "UCOPE_PAIRED_BRANCH_CREDIT_B10"
REPO = Path(__file__).resolve().parents[4]
MASTERS = (8971, 8972, 8973)
ARMS = ("R_CF", "R_FULL", "S_FULL")
MODES = ARMS + ("G",)
file_identity = inherited.file_identity
write_json = inherited.write_json
tensor_digest = inherited.tensor_digest


@dataclass(frozen=True)
class Config:
    master: int
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    pairs_per_round: int = 16
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(9971, 4, 4, 2, 2, True)


def require_config(config):
    expected = Config.engineering() if config.fixture else Config(config.master)
    if config != expected or (not config.fixture and config.master not in MASTERS):
        raise ValueError("B10 uses only the declared masters and fixed exposure")


def load_foundation(config, out, fixture_inputs=None):
    # Reuse the original digest/exposure/source/tensor checks without mutating
    # the historical B08 master mapping or its frozen deadline interface.
    source_config = inherited.Config(config.master - 20, config.horizon,
        config.train_episodes, config.eval_episodes, fixture=config.fixture)
    return inherited.load_foundation(source_config, out, fixture_inputs)


def reduce_panels(panels, expected):
    complete = all(len(panels.get(arm, [])) == expected for arm in MODES)
    result = {"complete": complete, "primary": "R_CF_minus_R_FULL", "world_scores": panels,
              "means": {arm: statistics.mean(values) if values else None for arm, values in panels.items()}}
    if complete:
        for left, right in (("R_CF", "R_FULL"), ("R_CF", "G"), ("R_CF", "S_FULL"),
                            ("S_FULL", "G"), ("R_FULL", "G")):
            result[left + "_minus_" + right] = inherited.difference_stats(panels[left], panels[right])
    return result


def _normal_counts(counts, phase):
    result = dict(counts)
    result.setdefault(phase + "_team_steps", result.get("team_steps", 0))
    result.setdefault(phase + "_episodes", result.get("completed_episodes", 0))
    result.setdefault("recurrent_agent_observations", 5 * result.get("foundation_forward_calls", 0))
    result.setdefault("gate_optimizer_steps", 0)
    result.setdefault("critic_optimizer_steps", 0)
    result.setdefault("optimizer_steps", result["gate_optimizer_steps"] + result["critic_optimizer_steps"])
    return result


def _record_episode(config, arm, phase, index, roll, world_seed):
    eligible = roll["eligible"]
    probability = (roll["keep_probability"] if "keep_probability" in roll else roll["logits"].sigmoid())
    values = probability[eligible]
    reward = roll["reward"].double()
    return {"master": config.master, "arm": arm, "phase": phase, "episode": index,
            "world_seed": world_seed, "steps": len(reward), "J": float(reward.sum() / config.horizon),
            "reward_sum": float(reward.sum()), "eligible": int(eligible.sum()),
            "kept": int(roll["keep"].sum()),
            "keep_probability_mean": float(values.mean()) if values.numel() else None,
            "keep_probability_std": float(values.std(unbiased=False)) if values.numel() else None}


class ZeroValue(torch.nn.Module):
    """B08 evaluation adapter only; no parameters, fitting or action influence."""
    def forward(self, features):
        return features.new_zeros(features.shape[:-1])


def _validate_paired_optimizer(gate, optimizer):
    if not isinstance(optimizer, torch.optim.Adam):
        raise TypeError("paired production update requires Adam")
    engine._validate_optimizer_ownership(optimizer, list(gate.parameters()), "paired gate")


def run(config, out, admission, *, fixture_inputs=None):
    require_config(config)
    if not config.fixture and (not admission or admission.get("direction") != "ucope"):
        raise ValueError("production B10 requires its UCOPE admission")
    start, cpu_start = time.monotonic(), time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("summary.json", "episodes.jsonl", "pairs.jsonl", "updates.jsonl")):
        raise ValueError("scientific outputs already exist; no overwrite or implicit resume")
    summary = {"object": OBJECT, "master": config.master, "configuration": asdict(config),
               "status": "RUNNING", "failure": None, "launch_sha": admission.get("sha") if admission else None,
               "prospective_notebook": "docs/research/candidates/ucope/NOTES.md (B10 paired branch credit)",
               "node": "local_linux", "arms": {}, "foundation_optimizer_steps": 0,
               "scientific_fixture": config.fixture, "owner_running_window": None}
    panels = {arm: [] for arm in MODES}
    artifacts, models = {}, {}
    foundation = None
    paths = list(inherited.SHARED.values()) + [
        "experiments/candidates/ucope/lower_scale_reuse_b07/study.py",
        "experiments/candidates/ucope/frozen_mean_gate_b08/engine.py",
        "experiments/candidates/ucope/frozen_mean_gate_b08/study.py",
        "experiments/candidates/ucope/normalized_distance_gate_b09/gate.py",
    ] + ["experiments/candidates/ucope/paired_branch_credit_b10/" + name for name in
         ("__init__.py", "collection.py", "credit.py", "learning.py", "storage.py", "study.py")] + [
        "scripts/run_ucope_paired_branch_credit_b10.py"]
    write_json(out / "source.json", {"object": OBJECT, "launch_sha": summary["launch_sha"],
        "files": {path: file_identity(REPO / path) for path in paths}})
    write_json(out / "config.json", asdict(config))
    write_json(out / "admission.json", dict(admission or {}))

    def publish():
        for record in summary["arms"].values():
            phases = {phase: {"counts": _normal_counts(record[phase + "_counts"], phase)}
                      for phase in ("train", "eval")}
            record["counts"] = inherited.counts_total(phases)
        summary["counts"] = inherited.counts_total(summary["arms"])
        summary["fit_accounting"] = {"planned_new_gate_fits": 3, "planned_batch_fits": 9,
            "started_new_gate_fits": sum(bool(record.get("fit_started")) for record in summary["arms"].values()),
            "completed_new_gate_fits": sum(bool(record.get("train_complete")) for record in summary["arms"].values()),
            "new_foundation_fits": 0}
        summary["final_panel"] = reduce_panels(panels, config.eval_episodes)
        summary["wall_seconds"] = time.monotonic() - start
        summary["process_cpu_seconds"] = time.process_time() - cpu_start
        summary["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if foundation is not None:
            summary["foundation_final_digest"] = tensor_digest(foundation.state_dict())
            summary["foundation_unchanged"] = summary["foundation_final_digest"] == summary["foundation"]["actor_parameter_digest"]
        write_json(out / "summary.json", summary)

    def env_for(seed):
        return SyntheticAdapter(seed, config.horizon) if config.fixture else make_real(seed)

    # Exposure is controlled by exact loop bounds. The owner removed the old
    # calendar deadline; no replacement scientific or wall-time endpoint.
    def check():
        pass

    base = 100000 * config.master
    with (out / "episodes.jsonl").open("w", encoding="utf-8") as ep_stream, \
         (out / "pairs.jsonl").open("w", encoding="utf-8") as pair_stream, \
         (out / "updates.jsonl").open("w", encoding="utf-8") as update_stream:
        def emit(stream, row):
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()

        try:
            foundation, provenance = load_foundation(config, out, fixture_inputs)
            summary["foundation"] = provenance
            publish()
            cases = schedule(config.train_episodes // 2, config.horizon, base + 81)
            for arm in ARMS:
                record = {"fit_started": True, "train_complete": False, "eval_complete": False,
                          "train_counts": {}, "eval_counts": {}}
                summary["arms"][arm] = record
                arm_start = time.monotonic()
                gate = (ScalarGate("scalar", base + 11, 0.0, 1.0) if arm == "S_FULL"
                        else engine.Gate("contextual", base + 11))
                initial_gate = inherited.snapshot(gate)
                record["initial_gate_digest"] = tensor_digest(gate.state_dict())
                critic = engine.make_critic(base + 12) if arm != "R_CF" else None
                initial_critic = inherited.snapshot(critic) if critic is not None else None
                optimizer = torch.optim.Adam(gate.parameters(), lr=3e-4)
                critic_optimizer = torch.optim.Adam(critic.parameters(), lr=3e-4) if critic is not None else None
                _validate_paired_optimizer(gate, optimizer)
                shuffle = torch.Generator(device="cpu").manual_seed(base + 91)
                env, pending = env_for(base + 10000), []
                counts = record["train_counts"]
                try:
                    if arm in ("R_FULL", "S_FULL"):
                        for episode in range(config.train_episodes):
                            roll = engine.collect_episode(env, foundation, gate, critic,
                                horizon=config.horizon, reset_seed=base + 10000 + episode,
                                gate_seed=base + 50000 + episode, phase="train", check=check, counts=counts)
                            emit(ep_stream, _record_episode(config, arm, "train", episode, roll, base + 10000 + episode))
                            pending.append(roll)
                            if len(pending) == 2:
                                stats = engine.update(gate, critic, optimizer, critic_optimizer, pending, shuffle,
                                    horizon=config.horizon, check=check, counts=counts)
                                emit(update_stream, {"arm": arm, "episodes_seen": episode + 1, "statistics": stats})
                                pending.clear()
                            if (episode + 1) % 32 == 0:
                                publish()
                    else:
                        behavior_digest = None
                        for index, case in enumerate(cases):
                            if not pending:
                                behavior_digest = tensor_digest(gate.state_dict())
                            pair = collect_pair(env, foundation, gate, None, horizon=config.horizon,
                                case=case, mode="paired", reset_seed=base + 10000 + index,
                                common_seed=base + 50000 + index, focal_seed=base + 60000 + index,
                                check=check, counts=counts)
                            if behavior_digest != tensor_digest(gate.state_dict()):
                                raise RuntimeError("gate changed during a fixed-policy collection round")
                            raw_path = Path("pairs") / arm / f"{index:04d}.npz"
                            identity = save_pair(out / raw_path, pair)
                            artifacts[str(raw_path)] = identity
                            emit(pair_stream, {"arm": arm, "pair": index, "tick": case.tick, "agent": case.agent,
                                "eligible": pair["eligible"], "world_seed": base + 10000 + index,
                                "common_seed": base + 50000 + index, "focal_seed": base + 60000 + index,
                                "behavior_digest": behavior_digest, "raw_path": str(raw_path), "raw": identity,
                                "old_logit": float(pair["old_logits"][case.agent]),
                                "suffix_returns": pair["suffix_returns"].tolist(),
                                "delta": float(pair["suffix_returns"][0] - pair["suffix_returns"][1])})
                            for branch, roll in enumerate(pair["episodes"]):
                                row = _record_episode(config, arm, "train", 2 * index + branch, roll, base + 10000 + index)
                                row.update(pair=index, branch="KEEP" if branch == 0 else "END", interventional=True)
                                emit(ep_stream, row)
                            pending.append(pair)
                            if len(pending) == config.pairs_per_round:
                                _validate_paired_optimizer(gate, optimizer)
                                stats = update_pairs(gate, optimizer, pending, horizon=config.horizon,
                                    check=check, counts=counts)
                                emit(update_stream, {"arm": arm, "pairs_seen": index + 1,
                                    "eligible_pairs": sum(pair["eligible"] for pair in pending), "statistics": stats})
                                pending.clear()
                                publish()
                    if pending:
                        raise RuntimeError("declared training left an unconsumed partial update")
                finally:
                    inherited._close(env)
                record["train_complete"] = True
                record["training_wall_seconds"] = time.monotonic() - arm_start
                record["movement"] = {"gate": inherited.movement(initial_gate, gate)}
                if critic is not None:
                    record["movement"]["critic"] = inherited.movement(initial_critic, critic)
                checkpoint = arm + "_final.pt"
                torch.save({"object": OBJECT, "master": config.master, "arm": arm,
                    "configuration": asdict(config), "launch_sha": summary["launch_sha"], "foundation": provenance,
                    "gate": gate.state_dict(), "critic": critic.state_dict() if critic is not None else None,
                    "gate_optimizer": optimizer.state_dict(),
                    "critic_optimizer": critic_optimizer.state_dict() if critic_optimizer is not None else None,
                    "shuffle_rng": shuffle.get_state() if critic is not None else None,
                    "counts": _normal_counts(counts, "train")}, out / checkpoint)
                record["checkpoint"] = artifacts[checkpoint] = file_identity(out / checkpoint)
                models[arm] = (gate, critic)
                publish()

            summary["arms"]["G"] = {"fit_started": False, "train_complete": False,
                                      "eval_complete": False, "train_counts": {}, "eval_counts": {}}
            models["G"] = (None, None)
            for arm in MODES:
                gate, critic = models[arm]
                evaluation_value = critic if critic is not None else (ZeroValue() if gate is not None else None)
                before_gate = tensor_digest(gate.state_dict()) if gate is not None else None
                before_critic = tensor_digest(critic.state_dict()) if critic is not None else None
                before_rng = torch.get_rng_state().clone()
                record = summary["arms"][arm]
                training_counts = dict(record["train_counts"])
                if gate is not None:
                    gate.eval()
                    evaluation_value.eval()
                env = env_for(base + 30000)
                arrays = {key: [] for key in ("reward", "commands", "means", "previous", "eligible", "keep",
                                               "keep_probability", "gate_uniforms", "context")}
                try:
                    for episode in range(config.eval_episodes):
                        roll = engine.collect_episode(env, foundation, gate, evaluation_value,
                            horizon=config.horizon, reset_seed=base + 30000 + episode,
                            gate_seed=base + 70000 + episode, phase="eval", check=check, counts=record["eval_counts"])
                        row = _record_episode(config, arm, "eval", episode, roll, base + 30000 + episode)
                        emit(ep_stream, row)
                        panels[arm].append(row["J"])
                        for key in arrays:
                            arrays[key].append(roll[key].numpy())
                finally:
                    inherited._close(env)
                    if arrays["reward"]:
                        name = arm + "_evaluation.npz"
                        np.savez_compressed(out / name, **{key: np.stack(value) for key, value in arrays.items()})
                        artifacts[name] = file_identity(out / name)
                record["evaluation_immutability"] = {
                    "gate_unchanged": gate is None or before_gate == tensor_digest(gate.state_dict()),
                    "critic_unchanged": critic is None or before_critic == tensor_digest(critic.state_dict()),
                    "global_torch_rng_unchanged": torch.equal(before_rng, torch.get_rng_state()),
                    "training_counts_unchanged": training_counts == record["train_counts"],
                    "zero_evaluation_updates": record["eval_counts"].get("optimizer_steps", 0) == 0}
                if not all(record["evaluation_immutability"].values()):
                    raise RuntimeError("evaluation mutated learning state")
                record["eval_complete"] = True
                publish()
            if tensor_digest(foundation.state_dict()) != provenance["actor_parameter_digest"]:
                raise RuntimeError("frozen foundation changed")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "INCOMPLETE"
            summary["failure"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        finally:
            for stream in (ep_stream, pair_stream, update_stream):
                stream.flush()
            for name in ("source.json", "config.json", "admission.json", "episodes.jsonl", "pairs.jsonl",
                         "updates.jsonl", "inherited_checkpoint.pt", "inherited_summary.json", "inherited_source.json"):
                if (out / name).is_file():
                    artifacts[name] = file_identity(out / name)
            summary["artifacts"] = artifacts
            summary["interpretation"] = (
                "Exploratory matched-native-step package comparison on B06-selected developmental foundations. "
                "Paired branches are interventions; copied prefixes count. No foundation updates. "
                "Worlds are nested within each fit; no isolated variance effect or general termination bound.")
            publish()
    return summary
