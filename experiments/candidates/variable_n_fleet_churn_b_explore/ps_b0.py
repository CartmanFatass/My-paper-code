"""Source-bound, actual-path PS-B0 presentation diagnostics.

This module deliberately constructs observations through revision-09's
``EpisodeFixture -> NativeInteractiveBatch`` path.  It does not synthesize or
reorder a public tensor after observation construction.  Presentation changes
are fixture inputs and therefore pass through the native observation encoder.

The diagnostic ``null/tie-support`` state is only a support-path probe: null is
legal, at least two physical agents are legal for one token, and every active
row carries its opaque deterministic tie rank.  No equal-logit claim is made.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import empirical_training as _training
from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import native_backend as _native
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import EpisodeFixture, GeneralAgentState
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import (
    DirectSetAR,
    MAPR4,
    initial_learned_availability,
    variable_prefix_mask,
)


ROSTERS = (3, 5, 7)
FAILED_ZONES = (1, 2)
STATE_KINDS = ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie")
PRESENTATIONS = ("canonical", "reverse", "cyclic", "seed_fixed_random")
# Runner address label ``final`` denotes the DEBUG-final checkpoint in PS-B0.
CHECKPOINTS = ("initial", "final")
ARMS = ("MAPR", "DIRECT")

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_PATHS = (
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/fixtures.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_training.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp",
    "experiments/candidates/variable_n_fleet_churn_b_explore/ps_b0.py",
)
_AGENT_TYPES = (
    (1, 1, 2), (2, 0, 2), (3, 1, 1), (4, 0, 1),
    (5, 1, 2), (6, 0, 2), (7, 1, 1), (8, 0, 1),
)
_EXPECTED_FAILED_RANK = {
    (3, 1): 1, (3, 2): 3,
    (5, 1): 1, (5, 2): 5,
    (7, 1): 1, (7, 2): 5,
}


class PSB0ConstructionError(RuntimeError):
    """The actual-path PS-B0 state or comparison could not be constructed."""


class PSB0SourceDriftError(PSB0ConstructionError):
    """A bound Python/native source or artifact changed after construction."""


@dataclass(frozen=True)
class _Snapshot:
    presentation: str
    fixture: EpisodeFixture
    failed_rank: int
    trace: Mapping[str, object]
    inputs: tuple[torch.Tensor, ...]
    origin: str


@dataclass(frozen=True)
class PSB0ActualState:
    roster_size: int
    failed_zone: int
    state_kind: str
    seed: int
    source_identity: Mapping[str, object]
    native_physical_command: tuple[int | None, ...] | None
    snapshots: Mapping[str, _Snapshot]


@dataclass(frozen=True)
class PSB0ActualComparison:
    """Runner-compatible fields plus the complete serializable diagnostic."""

    roster_size: int
    failed_zone: int
    state_kind: str
    presentation: str
    checkpoint: str
    arm: str
    agent_rows_copermuted: bool
    legal_masks_copermuted: bool
    fixed_occupants_copermuted: bool
    opaque_ranks_copermuted: bool
    physical_support_equal: bool
    canonical_physical_command: tuple[int | None, ...]
    inverse_mapped_physical_command: tuple[int | None, ...]
    null_case_present: bool
    fixed_or_acquiring_case_present: bool
    null_action_legal: bool
    legal_agent_candidate_count: int
    diagnostic_target_physical_token: int | None
    predecision_legal_agent_count: int
    opaque_deterministic_tie_ranks_complete: bool
    equal_logit_claim: bool
    presentation_path: str
    canonical_presentation_order: tuple[int, ...]
    tested_presentation_order: tuple[int, ...]
    native_physical_transition_command: tuple[int | None, ...] | None
    canonical_trace: Mapping[str, object]
    tested_trace: Mapping[str, object]
    copermutation_diagnostics: Mapping[str, object]
    score_probability_difference_diagnostics: Mapping[str, object]
    model_identity: Mapping[str, object]
    source_identity: Mapping[str, object]

    @property
    def address(self) -> tuple[object, ...]:
        return (
            self.roster_size, self.failed_zone, self.state_kind,
            self.presentation, self.checkpoint, self.arm,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def state_descriptors() -> tuple[dict[str, object], ...]:
    rows = tuple(
        {"roster_size": n, "failed_zone": zone, "state_kind": kind}
        for n in ROSTERS for zone in FAILED_ZONES for kind in STATE_KINDS
    )
    if len(rows) != 18:
        raise AssertionError("PS-B0 descriptor cardinality differs")
    return rows


def expected_addresses() -> frozenset[tuple[object, ...]]:
    return frozenset(
        (n, zone, kind, presentation, checkpoint, arm)
        for n in ROSTERS for zone in FAILED_ZONES for kind in STATE_KINDS
        for presentation in PRESENTATIONS for checkpoint in CHECKPOINTS for arm in ARMS
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_identity() -> dict[str, object]:
    files = []
    for relative in _SOURCE_PATHS:
        path = _REPOSITORY_ROOT / relative
        if not path.is_file():
            raise PSB0ConstructionError(f"PS-B0 bound source is absent: {relative}")
        files.append({"path": relative, "sha256": _sha256(path)})
    library = _native.require_cpp_batched_backend()
    artifact = Path(vars(library)["_name"]).resolve()
    return {
        "schema": "VNFC_BPCR_BEXP_R01_PS_B0_SOURCE_IDENTITY_V1",
        "files": tuple(files),
        "native": {
            "artifact_path": str(artifact),
            "artifact_sha256": _sha256(artifact),
            "artifact_size": artifact.stat().st_size,
            "build_key": _native.native_build_key(),
            "source_sha256": _native.native_source_sha256(),
            "abi_version": _native.NATIVE_ABI_VERSION,
        },
    }


def _seed_fixed_permutation(ranks: tuple[int, ...], seed: int, n: int, zone: int) -> tuple[int, ...]:
    keyed = sorted(
        ranks,
        key=lambda rank: hashlib.sha256(
            f"VNFC-BEXP-PS-B0/presentation/{seed}/{n}/{zone}/{rank}".encode("ascii")
        ).digest(),
    )
    candidate = tuple(keyed)
    prohibited = {ranks, tuple(reversed(ranks)), ranks[1:] + ranks[:1]}
    if candidate not in prohibited:
        return candidate
    # Pick the first digest-addressed permutation not already used.  This keeps
    # all four named fixture presentations distinct without a mutable RNG.
    permutations = tuple(p for p in itertools.permutations(ranks) if p not in prohibited)
    digest = hashlib.sha256(f"VNFC-BEXP-PS-B0/random-index/{seed}/{n}/{zone}".encode("ascii")).digest()
    return permutations[int.from_bytes(digest[:8], "big") % len(permutations)]


def _presentation_orders(n: int, zone: int, seed: int) -> dict[str, tuple[int, ...]]:
    preloss = tuple(range(1, n + 2))
    failed = _EXPECTED_FAILED_RANK[(n, zone)]
    active = tuple(rank for rank in preloss if rank != failed)
    active_orders = {
        "canonical": active,
        "reverse": tuple(reversed(active)),
        "cyclic": active[1:] + active[:1],
        "seed_fixed_random": _seed_fixed_permutation(active, seed, n, zone),
    }
    if set(active_orders) != set(PRESENTATIONS) or len(set(active_orders.values())) != 4:
        raise PSB0ConstructionError("four post-loss active presentations are not distinct")
    # EpisodeFixture accepts a full pre-loss roster.  Hold the failed executor
    # at one fixed final position so native removal cannot collapse two active
    # presentation labels into the same observation order.
    orders = {name: order + (failed,) for name, order in active_orders.items()}
    return orders


def _fixture(n: int, zone: int, order: tuple[int, ...], *, diagnostic: bool) -> EpisodeFixture:
    agents = tuple(GeneralAgentState(rank, rank, fast, radio) for rank, fast, radio in _AGENT_TYPES[: n + 1])
    demand_1 = [2] * 12
    demand_2 = [2] * 12
    blocked_1 = [1] * 12
    blocked_2 = [1] * 12
    if diagnostic:
        # Prehistory (indices 0..5) is unchanged.  Only the public t=0
        # exogenous surface is changed, through the native fixture path.
        demand_1[6] = demand_2[6] = 1
        blocked_1[6] = blocked_2[6] = 0
    fixture = EpisodeFixture(
        failed_zone=zone,
        agents=agents,
        demand_1=tuple(demand_1), demand_2=tuple(demand_2),
        blocked_1=tuple(blocked_1), blocked_2=tuple(blocked_2),
        post_commands=((None, None, None, None),) * 6,
        post_presentations=(order,) * 6,
    )
    fixture.validate()
    return fixture


def _inputs(trace: Mapping[str, object], fixture: EpisodeFixture, failed_rank: int) -> tuple[torch.Tensor, ...]:
    inputs = _training._model_inputs(trace, fixture, failed_rank)
    if len(inputs) != 6 or any(tensor.device.type != "cpu" for tensor in inputs):
        raise PSB0ConstructionError("production model-input conversion differed")
    return tuple(tensor.detach().clone() for tensor in inputs)


def _max_legal_agents(inputs: tuple[torch.Tensor, ...]) -> int:
    legal = inputs[3][0].bool()
    return max(int(legal[:, token].sum().item()) for token in range(4))


def _capture_cell(
    n: int,
    zone: int,
    seed: int,
    *,
    diagnostic: bool,
    record_call: Callable[[int, int, bool, str], None],
) -> tuple[dict[str, _Snapshot], tuple[int | None, ...] | None]:
    orders = _presentation_orders(n, zone, seed)
    surfaces = tuple(_fixture(n, zone, orders[name], diagnostic=diagnostic) for name in PRESENTATIONS)
    # R01 production admission is frozen at B>=8.  Each of the four actual
    # presentation fixtures is duplicated, and duplicates must be byte/value
    # exact at every native boundary.  Only four unique surfaces are returned.
    fixtures = tuple(fixture for fixture in surfaces for _ in range(2))
    if len(fixtures) != 8:
        raise AssertionError("PS-B0 native production width differs")
    batch = _native.NativeInteractiveBatch(fixtures)
    try:
        initial_rows = batch.initial
        record_call(n, zone, diagnostic, "reset")
        if any(initial_rows[index] != initial_rows[index + 1] for index in range(0, 8, 2)):
            raise PSB0ConstructionError(f"N={n}, zone={zone}: duplicate reset rows differ")
        surface_initial = initial_rows[::2]
        failed = {int(row["failed_rank"]) for row in surface_initial}
        if len(failed) != 1:
            raise PSB0ConstructionError(f"N={n}, zone={zone}: presentation changed failed executor")
        failed_rank = next(iter(failed))
        expected_failed = _EXPECTED_FAILED_RANK[(n, zone)]
        if failed_rank != expected_failed:
            raise PSB0ConstructionError(
                f"N={n}, zone={zone}: native failed rank {failed_rank} differs from frozen fixture mapping {expected_failed}"
            )
        t0 = {
            name: _Snapshot(
                name, fixture, failed_rank, row["next_observation"],
                _inputs(row["next_observation"], fixture, failed_rank),
                "native_interactive_reset_t0",
            )
            for name, fixture, row in zip(PRESENTATIONS, surfaces, surface_initial)
        }
        if diagnostic:
            support = tuple(_diagnostic_predecision_support(snapshot) for snapshot in t0.values())
            if min(int(row["target_legal_agent_count"]) for row in support) < 2 or not all(row["target_null_legal"] for row in support):
                raise PSB0ConstructionError(
                    f"N={n}, zone={zone}: reachable diagnostic support has fewer than two legal agents"
                )
            return t0, None

        bcrh = batch.bcrh(include_candidate_records=False)
        record_call(n, zone, diagnostic, "bcrh")
        if any(bcrh[index] != bcrh[index + 1] for index in range(0, 8, 2)):
            raise PSB0ConstructionError(f"N={n}, zone={zone}: duplicate BCRH rows differ")
        commands = {tuple(row["scorer_command"]) for row in bcrh}
        if len(commands) != 1:
            raise PSB0ConstructionError(f"N={n}, zone={zone}: native physical transition command changed by presentation")
        command = next(iter(commands))
        stepped = batch.step((command,) * len(fixtures))
        record_call(n, zone, diagnostic, "step")
        if any(stepped[index] != stepped[index + 1] for index in range(0, 8, 2)):
            raise PSB0ConstructionError(f"N={n}, zone={zone}: duplicate step rows differ")
        surface_stepped = stepped[::2]
        later: dict[str, _Snapshot] = {}
        for name, fixture, row in zip(PRESENTATIONS, surfaces, surface_stepped):
            trace = row["next_observation"]
            if trace is None:
                raise PSB0ConstructionError(f"N={n}, zone={zone}: one native step unexpectedly terminated")
            later[name] = _Snapshot(
                name, fixture, failed_rank, trace, _inputs(trace, fixture, failed_rank),
                "native_interactive_t0_plus_one_identical_physical_bcrh_command",
            )
        if not all(any(int(value) in (1, 2) for value in snapshot.trace["token_state"]) for snapshot in later.values()):
            raise PSB0ConstructionError(f"N={n}, zone={zone}: reachable later state lacks acquiring/fixed occupant")
        return {**{f"t0::{key}": value for key, value in t0.items()}, **{f"later::{key}": value for key, value in later.items()}}, command
    finally:
        batch.close()


def _physical_rows(snapshot: _Snapshot) -> tuple[dict[int, tuple[float, ...]], dict[int, tuple[int, ...]], dict[int, int]]:
    agents, _, _, legal, _, opaque = snapshot.inputs
    epoch = int(snapshot.trace["epoch"])
    presented = tuple(rank for rank in snapshot.fixture.post_presentations[epoch] if rank != snapshot.failed_rank)
    agent_rows = {rank: tuple(float(x) for x in agents[0, row].tolist()) for row, rank in enumerate(presented)}
    legal_rows = {rank: tuple(int(x) for x in legal[0, row].tolist()) for row, rank in enumerate(presented)}
    opaque_by_rank = {rank: int(opaque[0, row].item()) for row, rank in enumerate(presented)}
    return agent_rows, legal_rows, opaque_by_rank  # type: ignore[return-value]


def _fixed_physical(snapshot: _Snapshot) -> tuple[int | None, ...]:
    fixed = snapshot.inputs[4][0]
    epoch = int(snapshot.trace["epoch"])
    presented = tuple(rank for rank in snapshot.fixture.post_presentations[epoch] if rank != snapshot.failed_rank)
    return tuple(None if int(row) < 0 else presented[int(row)] for row in fixed)


def _diagnostic_predecision_support(snapshot: _Snapshot) -> dict[str, object]:
    """Select the strongest target token before any autoregressive choice.

    This is intentionally distinct from later prefix-conditioned availability.
    It asks whether the actual state exposes null plus at least two legal agents
    at one named token before the decoder has consumed any variable candidate.
    """
    _, _, _, legal, fixed, _ = snapshot.inputs
    epoch = int(snapshot.trace["epoch"])
    presented = tuple(rank for rank in snapshot.fixture.post_presentations[epoch] if rank != snapshot.failed_rank)
    n = len(presented)
    available = initial_learned_availability(fixed, n)[0]
    token_order = (0, 1, 2, 3) if snapshot.fixture.failed_zone == 1 else (2, 3, 0, 1)
    candidates = []
    for model_token, physical_token in enumerate(token_order):
        occupant = int(fixed[0, model_token].item())
        if occupant >= 0:
            support = (presented[occupant],)
            null_legal = False
        else:
            support = tuple(
                presented[row]
                for row in range(n)
                if bool(available[row]) and bool(legal[0, row, model_token])
            )
            null_legal = True
        candidates.append({
            "model_token": model_token,
            "physical_token": physical_token,
            "legal_physical_agent_ranks": tuple(sorted(support)),
            "legal_agent_count": len(support),
            "null_legal": null_legal,
        })
    eligible = tuple(row for row in candidates if row["null_legal"])
    if not eligible:
        raise PSB0ConstructionError("diagnostic state has no pre-decision null-legal token")
    target = min(eligible, key=lambda row: (-int(row["legal_agent_count"]), int(row["physical_token"])))
    return {
        "semantics": "actual_state_predecision_before_any_autoregressive_candidate_consumption",
        "tokens": tuple(candidates),
        "target_model_token": target["model_token"],
        "target_physical_token": target["physical_token"],
        "target_legal_physical_agent_ranks": target["legal_physical_agent_ranks"],
        "target_legal_agent_count": target["legal_agent_count"],
        "target_null_legal": target["null_legal"],
    }


def _hex(value: torch.Tensor) -> str:
    return float(value.item()).hex()


def _physical_command(relative: Sequence[int], snapshot: _Snapshot) -> tuple[int | None, ...]:
    epoch = int(snapshot.trace["epoch"])
    presented = tuple(rank for rank in snapshot.fixture.post_presentations[epoch] if rank != snapshot.failed_rank)
    n = len(presented)
    rel = tuple(None if int(row) == n else presented[int(row)] for row in relative)
    return rel if snapshot.fixture.failed_zone == 1 else (rel[2], rel[3], rel[0], rel[1])


def _model_trace(model: MAPR4, snapshot: _Snapshot) -> tuple[dict[str, object], tuple[int | None, ...]]:
    agents, zones, globals_, legal, fixed, opaque = snapshot.inputs
    with torch.no_grad():
        encoded, summary = model.encode(agents, zones, globals_)
        batch, n, _ = encoded.shape
        if batch != 1:
            raise PSB0ConstructionError("PS-B0 trace must be a scalar actual observation")
        available = initial_learned_availability(fixed, n)
        prefix_sum = torch.zeros((1, 64), dtype=torch.float64)
        prefix_max = torch.zeros((1, 64), dtype=torch.float64)
        prefix_has = torch.zeros((1, 1), dtype=torch.bool)
        commands: list[torch.Tensor] = []
        probability_rows: list[torch.Tensor] = []
        diagnostics = []
        epoch = int(snapshot.trace["epoch"])
        presented = tuple(rank for rank in snapshot.fixture.post_presentations[epoch] if rank != snapshot.failed_rank)
        token_order = (0, 1, 2, 3) if snapshot.fixture.failed_zone == 1 else (2, 3, 0, 1)
        for token in range(4):
            base_logits, hidden = model.candidate_logits(encoded, summary, token)
            adjusted = base_logits + model.prefix_adjustment(summary, hidden, prefix_sum, prefix_max)
            support = torch.cat((available & legal[:, :, token].bool(), torch.ones((1, 1), dtype=torch.bool)), 1)
            occupant = fixed[:, token]
            has_fixed = occupant >= 0
            support[has_fixed] = False
            support[has_fixed, occupant[has_fixed]] = True
            masked = adjusted.masked_fill(~support, -torch.inf)
            probabilities = torch.softmax(masked, 1)
            tie = torch.cat((opaque, torch.full((1, 1), 2**30, dtype=opaque.dtype)), 1)
            best = masked.max(1, keepdim=True).values
            choice = torch.where(masked == best, tie, torch.iinfo(tie.dtype).max).argmin(1)
            candidates: tuple[int | None, ...] = presented + (None,)
            diagnostics.append({
                "model_token": token,
                "physical_token": token_order[token],
                "prefix_physical_choices": tuple(
                    None if int(row.item()) == n else presented[int(row.item())] for row in commands
                ),
                "candidates": tuple({
                    "physical_rank": candidate,
                    "available_before": candidate is None or bool(available[0, index]),
                    "environment_legal": candidate is None or bool(legal[0, index, token]),
                    "masked_support": bool(support[0, index]),
                    "base_logit_binary64": _hex(base_logits[0, index]),
                    "prefix_conditioned_logit_binary64": _hex(adjusted[0, index]),
                    "masked_logit_binary64": _hex(masked[0, index]) if bool(support[0, index]) else None,
                    "probability_binary64": _hex(probabilities[0, index]),
                    "opaque_tie_rank": (2**30 if candidate is None else int(opaque[0, index])),
                } for index, candidate in enumerate(candidates)),
                "selected_physical_rank": None if int(choice.item()) == n else presented[int(choice.item())],
            })
            commands.append(choice)
            probability_rows.append(probabilities)
            chosen_agent = choice < n
            available[torch.arange(1)[chosen_agent], choice[chosen_agent]] = False
            chosen_hidden = hidden[torch.arange(1), choice]
            nonnull = variable_prefix_mask(fixed, token, choice, n)[:, None]
            prefix_sum = prefix_sum + torch.where(nonnull, chosen_hidden, torch.zeros_like(chosen_hidden))
            next_max = torch.where(prefix_has, torch.maximum(prefix_max, chosen_hidden), chosen_hidden)
            prefix_max = torch.where(nonnull, next_max, prefix_max)
            prefix_has = prefix_has | nonnull
        traced_commands = torch.stack(commands, 1)
        traced_probabilities = torch.stack(probability_rows, 1)
        forward = model(*snapshot.inputs)
        if not torch.equal(forward["command"], traced_commands) or not torch.equal(forward["token_probabilities"], traced_probabilities):
            raise PSB0ConstructionError("public-method prefix trace differs from exact model forward")
        command = _physical_command(tuple(int(x) for x in traced_commands[0]), snapshot)
        return {
            "origin": snapshot.origin,
            "native_epoch": int(snapshot.trace["epoch"]),
            "native_token_state": tuple(int(x) for x in snapshot.trace["token_state"]),
            "native_token_elapsed": tuple(int(x) for x in snapshot.trace["token_elapsed"]),
            "fixed_physical_occupants_model_order": _fixed_physical(snapshot),
            "tokens": tuple(diagnostics),
            "forward_command_rows": tuple(int(x) for x in forward["command"][0].tolist()),
            "inverse_mapped_physical_command": command,
            "forward_verified_exact": True,
            "forcing": "deterministic_opaque_tie_decoder",
        }, command


def _model_identity(model: MAPR4, arm: str) -> dict[str, object]:
    expected = MAPR4 if arm == "MAPR" else DirectSetAR
    if type(model) is not expected:
        raise PSB0ConstructionError(f"{arm} PS-B0 model class differs")
    digest = hashlib.sha256(b"VNFC-BEXP-PS-B0-MODEL-v1\0")
    inventory = []
    for name, tensor in sorted(model.state_dict().items()):
        value = tensor.detach().cpu().contiguous()
        if value.dtype != torch.float64 or not bool(torch.isfinite(value).all()):
            raise PSB0ConstructionError(f"{arm} model tensor is not finite CPU binary64: {name}")
        raw = value.numpy().tobytes(order="C")
        digest.update(name.encode("utf-8")); digest.update(str(tuple(value.shape)).encode("ascii")); digest.update(raw)
        inventory.append({"name": name, "shape": tuple(value.shape), "sha256": hashlib.sha256(raw).hexdigest()})
    return {"arm": arm, "class": type(model).__name__, "state_sha256": digest.hexdigest(), "tensors": tuple(inventory)}


def _aligned_score_probability_differences(
    canonical: Mapping[str, object],
    tested: Mapping[str, object],
) -> dict[str, object]:
    canonical_tokens = canonical["tokens"]
    tested_tokens = tested["tokens"]
    if len(canonical_tokens) != 4 or len(tested_tokens) != 4:  # type: ignore[arg-type]
        raise PSB0ConstructionError("score/probability trace token inventory differs")
    rows = []
    maximum_probability_difference = 0.0
    score_fields = (
        "base_logit_binary64",
        "prefix_conditioned_logit_binary64",
        "masked_logit_binary64",
        "probability_binary64",
    )
    for canonical_token, tested_token in zip(canonical_tokens, tested_tokens):  # type: ignore[arg-type]
        if canonical_token["physical_token"] != tested_token["physical_token"]:
            raise PSB0ConstructionError("physical token alignment differs")
        canonical_by_rank = {row["physical_rank"]: row for row in canonical_token["candidates"]}
        tested_by_rank = {row["physical_rank"]: row for row in tested_token["candidates"]}
        if set(canonical_by_rank) != set(tested_by_rank):
            raise PSB0ConstructionError("physical candidate alignment differs")
        candidates = []
        for rank in sorted(canonical_by_rank, key=lambda value: (value is None, -1 if value is None else int(value))):
            left, right = canonical_by_rank[rank], tested_by_rank[rank]
            differences: dict[str, object] = {}
            for field in score_fields:
                left_value, right_value = left[field], right[field]
                if left_value is None or right_value is None:
                    difference = None if left_value is None and right_value is None else "SUPPORT_MISMATCH"
                else:
                    difference_value = float.fromhex(str(right_value)) - float.fromhex(str(left_value))
                    difference = difference_value.hex()
                    if field == "probability_binary64":
                        maximum_probability_difference = max(maximum_probability_difference, abs(difference_value))
                differences[field.replace("_binary64", "_difference_binary64")] = difference
            candidates.append({
                "physical_rank": rank,
                "canonical": {field: left[field] for field in score_fields},
                "tested": {field: right[field] for field in score_fields},
                "differences": differences,
                "support_equal": left["masked_support"] == right["masked_support"],
                "opaque_tie_rank_equal": left["opaque_tie_rank"] == right["opaque_tie_rank"],
            })
        rows.append({
            "physical_token": canonical_token["physical_token"],
            "canonical_prefix_physical_choices": canonical_token["prefix_physical_choices"],
            "tested_prefix_physical_choices": tested_token["prefix_physical_choices"],
            "candidates_by_physical_rank": tuple(candidates),
        })
    return {
        "schema": "VNFC_BPCR_BEXP_R01_PS_B0_ALIGNED_SCORE_PROBABILITY_DIFF_V1",
        "alignment": "physical_token_then_physical_candidate_rank",
        "tokens": tuple(rows),
        "maximum_absolute_probability_difference_binary64": maximum_probability_difference.hex(),
        "physical_command_equal": canonical["inverse_mapped_physical_command"] == tested["inverse_mapped_physical_command"],
    }


class ActualPathPSB0Adapter:
    """Built-in adapter consumed by the R01 post-training DEBUG gate."""

    def __init__(self) -> None:
        self._cell_cache: dict[tuple[int, int, int, bool], tuple[dict[str, _Snapshot], tuple[int | None, ...] | None]] = {}
        self._host_calls: list[dict[str, object]] = []

    def _record_host_call(self, n: int, zone: int, diagnostic: bool, operation: str) -> None:
        if operation not in ("reset", "bcrh", "step"):
            raise AssertionError("PS-B0 native operation inventory differs")
        self._host_calls.append({
            "ordinal": len(self._host_calls) + 1,
            "roster_size": n,
            "failed_zone": zone,
            "state_family": "diagnostic" if diagnostic else "t0_and_later",
            "operation": operation,
            "batch_width": 8,
            "unique_presentation_surfaces": 4,
            "duplicates_per_surface": 2,
            "duplicate_exact_required": True,
            "primary_only": True,
            "result_bearing": False,
        })

    @property
    def host_call_ledger(self) -> dict[str, object]:
        rows = tuple(dict(row) for row in self._host_calls)
        return {
            "schema": "VNFC_BPCR_BEXP_R01_PS_B0_PRIMARY_HOST_CALL_LEDGER_V1",
            "records": rows,
            "primary_only_host_calls": len(rows),
            "reset_calls": sum(row["operation"] == "reset" for row in rows),
            "bcrh_calls": sum(row["operation"] == "bcrh" for row in rows),
            "step_calls": sum(row["operation"] == "step" for row in rows),
            "batch_widths": tuple(sorted({int(row["batch_width"]) for row in rows})),
            "scientific_values_exposed": False,
        }

    def require_complete_host_call_ledger(self) -> dict[str, object]:
        ledger = self.host_call_ledger
        expected_cells = {(n, zone) for n in ROSTERS for zone in FAILED_ZONES}
        actual_non_diagnostic = {
            (int(row["roster_size"]), int(row["failed_zone"]))
            for row in ledger["records"]  # type: ignore[union-attr]
            if row["state_family"] == "t0_and_later" and row["operation"] == "reset"
        }
        actual_diagnostic = {
            (int(row["roster_size"]), int(row["failed_zone"]))
            for row in ledger["records"]  # type: ignore[union-attr]
            if row["state_family"] == "diagnostic" and row["operation"] == "reset"
        }
        if (
            actual_non_diagnostic != expected_cells or actual_diagnostic != expected_cells
            or ledger["primary_only_host_calls"] != 24
            or ledger["reset_calls"] != 12 or ledger["bcrh_calls"] != 6 or ledger["step_calls"] != 6
            or ledger["batch_widths"] != (8,)
        ):
            raise PSB0ConstructionError("PS-B0 primary-only host-call ledger is incomplete")
        return ledger

    def build_support_path_state(self, descriptor: Mapping[str, object], seed: int) -> PSB0ActualState:
        expected = {"roster_size", "failed_zone", "state_kind"}
        if set(descriptor) != expected:
            raise PSB0ConstructionError("PS-B0 descriptor field inventory differs")
        n, zone, kind = int(descriptor["roster_size"]), int(descriptor["failed_zone"]), str(descriptor["state_kind"])
        if n not in ROSTERS or zone not in FAILED_ZONES or kind not in STATE_KINDS:
            raise PSB0ConstructionError("PS-B0 descriptor value differs")
        diagnostic = kind == "diagnostic_null_tie"
        key = (n, zone, int(seed), diagnostic)
        if key not in self._cell_cache:
            self._cell_cache[key] = _capture_cell(
                n, zone, int(seed), diagnostic=diagnostic, record_call=self._record_host_call
            )
        captured, command = self._cell_cache[key]
        prefix = "later::" if kind == "later_fixed_or_acquiring" else ("" if diagnostic else "t0::")
        snapshots = {name: captured[prefix + name] for name in PRESENTATIONS}
        return PSB0ActualState(n, zone, kind, int(seed), _source_identity(), command, snapshots)

    def compare_presentations(
        self,
        state: PSB0ActualState,
        presentation: str,
        checkpoint: str,
        arm: str,
        model: object,
        rng: object,
    ) -> PSB0ActualComparison:
        del rng  # presentation randomness was frozen in the actual fixture from state.seed
        if presentation not in PRESENTATIONS or checkpoint not in CHECKPOINTS or arm not in ARMS:
            raise PSB0ConstructionError("PS-B0 comparison address differs")
        current = _source_identity()
        if current != state.source_identity:
            raise PSB0SourceDriftError("PS-B0 source/native identity drifted after actual-state construction")
        canonical = state.snapshots["canonical"]
        tested = state.snapshots[presentation]
        typed_model = model
        identity = _model_identity(typed_model, arm)  # type: ignore[arg-type]
        canonical_diagnostic, canonical_command = _model_trace(typed_model, canonical)  # type: ignore[arg-type]
        tested_diagnostic, tested_command = _model_trace(typed_model, tested)  # type: ignore[arg-type]
        if state.state_kind == "diagnostic_null_tie":
            canonical_predecision = _diagnostic_predecision_support(canonical)
            tested_predecision = _diagnostic_predecision_support(tested)
            canonical_diagnostic = {**canonical_diagnostic, "diagnostic_predecision_support": canonical_predecision}
            tested_diagnostic = {**tested_diagnostic, "diagnostic_predecision_support": tested_predecision}
        else:
            canonical_predecision = tested_predecision = None
        canonical_agents, canonical_legal, canonical_opaque = _physical_rows(canonical)
        tested_agents, tested_legal, tested_opaque = _physical_rows(tested)
        canonical_fixed, tested_fixed = _fixed_physical(canonical), _fixed_physical(tested)
        canonical_support = tuple(
            tuple(sorted(
                (row["physical_rank"] for row in token["candidates"] if row["masked_support"]),
                key=lambda rank: (rank is None, -1 if rank is None else int(rank)),
            ))
            for token in canonical_diagnostic["tokens"]  # type: ignore[index]
        )
        tested_support = tuple(
            tuple(sorted(
                (row["physical_rank"] for row in token["candidates"] if row["masked_support"]),
                key=lambda rank: (rank is None, -1 if rank is None else int(rank)),
            ))
            for token in tested_diagnostic["tokens"]  # type: ignore[index]
        )
        canonical_predecision_support = (
            tuple(canonical_predecision["target_legal_physical_agent_ranks"])
            if canonical_predecision is not None else ()
        )
        tested_predecision_support = (
            tuple(tested_predecision["target_legal_physical_agent_ranks"])
            if tested_predecision is not None else ()
        )
        max_legal = int(tested_predecision["target_legal_agent_count"]) if tested_predecision is not None else 0
        opaque_values = tuple(tested_opaque.values())
        complete_opaque = len(opaque_values) == state.roster_size and len(set(opaque_values)) == state.roster_size
        null_legal = bool(tested_predecision["target_null_legal"]) if tested_predecision is not None else False
        later_present = state.state_kind == "later_fixed_or_acquiring" and any(int(x) in (1, 2) for x in tested.trace["token_state"])
        return PSB0ActualComparison(
            roster_size=state.roster_size, failed_zone=state.failed_zone, state_kind=state.state_kind,
            presentation=presentation, checkpoint=checkpoint, arm=arm,
            agent_rows_copermuted=canonical_agents == tested_agents,
            legal_masks_copermuted=canonical_legal == tested_legal,
            fixed_occupants_copermuted=canonical_fixed == tested_fixed,
            opaque_ranks_copermuted=canonical_opaque == tested_opaque,
            physical_support_equal=(
                canonical_support == tested_support
                and canonical_predecision_support == tested_predecision_support
                and (
                    canonical_predecision is None or tested_predecision is None
                    or canonical_predecision["target_physical_token"] == tested_predecision["target_physical_token"]
                )
            ),
            canonical_physical_command=canonical_command,
            inverse_mapped_physical_command=tested_command,
            null_case_present=state.state_kind == "diagnostic_null_tie",
            fixed_or_acquiring_case_present=later_present,
            null_action_legal=null_legal,
            legal_agent_candidate_count=max_legal,
            diagnostic_target_physical_token=(
                int(tested_predecision["target_physical_token"])
                if tested_predecision is not None else None
            ),
            predecision_legal_agent_count=max_legal,
            opaque_deterministic_tie_ranks_complete=complete_opaque,
            equal_logit_claim=False,
            presentation_path="EpisodeFixture.post_presentations -> NativeInteractiveBatch -> native gobservation",
            canonical_presentation_order=tuple(
                rank for rank in canonical.fixture.post_presentations[int(canonical.trace["epoch"])]
                if rank != canonical.failed_rank
            ),
            tested_presentation_order=tuple(
                rank for rank in tested.fixture.post_presentations[int(tested.trace["epoch"])]
                if rank != tested.failed_rank
            ),
            native_physical_transition_command=state.native_physical_command,
            canonical_trace=canonical_diagnostic, tested_trace=tested_diagnostic,
            copermutation_diagnostics={
                "canonical": {
                    "agent_rows_by_physical_rank": canonical_agents,
                    "legal_masks_by_physical_rank": canonical_legal,
                    "fixed_occupants_physical": canonical_fixed,
                    "opaque_ranks_by_physical_rank": canonical_opaque,
                    "prefix_conditioned_physical_support": canonical_support,
                    "diagnostic_predecision_target_support": canonical_predecision_support,
                },
                "tested": {
                    "agent_rows_by_physical_rank": tested_agents,
                    "legal_masks_by_physical_rank": tested_legal,
                    "fixed_occupants_physical": tested_fixed,
                    "opaque_ranks_by_physical_rank": tested_opaque,
                    "prefix_conditioned_physical_support": tested_support,
                    "diagnostic_predecision_target_support": tested_predecision_support,
                },
            },
            score_probability_difference_diagnostics={
                "deterministic_decoder": _aligned_score_probability_differences(
                    canonical_diagnostic, tested_diagnostic
                ),
                "diagnostic_support_semantics": (
                    "actual_state_predecision_target_token"
                    if tested_predecision is not None else None
                ),
            },
            model_identity=identity, source_identity=state.source_identity,
        )


def build_all_comparisons(
    models_by_checkpoint: Mapping[str, Mapping[str, object]],
    *, seed: int,
    adapter: ActualPathPSB0Adapter | None = None,
) -> tuple[PSB0ActualComparison, ...]:
    if set(models_by_checkpoint) != set(CHECKPOINTS) or any(set(models_by_checkpoint[key]) != set(ARMS) for key in CHECKPOINTS):
        raise PSB0ConstructionError("PS-B0 checkpoint/arm model inventory differs")
    actual = adapter or ActualPathPSB0Adapter()
    rows = []
    for descriptor in state_descriptors():
        state = actual.build_support_path_state(descriptor, seed)
        for presentation in PRESENTATIONS:
            for checkpoint in CHECKPOINTS:
                for arm in ARMS:
                    rows.append(actual.compare_presentations(state, presentation, checkpoint, arm, models_by_checkpoint[checkpoint][arm], None))
    materialized = tuple(rows)
    if len(materialized) != 288 or {row.address for row in materialized} != expected_addresses():
        raise PSB0ConstructionError("PS-B0 built comparison cardinality/address inventory differs")
    actual.require_complete_host_call_ledger()
    return materialized


__all__ = [
    "ActualPathPSB0Adapter", "PSB0ActualComparison", "PSB0ActualState",
    "PSB0ConstructionError", "PSB0SourceDriftError", "build_all_comparisons",
    "expected_addresses", "state_descriptors",
]
