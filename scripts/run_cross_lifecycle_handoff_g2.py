#!/usr/bin/env python3
"""Train, evaluate and analyze the frozen cross-lifecycle handoff G2."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
from typing import Any, Iterable, Mapping

import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.cross_lifecycle_handoff_g2 import (
    ACTION_VALUES,
    ACTOR_WIDTH,
    CRITIC_WIDTH,
    MAXIMUM_CAPACITY,
    PASS_RESULT as INFORMATION_GATE_PASS,
    CrossLifecycleHandoffG2Env,
    build_cases,
    evaluate_information_gate,
    make_episode_spec,
)
from ha_ctse_process.ehc_handoff_g2 import (
    ARM_NAMES,
    HIDDEN_WIDTH,
    PPO_PASSES,
    SOURCE_FAMILY,
    ArmState,
    SeedRegistry,
    _advance_hidden,
    assert_replay_equal,
    collect_rollout,
    initialize_matched_arms,
    load_checkpoint,
    optimize_rollout,
    replay_rollout,
    save_checkpoint,
)


RUNNER_SCHEMA = "cross_lifecycle_commitment_handoff_g2_runner_v1"
MANIFEST_SCHEMA = "cross_lifecycle_commitment_handoff_g2_manifest_v1"
EVALUATION_MANIFEST_SCHEMA = "cross_lifecycle_commitment_handoff_g2_eval_manifest_v1"
EVALUATION_ROW_SCHEMA = "cross_lifecycle_commitment_handoff_g2_eval_row_v1"
AUDIT_ROW_SCHEMA = "cross_lifecycle_commitment_handoff_g2_audit_row_v1"
ANALYSIS_SCHEMA = "cross_lifecycle_commitment_handoff_g2_analysis_v1"
SOURCE_CONTROL_SCHEMA = "cross_lifecycle_commitment_handoff_g2_controls_v1"

FORMAL_AUTHORIZATION_TOKEN = (
    "AUTHORIZE_CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_FORMAL_CPU_V1"
)
REPLICATES = tuple(range(5))
EVALUATION_PROFILES = (
    "iid_deterministic",
    "iid_stochastic",
    "heldout_deterministic",
    "heldout_stochastic",
)
FORMAL_BUDGET: dict[str, int] = {
    "replicates": 5,
    "environments": 16,
    "horizon": 64,
    "updates": 160,
    "ppo_passes": 4,
    "evaluation_episodes_per_cell": 256,
    "audit_episodes_per_replicate": 128,
    "bootstrap_repetitions": 10_000,
}
EXERCISE_BUDGET: dict[str, int] = {
    "replicates": 1,
    "environments": 2,
    "horizon": 24,
    "updates": 1,
    "ppo_passes": 4,
    "evaluation_episodes_per_cell": 8,
    "audit_episodes_per_replicate": 8,
    "bootstrap_repetitions": 32,
}
SEED_REGISTRY = SeedRegistry()

_ATOMIC_REPLACE_ATTEMPTS = 100
_ATOMIC_REPLACE_RETRY_DELAY_SECONDS = 0.05


def configure_cpu_runtime() -> None:
    if torch.cuda.is_initialized():
        raise RuntimeError("G2 cannot start after a CUDA runtime was initialized")
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        if torch.get_num_interop_threads() != 1:
            raise
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise RuntimeError("G2 requires exactly one Torch CPU thread")


def _replace_with_permission_retry(temporary: Path, destination: Path) -> None:
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            os.replace(temporary, destination)
            return
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(_ATOMIC_REPLACE_RETRY_DELAY_SECONDS)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _replace_with_permission_retry(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        _replace_with_permission_retry(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(value)
    return rows


def _relative(run_root: Path, path: Path) -> str:
    return PurePosixPath(path.relative_to(run_root)).as_posix()


def _resolve_reference(run_root: Path, reference: object) -> Path:
    if not isinstance(reference, str) or not reference:
        raise ValueError("artifact reference must be a nonempty string")
    pure = PurePosixPath(reference)
    if pure.is_absolute() or ".." in pure.parts or "\\" in reference:
        raise ValueError("artifact reference escapes the run root")
    resolved = (run_root / Path(*pure.parts)).resolve()
    if run_root.resolve() not in resolved.parents:
        raise ValueError("artifact reference escapes the run root")
    return resolved


def _source_commit(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise argparse.ArgumentTypeError("source commit must be 40 lowercase hex chars")
    return value


def _budget(formal: bool) -> dict[str, int]:
    return dict(FORMAL_BUDGET if formal else EXERCISE_BUDGET)


def _replicates(budget: Mapping[str, int]) -> tuple[int, ...]:
    return tuple(range(int(budget["replicates"])))


def _manifest_identity(
    *, formal: bool, source_commit: str, budget: Mapping[str, int]
) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "backend": "cpu",
        "torch_threads": 1,
        "arms": list(ARM_NAMES),
        "replicates": list(_replicates(budget)),
        "budget": dict(budget),
        "seed_registry": asdict(SEED_REGISTRY),
        "authorization_token": FORMAL_AUTHORIZATION_TOKEN if formal else None,
    }


def _validate_manifest_identity(
    manifest: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"manifest {key} mismatch")


def train_run(
    run_root: Path,
    *,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
) -> dict[str, Any]:
    configure_cpu_runtime()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source commit must be 40 lowercase hex chars")
    if formal and authorization_token != FORMAL_AUTHORIZATION_TOKEN:
        raise ValueError("formal G2 authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("nonformal G2 cannot carry a formal authorization token")

    budget = _budget(formal)
    expected = _manifest_identity(
        formal=formal, source_commit=source_commit, budget=budget
    )
    manifest_path = run_root / "manifest.json"
    if manifest_path.exists():
        manifest = _read_json(manifest_path)
        _validate_manifest_identity(manifest, expected)
    else:
        if run_root.exists() and any(run_root.iterdir()):
            raise FileExistsError(f"run root already exists and is not empty: {run_root}")
        run_root.mkdir(parents=True, exist_ok=True)
        manifest = {**expected, "status": "TRAINING", "checkpoint_references": []}
        _atomic_json(manifest_path, manifest)

    checkpoint_references: list[str] = []
    for replicate in _replicates(budget):
        matched = initialize_matched_arms(replicate=replicate)
        for arm in ARM_NAMES:
            final_path = (
                run_root
                / "checkpoints"
                / arm
                / f"replicate_{replicate}"
                / f"update_{budget['updates']}.pt"
            )
            latest_path = final_path.with_name("latest.pt")
            if final_path.exists():
                state = load_checkpoint(
                    final_path,
                    expected_source_commit=source_commit,
                    expected_arm=arm,
                    expected_replicate=replicate,
                )
                if state.completed_updates != budget["updates"]:
                    raise ValueError("final checkpoint update mismatch")
                if latest_path.exists():
                    latest_path.unlink()
                checkpoint_references.append(_relative(run_root, final_path))
                continue
            if latest_path.exists():
                state = load_checkpoint(
                    latest_path,
                    expected_source_commit=source_commit,
                    expected_arm=arm,
                    expected_replicate=replicate,
                )
            else:
                state = matched[arm]
            for update_index in range(state.completed_updates, budget["updates"]):
                batch = collect_rollout(
                    state,
                    environments=budget["environments"],
                    horizon=budget["horizon"],
                    update_index=update_index,
                )
                replay_errors = assert_replay_equal(
                    batch, replay_rollout(state.model, arm, batch)
                )
                report = optimize_rollout(state, batch)
                state.episodes_completed += len(batch.episode_records)
                state.completed_updates = update_index + 1
                save_checkpoint(
                    latest_path,
                    state,
                    source_commit=source_commit,
                    update=state.completed_updates,
                )
                _atomic_json(
                    run_root / "progress.json",
                    {
                        "schema": RUNNER_SCHEMA,
                        "formal": formal,
                        "status": "TRAINING",
                        "replicate": replicate,
                        "arm": arm,
                        "update": state.completed_updates,
                        "optimizer_steps": state.optimizer_steps,
                        "replay_errors": replay_errors,
                        "last_report": report,
                    },
                )
            save_checkpoint(
                final_path,
                state,
                source_commit=source_commit,
                update=state.completed_updates,
            )
            if latest_path.exists():
                latest_path.unlink()
            checkpoint_references.append(_relative(run_root, final_path))

    expected_checkpoint_count = len(ARM_NAMES) * budget["replicates"]
    if len(set(checkpoint_references)) != expected_checkpoint_count:
        raise RuntimeError("final checkpoint inventory is incomplete")
    manifest = {
        **expected,
        "status": "TRAIN_COMPLETE",
        "checkpoint_references": sorted(checkpoint_references),
    }
    _atomic_json(manifest_path, manifest)
    _atomic_json(
        run_root / "progress.json",
        {
            "schema": RUNNER_SCHEMA,
            "formal": formal,
            "status": "TRAIN_COMPLETE",
            "updates": budget["updates"],
            "arms": list(ARM_NAMES),
            "replicates": list(_replicates(budget)),
        },
    )
    return manifest


def _pack_single_observation(
    environment: CrossLifecycleHandoffG2Env,
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    actor = torch.zeros(1, MAXIMUM_CAPACITY, ACTOR_WIDTH)
    critic = torch.zeros(1, MAXIMUM_CAPACITY, CRITIC_WIDTH)
    active = torch.zeros(1, MAXIMUM_CAPACITY, dtype=torch.bool)
    reset = torch.zeros_like(active)
    create = torch.zeros_like(active)
    for slot, observation in environment.observe().items():
        actor[0, slot] = torch.tensor(observation.actor)
        critic[0, slot] = torch.tensor(observation.critic)
        active[0, slot] = True
        reset[0, slot] = observation.actor[2] == 1.0
        create[0, slot] = observation.opportunity_kind == "CREATE"
    return actor, critic, active, reset, create


def _policy_episode(
    state: ArmState,
    environment: CrossLifecycleHandoffG2Env,
    *,
    deterministic: bool,
    primitive_generator: torch.Generator,
    mark_generator: torch.Generator,
    forced_mark: int | None = None,
) -> dict[str, Any]:
    if forced_mark is not None and forced_mark not in (-1, 1):
        raise ValueError("forced mark must be -1 or +1")
    member_hidden = torch.zeros(1, MAXIMUM_CAPACITY, HIDDEN_WIDTH)
    team_hidden = torch.zeros(1, HIDDEN_WIDTH)
    held_mark = torch.zeros(1)
    selected_mark = 0
    successor_actions: list[int] = []
    state.model.eval()
    with torch.no_grad():
        while not environment.done:
            actor, critic, active, reset, create = _pack_single_observation(
                environment
            )
            del critic
            features, member_hidden, team_hidden = _advance_hidden(
                state.model,
                actor,
                active,
                reset,
                torch.tensor([environment.time == 0]),
                member_hidden,
                team_hidden,
            )
            if create.any():
                mark_logits = state.model.mark_head(features[create])
                if forced_mark is not None:
                    selected_mark = forced_mark
                elif deterministic:
                    selected_mark = 2 * int(mark_logits.argmax(dim=-1).item()) - 1
                else:
                    selected_mark = 2 * int(
                        torch.multinomial(
                            torch.softmax(mark_logits, dim=-1),
                            1,
                            generator=mark_generator,
                        ).item()
                    ) - 1
                held_mark[0] = selected_mark
            logits = state.model.primitive_logits(
                state.arm, member_hidden, team_hidden, held_mark
            )
            if deterministic:
                action_indices = logits.argmax(dim=-1)
            else:
                probabilities = torch.softmax(logits[active], dim=-1)
                sampled = torch.multinomial(
                    probabilities, 1, generator=primitive_generator
                ).squeeze(-1)
                action_indices = torch.zeros(1, MAXIMUM_CAPACITY, dtype=torch.long)
                action_indices[active] = sampled
            actions = {
                slot: ACTION_VALUES[int(action_indices[0, slot])]
                for slot in torch.nonzero(active[0], as_tuple=False).flatten().tolist()
            }
            transition = environment.step(actions)
            if transition["successor_action"] is not None:
                successor_actions.append(int(transition["successor_action"]))
            if not environment.done:
                next_active = set(environment.observe())
                for slot in range(MAXIMUM_CAPACITY):
                    if slot not in next_active:
                        member_hidden[0, slot].zero_()
    spec = environment.spec
    return {
        "base_id": spec.base_id,
        "sign_mate": spec.sign_mate,
        "bit": spec.bit,
        "creator_slot": spec.creator_slot,
        "successor_slot": spec.successor_slot,
        "survivor_slot": spec.survivor_slot,
        "creator_duration": spec.creator_duration,
        "gap": spec.gap,
        "successor_duration": spec.successor_duration,
        "utility": sum(action == spec.bit for action in successor_actions)
        / len(successor_actions),
        "mark": selected_mark,
        "mark_correct": float(selected_mark == spec.bit),
        "successor_actions": successor_actions,
    }


def _evaluation_spec(
    profile: str, *, base_id: int, sign_mate: int, replicate: int
):
    offset = replicate * SEED_REGISTRY.replicate_offset
    return make_episode_spec(
        profile,
        base_id=base_id,
        sign_mate=sign_mate,
        task_seed=SEED_REGISTRY.evaluation_task + offset,
        membership_seed=SEED_REGISTRY.evaluation_membership + offset,
        nuisance_seed=SEED_REGISTRY.evaluation_nuisance + offset,
    )


def _evaluation_rows(
    state: ArmState,
    *,
    profile_name: str,
    episode_count: int,
) -> list[dict[str, Any]]:
    source_profile, mode = profile_name.split("_", maxsplit=1)
    deterministic = mode == "deterministic"
    if mode not in ("deterministic", "stochastic") or episode_count % 2:
        raise ValueError("evaluation profile/count is invalid")
    primitive_generator = torch.Generator(device="cpu").manual_seed(
        SEED_REGISTRY.evaluation_primitive
        + state.replicate * SEED_REGISTRY.replicate_offset
    )
    mark_generator = torch.Generator(device="cpu").manual_seed(
        SEED_REGISTRY.evaluation_mark
        + state.replicate * SEED_REGISTRY.replicate_offset
    )
    rows: list[dict[str, Any]] = []
    for base_id in range(episode_count // 2):
        for sign_mate in (-1, 1):
            outcome = _policy_episode(
                state,
                CrossLifecycleHandoffG2Env(
                    _evaluation_spec(
                        source_profile,
                        base_id=base_id,
                        sign_mate=sign_mate,
                        replicate=state.replicate,
                    )
                ),
                deterministic=deterministic,
                primitive_generator=primitive_generator,
                mark_generator=mark_generator,
            )
            rows.append(
                {
                    "schema": EVALUATION_ROW_SCHEMA,
                    "arm": state.arm,
                    "replicate": state.replicate,
                    "profile": profile_name,
                    **{key: value for key, value in outcome.items() if key != "successor_actions"},
                    "successor_action_count": len(outcome["successor_actions"]),
                }
            )
    return rows


def _audit_rows(
    state: ArmState, *, episode_count: int
) -> list[dict[str, Any]]:
    if state.arm != "EHC" or episode_count % 2:
        raise ValueError("audit requires EHC and an even episode count")
    rows: list[dict[str, Any]] = []
    for base_id in range(episode_count // 2):
        for sign_mate in (-1, 1):
            spec = _evaluation_spec(
                "heldout",
                base_id=base_id,
                sign_mate=sign_mate,
                replicate=state.replicate,
            )
            natural, flipped = _paired_snapshot_audit(state, spec)
            natural_actions = natural["successor_actions"]
            flipped_actions = flipped["successor_actions"]
            if len(natural_actions) != len(flipped_actions) or not natural_actions:
                raise RuntimeError("audit successor sequence inventory mismatch")
            rows.append(
                {
                    "schema": AUDIT_ROW_SCHEMA,
                    "arm": "EHC",
                    "replicate": state.replicate,
                    "profile": "heldout_deterministic",
                    "base_id": base_id,
                    "sign_mate": sign_mate,
                    "bit": spec.bit,
                    "natural_mark": natural["mark"],
                    "mark_correct": natural["mark_correct"],
                    "natural_utility": natural["utility"],
                    "flipped_utility": flipped["utility"],
                    "action_tv": sum(
                        natural_action != flipped_action
                        for natural_action, flipped_action in zip(
                            natural_actions, flipped_actions, strict=True
                        )
                    )
                    / len(natural_actions),
                    "utility_drop": natural["utility"] - flipped["utility"],
                    "successor_action_count": len(natural_actions),
                }
            )
    return rows


def _deterministic_continuation(
    state: ArmState,
    *,
    environment_snapshot: Mapping[str, Any],
    member_hidden: Tensor,
    team_hidden: Tensor,
    held_mark: Tensor,
) -> dict[str, Any]:
    environment = CrossLifecycleHandoffG2Env.from_snapshot(environment_snapshot)
    successor_actions: list[int] = []
    with torch.no_grad():
        while not environment.done:
            actor, critic, active, reset, create = _pack_single_observation(
                environment
            )
            del critic
            if create.any():
                raise RuntimeError("post-handoff continuation contains CREATE")
            _, member_hidden, team_hidden = _advance_hidden(
                state.model,
                actor,
                active,
                reset,
                torch.tensor([False]),
                member_hidden,
                team_hidden,
            )
            logits = state.model.primitive_logits(
                state.arm, member_hidden, team_hidden, held_mark
            )
            indices = logits.argmax(dim=-1)
            actions = {
                slot: ACTION_VALUES[int(indices[0, slot])]
                for slot in torch.nonzero(active[0], as_tuple=False).flatten().tolist()
            }
            transition = environment.step(actions)
            if transition["successor_action"] is not None:
                successor_actions.append(int(transition["successor_action"]))
            if not environment.done:
                next_active = set(environment.observe())
                for slot in range(MAXIMUM_CAPACITY):
                    if slot not in next_active:
                        member_hidden[0, slot].zero_()
    return {
        "utility": sum(action == environment.spec.bit for action in successor_actions)
        / len(successor_actions),
        "successor_actions": successor_actions,
    }


def _paired_snapshot_audit(state: ArmState, spec) -> tuple[dict[str, Any], dict[str, Any]]:
    """Branch only after creator terminal departure from one exact snapshot."""

    environment = CrossLifecycleHandoffG2Env(spec)
    member_hidden = torch.zeros(1, MAXIMUM_CAPACITY, HIDDEN_WIDTH)
    team_hidden = torch.zeros(1, HIDDEN_WIDTH)
    held_mark = torch.zeros(1)
    selected_mark = 0
    state.model.eval()
    with torch.no_grad():
        while environment.time < spec.creator_duration:
            actor, critic, active, reset, create = _pack_single_observation(
                environment
            )
            del critic
            features, member_hidden, team_hidden = _advance_hidden(
                state.model,
                actor,
                active,
                reset,
                torch.tensor([environment.time == 0]),
                member_hidden,
                team_hidden,
            )
            if create.any():
                selected_mark = 2 * int(
                    state.model.mark_head(features[create]).argmax(dim=-1).item()
                ) - 1
                held_mark[0] = selected_mark
            logits = state.model.primitive_logits(
                state.arm, member_hidden, team_hidden, held_mark
            )
            indices = logits.argmax(dim=-1)
            actions = {
                slot: ACTION_VALUES[int(indices[0, slot])]
                for slot in torch.nonzero(active[0], as_tuple=False).flatten().tolist()
            }
            environment.step(actions)
            if environment.done:
                raise RuntimeError("creator departure unexpectedly ended the episode")
            next_active = set(environment.observe())
            for slot in range(MAXIMUM_CAPACITY):
                if slot not in next_active:
                    member_hidden[0, slot].zero_()

    if selected_mark not in (-1, 1):
        raise RuntimeError("natural CREATE did not produce a mark")
    snapshot = environment.snapshot_state()
    natural = _deterministic_continuation(
        state,
        environment_snapshot=snapshot,
        member_hidden=member_hidden.clone(),
        team_hidden=team_hidden.clone(),
        held_mark=held_mark.clone(),
    )
    flipped = _deterministic_continuation(
        state,
        environment_snapshot=snapshot,
        member_hidden=member_hidden.clone(),
        team_hidden=team_hidden.clone(),
        held_mark=-held_mark.clone(),
    )
    natural["mark"] = selected_mark
    natural["mark_correct"] = float(selected_mark == spec.bit)
    flipped["mark"] = -selected_mark
    return natural, flipped


def evaluate_run(run_root: Path, *, formal: bool) -> dict[str, Any]:
    configure_cpu_runtime()
    manifest = _read_json(run_root / "manifest.json")
    budget = _budget(formal)
    expected = _manifest_identity(
        formal=formal,
        source_commit=str(manifest.get("source_commit")),
        budget=budget,
    )
    _validate_manifest_identity(manifest, expected)
    if manifest.get("status") != "TRAIN_COMPLETE":
        raise ValueError("training is not complete")

    references: list[str] = []
    audit_rows: list[dict[str, Any]] = []
    for replicate in _replicates(budget):
        for arm in ARM_NAMES:
            checkpoint = (
                run_root
                / "checkpoints"
                / arm
                / f"replicate_{replicate}"
                / f"update_{budget['updates']}.pt"
            )
            state = load_checkpoint(
                checkpoint,
                expected_source_commit=str(manifest["source_commit"]),
                expected_arm=arm,
                expected_replicate=replicate,
            )
            for profile in EVALUATION_PROFILES:
                rows = _evaluation_rows(
                    state,
                    profile_name=profile,
                    episode_count=budget["evaluation_episodes_per_cell"],
                )
                path = (
                    run_root
                    / "evaluation"
                    / arm
                    / f"replicate_{replicate}"
                    / f"{profile}.jsonl"
                )
                _write_jsonl(path, rows)
                references.append(_relative(run_root, path))
            if arm == "EHC":
                audit_rows.extend(
                    _audit_rows(
                        state,
                        episode_count=budget["audit_episodes_per_replicate"],
                    )
                )

    source_controls = {
        **evaluate_information_gate(build_cases()),
        "schema": SOURCE_CONTROL_SCHEMA,
        "source_commit": manifest["source_commit"],
        "constructive_team_rec_utility": 1.0,
        "constructive_ehc_utility": 1.0,
        "fresh_per_member_bound": 0.5,
    }
    _atomic_json(run_root / "source_controls.json", source_controls)
    _write_jsonl(run_root / "causal_audit.jsonl", audit_rows)
    evaluation_manifest = {
        "schema": EVALUATION_MANIFEST_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": formal,
        "backend": "cpu",
        "torch_threads": 1,
        "status": "EVALUATION_COMPLETE",
        "budget": budget,
        "evaluation_references": sorted(references),
        "source_control_reference": "source_controls.json",
        "audit_reference": "causal_audit.jsonl",
    }
    expected_references = len(ARM_NAMES) * budget["replicates"] * len(
        EVALUATION_PROFILES
    )
    if len(set(references)) != expected_references:
        raise RuntimeError("evaluation reference inventory is incomplete")
    _atomic_json(run_root / "evaluation_manifest.json", evaluation_manifest)
    return evaluation_manifest


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a non-boolean number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    return converted


def _interval(point: float, samples: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(point),
        "lcb95": float(np.percentile(samples, 2.5)),
        "ucb95": float(np.percentile(samples, 97.5)),
    }


def _bootstrap_means(
    values: np.ndarray, *, repetitions: int, seed: int
) -> np.ndarray:
    if values.ndim != 3 or not np.isfinite(values).all():
        raise ValueError("bootstrap values must be a finite [replicate,base,metric] array")
    replicate_count, base_count, metric_count = values.shape
    generator = np.random.default_rng(seed)
    result = np.empty((repetitions, metric_count), dtype=np.float64)
    chunk_size = 256
    for start in range(0, repetitions, chunk_size):
        stop = min(start + chunk_size, repetitions)
        chunk = stop - start
        replicate_indices = generator.integers(
            0, replicate_count, size=(chunk, replicate_count)
        )
        base_indices = generator.integers(
            0, base_count, size=(chunk, replicate_count, base_count)
        )
        selected = values[replicate_indices[:, :, None], base_indices]
        result[start:stop] = selected.mean(axis=(1, 2))
    return result


def _validate_evaluation_rows(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    replicate: int,
    profile: str,
    episode_count: int,
) -> None:
    if len(rows) != episode_count:
        raise ValueError("evaluation row count mismatch")
    expected_pairs = {
        (base_id, sign_mate)
        for base_id in range(episode_count // 2)
        for sign_mate in (-1, 1)
    }
    observed_pairs: set[tuple[int, int]] = set()
    source_profile = profile.split("_", maxsplit=1)[0]
    for row in rows:
        if row.get("schema") != EVALUATION_ROW_SCHEMA:
            raise ValueError("evaluation row schema mismatch")
        if row.get("arm") != arm or row.get("replicate") != replicate:
            raise ValueError("evaluation row arm/replicate mismatch")
        if row.get("profile") != profile:
            raise ValueError("evaluation row profile mismatch")
        base_id = row.get("base_id")
        sign_mate = row.get("sign_mate")
        if type(base_id) is not int or sign_mate not in (-1, 1):
            raise ValueError("evaluation row pair identity is invalid")
        if (base_id, sign_mate) in observed_pairs:
            raise ValueError("evaluation pair identity is duplicated")
        observed_pairs.add((base_id, sign_mate))
        spec = _evaluation_spec(
            source_profile,
            base_id=base_id,
            sign_mate=sign_mate,
            replicate=replicate,
        )
        for name in (
            "bit",
            "creator_slot",
            "successor_slot",
            "survivor_slot",
            "creator_duration",
            "gap",
            "successor_duration",
        ):
            if row.get(name) != getattr(spec, name):
                raise ValueError(f"evaluation row {name} provenance mismatch")
        utility = _finite_number(row.get("utility"), "evaluation utility")
        if not 0 <= utility <= 1:
            raise ValueError("evaluation utility is outside [0,1]")
        mark = row.get("mark")
        if mark not in (-1, 1):
            raise ValueError("evaluation mark is outside {-1,+1}")
        if row.get("mark_correct") != float(mark == spec.bit):
            raise ValueError("evaluation mark correctness mismatch")
        action_count = row.get("successor_action_count")
        if type(action_count) is not int or action_count != spec.successor_duration:
            raise ValueError("evaluation action count is invalid")
    if observed_pairs != expected_pairs:
        raise ValueError("evaluation sign-mated inventory mismatch")


def _validate_audit_rows(
    rows: list[dict[str, Any]], *, replicates: tuple[int, ...], episode_count: int
) -> None:
    if len(rows) != len(replicates) * episode_count:
        raise ValueError("audit row count mismatch")
    for replicate in replicates:
        selected = [row for row in rows if row.get("replicate") == replicate]
        expected_pairs = {
            (base_id, sign_mate)
            for base_id in range(episode_count // 2)
            for sign_mate in (-1, 1)
        }
        observed: set[tuple[int, int]] = set()
        for row in selected:
            if row.get("schema") != AUDIT_ROW_SCHEMA or row.get("arm") != "EHC":
                raise ValueError("audit row schema/arm mismatch")
            if row.get("profile") != "heldout_deterministic":
                raise ValueError("audit profile mismatch")
            identity = (row.get("base_id"), row.get("sign_mate"))
            if identity in observed:
                raise ValueError("audit pair identity is duplicated")
            observed.add(identity)
            if type(identity[0]) is not int or identity[1] not in (-1, 1):
                raise ValueError("audit pair identity is invalid")
            spec = _evaluation_spec(
                "heldout",
                base_id=identity[0],
                sign_mate=identity[1],
                replicate=replicate,
            )
            if row.get("bit") != spec.bit:
                raise ValueError("audit bit provenance mismatch")
            if row.get("natural_mark") not in (-1, 1):
                raise ValueError("audit natural mark is invalid")
            if row.get("mark_correct") != float(
                row.get("natural_mark") == spec.bit
            ):
                raise ValueError("audit mark correctness mismatch")
            if row.get("successor_action_count") != spec.successor_duration:
                raise ValueError("audit action count mismatch")
            for name in (
                "mark_correct",
                "natural_utility",
                "flipped_utility",
                "action_tv",
                "utility_drop",
            ):
                value = _finite_number(row.get(name), f"audit {name}")
                if not -1 <= value <= 1:
                    raise ValueError(f"audit {name} is outside [-1,1]")
            if not math.isclose(
                float(row["utility_drop"]),
                float(row["natural_utility"]) - float(row["flipped_utility"]),
                abs_tol=1e-12,
            ):
                raise ValueError("audit utility-drop identity mismatch")
        if observed != expected_pairs:
            raise ValueError("audit sign-mated inventory mismatch")


def select_result_branch(predicate_inputs: Mapping[str, object]) -> str:
    required = {
        "operational_valid",
        "source_identifiable",
        "max_arm_lcb",
        "max_arm_ucb",
        "g_team_lcb",
        "g_team_ucb",
        "g_link_lcb",
        "g_link_ucb",
        "mark_accuracy_lcb",
        "mark_accuracy_ucb",
        "action_tv_lcb",
        "action_tv_ucb",
        "utility_drop_lcb",
        "utility_drop_ucb",
        "ehc_utility_lcb",
        "ehc_utility_ucb",
    }
    if set(predicate_inputs) != required:
        raise ValueError("G2 selector predicate inventory mismatch")
    if type(predicate_inputs["operational_valid"]) is not bool or type(
        predicate_inputs["source_identifiable"]
    ) is not bool:
        raise ValueError("G2 selector booleans are invalid")
    numbers = {
        name: _finite_number(value, name)
        for name, value in predicate_inputs.items()
        if name not in ("operational_valid", "source_identifiable")
    }
    if not predicate_inputs["operational_valid"]:
        return "INVALID_OPERATIONAL_HANDOFF_G2"
    if not predicate_inputs["source_identifiable"]:
        return "SOURCE_NON_IDENTIFIABLE_HANDOFF_G2"
    if numbers["max_arm_ucb"] < 0.80:
        return "NO_ACCESS_HANDOFF_G2"
    if numbers["max_arm_lcb"] < 0.80 <= numbers["max_arm_ucb"]:
        return "UNDERPOWERED_ACCESS_HANDOFF_G2"
    battery_pass = (
        numbers["mark_accuracy_lcb"] > 0.75
        and numbers["action_tv_lcb"] > 0.10
        and numbers["utility_drop_lcb"] > 0.10
        and numbers["ehc_utility_lcb"] >= 0.80
    )
    if (
        numbers["g_team_lcb"] > 0.10
        and numbers["g_link_lcb"] > 0.10
        and battery_pass
    ):
        return "EHC_HANDOFF_SUPPORTED_G2"
    if numbers["g_team_ucb"] <= 0.10:
        return "TEAM_REC_SUFFICIENT_HANDOFF_G2"
    if numbers["g_link_ucb"] <= 0.10:
        return "LINK_NULL_HANDOFF_G2"
    confident_battery_failure = (
        numbers["mark_accuracy_ucb"] <= 0.75
        or numbers["action_tv_ucb"] <= 0.10
        or numbers["utility_drop_ucb"] <= 0.10
        or numbers["ehc_utility_ucb"] < 0.80
    )
    if (
        numbers["g_team_lcb"] > 0.10
        and numbers["g_link_lcb"] > 0.10
        and confident_battery_failure
    ):
        return "REPRESENTATION_ONLY_HANDOFF_G2"
    return "MIXED_UNDERPOWERED_HANDOFF_G2"


def _expected_evaluation_references(
    budget: Mapping[str, int], run_root: Path
) -> list[str]:
    return sorted(
        _relative(
            run_root,
            run_root
            / "evaluation"
            / arm
            / f"replicate_{replicate}"
            / f"{profile}.jsonl",
        )
        for replicate in _replicates(budget)
        for arm in ARM_NAMES
        for profile in EVALUATION_PROFILES
    )


def _derive_analysis(run_root: Path, *, formal: bool) -> dict[str, Any]:
    manifest = _read_json(run_root / "manifest.json")
    evaluation_manifest = _read_json(run_root / "evaluation_manifest.json")
    budget = _budget(formal)
    source_commit = str(manifest.get("source_commit"))
    expected_manifest = _manifest_identity(
        formal=formal, source_commit=source_commit, budget=budget
    )
    _validate_manifest_identity(manifest, expected_manifest)
    if manifest.get("status") != "TRAIN_COMPLETE":
        raise ValueError("training manifest is not complete")
    if evaluation_manifest.get("schema") != EVALUATION_MANIFEST_SCHEMA:
        raise ValueError("evaluation manifest schema mismatch")
    for key, value in (
        ("source_family", SOURCE_FAMILY),
        ("source_commit", source_commit),
        ("formal", formal),
        ("backend", "cpu"),
        ("torch_threads", 1),
        ("status", "EVALUATION_COMPLETE"),
        ("budget", budget),
    ):
        if evaluation_manifest.get(key) != value:
            raise ValueError(f"evaluation manifest {key} mismatch")

    checkpoint_references = manifest.get("checkpoint_references")
    expected_checkpoint_references = sorted(
        _relative(
            run_root,
            run_root
            / "checkpoints"
            / arm
            / f"replicate_{replicate}"
            / f"update_{budget['updates']}.pt",
        )
        for replicate in _replicates(budget)
        for arm in ARM_NAMES
    )
    if checkpoint_references != expected_checkpoint_references:
        raise ValueError("checkpoint reference inventory mismatch")
    if len(set(checkpoint_references)) != len(checkpoint_references):
        raise ValueError("checkpoint reference is duplicated")
    training_exposure: dict[str, dict[str, int]] = {}
    for replicate in _replicates(budget):
        for arm in ARM_NAMES:
            reference = _relative(
                run_root,
                run_root
                / "checkpoints"
                / arm
                / f"replicate_{replicate}"
                / f"update_{budget['updates']}.pt",
            )
            checkpoint_path = _resolve_reference(run_root, reference)
            if not checkpoint_path.is_file():
                raise ValueError("checkpoint reference is missing")
            checkpoint_state = load_checkpoint(
                checkpoint_path,
                expected_source_commit=source_commit,
                expected_arm=arm,
                expected_replicate=replicate,
            )
            if checkpoint_state.completed_updates != budget["updates"]:
                raise ValueError("checkpoint completed-update exposure mismatch")
            if checkpoint_state.optimizer_steps != budget["updates"] * PPO_PASSES:
                raise ValueError("checkpoint optimizer exposure mismatch")
            minimum_episodes = 2560 if formal else 1
            if checkpoint_state.episodes_completed < minimum_episodes:
                raise ValueError("checkpoint episode exposure is below contract")
            training_exposure[f"{arm}:replicate_{replicate}"] = {
                "updates": checkpoint_state.completed_updates,
                "optimizer_steps": checkpoint_state.optimizer_steps,
                "episodes_completed": checkpoint_state.episodes_completed,
            }
    if list(run_root.rglob("latest.pt")):
        raise ValueError("rolling checkpoint remains after TRAIN_COMPLETE")
    if [path for path in run_root.rglob("*.tmp") if path.is_file()]:
        raise ValueError("temporary artifact remains after pipeline completion")

    evaluation_references = evaluation_manifest.get("evaluation_references")
    if evaluation_references != _expected_evaluation_references(budget, run_root):
        raise ValueError("evaluation reference inventory mismatch")
    source_control_path = _resolve_reference(
        run_root, evaluation_manifest.get("source_control_reference")
    )
    audit_path = _resolve_reference(run_root, evaluation_manifest.get("audit_reference"))
    if not source_control_path.is_file() or not audit_path.is_file():
        raise ValueError("source-control or audit reference is missing")

    heldout_values = np.empty(
        (
            budget["replicates"],
            budget["evaluation_episodes_per_cell"] // 2,
            len(ARM_NAMES),
        ),
        dtype=np.float64,
    )
    for replicate in _replicates(budget):
        for arm_index, arm in enumerate(ARM_NAMES):
            for profile in EVALUATION_PROFILES:
                path = (
                    run_root
                    / "evaluation"
                    / arm
                    / f"replicate_{replicate}"
                    / f"{profile}.jsonl"
                )
                rows = _read_jsonl(path)
                _validate_evaluation_rows(
                    rows,
                    arm=arm,
                    replicate=replicate,
                    profile=profile,
                    episode_count=budget["evaluation_episodes_per_cell"],
                )
                if profile == "heldout_deterministic":
                    by_base: dict[int, list[float]] = {}
                    for row in rows:
                        by_base.setdefault(int(row["base_id"]), []).append(
                            float(row["utility"])
                        )
                    for base_id, utilities in by_base.items():
                        if len(utilities) != 2:
                            raise ValueError("heldout sign-mate cluster is incomplete")
                        heldout_values[replicate, base_id, arm_index] = float(
                            np.mean(utilities)
                        )

    source_controls = _read_json(source_control_path)
    if source_controls.get("schema") != SOURCE_CONTROL_SCHEMA:
        raise ValueError("source-control schema mismatch")
    if source_controls.get("source_commit") != source_commit:
        raise ValueError("source-control commit mismatch")
    information_gate_pass = source_controls.get("result") == INFORMATION_GATE_PASS
    controls_exact = (
        source_controls.get("constructive_team_rec_utility") == 1.0
        and source_controls.get("constructive_ehc_utility") == 1.0
        and source_controls.get("fresh_per_member_bound") == 0.5
        and source_controls.get("case_count") == 96
    )

    audit_rows = _read_jsonl(audit_path)
    _validate_audit_rows(
        audit_rows,
        replicates=_replicates(budget),
        episode_count=budget["audit_episodes_per_replicate"],
    )
    audit_values = np.empty(
        (
            budget["replicates"],
            budget["audit_episodes_per_replicate"] // 2,
            3,
        ),
        dtype=np.float64,
    )
    for replicate in _replicates(budget):
        selected = [row for row in audit_rows if row["replicate"] == replicate]
        for base_id in range(budget["audit_episodes_per_replicate"] // 2):
            cluster = [row for row in selected if row["base_id"] == base_id]
            audit_values[replicate, base_id] = np.mean(
                [
                    [row["mark_correct"], row["action_tv"], row["utility_drop"]]
                    for row in cluster
                ],
                axis=0,
            )

    utility_samples = _bootstrap_means(
        heldout_values,
        repetitions=budget["bootstrap_repetitions"],
        seed=SEED_REGISTRY.bootstrap,
    )
    audit_samples = _bootstrap_means(
        audit_values,
        repetitions=budget["bootstrap_repetitions"],
        seed=SEED_REGISTRY.bootstrap + 1,
    )
    utility_points = heldout_values.mean(axis=(0, 1))
    audit_points = audit_values.mean(axis=(0, 1))
    arm_metrics = {
        arm: _interval(float(utility_points[index]), utility_samples[:, index])
        for index, arm in enumerate(ARM_NAMES)
    }
    ehc_index = ARM_NAMES.index("EHC")
    team_index = ARM_NAMES.index("TEAM_REC")
    dum_index = ARM_NAMES.index("DUM")
    g_team_samples = utility_samples[:, ehc_index] - utility_samples[:, team_index]
    g_link_samples = utility_samples[:, ehc_index] - utility_samples[:, dum_index]
    g_team = _interval(
        float(utility_points[ehc_index] - utility_points[team_index]),
        g_team_samples,
    )
    g_link = _interval(
        float(utility_points[ehc_index] - utility_points[dum_index]),
        g_link_samples,
    )
    mark_accuracy = _interval(float(audit_points[0]), audit_samples[:, 0])
    action_tv = _interval(float(audit_points[1]), audit_samples[:, 1])
    utility_drop = _interval(float(audit_points[2]), audit_samples[:, 2])
    max_arm_lcb = max(metric["lcb95"] for metric in arm_metrics.values())
    max_arm_ucb = max(metric["ucb95"] for metric in arm_metrics.values())
    quota_pass = all(
        sum(row["replicate"] == replicate for row in audit_rows) >= 128
        for replicate in _replicates(budget)
    )
    source_identifiable = information_gate_pass and controls_exact and quota_pass
    predicate_inputs: dict[str, object] = {
        "operational_valid": True,
        "source_identifiable": source_identifiable,
        "max_arm_lcb": max_arm_lcb,
        "max_arm_ucb": max_arm_ucb,
        "g_team_lcb": g_team["lcb95"],
        "g_team_ucb": g_team["ucb95"],
        "g_link_lcb": g_link["lcb95"],
        "g_link_ucb": g_link["ucb95"],
        "mark_accuracy_lcb": mark_accuracy["lcb95"],
        "mark_accuracy_ucb": mark_accuracy["ucb95"],
        "action_tv_lcb": action_tv["lcb95"],
        "action_tv_ucb": action_tv["ucb95"],
        "utility_drop_lcb": utility_drop["lcb95"],
        "utility_drop_ucb": utility_drop["ucb95"],
        "ehc_utility_lcb": arm_metrics["EHC"]["lcb95"],
        "ehc_utility_ucb": arm_metrics["EHC"]["ucb95"],
    }
    result = select_result_branch(predicate_inputs)
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "backend": "cpu",
        "torch_threads": 1,
        "status": "COMPLETE",
        "budget": budget,
        "bootstrap_repetitions": budget["bootstrap_repetitions"],
        "checkpoint_references": checkpoint_references,
        "evaluation_references": evaluation_references,
        "source_control_reference": evaluation_manifest["source_control_reference"],
        "audit_reference": evaluation_manifest["audit_reference"],
        "operational_errors": [],
        "training_exposure": training_exposure,
        "metrics": {
            "arm_utility": arm_metrics,
            "g_team": g_team,
            "g_link": g_link,
            "mark_accuracy": mark_accuracy,
            "action_tv": action_tv,
            "utility_drop": utility_drop,
        },
        "source_identification": {
            "information_gate_pass": information_gate_pass,
            "controls_exact": controls_exact,
            "natural_quota_pass": quota_pass,
        },
        "predicate_inputs": predicate_inputs,
        "result": result,
    }


def analyze_run(run_root: Path, *, formal: bool) -> dict[str, Any]:
    configure_cpu_runtime()
    try:
        analysis = _derive_analysis(run_root, formal=formal)
    except Exception as error:
        manifest = _read_json(run_root / "manifest.json")
        analysis = {
            "schema": ANALYSIS_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": manifest.get("source_commit"),
            "formal": formal,
            "backend": "cpu",
            "torch_threads": 1,
            "status": "COMPLETE",
            "budget": _budget(formal),
            "operational_errors": [f"{type(error).__name__}: {error}"],
            "predicate_inputs": {
                "operational_valid": False,
                "source_identifiable": False,
                "max_arm_lcb": 0.0,
                "max_arm_ucb": 0.0,
                "g_team_lcb": 0.0,
                "g_team_ucb": 0.0,
                "g_link_lcb": 0.0,
                "g_link_ucb": 0.0,
                "mark_accuracy_lcb": 0.0,
                "mark_accuracy_ucb": 0.0,
                "action_tv_lcb": 0.0,
                "action_tv_ucb": 0.0,
                "utility_drop_lcb": 0.0,
                "utility_drop_ucb": 0.0,
                "ehc_utility_lcb": 0.0,
                "ehc_utility_ucb": 0.0,
            },
            "result": "INVALID_OPERATIONAL_HANDOFF_G2",
        }
    _atomic_json(run_root / "analysis_result.json", analysis)
    return analysis


def validate_formal_result(run_root: Path) -> dict[str, Any]:
    persisted = _read_json(run_root / "analysis_result.json")
    if persisted.get("formal") is not True:
        raise ValueError("formal result validation requires formal=true")
    rederived = _derive_analysis(run_root, formal=True)
    if persisted != rederived:
        raise ValueError("persisted formal analysis does not equal rederived evidence")
    if select_result_branch(rederived["predicate_inputs"]) != rederived["result"]:
        raise ValueError("persisted formal result branch is not reproducible")
    return rederived


def exercise_run(run_root: Path, *, source_commit: str) -> dict[str, Any]:
    if run_root.exists():
        raise FileExistsError(f"exercise run root already exists: {run_root}")
    train_run(
        run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
    )
    evaluate_run(run_root, formal=False)
    return analyze_run(run_root, formal=False)


def _add_run_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-root", type=Path, required=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train")
    _add_run_root(train)
    train.add_argument("--source-commit", type=_source_commit, required=True)
    train.add_argument("--formal", action="store_true")
    train.add_argument("--authorization-token")

    evaluate = subparsers.add_parser("evaluate")
    _add_run_root(evaluate)
    evaluate.add_argument("--formal", action="store_true")

    analyze = subparsers.add_parser("analyze")
    _add_run_root(analyze)
    analyze.add_argument("--formal", action="store_true")

    exercise = subparsers.add_parser("exercise")
    _add_run_root(exercise)
    exercise.add_argument("--source-commit", type=_source_commit, required=True)

    arguments = parser.parse_args()
    if arguments.command == "train":
        payload = train_run(
            arguments.run_root,
            source_commit=arguments.source_commit,
            formal=arguments.formal,
            authorization_token=arguments.authorization_token,
        )
        summary = {"status": payload["status"], "formal": payload["formal"]}
    elif arguments.command == "evaluate":
        payload = evaluate_run(arguments.run_root, formal=arguments.formal)
        summary = {"status": payload["status"], "formal": payload["formal"]}
    elif arguments.command == "analyze":
        payload = analyze_run(arguments.run_root, formal=arguments.formal)
        summary = {
            "status": payload["status"],
            "formal": payload["formal"],
            "result": payload["result"],
        }
    else:
        payload = exercise_run(
            arguments.run_root, source_commit=arguments.source_commit
        )
        summary = {
            "status": payload["status"],
            "formal": payload["formal"],
            "result": payload["result"],
            "artifact": str(arguments.run_root / "analysis_result.json"),
        }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
