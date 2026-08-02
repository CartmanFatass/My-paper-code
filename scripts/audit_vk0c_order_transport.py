"""V-K0C order-transport localization -- evaluation-only driver.

Contract: `docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md`
(VC-D1..VC-D6 and every amendment A-VC-1..A-VC-11, plus the five Gate-B
realization clarifications C-1..C-5 recorded in that ledger's header).

Zero training, zero policy updates, zero checkpoint selection. Inputs are
ONLY the six `VK0B_R2_VALID_EXPOSURE_CHECKPOINTS` bundles under
`logs/vk0b_r2/<seed>` plus the V-K0B evaluation artifacts under
`logs/vk0b_r2_eval/`; the historical `logs/vk0b/<seed>` bundles never enter
the chain (they are byte-identical aliases, and naming them would make the
provenance chain ambiguous).

What this module does NOT do: it computes no statistic, no bound and no
result branch. `scripts/analyze_vk0c_result.py` owns all of that and
consumes exactly the three JSONL row files plus `vk0c_input_manifest.json`
written here (A-VC-10, C-5: authorization comes from the manifest and the
stamped rows, never from a directory or file name).

Probability authority (C-1/A-VC-2): every probability in this module comes
from `FixedClockAREditPolicy.token_mass(...)` and every within-check roster
advance from `advance_working_state(...)`. There is deliberately no second
logits-to-probability path anywhere in this file -- a `softmax`/`sigmoid`
written here would reopen A-VC-1/A-VC-2 no matter how carefully it matched.

Frozen propagation state (C-2): `(initial signs, check index, physical-agent
joint skill pair, skill ages, active mask)`. The toy's local observations
are identically zero and its centralized state is a pure function of
`(steps, initial signs)` (`envs/pettingzoo/two_timescale_role_free_actions.py`
`_get_state`/`_targets`), the executor is a stateless constant table, and
the high actor is feedforward -- so that tuple is the complete high-level
state. `target phase/sign state` in C-2's wording is carried by
`(initial signs, check index)`, since `_targets()` reads only
`self.steps` and the two signs drawn at reset.

Numerical sequence (C-3/A-VC-7): raw token masses in the policy probability
dtype -> validate -> ONE canonical normalized distribution p_hat used for
every downstream quantity, with the raw masses and the normalization
correction both recorded on the rows.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
for _p in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.r30_fixed_clock import (
    INVALID_SKILL,
    KEEP_TOKEN,
    SET_TOKEN,
    advance_working_state,
)
from ha_ctse_process.standalone_agent import StandaloneProcessAgent

import audit_vk0a_source_urgency_oracle as vk0a_oracle
import audit_vk0b_r30_access as vk0b


# =============================================================================
# Frozen identity -- MUST match scripts/analyze_vk0c_result.py's constants of
# the same name. The VK0-family constants are imported from the V-K0B driver
# rather than duplicated, since that module is already on this module's import
# path (unlike the V-K0B/analyzer pair, which had no shared import).
# =============================================================================

CONTRACT_ID = vk0b.CONTRACT_ID
VK0C_SCHEMA_VERSION = "vk0c-1"
VK0B_TRACE_SCHEMA_VERSION = vk0b.TRACE_SCHEMA_VERSION

INVALID_VERDICT = "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"

# Reason codes. Every one of them is fail-closed: nothing in this module ever
# drops, skips or reselects a row to make a gate pass.
REASON_ANCHOR_INVENTORY_INCONSISTENT = "ANCHOR_INVENTORY_INCONSISTENT"
REASON_SOURCE_ARTIFACT_MISSING = "SOURCE_ARTIFACT_MISSING"
REASON_SOURCE_ARTIFACT_HASH_MISMATCH = "SOURCE_ARTIFACT_HASH_MISMATCH"
REASON_SOURCE_POPULATION_MISMATCH = "SOURCE_POPULATION_MISMATCH"
REASON_SOURCE_RUN_NOT_VALID = "SOURCE_RUN_NOT_VALID"
REASON_CHECKPOINT_AUTHORIZATION_FAILED = "CHECKPOINT_AUTHORIZATION_FAILED"
REASON_ANCHOR_RESTORATION_FINGERPRINT_MISMATCH = (
    "ANCHOR_RESTORATION_FINGERPRINT_MISMATCH"
)
REASON_ENUMERATION_VALIDITY_FAILED = "ENUMERATION_VALIDITY_FAILED"
REASON_GATE_B_TRANSITION_PARITY_FAILED = "GATE_B_TRANSITION_PARITY_FAILED"
REASON_ORDER_CONJUGACY_POSITIVE_CONTROL_FAILED = (
    "ORDER_CONJUGACY_POSITIVE_CONTROL_FAILED"
)
REASON_FACTUAL_ROW_REPRODUCTION_FAILED = "FACTUAL_ROW_REPRODUCTION_FAILED"
REASON_FRESH_INITIALIZATION_NONDETERMINISTIC = "FRESH_INITIALIZATION_NONDETERMINISTIC"
REASON_POLICY_RNG_CONSUMED_BY_PURE_PATH = "POLICY_RNG_CONSUMED_BY_PURE_PATH"

POLICY_STATE_FRESH = "fresh"
POLICY_STATE_TRAINED = "trained"

ORDER_CANONICAL = vk0b.AGENT_ORDER_CANONICAL      # "canonical"
ORDER_REVERSED = vk0b.AGENT_ORDER_REVERSED        # "reversed"
ORDER_CODES = (ORDER_CANONICAL, ORDER_REVERSED)
ORDER_SEQUENCES = {ORDER_CANONICAL: (0, 1), ORDER_REVERSED: (1, 0)}

STRATUM_CANONICAL_OCCUPANCY = "CANONICAL_OCCUPANCY"
STRATUM_REVERSED_OCCUPANCY = "REVERSED_OCCUPANCY"
STRATUM_BY_ORDER_CODE = {
    ORDER_CANONICAL: STRATUM_CANONICAL_OCCUPANCY,
    ORDER_REVERSED: STRATUM_REVERSED_OCCUPANCY,
}

TOKEN_KEEP = "KEEP"
TOKEN_SET = "SET"

AGENT_KEYS = ("agent_0", "agent_1")

CONTROL_TYPE_POSITIVE = "ORDER_CONJUGACY_POSITIVE_CONTROL"
CONTROL_TYPE_FRESH_INIT = "FRESH_INIT_DETERMINISM_CONTROL"

N_OUTCOMES = 16

# Toy geometry, re-used from V-K0A rather than redefined (identical by
# construction: same fixed clock, same toy).
K0 = vk0a_oracle.K0                              # 5
WINDOW = vk0a_oracle.WINDOW                      # 5
N_SKILLS = vk0a_oracle.N_SKILLS                  # 4
NONINITIAL_CHECKS = vk0a_oracle.NONINITIAL_CHECKS  # 7
TOTAL_CHECKS = vk0a_oracle.TOTAL_CHECKS          # 8
SLOW_DUTY_SKILLS = vk0a_oracle.SLOW_DUTY_SKILLS  # (0, 1)
FAST_DUTY_SKILLS = vk0a_oracle.FAST_DUTY_SKILLS  # (2, 3)

N_AGENTS = 2

# A-VC-3 frozen source-population identities. These describe the SOURCE
# V-K0B evaluation, not this run's audited scope: the driver refuses if the
# source does not have exactly this shape, and reports its own audited scope
# separately (see `audited_scope` in the manifest).
FROZEN_CHECK_ROW_COUNT = 5_376
FROZEN_ANCHOR_COUNT = 2_688
FROZEN_EPISODES_PER_SEED = 64
FROZEN_NONINITIAL_CHECKS = 7
FROZEN_SEED_COUNT = 6

VK0C_MANIFEST_FILENAME = "vk0c_input_manifest.json"
VK0C_MATCHED_STATE_FILENAME = "vk0c_matched_state_rows.jsonl"
VK0C_PROPAGATION_FILENAME = "vk0c_propagation_rows.jsonl"
VK0C_CONTROL_FILENAME = "vk0c_control_rows.jsonl"
VK0C_FOUR_SIGN_PANEL_FILENAME = "vk0c_four_sign_panel.json"

VK0A_PANEL_FILENAME = "source_oracle_panel.json"
VK0A_SIDECAR_FILENAME = "source_oracle_panel.sha256"
VK0B_SUMMARY_FILENAME = "summary.json"

# A-VC-11: the two construction-hash scopes. `DECISION_CONTEXT_MODULES` is the
# set A-VC-11 names -- the modules reachable on the decision path under THIS
# resolved configuration (`r39_toy_direct_state_context=True` bypasses
# `compact`/`bridge` entirely in `_high_context_batch`, and `high_value` is the
# critic, which never participates in an evaluation-time decision). `low` is
# in scope because the fixed skill->action table is what turns a decision into
# a reward. `ALL_CONSTRUCTED_MODULES` is recorded alongside it as supplementary
# evidence that construction consumes the global torch stream in a fixed order;
# only the decision-context hash is the one the analyzer's determinism gate
# reads, so the supplementary scope can never widen an invalidity.
DECISION_CONTEXT_MODULES = ("high", "low")
ALL_CONSTRUCTED_MODULES = ("compact", "bridge", "high", "high_value", "low")

# Fresh-initialization rows have no checkpoint. The analyzer requires a
# non-empty `checkpoint_hash` on every row and cross-checks it against the
# manifest for TRAINED rows only, so a named sentinel is both legal and
# unambiguous -- never a trained checkpoint's hash copied onto a fresh row.
FRESH_INIT_CHECKPOINT_SENTINEL = "FRESH_INIT_NO_CHECKPOINT"


class Vk0cRefusalError(Exception):
    """Precedence-1 refusal, named before any anchor work begins."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = str(reason_code)
        self.detail = str(detail)


class Vk0cAssertionError(AssertionError):
    """A structural invariant this module asserts rather than records.

    Used only where a violation means the code is wrong (a same-label SET
    carrying mass, an enumeration that is not exactly 16 distinct outcomes,
    a pure path that consumed RNG) rather than where it means the *data* is
    invalid -- data invalidity is recorded on the rows and in the run
    verdict so the analyzer can fire it independently.
    """


# =============================================================================
# Hash helpers (SHA-256 everywhere, mirroring the V-K0B driver)
# =============================================================================


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_file(path: Path) -> str:
    return hash_bytes(Path(path).read_bytes())


def git_blob_sha1(path: Path) -> str:
    """Git identity of a source file (the repository's code-identity
    convention; `scripts/analyze_vk0c_result.py` uses the same helper)."""
    try:
        out = subprocess.run(
            ["git", "hash-object", str(path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def module_state_digest(module: torch.nn.Module) -> str:
    """SHA-256 over a module's complete `state_dict` -- parameters AND
    registered buffers, in sorted key order, each entry binding its key,
    shape, dtype and exact bytes. A shape- or dtype-only change can never
    collide with a value change because all three are in the payload."""
    chunks: list[bytes] = []
    for key, value in sorted(module.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        chunks.append(key.encode("utf-8"))
        chunks.append(str(tuple(tensor.shape)).encode("utf-8"))
        chunks.append(str(tensor.dtype).encode("utf-8"))
        chunks.append(tensor.numpy().tobytes())
        chunks.append(b"\x00")
    return hash_bytes(b"".join(chunks))


def agent_construction_hash(
    agent: StandaloneProcessAgent, module_names: Iterable[str], resolved_config_hash: str
) -> str:
    """A-VC-11: the construction hash covers the named modules' full
    `state_dict`s (parameters + buffers) AND the resolved configuration
    identity, so two constructions under different configs can never hash
    equal even with identical weights."""
    payload = {
        "resolved_config_hash": str(resolved_config_hash),
        "modules": {},
    }
    for name in module_names:
        module = getattr(agent, name, None)
        if module is None:
            payload["modules"][name] = "absent"
            continue
        payload["modules"][name] = module_state_digest(module)
    return hash_text(canonical_json(payload))


# =============================================================================
# (1) Input manifest -- A-VC-3
# =============================================================================


@dataclass
class SourceInputs:
    eval_dir: Path
    trace_path: Path
    units_path: Path
    vk0b_manifest_path: Path
    summary_path: Path
    panel_path: Path
    sidecar_path: Path
    trace_rows: list[dict[str, Any]]
    vk0b_manifest: dict[str, Any]
    summary: dict[str, Any]
    source_bindings: dict[str, str]
    vk0a_authorization: dict[str, Any]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise Vk0cRefusalError(
                    REASON_SOURCE_ARTIFACT_MISSING, f"{path}:{line_no} is not valid JSON ({exc})"
                ) from exc
    return rows


def _require_file(path: Path, label: str) -> Path:
    if not Path(path).is_file():
        raise Vk0cRefusalError(REASON_SOURCE_ARTIFACT_MISSING, f"{label} not found at {path}")
    return Path(path)


def load_source_inputs(eval_dir: Path, panel_path: Path, sidecar_path: Path) -> SourceInputs:
    """Bind every V-K0B / V-K0A input artifact by SHA-256 and refuse, named,
    on any tamper the artifacts can themselves evidence.

    Three independent tamper detectors, none of which can be satisfied by
    the tampered file alone:

    * the V-K0A panel's bytes against its `.sha256` sidecar, and the panel's
      recomputed nine-field authorization tuple against the copy the V-K0B
      evaluation manifest recorded when it ran;
    * `summary.json`'s recorded `row_counts` against the trace/unit files as
      actually read here;
    * every trace row's `checkpoint_hash` / `resolved_config_hash` against
      the per-seed block of `train_and_checkpoint_manifest.json` (and, later,
      against each checkpoint file's own recomputed SHA-256).
    """
    eval_dir = Path(eval_dir)
    trace_path = _require_file(eval_dir / vk0b.VK0B_TRACE_FILENAME, "V-K0B check trace")
    units_path = _require_file(eval_dir / vk0b.VK0B_UNITS_FILENAME, "V-K0B counterfactual units")
    vk0b_manifest_path = _require_file(
        eval_dir / vk0b.VK0B_MANIFEST_FILENAME, "V-K0B train/checkpoint manifest"
    )
    summary_path = _require_file(eval_dir / VK0B_SUMMARY_FILENAME, "V-K0B analyzer summary")
    panel_path = _require_file(panel_path, "V-K0A oracle panel")
    sidecar_path = _require_file(sidecar_path, "V-K0A oracle panel digest sidecar")

    source_bindings = {
        "renewal_check_trace_sha256": hash_file(trace_path),
        "renewal_counterfactual_units_sha256": hash_file(units_path),
        "train_and_checkpoint_manifest_sha256": hash_file(vk0b_manifest_path),
        "summary_sha256": hash_file(summary_path),
        "vk0a_panel_sha256": hash_file(panel_path),
        "vk0a_sidecar_sha256": hash_file(sidecar_path),
    }

    # V-K0A panel: bytes vs sidecar, and the recomputed authorization tuple.
    # `load_and_authorize_panel` raises `Vk0bRefusalError` on a digest
    # mismatch; re-raise it under this audit's own reason code so a V-K0C
    # refusal is never reported with a V-K0B verdict label.
    try:
        auth_bundle = vk0b.load_and_authorize_panel(panel_path, sidecar_path)
    except vk0b.Vk0bRefusalError as exc:
        raise Vk0cRefusalError(REASON_SOURCE_ARTIFACT_HASH_MISMATCH, str(exc)) from exc
    vk0a_authorization = auth_bundle["authorization"]

    vk0b_manifest = json.loads(vk0b_manifest_path.read_text(encoding="utf-8"))
    recorded_auth = vk0b_manifest.get("authorization")
    if recorded_auth != vk0a_authorization:
        raise Vk0cRefusalError(
            REASON_SOURCE_ARTIFACT_HASH_MISMATCH,
            "the V-K0A authorization tuple recomputed from the panel does not match the "
            "copy recorded in the V-K0B evaluation manifest",
        )
    if bool(vk0b_manifest.get("replay_mismatch")) or vk0b_manifest.get("run_verdict") is not None:
        raise Vk0cRefusalError(
            REASON_SOURCE_RUN_NOT_VALID,
            f"the source V-K0B evaluation is not valid: replay_mismatch="
            f"{vk0b_manifest.get('replay_mismatch')!r} run_verdict={vk0b_manifest.get('run_verdict')!r}",
        )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    trace_rows = _read_jsonl(trace_path)
    with units_path.open("r", encoding="utf-8") as handle:
        unit_row_count = sum(1 for line in handle if line.strip())

    recorded_counts = summary.get("row_counts") or {}
    if int(recorded_counts.get("check_rows", -1)) != len(trace_rows):
        raise Vk0cRefusalError(
            REASON_SOURCE_ARTIFACT_HASH_MISMATCH,
            f"summary.json records check_rows={recorded_counts.get('check_rows')!r} but the trace "
            f"file carries {len(trace_rows)} rows",
        )
    if int(recorded_counts.get("unit_rows", -1)) != unit_row_count:
        raise Vk0cRefusalError(
            REASON_SOURCE_ARTIFACT_HASH_MISMATCH,
            f"summary.json records unit_rows={recorded_counts.get('unit_rows')!r} but the units "
            f"file carries {unit_row_count} rows",
        )

    if len(trace_rows) != FROZEN_CHECK_ROW_COUNT:
        raise Vk0cRefusalError(
            REASON_SOURCE_POPULATION_MISMATCH,
            f"expected {FROZEN_CHECK_ROW_COUNT} V-K0B check rows, found {len(trace_rows)}",
        )
    for index, row in enumerate(trace_rows):
        if row.get("contract_id") != CONTRACT_ID:
            raise Vk0cRefusalError(
                REASON_SOURCE_POPULATION_MISMATCH, f"trace row {index} carries a foreign contract_id"
            )
        if row.get("trace_schema_version") != VK0B_TRACE_SCHEMA_VERSION:
            raise Vk0cRefusalError(
                REASON_SOURCE_POPULATION_MISMATCH,
                f"trace row {index} carries trace_schema_version {row.get('trace_schema_version')!r}",
            )

    return SourceInputs(
        eval_dir=eval_dir,
        trace_path=trace_path,
        units_path=units_path,
        vk0b_manifest_path=vk0b_manifest_path,
        summary_path=summary_path,
        panel_path=panel_path,
        sidecar_path=sidecar_path,
        trace_rows=trace_rows,
        vk0b_manifest=vk0b_manifest,
        summary=summary,
        source_bindings=source_bindings,
        vk0a_authorization=vk0a_authorization,
    )


# =============================================================================
# (2) Anchor gate -- A-VC-3
# =============================================================================

# Every field a V-K0B check row carries that describes the CHECK rather than
# the focal agent. The two focal rows of one (seed, episode, check) must agree
# exactly on all of them. Enumerated explicitly (rather than "every field
# except a deny-list") so a new focal-specific field added upstream cannot
# silently become a shared-agreement requirement, and a new shared field
# cannot silently escape the gate -- `assert_anchor_field_coverage` below
# checks the partition against a real row.
ANCHOR_SHARED_FIELDS: tuple[str, ...] = (
    "contract_id",
    "trace_schema_version",
    "training_seed",
    "evaluation_seed",
    "episode_id",
    "agent_order_code",
    "check_index",
    "checkpoint_hash",
    "resolved_config_hash",
    "primitive_step",
    "active_mask",
    "steps_to_check",
    "state_hash",
    "observation_hash",
    "pre_check_fingerprint",
    "factual_joint_token",
    "post_window_end_authority",
    "current_targets",
    "previous_targets",
    "natural_external_reward_vector",
    "slow_match_vector",
    "fast_match_vector",
)

ANCHOR_FOCAL_FIELDS: tuple[str, ...] = (
    "focal_agent",
    "check_unit_id",
    "current_skill",
    "skill_age",
    "oracle_u_src",
    "oracle_urgency_class",
    "natural_token_kind",
    "natural_set_skill",
    "keep_prob",
    "segment_origin",
    "incumbent_end_authority_at_check",
)


@dataclass(frozen=True)
class Anchor:
    training_seed: int
    evaluation_index: int
    episode_id: int
    check_index: int
    agent_order_code: str
    occupancy_stratum: str
    checkpoint_hash: str
    resolved_config_hash: str
    pre_check_fingerprint: str
    primitive_step: int
    active_mask: tuple[bool, bool]
    incumbent: tuple[int, int]
    skill_age: tuple[int, int]
    current_targets: dict[str, list[float]]
    previous_targets: dict[str, list[float]] | None
    natural_reward_vector: tuple[float, ...]
    slow_match_vector: tuple[int, ...]
    fast_match_vector: tuple[int, ...]
    factual_joint_token: dict[str, dict[str, Any]]

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.training_seed, self.evaluation_index, self.check_index)


def assert_anchor_field_coverage(row: dict[str, Any]) -> None:
    """The shared/focal partition must exactly cover a real V-K0B row.

    Without this, a field added upstream would silently fall out of the
    anchor gate: the gate would still pass, while no longer comparing the
    thing that was added. Mirrors `build_fingerprint`'s own
    `FINGERPRINT_FIELDS` coverage assertion.
    """
    declared = set(ANCHOR_SHARED_FIELDS) | set(ANCHOR_FOCAL_FIELDS)
    actual = set(row.keys())
    if declared != actual:
        raise Vk0cAssertionError(
            "anchor field partition drifted from the V-K0B row schema: "
            f"missing={sorted(actual - declared)} extra={sorted(declared - actual)}"
        )


def build_anchor_inventory(trace_rows: list[dict[str, Any]]) -> list[Anchor]:
    """A-VC-3 anchor gate. Any missing row, third duplicate, or disagreement
    on a shared field is `INVALID_VK0C_ORDER_TRANSPORT_AUDIT /
    ANCHOR_INVENTORY_INCONSISTENT` -- never row selection, never a dropped
    anchor, never "take the first of the duplicates"."""
    if trace_rows:
        assert_anchor_field_coverage(trace_rows[0])

    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for row in trace_rows:
        key = (int(row["training_seed"]), int(row["evaluation_seed"]), int(row["check_index"]))
        grouped.setdefault(key, []).append(row)

    anchors: list[Anchor] = []
    for key in sorted(grouped):
        rows = grouped[key]
        if len(rows) != N_AGENTS:
            raise Vk0cRefusalError(
                REASON_ANCHOR_INVENTORY_INCONSISTENT,
                f"anchor {key} has {len(rows)} focal rows, expected exactly {N_AGENTS}",
            )
        first, second = rows
        for field_name in ANCHOR_SHARED_FIELDS:
            if first.get(field_name) != second.get(field_name):
                raise Vk0cRefusalError(
                    REASON_ANCHOR_INVENTORY_INCONSISTENT,
                    f"anchor {key} focal rows disagree on shared field {field_name!r}: "
                    f"{first.get(field_name)!r} != {second.get(field_name)!r}",
                )
        by_focal = {int(r["focal_agent"]): r for r in rows}
        if sorted(by_focal) != list(range(N_AGENTS)):
            raise Vk0cRefusalError(
                REASON_ANCHOR_INVENTORY_INCONSISTENT,
                f"anchor {key} does not reconstruct one ordered roster: focal agents "
                f"{sorted(int(r['focal_agent']) for r in rows)}",
            )

        order_code = str(first["agent_order_code"])
        expected_order = vk0b.agent_order_for_evaluation_index(int(first["evaluation_seed"]))[1]
        if order_code != expected_order:
            raise Vk0cRefusalError(
                REASON_ANCHOR_INVENTORY_INCONSISTENT,
                f"anchor {key} carries agent_order_code {order_code!r} but the frozen 64-episode "
                f"bank parity assigns {expected_order!r}",
            )

        anchors.append(
            Anchor(
                training_seed=int(first["training_seed"]),
                evaluation_index=int(first["evaluation_seed"]),
                episode_id=int(first["episode_id"]),
                check_index=int(first["check_index"]),
                agent_order_code=order_code,
                occupancy_stratum=STRATUM_BY_ORDER_CODE[order_code],
                checkpoint_hash=str(first["checkpoint_hash"]),
                resolved_config_hash=str(first["resolved_config_hash"]),
                pre_check_fingerprint=str(first["pre_check_fingerprint"]),
                primitive_step=int(first["primitive_step"]),
                active_mask=tuple(bool(x) for x in first["active_mask"]),
                incumbent=tuple(int(by_focal[a]["current_skill"]) for a in range(N_AGENTS)),
                skill_age=tuple(int(by_focal[a]["skill_age"]) for a in range(N_AGENTS)),
                current_targets=first["current_targets"],
                previous_targets=first["previous_targets"],
                natural_reward_vector=tuple(float(x) for x in first["natural_external_reward_vector"]),
                slow_match_vector=tuple(int(x) for x in first["slow_match_vector"]),
                fast_match_vector=tuple(int(x) for x in first["fast_match_vector"]),
                factual_joint_token=first["factual_joint_token"],
            )
        )
    return anchors


def assert_anchor_population(anchors: list[Anchor]) -> dict[str, Any]:
    """Refuse unless the deduplicated anchor inventory has exactly the frozen
    A-VC-3 shape: 2,688 anchors = 6 seeds x 64 episodes x 7 noninitial checks."""
    seeds = sorted({a.training_seed for a in anchors})
    episodes_per_seed = {s: len({a.evaluation_index for a in anchors if a.training_seed == s}) for s in seeds}
    checks = sorted({a.check_index for a in anchors})
    problems: list[str] = []
    if len(anchors) != FROZEN_ANCHOR_COUNT:
        problems.append(f"anchor count {len(anchors)} != {FROZEN_ANCHOR_COUNT}")
    if len(seeds) != FROZEN_SEED_COUNT:
        problems.append(f"seed count {len(seeds)} != {FROZEN_SEED_COUNT}")
    if any(n != FROZEN_EPISODES_PER_SEED for n in episodes_per_seed.values()):
        problems.append(f"episodes per seed {episodes_per_seed} != {FROZEN_EPISODES_PER_SEED}")
    if checks != list(range(1, FROZEN_NONINITIAL_CHECKS + 1)):
        problems.append(f"noninitial check indices {checks} != 1..{FROZEN_NONINITIAL_CHECKS}")
    if problems:
        raise Vk0cRefusalError(REASON_SOURCE_POPULATION_MISMATCH, "; ".join(problems))
    return {
        "seeds": seeds,
        "episodes_per_seed": FROZEN_EPISODES_PER_SEED,
        "noninitial_checks": FROZEN_NONINITIAL_CHECKS,
        "deduplicated_anchor_count": len(anchors),
    }


# =============================================================================
# Deterministic reward kernel (A-VC-6): the V-K0A window evaluator
# =============================================================================


def _zero_joint_action() -> np.ndarray:
    return np.zeros((N_AGENTS, 2), dtype=np.float32)


class WindowKernel:
    """Memoized deterministic five-step window evaluator.

    A window's outcome is a pure function of `(initial signs, check index,
    physical-agent skill pair)`: the env's targets read only `steps` and the
    two signs drawn at reset, and the executor is a constant table. So the
    whole audit needs at most `4 x TOTAL_CHECKS x N_SKILLS^2 = 512` distinct
    window evaluations no matter how many anchors it visits.

    The five-step REWARD comes from `audit_vk0a_source_urgency_oracle.
    evaluate_window` -- the V-K0A window evaluator is the deterministic
    reward kernel per A-VC-6. That function does not return the per-step
    slow/fast match scores, which A-VC-6 also requires, so this class rolls
    the same deepcopied env a second time to read them from `reward_info`
    and asserts the two rolls' reward vectors are bit-identical. The second
    roll is therefore a cross-check on the first, never an independent
    reward path.
    """

    def __init__(self, config) -> None:
        self._config = config
        self._cache: dict[tuple, dict[str, Any]] = {}
        self._sign_seeds: dict[tuple[int, int], int] | None = None
        self._env_cache: dict[tuple[tuple[int, int], int], Any] = {}
        self.evaluations = 0
        self.cache_hits = 0

    # -- sign-addressed env construction ------------------------------------

    def sign_seeds(self) -> dict[tuple[int, int], int]:
        """`reset(seed)` over seed = 0, 1, 2, ... until all four (slow, fast)
        sign combinations appear -- the same scan V-K0A's own
        `scan_sign_combinations` performs, but through `vk0b.make_env` so the
        env is constructed exactly the way every other path in this chain
        constructs it."""
        if self._sign_seeds is None:
            found: dict[tuple[int, int], int] = {}
            seed = 0
            while len(found) < 4:
                wrapped = vk0b.make_env(self._config, int(seed))
                try:
                    wrapped.reset(seed=int(seed))
                    combo = (
                        int(np.sign(wrapped.env._initial_slow_sign)),
                        int(np.sign(wrapped.env._initial_fast_sign)),
                    )
                finally:
                    wrapped.close()
                found.setdefault(combo, int(seed))
                seed += 1
                if seed > 100_000:
                    raise Vk0cAssertionError(
                        "could not find all four sign combinations within 100000 seeds"
                    )
            self._sign_seeds = found
        return self._sign_seeds

    def raw_env_at(self, signs: tuple[int, int], check_index: int):
        """A freshly constructed RAW env positioned at `(steps=check_index*K0,
        signs)` by zero-action stepping -- the documented action-independence
        of the toy's clock (`step()` advances `steps` unconditionally and
        `_targets()` reads only `steps` and the two reset-drawn signs), the
        same reconstruction `audit_vk0b_r30_access._emit_check_and_units`
        already relies on for its oracle invocation."""
        seed = self.sign_seeds()[tuple(signs)]
        wrapped = vk0b.make_env(self._config, int(seed))
        wrapped.reset(seed=int(seed))
        raw = wrapped.env
        for _ in range(int(check_index) * K0):
            raw.step({"agent_0": np.zeros(2, dtype=np.float32), "agent_1": np.zeros(2, dtype=np.float32)})
        observed = (int(np.sign(raw._initial_slow_sign)), int(np.sign(raw._initial_fast_sign)))
        if observed != tuple(signs) or int(raw.steps) != int(check_index) * K0:
            raise Vk0cAssertionError(
                f"env reconstruction landed at steps={raw.steps} signs={observed}, "
                f"expected steps={check_index * K0} signs={tuple(signs)}"
            )
        return wrapped, raw

    def policy_inputs_at(self, signs: tuple[int, int], check_index: int) -> tuple[np.ndarray, np.ndarray]:
        """`(joint_obs, centralized_state)` exactly as the natural driver
        hands them to the policy: taken from the WRAPPED env's reset/step
        infos, not from a private env accessor, so any wrapper-level
        transform is reproduced rather than bypassed."""
        key = (tuple(signs), int(check_index))
        if key in self._env_cache:
            return self._env_cache[key]
        seed = self.sign_seeds()[tuple(signs)]
        wrapped = vk0b.make_env(self._config, int(seed))
        try:
            obs, info = wrapped.reset(seed=int(seed))
            state = info.get("state")
            for _ in range(int(check_index) * K0):
                obs, _reward, _term, _trunc, info = wrapped.step(_zero_joint_action())
                state = info.get("next_state", state)
            observed = (
                int(np.sign(wrapped.env._initial_slow_sign)),
                int(np.sign(wrapped.env._initial_fast_sign)),
            )
            if observed != tuple(signs):
                raise Vk0cAssertionError(
                    f"policy-input reconstruction drew signs {observed}, expected {tuple(signs)}"
                )
            payload = (
                np.asarray(obs, dtype=np.float32).copy(),
                np.asarray(state, dtype=np.float32).copy(),
            )
        finally:
            wrapped.close()
        self._env_cache[key] = payload
        return payload

    # -- the window itself ---------------------------------------------------

    def evaluate(self, signs: tuple[int, int], check_index: int, skills: tuple[int, int]) -> dict[str, Any]:
        key = (tuple(signs), int(check_index), int(skills[0]), int(skills[1]))
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached

        wrapped, raw = self.raw_env_at(signs, check_index)
        try:
            ref_fp = vk0a_oracle.fingerprint(raw)
            total, kernel_rewards = vk0a_oracle.evaluate_window(
                raw,
                int(skills[0]),
                int(skills[1]),
                vk0b._ACTION_TABLE,
                vk0b._ACTION_TABLE_HASH,
                None,
                ref_fp,
            )
            # Second roll on an independent deepcopy of the SAME source env,
            # solely to read the per-step slow/fast match scores the V-K0A
            # evaluator does not return. Its rewards must agree bit-for-bit
            # with the kernel's; if they ever did not, the match vectors
            # would not describe the kernel's own window.
            branch = copy.deepcopy(raw)
            action0 = vk0b._ACTION_TABLE[int(skills[0])]
            action1 = vk0b._ACTION_TABLE[int(skills[1])]
            rewards: list[float] = []
            slow: list[int] = []
            fast: list[int] = []
            actions: list[list[list[float]]] = []
            for _ in range(WINDOW):
                _obs, step_rewards, _term, _trunc, infos = branch.step(
                    {"agent_0": action0, "agent_1": action1}
                )
                metrics = (infos.get("agent_0", {}) or {}).get("reward_info") or {}
                rewards.append(float(step_rewards["agent_0"]))
                slow.append(vk0b._binary_match(metrics.get("r39_toy_slow_match", 0.0)))
                fast.append(vk0b._binary_match(metrics.get("r39_toy_fast_match", 0.0)))
                actions.append([[float(x) for x in action0], [float(x) for x in action1]])
            if rewards != [float(x) for x in kernel_rewards]:
                raise Vk0cAssertionError(
                    f"match-vector roll disagreed with the V-K0A reward kernel at {key}: "
                    f"{rewards} != {list(kernel_rewards)}"
                )
            payload = {
                "rewards": rewards,
                "total": float(total),
                "slow": slow,
                "fast": fast,
                "actions": actions,
            }
        finally:
            wrapped.close()
        self.evaluations += 1
        self._cache[key] = payload
        return payload


def signs_from_targets(
    targets: dict[str, list[float]], check_index: int, slow_period_blocks: int
) -> tuple[int, int]:
    """Recover the episode's INITIAL signs from a stored V-K0B row's
    `current_targets`, by inverting `_targets()`'s block arithmetic. Used
    only as an independent cross-check against the signs read from a real
    env reset -- never as the authoritative source."""
    fast_block = (int(check_index) * K0) // K0
    slow_block = (int(check_index) * K0) // (K0 * int(slow_period_blocks))
    slow_sign_now = 1 if float(targets["slow"][0]) > 0 else -1
    fast_sign_now = 1 if float(targets["fast"][1]) > 0 else -1
    slow_initial = slow_sign_now * (-1 if slow_block % 2 else 1)
    fast_initial = fast_sign_now * (-1 if fast_block % 2 else 1)
    return (int(slow_initial), int(fast_initial))


def episode_initial_signs(config, evaluation_index: int) -> tuple[int, int]:
    seed = int(vk0b.episode_seed(int(evaluation_index)))
    wrapped = vk0b.make_env(config, seed)
    try:
        wrapped.reset(seed=seed)
        return (
            int(np.sign(wrapped.env._initial_slow_sign)),
            int(np.sign(wrapped.env._initial_fast_sign)),
        )
    finally:
        wrapped.close()


# =============================================================================
# (3) Anchor restoration -- VC-D2
# =============================================================================


@dataclass
class RestoredAnchor:
    fingerprint_match: bool
    obs: np.ndarray
    state: np.ndarray
    incumbent: tuple[int, int]
    skill_age: tuple[int, int]
    active_mask: tuple[bool, bool]
    initial_signs: tuple[int, int]
    primitive_step: int
    agent_order: np.ndarray
    agent_order_code: str
    fingerprint: dict[str, Any]


def restore_anchor(
    *,
    agent: StandaloneProcessAgent,
    config,
    anchor: Anchor,
    fingerprint_perturber=None,
):
    """From-reset natural replay to `anchor.check_index`, byte-verified
    against the stored V-K0B `pre_check_fingerprint` (VC-D2).

    The prefix logic is `audit_vk0b_r30_access.replay_branch`'s, reusing that
    module's own seed derivation, env construction and `build_fingerprint`;
    it is re-expressed here rather than called because `replay_branch`
    returns a post-window `BranchOutcome` and never exposes the anchor state
    itself, which is exactly what VC-D1's pure enumeration and VC-D2's
    two-agent positive control both need.

    Returns `(wrapped_env, RestoredAnchor)`; the caller owns closing the env.
    A fingerprint mismatch is recorded on the returned object and propagated
    to `boundary_state_replay_ok` on every row of that anchor -- it is
    invalidity, never a dropped anchor, so the replay is NOT aborted.

    `fingerprint_perturber` is a test-only hook (never reachable from the
    CLI) that mutates the freshly computed fingerprint before comparison, to
    drive the fail-closed guard red on demand.
    """
    agent_order, agent_order_code = vk0b.agent_order_for_evaluation_index(anchor.evaluation_index)
    ep_seed = vk0b.episode_seed(anchor.evaluation_index)
    pol_seed = vk0b.policy_stream_seed(anchor.training_seed, anchor.evaluation_index, agent_order_code)

    wrapped_env = vk0b.make_env(config, int(ep_seed))
    ok = False
    try:
        torch.manual_seed(int(pol_seed))
        np.random.seed(vk0b._legacy_numpy_seed(pol_seed))
        obs, info = wrapped_env.reset(seed=int(ep_seed))
        state = info.get("state")
        agent.reset_env_state(0)
        raw_env = wrapped_env.env

        step = 0
        check_index = -1
        max_steps = int(config.max_steps)
        while True:
            due = bool(not np.all(agent.has_active_skill[0]) or int(agent.steps_to_check[0]) <= 0)
            if not due:
                raise Vk0cAssertionError(
                    "anchor restoration reached a non-due step outside a check window"
                )
            check_index += 1
            if check_index < anchor.check_index:
                agent.maybe_assign_skills(
                    obs, state=state, step=step, k=K0, env_id=0, deterministic=False,
                    collect_r31=False, agent_order=agent_order,
                )
                done = False
                for _ in range(WINDOW):
                    actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
                    obs, reward, terminated, truncated, info = wrapped_env.step(actions)
                    state = info.get("next_state", state)
                    step += 1
                    done = bool(terminated or truncated) or step >= max_steps
                    agent.record_environment_step(
                        0, reward=float(reward), next_obs=obs, next_state=state,
                        done=done, collect_r31=False,
                    )
                    if done:
                        break
                if done:
                    raise Vk0cAssertionError("episode ended before reaching the anchor check")
                continue

            fp = vk0b.build_fingerprint(
                raw_env=raw_env, agent=agent, env_id=0, obs=obs, state=state,
                agent_order=agent_order, checkpoint_sha256=anchor.checkpoint_hash,
                resolved_config_hash=anchor.resolved_config_hash,
            )
            compared = fp if fingerprint_perturber is None else fingerprint_perturber(dict(fp))
            match = vk0b.fingerprint_digest(compared) == anchor.pre_check_fingerprint
            restored = RestoredAnchor(
                fingerprint_match=bool(match),
                obs=np.asarray(obs, dtype=np.float32).copy(),
                state=np.asarray(state, dtype=np.float32).copy(),
                incumbent=(
                    int(agent.active_skills[0][0]) if agent.has_active_skill[0][0] else INVALID_SKILL,
                    int(agent.active_skills[0][1]) if agent.has_active_skill[0][1] else INVALID_SKILL,
                ),
                skill_age=(int(agent.skill_age[0][0]), int(agent.skill_age[0][1])),
                active_mask=(bool(agent.has_active_skill[0][0]), bool(agent.has_active_skill[0][1])),
                initial_signs=(
                    int(np.sign(raw_env._initial_slow_sign)),
                    int(np.sign(raw_env._initial_fast_sign)),
                ),
                primitive_step=int(step),
                agent_order=agent_order,
                agent_order_code=agent_order_code,
                fingerprint=fp,
            )
            ok = True
            return wrapped_env, restored
    finally:
        if not ok:
            wrapped_env.close()


# =============================================================================
# (4) Pure enumeration -- VC-D1 / A-VC-1 / A-VC-7
# =============================================================================


@dataclass(frozen=True)
class Outcome:
    first_agent: int
    second_agent: int
    first_kind: int
    first_skill: int
    second_kind: int
    second_skill: int
    raw_first_mass: float
    raw_second_mass: float
    raw_joint_mass: float
    final_skills: tuple[int, int]

    def token(self, position: str) -> dict[str, Any]:
        kind = self.first_kind if position == "first" else self.second_kind
        skill = self.first_skill if position == "first" else self.second_skill
        if int(kind) == KEEP_TOKEN:
            return {"kind": TOKEN_KEEP, "skill": None}
        return {"kind": TOKEN_SET, "skill": str(int(skill))}


def legal_tokens(incumbent: int, active: bool) -> list[tuple[int, int]]:
    """A-VC-1 support. Active learned-KEEP agent: KEEP plus the three
    non-incumbent SETs. No incumbent: the four unmasked SETs, no KEEP."""
    if active:
        return [(KEEP_TOKEN, INVALID_SKILL)] + [
            (SET_TOKEN, z) for z in range(N_SKILLS) if z != int(incumbent)
        ]
    return [(SET_TOKEN, z) for z in range(N_SKILLS)]


def _mass_of(mass: dict[str, torch.Tensor], kind: int, skill: int) -> float:
    if int(kind) == KEEP_TOKEN:
        return float(mass["keep_mass"].reshape(-1)[0].item())
    return float(mass["set_mass"].reshape(-1)[int(skill)].item())


def policy_context(agent: StandaloneProcessAgent, obs: np.ndarray, state: np.ndarray):
    """The exact decision context `_r30_maybe_assign_skills` builds, taken
    from the agent's own `_r30_context_tensors` -- never rebuilt here."""
    joint_obs = agent._joint_obs_array(obs)
    state_arr = agent._state_array(state, joint_obs)
    with torch.no_grad():
        ctx = agent._r30_context_tensors(state_arr, joint_obs)
    (_state_t, joint_t, compact, _team_code, team_vector, _tp, _tl, _cd, _cmi, _ae, weights, relevance) = ctx
    omega = weights if agent.high_condition_on_omega else None
    agent_relevance = relevance if agent.use_agent_prototype_relevance else None
    return {
        "joint_obs": joint_t.squeeze(0),
        "compact": compact,
        "team_vector": team_vector,
        "omega": omega,
        "agent_relevance": agent_relevance,
    }


def enumerate_order(
    agent: StandaloneProcessAgent,
    context: dict[str, Any],
    skills: tuple[int, int],
    ages: tuple[int, int],
    active: tuple[bool, bool],
    order_code: str,
) -> list[Outcome]:
    """VC-D1: the joint distribution under one order, read entirely from
    `token_mass` and advanced entirely by `advance_working_state`.

    First agent's distribution from the initial roster; for each of its four
    outcomes the working state is advanced and the second agent's
    conditional is read; the joint product is accumulated in float64
    (A-VC-7) from raw masses in the policy probability dtype.
    """
    first_agent, second_agent = ORDER_SEQUENCES[order_code]
    base_skills = torch.as_tensor(skills, dtype=torch.long)
    base_ages = torch.as_tensor(ages, dtype=torch.long)
    base_active = torch.as_tensor(active, dtype=torch.bool)

    rng_before = torch.get_rng_state()
    outcomes: list[Outcome] = []
    with torch.no_grad():
        first_mass = agent.high.token_mass(
            context["joint_obs"], context["compact"], context["team_vector"],
            base_skills, base_ages, base_active, first_agent,
            context["omega"], context["agent_relevance"],
        )
        _assert_branch_semantics(first_mass, int(skills[first_agent]), bool(active[first_agent]))

        for first_kind, first_skill in legal_tokens(int(skills[first_agent]), bool(active[first_agent])):
            m1 = _mass_of(first_mass, first_kind, first_skill)
            ws = base_skills.clone()
            wa = base_ages.clone()
            wact = base_active.clone()
            advance_working_state(ws, wa, wact, first_agent, first_kind, first_skill)
            second_mass = agent.high.token_mass(
                context["joint_obs"], context["compact"], context["team_vector"],
                ws, wa, wact, second_agent,
                context["omega"], context["agent_relevance"],
            )
            _assert_branch_semantics(second_mass, int(ws[second_agent].item()), bool(wact[second_agent].item()))
            for second_kind, second_skill in legal_tokens(
                int(ws[second_agent].item()), bool(wact[second_agent].item())
            ):
                m2 = _mass_of(second_mass, second_kind, second_skill)
                final = ws.clone()
                final_ages = wa.clone()
                final_active = wact.clone()
                advance_working_state(final, final_ages, final_active, second_agent, second_kind, second_skill)
                outcomes.append(
                    Outcome(
                        first_agent=first_agent,
                        second_agent=second_agent,
                        first_kind=int(first_kind),
                        first_skill=int(first_skill),
                        second_kind=int(second_kind),
                        second_skill=int(second_skill),
                        raw_first_mass=float(m1),
                        raw_second_mass=float(m2),
                        raw_joint_mass=float(np.float64(m1) * np.float64(m2)),
                        final_skills=(int(final[0].item()), int(final[1].item())),
                    )
                )

    if not torch.equal(rng_before, torch.get_rng_state()):
        raise Vk0cAssertionError(
            f"{REASON_POLICY_RNG_CONSUMED_BY_PURE_PATH}: the VC-D1 enumeration consumed torch RNG; "
            "the pure path must never sample"
        )
    if len(outcomes) != N_OUTCOMES:
        raise Vk0cAssertionError(
            f"enumeration produced {len(outcomes)} outcomes, expected exactly {N_OUTCOMES}"
        )
    coordinates = {o.final_skills for o in outcomes}
    if len(coordinates) != N_OUTCOMES:
        raise Vk0cAssertionError(
            f"enumeration produced {len(coordinates)} distinct final-skill coordinates, "
            f"expected exactly {N_OUTCOMES}"
        )
    return outcomes


def _assert_branch_semantics(mass: dict[str, torch.Tensor], incumbent: int, active: bool) -> None:
    """A-VC-1/A-VC-7 structural invariants, asserted rather than recorded:
    a same-label SET carrying any mass, or a KEEP carrying mass with no
    incumbent, means the probability layer is wrong, not the data."""
    set_mass = mass["set_mass"].reshape(-1)
    keep_mass = float(mass["keep_mass"].reshape(-1)[0].item())
    if active:
        value = float(set_mass[int(incumbent)].item())
        if value != 0.0:
            raise Vk0cAssertionError(
                f"same-label SET mass on incumbent skill {incumbent} is {value!r}, must be exactly 0"
            )
    elif keep_mass != 0.0:
        raise Vk0cAssertionError(
            f"keep_mass is {keep_mass!r} with no incumbent, must be exactly 0"
        )
    if not np.isfinite(keep_mass) or keep_mass < 0.0:
        raise Vk0cAssertionError(f"keep_mass {keep_mass!r} is not finite and non-negative")
    values = set_mass.detach().cpu().numpy().astype(np.float64)
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise Vk0cAssertionError(f"set_mass {values.tolist()!r} is not finite and non-negative")


def policy_probability_dtype(agent: StandaloneProcessAgent) -> str:
    return str(agent.high.skill_head.weight.dtype).replace("torch.", "")


def mass_tolerance(dtype_name: str) -> float:
    """A-VC-7: `mass_tolerance = 32 x eps(policy probability dtype)`."""
    return 32.0 * float(np.finfo(np.dtype(dtype_name)).eps)


@dataclass
class CanonicalDistribution:
    """C-3: the ONE canonical normalized distribution. Built once per
    (anchor, order, policy state) after validation, and used for every
    downstream quantity -- TV, marginals, task consequences, occupancy
    propagation. Raw masses and the normalization correction are preserved
    on it so the rows can record both."""

    outcomes: list[Outcome]
    probabilities: list[float]
    raw_joint_mass_sum: float
    normalization_correction: float
    tolerance: float
    dtype_name: str
    within_tolerance: bool


def canonicalize(outcomes: list[Outcome], dtype_name: str) -> CanonicalDistribution:
    tolerance = mass_tolerance(dtype_name)
    raw_sum = float(np.float64(math_fsum(o.raw_joint_mass for o in outcomes)))
    within = bool(abs(raw_sum - 1.0) <= tolerance)
    if raw_sum <= 0.0:
        raise Vk0cAssertionError(f"raw joint mass sum {raw_sum!r} is not positive")
    probabilities = [float(np.float64(o.raw_joint_mass) / np.float64(raw_sum)) for o in outcomes]
    return CanonicalDistribution(
        outcomes=outcomes,
        probabilities=probabilities,
        raw_joint_mass_sum=raw_sum,
        normalization_correction=float(1.0 - raw_sum),
        tolerance=tolerance,
        dtype_name=dtype_name,
        within_tolerance=within,
    )


def math_fsum(values: Iterable[float]) -> float:
    """Exact-in-float64 summation of the sixteen raw joint masses (A-VC-7).
    `sum()` would leave a term whose magnitude is comparable to the
    dtype-derived `mass_tolerance` the sum is then tested against, so the
    validity test would partly be measuring its own accumulation error."""
    return math.fsum(values)


def keep_and_set_marginals(dist: CanonicalDistribution) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """Per-agent KEEP / SET marginals from the canonical p_hat (A-VC-7:
    p_hat drives marginals, never the raw masses)."""
    keep = {key: 0.0 for key in AGENT_KEYS}
    sets: dict[str, dict[str, float]] = {key: {str(z): 0.0 for z in range(N_SKILLS)} for key in AGENT_KEYS}
    for outcome, p in zip(dist.outcomes, dist.probabilities):
        for position in ("first", "second"):
            agent_id = outcome.first_agent if position == "first" else outcome.second_agent
            token = outcome.token(position)
            key = AGENT_KEYS[agent_id]
            if token["kind"] == TOKEN_KEEP:
                keep[key] += p
            else:
                sets[key][token["skill"]] += p
    return keep, sets


def coverage_flags(slow_vector: list[int], fast_vector: list[int]) -> tuple[bool, bool]:
    """Realization binding (recorded, not a result-branch threshold -- the
    analyzer reports coverage-failure MASS under A-VC-8 and no Factor A-D
    predicate reads it): a duty is "covered" over a window only if its match
    score is 1 at every one of the window's five primitive steps. On this
    toy a match of 1 requires exactly the target axis AND the target sign, so
    this is the direct measurable form of "the duty went unserved"."""
    slow_failure = any(int(v) != 1 for v in slow_vector)
    fast_failure = any(int(v) != 1 for v in fast_vector)
    return bool(slow_failure), bool(fast_failure)


# =============================================================================
# (5) Positive control -- VC-D2
# =============================================================================


def forced_token_for_target(incumbent: int, active: bool, target_skill: int) -> tuple[int, int]:
    """The forced token that lands `agent` on `target_skill`. With an
    incumbent, landing on the incumbent is a KEEP (a same-label SET is
    structurally excluded, and `_force_token` refuses it); every other target
    is a SET. With no incumbent every target is a SET."""
    if active and int(target_skill) == int(incumbent):
        return (KEEP_TOKEN, INVALID_SKILL)
    return (SET_TOKEN, int(target_skill))


@dataclass
class ForcedWindowOutcome:
    fingerprint_match: bool
    realized_skills: tuple[int, int]
    primitive_actions: list[list[list[float]]]
    reward_vector: list[float]
    slow_match_vector: list[int]
    fast_match_vector: list[int]
    post_window_state_hash: str


def run_forced_window(
    *,
    agent: StandaloneProcessAgent,
    config,
    anchor: Anchor,
    order_code: str,
    forced_tokens: dict[int, tuple[int, int]],
) -> ForcedWindowOutcome:
    """VC-D2 deterministic positive control: restore the anchor by from-reset
    natural replay, force BOTH agents through the existing multi-agent
    `forced_tokens` dict under `order_code`, then roll exactly five executed
    primitive steps. Every quantity below is read from the real agent/env,
    never from the analytic kernel -- the ledger requires an executed replay
    here ("no analytic shortcut where the ruling requires executed replay")."""
    order_sequence = np.asarray(ORDER_SEQUENCES[order_code], dtype=np.int64)
    wrapped_env, restored = restore_anchor(agent=agent, config=config, anchor=anchor)
    try:
        obs = restored.obs
        state = restored.state
        step = restored.primitive_step
        max_steps = int(config.max_steps)
        agent.maybe_assign_skills(
            obs, state=state, step=step, k=K0, env_id=0, deterministic=False,
            collect_r31=False, forced_tokens=forced_tokens, agent_order=order_sequence,
        )
        realized = (int(agent.active_skills[0][0]), int(agent.active_skills[0][1]))
        rewards: list[float] = []
        slow: list[int] = []
        fast: list[int] = []
        actions_log: list[list[list[float]]] = []
        for _ in range(WINDOW):
            actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
            actions_arr = np.asarray(actions, dtype=np.float32).reshape(N_AGENTS, -1)
            actions_log.append([[float(x) for x in row] for row in actions_arr])
            obs, reward, terminated, truncated, info = wrapped_env.step(actions)
            state = info.get("next_state", state)
            metrics = info.get("reward_info") or {}
            rewards.append(float(reward))
            slow.append(vk0b._binary_match(metrics.get("r39_toy_slow_match", 0.0)))
            fast.append(vk0b._binary_match(metrics.get("r39_toy_fast_match", 0.0)))
            step += 1
            done = bool(terminated or truncated) or step >= max_steps
            agent.record_environment_step(
                0, reward=float(reward), next_obs=obs, next_state=state, done=done, collect_r31=False,
            )
            if done:
                break
        if len(rewards) != WINDOW:
            raise Vk0cAssertionError(
                f"positive-control window ran {len(rewards)} steps, expected exactly {WINDOW}"
            )
        return ForcedWindowOutcome(
            fingerprint_match=bool(restored.fingerprint_match),
            realized_skills=realized,
            primitive_actions=actions_log,
            reward_vector=rewards,
            slow_match_vector=slow,
            fast_match_vector=fast,
            post_window_state_hash=hash_bytes(np.asarray(state, dtype=np.float32).tobytes()),
        )
    finally:
        wrapped_env.close()


# =============================================================================
# (6a) Inter-check transition + Gate B -- A-VC-4
# =============================================================================


def pure_inter_check_transition(
    skills: tuple[int, int],
    ages: tuple[int, int],
    active: tuple[bool, bool],
    tokens: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int], tuple[bool, bool], tuple[int, int]]:
    """A-VC-4's frozen inter-check transition.

    KEEP -> same skill, age + K0. SET(z) -> skill z, age 0 at the edit and
    K0 at the next check. Active True after any legal token. Returns
    `(post_check_skills, next_check_ages, next_check_active,
    post_check_ages)`; `post_check_ages` is the roster the WINDOW runs with
    (age 0 for a just-edited agent), `next_check_ages` is the pre-decision
    roster of check + 1.

    The within-check part of the mutation is delegated to
    `advance_working_state` -- the same helper `act_sequence` and the
    enumeration both use -- so only the inter-check ageing is written here.
    """
    ws = torch.as_tensor(skills, dtype=torch.long).clone()
    wa = torch.as_tensor(ages, dtype=torch.long).clone()
    wact = torch.as_tensor(active, dtype=torch.bool).clone()
    for agent_id in range(N_AGENTS):
        kind, skill = tokens[agent_id]
        advance_working_state(ws, wa, wact, agent_id, int(kind), int(skill))
    post_skills = (int(ws[0].item()), int(ws[1].item()))
    post_ages = (int(wa[0].item()), int(wa[1].item()))
    post_active = (bool(wact[0].item()), bool(wact[1].item()))
    next_ages = tuple(
        int(post_ages[i]) + K0 if post_active[i] else int(post_ages[i]) for i in range(N_AGENTS)
    )
    return post_skills, (int(next_ages[0]), int(next_ages[1])), post_active, post_ages


# Reachable pre-decision ages for an ACTIVE agent on this frozen 8-check
# clock: a skill set at check j has age K0 * (c - j) at check c, so the
# reachable set at any check is {K0, 2*K0, ..., (TOTAL_CHECKS-1)*K0}.
REACHABLE_ACTIVE_AGES = tuple(K0 * m for m in range(1, TOTAL_CHECKS))


def canonical_transition_cases() -> Iterator[dict[str, Any]]:
    """The complete set of canonical transition cases A-VC-4's Gate B must
    cover: every pre-decision roster class reachable on this clock, crossed
    with every legal joint token.

    * no-incumbent class (the initial check): `active=(False, False)`,
      `skills=(INVALID_SKILL, INVALID_SKILL)`, `ages=(0, 0)`, and all 16
      SET/SET joint tokens;
    * incumbent class: all 16 physical-agent skill pairs, all 49 reachable
      active age pairs, and all 16 legal joint tokens
      (KEEP + the three non-incumbent SETs per agent).

    The age dimension is enumerated in full rather than sampled because
    A-VC-4's rule is stated on the age (`age + 5` / `0 then 5`), and a rule
    stated on a value is not tested by one value of it.
    """
    for tokens in _joint_tokens(INVALID_SKILL, INVALID_SKILL, False, False):
        yield {
            "skills": (INVALID_SKILL, INVALID_SKILL),
            "ages": (0, 0),
            "active": (False, False),
            "tokens": tokens,
        }
    for skill0 in range(N_SKILLS):
        for skill1 in range(N_SKILLS):
            for age0 in REACHABLE_ACTIVE_AGES:
                for age1 in REACHABLE_ACTIVE_AGES:
                    for tokens in _joint_tokens(skill0, skill1, True, True):
                        yield {
                            "skills": (skill0, skill1),
                            "ages": (age0, age1),
                            "active": (True, True),
                            "tokens": tokens,
                        }


def _joint_tokens(skill0: int, skill1: int, active0: bool, active1: bool):
    for t0 in legal_tokens(skill0, active0):
        for t1 in legal_tokens(skill1, active1):
            yield (t0, t1)


def execute_one_window_transition(
    *,
    agent: StandaloneProcessAgent,
    wrapped_env,
    env_seed: int,
    case: dict[str, Any],
    check_index: int = 1,
) -> tuple[tuple[int, int], tuple[int, int], tuple[bool, bool]]:
    """Drive the REAL agent and env through one forced check plus one
    executed five-step window from `case`'s pre-decision roster, and read
    back the agent's own next-check roster."""
    obs, info = wrapped_env.reset(seed=int(env_seed))
    state = info.get("state")
    agent.reset_env_state(0)
    for _ in range(int(check_index) * K0):
        obs, _reward, _term, _trunc, info = wrapped_env.step(_zero_joint_action())
        state = info.get("next_state", state)
    # Install the case's pre-decision roster directly. `reset_env_state`
    # has just zeroed every per-env array, so these four writes are the
    # complete high-level state the check reads (`_r30_maybe_assign_skills`
    # reads active_skills / skill_age / has_active_skill / steps_to_check
    # and nothing else about the roster).
    agent.active_skills[0, :] = np.asarray(
        [max(int(s), 0) for s in case["skills"]], dtype=agent.active_skills.dtype
    )
    agent.skill_age[0, :] = np.asarray(case["ages"], dtype=agent.skill_age.dtype)
    agent.has_active_skill[0, :] = np.asarray(case["active"], dtype=bool)
    agent.steps_to_check[0] = 0

    forced = {i: tuple(int(x) for x in case["tokens"][i]) for i in range(N_AGENTS)}
    agent.maybe_assign_skills(
        obs, state=state, step=int(check_index) * K0, k=K0, env_id=0, deterministic=False,
        collect_r31=False, forced_tokens=forced,
        agent_order=np.asarray(ORDER_SEQUENCES[ORDER_CANONICAL], dtype=np.int64),
    )
    post_skills = (int(agent.active_skills[0][0]), int(agent.active_skills[0][1]))
    for _ in range(WINDOW):
        actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
        obs, reward, _terminated, _truncated, info = wrapped_env.step(actions)
        state = info.get("next_state", state)
        agent.record_environment_step(
            0, reward=float(reward), next_obs=obs, next_state=state, done=False, collect_r31=False,
        )
    next_ages = (int(agent.skill_age[0][0]), int(agent.skill_age[0][1]))
    next_active = (bool(agent.has_active_skill[0][0]), bool(agent.has_active_skill[0][1]))
    return post_skills, next_ages, next_active


def gate_b_transition_parity(
    *,
    agent: StandaloneProcessAgent,
    config,
    kernel: WindowKernel,
    cases: Iterable[dict[str, Any]] | None = None,
    signs: tuple[int, int] = (1, 1),
) -> dict[str, Any]:
    """A-VC-4 Gate B: the pure transition against an executed one-window
    agent/env transition, over the complete canonical case set.

    Gate B is policy-independent by construction (both agents' tokens are
    forced, and A-VC-4's rule is stated on skills/ages/active alone), so the
    driver runs it once per audit rather than once per checkpoint bundle.
    """
    cases = canonical_transition_cases() if cases is None else cases
    env_seed = int(kernel.sign_seeds()[tuple(signs)])
    wrapped_env = vk0b.make_env(config, env_seed)
    checked = 0
    mismatches: list[dict[str, Any]] = []
    try:
        for case in cases:
            pure_skills, pure_next_ages, pure_next_active, _post_ages = pure_inter_check_transition(
                case["skills"], case["ages"], case["active"], case["tokens"]
            )
            exec_skills, exec_next_ages, exec_next_active = execute_one_window_transition(
                agent=agent, wrapped_env=wrapped_env, env_seed=env_seed, case=case
            )
            checked += 1
            if (pure_skills, pure_next_ages, pure_next_active) != (
                exec_skills,
                exec_next_ages,
                exec_next_active,
            ):
                mismatches.append(
                    {
                        "case": {k: list(v) if isinstance(v, tuple) else v for k, v in case.items()},
                        "pure": [list(pure_skills), list(pure_next_ages), list(pure_next_active)],
                        "executed": [list(exec_skills), list(exec_next_ages), list(exec_next_active)],
                    }
                )
    finally:
        wrapped_env.close()
    return {"cases_checked": checked, "mismatches": mismatches[:8], "mismatch_count": len(mismatches)}


# =============================================================================
# (6b) Exact propagation by finite-state occupancy -- VC-D3 / A-VC-4 / A-VC-6
# =============================================================================


PropagationState = tuple[int, int, int, int, bool, bool]
"""(skill0, skill1, age0, age1, active0, active1) at a check's pre-decision
moment. The check index and the initial signs are carried by the occupancy
map's position in the sweep, not repeated inside each key."""

INITIAL_PROPAGATION_STATE: PropagationState = (
    INVALID_SKILL,
    INVALID_SKILL,
    0,
    0,
    False,
    False,
)
"""A-VC-4: propagation begins at `check_index = 0, active_mask =
[False, False], no incumbents, ages = [0, 0]` under the no-incumbent
semantics."""


def state_key(check_index: int, state: PropagationState) -> str:
    s0, s1, a0, a1, act0, act1 = state
    return f"c{int(check_index)}|s{int(s0)},{int(s1)}|a{int(a0)},{int(a1)}|m{int(bool(act0))}{int(bool(act1))}"


def reachable_state_bound() -> int:
    """The finite-state bound VC-D3 relies on: one no-incumbent state at
    check 0, then at check c >= 1 at most `N_SKILLS^2 * c^2` states (16 skill
    pairs x the c reachable ages per agent). 2,241 for this frozen clock --
    against `N_OUTCOMES ** TOTAL_CHECKS` = 4.3e9 tree paths."""
    return 1 + sum(N_SKILLS**2 * (c**2) for c in range(1, TOTAL_CHECKS))


@dataclass
class PropagationResult:
    rows: list[dict[str, Any]]
    distinct_states_visited: int
    distribution_evaluations: int
    occupancy_by_check: list[dict[str, float]]


class Propagator:
    """Memoized finite-state occupancy pushforward (VC-D3).

    The 16-outcome distribution at a state is memoized on
    `(check_index, state, order_code)` -- the policy and the initial signs
    are fixed for the life of one `Propagator`. That memo is what bounds the
    work to the reachable-state count instead of the `16 ** TOTAL_CHECKS`
    paths a tree replay would walk.
    """

    def __init__(
        self,
        *,
        agent: StandaloneProcessAgent,
        kernel: WindowKernel,
        signs: tuple[int, int],
        dtype_name: str,
    ) -> None:
        self.agent = agent
        self.kernel = kernel
        self.signs = tuple(signs)
        self.dtype_name = str(dtype_name)
        self._context_cache: dict[int, dict[str, Any]] = {}
        self._dist_cache: dict[tuple[int, PropagationState, str], CanonicalDistribution] = {}
        self._run_cache: dict[str, PropagationResult] = {}
        self.distribution_evaluations = 0
        self.distinct_states_visited: set[tuple[int, PropagationState]] = set()
        self.tolerance_violations: list[str] = []

    def context_at(self, check_index: int) -> dict[str, Any]:
        cached = self._context_cache.get(int(check_index))
        if cached is None:
            obs, state = self.kernel.policy_inputs_at(self.signs, int(check_index))
            cached = policy_context(self.agent, obs, state)
            self._context_cache[int(check_index)] = cached
        return cached

    def distribution(self, check_index: int, state: PropagationState, order_code: str) -> CanonicalDistribution:
        key = (int(check_index), state, str(order_code))
        cached = self._dist_cache.get(key)
        if cached is not None:
            return cached
        s0, s1, a0, a1, act0, act1 = state
        outcomes = enumerate_order(
            self.agent,
            self.context_at(check_index),
            (int(s0), int(s1)),
            (int(a0), int(a1)),
            (bool(act0), bool(act1)),
            order_code,
        )
        dist = canonicalize(outcomes, self.dtype_name)
        if not dist.within_tolerance:
            self.tolerance_violations.append(
                f"{state_key(check_index, state)}|{order_code}: raw sum {dist.raw_joint_mass_sum!r}"
            )
        self._dist_cache[key] = dist
        self.distribution_evaluations += 1
        return dist

    def run(self, order_code: str) -> PropagationResult:
        cached = self._run_cache.get(str(order_code))
        if cached is not None:
            return cached
        occupancy: dict[PropagationState, float] = {INITIAL_PROPAGATION_STATE: 1.0}
        rows: list[dict[str, Any]] = []
        occupancy_by_check: list[dict[str, float]] = []
        lifetime_keys = [str(K0 * m) for m in range(0, TOTAL_CHECKS + 1)]
        visited_this_run: set[tuple[int, PropagationState]] = set()

        for check_index in range(TOTAL_CHECKS):
            occupancy_by_check.append(
                {state_key(check_index, s): float(p) for s, p in sorted(occupancy.items())}
            )
            next_occupancy: dict[PropagationState, float] = defaultdict(float)
            expected_reward = [0.0] * WINDOW
            expected_slow = [0.0] * WINDOW
            expected_fast = [0.0] * WINDOW
            keep_rate = {key: 0.0 for key in AGENT_KEYS}
            set_rate = {key: 0.0 for key in AGENT_KEYS}
            renewal_rate = {key: 0.0 for key in AGENT_KEYS}
            lifetime = {key: {length: 0.0 for length in lifetime_keys} for key in AGENT_KEYS}

            for state, occ in occupancy.items():
                visited_this_run.add((check_index, state))
                self.distinct_states_visited.add((check_index, state))
                dist = self.distribution(check_index, state, order_code)
                s0, s1, a0, a1, act0, act1 = state
                pre_ages = (int(a0), int(a1))
                pre_active = (bool(act0), bool(act1))
                for outcome, probability in zip(dist.outcomes, dist.probabilities):
                    weight = float(occ) * float(probability)
                    if weight == 0.0:
                        continue
                    tokens = _tokens_by_agent(outcome)
                    post_skills, next_ages, next_active, post_ages = pure_inter_check_transition(
                        (int(s0), int(s1)), pre_ages, pre_active, tokens
                    )
                    window = self.kernel.evaluate(self.signs, check_index, post_skills)
                    for step in range(WINDOW):
                        expected_reward[step] += weight * float(window["rewards"][step])
                        expected_slow[step] += weight * float(window["slow"][step])
                        expected_fast[step] += weight * float(window["fast"][step])
                    for agent_id in range(N_AGENTS):
                        key = AGENT_KEYS[agent_id]
                        kind = int(tokens[agent_id][0])
                        if kind == KEEP_TOKEN:
                            keep_rate[key] += weight
                        else:
                            set_rate[key] += weight
                            if pre_active[agent_id]:
                                # A renewal is a voluntary SET onto an agent
                                # that HAD an incumbent; the initial check's
                                # SET is an assignment, not a renewal.
                                renewal_rate[key] += weight
                                lifetime[key][str(int(pre_ages[agent_id]))] += weight
                        if check_index == TOTAL_CHECKS - 1:
                            # Every segment still open at the last check is
                            # ended by episode termination K0 steps later.
                            lifetime[key][str(int(post_ages[agent_id]) + K0)] += weight
                    next_occupancy[
                        (
                            int(post_skills[0]),
                            int(post_skills[1]),
                            int(next_ages[0]),
                            int(next_ages[1]),
                            bool(next_active[0]),
                            bool(next_active[1]),
                        )
                    ] += weight

            rows.append(
                {
                    "check_index": int(check_index),
                    "occupancy_summary": [
                        {"state_key": key, "occupancy_probability": _unit(value, "occupancy")}
                        for key, value in occupancy_by_check[-1].items()
                    ],
                    "expected_external_reward_vector": [float(x) for x in expected_reward],
                    "expected_slow_match_vector": [_unit(x, "slow match") for x in expected_slow],
                    "expected_fast_match_vector": [_unit(x, "fast match") for x in expected_fast],
                    "expected_window_return": float(sum(expected_reward)),
                    "expected_keep_rate": {k: _unit(v, "keep rate") for k, v in keep_rate.items()},
                    "expected_set_rate": {k: _unit(v, "set rate") for k, v in set_rate.items()},
                    "expected_renewal_rate": {k: _unit(v, "renewal rate") for k, v in renewal_rate.items()},
                    "lifetime_mass": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in lifetime.items()},
                }
            )
            occupancy = dict(next_occupancy)

        episode_return = float(sum(sum(row["expected_external_reward_vector"]) for row in rows))
        for row in rows:
            row["expected_episode_return_total"] = episode_return
        result = PropagationResult(
            rows=rows,
            distinct_states_visited=len(visited_this_run),
            distribution_evaluations=self.distribution_evaluations,
            occupancy_by_check=occupancy_by_check,
        )
        self._run_cache[str(order_code)] = result
        return result


def _unit(value: float, label: str, tolerance: float = 1e-9) -> float:
    """Clamp an occupancy-weighted expectation into [0, 1] -- but only after
    asserting it was already there up to float64 accumulation noise. A
    silent clamp would turn a genuinely broken occupancy sweep (mass leaking
    or duplicating) into a value that still validates."""
    value = float(value)
    if not np.isfinite(value) or value < -tolerance or value > 1.0 + tolerance:
        raise Vk0cAssertionError(
            f"{label} expectation {value!r} is outside [0, 1] by more than {tolerance!r}; "
            "the occupancy sweep does not carry unit mass"
        )
    return float(min(max(value, 0.0), 1.0))


def _tokens_by_agent(outcome: Outcome) -> tuple[tuple[int, int], tuple[int, int]]:
    tokens: dict[int, tuple[int, int]] = {
        outcome.first_agent: (outcome.first_kind, outcome.first_skill),
        outcome.second_agent: (outcome.second_kind, outcome.second_skill),
    }
    return (tokens[0], tokens[1])


# =============================================================================
# Factual-row reproduction (VC-D3)
# =============================================================================


def reproduce_factual_episode(
    *,
    kernel: WindowKernel,
    signs: tuple[int, int],
    anchors_by_check: dict[int, Anchor],
) -> dict[str, Any]:
    """Replay one episode's FACTUAL token sequence through the same
    finite-state machinery and the same deterministic reward kernel, and
    compare against the stored V-K0B rows' five-step vectors.

    The V-K0B trace omits the initial check (index 0) by convention, so its
    tokens are not stored; check 1's own recorded incumbent pair IS the
    outcome of check 0 (a skill set at check 0 has age K0 at check 1), so
    the sequence is reconstructed from there and check 0's window is
    reproduced as a by-product rather than assumed.

    Failure is invalidity, not evidence.
    """
    checks = sorted(anchors_by_check)
    if not checks or checks != list(range(checks[0], checks[0] + len(checks))):
        raise Vk0cRefusalError(
            REASON_ANCHOR_INVENTORY_INCONSISTENT,
            f"factual reproduction needs a contiguous run of checks, got {checks}",
        )

    first = anchors_by_check[checks[0]]
    skills = tuple(int(x) for x in first.incumbent)
    ages = tuple(int(x) for x in first.skill_age)
    active = tuple(bool(x) for x in first.active_mask)

    conformance = {
        "factual_reward_vector_reproduced": True,
        "factual_slow_match_vector_reproduced": True,
        "factual_fast_match_vector_reproduced": True,
        "factual_roster_transition_reproduced": True,
    }
    details: list[str] = []

    reproduced_windows: dict[int, dict[str, Any]] = {}
    if checks[0] == 1:
        # The V-K0B trace omits the initial check by convention, so check 0's
        # tokens are not stored -- but check 1's own recorded incumbent pair
        # IS their outcome, so check 0's window is reproduced here rather
        # than assumed.
        reproduced_windows[0] = kernel.evaluate(signs, 0, skills)

    for check_index in checks:
        anchor = anchors_by_check[check_index]
        if tuple(int(x) for x in anchor.incumbent) != skills or tuple(
            int(x) for x in anchor.skill_age
        ) != ages or tuple(bool(x) for x in anchor.active_mask) != active:
            conformance["factual_roster_transition_reproduced"] = False
            details.append(
                f"check {check_index}: propagated roster {(skills, ages, active)} != stored "
                f"{(tuple(anchor.incumbent), tuple(anchor.skill_age), tuple(anchor.active_mask))}"
            )
        tokens = _factual_tokens(anchor)
        post_skills, next_ages, next_active, _post_ages = pure_inter_check_transition(
            skills, ages, active, tokens
        )
        window = kernel.evaluate(signs, check_index, post_skills)
        reproduced_windows[check_index] = window
        if [float(x) for x in window["rewards"]] != [float(x) for x in anchor.natural_reward_vector]:
            conformance["factual_reward_vector_reproduced"] = False
            details.append(
                f"check {check_index}: reward {window['rewards']} != stored {list(anchor.natural_reward_vector)}"
            )
        if [int(x) for x in window["slow"]] != [int(x) for x in anchor.slow_match_vector]:
            conformance["factual_slow_match_vector_reproduced"] = False
            details.append(
                f"check {check_index}: slow {window['slow']} != stored {list(anchor.slow_match_vector)}"
            )
        if [int(x) for x in window["fast"]] != [int(x) for x in anchor.fast_match_vector]:
            conformance["factual_fast_match_vector_reproduced"] = False
            details.append(
                f"check {check_index}: fast {window['fast']} != stored {list(anchor.fast_match_vector)}"
            )
        skills, ages, active = post_skills, next_ages, next_active

    return {"conformance": conformance, "details": details[:8], "windows": reproduced_windows}


def _factual_tokens(anchor: Anchor) -> tuple[tuple[int, int], tuple[int, int]]:
    tokens: list[tuple[int, int]] = []
    for agent_id in range(N_AGENTS):
        entry = anchor.factual_joint_token[str(agent_id)]
        if str(entry["kind"]) == vk0b.NATURAL_TOKEN_KEEP:
            tokens.append((KEEP_TOKEN, INVALID_SKILL))
        else:
            tokens.append((SET_TOKEN, int(entry["set_skill"])))
    return (tokens[0], tokens[1])


# =============================================================================
# (8) Fresh-initialization control -- VC-D5 / A-VC-11
# =============================================================================


def build_fresh_agent(config_module_name: str, training_seed: int) -> StandaloneProcessAgent:
    """VC-D5: `torch.manual_seed(seed)` IMMEDIATELY before the construction,
    with a freshly instantiated `Config` so no earlier construction can have
    mutated it. Construction consumes the global torch stream in a fixed
    order and performs no internal reseeding (scout-verified), which is
    exactly what the two-construction hash equality below evidences."""
    config = importlib.import_module(config_module_name).Config()
    torch.manual_seed(int(training_seed))
    agent = vk0b.build_agent(config, checkpoint_path=None)
    return agent


def fresh_init_control(
    *, config_module_name: str, training_seed: int, resolved_config_hash: str
) -> dict[str, Any]:
    hashes: list[tuple[str, str]] = []
    for _ in range(2):
        agent = build_fresh_agent(config_module_name, training_seed)
        hashes.append(
            (
                agent_construction_hash(agent, DECISION_CONTEXT_MODULES, resolved_config_hash),
                agent_construction_hash(agent, ALL_CONSTRUCTED_MODULES, resolved_config_hash),
            )
        )
        del agent
    return {
        "construction_1_param_hash": hashes[0][0],
        "construction_2_param_hash": hashes[1][0],
        "construction_1_all_module_hash": hashes[0][1],
        "construction_2_all_module_hash": hashes[1][1],
        "decision_context_modules": list(DECISION_CONTEXT_MODULES),
        "all_constructed_modules": list(ALL_CONSTRUCTED_MODULES),
        "deterministic": bool(hashes[0][0] == hashes[1][0]),
    }


# =============================================================================
# Row construction
# =============================================================================


def build_matched_state_rows(
    *,
    anchor: Anchor,
    policy_state: str,
    checkpoint_hash: str,
    order_code: str,
    dist: CanonicalDistribution,
    kernel: WindowKernel,
    signs: tuple[int, int],
    boundary_state_replay_ok: bool,
) -> list[dict[str, Any]]:
    keep_marginal, set_marginal = keep_and_set_marginals(dist)
    windows = [kernel.evaluate(signs, anchor.check_index, o.final_skills) for o in dist.outcomes]
    best_total = max(float(w["total"]) for w in windows)
    rows: list[dict[str, Any]] = []
    for index, (outcome, probability, window) in enumerate(zip(dist.outcomes, dist.probabilities, windows)):
        slow_failure, fast_failure = coverage_flags(window["slow"], window["fast"])
        rows.append(
            {
                "contract_id": CONTRACT_ID,
                "vk0c_schema_version": VK0C_SCHEMA_VERSION,
                "training_seed": int(anchor.training_seed),
                "evaluation_index": int(anchor.evaluation_index),
                "episode_id": int(anchor.episode_id),
                "check_index": int(anchor.check_index),
                "occupancy_stratum": anchor.occupancy_stratum,
                "checkpoint_hash": str(checkpoint_hash),
                "resolved_config_hash": str(anchor.resolved_config_hash),
                "policy_state": str(policy_state),
                "order_code": str(order_code),
                "outcome_index": int(index),
                "incumbent_skill": {AGENT_KEYS[i]: str(int(anchor.incumbent[i])) for i in range(N_AGENTS)},
                "final_skill": {AGENT_KEYS[i]: str(int(outcome.final_skills[i])) for i in range(N_AGENTS)},
                "first_token": outcome.token("first"),
                "second_token": outcome.token("second"),
                "first_agent": int(outcome.first_agent),
                "second_agent": int(outcome.second_agent),
                "policy_probability_dtype": dist.dtype_name,
                "mass_tolerance": float(dist.tolerance),
                "raw_first_mass": float(outcome.raw_first_mass),
                "raw_second_mass": float(outcome.raw_second_mass),
                "raw_joint_mass": float(outcome.raw_joint_mass),
                "raw_joint_mass_sum": float(dist.raw_joint_mass_sum),
                "normalization_correction": float(dist.normalization_correction),
                "canonical_joint_probability": float(probability),
                "keep_marginal": {k: float(v) for k, v in keep_marginal.items()},
                "set_marginal": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in set_marginal.items()},
                "five_step_reward": float(window["total"]),
                "slow_match_vector": [int(x) for x in window["slow"]],
                "fast_match_vector": [int(x) for x in window["fast"]],
                "task_optimal": bool(float(window["total"]) >= best_total - 1e-12),
                "slow_coverage_failure": bool(slow_failure),
                "fast_coverage_failure": bool(fast_failure),
                "boundary_state_replay_ok": bool(boundary_state_replay_ok),
            }
        )
    return rows


def build_propagation_rows(
    *,
    training_seed: int,
    evaluation_index: int,
    episode_id: int,
    occupancy_stratum: str,
    checkpoint_hash: str,
    policy_state: str,
    order_code: str,
    result: PropagationResult,
    replay_conformance: dict[str, bool],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in result.rows:
        rows.append(
            {
                "contract_id": CONTRACT_ID,
                "vk0c_schema_version": VK0C_SCHEMA_VERSION,
                "training_seed": int(training_seed),
                "evaluation_index": int(evaluation_index),
                "episode_id": int(episode_id),
                "check_index": int(row["check_index"]),
                "occupancy_stratum": str(occupancy_stratum),
                "checkpoint_hash": str(checkpoint_hash),
                "policy_state": str(policy_state),
                "order_code": str(order_code),
                "occupancy_summary": row["occupancy_summary"],
                "expected_slow_match_vector": row["expected_slow_match_vector"],
                "expected_fast_match_vector": row["expected_fast_match_vector"],
                "expected_external_reward_vector": row["expected_external_reward_vector"],
                # A-VC-6 requires the expectation at EVERY primitive step and
                # the expected episode return. One row per check carries its
                # own five primitive steps, so `expected_episode_return` is
                # this check's window contribution (the identity the analyzer
                # checks: it must equal the sum of this row's five-vector) and
                # `expected_episode_return_total` -- identical on all eight of
                # an episode's rows -- carries the whole-episode expectation.
                "expected_episode_return": float(row["expected_window_return"]),
                "expected_episode_return_total": float(row["expected_episode_return_total"]),
                "expected_keep_rate": row["expected_keep_rate"],
                "expected_set_rate": row["expected_set_rate"],
                "expected_renewal_rate": row["expected_renewal_rate"],
                "lifetime_mass": row["lifetime_mass"],
                "replay_conformance": {k: bool(v) for k, v in replay_conformance.items()},
                "distinct_states_visited": int(result.distinct_states_visited),
                "reachable_state_bound": int(reachable_state_bound()),
            }
        )
    return rows


# =============================================================================
# Orchestration
# =============================================================================


@dataclass
class RunAccumulator:
    matched_state_rows: list[dict[str, Any]] = field(default_factory=list)
    propagation_rows: list[dict[str, Any]] = field(default_factory=list)
    control_rows: list[dict[str, Any]] = field(default_factory=list)
    four_sign_panel: list[dict[str, Any]] = field(default_factory=list)
    invalid_reasons: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def flag(self, reason_code: str, detail: str) -> None:
        entry = f"{reason_code}: {detail}"
        if entry not in self.invalid_reasons:
            self.invalid_reasons.append(entry)


def evaluate_checkpoint_bundle(
    *,
    entry: dict[str, Any],
    config_module_name: str,
    anchors: list[Anchor],
    accumulator: RunAccumulator,
    kernel: WindowKernel,
) -> None:
    config_module = importlib.import_module(config_module_name)
    config = config_module.Config()
    training_seed = int(entry["training_seed"])
    checkpoint_hash = str(entry["checkpoint_sha256"])
    resolved_config_hash = str(entry["resolved_config_hash"])

    trained = vk0b.build_agent(config, checkpoint_path=entry["checkpoint_path"])
    fresh = build_fresh_agent(config_module_name, training_seed)
    for module in (fresh.high, fresh.high_value):
        if module is not None:
            module.eval()
    dtype_name = policy_probability_dtype(trained)

    # ---- (8) fresh-init determinism control (VC-D5 / A-VC-11) -------------
    control = fresh_init_control(
        config_module_name=config_module_name,
        training_seed=training_seed,
        resolved_config_hash=resolved_config_hash,
    )
    accumulator.control_rows.append(
        {
            "contract_id": CONTRACT_ID,
            "vk0c_schema_version": VK0C_SCHEMA_VERSION,
            "control_type": CONTROL_TYPE_FRESH_INIT,
            "training_seed": training_seed,
            **control,
        }
    )
    if not control["deterministic"]:
        accumulator.flag(
            REASON_FRESH_INITIALIZATION_NONDETERMINISTIC,
            f"seed {training_seed}: two same-seed constructions hashed differently",
        )

    seed_anchors = [a for a in anchors if a.training_seed == training_seed]
    for anchor in seed_anchors:
        if anchor.checkpoint_hash != checkpoint_hash or anchor.resolved_config_hash != resolved_config_hash:
            raise Vk0cRefusalError(
                REASON_CHECKPOINT_AUTHORIZATION_FAILED,
                f"anchor {anchor.key} carries checkpoint/config identity "
                f"({anchor.checkpoint_hash}, {anchor.resolved_config_hash}) which does not match "
                f"the authorized bundle ({checkpoint_hash}, {resolved_config_hash})",
            )

    signs_by_episode: dict[int, tuple[int, int]] = {}
    anchors_by_episode: dict[int, dict[int, Anchor]] = defaultdict(dict)
    for anchor in seed_anchors:
        anchors_by_episode[anchor.evaluation_index][anchor.check_index] = anchor

    # ---- (3)+(4)+(5) per anchor -------------------------------------------
    for anchor in seed_anchors:
        wrapped_env, restored = restore_anchor(agent=trained, config=config, anchor=anchor)
        try:
            if not restored.fingerprint_match:
                accumulator.flag(
                    REASON_ANCHOR_RESTORATION_FINGERPRINT_MISMATCH,
                    f"anchor {anchor.key}: from-reset natural replay did not reproduce the stored "
                    "pre_check_fingerprint",
                )
            signs = restored.initial_signs
            signs_by_episode[anchor.evaluation_index] = signs
            declared = signs_from_targets(
                anchor.current_targets,
                anchor.check_index,
                int(getattr(config, "r39_toy_slow_period_blocks", 6)),
            )
            if declared != signs:
                accumulator.flag(
                    REASON_ANCHOR_RESTORATION_FINGERPRINT_MISMATCH,
                    f"anchor {anchor.key}: signs {signs} from the replayed env disagree with "
                    f"{declared} implied by the stored current_targets",
                )
            if restored.incumbent != anchor.incumbent or restored.skill_age != anchor.skill_age:
                accumulator.flag(
                    REASON_ANCHOR_RESTORATION_FINGERPRINT_MISMATCH,
                    f"anchor {anchor.key}: restored roster {(restored.incumbent, restored.skill_age)} "
                    f"!= stored {(anchor.incumbent, anchor.skill_age)}",
                )
            trained_context = policy_context(trained, restored.obs, restored.state)
            fresh_context = policy_context(fresh, restored.obs, restored.state)
        finally:
            wrapped_env.close()

        for policy_state, agent_obj, context, row_checkpoint in (
            (POLICY_STATE_TRAINED, trained, trained_context, checkpoint_hash),
            (POLICY_STATE_FRESH, fresh, fresh_context, FRESH_INIT_CHECKPOINT_SENTINEL),
        ):
            for order_code in ORDER_CODES:
                outcomes = enumerate_order(
                    agent_obj,
                    context,
                    anchor.incumbent,
                    anchor.skill_age,
                    anchor.active_mask,
                    order_code,
                )
                dist = canonicalize(outcomes, dtype_name)
                if not dist.within_tolerance:
                    accumulator.flag(
                        REASON_ENUMERATION_VALIDITY_FAILED,
                        f"anchor {anchor.key} {policy_state}/{order_code}: |raw_joint_mass_sum - 1| = "
                        f"{abs(dist.raw_joint_mass_sum - 1.0)!r} exceeds mass_tolerance {dist.tolerance!r}",
                    )
                accumulator.matched_state_rows.extend(
                    build_matched_state_rows(
                        anchor=anchor,
                        policy_state=policy_state,
                        checkpoint_hash=row_checkpoint,
                        order_code=order_code,
                        dist=dist,
                        kernel=kernel,
                        signs=signs,
                        boundary_state_replay_ok=bool(restored.fingerprint_match),
                    )
                )

        # ---- (5) positive control: every legal final joint assignment ----
        for target0 in range(N_SKILLS):
            for target1 in range(N_SKILLS):
                forced = {
                    0: forced_token_for_target(anchor.incumbent[0], anchor.active_mask[0], target0),
                    1: forced_token_for_target(anchor.incumbent[1], anchor.active_mask[1], target1),
                }
                per_order: dict[str, ForcedWindowOutcome] = {}
                for order_code in ORDER_CODES:
                    per_order[order_code] = run_forced_window(
                        agent=trained, config=config, anchor=anchor,
                        order_code=order_code, forced_tokens=forced,
                    )
                row = {
                    "contract_id": CONTRACT_ID,
                    "vk0c_schema_version": VK0C_SCHEMA_VERSION,
                    "control_type": CONTROL_TYPE_POSITIVE,
                    "training_seed": int(anchor.training_seed),
                    "evaluation_index": int(anchor.evaluation_index),
                    "episode_id": int(anchor.episode_id),
                    "check_index": int(anchor.check_index),
                    "occupancy_stratum": anchor.occupancy_stratum,
                    "checkpoint_hash": checkpoint_hash,
                    "forced_assignment": {
                        AGENT_KEYS[0]: str(int(target0)),
                        AGENT_KEYS[1]: str(int(target1)),
                    },
                }
                for order_code, outcome in per_order.items():
                    row[f"{order_code}_realized_skill"] = {
                        AGENT_KEYS[i]: str(int(outcome.realized_skills[i])) for i in range(N_AGENTS)
                    }
                    row[f"{order_code}_primitive_actions"] = outcome.primitive_actions
                    row[f"{order_code}_reward_vector"] = outcome.reward_vector
                    row[f"{order_code}_slow_match_vector"] = outcome.slow_match_vector
                    row[f"{order_code}_fast_match_vector"] = outcome.fast_match_vector
                    row[f"{order_code}_post_window_state_hash"] = outcome.post_window_state_hash
                    row[f"{order_code}_boundary_state_replay_ok"] = bool(outcome.fingerprint_match)
                accumulator.control_rows.append(row)
                if not _positive_control_holds(row):
                    accumulator.flag(
                        REASON_ORDER_CONJUGACY_POSITIVE_CONTROL_FAILED,
                        f"anchor {anchor.key} forced assignment ({target0}, {target1})",
                    )

    # ---- (6) propagation + factual-row reproduction -----------------------
    # One `Propagator` per (policy state, initial signs): the finite-state
    # sweep depends on the episode only through its two initial signs, so the
    # 64-episode bank costs four sweeps per policy per order, not 64. Both
    # orders share one instance because the distribution memo is keyed on the
    # order code.
    propagators: dict[tuple[str, tuple[int, int]], Propagator] = {}

    def propagator_for(policy_state: str, agent_obj, signs: tuple[int, int]) -> Propagator:
        key = (str(policy_state), tuple(signs))
        if key not in propagators:
            propagators[key] = Propagator(
                agent=agent_obj, kernel=kernel, signs=tuple(signs), dtype_name=dtype_name
            )
        return propagators[key]

    for evaluation_index, by_check in sorted(anchors_by_episode.items()):
        signs = signs_by_episode.get(evaluation_index)
        if signs is None:
            signs = episode_initial_signs(config, evaluation_index)
        episode_id = int(next(iter(by_check.values())).episode_id)
        stratum = next(iter(by_check.values())).occupancy_stratum

        replay_conformance = {"factual_row_reproduction_not_attempted": True}
        if sorted(by_check) == list(range(1, FROZEN_NONINITIAL_CHECKS + 1)):
            factual = reproduce_factual_episode(kernel=kernel, signs=signs, anchors_by_check=by_check)
            replay_conformance = factual["conformance"]
            if any(v is False for v in replay_conformance.values()):
                accumulator.flag(
                    REASON_FACTUAL_ROW_REPRODUCTION_FAILED,
                    f"seed {training_seed} episode {evaluation_index}: {factual['details']}",
                )

        for policy_state, agent_obj, row_checkpoint in (
            (POLICY_STATE_TRAINED, trained, checkpoint_hash),
            (POLICY_STATE_FRESH, fresh, FRESH_INIT_CHECKPOINT_SENTINEL),
        ):
            for order_code in ORDER_CODES:
                propagator = propagator_for(policy_state, agent_obj, signs)
                result = propagator.run(order_code)
                for violation in propagator.tolerance_violations:
                    accumulator.flag(REASON_ENUMERATION_VALIDITY_FAILED, f"propagation {violation}")
                accumulator.propagation_rows.extend(
                    build_propagation_rows(
                        training_seed=training_seed,
                        evaluation_index=evaluation_index,
                        episode_id=episode_id,
                        occupancy_stratum=stratum,
                        checkpoint_hash=row_checkpoint,
                        policy_state=policy_state,
                        order_code=order_code,
                        result=result,
                        replay_conformance=replay_conformance,
                    )
                )

    # ---- (7) four-sign descriptive panel (A-VC-5) -------------------------
    for slow_sign in (-1, 1):
        for fast_sign in (-1, 1):
            for policy_state, agent_obj in (
                (POLICY_STATE_TRAINED, trained),
                (POLICY_STATE_FRESH, fresh),
            ):
                for order_code in ORDER_CODES:
                    propagator = propagator_for(policy_state, agent_obj, (slow_sign, fast_sign))
                    result = propagator.run(order_code)
                    accumulator.four_sign_panel.append(
                        {
                            "contract_id": CONTRACT_ID,
                            "vk0c_schema_version": VK0C_SCHEMA_VERSION,
                            "panel_kind": "FOUR_SIGN_DESCRIPTIVE_PANEL",
                            "non_inferential": True,
                            "training_seed": training_seed,
                            "initial_slow_sign": int(slow_sign),
                            "initial_fast_sign": int(fast_sign),
                            "policy_state": policy_state,
                            "order_code": order_code,
                            "checks": result.rows,
                        }
                    )


def _take(iterator: Iterable[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in iterator:
        if len(out) >= count:
            break
        out.append(item)
    return out


def _positive_control_holds(row: dict[str, Any]) -> bool:
    """Order-conjugacy predicate, recomputed here from the raw recorded
    vectors exactly as `scripts/analyze_vk0c_result.py::_positive_control_holds`
    does -- the driver never writes a pre-computed pass flag the analyzer
    would then have to trust."""
    forced = row["forced_assignment"]
    for order_code in ORDER_CODES:
        if row[f"{order_code}_realized_skill"] != forced:
            return False
    if row[f"{ORDER_CANONICAL}_realized_skill"] != row[f"{ORDER_REVERSED}_realized_skill"]:
        return False
    if row[f"{ORDER_CANONICAL}_primitive_actions"] != row[f"{ORDER_REVERSED}_primitive_actions"]:
        return False
    for name in ("reward_vector", "slow_match_vector", "fast_match_vector"):
        a = row[f"{ORDER_CANONICAL}_{name}"]
        b = row[f"{ORDER_REVERSED}_{name}"]
        if len(a) != len(b) or any(abs(float(x) - float(y)) > 1e-9 for x, y in zip(a, b)):
            return False
    return row[f"{ORDER_CANONICAL}_post_window_state_hash"] == row[f"{ORDER_REVERSED}_post_window_state_hash"]


# =============================================================================
# Manifest and output
# =============================================================================


def run_verdict_for(invalid_reasons: list[str]) -> str | None:
    """One recorded reason is enough to make the whole run invalid. There is
    deliberately no severity ladder and no reason that is merely a warning:
    every gate in this module is fail-closed."""
    return INVALID_VERDICT if invalid_reasons else None


def build_input_manifest(
    *,
    source: SourceInputs,
    entries: list[dict[str, Any]],
    anchors: list[Anchor],
    audited_anchors: list[Anchor],
    config_module_name: str,
    audited_scope: dict[str, Any],
) -> dict[str, Any]:
    """A-VC-3 / A-VC-10: the immutable anchor-input manifest.

    `deduplicated_anchor_count` and friends describe THIS run's audited
    population, not the source's -- a bounded smoke therefore declares its
    own smaller numbers and the analyzer's frozen-population check fires
    precedence-1 invalidity on it, which is the intended behaviour: a smoke
    artifact must never be readable as the formal record. The source's own
    (always-full) shape is recorded separately under `source_population`.
    """
    seeds_block: dict[str, Any] = {}
    manifest_seeds = source.vk0b_manifest.get("seeds") or {}
    for entry in entries:
        seed_key = str(int(entry["training_seed"]))
        source_seed = manifest_seeds.get(seed_key) or {}
        seeds_block[seed_key] = {
            "checkpoint_hash": str(entry["checkpoint_sha256"]),
            "checkpoint_path": str(entry["checkpoint_path"]),
            "resolved_config_hash": str(entry["resolved_config_hash"]),
            "config_module": str(entry["config_module"]),
            "preflight_manifest_path": str(entry["preflight_manifest_path"]),
            "low_optimizer_steps": int(entry["low_optimizer_steps"]),
            "exposure_authorization": entry["actual_exposure"],
            "source_run_manifest_sha256": str(entry["source_run_manifest_sha256"]),
            "vk0b_recorded_source_run_manifest_sha256": source_seed.get("source_run_manifest_sha256"),
        }

    audited_seeds = sorted({a.training_seed for a in audited_anchors})
    episodes_per_seed = sorted(
        {len({a.evaluation_index for a in audited_anchors if a.training_seed == s}) for s in audited_seeds}
    )
    audited_checks = sorted({a.check_index for a in audited_anchors})

    return {
        "contract_id": CONTRACT_ID,
        "vk0c_schema_version": VK0C_SCHEMA_VERSION,
        "vk0b_trace_schema_version": VK0B_TRACE_SCHEMA_VERSION,
        "vk0b_source_bindings": source.source_bindings,
        "vk0b_source_paths": {
            "renewal_check_trace": str(source.trace_path),
            "renewal_counterfactual_units": str(source.units_path),
            "train_and_checkpoint_manifest": str(source.vk0b_manifest_path),
            "summary": str(source.summary_path),
            "vk0a_panel": str(source.panel_path),
            "vk0a_sidecar": str(source.sidecar_path),
        },
        "vk0a_authorization": source.vk0a_authorization,
        "source_population": {
            "check_row_count": len(source.trace_rows),
            "deduplicated_anchor_count": len(anchors),
            "episodes_per_seed": FROZEN_EPISODES_PER_SEED,
            "noninitial_checks": FROZEN_NONINITIAL_CHECKS,
            "seed_count": len({a.training_seed for a in anchors}),
        },
        "check_row_count": len(audited_anchors) * N_AGENTS,
        "deduplicated_anchor_count": len(audited_anchors),
        "episodes_per_seed": episodes_per_seed[0] if len(episodes_per_seed) == 1 else episodes_per_seed,
        "noninitial_checks": len(audited_checks),
        "seeds": seeds_block,
        "audited_scope": audited_scope,
        "code_identity": {
            "driver_git_blob_sha1": git_blob_sha1(Path(__file__)),
            "vk0b_driver_git_blob_sha1": git_blob_sha1(Path(vk0b.__file__)),
            "vk0a_oracle_git_blob_sha1": git_blob_sha1(Path(vk0a_oracle.__file__)),
            "policy_module_git_blob_sha1": git_blob_sha1(
                PROJECT_ROOT / "ha_ctse_process" / "r30_fixed_clock.py"
            ),
            "config_module": str(config_module_name),
        },
        "runtime": {
            "torch_version": str(torch.__version__),
            "torch_num_threads": int(torch.get_num_threads()),
            "device": "cpu",
        },
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def run_full_audit(
    *,
    checkpoint_paths: list[str],
    eval_dir: Path,
    oracle_panel_path: Path,
    panel_digest_path: Path,
    out_dir: Path,
    config_module_name: str = "config_d7_2b_toy_learned_keep",
    limit_seeds: int | None = None,
    limit_episodes: int | None = None,
    limit_checks: int | None = None,
    run_gate_b: bool = True,
    gate_b_case_limit: int | None = None,
) -> dict[str, Any]:
    source = load_source_inputs(Path(eval_dir), Path(oracle_panel_path), Path(panel_digest_path))
    anchors = build_anchor_inventory(source.trace_rows)
    assert_anchor_population(anchors)

    entries = [vk0b.resolve_checkpoint_entry(p) for p in checkpoint_paths]
    manifest_seeds = source.vk0b_manifest.get("seeds") or {}
    for entry in entries:
        seed_key = str(int(entry["training_seed"]))
        recorded = manifest_seeds.get(seed_key)
        if recorded is None:
            raise Vk0cRefusalError(
                REASON_CHECKPOINT_AUTHORIZATION_FAILED,
                f"seed {seed_key} is not one of the V-K0B evaluation's own seeds",
            )
        if str(recorded.get("checkpoint_hash")) != str(entry["checkpoint_sha256"]):
            raise Vk0cRefusalError(
                REASON_CHECKPOINT_AUTHORIZATION_FAILED,
                f"seed {seed_key}: checkpoint SHA-256 recomputed from the bundle "
                f"({entry['checkpoint_sha256']}) != the V-K0B evaluation manifest's "
                f"({recorded.get('checkpoint_hash')})",
            )
        if str(recorded.get("source_run_manifest_sha256")) != str(entry["source_run_manifest_sha256"]):
            raise Vk0cRefusalError(
                REASON_CHECKPOINT_AUTHORIZATION_FAILED,
                f"seed {seed_key}: source run-manifest SHA-256 recomputed from the bundle does not "
                "match the V-K0B evaluation manifest's",
            )
        exposure = entry["actual_exposure"]
        if not isinstance(exposure, dict) or exposure.get("actual_exposure_schema") != vk0b.ACTUAL_EXPOSURE_SCHEMA:
            raise Vk0cRefusalError(
                REASON_CHECKPOINT_AUTHORIZATION_FAILED,
                f"seed {seed_key}: missing a {vk0b.ACTUAL_EXPOSURE_SCHEMA!r} exposure block",
            )

    selected_seeds = sorted({int(e["training_seed"]) for e in entries})
    if limit_seeds is not None:
        selected_seeds = selected_seeds[: int(limit_seeds)]
        entries = [e for e in entries if int(e["training_seed"]) in set(selected_seeds)]

    audited = [a for a in anchors if a.training_seed in set(selected_seeds)]
    if limit_episodes is not None:
        keep_episodes = sorted({a.evaluation_index for a in audited})[: int(limit_episodes)]
        audited = [a for a in audited if a.evaluation_index in set(keep_episodes)]
    if limit_checks is not None:
        keep_checks = sorted({a.check_index for a in audited})[: int(limit_checks)]
        audited = [a for a in audited if a.check_index in set(keep_checks)]

    bounded = bool(
        limit_seeds is not None
        or limit_episodes is not None
        or limit_checks is not None
        or gate_b_case_limit is not None
        or not run_gate_b
    )
    if not bounded and len(entries) != FROZEN_SEED_COUNT:
        raise Vk0cRefusalError(
            REASON_CHECKPOINT_AUTHORIZATION_FAILED,
            f"an unbounded V-K0C run needs exactly {FROZEN_SEED_COUNT} checkpoint bundles, got {len(entries)}",
        )
    audited_scope = {
        "bounded_smoke": bounded,
        "seeds": selected_seeds,
        "episodes": sorted({a.evaluation_index for a in audited}),
        "check_indices": sorted({a.check_index for a in audited}),
        "anchor_count": len(audited),
        "gate_b_executed": bool(run_gate_b),
        "gate_b_case_limit": gate_b_case_limit,
    }

    config_module = importlib.import_module(config_module_name)
    kernel = WindowKernel(config_module.Config())
    accumulator = RunAccumulator()

    # ---- Gate B (A-VC-4), once per audit ----------------------------------
    # Forced tokens make the transition policy-independent, so running it per
    # checkpoint bundle would repeat the identical comparison six times.
    if run_gate_b:
        gate_b_agent = vk0b.build_agent(config_module.Config(), checkpoint_path=None)
        cases = canonical_transition_cases()
        if gate_b_case_limit is not None:
            cases = _take(cases, int(gate_b_case_limit))
        gate_b = gate_b_transition_parity(
            agent=gate_b_agent, config=config_module.Config(), kernel=kernel, cases=cases
        )
        accumulator.diagnostics["gate_b"] = gate_b
        if gate_b["mismatch_count"]:
            accumulator.flag(
                REASON_GATE_B_TRANSITION_PARITY_FAILED,
                f"{gate_b['mismatch_count']} of {gate_b['cases_checked']} canonical transition "
                f"cases disagree; first={gate_b['mismatches'][0]}",
            )
        del gate_b_agent

    for entry in entries:
        evaluate_checkpoint_bundle(
            entry=entry,
            config_module_name=config_module_name,
            anchors=audited,
            accumulator=accumulator,
            kernel=kernel,
        )

    manifest = build_input_manifest(
        source=source,
        entries=entries,
        anchors=anchors,
        audited_anchors=audited,
        config_module_name=config_module_name,
        audited_scope=audited_scope,
    )
    manifest["run_verdict"] = run_verdict_for(accumulator.invalid_reasons)
    manifest["invalid_reasons"] = list(accumulator.invalid_reasons)
    manifest["diagnostics"] = {
        **accumulator.diagnostics,
        "window_kernel_evaluations": int(kernel.evaluations),
        "window_kernel_cache_hits": int(kernel.cache_hits),
        "reachable_state_bound": int(reachable_state_bound()),
        "row_counts": {
            "matched_state_rows": len(accumulator.matched_state_rows),
            "propagation_rows": len(accumulator.propagation_rows),
            "control_rows": len(accumulator.control_rows),
            "four_sign_panel_entries": len(accumulator.four_sign_panel),
        },
    }

    out_dir = Path(out_dir)
    write_jsonl(out_dir / VK0C_MATCHED_STATE_FILENAME, accumulator.matched_state_rows)
    write_jsonl(out_dir / VK0C_PROPAGATION_FILENAME, accumulator.propagation_rows)
    write_jsonl(out_dir / VK0C_CONTROL_FILENAME, accumulator.control_rows)
    write_json(
        out_dir / VK0C_FOUR_SIGN_PANEL_FILENAME,
        {
            "contract_id": CONTRACT_ID,
            "vk0c_schema_version": VK0C_SCHEMA_VERSION,
            "panel_kind": "FOUR_SIGN_DESCRIPTIVE_PANEL",
            "non_inferential": True,
            "never_pooled_with_episode_bank": True,
            "entries": accumulator.four_sign_panel,
        },
    )
    write_json(out_dir / VK0C_MANIFEST_FILENAME, manifest)
    return manifest


def write_refusal(out_dir: Path, error: Vk0cRefusalError) -> None:
    write_json(
        Path(out_dir) / VK0C_MANIFEST_FILENAME,
        {
            "contract_id": CONTRACT_ID,
            "vk0c_schema_version": VK0C_SCHEMA_VERSION,
            "refused": True,
            "refusal_reason_code": error.reason_code,
            "refusal_detail": error.detail,
            "run_verdict": INVALID_VERDICT,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="V-K0C order-transport localization driver.")
    parser.add_argument("--checkpoints", nargs="+", required=True)
    parser.add_argument("--vk0b-eval-dir", dest="eval_dir", required=True)
    parser.add_argument("--oracle-panel", dest="oracle_panel", required=True)
    parser.add_argument("--panel-digest", dest="panel_digest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default="config_d7_2b_toy_learned_keep")
    parser.add_argument("--limit-seeds", type=int, default=None)
    parser.add_argument("--limit-episodes", type=int, default=None)
    parser.add_argument("--limit-checks", type=int, default=None)
    parser.add_argument("--gate-b-case-limit", type=int, default=None)
    parser.add_argument("--skip-gate-b", action="store_true")
    args = parser.parse_args()

    torch.set_num_threads(1)
    out_dir = Path(args.out)
    try:
        manifest = run_full_audit(
            checkpoint_paths=list(args.checkpoints),
            eval_dir=Path(args.eval_dir),
            oracle_panel_path=Path(args.oracle_panel),
            panel_digest_path=Path(args.panel_digest),
            out_dir=out_dir,
            config_module_name=str(args.config),
            limit_seeds=args.limit_seeds,
            limit_episodes=args.limit_episodes,
            limit_checks=args.limit_checks,
            run_gate_b=not args.skip_gate_b,
            gate_b_case_limit=args.gate_b_case_limit,
        )
    except Vk0cRefusalError as exc:
        write_refusal(out_dir, exc)
        print(f"VK0C_REFUSED={exc}")
        raise SystemExit(1) from exc

    print(f"VK0C_RUN_VERDICT={manifest['run_verdict']}")
    print(f"VK0C_INVALID_REASONS={len(manifest['invalid_reasons'])}")
    print(f"VK0C_ROW_COUNTS={manifest['diagnostics']['row_counts']}")
    print(f"VK0C_OUT={out_dir}")


if __name__ == "__main__":
    main()
