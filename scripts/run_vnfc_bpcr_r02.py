"""Runner for VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02 (B/EXPLORE).

R02 is the R01 object with exactly one presentation change: the canonical
opaque-rank sort.  Physical candidate rows are serialised in ascending opaque
rank before the first tensor operation and the null candidate stays last, so the
deterministic command, the physically aligned probability vector and the
RNG-coupled sampled command are functions of physical state alone.

This module does not copy the R01 runner.  It imports
``scripts/run_vnfc_bpcr_b_explore.py`` and installs the R02 law and identity on
it, and it adds the PRIMARY CLI path the R01 runner intentionally omitted.

Section 11 recast in force (owner decisions 4, 6 and 7 of
``docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`` A.4,
recorded in
``docs/research/candidates/variable_n_fleet_churn/VNFC_SECTION11_RECAST_INTAKE_20260903.md``):

* the 304-row A0 finite-physical-action law is optional analysis and holds
  nothing.  Its replacement section 4 integrity item is the 52-row
  unit-test-scale check ``VNFC-R02-PRESENTATION-CONFORMANCE-52`` in
  ``tests/experiments/candidates/variable_n_fleet_churn_b_explore/``;
* byte manifests and the native build key are RECORDED, never REQUIRED.  The
  native backend may be compiled from unchanged source; the observed build key
  and artifact digest are recorded with ``gating: false``;
* missing RESOURCE telemetry downgrades to ``resources_unmeasured: true`` with
  reasons and never annuls.  Learner-side instrumentation failure still
  quarantines under evidence-spec section 6.2.

What still gates a launch: the section 4 integrity items, the nonzero counts,
the fresh 4 GiB admission, and one exposure line
(``||theta - theta0|| / ||theta0||`` per arm per update).
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
import math
import sys
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

import torch

RUN_REVISION = "VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02"
DEBUG_STAGE = "B0-DEBUG"
PRIMARY_STAGE = "B1-B3-PRIMARY"
DEBUG_SEED = 2026090301
PRIMARY_SEEDS = (2026090311, 2026090321, 2026090331)
PRESENTATION_LAW = "VNFC-R02-ORC-CANONICAL-OPAQUE-RANK-SORT-V1"
CONFORMANCE_OBJECT = "VNFC-R02-PRESENTATION-CONFORMANCE-52"
RECAST_INTAKE = (
    "docs/research/candidates/variable_n_fleet_churn/VNFC_SECTION11_RECAST_INTAKE_20260903.md"
)

# Recorded, never required (recast rows 5 and 6).
FROZEN_A0_NATIVE_LITERALS = {
    "bpcr_backend_dll_build_key": "7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99",
    "bpcr_backend_dll_sha256": "dadac9589cf1a885b1acd3891f7411152fa2748cbc34ddbf3537d0b2708f5f68",
    "bpcr_backend_dll_size_bytes": 213504,
    "loaded_python_dependency_sources": 942,
    "opened_distribution_resources": 31,
    "compiled_modules_pre_load": 81,
    "compiled_modules_post_load": 82,
    "post_load_canonical_root": "ce22039a3888cea1f3e12963e4e0e3fb8eb00753446b332770cb8257c521ed63",
}

# Owner decision 7: a failure of RESOURCE measurement downgrades.  Every other
# telemetry refusal is a learner-side or scientific binding and still quarantines
# under evidence-spec section 6.2.
RESOURCE_MEASUREMENT_FAILURES = frozenset({
    "scientific result telemetry contains unmeasured fields",
    "external telemetry contains nonpositive measured fields",
    "external stage wall/CPU telemetry differs",
    "external storage/I/O telemetry differs",
    "process-tree telemetry measurement source/limitations differ",
    "process-tree telemetry sampling/exposure value differs",
    "process-tree host CPU occupancy differs",
    "process-tree telemetry extended I/O differs",
    "process-tree aggregate I/O binding differs",
    "process-tree scientific throughput binding differs",
})


class R02ContractError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# the R01 runner, imported as a module (never copied)
# --------------------------------------------------------------------------

def load_r01_runner() -> types.ModuleType:
    """Import scripts/run_vnfc_bpcr_b_explore.py as a module."""
    name = "vnfc_bpcr_b_explore_runner"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    path = _REPOSITORY_ROOT / "scripts" / "run_vnfc_bpcr_b_explore.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise R02ContractError("the R01 B/EXPLORE runner could not be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# the canonical opaque-rank sort
# --------------------------------------------------------------------------

def canonical_permutation(opaque_ranks: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Return (perm, inverse) for the ascending opaque-rank serialisation.

    ``perm[b, c]`` is the presented row index of the ``c``-th canonical
    candidate; ``inverse[b, r]`` is the canonical position of presented row
    ``r``.  Opaque ranks are a unique total order (fixtures.py enforces it), so
    the sort is total and needs no secondary key.  The null candidate is not a
    row: it keeps index ``N`` and therefore stays last.
    """
    if opaque_ranks.ndim != 2:
        raise R02ContractError("opaque rank tensor shape differs")
    perm = torch.argsort(opaque_ranks, dim=1, stable=True)
    inverse = torch.argsort(perm, dim=1)
    return perm, inverse


def _map_candidate_index(index: torch.Tensor, mapping: torch.Tensor, n: int) -> torch.Tensor:
    """Map agent candidate indices through ``mapping``; leave the null index."""
    if n == 0:
        return index
    return torch.where(index < n, torch.gather(mapping, 1, index.clamp(max=n - 1)), index)


def canonicalize_inputs(
    agents: torch.Tensor,
    legal_masks: torch.Tensor,
    fixed_occupants: torch.Tensor,
    opaque_ranks: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    perm, inverse = canonical_permutation(opaque_ranks)
    c_agents = torch.gather(agents, 1, perm[:, :, None].expand(-1, -1, agents.shape[2]))
    c_legal = torch.gather(legal_masks, 1, perm[:, :, None].expand(-1, -1, legal_masks.shape[2]))
    c_opaque = torch.gather(opaque_ranks, 1, perm)
    c_fixed = torch.where(
        fixed_occupants >= 0,
        torch.gather(inverse, 1, fixed_occupants.clamp_min(0)),
        fixed_occupants,
    )
    return c_agents, c_legal, c_fixed, c_opaque, perm, inverse


class CanonicalOpaqueRankForward:
    """Mixin: canonicalise before the first tensor op, invert on the way out.

    The public tensor contract is unchanged.  Callers keep passing rows in the
    host's presentation order and keep receiving command indices in that same
    order, so every ``presented[row]`` decoder downstream is untouched.  What
    changes is that every float reduction inside the model sees the same rows in
    the same positions for every co-presentation of one physical state.
    """

    presentation_law = PRESENTATION_LAW

    def forward(  # type: ignore[override]
        self,
        agents: torch.Tensor,
        zones: torch.Tensor,
        globals_: torch.Tensor,
        legal_masks: torch.Tensor,
        fixed_occupants: torch.Tensor,
        opaque_ranks: torch.Tensor,
        uniforms: torch.Tensor | None = None,
        forced_commands: torch.Tensor | None = None,
        _evaluation_support_valid_forcing: bool = False,
    ) -> dict[str, torch.Tensor]:
        n = agents.shape[1]
        c_agents, c_legal, c_fixed, c_opaque, perm, inverse = canonicalize_inputs(
            agents, legal_masks, fixed_occupants, opaque_ranks
        )
        c_forced = (
            None if forced_commands is None
            else _map_candidate_index(forced_commands, inverse, n)
        )
        output = super().forward(  # type: ignore[misc]
            c_agents, zones, globals_, c_legal, c_fixed, c_opaque,
            uniforms, c_forced, _evaluation_support_valid_forcing,
        )
        command = _map_candidate_index(output["command"], perm, n)
        probabilities = output["token_probabilities"]
        target = torch.cat((perm, torch.full((perm.shape[0], 1), n, dtype=perm.dtype)), 1)
        restored = torch.empty_like(probabilities)
        restored.scatter_(
            2, target[:, None, :].expand(-1, probabilities.shape[1], -1), probabilities
        )
        return {**output, "command": command, "token_probabilities": restored}


def build_canonical_model_classes(r01: types.ModuleType) -> tuple[type, type]:
    base_mapr = r01.MAPR4
    base_direct = r01.DirectSetAR
    canonical_mapr = type("CanonicalMAPR4", (CanonicalOpaqueRankForward, base_mapr), {})
    canonical_direct = type("CanonicalDirectSetAR", (CanonicalOpaqueRankForward, base_direct), {})
    return canonical_mapr, canonical_direct


# --------------------------------------------------------------------------
# PS-B0: trace the canonical serialisation, not the host's presentation order
# --------------------------------------------------------------------------

def _canonical_snapshot(ps_b0: types.ModuleType, r01: types.ModuleType, snapshot: object):
    """Re-express one PS-B0 snapshot in the canonical opaque-rank order.

    ``ps_b0._model_trace`` re-implements the decoder in the snapshot's row order
    and asserts byte equality against ``model(*snapshot.inputs)``.  Under the
    R02 law the model computes in canonical order, so the trace has to be taken
    in canonical order too.  Rather than duplicate ninety lines of trace, the
    snapshot's rows and its physical-rank decoder are both moved into canonical
    order and the original trace is used unchanged.
    """
    opaque = snapshot.inputs[5]
    perm = torch.argsort(opaque, dim=1, stable=True)[0].tolist()
    canonical_inputs = r01._permuted_inputs(snapshot.inputs, perm)
    epoch = int(snapshot.trace["epoch"])
    fixture = snapshot.fixture
    presented = tuple(
        rank for rank in fixture.post_presentations[epoch] if rank != snapshot.failed_rank
    )
    canonical_presented = tuple(presented[index] for index in perm)
    presentations = list(fixture.post_presentations)
    presentations[epoch] = canonical_presented + (snapshot.failed_rank,)
    proxy_fixture = types.SimpleNamespace(
        post_presentations=tuple(presentations),
        failed_zone=fixture.failed_zone,
    )
    return dataclasses.replace(snapshot, fixture=proxy_fixture, inputs=canonical_inputs)


def install_canonical_ps_b0_trace(ps_b0: types.ModuleType, r01: types.ModuleType) -> None:
    original = getattr(ps_b0, "_r01_model_trace", None) or ps_b0._model_trace
    ps_b0._r01_model_trace = original

    def canonical_model_trace(model, snapshot):
        return original(model, _canonical_snapshot(ps_b0, r01, snapshot))

    ps_b0._model_trace = canonical_model_trace


# --------------------------------------------------------------------------
# gate-to-field: native artifacts, byte manifests, resource telemetry
# --------------------------------------------------------------------------

def prepare_native_backends() -> dict[str, object]:
    """Build (if absent) and load the two content-keyed native artifacts.

    Recast row 6: compilation from unchanged source is permitted and the
    observed build key is RECORDED, never REQUIRED.  This runs before the
    telemetry sink is constructed so that no compiler child process can appear
    inside the monitored window.
    """
    from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import native_backend as r09_native
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native

    r09_native.require_cpp_batched_backend()
    b_native.require_b_native_telemetry()
    binding = b_native.resolve_prebuilt_load_only_binding()
    # The resolver only reports; installing is what binds the process-local
    # load-only functions the R01 runner's storage contract reads back.
    b_native._install_prebuilt_load_only_binding(binding)
    return binding


def native_identity_record(binding: Mapping[str, object]) -> dict[str, object]:
    """Recorded native identity.  ``gating`` is false by construction."""
    observed_key = str(binding["r09_build_key"])
    observed_sha = str(binding["primary_artifact_sha256"])
    observed_size = int(binding["primary_artifact_size"])
    frozen = FROZEN_A0_NATIVE_LITERALS
    return {
        "schema": "VNFC_BPCR_R02_NATIVE_IDENTITY_RECORD_V1",
        "gating": False,
        "recorded_only_reason": (
            "evidence spec 11.4: hash chains and byte manifests may not hold a B launch; "
            "recast intake row 6"
        ),
        "observed_bpcr_backend_dll_build_key": observed_key,
        "observed_bpcr_backend_dll_sha256": observed_sha,
        "observed_bpcr_backend_dll_size_bytes": observed_size,
        "observed_bpcr_backend_dll_path": str(binding["primary_artifact_path"]),
        "observed_shadow_build_key": str(binding["shadow_build_key"]),
        "observed_shadow_sha256": str(binding["shadow_artifact_sha256"]),
        "observed_shadow_size_bytes": int(binding["shadow_artifact_size"]),
        "observed_compiler_path": str(binding["compiler_path"]),
        "observed_compiler_sha256": str(binding["compiler_sha256"]),
        "frozen_a0_literals": dict(frozen),
        "build_key_equals_frozen_literal": observed_key == frozen["bpcr_backend_dll_build_key"],
        "artifact_sha256_equals_frozen_literal": observed_sha == frozen["bpcr_backend_dll_sha256"],
        "artifact_size_equals_frozen_literal": observed_size == frozen["bpcr_backend_dll_size_bytes"],
        "rebuild_from_unchanged_source_holds_nothing": True,
    }


def byte_manifest_record() -> dict[str, object]:
    """The A0 byte manifests, recorded as present-or-absent, never required."""
    directory = _REPOSITORY_ROOT / "docs" / "research" / "candidates" / "variable_n_fleet_churn"
    rows = []
    for name in (
        "VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_KERNEL_BYTE_MANIFEST_20260901.md",
        "VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv",
    ):
        path = directory / name
        present = path.is_file()
        rows.append({
            "manifest": name,
            "present": present,
            "size_bytes": path.stat().st_size if present else None,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if present else None,
        })
    return {
        "schema": "VNFC_BPCR_R02_BYTE_MANIFEST_RECORD_V1",
        "gating": False,
        "required": False,
        "recorded_only_reason": (
            "evidence spec 11.4 and 11.6; recast intake rows 3, 5 and 6: the A0 byte manifests are "
            "recorded if the tooling produces them and never hold an R02 launch"
        ),
        "manifests": tuple(rows),
        "a0_disposition": "OPTIONAL_ANALYSIS_HOLDS_NOTHING",
        "a0_implementation_started": False,
    }


def _json_material(value: object) -> object:
    """Convert working dataclass rows to the JSON values a digest can take."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        to_dict = getattr(value, "to_dict", None)
        return to_dict() if callable(to_dict) else dataclasses.asdict(value)
    if isinstance(value, Mapping):
        return {key: _json_material(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_material(item) for item in value]
    return value


def install_serializable_freeze_material(r01: types.ModuleType) -> None:
    """Repair, in the R02 runner, the held-out freeze token's digest input.

    `assess_posttraining_debug_gate` carries the live PS-B0 comparison rows under
    `ps_b0_comparisons` so that the artifact serialiser can consume them, and
    `_freeze_before_n7` then puts `dict(gate)` into a canonical-JSON digest.  On
    the DEBUG path with a real adapter those rows are `PSB0ActualComparison`
    dataclasses, so the digest raises
    `TypeError: Object of type PSB0ActualComparison is not JSON serializable`
    before the held-out `N=7` evaluation is opened.  The rows are bound through
    the same `to_dict()`/`asdict()` conversion the PS-B0 artifact serialiser
    already uses at `_serialize_ps_b0_artifact_once`, so the freeze still binds
    the whole gate and nothing scientific changes: the token's digest is never
    compared against any external value, only its namespace is.

    The R01 runner is reused read-only as substrate (DIRECTION.md:164-165), so
    the repair lives here rather than in `scripts/run_vnfc_bpcr_b_explore.py`.
    """
    original = getattr(r01, "_r01_freeze_before_n7", None) or r01._freeze_before_n7
    r01._r01_freeze_before_n7 = original

    def freeze_before_n7(config, training, checkpoints, gate):
        return original(config, training, checkpoints, _json_material(gate))

    r01._freeze_before_n7 = freeze_before_n7


# --------------------------------------------------------------------------
# the repaired per-decision relabel probe (owner decision F.4(a), 2026-09-03)
# --------------------------------------------------------------------------

RELABEL_PROBE_LAW = "VNFC-R02-RELABEL-LIKE-FOR-LIKE-V1"

# The R01 probe compared a batch-8 forward against a batch-1 relabelled forward,
# so it varied presentation and batch width together.  The repaired probe spends
# two batch-1 forwards per decision: the identity presentation and the fresh
# relabel.  The batch-position residual then falls out of the identity forward
# against the batch-8 policy forward, at no extra cost.
FROZEN_DIAGNOSTIC_FORWARDS = {"MAPR": 48, "DIRECT": 60}
R02_DIAGNOSTIC_FORWARDS = {"MAPR": 96, "DIRECT": 108}


def install_like_for_like_relabel_probe(
    r01: types.ModuleType, residual_sink: list[dict[str, object]]
) -> None:
    """Repair `_evaluate_learned_batch`'s per-decision fresh-relabel comparison.

    Before, at `scripts/run_vnfc_bpcr_b_explore.py:477,490-494`:

        permuted_output = model(*_permuted_inputs(inputs[index], permutation))
        permuted = permuted_output["command"][0]
        mapped = tuple(len(permutation) if int(choice) == len(permutation) else permutation[int(choice)] for choice in permuted)
        mismatch += int(tuple(int(choice) for choice in output["command"][index]) != mapped)

    `output` is a forward over a batch of 8 worlds and `permuted_output` a forward
    over a batch of 1, so the comparison varies the presentation *and* the batch
    width.  It therefore refuses a law whose presentation dependence is exactly
    zero, and it is less sensitive to real presentation failure than a
    like-for-like comparison (measured 8/192 versus 15/192 under the R01 law).

    After: both sides are batch-1 forwards of the same decision state at the same
    batch position, so presentation is the only quantity that varies.  This is the
    comparison the direction declares -- "Every later evaluation decision state
    also receives one fresh relabel of that arm's own checkpoint with zero
    physical-command mismatches required"
    (`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:66-68).
    It stays a launch condition and still requires exactly zero.

    The batch-position residual (batch-8 versus batch-1 at the *same* presentation)
    is computed from the identity forward and appended to `residual_sink`.  It is
    descriptive and never gates: it is a property of the arithmetic, identical
    under both laws, and is the channel the A0 freeze forbids relying on rather
    than one any presentation law removes.

    Installed from here; `scripts/run_vnfc_bpcr_b_explore.py` stays untouched
    (DIRECTION.md:164-165, R01 source is read-only substrate).
    """
    if getattr(r01, "_r02_relabel_probe_installed", False):
        return

    from experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training import _model_inputs

    def evaluate_learned_batch(config, rng, token, fixtures, model, arm, checkpoint, cell, world_rows, now):
        if token.namespace != config.namespace or len(fixtures) != 8 or len(world_rows) != 8:
            raise r01.BExploreContractError("held-out freeze token/evaluation native batch differs")
        from experiments.candidates.variable_n_fleet_churn_b_explore import PairedPrimaryShadowBatch
        batch = PairedPrimaryShadowBatch(fixtures)
        mismatch = 0
        raw_sensitivity = tuple(batch.sensitivity()) if cell.startswith("N7") else ()
        sensitivity = tuple({"world": int(world_rows[index]), **row} for index, row in enumerate(raw_sensitivity))
        rows = ()
        residual_rows = []
        policy_forwards = 0
        diagnostic_forwards = 0
        zero = copy.deepcopy(model) if arm == "DIRECT" else None
        if zero is not None:
            with torch.no_grad():
                zero.p("residual.out.weight").zero_()
                zero.p("residual.out.bias").zero_()
        try:
            observations = tuple(row["next_observation"] for row in batch.initial)
            failed = tuple(row["failed_rank"] for row in batch.initial)
            for epoch in range(6):
                inputs = [_model_inputs(observation, fixture, failed_rank)
                          for observation, fixture, failed_rank in zip(observations, fixtures, failed)]
                stacked = tuple(torch.cat([row[index] for row in inputs], 0) for index in range(6))
                with torch.no_grad():
                    output = model(*stacked)
                    policy_forwards += 1
                    r01._validate_model_output(output, context=f"evaluation/{cell}/{checkpoint}/{arm}/policy/epoch{epoch}")
                    if zero is not None:
                        ablated = zero(*stacked, forced_commands=output["command"], _evaluation_support_valid_forcing=True)
                        zero_free = zero(*stacked)
                        diagnostic_forwards += 2
                        r01._validate_model_output(ablated, context=f"evaluation/{cell}/{checkpoint}/{arm}/ablation/epoch{epoch}")
                        r01._validate_model_output(zero_free, context=f"evaluation/{cell}/{checkpoint}/{arm}/zero-free/epoch{epoch}")
                        tv = .5 * torch.abs(output["token_probabilities"] - ablated["token_probabilities"]).sum(2).max(1).values
                        residual_rows.extend({
                            "boundary": epoch, "world_row": world_rows[index],
                            "total_variation": float(tv[index]),
                            "physical_command_change": not torch.equal(output["command"][index], zero_free["command"][index]),
                            "status": "OBSERVED_DIRECT_ABLATION",
                        } for index in range(8))
                commands = tuple(r01._physical_command(output["command"][index], fixture, int(failed[index]), epoch)
                                 for index, fixture in enumerate(fixtures))
                for index, fixture in enumerate(fixtures):
                    permutation = r01._fresh_relabel_permutation(rng, config, arm, checkpoint, fixture, int(world_rows[index]), epoch, now)
                    with torch.no_grad():
                        identity_output = model(*inputs[index])
                        diagnostic_forwards += 1
                        r01._validate_model_output(identity_output, context=f"evaluation/{cell}/{checkpoint}/{arm}/identity/world{index}/epoch{epoch}")
                        permuted_output = model(*r01._permuted_inputs(inputs[index], permutation))
                        diagnostic_forwards += 1
                        r01._validate_model_output(permuted_output, context=f"evaluation/{cell}/{checkpoint}/{arm}/relabel/world{index}/epoch{epoch}")
                        identity = identity_output["command"][0]
                        permuted = permuted_output["command"][0]
                    mapped = tuple(len(permutation) if int(choice) == len(permutation) else permutation[int(choice)]
                                   for choice in permuted)
                    reference = tuple(int(choice) for choice in identity)
                    # gating: presentation only, both sides batch 1, same batch position
                    mismatch += int(reference != mapped)
                    # descriptive: batch position only, same (identity) presentation
                    batched = tuple(int(choice) for choice in output["command"][index])
                    residual_sink.append({
                        "cell": cell, "checkpoint": checkpoint, "arm": arm, "boundary": epoch,
                        "world_row": int(world_rows[index]),
                        "batch_position_command_differs": batched != reference,
                    })
                paired = batch.step(commands)
                rows = paired["primary_rows"]
                shadow_rows = paired["shadow_rows"]
                observations = tuple(row["next_observation"] for row in rows)
            receipt = r01.build_shadow_receipt(f"{config.namespace}/{cell}/{checkpoint}/{arm}", batch.receipt, shadow_rows)
            validated_endpoint_rows = r01._validate_host_endpoint_rows(rows, context=f"evaluation/{cell}/{checkpoint}/{arm}")
            expected_diagnostic = R02_DIAGNOSTIC_FORWARDS[arm]
            if policy_forwards != 6 or diagnostic_forwards != expected_diagnostic:
                raise r01.BExploreContractError("evaluation policy/diagnostic forward exposure differs")
            return {
                "arm": arm, "checkpoint": checkpoint, "cell": cell, "rollouts": 8,
                "relabel_mismatch_count": mismatch,
                "hard_valid": all(row["terminal"] and not row["safety_violation"] and not row["exclusivity_violation"] for row in rows),
                "finite_values": validated_endpoint_rows == 8 and policy_forwards == 6 and diagnostic_forwards == expected_diagnostic,
                "evaluation_policy_forward_calls": policy_forwards,
                "diagnostic_forward_calls": diagnostic_forwards,
                "action_sensitivity": sensitivity,
                "action_sensitivity_status": "OBSERVED_TREATMENT_BLIND_N7" if cell.startswith("N7") else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL",
                "direct_residual_activity": tuple(residual_rows),
                "direct_residual_activity_status": "OBSERVED_DIRECT_ABLATION" if arm == "DIRECT" else "NOT_APPLICABLE_MAPR",
                "endpoints": tuple({key: row[key] for key in ("fail_endpoint", "total_endpoint", "intact_endpoint")} for row in rows),
                "shadow_receipts": (receipt,),
            }
        finally:
            batch.close()

    original_cross = (
        getattr(r01, "_r01_validate_runtime_payload_cross_consistency", None)
        or r01._validate_runtime_payload_cross_consistency
    )
    r01._r01_validate_runtime_payload_cross_consistency = original_cross

    def cross_consistency(config, terminal):
        """Validate the R02 exposure budget here, then run every frozen check.

        The R01 validator pins `diagnostic_forward_calls` to the frozen 48/60 of
        the old probe, which the repaired probe cannot satisfy: it spends two
        batch-1 forwards per decision instead of one.  The true budget (96/108) is
        asserted here and is what the terminal publishes; the frozen accounting
        constant is satisfied on a throwaway copy so that the validator's other
        checks still run against the real terminal.  Recorded as a deviation.
        """
        evaluation = terminal.get("evaluation")
        learned = evaluation.get("learned") if isinstance(evaluation, Mapping) else None
        normalized = terminal
        if isinstance(learned, Sequence) and not isinstance(learned, (str, bytes)):
            for row in learned:
                if not isinstance(row, Mapping):
                    raise r01.BExploreContractError("learned evaluation row schema differs")
                if R02_DIAGNOSTIC_FORWARDS.get(row.get("arm")) != row.get("diagnostic_forward_calls"):
                    raise r01.BExploreContractError("R02 like-for-like relabel probe exposure differs")
                if row.get("relabel_mismatch_count") != 0:
                    raise r01.BExploreContractError("R02 like-for-like relabel probe presentation mismatch")
            normalized_learned = tuple(
                {**row, "diagnostic_forward_calls": FROZEN_DIAGNOSTIC_FORWARDS[row["arm"]]}
                for row in learned
            )
            normalized = {**terminal, "evaluation": {**evaluation, "learned": normalized_learned}}
        original_cross(config, normalized)

    r01._evaluate_learned_batch = evaluate_learned_batch
    r01._validate_runtime_payload_cross_consistency = cross_consistency
    r01._r02_relabel_probe_installed = True
    r01._r02_relabel_probe_law = RELABEL_PROBE_LAW


def batch_residual_record(residual_sink):
    """The batch-position residual, published descriptively and never gating."""
    rows = tuple(residual_sink)
    differing = tuple(row for row in rows if row["batch_position_command_differs"])
    by_cell = {}
    for row in differing:
        by_cell[str(row["cell"])] = by_cell.get(str(row["cell"]), 0) + 1
    return {
        "schema": "VNFC_BPCR_R02_BATCH_POSITION_RESIDUAL_V1",
        "gating": False,
        "recorded_only_reason": (
            "owner decision F.4(a) 2026-09-03: batch-position dependence is a property of the "
            "arithmetic, identical under the R01 and R02 laws, and is not a presentation quantity"
        ),
        "probe_law": RELABEL_PROBE_LAW,
        "comparison": "batch-8 policy forward versus batch-1 forward of the same decision state, same presentation",
        "decisions": len(rows),
        "differing_decisions": len(differing),
        "differing_by_cell": dict(sorted(by_cell.items())),
        "rows": rows,
    }


def install_resource_telemetry_downgrade(r01: types.ModuleType, sink: dict[str, object]) -> None:
    """Owner decision 7: missing resource telemetry downgrades, never annuls."""
    original = getattr(r01, "_r01_validate_telemetry_payload", None) or r01.validate_telemetry_payload
    r01._r01_validate_telemetry_payload = original

    def validate_telemetry_payload(payload: Mapping[str, object]) -> None:
        try:
            original(payload)
        except r01.BExploreContractError as error:
            reason = str(error)
            if reason not in RESOURCE_MEASUREMENT_FAILURES:
                raise
            sink["resources_unmeasured"] = True
            reasons = list(sink.get("resources_unmeasured_reasons", ()))
            if reason not in reasons:
                reasons.append(reason)
            sink["resources_unmeasured_reasons"] = tuple(reasons)

    r01.validate_telemetry_payload = validate_telemetry_payload


# --------------------------------------------------------------------------
# the exposure line
# --------------------------------------------------------------------------

def _parameter_vector(model: torch.nn.Module) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def install_exposure_line(r01: types.ModuleType, sink: list[dict[str, object]]) -> None:
    """Record ``||theta - theta0|| / ||theta0||`` per arm per update.

    Section 11.4's exposure clause: one machine-generated statement that the
    learner can move inside its budget.  It is written beside the run rather
    than into the create-once scientific root, whose schema is frozen.
    """
    original = getattr(r01, "_r01_train_one_update", None) or r01._train_one_update
    r01._r01_train_one_update = original
    initial: dict[str, torch.Tensor] = {}

    def train_one_update(config, rng, model, optimizer, arm, update, now):
        if arm not in initial:
            initial[arm] = _parameter_vector(model).clone()
        result = original(config, rng, model, optimizer, arm, update, now)
        base = initial[arm]
        current = _parameter_vector(model)
        base_norm = float(torch.linalg.vector_norm(base))
        displacement = float(torch.linalg.vector_norm(current - base))
        sink.append({
            "arm": arm,
            "update": int(update),
            "initial_parameter_norm": base_norm,
            "absolute_parameter_displacement": displacement,
            "relative_parameter_displacement": (
                displacement / base_norm if base_norm > 0 else None
            ),
            "mean_preclip_gradient_norm": (
                sum(float(row["preclip_gradient_norm"]) for row in result["loss_rows"])
                / len(result["loss_rows"])
            ),
            "optimizer_steps": int(result["optimizer_steps"]),
        })
        return result

    r01._train_one_update = train_one_update


# --------------------------------------------------------------------------
# installing the R02 object on the R01 runner
# --------------------------------------------------------------------------

def install_r02(
    *,
    exposure_sink: list[dict[str, object]] | None = None,
    telemetry_sink: dict[str, object] | None = None,
    residual_sink: list[dict[str, object]] | None = None,
) -> types.ModuleType:
    """Install the R02 law, identity and recast records on the R01 runner."""
    r01 = load_r01_runner()
    if getattr(r01, "_r02_installed", False):
        return r01

    from experiments.candidates.variable_n_fleet_churn_b_explore import ps_b0

    canonical_mapr, canonical_direct = build_canonical_model_classes(r01)
    r01.MAPR4 = canonical_mapr
    r01.DirectSetAR = canonical_direct
    ps_b0.MAPR4 = canonical_mapr
    ps_b0.DirectSetAR = canonical_direct
    install_canonical_ps_b0_trace(ps_b0, r01)
    install_serializable_freeze_material(r01)
    if residual_sink is not None:
        install_like_for_like_relabel_probe(r01, residual_sink)

    # R02 run identity: a fresh revision, namespace and seed family.  R02 may not
    # reuse an R01 checkpoint, optimizer state, namespace or RNG family
    # (DIRECTION.md:111-113).
    r01.RUN_REVISION = RUN_REVISION
    r01.RUN_NAMESPACE = RUN_REVISION
    r01.DEBUG_SEED = DEBUG_SEED
    r01.PRIMARY_SEEDS = PRIMARY_SEEDS

    # Bind this file into the runner's own source identity, so the law that is
    # actually executed is inside the source fence.
    if "scripts/run_vnfc_bpcr_r02.py" not in r01._ACTUAL_SOURCE_PATHS:
        r01._ACTUAL_SOURCE_PATHS = r01._ACTUAL_SOURCE_PATHS + ("scripts/run_vnfc_bpcr_r02.py",)

    if exposure_sink is not None:
        install_exposure_line(r01, exposure_sink)
    if telemetry_sink is not None:
        install_resource_telemetry_downgrade(r01, telemetry_sink)

    r01._r02_installed = True
    r01._r02_presentation_law = PRESENTATION_LAW
    return r01


def r02_recast_record() -> dict[str, object]:
    return {
        "schema": "VNFC_BPCR_R02_SECTION11_RECAST_RECORD_V1",
        "run_revision": RUN_REVISION,
        "presentation_law": PRESENTATION_LAW,
        "conformance_object": CONFORMANCE_OBJECT,
        "conformance_rows": 52,
        "relabel_probe_law": RELABEL_PROBE_LAW,
        "relabel_probe_decision": (
            "docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md F.4 decision 1, "
            "owner 2026-09-03, option (a)"
        ),
        "recast_intake": RECAST_INTAKE,
        "decisions": (
            "docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md A.4 decisions 4, 6, 7",
            "docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md",
        ),
        "a0_law_disposition": "OPTIONAL_ANALYSIS",
        "superseded_launch_condition": (
            "DIRECTION.md:181-182 'No R02 result-bearing DEBUG is permitted until the one-law A0 "
            "object is complete and passing under its finite claim ceiling.'"
        ),
        "still_gating": (
            "evidence spec section 4 integrity items",
            "section 5.2 nonzero transition/update/evaluation counts",
            "fresh 4 GiB physical and effective memory admission per invocation",
            "one exposure line: ||theta - theta0|| / ||theta0|| per arm per update",
            "equal MAPR/DIRECT interaction and optimizer exposure",
            "held-out N=7 leakage boundary and freeze token",
            "per-decision fresh-relabel mismatch counts, like-for-like: presentation only, both sides batch 1",
            "BCRH comparator competence precheck",
            "create-once publication and section 6.2 quarantine",
        ),
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _read_receipt(path: Path) -> tuple[Mapping[str, object], str]:
    raw = Path(path).read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise R02ContractError("preflight receipt JSON root is not an object")
    return value, hashlib.sha256(raw).hexdigest()


def _canonical_json_line(value: Mapping[str, object]) -> str:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_vnfc_bpcr_r02.py")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("debug", "primary"):
        sub = commands.add_parser(name)
        sub.add_argument("--stage", required=True)
        sub.add_argument("--seed", type=int, required=True)
        sub.add_argument("--updates", type=int, required=True)
        sub.add_argument("--preflight-receipt", type=Path, required=True)
        sub.add_argument("--scratch-root", type=Path, required=True)
        sub.add_argument("--durable-root", type=Path, required=True)
        sub.add_argument("--publication-root", type=Path, required=True)
        sub.add_argument("--record-root", type=Path, required=True)
        if name == "primary":
            sub.add_argument("--archived-debug-valid-claim", type=Path, required=True)
            sub.add_argument("--archived-debug-scientific-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "debug" and (args.stage, args.seed, args.updates) != (DEBUG_STAGE, DEBUG_SEED, 8):
        parser.error(f"debug requires exactly --stage {DEBUG_STAGE} --seed {DEBUG_SEED} --updates 8")
    if args.command == "primary" and (args.stage, args.updates) != (PRIMARY_STAGE, 64):
        parser.error(f"primary requires exactly --stage {PRIMARY_STAGE} --updates 64")
    if args.command == "primary" and args.seed not in PRIMARY_SEEDS:
        parser.error(f"primary seed must be one of {PRIMARY_SEEDS}")

    exposure: list[dict[str, object]] = []
    residual: list[dict[str, object]] = []
    telemetry_state: dict[str, object] = {"resources_unmeasured": False, "resources_unmeasured_reasons": ()}
    record_root = Path(args.record_root)
    record_root.mkdir(parents=True, exist_ok=True)
    record_path = record_root / f"r02-record-{args.stage}-{args.seed}.json"

    started = datetime.now(timezone.utc)
    try:
        binding = prepare_native_backends()
        native_record = native_identity_record(binding)
        r01 = install_r02(exposure_sink=exposure, telemetry_sink=telemetry_state, residual_sink=residual)
        preflight, preflight_sha = _read_receipt(args.preflight_receipt)
        now = datetime.now(timezone.utc)
        config = r01.BExploreRunConfig(args.stage, args.seed, args.updates)
        config.validate()
        r01.validate_preflight_receipt(preflight, now=now)

        frozen = r01._current_prebuilt_native_artifacts()
        from experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry import (
            ExactStorageContract,
            ProcessTreeTelemetrySink,
        )
        storage = ExactStorageContract(
            frozen_native_artifacts=frozen,
            scratch_not_shared_with_children_or_loaders=True,
            durable_root_is_new_namespace=True,
            durable_writes_use_create_once_recorder_only=True,
            serial_no_child_processes=True,
            source_stage_loads_frozen_native_without_build=True,
        )
        sink = ProcessTreeTelemetrySink(
            preflight_receipt=preflight,
            scratch_root=args.scratch_root,
            durable_root=args.durable_root,
            exact_storage_contract=storage,
        )
        extra: dict[str, object] = {}
        if args.command == "primary":
            extra = {
                "archived_debug_valid_claim_path": Path(args.archived_debug_valid_claim),
                "archived_debug_scientific_root": Path(args.archived_debug_scientific_root),
            }
        result = r01.run_b_explore_runtime(
            config,
            preflight_receipt=preflight,
            telemetry_sink=sink,
            now=now,
            scratch_root=args.scratch_root,
            durable_root=args.durable_root,
            publication_root=args.publication_root,
            **extra,
        )
        finished = datetime.now(timezone.utc)
        record = {
            **r02_recast_record(),
            "stage": args.stage,
            "seed": args.seed,
            "updates": args.updates,
            "namespace": config.namespace,
            "preflight_receipt_sha256": preflight_sha,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "wall_seconds": (finished - started).total_seconds(),
            "native_identity_record": native_record,
            "byte_manifest_record": byte_manifest_record(),
            "resources_unmeasured": bool(telemetry_state["resources_unmeasured"]),
            "resources_unmeasured_reasons": tuple(telemetry_state["resources_unmeasured_reasons"]),
            "exposure_line": tuple(exposure),
            "batch_position_residual": batch_residual_record(residual),
            "publication_root": result["publication_root"],
            "status": "COMPLETE",
        }
        record_path.write_text(_canonical_json_line(record), encoding="utf-8")
        sys.stdout.write(_canonical_json_line({
            "schema": "VNFC_BPCR_R02_EXECUTION_RECEIPT_V1",
            "namespace": config.namespace,
            "record": str(record_path),
            "wall_seconds": record["wall_seconds"],
            "resources_unmeasured": record["resources_unmeasured"],
            "exposure_rows": len(exposure),
            "batch_position_residual_decisions": len(residual),
            "publication_root": result["publication_root"],
        }))
        return 0
    except BaseException as error:  # noqa: BLE001 - the quarantine record must be written
        finished = datetime.now(timezone.utc)
        quarantine = {
            **r02_recast_record(),
            "stage": getattr(args, "stage", None),
            "seed": getattr(args, "seed", None),
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "wall_seconds": (finished - started).total_seconds(),
            "resources_unmeasured": bool(telemetry_state["resources_unmeasured"]),
            "resources_unmeasured_reasons": tuple(telemetry_state["resources_unmeasured_reasons"]),
            "exposure_line": tuple(exposure),
            "batch_position_residual": batch_residual_record(residual),
            "status": "QUARANTINED_INCOMPLETE_ATTEMPT",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        try:
            record_path.write_text(_canonical_json_line(quarantine), encoding="utf-8")
        except OSError:
            pass
        sys.stderr.write(_canonical_json_line({
            "schema": "VNFC_BPCR_R02_CLI_ERROR_V1",
            "error_type": type(error).__name__,
            "message": str(error),
            "record": str(record_path),
        }))
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        return 2


__all__ = [
    "CONFORMANCE_OBJECT",
    "CanonicalOpaqueRankForward",
    "DEBUG_SEED",
    "FROZEN_A0_NATIVE_LITERALS",
    "PRIMARY_SEEDS",
    "PRESENTATION_LAW",
    "R02ContractError",
    "R02_DIAGNOSTIC_FORWARDS",
    "RELABEL_PROBE_LAW",
    "RESOURCE_MEASUREMENT_FAILURES",
    "RUN_REVISION",
    "build_canonical_model_classes",
    "batch_residual_record",
    "byte_manifest_record",
    "canonical_permutation",
    "canonicalize_inputs",
    "install_exposure_line",
    "install_like_for_like_relabel_probe",
    "install_r02",
    "install_serializable_freeze_material",
    "install_resource_telemetry_downgrade",
    "load_r01_runner",
    "native_identity_record",
    "prepare_native_backends",
    "r02_recast_record",
]


if __name__ == "__main__":
    raise SystemExit(main())
