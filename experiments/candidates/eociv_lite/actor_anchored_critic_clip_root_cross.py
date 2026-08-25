"""EOCIV-B6 actor-anchored critic-clip/root-cross discriminator.

The production entry implements the frozen matched training, retained-state
diagnostic panel and natural-prior evaluation.  It reuses the real B4/B5
environment, receipt, latch and GAE paths; all new state and gradient behavior
is candidate-local.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import actor_anchored_gradient_geometry as geom
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import host_reward_snr_discrimination as b5
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import recurrent_retention_learnability as b4
from experiments.candidates.eociv_lite import sibling_env as sib


TREATMENT = "EOCIV-B6-ACTOR-ANCHORED-CRITIC-CLIP-ROOT-CROSS-DISCRIMINATOR"
CONDITIONS = ("JOINT_GLOBAL_CLIP", "ACTOR_ANCHORED_CRITIC_CLIP")
STATE_LEVELS = ("INIT", "BASELINE_FINAL", "TREATMENT_FINAL")
ACTOR_SEEDS = (87031, 87032, 87033)
PROFILES = b1.PROFILES
EVALUATION_ARMS = b2.EVALUATION_ARMS
CRITICAL_TUPLES = b5.CRITICAL_TUPLES
BLOCK_SIZE = 4
TRAIN_EPISODE_BASE = 18_000_000
HELDOUT_EPISODE_BASE = 19_000_000
DIAGNOSTIC_TAPE_BASE = 19_900_000
TERMINALS = (
    "OPTIMIZER_TREATMENT_IMPROVES_STABLE_SEMANTICS",
    "PUBLIC_ROOT_VARIABILITY_DOMINATES",
    "BOTH_MATTER",
    "NEITHER_SUPPORTED",
    "INTERVENTION_FAILURE",
    "UNIDENTIFIED",
)


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    actor_seeds: tuple[int, ...]
    profiles: tuple[roster_env.RosterProfile, ...]
    training_roots_per_profile: int
    heldout_roots_per_profile: int
    horizon: int = roster_env.HORIZON

    @property
    def trained_actors(self) -> int:
        return len(CONDITIONS) * len(self.actor_seeds)

    @property
    def optimizer_updates(self) -> int:
        return self.trained_actors * len(self.profiles) * self.training_roots_per_profile

    @property
    def training_episodes(self) -> int:
        return self.optimizer_updates * BLOCK_SIZE

    @property
    def retained_states(self) -> int:
        return len(self.actor_seeds) * len(STATE_LEVELS)

    @property
    def diagnostic_episodes(self) -> int:
        return self.retained_states * len(self.profiles) * self.heldout_roots_per_profile * len(CRITICAL_TUPLES)

    @property
    def evaluation_episodes(self) -> int:
        return self.retained_states * len(self.profiles) * self.heldout_roots_per_profile * len(EVALUATION_ARMS)

    @property
    def total_episodes(self) -> int:
        return self.training_episodes + self.diagnostic_episodes + self.evaluation_episodes

    @property
    def total_transitions(self) -> int:
        return self.total_episodes * self.horizon


FULL_PLAN = ExperimentPlan("full", ACTOR_SEEDS, PROFILES, 8, 3)
SMOKE_PLAN = ExperimentPlan("smoke", ACTOR_SEEDS[:1], PROFILES[:1], 1, 1)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "full":
        return FULL_PLAN
    if mode == "smoke":
        return SMOKE_PLAN
    raise ValueError("mode must be smoke or full")


def _assert_plan_constants() -> None:
    if (
        FULL_PLAN.training_episodes,
        FULL_PLAN.diagnostic_episodes,
        FULL_PLAN.evaluation_episodes,
        FULL_PLAN.total_episodes,
        FULL_PLAN.total_transitions,
        FULL_PLAN.optimizer_updates,
        FULL_PLAN.trained_actors,
        FULL_PLAN.retained_states,
    ) != (576, 324, 243, 1_143, 54_864, 144, 6, 9):
        raise RuntimeError("registered B6 full plan drifted")
    if (
        SMOKE_PLAN.training_episodes,
        SMOKE_PLAN.diagnostic_episodes,
        SMOKE_PLAN.evaluation_episodes,
        SMOKE_PLAN.total_episodes,
        SMOKE_PLAN.total_transitions,
        SMOKE_PLAN.optimizer_updates,
    ) != (8, 12, 9, 29, 1_392, 2):
        raise RuntimeError("registered B6 smoke plan drifted")


def training_episode_id(seed_index: int, profile_index: int, root: int) -> int:
    if min(seed_index, profile_index, root) < 0:
        raise ValueError("negative training coordinate")
    return TRAIN_EPISODE_BASE + seed_index * 100_000 + profile_index * 10_000 + root


def heldout_episode_id(profile_index: int, root: int) -> int:
    if min(profile_index, root) < 0:
        raise ValueError("negative heldout coordinate")
    return HELDOUT_EPISODE_BASE + profile_index * 10_000 + root


def diagnostic_tape_identity(profile_index: int) -> int:
    if profile_index < 0:
        raise ValueError("negative tape coordinate")
    return DIAGNOSTIC_TAPE_BASE + profile_index


def _new_actor(seed: int) -> b1.RecurrentActorCritic:
    return b1.RecurrentActorCritic(PROFILES[0].member_capacity, seed, encoder_kind="content_separating")


def _new_optimizer(actor: b1.RecurrentActorCritic) -> torch.optim.Adam:
    optimizer = torch.optim.Adam(actor.parameters(), lr=b1.ACTOR_LR)
    geom.materialize_zero_adam(optimizer)
    return optimizer


def _state_identity(actor: b1.RecurrentActorCritic, optimizer: torch.optim.Adam) -> dict[str, Any]:
    parameters = geom.serialize_parameter_state(actor)
    moments = geom.serialize_optimizer_state(actor, optimizer)
    return {
        "parameter_state_sha256": parameters["state_sha256"],
        "optimizer_state_sha256": moments["state_sha256"],
        "layout_sha256": parameters["layout_sha256"],
    }


def _retained_state(
    actor: b1.RecurrentActorCritic,
    optimizer: torch.optim.Adam,
    *,
    seed: int,
    level: str,
    condition: str,
) -> dict[str, Any]:
    return {
        "actor_seed": seed,
        "state_level": level,
        "condition": condition,
        "parameters": geom.serialize_parameter_state(actor),
        "optimizer": geom.serialize_optimizer_state(actor, optimizer),
        "identity": _state_identity(actor, optimizer),
    }


def _diagnostic_tape(profile: roster_env.RosterProfile, profile_index: int) -> tuple[np.ndarray, dict[str, Any]]:
    identity = diagnostic_tape_identity(profile_index)
    action_seed = sib.profile_stream_identity(sib.ACTION_NOISE_STREAM, art.ACTION_NOISE_SEED, profile.name)
    tape = roster_env.make_action_noise([identity], action_seed=action_seed, member_capacity=profile.member_capacity)[:, 0, :, :]
    raw = np.ascontiguousarray(tape).tobytes()
    return tape, {
        "profile": profile.name,
        "tape_identity": identity,
        "action_seed_identity": action_seed,
        "dtype": str(tape.dtype),
        "shape": list(tape.shape),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes_base64": __import__("base64").b64encode(raw).decode("ascii"),
    }


def _runner(
    actor: b1.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    episode_id: int,
    body_fn,
    *,
    shock_tuple: tuple[str, str] | None,
    noise: np.ndarray | None,
) -> b4.RetentionEpisodeRunner:
    env = b5._make_env(profile, episode_id, shock_tuple)
    policy = b4.RetentionPolicy(actor, "SEGMENT_LATCH_RNN")
    runner = b4.RetentionEpisodeRunner(env, "LR", tape_seed=b1.TAPE_SEED, d_learned_fn=lambda _: True, body_fn=body_fn, policy=policy)
    if noise is not None:
        supplied = np.asarray(noise, dtype=np.float32)
        if supplied.shape != runner.noise.shape:
            raise RuntimeError("B6 supplied tape shape mismatch")
        runner.noise = supplied.copy()
    runner.run_episode()
    return runner


def _four_episode_gradients(
    actor: b1.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    episode_id: int,
    noise: np.ndarray | None = None,
) -> tuple[torch.Tensor, torch.Tensor, list[dict[str, Any]]]:
    actor_losses, critic_losses, rows = [], [], []
    actor.set_capture(True)
    for shock_index, shock_tuple in enumerate(CRITICAL_TUPLES):
        runner = _runner(actor, profile, episode_id, b2._correct_body, shock_tuple=shock_tuple, noise=noise)
        actor_loss, critic_loss, diagnostics = b5._episode_loss_tensors(actor, runner.env.reward_trace)
        actor_losses.append(actor_loss)
        critic_losses.append(critic_loss)
        rows.append({
            "shock_index": shock_index, "critical_shock_tuple": list(shock_tuple),
            "episode_id": episode_id, "episode_return": float(sum(runner.env.reward_trace)),
            "public_world_digest": b5.public_world_digest(runner.env),
            "lifecycle_digest": b5.lifecycle_digest(runner),
            "action_noise_tape_digest": b5.action_noise_digest(runner),
            "accepted_boundary_ticks": list(runner.accepted_boundary_ticks),
            **diagnostics,
        })
    parameters = tuple(actor.parameters())
    actor_vector, critic_vector = geom.actor_critic_vectors(torch.stack(actor_losses).mean(), torch.stack(critic_losses).mean(), actor)
    actor.set_capture(False)
    # Release the last captured recurrent graph before the result row is
    # retained. Only detached vectors and scalar diagnostics survive.
    actor.initial_state()
    if len({row["public_world_digest"] for row in rows}) != 1 or len({row["lifecycle_digest"] for row in rows}) != 1 or len({row["action_noise_tape_digest"] for row in rows}) != 1:
        raise RuntimeError("B6 four-stratum matching failed")
    if any(parameter.grad is not None for parameter in parameters):
        raise RuntimeError("B6 gradient extraction polluted .grad")
    return actor_vector, critic_vector, rows


def _train_condition(
    actor: b1.RecurrentActorCritic,
    optimizer: torch.optim.Adam,
    condition: str,
    seed: int,
    seed_index: int,
    plan: ExperimentPlan,
) -> list[dict[str, Any]]:
    rows = []
    for root in range(plan.training_roots_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            episode = training_episode_id(seed_index, profile_index, root)
            pre_step_identity = _state_identity(actor, optimizer)
            a, v, episodes = _four_episode_gradients(actor, profile, episode)
            rule = geom.intervention_vectors(a, v)
            selected = rule["baseline"] if condition == CONDITIONS[0] else rule["treatment"]
            realized = geom.assign_gradient_vector(actor, selected)
            if not torch.equal(realized, selected.to(torch.float32).to(torch.float64)):
                raise RuntimeError("B6 selected gradient was not realized")
            optimizer.step()
            post_step_identity = _state_identity(actor, optimizer)
            optimizer.zero_grad(set_to_none=True)
            rows.append({
                "condition": condition, "actor_seed": seed, "profile": profile.name,
                "root": root, "order_index": len(rows), "update": len(rows)+1,
                "episode_id": episode, "shock_tuples": [list(value) for value in CRITICAL_TUPLES],
                "episodes": episodes,
                "actor_norm": rule["actor_norm"], "critic_norm": rule["critic_norm"],
                "actor_critic_cross": float(torch.dot(a, v)), "alpha": rule["alpha"],
                "baseline_pre_norm": rule["baseline_pre_norm"], "treatment_pre_norm": rule["treatment_pre_norm"],
                "baseline_final_scale": rule["baseline_final_scale"], "treatment_final_scale": rule["treatment_final_scale"],
                "selected_final_norm": geom.l2_norm(realized),
                "intervention_constraint_passed": geom.l2_norm(rule["alpha"] * v) <= min(rule["actor_norm"], b1.GRAD_NORM_CAP) + 1e-12,
                "pre_step_state_identity": pre_step_identity,
                "post_step_state_identity": post_step_identity,
            })
    return rows


def _matching_training(baseline: Sequence[Mapping[str, Any]], treatment: Sequence[Mapping[str, Any]], plan: ExperimentPlan) -> dict[str, bool]:
    expected_order = [(root, profile.name) for root in range(plan.training_roots_per_profile) for profile in plan.profiles]
    return {
        "root_major_profile_interleaved": [(row["root"], row["profile"]) for row in baseline] == expected_order == [(row["root"], row["profile"]) for row in treatment],
        "same_episode_ids": [row["episode_id"] for row in baseline] == [row["episode_id"] for row in treatment],
        "same_public_world": [[x["public_world_digest"] for x in row["episodes"]] for row in baseline] == [[x["public_world_digest"] for x in row["episodes"]] for row in treatment],
        "same_lifecycle": [[x["lifecycle_digest"] for x in row["episodes"]] for row in baseline] == [[x["lifecycle_digest"] for x in row["episodes"]] for row in treatment],
        "same_action_noise": [[x["action_noise_tape_digest"] for x in row["episodes"]] for row in baseline] == [[x["action_noise_tape_digest"] for x in row["episodes"]] for row in treatment],
        "exact_four_strata": all(row["shock_tuples"] == [list(value) for value in CRITICAL_TUPLES] for row in (*baseline, *treatment)),
    }


def _probe_state(
    actor: b1.RecurrentActorCritic,
    optimizer: torch.optim.Adam,
    state_meta: Mapping[str, Any],
    profile: roster_env.RosterProfile,
    profile_index: int,
    root: int,
    tape: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before = _state_identity(actor, optimizer)
    layout = geom.ordered_layout(actor)
    cells, avectors, cvectors = [], {}, {}
    for shock_index, shock_tuple in enumerate(CRITICAL_TUPLES):
        actor.set_capture(True)
        runner = _runner(actor, profile, heldout_episode_id(profile_index, root), b2._correct_body, shock_tuple=shock_tuple, noise=tape)
        aloss, closs, diagnostics = b5._episode_loss_tensors(actor, runner.env.reward_trace)
        a, v = geom.actor_critic_vectors(aloss, closs, actor)
        actor.set_capture(False)
        rule = geom.intervention_vectors(a, v)
        avectors[shock_index], cvectors[shock_index] = a, v
        cells.append({
            **state_meta, "profile": profile.name, "root": root, "shock_index": shock_index,
            "source_state_identity": before,
            "critical_shock_tuple": list(shock_tuple), "episode_id": heldout_episode_id(profile_index, root),
            "public_world_digest": b5.public_world_digest(runner.env), "lifecycle_digest": b5.lifecycle_digest(runner),
            "action_noise_tape_digest": b5.action_noise_digest(runner), "episode_return": float(sum(runner.env.reward_trace)),
            "actor_vector": geom.vector_record("actor", a), "critic_vector": geom.vector_record("half_critic", v),
            "geometry": geom.energy_identity(a, v, layout),
            "alpha": rule["alpha"], "actor_norm": rule["actor_norm"], "critic_norm": rule["critic_norm"],
            "baseline_pre_norm": rule["baseline_pre_norm"], "treatment_pre_norm": rule["treatment_pre_norm"],
            "baseline_final_scale": rule["baseline_final_scale"], "treatment_final_scale": rule["treatment_final_scale"],
            "diagnostics": diagnostics,
        })
    amean = torch.stack(list(avectors.values())).mean(0)
    cmean = torch.stack(list(cvectors.values())).mean(0)
    rules = geom.intervention_vectors(amean, cmean)
    baseline_delta = geom.copied_adam_next_delta(actor, optimizer, rules["baseline"])
    treatment_delta = geom.copied_adam_next_delta(actor, optimizer, rules["treatment"])
    after = _state_identity(actor, optimizer)
    if before != after or any(parameter.grad is not None for parameter in actor.parameters()):
        raise RuntimeError("B6 no-step probe mutated checkpoint or gradients")
    aggregate = {
        **state_meta, "profile": profile.name, "root": root,
        "actor_mean_vector": geom.vector_record("actor_mean", amean),
        "critic_mean_vector": geom.vector_record("half_critic_mean", cmean),
        "baseline": geom.projection_diagnostics(amean, baseline_delta, layout),
        "treatment": geom.projection_diagnostics(amean, treatment_delta, layout),
        "raw_baseline_actor_projection": float(torch.dot(rules["baseline"], amean)),
        "raw_treatment_actor_projection": float(torch.dot(rules["treatment"], amean)),
        "raw_projection_increase": float(torch.dot(rules["treatment"]-rules["baseline"], amean)),
        "projection_increase": geom.projection_diagnostics(amean, treatment_delta, layout)["negative_delta_actor_projection"] - geom.projection_diagnostics(amean, baseline_delta, layout)["negative_delta_actor_projection"],
        "state_identity_before": before, "state_identity_after": after,
    }
    return cells, aggregate


def _summary(values: Sequence[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise RuntimeError("summary requires finite nonempty values")
    return {"values": [float(v) for v in values], "count": int(array.size), "mean": float(array.mean()), "minimum": float(array.min()), "maximum": float(array.max())}


def _semantic_summaries(rows: Sequence[Mapping[str, Any]], plan: ExperimentPlan) -> dict[str, Any]:
    index = {(int(r["actor_seed"]), str(r["state_level"]), str(r["profile"]), int(r["root"])): r for r in rows}
    cells = []
    for seed in plan.actor_seeds:
        for profile in plan.profiles:
            for root in range(plan.heldout_roots_per_profile):
                base = index[(seed, "BASELINE_FINAL", profile.name, root)]
                treat = index[(seed, "TREATMENT_FINAL", profile.name, root)]
                cells.append({
                    "actor_seed": seed, "profile": profile.name, "root": root,
                    "correct_minus_swapped": float(treat["contrasts"]["correct_minus_swapped"] - base["contrasts"]["correct_minus_swapped"]),
                    "correct_minus_native_neutral": float(treat["contrasts"]["correct_minus_native_neutral"] - base["contrasts"]["correct_minus_native_neutral"]),
                    "absolute_correct": float(treat["arms"]["CORRECT"] - base["arms"]["CORRECT"]),
                })
    fields = ("correct_minus_swapped", "correct_minus_native_neutral", "absolute_correct")
    seed_aggregates = [{"actor_seed": seed, **{field: float(np.mean([r[field] for r in cells if r["actor_seed"] == seed])) for field in fields}} for seed in plan.actor_seeds]
    grand = {field: float(np.mean([r[field] for r in cells])) for field in fields}
    lop = [{"left_out_profile": profile.name, **{field: float(np.mean([r[field] for r in cells if r["profile"] != profile.name])) for field in fields}} for profile in plan.profiles] if len(plan.profiles)>1 else []
    lor = [{"left_out_root": root, **{field: float(np.mean([r[field] for r in cells if r["root"] != root])) for field in fields}} for root in range(plan.heldout_roots_per_profile)] if plan.heldout_roots_per_profile>1 else []
    return {"cells": cells, "seed_aggregates": seed_aggregates, "grand": grand, "leave_one_profile": lop, "leave_one_root": lor}


def _joint_root_minus_shock(cells: Mapping[tuple[int, int], torch.Tensor], roots: Sequence[int]) -> float:
    shocks = range(4)
    root_means = {root: torch.stack([cells[(root, shock)].to(torch.float64) for shock in shocks]).mean(0) for root in roots}
    grand = torch.stack(list(root_means.values())).mean(0)
    v_root = float(torch.stack([(root_means[root]-grand).square().sum() for root in roots]).mean())
    # Exact registered variance of a four-IID-draw shock mean.
    v_shock = float(torch.stack([(cells[(root,shock)].to(torch.float64)-root_means[root]).square().sum() for root in roots for shock in shocks]).sum() / (len(roots)*16.0))
    return v_root-v_shock


def _root_dominance_summaries(raw: Mapping[str, Any], plan: ExperimentPlan) -> list[dict[str, Any]]:
    cache = {}
    for cell in raw["diagnostic_cells"]:
        key = (int(cell["actor_seed"]), str(cell["state_level"]), str(cell["profile"]), int(cell["root"]), int(cell["shock_index"]))
        cache[key] = geom.tensor_from_record(cell["actor_vector"])+geom.tensor_from_record(cell["critic_vector"])
    output = []
    roots = list(range(plan.heldout_roots_per_profile))
    if len(roots) != 3:
        return output
    for seed in plan.actor_seeds:
        for level in ("BASELINE_FINAL", "TREATMENT_FINAL"):
            by_profile = {}
            for profile in plan.profiles:
                cells = {(root, shock): cache[(seed,level,profile.name,root,shock)] for root in roots for shock in range(4)}
                by_profile[profile.name] = {"full": _joint_root_minus_shock(cells, roots), "leave_one_root": {str(left): _joint_root_minus_shock(cells, [root for root in roots if root != left]) for left in roots}}
            output.append({
                "actor_seed": seed, "state_level": level, "profile_values": by_profile,
                "seed_aggregate": float(np.mean([row["full"] for row in by_profile.values()])),
                "leave_one_profile": {profile.name: float(np.mean([row["full"] for name,row in by_profile.items() if name != profile.name])) for profile in plan.profiles},
                "leave_one_root": {str(left): float(np.mean([row["leave_one_root"][str(left)] for row in by_profile.values()])) for left in roots},
            })
    return output


def _evaluate_state(
    actor: b1.RecurrentActorCritic,
    state_meta: Mapping[str, Any],
    profile: roster_env.RosterProfile,
    profile_index: int,
    root: int,
    tape: np.ndarray,
    natural_shocks: tuple[str, str],
) -> dict[str, Any]:
    arms = {}
    digests = []
    for arm in EVALUATION_ARMS:
        runner = _runner(actor, profile, heldout_episode_id(profile_index, root), b2.BODY_RULES[arm], shock_tuple=natural_shocks, noise=tape)
        arms[arm] = float(sum(runner.env.reward_trace))
        digests.append((b5.public_world_digest(runner.env), b5.lifecycle_digest(runner), b5.action_noise_digest(runner), tuple(runner.env._shock_states)))
    if len(set(digests)) != 1:
        raise RuntimeError("B6 natural evaluation matching failed")
    return {
        **state_meta, "profile": profile.name, "root": root, "episode_id": heldout_episode_id(profile_index, root),
        "natural_shock_tuple": list(digests[0][3]), "public_world_digest": digests[0][0],
        "lifecycle_digest": digests[0][1], "action_noise_tape_digest": digests[0][2], "arms": arms,
        "contrasts": {"correct_minus_swapped": arms["CORRECT"]-arms["SWAPPED"], "correct_minus_native_neutral": arms["CORRECT"]-arms["NATIVE_NEUTRAL"]},
    }


def run_train(mode: str, *, source_commit: str, run_id: str) -> dict[str, Any]:
    _assert_plan_constants()
    plan = plan_for_mode(mode)
    if not source_commit or not run_id:
        raise ValueError("source commit and run identity are required")
    layout = geom.ordered_layout(_new_actor(plan.actor_seeds[0]))
    tapes = [_diagnostic_tape(profile, index) for index, profile in enumerate(plan.profiles)]
    actors_runtime: list[tuple[dict[str, Any], b1.RecurrentActorCritic, torch.optim.Adam]] = []
    retained, training, matching = [], [], []
    for seed_index, seed in enumerate(plan.actor_seeds):
        shared_init = _new_actor(seed)
        baseline_actor, treatment_actor = copy.deepcopy(shared_init), copy.deepcopy(shared_init)
        baseline_optimizer, treatment_optimizer = _new_optimizer(baseline_actor), _new_optimizer(treatment_actor)
        init_optimizer = _new_optimizer(shared_init)
        baseline_init_identity = _state_identity(baseline_actor, baseline_optimizer)
        treatment_init_identity = _state_identity(treatment_actor, treatment_optimizer)
        shared_init_identity = _state_identity(shared_init, init_optimizer)
        init_meta = {"actor_seed": seed, "state_level": "INIT", "condition": "SHARED_INIT"}
        retained.append(_retained_state(shared_init, init_optimizer, seed=seed, level="INIT", condition="SHARED_INIT"))
        actors_runtime.append((init_meta, shared_init, init_optimizer))
        baseline_rows = _train_condition(baseline_actor, baseline_optimizer, CONDITIONS[0], seed, seed_index, plan)
        treatment_rows = _train_condition(treatment_actor, treatment_optimizer, CONDITIONS[1], seed, seed_index, plan)
        proof = _matching_training(baseline_rows, treatment_rows, plan)
        proof["bit_identical_shared_init_parameters_and_zero_adam"] = baseline_init_identity == treatment_init_identity == shared_init_identity
        if not all(proof.values()):
            raise RuntimeError(f"B6 cross-condition matching failed: {proof}")
        matching.append({"actor_seed": seed, **proof})
        training.extend(baseline_rows + treatment_rows)
        for level, condition, actor, optimizer in (
            ("BASELINE_FINAL", CONDITIONS[0], baseline_actor, baseline_optimizer),
            ("TREATMENT_FINAL", CONDITIONS[1], treatment_actor, treatment_optimizer),
        ):
            meta = {"actor_seed": seed, "state_level": level, "condition": condition}
            retained.append(_retained_state(actor, optimizer, seed=seed, level=level, condition=condition))
            actors_runtime.append((meta, actor, optimizer))

    diagnostic_cells, copied_rows = [], []
    vector_cache: dict[tuple[int, str, str, int, int], tuple[torch.Tensor, torch.Tensor]] = {}
    for meta, actor, optimizer in actors_runtime:
        for profile_index, profile in enumerate(plan.profiles):
            tape = tapes[profile_index][0]
            for root in range(plan.heldout_roots_per_profile):
                cells, copied = _probe_state(actor, optimizer, meta, profile, profile_index, root, tape)
                diagnostic_cells.extend(cells); copied_rows.append(copied)
                for cell in cells:
                    key = (int(cell["actor_seed"]), str(cell["state_level"]), profile.name, root, int(cell["shock_index"]))
                    vector_cache[key] = (geom.tensor_from_record(cell["actor_vector"]), geom.tensor_from_record(cell["critic_vector"]))

    variance_rows, factorial_rows = [], []
    for seed in plan.actor_seeds:
        for level in STATE_LEVELS:
            for profile in plan.profiles:
                acells = {(root, shock): vector_cache[(seed, level, profile.name, root, shock)][0] for root in range(plan.heldout_roots_per_profile) for shock in range(4)}
                ccells = {(root, shock): vector_cache[(seed, level, profile.name, root, shock)][1] for root in range(plan.heldout_roots_per_profile) for shock in range(4)}
                if plan.heldout_roots_per_profile == 3:
                    variance_rows.append({"actor_seed": seed, "state_level": level, "profile": profile.name, **geom.finite_variance(acells, ccells, layout)})
        if plan.heldout_roots_per_profile == 3:
            for profile in plan.profiles:
                acells = {(level, root, shock): vector_cache[(seed, level, profile.name, root, shock)][0] for level in STATE_LEVELS for root in range(3) for shock in range(4)}
                ccells = {(level, root, shock): vector_cache[(seed, level, profile.name, root, shock)][1] for level in STATE_LEVELS for root in range(3) for shock in range(4)}
                factorial_rows.append({"actor_seed": seed, "profile": profile.name, "terms": geom.balanced_factorial(acells, ccells, layout)})

    natural = {}
    for profile_index, profile in enumerate(plan.profiles):
        for root in range(plan.heldout_roots_per_profile):
            probe = b5._make_env(profile, heldout_episode_id(profile_index, root), None)
            natural[(profile_index, root)] = (probe._shock_states[0], probe._shock_states[2])
    evaluation_rows = []
    for meta, actor, _ in actors_runtime:
        for profile_index, profile in enumerate(plan.profiles):
            for root in range(plan.heldout_roots_per_profile):
                evaluation_rows.append(_evaluate_state(actor, meta, profile, profile_index, root, tapes[profile_index][0], natural[(profile_index, root)]))

    counts = {
        "training_episodes": len(training)*4, "diagnostic_episodes": len(diagnostic_cells),
        "evaluation_episodes": len(evaluation_rows)*3, "total_episodes": len(training)*4+len(diagnostic_cells)+len(evaluation_rows)*3,
        "environment_transitions": (len(training)*4+len(diagnostic_cells)+len(evaluation_rows)*3)*roster_env.HORIZON,
        "policy_calls": (len(training)*4+len(diagnostic_cells)+len(evaluation_rows)*3)*roster_env.HORIZON,
        "optimizer_updates": len(training), "trained_actors": len(plan.actor_seeds)*2, "retained_states": len(retained),
        "hypothetical_transitions": 0, "coefficient_searches": 0, "rescue_arms": 0,
    }
    expected = {"training_episodes": plan.training_episodes, "diagnostic_episodes": plan.diagnostic_episodes, "evaluation_episodes": plan.evaluation_episodes, "total_episodes": plan.total_episodes, "environment_transitions": plan.total_transitions, "policy_calls": plan.total_transitions, "optimizer_updates": plan.optimizer_updates, "trained_actors": plan.trained_actors, "retained_states": plan.retained_states, "hypothetical_transitions": 0, "coefficient_searches": 0, "rescue_arms": 0}
    if counts != expected:
        raise RuntimeError(f"B6 activity counts drifted: {counts} != {expected}")
    return {
        "artifact_kind": "EOCIV_B6_RAW", "treatment": TREATMENT, "mode": mode,
        "source_commit": source_commit, "run_id": run_id, "scientific_disposition": None,
        "registered_c_outcome_experiment_licensed": capability_gate.REGISTERED_OUTCOME_EXPERIMENT["licensed"],
        "configuration": {"conditions": list(CONDITIONS), "actor_seeds": list(plan.actor_seeds), "profiles": [p.name for p in plan.profiles], "training_roots": list(range(plan.training_roots_per_profile)), "heldout_roots": list(range(plan.heldout_roots_per_profile)), "horizon": plan.horizon, "critical_tuples": [list(v) for v in CRITICAL_TUPLES], "evaluation_arms": list(EVALUATION_ARMS), "actor_lr": b1.ACTOR_LR, "adam_betas": [0.9,0.999], "adam_epsilon": 1e-8, "gae_gamma": b1.GAMMA, "gae_lambda": b5.GAE_LAMBDA, "final_grad_cap": b1.GRAD_NORM_CAP, "parameter_layout": layout},
        "root_tape_manifest": {"training_episode_base": TRAIN_EPISODE_BASE, "heldout_episode_base": HELDOUT_EPISODE_BASE, "diagnostic_tape_base": DIAGNOSTIC_TAPE_BASE, "tapes": [row for _, row in tapes]},
        "counts": counts, "training_matching": matching, "training_updates": training,
        "retained_states": retained, "diagnostic_cells": diagnostic_cells, "copied_adam_rows": copied_rows,
        "variance_rows": variance_rows, "factorial_rows": factorial_rows, "evaluation_rows": evaluation_rows,
        "mechanical_status": "MECHANICAL_B6_TRAIN_COMPLETE",
    }


def _validate_update_identity_chain(
    ordered: Sequence[Mapping[str, Any]],
    init_identity: Mapping[str, Any],
    final_identity: Mapping[str, Any],
) -> None:
    if not ordered:
        raise RuntimeError("B6 update identity chain is empty")
    if ordered[0].get("pre_step_state_identity") != init_identity:
        raise RuntimeError("B6 update identity chain INIT admission failed")
    if any(left.get("post_step_state_identity") != right.get("pre_step_state_identity") for left,right in zip(ordered,ordered[1:])):
        raise RuntimeError("B6 update identity chain continuity admission failed")
    if ordered[-1].get("post_step_state_identity") != final_identity:
        raise RuntimeError("B6 update identity chain FINAL admission failed")


def _validate_raw(raw: Mapping[str, Any]) -> ExperimentPlan:
    plan = plan_for_mode(str(raw["mode"])); _assert_plan_constants()
    if raw.get("artifact_kind") != "EOCIV_B6_RAW" or raw.get("treatment") != TREATMENT:
        raise RuntimeError("B6 raw identity admission failed")
    if not isinstance(raw.get("source_commit"), str) or len(raw["source_commit"]) != 40 or not all(character in "0123456789abcdef" for character in raw["source_commit"]):
        raise RuntimeError("B6 source commit admission failed")
    if not isinstance(raw.get("run_id"), str) or not raw["run_id"]:
        raise RuntimeError("B6 run identity admission failed")
    config = raw["configuration"]
    expected_config = {
        "conditions": list(CONDITIONS), "actor_seeds": list(plan.actor_seeds),
        "profiles": [profile.name for profile in plan.profiles],
        "training_roots": list(range(plan.training_roots_per_profile)),
        "heldout_roots": list(range(plan.heldout_roots_per_profile)),
        "horizon": roster_env.HORIZON, "critical_tuples": [list(value) for value in CRITICAL_TUPLES],
        "evaluation_arms": list(EVALUATION_ARMS), "actor_lr": b1.ACTOR_LR,
        "adam_betas": [0.9, 0.999], "adam_epsilon": 1e-8,
        "gae_gamma": b1.GAMMA, "gae_lambda": b5.GAE_LAMBDA,
        "final_grad_cap": b1.GRAD_NORM_CAP,
    }
    if any(config.get(key) != value for key,value in expected_config.items()):
        raise RuntimeError("B6 configuration admission failed")
    expected = (plan.total_episodes, plan.total_transitions, plan.optimizer_updates, plan.retained_states)
    observed = (raw["counts"]["total_episodes"], raw["counts"]["environment_transitions"], raw["counts"]["optimizer_updates"], raw["counts"]["retained_states"])
    if observed != expected or raw["counts"]["policy_calls"] != plan.total_transitions:
        raise RuntimeError("B6 raw count admission failed")
    shapes = (len(raw["training_updates"]), len(raw["diagnostic_cells"]), len(raw["evaluation_rows"]), len(raw["retained_states"]))
    if shapes != (plan.optimizer_updates, plan.diagnostic_episodes, plan.evaluation_episodes//3, plan.retained_states):
        raise RuntimeError(f"B6 raw shape admission failed: {shapes}")
    if not all(all(value for key,value in row.items() if key != "actor_seed") for row in raw["training_matching"]):
        raise RuntimeError("B6 training matching admission failed")
    expected_updates = {
        (condition, seed, profile.name, root)
        for condition in CONDITIONS for seed in plan.actor_seeds for profile in plan.profiles
        for root in range(plan.training_roots_per_profile)
    }
    observed_updates = {(row["condition"], int(row["actor_seed"]), row["profile"], int(row["root"])) for row in raw["training_updates"]}
    if observed_updates != expected_updates or not all(row["shock_tuples"] == [list(value) for value in CRITICAL_TUPLES] for row in raw["training_updates"]):
        raise RuntimeError("B6 training roster admission failed")
    expected_states = {(seed, level) for seed in plan.actor_seeds for level in STATE_LEVELS}
    observed_states = {(int(row["actor_seed"]), str(row["state_level"])) for row in raw["retained_states"]}
    if observed_states != expected_states or any(row["state_level"] == "MID" for row in raw["retained_states"]):
        raise RuntimeError("B6 retained-state roster admission failed")
    retained_identity = {
        (int(row["actor_seed"]), str(row["state_level"])): row["identity"]
        for row in raw["retained_states"]
    }
    final_level = {
        CONDITIONS[0]: "BASELINE_FINAL",
        CONDITIONS[1]: "TREATMENT_FINAL",
    }
    for condition in CONDITIONS:
        for seed in plan.actor_seeds:
            ordered = sorted(
                (row for row in raw["training_updates"] if row["condition"] == condition and int(row["actor_seed"]) == seed),
                key=lambda row: int(row["order_index"]),
            )
            if len(ordered) != len(plan.profiles) * plan.training_roots_per_profile:
                raise RuntimeError("B6 update identity chain length admission failed")
            _validate_update_identity_chain(
                ordered,
                retained_identity[(seed, "INIT")],
                retained_identity[(seed, final_level[condition])],
            )
    expected_diagnostics = {(seed,level,profile.name,root,shock) for seed in plan.actor_seeds for level in STATE_LEVELS for profile in plan.profiles for root in range(plan.heldout_roots_per_profile) for shock in range(4)}
    observed_diagnostics = {(int(row["actor_seed"]),str(row["state_level"]),str(row["profile"]),int(row["root"]),int(row["shock_index"])) for row in raw["diagnostic_cells"]}
    if observed_diagnostics != expected_diagnostics:
        raise RuntimeError("B6 diagnostic roster admission failed")
    expected_evaluation = {(seed,level,profile.name,root) for seed in plan.actor_seeds for level in STATE_LEVELS for profile in plan.profiles for root in range(plan.heldout_roots_per_profile)}
    observed_evaluation = {(int(row["actor_seed"]),str(row["state_level"]),str(row["profile"]),int(row["root"])) for row in raw["evaluation_rows"]}
    if observed_evaluation != expected_evaluation:
        raise RuntimeError("B6 evaluation roster admission failed")
    for profile in plan.profiles:
        if len({row["action_noise_tape_digest"] for row in raw["diagnostic_cells"] if row["profile"] == profile.name}) != 1:
            raise RuntimeError("B6 diagnostic common-tape admission failed")
    for profile in plan.profiles:
        for root in range(plan.heldout_roots_per_profile):
            selected = [row for row in raw["evaluation_rows"] if row["profile"] == profile.name and row["root"] == root]
            if len({tuple(row["natural_shock_tuple"]) for row in selected}) != 1 or len({row["action_noise_tape_digest"] for row in selected}) != 1:
                raise RuntimeError("B6 natural shock/tape reuse admission failed")
    if any(raw["counts"][key] != 0 for key in ("hypothetical_transitions","coefficient_searches","rescue_arms")):
        raise RuntimeError("B6 exclusion admission failed")
    return plan


def evaluate_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    plan = _validate_raw(raw)
    semantic = _semantic_summaries(raw["evaluation_rows"], plan)
    projection = {}
    raw_projection = {}
    for seed in plan.actor_seeds:
        selected = [row for row in raw["copied_adam_rows"] if row["actor_seed"] == seed]
        projection[str(seed)] = _summary([float(row["projection_increase"]) for row in selected])
        raw_projection[str(seed)] = _summary([float(row["raw_projection_increase"]) for row in selected])
    finite_values = all(math.isfinite(float(cell["diagnostics"][key])) for cell in raw["diagnostic_cells"] for key in ("critic_loss","value_target_mean","value_target_population_std","value_target_error"))
    critic_nonzero = all(float(cell["critic_norm"]) > 0.0 for cell in raw["diagnostic_cells"])
    projection_increased = all(float(row["mean"]) > 0.0 for row in projection.values())
    raw_projection_increased = all(float(row["mean"]) > 0.0 for row in raw_projection.values())
    root_summaries = _root_dominance_summaries(raw, plan)
    fidelity = {
        "exact_counts_and_shapes": True,
        "all_training_matching": True,
        "actor_anchored_constraint_all_updates": all(row["intervention_constraint_passed"] for row in raw["training_updates"]),
        "finite_value_diagnostics": finite_values,
        "no_critic_collapse": critic_nonzero,
        "copied_adam_projection_increased_all_seed_aggregates": projection_increased,
        "raw_actor_projection_increased_all_seed_aggregates": raw_projection_increased,
        "no_mutation_all_probes": all(row["state_identity_before"] == row["state_identity_after"] for row in raw["copied_adam_rows"]),
    }
    full_admitted = plan.mode == "full"
    return {
        "artifact_kind": "EOCIV_B6_EVALUATION_RECEIPT", "mode": plan.mode,
        "source_commit": raw["source_commit"], "run_id": raw["run_id"],
        "scientific_terminal_admitted": full_admitted, "technical_only": not full_admitted,
        "counts": raw["counts"], "fidelity": fidelity, "semantic": semantic,
        "projection_by_seed": projection, "raw_projection_by_seed": raw_projection,
        "variance_rows": raw["variance_rows"], "factorial_rows": raw["factorial_rows"],
        "root_dominance_summaries": root_summaries,
        "scientific_disposition": None, "registered_c_outcome_experiment_licensed": False,
        "mechanical_status": "MECHANICAL_B6_EVALUATE_COMPLETE",
    }


def _all_positive(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bool:
    return bool(rows) and all(float(row[field]) > 0.0 for row in rows for field in fields)


def analyze_evaluation(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if receipt["artifact_kind"] != "EOCIV_B6_EVALUATION_RECEIPT":
        raise RuntimeError("wrong B6 evaluation artifact")
    fidelity = all(bool(value) for value in receipt["fidelity"].values())
    terminal = None
    root_dominance = False
    stable = False
    root_sensitive_failure = False
    both_coverage_modulated = False
    if receipt["scientific_terminal_admitted"]:
        semantic = receipt["semantic"]
        fields = ("correct_minus_swapped", "correct_minus_native_neutral")
        stable = (
            all(float(semantic["grand"][field]) > 0.0 for field in fields)
            and _all_positive(semantic["seed_aggregates"], fields)
            and _all_positive(semantic["leave_one_profile"], fields)
            and _all_positive(semantic["leave_one_root"], fields)
            and float(semantic["grand"]["absolute_correct"]) >= 0.0
            and receipt["fidelity"]["copied_adam_projection_increased_all_seed_aggregates"]
        )
        summaries = receipt["root_dominance_summaries"]
        root_nonzero = bool(summaries) and all(
            float(row["seed_aggregate"]) > 0.0
            and all(float(value) > 0.0 for value in row["leave_one_profile"].values())
            and all(float(value) > 0.0 for value in row["leave_one_root"].values())
            for row in summaries
        )
        factorial = receipt["factorial_rows"]
        coherent = bool(factorial) and all(float(row["terms"]["root"]["joint"]) > 0.0 and float(row["terms"]["state_x_root"]["joint"]) > 0.0 for row in factorial)
        root_span = any(
            len({round(float(cell[field]),12) for cell in semantic["cells"] if cell["actor_seed"]==seed and cell["profile"]==profile}) > 1
            for seed in {cell["actor_seed"] for cell in semantic["cells"]}
            for profile in {cell["profile"] for cell in semantic["cells"]}
            for field in fields
        )
        # Full registered roster has exactly 3 profiles and 3 roots.  Positive
        # every-cell differences imply every seed/leave-one recomputation.
        root_dominance = root_nonzero and coherent and root_span
        root_sensitive_failure = not stable and root_span
        # No arbitrary materiality threshold: exact coverage modulation means
        # at least one semantic treatment-effect sign differs across roots.
        both_coverage_modulated = any(len({np.sign(cell[field]) for cell in semantic["cells"] if cell["actor_seed"]==seed and cell["profile"]==profile}) > 1 for seed in {c["actor_seed"] for c in semantic["cells"]} for profile in {c["profile"] for c in semantic["cells"]} for field in fields)
        nonpositive_all_seeds = all(float(row[field]) <= 0.0 for row in semantic["seed_aggregates"] for field in fields)
        if not fidelity:
            terminal = "INTERVENTION_FAILURE"
        elif stable and root_dominance:
            terminal = "BOTH_MATTER" if both_coverage_modulated else "UNIDENTIFIED"
        elif stable:
            terminal = "OPTIMIZER_TREATMENT_IMPROVES_STABLE_SEMANTICS"
        elif root_dominance and root_sensitive_failure:
            terminal = "PUBLIC_ROOT_VARIABILITY_DOMINATES"
        elif nonpositive_all_seeds and not root_dominance:
            terminal = "NEITHER_SUPPORTED"
        else:
            terminal = "UNIDENTIFIED"
        if terminal not in TERMINALS:
            raise RuntimeError("B6 terminal map failed")
    return {
        "artifact_kind": "EOCIV_B6_ANALYSIS", "mode": receipt["mode"],
        "source_commit": receipt["source_commit"], "run_id": receipt["run_id"],
        "scientific_terminal_admitted": bool(receipt["scientific_terminal_admitted"]),
        "technical_only": bool(receipt["technical_only"]), "terminal_label": terminal,
        "intervention_fidelity": fidelity, "stable_semantic_improvement": stable,
        "root_dominance": root_dominance, "root_sensitive_failure": root_sensitive_failure,
        "exact_coverage_modulation": both_coverage_modulated,
        "scientific_disposition": None, "registered_c_outcome_experiment_licensed": False,
        "strongest_confound": "Total adaptive Adam/on-policy history after the first differing update; finite three-root panel conditional on one profile tape.",
        "mechanical_status": "MECHANICAL_B6_ANALYZE_COMPLETE",
    }


def write_json(value: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
