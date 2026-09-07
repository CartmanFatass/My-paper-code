"""A02: fixed-state, same-graph score decomposition; no learner updates."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as host
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import C1P1, FLEX, BASELINE_DECAY
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    TBCFVModel, apply_affine_fixture_uniforms, required_affine_fixture_uniforms,
    exact_advantage_loss, make_pointer_inputs,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.study import (
    B01BlockAuthority, TRAINING_CELLS, block_digest_hex, seed_root_key,
    native_certificate_payload, peak_rss_bytes,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
    make_b02_semantic_rng, SEED_KEY_ASCII,
)

OBJECT = "RCLE-TBCFV-A02-FROZEN-SCORE-ALLOCATION"
PURPOSE = "post-b02-frozen-probe"
BLOCKS = (19001, 19002)
CONFIGURATIONS = (("C1P1-init", C1P1), ("FLEX-init", FLEX),
                  ("C1P1-final", C1P1), ("FLEX-final", FLEX))
GROUPS = ("encoders", "manager", "pointer", "common_update", "agent_update")
TICKS = (0, 24, 28, 60)
RESIDUAL_ATOL = 1e-10
RESIDUAL_RTOL = 1e-8


def probe_rng(block):
    digest = block_digest_hex(seed_root_key(SEED_KEY_ASCII), PURPOSE, block)
    authority = B01BlockAuthority({"native": native_certificate_payload()}, block, digest)
    return host.SemanticRNG(authority, block, now=datetime.now(timezone.utc), arm_only_domain=PURPOSE)


def initial_model(rng):
    """Original initialization addresses and affine law, exactly one model."""
    model = TBCFVModel()
    uniforms = {}
    for name, shape in required_affine_fixture_uniforms(model).items():
        values = rng.uniform_many(tuple(host._address(
            rng.block_index, parameter_entry=name,
            draw_kind="common-initial-parameter", draw_index=index,
        ) for index in range(math.prod(shape))))
        uniforms[name] = torch.tensor(values, dtype=torch.float64).reshape(shape)
    apply_affine_fixture_uniforms(model, uniforms)
    return model


def reconstruct_baseline(summary):
    """Use full-precision retained cell means; never use the new probe returns."""
    curves = summary.get("curves", [])
    if len(curves) != 200 or [row.get("update") for row in curves] != list(range(200)):
        return None
    baseline = torch.zeros(8, dtype=torch.float64)
    for row in curves:
        cells = row.get("per_cell", [])
        if [cell.get("cell") for cell in cells] != list(TRAINING_CELLS):
            return None
        means = torch.tensor([cell["Y_mean"] for cell in cells], dtype=torch.float64)
        if not bool(torch.isfinite(means).all()):
            return None
        baseline = BASELINE_DECAY * baseline + (1.0 - BASELINE_DECAY) * means
    return baseline


def group_name(name):
    if name.startswith(("agent_encoder.", "beacon_encoder.")):
        return "encoders"
    return next(group for group in GROUPS[1:] if name.startswith(group + "_"))


def vector(values, parameters):
    return torch.cat([(torch.zeros_like(p) if value is None else value.detach()).reshape(-1)
                      for value, p in zip(values, parameters)])


def projection(names, values):
    tensors = {name: {"norm": None if value is None else float(value.norm()),
                      "gradient_state": "no_graph" if value is None else
                      ("zero" if not bool(value.count_nonzero()) else "nonzero")}
               for name, value in zip(names, values)}
    groups = {group: math.sqrt(math.fsum(
        (tensors[name]["norm"] or 0.0) ** 2 for name in names if group_name(name) == group
    )) for group in GROUPS}
    return {"tensors": tensors, "groups": groups,
            "norm": math.sqrt(math.fsum(value ** 2 for value in groups.values()))}


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def cosine(left, right):
    return ratio(float(torch.dot(left, right)), float(left.norm()) * float(right.norm()))


def allocation(manager, actor, joint, pointer_norm):
    mn, an, jn = (float(value.norm()) for value in (manager, actor, joint))
    return {"manager_norm": mn, "actor_norm": an, "joint_norm": jn,
            "manager_actor_cosine": cosine(manager, actor),
            "cancellation_ratio": ratio(jn, mn + an),
            "r_A": ratio(an, mn + an), "r_P": ratio(pointer_norm, jn),
            "manager_dominant": None if mn + an == 0 else an / (mn + an) < 0.5}


def measure_gradients(model, results, baseline, final, progress=None):
    names, parameters = zip(*model.named_parameters())
    cells = torch.arange(8).repeat_interleave(8)
    returns = torch.tensor([item.Y for item in results], dtype=torch.float64)
    plans = [torch.stack(item.plan_scores) for item in results]
    claims = [torch.stack(item.claim_scores) for item in results]
    manager_scores = torch.stack([item.mean() for item in plans])
    actor_scores = torch.stack([item.mean() for item in claims])
    original_available = baseline is not None
    used_baseline = torch.zeros(8, dtype=torch.float64) if baseline is None else baseline
    advantage = returns.detach() - used_baseline.detach()[cells]
    losses = [-(advantage * manager_scores).mean(), -(advantage * actor_scores).mean(),
              exact_advantage_loss(returns, cells, used_baseline, plans, claims)]
    if final and original_available:
        losses.extend((-(returns.detach() * manager_scores).mean(),
                       -(returns.detach() * actor_scores).mean()))
    derivatives = []
    for index, loss in enumerate(losses):
        if progress is not None:
            progress["in_flight"] = f"derivative_{index + 1}"
            progress["counts"]["derivative_attempts"] += 1
        derivatives.append(torch.autograd.grad(loss, parameters, allow_unused=True,
                           retain_graph=index < len(losses) - 1))
        if progress is not None:
            progress["counts"]["derivative_evaluations"] += 1
            progress["in_flight"] = None
    projections = [projection(names, values) for values in derivatives]
    vectors = [vector(values, parameters) for values in derivatives]
    manager, actor, joint = vectors[:3]
    residual = float((joint - manager - actor).norm())
    tolerance = RESIDUAL_ATOL + RESIDUAL_RTOL * float(manager.norm() + actor.norm())
    reading = allocation(manager, actor, joint, projections[2]["groups"]["pointer"])
    reading.update({"projections": dict(zip(("manager", "actor", "joint"), projections[:3])),
                    "additivity_residual": residual, "additivity_tolerance": tolerance,
                    "additivity_pass": residual <= tolerance})
    cell_rows = []
    for index, cell in enumerate(TRAINING_CELLS):
        y, adv = returns[cells == index], advantage[cells == index]
        cell_rows.append({"cell": cell, "episodes": len(y), "Y_mean": float(y.mean()),
                          "Y_std": float(y.std(correction=0)),
                          "baseline": float(used_baseline[index]) if original_available else None,
                          "advantage_mean": float(adv.mean()),
                          "advantage_rms": float(adv.square().mean().sqrt()),
                          "advantage_std": float(adv.std(correction=0)),
                          "advantage_baseline": "original" if original_available else "zero_fallback"})
    output = {"original_baseline_available": original_available, "cells": cell_rows,
              "derivative_evaluations": len(losses),
              "original" if original_available else "zero_baseline": reading}
    if final and original_available:
        zero_joint = vectors[3] + vectors[4]
        zero_values = tuple(None if left is None and right is None else
                            (torch.zeros_like(p) if left is None else left) +
                            (torch.zeros_like(p) if right is None else right)
                            for left, right, p in zip(derivatives[3], derivatives[4], parameters))
        zero_projection = projection(names, zero_values)
        zero = allocation(vectors[3], vectors[4], zero_joint, zero_projection["groups"]["pointer"])
        zero["projections"] = {"manager": projections[3], "actor": projections[4], "joint": zero_projection}
        output["zero_baseline"] = zero
        output["original_over_zero_norm"] = ratio(float(joint.norm()), float(zero_joint.norm()))
        output["original_zero_cosine"] = cosine(joint, zero_joint)
    return output


def capture_inputs(points, coordinates, snapshots, plans):
    selected = [(lane, coordinate) for lane, coordinate in enumerate(coordinates)
                if coordinate.episode_row < 2 and snapshots[lane].tick in TICKS]
    if not selected:
        return
    packed = host._batched_public_tensors(snapshots)
    for lane, coordinate in selected:
        snapshot, plan = snapshots[lane], plans[lane]
        count = packed.counts[lane]
        keys = tuple(int(key) for key in snapshot.transport_keys)
        for member in (0, count - 1):
            points.append({"block": coordinate.block_index, "cell": coordinate.cell,
                           "episode": coordinate.episode_row, "tick": snapshot.tick,
                           "public_member_index": member,
                           "agents": packed.agents[lane, :count].detach().clone(),
                           "beacons": packed.beacons[lane].detach().clone(),
                           "context": packed.contexts[lane].detach().clone(),
                           "own": packed.own[lane, member].detach().clone(),
                           "candidates": packed.candidates[lane, member].detach().clone(),
                           "z": plan.current[keys[member]].detach().clone()})


def conditional_probabilities(model, points, progress=None):
    values = []
    with torch.no_grad():
        for point in points:
            if progress is not None:
                progress["in_flight"] = "conditional_probability_vector"
            pooled = torch.cat((model.agent_encoder(point["agents"]),
                                model.beacon_encoder(point["beacons"])))
            inputs = make_pointer_inputs(pooled, point["own"], point["context"],
                                         point["candidates"], point["z"])
            values.append(model.claim_probabilities(inputs))
            if progress is not None:
                progress["counts"]["probability_vectors"] += 1
                progress["in_flight"] = None
    return torch.stack(values)


def probability_report(probabilities, points):
    rows = []
    for block in BLOCKS:
        for cell in (None, *TRAINING_CELLS):
            indices = [index for index, point in enumerate(points)
                       if point["block"] == block and (cell is None or point["cell"] == cell)]
            if not indices:
                continue
            p = {name: value[indices] for name, value in probabilities.items()}
            row = {"block": block, "cell": cell, "points": len(indices),
                   "entropy_mean": {name: float((-(value * value.log()).sum(-1)).mean())
                                    for name, value in p.items()}, "TV": {}}
            for left, right in (("C1P1-final", "init"), ("FLEX-final", "init"),
                                ("FLEX-final", "C1P1-final")):
                tv = 0.5 * (p[left] - p[right]).abs().sum(-1)
                row["TV"][left + "_vs_" + right] = {"mean": float(tv.mean()), "max": float(tv.max())}
            rows.append(row)
    return rows


def displacement(left, right):
    return projection(tuple(left), tuple(left[name] - right[name] for name in left))


def write_summary(out, summary):
    temporary = out / "summary.tmp"
    temporary.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(out / "summary.json")


def run(out, state_root, summary_root, launch_sha, admission_receipt, started):
    out.mkdir(parents=True, exist_ok=True)
    summary = {"object": OBJECT, "launch_sha": launch_sha,
               "admission_receipt": str(admission_receipt), "seed": 18,
               "probe_domain": PURPOSE,
               "seed_root_key_hex": seed_root_key(SEED_KEY_ASCII).hex(),
               "probe_block_digests": {str(block): block_digest_hex(seed_root_key(SEED_KEY_ASCII), PURPOSE, block) for block in BLOCKS},
               "standard_deviation": "population, correction=0, eight samples per cell",
               "count_semantics": "completed operations; a named in_flight operation may be partially executed on a stop",
               "status": "RUNNING", "measurements": [], "inputs": {},
               "counts": {"models": 0, "episodes": 0, "environment_ticks": 0,
                          "derivative_evaluations": 0, "derivative_attempts": 0, "optimizer_steps": 0,
                          "fixed_input_points": 0, "probability_vectors": 0}}
    points, probabilities = [], {}
    try:
        _, init_rng = make_b02_semantic_rng()
        initial = initial_model(init_rng)
        summary["counts"]["models"] = 1
        models = {"C1P1-init": initial}
        initial_state = {name: value.clone() for name, value in initial.state_dict().items()}
        baseline = {"C1P1-init": torch.zeros(8, dtype=torch.float64),
                    "FLEX-init": torch.zeros(8, dtype=torch.float64)}
        summaries = {}
        for label, _ in CONFIGURATIONS[1:]:
            models[label] = TBCFVModel()
            summary["counts"]["models"] += 1
            if label.endswith("init"):
                models[label].load_state_dict(initial_state)
            else:
                arm = "c1p1" if label.startswith("C1P1") else "flex"
                path = state_root / arm / "parameters.pt"
                models[label].load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
                summaries[label] = json.loads((summary_root / arm / "summary.json").read_text())
                baseline[label] = reconstruct_baseline(summaries[label])
                summary["inputs"][label] = {"parameters": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "training_curve": str(summary_root / arm / "summary.json"),
                    "baseline": "reconstructed" if baseline[label] is not None else "unavailable",
                    "baseline_precision": "FP64 JSON math.fsum cell means; original buffer used torch.mean; not bit-exact"}
        initial_norm = math.sqrt(math.fsum(float(value.square().sum()) for value in initial_state.values()))
        recorded_norm = summaries["C1P1-final"]["initial_parameter_norm"]
        summary["inputs"]["init"] = {"method": "rebuilt_original_seed18_affine_law", "norm": initial_norm,
            "recorded_norm": recorded_norm, "norm_matches": math.isclose(initial_norm, recorded_norm, rel_tol=1e-12, abs_tol=1e-12)}
        if not summary["inputs"]["init"]["norm_matches"]:
            raise ValueError("rebuilt initialization norm differs from retained seed18 identity")
        c_state, f_state = models["C1P1-final"].state_dict(), models["FLEX-final"].state_dict()
        summary["displacements"] = {"C1P1_final_minus_init": displacement(c_state, initial_state),
                                    "FLEX_final_minus_init": displacement(f_state, initial_state),
                                    "FLEX_final_minus_C1P1_final": displacement(f_state, c_state)}
        write_summary(out, summary)
        for label, arm in CONFIGURATIONS:
            for block in BLOCKS:
                rng = probe_rng(block)
                results = []
                def observer(coords, snaps, plans):
                    capture_inputs(points, coords, snaps, plans)
                    summary["counts"]["fixed_input_points"] = len(points)
                summary["active_configuration_block"] = [label, block]
                for cell_start in (0, 4):
                    coords = tuple(host.EpisodeCoordinate(block, cell, 0, row)
                                   for cell in TRAINING_CELLS[cell_start:cell_start + 4] for row in range(8))
                    summary["in_flight"] = "native_batch_32episodes"
                    results.extend(host.execute_learned_batch(models[label], arm, rng, coords,
                                   training=True, claim_observer=observer if label == "C1P1-init" else None))
                    summary["counts"]["episodes"] += len(coords)
                    summary["counts"]["environment_ticks"] += len(coords) * 64
                    summary["in_flight"] = None
                measured = measure_gradients(models[label], results, baseline[label], label.endswith("final"), summary)
                summary["measurements"].append({"configuration": label, "block": block, **measured})
                del results
                if label == "C1P1-init":
                    torch.save({"points": points, "probabilities": probabilities}, out / "fixed_inputs.pt")
                write_summary(out, summary)
        for label, model in (("init", initial), ("C1P1-final", models["C1P1-final"]),
                             ("FLEX-final", models["FLEX-final"])):
            probabilities[label] = conditional_probabilities(model, points, summary)
            torch.save({"points": points, "probabilities": probabilities}, out / "fixed_inputs.pt")
        summary["conditional_probabilities"] = probability_report(probabilities, points)
        summary["status"] = "COMPLETE"
        summary["all_additivity_pass"] = all(row.get("original", row.get("zero_baseline"))["additivity_pass"]
                                             for row in summary["measurements"])
    except Exception as exc:
        summary["status"] = "TECHNICAL_STOP"
        summary["stop_reason"] = f"{type(exc).__name__}: {exc}"
        if points:
            torch.save({"points": points, "probabilities": probabilities}, out / "fixed_inputs.pt")
    summary["wall_seconds"] = time.perf_counter() - started
    summary["probability_vectors_retained"] = sum(len(value) for value in probabilities.values())
    summary["wall_scope"] = "process start through measurements/intermediate publication; excludes final summary write; GNU time records complete process"
    summary["peak_rss_bytes"] = peak_rss_bytes()
    write_summary(out, summary)
    return summary
