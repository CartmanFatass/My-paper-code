"""Two parameter-free stage rules against the existing frozen timing policies."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import time

import numpy as np
import torch
from torch import nn

from ..c01.host import CrossingHost, Worlds
from ..c01.learner import flat_parameters
from ..c01.study import write_json
from ..c03.study import CHECKPOINTS, Config as ReleaseConfig, collect, load_frozen, paired, reading


@dataclass(frozen=True)
class Config(ReleaseConfig):
    seed: int = 73151


class StageRule(nn.Module):
    """Parameter-free adapter for the audited collector, never a trained policy."""

    def __init__(self, name):
        super().__init__()
        if name not in ("ACTIVE_FIRST", "APPROACH_FIRST"):
            raise ValueError("unknown fixed stage rule")
        self.name = name

    def forward(self, features):
        # C01's first three legal features are APPROACH/CROSSING/DONE one-hot.
        wanted = features[:, 0] > .5
        if self.name == "ACTIVE_FIRST":
            wanted = wanted | (features[:, 1] > .5)
        logits = torch.where(wanted, 1., -1.)
        return logits, torch.zeros_like(logits)


def run_study(out, launch_sha, source_root, config=Config(), checkpoint_specs=CHECKPOINTS):
    out = Path(out)
    if (out / "summary.json").exists():
        raise FileExistsError("C04 never overwrites or resumes scientific output")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    started = time.monotonic()
    counts = dict(started_fits=0, train_episodes=0, train_transitions=0, optimizer_steps=0,
        evaluation_optimizer_steps=0, selection_episodes=0, selection_transitions=0,
        selection_choice_opportunities=0, eval_episodes=0, eval_transitions=0,
        eval_choice_opportunities=0)
    summary = dict(object="SIR-C04", direction="skill_information_refresh", status="RUNNING",
        launch_sha=launch_sha, config=asdict(config), counts=counts, checkpoints=[], limits=[],
        selection=[], final={}, dtype="float32", device="cpu", native_threads=1,
        phases_seconds={}, resources_unmeasured=False,
        fixed_stage_rules={name: dict(parameters=0, training_updates=0)
            for name in ("ACTIVE_FIRST", "APPROACH_FIRST")},
        claim_scope="stage-only null versus three frozen policies; no new learning or training units")
    write_json(out / "config.json", asdict(config))
    write_json(out / "summary.json", summary)
    models, originals, final_rows = {}, {}, {}
    stage_rules = {name: StageRule(name) for name in ("ACTIVE_FIRST", "APPROACH_FIRST")}
    with (out / "episodes.jsonl").open("x") as stream, (out / "updates.jsonl").open("x"):
        def evaluate(name, phase, phase_id, episodes, *, arm=None, model=None,
                     distance_delta=2, age_limit=None, variant=None, retain_trace=False):
            if name in stage_rules:
                arm, model = "LEARNED", stage_rules[name]  # Interface only; labels/counts stay nonlearning.
            rows, trace_batches = [], []
            for start in range(0, episodes, config.batch):
                ids = range(start, min(start + config.batch, episodes))
                host = CrossingHost(Worlds.make(config.seed, phase_id, ids, config.horizon))
                batch_rows, trace = collect(host, model=model, arm=arm, release=False,
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
            age_variants = []
            for delta in (1, 2, 4):
                for age in (8, 12, None):
                    variant = f"delta{delta}_age{age if age is not None else 'off'}"
                    rows = evaluate("AGE_CHANGE", "selection", 6, config.selection_episodes,
                        arm="AGE_CHANGE", distance_delta=delta, age_limit=age, variant=variant)
                    record = dict(arm="AGE_CHANGE", variant=variant, distance_delta=delta,
                        age_limit=age, reading=reading(rows))
                    age_variants.append(record)
                    summary["selection"].append(record)
            selected_age = sorted(age_variants, key=lambda r: (-r["reading"]["service"], r["variant"]))[0]
            candidates = [selected_age]
            for name in ("ACTIVE_FIRST", "APPROACH_FIRST", "PRE_DECISION"):
                rows = evaluate(name, "selection", 6, config.selection_episodes, arm=name)
                record = dict(arm=name, variant=None, reading=reading(rows))
                candidates.append(record)
                summary["selection"].append(record)
            selected = sorted(candidates, key=lambda r: (-r["reading"]["service"], r["arm"]))[0]
            summary["selected_age"] = selected_age
            summary["selected_simple_reference"] = selected["arm"]
            summary["phases_seconds"]["selection"] = time.monotonic() - phase_start
            write_json(out / "selection.json", dict(variants=summary["selection"],
                selected_age=selected_age, simple_reference=selected["arm"]))
            phase_start = time.monotonic()
            for name, model in models.items():
                final_rows[name] = evaluate(name, "eval", 7, config.final_episodes,
                    arm="LEARNED", model=model, retain_trace=True)
            final_rows["AGE_CHANGE"] = evaluate("AGE_CHANGE", "eval", 7, config.final_episodes,
                arm="AGE_CHANGE", distance_delta=selected_age["distance_delta"],
                age_limit=selected_age["age_limit"], variant=selected_age["variant"], retain_trace=True)
            for name in ("ACTIVE_FIRST", "APPROACH_FIRST", "PRE_DECISION", "POLL"):
                final_rows[name] = evaluate(name, "eval", 7, config.final_episodes, arm=name, retain_trace=True)
            summary["phases_seconds"]["eval"] = time.monotonic() - phase_start
            summary["final"] = {name: reading(rows) for name, rows in final_rows.items()}
            summary["versus_selected_simple"] = {name: paired(final_rows[name], final_rows[selected["arm"]])
                for name in models}
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
