"""Three closed-loop send laws for one strictly identified, trained RR actor.

The evaluator never calls a collector, optimizer, or training-storage routine.
Each trace row is fsynced before the next native step; a failed episode keeps its
``.partial`` trace and the summary retains only the completed comparison frontier.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import statistics
import sys
import tarfile
import time
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel, COST, N, payloads
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm, sample_actions
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, make_real, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator


ROOT = Path(__file__).resolve().parents[4]
OBJECT_ID = "c2_rr_fast_none_b01"
TAG = "c2_rr_fast_none_b01_s9302"
ARMS = ("RR", "FAST_ONLY", "NONE")
MASTER = 9302
ARCHIVE = ROOT / "docs/research/candidates/contention_aware_decentralized_communication/evidence/cadc_b01_9302/CADC_RESULTS.tar.gz"
ARCHIVE_SHA256 = "f3804156ab239fa177b5773743e2508bd7f3c6453f7c52c005185ce1f529c41a"
MEMBER = "RR/final.pt"
MEMBER_SHA256 = "c1a59c160750151e9ba65eca0006b15cc6fdbd7290c2ae90eaf8dc999471e134"
SOURCE_SHA256 = {
    "experiments/candidates/contention_aware_decentralized_communication/cadc_b01/channel.py": "f28cdd2e452646169653daabdad963c1a0cdf00f9388454e7de7a0710145bf91",
    "experiments/candidates/contention_aware_decentralized_communication/cadc_b01/model.py": "46ed96aeeb6c13640bd4105d283ebf3e12f9660844ee9456b65d60eb0d143633",
    "experiments/candidates/contention_aware_decentralized_communication/cadc_b01/learner.py": "66978ca5d4a8f4b3fd15a6c4e6dc6a7107a8071386c2e507b7434aeb17a22589",
    "experiments/candidates/contention_aware_decentralized_communication/cadc_b01/study.py": "a0b3d568ad44d6e293e4fb9da96e9a48fc740d73656d13e8e5755fe592253b4e",
    "experiments/candidates/ucope/uav_motion_prefix_b01/environment.py": "fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6",
    "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py": "e324640251d0d025549705ff7541b765e7b96733f422c48ee9c2f5bd07709614",
    "envs/pettingzoo/uav_env.py": "f50d74cdba92d5ef976c8ba53d2697fc72742683fcb746b404b8c8807f463803",
    "envs/pettingzoo/env_adapter.py": "8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40",
}


@dataclass(frozen=True)
class Spec:
    episodes: int = 32
    horizon: int = 256
    reset_base: int = 930_210_000
    channel_base: int = 930_220_000
    motion_base: int = 930_230_000
    send_base: int = 930_240_000
    production: bool = True


PRODUCTION = Spec()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_identity(path: Path, relative: str | None = None) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
            size += len(part)
    return {"path": relative or str(path), "bytes": size, "sha256": digest.hexdigest()}


def _json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, allow_nan=False, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _array(value: Any) -> list[Any]:
    array = np.asarray(value)
    if not np.isfinite(array).all():
        raise FloatingPointError("nonfinite trace array")
    return array.tolist()


def _tensor_digest(tensor: torch.Tensor) -> str:
    return sha256(tensor.detach().contiguous().cpu().numpy().tobytes())


def _model_digest(actor: torch.nn.Module, critic: torch.nn.Module) -> dict[str, str]:
    def digest(module: torch.nn.Module) -> str:
        h = hashlib.sha256()
        for key, value in module.state_dict().items():
            h.update(key.encode())
            h.update(value.detach().contiguous().cpu().numpy().tobytes())
        return h.hexdigest()
    return {"actor": digest(actor), "critic": digest(critic)}


def _source_identity(production: bool) -> dict[str, str]:
    current = {path: file_identity(ROOT / path)["sha256"] for path in SOURCE_SHA256}
    if production and current != SOURCE_SHA256:
        raise ValueError("frozen CADC/UCOPE/native source identity differs")
    return current


def load_asset(archive: Path = ARCHIVE, *, archive_sha: str = ARCHIVE_SHA256,
               member_sha: str = MEMBER_SHA256) -> tuple[dict[str, Any], dict[str, Any]]:
    archive = Path(archive)
    identity = file_identity(archive)
    if identity["sha256"] != archive_sha:
        raise ValueError("frozen RR archive SHA256 mismatch")
    with tarfile.open(archive, "r:gz") as bundle:
        members = [m for m in bundle.getmembers() if m.name == MEMBER]
        if len(members) != 1 or not members[0].isfile():
            raise ValueError("frozen RR member missing or ambiguous")
        stream = bundle.extractfile(members[0])
        if stream is None:
            raise ValueError("frozen RR member cannot be extracted")
        data = stream.read()
    if sha256(data) != member_sha:
        raise ValueError("frozen RR member SHA256 mismatch")
    state = torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or set(state) != {"actor", "critic", "arm", "master", "input_size", "critic_size"}:
        raise ValueError("frozen RR checkpoint fields mismatch")
    if (state["arm"], state["master"], state["input_size"], state["critic_size"]) != ("RR", MASTER, 171, 451):
        raise ValueError("frozen RR checkpoint contract mismatch")
    template_actor, template_critic = build_arm(MASTER, "RR")
    for name, template in (("actor", template_actor), ("critic", template_critic)):
        values = state[name]
        expected = template.state_dict()
        if not isinstance(values, dict) or set(values) != set(expected):
            raise ValueError(f"frozen RR {name} tensor names mismatch")
        for key, value in values.items():
            if (not isinstance(value, torch.Tensor) or value.dtype != torch.float32 or
                    value.shape != expected[key].shape or not torch.isfinite(value).all()):
                raise ValueError(f"frozen RR {name}.{key} tensor contract mismatch")
    details = {"archive": identity | {"path": str(archive.relative_to(ROOT)) if archive.is_relative_to(ROOT) else str(archive)},
               "member": {"path": MEMBER, "bytes": len(data), "sha256": sha256(data)},
               "arm": "RR", "master": MASTER, "input_size": 171, "critic_size": 451,
               "actor_parameters": sum(v.numel() for v in state["actor"].values()),
               "critic_parameters": sum(v.numel() for v in state["critic"].values())}
    return state, details


def _fresh_models(state: dict[str, Any]) -> tuple[torch.nn.Module, torch.nn.Module]:
    actor, critic = build_arm(MASTER, "RR")
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.eval()
    critic.eval()
    return actor, critic


def send_request(rule: str, channel: Channel) -> np.ndarray:
    if rule not in ARMS:
        raise ValueError("unknown fixed send law")
    requests = np.zeros(N, dtype=bool)
    owner = channel.t % N
    if rule != "NONE" and not channel.pending[owner] and (rule == "RR" or channel.good):
        requests[owner] = True
    return requests


def _service(connections: np.ndarray, sinr: np.ndarray) -> tuple[int, float, float]:
    connected = np.asarray(connections, dtype=bool)
    values = np.asarray(sinr, dtype=np.float64)
    if connected.shape != (5, 50) or values.shape != (5, 50) or not np.isfinite(values).all():
        raise ValueError("native service arrays have wrong shape or nonfinite SINR")
    served = int(connected.sum())
    coverage = served / 50
    quality = float(np.clip((values[connected] - 3) / 30, 0, 1).sum() / max(served, 1))
    return served, coverage, quality


def _gaps(delivery_ticks: list[list[list[int]]], horizon: int) -> dict[str, Any]:
    rows = []
    for receiver in range(N):
        for sender in range(N):
            if sender == receiver:
                continue
            ticks = delivery_ticks[receiver][sender]
            boundaries = [0] + ticks + [horizon]
            rows.append({"receiver": receiver, "sender": sender,
                         "initial_censored_ticks": ticks[0] if ticks else horizon,
                         "between_updates_ticks": [b - a for a, b in zip(ticks, ticks[1:])],
                         "terminal_censored_ticks": horizon - ticks[-1] if ticks else horizon,
                         "all_boundary_gaps": [b - a for a, b in zip(boundaries, boundaries[1:])]})
    return {"per_receiver_sender": rows,
            "initial_censored_ticks": [r["initial_censored_ticks"] for r in rows],
            "between_updates_ticks": [gap for r in rows for gap in r["between_updates_ticks"]],
            "terminal_censored_ticks": [r["terminal_censored_ticks"] for r in rows]}


def _distribution(values: list[int]) -> dict[str, Any]:
    return {"count": len(values), "mean": statistics.mean(values) if values else None,
            "min": min(values) if values else None, "max": max(values) if values else None}


@torch.no_grad()
def _episode_with_env(rule: str, index: int, spec: Spec, actor: torch.nn.Module,
                      env: Any, raw_dir: Path,
                      progress: Callable[[str, int, dict[str, Any] | None], None]) -> dict[str, Any]:
    reset_seed = spec.reset_base + index
    channel_seed = spec.channel_base + index
    motion_seed = spec.motion_base + index
    send_seed = spec.send_base + index  # retained unused RR send stream
    raw, info = env.reset(seed=reset_seed)
    state = np.asarray(info["state"], dtype=np.float32)
    raw = np.asarray(raw, dtype=np.float32)
    if raw.shape != (5, 104) or state.shape != (116,):
        raise ValueError("native initial observation/state shape mismatch")
    native = env.env
    scene = {}
    for name, shape in (("uav_positions", (5, 3)), ("user_positions", (50, 2)),
                        ("ground_bs_positions", (1, 3)), ("connections", (5, 50)),
                        ("sinr_matrix", (5, 50))):
        values = np.ascontiguousarray(np.asarray(getattr(native, name)).copy())
        if values.shape != shape or not np.isfinite(values).all():
            raise ValueError(f"native initial {name} shape/finiteness mismatch")
        if spec.production and values.dtype != (np.bool_ if name == "connections" else np.float64):
            raise ValueError(f"native initial {name} dtype mismatch")
        scene[name] = {"dtype": values.dtype.str, "shape": list(values.shape),
                       "sha256": sha256(values.tobytes()), "values": values.tolist()}
    if int(native.current_step) != 0:
        raise ValueError("native reset did not start at tick zero")
    initial = {"raw": _array(raw), "state": _array(state),
               "state_sha256": sha256(state.tobytes()), "raw_sha256": sha256(raw.tobytes()),
               "native_scene": scene, "native_current_step": 0}
    channel = Channel(channel_seed)
    motion_rng = generator(motion_seed)
    send_rng = generator(send_seed)
    initial_send_rng_sha256 = _tensor_digest(send_rng.get_state())
    last = np.zeros((N, 3), dtype=np.float32)
    remaining = np.zeros(N, dtype=np.int64)
    hidden = torch.zeros(1, N, 64)
    trace_path = raw_dir / f"{rule.lower()}_episode_{index:02d}.jsonl"
    partial_path = trace_path.with_suffix(".jsonl.partial")
    physical_sum = fee_sum = coverage_sum = quality_sum = served_sum = height_sum = 0.0
    valid_total = missing_total = age_total = 0
    delays: list[int] = []
    delivery_ticks: list[list[list[int]]] = [[[] for _ in range(N)] for _ in range(N)]
    channel_states: list[bool] = []
    tick_count = 0
    with partial_path.open("w", encoding="utf-8") as stream:
        header = {"type": "initial", "rule": rule, "episode": index, "reset_seed": reset_seed,
                  "channel_seed": channel_seed, "motion_seed": motion_seed,
                  "send_seed_unused": send_seed, "initial": initial,
                  "initial_channel_good": channel.good,
                  "initial_motion_rng_sha256": _tensor_digest(motion_rng.get_state()),
                  "initial_unused_send_rng_sha256": initial_send_rng_sha256,
                  "initial_hidden": _array(hidden.numpy()), "initial_last": _array(last),
                  "initial_remaining": _array(remaining)}
        stream.write(json.dumps(header, allow_nan=False, separators=(",", ":")) + "\n")
        stream.flush(); os.fsync(stream.fileno())
        progress("header", 0, {"path": str(partial_path.relative_to(raw_dir.parent)),
                               "bytes": os.fstat(stream.fileno()).st_size})
        try:
            for t in range(spec.horizon):
                if channel.t != t:
                    raise AssertionError("channel tick drift")
                before_inflight = [(sender, sent, due, _array(payload))
                                   for sender, sent, due, payload in channel.inflight]
                due_packets = [dict(sender=sender, sent=sent, due=due, delivered_at=t,
                                    delay=t - sent, payload=payload)
                               for sender, sent, due, payload in before_inflight if due <= t]
                channel.begin_tick()
                progress("delivery", t, {"delivered": len(due_packets)})
                for packet in due_packets:
                    delays.append(packet["delay"])
                    for receiver in range(N):
                        if receiver != packet["sender"]:
                            delivery_ticks[receiver][packet["sender"]].append(t)
                records = channel.records.copy()
                valid = records[:, :, 7] > 0
                peer = ~np.eye(N, dtype=bool)
                valid_count = int((valid & peer).sum())
                missing_count = int((~valid & peer).sum())
                valid_total += valid_count
                missing_total += missing_count
                age_total += int(np.rint((records[:, :, 9][valid & peer] * 256)).sum())
                channel_states.append(bool(channel.good))
                extras = channel.features()
                x = np.concatenate((actor_features(raw, last, remaining), extras), axis=1)
                if x.shape != (N, 171):
                    raise AssertionError("actor171 input contract changed")
                hidden_before = hidden.clone()
                mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
                progress("actor", t, None)
                mean, recurrent = mean[0], recurrent[0]
                eligible = torch.from_numpy(~channel.pending.copy())
                # The unchanged CADC primitive consumes the torch motion generator in
                # physical-ID/coordinate order.  The send generator is never consumed.
                u, original_rr = sample_actions(actor, mean, recurrent, eligible, t,
                                                motion_rng, send_rng)
                progress("motion", t, None)
                requested = send_request(rule, channel)
                if rule == "RR" and not np.array_equal(requested, original_rr.numpy()):
                    raise AssertionError("RR request differs from original CADC path")
                command = u.tanh().numpy()
                pending_at_action = channel.pending.copy()
                good_at_action = bool(channel.good)
                accepted_before, collided_before = channel.accepted, channel.collisions
                charge = channel.resolve(requested, raw)
                progress("resolve", t, {"attempted": int(requested.sum()),
                                        "accepted": channel.accepted - accepted_before,
                                        "collided": channel.collisions - collided_before})
                raw_next, adapter_reward, terminated, truncated, info_next = env.step(command)
                progress("native", t, None)
                raw_next = np.asarray(raw_next, dtype=np.float32)
                next_state = np.asarray(info_next["next_state"], dtype=np.float32)
                native_post_positions = np.asarray(env.env.uav_positions, dtype=np.float64).copy()
                native_reward = team_reward(info_next)
                global_info = info_next["infos_dict"]["uav_0"]["global"]
                connections = np.asarray(global_info["connections"], dtype=bool)
                sinr = np.asarray(global_info["sinr_matrix"], dtype=np.float64)
                served, coverage, quality = _service(connections, sinr)
                if not math.isclose(native_reward, .7 * coverage + .3 * quality, abs_tol=1e-8):
                    raise AssertionError("native team reward/service decomposition differs")
                if not math.isclose(charge, COST * int(requested.sum()), abs_tol=1e-12):
                    raise AssertionError("attempt fee differs")
                if not all(np.isfinite(v).all() for v in (raw_next, next_state,
                                                           native_post_positions, command, u.numpy())):
                    raise FloatingPointError("nonfinite physical or actor output")
                if (terminated or truncated) and t + 1 < spec.horizon:
                    raise RuntimeError(f"unexpected native terminal at tick {t}: {terminated}/{truncated}")
                if spec.production and t + 1 == spec.horizon and not (terminated or truncated):
                    raise RuntimeError("native H256 endpoint did not terminate")
                row = {
                    "type": "tick", "t": t, "pre_raw": _array(raw), "pre_state": _array(state),
                    "actor_input": _array(x), "hidden_before_sha256": _tensor_digest(hidden_before),
                    "hidden_after_sha256": _tensor_digest(hidden), "actor_mean": _array(mean.numpy()),
                    "raw_motion": _array(u.numpy()), "executed_motion": _array(command),
                    "motion_rng_after_sha256": _tensor_digest(motion_rng.get_state()),
                    "channel_good": good_at_action, "eligible_owner": t % N,
                    "pending_at_action": _array(pending_at_action.astype(np.int8)),
                    "cache_at_action": _array(records), "valid_peer_entries": valid_count,
                    "missing_peer_entries": missing_count, "deliveries_before_action": due_packets,
                    "requested": _array(requested.astype(np.int8)),
                    "pre_motion_payloads": _array(payloads(raw)),
                    "inflight_before_action": before_inflight,
                    "inflight_after_resolve": [(sender, sent, due, _array(payload))
                                               for sender, sent, due, payload in channel.inflight],
                    "fee": charge, "post_raw": _array(raw_next), "post_state": _array(next_state),
                    "post_native_uav_positions": _array(native_post_positions),
                    "native_rewards": {name: float(value) for name, value in info_next["rewards_dict"].items()},
                    "adapter_mean_reward_unused": float(adapter_reward),
                    "connections": _array(connections.astype(np.int8)), "sinr_db": _array(sinr),
                    "served_users": served, "coverage": coverage, "quality": quality,
                    "J_physical": native_reward, "J_net": native_reward - charge,
                    "height_mean": float(next_state[:15].reshape(N, 3)[:, 2].mean()),
                    "terminated": bool(terminated), "truncated": bool(truncated),
                }
                stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
                stream.flush(); os.fsync(stream.fileno())
                tick_count += 1
                progress("traced", tick_count, {"path": str(partial_path.relative_to(raw_dir.parent)),
                                                "bytes": os.fstat(stream.fileno()).st_size})
                physical_sum += native_reward
                fee_sum += charge
                coverage_sum += coverage
                quality_sum += quality
                served_sum += served
                height_sum += row["height_mean"]
                last[:] = command
                raw, state = raw_next, next_state
                channel.advance()
            censored = [dict(sender=sender, sent=sent, due=due, censored_at=spec.horizon,
                             payload=_array(payload)) for sender, sent, due, payload in channel.inflight]
            if channel.accepted != channel.delivered + len(censored):
                raise AssertionError("accepted/delivered/censored accounting differs")
            if channel.attempts != channel.accepted + channel.collisions:
                raise AssertionError("attempt/collision accounting differs")
            progress("censor", spec.horizon, {"censored": len(censored)})
            gaps = _gaps(delivery_ticks, spec.horizon)
            terminal_reason = "native_horizon" if spec.production else "technical_horizon"
            terminal = {"type": "terminal", "reason": terminal_reason,
                        "censored_packets": censored, "channel_t": channel.t,
                        "channel_good_after_horizon": channel.good,
                        "final_motion_rng_sha256": _tensor_digest(motion_rng.get_state()),
                        "unused_send_rng_unchanged": _tensor_digest(send_rng.get_state()) == initial_send_rng_sha256,
                        "packet_delays": delays,
                        "receive_update_gaps": gaps}
            if not terminal["unused_send_rng_unchanged"]:
                raise AssertionError("RR send generator was consumed")
            stream.write(json.dumps(terminal, allow_nan=False, separators=(",", ":")) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        except BaseException:
            # The partial trace is the actual durable frontier, even if the summary
            # cannot be updated by a hard process exit.
            raise
    os.replace(partial_path, trace_path)
    directory = os.open(raw_dir, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    row = {"rule": rule, "episode": index, "reset_seed": reset_seed,
           "channel_seed": channel_seed, "motion_seed": motion_seed,
           "send_seed_unused": send_seed, "steps": spec.horizon,
           "initial_state_sha256": initial["state_sha256"],
           "initial_raw_sha256": initial["raw_sha256"],
           "initial_native_scene_sha256": {key: value["sha256"] for key, value in scene.items()},
           "channel_good_sequence_sha256": sha256(np.asarray(channel_states, dtype=np.uint8).tobytes()),
           "channel_good_ticks": sum(channel_states),
           "J_physical": physical_sum / spec.horizon,
           "J_net": (physical_sum - fee_sum) / spec.horizon,
           "fee_per_tick": fee_sum / spec.horizon,
           "served_users_per_tick": served_sum / spec.horizon,
           "coverage": coverage_sum / spec.horizon, "quality": quality_sum / spec.horizon,
           "mean_height": height_sum / spec.horizon,
           "attempted": channel.attempts, "accepted": channel.accepted,
           "delivered": channel.delivered, "collided": channel.collisions,
           "censored": len(censored), "pending_at_end": int(channel.pending.sum()),
           "packet_delay_ticks": _distribution(delays),
           "action_time_cache": {"valid_peer_entries": valid_total,
                                 "missing_peer_entries": missing_total,
                                 "valid_only_mean_age_ticks": age_total / valid_total if valid_total else None},
           "receive_update_gaps": {
               "initial_censored_ticks": _distribution(gaps["initial_censored_ticks"]),
               "between_updates_ticks": _distribution(gaps["between_updates_ticks"]),
               "terminal_censored_ticks": _distribution(gaps["terminal_censored_ticks"])},
           "trace": file_identity(trace_path, str(trace_path.relative_to(raw_dir.parent))),
           "terminal_reason": terminal_reason}
    return row


def episode(rule: str, index: int, spec: Spec, actor: torch.nn.Module, critic: torch.nn.Module,
            factory: Callable[[int], Any], raw_dir: Path,
            progress: Callable[[str, int, dict[str, Any] | None], None]) -> dict[str, Any]:
    env = factory(spec.reset_base + index)
    try:
        return _episode_with_env(rule, index, spec, actor, env, raw_dir, progress)
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()


def _pairwise(rows: dict[str, list[dict[str, Any]]], spec: Spec) -> dict[str, Any]:
    for rule in ARMS:
        if len(rows[rule]) != spec.episodes or [r["episode"] for r in rows[rule]] != list(range(spec.episodes)):
            raise ValueError("incomplete panel cannot form paired reading")
    for index in range(spec.episodes):
        identities = {(rows[rule][index]["initial_state_sha256"],
                       rows[rule][index]["initial_raw_sha256"],
                       tuple(sorted(rows[rule][index]["initial_native_scene_sha256"].items())),
                       rows[rule][index]["channel_good_sequence_sha256"]) for rule in ARMS}
        if len(identities) != 1:
            raise ValueError("physical/channel exogenous identity differs across rules")
    contrasts = {}
    for left, right in (("FAST_ONLY", "RR"), ("FAST_ONLY", "NONE"), ("RR", "NONE")):
        metrics = {}
        for key in ("J_net", "J_physical", "served_users_per_tick", "coverage", "quality", "fee_per_tick", "mean_height"):
            values = [rows[left][i][key] - rows[right][i][key] for i in range(spec.episodes)]
            if not all(math.isfinite(x) for x in values):
                raise FloatingPointError("nonfinite paired contrast")
            metrics[key] = {"per_world": values, "mean": statistics.mean(values),
                            "positive": sum(x > 0 for x in values),
                            "adverse": sum(x < 0 for x in values),
                            "zero": sum(x == 0 for x in values),
                            "adverse_worlds": [i for i, x in enumerate(values) if x < 0]}
        contrasts[f"{left}_minus_{right}"] = metrics
    return contrasts


def run(output: Path, launch_sha: str, admission: dict[str, Any], *, spec: Spec = PRODUCTION,
        factory: Callable[[int], Any] = make_real, asset: Path = ARCHIVE,
        archive_sha: str = ARCHIVE_SHA256, member_sha: str = MEMBER_SHA256) -> dict[str, Any]:
    output = Path(output)
    if spec.production and spec != PRODUCTION:
        raise ValueError("production C2 spec differs from prospectively fixed contract")
    if spec.production and (not isinstance(launch_sha, str) or
                            re.fullmatch(r"[0-9a-f]{40}", launch_sha) is None or
                            admission.get("sha") != launch_sha):
        raise ValueError("production C2 source SHA/admission mismatch")
    if spec.episodes <= 0 or spec.horizon <= 0:
        raise ValueError("empty technical C2 spec")
    if spec.production and output.name != TAG:
        raise ValueError("production C2 output tag mismatch")
    if output.exists() and any(output.iterdir()):
        permitted = {"launch-manifest.json", "launch-status.json", "admission-preflight.json", "stdout.log", "stderr.log"}
        if any(p.name not in permitted for p in output.iterdir()):
            raise FileExistsError("C2 scientific output already exists")
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "raw"
    raw_dir.mkdir(exist_ok=False)
    started = time.perf_counter()
    before_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rows: dict[str, list[dict[str, Any]]] = {rule: [] for rule in ARMS}
    counts = {"fits": 0, "optimizer_steps": 0, "training_storage_calls": 0,
              "complete_episodes": 0, "completed_team_steps": 0,
              "native_steps_returned": 0, "durably_traced_ticks": 0,
              "actor_calls": 0, "motion_decisions": 0,
              "attempted": 0, "accepted": 0, "delivered": 0,
              "collided": 0, "censored": 0}
    summary: dict[str, Any] = {"object_id": OBJECT_ID, "status": "incomplete",
                               "launch_sha": launch_sha, "config": None,
                               "checkpoint": None, "rows": rows, "counts": counts,
                               "active": None, "pairwise": None,
                               "failure": None,
                               "counter_semantics": {
                                   "native_steps_returned": "env.step returned; a thrown step has unknown internal effects",
                                   "actor_calls": "batched actor.forward returned",
                                   "motion_decisions": "sampled five UAV motions from the source primitive",
                                   "durably_traced_ticks": "tick row flushed and fsynced",
                                   "packet_counts": "known event-level deliveries/resolutions, including caught incomplete episodes; completed per-world packet totals are in rows",
                                   "hard_exit": "summary may stop at the last completed episode; inspect raw/*.jsonl.partial for a later durable tick frontier"}}

    def publish() -> None:
        summary["wall_seconds"] = time.perf_counter() - started
        summary["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        summary["process_peak_rss_delta_from_start_kib"] = max(0, summary["process_peak_rss_kib"] - before_rss_kib)
        _json_atomic(output / "summary.json", summary)

    publish()
    signal_before = signal.getsignal(signal.SIGTERM)
    def interrupt(_signum, _frame):
        raise InterruptedError("C2 evaluation received SIGTERM")
    signal.signal(signal.SIGTERM, interrupt)
    try:
        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            if torch.get_num_interop_threads() != 1:
                raise
        source_hashes = _source_identity(False)
        config = {"object_id": OBJECT_ID, "tag": TAG if spec.production else output.name,
                  "launch_sha": launch_sha, "admission": admission, "spec": asdict(spec),
                  "rules": ARMS, "dtype": "torch.float32", "device": "cpu",
                  "runtime": {"python_executable": sys.executable, "python_version": sys.version,
                              "numpy_version": np.__version__, "torch_version": torch.__version__,
                              "torch_threads": torch.get_num_threads(),
                              "torch_interop_threads": torch.get_num_interop_threads(),
                              "blas_thread_environment": {name: os.environ.get(name) for name in
                                  ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                   "NUMEXPR_NUM_THREADS")}},
                  "reward": "sum native per-agent rewards = .7 coverage + .3 quality",
                  "fee": ".001 per eligible attempted packet", "source_hashes": source_hashes}
        _json_atomic(output / "config.json", config)
        summary["config"] = "config.json"
        publish()
        if spec.production and (config["runtime"]["torch_threads"] != 1 or
                                config["runtime"]["torch_interop_threads"] != 1 or
                                any(value != "1" for value in config["runtime"]["blas_thread_environment"].values())):
            raise ValueError("production C2 thread contract differs")
        if spec.production and source_hashes != SOURCE_SHA256:
            raise ValueError("frozen CADC/UCOPE/native source identity differs")
        checkpoint, identity = load_asset(asset, archive_sha=archive_sha, member_sha=member_sha)
        summary["checkpoint"] = identity
        publish()
        for rule in ARMS:
            actor, critic = _fresh_models(checkpoint)
            initial_digest = _model_digest(actor, critic)
            for index in range(spec.episodes):
                summary["active"] = {"rule": rule, "episode": index,
                                     "native_steps_returned": 0, "durably_traced_ticks": 0,
                                     "actor_calls": 0, "motion_decisions": 0,
                                     "attempted": 0, "accepted": 0, "delivered": 0,
                                     "collided": 0, "censored": 0,
                                     "partial_trace": {"path": f"raw/{rule.lower()}_episode_{index:02d}.jsonl.partial",
                                                       "bytes": 0}}
                publish()
                def progress(event: str, ticks: int, locator: dict[str, Any] | None) -> None:
                    active = summary["active"]
                    if event == "actor":
                        counts["actor_calls"] += 1
                        active["actor_calls"] += 1
                    elif event == "motion":
                        counts["motion_decisions"] += N
                        active["motion_decisions"] += N
                    elif event == "native":
                        counts["native_steps_returned"] += 1
                        active["native_steps_returned"] += 1
                    elif event in ("header", "traced"):
                        if event == "traced":
                            counts["durably_traced_ticks"] += 1
                            active["durably_traced_ticks"] = ticks
                        active["partial_trace"] = locator
                    elif event in ("delivery", "resolve", "censor"):
                        assert locator is not None
                        for key, delta in locator.items():
                            counts[key] += delta
                            active[key] += delta
                    else:
                        raise AssertionError("unknown progress event")
                    # On caught failure these in-memory counters are published.
                    # A hard exit leaves the prior summary plus the fsynced trace.
                row = episode(rule, index, spec, actor, critic, factory, raw_dir, progress)
                rows[rule].append(row)
                counts["complete_episodes"] += 1
                counts["completed_team_steps"] += row["steps"]
                if any(summary["active"][key] != row[key]
                       for key in ("attempted", "accepted", "delivered", "collided", "censored")):
                    raise AssertionError("streamed packet counts differ from completed episode")
                summary["active"] = None
                summary.setdefault("model_checks", []).append({"rule": rule, "episode": index,
                                                                 "before": initial_digest,
                                                                 "after": _model_digest(actor, critic),
                                                                 "unchanged": initial_digest == _model_digest(actor, critic)})
                if not summary["model_checks"][-1]["unchanged"]:
                    raise AssertionError("fixed model changed during evaluation")
                publish()
        expected = len(ARMS) * spec.episodes * spec.horizon
        if counts["complete_episodes"] != len(ARMS) * spec.episodes or counts["completed_team_steps"] != expected:
            raise AssertionError("complete episode/step count differs")
        if counts["native_steps_returned"] != expected or counts["durably_traced_ticks"] != expected:
            raise AssertionError("native/durable step count differs")
        pairwise = _pairwise(rows, spec)
        rule_summaries = {
            rule: {
                "mean": {key: statistics.mean(row[key] for row in rows[rule])
                         for key in ("J_net", "J_physical", "served_users_per_tick",
                                     "coverage", "quality", "fee_per_tick", "mean_height")},
                "packets": {key: sum(row[key] for row in rows[rule])
                            for key in ("attempted", "accepted", "delivered", "collided", "censored")},
            }
            for rule in ARMS
        }
        summary["pairwise"] = pairwise
        summary["rule_summaries"] = rule_summaries
        summary["status"] = "complete"
        summary["active"] = None
        raw_identities = [r["trace"] for rule in ARMS for r in rows[rule]]
        summary["raw_bytes"] = sum(r["bytes"] for r in raw_identities)
        summary["raw_trace_count"] = len(raw_identities)
        publish()
    except BaseException as error:
        summary["status"] = "failed"
        summary["failure"] = {"type": type(error).__name__, "message": str(error)}
        publish()
        raise
    finally:
        signal.signal(signal.SIGTERM, signal_before)
    return summary
