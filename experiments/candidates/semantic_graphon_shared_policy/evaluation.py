from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

import numpy as np
import torch

from .authorization import ProductionPermit
from .config import ALL_SIZES, ARMS, EDGE_ARMS, HELDOUT_SIZES, REGIMES, REGISTERED
from .policies import SharedSGSPPolicy, actions_from_uniforms
from .rng import forced_nonidentity_audit_permutation
from .world import World, generate_world, team_return


def cell_key(n: int, regime: str) -> str:
    return f"N={n}|regime={regime}"


def _run_policy(
    model: SharedSGSPPolicy,
    world: World,
    uniforms: np.ndarray,
    sender_roles_override: np.ndarray | None = None,
    center_swap: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    messages = torch.from_numpy(world.x.copy()).to(torch.float64)
    receiver_roles = torch.from_numpy(world.roles.copy()).to(torch.int64)
    override = None if sender_roles_override is None else torch.from_numpy(
        sender_roles_override.copy()
    ).to(torch.int64)
    uniform_tensor = torch.from_numpy(uniforms.copy()).to(torch.float64)
    with torch.no_grad():
        output = model(messages, receiver_roles, override, center_swap=center_swap)
        actions = actions_from_uniforms(output.probabilities, uniform_tensor)
    return (
        output.logits.cpu().numpy(),
        output.probabilities.cpu().numpy(),
        actions.cpu().numpy(),
    )


def _identity_replay(
    model: SharedSGSPPolicy,
    world: World,
    uniforms: np.ndarray,
    permutation: np.ndarray,
    canonical_logits: np.ndarray,
    canonical_actions: np.ndarray,
    sender_roles_override: np.ndarray | None = None,
    center_swap: bool = False,
) -> tuple[float, bool, bool]:
    permuted_world = world.permuted(permutation)
    permuted_override = (
        None if sender_roles_override is None else sender_roles_override[permutation]
    )
    replay_logits, _, replay_actions = _run_policy(
        model,
        permuted_world,
        uniforms[permutation],
        permuted_override,
        center_swap,
    )
    inverse = np.argsort(permutation)
    restored_logits = replay_logits[inverse]
    restored_actions = replay_actions[inverse]
    error = float(np.max(np.abs(canonical_logits - restored_logits)))
    actions_equal = bool(np.array_equal(canonical_actions, restored_actions))
    returns_equal = team_return(canonical_actions, world.targets) == team_return(
        restored_actions, world.targets
    )
    return error, actions_equal, returns_equal


def evaluate_seed(
    permit: ProductionPermit, seed: int, models: dict[str, SharedSGSPPolicy],
    progress_guard: Callable[[], None] | None = None,
) -> dict[str, object]:
    permit.require_seed(seed)
    for model in models.values():
        model.eval()
    cells: dict[str, object] = {}
    global_min_probability = 1.0
    global_max_probability = 0.0
    global_finite = True
    global_identity_error = 0.0
    global_actions_equal = True
    global_returns_equal = True

    for n in ALL_SIZES:
        for regime in REGIMES:
            intact_returns: dict[str, list[float]] = defaultdict(list)
            reassociation_returns: dict[str, list[float]] = defaultdict(list)
            reassociation_tvs: dict[str, list[float]] = defaultdict(list)
            center_swap_returns: list[float] = []
            center_swap_tvs: list[float] = []
            tv_support_caps: list[float] = []
            upper_correct = 0
            lower_correct = 0
            observations = 0
            panel_identity: dict[str, dict[str, object]] = {}

            def record_identity(name: str, result: tuple[float, bool, bool]) -> None:
                nonlocal global_identity_error, global_actions_equal, global_returns_equal
                error, actions_equal, returns_equal = result
                current = panel_identity.setdefault(name, {
                    "max_abs_logit_error": 0.0,
                    "inverse_permuted_actions_equal": True,
                    "team_return_equal": True,
                })
                current["max_abs_logit_error"] = max(
                    float(current["max_abs_logit_error"]), error
                )
                current["inverse_permuted_actions_equal"] = bool(
                    current["inverse_permuted_actions_equal"] and actions_equal
                )
                current["team_return_equal"] = bool(
                    current["team_return_equal"] and returns_equal
                )
                global_identity_error = max(global_identity_error, error)
                global_actions_equal = global_actions_equal and actions_equal
                global_returns_equal = global_returns_equal and returns_equal

            for episode in range(REGISTERED.eval_worlds_per_cell):
                if progress_guard is not None:
                    progress_guard()
                world = generate_world(permit, "evaluation", seed, n, regime, episode)
                uniforms = world.action_uniforms(permit)
                permutation = forced_nonidentity_audit_permutation(
                    permit, seed, n, regime, episode,
                )
                targets = world.targets
                upper_correct += int(np.sum(
                    np.where(targets == 1, uniforms < 0.98, uniforms >= 0.02)
                ))
                lower_correct += int(np.sum(
                    np.where(targets == 1, uniforms < 0.02, uniforms >= 0.98)
                ))
                observations += n

                intact_outputs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
                for arm in ARMS:
                    logits, probabilities, actions = _run_policy(models[arm], world, uniforms)
                    intact_outputs[arm] = (logits, probabilities, actions)
                    intact_returns[arm].append(team_return(actions, targets))
                    global_min_probability = min(
                        global_min_probability, float(probabilities.min())
                    )
                    global_max_probability = max(
                        global_max_probability, float(probabilities.max())
                    )
                    global_finite = global_finite and bool(
                        np.isfinite(logits).all() and np.isfinite(probabilities).all()
                    )
                    record_identity(
                        f"{arm}|intact",
                        _identity_replay(
                            models[arm], world, uniforms, permutation, logits, actions,
                        ),
                    )

                if n in HELDOUT_SIZES and regime == "OPPOSED":
                    sgsp_probabilities = intact_outputs["SGSP-W"][1]
                    tv_support_caps.append(float(np.mean(np.maximum(
                        sgsp_probabilities[:, 1] - REGISTERED.support_floor,
                        REGISTERED.support_ceiling - sgsp_probabilities[:, 1],
                    ), dtype=np.float64)))
                    reassociated_roles = 1 - world.roles
                    for arm in EDGE_ARMS:
                        logits, probabilities, actions = _run_policy(
                            models[arm], world, uniforms, reassociated_roles,
                        )
                        reassociation_returns[arm].append(team_return(actions, targets))
                        reassociation_tvs[arm].append(float(np.mean(np.abs(
                            intact_outputs[arm][1][:, 1] - probabilities[:, 1]
                        ), dtype=np.float64)))
                        record_identity(
                            f"{arm}|sender_reassociation",
                            _identity_replay(
                                models[arm], world, uniforms, permutation, logits, actions,
                                reassociated_roles,
                            ),
                        )

                    swap_logits, swap_probabilities, swap_actions = _run_policy(
                        models["SGSP-W"], world, uniforms, center_swap=True,
                    )
                    center_swap_returns.append(team_return(swap_actions, targets))
                    center_swap_tvs.append(float(np.mean(np.abs(
                        intact_outputs["SGSP-W"][1][:, 1] - swap_probabilities[:, 1]
                    ), dtype=np.float64)))
                    record_identity(
                        "SGSP-W|center_swap",
                        _identity_replay(
                            models["SGSP-W"], world, uniforms, permutation,
                            swap_logits, swap_actions, center_swap=True,
                        ),
                    )

            intact_work = {
                arm: SharedSGSPPolicy.output_relevant_work(n, regime, "intact")
                for arm in EDGE_ARMS
            }
            common_replay_work = {
                "identity": {
                    arm: SharedSGSPPolicy.output_relevant_work(n, regime, "identity")
                    for arm in EDGE_ARMS
                }
            }
            if n in HELDOUT_SIZES and regime == "OPPOSED":
                common_replay_work["sender_reassociation"] = {
                    arm: SharedSGSPPolicy.output_relevant_work(
                        n, regime, "sender_reassociation"
                    ) for arm in EDGE_ARMS
                }
            cells[cell_key(n, regime)] = {
                "n": n,
                "regime": regime,
                "world_count": REGISTERED.eval_worlds_per_cell,
                "mean_intact_return": {
                    arm: float(np.mean(intact_returns[arm], dtype=np.float64)) for arm in ARMS
                },
                "mean_sender_reassociation_return": {
                    arm: float(np.mean(reassociation_returns[arm], dtype=np.float64))
                    for arm in EDGE_ARMS if reassociation_returns[arm]
                },
                "mean_sender_reassociation_tv": {
                    arm: float(np.mean(reassociation_tvs[arm], dtype=np.float64))
                    for arm in EDGE_ARMS if reassociation_tvs[arm]
                },
                "mean_sgsp_center_swap_return": (
                    float(np.mean(center_swap_returns, dtype=np.float64))
                    if center_swap_returns else None
                ),
                "mean_sgsp_center_swap_tv": (
                    float(np.mean(center_swap_tvs, dtype=np.float64))
                    if center_swap_tvs else None
                ),
                "mean_sgsp_tv_support_cap": (
                    float(np.mean(tv_support_caps, dtype=np.float64))
                    if tv_support_caps else None
                ),
                "sampled_return_envelope": {
                    "upper": upper_correct / float(observations),
                    "lower": lower_correct / float(observations),
                },
                "identity_replay_by_panel": panel_identity,
                "intact_edge_arm_work": intact_work,
                "intact_edge_arm_work_exactly_equal": len({
                    repr(intact_work[arm]) for arm in EDGE_ARMS
                }) == 1,
                "intact_edge_arm_work_ratio_to_sgsp": {
                    arm: 1 for arm in EDGE_ARMS
                },
                "common_structural_replay_work": common_replay_work,
                "common_structural_replay_work_exactly_equal": all(
                    len({repr(by_arm[arm]) for arm in EDGE_ARMS}) == 1
                    for by_arm in common_replay_work.values()
                ),
                "common_structural_replay_work_ratio_to_sgsp": {
                    panel: {arm: 1 for arm in EDGE_ARMS}
                    for panel in common_replay_work
                },
                "sgsp_center_swap_work_separate_post_training_ledger": (
                    SharedSGSPPolicy.output_relevant_work(n, regime, "center_swap")
                    if n in HELDOUT_SIZES and regime == "OPPOSED" else None
                ),
            }

    return {
        "seed": seed,
        "cells": cells,
        "common_support": {
            "minimum_probability": global_min_probability,
            "maximum_probability": global_max_probability,
            "finite_logits_and_probabilities": global_finite,
            "floor_pass": global_min_probability >= REGISTERED.support_floor,
            "ceiling_pass": global_max_probability <= REGISTERED.support_ceiling,
        },
        "identity_replay": {
            "max_abs_logit_error": global_identity_error,
            "max_error_pass": global_identity_error <= REGISTERED.permutation_tolerance,
            "inverse_permuted_actions_equal": global_actions_equal,
            "team_return_equal": global_returns_equal,
            "one_permutation_reused_across_arms_and_panels_per_world": True,
        },
    }
