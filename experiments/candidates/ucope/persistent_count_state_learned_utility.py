"""Frozen train/evaluate/analyze package for UCOPE-B1.

This module owns the matched tabular controllers, deterministic training tapes,
exact weighted real-transition panels, retained artifacts, and frozen branch
precedence.  It grants no authority to execute a registered full.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import random
import re
from dataclasses import asdict, dataclass
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping

import numpy as np

from experiments.candidates.ucope.persistent_count_state_host import (
    HAZARDS,
    L,
    PERSISTENT,
    PREFIX_PERIODS,
    REGIMES,
    S,
    STRATA,
    THETA_L,
    THETA_S,
    TRIAL5_REDRAW,
    Generation,
    PersistentCountStateHost,
    canonical_bytes,
    fraction_string,
    generation_for_block,
    history_probability,
    uniform_for_mark,
)


ASSIGNMENT_ID = "UCOPE-B1-PERSISTENT-COUNT-STATE-LEARNED-UTILITY"
CANDIDATE = "CAND-VSP-07-UCOPE@adversarial-revision-v6"
HOST_ID = "ucope_five_trial_marked_renewal_contextual_bandit_v1"
RAW_OUTPUT_BINDING = "ucope.persistent_count_state_learned_utility.v1"
SCHEMA_VERSION = 1
COUNT = "COUNT_LEARNER"
BLIND = "COUNT_BLIND_LEARNER"
ORACLE = "BAYES_ORACLE_EVALUATION_ONLY"
LEARNED_ARMS = (COUNT, BLIND)
ARMS = (COUNT, BLIND, ORACLE)
MASTER_SEEDS = (1103, 2207, 3301, 4409)
D_VALUES = (-2, -1, 0, 1, 2)
ACTIONS = (S, L)
CANONICAL_HISTORIES = tuple(product((0, 1), repeat=4))
UNIFORM_STRATA = (
    ("LOW", Fraction(1, 20), Fraction(1, 10)),
    ("MIDDLE", Fraction(1, 2), Fraction(8, 10)),
    ("HIGH", Fraction(19, 20), Fraction(1, 10)),
)
BRANCHES = (
    "B1_INVALID_CONTRACT",
    "B1_LEAKAGE_OR_INFORMATION_MISMATCH",
    "B1_HOST_OR_TRAINER_CALIBRATION_FAILED",
    "B1_COUNT_USE_NOT_ESTABLISHED_AT_CAP",
    "B1_LEARNED_COUNT_USE_WITHOUT_UTILITY",
    "B1_UTILITY_WITHOUT_BOUNDARY_SPECIFICITY",
    "B1_LOCAL_LEARNED_COUNT_USE_AND_UTILITY_SUPPORTED",
    "B1_INDETERMINATE_AT_CAP",
)
SOURCE_PATHS = (
    "experiments/candidates/ucope/persistent_count_state_host.py",
    "experiments/candidates/ucope/persistent_count_state_learned_utility.py",
    "scripts/run_ucope_b1_persistent_count_state_learned_utility.py",
    "tests/experiments/candidates/ucope/test_persistent_count_state_learned_utility.py",
    "docs/research/candidates/ucope/CODE_SCIENCE_INDEX.md",
)
FORBIDDEN_INPUTS = (
    "latent_regime",
    "stratum",
    "raw_history",
    "raw_long_alias",
    "cell_identity",
    "partner_identity",
    "slot_identity",
    "owner_identity",
    "source_identity",
    "seed_identity",
    "executor_generation",
    "future_uniform",
    "future_outcome",
    "task_reward",
    "cached_state",
)
CLAIM_BOUNDARY = (
    "One supplied immutable count statistic in one finite five-trial tabular host; "
    "no prefix acquisition value, learned belief discovery, target-environment persistence, "
    "task-return/sample-efficiency, transfer, promotion, C, or formal claim."
)


@dataclass(frozen=True)
class ExperimentConfig:
    host_id: str
    learned_arms: tuple[str, ...]
    oracle_arm: str
    strata: tuple[str, ...]
    master_seeds: tuple[int, ...]
    blocks_per_replica: int
    trials_per_block: int
    panel_histories: int
    k_search: int
    hypothetical_transitions: int
    technical_only: bool

    def to_json(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("learned_arms", "strata", "master_seeds"):
            value[key] = list(value[key])
        return value


def registered_config() -> ExperimentConfig:
    return ExperimentConfig(
        host_id=HOST_ID,
        learned_arms=LEARNED_ARMS,
        oracle_arm=ORACLE,
        strata=STRATA,
        master_seeds=MASTER_SEEDS,
        blocks_per_replica=4096,
        trials_per_block=5,
        panel_histories=16,
        k_search=0,
        hypothetical_transitions=0,
        technical_only=False,
    )


def technical_smoke_config() -> ExperimentConfig:
    return ExperimentConfig(
        **{
            **registered_config().to_json(),
            "learned_arms": LEARNED_ARMS,
            "strata": STRATA,
            "master_seeds": (MASTER_SEEDS[0],),
            "blocks_per_replica": 128,
            "technical_only": True,
        }
    )


def parse_fraction(value: str) -> Fraction:
    if not isinstance(value, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?", value):
        raise ValueError("non-canonical rational string")
    return Fraction(value)


def _write_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError(f"artifact already exists: {path}")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_claim(root: Path, *, source_commit: str, run_id: str, technical_only: bool) -> dict[str, Any]:
    claim = _read_json(root / "registered_claim.json")
    expected = {
        "artifact_kind": "UCOPE_B1_TECHNICAL_EXERCISE_CLAIM" if technical_only else "UCOPE_B1_REGISTERED_RUN_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_only,
        "canonical_result_name": "raw_result.json",
    }
    if claim != expected:
        raise ValueError("registered claim identity or canonical result binding drift")
    return claim


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _binding(path: Path, *, rows: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }
    if rows is not None:
        value["rows"] = int(rows)
    return value


def _validate_binding(root: Path, binding: Mapping[str, Any], *, subdir: str | None = None) -> Path:
    path = root / (subdir or "") / str(binding["path"])
    if not path.is_file():
        raise ValueError(f"bound artifact absent: {path}")
    if path.stat().st_size != int(binding["size_bytes"]) or _sha256_file(path) != binding["sha256"]:
        raise ValueError(f"bound artifact drift: {path}")
    return path


class _GzipWriter:
    def __init__(self, path: Path) -> None:
        if path.exists() or path.with_suffix(path.suffix + ".tmp").exists():
            raise FileExistsError(f"artifact already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.temporary = path.with_suffix(path.suffix + ".tmp")
        self.raw = self.temporary.open("wb")
        self.stream = gzip.GzipFile(filename="", mode="wb", fileobj=self.raw, mtime=0)
        self.rows = 0

    def write(self, value: Mapping[str, Any]) -> None:
        self.stream.write(canonical_bytes(dict(value)) + b"\n")
        self.rows += 1

    def __enter__(self) -> "_GzipWriter":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stream.close()
        self.raw.close()
        if exc_type is None:
            os.replace(self.temporary, self.path)
        elif self.temporary.exists():
            self.temporary.unlink()


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def _derive_seed(master_seed: int, stratum: str, stream: str) -> int:
    digest = hashlib.sha256(
        f"{ASSIGNMENT_ID}|{master_seed}|{stratum}|{stream}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _exact_uniform(rng: random.Random) -> Fraction:
    return Fraction(rng.getrandbits(64), 2**64)


def _regime(rng: random.Random) -> str:
    return REGIMES[rng.getrandbits(1)]


def observation(arm: str, true_d: int) -> dict[str, object]:
    if arm not in LEARNED_ARMS:
        raise ValueError("observation is only defined for learned arms")
    if true_d not in D_VALUES:
        raise ValueError("count state outside support")
    return {
        "registered_noncount_context": "ucope-trial5-h3-c1-period-choice-v1",
        "d": int(true_d if arm == COUNT else 0),
    }


class TabularQController:
    """Matched zero-initialized float64 5x2 controller."""

    def __init__(self) -> None:
        self.q = np.zeros((5, 2), dtype=np.float64)
        self.visits = np.zeros((5, 2), dtype=np.int64)
        self.return_sum = np.zeros((5, 2), dtype=np.float64)

    @staticmethod
    def row_index(d: int) -> int:
        if d not in D_VALUES:
            raise ValueError("visible d outside support")
        return d + 2

    @staticmethod
    def action_index(action: str) -> int:
        if action not in ACTIONS:
            raise ValueError("unknown action")
        return 0 if action == S else 1

    def policy_call(self, visible_d: int, forced_action: str | None = None) -> str:
        row = self.row_index(visible_d)
        if forced_action is not None:
            if forced_action not in ACTIONS:
                raise ValueError("invalid sealed-tape action")
            return forced_action
        return S if self.q[row, 0] >= self.q[row, 1] else L

    def update(self, visible_d: int, action: str, reward: int) -> None:
        if reward not in (0, 1, 2):
            raise ValueError("trial-5 AUC return outside support")
        row, column = self.row_index(visible_d), self.action_index(action)
        self.visits[row, column] += 1
        self.return_sum[row, column] += np.float64(reward)
        count = np.float64(self.visits[row, column])
        self.q[row, column] += (np.float64(reward) - self.q[row, column]) / count

    def to_json(self) -> dict[str, Any]:
        return {
            "class": "TabularQController",
            "shape": [5, 2],
            "parameter_count": 10,
            "dtype": "float64",
            "row_order": list(D_VALUES),
            "action_order": list(ACTIONS),
            "q": self.q.tolist(),
            "visits": self.visits.tolist(),
            "return_sum": self.return_sum.tolist(),
            "hidden_state": {},
            "critic": False,
            "auxiliary_head": False,
            "final_checkpoint_only": True,
        }

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> "TabularQController":
        if (
            value.get("class") != "TabularQController"
            or value.get("shape") != [5, 2]
            or value.get("parameter_count") != 10
            or value.get("dtype") != "float64"
            or value.get("row_order") != list(D_VALUES)
            or value.get("action_order") != list(ACTIONS)
            or value.get("hidden_state") != {}
            or value.get("critic") is not False
            or value.get("auxiliary_head") is not False
            or value.get("final_checkpoint_only") is not True
        ):
            raise ValueError("controller schema drift")
        controller = cls()
        controller.q = np.asarray(value["q"], dtype=np.float64)
        controller.visits = np.asarray(value["visits"], dtype=np.int64)
        controller.return_sum = np.asarray(value["return_sum"], dtype=np.float64)
        if controller.q.shape != (5, 2) or controller.visits.shape != (5, 2) or controller.return_sum.shape != (5, 2):
            raise ValueError("controller tensor shape drift")
        if not np.all(np.isfinite(controller.q)) or not np.all(np.isfinite(controller.return_sum)):
            raise ValueError("controller contains non-finite values")
        return controller


def _controller_digest(controller: TabularQController) -> str:
    return hashlib.sha256(canonical_bytes(controller.to_json())).hexdigest()


def _training_plan(config: ExperimentConfig, seed: int, stratum: str) -> list[dict[str, Any]]:
    regime_rng = random.Random(_derive_seed(seed, stratum, "regimes"))
    prefix_rng = random.Random(_derive_seed(seed, stratum, "prefix_uniforms"))
    trial5_rng = random.Random(_derive_seed(seed, stratum, "trial5_uniforms"))
    action_rng = random.Random(_derive_seed(seed, stratum, "action_tape"))
    actions = [ACTIONS[index % 2] for index in range(config.blocks_per_replica)]
    action_rng.shuffle(actions)
    rows: list[dict[str, Any]] = []
    for block in range(config.blocks_per_replica):
        prefix_regime = _regime(regime_rng)
        trial5_regime = prefix_regime if stratum == PERSISTENT else _regime(regime_rng)
        rows.append(
            {
                "block": block,
                "prefix_regime": prefix_regime,
                "trial5_regime": trial5_regime,
                "prefix_uniforms": [fraction_string(_exact_uniform(prefix_rng)) for _ in range(4)],
                "trial5_uniform": fraction_string(_exact_uniform(trial5_rng)),
                "exploration_action": actions[block],
            }
        )
    return rows


def build_manifest(*, config: ExperimentConfig, source_commit: str, run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be lowercase 40-hex")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", run_id):
        raise ValueError("run id is invalid")
    plans = {
        f"{seed}:{stratum}": _training_plan(config, seed, stratum)
        for seed in config.master_seeds
        for stratum in config.strata
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B1_FROZEN_MANIFEST",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": config.technical_only,
        "config": config.to_json(),
        "source_paths": list(SOURCE_PATHS),
        "controller_contract": {
            "shape": [5, 2],
            "parameter_count": 10,
            "dtype": "float64",
            "initialization": "all_zero",
            "update": "executed_cell_incremental_sample_mean",
            "greedy_tie_order": [S, L],
            "checkpoint": "after_exact_final_update_only",
            "hidden_state": {},
        },
        "training_plans": plans,
        "rng_derivation": "sha256(UCOPE-B1|master_seed|stratum|stream)[:8]-big-endian; Python-MT19937",
        "paired_across_learned_arms": True,
        "evaluation_panel": {
            "histories": ["".join(map(str, history)) for history in CANONICAL_HISTORIES],
            "uniform_strata": [
                {"id": name, "uniform": fraction_string(uniform), "mass": fraction_string(mass)}
                for name, uniform, mass in UNIFORM_STRATA
            ],
        },
    }
    manifest["content_sha256"] = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    return manifest


def _execute_training_block(
    *, controller: TabularQController, arm: str, stratum: str, plan: Mapping[str, Any]
) -> dict[str, Any]:
    generation = generation_for_block(int(plan["block"]))
    host = PersistentCountStateHost(
        stratum=stratum,
        prefix_regime=str(plan["prefix_regime"]),
        trial5_regime=str(plan["trial5_regime"]),
        generation=generation,
    )
    prefix = [
        host.step_prefix(uniform=parse_fraction(value), generation=generation)
        for value in plan["prefix_uniforms"]
    ]
    true_d, ledger_bytes = host.freeze_count(generation=generation)
    obs = observation(arm, true_d)
    visible_d = int(obs["d"])
    forced = str(plan["exploration_action"])
    action, before_policy, after_policy = host.policy_call(
        lambda d: controller.policy_call(d, forced),
        visible_d=visible_d,
        generation=generation,
    )
    trial5 = host.step_trial5(
        action=action,
        uniform=parse_fraction(str(plan["trial5_uniform"])),
        generation=generation,
        task_reward_placeholder={"forbidden": "ignored"},
    )
    host.close_block()
    controller.update(visible_d, action, trial5.physical_auc)
    history = [int(record.hit) for record in prefix]
    return {
        "phase": "train",
        "arm": arm,
        "stratum": stratum,
        "block": int(plan["block"]),
        "plan": dict(plan),
        "prefix_history": history,
        "N_S": history[0] + history[1],
        "N_L": history[2] + history[3],
        "E_S": 2,
        "E_L": 2,
        "true_d": true_d,
        "observation": obs,
        "observation_bytes_sha256": hashlib.sha256(canonical_bytes(obs)).hexdigest(),
        "action": action,
        "trial5_hit": trial5.hit,
        "return_auc": trial5.physical_auc,
        "environment_transitions": host.transition_count,
        "policy_calls": 1,
        "learner_calls": 1,
        "trainer_calls": 1,
        "optimizer_updates": 1,
        "ledger_frozen_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "ledger_unchanged_by_policy": before_policy == after_policy,
        "ledger_unchanged_by_trial5": trial5.ledger_before_sha == trial5.ledger_after_sha,
        "generation": generation.to_json(),
        "controller_state_before_block": {},
        "forbidden_inputs_present": [],
    }


def validate_training_row_reconstruction(
    row: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    master_seed: int,
    stratum: str,
    arm: str,
) -> None:
    """Rebuild one producer row from the frozen plan and host literals."""

    reconstructed = _execute_training_block(
        controller=TabularQController(),
        arm=arm,
        stratum=stratum,
        plan=plan,
    )
    reconstructed["master_seed"] = int(master_seed)
    if canonical_bytes(row) != canonical_bytes(reconstructed):
        differing = sorted(
            key
            for key in set(row) | set(reconstructed)
            if canonical_bytes(row.get(key)) != canonical_bytes(reconstructed.get(key))
        )
        raise ValueError(
            "training row fails independent manifest/host reconstruction: "
            + ",".join(differing)
        )


def expected_training_counts(config: Mapping[str, Any]) -> dict[str, int]:
    replicas = len(config["learned_arms"]) * len(config["strata"]) * len(config["master_seeds"])
    blocks = replicas * int(config["blocks_per_replica"])
    return {
        "learned_replicas": replicas,
        "training_blocks": blocks,
        "training_environment_transitions": blocks * 5,
        "training_policy_calls": blocks,
        "learner_calls": blocks,
        "trainer_calls": blocks,
        "optimizer_updates": blocks,
        "k_search": 0,
        "hypothetical_transitions": 0,
    }


def train(
    *, output_root: str | Path, source_commit: str, run_id: str, technical_smoke: bool = False
) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    config = technical_smoke_config() if technical_smoke else registered_config()
    claim = {
        "artifact_kind": "UCOPE_B1_REGISTERED_RUN_CLAIM" if not technical_smoke else "UCOPE_B1_TECHNICAL_EXERCISE_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_smoke,
        "canonical_result_name": "raw_result.json",
    }
    _write_once(root / "registered_claim.json", claim)
    manifest = build_manifest(config=config, source_commit=source_commit, run_id=run_id)
    _write_once(root / "frozen_manifest.json", manifest)
    checkpoints_dir = root / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    run_summaries: list[dict[str, Any]] = []
    sidecar_path = root / "train_rows.jsonl.gz"
    with _GzipWriter(sidecar_path) as sidecar:
        for seed in config.master_seeds:
            for stratum in config.strata:
                plan = manifest["training_plans"][f"{seed}:{stratum}"]
                for arm in config.learned_arms:
                    controller = TabularQController()
                    initial_digest = _controller_digest(controller)
                    for plan_row in plan:
                        row = _execute_training_block(
                            controller=controller, arm=arm, stratum=stratum, plan=plan_row
                        )
                        row["master_seed"] = int(seed)
                        sidecar.write(row)
                    checkpoint_name = f"{stratum.lower()}_{arm.lower()}_{seed}_final.json"
                    checkpoint = {
                        "schema_version": SCHEMA_VERSION,
                        "artifact_kind": "UCOPE_B1_FINAL_CHECKPOINT",
                        "source_commit": source_commit,
                        "run_id": run_id,
                        "master_seed": int(seed),
                        "stratum": stratum,
                        "arm": arm,
                        "initial_controller_sha256": initial_digest,
                        "updates": config.blocks_per_replica,
                        "controller": controller.to_json(),
                    }
                    checkpoint_path = checkpoints_dir / checkpoint_name
                    _write_once(checkpoint_path, checkpoint)
                    run_summaries.append(
                        {
                            "master_seed": int(seed),
                            "stratum": stratum,
                            "arm": arm,
                            "initial_controller_sha256": initial_digest,
                            "checkpoint": _binding(checkpoint_path),
                            "action_tape_sha256": hashlib.sha256(
                                canonical_bytes([row["exploration_action"] for row in plan])
                            ).hexdigest(),
                        }
                    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B1_TRAIN_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_smoke,
        "scientific_terminal_admitted": False,
        "config": config.to_json(),
        "manifest": _binding(root / "frozen_manifest.json"),
        "train_sidecar": _binding(sidecar_path, rows=expected_training_counts(config.to_json())["training_blocks"]),
        "run_summaries": run_summaries,
        "activity_counts": expected_training_counts(config.to_json()),
        "matching_contract": {
            "same_controller_class_shape_initialization_update_reward_checkpoint": True,
            "paired_environment_and_action_tapes": True,
            "count_access_sole_treatment_delta": True,
            "oracle_training_calls": 0,
        },
    }
    _write_once(root / "train_summary.json", summary)
    return summary


def _checkpoint_lookup(root: Path, summary: Mapping[str, Any]) -> dict[tuple[int, str, str], TabularQController]:
    values: dict[tuple[int, str, str], TabularQController] = {}
    for row in summary["run_summaries"]:
        path = _validate_binding(root, row["checkpoint"], subdir="checkpoints")
        checkpoint = _read_json(path)
        key = (int(checkpoint["master_seed"]), str(checkpoint["stratum"]), str(checkpoint["arm"]))
        if key in values:
            raise ValueError("duplicate checkpoint identity")
        values[key] = TabularQController.from_json(checkpoint["controller"])
    return values


def _panel_weight(
    *, stratum: str, prefix_regime: str, history: tuple[int, int, int, int], mass: Fraction
) -> Fraction:
    value = Fraction(1, 2) * history_probability(history, prefix_regime) * mass
    if stratum == TRIAL5_REDRAW:
        value *= Fraction(1, 2)
    return value


def _execute_panel_row(
    *,
    arm: str,
    stratum: str,
    prefix_regime: str,
    trial5_regime: str,
    history: tuple[int, int, int, int],
    uniform_id: str,
    trial5_uniform: Fraction,
    weight: Fraction,
    row_index: int,
    controller: TabularQController | None,
    master_seed: int | None,
) -> dict[str, Any]:
    generation = generation_for_block(row_index)
    host = PersistentCountStateHost(
        stratum=stratum,
        prefix_regime=prefix_regime,
        trial5_regime=trial5_regime,
        generation=generation,
    )
    prefix_records = []
    for bit, period in zip(history, PREFIX_PERIODS):
        uniform = uniform_for_mark(hit=bool(bit), hazard=HAZARDS[(prefix_regime, period)])
        prefix_records.append(host.step_prefix(uniform=uniform, generation=generation))
    true_d, ledger_bytes = host.freeze_count(generation=generation)
    expected_d = int(history[2]) + int(history[3]) - int(history[0]) - int(history[1])
    if true_d != expected_d:
        raise RuntimeError("host-generated count state disagrees with history")
    if arm == ORACLE:
        obs = None
        visible_d = true_d

        def policy_callable(d: int) -> str:
            # The stratum rule is prospectively fixed evaluator configuration;
            # neither latent realized regime is captured by this callable.
            return L if stratum == PERSISTENT and d > 0 else S

    else:
        if controller is None:
            raise ValueError("learned panel row requires a checkpoint")
        obs = observation(arm, true_d)
        visible_d = int(obs["d"])

        def policy_callable(d: int) -> str:
            return controller.policy_call(d)

    selected, before, after = host.policy_call(
        policy_callable,
        visible_d=visible_d,
        generation=generation,
    )
    trial5 = host.step_trial5(
        action=selected,
        uniform=trial5_uniform,
        generation=generation,
        task_reward_placeholder="ignored-evaluator-placeholder",
    )
    host.close_block()
    table = None if controller is None else controller.to_json()
    return {
        "phase": "evaluate",
        "arm": arm,
        "stratum": stratum,
        "master_seed": master_seed,
        "row_index": row_index,
        "prefix_regime": prefix_regime,
        "trial5_regime": trial5_regime,
        "prefix_history": "".join(map(str, history)),
        "generated_prefix_marks": [int(record.hit) for record in prefix_records],
        "N_S": int(history[0]) + int(history[1]),
        "N_L": int(history[2]) + int(history[3]),
        "E_S": 2,
        "E_L": 2,
        "true_d": true_d,
        "observation": obs,
        "observation_bytes_sha256": None if obs is None else hashlib.sha256(canonical_bytes(obs)).hexdigest(),
        "controller_table": table,
        "controller_sha256": None if controller is None else _controller_digest(controller),
        "action": selected,
        "trial5_uniform_stratum": uniform_id,
        "trial5_uniform": fraction_string(trial5_uniform),
        "trial5_hit": trial5.hit,
        "pathwise_auc": trial5.physical_auc,
        "always_s_hit": trial5_uniform < HAZARDS[(trial5_regime, S)],
        "always_s_auc": 2 * int(trial5_uniform < HAZARDS[(trial5_regime, S)]),
        "weight": fraction_string(weight),
        "weighted_auc": fraction_string(weight * trial5.physical_auc),
        "weighted_always_s_auc": fraction_string(weight * 2 * int(trial5_uniform < HAZARDS[(trial5_regime, S)])),
        "environment_transitions": host.transition_count,
        "policy_calls": 1,
        "updates_enabled": False,
        "ledger_frozen_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "ledger_unchanged_by_policy": before == after,
        "ledger_unchanged_by_trial5": trial5.ledger_before_sha == trial5.ledger_after_sha,
        "controller_hidden_state": {},
        "forbidden_inputs_present": [],
        "oracle_uses_realized_regime": False if arm == ORACLE else None,
    }


def _iter_panel_specs(stratum: str) -> Iterator[tuple[str, str, tuple[int, int, int, int], str, Fraction, Fraction]]:
    for prefix_regime in REGIMES:
        trial5_regimes = (prefix_regime,) if stratum == PERSISTENT else REGIMES
        for history in CANONICAL_HISTORIES:
            for trial5_regime in trial5_regimes:
                for uniform_id, uniform, mass in UNIFORM_STRATA:
                    yield (
                        prefix_regime,
                        trial5_regime,
                        history,
                        uniform_id,
                        uniform,
                        _panel_weight(
                            stratum=stratum,
                            prefix_regime=prefix_regime,
                            history=history,
                            mass=mass,
                        ),
                    )


def expected_evaluation_counts(config: Mapping[str, Any]) -> dict[str, int]:
    learned_persistent = len(config["master_seeds"]) * len(config["learned_arms"]) * 96
    learned_redraw = len(config["master_seeds"]) * len(config["learned_arms"]) * 192
    oracle = 96 + 192
    blocks = learned_persistent + learned_redraw + oracle
    return {
        "learned_persistent_evaluation_blocks": learned_persistent,
        "learned_redraw_evaluation_blocks": learned_redraw,
        "oracle_evaluation_blocks": oracle,
        "evaluation_blocks": blocks,
        "evaluation_environment_transitions": blocks * 5,
        "evaluation_policy_calls": blocks,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }


def evaluate(*, output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = _read_json(root / "train_summary.json")
    if not _config_matches(train_summary["config"], require_full=None):
        raise ValueError("train configuration is neither admitted full nor technical smoke")
    validate_claim(
        root,
        source_commit=str(train_summary["source_commit"]),
        run_id=str(train_summary["run_id"]),
        technical_only=bool(train_summary["technical_only"]),
    )
    config = train_summary["config"]
    controllers = _checkpoint_lookup(root, train_summary)
    sidecar_path = root / "evaluation_rows.jsonl.gz"
    row_index = 0
    with _GzipWriter(sidecar_path) as sidecar:
        for stratum in config["strata"]:
            specs = tuple(_iter_panel_specs(stratum))
            for seed in config["master_seeds"]:
                for arm in config["learned_arms"]:
                    controller = controllers[(int(seed), stratum, arm)]
                    for prefix_regime, trial5_regime, history, uniform_id, uniform, weight in specs:
                        sidecar.write(
                            _execute_panel_row(
                                arm=arm,
                                stratum=stratum,
                                prefix_regime=prefix_regime,
                                trial5_regime=trial5_regime,
                                history=history,
                                uniform_id=uniform_id,
                                trial5_uniform=uniform,
                                weight=weight,
                                row_index=row_index,
                                controller=controller,
                                master_seed=int(seed),
                            )
                        )
                        row_index += 1
            for prefix_regime, trial5_regime, history, uniform_id, uniform, weight in specs:
                sidecar.write(
                    _execute_panel_row(
                        arm=ORACLE,
                        stratum=stratum,
                        prefix_regime=prefix_regime,
                        trial5_regime=trial5_regime,
                        history=history,
                        uniform_id=uniform_id,
                        trial5_uniform=uniform,
                        weight=weight,
                        row_index=row_index,
                        controller=None,
                        master_seed=None,
                    )
                )
                row_index += 1
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B1_EVALUATION_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": train_summary["technical_only"],
        "scientific_terminal_admitted": False,
        "config": config,
        "evaluation_sidecar": _binding(sidecar_path, rows=row_index),
        "activity_counts": expected_evaluation_counts(config),
        "updates_enabled": False,
        "panel_unavailable_to_training": True,
        "ledger_or_action_injection": False,
    }
    _write_once(root / "evaluation_summary.json", summary)
    return summary


def _expected_train_plan_index(manifest: Mapping[str, Any]) -> dict[tuple[int, str, int], Mapping[str, Any]]:
    index: dict[tuple[int, str, int], Mapping[str, Any]] = {}
    for key, rows in manifest["training_plans"].items():
        seed_text, stratum = key.split(":", 1)
        for row in rows:
            identity = (int(seed_text), stratum, int(row["block"]))
            if identity in index:
                raise ValueError("duplicate manifest training identity")
            index[identity] = row
    return index


def _config_matches(config: Mapping[str, Any], *, require_full: bool | None) -> bool:
    full = registered_config().to_json()
    smoke = technical_smoke_config().to_json()
    return (
        dict(config) == full
        if require_full is True
        else dict(config) == smoke
        if require_full is False
        else dict(config) in (full, smoke)
    )


def validate_train(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "train_summary.json")
    if summary.get("artifact_kind") != "UCOPE_B1_TRAIN_SUMMARY" or summary.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("train summary schema/binding drift")
    config = summary["config"]
    if not _config_matches(config, require_full=require_full):
        raise ValueError("train configuration does not match admitted full/smoke")
    if bool(summary["technical_only"]) != bool(config["technical_only"]) or summary["scientific_terminal_admitted"]:
        raise ValueError("train phase crossed the scientific terminal")
    validate_claim(
        root,
        source_commit=str(summary["source_commit"]),
        run_id=str(summary["run_id"]),
        technical_only=bool(summary["technical_only"]),
    )
    if summary["activity_counts"] != expected_training_counts(config):
        raise ValueError("training activity counts drift")
    manifest_path = _validate_binding(root, summary["manifest"])
    manifest = _read_json(manifest_path)
    declared = manifest.get("content_sha256")
    content = dict(manifest)
    content.pop("content_sha256", None)
    if declared != hashlib.sha256(canonical_bytes(content)).hexdigest():
        raise ValueError("manifest content binding drift")
    if manifest["config"] != config or manifest["source_commit"] != summary["source_commit"] or manifest["run_id"] != summary["run_id"]:
        raise ValueError("manifest/summary identity drift")
    if manifest["source_paths"] != list(SOURCE_PATHS) or manifest["controller_contract"] != build_manifest(
        config=registered_config() if not config["technical_only"] else technical_smoke_config(),
        source_commit=manifest["source_commit"],
        run_id=manifest["run_id"],
    )["controller_contract"]:
        raise ValueError("source/controller contract drift")
    expected_plan = _expected_train_plan_index(manifest)
    train_sidecar = _validate_binding(root, summary["train_sidecar"])
    recomputed: dict[tuple[int, str, str], TabularQController] = {}
    paired: dict[tuple[int, str, int], dict[str, Mapping[str, Any]]] = {}
    rows = 0
    for row in _read_jsonl(train_sidecar):
        rows += 1
        seed, stratum, arm, block = int(row["master_seed"]), str(row["stratum"]), str(row["arm"]), int(row["block"])
        if seed not in config["master_seeds"] or stratum not in config["strata"] or arm not in config["learned_arms"]:
            raise ValueError("training row roster drift")
        expected = expected_plan.get((seed, stratum, block))
        if expected is None or canonical_bytes(row["plan"]) != canonical_bytes(expected):
            raise ValueError("training sidecar/manifest plan drift")
        validate_training_row_reconstruction(
            row,
            plan=expected,
            master_seed=seed,
            stratum=stratum,
            arm=arm,
        )
        if row["environment_transitions"] != 5 or row["policy_calls"] != 1 or row["learner_calls"] != 1 or row["trainer_calls"] != 1 or row["optimizer_updates"] != 1:
            raise ValueError("per-block real activity drift")
        if not row["ledger_unchanged_by_policy"] or not row["ledger_unchanged_by_trial5"] or row["forbidden_inputs_present"] != [] or row["controller_state_before_block"] != {}:
            raise ValueError("ledger/information firewall failed")
        true_d = int(row["true_d"])
        if row["observation"] != observation(arm, true_d):
            raise ValueError("learned observation drift/leakage")
        key = (seed, stratum, arm)
        controller = recomputed.setdefault(key, TabularQController())
        controller.update(int(row["observation"]["d"]), str(row["action"]), int(row["return_auc"]))
        pair = paired.setdefault((seed, stratum, block), {})
        if arm in pair:
            raise ValueError("duplicate matched training row")
        pair[arm] = row
    if rows != int(summary["train_sidecar"]["rows"]) or rows != expected_training_counts(config)["training_blocks"]:
        raise ValueError("training sidecar row count drift")
    if len(paired) != len(expected_plan) or any(set(value) != set(LEARNED_ARMS) for value in paired.values()):
        raise ValueError("matched learned-arm coverage drift")
    compared = (
        "plan",
        "prefix_history",
        "N_S",
        "N_L",
        "E_S",
        "E_L",
        "true_d",
        "action",
        "trial5_hit",
        "return_auc",
        "ledger_frozen_sha256",
        "generation",
    )
    for pair in paired.values():
        if any(canonical_bytes(pair[COUNT][field]) != canonical_bytes(pair[BLIND][field]) for field in compared):
            raise ValueError("paired learned arms differ outside count observation")
    checkpoints = _checkpoint_lookup(root, summary)
    if set(checkpoints) != set(recomputed):
        raise ValueError("final checkpoint roster drift")
    zero_digest = _controller_digest(TabularQController())
    run_index = {
        (int(row["master_seed"]), str(row["stratum"]), str(row["arm"])): row
        for row in summary["run_summaries"]
    }
    for key, actual in checkpoints.items():
        expected = recomputed[key]
        if not np.array_equal(actual.visits, expected.visits) or not np.allclose(actual.return_sum, expected.return_sum, atol=0.0, rtol=0.0) or not np.allclose(actual.q, expected.q, atol=0.0, rtol=0.0):
            raise ValueError("checkpoint differs from lossless training sidecar")
        means = np.divide(
            actual.return_sum,
            actual.visits,
            out=np.zeros_like(actual.return_sum),
            where=actual.visits > 0,
        )
        if not np.allclose(actual.q, means, atol=1e-12, rtol=0.0):
            raise ValueError("Q differs from empirical real-return mean")
        if run_index[key]["initial_controller_sha256"] != zero_digest:
            raise ValueError("learned replicas were not byte-identically zero initialized")
        if int(actual.visits.sum()) != int(config["blocks_per_replica"]):
            raise ValueError("final checkpoint update count drift")
        action_counts = [
            str(row["exploration_action"])
            for row in manifest["training_plans"][f"{key[0]}:{key[1]}"]
        ]
        if action_counts.count(S) != int(config["blocks_per_replica"]) // 2 or action_counts.count(L) != int(config["blocks_per_replica"]) // 2:
            raise ValueError("sealed alternating action tape is not exactly balanced")
        if key[2] == BLIND:
            if actual.visits[2].tolist() != [int(config["blocks_per_replica"]) // 2] * 2 or int(actual.visits.sum()) != int(actual.visits[2].sum()):
                raise ValueError("count-blind visits escaped visible d=0")
    return summary


def _expected_panel_keys(config: Mapping[str, Any]) -> set[tuple[str, str, int | None, str, str, str, str]]:
    keys: set[tuple[str, str, int | None, str, str, str, str]] = set()
    for stratum in config["strata"]:
        specs = tuple(_iter_panel_specs(stratum))
        for seed in config["master_seeds"]:
            for arm in config["learned_arms"]:
                for prefix_regime, trial5_regime, history, uniform_id, _uniform, _weight in specs:
                    keys.add((arm, stratum, int(seed), prefix_regime, trial5_regime, "".join(map(str, history)), uniform_id))
        for prefix_regime, trial5_regime, history, uniform_id, _uniform, _weight in specs:
            keys.add((ORACLE, stratum, None, prefix_regime, trial5_regime, "".join(map(str, history)), uniform_id))
    return keys


def _row_key(row: Mapping[str, Any]) -> tuple[str, str, int | None, str, str, str, str]:
    return (
        str(row["arm"]),
        str(row["stratum"]),
        None if row["master_seed"] is None else int(row["master_seed"]),
        str(row["prefix_regime"]),
        str(row["trial5_regime"]),
        str(row["prefix_history"]),
        str(row["trial5_uniform_stratum"]),
    )


def _exact_j(rows: Iterable[Mapping[str, Any]]) -> Fraction:
    return sum((parse_fraction(str(row["weighted_auc"])) for row in rows), Fraction())


def _exact_always_s(rows: Iterable[Mapping[str, Any]]) -> Fraction:
    return sum((parse_fraction(str(row["weighted_always_s_auc"])) for row in rows), Fraction())


def validate_evaluation(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = validate_train(root, require_full=require_full)
    summary = _read_json(root / "evaluation_summary.json")
    if summary.get("artifact_kind") != "UCOPE_B1_EVALUATION_SUMMARY" or summary.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("evaluation summary schema/binding drift")
    if summary["config"] != train_summary["config"] or summary["source_commit"] != train_summary["source_commit"] or summary["run_id"] != train_summary["run_id"]:
        raise ValueError("evaluation/train identity drift")
    if bool(summary["technical_only"]) != bool(train_summary["technical_only"]) or summary["scientific_terminal_admitted"] or summary["updates_enabled"] or not summary["panel_unavailable_to_training"] or summary["ledger_or_action_injection"]:
        raise ValueError("evaluation update/injection/terminal firewall failed")
    if summary["activity_counts"] != expected_evaluation_counts(summary["config"]):
        raise ValueError("evaluation activity counts drift")
    sidecar = _validate_binding(root, summary["evaluation_sidecar"])
    rows = list(_read_jsonl(sidecar))
    if len(rows) != int(summary["evaluation_sidecar"]["rows"]):
        raise ValueError("evaluation sidecar row count drift")
    expected_keys = _expected_panel_keys(summary["config"])
    seen: set[tuple[str, str, int | None, str, str, str, str]] = set()
    controllers = _checkpoint_lookup(root, train_summary)
    weights_by_panel: dict[tuple[str, int | None, str], Fraction] = {}
    equal_d: dict[tuple[str, str, int | None, int], tuple[bytes | None, str]] = {}
    blind_substitution_actions: dict[tuple[str, int, str], str] = {}
    for row in rows:
        key = _row_key(row)
        if key in seen or key not in expected_keys:
            raise ValueError("duplicate or unexpected evaluation panel row")
        seen.add(key)
        arm, stratum, seed, prefix_regime, trial5_regime, history_text, uniform_id = key
        history = tuple(int(bit) for bit in history_text)
        true_d = history[2] + history[3] - history[0] - history[1]
        if row["generated_prefix_marks"] != list(history) or int(row["N_S"]) != history[0] + history[1] or int(row["N_L"]) != history[2] + history[3] or int(row["true_d"]) != true_d or row["E_S"] != 2 or row["E_L"] != 2:
            raise ValueError("panel did not generate the exact prefix/ledger normally")
        uniform_record = next((item for item in UNIFORM_STRATA if item[0] == uniform_id), None)
        if uniform_record is None or parse_fraction(str(row["trial5_uniform"])) != uniform_record[1]:
            raise ValueError("uniform stratum drift")
        expected_weight = _panel_weight(
            stratum=stratum,
            prefix_regime=prefix_regime,
            history=history,
            mass=uniform_record[2],
        )
        weight = parse_fraction(str(row["weight"]))
        if weight != expected_weight:
            raise ValueError("exact panel weight drift")
        if row["environment_transitions"] != 5 or row["policy_calls"] != 1 or row["updates_enabled"] or not row["ledger_unchanged_by_policy"] or not row["ledger_unchanged_by_trial5"] or row["controller_hidden_state"] != {} or row["forbidden_inputs_present"] != []:
            raise ValueError("evaluation real-call or firewall drift")
        if arm == ORACLE:
            expected_action = L if stratum == PERSISTENT and true_d > 0 else S
            if seed is not None or row["observation"] is not None or row["controller_table"] is not None or row["controller_sha256"] is not None or row["oracle_uses_realized_regime"] is not False:
                raise ValueError("oracle crossed evaluation-only belief boundary")
        else:
            if seed is None:
                raise ValueError("learned row lacks seed")
            controller = controllers[(seed, stratum, arm)]
            obs = observation(arm, true_d)
            expected_action = controller.policy_call(int(obs["d"]))
            if row["observation"] != obs or row["controller_table"] != controller.to_json() or row["controller_sha256"] != _controller_digest(controller):
                raise ValueError("evaluation row/checkpoint/observation drift")
            signature = (canonical_bytes(obs), expected_action)
            equality_key = (arm, stratum, seed, true_d if arm == COUNT else 0)
            prior = equal_d.setdefault(equality_key, signature)
            if prior != signature:
                raise ValueError("equal-d or blind observation/action invariance failed")
            if arm == BLIND:
                substitution_key = (stratum, seed, history_text)
                prior_action = blind_substitution_actions.setdefault(substitution_key, expected_action)
                if prior_action != expected_action or obs["d"] != 0:
                    raise ValueError("count-blind substitution invariance failed")
        if row["action"] != expected_action:
            raise ValueError("greedy/oracle action extraction drift")
        uniform = uniform_record[1]
        expected_hit = uniform < HAZARDS[(trial5_regime, expected_action)]
        expected_auc = int(expected_hit) * (2 if expected_action == S else 1)
        always_hit = uniform < HAZARDS[(trial5_regime, S)]
        if bool(row["trial5_hit"]) != expected_hit or int(row["pathwise_auc"]) != expected_auc or row["always_s_hit"] != always_hit or int(row["always_s_auc"]) != 2 * int(always_hit):
            raise ValueError("physical-time host/AUC accounting drift")
        if parse_fraction(str(row["weighted_auc"])) != weight * expected_auc or parse_fraction(str(row["weighted_always_s_auc"])) != weight * 2 * int(always_hit):
            raise ValueError("weighted AUC drift")
        panel_identity = (arm, seed, stratum)
        weights_by_panel[panel_identity] = weights_by_panel.get(panel_identity, Fraction()) + weight
    if seen != expected_keys or any(value != 1 for value in weights_by_panel.values()):
        raise ValueError("panel completeness or exact weight normalization failed")
    oracle_p = [row for row in rows if row["arm"] == ORACLE and row["stratum"] == PERSISTENT]
    oracle_r = [row for row in rows if row["arm"] == ORACLE and row["stratum"] == TRIAL5_REDRAW]
    if _exact_j(oracle_p) != Fraction(26571, 20000) or _exact_j(oracle_r) != 1 or _exact_always_s(oracle_p) != 1 or _exact_always_s(oracle_r) != 1:
        raise ValueError("oracle/always-S exact calibration failed")
    hs = [row for row in oracle_p if row["prefix_history"] == "1100"]
    hl = [row for row in oracle_p if row["prefix_history"] == "0011"]
    if {row["action"] for row in hs} != {S} or {row["action"] for row in hl} != {L}:
        raise ValueError("HS/HL oracle action calibration failed")
    return summary


def total_activity_counts(config: Mapping[str, Any]) -> dict[str, int]:
    training = expected_training_counts(config)
    evaluation = expected_evaluation_counts(config)
    return {
        **training,
        **{key: value for key, value in evaluation.items() if key not in ("learner_calls", "trainer_calls", "optimizer_updates")},
        "total_complete_blocks": training["training_blocks"] + evaluation["evaluation_blocks"],
        "total_environment_transitions": training["training_environment_transitions"] + evaluation["evaluation_environment_transitions"],
        "total_policy_calls": training["training_policy_calls"] + evaluation["evaluation_policy_calls"],
        "full_runs": 0 if config["technical_only"] else 1,
        "sweeps_retries_rescues_extra_seeds_extra_strata_or_posthoc_arms": 0,
    }


def _action_maps(rows: list[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    maps: dict[str, Any] = {}
    for seed in config["master_seeds"]:
        seed_map: dict[str, Any] = {}
        for stratum in config["strata"]:
            stratum_map: dict[str, Any] = {}
            for arm in config["learned_arms"]:
                relevant = [row for row in rows if row["master_seed"] == seed and row["stratum"] == stratum and row["arm"] == arm]
                values: dict[str, str] = {}
                for d in D_VALUES:
                    actions = {str(row["action"]) for row in relevant if int(row["true_d"]) == d}
                    values[str(d)] = next(iter(actions)) if len(actions) == 1 else "NONINVARIANT"
                stratum_map[arm] = values
            seed_map[stratum] = stratum_map
        maps[str(seed)] = seed_map
    return maps


def _derive_metrics(root: Path) -> dict[str, Any]:
    train_summary = _read_json(root / "train_summary.json")
    config = train_summary["config"]
    eval_summary = _read_json(root / "evaluation_summary.json")
    rows = list(_read_jsonl(_validate_binding(root, eval_summary["evaluation_sidecar"])))
    maps = _action_maps(rows, config)
    j: dict[str, Any] = {}
    deltas: dict[str, Any] = {}
    for seed in config["master_seeds"]:
        seed_j: dict[str, Any] = {}
        for stratum in config["strata"]:
            values: dict[str, str] = {}
            for arm in config["learned_arms"]:
                relevant = [row for row in rows if row["master_seed"] == seed and row["stratum"] == stratum and row["arm"] == arm]
                values[arm] = fraction_string(_exact_j(relevant))
            seed_j[stratum] = values
        j[str(seed)] = seed_j
        deltas[str(seed)] = {
            "Delta_P": fraction_string(parse_fraction(seed_j[PERSISTENT][COUNT]) - parse_fraction(seed_j[PERSISTENT][BLIND])),
            "Delta_R": fraction_string(parse_fraction(seed_j[TRIAL5_REDRAW][COUNT]) - parse_fraction(seed_j[TRIAL5_REDRAW][BLIND])),
        }
    oracle = {}
    always_s = {}
    for stratum in config["strata"]:
        relevant = [row for row in rows if row["master_seed"] is None and row["stratum"] == stratum and row["arm"] == ORACLE]
        oracle[stratum] = fraction_string(_exact_j(relevant))
        always_s[stratum] = fraction_string(_exact_always_s(relevant))
    checkpoints = _checkpoint_lookup(root, train_summary)
    floors: dict[str, Any] = {}
    q_mean_errors: dict[str, str] = {}
    for (seed, stratum, arm), controller in checkpoints.items():
        key = f"{seed}:{stratum}:{arm}"
        if arm == COUNT:
            floors[key] = bool(np.all(controller.visits >= 64)) if not config["technical_only"] else None
        else:
            floors[key] = bool(controller.visits[2].tolist() == [2048, 2048] and int(controller.visits.sum()) == 4096) if not config["technical_only"] else None
        means = np.divide(controller.return_sum, controller.visits, out=np.zeros_like(controller.return_sum), where=controller.visits > 0)
        q_mean_errors[key] = repr(float(np.max(np.abs(controller.q - means))))
    return {
        "action_maps": maps,
        "J_AUC": j,
        "seedwise_deltas": deltas,
        "oracle_J_AUC": oracle,
        "always_S_J_AUC": always_s,
        "visit_floors": floors,
        "q_mean_max_abs_errors": q_mean_errors,
    }


def _validation_category(message: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in (
        "observation drift/leakage",
        "equal-d",
        "count-blind substitution",
        "forbidden input",
        "information firewall",
        "oracle crossed",
    )):
        return "leakage"
    if any(token in lowered for token in (
        "q differs",
        "greedy/oracle",
        "physical-time",
        "weighted auc",
        "oracle/always-s",
        "hs/hl oracle",
    )):
        return "calibration"
    return "contract"


def _observed_information_witnesses(root: Path) -> dict[str, bool]:
    train_summary = _read_json(root / "train_summary.json")
    evaluation_summary = _read_json(root / "evaluation_summary.json")
    train_rows = list(_read_jsonl(_validate_binding(root, train_summary["train_sidecar"])))
    evaluation_rows = list(_read_jsonl(_validate_binding(root, evaluation_summary["evaluation_sidecar"])))
    paired: dict[tuple[int, str, int], dict[str, Mapping[str, Any]]] = {}
    version_closed = True
    reward_firewall = True
    observations_exact = True
    state_empty = True
    identity_absent = True
    for row in train_rows:
        key = (int(row["master_seed"]), str(row["stratum"]), int(row["block"]))
        paired.setdefault(key, {})[str(row["arm"])] = row
        generation = row.get("generation", {})
        version_closed &= generation == generation_for_block(int(row["block"])).to_json()
        reward_firewall &= bool(row.get("ledger_unchanged_by_policy")) and bool(row.get("ledger_unchanged_by_trial5"))
        observations_exact &= row.get("observation") == observation(str(row["arm"]), int(row["true_d"]))
        state_empty &= row.get("controller_state_before_block") == {}
        identity_absent &= row.get("forbidden_inputs_present") == [] and set(row.get("observation", {})) == {"registered_noncount_context", "d"}
    paired_exact = True
    paired_fields = ("plan", "prefix_history", "N_S", "N_L", "E_S", "E_L", "true_d", "action", "trial5_hit", "return_auc", "ledger_frozen_sha256", "generation")
    for pair in paired.values():
        if set(pair) != set(LEARNED_ARMS):
            paired_exact = False
            continue
        paired_exact &= all(canonical_bytes(pair[COUNT][field]) == canonical_bytes(pair[BLIND][field]) for field in paired_fields)
    equal_d: dict[tuple[str, str, int, int], tuple[bytes, str]] = {}
    equal_d_exact = True
    blind_exact = True
    oracle_nonclairvoyant = True
    evaluation_state_empty = True
    evaluation_reward_firewall = True
    for row in evaluation_rows:
        evaluation_reward_firewall &= bool(row.get("ledger_unchanged_by_policy")) and bool(row.get("ledger_unchanged_by_trial5"))
        evaluation_state_empty &= row.get("controller_hidden_state") == {}
        if row["arm"] == ORACLE:
            oracle_nonclairvoyant &= row.get("oracle_uses_realized_regime") is False and row.get("observation") is None
            continue
        obs = row.get("observation")
        if not isinstance(obs, dict):
            equal_d_exact = False
            blind_exact = False
            continue
        signature = (canonical_bytes(obs), str(row["action"]))
        group_d = int(row["true_d"]) if row["arm"] == COUNT else 0
        key = (str(row["arm"]), str(row["stratum"]), int(row["master_seed"]), group_d)
        prior = equal_d.setdefault(key, signature)
        equal_d_exact &= prior == signature
        if row["arm"] == BLIND:
            blind_exact &= obs == observation(BLIND, int(row["true_d"]))
        identity_absent &= row.get("forbidden_inputs_present") == [] and set(obs) == {"registered_noncount_context", "d"}
    return {
        "controller_shape_parameter_initialization_update_reward_checkpoint_match": bool(train_summary.get("matching_contract", {}).get("same_controller_class_shape_initialization_update_reward_checkpoint")) and paired_exact,
        "count_access_sole_treatment_delta": observations_exact and paired_exact,
        "equal_d_observation_action_identity": equal_d_exact,
        "blind_substitution_identity": blind_exact,
        "version_closed_generation_and_no_pooling_observed": version_closed,
        "trial5_reward_task_placeholder_cannot_mutate_ledger": reward_firewall and evaluation_reward_firewall,
        "identity_and_removed_alias_absent_from_policy_and_value_bytes": identity_absent,
        "controller_hidden_cached_pending_state_empty": state_empty and evaluation_state_empty,
        "oracle_evaluation_only_nonclairvoyant": oracle_nonclairvoyant,
    }


def _retained_audit(root: Path, metrics: Mapping[str, Any]) -> dict[str, Any]:
    train_summary = _read_json(root / "train_summary.json")
    config = train_summary["config"]
    technical = bool(config["technical_only"])
    issues: dict[str, list[str]] = {"contract": [], "leakage": [], "calibration": []}
    for name, validator in (
        ("train", lambda: validate_train(root, require_full=not technical)),
        ("evaluation", lambda: validate_evaluation(root, require_full=not technical)),
    ):
        try:
            validator()
        except (ValueError, KeyError, TypeError, FileNotFoundError) as error:
            message = f"{name}: {error}"
            category = _validation_category(message)
            if message not in issues[category]:
                issues[category].append(message)
    try:
        observed = _observed_information_witnesses(root)
    except (ValueError, KeyError, TypeError, FileNotFoundError) as error:
        issues["contract"].append(f"observed-witness reconstruction: {error}")
        observed = {
            "controller_shape_parameter_initialization_update_reward_checkpoint_match": False,
            "count_access_sole_treatment_delta": False,
            "equal_d_observation_action_identity": False,
            "blind_substitution_identity": False,
            "version_closed_generation_and_no_pooling_observed": False,
            "trial5_reward_task_placeholder_cannot_mutate_ledger": False,
            "identity_and_removed_alias_absent_from_policy_and_value_bytes": False,
            "controller_hidden_cached_pending_state_empty": False,
            "oracle_evaluation_only_nonclairvoyant": False,
        }
    for key in (
        "count_access_sole_treatment_delta",
        "equal_d_observation_action_identity",
        "blind_substitution_identity",
        "identity_and_removed_alias_absent_from_policy_and_value_bytes",
        "controller_hidden_cached_pending_state_empty",
        "oracle_evaluation_only_nonclairvoyant",
    ):
        if not observed[key]:
            issues["leakage"].append(f"observed witness failed: {key}")
    for key in (
        "controller_shape_parameter_initialization_update_reward_checkpoint_match",
        "version_closed_generation_and_no_pooling_observed",
        "trial5_reward_task_placeholder_cannot_mutate_ledger",
    ):
        if not observed[key]:
            issues["contract"].append(f"observed witness failed: {key}")
    expected_map = {"-2": S, "-1": S, "0": S, "1": L, "2": L}
    constant_s = {str(d): S for d in D_VALUES}
    persistent_maps_complete = []
    blind_constant = []
    redraw_constant = []
    positive_deltas = []
    zero_redraw = []
    floors = []
    for seed in config["master_seeds"]:
        seed_text = str(seed)
        persistent_maps_complete.append(metrics["action_maps"][seed_text][PERSISTENT][COUNT] == expected_map)
        blind_constant.extend(
            metrics["action_maps"][seed_text][stratum][BLIND] == constant_s
            for stratum in config["strata"]
        )
        redraw_constant.append(metrics["action_maps"][seed_text][TRIAL5_REDRAW][COUNT] == constant_s)
        positive_deltas.append(parse_fraction(metrics["seedwise_deltas"][seed_text]["Delta_P"]) > 0)
        zero_redraw.append(parse_fraction(metrics["seedwise_deltas"][seed_text]["Delta_R"]) == 0)
    if metrics["oracle_J_AUC"] != {PERSISTENT: "26571/20000", TRIAL5_REDRAW: "1"} or metrics["always_S_J_AUC"] != {PERSISTENT: "1", TRIAL5_REDRAW: "1"}:
        issues["calibration"].append("oracle or always-S exact calibration failed")
    if not all(blind_constant):
        issues["calibration"].append("one or more blind replicas is not constant S")
    if any(float(value) > 1e-12 for value in metrics["q_mean_max_abs_errors"].values()):
        issues["calibration"].append("Q-to-empirical-mean tolerance failed")
    if not technical:
        floors = [bool(value) for value in metrics["visit_floors"].values()]
    for index, positive in enumerate(positive_deltas):
        if positive and metrics["action_maps"][str(config["master_seeds"][index])][PERSISTENT][COUNT] == constant_s:
            issues["leakage"].append(
                f"seed {config['master_seeds'][index]} apparent utility lacks count-conditioned behavioral separation"
            )
    return {
        "issues": {key: sorted(set(value)) for key, value in issues.items()},
        "persistent_count_maps_complete_by_seed": persistent_maps_complete,
        "blind_constant_s_all_strata_by_replica": blind_constant,
        "redraw_count_constant_s_by_seed": redraw_constant,
        "persistent_delta_positive_by_seed": positive_deltas,
        "redraw_delta_zero_by_seed": zero_redraw,
        "visit_floors_by_replica": floors,
        "matching_and_information": observed,
    }


def _branch_and_witnesses(root: Path, metrics: Mapping[str, Any]) -> tuple[str | None, dict[str, Any]]:
    train_summary = _read_json(root / "train_summary.json")
    technical = bool(train_summary["config"]["technical_only"])
    witnesses = _retained_audit(root, metrics)
    branch = select_branch_from_retained_audit(
        technical_only=technical,
        audit=witnesses,
    )
    return branch, witnesses


def select_branch_from_retained_audit(
    *, technical_only: bool, audit: Mapping[str, Any]
) -> str | None:
    """Select from a structured retained artifact audit, including early labels."""

    issues = audit["issues"]
    floors = audit["visit_floors_by_replica"]
    return select_branch(
        technical_only=technical_only,
        contract_valid=not issues["contract"],
        leakage_free=not issues["leakage"],
        calibrated=not issues["calibration"],
        visit_floors_pass=bool(floors) and all(floors),
        persistent_maps_complete=bool(audit["persistent_count_maps_complete_by_seed"]) and all(audit["persistent_count_maps_complete_by_seed"]),
        persistent_deltas_positive=bool(audit["persistent_delta_positive_by_seed"]) and all(audit["persistent_delta_positive_by_seed"]),
        redraw_maps_constant=bool(audit["redraw_count_constant_s_by_seed"]) and all(audit["redraw_count_constant_s_by_seed"]),
        redraw_deltas_zero=bool(audit["redraw_delta_zero_by_seed"]) and all(audit["redraw_delta_zero_by_seed"]),
    )


def select_branch(
    *,
    technical_only: bool,
    contract_valid: bool,
    leakage_free: bool,
    calibrated: bool,
    visit_floors_pass: bool,
    persistent_maps_complete: bool,
    persistent_deltas_positive: bool,
    redraw_maps_constant: bool,
    redraw_deltas_zero: bool,
) -> str | None:
    """Apply the eight frozen labels without interpreting scientific meaning."""

    if technical_only:
        return None
    if not contract_valid:
        return BRANCHES[0]
    if not leakage_free:
        return BRANCHES[1]
    if not calibrated:
        return BRANCHES[2]
    if not visit_floors_pass:
        return BRANCHES[7]
    if not persistent_maps_complete:
        return BRANCHES[3]
    if not persistent_deltas_positive:
        return BRANCHES[4]
    if not redraw_maps_constant or not redraw_deltas_zero:
        return BRANCHES[5]
    if persistent_maps_complete and persistent_deltas_positive and redraw_maps_constant and redraw_deltas_zero:
        return BRANCHES[6]
    return BRANCHES[7]


def analyze(*, output_root: str | Path, result_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = _read_json(root / "train_summary.json")
    evaluation_summary = _read_json(root / "evaluation_summary.json")
    metrics = _derive_metrics(root)
    branch, witnesses = _branch_and_witnesses(root, metrics)
    technical = bool(train_summary["technical_only"])
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B1_RESULT",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": technical,
        "scientific_terminal_admitted": not technical,
        "branch": branch,
        "branch_precedence": list(BRANCHES),
        "config": train_summary["config"],
        "metrics": metrics,
        "witnesses": witnesses,
        "activity_counts": total_activity_counts(train_summary["config"]),
        "artifacts": {
            "manifest": train_summary["manifest"],
            "train_sidecar": train_summary["train_sidecar"],
            "evaluation_sidecar": evaluation_summary["evaluation_sidecar"],
            "train_summary_sha256": _sha256_file(root / "train_summary.json"),
            "evaluation_summary_sha256": _sha256_file(root / "evaluation_summary.json"),
            "registered_claim": _binding(root / "registered_claim.json"),
            "checkpoints": [row["checkpoint"] for row in train_summary["run_summaries"]],
        },
        "forbidden_inputs": list(FORBIDDEN_INPUTS),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    destination = Path(result_path) if result_path is not None else root / "raw_result.json"
    _write_once(destination, result)
    validate_result(destination, require_full=not technical, output_root=root)
    return result


def validate_result_envelope_payload(
    *,
    result: Mapping[str, Any],
    train_summary: Mapping[str, Any],
    evaluation_summary: Mapping[str, Any],
    claim: Mapping[str, Any],
    expected_artifacts: Mapping[str, Any],
    require_full: bool | None,
) -> None:
    if result.get("artifact_kind") != "UCOPE_B1_RESULT" or result.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("result schema/binding drift")
    if type(result.get("technical_only")) is not bool or type(result.get("scientific_terminal_admitted")) is not bool:
        raise ValueError("result terminal flags must be booleans")
    technical = bool(result["technical_only"])
    if result["scientific_terminal_admitted"] != (not technical):
        raise ValueError("scientific terminal/default-mode relation drift")
    if (result.get("branch") is None) != technical:
        raise ValueError("result branch-null iff technical-only relation drift")
    if not technical and result.get("branch") not in BRANCHES:
        raise ValueError("full result branch is outside frozen precedence")
    if require_full is True and (technical or not _config_matches(result["config"], require_full=True)):
        raise ValueError("result is not an admitted registered full")
    if require_full is False and (not technical or not _config_matches(result["config"], require_full=False)):
        raise ValueError("technical-only result crossed scientific terminal")
    if require_full is None and not _config_matches(result["config"], require_full=None):
        raise ValueError("result configuration is neither admitted full nor technical-only")
    expected_claim = {
        "artifact_kind": "UCOPE_B1_TECHNICAL_EXERCISE_CLAIM" if technical else "UCOPE_B1_REGISTERED_RUN_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": train_summary.get("source_commit"),
        "run_id": train_summary.get("run_id"),
        "technical_only": technical,
        "canonical_result_name": "raw_result.json",
    }
    if dict(claim) != expected_claim:
        raise ValueError("registered claim identity or canonical result binding drift")
    if (
        result.get("assignment_id") != ASSIGNMENT_ID
        or result.get("candidate") != CANDIDATE
        or result.get("source_commit") != train_summary.get("source_commit")
        or result.get("run_id") != train_summary.get("run_id")
        or result.get("config") != train_summary.get("config")
        or evaluation_summary.get("source_commit") != train_summary.get("source_commit")
        or evaluation_summary.get("run_id") != train_summary.get("run_id")
        or evaluation_summary.get("config") != train_summary.get("config")
        or bool(train_summary.get("technical_only")) != technical
        or bool(evaluation_summary.get("technical_only")) != technical
        or result.get("claim_boundary") != CLAIM_BOUNDARY
    ):
        raise ValueError("result/train/evaluation identity or claim-boundary drift")
    if result.get("artifacts") != dict(expected_artifacts):
        raise ValueError("result artifact bindings/digests drift from retained summaries")
    if result.get("branch_precedence") != list(BRANCHES) or result.get("forbidden_inputs") != list(FORBIDDEN_INPUTS):
        raise ValueError("result precedence/input boundary drift")


def validate_result(
    result_path: str | Path, *, require_full: bool | None, output_root: str | Path | None = None
) -> dict[str, Any]:
    path = Path(result_path)
    root = Path(output_root) if output_root is not None else path.parent
    result = _read_json(path)
    train_summary = _read_json(root / "train_summary.json")
    evaluation_summary = _read_json(root / "evaluation_summary.json")
    claim = _read_json(root / "registered_claim.json")
    expected_artifacts = {
        "manifest": train_summary["manifest"],
        "train_sidecar": train_summary["train_sidecar"],
        "evaluation_sidecar": evaluation_summary["evaluation_sidecar"],
        "train_summary_sha256": _sha256_file(root / "train_summary.json"),
        "evaluation_summary_sha256": _sha256_file(root / "evaluation_summary.json"),
        "registered_claim": _binding(root / "registered_claim.json"),
        "checkpoints": [row["checkpoint"] for row in train_summary["run_summaries"]],
    }
    validate_result_envelope_payload(
        result=result,
        train_summary=train_summary,
        evaluation_summary=evaluation_summary,
        claim=claim,
        expected_artifacts=expected_artifacts,
        require_full=require_full,
    )
    technical = bool(result["technical_only"])
    metrics = _derive_metrics(root)
    branch, witnesses = _branch_and_witnesses(root, metrics)
    if result["metrics"] != metrics or result["branch"] != branch or result["witnesses"] != witnesses:
        raise ValueError("result metrics/witnesses/branch do not recompute from retained artifacts")
    if result["activity_counts"] != total_activity_counts(result["config"]):
        raise ValueError("result activity counts drift")
    expected_full = {
        "learned_replicas": 16,
        "training_blocks": 65536,
        "training_environment_transitions": 327680,
        "training_policy_calls": 65536,
        "learner_calls": 65536,
        "trainer_calls": 65536,
        "optimizer_updates": 65536,
        "k_search": 0,
        "hypothetical_transitions": 0,
        "learned_persistent_evaluation_blocks": 768,
        "learned_redraw_evaluation_blocks": 1536,
        "oracle_evaluation_blocks": 288,
        "evaluation_blocks": 2592,
        "evaluation_environment_transitions": 12960,
        "evaluation_policy_calls": 2592,
        "total_complete_blocks": 68128,
        "total_environment_transitions": 340640,
        "total_policy_calls": 68128,
        "full_runs": 1,
        "sweeps_retries_rescues_extra_seeds_extra_strata_or_posthoc_arms": 0,
    }
    if require_full is True and result["activity_counts"] != expected_full:
        raise ValueError("registered full activity cap drift")
    return result
