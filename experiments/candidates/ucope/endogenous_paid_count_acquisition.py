"""Frozen UCOPE-B2 paid-count train/evaluate/analyze lifecycle.

All learning targets are observed real returns.  Exact evaluator values are
derived only after final checkpoints exist and never enter training.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import gzip
import hashlib
import io
from itertools import product
import json
from pathlib import Path
import random
import struct
from typing import Any, Callable, Iterable, Iterator, Mapping

from .endogenous_paid_count_acquisition_host import (
    BUY_SL,
    COMMIT_L,
    COMMIT_S,
    L,
    PERSISTENT_POSITIVE,
    PERSISTENT_TARGET,
    REDRAW_AFTER_TWO,
    ROOT_ACTIONS,
    S,
    STRATA,
    THETA_L,
    THETA_S,
    EndogenousPaidCountHost,
    Generation,
    canonical_bytes,
    fraction_string,
    generation_for_episode,
    hazard_for,
    parse_fraction,
    uniform_for_mark,
)


ASSIGNMENT_ID = "UCOPE-B2-ENDOGENOUS-PAID-COUNT-ACQUISITION"
CANDIDATE = "CAND-VSP-07-UCOPE@adversarial-revision-v6"
HOST_ID = "ucope_paid_count_five_trial_fifteen_unit_host_v1"
RAW_OUTPUT_BINDING = "ucope.endogenous_paid_count_acquisition.v1"
SCHEMA_VERSION = 1
COUNT = "COUNT"
BLIND = "COUNT_BLIND"
ARMS = (COUNT, BLIND)
MASTER_SEEDS = (1709, 2903)
D_VALUES = (-1, 0, 1)
TAIL_ACTIONS = (S, L)
BRANCHES = (
    "B2_INVALID_CONTRACT",
    "B2_ACQUISITION_POLICY_CALIBRATION_FAILED",
    "B2_COUNT_USE_WITHOUT_NET_VALUE",
    "B2_NET_VALUE_WITHOUT_PERSISTENCE_SPECIFICITY",
    "B2_LOCAL_NET_ACQUISITION_SUPPORTED",
    "B2_INDETERMINATE_AT_CAP",
)
SOURCE_PATHS = (
    "experiments/candidates/ucope/endogenous_paid_count_acquisition_host.py",
    "experiments/candidates/ucope/endogenous_paid_count_acquisition.py",
    "scripts/run_ucope_b2_endogenous_paid_count_acquisition.py",
    "tests/experiments/candidates/ucope/test_endogenous_paid_count_acquisition.py",
    "docs/research/candidates/ucope/CODE_SCIENCE_INDEX.md",
)
FORBIDDEN_POLICY_FIELDS = (
    "stratum", "regime", "theta", "history", "acquisition_auc", "reward",
    "return", "future", "uniform", "hit", "identity", "version", "task",
)
REGISTERED_ESTIMANDS = {
    PERSISTENT_POSITIVE: {"B": "5", "A_C": "6", "A_B": "9/2", "U": "3/2", "Gamma": "1"},
    PERSISTENT_TARGET: {"B": "5", "A_C": "213/40", "A_B": "9/2", "U": "33/40", "Gamma": "13/40"},
    REDRAW_AFTER_TWO: {"B": "5", "A_C": "9/2", "A_B": "9/2", "U": "0", "Gamma": "-1/2"},
}


@dataclass(frozen=True)
class ExperimentConfig:
    technical_only: bool
    tail_episodes_per_replica: int
    root_triads_per_replica: int
    target_rows_per_policy: int
    redraw_rows_per_policy: int
    positive_rows_per_policy: int

    def to_json(self) -> dict[str, Any]:
        return {
            "technical_only": self.technical_only,
            "master_seeds": list(MASTER_SEEDS),
            "strata": list(STRATA),
            "arms": list(ARMS),
            "tail_episodes_per_replica": self.tail_episodes_per_replica,
            "root_triads_per_replica": self.root_triads_per_replica,
            "target_rows_per_policy": self.target_rows_per_policy,
            "redraw_rows_per_policy": self.redraw_rows_per_policy,
            "positive_rows_per_policy": self.positive_rows_per_policy,
            "trials_per_episode": 5,
            "physical_units_per_episode": 15,
            "controller_float64_values": 9,
            "root_tie_order": list(ROOT_ACTIONS),
            "tail_tie_order": list(TAIL_ACTIONS),
            "k_search": 0,
            "hypothetical_transitions": 0,
        }


@dataclass(frozen=True)
class RetainedValidationFinding:
    category: str
    message: str


class RetainedValidationError(ValueError):
    """Typed retained-control failure that is not a host/contract defect."""

    def __init__(self, category: str, message: str) -> None:
        if category not in {"calibration", "visit_floor"}:
            raise ValueError("unknown retained validation category")
        super().__init__(message)
        self.finding = RetainedValidationFinding(category, message)


def registered_config() -> ExperimentConfig:
    return ExperimentConfig(False, 1536, 768, 64, 128, 2)


def technical_smoke_config() -> ExperimentConfig:
    return ExperimentConfig(True, 24, 8, 8, 16, 2)


def _write_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value) + b"\n"
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"write-once artifact differs: {path}")
        return
    path.write_bytes(payload)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _binding(path: Path, *, rows: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"path": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size}
    if rows is not None:
        value["rows"] = rows
    return value


def _validate_binding(root: Path, binding: Mapping[str, Any], *, subdir: str | None = None) -> Path:
    path = root / subdir / str(binding["path"]) if subdir else root / str(binding["path"])
    if not path.is_file() or _sha256(path) != binding.get("sha256") or path.stat().st_size != binding.get("bytes"):
        raise ValueError(f"artifact binding drift: {path}")
    return path


class _GzipWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.count = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"row artifact already exists: {path}")
        self._raw = path.open("wb")
        self._gzip = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, mtime=0)
        self._stream = io.TextIOWrapper(self._gzip, encoding="utf-8", newline="\n")

    def write(self, row: Mapping[str, Any]) -> None:
        self._stream.write(canonical_bytes(row).decode("utf-8") + "\n")
        self.count += 1

    def close(self) -> None:
        self._stream.close()
        if not self._raw.closed:
            self._raw.close()

    def __enter__(self) -> "_GzipWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def _derive_seed(master_seed: int, stratum: str, stream: str) -> int:
    payload = f"{ASSIGNMENT_ID}|{master_seed}|{stratum}|{stream}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _training_generation(seed: int, stratum: str, plan_index: int) -> int:
    """Arm-independent identity so COUNT/BLIND are paired on generation too."""

    return seed * 10_000_000 + STRATA.index(stratum) * 1_000_000 + plan_index


def _exact_uniform(rng: random.Random) -> Fraction:
    return Fraction(rng.getrandbits(53), 1 << 53)


def _regime(rng: random.Random) -> str:
    return THETA_S if rng.getrandbits(1) == 0 else THETA_L


def root_observation() -> bytes:
    return canonical_bytes({"phase": "ROOT", "remaining_trials": 5})


def tail_observation(arm: str, true_d: int) -> bytes:
    if arm not in ARMS or true_d not in D_VALUES:
        raise ValueError("invalid tail observation literal")
    visible = true_d if arm == COUNT else 0
    value = {"phase": "TAIL", "remaining_trials": 3, "d": visible}
    if any(field in value for field in FORBIDDEN_POLICY_FIELDS):
        raise RuntimeError("forbidden field entered policy observation")
    return canonical_bytes(value)


class NineValueController:
    """Stateless float64 root[3] plus tail[3,2] sample-mean controller."""

    def __init__(self, arm: str) -> None:
        if arm not in ARMS:
            raise ValueError("unknown arm")
        self.arm = arm
        self.root_values = [0.0, 0.0, 0.0]
        self.root_sums = [0.0, 0.0, 0.0]
        self.root_visits = [0, 0, 0]
        self.tail_values = [[0.0, 0.0] for _ in D_VALUES]
        self.tail_sums = [[0.0, 0.0] for _ in D_VALUES]
        self.tail_visits = [[0, 0] for _ in D_VALUES]

    def _visible_d(self, true_d: int) -> int:
        return true_d if self.arm == COUNT else 0

    def call_root(self, observation: bytes) -> str:
        if observation != root_observation():
            raise ValueError("root observation drift")
        return ROOT_ACTIONS[max(range(3), key=lambda i: (self.root_values[i], -i))]

    def call_tail(self, observation: bytes) -> str:
        decoded = json.loads(observation)
        if set(decoded) != {"phase", "remaining_trials", "d"} or decoded["phase"] != "TAIL" or decoded["remaining_trials"] != 3:
            raise ValueError("tail observation drift")
        d = int(decoded["d"])
        if d not in D_VALUES:
            raise ValueError("visible d outside support")
        values = self.tail_values[D_VALUES.index(d)]
        return TAIL_ACTIONS[max(range(2), key=lambda i: (values[i], -i))]

    def update_tail(self, true_d: int, action: str, target: float) -> None:
        d = self._visible_d(true_d)
        di, ai = D_VALUES.index(d), TAIL_ACTIONS.index(action)
        self.tail_sums[di][ai] += float(target)
        self.tail_visits[di][ai] += 1
        self.tail_values[di][ai] = self.tail_sums[di][ai] / self.tail_visits[di][ai]

    def update_root(self, action: str, target: float) -> None:
        ai = ROOT_ACTIONS.index(action)
        self.root_sums[ai] += float(target)
        self.root_visits[ai] += 1
        self.root_values[ai] = self.root_sums[ai] / self.root_visits[ai]

    def flat_values(self) -> list[float]:
        return list(self.root_values) + [value for row in self.tail_values for value in row]

    def value_bytes(self) -> bytes:
        return struct.pack("<9d", *self.flat_values())

    def to_json(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "root_values": dict(zip(ROOT_ACTIONS, self.root_values)),
            "root_sums": dict(zip(ROOT_ACTIONS, self.root_sums)),
            "root_visits": dict(zip(ROOT_ACTIONS, self.root_visits)),
            "tail_values": {str(d): dict(zip(TAIL_ACTIONS, self.tail_values[i])) for i, d in enumerate(D_VALUES)},
            "tail_sums": {str(d): dict(zip(TAIL_ACTIONS, self.tail_sums[i])) for i, d in enumerate(D_VALUES)},
            "tail_visits": {str(d): dict(zip(TAIL_ACTIONS, self.tail_visits[i])) for i, d in enumerate(D_VALUES)},
            "value_bytes_hex": self.value_bytes().hex(),
            "shape": [3, 3, 2],
            "parameter_count": 9,
            "stateless": True,
        }

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> "NineValueController":
        controller = cls(str(value["arm"]))
        controller.root_values = [float(value["root_values"][a]) for a in ROOT_ACTIONS]
        controller.root_sums = [float(value["root_sums"][a]) for a in ROOT_ACTIONS]
        controller.root_visits = [int(value["root_visits"][a]) for a in ROOT_ACTIONS]
        controller.tail_values = [[float(value["tail_values"][str(d)][a]) for a in TAIL_ACTIONS] for d in D_VALUES]
        controller.tail_sums = [[float(value["tail_sums"][str(d)][a]) for a in TAIL_ACTIONS] for d in D_VALUES]
        controller.tail_visits = [[int(value["tail_visits"][str(d)][a]) for a in TAIL_ACTIONS] for d in D_VALUES]
        if controller.value_bytes().hex() != value["value_bytes_hex"]:
            raise ValueError("checkpoint float64 bytes drift")
        return controller


def _controller_digest(controller: NineValueController) -> str:
    return hashlib.sha256(controller.value_bytes()).hexdigest()


def _training_plan(config: ExperimentConfig, seed: int, stratum: str) -> list[dict[str, Any]]:
    rng = random.Random(_derive_seed(seed, stratum, "environment"))
    actions = [S] * (config.tail_episodes_per_replica // 2) + [L] * (config.tail_episodes_per_replica // 2)
    if len(actions) != config.tail_episodes_per_replica:
        raise ValueError("tail tape must be even and exactly balanced")
    random.Random(_derive_seed(seed, stratum, "tail-action-tape")).shuffle(actions)

    def tape() -> dict[str, Any]:
        prefix = _regime(rng)
        tail = _regime(rng) if stratum == REDRAW_AFTER_TWO else prefix
        return {
            "prefix_regime": prefix,
            "tail_regime": tail,
            "uniforms": [fraction_string(_exact_uniform(rng)) for _ in range(5)],
        }

    rows: list[dict[str, Any]] = []
    for index, action in enumerate(actions):
        rows.append({"phase": "TAIL_FIT", "index": index, "tail_action": action, **tape()})
    for triad in range(config.root_triads_per_replica):
        common = tape()
        for action in ROOT_ACTIONS:
            rows.append({"phase": "ROOT_FIT", "triad": triad, "root_action": action, **common})
    return rows


def build_manifest(*, config: ExperimentConfig, source_commit: str, run_id: str) -> dict[str, Any]:
    plans = {}
    for seed in MASTER_SEEDS:
        for stratum in STRATA:
            plan = _training_plan(config, seed, stratum)
            plans[f"{seed}|{stratum}"] = {
                "rows": len(plan),
                "canonical_sha256": hashlib.sha256(canonical_bytes(plan)).hexdigest(),
                "environment_seed": _derive_seed(seed, stratum, "environment"),
                "tail_action_seed": _derive_seed(seed, stratum, "tail-action-tape"),
            }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_FROZEN_MANIFEST",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "host_id": HOST_ID,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": source_commit,
        "run_id": run_id,
        "config": config.to_json(),
        "branch_precedence": list(BRANCHES),
        "source_paths": list(SOURCE_PATHS),
        "plans": plans,
        "registered_estimands_evaluation_only": REGISTERED_ESTIMANDS,
        "matching": {
            "count_access_sole_arm_delta": True,
            "arms_same_shape_initialization_updates_data_optimization": True,
            "no_transfer": True,
            "training_never_reads_registered_estimands": True,
            "root_observations_byte_identical": True,
            "history_00_11_collapse_to_d0": True,
        },
        "activity_caps": total_activity_counts(config.to_json()),
    }


def validate_claim(root: Path, *, source_commit: str, run_id: str, technical_only: bool) -> dict[str, Any]:
    claim = _read_json(root / "registered_claim.json")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_REGISTERED_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "host_id": HOST_ID,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_only,
        "branch_precedence": list(BRANCHES),
        "source_paths": list(SOURCE_PATHS),
    }
    if claim != expected:
        raise ValueError("registered claim drift")
    return claim


def _execute_episode(
    *,
    controller: NineValueController,
    arm: str,
    stratum: str,
    prefix_regime: str,
    tail_regime: str,
    uniforms: Iterable[str],
    generation: Generation,
    root_action: str | None,
    tail_action: str | None,
    tail_training: bool = False,
) -> dict[str, Any]:
    us = tuple(parse_fraction(value) for value in uniforms)
    if len(us) != 5:
        raise ValueError("episode requires five uniforms")
    host = EndogenousPaidCountHost(stratum=stratum, prefix_regime=prefix_regime, tail_regime=tail_regime, generation=generation)
    root_observation_hex: str | None = None
    tail_observation_hex: str | None = None
    if tail_training:
        if root_action != BUY_SL or tail_action not in TAIL_ACTIONS:
            raise ValueError("tail training requires forced BUY_SL and sealed tail action")
        host.begin_forced_buy_training(generation=generation)
        chosen_root = BUY_SL
    else:
        root_callback: Callable[[bytes], str]
        if root_action is None:
            root_callback = controller.call_root
        else:
            root_callback = lambda observation: root_action if observation == root_observation() else "INVALID"
        chosen_root, root_observation_bytes = host.root_policy_call(root_callback, generation=generation)
        root_observation_hex = root_observation_bytes.hex()
    true_d: int | None = None
    visible_d: int | None = None
    chosen_tail: str | None = None
    ledger_bytes_hex: str | None = None
    if chosen_root == BUY_SL:
        host.execute_acquisition(uniforms=(us[0], us[1]), generation=generation)
        true_d, ledger_bytes = host.freeze_count(generation=generation)
        visible_d = true_d if arm == COUNT else 0
        expected_observation = tail_observation(arm, true_d)
        callback = controller.call_tail if tail_action is None else (lambda observation: tail_action if observation == expected_observation else "INVALID")
        chosen_tail, tail_observation_bytes, ledger_bytes_again = host.tail_policy_call(callback, visible_d=visible_d, generation=generation)
        if tail_observation_bytes != expected_observation or ledger_bytes != ledger_bytes_again:
            raise RuntimeError("tail observation or ledger binding drift")
        tail_observation_hex = tail_observation_bytes.hex()
        ledger_bytes_hex = ledger_bytes.hex()
        host.execute_remaining(uniforms=us[2:], generation=generation, task_reward_placeholder={"must_not_mutate": True})
    else:
        host.execute_remaining(uniforms=us, generation=generation, task_reward_placeholder={"must_not_mutate": True})
    host.close_episode()
    if host.transition_count != 5:
        raise RuntimeError("episode did not execute exactly five real transitions")
    return {
        "root_action": chosen_root,
        "tail_action": chosen_tail,
        "true_d": true_d,
        "visible_d": visible_d,
        "root_observation_hex": root_observation_hex,
        "tail_observation_hex": tail_observation_hex,
        "ledger_bytes_hex": ledger_bytes_hex,
        "acquisition_auc": host.acquisition_auc,
        "tail_return": host.tail_auc,
        "total_return": host.total_auc,
        "policy_calls": host.policy_calls,
        "transition_count": host.transition_count,
        "records": [record.to_json() for record in host.records],
    }


def expected_training_counts(config: Mapping[str, Any]) -> dict[str, int]:
    replicas = len(MASTER_SEEDS) * len(STRATA) * len(ARMS)
    tail = int(config["tail_episodes_per_replica"])
    triads = int(config["root_triads_per_replica"])
    episodes = replicas * (tail + 3 * triads)
    policy_calls = replicas * (tail + 4 * triads)
    return {
        "learned_replicas": replicas,
        "training_episodes": episodes,
        "training_env_transitions": episodes * 5,
        "training_policy_calls": policy_calls,
        "training_learner_updates": episodes,
        "training_trainer_updates": episodes,
        "training_optimizer_updates": episodes,
        "final_checkpoints": replicas,
    }


def expected_evaluation_counts(config: Mapping[str, Any]) -> dict[str, int]:
    target = int(config["target_rows_per_policy"])
    redraw = int(config["redraw_rows_per_policy"])
    positive = int(config["positive_rows_per_policy"])
    learned = len(ARMS) * len(MASTER_SEEDS) * 2 * (target + redraw + positive)
    fixed = 2 * (target + redraw + positive)
    episodes = learned + fixed
    return {
        "learned_rows": learned,
        "fixed_reference_rows": fixed,
        "evaluation_episodes": episodes,
        "evaluation_env_transitions": episodes * 5,
        "evaluation_policy_call_cap": learned * 2 + fixed,
    }


def total_activity_counts(config: Mapping[str, Any]) -> dict[str, int]:
    train_counts = expected_training_counts(config)
    eval_counts = expected_evaluation_counts(config)
    return {
        **train_counts,
        **eval_counts,
        "total_episodes": train_counts["training_episodes"] + eval_counts["evaluation_episodes"],
        "total_env_transitions": train_counts["training_env_transitions"] + eval_counts["evaluation_env_transitions"],
        "total_policy_call_cap": train_counts["training_policy_calls"] + eval_counts["evaluation_policy_call_cap"],
        "hypothetical_env_transitions": 0,
        "k_search": 0,
        "retries": 0,
        "sweeps": 0,
        "rescues": 0,
        "extra_seeds": 0,
        "extra_strata": 0,
        "extra_arms": 0,
        "extra_checkpoints": 0,
        "full_runs": 0 if bool(config["technical_only"]) else 1,
    }


def _training_row(
    *,
    controller: NineValueController,
    arm: str,
    stratum: str,
    seed: int,
    spec: Mapping[str, Any],
    generation_index: int,
) -> dict[str, Any]:
    before = _controller_digest(controller)
    if spec["phase"] == "TAIL_FIT":
        episode = _execute_episode(
            controller=controller,
            arm=arm,
            stratum=stratum,
            prefix_regime=str(spec["prefix_regime"]),
            tail_regime=str(spec["tail_regime"]),
            uniforms=spec["uniforms"],
            generation=generation_for_episode(generation_index),
            root_action=BUY_SL,
            tail_action=str(spec["tail_action"]),
            tail_training=True,
        )
        controller.update_tail(int(episode["true_d"]), str(episode["tail_action"]), float(episode["tail_return"]))
        update = {"table": "tail", "target": episode["tail_return"]}
    else:
        episode = _execute_episode(
            controller=controller,
            arm=arm,
            stratum=stratum,
            prefix_regime=str(spec["prefix_regime"]),
            tail_regime=str(spec["tail_regime"]),
            uniforms=spec["uniforms"],
            generation=generation_for_episode(generation_index),
            root_action=str(spec["root_action"]),
            tail_action=None,
        )
        controller.update_root(str(episode["root_action"]), float(episode["total_return"]))
        update = {"table": "root", "target": episode["total_return"]}
    return {
        "seed": seed,
        "stratum": stratum,
        "arm": arm,
        "plan": dict(spec),
        "generation": generation_for_episode(generation_index).to_json(),
        "controller_before_sha256": before,
        "controller_after_sha256": _controller_digest(controller),
        "update": update,
        "episode": episode,
    }


def train(
    *, output_root: str | Path, source_commit: str, run_id: str, technical_smoke: bool = False
) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    config = technical_smoke_config() if technical_smoke else registered_config()
    claim = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_REGISTERED_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "host_id": HOST_ID,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_smoke,
        "branch_precedence": list(BRANCHES),
        "source_paths": list(SOURCE_PATHS),
    }
    _write_once(root / "registered_claim.json", claim)
    manifest = build_manifest(config=config, source_commit=source_commit, run_id=run_id)
    _write_once(root / "frozen_manifest.json", manifest)
    checkpoints = root / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    row_path = root / "train_rows.jsonl.gz"
    episode_count = 0
    checkpoint_bindings: list[dict[str, Any]] = []
    with _GzipWriter(row_path) as writer:
        for seed in MASTER_SEEDS:
            for stratum in STRATA:
                plan = _training_plan(config, seed, stratum)
                for arm in ARMS:
                    controller = NineValueController(arm)
                    for plan_index, spec in enumerate(plan):
                        writer.write(
                            _training_row(
                                controller=controller,
                                arm=arm,
                                stratum=stratum,
                                seed=seed,
                                spec=spec,
                                generation_index=_training_generation(seed, stratum, plan_index),
                            )
                        )
                        episode_count += 1
                    checkpoint_path = checkpoints / f"{stratum.lower()}_{arm.lower()}_{seed}_final.json"
                    _write_once(
                        checkpoint_path,
                        {
                            "schema_version": SCHEMA_VERSION,
                            "artifact_kind": "UCOPE_B2_FINAL_CHECKPOINT",
                            "source_commit": source_commit,
                            "run_id": run_id,
                            "technical_only": technical_smoke,
                            "seed": seed,
                            "stratum": stratum,
                            "arm": arm,
                            "controller": controller.to_json(),
                        },
                    )
                    checkpoint_bindings.append(_binding(checkpoint_path))
    counts = expected_training_counts(config.to_json())
    if episode_count != counts["training_episodes"]:
        raise RuntimeError("training episode count drift")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_TRAIN_SUMMARY",
        "source_commit": source_commit,
        "run_id": run_id,
        "technical_only": technical_smoke,
        "config": config.to_json(),
        "claim": _binding(root / "registered_claim.json"),
        "manifest": _binding(root / "frozen_manifest.json"),
        "rows": _binding(row_path, rows=counts["training_episodes"]),
        "checkpoints": checkpoint_bindings,
        "activity_counts": counts,
    }
    _write_once(root / "train_summary.json", summary)
    return summary


def _checkpoint_lookup(root: Path, summary: Mapping[str, Any]) -> dict[tuple[int, str, str], NineValueController]:
    expected_by_name = {
        f"{stratum.lower()}_{arm.lower()}_{seed}_final.json": (seed, stratum, arm)
        for seed in MASTER_SEEDS for stratum in STRATA for arm in ARMS
    }
    bindings = summary.get("checkpoints")
    if not isinstance(bindings, list) or len(bindings) != 12:
        raise ValueError("checkpoint binding set drift")
    observed_names = [binding.get("path") for binding in bindings if isinstance(binding, Mapping)]
    if len(observed_names) != len(bindings) or set(observed_names) != set(expected_by_name) or len(set(observed_names)) != 12:
        raise ValueError("checkpoint binding filename set drift")
    checkpoint_dir = root / "checkpoints"
    if {path.name for path in checkpoint_dir.glob("*.json")} != set(expected_by_name):
        raise ValueError("checkpoint on-disk filename set drift")
    result = {}
    for binding in bindings:
        if set(binding) != {"path", "sha256", "bytes"}:
            raise ValueError("checkpoint binding envelope drift")
        path = _validate_binding(root, binding, subdir="checkpoints")
        value = _read_json(path)
        expected_seed, expected_stratum, expected_arm = expected_by_name[path.name]
        expected_envelope = {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "UCOPE_B2_FINAL_CHECKPOINT",
            "source_commit": summary.get("source_commit"),
            "run_id": summary.get("run_id"),
            "technical_only": summary.get("technical_only"),
            "seed": expected_seed,
            "stratum": expected_stratum,
            "arm": expected_arm,
        }
        if set(value) != set(expected_envelope) | {"controller"} or any(value.get(key) != expected for key, expected in expected_envelope.items()):
            raise ValueError(f"checkpoint identity/envelope drift: {path.name}")
        controller = NineValueController.from_json(value["controller"])
        if controller.arm != expected_arm:
            raise ValueError(f"checkpoint controller arm drift: {path.name}")
        result[(expected_seed, expected_stratum, expected_arm)] = controller
    return result


def _full_panel_specs(stratum: str) -> list[tuple[str, str, tuple[int, ...] | None]]:
    if stratum == PERSISTENT_POSITIVE:
        return [(regime, regime, None) for regime in (THETA_S, THETA_L)]
    if stratum == PERSISTENT_TARGET:
        return [(regime, regime, marks) for regime in (THETA_S, THETA_L) for marks in product((0, 1), repeat=5)]
    if stratum == REDRAW_AFTER_TWO:
        return [(prefix, tail, marks) for prefix in (THETA_S, THETA_L) for tail in (THETA_S, THETA_L) for marks in product((0, 1), repeat=5)]
    raise ValueError("unknown stratum")


def _panel_specs(config: Mapping[str, Any], stratum: str) -> list[tuple[str, str, tuple[int, ...] | None]]:
    rows = _full_panel_specs(stratum)
    limit = {
        PERSISTENT_TARGET: int(config["target_rows_per_policy"]),
        REDRAW_AFTER_TWO: int(config["redraw_rows_per_policy"]),
        PERSISTENT_POSITIVE: int(config["positive_rows_per_policy"]),
    }[stratum]
    return rows[:limit]


def _predict_actions(
    controller: NineValueController,
    arm: str,
    mode: str,
    marks: tuple[int, ...] | None,
    prefix_regime: str,
    stratum: str,
) -> tuple[str, str | None, tuple[int, ...]]:
    deterministic_marks = marks is None
    root_action = controller.call_root(root_observation()) if mode == "GREEDY_ROOT" else mode.removeprefix("FIXED_")
    if mode == "FORCED_BUY":
        root_action = BUY_SL
    if root_action == BUY_SL:
        if deterministic_marks:
            first = int(hazard_for(stratum, prefix_regime, S) == 1)
            second = int(hazard_for(stratum, prefix_regime, L) == 1)
            marks = (first, second, 0, 0, 0)
        true_d = int(marks[1]) - int(marks[0])
        tail_action = controller.call_tail(tail_observation(arm, true_d))
        actions = (S, L, tail_action, tail_action, tail_action)
    else:
        tail_action = None
        period = S if root_action == COMMIT_S else L
        actions = (period,) * 5
    if deterministic_marks:
        regimes = (prefix_regime, prefix_regime, prefix_regime, prefix_regime, prefix_regime)
        marks = tuple(int(hazard_for(stratum, regime, action) == 1) for regime, action in zip(regimes, actions))
    return root_action, tail_action, marks


def _panel_row(
    *, controller: NineValueController, arm: str, stratum: str, seed: int | None,
    mode: str, prefix_regime: str, tail_regime: str, marks: tuple[int, ...] | None,
    generation_index: int,
) -> dict[str, Any]:
    root_action, predicted_tail, realized_marks = _predict_actions(controller, arm, mode, marks, prefix_regime, stratum)
    actions = (S, L, predicted_tail, predicted_tail, predicted_tail) if root_action == BUY_SL else ((S,) * 5 if root_action == COMMIT_S else (L,) * 5)
    regimes = (prefix_regime, prefix_regime, tail_regime, tail_regime, tail_regime)
    uniforms = tuple(uniform_for_mark(hit=bool(mark), hazard=hazard_for(stratum, regime, action)) for mark, regime, action in zip(realized_marks, regimes, actions))
    episode = _execute_episode(
        controller=controller,
        arm=arm,
        stratum=stratum,
        prefix_regime=prefix_regime,
        tail_regime=tail_regime,
        uniforms=[fraction_string(value) for value in uniforms],
        generation=generation_for_episode(generation_index),
        root_action=None if mode == "GREEDY_ROOT" else root_action,
        tail_action=None,
    )
    if episode["root_action"] != root_action or episode["tail_action"] != predicted_tail:
        raise RuntimeError("actual host callbacks disagree with predicted panel route")
    prior = Fraction(1, 2) if stratum != REDRAW_AFTER_TWO else Fraction(1, 4)
    weight = prior
    for mark, regime, action in zip(realized_marks, regimes, actions):
        hazard = hazard_for(stratum, regime, action)
        weight *= hazard if mark else 1 - hazard
    return {
        "seed": seed,
        "stratum": stratum,
        "arm": arm,
        "policy_mode": mode,
        "prefix_regime": prefix_regime,
        "tail_regime": tail_regime,
        "marks": list(realized_marks),
        "weight": fraction_string(weight),
        "generation": generation_for_episode(generation_index).to_json(),
        "episode": episode,
    }


def evaluate(*, output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = _read_json(root / "train_summary.json")
    config = train_summary["config"]
    controllers = _checkpoint_lookup(root, train_summary)
    row_path = root / "evaluation_rows.jsonl.gz"
    generation_index = 10_000_000
    policy_calls = 0
    with _GzipWriter(row_path) as writer:
        for stratum in STRATA:
            specs = _panel_specs(config, stratum)
            for seed in MASTER_SEEDS:
                for arm in ARMS:
                    controller = controllers[(seed, stratum, arm)]
                    for mode in ("GREEDY_ROOT", "FORCED_BUY"):
                        for prefix, tail, marks in specs:
                            row = _panel_row(controller=controller, arm=arm, stratum=stratum, seed=seed, mode=mode, prefix_regime=prefix, tail_regime=tail, marks=marks, generation_index=generation_index)
                            writer.write(row)
                            policy_calls += int(row["episode"]["policy_calls"])
                            generation_index += 1
            for root_action in (COMMIT_S, COMMIT_L):
                controller = NineValueController(BLIND)
                for prefix, tail, marks in specs:
                    row = _panel_row(controller=controller, arm="FIXED_REFERENCE", stratum=stratum, seed=None, mode=f"FIXED_{root_action}", prefix_regime=prefix, tail_regime=tail, marks=marks, generation_index=generation_index)
                    writer.write(row)
                    policy_calls += int(row["episode"]["policy_calls"])
                    generation_index += 1
    counts = expected_evaluation_counts(config)
    counts["evaluation_policy_calls"] = policy_calls
    if writer.count != counts["evaluation_episodes"] or policy_calls > counts["evaluation_policy_call_cap"]:
        raise RuntimeError("evaluation activity count or policy-call cap drift")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_EVALUATION_SUMMARY",
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": train_summary["technical_only"],
        "train_summary": _binding(root / "train_summary.json"),
        "rows": _binding(row_path, rows=writer.count),
        "activity_counts": counts,
    }
    _write_once(root / "evaluation_summary.json", summary)
    return summary


def _config_matches(config: Mapping[str, Any], require_full: bool | None) -> bool:
    if require_full is None:
        return config in (registered_config().to_json(), technical_smoke_config().to_json())
    expected = registered_config() if require_full else technical_smoke_config()
    return config == expected.to_json()


def _expected_checkpoint_names() -> set[str]:
    return {f"{stratum.lower()}_{arm.lower()}_{seed}_final.json" for seed in MASTER_SEEDS for stratum in STRATA for arm in ARMS}


def _assert_sample_means(controller: NineValueController) -> None:
    for i in range(3):
        expected = controller.root_sums[i] / controller.root_visits[i] if controller.root_visits[i] else 0.0
        if abs(controller.root_values[i] - expected) > 1e-12:
            raise RetainedValidationError("calibration", "root Q does not equal empirical real-return mean")
    for di in range(3):
        for ai in range(2):
            visits = controller.tail_visits[di][ai]
            expected = controller.tail_sums[di][ai] / visits if visits else 0.0
            if abs(controller.tail_values[di][ai] - expected) > 1e-12:
                raise RetainedValidationError("calibration", "tail Q does not equal empirical real-return mean")


def _assert_visit_floors(controller: NineValueController, stratum: str, *, require_full: bool) -> None:
    if not require_full:
        return
    if controller.root_visits != [768, 768, 768]:
        raise RetainedValidationError("visit_floor", "root visit floor drift")
    if controller.arm == BLIND:
        if controller.tail_visits != [[0, 0], [768, 768], [0, 0]]:
            raise RetainedValidationError("visit_floor", "BLIND visible-d visits drift")
    elif stratum == PERSISTENT_POSITIVE:
        for d in (-1, 1):
            if any(v < 256 for v in controller.tail_visits[D_VALUES.index(d)]):
                raise RetainedValidationError("visit_floor", "positive COUNT reachable visit floor failed")
        if controller.tail_visits[D_VALUES.index(0)] != [0, 0]:
            raise RetainedValidationError("visit_floor", "positive COUNT d=0 must be structurally unreachable")
    else:
        for d in D_VALUES:
            if any(v < 96 for v in controller.tail_visits[D_VALUES.index(d)]):
                raise RetainedValidationError("visit_floor", "COUNT reachable visit floor failed")


def validate_train(output_root: str | Path, *, require_full: bool | None = None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "train_summary.json")
    if (
        summary.get("schema_version") != SCHEMA_VERSION
        or summary.get("artifact_kind") != "UCOPE_B2_TRAIN_SUMMARY"
        or not _config_matches(summary.get("config", {}), require_full)
        or type(summary.get("technical_only")) is not bool
    ):
        raise ValueError("train summary identity or config drift")
    technical_only = bool(summary["technical_only"])
    if technical_only != bool(summary["config"]["technical_only"]):
        raise ValueError("technical mode drift")
    validate_claim(root, source_commit=str(summary["source_commit"]), run_id=str(summary["run_id"]), technical_only=technical_only)
    _validate_binding(root, summary["claim"])
    manifest_path = _validate_binding(root, summary["manifest"])
    manifest = _read_json(manifest_path)
    expected_manifest = build_manifest(
        config=technical_smoke_config() if technical_only else registered_config(),
        source_commit=str(summary["source_commit"]),
        run_id=str(summary["run_id"]),
    )
    if manifest != expected_manifest:
        raise ValueError("manifest reconstruction drift")
    row_path = _validate_binding(root, summary["rows"])
    rows = iter(_read_jsonl(row_path))
    episode_count = 0
    reconstructed_checkpoints: dict[tuple[int, str, str], NineValueController] = {}
    config = technical_smoke_config() if technical_only else registered_config()
    for seed in MASTER_SEEDS:
        for stratum in STRATA:
            plan = _training_plan(config, seed, stratum)
            for arm in ARMS:
                controller = NineValueController(arm)
                for plan_index, spec in enumerate(plan):
                    try:
                        observed = next(rows)
                    except StopIteration as exc:
                        raise ValueError("training rows truncated") from exc
                    expected = _training_row(controller=controller, arm=arm, stratum=stratum, seed=seed, spec=spec, generation_index=_training_generation(seed, stratum, plan_index))
                    if observed != expected:
                        raise ValueError("training row reconstruction drift")
                    episode_count += 1
                _assert_sample_means(controller)
                _assert_visit_floors(controller, stratum, require_full=not technical_only)
                reconstructed_checkpoints[(seed, stratum, arm)] = controller
    try:
        next(rows)
    except StopIteration:
        pass
    else:
        raise ValueError("extra training row")
    checkpoint_dir = root / "checkpoints"
    observed_names = {path.name for path in checkpoint_dir.glob("*.json")}
    if observed_names != _expected_checkpoint_names():
        raise ValueError("final-only checkpoint set drift")
    loaded = _checkpoint_lookup(root, summary)
    if set(loaded) != set(reconstructed_checkpoints) or len(summary["checkpoints"]) != 12:
        raise ValueError("checkpoint binding set drift")
    for key, expected in reconstructed_checkpoints.items():
        observed = loaded[key]
        _assert_sample_means(observed)
        _assert_visit_floors(observed, key[1], require_full=not technical_only)
        if observed.to_json() != expected.to_json():
            raise ValueError("checkpoint does not match reconstructed training")
    expected_counts = expected_training_counts(summary["config"])
    if summary["activity_counts"] != expected_counts or episode_count != expected_counts["training_episodes"]:
        raise ValueError("training activity drift")
    return summary


def _exact_weighted(rows: Iterable[Mapping[str, Any]], field: str = "total_return") -> Fraction:
    return sum((parse_fraction(str(row["weight"])) * int(row["episode"][field]) for row in rows), Fraction(0))


def _evaluation_group_key(row: Mapping[str, Any]) -> tuple[str, str, int | None, str]:
    return str(row["stratum"]), str(row["arm"]), row["seed"], str(row["policy_mode"])


def _registered_panel_values(rows: list[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    groups: dict[tuple[str, str, int | None, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_evaluation_group_key(row), []).append(row)
    result: dict[str, dict[str, str]] = {}
    for stratum in STRATA:
        fixed_s = _exact_weighted(groups[(stratum, "FIXED_REFERENCE", None, f"FIXED_{COMMIT_S}")])
        fixed_l = _exact_weighted(groups[(stratum, "FIXED_REFERENCE", None, f"FIXED_{COMMIT_L}")])
        b_value = max(fixed_s, fixed_l)
        seed_values: dict[str, Any] = {}
        for seed in MASTER_SEEDS:
            count = _exact_weighted(groups[(stratum, COUNT, seed, "FORCED_BUY")])
            blind = _exact_weighted(groups[(stratum, BLIND, seed, "FORCED_BUY")])
            seed_values[str(seed)] = {
                "B": fraction_string(b_value),
                "A_C": fraction_string(count),
                "A_B": fraction_string(blind),
                "U": fraction_string(count - blind),
                "Gamma": fraction_string(count - b_value),
                "J_COUNT": fraction_string(_exact_weighted(groups[(stratum, COUNT, seed, "GREEDY_ROOT")])),
                "J_BLIND": fraction_string(_exact_weighted(groups[(stratum, BLIND, seed, "GREEDY_ROOT")])),
            }
        result[stratum] = seed_values
    return result


def validate_evaluation(output_root: str | Path, *, require_full: bool | None = None) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = validate_train(root, require_full=require_full)
    summary = _read_json(root / "evaluation_summary.json")
    if (
        summary.get("schema_version") != SCHEMA_VERSION
        or summary.get("artifact_kind") != "UCOPE_B2_EVALUATION_SUMMARY"
        or summary.get("source_commit") != train_summary["source_commit"]
        or summary.get("run_id") != train_summary["run_id"]
        or summary.get("technical_only") is not train_summary["technical_only"]
    ):
        raise ValueError("evaluation summary identity drift")
    if summary.get("train_summary") != _binding(root / "train_summary.json"):
        raise ValueError("evaluation train-summary binding drift")
    _validate_binding(root, summary["train_summary"])
    if summary.get("rows", {}).get("path") != "evaluation_rows.jsonl.gz":
        raise ValueError("evaluation row binding path drift")
    path = _validate_binding(root, summary["rows"])
    observed_rows = list(_read_jsonl(path))
    controllers = _checkpoint_lookup(root, train_summary)
    config = train_summary["config"]
    expected_rows: list[dict[str, Any]] = []
    generation_index = 10_000_000
    for stratum in STRATA:
        specs = _panel_specs(config, stratum)
        for seed in MASTER_SEEDS:
            for arm in ARMS:
                controller = controllers[(seed, stratum, arm)]
                for mode in ("GREEDY_ROOT", "FORCED_BUY"):
                    for prefix, tail, marks in specs:
                        expected_rows.append(_panel_row(controller=controller, arm=arm, stratum=stratum, seed=seed, mode=mode, prefix_regime=prefix, tail_regime=tail, marks=marks, generation_index=generation_index))
                        generation_index += 1
        for root_action in (COMMIT_S, COMMIT_L):
            controller = NineValueController(BLIND)
            for prefix, tail, marks in specs:
                expected_rows.append(_panel_row(controller=controller, arm="FIXED_REFERENCE", stratum=stratum, seed=None, mode=f"FIXED_{root_action}", prefix_regime=prefix, tail_regime=tail, marks=marks, generation_index=generation_index))
                generation_index += 1
    if observed_rows != expected_rows:
        raise ValueError("evaluation rows are not reconstructed real host executions")
    expected_counts = expected_evaluation_counts(config)
    expected_counts["evaluation_policy_calls"] = sum(int(row["episode"]["policy_calls"]) for row in expected_rows)
    if summary["activity_counts"] != expected_counts or expected_counts["evaluation_policy_calls"] > expected_counts["evaluation_policy_call_cap"]:
        raise ValueError("evaluation activity drift")
    if not train_summary["technical_only"]:
        groups: dict[tuple[str, str, int | None, str], list[Mapping[str, Any]]] = {}
        for row in expected_rows:
            groups.setdefault(_evaluation_group_key(row), []).append(row)
        for group in groups.values():
            if sum((parse_fraction(str(row["weight"])) for row in group), Fraction(0)) != 1:
                raise ValueError("exact panel weights do not normalize")
        values = _registered_panel_values(expected_rows)
        for stratum in STRATA:
            for seed in MASTER_SEEDS:
                observed = values[stratum][str(seed)]
                for key, expected in REGISTERED_ESTIMANDS[stratum].items():
                    if observed[key] != expected:
                        raise ValueError("registered exact real panel calibration drift")
    return summary


def _policy_maps(root: Path, train_summary: Mapping[str, Any]) -> dict[str, Any]:
    controllers = _checkpoint_lookup(root, train_summary)
    result: dict[str, Any] = {}
    for seed in MASTER_SEEDS:
        result[str(seed)] = {}
        for stratum in STRATA:
            result[str(seed)][stratum] = {}
            for arm in ARMS:
                controller = controllers[(seed, stratum, arm)]
                result[str(seed)][stratum][arm] = {
                    "root": controller.call_root(root_observation()),
                    "tail": {str(d): controller.call_tail(tail_observation(arm, d)) for d in D_VALUES},
                    "controller": controller.to_json(),
                }
    return result


def _information_witnesses(
    policy_maps: Mapping[str, Any],
    train_rows: Iterable[Mapping[str, Any]] = (),
    evaluation_rows: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    retained_train = list(train_rows)
    retained_eval = list(evaluation_rows)
    d0_count = tail_observation(COUNT, 0)
    d0_blind = tail_observation(BLIND, 0)
    controllers = [
        values[stratum][arm]["controller"]
        for values in policy_maps.values() for stratum in STRATA for arm in ARMS
    ]
    root_rows = [row for row in retained_train if row["plan"]["phase"] == "ROOT_FIT"]
    learned_eval = [row for row in retained_eval if row["arm"] in ARMS]
    fixed_eval = [row for row in retained_eval if row["arm"] == "FIXED_REFERENCE"]
    ledger_rows = [row for row in retained_train + retained_eval if row["episode"]["root_action"] == BUY_SL]

    history_pairs_ok = True
    if retained_eval:
        for seed in MASTER_SEEDS:
            for arm in ARMS:
                candidates = [
                    row for row in retained_eval
                    if row["stratum"] == PERSISTENT_TARGET and row["seed"] == seed
                    and row["arm"] == arm and row["policy_mode"] == "FORCED_BUY"
                ]
                zero = next((row for row in candidates if row["marks"][:2] == [0, 0]), None)
                one = next((row for row in candidates if row["marks"][:2] == [1, 1]), None)
                history_pairs_ok &= bool(
                    zero and one
                    and zero["episode"]["true_d"] == one["episode"]["true_d"] == 0
                    and zero["episode"]["acquisition_auc"] == 0
                    and one["episode"]["acquisition_auc"] == 3
                    and zero["episode"]["tail_observation_hex"] == one["episode"]["tail_observation_hex"]
                    and zero["episode"]["tail_action"] == one["episode"]["tail_action"]
                )
    return {
        "root_observations_byte_identical": all(
            row["episode"]["root_observation_hex"] == root_observation().hex()
            for row in root_rows + learned_eval + fixed_eval
        ),
        "count_access_sole_arm_delta": d0_count == d0_blind and tail_observation(BLIND, -1) == tail_observation(BLIND, 1),
        "history_00_11_d0_observations_byte_identical": history_pairs_ok,
        "history_00_11_actions_byte_identical": history_pairs_ok,
        "controller_shape_parameter_initialization_update_match": all(
            value.get("parameter_count") == 9 and value.get("shape") == [3, 3, 2]
            and value.get("stateless") is True and len(bytes.fromhex(value["value_bytes_hex"])) == 72
            for value in controllers
        ),
        "version_reward_postdecision_firewalls": all(
            row["episode"]["transition_count"] == 5
            and all(record["ledger_before_sha"] == record["ledger_after_sha"] for record in row["episode"]["records"][2:])
            for row in ledger_rows
        ),
        "evaluation_real_host_callbacks_only": all(
            row["episode"]["policy_calls"] == (2 if row["episode"]["root_action"] == BUY_SL else 1)
            for row in learned_eval
        ) and all(row["episode"]["policy_calls"] == 1 for row in fixed_eval),
        "fixed_references_evaluation_only": all(row["arm"] in ARMS for row in retained_train)
        and all(row["arm"] == "FIXED_REFERENCE" for row in fixed_eval),
    }


def select_branch_from_audit(audit: Mapping[str, Any]) -> str:
    if audit.get("contract_valid") is not True:
        return BRANCHES[0]
    if audit.get("calibration_pass") is not True:
        return BRANCHES[1]
    if audit.get("visit_floor_pass") is not True:
        return BRANCHES[5]
    if audit.get("all_target_tail_and_u") is True and audit.get("all_target_decline_or_no_net") is True:
        return BRANCHES[2]
    if audit.get("all_target_positive_net") is True and audit.get("any_redraw_specificity_failure") is True:
        return BRANCHES[3]
    if audit.get("full_support") is True:
        return BRANCHES[4]
    return BRANCHES[5]


def _retained_audit(root: Path, metrics: Mapping[str, Any]) -> dict[str, Any]:
    contract_issues: list[str] = []
    calibration_issues: list[str] = []
    visit_floor_issues: list[str] = []
    try:
        validate_train(root, require_full=True)
        validate_evaluation(root, require_full=True)
    except RetainedValidationError as exc:
        target = calibration_issues if exc.finding.category == "calibration" else visit_floor_issues
        target.append(exc.finding.message)
    except Exception as exc:  # invalid-contract branch retains the first direct reason
        contract_issues.append(str(exc))
    maps = metrics["policy_maps"]
    panels = metrics["exact_panels"]
    witnesses = metrics["information_witnesses"]

    def values(seed: int, stratum: str, arm: str) -> tuple[str, dict[str, str], Mapping[str, str]]:
        item = maps[str(seed)][stratum][arm]
        return item["root"], item["tail"], panels[stratum][str(seed)]

    calibration = True
    target_tail_and_u = True
    target_decline = True
    target_positive = True
    redraw_failure = False
    full_support = True
    for seed in MASTER_SEEDS:
        p_root, p_tail, p_panel = values(seed, PERSISTENT_POSITIVE, COUNT)
        pb_root, pb_tail, pb_panel = values(seed, PERSISTENT_POSITIVE, BLIND)
        positive_ok = p_tail["-1"] == S and p_tail["1"] == L and p_root == BUY_SL and p_panel["J_COUNT"] == "6" and p_panel["Gamma"] == "1"
        blind_positive_ok = len(set(pb_tail.values())) == 1 and pb_tail["0"] == S and pb_root == COMMIT_S
        calibration &= positive_ok and blind_positive_ok

        t_root, t_tail, t_panel = values(seed, PERSISTENT_TARGET, COUNT)
        tb_root, tb_tail, _ = values(seed, PERSISTENT_TARGET, BLIND)
        target_map = t_tail == {"-1": S, "0": S, "1": L}
        target_tail_and_u &= target_map and t_panel["U"] == "33/40"
        target_decline &= t_root != BUY_SL or parse_fraction(t_panel["J_COUNT"]) <= 5
        target_positive &= t_root == BUY_SL and t_panel["J_COUNT"] == "213/40" and t_panel["Gamma"] == "13/40"
        calibration &= len(set(tb_tail.values())) == 1 and tb_tail["0"] == S and tb_root == COMMIT_S

        r_root, r_tail, r_panel = values(seed, REDRAW_AFTER_TWO, COUNT)
        rb_root, rb_tail, rblind_panel = values(seed, REDRAW_AFTER_TWO, BLIND)
        redraw_ok = len(set(r_tail.values())) == 1 and r_tail["0"] == S and r_root == COMMIT_S and r_panel["U"] == "0" and parse_fraction(r_panel["J_COUNT"]) - parse_fraction(rblind_panel["J_BLIND"]) == 0
        redraw_failure |= not redraw_ok
        calibration &= len(set(rb_tail.values())) == 1 and rb_tail["0"] == S and rb_root == COMMIT_S
        full_support &= positive_ok and blind_positive_ok and target_map and target_positive and redraw_ok
    full_support &= all(bool(value) for value in witnesses.values())
    return {
        "contract_valid": not contract_issues and all(bool(value) for value in witnesses.values()),
        "contract_issues": contract_issues,
        "calibration_issues": calibration_issues,
        "visit_floor_issues": visit_floor_issues,
        "calibration_pass": not calibration_issues and calibration,
        "visit_floor_pass": not visit_floor_issues,
        "all_target_tail_and_u": target_tail_and_u,
        "all_target_decline_or_no_net": target_decline,
        "all_target_positive_net": target_positive,
        "any_redraw_specificity_failure": redraw_failure,
        "full_support": full_support,
    }


def _derive_metrics(root: Path) -> dict[str, Any]:
    train_summary = _read_json(root / "train_summary.json")
    train_rows = list(_read_jsonl(root / "train_rows.jsonl.gz"))
    rows = list(_read_jsonl(root / "evaluation_rows.jsonl.gz"))
    maps = _policy_maps(root, train_summary)
    return {
        "policy_maps": maps,
        "exact_panels": _registered_panel_values(rows),
        "information_witnesses": _information_witnesses(maps, train_rows, rows),
    }


def _expected_result_artifacts(
    root: Path, train_summary: Mapping[str, Any], evaluation_summary: Mapping[str, Any]
) -> dict[str, Any]:
    checkpoint_bindings = [
        _binding(root / "checkpoints" / f"{stratum.lower()}_{arm.lower()}_{seed}_final.json")
        for seed in MASTER_SEEDS for stratum in STRATA for arm in ARMS
    ]
    return {
        "registered_claim": _binding(root / "registered_claim.json"),
        "frozen_manifest": _binding(root / "frozen_manifest.json"),
        "train_summary": _binding(root / "train_summary.json"),
        "evaluation_summary": _binding(root / "evaluation_summary.json"),
        "train_rows": _binding(
            root / "train_rows.jsonl.gz",
            rows=int(train_summary["activity_counts"]["training_episodes"]),
        ),
        "evaluation_rows": _binding(
            root / "evaluation_rows.jsonl.gz",
            rows=int(evaluation_summary["activity_counts"]["evaluation_episodes"]),
        ),
        "checkpoints": checkpoint_bindings,
    }


def validate_result_envelope_payload(
    result: Mapping[str, Any],
    *,
    train_summary: Mapping[str, Any],
    evaluation_summary: Mapping[str, Any],
    expected_metrics: Mapping[str, Any],
    expected_audit: Mapping[str, Any],
    expected_branch: str | None,
    expected_artifacts: Mapping[str, Any],
) -> None:
    expected_keys = {
        "schema_version", "artifact_kind", "assignment_id", "candidate", "host_id",
        "raw_output_binding", "source_commit", "run_id", "technical_only",
        "scientific_terminal_admitted", "branch_precedence", "branch", "config",
        "activity_counts", "metrics", "retained_audit", "artifacts",
    }
    if set(result) != expected_keys:
        raise ValueError("result envelope key set drift")
    technical = bool(train_summary["technical_only"])
    expected_identity = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_RESULT",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "host_id": HOST_ID,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": technical,
        "scientific_terminal_admitted": not technical,
        "branch_precedence": list(BRANCHES),
        "branch": expected_branch,
        "config": train_summary["config"],
        "activity_counts": analyze_activity(train_summary, evaluation_summary),
        "metrics": expected_metrics,
        "retained_audit": expected_audit,
        "artifacts": expected_artifacts,
    }
    for key, expected in expected_identity.items():
        if result.get(key) != expected:
            raise ValueError(f"result {key} drift")


def analyze(*, output_root: str | Path, result_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = _read_json(root / "train_summary.json")
    evaluation_summary = _read_json(root / "evaluation_summary.json")
    technical_only = bool(train_summary["technical_only"])
    if technical_only:
        validate_train(root, require_full=False)
        validate_evaluation(root, require_full=False)
    metrics = _derive_metrics(root)
    if technical_only:
        audit = {"technical_only": True, "contract_valid": True}
        branch = None
    else:
        audit = _retained_audit(root, metrics)
        branch = select_branch_from_audit(audit)
    train_counts = train_summary["activity_counts"]
    eval_counts = evaluation_summary["activity_counts"]
    activity = {
        **train_counts,
        **eval_counts,
        "total_episodes": train_counts["training_episodes"] + eval_counts["evaluation_episodes"],
        "total_env_transitions": train_counts["training_env_transitions"] + eval_counts["evaluation_env_transitions"],
        "total_policy_calls": train_counts["training_policy_calls"] + eval_counts["evaluation_policy_calls"],
        "total_policy_call_cap": train_counts["training_policy_calls"] + eval_counts["evaluation_policy_call_cap"],
        "hypothetical_env_transitions": 0,
        "k_search": 0,
        "full_runs": 0 if technical_only else 1,
        "retries": 0,
        "sweeps": 0,
        "rescues": 0,
        "extra_seeds": 0,
        "extra_strata": 0,
        "extra_arms": 0,
        "extra_checkpoints": 0,
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "UCOPE_B2_RESULT",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "host_id": HOST_ID,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": technical_only,
        "scientific_terminal_admitted": not technical_only,
        "branch_precedence": list(BRANCHES),
        "branch": branch,
        "config": train_summary["config"],
        "activity_counts": activity,
        "metrics": metrics,
        "retained_audit": audit,
        "artifacts": _expected_result_artifacts(root, train_summary, evaluation_summary),
    }
    target = Path(result_path) if result_path else root / "raw_result.json"
    _write_once(target, result)
    return result


def validate_result(
    result_path: str | Path, *, require_full: bool | None = None, output_root: str | Path | None = None
) -> dict[str, Any]:
    path = Path(result_path)
    result = _read_json(path)
    root = Path(output_root) if output_root else path.parent
    train_summary = validate_train(root, require_full=require_full)
    evaluation_summary = validate_evaluation(root, require_full=require_full)
    technical = bool(train_summary["technical_only"])
    metrics = _derive_metrics(root)
    expected_audit = {"technical_only": True, "contract_valid": True} if technical else _retained_audit(root, metrics)
    expected_branch = None if technical else select_branch_from_audit(expected_audit)
    expected_artifacts = _expected_result_artifacts(root, train_summary, evaluation_summary)
    validate_result_envelope_payload(
        result,
        train_summary=train_summary,
        evaluation_summary=evaluation_summary,
        expected_metrics=metrics,
        expected_audit=expected_audit,
        expected_branch=expected_branch,
        expected_artifacts=expected_artifacts,
    )
    for name, binding in expected_artifacts.items():
        if name == "checkpoints":
            for item in binding:
                _validate_binding(root, item, subdir="checkpoints")
        else:
            _validate_binding(root, binding)
    return result


def analyze_activity(train_summary: Mapping[str, Any], evaluation_summary: Mapping[str, Any]) -> dict[str, Any]:
    train_counts = train_summary["activity_counts"]
    eval_counts = evaluation_summary["activity_counts"]
    return {
        **train_counts,
        **eval_counts,
        "total_episodes": train_counts["training_episodes"] + eval_counts["evaluation_episodes"],
        "total_env_transitions": train_counts["training_env_transitions"] + eval_counts["evaluation_env_transitions"],
        "total_policy_calls": train_counts["training_policy_calls"] + eval_counts["evaluation_policy_calls"],
        "total_policy_call_cap": train_counts["training_policy_calls"] + eval_counts["evaluation_policy_call_cap"],
        "hypothetical_env_transitions": 0,
        "k_search": 0,
        "full_runs": 0 if bool(train_summary["technical_only"]) else 1,
        "retries": 0,
        "sweeps": 0,
        "rescues": 0,
        "extra_seeds": 0,
        "extra_strata": 0,
        "extra_arms": 0,
        "extra_checkpoints": 0,
    }
