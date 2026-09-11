"""One B04 fit: native-return learning from an overridable nearest-action prior."""
from datetime import datetime, timezone
import math
import time
import traceback

import numpy as np
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import TBCFVModel
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study as b03

host = b03.host
OBJECT_ID = "RCLE-TBCFV-B04-NEAREST-PRIOR"
SEED = 24
UPDATES = 200
LAW = {"nearest_probability": .9, "other_probability": .02,
       "distance_field": 76, "tie": "first candidate", "pointer_output_initially_zero": True}


class NearestPriorModel(TBCFVModel):
    def __init__(self, action_law=None):
        super().__init__()
        self.action_law = dict(LAW if action_law is None else action_law)

    def claim_probabilities(self, pointer_inputs):
        logits = self.pointer_logits(pointer_inputs)
        nearest = pointer_inputs[..., self.action_law["distance_field"]].abs().argmin(dim=-1, keepdim=True)
        odds = self.action_law["nearest_probability"] / self.action_law["other_probability"]
        offset = torch.zeros_like(logits).scatter_(-1, nearest, math.log(odds))
        return torch.softmax(logits + offset, dim=-1)


def initialize_model(rng, action_law=None):
    helpers = b03.initialize_block_models(rng)
    model = NearestPriorModel(action_law=action_law)
    model.load_state_dict(helpers[b03.FLEX].state_dict())
    with torch.no_grad():
        model.pointer_score.weight.zero_()
        model.pointer_score.bias.zero_()
    return model


def save_model(model, path):
    torch.save({"state_dict": model.state_dict(), "action_law": model.action_law,
                "model": "NearestPriorModel"}, path)


def make_rng(seed, object_id=OBJECT_ID):
    key = host.seed_root_key(f"{object_id}/seed/{seed}")
    digest = host.block_digest_hex(key, object_id, 0)
    authority = host.B01BlockAuthority(
        certificate={"native": host.native_certificate_payload()}, block_index=0, root_digest=digest)
    return authority, b03.SemanticRNG(authority, 0, now=datetime.now(timezone.utc))


def comparisons(initial, final, reference):
    groups = [host._group(rows) for rows in (initial, final, reference)]
    cells = {}
    for cell in host.HELDOUT_CELLS:
        rows = [group[cell] for group in groups]
        indices = [[int(row["index"]) for row in role] for role in rows]
        if indices[0] != indices[1] or indices[0] != indices[2] or len(set(indices[0])) != len(indices[0]):
            raise ValueError(f"paired indices differ or duplicate: {cell}")
        values = [{k: np.array([r[k] for r in role], dtype=float) for k in ("U", "F", "tau")}
                  for role in rows]
        delta = values[2]["U"] - values[1]["U"]
        cells[cell] = dict(n=len(delta), Delta_ref=float(delta.mean()),
                          SE=float(delta.std(ddof=1) / math.sqrt(len(delta))),
                          G_U=float((values[0]["U"] - values[1]["U"]).mean()),
                          reference_gap=float(-delta.mean()),
                          initial_U=float(values[0]["U"].mean()),
                          final_U=float(values[1]["U"].mean()),
                          reference_U=float(values[2]["U"].mean()),
                          final_minus_initial={k: float((values[1][k] - values[0][k]).mean())
                                              for k in ("U", "F", "tau")},
                          final_minus_reference={k: float((values[1][k] - values[2][k]).mean())
                                                for k in ("U", "F", "tau")})
    paths = [dict(cell=cell, **cells[cell]) for cell in host.PRIMARY_CELLS]
    primary = {k: host._mean([path[k] for path in paths])
               for k in ("Delta_ref", "G_U", "reference_gap", "initial_U", "final_U", "reference_U")}
    primary["SE"] = host.se_of_mean_of_independent_ses([path["SE"] for path in paths])
    primary["approximate_95_interval"] = [primary["Delta_ref"] + sign * 1.96 * primary["SE"]
                                          for sign in (-1, 1)]
    primary.update(active_paths=paths, MEI_U=.05, positive_favors="learned final",
                   uncertainty="conditional scenario Monte Carlo, one training instance; distinct cell RNG domains")
    return {"primary": primary, "cells": cells}


def reading(delta, gain, mixed):
    branches = []
    if delta >= .05 and gain > 0:
        branches.append("above-interest reference improvement with learning")
    if 0 < delta < .05:
        branches.append("small reference improvement")
    if delta <= 0 and gain > 0:
        branches.append("learning from prior with reference deficit")
    if gain <= 0:
        branches.append("no positive learning from initialization")
    if mixed:
        branches.append("mixed native consequences")
    return branches


def run(arm, out, launch_sha, admission_receipt, started, wall_cap, learned_summary=None, seed=SEED,
        *, updates=UPDATES, object_id=OBJECT_ID, panel_label="B04", action_law=None):
    action_law = dict(LAW if action_law is None else action_law)
    out.mkdir(parents=True, exist_ok=True)
    summary = dict(object=object_id, seed=seed, arm=arm, launch_sha=launch_sha,
                   admission_receipt=str(admission_receipt), action_law=action_law,
                   status="IN_PROGRESS", scenarios=[], curves=[])
    try:
        authority, rng = make_rng(seed, object_id=object_id)
        summary.update(root_key_hex=host.seed_root_key(f"{object_id}/seed/{seed}").hex(),
                       block_digest_hex=authority.root_digest, native=authority.certificate["native"])
        if arm == "learned":
            model = initialize_model(rng, action_law=action_law)
            initial = host.flat_parameters(model).clone()
            summary.update(allocations=dict(models=7, training_instances=1, untrained_helpers=6),
                           initial_parameter_norm=float(torch.linalg.vector_norm(initial)),
                           actor_score_weight=100, updates_per_fit=updates)
            save_model(model, out / "initial_parameters.pt")
            summary["initialization_panel"] = b03.panel(model, rng, f"{panel_label}-INITIAL", started, wall_cap)
            host.write_json(out / "init_scenarios.json", summary["initialization_panel"])
            baselines = torch.zeros(8, dtype=torch.float64)
            for update in range(updates):
                host.check_wall(started, wall_cap)
                baselines, curve = b03.training_update(model, rng, update, baselines, 100.0)
                summary["curves"].append(curve)
                with (out / "completed_blocks.jsonl").open("a", encoding="ascii") as blocks:
                    blocks.write(b03.json.dumps(curve, allow_nan=False) + "\n")
            save_model(model, out / "parameters.pt")
            host.write_json(out / "summary.json", summary)
            summary["scenarios"] = b03.panel(model, rng, f"{panel_label}-FINAL", started, wall_cap)
            summary["initialization_summary"] = b03.panel_summary(summary["initialization_panel"])
            summary["final_displacement"] = float(torch.linalg.vector_norm(host.flat_parameters(model) - initial))
            summary["final_baselines"] = baselines.tolist()
        else:
            summary["allocations"] = dict(models=0, training_instances=0)
            summary["scenarios"] = host.evaluate_scripted(rng, 256)
            summary["Y_note"] = "ScriptedEpisodeResult has no Y; Y is unavailable"
            learned = host.load_control_summary(learned_summary)
            result = comparisons(learned["initialization_panel"], learned["scenarios"], summary["scenarios"])
            summary["comparison"] = result
            paths = result["primary"]["active_paths"]
            mixed = (min(p["Delta_ref"] for p in paths) < 0 < max(p["Delta_ref"] for p in paths)
                     or any(c[key][metric] > 0 for c in result["cells"].values()
                            for key in ("final_minus_initial", "final_minus_reference") for metric in ("F", "tau")))
            summary["reading"] = reading(result["primary"]["Delta_ref"], result["primary"]["G_U"], mixed)
        summary.update(b03.panel_summary(summary["scenarios"]))
        host.check_wall(started, wall_cap)
        summary["status"] = "COMPLETE"
    except Exception as exc:
        traceback.print_exc()
        summary.update(status="TECHNICAL_STOP", stop_reason=f"{type(exc).__name__}: {exc}")
        if isinstance(exc, host.ArmWallExpired) and exc.evaluated_rows:
            summary["partial_evaluation_rows"] = list(exc.evaluated_rows)
    finally:
        curves = summary["curves"]
        summary["counts"] = dict(training_episodes=sum(c["training_episodes"] for c in curves),
                                  backward_step_calls=len(curves), nonzero_steps=sum(c["nonzero"] for c in curves),
                                  final_episodes=len(summary["scenarios"]),
                                  init_episodes=len(summary.get("initialization_panel", [])))
        summary["wall_seconds"] = time.perf_counter() - started
        summary["peak_rss_bytes"] = host.peak_rss_bytes()
        host.write_json(out / "summary.json", summary)
    return summary
