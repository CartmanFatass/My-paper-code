"""Frozen-policy release priority: no training and no change to the C01 host."""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np
import torch

from ..c01.host import APPROACH, DONE, SHARED, CrossingHost, Worlds, gate, project, simple_requests
from ..c01.learner import build_scheduler, flat_parameters
from ..c01.study import mean_reading, write_json


@dataclass(frozen=True)
class Checkpoint:
    seed: int
    path: str
    sha256: str
    source_sha: str


CHECKPOINTS = (
    Checkpoint(73141, "runs/skill_information_refresh/c01_s73141_20260920/final.pt",
        "461db24607e23cc3c92c9e636850c61e1a9e29b703ed3b9a09d4e4a4f6b5b10e",
        "037d948f7743b282cce1b78d4d4699bc784cfe1c"),
    Checkpoint(73142, "runs/skill_information_refresh/c02_s73142_20260920/final.pt",
        "2d7d1a3d6db1f16b0f6fe4ad1041ea0dfc3afce0746748adf7fe936ae8ce43f7",
        "118d8bc391c0e9acafc054ed16a8899ccd795de9"),
    Checkpoint(73143, "runs/skill_information_refresh/c02_s73143_20260920/final.pt",
        "522011e9b8dc0ce6e4d16f91b856e3278dda6bf3e575bddcb97bd16965048e55",
        "118d8bc391c0e9acafc054ed16a8899ccd795de9"),
)


@dataclass(frozen=True)
class Config:
    seed: int = 73150
    horizon: int = 96
    selection_episodes: int = 256
    final_episodes: int = 256
    batch: int = 32

    def __post_init__(self):
        if self.seed < 0 or self.horizon <= 0 or self.horizon % 48:
            raise ValueError("invalid seed or nonterminal horizon")
        if min(self.selection_episodes, self.final_episodes, self.batch) <= 0:
            raise ValueError("exposure counts must be positive")


def release_due(view):
    """Infer the receiver's last self-packet from legal sender-owned information."""
    stale_self, valid, _ = project(view.last_sent, view.last_sent_time, view.t)
    return (view.own[:, 0] == DONE) & valid & (stale_self[:, 4] == SHARED) & (
        stale_self[:, 0] == APPROACH) & (stale_self[:, 1] <= 1)


def stale_release_waits(host):
    """Privileged factual diagnostic; never consumed by a scheduling policy."""
    own = host.payloads()
    cached, valid, _ = project(host.cache, host.cache_time, host.t)
    actual_peer = own[:, ::-1]
    permitted = gate(own, cached, valid, np.arange(2))
    full = gate(own, actual_peer, np.ones_like(valid), np.arange(2))
    stale_approach = valid & (cached[..., 4] == SHARED) & (
        cached[..., 0] == APPROACH) & (cached[..., 1] <= 1)
    return ((actual_peer[..., 0] == DONE) & stale_approach & ~permitted & full).sum(1)


def load_frozen(source_root, spec):
    path = Path(source_root) / spec.path
    actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_digest != spec.sha256:
        raise ValueError(f"checkpoint digest mismatch: {spec.path}")
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    expected_config = dict(seed=spec.seed, horizon=96, train_episodes=4096,
        initial_episodes=64, selection_episodes=256, final_episodes=256, batch=32, epochs=4)
    if checkpoint["launch_sha"] != spec.source_sha or checkpoint["config"] != expected_config:
        raise ValueError(f"checkpoint metadata mismatch: {spec.path}")
    model = build_scheduler(spec.seed)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval().requires_grad_(False)
    if not all(torch.isfinite(p).all() for p in model.parameters()):
        raise FloatingPointError("non-finite frozen checkpoint")
    return model


def collect(host, *, model=None, arm="LEARNED", release=False, distance_delta=2,
            age_limit=None, retain_trace=False):
    traces = {key: [] for key in ("features", "raw_requested", "requested", "release_due",
        "choice_mask", "sent", "state", "delivered_cache", "cache_send_time")}
    for key in ("release_overrides", "stale_release_waits"):
        host.metrics[key] = np.zeros(host.batch, dtype=np.int64)
    while host.t < host.horizon:
        view = host.view()
        features = view.features()
        if arm == "LEARNED":
            if model is None:
                raise ValueError("learned scheduling requires a frozen model")
            with torch.no_grad():
                logits, _ = model(torch.from_numpy(features))
                raw_requested = (logits.sigmoid() >= .5).numpy()
        else:
            raw_requested = simple_requests(view, arm, distance_delta, age_limit)
        due = release_due(view)
        requested = raw_requested | due if release else raw_requested
        host.metrics["release_overrides"] += release & due & ~raw_requested & view.choice_mask
        host.metrics["stale_release_waits"] += stale_release_waits(host)
        if retain_trace:
            values = dict(features=features, raw_requested=raw_requested, requested=requested,
                release_due=due, choice_mask=view.choice_mask,
                sent=view.available & (requested | view.forced), state=host.payloads(),
                delivered_cache=host.cache, cache_send_time=host.cache_time)
            for key, value in values.items():
                traces[key].append(value.copy())
        host.step(requested)
    trace = None
    if retain_trace:
        trace = {key: np.stack(values, axis=1) for key, values in traces.items()}
        trace["world_ids"] = np.asarray(host.worlds.ids, dtype=np.int64)
    return host.rows(), trace


def reading(rows):
    result = mean_reading(rows)
    for key in ("release_overrides", "stale_release_waits"):
        result[key] = float(np.mean([row[key] for row in rows]))
    return result


def paired(left, right):
    if [r["world_id"] for r in left] != [r["world_id"] for r in right]:
        raise ValueError("paired worlds do not match")
    difference = np.asarray([a["service"] - b["service"] for a, b in zip(left, right)])
    return dict(mean=float(difference.mean()), positive=int((difference > 0).sum()),
        negative=int((difference < 0).sum()), ties=int((difference == 0).sum()),
        world_ids=[r["world_id"] for r in left], per_world_difference=difference.tolist(),
        conditional_on="frozen trained policies on a shared fresh world panel; no new training units")


def run_study(out, launch_sha, source_root, config=Config(), checkpoint_specs=CHECKPOINTS):
    out = Path(out)
    if (out / "summary.json").exists():
        raise FileExistsError("C03 never overwrites or resumes scientific output")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    started = time.monotonic()
    counts = dict(started_fits=0, train_episodes=0, train_transitions=0, optimizer_steps=0,
        evaluation_optimizer_steps=0, selection_episodes=0, selection_transitions=0,
        selection_choice_opportunities=0, eval_episodes=0, eval_transitions=0,
        eval_choice_opportunities=0)
    summary = dict(object="SIR-C03", direction="skill_information_refresh", status="RUNNING",
        launch_sha=launch_sha, config=asdict(config), counts=counts, checkpoints=[],
        limits=[], selection=[], final={}, dtype="float32", device="cpu", native_threads=1,
        phases_seconds={}, resources_unmeasured=False,
        claim_scope="release-priority intervention on frozen C01/C02 policies; no new learning")
    write_json(out / "config.json", asdict(config))
    write_json(out / "summary.json", summary)
    models, originals, final_rows = {}, {}, {}
    with (out / "episodes.jsonl").open("x") as stream, (out / "updates.jsonl").open("x"):
        def evaluate(name, phase, phase_id, episodes, *, arm, release=False, model=None,
                     distance_delta=2, age_limit=None, variant=None, retain_trace=False):
            rows, trace_batches = [], []
            for start in range(0, episodes, config.batch):
                ids = range(start, min(start + config.batch, episodes))
                host = CrossingHost(Worlds.make(config.seed, phase_id, ids, config.horizon))
                batch_rows, trace = collect(host, model=model, arm=arm, release=release,
                    distance_delta=distance_delta, age_limit=age_limit, retain_trace=retain_trace)
                for row in batch_rows:
                    stream.write(json.dumps(dict(phase=phase, arm=name, variant=variant, **row),
                        allow_nan=False) + "\n")
                stream.flush()
                rows.extend(batch_rows)
                counts[f"{phase}_episodes"] += len(batch_rows)
                counts[f"{phase}_transitions"] += len(batch_rows) * config.horizon
                counts[f"{phase}_choice_opportunities"] += sum(r["choice_opportunities"] for r in batch_rows)
                if trace is not None:
                    trace_batches.append(trace)
            if retain_trace:
                np.savez_compressed(out / f"final_trace_{name}.npz", **{
                    key: np.concatenate([tr[key] for tr in trace_batches]) for key in trace_batches[0]})
            return rows

        try:
            for spec in checkpoint_specs:
                name = f"L{spec.seed}"
                if name in models:
                    raise ValueError("duplicate frozen policy identity")
                models[name] = load_frozen(source_root, spec)
                originals[name] = flat_parameters(models[name])
                summary["checkpoints"].append(dict(name=name, **asdict(spec)))
            phase_start = time.monotonic()
            selected = {}
            for family, release in (("AGE_CHANGE", False), ("AGE_RELEASE", True)):
                variants = []
                for delta in (1, 2, 4):
                    for age in (8, 12, None):
                        variant = f"delta{delta}_age{age if age is not None else 'off'}"
                        rows = evaluate(family, "selection", 4, config.selection_episodes,
                            arm="AGE_CHANGE", release=release, distance_delta=delta,
                            age_limit=age, variant=variant)
                        record = dict(family=family, variant=variant, distance_delta=delta,
                            age_limit=age, reading=reading(rows))
                        variants.append(record)
                        summary["selection"].append(record)
                selected[family] = sorted(variants, key=lambda r: (-r["reading"]["service"], r["variant"]))[0]
            simple = sorted(selected.values(), key=lambda r: (-r["reading"]["service"], r["family"]))[0]
            summary["selected_baselines"] = selected
            summary["selected_simple_reference"] = simple["family"]
            summary["phases_seconds"]["selection"] = time.monotonic() - phase_start
            write_json(out / "selection.json", dict(variants=summary["selection"],
                selected=selected, simple_reference=simple["family"]))
            phase_start = time.monotonic()
            for name, model in models.items():
                for release in (False, True):
                    label = name + ("_RELEASE" if release else "")
                    final_rows[label] = evaluate(label, "eval", 5, config.final_episodes,
                        arm="LEARNED", model=model, release=release, retain_trace=True)
            for family, release in (("AGE_CHANGE", False), ("AGE_RELEASE", True)):
                best = selected[family]
                final_rows[family] = evaluate(family, "eval", 5, config.final_episodes,
                    arm="AGE_CHANGE", release=release, distance_delta=best["distance_delta"],
                    age_limit=best["age_limit"], variant=best["variant"], retain_trace=True)
            for arm in ("PRE_DECISION", "POLL"):
                final_rows[arm] = evaluate(arm, "eval", 5, config.final_episodes,
                    arm=arm, retain_trace=True)
            summary["phases_seconds"]["eval"] = time.monotonic() - phase_start
            summary["final"] = {arm: reading(rows) for arm, rows in final_rows.items()}
            summary["release_effect"] = {name: paired(final_rows[name + "_RELEASE"], final_rows[name])
                for name in models}
            summary["versus_selected_simple"] = {name: paired(rows, final_rows[simple["family"]])
                for name, rows in final_rows.items() if name.startswith("L")}
            if not all(row["packets"] == 2 * config.horizon // 8
                       for rows in final_rows.values() for row in rows):
                raise RuntimeError("fixed packet quota violated")
            for name, model in models.items():
                if not torch.equal(flat_parameters(model), originals[name]):
                    raise RuntimeError("frozen model changed during evaluation")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "TECHNICAL_FAILURE"
            summary["limits"].append(f"{type(error).__name__}: {error}")
            raise
        finally:
            summary["frozen_parameters"] = {name: dict(
                parameters=sum(p.numel() for p in model.parameters()),
                displacement_from_loaded=float((flat_parameters(model) - originals[name]).norm()),
                parameters_finite=bool(all(torch.isfinite(p).all() for p in model.parameters())))
                for name, model in models.items() if name in originals}
            summary["wall_seconds"] = time.monotonic() - started
            usage = resource.getrusage(resource.RUSAGE_SELF)
            summary["resources"] = dict(peak_rss_kib=usage.ru_maxrss,
                rss_scope="one Linux scientific child, not aggregate node occupancy",
                user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime)
            write_json(out / "summary.json", summary)
    published = json.loads((out / "summary.json").read_text())
    if published["counts"] != counts or published["status"] != "COMPLETE":
        raise RuntimeError("summary readback failed")
    return summary
