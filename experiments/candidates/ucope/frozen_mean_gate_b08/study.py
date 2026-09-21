"""One declared UCOPE B08 gate pair on a byte-bound frozen B06 controller."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
import statistics
import time
import traceback

import numpy as np
import torch

from ..lower_scale_reuse_b07.study import (
    EXPECTED_INPUT_SHA256, EXPECTED_SHARED_SHA256, SOURCE_OBJECT, SOURCE_SHA,
)
from ..uav_motion_prefix_b01.environment import make_real, SyntheticAdapter
from ..uav_motion_prefix_b01.policy import Actor
from . import engine


OBJECT = "UCOPE_FROZEN_MEAN_GATE_B08"
REPO = Path(__file__).resolve().parents[4]
MASTERS = (8951, 8952, 8953)
ARMS = ("agreement", "contextual")
MODES = ARMS + ("ordinary",)
CONTEXT_EPISODES = tuple(range(0, 64, 8))
DEADLINE = datetime(2026, 9, 21, 4, 6, 7, tzinfo=timezone.utc).timestamp()
SHARED = {
    "ordinary_policy": "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py",
    "ordinary_environment": "experiments/candidates/ucope/uav_motion_prefix_b01/environment.py",
    "ordinary_learner": "experiments/candidates/ucope/uav_motion_prefix_b01/learner.py",
}


@dataclass(frozen=True)
class Config:
    master: int
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    watchdog_seconds: float = 7200.0
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(9951, 8, 4, 3, 180.0, True)


@dataclass(frozen=True)
class Inputs:
    checkpoint: Path
    summary: Path
    source: Path
    checkpoint_sha256: str
    summary_sha256: str
    source_sha256: str


def require_config(config):
    if config.fixture:
        if config != Config.engineering():
            raise ValueError("only the declared synthetic engineering fixture is supported")
    elif config.master not in MASTERS or config != Config(config.master):
        raise ValueError("B08 masters and scientific exposure are fixed")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def file_identity(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw)}


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def tensor_digest(state):
    digest = hashlib.sha256()
    for key, value in sorted(state.items()):
        value = value.detach().cpu().contiguous()
        digest.update(key.encode() + b"\0")
        digest.update(str(value.dtype).encode() + b"\0")
        digest.update(str(tuple(value.shape)).encode() + b"\0")
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def snapshot(module):
    return torch.cat([p.detach().reshape(-1) for p in module.parameters()]).clone()


def movement(initial, module):
    final = snapshot(module)
    return {"parameters": int(final.numel()), "initial_norm": float(initial.norm()),
            "final_norm": float(final.norm()), "displacement": float((final - initial).norm())}


def input_files(config, fixture_inputs=None):
    if config.fixture:
        if not isinstance(fixture_inputs, Inputs):
            raise ValueError("synthetic fixture requires explicit tensor input files")
        return fixture_inputs
    if fixture_inputs is not None:
        raise ValueError("production input bindings cannot be overridden")
    foundation = config.master - 10
    root = REPO / f"runs/ucope/gaussian_scale_initialization_b06_{foundation}"
    expected = EXPECTED_INPUT_SHA256[foundation]
    return Inputs(root / "Ghalf_final.pt", root / "summary.json", root / "source.json",
                  expected["checkpoint"], expected["summary"], expected["source"])


def load_foundation(config, out, fixture_inputs=None):
    files = input_files(config, fixture_inputs)
    raw, identities = {}, {}
    for name in ("checkpoint", "summary", "source"):
        path = getattr(files, name)
        raw[name] = Path(path).read_bytes()
        actual = sha256(raw[name])
        if actual != getattr(files, name + "_sha256"):
            raise ValueError(f"inherited {name} digest mismatch")
        identities[name] = {"path": str(path), "sha256": actual, "bytes": len(raw[name])}
    payload = torch.load(io.BytesIO(raw["checkpoint"]), map_location="cpu", weights_only=True)
    summary, source = json.loads(raw["summary"]), json.loads(raw["source"])
    foundation = config.master - 10
    expected = {"object": SOURCE_OBJECT, "arm": "Ghalf", "seed": foundation,
                "train_episodes": config.train_episodes,
                "optimizer_steps": config.train_episodes * 2}
    if not isinstance(payload, dict) or any(payload.get(k) != v for k, v in expected.items()):
        raise ValueError("inherited checkpoint object/arm/exposure mismatch")
    if (summary.get("object") != SOURCE_OBJECT or summary.get("master") != foundation
            or summary.get("launch_sha") != SOURCE_SHA or summary.get("status") != "COMPLETE"
            or source.get("object") != SOURCE_OBJECT or source.get("launch_sha") != SOURCE_SHA):
        raise ValueError("inherited summary/source identity mismatch")
    for key in ("horizon", "train_episodes", "eval_episodes"):
        if summary.get("configuration", {}).get(key) != getattr(config, key):
            raise ValueError("inherited foundation exposure mismatch")
    recorded = summary.get("arms", {}).get("Ghalf", {})
    if (not recorded.get("train_complete")
            or recorded.get("checkpoint", {}).get("sha256") != identities["checkpoint"]["sha256"]
            or recorded.get("counts", {}).get("train_episodes") != config.train_episodes
            or recorded.get("counts", {}).get("optimizer_steps") != config.train_episodes * 2):
        raise ValueError("inherited checkpoint completion/digest binding mismatch")
    current_policy = file_identity(REPO / SHARED["ordinary_policy"])
    if current_policy["sha256"] != EXPECTED_SHARED_SHA256["ordinary_policy"]:
        raise ValueError("frozen Actor source differs from the bound B06 construction")
    for name in ("actor", "critic"):
        state = payload.get(name)
        if not isinstance(state, dict) or not state or not all(
                isinstance(v, torch.Tensor) and v.device.type == "cpu"
                and v.dtype == torch.float32 and torch.isfinite(v).all() for v in state.values()):
            raise ValueError("inherited tensors must be finite CPU FP32")
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(0)
        actor = Actor()
    actor.load_state_dict(payload["actor"], strict=True)
    engine.freeze_foundation(actor)
    for name, suffix in (("checkpoint", ".pt"), ("summary", ".json"), ("source", ".json")):
        (out / ("inherited_" + name + suffix)).write_bytes(raw[name])
    return actor, {"foundation_master": foundation, "source_sha": SOURCE_SHA,
                   "files": identities, "actor_source": current_policy,
                   "actor_parameter_digest": tensor_digest(actor.state_dict()),
                   "selection": "B06-selected developmental Ghalf instance; no new foundation fit"}


def episode_record(config, arm, phase, episode, rollout):
    eligible = rollout["eligible"].bool()
    probabilities = rollout["keep_probability"][eligible]
    mean = float(probabilities.mean()) if probabilities.numel() else None
    std = float(probabilities.std(unbiased=False)) if probabilities.numel() else None
    rewards = rollout["reward"].double()
    return {"master": config.master, "arm": arm, "phase": phase, "episode": episode,
            "world_seed": 100000 * config.master + (10000 if phase == "train" else 30000) + episode,
            "steps": int(len(rewards)), "reward_sum": float(rewards.sum()),
            "J": float(rewards.sum() / config.horizon),
            "eligible": int(eligible.sum()), "kept": int(rollout["keep"].sum()),
            "keep_probability_mean": mean, "keep_probability_std": std}


def difference_stats(left, right):
    differences = [a - b for a, b in zip(left, right)]
    n = len(differences)
    return {"differences": differences, "worlds": n,
            "mean": statistics.mean(differences) if n else None,
            "conditional_world_se": statistics.stdev(differences) / n ** .5 if n > 1 else None,
            "positive": sum(v > 0 for v in differences), "negative": sum(v < 0 for v in differences),
            "tie": sum(v == 0 for v in differences)}


def reduce_panels(panels, expected):
    complete = all(len(panels.get(arm, [])) == expected for arm in MODES)
    result = {"complete": complete, "primary": "contextual_minus_agreement",
              "world_scores": panels,
              "means": {a: statistics.mean(v) if v else None for a, v in panels.items()}}
    if complete:
        for first, second in (("contextual", "agreement"), ("contextual", "ordinary"),
                              ("agreement", "ordinary")):
            result[first + "_minus_" + second] = difference_stats(panels[first], panels[second])
    return result


def counts_total(arms):
    total = {}
    for arm in arms.values():
        for name, value in arm.get("counts", {}).items():
            if isinstance(value, int):
                if name.startswith("max_"):
                    total[name] = max(total.get(name, 0), value)
                else:
                    total[name] = total.get(name, 0) + value
    return total


def _close(env):
    close = getattr(env, "close", None)
    if callable(close):
        close()


def run(config, out, admission, *, start=None, fixture_inputs=None):
    require_config(config)
    if not config.fixture and (not admission or admission.get("direction") != "ucope"):
        raise ValueError("production study requires its UCOPE admission")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / p).exists() for p in ("summary.json", "episodes.jsonl", "updates.jsonl")):
        raise ValueError("scientific outputs already exist; no overwrite or implicit resume")
    summary = {"object": OBJECT, "master": config.master, "status": "RUNNING", "failure": None,
               "configuration": asdict(config), "launch_sha": admission.get("sha") if admission else None,
               "prospective_notebook": "docs/research/candidates/ucope/NOTES.md (UCOPE frozen-mean B08)",
               "node": "local_linux", "arms": {}, "counts": {}, "fit_accounting": {},
               "foundation_optimizer_steps": 0, "scientific_fixture": config.fixture}
    panels = {arm: [] for arm in MODES}
    artifacts = []
    foundation = None
    source = {"object": OBJECT, "launch_sha": summary["launch_sha"], "files": {}}
    paths = list(SHARED.values()) + [
        "experiments/candidates/ucope/lower_scale_reuse_b07/study.py",
        "experiments/candidates/ucope/frozen_mean_gate_b08/engine.py",
        "experiments/candidates/ucope/frozen_mean_gate_b08/study.py",
        "scripts/run_ucope_frozen_mean_gate_b08.py",
    ]
    for path in paths:
        source["files"][path] = file_identity(REPO / path)
    write_json(out / "config.json", asdict(config))
    write_json(out / "source.json", source)
    write_json(out / "admission.json", dict(admission or {}))

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError("declared invocation watchdog exceeded")
        if not config.fixture and time.time() >= DEADLINE:
            raise TimeoutError("owner's original hard deadline reached")

    def publish():
        summary["counts"] = counts_total(summary["arms"])
        trained = [summary["arms"].get(a, {}) for a in ARMS]
        summary["fit_accounting"] = {"planned_new_gate_fits": 2, "planned_batch_fits": 6,
             "started_new_gate_fits": sum(bool(a.get("fit_started")) for a in trained),
             "completed_new_gate_fits": sum(bool(a.get("train_complete")) for a in trained),
             "new_foundation_fits": 0}
        summary["final_panel"] = reduce_panels(panels, config.eval_episodes)
        summary["wall_seconds"] = time.monotonic() - start
        summary["process_cpu_seconds"] = time.process_time() - cpu_start
        summary["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if foundation is not None:
            summary["foundation_final_digest"] = tensor_digest(foundation.state_dict())
            summary["foundation_unchanged"] = (summary["foundation_final_digest"]
                == summary["foundation"]["actor_parameter_digest"])
        write_json(out / "summary.json", summary)

    def env_for(seed):
        return SyntheticAdapter(seed, config.horizon) if config.fixture else make_real(seed)

    primitive_keys = ("reward", "commands", "means", "previous", "eligible", "keep",
                      "keep_probability", "gate_uniforms")
    base = 100000 * config.master
    with (out / "episodes.jsonl").open("w", encoding="utf-8") as ep_stream, \
            (out / "updates.jsonl").open("w", encoding="utf-8") as update_stream:
        def emit(stream, row):
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()

        def evaluate(arm, gate, critic, record):
            env = env_for(base + 30000)
            arrays = {key: [] for key in primitive_keys}
            context, context_ids = [], []
            parameter_before = tensor_digest(gate.state_dict()) if gate is not None else None
            critic_before = tensor_digest(critic.state_dict()) if critic is not None else None
            counters_before = {k: record["counts"].get(k, 0) for k in
                               ("gate_optimizer_steps", "critic_optimizer_steps", "optimizer_steps")}
            torch_before = torch.get_rng_state().clone()
            try:
                if gate is not None:
                    gate.eval()
                    critic.eval()
                for episode in range(config.eval_episodes):
                    roll = engine.collect_episode(env, foundation, gate, critic,
                        horizon=config.horizon, reset_seed=base + 30000 + episode,
                        gate_seed=base + 70000 + episode, phase="eval", check=check, counts=record["counts"])
                    row = episode_record(config, arm, "eval", episode, roll)
                    emit(ep_stream, row)
                    panels[arm].append(row["J"])
                    for key in primitive_keys:
                        arrays[key].append(roll[key].numpy())
                    if episode in CONTEXT_EPISODES:
                        context.append(roll["context"].numpy())
                        context_ids.append(episode)
            finally:
                _close(env)
                if arrays["reward"]:
                    filename = f"{arm}_evaluation.npz"
                    np.savez_compressed(out / filename,
                        **{k: np.stack(v) for k, v in arrays.items()},
                        context=np.stack(context) if context else np.empty((0, config.horizon, 5, 175), np.float32),
                        context_episode_ids=np.asarray(context_ids, dtype=np.int64))
                    artifacts.append(filename)
            record["evaluation_immutability"] = {
                "gate_unchanged": gate is None or parameter_before == tensor_digest(gate.state_dict()),
                "critic_unchanged": critic is None or critic_before == tensor_digest(critic.state_dict()),
                "global_torch_rng_unchanged": torch.equal(torch_before, torch.get_rng_state()),
                "optimizer_counts_unchanged": all(record["counts"].get(k, 0) == v for k, v in counters_before.items()),
            }
            if not all(record["evaluation_immutability"].values()):
                raise RuntimeError("evaluation mutated a learner or training RNG")
            record["eval_complete"] = True

        try:
            check()
            foundation, provenance = load_foundation(config, out, fixture_inputs)
            summary["foundation"] = provenance
            artifacts.extend(("inherited_checkpoint.pt", "inherited_summary.json", "inherited_source.json"))
            publish()
            for index, arm in enumerate(ARMS):
                check()
                record = {"fit_started": True, "train_complete": False, "eval_complete": False, "counts": {}}
                summary["arms"][arm] = record
                arm_start = time.monotonic()
                gate = engine.Gate(arm, seed=base + 11)
                critic = engine.make_critic(base + 12)
                before_gate, before_critic = snapshot(gate), snapshot(critic)
                gate_optimizer, critic_optimizer = engine.make_optimizers(gate, critic)
                shuffle = torch.Generator(device="cpu").manual_seed(base + 41 + 10 * index)
                env = env_for(base + 10000)
                pending = []
                try:
                    for episode in range(config.train_episodes):
                        roll = engine.collect_episode(env, foundation, gate, critic,
                            horizon=config.horizon, reset_seed=base + 10000 + episode,
                            gate_seed=base + 50000 + episode, phase="train", check=check, counts=record["counts"])
                        emit(ep_stream, episode_record(config, arm, "train", episode, roll))
                        pending.append(roll)
                        if len(pending) == 2:
                            stats = engine.update(gate, critic, gate_optimizer, critic_optimizer,
                                pending, shuffle, horizon=config.horizon, check=check, counts=record["counts"])
                            emit(update_stream, {"arm": arm, "episodes_seen": episode + 1,
                                 "statistics": stats, "b0": float(gate.b0.detach()),
                                 "b1": float(gate.b1.detach())})
                            pending = []
                        if (episode + 1) % 32 == 0:
                            publish()
                finally:
                    _close(env)
                record["train_complete"] = True
                record["training_wall_seconds"] = time.monotonic() - arm_start
                record["movement"] = {"gate": movement(before_gate, gate), "critic": movement(before_critic, critic)}
                record["final_affine"] = {"b0": float(gate.b0.detach()), "b1": float(gate.b1.detach())}
                checkpoint = f"{arm}_final.pt"
                torch.save({"object": OBJECT, "master": config.master, "arm": arm,
                    "configuration": asdict(config), "launch_sha": summary["launch_sha"],
                    "foundation": provenance, "gate": gate.state_dict(), "critic": critic.state_dict(),
                    "gate_optimizer": gate_optimizer.state_dict(), "critic_optimizer": critic_optimizer.state_dict(),
                    "shuffle_rng": shuffle.get_state(), "counts": dict(record["counts"])}, out / checkpoint)
                record["checkpoint"] = file_identity(out / checkpoint)
                artifacts.append(checkpoint)
                evaluate(arm, gate, critic, record)
                publish()
            summary["arms"]["ordinary"] = {"fit_started": False, "counts": {}, "eval_complete": False}
            evaluate("ordinary", None, None, summary["arms"]["ordinary"])
            if tensor_digest(foundation.state_dict()) != provenance["actor_parameter_digest"]:
                raise RuntimeError("frozen foundation parameters changed")
            summary["status"] = "COMPLETE"
        except Exception as exc:
            summary["status"] = "INCOMPLETE"
            summary["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        finally:
            ep_stream.flush()
            update_stream.flush()
            artifacts.extend(("config.json", "source.json", "admission.json", "episodes.jsonl", "updates.jsonl"))
            summary["artifacts"] = {name: file_identity(out / name) for name in artifacts if (out / name).is_file()}
            summary["interpretation"] = (
                "Exploratory gate-learning comparison on three development-selected frozen ordinary controllers. "
                "Worlds are nested within each gate fit. No new foundation fit, velocity sampling, "
                "switch cost, production deployment, or isolated information-value claim.")
            publish()
    return summary
