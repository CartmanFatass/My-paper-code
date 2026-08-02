"""V-K0B unrestricted-R30 natural-access screen -- evaluation-only driver.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D3,
VK-D5, VK-D6, VK-D7, VK-D8, VK-D10 and every A-VK-D amendment), the ruling
`docs/external-review/rounds/20260801_variable_k_algorithm_direction/
21_PRO_OPEN_RAW.md` (MEASUREMENT sections 2, 4, 5, 6; EVIDENCE_DESIGN Stage
V-K0B), the conformance round
`docs/external-review/rounds/20260801_vk0_design_conformance/21_PRO_OPEN_RAW.md`
(VK-D3, VK-D5, VK-D6, VK-D8, VK-D10) and `22_PRO_CONVERGENCE.md` (both
realization clarifications).

No training, no policy update. This drives the existing evaluation-only
forced-token surface (`StandaloneProcessAgent.maybe_assign_skills(...,
forced_tokens=..., agent_order=...)`) against a frozen checkpoint, exactly
like the D7.2B precedent (`scripts/audit_d7_2b_toy_positive_control.py`'s
`ToyAuditHost`), extended with: the reversed-roster hook (VK-D5), the
exhaustive V-K0A oracle invoked on each check's ACTUAL incumbent pair rather
than a phase/axis label (A-VK-D10), a complete pre-decision boundary
fingerprint with fail-closed replay (A-VK-D3/A-VK-D4), and the durable row
schema `scripts/analyze_vk0_result.py` already freezes (A-VK-D6) -- every
constant that must match that module's own frozen constants is written here
as a literal duplicate (there is no shared module to import from without
widening this task's file scope) and cross-checked in
`tests/audit_vk0b_driver_test.py`.

The frozen schema this module writes is authoritative in
`scripts/analyze_vk0_result.py` (developed against synthetic fixtures because
this driver did not exist yet); this module is the first thing to write real
rows against it. Nothing here computes a statistic, a bound, or a result
branch -- that is the analyzer's job, run separately against the row files
this module produces.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
for _p in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.r30_fixed_clock import INVALID_SKILL, KEEP_TOKEN, SET_TOKEN
from ha_ctse_process.standalone_agent import StandaloneProcessAgent

import audit_vk0a_source_urgency_oracle as vk0a_oracle

# =============================================================================
# Frozen identity -- MUST match scripts/analyze_vk0_result.py's own constants
# of the same name exactly; there is no shared module, so this is a literal
# duplicate rather than an import, per this task's file scope.
# =============================================================================

CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
TRACE_SCHEMA_VERSION = "vk0-trace-2"

AGENT_ORDER_CANONICAL = "canonical"
AGENT_ORDER_REVERSED = "reversed"

NATURAL_TOKEN_KEEP = "KEEP"
NATURAL_TOKEN_SET = "SET"

ESTIMAND_KEEP_REFERENCE = "KEEP_REFERENCE"
ESTIMAND_OPP_NAMED_SET = "OPP_NAMED_SET"
ESTIMAND_SET_SAMPLED = "SET_SAMPLED"
ESTIMAND_NATURAL = "NATURAL"

PHASE_SELECT = "select"
PHASE_EVALUATE = "evaluate"

SEGMENT_ORIGINS = {"initial_assignment", "voluntary_set"}

# A-W6-4 (conformance round `20260801_vk0b_rerun_exposure_conformance`,
# `21_PRO_OPEN_RAW.md` section 5): the single `segment_ending_authority`
# scalar could not represent a final-check voluntary SET (which ends the
# incumbent segment) whose newly-started segment is itself ended five
# primitive steps later by episode termination -- one field can carry only
# one of those two events. Replaced by two independent fields:
#
# `incumbent_end_authority_at_check` -- did a voluntary SET end the segment
# that was incumbent going INTO this check? "voluntary_set" if this row's
# natural token is SET, else "none_open". `active_mask_change`,
# `team_intent_boundary` and `forced_renewal` never apply here (no
# active-mask flips, `enable_team_intent=False`,
# `r30_force_refresh_every_check=False`) so they are not legal values of
# THIS field at all -- they belong only to `post_window_end_authority`.
#
# `post_window_end_authority` -- what ends the newly-current segment within
# the WINDOW primitive steps that follow this check? On this frozen 8-check
# clock only the final noninitial check's window runs into episode
# truncation, so this is "episode_termination" at `check_index ==
# NONINITIAL_CHECKS` and "none_open" everywhere else; `active_mask_change`,
# `team_intent_boundary` and `forced_renewal` are legal schema values,
# structurally unreachable under this config.
#
# `segment_origin` keeps the ORIGIN provenance the old field conflated in
# ("initial_assignment" until the first voluntary SET for that agent,
# "voluntary_set" afterward) -- never itself an ending authority.
#
# None of the three fields is consumed by a registered statistic in
# `scripts/analyze_vk0_result.py` (checked: membership-validated there only).
INCUMBENT_END_AUTHORITIES = {"voluntary_set", "none_open"}
POST_WINDOW_END_AUTHORITIES = {
    "episode_termination",
    "active_mask_change",
    "team_intent_boundary",
    "forced_renewal",
    "none_open",
}

# A-W6-5: the frozen schema tag the training-side `actual_exposure` block
# must carry (literal duplicate of `scripts/run_vk0b_training.py`'s own
# `ACTUAL_EXPOSURE_SCHEMA` -- no shared module, per this task's file scope).
# This driver treats the block's contents as opaque beyond checking this tag
# and presence; `scripts/analyze_vk0_result.py` owns full semantic
# validation of its mandatory keys.
ACTUAL_EXPOSURE_SCHEMA = "vk0b-exposure-1"

# K0/WINDOW/N_SKILLS/NONINITIAL_CHECKS/TOTAL_CHECKS are re-used from the V-K0A
# module rather than redefined, since they must be identical by construction
# (the same fixed clock, the same toy).
K0 = vk0a_oracle.K0
WINDOW = vk0a_oracle.WINDOW
N_SKILLS = vk0a_oracle.N_SKILLS
NONINITIAL_CHECKS = vk0a_oracle.NONINITIAL_CHECKS
TOTAL_CHECKS = vk0a_oracle.TOTAL_CHECKS

EVAL_EPISODES = 64
N_SELECT = 2
N_EVAL = 2
SHARED_CANDIDATE_TOKEN = "shared"

INVALID_VERDICT = "INVALID_VARIABLE_K_URGENCY_AUDIT"

VK0B_TRACE_FILENAME = "renewal_check_trace.jsonl"
VK0B_UNITS_FILENAME = "renewal_counterfactual_units.jsonl"
VK0B_MANIFEST_FILENAME = "train_and_checkpoint_manifest.json"


class Vk0bRefusalError(Exception):
    """Precedence-1 refusal: named, before any checkpoint is loaded."""


# =============================================================================
# Hash / seed helpers
# =============================================================================


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))


def derive_seed(*fields: Any, contract_id: str = CONTRACT_ID) -> int:
    payload = "|".join(str(f) for f in (contract_id, *fields))
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _legacy_numpy_seed(x: int) -> int:
    """`np.random.seed` (the legacy global RNG, used only because the
    precedent script seeds it defensively alongside torch) accepts only
    0..2**32-1, unlike `torch.manual_seed` and `np.random.default_rng`
    (both accept the full 64-bit `derive_seed` range directly, checked
    empirically). Masking happens ONLY at this one call site -- the
    `derived_seed` row field and every other seed use keep the true,
    unmasked SHA-256-derived value VK-D7 requires, mirroring the
    `stream_seed` precedent's `% (2**32 - 1)` masking
    (`scripts/audit_d7_s_event_aligned.py`)."""
    return int(x) % (2**32 - 1)


def episode_seed(evaluation_index: int) -> int:
    """VK-D7: one frozen common evaluation-seed bank, shared across every
    training seed -- so this must NOT depend on `training_seed`."""
    return derive_seed("episode", evaluation_index)


def policy_stream_seed(training_seed: int, evaluation_index: int, agent_order_code: str) -> int:
    return derive_seed("policy_stream", training_seed, evaluation_index, agent_order_code)


def branch_continuation_seed(
    *,
    training_seed: int,
    evaluation_index: int,
    agent_order_code: str,
    check_index: int,
    focal_agent: int,
    candidate_target_id: str,
    phase: str,
    replicate_index: int,
) -> int:
    """VK-D7 counterfactual stream, mirroring `stream_seed`
    (`scripts/audit_d7_s_event_aligned.py`): `candidate_target_id` is the
    disjointness lever. At `phase="select"` it is the candidate's own skill
    id, so every named candidate gets an independent selection stream. At
    `phase="evaluate"` every family (KEEP_REFERENCE, every OPP_NAMED_SET
    candidate, SET_SAMPLED, NATURAL) passes the fixed `SHARED_CANDIDATE_TOKEN`
    sentinel, so they all land on the identical continuation seed per
    replicate index -- the common-random-numbers pairing ruling section 5
    requires ("Use the same base random draws"). `estimand_family` is
    deliberately NOT hashed: it is exactly the lever that must NOT
    distinguish the seed at evaluate phase, or the CRN pairing breaks."""
    return derive_seed(
        "counterfactual",
        training_seed,
        evaluation_index,
        agent_order_code,
        check_index,
        focal_agent,
        candidate_target_id,
        phase,
        replicate_index,
    )


def agent_order_for_evaluation_index(i: int) -> tuple[np.ndarray, str]:
    """64-episode bank split 32/32 canonical/reversed (ruling "Held-out
    evaluation": "32 canonical + 32 reversed"). Interleaved by parity so the
    split is a fixed, documented, index-independent-of-seed convention, not a
    magic contiguous half."""
    if i % 2 == 0:
        return np.array([0, 1], dtype=np.int64), AGENT_ORDER_CANONICAL
    return np.array([1, 0], dtype=np.int64), AGENT_ORDER_REVERSED


def legal_set_candidates(incumbent_skill: int) -> list[int]:
    return [z for z in range(N_SKILLS) if z != int(incumbent_skill)]


def check_unit_id(training_seed: int, evaluation_index: int, agent_order_code: str, check_index: int, focal_agent: int) -> str:
    return f"vk0b:{training_seed}:{evaluation_index}:{agent_order_code}:{check_index}:{focal_agent}"


def branch_unit_id(parent_id: str, family: str, candidate: int | None, phase: str, replicate_index: int) -> str:
    candidate_token = "none" if candidate is None else str(int(candidate))
    return f"{parent_id}:{family}:{candidate_token}:{phase}:{replicate_index}"


# =============================================================================
# Boundary fingerprint (A-VK-D3 + convergence clarification 2): the module
# enumerates the concrete field set explicitly so the internal gate below can
# verify coverage, rather than leaving "plus any other mutable field" implicit.
# =============================================================================

FINGERPRINT_FIELDS: tuple[str, ...] = (
    "env_steps",
    "env_initial_signs",
    "env_np_random_state",
    "observation_bytes",
    "centralized_state_bytes",
    "active_skills",
    "skill_ages",
    "active_mask",
    "steps_to_check",
    "episode_steps",
    "agent_order",
    "low_actor_hidden",
    "low_critic_hidden",
    "numpy_global_rng_state",
    "torch_cpu_rng_state",
    "torch_cuda_rng_state",
    "checkpoint_sha256",
    "resolved_config_hash",
    "contract_id",
    "trace_schema_version",
)


def build_fingerprint(
    *,
    raw_env,
    agent: StandaloneProcessAgent,
    env_id: int,
    obs: np.ndarray,
    state: np.ndarray,
    agent_order: np.ndarray,
    checkpoint_sha256: str,
    resolved_config_hash: str,
) -> dict[str, Any]:
    numpy_legacy = np.random.get_state()
    numpy_legacy_repr = json.dumps(
        [
            numpy_legacy[0],
            np.asarray(numpy_legacy[1]).tolist(),
            int(numpy_legacy[2]),
            int(numpy_legacy[3]),
            float(numpy_legacy[4]),
        ]
    )
    fp = {
        "env_steps": int(raw_env.steps),
        "env_initial_signs": [float(raw_env._initial_slow_sign), float(raw_env._initial_fast_sign)],
        "env_np_random_state": hash_text(
            json.dumps(raw_env.np_random.bit_generator.state, sort_keys=True, default=str)
        ),
        "observation_bytes": hash_bytes(np.asarray(obs, dtype=np.float32).tobytes()),
        "centralized_state_bytes": hash_bytes(np.asarray(state, dtype=np.float32).tobytes()),
        "active_skills": [int(x) for x in agent.active_skills[env_id]],
        "skill_ages": [int(x) for x in agent.skill_age[env_id]],
        "active_mask": [bool(x) for x in agent.has_active_skill[env_id]],
        "steps_to_check": int(agent.steps_to_check[env_id]),
        "episode_steps": int(agent.episode_steps[env_id]),
        "agent_order": [int(x) for x in agent_order],
        "low_actor_hidden": hash_bytes(np.asarray(agent.low_actor_hxs[env_id], dtype=np.float32).tobytes()),
        "low_critic_hidden": hash_bytes(np.asarray(agent.low_critic_hxs[env_id], dtype=np.float32).tobytes()),
        "numpy_global_rng_state": hash_text(numpy_legacy_repr),
        "torch_cpu_rng_state": hash_bytes(torch.get_rng_state().numpy().tobytes()),
        "torch_cuda_rng_state": "cpu_only" if not torch.cuda.is_available() else hash_bytes(
            torch.cuda.get_rng_state().numpy().tobytes()
        ),
        "checkpoint_sha256": str(checkpoint_sha256),
        "resolved_config_hash": str(resolved_config_hash),
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
    }
    if set(fp.keys()) != set(FINGERPRINT_FIELDS):
        raise AssertionError(
            f"fingerprint coverage drifted from FINGERPRINT_FIELDS: "
            f"missing={set(FINGERPRINT_FIELDS) - set(fp.keys())} "
            f"extra={set(fp.keys()) - set(FINGERPRINT_FIELDS)}"
        )
    return fp


def fingerprint_digest(fp: dict[str, Any]) -> str:
    return hash_text(json.dumps(fp, sort_keys=True, separators=(",", ":")))


# =============================================================================
# W6-D4 target vectors (A-W6-4/conforms): the env's OWN `_targets()` read at
# the check's pre-decision moment -- the same private accessor pattern
# `build_fingerprint` already uses for `_initial_slow_sign`/`_initial_fast_sign`.
# =============================================================================


def target_vectors(raw_env) -> dict[str, list[float]]:
    slow, fast = raw_env._targets()
    return {"slow": [float(x) for x in slow], "fast": [float(x) for x in fast]}


def validate_segment_fields(row: dict[str, Any]) -> None:
    """W6-D4/A-W6-4 internal row-vocabulary guard, mirroring
    `build_fingerprint`'s own coverage assertion: fail fast and named rather
    than let an illegal value reach a written row."""
    if row["segment_origin"] not in SEGMENT_ORIGINS:
        raise AssertionError(
            f"segment_origin must be one of {SEGMENT_ORIGINS}, got {row['segment_origin']!r}"
        )
    if row["incumbent_end_authority_at_check"] not in INCUMBENT_END_AUTHORITIES:
        raise AssertionError(
            "incumbent_end_authority_at_check must be one of "
            f"{INCUMBENT_END_AUTHORITIES}, got {row['incumbent_end_authority_at_check']!r}"
        )
    if row["post_window_end_authority"] not in POST_WINDOW_END_AUTHORITIES:
        raise AssertionError(
            "post_window_end_authority must be one of "
            f"{POST_WINDOW_END_AUTHORITIES}, got {row['post_window_end_authority']!r}"
        )


# =============================================================================
# (a) AUTHORIZATION -- A-VK-D10 + convergence clarification 1
# =============================================================================


def load_and_authorize_panel(panel_path: Path, digest_path: Path) -> dict[str, Any]:
    if not panel_path.is_file():
        raise Vk0bRefusalError(f"PANEL_FILE_MISSING: {panel_path}")
    if not digest_path.is_file():
        raise Vk0bRefusalError(f"PANEL_DIGEST_FILE_MISSING: {digest_path}")
    panel_bytes = panel_path.read_bytes()
    recomputed = hash_bytes(panel_bytes)
    expected = digest_path.read_text(encoding="utf-8").strip()
    if recomputed != expected:
        raise Vk0bRefusalError(
            f"PANEL_DIGEST_MISMATCH: recomputed sha256 {recomputed} != sidecar {expected} ({digest_path})"
        )
    panel = json.loads(panel_bytes.decode("utf-8"))
    if panel.get("contract_id") != CONTRACT_ID:
        raise Vk0bRefusalError(f"PANEL_CONTRACT_ID_MISMATCH: {panel.get('contract_id')!r}")
    if panel.get("verdict") != vk0a_oracle.VALID_VERDICT:
        raise Vk0bRefusalError(f"PANEL_VERDICT_NOT_IDENTIFIED: {panel.get('verdict')!r}")
    if panel.get("panel_schema_version") != vk0a_oracle.PANEL_SCHEMA_VERSION:
        raise Vk0bRefusalError(f"PANEL_SCHEMA_VERSION_MISMATCH: {panel.get('panel_schema_version')!r}")
    row_count = panel.get("row_count")
    if int(row_count or -1) != 112 or len(panel.get("rows") or []) != 112:
        raise Vk0bRefusalError(f"PANEL_ROW_COUNT_MISMATCH: row_count={row_count!r}")
    validity = panel.get("validity") or {}
    if not bool(validity.get("all_passed")):
        raise Vk0bRefusalError("PANEL_VALIDITY_NOT_ALL_PASSED")
    for name in vk0a_oracle.ValidityTracker.NAMES:
        if validity.get(name) is not True:
            raise Vk0bRefusalError(f"PANEL_VALIDITY_PREDICATE_FALSE: {name}")

    validity_predicates = {name: bool(validity[name]) for name in vk0a_oracle.ValidityTracker.NAMES}
    # The authorization tuple's OWN "artifact_sha256" is not the raw panel
    # file's byte hash (that one is `recomputed`, already verified against
    # the sidecar above per convergence clarification 1 -- "non-self-
    # referential": the panel file is not required to contain the hash of its
    # own bytes). It is the SHA-256 of the canonical-JSON nine-field tuple
    # itself (contract_id, stage_commit, environment_blob_sha,
    # action_table_hash, oracle_script_hash, panel_schema_version, row_count,
    # validity_predicates, verdict) -- exactly the formula
    # `scripts/analyze_vk0_result.py`'s private `_panel_expected_sha256` /
    # `_panel_tuple_payload` recomputes and compares this field against, so
    # it must be reproduced byte-for-byte (`sort_keys=True,
    # separators=(",", ":")`) rather than substituted with the file hash.
    tuple_payload = {
        "contract_id": panel["contract_id"],
        "stage_commit": panel["stage_commit"],
        "environment_blob_sha": panel["environment_blob_sha"],
        "action_table_hash": panel["action_table_hash"],
        "oracle_script_hash": panel["oracle_script_hash"],
        "panel_schema_version": panel["panel_schema_version"],
        "row_count": int(panel["row_count"]),
        "validity_predicates": validity_predicates,
        "verdict": panel["verdict"],
    }
    artifact_sha256 = hash_text(json.dumps(tuple_payload, sort_keys=True, separators=(",", ":")))
    authorization = {**tuple_payload, "artifact_sha256": artifact_sha256}
    return {"panel": panel, "authorization": authorization, "panel_file_digest": recomputed}


# =============================================================================
# Checkpoint manifest resolution (launcher output -> evaluation input)
# =============================================================================


def resolve_actual_exposure(training: dict[str, Any], manifest_path: Path) -> tuple[dict[str, Any], str]:
    """A-W6-5 chain, driver leg: read the training `run_manifest.json` named
    by the launcher manifest's `training.run_manifest_path`, verify its bytes
    against `training.run_manifest_sha256` (the launcher's own recorded
    hash -- same fail-closed shape as the checkpoint hash check just above),
    and return `(actual_exposure_block, source_run_manifest_sha256)` where
    the hash is THIS function's own recomputation over the bytes it read,
    never the launcher-supplied value substituted in its place. The block's
    contents are opaque beyond the schema tag and presence check --
    `scripts/analyze_vk0_result.py` owns full semantic validation (A-W6-5,
    "independently validates the complete block before row 2")."""
    run_manifest_path = training.get("run_manifest_path")
    expected_run_manifest_sha256 = training.get("run_manifest_sha256")
    if not run_manifest_path or not expected_run_manifest_sha256:
        raise Vk0bRefusalError(
            f"RUN_MANIFEST_REFERENCE_INCOMPLETE: {manifest_path} training block missing "
            "run_manifest_path/run_manifest_sha256"
        )
    run_manifest_file = Path(run_manifest_path)
    if not run_manifest_file.is_file():
        raise Vk0bRefusalError(f"RUN_MANIFEST_FILE_MISSING: {run_manifest_path}")
    try:
        run_manifest_bytes = run_manifest_file.read_bytes()
        run_manifest = json.loads(run_manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Vk0bRefusalError(f"RUN_MANIFEST_UNREADABLE: {run_manifest_path}: {exc}") from exc
    source_run_manifest_sha256 = hash_bytes(run_manifest_bytes)
    if source_run_manifest_sha256 != expected_run_manifest_sha256:
        raise Vk0bRefusalError(
            f"RUN_MANIFEST_HASH_MISMATCH: {run_manifest_path} recomputed "
            f"{source_run_manifest_sha256} != launcher manifest {expected_run_manifest_sha256}"
        )
    actual_exposure = run_manifest.get("actual_exposure")
    if not isinstance(actual_exposure, dict) or actual_exposure.get("actual_exposure_schema") != ACTUAL_EXPOSURE_SCHEMA:
        raise Vk0bRefusalError(
            f"ACTUAL_EXPOSURE_BLOCK_MISSING_OR_WRONG_SCHEMA: {run_manifest_path} has no "
            f"actual_exposure block tagged {ACTUAL_EXPOSURE_SCHEMA!r}"
        )
    return actual_exposure, source_run_manifest_sha256


def resolve_checkpoint_entry(path_or_dir: str) -> dict[str, Any]:
    p = Path(path_or_dir)
    manifest_path = p if p.is_file() else p / "vk0b_preflight_manifest.json"
    if not manifest_path.is_file():
        raise Vk0bRefusalError(f"CHECKPOINT_MANIFEST_NOT_FOUND: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if bool(manifest.get("nonscientific")):
        raise Vk0bRefusalError(f"CHECKPOINT_NONSCIENTIFIC: {manifest_path} is a nonscientific microbenchmark run")
    resolved = manifest.get("resolved") or {}
    training = manifest.get("training") or {}
    checkpoint_path = training.get("final_checkpoint_path")
    checkpoint_sha256 = training.get("checkpoint_sha256")
    if not checkpoint_path or not checkpoint_sha256:
        raise Vk0bRefusalError(
            f"CHECKPOINT_MANIFEST_INCOMPLETE: {manifest_path} missing "
            "final_checkpoint_path/checkpoint_sha256"
        )
    if not Path(checkpoint_path).is_file():
        raise Vk0bRefusalError(f"CHECKPOINT_FILE_MISSING: {checkpoint_path}")
    actual_sha = hash_bytes(Path(checkpoint_path).read_bytes())
    if actual_sha != checkpoint_sha256:
        raise Vk0bRefusalError(
            f"CHECKPOINT_HASH_MISMATCH: {checkpoint_path} recomputed {actual_sha} "
            f"!= manifest {checkpoint_sha256}"
        )
    training_seed = resolved.get("training_seed")
    if training_seed is None:
        raise Vk0bRefusalError(f"CHECKPOINT_MANIFEST_INCOMPLETE: {manifest_path} missing resolved.training_seed")
    low_absence = resolved.get("low_optimizer_absence") or {}
    if low_absence.get("use_recurrent_low_level") is False and low_absence.get(
        "r39_toy_fixed_skill_primitives"
    ) is True:
        low_optimizer_steps = 0
    else:
        raise Vk0bRefusalError(
            f"LOW_OPTIMIZER_EXPOSURE_UNKNOWN: {manifest_path} cannot establish zero "
            "low-level optimizer exposure from its resolved config"
        )
    actual_exposure, source_run_manifest_sha256 = resolve_actual_exposure(training, manifest_path)
    return {
        "training_seed": int(training_seed),
        "checkpoint_path": checkpoint_path,
        "checkpoint_sha256": checkpoint_sha256,
        "resolved_config_hash": manifest.get("resolved_config_hash"),
        "config_module": resolved.get("config_module"),
        "preflight_manifest_path": str(manifest_path),
        "low_optimizer_steps": low_optimizer_steps,
        "actual_exposure": actual_exposure,
        "source_run_manifest_sha256": source_run_manifest_sha256,
    }


# =============================================================================
# Agent / env construction
# =============================================================================


def build_agent(config, *, checkpoint_path: str | None) -> StandaloneProcessAgent:
    """`checkpoint_path=None` builds a freshly-initialized (untrained, random)
    agent, for the proof-sized skeleton test only -- the CLI path below always
    supplies a real checkpoint. Mirrors
    `scripts/audit_d7_2b_toy_positive_control.py`'s construction exactly."""
    agent = StandaloneProcessAgent(
        obs_dim=int(config.obs_dim),
        action_dim=int(config.action_dim),
        n_agents=int(config.n_agents),
        config=config,
        device="cpu",
        action_space_type=str(config.action_space_type),
        num_envs=1,
    )
    if checkpoint_path is not None:
        process_train.load_checkpoint(checkpoint_path, agent, load_optimizers=False)
    for module in (agent.high, agent.high_value):
        if module is not None:
            module.eval()
    return agent


def make_env(config, seed: int):
    return process_train.create_env(config, config.scenario, seed, rank=0, scale_mode="eval")


# =============================================================================
# Episode driver
# =============================================================================


@dataclass
class CheckContext:
    check_index: int
    step: int
    obs: np.ndarray
    state: np.ndarray
    incumbent: tuple[int, int]
    skill_age: tuple[int, int]
    active_mask: tuple[bool, bool]
    reference_fingerprint: dict[str, Any]
    current_targets: dict[str, list[float]]
    previous_targets: dict[str, list[float]] | None


@dataclass
class NaturalCheckResult:
    context: CheckContext
    factual_token_kind: dict[int, str]
    factual_set_skill: dict[int, int | None]
    factual_keep_prob: dict[int, float]
    window_rewards: list[float]
    window_slow: list[int]
    window_fast: list[int]
    segment_origin: dict[int, str]


def _binary_match(value: Any) -> int:
    v = float(value)
    if abs(v) < 1e-6:
        return 0
    if abs(v - 1.0) < 1e-6:
        return 1
    raise AssertionError(
        f"slow/fast match score {v} is not structurally binary on this fixed-executor "
        "toy -- a genuinely fractional match would invalidate the schema's 0/1 "
        "vector assumption rather than silently round"
    )


def run_natural_episode(
    *,
    agent: StandaloneProcessAgent,
    config,
    training_seed: int,
    evaluation_index: int,
    checkpoint_sha256: str,
    resolved_config_hash: str,
    forced_tokens_by_check: dict[int, dict[int, tuple[int, int]]] | None = None,
) -> list[NaturalCheckResult]:
    """Drive one full episode, recording every noninitial check's reference
    fingerprint, factual tokens and five-step window (c) -- the natural pass
    every counterfactual branch for that episode/order must reproduce
    bit-for-bit up to its own focal check.

    `forced_tokens_by_check` is a test-only hook (never reachable from the
    CLI, which always leaves it `None`): the same `forced_tokens` mechanism
    `replay_branch` already uses for counterfactual branches, applied here to
    the NATURAL pass instead, keyed by `check_index`. It exists only to make
    the Pro-named final-check voluntary-SET witness (A-W6-4) reproducible on
    demand rather than dependent on an untrained policy's stochastic output."""
    agent_order, agent_order_code = agent_order_for_evaluation_index(evaluation_index)
    ep_seed = episode_seed(evaluation_index)
    pol_seed = policy_stream_seed(training_seed, evaluation_index, agent_order_code)

    wrapped_env = make_env(config, int(ep_seed))
    try:
        torch.manual_seed(int(pol_seed))
        np.random.seed(_legacy_numpy_seed(pol_seed))
        obs, info = wrapped_env.reset(seed=int(ep_seed))
        state = info.get("state")
        agent.reset_env_state(0)
        raw_env = wrapped_env.env

        results: list[NaturalCheckResult] = []
        segment_origin = {0: "initial_assignment", 1: "initial_assignment"}
        check_targets_by_index: dict[int, dict[str, list[float]]] = {}
        step = 0
        check_index = -1
        max_steps = int(config.max_steps)
        while True:
            due = bool(not np.all(agent.has_active_skill[0]) or int(agent.steps_to_check[0]) <= 0)
            if due:
                check_index += 1
                incumbent = (
                    int(agent.active_skills[0][0]) if agent.has_active_skill[0][0] else -1,
                    int(agent.active_skills[0][1]) if agent.has_active_skill[0][1] else -1,
                )
                # Captured NOW, at this check's own pre-decision moment --
                # `agent.skill_age`/`has_active_skill` are live arrays that
                # keep mutating for the rest of the episode, so a caller
                # reading them after `run_natural_episode` returns would see
                # the END-of-episode values for every check, not each one's
                # own.
                skill_age_here = (int(agent.skill_age[0][0]), int(agent.skill_age[0][1]))
                active_mask_here = (bool(agent.has_active_skill[0][0]), bool(agent.has_active_skill[0][1]))
                fp = build_fingerprint(
                    raw_env=raw_env, agent=agent, env_id=0, obs=obs, state=state,
                    agent_order=agent_order, checkpoint_sha256=checkpoint_sha256,
                    resolved_config_hash=resolved_config_hash,
                )
                # W6-D4: the env's own `_targets()` at this check's pre-decision
                # moment (same instant the fingerprint above is taken) and, if
                # one exists, the value captured at the immediately preceding
                # check -- the initial check (index 0) always has a value, so
                # `previous_targets` is only ever `None` for the initial check
                # itself (whose row is never emitted -- see the check_index==0
                # skip in `evaluate_checkpoint`).
                current_targets = target_vectors(raw_env)
                previous_targets = check_targets_by_index.get(check_index - 1)
                check_targets_by_index[check_index] = current_targets
                ctx = CheckContext(
                    check_index=check_index, step=step, obs=np.asarray(obs, dtype=np.float32).copy(),
                    state=np.asarray(state, dtype=np.float32).copy(), incumbent=incumbent,
                    skill_age=skill_age_here, active_mask=active_mask_here, reference_fingerprint=fp,
                    current_targets=current_targets, previous_targets=previous_targets,
                )
                forced = (
                    forced_tokens_by_check.get(check_index) if forced_tokens_by_check is not None else None
                )
                agent.maybe_assign_skills(
                    obs, state=state, step=step, k=K0, env_id=0, deterministic=False,
                    collect_r31=False, agent_order=agent_order, forced_tokens=forced,
                )
                pending = agent.high_check_buffer.pending[0]
                order_np = np.asarray(pending.agent_order, dtype=np.int64).reshape(-1)
                kinds_np = np.asarray(pending.token_kind, dtype=np.int64).reshape(-1)
                sets_np = np.asarray(pending.set_skill, dtype=np.int64).reshape(-1)
                keeps_np = np.asarray(pending.keep_prob, dtype=np.float32).reshape(-1)
                factual_kind: dict[int, str] = {}
                factual_set: dict[int, int | None] = {}
                factual_keep: dict[int, float] = {}
                for position, aid in enumerate(order_np):
                    aid = int(aid)
                    is_set = int(kinds_np[position]) == SET_TOKEN
                    factual_kind[aid] = NATURAL_TOKEN_SET if is_set else NATURAL_TOKEN_KEEP
                    factual_set[aid] = int(sets_np[position]) if is_set else None
                    factual_keep[aid] = float(keeps_np[position])
                    if is_set:
                        segment_origin[aid] = "voluntary_set"
                # Records, for each agent, whether the segment now active
                # (whether just (re)started here or continuing from an
                # earlier check) originated from the initial assignment or a
                # later voluntary SET -- see the note above `SEGMENT_ORIGINS`
                # for why those are the only two reachable values under this
                # frozen config.
                origin_snapshot = dict(segment_origin)

                window_rewards: list[float] = []
                window_slow: list[int] = []
                window_fast: list[int] = []
                for _ in range(WINDOW):
                    actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
                    obs, reward, terminated, truncated, info = wrapped_env.step(actions)
                    state = info.get("next_state", state)
                    metrics = info.get("reward_info") or {}
                    window_rewards.append(float(reward))
                    window_slow.append(_binary_match(metrics.get("r39_toy_slow_match", 0.0)))
                    window_fast.append(_binary_match(metrics.get("r39_toy_fast_match", 0.0)))
                    step += 1
                    done = bool(terminated or truncated) or step >= max_steps
                    agent.record_environment_step(
                        0, reward=float(reward), next_obs=obs, next_state=state, done=done, collect_r31=False,
                    )
                    if done:
                        break

                results.append(
                    NaturalCheckResult(
                        context=ctx, factual_token_kind=factual_kind, factual_set_skill=factual_set,
                        factual_keep_prob=factual_keep, window_rewards=window_rewards,
                        window_slow=window_slow, window_fast=window_fast, segment_origin=origin_snapshot,
                    )
                )
                if step >= max_steps:
                    break
            else:
                raise RuntimeError("natural pass reached a non-due step outside a check window")
        return results
    finally:
        wrapped_env.close()


@dataclass
class BranchOutcome:
    fingerprint_match: bool
    external_reward_vector: list[float] | None
    window_return: float | None
    post_window_state_hash: str | None
    window_length_exact: bool
    no_inner_check_observed: bool
    # The skill the focal agent's token actually realized (SET only; None for
    # KEEP or when the branch aborted before the decision was made). Needed
    # because SET_SAMPLED's replacement skill is chosen by the policy at
    # replay time, not named by the driver in advance -- unlike
    # OPP_NAMED_SET, whose `candidate_skill` is already known from the plan.
    realized_set_skill: int | None


def replay_branch(
    *,
    agent: StandaloneProcessAgent,
    config,
    training_seed: int,
    evaluation_index: int,
    agent_order: np.ndarray,
    agent_order_code: str,
    stop_at_check_index: int,
    focal_agent: int,
    forced_token: tuple[int, int] | None,
    continuation_seed: int,
    reference_fingerprint: dict[str, Any],
    checkpoint_sha256: str,
    resolved_config_hash: str,
    fingerprint_perturber: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> BranchOutcome:
    """From-reset paired replay (VK-D3): reseed env+torch+numpy, replay the
    identical prefix through `stop_at_check_index - 1` unforced, compute and
    compare the boundary fingerprint, apply `forced_token` (None = NATURAL),
    reseed the continuation, step exactly WINDOW primitive steps, assert no
    inner check. `fingerprint_perturber` is a test-only hook (never reachable
    from the CLI) that mutates the freshly computed branch fingerprint before
    comparison, to drive the fail-closed guard red on demand."""
    ep_seed = episode_seed(evaluation_index)
    pol_seed = policy_stream_seed(training_seed, evaluation_index, agent_order_code)
    wrapped_env = make_env(config, int(ep_seed))
    try:
        torch.manual_seed(int(pol_seed))
        np.random.seed(_legacy_numpy_seed(pol_seed))
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
                raise RuntimeError("counterfactual replay reached a non-due step outside a check window")
            check_index += 1
            if check_index < stop_at_check_index:
                # Unforced prefix check: exactly one K0=WINDOW-primitive-step
                # window elapses between due-checks on this fixed clock, so
                # advancing one step at a time (rather than the whole window)
                # would find the NEXT due-check false for the intervening
                # steps -- mirror `run_natural_episode`'s own window-consuming
                # shape rather than stepping once and re-checking `due`.
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
                        0, reward=float(reward), next_obs=obs, next_state=state, done=done, collect_r31=False,
                    )
                    if done:
                        break
                if done:
                    raise RuntimeError("episode ended before reaching the focal check")
                continue

            branch_fp = build_fingerprint(
                raw_env=raw_env, agent=agent, env_id=0, obs=obs, state=state,
                agent_order=agent_order, checkpoint_sha256=checkpoint_sha256,
                resolved_config_hash=resolved_config_hash,
            )
            compared_fp = branch_fp if fingerprint_perturber is None else fingerprint_perturber(dict(branch_fp))
            if fingerprint_digest(compared_fp) != fingerprint_digest(reference_fingerprint):
                return BranchOutcome(
                    fingerprint_match=False, external_reward_vector=None, window_return=None,
                    post_window_state_hash=None, window_length_exact=False, no_inner_check_observed=False,
                    realized_set_skill=None,
                )

            forced = {focal_agent: forced_token} if forced_token is not None else None
            agent.maybe_assign_skills(
                obs, state=state, step=step, k=K0, env_id=0, deterministic=False,
                collect_r31=False, forced_tokens=forced, agent_order=agent_order,
            )
            pending = agent.high_check_buffer.pending[0]
            order_np = np.asarray(pending.agent_order, dtype=np.int64).reshape(-1)
            position = int(np.where(order_np == int(focal_agent))[0][0])
            realized_kind = int(np.asarray(pending.token_kind, dtype=np.int64).reshape(-1)[position])
            realized_set_skill = (
                int(np.asarray(pending.set_skill, dtype=np.int64).reshape(-1)[position])
                if realized_kind == SET_TOKEN
                else None
            )
            torch.manual_seed(int(continuation_seed))
            np.random.seed(_legacy_numpy_seed(continuation_seed))

            rewards: list[float] = []
            for _ in range(WINDOW):
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
                obs, reward, terminated, truncated, info = wrapped_env.step(actions)
                state = info.get("next_state", state)
                step += 1
                rewards.append(float(reward))
                done = bool(terminated or truncated) or step >= max_steps
                agent.record_environment_step(
                    0, reward=float(reward), next_obs=obs, next_state=state, done=done, collect_r31=False,
                )
                if done:
                    break

            window_length_exact = len(rewards) == WINDOW
            no_inner_check = window_length_exact and int(agent.steps_to_check[0]) == 0
            return BranchOutcome(
                fingerprint_match=True,
                external_reward_vector=rewards + [0.0] * (WINDOW - len(rewards)),
                window_return=float(sum(rewards)),
                post_window_state_hash=hash_bytes(np.asarray(state, dtype=np.float32).tobytes()),
                window_length_exact=window_length_exact,
                no_inner_check_observed=no_inner_check,
                realized_set_skill=realized_set_skill,
            )
    finally:
        wrapped_env.close()


# =============================================================================
# Per-checkpoint orchestration
# =============================================================================


@dataclass
class SeedEvaluationResult:
    check_rows: list[dict[str, Any]] = field(default_factory=list)
    unit_rows: list[dict[str, Any]] = field(default_factory=list)
    replay_mismatch: bool = False
    mismatched_families: list[str] = field(default_factory=list)


def evaluate_checkpoint(
    *,
    entry: dict[str, Any],
    config,
    episodes: int = EVAL_EPISODES,
    n_select: int = N_SELECT,
    n_eval: int = N_EVAL,
    load_checkpoint: bool = True,
    fingerprint_perturber: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    forced_tokens_by_check: dict[int, dict[int, tuple[int, int]]] | None = None,
) -> SeedEvaluationResult:
    """Evaluate one trained checkpoint. `load_checkpoint=False` (skeleton-test
    hook only) builds an untrained, randomly-initialized agent instead of
    loading `entry['checkpoint_path']`; the CLI path (`run_full_evaluation`)
    never sets this, so it always loads the real checkpoint. `forced_tokens_by_check`
    is likewise a test-only hook (see `run_natural_episode`), applied identically
    to every episode's natural pass; the CLI path never sets it either."""
    training_seed = int(entry["training_seed"])
    checkpoint_sha256 = str(entry["checkpoint_sha256"])
    resolved_config_hash = str(entry["resolved_config_hash"])

    load_from = entry["checkpoint_path"] if load_checkpoint else None
    agent = build_agent(config, checkpoint_path=load_from)

    result = SeedEvaluationResult()

    for i in range(episodes):
        agent_order, agent_order_code = agent_order_for_evaluation_index(i)
        natural_checks = run_natural_episode(
            agent=agent, config=config, training_seed=training_seed, evaluation_index=i,
            checkpoint_sha256=checkpoint_sha256, resolved_config_hash=resolved_config_hash,
            forced_tokens_by_check=forced_tokens_by_check,
        )
        for nc in natural_checks:
            if nc.context.check_index == 0:
                continue  # V-K0A convention: initial check has no incumbent, excluded (VK-D1).
            _emit_check_and_units(
                result=result, agent=agent, config=config, training_seed=training_seed,
                evaluation_index=i, agent_order=agent_order, agent_order_code=agent_order_code,
                natural=nc, checkpoint_sha256=checkpoint_sha256, resolved_config_hash=resolved_config_hash,
                n_select=n_select, n_eval=n_eval, fingerprint_perturber=fingerprint_perturber,
            )
    return result


def _oracle_u_src_at_check(raw_env, incumbent: tuple[int, int], action_table, table_hash) -> dict[int, dict]:
    return vk0a_oracle.compute_u_src(raw_env, incumbent, action_table, table_hash)


def _action_table_and_hash():
    from ha_ctse_process.standalone_agent import FixedSkillPrimitivePolicy

    policy = FixedSkillPrimitivePolicy(4, 2, "continuous")
    table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    table_hash = hash_bytes(np.ascontiguousarray(table).tobytes())
    return table, table_hash


_ACTION_TABLE, _ACTION_TABLE_HASH = _action_table_and_hash()


def _emit_check_and_units(
    *,
    result: SeedEvaluationResult,
    agent: StandaloneProcessAgent,
    config,
    training_seed: int,
    evaluation_index: int,
    agent_order: np.ndarray,
    agent_order_code: str,
    natural: NaturalCheckResult,
    checkpoint_sha256: str,
    resolved_config_hash: str,
    n_select: int,
    n_eval: int,
    fingerprint_perturber: Callable[[dict[str, Any]], dict[str, Any]] | None,
) -> None:
    ctx = natural.context
    check_index = ctx.check_index

    # A-VK-D10: the exhaustive oracle on the ACTUAL pre-decision incumbent
    # pair, computed on a fresh env replay to this exact check state -- never
    # from phase, axis, labels, or the V-K0A optimal track. Reusing the
    # natural pass's own `raw_env` after it has advanced past this check
    # would read the WRONG (post-decision) state, so this reconstructs it
    # independently instead.
    #
    # `TwoTimescaleRoleFreeActionsEnv` is deterministic given `reset(seed)`
    # and `steps` alone (VK-D1): `_targets()` depends only on `self.steps`
    # and the two initial signs drawn at reset, and `step()` advances `steps`
    # unconditionally regardless of the action passed. So stepping the raw
    # env forward `check_index * K0` primitive steps with ANY legal action
    # reproduces the identical `(steps, signs)` state the oracle's own
    # `fingerprint()` compares on -- no policy replay is needed to reach it.
    oracle_env = make_env(config, int(episode_seed(evaluation_index)))
    oracle_env.reset(seed=int(episode_seed(evaluation_index)))
    raw_oracle_env = oracle_env.env
    zero_action = {"agent_0": np.zeros(2, dtype=np.float32), "agent_1": np.zeros(2, dtype=np.float32)}
    for _ in range(check_index * K0):
        raw_oracle_env.step(zero_action)
    per_focal = _oracle_u_src_at_check(raw_oracle_env, ctx.incumbent, _ACTION_TABLE, _ACTION_TABLE_HASH)
    oracle_env.close()

    for focal in (0, 1):
        c_id = check_unit_id(training_seed, evaluation_index, agent_order_code, check_index, focal)
        token_kind = natural.factual_token_kind[focal]
        set_skill = natural.factual_set_skill[focal]
        keep_prob = natural.factual_keep_prob[focal]
        keep_prob_out = None if (isinstance(keep_prob, float) and np.isnan(keep_prob)) else float(keep_prob)

        check_row = {
            "contract_id": CONTRACT_ID,
            "trace_schema_version": TRACE_SCHEMA_VERSION,
            "training_seed": int(training_seed),
            "evaluation_seed": int(evaluation_index),
            "episode_id": int(episode_seed(evaluation_index)),
            "agent_order_code": agent_order_code,
            "check_index": int(check_index),
            "focal_agent": int(focal),
            "check_unit_id": c_id,
            "checkpoint_hash": checkpoint_sha256,
            "resolved_config_hash": resolved_config_hash,
            "primitive_step": int(ctx.step),
            "active_mask": [bool(x) for x in ctx.active_mask],
            "current_skill": int(ctx.incumbent[focal]),
            "skill_age": int(ctx.skill_age[focal]),
            "steps_to_check": int(ctx.reference_fingerprint["steps_to_check"]),
            "state_hash": ctx.reference_fingerprint["centralized_state_bytes"],
            "observation_hash": ctx.reference_fingerprint["observation_bytes"],
            "pre_check_fingerprint": fingerprint_digest(ctx.reference_fingerprint),
            "oracle_u_src": float(per_focal[focal]["U_src"]),
            "oracle_urgency_class": per_focal[focal]["urgency_class"],
            "natural_token_kind": token_kind,
            "natural_set_skill": None if set_skill is None else str(int(set_skill)),
            "keep_prob": keep_prob_out,
            "factual_joint_token": {
                str(a): {
                    "kind": natural.factual_token_kind[a],
                    "set_skill": (
                        None if natural.factual_set_skill[a] is None else str(int(natural.factual_set_skill[a]))
                    ),
                }
                for a in (0, 1)
            },
            "segment_origin": natural.segment_origin[focal],
            "incumbent_end_authority_at_check": (
                "voluntary_set" if token_kind == NATURAL_TOKEN_SET else "none_open"
            ),
            "post_window_end_authority": (
                "episode_termination" if check_index == NONINITIAL_CHECKS else "none_open"
            ),
            "current_targets": ctx.current_targets,
            "previous_targets": ctx.previous_targets,
            "natural_external_reward_vector": [float(x) for x in natural.window_rewards]
            + [0.0] * (WINDOW - len(natural.window_rewards)),
            "slow_match_vector": [int(x) for x in natural.window_slow] + [0] * (WINDOW - len(natural.window_slow)),
            "fast_match_vector": [int(x) for x in natural.window_fast] + [0] * (WINDOW - len(natural.window_fast)),
        }
        validate_segment_fields(check_row)
        result.check_rows.append(check_row)

        family_plan: list[tuple[str, int | None, str, int]] = [
            (ESTIMAND_KEEP_REFERENCE, None, PHASE_SELECT, r) for r in range(n_select)
        ] + [
            (ESTIMAND_KEEP_REFERENCE, None, PHASE_EVALUATE, r) for r in range(n_eval)
        ]
        candidates = legal_set_candidates(ctx.incumbent[focal])
        for z in candidates:
            family_plan.extend((ESTIMAND_OPP_NAMED_SET, z, PHASE_SELECT, r) for r in range(n_select))
            family_plan.extend((ESTIMAND_OPP_NAMED_SET, z, PHASE_EVALUATE, r) for r in range(n_eval))
        family_plan.extend((ESTIMAND_SET_SAMPLED, None, PHASE_EVALUATE, r) for r in range(n_eval))
        family_plan.extend((ESTIMAND_NATURAL, None, PHASE_EVALUATE, r) for r in range(n_eval))

        keep_unit_by_replicate: dict[tuple[str, int], str] = {}
        aborted_families: set[tuple[str, int | None]] = set()

        for family, candidate, phase, replicate_index in family_plan:
            if (family, candidate) in aborted_families:
                continue
            candidate_token = (
                SHARED_CANDIDATE_TOKEN
                if (family != ESTIMAND_OPP_NAMED_SET or phase == PHASE_EVALUATE)
                else str(candidate)
            )
            seed = branch_continuation_seed(
                training_seed=training_seed, evaluation_index=evaluation_index,
                agent_order_code=agent_order_code, check_index=check_index, focal_agent=focal,
                candidate_target_id=candidate_token, phase=phase, replicate_index=replicate_index,
            )
            if family == ESTIMAND_KEEP_REFERENCE:
                forced_token = (KEEP_TOKEN, INVALID_SKILL)
            elif family == ESTIMAND_OPP_NAMED_SET:
                forced_token = (SET_TOKEN, int(candidate))
            elif family == ESTIMAND_SET_SAMPLED:
                forced_token = (SET_TOKEN, INVALID_SKILL)
            else:
                forced_token = None

            b_id = branch_unit_id(c_id, family, candidate, phase, replicate_index)
            outcome = replay_branch(
                agent=agent, config=config, training_seed=training_seed, evaluation_index=evaluation_index,
                agent_order=agent_order, agent_order_code=agent_order_code, stop_at_check_index=check_index,
                focal_agent=focal, forced_token=forced_token, continuation_seed=seed,
                reference_fingerprint=ctx.reference_fingerprint, checkpoint_sha256=checkpoint_sha256,
                resolved_config_hash=resolved_config_hash, fingerprint_perturber=fingerprint_perturber,
            )

            paired_keep_id = (
                None if family == ESTIMAND_KEEP_REFERENCE
                else keep_unit_by_replicate.get((phase, replicate_index))
            )
            if family == ESTIMAND_KEEP_REFERENCE:
                keep_unit_by_replicate[(phase, replicate_index)] = b_id

            # SET_SAMPLED's replacement skill is chosen by the policy at
            # replay time (forced_token names only the KIND, INVALID_SKILL
            # for the skill), so it is read back from the branch outcome
            # rather than known upfront the way OPP_NAMED_SET's `candidate`
            # is. `validate_unit_row` (scripts/analyze_vk0_result.py)
            # requires a non-empty str for both families regardless of
            # replay outcome, so an aborted (fingerprint-mismatch) row still
            # needs a placeholder rather than null.
            if family == ESTIMAND_OPP_NAMED_SET:
                candidate_skill_out = str(int(candidate))
            elif family == ESTIMAND_SET_SAMPLED:
                candidate_skill_out = (
                    str(outcome.realized_set_skill)
                    if outcome.realized_set_skill is not None
                    else "unresolved_replay_mismatch"
                )
            else:
                candidate_skill_out = None

            unit_row = {
                "contract_id": CONTRACT_ID,
                "trace_schema_version": TRACE_SCHEMA_VERSION,
                "training_seed": int(training_seed),
                "evaluation_seed": int(evaluation_index),
                "episode_id": int(episode_seed(evaluation_index)),
                "agent_order_code": agent_order_code,
                "check_index": int(check_index),
                "focal_agent": int(focal),
                "check_unit_id": c_id,
                "checkpoint_hash": checkpoint_sha256,
                "resolved_config_hash": resolved_config_hash,
                "branch_unit_id": b_id,
                "estimand_family": family,
                "parent_check_unit_id": c_id,
                "candidate_skill": candidate_skill_out,
                "phase": phase,
                "replicate_index": int(replicate_index),
                "derived_seed": int(seed),
                "external_reward_vector": outcome.external_reward_vector or [0.0] * WINDOW,
                "window_return": outcome.window_return if outcome.window_return is not None else 0.0,
                "post_window_state_hash": outcome.post_window_state_hash or "",
                "paired_keep_unit_id": paired_keep_id,
                "replay_conformance": {"fingerprint_match": bool(outcome.fingerprint_match)}
                if not outcome.fingerprint_match
                else {
                    "fingerprint_match": True,
                    "window_length_exact": bool(outcome.window_length_exact),
                    "no_inner_check_observed": bool(outcome.no_inner_check_observed),
                },
            }
            result.unit_rows.append(unit_row)

            if not outcome.fingerprint_match:
                result.replay_mismatch = True
                result.mismatched_families.append(f"{c_id}:{family}:{candidate}:{phase}:{replicate_index}")
                aborted_families.add((family, candidate))


# =============================================================================
# Output
# =============================================================================


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_full_evaluation(
    *, checkpoint_paths: list[str], oracle_panel_path: Path, panel_digest_path: Path,
    config_name: str, out_dir: Path,
) -> dict[str, Any]:
    auth = load_and_authorize_panel(oracle_panel_path, panel_digest_path)
    entries = [resolve_checkpoint_entry(p) for p in checkpoint_paths]

    config_module = importlib.import_module(config_name)

    all_check_rows: list[dict[str, Any]] = []
    all_unit_rows: list[dict[str, Any]] = []
    seeds_manifest: dict[str, Any] = {}
    overall_replay_mismatch = False

    for entry in entries:
        config = config_module.Config()
        result = evaluate_checkpoint(entry=entry, config=config)
        all_check_rows.extend(result.check_rows)
        all_unit_rows.extend(result.unit_rows)
        overall_replay_mismatch = overall_replay_mismatch or result.replay_mismatch
        seeds_manifest[str(entry["training_seed"])] = {
            "checkpoint_hash": entry["checkpoint_sha256"],
            "resolved_config_hash": entry["resolved_config_hash"],
            "low_optimizer_steps": entry["low_optimizer_steps"],
            "preflight_manifest_path": entry["preflight_manifest_path"],
            "replay_mismatch": result.replay_mismatch,
            "mismatched_families": result.mismatched_families,
            # A-W6-5: verbatim source-labelled block plus the driver's own
            # recomputed hash of the training run_manifest.json it came
            # from -- never the launcher's copy of that hash substituted in
            # its place (see `resolve_actual_exposure`).
            "actual_exposure": entry["actual_exposure"],
            "source_run_manifest_sha256": entry["source_run_manifest_sha256"],
        }

    manifest = {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "authorization": auth["authorization"],
        "seeds": seeds_manifest,
        "replay_mismatch": overall_replay_mismatch,
        "run_verdict": INVALID_VERDICT if overall_replay_mismatch else None,
    }

    write_jsonl(out_dir / VK0B_TRACE_FILENAME, all_check_rows)
    write_jsonl(out_dir / VK0B_UNITS_FILENAME, all_unit_rows)
    (out_dir / VK0B_MANIFEST_FILENAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
    )
    return manifest


def _write_refusal(out_dir: Path, error: Exception, authorization: dict[str, Any] | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "refused": True,
        "refusal_reason": str(error),
        "authorization": authorization,
    }
    (out_dir / VK0B_MANIFEST_FILENAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-panel", dest="oracle_panel", required=True)
    parser.add_argument("--panel-digest", dest="panel_digest", required=True)
    parser.add_argument("--checkpoints", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default="config_d7_2b_toy_learned_keep")
    args = parser.parse_args()

    out_dir = Path(args.out)

    try:
        auth = load_and_authorize_panel(Path(args.oracle_panel), Path(args.panel_digest))
    except Vk0bRefusalError as exc:
        _write_refusal(out_dir, exc)
        print(f"VK0B_REFUSED={exc}")
        raise SystemExit(1) from exc

    if len(args.checkpoints) != 6:
        exc = Vk0bRefusalError(f"CHECKPOINT_COUNT_MISMATCH: expected 6, got {len(args.checkpoints)}")
        _write_refusal(out_dir, exc, authorization=auth["authorization"])
        print(f"VK0B_REFUSED={exc}")
        raise SystemExit(1)

    try:
        manifest = run_full_evaluation(
            checkpoint_paths=list(args.checkpoints), oracle_panel_path=Path(args.oracle_panel),
            panel_digest_path=Path(args.panel_digest), config_name=str(args.config), out_dir=out_dir,
        )
    except Vk0bRefusalError as exc:
        _write_refusal(out_dir, exc, authorization=auth["authorization"])
        print(f"VK0B_REFUSED={exc}")
        raise SystemExit(1) from exc

    print(f"VK0B_REPLAY_MISMATCH={manifest['replay_mismatch']}")
    print(f"VK0B_RUN_VERDICT={manifest['run_verdict']}")
    print(f"VK0B_OUT={out_dir}")


if __name__ == "__main__":
    main()
