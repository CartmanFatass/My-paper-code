"""B03: two FLEX policies, with reporting labels outside all random addresses."""
from datetime import datetime, timezone
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import FLEX
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import (
    SemanticRNG, EpisodeCoordinate, execute_learned_batch, initialize_block_models,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    averaged_episode_score, _validated_block_cells,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01 import study as host
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
    apply_b02_block_update,
)

OBJECT_ID = "RCLE-TBCFV-B03-ACTOR100"
SEED = 19
WEIGHTS = {"W1": 1.0, "W100": 100.0}


def make_rng():
    digest = host.block_digest_hex(host.seed_root_key(f"{OBJECT_ID}/seed/{SEED}"), OBJECT_ID, 0)
    authority = host.B01BlockAuthority(
        certificate={"native": host.native_certificate_payload()}, block_index=0, root_digest=digest,
    )
    return authority, SemanticRNG(authority, 0, now=datetime.now(timezone.utc))


def weighted_loss(returns, cell_indices, baselines, plan_scores, claim_scores, weight):
    cells = _validated_block_cells(cell_indices)
    means = [averaged_episode_score(p, a) for p, a in zip(plan_scores, claim_scores)]
    scores = torch.stack([p + weight * a for p, a, _ in means])
    advantage = returns.detach().to(scores) - baselines.detach().to(scores)[cells]
    return -(advantage * scores).mean()


def training_update(model, rng, update, baselines, weight):
    results, cells = [], []
    for start in range(0, 8, 4):
        coordinates = tuple(
            EpisodeCoordinate(rng.block_index, cell, update, row)
            for cell in host.TRAINING_CELLS[start:start + 4] for row in range(8)
        )
        results.extend(execute_learned_batch(model, FLEX, rng, coordinates, training=True))
        cells.extend(cell for cell in range(start, start + 4) for _ in range(8))
    returns = torch.tensor([r.Y for r in results], dtype=torch.float64)
    indices = torch.tensor(cells, dtype=torch.int64)
    model.zero_grad(set_to_none=True)
    loss = weighted_loss(returns, indices, baselines,
                         [torch.stack(r.plan_scores) for r in results],
                         [torch.stack(r.claim_scores) for r in results], weight)
    if not bool(torch.isfinite(loss)):
        raise RuntimeError("nonfinite loss")
    loss.backward()
    if any(p.grad is not None and not bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
        raise RuntimeError("nonfinite gradient")
    audit = apply_b02_block_update(model, baselines, returns, indices, 0.02)
    step = audit.block.parameter_update
    curve = {
        "update": update, "loss": float(loss.detach()),
        "raw_gradient_norm": step.raw_gradient_norm, "nonzero": step.nonzero,
        "parameter_delta_norm": step.parameter_delta_norm,
        "measured_parameter_delta_norm": audit.measured_parameter_delta_norm,
        "event_order": list(audit.block.event_order),
        "per_cell": [dict(cell=cell, episodes=8, **{
            f"{key}_mean": host._mean([float(getattr(results[i], key)) for i in range(64) if cells[i] == c])
            for key in ("Y", "U", "tau", "F")
        }) for c, cell in enumerate(host.TRAINING_CELLS)],
        "training_episodes": len(results), "environment_ticks": 64 * len(results),
        "agent_ticks": sum(r.agent_ticks for r in results),
        "agent_claim_decisions": sum(r.claim_decisions for r in results),
    }
    return audit.block.updated_baselines, curve


def panel(model, rng, label, started, cap):
    rows, _ = host.evaluate_learned(model, FLEX, rng, 256, started=started, wall_cap=cap)
    return [dict(row, arm=label, package=FLEX) for row in rows]


def panel_summary(rows):
    cells = host.cell_endpoint_means(rows)
    for values in cells.values():
        values["40U_mean"] = 40 * values["U_mean"]
    secondary = host.eight_cell_mean(cells)
    secondary["40U_mean"] = 40 * secondary["U_mean"]
    return dict(cells=cells, eight_cell_mean=secondary)


def primary(init_rows, w1_rows, w100_rows):
    init, w1, w100 = map(host._group, (init_rows, w1_rows, w100_rows))
    paths = []
    for cell in host.PRIMARY_CELLS:
        a, b, z = w1[cell], w100[cell], init[cell]
        indices = [int(row["index"]) for row in a]
        if len(set(indices)) != len(indices) or any(
            indices != [int(row["index"]) for row in rows] for rows in (b, z)
        ):
            raise ValueError(f"paired indices differ or duplicate: {cell}")
        us = [np.array([row["U"] for row in rows], dtype=np.float64) for rows in (a, b, z)]
        d = us[0] - us[1]
        se = float(d.std(ddof=1) / np.sqrt(len(d)))
        paths.append(dict(cell=cell, n=len(d), Delta_U=float(d.mean()), SE=se,
                          W1_U=float(us[0].mean()), W100_U=float(us[1].mean()),
                          init_U=float(us[2].mean()),
                          G_U_W1=float((us[2] - us[0]).mean()),
                          G_U_W100=float((us[2] - us[1]).mean())))
    delta = host._mean([p["Delta_U"] for p in paths])
    se = host.se_of_mean_of_independent_ses([p["SE"] for p in paths])
    return dict(active_paths=paths, Delta_U=delta, SE=se,
                approximate_95_interval=[delta - 1.96 * se, delta + 1.96 * se],
                G_U_W1=host._mean([p["G_U_W1"] for p in paths]),
                G_U_W100=host._mean([p["G_U_W100"] for p in paths]),
                uncertainty="conditional scenario Monte Carlo; distinct cell RNG domains; one training pair",
                positive_favors="W100", MEI_U=0.05)


def run(arm, out, launch_sha, admission_receipt, started, wall_cap, control_summary=None):
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_rng()
    summary = dict(object=OBJECT_ID, arm=arm, package=FLEX if arm in WEIGHTS else arm,
                   seed=SEED, launch_sha=launch_sha, admission_receipt=str(admission_receipt),
                   root_key_hex=host.seed_root_key(f"{OBJECT_ID}/seed/{SEED}").hex(),
                   block_digest_hex=authority.root_digest, native=authority.certificate["native"],
                   status="IN_PROGRESS", scenarios=[], curves=[])
    try:
        if arm == "reference":
            summary["scenarios"] = host.evaluate_scripted(rng, 256)
            summary["Y_note"] = "ScriptedEpisodeResult has no Y; Y is null"
            summary["allocations"] = dict(models=0, training_instances=0)
        else:
            # Existing initializer makes one helper plus five package copies; only FLEX trains.
            allocated = initialize_block_models(rng)
            model = allocated[FLEX]
            del allocated
            initial = host.flat_parameters(model).clone()
            summary["allocations"] = dict(models=6, training_instances=1, untrained_helpers=5)
            summary["initial_parameter_norm"] = float(torch.linalg.vector_norm(initial))
            summary["actor_score_weight"] = WEIGHTS[arm]
            torch.save(model.state_dict(), out / "initial_parameters.pt")
            if arm == "W1":
                summary["initialization_panel"] = panel(model, rng, "FLEX-INIT", started, wall_cap)
                host.write_json(out / "init_scenarios.json", summary["initialization_panel"])
            baselines = torch.zeros(8, dtype=torch.float64)
            for update in range(200):
                host.check_wall(started, wall_cap)
                baselines, curve = training_update(model, rng, update, baselines, WEIGHTS[arm])
                summary["curves"].append(curve)
            torch.save(model.state_dict(), out / "parameters.pt")
            host.write_json(out / "summary.json", summary)
            summary["scenarios"] = panel(model, rng, arm, started, wall_cap)
            summary["final_displacement"] = float(torch.linalg.vector_norm(host.flat_parameters(model) - initial))
            summary["final_baselines"] = baselines.tolist()
            if arm == "W100":
                control = host.load_control_summary(control_summary)
                summary["paired_primary"] = primary(control["initialization_panel"],
                                                     control["scenarios"], summary["scenarios"])
        summary.update(panel_summary(summary["scenarios"]))
        if "initialization_panel" in summary:
            summary["initialization_summary"] = panel_summary(summary["initialization_panel"])
        host.check_wall(started, wall_cap)
        summary["status"] = "COMPLETE"
    except Exception as exc:
        summary["status"] = "TECHNICAL_STOP"
        summary["stop_reason"] = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, host.ArmWallExpired) and exc.evaluated_rows:
            summary["partial_evaluation_rows"] = list(exc.evaluated_rows)
    finally:
        curves = summary["curves"]
        summary["counts"] = dict(training_episodes=sum(c["training_episodes"] for c in curves),
                                  backward_step_calls=len(curves),
                                  nonzero_steps=sum(c["nonzero"] for c in curves),
                                  zero_steps=sum(not c["nonzero"] for c in curves),
                                  final_episodes=len(summary["scenarios"]),
                                  init_episodes=len(summary.get("initialization_panel", [])))
        summary["wall_seconds"] = time.perf_counter() - started
        summary["peak_rss_bytes"] = host.peak_rss_bytes()
        host.write_json(out / "summary.json", summary)
    return summary
