"""Fixed-checkpoint C/B/G deployment evaluation with no training or optimizer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import hashlib
import inspect
import io
import json
import math
from pathlib import Path
import statistics
import tarfile
import time
import traceback

import numpy as np
import torch

from ..reactive_renewal_b01.reactive import END, KEEP
from ..reactive_rate_b03.scalar import scalar_actor
from ..uav_motion_prefix_b01.environment import actor_features, team_reward
from ..uav_motion_prefix_b01.policy import arm_copy, templates


OBJECT = "UCOPE_MEAN_AGREEMENT_DEPLOYMENT_B05"
SOURCE_OBJECT = "UCOPE_SCALAR_FEEDBACK_B04"
NOTEBOOK = "docs/research/candidates/ucope/NOTES.md"
NOTEBOOK_SECTION = "2026-09-20 — selected B05: frozen-policy mean-agreement deployment"
EXECUTION_NODE = "local_linux"
ALLOWED_MASTERS = (8931, 8932, 8933)
ARMS = ("C", "B", "G_sampled", "G_mean")
CONTRASTS = (
    ("C_minus_G_sampled", "C", "G_sampled"),
    ("C_minus_B", "C", "B"),
    ("C_minus_G_mean", "C", "G_mean"),
    ("G_mean_minus_G_sampled", "G_mean", "G_sampled"),
)
ARCHIVE_SHA256 = {
    8931: "a95ef61361aaa823c2c00fcfc9c77e7660d3c7402f3eb3de7dca0d371140ef86",
    8932: "e6d5b28087152353ab7de164e38de84afe80ad769b30f22156aa6093c5827f59",
    8933: "d9f47cec19cc6e5c7629687932d0435dec1318cfa1a33ee425e464a8b0bd4528",
}
REPO = Path(__file__).resolve().parents[4]
FORCED_FRESH = 2

_GH_NODES_ARRAY, _GH_WEIGHTS_ARRAY = np.polynomial.hermite.hermgauss(64)
_GH_NODES = torch.from_numpy(_GH_NODES_ARRAY)
_GH_WEIGHTS = torch.from_numpy(_GH_WEIGHTS_ARRAY)


@dataclass(frozen=True)
class Config:
    master: int
    horizon: int = 256
    eval_episodes: int = 64
    watchdog_seconds: float = 1800.0
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(
            master=9931,
            horizon=6,
            eval_episodes=3,
            watchdog_seconds=180.0,
            fixture=True,
        )


def require_config(config):
    if config.fixture:
        if config != Config.engineering():
            raise ValueError("only the fixed B05 engineering fixture is supported off path")
        return
    if config.master not in ALLOWED_MASTERS:
        raise ValueError("master must be one of the three selected B05 checkpoint pairs")
    if config != Config(master=config.master):
        raise ValueError("B05 fixed-checkpoint evaluation exposure is fixed")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _file_identity(path):
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "present": False}
    data = path.read_bytes()
    return {
        "path": str(path),
        "present": True,
        "bytes": len(data),
        "sha256": _sha256(data),
    }


def _write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def archive_spec(config, archive_path=None, archive_sha256=None):
    if config.fixture:
        if archive_path is None or archive_sha256 is None:
            raise ValueError("the engineering test API requires its archive and digest")
        return Path(archive_path), archive_sha256
    if archive_path is not None or archive_sha256 is not None:
        raise ValueError("production B05 archive identity cannot be overridden")
    path = REPO / f"runs/ucope/scalar_feedback_b04_{config.master}/checkpoints-and-console.tar.gz"
    return path, ARCHIVE_SHA256[config.master]


def _safe_torch_load(data):
    options = {"map_location": "cpu"}
    if "weights_only" in inspect.signature(torch.load).parameters:
        options["weights_only"] = True
    return torch.load(io.BytesIO(data), **options)


def _validate_checkpoint(payload, arm, master):
    expected = {
        "object": SOURCE_OBJECT,
        "arm": arm,
        "seed": master,
        "train_episodes": 2048,
        "optimizer_steps": 4096,
    }
    if not isinstance(payload, dict):
        raise ValueError(f"{arm} checkpoint is not a mapping")
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"{arm} checkpoint {key} mismatch")
    state = payload.get("actor")
    if not isinstance(state, dict) or not state:
        raise ValueError(f"{arm} checkpoint has no actor state")
    if not all(
        isinstance(value, torch.Tensor)
        and value.device.type == "cpu"
        and torch.isfinite(value).all()
        for value in state.values()
    ):
        raise ValueError(f"{arm} actor state is not finite CPU tensor data")


def load_checkpoint_pair(config, archive_path=None, archive_sha256=None):
    """Verify the committed archive, then read only B/G checkpoint members in memory."""
    path, expected_digest = archive_spec(config, archive_path, archive_sha256)
    raw = path.read_bytes()
    actual_digest = _sha256(raw)
    if actual_digest != expected_digest:
        raise ValueError("B04 checkpoint archive SHA256 mismatch")
    payloads = {}
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        entries = archive.getmembers()
        for arm in ("B", "G"):
            name = f"{arm}_final.pt"
            matches = [entry for entry in entries if entry.name == name]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError(f"archive must contain exactly one regular {name}")
            stream = archive.extractfile(matches[0])
            if stream is None:
                raise ValueError(f"archive member {name} is unreadable")
            data = stream.read()
            if len(data) != matches[0].size:
                raise ValueError(f"archive member {name} is truncated")
            payload = _safe_torch_load(data)
            _validate_checkpoint(payload, arm, config.master)
            payloads[arm] = payload
            members[arm] = {
                "name": name,
                "bytes": len(data),
                "sha256": _sha256(data),
                "metadata": {
                    key: payload[key]
                    for key in ("object", "arm", "seed", "train_episodes", "optimizer_steps")
                },
            }
    identity = {
        "path": str(path.relative_to(REPO) if path.is_relative_to(REPO) else path),
        "bytes": len(raw),
        "expected_sha256": expected_digest,
        "sha256": actual_digest,
        "members": members,
        "in_memory_extraction_only": True,
    }
    return payloads, identity


def actor_digest(actor):
    digest = hashlib.sha256()
    for name, value in sorted(actor.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(json.dumps(list(tensor.shape)).encode("ascii") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _snapshot(actor):
    return {name: value.detach().clone() for name, value in actor.state_dict().items()}


def _movement(before, actor):
    after = actor.state_dict()
    exact = all(torch.equal(before[name], after[name]) for name in before)
    squared = sum(
        float((after[name].detach().double() - before[name].double()).square().sum())
        for name in before
    )
    return exact, math.sqrt(squared)


def build_frozen_actors(master, payloads):
    common = templates(master)
    b_template, _ = scalar_actor(common)
    g_template, _ = arm_copy(common, False)
    actors = {
        "C": copy.deepcopy(b_template),
        "B": copy.deepcopy(b_template),
        "G_sampled": copy.deepcopy(g_template),
        "G_mean": copy.deepcopy(g_template),
    }
    for arm, actor in actors.items():
        source = "B" if arm in ("C", "B") else "G"
        actor.load_state_dict(payloads[source]["actor"], strict=True)
        actor.eval()
        actor.requires_grad_(False)
        if any(
            parameter.device.type != "cpu" or parameter.dtype != torch.float32
            for parameter in actor.parameters()
        ):
            raise ValueError("B05 actors must remain CPU FP32")
    if actor_digest(actors["C"]) != actor_digest(actors["B"]):
        raise RuntimeError("C and B did not load identical actor bytes")
    if actor_digest(actors["G_sampled"]) != actor_digest(actors["G_mean"]):
        raise RuntimeError("G deployment modes did not load identical actor bytes")
    return actors


def mean_agreement_distances(previous, mean, log_std):
    """Return D_keep and fixed GH64 D_fresh in float64 from FP32 actor outputs."""
    previous = torch.as_tensor(previous, dtype=torch.float64)
    mean64 = mean.detach().to(dtype=torch.float64, device="cpu")
    sigma64 = log_std.detach().clamp(-5, 2).exp().to(dtype=torch.float64, device="cpu")
    center = mean64.tanh()
    sampled = (
        mean64[..., None]
        + sigma64[..., None] * math.sqrt(2.0) * _GH_NODES
    ).tanh()
    expected = (
        _GH_WEIGHTS * (sampled - center[..., None]).square()
    ).sum(-1) / math.sqrt(math.pi)
    d_keep = (previous - center).square().sum(-1)
    d_fresh = expected.sum(-1)
    return d_keep, d_fresh


def keep_from_distances(d_keep, d_fresh):
    """The frozen deterministic tie rule is KEEP."""
    return torch.as_tensor(d_keep) <= torch.as_tensor(d_fresh)


@torch.no_grad()
def command_step(actor, arm, mean, recurrent, previous, eligible, gaussian, gate_uniform):
    """Apply one deployment command decision without advancing an environment."""
    if arm not in ARMS:
        raise ValueError(f"unknown B05 arm {arm}")
    previous_t = torch.as_tensor(previous, dtype=torch.float32)
    gaussian = torch.as_tensor(gaussian, dtype=torch.float32)
    gate_uniform = torch.as_tensor(gate_uniform, dtype=torch.float32)
    phase = torch.as_tensor(eligible, dtype=torch.bool)
    if arm.startswith("G_"):
        phase = torch.zeros(5, dtype=torch.bool)
    branch = torch.full((5,), FORCED_FRESH, dtype=torch.int8)
    d_keep = torch.full((5,), torch.nan, dtype=torch.float64)
    d_fresh = torch.full((5,), torch.nan, dtype=torch.float64)
    gate_probability = torch.full((5,), torch.nan, dtype=torch.float32)

    if arm == "G_mean":
        fresh = torch.ones(5, dtype=torch.bool)
        sent = mean.tanh()
        next_eligible = torch.zeros(5, dtype=torch.bool)
        gaussian_used = 0
        gate_used = 0
    else:
        keep = torch.zeros(5, dtype=torch.bool)
        if arm == "C" and phase.any():
            all_d_keep, all_d_fresh = mean_agreement_distances(
                previous_t, mean, actor.log_std
            )
            d_keep[phase] = all_d_keep[phase]
            d_fresh[phase] = all_d_fresh[phase]
            keep[phase] = keep_from_distances(d_keep[phase], d_fresh[phase])
        elif arm == "B" and phase.any():
            inputs = torch.cat((recurrent[phase], previous_t[phase]), -1)
            probabilities = actor.duration(inputs).softmax(-1)[:, KEEP]
            gate_probability[phase] = probabilities
            keep[phase] = gate_uniform[phase] < probabilities
        branch[phase] = torch.where(
            keep[phase], torch.tensor(KEEP, dtype=torch.int8), torch.tensor(END, dtype=torch.int8)
        )
        fresh = ~keep
        u = mean + actor.log_std.clamp(-5, 2).exp() * gaussian
        sent = previous_t.clone()
        sent[fresh] = u[fresh].tanh()
        next_eligible = fresh if arm in ("C", "B") else torch.zeros(5, dtype=torch.bool)
        gaussian_used = int(fresh.sum())
        gate_used = int(phase.sum()) if arm == "B" else 0

    return {
        "sent": sent.numpy().astype(np.float32, copy=False),
        "eligible": phase.numpy(),
        "branch": branch.numpy(),
        "fresh": fresh.numpy(),
        "next_eligible": next_eligible.numpy(),
        "d_keep": d_keep.numpy(),
        "d_fresh": d_fresh.numpy(),
        "gate_keep_probability": gate_probability.numpy(),
        "gaussian_vectors_used": gaussian_used,
        "gate_uniforms_used": gate_used,
    }


def _empty_primitives(config):
    e, a, h, n, d = config.eval_episodes, len(ARMS), config.horizon, 5, 3
    return {
        "arm_names": np.asarray(ARMS, dtype="U16"),
        "completed": np.zeros((e, a, h), dtype=bool),
        "rewards": np.full((e, a, h), np.nan, dtype=np.float64),
        "commands": np.full((e, a, h, n, d), np.nan, dtype=np.float32),
        "means": np.full((e, a, h, n, d), np.nan, dtype=np.float32),
        "eligibility": np.zeros((e, a, h, n), dtype=bool),
        "branches": np.full((e, a, h, n), -1, dtype=np.int8),
        "fresh": np.zeros((e, a, h, n), dtype=bool),
        "c_d_keep": np.full((e, a, h, n), np.nan, dtype=np.float64),
        "c_d_fresh": np.full((e, a, h, n), np.nan, dtype=np.float64),
        "b_keep_probability": np.full((e, a, h, n), np.nan, dtype=np.float32),
        "gaussian_slots": np.full((e, h, n, d), np.nan, dtype=np.float32),
        "gate_uniform_slots": np.full((e, h, n), np.nan, dtype=np.float32),
    }


def episode_slots(base, episode, horizon):
    before = torch.random.get_rng_state().clone()
    gaussian_rng = torch.Generator(device="cpu").manual_seed(base + 80000 + episode)
    gate_rng = torch.Generator(device="cpu").manual_seed(base + 85000 + episode)
    gaussian = torch.randn((horizon, 5, 3), generator=gaussian_rng, dtype=torch.float32)
    uniforms = torch.rand((horizon, 5), generator=gate_rng, dtype=torch.float32)
    if not torch.equal(before, torch.random.get_rng_state()):
        raise RuntimeError("private B05 slot generation changed the global Torch RNG")
    return gaussian, uniforms


@torch.no_grad()
def deploy_episode(env, actor, arm, horizon, reset_seed, gaussian, gate_uniforms,
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
        "c_proxy_decisions": 0,
        "gaussian_vectors_used": 0,
        "gate_uniforms_used": 0,
    }
    for tick in range(horizon):
        check()
        phase = eligible if arm in ("C", "B") else np.zeros(5, dtype=bool)
        x = actor_features(obs, last, phase.astype(np.int64))
        mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        if mean.dtype != torch.float32 or not torch.isfinite(mean).all():
            raise FloatingPointError("nonfinite or non-FP32 B05 actor output")
        counters["actor_forward_calls"] += 1
        counters["recurrent_observations"] += 5
        step = command_step(
            actor, arm, mean, recurrent, last, phase,
            gaussian[tick], gate_uniforms[tick],
        )
        destination["means"][tick] = mean.numpy()
        destination["commands"][tick] = step["sent"]
        destination["eligibility"][tick] = step["eligible"]
        destination["branches"][tick] = step["branch"]
        destination["fresh"][tick] = step["fresh"]
        destination["c_d_keep"][tick] = step["d_keep"]
        destination["c_d_fresh"][tick] = step["d_fresh"]
        destination["b_keep_probability"][tick] = step["gate_keep_probability"]

        events = {
            "eligibility_decisions": int(step["eligible"].sum()),
            "keep_decisions": int((step["branch"] == KEEP).sum()),
            "end_decisions": int((step["branch"] == END).sum()),
            "forced_fresh_decisions": int((step["branch"] == FORCED_FRESH).sum()),
            "fresh_commands": int(step["fresh"].sum()),
            "c_proxy_decisions": int(step["eligible"].sum()) if arm == "C" else 0,
            "gaussian_vectors_used": step["gaussian_vectors_used"],
            "gate_uniforms_used": step["gate_uniforms_used"],
        }
        for name, amount in events.items():
            decisions[name] += amount
            counters[name] += amount

        counters["step_calls"] += 1
        next_obs, _scalar, terminated, truncated, info = env.step(step["sent"])
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite B05 team reward")
        destination["rewards"][tick] = reward
        destination["completed"][tick] = True
        rewards.append(reward)
        counters["team_steps"] += 1
        last = step["sent"].copy()
        eligible = step["next_eligible"].copy()
        obs = next_obs
        if (terminated or truncated) and tick + 1 < horizon:
            raise RuntimeError(f"incomplete B05 episode: boundary at {tick + 1}/{horizon}")
        check()
    if arm.startswith("G_") and destination["eligibility"].any():
        raise RuntimeError("ordinary G deployment used nonzero phase")
    total = sum(rewards)
    return dict(
        metadata,
        reset_seed=reset_seed,
        steps=horizon,
        reward_sum=total,
        J=total / horizon,
        **decisions,
    )


def final_panel(rows, expected, invocation_complete):
    values = {
        arm: {
            row["episode"]: row["J"]
            for row in rows
            if row["arm"] == arm and row["phase"] == "eval"
        }
        for arm in ARMS
    }
    full = {
        arm: sorted(items) == list(range(expected))
        and all(math.isfinite(value) for value in items.values())
        for arm, items in values.items()
    }
    panel = {
        "selected_contrast": "C_minus_G_sampled",
        "returns": {
            arm: [items[index] for index in sorted(items)]
            for arm, items in values.items()
        },
        "episode_ids": {arm: sorted(items) for arm, items in values.items()},
        "arm_means": {
            arm: statistics.mean(items.values()) if items else None
            for arm, items in values.items()
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
    panel["primary"] = panel["C_minus_G_sampled"]
    panel["complete"] = bool(invocation_complete and panel["all_panels_complete"])
    panel["reading_scope"] = (
        "Paired deployment worlds from one frozen checkpoint pair; conditional world-panel "
        "SEs are not independent training-instance precision or an equivalence verdict."
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
        "wall_scope": "runner main entry through B05 publication accounting",
        "process_cpu_seconds": time.process_time() - cpu_start,
        "process_cpu_scope": "study entry through B05 publication accounting",
        "peak_rss_kib": peak_rss_kib,
        "peak_rss_scope": "single process ru_maxrss" if peak_rss_kib is not None else "unavailable",
        "complete_process_exit_wall": None,
        "external_scope": "the native launch manifest is authoritative for actual-node and complete-process telemetry",
        "resources_unmeasured": unmeasured,
    }


def run(config, out, admission, start=None, factory=None, archive_path=None,
        archive_sha256=None):
    """Evaluate one frozen checkpoint pair; overrides exist only for the fixed test API."""
    require_config(config)
    if not config.fixture and factory is not None:
        raise ValueError("production B05 environment cannot be overridden")
    admitted_sha = admission.get("sha")
    if not isinstance(admitted_sha, str) or not admitted_sha:
        raise ValueError("B05 requires an admitted source SHA")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "config.json", asdict(config))
    _write_json(out / "admission.json", dict(admission))

    arrays = _empty_primitives(config)
    rows = []
    limits = []
    actors = {}
    snapshots = {}
    environments = {}
    source = {
        "object": OBJECT,
        "launch_sha": admitted_sha,
        "runner": _file_identity(REPO / "scripts/run_ucope_mean_agreement_deployment_b05.py"),
        "study": _file_identity(Path(__file__)),
    }
    summary = {
        "object": OBJECT,
        "notebook": NOTEBOOK,
        "notebook_section": NOTEBOOK_SECTION,
        "configuration": asdict(config),
        "master": config.master,
        "selected_masters": list(ALLOWED_MASTERS),
        "launch_sha": admitted_sha,
        "admission": dict(admission),
        "declared_execution_node": EXECUTION_NODE,
        "device": "cpu",
        "dtype": "float32",
        "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
        "quadrature": {"kind": "Gauss-Hermite", "nodes": 64, "dtype": "float64"},
        "status": "INCOMPLETE",
        "mode": "ENGINEERING_FIXTURE" if config.fixture else "FROZEN_POLICY_DEPLOYMENT",
        "limits": limits,
        "policy_definitions": {
            "C": "B actor; eligible KEEP iff D_keep <= GH64 expected D_fresh; otherwise fixed-slot sampled fresh",
            "B": "B actor; scalar learned KEEP probability compared with its fixed-slot uniform",
            "G_sampled": "G actor; phase zero and fixed-slot sampled fresh every tick",
            "G_mean": "G actor; phase zero and tanh(mu) fresh every tick",
            "phase_law": "C/B fresh makes next tick eligible; eligible KEEP forces next tick fresh; G phase is always zero",
        },
        "training_exposure": {
            "new_fits": 0,
            "new_training_episodes": 0,
            "new_optimizer_steps": 0,
            "inherited_B04_training_fits_complete_batch": 6,
            "inherited_B04_train_episodes_per_fit": 2048,
            "inherited_B04_optimizer_steps_per_fit": 4096,
            "qualification": "post-selection frozen-policy deployment, not fresh training replication or confirmation",
        },
    }
    counter_names = (
        "environment_constructors", "actor_forward_calls", "recurrent_observations",
        "explicit_resets", "step_calls",
        "team_steps", "eligibility_decisions", "keep_decisions", "end_decisions",
        "forced_fresh_decisions", "fresh_commands", "c_proxy_decisions",
        "gaussian_vectors_used", "gate_uniforms_used",
    )
    counters = {
        arm: dict.fromkeys(counter_names, 0)
        for arm in ARMS
    }
    prepared_episodes = 0

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError(
                f"B05 {config.watchdog_seconds:g}-second invocation watchdog expired; preserve partial work"
            )

    episodes_path = out / "episodes.jsonl"
    with episodes_path.open("w", encoding="utf-8") as episode_file:
        try:
            check()
            payloads, archive_identity = load_checkpoint_pair(
                config, archive_path=archive_path, archive_sha256=archive_sha256
            )
            source["checkpoint_archive"] = archive_identity
            summary["checkpoint_archive"] = archive_identity
            summary["actor_sources"] = {
                arm: {
                    "checkpoint_arm": "B" if arm in ("C", "B") else "G",
                    "member": archive_identity["members"]["B" if arm in ("C", "B") else "G"]["name"],
                    "member_sha256": archive_identity["members"]["B" if arm in ("C", "B") else "G"]["sha256"],
                }
                for arm in ARMS
            }
            actors = build_frozen_actors(config.master, payloads)
            snapshots = {arm: _snapshot(actor) for arm, actor in actors.items()}
            summary["actor_digests_before"] = {
                arm: actor_digest(actor) for arm, actor in actors.items()
            }
            if factory is None:
                if config.fixture:
                    from ..uav_motion_prefix_b01.environment import SyntheticAdapter
                    factory = lambda seed: SyntheticAdapter(seed, config.horizon)
                else:
                    from ..uav_motion_prefix_b01.environment import make_real
                    factory = make_real
            base = 100000 * config.master
            for arm in ARMS:
                check()
                environments[arm] = factory(base + 30000)
                counters[arm]["environment_constructors"] += 1
            for episode in range(config.eval_episodes):
                check()
                gaussian, uniforms = episode_slots(base, episode, config.horizon)
                arrays["gaussian_slots"][episode] = gaussian.numpy()
                arrays["gate_uniform_slots"][episode] = uniforms.numpy()
                prepared_episodes += 1
                for arm_index, arm in enumerate(ARMS):
                    destination = {
                        key: arrays[key][episode, arm_index]
                        for key in (
                            "completed", "rewards", "commands", "means", "eligibility",
                            "branches", "fresh", "c_d_keep", "c_d_fresh",
                            "b_keep_probability",
                        )
                    }
                    row = deploy_episode(
                        environments[arm], actors[arm], arm, config.horizon,
                        base + 30000 + episode, gaussian, uniforms,
                        {"master": config.master, "arm": arm, "phase": "eval", "episode": episode},
                        destination, check, counters[arm],
                    )
                    rows.append(row)
                    episode_file.write(json.dumps(row, allow_nan=False) + "\n")
                    episode_file.flush()
            summary["status"] = "COMPLETE"
        except Exception as error:
            traceback.print_exc()
            summary["error"] = {"type": type(error).__name__, "message": str(error)}
        finally:
            close_errors = []
            for arm, env in environments.items():
                try:
                    if hasattr(env, "close"):
                        env.close()
                except Exception as error:
                    close_errors.append(f"{arm}: {type(error).__name__}: {error}")
            if close_errors:
                limits.extend(close_errors)
                if summary["status"] == "COMPLETE":
                    summary["status"] = "INCOMPLETE"
                    summary["error"] = {
                        "type": "EnvironmentCloseError",
                        "message": "; ".join(close_errors),
                    }

    integrity = {}
    for arm, actor in actors.items():
        exact, movement = _movement(snapshots[arm], actor)
        integrity[arm] = {
            "before_sha256": summary["actor_digests_before"][arm],
            "after_sha256": actor_digest(actor),
            "exactly_unchanged": exact,
            "parameter_l2_movement": movement,
            "optimizer_steps": 0,
        }
    summary["actor_integrity"] = integrity
    if integrity and not all(item["exactly_unchanged"] for item in integrity.values()):
        summary["status"] = "INCOMPLETE"
        summary["error"] = {
            "type": "ActorMutationError",
            "message": "a frozen actor changed during evaluation",
        }

    invocation_complete = summary["status"] == "COMPLETE"
    summary["panel"] = final_panel(rows, config.eval_episodes, invocation_complete)
    per_arm_counts = {
        arm: {
            **counters[arm],
            "eval_episodes": sum(row["arm"] == arm for row in rows),
            "eval_team_steps": counters[arm]["team_steps"],
            "optimizer_steps": 0,
        }
        for arm in ARMS
    }
    summary["counts"] = {
        "new_fits": 0,
        "train_episodes": 0,
        "train_team_steps": 0,
        "optimizer_steps": 0,
        "eval_episodes": len(rows),
        "eval_team_steps": int(arrays["completed"].sum()),
        "team_steps": int(arrays["completed"].sum()),
        "prepared_world_slot_episodes": prepared_episodes,
        "gaussian_scalar_slots_prepared": prepared_episodes * config.horizon * 5 * 3,
        "gate_uniform_slots_prepared": prepared_episodes * config.horizon * 5,
        "gaussian_scalar_draws_used": 3 * sum(
            item["gaussian_vectors_used"] for item in counters.values()
        ),
        "gate_uniform_draws_used": sum(item["gate_uniforms_used"] for item in counters.values()),
        "per_arm": per_arm_counts,
        "expected_complete_invocation_eval_episodes": len(ARMS) * config.eval_episodes,
        "expected_complete_invocation_team_steps": len(ARMS) * config.eval_episodes * config.horizon,
        "expected_complete_three_master_eval_episodes": 768,
        "expected_complete_three_master_team_steps": 196608,
    }
    summary["rng"] = {
        "base": 100000 * config.master,
        "world_start": 100000 * config.master + 30000,
        "gaussian_slot_seed": "base+80000+episode",
        "gate_uniform_slot_seed": "base+85000+episode",
        "slot_index": "primitive tick, UAV, action coordinate",
        "branch_invariant": True,
    }
    summary["telemetry"] = _telemetry(start, cpu_start)
    summary["resource_note"] = (
        "Runner telemetry has explicit scopes; missing complete-process telemetry limits only resource claims."
    )
    unverified_archive = {
        "path": str(archive_spec(config, archive_path, archive_sha256)[0]),
        "expected_sha256": archive_spec(config, archive_path, archive_sha256)[1],
        "verified": False,
    }
    source.setdefault("checkpoint_archive", unverified_archive)
    summary.setdefault("checkpoint_archive", unverified_archive)
    _write_json(out / "source.json", source)
    np.savez_compressed(out / "primitives.npz", **arrays)
    summary["artifacts"] = {
        name: _file_identity(out / name)
        for name in ("config.json", "source.json", "admission.json", "episodes.jsonl", "primitives.npz")
    }
    _write_json(out / "summary.json", summary)
    return summary
