"""Train Bhalf once and compare it with the bound retained B06 Ghalf endpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import statistics
import time
import traceback

import numpy as np
import torch

from ..reactive_renewal_b01 import reactive
from ..reactive_renewal_b01.reactive import END, KEEP
from ..reactive_rate_b03.scalar import ScalarGate, scalar_actor
from ..uav_motion_prefix_b01.environment import actor_features, team_reward
from ..uav_motion_prefix_b01.learner import optimizer_for
from ..uav_motion_prefix_b01.policy import arm_copy, generator, templates
from ..uav_motion_prefix_b01.study import new_counts, write_summary


OBJECT = "UCOPE_LOWER_SCALE_REUSE_B07"
SOURCE_OBJECT = "UCOPE_GAUSSIAN_SCALE_INITIALIZATION_B06"
SOURCE_SHA = "7ad9a8668d17a25724b9649dece7d5479e7d22c5"
NOTEBOOK = "docs/research/candidates/ucope/NOTES.md"
NOTEBOOK_SECTION = "B07 prepared practical comparison: reuse against the improved ordinary endpoint"
EXECUTION_NODE = "local_linux"
ALLOWED_MASTERS = (8941, 8942, 8943)
MODES = ("Bhalf_sampled", "Bhalf_mean", "Ghalf_sampled", "Ghalf_mean")
CONTRASTS = (
    ("Bhalf_sampled_minus_Ghalf_mean", "Bhalf_sampled", "Ghalf_mean"),
    ("Bhalf_mean_minus_Ghalf_mean", "Bhalf_mean", "Ghalf_mean"),
    ("Bhalf_sampled_minus_Ghalf_sampled", "Bhalf_sampled", "Ghalf_sampled"),
    ("Bhalf_mean_minus_Bhalf_sampled", "Bhalf_mean", "Bhalf_sampled"),
    ("Ghalf_mean_minus_Ghalf_sampled", "Ghalf_mean", "Ghalf_sampled"),
)
REPO = Path(__file__).resolve().parents[4]
FORCED_FRESH = 2
EXPECTED_SHARED_SHA256 = {
    "ordinary_learner": "466ec7b0efabdf474f838b662e781a2b7a3b5e1c1a41096b6ccf0f00eb0471f1",
    "ordinary_policy": "e324640251d0d025549705ff7541b765e7b96733f422c48ee9c2f5bd07709614",
    "reactive_learner": "5de62a9fe8512601f427e3995a3bfa22a86d5bfb2f61b12792beaae435c6428a",
    "scalar_gate": "adbb038a374a5566ec344dbb30d4b3546b647dda2d148d60f9e0a681cab04894",
}
EXPECTED_INPUT_SHA256 = {
    8941: {
        "checkpoint": "67b85e626f7d56c7e099f74b175c9ab147db3980463684f78f85d1b7017a82df",
        "summary": "04bc2a22e5e1fa31e4c2075d7ce9e7ed2fcc283413eeb6cb1a9cd98ad185467a",
        "source": "6ed1487b1e8c49357529a384df5ac8d2e324e4a2dbc0d3a825b37921c6654b46",
    },
    8942: {
        "checkpoint": "d7a6623a2eb8ed5e779458509063ff5bb663dad53eef9edf5b00f7506cf102ef",
        "summary": "7ea865bdde87d86fea2327c05a428829c34049365cd6ff6b3ee74bea17b8b14a",
        "source": "163cab0567bb386e0f8c775a63553e6a7344c39f7ae209397220eb13fb27af4e",
    },
    8943: {
        "checkpoint": "870aad70083ccc915afa4e6d5397f9a6e5540fc9d7f1be965632b4d70ea8c912",
        "summary": "b9637450628c1bc597c691d22c9a9381e5e95f6bca7a50830b3a14b96772dd41",
        "source": "37c30a258a7d9290fbea5f0cca92d05eda49f4e80ef679cb5c7c247ba3fcae78",
    },
}


@dataclass(frozen=True)
class Config:
    master: int
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    chunk: int = 32
    watchdog_seconds: float = 6000.0
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(
            master=9941,
            horizon=8,
            train_episodes=4,
            eval_episodes=3,
            chunk=4,
            watchdog_seconds=180.0,
            fixture=True,
        )


@dataclass(frozen=True)
class InheritedFiles:
    checkpoint: Path
    summary: Path
    source: Path
    checkpoint_sha256: str
    summary_sha256: str
    source_sha256: str


def require_config(config):
    if config.fixture:
        if config != Config.engineering():
            raise ValueError("only the fixed B07 engineering fixture is supported off path")
        return
    if config.master not in ALLOWED_MASTERS:
        raise ValueError("master must be one of the three fixed B07 pairs")
    if config != Config(master=config.master):
        raise ValueError("B07 training and evaluation exposure is fixed")


def inherited_files(config, fixture_files=None):
    if config.fixture:
        if not isinstance(fixture_files, InheritedFiles):
            raise ValueError("the engineering fixture requires fixed inherited files")
        return fixture_files
    if fixture_files is not None:
        raise ValueError("production B07 inherited inputs cannot be overridden")
    root = REPO / f"runs/ucope/gaussian_scale_initialization_b06_{config.master}"
    hashes = EXPECTED_INPUT_SHA256[config.master]
    return InheritedFiles(
        checkpoint=root / "Ghalf_final.pt",
        summary=root / "summary.json",
        source=root / "source.json",
        checkpoint_sha256=hashes["checkpoint"],
        summary_sha256=hashes["summary"],
        source_sha256=hashes["source"],
    )


def _inherited_spec_record(files):
    return {
        "checkpoint": str(files.checkpoint),
        "summary": str(files.summary),
        "source": str(files.source),
        "checkpoint_sha256": files.checkpoint_sha256,
        "summary_sha256": files.summary_sha256,
        "source_sha256": files.source_sha256,
    }


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _file_identity(path):
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "present": False}
    raw = path.read_bytes()
    return {"path": str(path), "present": True, "bytes": len(raw), "sha256": _sha256(raw)}


def _write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _tensor_digest(tensor):
    tensor = tensor.detach().cpu().contiguous()
    return _sha256(tensor.numpy().tobytes())


def _generator_digest(rng):
    return _tensor_digest(rng.get_state())


def _model_digest(actor, critic, *, common_only=False):
    digest = hashlib.sha256()
    items = [(f"actor.{name}", value) for name, value in actor.state_dict().items()]
    items += [(f"critic.{name}", value) for name, value in critic.state_dict().items()]
    for name, value in sorted(items):
        if common_only and (name == "actor.log_std" or name.startswith("actor.duration.")):
            continue
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(json.dumps(list(tensor.shape)).encode("ascii") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _parameter_groups(actor, critic):
    common = [
        parameter
        for name, parameter in actor.named_parameters()
        if not name.startswith("duration.")
    ]
    groups = {
        "common_actor": common,
        "critic": list(critic.parameters()),
        "total": list(actor.parameters()) + list(critic.parameters()),
    }
    if actor.duration is not None:
        groups["gate"] = list(actor.duration.parameters())
    return groups


def _snapshot(actor, critic):
    return {
        name: torch.cat([parameter.detach().flatten() for parameter in group]).clone()
        for name, group in _parameter_groups(actor, critic).items()
    }


def _exposure(initial, actor, critic):
    final = _snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        end = final[name]
        initial_norm = float(start.norm())
        displacement = float((end - start).norm())
        result[name] = {
            "parameters": start.numel(),
            "initial_norm": initial_norm,
            "final_norm": float(end.norm()),
            "displacement": displacement,
            "relative_displacement": None if initial_norm == 0 else displacement / initial_norm,
        }
    return result


def _safe_torch_load(raw):
    import io

    options = {"map_location": "cpu"}
    if "weights_only" in inspect.signature(torch.load).parameters:
        options["weights_only"] = True
    return torch.load(io.BytesIO(raw), **options)


def _read_and_check(path, expected, label):
    path = Path(path)
    raw = path.read_bytes()
    actual = _sha256(raw)
    if actual != expected:
        raise ValueError(f"retained B06 {label} SHA256 mismatch")
    return raw, {
        "path": str(path.relative_to(REPO) if path.is_relative_to(REPO) else path),
        "bytes": len(raw),
        "expected_sha256": expected,
        "sha256": actual,
    }


def _validate_tensor_state(state, label):
    if not isinstance(state, dict) or not state:
        raise ValueError(f"retained B06 {label} state is missing")
    if not all(
        isinstance(value, torch.Tensor)
        and value.device.type == "cpu"
        and value.dtype == torch.float32
        and torch.isfinite(value).all()
        for value in state.values()
    ):
        raise ValueError(f"retained B06 {label} state is not finite CPU FP32 tensor data")


def validate_and_copy_inputs(config, out, fixture_files=None):
    """Validate all retained bytes and metadata before any B scientific effect."""
    files = inherited_files(config, fixture_files)
    checkpoint_raw, checkpoint_identity = _read_and_check(
        files.checkpoint, files.checkpoint_sha256, "checkpoint"
    )
    summary_raw, summary_identity = _read_and_check(
        files.summary, files.summary_sha256, "summary"
    )
    source_raw, source_identity = _read_and_check(
        files.source, files.source_sha256, "source"
    )
    try:
        retained_summary = json.loads(summary_raw)
        retained_source = json.loads(source_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("retained B06 JSON input is invalid") from error
    payload = _safe_torch_load(checkpoint_raw)

    expected_metadata = {
        "object": SOURCE_OBJECT,
        "arm": "Ghalf",
        "seed": config.master,
        "train_episodes": 2048 if not config.fixture else config.train_episodes,
        "optimizer_steps": 4096 if not config.fixture else 2 * config.train_episodes,
    }
    if not isinstance(payload, dict):
        raise ValueError("retained B06 checkpoint is not a mapping")
    for key, expected in expected_metadata.items():
        if payload.get(key) != expected:
            raise ValueError(f"retained B06 checkpoint {key} mismatch")
    _validate_tensor_state(payload.get("actor"), "actor")
    _validate_tensor_state(payload.get("critic"), "critic")
    expected_log_std = [math.log(0.5)] * 3
    if not np.allclose(payload.get("initial_log_std"), expected_log_std, rtol=0, atol=1e-7):
        raise ValueError("retained B06 checkpoint initial_log_std mismatch")

    expected_summary = {
        "object": SOURCE_OBJECT,
        "master": config.master,
        "launch_sha": SOURCE_SHA,
        "status": "COMPLETE",
    }
    for key, expected in expected_summary.items():
        if retained_summary.get(key) != expected:
            raise ValueError(f"retained B06 summary {key} mismatch")
    expected_configuration = {
        "master": config.master,
        "horizon": config.horizon,
        "train_episodes": config.train_episodes,
        "eval_episodes": config.eval_episodes,
        "chunk": config.chunk,
        "watchdog_seconds": config.watchdog_seconds,
        "fixture": config.fixture,
    }
    if retained_summary.get("configuration") != expected_configuration:
        raise ValueError("retained B06 summary configuration mismatch")
    arm_record = retained_summary.get("arms", {}).get("Ghalf", {})
    if not arm_record.get("train_complete"):
        raise ValueError("retained B06 Ghalf fit is incomplete")
    if arm_record.get("checkpoint", {}).get("sha256") != checkpoint_identity["sha256"]:
        raise ValueError("retained B06 summary checkpoint digest mismatch")
    if arm_record.get("checkpoint", {}).get("bytes") != checkpoint_identity["bytes"]:
        raise ValueError("retained B06 summary checkpoint size mismatch")
    if arm_record.get("common_initial_sha256") != retained_summary.get(
        "paired_common_initial_sha256"
    ):
        raise ValueError("retained B06 common initialization digest mismatch")
    if not np.allclose(arm_record.get("initial_log_std"), expected_log_std, rtol=0, atol=1e-7):
        raise ValueError("retained B06 summary initial_log_std mismatch")
    expected_arm_counts = {
        "train_episodes": config.train_episodes,
        "train_team_steps": config.train_episodes * config.horizon,
        "optimizer_steps": 2 * config.train_episodes,
    }
    for key, expected in expected_arm_counts.items():
        if arm_record.get("counts", {}).get(key) != expected:
            raise ValueError(f"retained B06 summary Ghalf {key} mismatch")
    immutability = arm_record.get("evaluation_immutability", {})
    if immutability.get("optimizer_steps") != 0 or immutability.get(
        "parameter_exposure", {}
    ).get("total", {}).get("displacement") != 0:
        raise ValueError("retained B06 evaluation immutability metadata mismatch")

    if retained_source.get("object") != SOURCE_OBJECT or retained_source.get("launch_sha") != SOURCE_SHA:
        raise ValueError("retained B06 source binding mismatch")
    for field, expected in (
        ("shared_collector", EXPECTED_SHARED_SHA256["ordinary_learner"]),
        ("shared_policy", EXPECTED_SHARED_SHA256["ordinary_policy"]),
    ):
        identity = retained_source.get(field, {})
        if not identity.get("present") or identity.get("sha256") != expected:
            raise ValueError(f"retained B06 {field} identity mismatch")

    current_sources = {
        "ordinary_learner": REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/learner.py",
        "ordinary_policy": REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py",
        "reactive_learner": REPO / "experiments/candidates/ucope/reactive_renewal_b01/reactive.py",
        "scalar_gate": REPO / "experiments/candidates/ucope/reactive_rate_b03/scalar.py",
    }
    current_identities = {name: _file_identity(path) for name, path in current_sources.items()}
    for name, expected in EXPECTED_SHARED_SHA256.items():
        if current_identities[name].get("sha256") != expected:
            raise ValueError(f"B07 bound {name} source SHA256 mismatch")

    common = templates(config.master)
    b_actor, b_critic = scalar_actor(common)
    with torch.no_grad():
        b_actor.log_std.fill_(math.log(0.5))
    g_actor, g_critic = arm_copy(common, False)
    common_digests = {
        "Bhalf": _model_digest(b_actor, b_critic, common_only=True),
        "Ghalf_recreated": _model_digest(g_actor, g_critic, common_only=True),
        "B06_recorded": retained_summary["paired_common_initial_sha256"],
    }
    if len(set(common_digests.values())) != 1:
        raise ValueError("recreated B07/B06 common initialization digest mismatch")
    if not isinstance(b_actor.duration, ScalarGate) or not torch.equal(
        b_actor.duration.logits.detach(), torch.zeros(2)
    ):
        raise RuntimeError("Bhalf scalar gate did not initialize to zero logits")
    if not torch.allclose(
        b_actor.log_std.detach(), torch.full((3,), math.log(0.5)), rtol=0, atol=0
    ):
        raise RuntimeError("Bhalf latent scale did not initialize to 0.5")
    g_actor.load_state_dict(payload["actor"], strict=True)
    g_critic.load_state_dict(payload["critic"], strict=True)

    copies = {
        "checkpoint": (out / "inherited_Ghalf_final.pt", checkpoint_raw),
        "summary": (out / "inherited_B06_summary.json", summary_raw),
        "source": (out / "inherited_B06_source.json", source_raw),
    }
    for path, raw in copies.values():
        path.write_bytes(raw)
    copy_identities = {name: _file_identity(path) for name, (path, _raw) in copies.items()}
    for name, original in (
        ("checkpoint", checkpoint_identity),
        ("summary", summary_identity),
        ("source", source_identity),
    ):
        if copy_identities[name]["sha256"] != original["sha256"]:
            raise RuntimeError(f"retained B06 {name} copy is not byte-identical")

    provenance = {
        "source_sha": SOURCE_SHA,
        "originals": {
            "checkpoint": checkpoint_identity,
            "summary": summary_identity,
            "source": source_identity,
        },
        "copies": copy_identities,
        "checkpoint_metadata": {
            **expected_metadata,
            "initial_log_std": list(payload["initial_log_std"]),
        },
        "common_initial_sha256": common_digests,
        "bound_source_identities": current_identities,
        "g_optimizer_constructed": False,
        "retained_selection_scope": (
            "Ghalf is a selected B06 instance reused without retraining; this is conditional "
            "selected-instance evidence, not a fresh G learning replicate."
        ),
    }
    return {
        "b_actor": b_actor,
        "b_critic": b_critic,
        "g_actor": g_actor,
        "g_critic": g_critic,
        "provenance": provenance,
    }


def _curve_record(actor, rollout, when, episodes_seen):
    scale = actor.log_std.detach().clamp(-5, 2).exp()
    logits = actor.duration.logits.detach()
    return {
        "rollout": rollout,
        "when": when,
        "training_episodes_seen": episodes_seen,
        "log_std": actor.log_std.detach().tolist(),
        "latent_scale": scale.tolist(),
        "arithmetic_mean_latent_scale": float(scale.mean()),
        "gate_logits": logits.tolist(),
        "gate_probabilities": logits.softmax(-1).tolist(),
    }


def _early_scale_summary(values):
    selected = list(values[:256])
    return {
        "definition": (
            "arithmetic mean of the three latent Gaussian scales at each actual episode "
            "start, averaged over the first 256 Bhalf training episodes"
        ),
        "target_episode_starts": 256,
        "observed_episode_starts": len(selected),
        "complete": len(selected) == 256,
        "mean": statistics.mean(selected) if selected else None,
        "values": selected,
    }


def episode_slots(base, episode, horizon):
    before = torch.random.get_rng_state().clone()
    gaussian_rng = generator(base + 90000 + episode)
    gate_rng = generator(base + 95000 + episode)
    gaussian = torch.randn((horizon, 5, 3), generator=gaussian_rng, dtype=torch.float32)
    uniforms = torch.rand((horizon, 5), generator=gate_rng, dtype=torch.float32)
    if not torch.equal(before, torch.random.get_rng_state()):
        raise RuntimeError("private B07 slot generation changed the global Torch RNG")
    return gaussian, uniforms


@torch.no_grad()
def command_step(actor, mode, mean, recurrent, previous, eligible, gaussian, gate_uniform):
    if mode not in MODES:
        raise ValueError(f"unknown B07 mode {mode}")
    previous_t = torch.as_tensor(previous, dtype=torch.float32)
    gaussian = torch.as_tensor(gaussian, dtype=torch.float32)
    gate_uniform = torch.as_tensor(gate_uniform, dtype=torch.float32)
    is_b = mode.startswith("Bhalf_")
    is_mean = mode.endswith("mean")
    phase = torch.as_tensor(eligible, dtype=torch.bool) if is_b else torch.zeros(5, dtype=torch.bool)
    branch = torch.full((5,), FORCED_FRESH, dtype=torch.int8)
    gate_probability = torch.full((5,), torch.nan, dtype=torch.float32)
    keep = torch.zeros(5, dtype=torch.bool)
    if is_b and phase.any():
        inputs = torch.cat((recurrent[phase], previous_t[phase]), -1)
        probabilities = actor.duration(inputs).softmax(-1)[:, KEEP]
        gate_probability[phase] = probabilities
        keep[phase] = gate_uniform[phase] < probabilities
        branch[phase] = torch.where(
            keep[phase], torch.tensor(KEEP, dtype=torch.int8), torch.tensor(END, dtype=torch.int8)
        )
    fresh = ~keep
    if is_mean:
        u = mean
        gaussian_used = 0
    else:
        u = mean + actor.log_std.clamp(-5, 2).exp() * gaussian
        gaussian_used = int(fresh.sum())
    sent = previous_t.clone()
    sent[fresh] = u[fresh].tanh()
    next_eligible = fresh.numpy() if is_b else np.zeros(5, dtype=bool)
    return {
        "sent": sent.numpy().astype(np.float32, copy=False),
        "eligible": phase.numpy(),
        "branch": branch.numpy(),
        "fresh": fresh.numpy(),
        "next_eligible": next_eligible,
        "gate_keep_probability": gate_probability.numpy(),
        "gaussian_vectors_used": gaussian_used,
        "gate_uniforms_used": int(phase.sum()) if is_b else 0,
    }


def _empty_primitives(config):
    e, m, h, n, d = config.eval_episodes, len(MODES), config.horizon, 5, 3
    return {
        "mode_names": np.asarray(MODES, dtype="U20"),
        "completed": np.zeros((e, m, h), dtype=bool),
        "rewards": np.full((e, m, h), np.nan, dtype=np.float64),
        "commands": np.full((e, m, h, n, d), np.nan, dtype=np.float32),
        "means": np.full((e, m, h, n, d), np.nan, dtype=np.float32),
        "eligibility": np.zeros((e, m, h, n), dtype=bool),
        "branches": np.full((e, m, h, n), -1, dtype=np.int8),
        "fresh": np.zeros((e, m, h, n), dtype=bool),
        "gate_keep_probability": np.full((e, m, h, n), np.nan, dtype=np.float32),
        "gaussian_slots": np.full((e, h, n, d), np.nan, dtype=np.float32),
        "gate_uniform_slots": np.full((e, h, n), np.nan, dtype=np.float32),
    }


@torch.no_grad()
def deploy_episode(env, actor, mode, horizon, reset_seed, gaussian, gate_uniforms,
                   metadata, destination, check, counters):
    check()
    obs, _info = env.reset(seed=reset_seed)
    counters["explicit_resets"] += 1
    last = np.zeros((5, 3), dtype=np.float32)
    eligible = np.zeros(5, dtype=bool)
    hidden = torch.zeros(1, 5, 64, dtype=torch.float32)
    rewards = []
    decisions = {
        "eligibility_decisions": 0,
        "keep_decisions": 0,
        "end_decisions": 0,
        "forced_fresh_decisions": 0,
        "fresh_commands": 0,
        "gaussian_vectors_used": 0,
        "gate_uniforms_used": 0,
    }
    for tick in range(horizon):
        check()
        phase = eligible if mode.startswith("Bhalf_") else np.zeros(5, dtype=bool)
        x = actor_features(obs, last, phase.astype(np.int64))
        mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        if mean.dtype != torch.float32 or not torch.isfinite(mean).all():
            raise FloatingPointError("nonfinite or non-FP32 B07 actor output")
        counters["actor_forward_calls"] += 1
        counters["recurrent_observations"] += 5
        step = command_step(
            actor, mode, mean, recurrent, last, phase, gaussian[tick], gate_uniforms[tick]
        )
        destination["means"][tick] = mean.numpy()
        destination["commands"][tick] = step["sent"]
        destination["eligibility"][tick] = step["eligible"]
        destination["branches"][tick] = step["branch"]
        destination["fresh"][tick] = step["fresh"]
        destination["gate_keep_probability"][tick] = step["gate_keep_probability"]
        events = {
            "eligibility_decisions": int(step["eligible"].sum()),
            "keep_decisions": int((step["branch"] == KEEP).sum()),
            "end_decisions": int((step["branch"] == END).sum()),
            "forced_fresh_decisions": int((step["branch"] == FORCED_FRESH).sum()),
            "fresh_commands": int(step["fresh"].sum()),
            "gaussian_vectors_used": step["gaussian_vectors_used"],
            "gate_uniforms_used": step["gate_uniforms_used"],
        }
        for name, amount in events.items():
            decisions[name] += amount
            counters[name] += amount
        counters["step_calls"] += 1
        next_obs, _scalar, terminated, truncated, info = env.step(step["sent"])
        # A returned environment transition is exposure even if reward extraction or
        # validation fails; completed remains the stricter valid-reward primitive mask.
        counters["team_steps"] += 1
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite B07 team reward")
        destination["rewards"][tick] = reward
        destination["completed"][tick] = True
        counters["valid_reward_steps"] += 1
        rewards.append(reward)
        last = step["sent"].copy()
        eligible = step["next_eligible"].copy()
        obs = next_obs
        if (terminated or truncated) and tick + 1 < horizon:
            raise RuntimeError(f"incomplete B07 episode: boundary at {tick + 1}/{horizon}")
        check()
    if mode.startswith("Ghalf_") and destination["eligibility"].any():
        raise RuntimeError("retained ordinary Ghalf used nonzero phase")
    total = sum(rewards)
    return dict(metadata, reset_seed=reset_seed, steps=horizon, reward_sum=total,
                J=total / horizon, **decisions)


def final_panel(rows, expected, invocation_complete):
    values = {
        mode: {
            row["episode"]: row["J"]
            for row in rows
            if row["mode"] == mode and row["phase"] == "eval"
        }
        for mode in MODES
    }
    full = {
        mode: sorted(items) == list(range(expected))
        and all(math.isfinite(value) for value in items.values())
        for mode, items in values.items()
    }
    panel = {
        "selected_contrast": "Bhalf_sampled_minus_Ghalf_mean",
        "returns": {
            mode: [items[index] for index in sorted(items)]
            for mode, items in values.items()
        },
        "episode_ids": {mode: sorted(items) for mode, items in values.items()},
        "arm_means": {
            mode: statistics.mean(items.values()) if items else None
            for mode, items in values.items()
        },
        "all_panels_complete": all(full.values()),
    }
    for name, first, second in CONTRASTS:
        ids = sorted(values[first].keys() & values[second].keys())
        differences = [values[first][index] - values[second][index] for index in ids]
        panel[name] = {
            "episode_ids": ids,
            "differences": differences,
            "mean": statistics.mean(differences) if differences else None,
            "conditional_se": (
                statistics.stdev(differences) / math.sqrt(len(differences))
                if len(differences) > 1 else None
            ),
            "signs": [1 if value > 0 else -1 if value < 0 else 0 for value in differences],
            "favorable": sum(value > 0 for value in differences),
            "adverse": sum(value < 0 for value in differences),
            "tied": sum(value == 0 for value in differences),
            "panel_complete": full[first] and full[second],
            "complete": bool(invocation_complete and full[first] and full[second]),
        }
    panel["primary"] = panel["Bhalf_sampled_minus_Ghalf_mean"]
    panel["complete"] = bool(invocation_complete and panel["all_panels_complete"])
    panel["reading_scope"] = (
        "Conditional comparison with one newly trained Bhalf and the selected retained B06 "
        "Ghalf instance; world-panel SEs are not training-population precision."
    )
    return panel


def _telemetry(start, cpu_start):
    peak_rss_kib = None
    unmeasured = ["complete process exit wall"]
    try:
        import resource
        peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        unmeasured.append("single-process peak RSS")
    return {
        "wall_seconds": time.monotonic() - start,
        "wall_scope": "runner main entry through B07 publication accounting",
        "process_cpu_seconds": time.process_time() - cpu_start,
        "process_cpu_scope": "study entry through B07 publication accounting",
        "peak_rss_kib": peak_rss_kib,
        "peak_rss_scope": "single process ru_maxrss" if peak_rss_kib is not None else "unavailable",
        "complete_process_exit_wall": None,
        "external_scope": (
            "the native launch manifest is authoritative for actual-node and complete-process telemetry"
        ),
        "resources_unmeasured": unmeasured,
    }


def _close_all(environments):
    errors = []
    for mode, env in environments.items():
        if hasattr(env, "close"):
            try:
                env.close()
            except Exception as error:
                errors.append(f"{mode}: {type(error).__name__}: {error}")
    return errors


def run(config, out, admission, start=None, factory=None, fixture_files=None):
    """Run one Bhalf fit and its fixed retained-Ghalf comparison."""
    require_config(config)
    if not config.fixture and factory is not None:
        raise ValueError("production B07 environment cannot be overridden")
    if not config.fixture and fixture_files is not None:
        raise ValueError("production B07 inherited inputs cannot be overridden")
    admitted_sha = admission.get("sha")
    if not isinstance(admitted_sha, str) or not admitted_sha:
        raise ValueError("B07 requires an admitted source SHA")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "config.json", asdict(config))
    _write_json(out / "admission.json", dict(admission))

    source = {
        "object": OBJECT,
        "launch_sha": admitted_sha,
        "runner": _file_identity(REPO / "scripts/run_ucope_lower_scale_reuse_b07.py"),
        "study": _file_identity(Path(__file__)),
        "reactive_learner": _file_identity(
            REPO / "experiments/candidates/ucope/reactive_renewal_b01/reactive.py"
        ),
        "scalar_gate": _file_identity(
            REPO / "experiments/candidates/ucope/reactive_rate_b03/scalar.py"
        ),
        "ordinary_learner": _file_identity(
            REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/learner.py"
        ),
        "ordinary_policy": _file_identity(
            REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py"
        ),
    }
    limits = []
    rows, train_rows, update_rows, curve_rows = [], [], [], []
    arrays = _empty_primitives(config)
    arm_record = {"fit_started": False, "train_complete": False}
    evaluation_counts = {}
    actors = {}
    critics = {}
    evaluation_snapshots = {}
    summary = {
        "object": OBJECT,
        "notebook": NOTEBOOK,
        "notebook_section": NOTEBOOK_SECTION,
        "configuration": asdict(config),
        "master": config.master,
        "selected_masters": list(ALLOWED_MASTERS),
        "launch_sha": admitted_sha,
        "admission": dict(admission),
        "process_identity": {
            "runner_pid": os.getpid(),
            "runner_parent_pid": os.getppid(),
            "admission_parent_pid": admission.get("parent_pid"),
            "admission_child_pid": admission.get("child_pid"),
        },
        "declared_execution_node": EXECUTION_NODE,
        "device": "cpu",
        "dtype": "float32",
        "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
        "mode": "ENGINEERING_FIXTURE" if config.fixture else "BHALF_RETAINED_GHALF_COMPARISON",
        "status": "INCOMPLETE",
        "new_Bhalf": arm_record,
        "evaluation_counts": evaluation_counts,
        "limits": limits,
        "policy_definition": {
            "Bhalf": (
                "trainable scalar KEEP/END gate with zero initial logits, trainable initial "
                "latent scale 0.5, minimum-one/maximum-two-tick reactive command law"
            ),
            "Ghalf": "retained B06 checkpoint, frozen ordinary fresh phase-zero control",
            "primary": "Bhalf_sampled minus Ghalf_mean on paired new worlds",
        },
        "prepared_new_exposure": {
            "started_fits_if_authorized": 3,
            "train_episodes": 6144,
            "train_team_steps": 1572864,
            "optimizer_calls": 12288,
            "eval_episodes": 768,
            "eval_team_steps": 196608,
            "total_new_team_steps": 1769472,
            "owner_window_started_fits_before_request": 12,
            "owner_window_started_fits_if_authorized": 15,
            "unchanged_deadline_utc": "2026-09-21 04:06:07 UTC",
            "preparation_boundary": (
                "This implementation grants no launch; the twelve-fit owner ceiling is exhausted "
                "and execution requires a new explicit owner allocation plus admission."
            ),
        },
        "inherited_exposure": {
            "retained_Ghalf_fits": 3,
            "new_Ghalf_fits": 0,
            "qualification": "B06 training and selection provenance is inherited, not replicated.",
        },
    }
    base = 100000 * config.master
    summary["rng"] = {
        "base": base,
        "common_initialization": base + 11,
        "train_world_start": base + 10000,
        "Bhalf_training_velocity": base + 21,
        "Bhalf_training_gate": base + 22,
        "eval_world_start": base + 40000,
        "eval_gaussian_slots": "base+90000+episode",
        "eval_gate_uniform_slots": "base+95000+episode",
    }
    global_rng_before = torch.random.get_rng_state().clone()

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError(
                f"B07 {config.watchdog_seconds:g}-second watchdog expired; preserve partial work"
            )

    if factory is None:
        if config.fixture:
            from ..uav_motion_prefix_b01.environment import SyntheticAdapter
            factory = lambda seed: SyntheticAdapter(seed, config.horizon)
        else:
            from ..uav_motion_prefix_b01.environment import make_real
            factory = make_real

    train_path = out / "train_episodes.jsonl"
    update_path = out / "updates.jsonl"
    curve_path = out / "curves.jsonl"
    eval_path = out / "eval_episodes.jsonl"
    with (
        train_path.open("w", encoding="utf-8") as train_file,
        update_path.open("w", encoding="utf-8") as update_file,
        curve_path.open("w", encoding="utf-8") as curve_file,
        eval_path.open("w", encoding="utf-8") as eval_file,
    ):
        def emit_train(row):
            train_rows.append(row)
            train_file.write(json.dumps(row, allow_nan=False) + "\n")
            train_file.flush()

        try:
            check()
            validated = validate_and_copy_inputs(config, out, fixture_files)
            summary["inherited_input"] = validated["provenance"]
            source["inherited_input"] = validated["provenance"]
            actors = {
                "Bhalf": validated["b_actor"],
                "Ghalf": validated["g_actor"],
            }
            critics = {
                "Bhalf": validated["b_critic"],
                "Ghalf": validated["g_critic"],
            }
            actor, critic = actors["Bhalf"], critics["Bhalf"]
            initial = _snapshot(actor, critic)
            arm_record.update({
                "initial_model_sha256": _model_digest(actor, critic),
                "common_initial_sha256": _model_digest(actor, critic, common_only=True),
                "initial_log_std": actor.log_std.detach().tolist(),
                "initial_scale": actor.log_std.detach().clamp(-5, 2).exp().tolist(),
                "initial_gate_logits": actor.duration.logits.detach().tolist(),
                "initial_gate_probabilities": actor.duration.logits.detach().softmax(-1).tolist(),
                "counts": new_counts(renewal=True, short=True),
            })
            counts = arm_record["counts"]
            optimizer = optimizer_for(actor, critic)
            optimizer_parameters = {
                id(parameter)
                for group in optimizer.param_groups
                for parameter in group["params"]
            }
            if not actor.log_std.requires_grad or id(actor.log_std) not in optimizer_parameters:
                raise RuntimeError("Bhalf log_std is not trainable through its optimizer")
            if id(actor.duration.logits) not in optimizer_parameters:
                raise RuntimeError("Bhalf scalar gate is not trainable through its optimizer")
            velocity_rng = generator(base + 21)
            gate_rng = generator(base + 22)
            velocity_initial = _generator_digest(velocity_rng)
            gate_initial = _generator_digest(gate_rng)
            episode_start_scales = []
            env = None
            training_error = None
            try:
                check()
                # The retained input/model validation above is not a new fit. The Bhalf
                # attempt starts only when its scientific environment construction begins.
                arm_record["fit_started"] = True
                env = factory(base + 10000)
                counts["constructors"] += 1
                counts["constructor_resets"] += 1
                for rollout in range(config.train_episodes // 2):
                    before = _curve_record(actor, rollout, "before_collection", 2 * rollout)
                    curve_rows.append(before)
                    curve_file.write(json.dumps(before, allow_nan=False) + "\n")
                    curve_file.flush()
                    episodes = []
                    for offset in range(2):
                        episode = 2 * rollout + offset
                        resets_before = counts["explicit_resets"]
                        try:
                            collected = reactive.collect_episode(
                                env, actor, critic, config.horizon,
                                base + 10000 + episode, velocity_rng, gate_rng,
                                {"master": config.master, "arm": "Bhalf",
                                 "phase": "train", "episode": episode},
                                check, counts, emit_train, real=not config.fixture,
                            )
                        finally:
                            if counts["explicit_resets"] > resets_before:
                                episode_start_scales.append(
                                    before["arithmetic_mean_latent_scale"]
                                )
                        episodes.append(collected)
                    losses = reactive.update(
                        actor, critic, optimizer, episodes, config.chunk, check, counts
                    )
                    counts["rollouts"] += 1
                    update_row = {"arm": "Bhalf", "rollout": rollout, "epochs": losses}
                    update_rows.append(update_row)
                    update_file.write(json.dumps(update_row, allow_nan=False) + "\n")
                    update_file.flush()
                    after = _curve_record(
                        actor, rollout, "after_update", 2 * rollout + 2
                    )
                    curve_rows.append(after)
                    curve_file.write(json.dumps(after, allow_nan=False) + "\n")
                    curve_file.flush()
                arm_record["train_complete"] = True
                checkpoint = out / "Bhalf_final.pt"
                torch.save(
                    {
                        "object": OBJECT,
                        "actor": actor.state_dict(),
                        "critic": critic.state_dict(),
                        "arm": "Bhalf",
                        "seed": config.master,
                        "train_episodes": config.train_episodes,
                        "optimizer_steps": counts["optimizer_steps"],
                        "initial_log_std": arm_record["initial_log_std"],
                        "inherited_Ghalf_sha256": validated["provenance"]["originals"]
                        ["checkpoint"]["sha256"],
                    },
                    checkpoint,
                )
                arm_record["checkpoint"] = _file_identity(checkpoint)
            except Exception as error:
                training_error = error
            finally:
                close_errors = _close_all({"Bhalf_training": env} if env is not None else {})
                arm_record["movement"] = _exposure(initial, actor, critic)
                arm_record["final_log_std"] = actor.log_std.detach().tolist()
                arm_record["final_scale"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
                arm_record["final_gate_logits"] = actor.duration.logits.detach().tolist()
                arm_record["final_gate_probabilities"] = (
                    actor.duration.logits.detach().softmax(-1).tolist()
                )
                arm_record["first_256_episode_start_scale"] = _early_scale_summary(
                    episode_start_scales
                )
                arm_record["velocity_rng"] = {
                    "initial_sha256": velocity_initial,
                    "final_sha256": _generator_digest(velocity_rng),
                }
                arm_record["gate_rng"] = {
                    "initial_sha256": gate_initial,
                    "final_sha256": _generator_digest(gate_rng),
                }
                if close_errors:
                    limits.extend(close_errors)
            if training_error is not None:
                raise training_error
            if close_errors:
                raise RuntimeError("; ".join(close_errors))

            for model in (*actors.values(), *critics.values()):
                model.eval()
                model.requires_grad_(False)
            evaluation_snapshots = {
                name: _snapshot(actors[name], critics[name]) for name in ("Bhalf", "Ghalf")
            }
            counter_names = (
                "environment_constructors", "actor_forward_calls", "recurrent_observations",
                "explicit_resets", "step_calls", "team_steps", "valid_reward_steps",
                "completed_episodes", "eligibility_decisions",
                "keep_decisions", "end_decisions", "forced_fresh_decisions", "fresh_commands",
                "gaussian_vectors_used", "gate_uniforms_used",
            )
            evaluation_counts.update({
                mode: dict.fromkeys(counter_names, 0) for mode in MODES
            })
            eval_environments = {}
            evaluation_error = None
            try:
                for mode in MODES:
                    eval_environments[mode] = factory(base + 40000)
                    evaluation_counts[mode]["environment_constructors"] += 1
                for episode in range(config.eval_episodes):
                    check()
                    gaussian, uniforms = episode_slots(base, episode, config.horizon)
                    arrays["gaussian_slots"][episode] = gaussian.numpy()
                    arrays["gate_uniform_slots"][episode] = uniforms.numpy()
                    for mode_index, mode in enumerate(MODES):
                        family = "Bhalf" if mode.startswith("Bhalf_") else "Ghalf"
                        destination = {
                            key: arrays[key][episode, mode_index]
                            for key in (
                                "completed", "rewards", "commands", "means", "eligibility",
                                "branches", "fresh", "gate_keep_probability",
                            )
                        }
                        row = deploy_episode(
                            eval_environments[mode], actors[family], mode, config.horizon,
                            base + 40000 + episode, gaussian, uniforms,
                            {"master": config.master, "mode": mode,
                             "phase": "eval", "episode": episode},
                            destination, check, evaluation_counts[mode],
                        )
                        rows.append(row)
                        evaluation_counts[mode]["completed_episodes"] += 1
                        eval_file.write(json.dumps(row, allow_nan=False) + "\n")
                        eval_file.flush()
                        if mode == "Bhalf_mean":
                            b_sampled = MODES.index("Bhalf_sampled")
                            b_mean = MODES.index("Bhalf_mean")
                            if not np.array_equal(
                                arrays["eligibility"][episode, b_sampled],
                                arrays["eligibility"][episode, b_mean],
                            ) or not np.array_equal(
                                arrays["branches"][episode, b_sampled],
                                arrays["branches"][episode, b_mean],
                            ):
                                raise RuntimeError("Bhalf sampled/mean branch masks diverged")
            except Exception as error:
                evaluation_error = error
            finally:
                close_errors = _close_all(eval_environments)
                if close_errors:
                    limits.extend(close_errors)
            if evaluation_error is not None:
                raise evaluation_error
            if close_errors:
                raise RuntimeError("; ".join(close_errors))
            summary["status"] = "COMPLETE"
        except Exception as error:
            traceback.print_exc()
            summary["error"] = {"type": type(error).__name__, "message": str(error)}

    integrity = {}
    for family, initial in evaluation_snapshots.items():
        movement = _exposure(initial, actors[family], critics[family])
        integrity[family] = {
            "parameter_exposure": movement,
            "exactly_unchanged": movement["total"]["displacement"] == 0,
            "optimizer_steps": 0,
        }
    summary["evaluation_immutability"] = integrity
    if integrity and not all(item["exactly_unchanged"] for item in integrity.values()):
        summary["status"] = "INCOMPLETE"
        summary["error"] = {
            "type": "EvaluationMutationError",
            "message": "a frozen B07 evaluation model changed",
        }

    invocation_complete = summary["status"] == "COMPLETE"
    summary["panel"] = final_panel(rows, config.eval_episodes, invocation_complete)
    summary["fit_accounting"] = {
        "new_fit_arm": "Bhalf",
        "allocated_new_fits_this_invocation": 1,
        "allocated_new_fits_complete_batch": 3,
        "started_new_fits": int(bool(arm_record.get("fit_started"))),
        "completed_new_fits": int(bool(arm_record.get("train_complete"))),
        "inherited_Ghalf_fits_this_invocation": 1 if "inherited_input" in summary else 0,
        "inherited_fits_are_not_new_starts": True,
        "qualification": (
            "Prepared without launch authority. If separately allocated and admitted, every "
            "started Bhalf attempt counts and no failed attempt gains replacement allowance."
        ),
    }
    train_counts = arm_record.get("counts", {})
    eval_episodes = sum(
        item.get("completed_episodes", 0) for item in evaluation_counts.values()
    )
    eval_steps = sum(item.get("team_steps", 0) for item in evaluation_counts.values())
    eval_valid_reward_steps = sum(
        item.get("valid_reward_steps", 0) for item in evaluation_counts.values()
    )
    summary["counts"] = {
        "new_train_episodes": train_counts.get("train_episodes", 0),
        "new_train_team_steps": train_counts.get("train_team_steps", 0),
        "new_optimizer_steps": train_counts.get("optimizer_steps", 0),
        "new_training_step_calls": train_counts.get("step_calls", 0),
        "new_training_gate_decisions": train_counts.get("train_gate_decisions", 0),
        "new_training_keep_decisions": train_counts.get("train_keep_decisions", 0),
        "new_training_end_decisions": train_counts.get("train_end_decisions", 0),
        "final_eval_episodes": eval_episodes,
        "final_eval_team_steps": eval_steps,
        "final_eval_valid_reward_steps": eval_valid_reward_steps,
        "evaluation_optimizer_steps": 0,
        "new_team_steps": train_counts.get("train_team_steps", 0) + eval_steps,
        "per_mode_evaluation": evaluation_counts,
    }
    summary["rng_isolation"] = {
        "global_torch_rng_unchanged": bool(
            torch.equal(global_rng_before, torch.random.get_rng_state())
        ),
        "qualification": (
            "Bhalf velocity and gate streams are private; no equality with the historical "
            "Ghalf final RNG state is claimed because B consumes fewer velocity draws."
        ),
    }
    summary["telemetry"] = _telemetry(start, cpu_start)
    summary["process_identity"]["publication_pid"] = os.getpid()
    summary["resource_note"] = (
        "Telemetry scopes are explicit; unavailable complete-process telemetry limits only resource claims."
    )
    source.setdefault("inherited_input", {
        "validated": False,
        "expected": _inherited_spec_record(inherited_files(config, fixture_files)),
    })
    _write_json(out / "source.json", source)
    np.savez_compressed(out / "evaluation_primitives.npz", **arrays)
    artifact_names = (
        "config.json", "admission.json", "source.json", "train_episodes.jsonl",
        "updates.jsonl", "curves.jsonl", "eval_episodes.jsonl",
        "evaluation_primitives.npz", "Bhalf_final.pt", "inherited_Ghalf_final.pt",
        "inherited_B06_summary.json", "inherited_B06_source.json",
    )
    summary["artifacts"] = {
        name: _file_identity(out / name) for name in artifact_names
    }
    write_summary(out / "summary.json", summary)
    return summary
