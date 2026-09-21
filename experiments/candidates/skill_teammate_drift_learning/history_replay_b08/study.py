"""B08 fixed-history continuations of the frozen B05 decision learners.

The module consumes saved B07 records.  It has no environment or law-learner
interface: the donor's causal, pre-outcome law feature is part of each fixed row.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

import numpy as np

from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05.learning import (
    OUTCOMES,
    DecisionLearner,
    Spec,
)


SOURCE_MACROS = 2048
TARGET_MACROS = 256
CONTEXTS = 4
EPSILON = 0.20
ENDPOINT_WINDOW = 64

RESPONSE_SPEC = Spec("response_all", "response", 2.0)
FULL_SPEC = Spec("fingerprint_full", "hybrid", 2.0)


@dataclass(frozen=True)
class Continuation:
    id: str
    recipient_branch: str
    donor_branch: str
    spec: Spec


CONTINUATIONS = (
    Continuation("R_on_F_E_history", "R_E", "F_E", RESPONSE_SPEC),
    Continuation("F_on_R_E_history", "F_E", "R_E", FULL_SPEC),
)

_DONOR_KEYS = (
    "macro_index",
    "version",
    "context",
    "estimated_law",
    "collection_action",
    "outcome",
    "reward",
    "exact_values",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def decision_state_from_prefix(
    arrays: Mapping[str, np.ndarray], prefix: str = "source_decision_"
) -> dict[str, np.ndarray]:
    state = {
        key.removeprefix(prefix): np.asarray(value).copy()
        for key, value in arrays.items()
        if key.startswith(prefix)
    }
    if not state:
        raise ValueError(f"no decision state has prefix {prefix!r}")
    return state


def _require_scalar(state: Mapping[str, np.ndarray], key: str, dtype: np.dtype) -> Any:
    value = np.asarray(state[key])
    if value.shape != (1,) or value.dtype != dtype:
        raise ValueError(f"source decision field {key} has wrong shape or dtype")
    return value[0].item()


def restore_decision_learner(
    spec: Spec, contexts: int, state: Mapping[str, np.ndarray]
) -> DecisionLearner:
    """Restore and exactly round-trip a full-history B05 decision state."""
    if spec.family not in ("response_all", "fingerprint_full"):
        raise ValueError("B08 restores only the two frozen full-history learners")
    learner = DecisionLearner(spec, contexts)
    expected = learner.export_state()
    if set(state) != set(expected):
        missing = sorted(set(expected) - set(state))
        extra = sorted(set(state) - set(expected))
        raise ValueError(f"source decision state keys differ: missing={missing}, extra={extra}")
    for key, template in expected.items():
        value = np.asarray(state[key])
        if value.shape != template.shape or value.dtype != template.dtype:
            raise ValueError(f"source decision field {key} has wrong shape or dtype")
        if not np.isfinite(value).all():
            raise ValueError(f"source decision field {key} is non-finite")

    for key in (
        "window_macro_index",
        "window_reward",
        "window_version",
        "window_context",
        "window_features",
    ):
        if np.asarray(state[key]).shape[0] != 0:
            raise ValueError("frozen full-history source must have an empty recent window")

    learner.safe_count = int(_require_scalar(state, "safe_count", np.dtype("int64")))
    learner.safe_reward_sum = float(
        _require_scalar(state, "safe_reward_sum", np.dtype("float64"))
    )
    learner.safe_updates = int(
        _require_scalar(state, "safe_posterior_updates", np.dtype("int64"))
    )
    learner.cooperative_updates = int(
        _require_scalar(state, "cooperative_observations", np.dtype("int64"))
    )
    learner.solve_calls = int(
        _require_scalar(state, "regression_solves", np.dtype("int64"))
    )
    learner.expiration_recomputations = int(
        _require_scalar(state, "expiration_recomputations", np.dtype("int64"))
    )
    learner.response_counts = np.asarray(state["response_counts"]).copy()
    learner.response_reward_sums = np.asarray(state["response_reward_sums"]).copy()
    learner.cell_counts = np.asarray(state["cell_counts"]).copy()
    learner.cell_reward_sums = np.asarray(state["cell_reward_sums"]).copy()
    learner.coefficients = np.asarray(state["coefficients"]).copy()
    learner.xtx = np.asarray(state["xtx"]).copy()
    learner.xty = np.asarray(state["xty"]).copy()

    restored = learner.export_state()
    for key in expected:
        if not np.array_equal(restored[key], np.asarray(state[key])):
            raise ValueError(f"source decision state does not round-trip at {key}")
    return learner


def _validate_donor_rows(rows: Mapping[str, np.ndarray]) -> int:
    if set(_DONOR_KEYS) - set(rows):
        raise ValueError(f"donor rows omit {sorted(set(_DONOR_KEYS) - set(rows))}")
    count = len(np.asarray(rows["macro_index"]))
    if count <= 0:
        raise ValueError("donor history must be nonempty")
    shapes = {
        "macro_index": (count,),
        "version": (count,),
        "context": (count,),
        "estimated_law": (count, OUTCOMES),
        "collection_action": (count,),
        "outcome": (count,),
        "reward": (count,),
        "exact_values": (count, 2),
    }
    for key, shape in shapes.items():
        value = np.asarray(rows[key])
        if value.shape != shape or not np.isfinite(value).all():
            raise ValueError(f"donor field {key} has invalid shape or value")
    if not np.array_equal(
        np.asarray(rows["macro_index"]),
        np.arange(int(np.asarray(rows["macro_index"])[0]), int(np.asarray(rows["macro_index"])[0]) + count),
    ):
        raise ValueError("donor macro indices must be consecutive")
    if not np.isin(rows["version"], (0, 1)).all():
        raise ValueError("invalid donor version")
    if not np.logical_and(np.asarray(rows["context"]) >= 0, np.asarray(rows["context"]) < CONTEXTS).all():
        raise ValueError("invalid donor context")
    if not np.isin(rows["collection_action"], (0, 1)).all() or not np.isin(rows["reward"], (0, 1)).all():
        raise ValueError("invalid donor action or reward")
    cooperative = np.asarray(rows["collection_action"]) == 1
    if not np.logical_and(np.asarray(rows["outcome"])[cooperative] >= 0, np.asarray(rows["outcome"])[cooperative] < OUTCOMES).all():
        raise ValueError("invalid donor cooperative outcome")
    return count


def _state_delta(final: Mapping[str, np.ndarray], source: Mapping[str, np.ndarray]) -> dict[str, int]:
    scalar = lambda state, key: int(np.asarray(state[key])[0])
    return {
        "decision_observations": scalar(final, "safe_posterior_updates")
        + scalar(final, "cooperative_observations")
        - scalar(source, "safe_posterior_updates")
        - scalar(source, "cooperative_observations"),
        "safe_posterior_updates": scalar(final, "safe_posterior_updates")
        - scalar(source, "safe_posterior_updates"),
        "cooperative_observations": scalar(final, "cooperative_observations")
        - scalar(source, "cooperative_observations"),
        "cooperative_posterior_updates": scalar(
            final, "cooperative_posterior_updates"
        )
        - scalar(source, "cooperative_posterior_updates"),
        "regression_statistic_updates": scalar(final, "regression_statistic_updates")
        - scalar(source, "regression_statistic_updates"),
        "regression_solves": scalar(final, "regression_solves")
        - scalar(source, "regression_solves"),
        "expiration_recomputations": scalar(final, "expiration_recomputations")
        - scalar(source, "expiration_recomputations"),
    }


def fixed_history_readouts(
    predictions: np.ndarray, exact_values: np.ndarray, epsilon: float = EPSILON
) -> dict[str, float | int]:
    """The two declared off-collector reductions for one fixed-history row."""
    predictions = np.asarray(predictions, dtype=np.float64)
    truth = np.asarray(exact_values, dtype=np.float64)
    if predictions.shape != (2,) or truth.shape != (2,):
        raise ValueError("predictions and exact values must have shape (2,)")
    if not np.isfinite(predictions).all() or not np.isfinite(truth).all():
        raise ValueError("fixed-history readout inputs must be finite")
    if not np.isfinite(epsilon) or not 0.0 <= epsilon <= 1.0:
        raise ValueError("epsilon must lie in [0, 1]")
    greedy = int(predictions[1] > predictions[0])
    matched_probability = epsilon / 2.0 + (1.0 - epsilon) * greedy
    return {
        "greedy_action": greedy,
        "matched_epsilon_propensity": matched_probability,
        "greedy_expected_return": float(truth[greedy]),
        "matched_epsilon_expected_return": float(
            (1.0 - matched_probability) * truth[0]
            + matched_probability * truth[1]
        ),
    }


def run_continuation(
    *,
    spec: Spec,
    source_state: Mapping[str, np.ndarray],
    donor_rows: Mapping[str, np.ndarray],
    expected_first_raw_prediction: np.ndarray | None = None,
    epsilon: float = EPSILON,
) -> dict[str, Any]:
    """Replay one fixed donor history, predicting before each recorded feedback row."""
    count = _validate_donor_rows(donor_rows)
    source = {key: np.asarray(value).copy() for key, value in source_state.items()}
    learner = restore_decision_learner(spec, CONTEXTS, source)
    trajectory = {
        key: np.asarray(donor_rows[key]).copy() for key in _DONOR_KEYS
    }
    trajectory.update(
        raw_predictions=np.empty((count, 2), dtype=np.float64),
        clipped_predictions=np.empty((count, 2), dtype=np.float64),
        greedy_action=np.empty(count, dtype=np.int8),
        matched_epsilon_propensity=np.empty(count, dtype=np.float64),
        greedy_expected_return=np.empty(count, dtype=np.float64),
        matched_epsilon_expected_return=np.empty(count, dtype=np.float64),
        decision_updates_before=np.empty(count, dtype=np.int64),
        regression_solves_before=np.empty(count, dtype=np.int64),
    )
    started = perf_counter()
    for row in range(count):
        macro_index = int(trajectory["macro_index"][row])
        version = int(trajectory["version"][row])
        context = int(trajectory["context"][row])
        law = trajectory["estimated_law"][row].copy()
        learner.expire_before(macro_index)
        trajectory["decision_updates_before"][row] = learner.safe_updates + learner.cooperative_updates
        trajectory["regression_solves_before"][row] = learner.solve_calls
        raw = learner.predict(version=version, context=context, estimated_law=law)
        if row == 0 and expected_first_raw_prediction is not None and not np.array_equal(
            raw, np.asarray(expected_first_raw_prediction)
        ):
            raise ValueError("restored source state fails first-target prediction fidelity")
        clipped = np.clip(raw, 0.0, 1.0)
        truth = trajectory["exact_values"][row]
        readout = fixed_history_readouts(clipped, truth, epsilon)
        trajectory["raw_predictions"][row] = raw
        trajectory["clipped_predictions"][row] = clipped
        trajectory["greedy_action"][row] = readout["greedy_action"]
        trajectory["matched_epsilon_propensity"][row] = readout[
            "matched_epsilon_propensity"
        ]
        trajectory["greedy_expected_return"][row] = readout[
            "greedy_expected_return"
        ]
        trajectory["matched_epsilon_expected_return"][row] = readout[
            "matched_epsilon_expected_return"
        ]
        learner.observe(
            macro_index=macro_index,
            action=int(trajectory["collection_action"][row]),
            version=version,
            context=context,
            estimated_law=law,
            outcome=int(trajectory["outcome"][row]),
            reward=int(trajectory["reward"][row]),
        )
    compute_wall = perf_counter() - started
    final = learner.export_state()
    counts = _state_delta(final, source)
    if counts["decision_observations"] != count:
        raise RuntimeError("continuation did not consume every donor row exactly once")
    saved_state = {
        **{f"source_decision_{key}": value.copy() for key, value in source.items()},
        **{f"final_decision_{key}": value.copy() for key, value in final.items()},
    }
    if expected_first_raw_prediction is not None:
        saved_state.update(
            fidelity_expected_first_raw_prediction=np.asarray(
                expected_first_raw_prediction, dtype=np.float64
            ).copy(),
            fidelity_actual_first_raw_prediction=trajectory["raw_predictions"][0].copy(),
            fidelity_donor_first_estimated_law=trajectory["estimated_law"][0].copy(),
        )
    return {
        "trajectory": trajectory,
        "state": saved_state,
        "summary": {
            "spec": asdict(spec),
            "records_read": count,
            "recorded_feedback_updates": count,
            "new_preupdate_q_predictions": count,
            "scalar_policy_reductions": 2 * count,
            "counts": counts,
            "first_prediction_fidelity": expected_first_raw_prediction is not None,
            "source_state_roundtrip": True,
            "decision_source_to_final_l2_movement": float(
                np.linalg.norm(final["estimate"] - source["estimate"])
            ),
            "compute_wall_seconds": compute_wall,
            "compute_wall_scope": "recipient decision expire, predict, exact readouts, and recorded-feedback update",
            "law_fits": 0,
            "source_fits": 0,
            "environment_ticks": 0,
            "sampled_rewards": 0,
            "gradient_optimizer_calls": 0,
            "readout_role": "off-collector fixed-history matched-epsilon recommendation value",
        },
    }


def _endpoint_slice(count: int, endpoint: str) -> slice:
    width = min(ENDPOINT_WINDOW, count)
    if endpoint == "first64":
        return slice(0, width)
    if endpoint == "full":
        return slice(0, count)
    if endpoint == "late64":
        return slice(count - width, count)
    raise ValueError(f"unknown endpoint {endpoint}")


def reduce_crossed_histories(
    *,
    r_on_r: Mapping[str, np.ndarray],
    f_on_r: Mapping[str, np.ndarray],
    r_on_f: Mapping[str, np.ndarray],
    f_on_f: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    """Reduce the 2x2 matched-epsilon table on the two fixed donor histories."""
    panels = {"R_on_R": r_on_r, "F_on_R": f_on_r, "R_on_F": r_on_f, "F_on_F": f_on_f}
    count = len(np.asarray(r_on_r["matched_epsilon_expected_return"]))
    for name, panel in panels.items():
        values = np.asarray(panel["matched_epsilon_expected_return"], dtype=np.float64)
        contexts = np.asarray(panel["context"])
        if values.shape != (count,) or contexts.shape != (count,) or not np.isfinite(values).all():
            raise ValueError(f"invalid reduction panel {name}")
        if not np.array_equal(contexts, np.asarray(r_on_r["context"])):
            raise ValueError("all reduction panels must describe the same context schedule")
    result: dict[str, Any] = {"by_endpoint": {}}
    for endpoint in ("first64", "full", "late64"):
        rows = _endpoint_slice(count, endpoint)
        means = {name: float(np.mean(panel["matched_epsilon_expected_return"][rows])) for name, panel in panels.items()}
        result["by_endpoint"][endpoint] = {
            "matched_epsilon_2x2": {
                "R_history": {"R": means["R_on_R"], "F": means["F_on_R"]},
                "F_history": {"R": means["R_on_F"], "F": means["F_on_F"]},
            },
            "per_history_response_minus_full": {
                "R_history": means["R_on_R"] - means["F_on_R"],
                "F_history": means["R_on_F"] - means["F_on_F"],
            },
            "per_method_R_history_minus_F_history": {
                "R": means["R_on_R"] - means["R_on_F"],
                "F": means["F_on_R"] - means["F_on_F"],
            },
        }
    contributions = {}
    contexts = np.asarray(r_on_r["context"])
    for context in range(CONTEXTS):
        mask = contexts == context
        if not mask.any():
            contributions[str(context)] = {
                key: 0.0
                for key in ("R_minus_F_on_R_history", "R_minus_F_on_F_history", "R_history_minus_F_history_for_R", "R_history_minus_F_history_for_F")
            }
            continue
        get = lambda name: np.asarray(panels[name]["matched_epsilon_expected_return"])
        contributions[str(context)] = {
            "R_minus_F_on_R_history": float(np.sum((get("R_on_R") - get("F_on_R"))[mask]) / count),
            "R_minus_F_on_F_history": float(np.sum((get("R_on_F") - get("F_on_F"))[mask]) / count),
            "R_history_minus_F_history_for_R": float(np.sum((get("R_on_R") - get("R_on_F"))[mask]) / count),
            "R_history_minus_F_history_for_F": float(np.sum((get("F_on_R") - get("F_on_F"))[mask]) / count),
        }
    result.update(
        context_contributions=contributions,
        context_contribution_definition="sum of row-level matched-epsilon value contrast in context divided by all target rows",
        all_values_role="off-collector matched-epsilon recommendation readout; diagonals are reused B07 panels",
        no_actual_collector_or_sampled_reward_claim=True,
    )
    return result


def validate_block_inputs(
    *,
    input_root: Path,
    seed: int,
    expected_manifest_sha256: str,
    expected_source_identity: str,
    expected_target_macros: int = TARGET_MACROS,
) -> dict[str, Any]:
    """Hash and validate every B07 byte needed by one B08 block before fitting."""
    block_root = Path(input_root) / f"seed_{seed}"
    manifest_path = block_root / "artifacts.json"
    if _sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError(f"seed {seed} B07 artifact manifest digest mismatch")
    manifest = json.loads(manifest_path.read_text())
    required = ["summary.json"]
    for branch in ("R_E", "F_E"):
        required.extend((f"{branch}/state.npz", f"{branch}/trajectory.npz", f"{branch}/summary.json"))
    verified = {"artifacts.json": expected_manifest_sha256}
    for relative in required:
        path = block_root / relative
        digest = _sha256(path)
        if manifest.get(relative) != digest:
            raise ValueError(f"seed {seed} required B07 artifact digest mismatch: {relative}")
        verified[relative] = digest

    block_summary = json.loads((block_root / "summary.json").read_text())
    if block_summary.get("seed") != seed or block_summary.get("status") != "COMPLETE":
        raise ValueError("B07 block seed/status mismatch")
    if block_summary.get("source_identity") != expected_source_identity:
        raise ValueError("B07 block scientific source identity mismatch")
    expected_config = {"source_macros": SOURCE_MACROS, "target_macros": expected_target_macros, "contexts": CONTEXTS, "skill_ticks": 3, "epsilon": EPSILON}
    if block_summary.get("config") != expected_config:
        raise ValueError("B07 block config mismatch")

    branches = {}
    for branch, spec in (("R_E", RESPONSE_SPEC), ("F_E", FULL_SPEC)):
        summary = json.loads((block_root / branch / "summary.json").read_text())
        if summary.get("seed") != seed or summary.get("source_identity") != expected_source_identity:
            raise ValueError(f"B07 {branch} identity mismatch")
        if summary.get("spec") != asdict(spec) or summary.get("branch") != branch:
            raise ValueError(f"B07 {branch} learner setting mismatch")
        state_arrays = _load_npz(block_root / branch / "state.npz")
        source_state = decision_state_from_prefix(state_arrays)
        restore_decision_learner(spec, CONTEXTS, source_state)
        trajectory = _load_npz(block_root / branch / "trajectory.npz")
        start, stop = SOURCE_MACROS, SOURCE_MACROS + expected_target_macros
        donor = {key: np.asarray(trajectory[key])[start:stop].copy() for key in _DONOR_KEYS}
        if len(donor["macro_index"]) != expected_target_macros:
            raise ValueError(f"B07 {branch} target history length mismatch")
        branches[branch] = {
            "summary": summary,
            "source_state": source_state,
            "donor_rows": donor,
            "first_raw_prediction": np.asarray(trajectory["raw_predictions"])[start].copy(),
            "diagonal": {
                "context": np.asarray(trajectory["context"])[start:stop].copy(),
                "matched_epsilon_expected_return": np.asarray(trajectory["matched_epsilon_expected_return"])[start:stop].copy(),
            },
        }
    r_first = branches["R_E"]["donor_rows"]
    f_first = branches["F_E"]["donor_rows"]
    for key in ("version", "context", "estimated_law"):
        if not np.array_equal(np.asarray(r_first[key])[0], np.asarray(f_first[key])[0]):
            raise ValueError(
                f"B07 recipient and donor first-target {key} differ; prediction fidelity is not transferable"
            )
    return {
        "seed": seed,
        "block_summary": block_summary,
        "branches": branches,
        "verified_digests": verified,
        "manifest_sha256": expected_manifest_sha256,
    }
