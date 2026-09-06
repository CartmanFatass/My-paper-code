"""B02 two-arm single-seed study: own 0.02-norm step, reuse B01 host helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Mapping, Sequence

import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    C1P1,
    FLEX,
    INDEPENDENT_NEAREST,
    LEARNED_PACKAGES,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import (
    EpisodeCoordinate,
    SemanticRNG,
    execute_learned_batch,
    initialize_block_models,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    BASELINE_DECAY,
    REGISTERED,
    TRAIN_CELLS,
    TRAIN_EPISODES_PER_BLOCK,
    BlockUpdateAudit,
    ParameterUpdateAudit,
    TBCFVModel,
    _validated_block_cells,
    exact_advantage_loss,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.study import (
    B01_ARMS,
    B01BlockAuthority,
    PRIMARY_CELLS,
    TRAINING_CELLS,
    HELDOUT_CELLS,
    ArmWallExpired,
    block_digest_hex,
    build_native,
    cell_endpoint_means,
    check_wall,
    cost_law,
    directory_bytes,
    eight_cell_mean,
    evaluate_learned,
    evaluate_scripted,
    flat_parameters,
    heldout_batches,
    initialize_b01_models,
    load_control_summary,
    native_available,
    native_certificate_payload,
    peak_rss_bytes,
    process_cpu_seconds,
    publish_paired_primary,
    restrict_two_arms,
    se_of_mean_of_independent_ses,
    seed_root_key,
    validate_control_summary,
    write_json,
    _group,
    _mean,
)

OBJECT_ID = "RCLE-TBCFV-B02-NORM-0p02"
IDENTITY = OBJECT_ID
SEED = 18
BLOCK_INDEX = 0
SEED_KEY_ASCII = f"{OBJECT_ID}/seed/{SEED}"
NONZERO_UPDATE_NORM_B02 = 0.02
PREVIOUS_NONZERO_UPDATE_NORM = 0.0005
MEI_U = 0.05
MEI_TAU_TICKS = 4
INIT_ARM = "C1P1-INIT"
INIT_SOURCE = "new:init:update0"
REFERENCE_SOURCE = "new:INDEPENDENT-NEAREST:seed18"
INITIAL_PARAMETER_NORM_REFERENCE_B01 = 21.186038495201018
PATH_BOUND = 4.0
STEP_LAW = "theta <- theta - 0.02 * g / ||g||_2 if g != 0 else no update"
SELECTION_HISTORY = (
    "0.0005 (B01, seed 17) -> 0.02 (B02, seed 18) after B01 intake"
)
FINAL_SOURCE = {
    "C1P1": f"new:{C1P1}:update200",
    "FLEX": f"new:{FLEX}:update200",
}


@dataclass(frozen=True)
class B02StepAudit:
    audit: ParameterUpdateAudit
    measured_parameter_delta_norm: float


@dataclass(frozen=True)
class B02BlockAudit:
    block: BlockUpdateAudit
    measured_parameter_delta_norm: float


def make_b02_semantic_rng(
    *, key_ascii: str = SEED_KEY_ASCII, now: datetime | None = None
) -> tuple[B01BlockAuthority, SemanticRNG]:
    digest = block_digest_hex(seed_root_key(key_ascii), IDENTITY, BLOCK_INDEX)
    authority = B01BlockAuthority(
        certificate={"native": native_certificate_payload()},
        block_index=BLOCK_INDEX,
        root_digest=digest,
    )
    rng = SemanticRNG(
        authority, BLOCK_INDEX, now=now or datetime.now(timezone.utc)
    )
    return authority, rng


def fixed_norm_sgd_step(
    model: TBCFVModel, nonzero_update_norm: float
) -> B02StepAudit:
    """Apply a full-vector fixed-norm SGD step parameterised by the prescribed norm."""

    parameters = tuple(model.parameters())
    if sum(parameter.numel() for parameter in parameters) != REGISTERED.parameters_per_arm:
        raise ValueError("SGD surface requires the complete registered 26,161-scalar tensor")
    squared_norm = torch.zeros((), dtype=torch.float64)
    for parameter in parameters:
        if parameter.grad is not None:
            squared_norm = squared_norm + parameter.grad.detach().to(torch.float64).square().sum()
    raw_norm_tensor = torch.sqrt(squared_norm)
    raw_norm = float(raw_norm_tensor.item())
    if raw_norm == 0.0:
        return B02StepAudit(
            ParameterUpdateAudit(0.0, 0.0, 0.0, False),
            measured_parameter_delta_norm=0.0,
        )
    multiplier = -nonzero_update_norm / raw_norm
    measured_sq = torch.zeros((), dtype=torch.float64)
    with torch.no_grad():
        for parameter in parameters:
            if parameter.grad is not None:
                grad64 = parameter.grad.detach().to(torch.float64)
                delta = multiplier * grad64
                measured_sq = measured_sq + delta.square().sum()
                parameter.add_(parameter.grad.to(parameter), alpha=multiplier)
    measured = float(torch.sqrt(measured_sq).item())
    return B02StepAudit(
        ParameterUpdateAudit(
            raw_gradient_norm=raw_norm,
            direction_norm=1.0,
            parameter_delta_norm=nonzero_update_norm,
            nonzero=True,
        ),
        measured_parameter_delta_norm=measured,
    )


def apply_b02_block_update(
    model: TBCFVModel,
    baselines: torch.Tensor,
    returns: torch.Tensor,
    cell_indices: torch.Tensor,
    nonzero_update_norm: float,
) -> B02BlockAudit:
    """Update parameters first and only then update all eight stopped baselines."""

    cells = _validated_block_cells(cell_indices)
    returns64 = returns.detach().to(torch.float64).reshape(-1)
    baseline8 = baselines.detach().to(torch.float64).reshape(-1)
    if returns64.numel() != TRAIN_EPISODES_PER_BLOCK or baseline8.numel() != TRAIN_CELLS:
        raise ValueError("returns must have 64 entries and baselines must have eight")
    step = fixed_norm_sgd_step(model, nonzero_update_norm)
    # This operation is intentionally below the joint parameter step.
    cell_means = torch.stack(
        [returns64[cells == cell].mean() for cell in range(TRAIN_CELLS)]
    )
    updated = BASELINE_DECAY * baseline8 + (1.0 - BASELINE_DECAY) * cell_means
    block = BlockUpdateAudit(
        parameter_update=step.audit, updated_baselines=updated.detach()
    )
    return B02BlockAudit(block=block, measured_parameter_delta_norm=step.measured_parameter_delta_norm)


def execute_b02_training_update(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    update: int,
    baselines: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, int], dict[str, object], bool]:
    results = []
    cells: list[int] = []
    for cell_start in range(0, len(TRAINING_CELLS), 4):
        selected = TRAINING_CELLS[cell_start : cell_start + 4]
        coordinates = tuple(
            EpisodeCoordinate(rng.block_index, cell, update, row)
            for cell in selected
            for row in range(8)
        )
        batch = execute_learned_batch(model, arm, rng, coordinates, training=True)
        results.extend(batch)
        for cell_index in range(cell_start, cell_start + len(selected)):
            cells.extend([cell_index] * 8)
    if len(results) != 64:
        raise RuntimeError("one B02 training update did not produce 64 episodes")
    returns = torch.tensor([item.Y for item in results], dtype=torch.float64)
    cell_indices = torch.tensor(cells, dtype=torch.int64)
    model.zero_grad(set_to_none=True)
    loss = exact_advantage_loss(
        returns,
        cell_indices,
        baselines,
        [torch.stack(item.plan_scores) for item in results],
        [torch.stack(item.claim_scores) for item in results],
    )
    if not bool(torch.isfinite(loss)):
        raise RuntimeError("training loss is nonfinite")
    loss.backward()
    b02_block = apply_b02_block_update(
        model, baselines, returns, cell_indices, NONZERO_UPDATE_NORM_B02
    )
    audit = b02_block.block
    per_cell = []
    for cell_index, cell in enumerate(TRAINING_CELLS):
        chosen = [results[row] for row in range(64) if cells[row] == cell_index]
        per_cell.append(
            {
                "cell": cell,
                "episodes": len(chosen),
                "Y_mean": _mean([float(item.Y) for item in chosen]),
                "tau_mean": _mean([float(item.tau) for item in chosen]),
                "U_mean": _mean([float(item.U) for item in chosen]),
                "F_mean": _mean([float(item.F) for item in chosen]),
            }
        )
    curve = {
        "update": update,
        "Y_mean": float(returns.mean().item()),
        "per_cell": per_cell,
        "nonzero": audit.parameter_update.nonzero,
        "parameter_delta_norm": audit.parameter_update.parameter_delta_norm,
        "measured_parameter_delta_norm": b02_block.measured_parameter_delta_norm,
        "raw_gradient_norm": audit.parameter_update.raw_gradient_norm,
        "event_order": list(audit.event_order),
    }
    counts = {
        "training_episodes": 64,
        "environment_ticks": 64 * 64,
        "agent_ticks": sum(item.agent_ticks for item in results),
        "agent_claim_decisions": sum(item.claim_decisions for item in results),
    }
    return audit.updated_baselines, counts, curve, audit.parameter_update.nonzero


def tag_init_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    tagged: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        item["arm"] = INIT_ARM
        item["source"] = INIT_SOURCE
        tagged.append(item)
    return tagged


def initialization_panel(
    model: TBCFVModel,
    rng: SemanticRNG,
    eval_episodes: int,
    started: float,
    wall_cap: float,
) -> tuple[list[dict[str, object]], list[str], dict[str, dict[str, object]], dict[str, object]]:
    rows, evaluated = evaluate_learned(
        model, C1P1, rng, eval_episodes, started=started, wall_cap=wall_cap
    )
    tagged = tag_init_rows(rows)
    cells = cell_endpoint_means(tagged)
    grouped = _group(tagged)
    path_u: dict[str, object] = {}
    for cell in PRIMARY_CELLS:
        items = grouped.get(cell, [])
        path_u[cell] = None if not items else _mean([float(item["U"]) for item in items])
    return tagged, evaluated, cells, path_u


def b02_configuration(
    *,
    updates: int,
    updates_completed: int,
    eval_episodes: int,
    wall_cap: float,
) -> dict[str, object]:
    return {
        "updates_requested": updates,
        "updates_completed": updates_completed,
        "eval_episodes_per_cell": eval_episodes,
        "heldout_cells": list(HELDOUT_CELLS),
        "training_cells": list(TRAINING_CELLS),
        "wall_cap": wall_cap,
        "nonzero_update_norm": NONZERO_UPDATE_NORM_B02,
        "previous_nonzero_update_norm": PREVIOUS_NONZERO_UPDATE_NORM,
        "step_law": STEP_LAW,
        "selection_history": SELECTION_HISTORY,
        "initial_parameter_norm_reference_b01": INITIAL_PARAMETER_NORM_REFERENCE_B01,
        "path_bound": PATH_BOUND,
    }


def b02_allocations() -> dict[str, object]:
    return {
        "package_models_allocated": list(LEARNED_PACKAGES),
        "package_models_allocated_count": len(LEARNED_PACKAGES),
        "training_instances": list(B01_ARMS),
        "training_instances_count": len(B01_ARMS),
    }


def load_and_validate_b02_control_summary(
    path: Path,
    *,
    updates: int,
    eval_episodes: int,
    block_digest: str,
) -> tuple[dict[str, object], dict[str, object]]:
    control = load_control_summary(path)
    identity = validate_control_summary(
        control,
        updates=updates,
        eval_episodes=eval_episodes,
        block_digest=block_digest,
        object_id=OBJECT_ID,
        seed=SEED,
    )
    identity["control_summary_path"] = str(path)
    panel = control.get("initialization_panel")
    if not isinstance(panel, Mapping):
        raise ValueError("control summary field initialization_panel is required")
    scenarios = panel.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError(
            "control summary field initialization_panel.scenarios is required"
        )
    return control, identity


def publish_b02_primary(
    init_rows: Sequence[Mapping[str, object]],
    treatment_rows: Sequence[Mapping[str, object]],
    flex_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    paired = publish_paired_primary(treatment_rows, flex_rows)
    init_grouped = _group(init_rows)
    treatment_grouped = _group(treatment_rows)
    u_ses: list[float | None] = []
    g_c1p1: list[float] = []
    g_flex: list[float] = []
    d_u: list[float] = []
    for path in paired["active_paths"]:
        cell = str(path["cell"])
        init_items = init_grouped[cell]
        left = treatment_grouped[cell]
        if [int(item["index"]) for item in init_items] != [
            int(item["index"]) for item in left
        ]:
            raise ValueError(f"init scenario indices differ on {cell}")
        init_u = _mean([float(item["U"]) for item in init_items])
        path["init_U_mean"] = init_u
        path["G_U_c1p1"] = init_u - float(path["c1p1_U_mean"])
        path["G_U_flex"] = init_u - float(path["flex_U_mean"])
        d_u.append(float(path["difference_U_flex_minus_c1p1"]))
        u_ses.append(path["paired_U_se"])  # type: ignore[arg-type]
        g_c1p1.append(float(path["G_U_c1p1"]))
        g_flex.append(float(path["G_U_flex"]))
    init_cells = cell_endpoint_means(init_rows)
    return {
        "active_paths": paired["active_paths"],
        "delta_U_b02": _mean(d_u),
        "delta_U_b02_se": se_of_mean_of_independent_ses(u_ses),
        "G_U_c1p1": _mean(g_c1p1),
        "G_U_flex": _mean(g_flex),
        "delta_tau_b02": paired["delta_tau_b01"],
        "delta_tau_b02_se": paired["delta_tau_b01_se"],
        "MEI_U": MEI_U,
        "MEI_tau_ticks": MEI_TAU_TICKS,
        "init_cells": init_cells,
        "c1p1_cells": paired["c1p1_cells"],
        "flex_cells": paired["flex_cells"],
        "init_eight_cell_mean": eight_cell_mean(init_cells),
        "c1p1_eight_cell_mean": paired["c1p1_eight_cell_mean"],
        "flex_eight_cell_mean": paired["flex_eight_cell_mean"],
        "sources": {
            "init": INIT_SOURCE,
            "C1P1": FINAL_SOURCE["C1P1"],
            "FLEX": FINAL_SOURCE["FLEX"],
            "reference": REFERENCE_SOURCE,
        },
    }


def publish_b02_primary_or_error(
    init_rows: Sequence[Mapping[str, object]],
    treatment_rows: Sequence[Mapping[str, object]],
    flex_rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object] | None, str | None]:
    try:
        if not init_rows:
            raise ValueError("init scenarios are empty")
        if not treatment_rows:
            raise ValueError("control scenarios are empty")
        if not flex_rows:
            raise ValueError("flex scenarios are empty")
        return publish_b02_primary(init_rows, treatment_rows, flex_rows), None
    except ArmWallExpired:
        raise
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def run_arm(
    *,
    arm: str,
    out: Path,
    updates: int,
    eval_episodes: int,
    wall_cap: float,
    admission_receipt: Path | None,
    launch_sha: str,
    control_summary: Path | None = None,
) -> dict[str, object]:
    if arm not in B01_ARMS:
        raise ValueError(f"B02 arm must be {B01_ARMS}, got {arm!r}")
    if arm == FLEX and control_summary is None:
        raise ValueError("FLEX requires --control-summary")
    current_digest = block_digest_hex(
        seed_root_key(SEED_KEY_ASCII), IDENTITY, BLOCK_INDEX
    )
    control_payload: dict[str, object] | None = None
    control_identity: dict[str, object] | None = None
    if arm == FLEX:
        assert control_summary is not None
        control_payload, control_identity = load_and_validate_b02_control_summary(
            Path(control_summary),
            updates=updates,
            eval_episodes=eval_episodes,
            block_digest=current_digest,
        )
    started = time.perf_counter()
    cpu0 = process_cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_b02_semantic_rng()
    allocated = initialize_block_models(rng)
    models = restrict_two_arms(allocated)
    model = models[arm]
    initial_norm = float(torch.linalg.vector_norm(flat_parameters(model)).item())
    initial = flat_parameters(model).clone()
    if arm == FLEX:
        other = models[C1P1]
        if not torch.equal(flat_parameters(model), flat_parameters(other)):
            raise RuntimeError("C1P1 and FLEX initial tensors differ")
    init_rows: list[dict[str, object]] = []
    init_evaluated: list[str] = []
    init_cells: dict[str, dict[str, object]] = {}
    init_path_u: dict[str, object] = {}
    baselines = torch.zeros(8, dtype=torch.float64)
    curves: list[dict[str, object]] = []
    zero_updates = 0
    nonzero_updates = 0
    status = "COMPLETE"
    stop_reason = None
    try:
        if arm == C1P1:
            check_wall(started, wall_cap)
            init_rows, init_evaluated, init_cells, init_path_u = initialization_panel(
                model, rng, eval_episodes, started, wall_cap
            )
            write_json(out / "init_scenarios.json", init_rows)
        for update in range(updates):
            check_wall(started, wall_cap)
            baselines, _counts, curve, nonzero = execute_b02_training_update(
                model, arm, rng, update, baselines
            )
            curves.append(curve)
            if nonzero:
                nonzero_updates += 1
            else:
                zero_updates += 1
        check_wall(started, wall_cap)
    except ArmWallExpired as exc:
        status = "TECHNICAL_STOP"
        stop_reason = "wall_cap"
        if arm == C1P1 and not init_rows:
            init_rows = tag_init_rows(list(exc.evaluated_rows))
            init_evaluated = list(exc.evaluated_cells)
            init_cells = cell_endpoint_means(init_rows) if init_rows else {}
            grouped = _group(init_rows) if init_rows else {}
            init_path_u = {
                cell: None
                if cell not in grouped
                else _mean([float(item["U"]) for item in grouped[cell]])
                for cell in PRIMARY_CELLS
            }
            write_json(out / "init_scenarios.json", init_rows)
    displacement = float(
        torch.linalg.vector_norm(flat_parameters(model) - initial).item()
    )

    def initialization_panel_body() -> dict[str, object]:
        if arm == FLEX and isinstance(control_payload, Mapping):
            panel = control_payload.get("initialization_panel")
            if isinstance(panel, Mapping):
                return dict(panel)
        return {
            "arm": INIT_ARM,
            "source": INIT_SOURCE,
            "scenarios": init_rows,
            "cells": init_cells,
            "eight_cell_mean": eight_cell_mean(init_cells) if init_cells else None,
            "path_U_means": init_path_u,
            "evaluated_cells": init_evaluated,
        }

    def snapshot(
        *,
        status_value: str,
        stop: str | None,
        scenarios_value: list[dict[str, object]],
        evaluated: list[str],
        paired_value: object,
        paired_error_value: str | None,
        wall: float,
    ) -> dict[str, object]:
        cells = cell_endpoint_means(scenarios_value) if scenarios_value else {}
        body: dict[str, object] = {
            "object": OBJECT_ID,
            "status": status_value,
            "stop_reason": stop,
            "arm": arm,
            "seed": SEED,
            "identity": IDENTITY,
            "root_key_hex": seed_root_key(SEED_KEY_ASCII).hex(),
            "block_digest_hex": authority.root_digest,
            "native": authority.certificate["native"],
            "configuration": b02_configuration(
                updates=updates,
                updates_completed=len(curves),
                eval_episodes=eval_episodes,
                wall_cap=wall_cap,
            ),
            "allocations": b02_allocations(),
            "initialization_panel": initialization_panel_body(),
            "counts": {
                "completed_updates": len(curves),
                "zero_update_incidence": zero_updates,
                "nonzero_update_count": nonzero_updates,
                "heldout_scenarios": len(scenarios_value),
            },
            "evaluated_cells": evaluated,
            "initial_parameter_norm": initial_norm,
            "final_displacement": displacement,
            "curves": curves,
            "display_points": [
                row for row in curves if int(row["update"]) % 25 == 0  # type: ignore[arg-type]
            ],
            "scenarios": scenarios_value,
            "cells": cells,
            "eight_cell_mean": eight_cell_mean(cells) if cells else None,
            "paired_primary": paired_value,
            "paired_primary_error": paired_error_value,
            "cost_law": cost_law(updates, eval_episodes),
            "wall_seconds": wall,
            "process_cpu_seconds": process_cpu_seconds() - cpu0,
            "peak_rss_bytes": peak_rss_bytes(),
            "scratch_bytes": None,
            "admission_receipt": None if admission_receipt is None else str(admission_receipt),
            "launch_sha": launch_sha,
        }
        if control_identity is not None:
            body.update(control_identity)
        return body

    torch.save(model.state_dict(), out / "parameters.pt")
    write_json(
        out / "summary.json",
        snapshot(
            status_value="TRAINED_UNEVALUATED",
            stop=None,
            scenarios_value=[],
            evaluated=[],
            paired_value=None,
            paired_error_value=None,
            wall=time.perf_counter() - started,
        ),
    )
    scenarios: list[dict[str, object]] = []
    evaluated_cells: list[str] = []
    if status == "COMPLETE":
        try:
            scenarios, evaluated_cells = evaluate_learned(
                model,
                arm,
                rng,
                eval_episodes,
                started=started,
                wall_cap=wall_cap,
            )
        except ArmWallExpired as exc:
            status = "TECHNICAL_STOP"
            stop_reason = "wall_cap"
            scenarios = list(exc.evaluated_rows)
            evaluated_cells = list(exc.evaluated_cells)
        else:
            try:
                check_wall(started, wall_cap)
            except ArmWallExpired:
                status = "TECHNICAL_STOP"
                stop_reason = "wall_cap"
    paired = None
    paired_error = None
    if arm == FLEX:
        control_rows: list[Mapping[str, object]] = []
        init_for_publish: list[Mapping[str, object]] = []
        if isinstance(control_payload, Mapping):
            raw_rows = control_payload.get("scenarios", [])
            if isinstance(raw_rows, list):
                control_rows = raw_rows
            panel = control_payload.get("initialization_panel")
            if isinstance(panel, Mapping):
                raw_init = panel.get("scenarios", [])
                if isinstance(raw_init, list):
                    init_for_publish = raw_init
        paired, paired_error = publish_b02_primary_or_error(
            init_for_publish, control_rows, scenarios
        )
    wall = time.perf_counter() - started
    summary = snapshot(
        status_value=status,
        stop=stop_reason,
        scenarios_value=scenarios,
        evaluated=evaluated_cells,
        paired_value=paired,
        paired_error_value=paired_error,
        wall=wall,
    )
    torch.save(model.state_dict(), out / "parameters.pt")
    write_json(out / "summary.json", summary)
    summary["scratch_bytes"] = directory_bytes(out)
    write_json(out / "summary.json", summary)
    return summary


def run_reference(
    *,
    out: Path,
    eval_episodes: int,
    admission_receipt: Path | None,
    launch_sha: str,
) -> dict[str, object]:
    started = time.perf_counter()
    cpu0 = process_cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_b02_semantic_rng()
    scenarios = evaluate_scripted(rng, eval_episodes)
    tagged = []
    for row in scenarios:
        item = dict(row)
        item["source"] = REFERENCE_SOURCE
        tagged.append(item)
    cells = cell_endpoint_means(tagged)
    summary = {
        "object": OBJECT_ID,
        "status": "COMPLETE",
        "arm": INDEPENDENT_NEAREST,
        "seed": SEED,
        "identity": IDENTITY,
        "root_key_hex": seed_root_key(SEED_KEY_ASCII).hex(),
        "block_digest_hex": authority.root_digest,
        "native": authority.certificate["native"],
        "configuration": {
            "eval_episodes_per_cell": eval_episodes,
            "heldout_cells": list(HELDOUT_CELLS),
        },
        "scenarios": tagged,
        "cells": cells,
        "eight_cell_mean": eight_cell_mean(cells),
        "wall_seconds": time.perf_counter() - started,
        "process_cpu_seconds": process_cpu_seconds() - cpu0,
        "peak_rss_bytes": peak_rss_bytes(),
        "scratch_bytes": None,
        "admission_receipt": None if admission_receipt is None else str(admission_receipt),
        "launch_sha": launch_sha,
        "Y_note": "ScriptedEpisodeResult has no Y; rows store Y as null",
        "source": REFERENCE_SOURCE,
    }
    write_json(out / "summary.json", summary)
    summary["scratch_bytes"] = directory_bytes(out)
    write_json(out / "summary.json", summary)
    return summary
