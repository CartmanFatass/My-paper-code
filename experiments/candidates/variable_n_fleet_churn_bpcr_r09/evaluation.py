"""Exact revision-09 evaluation execution and replicate-first reduction.

The public coordinator in :mod:`services` always uses the complete frozen
panel. This module contains no entropy source, controller extension point, or Python
environment fallback. Its only smaller-plan seam is protected by a private
construction-test seal and is never reached by the production runner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import copy
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch
import zlib

from .association import row_cut
from .branch_reducer import derive_branch_flags, reduce_branches
from .contracts import canonical_json_bytes
from .empirical_contract import LEARNED_ARMS, PANEL_COUNTS, REPLICATE_ROLES
from .empirical_training import _model_inputs, make_optimizer
from .fixtures import EpisodeFixture
from .frontier import (
    AtomicFrontier,
    CATEGORY_CARDINALITIES,
    COMPLETE_CATEGORIES,
    CheckpointReceipt,
    ValidatedCheckpointBarrier,
    FrontierError,
)
from .inference import family_intervals
from .lifecycle import EvidenceLifecycleError, write_once
from .native_backend import NativeInteractiveBatch
from .rng import EmpiricalRNG, address
from .torch_models import DirectSetAR, MAPR4


class EvaluationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PanelPlan:
    validation: tuple[tuple[str, str, int, int, int, int], ...]
    conclusion: tuple[tuple[str, str, int, int], ...]
    full: bool

    def validate(self) -> None:
        if not self.validation or not self.conclusion:
            raise EvaluationError("evaluation plan is empty")
        if self.full:
            required_validation = {
                (role, arm, checkpoint, roster, zone, row)
                for role in REPLICATE_ROLES
                for arm in LEARNED_ARMS
                for checkpoint in (0, 256)
                for roster in (3, 5)
                for zone in (1, 2)
                for row in range(32)
            }
            required_conclusion = {
                (role, arm, zone, row)
                for role in REPLICATE_ROLES
                for arm in ("MAPR", "DIRECT", "BCRH", "CUT")
                for zone in (1, 2)
                for row in range(32)
            }
            if set(self.validation) != required_validation or len(self.validation) != 8192:
                raise EvaluationError("complete validation plan differs")
            if set(self.conclusion) != required_conclusion or len(self.conclusion) != 4096:
                raise EvaluationError("complete conclusion plan differs")


@dataclass(frozen=True)
class LoadedSlot:
    receipt: CheckpointReceipt
    initial_model: MAPR4 | DirectSetAR
    final_model: MAPR4 | DirectSetAR


@dataclass(frozen=True)
class AtomicCategoryPayload:
    logical_cardinality: int
    value: object


_CONSTRUCTION_TEST_SEAL = object()


def full_panel_plan() -> PanelPlan:
    from .services import conclusion_addresses, validation_addresses

    plan = PanelPlan(validation_addresses(), conclusion_addresses(), True)
    plan.validate()
    return plan


def _physical_command(
    relative: Sequence[int | torch.Tensor], fixture: EpisodeFixture, failed: int, epoch: int
) -> tuple[int | None, ...]:
    roster = len(fixture.agents) - 1
    presented = tuple(rank for rank in fixture.post_presentations[epoch] if rank != failed)
    command = tuple(None if int(item) == roster else presented[int(item)] for item in relative)
    return command if fixture.failed_zone == 1 else (command[2], command[3], command[0], command[1])


def _permuted_inputs(inputs: tuple[torch.Tensor, ...], permutation: Sequence[int]) -> tuple[torch.Tensor, ...]:
    agents, zones, globals_, legal, fixed, opaque = inputs
    p = tuple(int(item) for item in permutation)
    n = agents.shape[1]
    if sorted(p) != list(range(n)):
        raise EvaluationError("consistent-relabel permutation differs")
    inverse = {old: new for new, old in enumerate(p)}
    remapped_fixed = fixed.clone()
    for token in range(4):
        if int(fixed[0, token]) >= 0:
            remapped_fixed[0, token] = inverse[int(fixed[0, token])]
    return agents[:, p], zones, globals_, legal[:, p], remapped_fixed, opaque[:, p]


def _consistent_relabel(
    model: MAPR4,
    inputs: tuple[torch.Tensor, ...],
    reference: torch.Tensor,
    permutation: Sequence[int],
) -> bool:
    permuted = _permuted_inputs(inputs, permutation)
    n = permuted[0].shape[1]
    output = model(*permuted)["command"][0]
    mapped = tuple(n if int(item) == n else int(permutation[int(item)]) for item in output)
    return mapped == tuple(int(item) for item in reference)


def _decode_score_table(
    score_rows: np.ndarray,
    null_scores: np.ndarray,
    legal: torch.Tensor,
    fixed: torch.Tensor,
    opaque: torch.Tensor,
) -> tuple[int, int, int, int]:
    rows = np.asarray(score_rows, dtype=np.float64)
    null = np.asarray(null_scores, dtype=np.float64)
    n = rows.shape[0]
    if rows.shape != (n, 4) or null.shape != (4,):
        raise EvaluationError("CUT score table shape differs")
    available = set(range(n))
    command: list[int] = []
    for token in range(4):
        fixed_row = int(fixed[token])
        if fixed_row >= 0:
            if fixed_row not in available:
                raise EvaluationError("CUT fixed occupant repeats")
            choice = fixed_row
        else:
            candidates = [row for row in available if bool(legal[row, token])]
            best_score = null[token]
            choice = n
            best_rank = 2**31 - 1
            for row in candidates:
                score = rows[row, token]
                rank = int(opaque[row])
                if score > best_score or (score == best_score and rank < best_rank):
                    best_score, best_rank, choice = score, rank, row
        command.append(choice)
        if choice < n:
            available.remove(choice)
    return tuple(command)  # type: ignore[return-value]


def _trace_record(
    observation: Mapping[str, object],
    applied: Mapping[str, object],
    issued_command: Sequence[int | None],
    relabel_ok: bool,
    **extra: object,
) -> dict[str, object]:
    return {
        "observation": dict(observation),
        "issued_command": tuple(issued_command),
        "applied": dict(applied),
        "consistent_relabel": bool(relabel_ok),
        **extra,
    }


def _compact_interactive_bcrh(row: Mapping[str, object]) -> dict[str, object]:
    records = tuple(row["candidate_records"])  # type: ignore[arg-type]
    raw = bytearray()
    for record in records:
        command = tuple(255 if item is None else int(item) for item in record["command"])
        if len(command) != 4 or not bool(record["exact_match"]):
            raise EvaluationError("interactive BCRH candidate record differs")
        raw.extend(bytes((*command, 1)))
    compressed = zlib.compress(bytes(raw), level=9)
    return {
        **{key: value for key, value in row.items() if key != "candidate_records"},
        "candidate_records": {
            "schema": "VNFC_BPCR_R09_INTERACTIVE_BCRH_CANDIDATES_V1",
            "record_count": len(records),
            "record_bytes": 5,
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
            "codec": "zlib-level9-wbits15-no-dictionary",
            "payload_base64": base64.b64encode(compressed).decode("ascii"),
        },
    }


def run_learned_batch(
    fixtures: Sequence[EpisodeFixture],
    model: MAPR4 | DirectSetAR,
    *,
    direct: bool,
    mapr_relabel_model: MAPR4,
    relabel_permutations: Sequence[Sequence[Sequence[int]]],
    action_sensitivity: bool = False,
) -> tuple[dict[str, object], ...]:
    materialized = tuple(fixtures)
    if len(materialized) < 8:
        raise EvaluationError("native evaluation batches require B>=8")
    if len(relabel_permutations) != 6 or any(len(rows) != len(materialized) for rows in relabel_permutations):
        raise EvaluationError("relabel schedule shape differs")
    model.eval(); mapr_relabel_model.eval()
    batch = NativeInteractiveBatch(materialized)
    audits = [
        {"traces": [], "residual_active": [], "residual_change": [], "relabel_ok": True, "action_sensitive": False, "sensitivity": None}
        for _ in materialized
    ]
    zero = copy.deepcopy(model) if direct else None
    if zero is not None:
        with torch.no_grad():
            zero.p("residual.out.weight").zero_()
            zero.p("residual.out.bias").zero_()
        zero.eval()
    try:
        if action_sensitivity:
            sensitivity = batch.sensitivity()
            for i, row in enumerate(sensitivity):
                audits[i]["action_sensitive"] = bool(row["sensitive"])
                audits[i]["sensitivity"] = row
        observations = tuple(row["next_observation"] for row in batch.initial)
        failed = tuple(int(row["failed_rank"]) for row in batch.initial)
        rows: tuple[dict[str, object], ...] = ()
        with torch.no_grad():
            for epoch in range(6):
                inputs = [_model_inputs(obs, fixture, fr) for obs, fixture, fr in zip(observations, materialized, failed)]
                stacked = tuple(torch.cat([item[j] for item in inputs], 0) for j in range(6))
                out = model(*stacked)
                reference = out if isinstance(model, MAPR4) and not direct else mapr_relabel_model(*stacked)
                relabel = tuple(
                    _consistent_relabel(mapr_relabel_model, inputs[i], reference["command"][i], relabel_permutations[epoch][i])
                    for i in range(len(materialized))
                )
                commands = tuple(_physical_command(out["command"][i], fixture, failed[i], epoch) for i, fixture in enumerate(materialized))
                residual_payload: list[dict[str, object]] = [{} for _ in materialized]
                if zero is not None:
                    ablated = zero(*stacked, forced_commands=out["command"], _evaluation_support_valid_forcing=True)
                    zero_free = zero(*stacked)
                    tv = .5 * torch.abs(out["token_probabilities"] - ablated["token_probabilities"]).sum(2).max(1).values
                    for i in range(len(audits)):
                        active = int(tv[i] >= .05)
                        changed = int(not torch.equal(out["command"][i], zero_free["command"][i]))
                        audits[i]["residual_active"].append(active)  # type: ignore[union-attr]
                        audits[i]["residual_change"].append(changed)  # type: ignore[union-attr]
                        residual_payload[i] = {
                            "direct_full_relative_command": tuple(int(x) for x in out["command"][i]),
                            "direct_zero_relative_command": tuple(int(x) for x in zero_free["command"][i]),
                            "direct_residual_total_variation": float(tv[i]),
                            "direct_residual_active": active,
                            "direct_command_change": changed,
                        }
                rows = batch.step(commands)
                for i, row in enumerate(rows):
                    audits[i]["relabel_ok"] = bool(audits[i]["relabel_ok"]) and relabel[i]
                    audits[i]["traces"].append(_trace_record(observations[i], row["applied_decision"], commands[i], relabel[i], **residual_payload[i]))  # type: ignore[union-attr]
                observations = tuple(row["next_observation"] for row in rows)
        return tuple(
            {
                **audits[i],
                "fail_endpoint": row["fail_endpoint"],
                "total_endpoint": row["total_endpoint"],
                "intact_endpoint": row["intact_endpoint"],
                "hard_valid": not row["safety_violation"] and not row["exclusivity_violation"] and bool(row["terminal"]),
            }
            for i, row in enumerate(rows)
        )
    finally:
        batch.close()


def run_bcrh_batch(
    fixtures: Sequence[EpisodeFixture],
    *,
    mapr_relabel_model: MAPR4,
    relabel_permutations: Sequence[Sequence[Sequence[int]]],
) -> tuple[dict[str, object], ...]:
    materialized = tuple(fixtures)
    if len(materialized) < 8:
        raise EvaluationError("native evaluation batches require B>=8")
    batch = NativeInteractiveBatch(materialized)
    audits: list[list[dict[str, object]]] = [[] for _ in materialized]
    relabel_ok = [True] * len(materialized)
    try:
        observations = tuple(row["next_observation"] for row in batch.initial)
        failed = tuple(int(row["failed_rank"]) for row in batch.initial)
        rows: tuple[dict[str, object], ...] = ()
        with torch.no_grad():
            for epoch in range(6):
                inputs = [_model_inputs(obs, fixture, fr) for obs, fixture, fr in zip(observations, materialized, failed)]
                stacked = tuple(torch.cat([item[j] for item in inputs], 0) for j in range(6))
                reference = mapr_relabel_model(*stacked)["command"]
                relabel = tuple(_consistent_relabel(mapr_relabel_model, inputs[i], reference[i], relabel_permutations[epoch][i]) for i in range(len(materialized)))
                decisions = batch.bcrh(include_candidate_records=True)
                if not all(
                    row["scorer_checker_equal"]
                    and row["independent_enumerator_equal"]
                    and row["candidate_count"] <= 1961
                    and len(row["candidate_records"]) == row["candidate_count"]
                    and all(record["exact_match"] for record in row["candidate_records"])
                    for row in decisions
                ):
                    raise EvaluationError("BCRH scorer/checker/candidate record differs")
                compact = tuple(_compact_interactive_bcrh(row) for row in decisions)
                commands = tuple(row["scorer_command"] for row in decisions)
                rows = batch.step(commands)
                for i, row in enumerate(rows):
                    relabel_ok[i] = relabel_ok[i] and relabel[i]
                    audits[i].append(_trace_record(observations[i], row["applied_decision"], commands[i], relabel[i], bcrh=compact[i]))
                observations = tuple(row["next_observation"] for row in rows)
        return tuple(
            {
                "traces": tuple(audits[i]),
                "bcrh": tuple(trace["bcrh"] for trace in audits[i]),
                "relabel_ok": relabel_ok[i],
                "fail_endpoint": row["fail_endpoint"],
                "total_endpoint": row["total_endpoint"],
                "intact_endpoint": row["intact_endpoint"],
                "hard_valid": not row["safety_violation"] and not row["exclusivity_violation"] and bool(row["terminal"]),
            }
            for i, row in enumerate(rows)
        )
    finally:
        batch.close()


def _uniform_derangement(
    block: tuple[int, ...],
    rng: EmpiricalRNG,
    *,
    replicate_role: str,
    failed_zone: int,
    panel_row: int,
    now: object,
) -> tuple[int, ...]:
    candidates = tuple(p for p in itertools.permutations(block) if all(a != b for a, b in zip(block, p)))
    if not candidates:
        raise EvaluationError("eligible CUT block has no derangement")
    limit = len(candidates)
    bound = ((1 << 64) // limit) * limit
    draw = 0
    while True:
        word = rng.word(
            address(
                replicate_role=replicate_role,
                domain="conclusion/cut-derangement",
                purpose="MAPR-ROW-CUT@0/" + ",".join(map(str, block)),
                roster_size=7,
                failed_zone=failed_zone,
                update_or_panel_row=panel_row,
                episode_row=panel_row,
                physical_time=0,
                draw=draw,
            ),
            now=now,  # type: ignore[arg-type]
        )
        draw += 1
        if word < bound:
            return candidates[word % limit]


def run_cut_batch(
    fixtures: Sequence[EpisodeFixture],
    model: MAPR4,
    *,
    rng: EmpiricalRNG,
    replicate_role: str,
    failed_zone: int,
    panel_rows: Sequence[int],
    now: object,
    relabel_permutations: Sequence[Sequence[Sequence[int]]],
) -> tuple[dict[str, object], ...]:
    materialized = tuple(fixtures)
    if len(materialized) < 8 or len(panel_rows) != len(materialized):
        raise EvaluationError("CUT batch width/address differs")
    batch = NativeInteractiveBatch(materialized)
    audits = [{"traces": [], "relabel_ok": True, "association_opportunity": 0, "association_change": 0, "cut": None} for _ in materialized]
    try:
        observations = tuple(row["next_observation"] for row in batch.initial)
        failed = tuple(int(row["failed_rank"]) for row in batch.initial)
        rows: tuple[dict[str, object], ...] = ()
        with torch.no_grad():
            for epoch in range(6):
                inputs = [_model_inputs(obs, fixture, fr) for obs, fixture, fr in zip(observations, materialized, failed)]
                stacked = tuple(torch.cat([item[j] for item in inputs], 0) for j in range(6))
                ordinary = model(*stacked)
                relabel = tuple(_consistent_relabel(model, inputs[i], ordinary["command"][i], relabel_permutations[epoch][i]) for i in range(len(materialized)))
                cut_records: list[dict[str, object] | None] = [None] * len(materialized)
                relative = [tuple(int(x) for x in ordinary["command"][i]) for i in range(len(materialized))]
                if epoch == 0:
                    score_rows, null_scores = model.score_table(stacked[0], stacked[1], stacked[2])
                    for i, fixture in enumerate(materialized):
                        raw = np.asarray(observations[i]["agent_rows"], dtype=np.float64).reshape(len(fixture.agents) - 1, 38)
                        keys = tuple((int(row[0]), int(row[1]), float(row[2]), tuple(int(x) for x in row[26:30])) for row in raw)
                        cut = row_cut(
                            score_rows[i].detach().numpy(),
                            keys,
                            lambda block, i=i: _uniform_derangement(block, rng, replicate_role=replicate_role, failed_zone=failed_zone, panel_row=int(panel_rows[i]), now=now),
                        )
                        cut_command = _decode_score_table(cut.reassigned_rows, null_scores[i].detach().numpy(), stacked[3][i], stacked[4][i], stacked[5][i])
                        relative[i] = cut_command
                        ordinary_physical = _physical_command(ordinary["command"][i], fixture, failed[i], epoch)
                        cut_physical = _physical_command(cut_command, fixture, failed[i], epoch)
                        cut_records[i] = {
                            "partition_keys": keys,
                            "blocks": cut.blocks,
                            "origin_for_recipient": cut.origin_for_recipient,
                            "row_multiset_preserved": True,
                            "opportunity": int(cut.opportunity),
                            "ordinary_physical_command": ordinary_physical,
                            "cut_physical_command": cut_physical,
                            "command_changed": int(ordinary_physical != cut_physical),
                        }
                        audits[i]["association_opportunity"] = int(cut.opportunity)
                        audits[i]["association_change"] = int(ordinary_physical != cut_physical)
                        audits[i]["cut"] = cut_records[i]
                commands = tuple(_physical_command(relative[i], fixture, failed[i], epoch) for i, fixture in enumerate(materialized))
                rows = batch.step(commands)
                for i, row in enumerate(rows):
                    audits[i]["relabel_ok"] = bool(audits[i]["relabel_ok"]) and relabel[i]
                    audits[i]["traces"].append(_trace_record(observations[i], row["applied_decision"], commands[i], relabel[i], cut=cut_records[i]))  # type: ignore[union-attr]
                observations = tuple(row["next_observation"] for row in rows)
        return tuple(
            {
                **audits[i],
                "fail_endpoint": row["fail_endpoint"],
                "total_endpoint": row["total_endpoint"],
                "intact_endpoint": row["intact_endpoint"],
                "hard_valid": not row["safety_violation"] and not row["exclusivity_violation"] and bool(row["terminal"]),
            }
            for i, row in enumerate(rows)
        )
    finally:
        batch.close()


def endpoint(row: Mapping[str, object], name: str) -> Fraction:
    key = {"fail": "fail_endpoint", "total": "total_endpoint", "intact": "intact_endpoint"}[name]
    numerator, denominator = row[key]  # type: ignore[misc]
    if int(denominator) <= 0:
        raise EvaluationError("endpoint denominator is nonpositive")
    return Fraction(int(numerator), int(denominator))


def family_coordinate_names() -> dict[str, tuple[str, ...]]:
    populations = ("aggregate", "zone1", "zone2")
    contrasts = (("MAPR", "DIRECT"), ("MAPR", "BCRH"), ("MAPR", "CUT"), ("DIRECT", "BCRH"))
    efficacy = tuple(f"fail/{a}-{b}/{population}" for population in populations for a, b in contrasts)
    non_harm = tuple(f"{metric}/{a}-{b}/{population}" for population in populations for metric in ("total", "intact") for a, b in contrasts)
    training_gain = tuple(f"gate/training_gain/{arm}/N{roster}/zone{zone}" for arm in LEARNED_ARMS for roster in (3, 5) for zone in (1, 2))
    competence = tuple(
        [f"gate/competence/{arm}/N{roster}z{zone}/{metric}" for metric in ("fail", "total") for arm in LEARNED_ARMS for roster in (3, 5) for zone in (1, 2)]
        + [f"gate/competence/{arm}/heldz{zone}/{metric}" for metric in ("fail", "total") for arm in ("MAPR", "DIRECT", "BCRH") for zone in (1, 2)]
    )
    mechanism = tuple(
        [f"gate/direct_residual_active/{cell}" for cell in ("N3z1", "N3z2", "N5z1", "N5z2", "heldz1", "heldz2")]
        + [f"gate/direct_command_change/{cell}" for cell in ("N3z1", "N3z2", "N5z1", "N5z2", "heldz1", "heldz2")]
        + [f"gate/action_sensitivity/zone{zone}" for zone in (1, 2)]
        + [f"gate/association_opportunity/zone{zone}" for zone in (1, 2)]
        + [f"gate/association_change/zone{zone}" for zone in (1, 2)]
    )
    result = {"efficacy": efficacy, "non_harm": non_harm, "training_gain": training_gain, "competence": competence, "mechanism": mechanism}
    if tuple(map(len, result.values())) != (12, 24, 8, 28, 18):
        raise AssertionError("family coordinate names differ")
    return result


class ExactPanelReducer:
    def __init__(self, validation: Sequence[Mapping[str, object]], conclusion: Sequence[Mapping[str, object]]):
        self.validation = tuple(validation)
        self.conclusion = tuple(conclusion)

    @staticmethod
    def _mean(values: Sequence[Fraction]) -> Fraction:
        if not values:
            raise EvaluationError("registered reduction cell is empty")
        return sum(values, Fraction()) / len(values)

    def matrices(self) -> dict[str, list[list[float]]]:
        families = {name: [] for name in ("efficacy", "non_harm", "training_gain", "competence", "mechanism")}
        roles = sorted({str(row["replicate_role"]) for row in self.conclusion})
        if roles != list(REPLICATE_ROLES):
            raise EvaluationError("replicate inventory differs before reduction")
        for role in roles:
            con = [row for row in self.conclusion if row["replicate_role"] == role]
            val = [row for row in self.validation if row["replicate_role"] == role]

            def cm(arm: str, population: str, metric: str) -> Fraction:
                rows = [row for row in con if row["arm"] == arm and (population == "aggregate" or row["failed_zone"] == int(population[-1]))]
                return self._mean([endpoint(row, metric) for row in rows])

            efficacy = [cm(a, population, "fail") - cm(b, population, "fail") for population in ("aggregate", "zone1", "zone2") for a, b in (("MAPR", "DIRECT"), ("MAPR", "BCRH"), ("MAPR", "CUT"), ("DIRECT", "BCRH"))]
            non_harm = [cm(a, population, metric) - cm(b, population, metric) for population in ("aggregate", "zone1", "zone2") for metric in ("total", "intact") for a, b in (("MAPR", "DIRECT"), ("MAPR", "BCRH"), ("MAPR", "CUT"), ("DIRECT", "BCRH"))]
            gain = [
                self._mean([endpoint(row, "fail") for row in val if row["arm"] == arm and row["checkpoint"] == 256 and row["roster_size"] == roster and row["failed_zone"] == zone])
                - self._mean([endpoint(row, "fail") for row in val if row["arm"] == arm and row["checkpoint"] == 0 and row["roster_size"] == roster and row["failed_zone"] == zone])
                for arm in LEARNED_ARMS for roster in (3, 5) for zone in (1, 2)
            ]
            competence = []
            for metric in ("fail", "total"):
                competence.extend(self._mean([endpoint(row, metric) for row in val if row["arm"] == arm and row["checkpoint"] == 256 and row["roster_size"] == roster and row["failed_zone"] == zone]) for arm in LEARNED_ARMS for roster in (3, 5) for zone in (1, 2))
                competence.extend(cm(arm, f"zone{zone}", metric) for arm in ("MAPR", "DIRECT", "BCRH") for zone in (1, 2))
            mechanism = []
            for key in ("residual_active", "residual_change"):
                mechanism.extend(Fraction(sum(sum(row[key]) for row in val if row["arm"] == "DIRECT" and row["checkpoint"] == 256 and row["roster_size"] == roster and row["failed_zone"] == zone), 6 * 32) for roster, zone in ((3, 1), (3, 2), (5, 1), (5, 2)))
                mechanism.extend(Fraction(sum(sum(row[key]) for row in con if row["arm"] == "DIRECT" and row["failed_zone"] == zone), 6 * 32) for zone in (1, 2))
            mechanism.extend(Fraction(sum(int(row["action_sensitive"]) for row in con if row["arm"] == "MAPR" and row["failed_zone"] == zone), 32) for zone in (1, 2))
            mechanism.extend(Fraction(sum(int(row["association_opportunity"]) for row in con if row["arm"] == "MAPR" and row["failed_zone"] == zone), 32) for zone in (1, 2))
            mechanism.extend(Fraction(sum(int(row["association_change"]) for row in con if row["arm"] == "MAPR" and row["failed_zone"] == zone), 32) for zone in (1, 2))
            for name, values in (("efficacy", efficacy), ("non_harm", non_harm), ("training_gain", gain), ("competence", competence), ("mechanism", mechanism)):
                families[name].append([float(value) for value in values])
        expected = {"efficacy": 12, "non_harm": 24, "training_gain": 8, "competence": 28, "mechanism": 18}
        if any(len(families[name]) != 16 or any(len(row) != width for row in families[name]) for name, width in expected.items()):
            raise EvaluationError("replicate matrix shape differs")
        return families


def _fraction_record(value: Fraction) -> tuple[int, int]:
    return value.numerator, value.denominator


def exact_reduction(matrices: Mapping[str, Sequence[Sequence[float]]]) -> dict[str, object]:
    names = family_coordinate_names()
    if set(matrices) != set(names):
        raise EvaluationError("five-family matrix inventory differs")
    point_rows: list[dict[str, object]] = []
    interval_rows: list[dict[str, object]] = []
    interval_map: dict[str, tuple[Fraction, Fraction]] = {}
    for family in ("efficacy", "non_harm", "training_gain", "competence", "mechanism"):
        rows = tuple(tuple(float(value) for value in row) for row in matrices[family])
        intervals = family_intervals(rows, len(names[family]))
        for column, name in enumerate(names[family]):
            values = tuple(Fraction.from_float(row[column]) for row in rows)
            point = sum(values, Fraction()) / 16
            interval = intervals[column]
            interval_map[name] = (interval.lower, interval.upper)
            point_rows.append({"family": family, "coordinate": name, "value": _fraction_record(point)})
            interval_rows.append({"family": family, "coordinate": name, "lower": _fraction_record(interval.lower), "upper": _fraction_record(interval.upper), "q": interval.q, "partition_visits": interval.partition_visits, "subset_mean_constructions": interval.subset_mean_constructions, "comparison_ceiling": interval.comparison_ceiling})
    if len(point_rows) != 90 or len(interval_rows) != 90:
        raise AssertionError("registered inference coordinate count differs")
    return {"points": tuple(point_rows), "intervals": tuple(interval_rows), "interval_map": interval_map}


def _strict_lower(intervals: Mapping[str, tuple[Fraction, Fraction]], name: str, threshold: Fraction) -> bool:
    return intervals[name][0] > threshold


def exact_gates(
    intervals: Mapping[str, tuple[Fraction, Fraction]],
    validation: Sequence[Mapping[str, object]],
    conclusion: Sequence[Mapping[str, object]],
    certificate: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    relabel = all(bool(row["relabel_ok"]) for row in itertools.chain(validation, conclusion))
    hard = all(bool(row["hard_valid"]) for row in itertools.chain(validation, conclusion))
    bcrh = all(decision["scorer_checker_equal"] and decision["independent_enumerator_equal"] for row in conclusion if row["arm"] == "BCRH" for decision in row["bcrh"]) and len(certificate) == 64 and all(row["scorer_checker_equal"] and row["independent_enumerator_equal"] for row in certificate)
    association_valid = relabel and all((row.get("cut") or {}).get("row_multiset_preserved", False) for row in conclusion if row["arm"] == "CUT")
    training_gain = all(_strict_lower(intervals, f"gate/training_gain/{arm}/N{roster}/zone{zone}", Fraction(1, 10)) for arm in LEARNED_ARMS for roster in (3, 5) for zone in (1, 2))
    competence = all(_strict_lower(intervals, f"gate/competence/{arm}/{cell}/{metric}", Fraction(1, 30) if metric == "fail" else Fraction(7, 10)) for metric in ("fail", "total") for arm in LEARNED_ARMS for cell in ("N3z1", "N3z2", "N5z1", "N5z2", "heldz1", "heldz2")) and all(_strict_lower(intervals, f"gate/competence/BCRH/heldz{zone}/{metric}", Fraction(1, 30) if metric == "fail" else Fraction(7, 10)) for zone in (1, 2) for metric in ("fail", "total"))
    direct = all(_strict_lower(intervals, f"gate/direct_{kind}/{cell}", Fraction(1, 10)) for kind in ("residual_active", "command_change") for cell in ("N3z1", "N3z2", "N5z1", "N5z2", "heldz1", "heldz2"))
    action = all(_strict_lower(intervals, f"gate/action_sensitivity/zone{zone}", Fraction(1, 4)) for zone in (1, 2))
    association = all(_strict_lower(intervals, f"gate/association_opportunity/zone{zone}", Fraction(1, 4)) and _strict_lower(intervals, f"gate/association_change/zone{zone}", Fraction(1, 10)) for zone in (1, 2))
    return (
        {"gate": "complete_integrity", "passed": hard and bcrh},
        {"gate": "consistent_relabel", "passed": relabel},
        {"gate": "action_sensitivity", "passed": action},
        {"gate": "learned_training_gain", "passed": training_gain},
        {"gate": "level_competence", "passed": competence},
        {"gate": "direct_containment", "passed": True, "basis": "source-manifest-bound static conformance"},
        {"gate": "direct_activity", "passed": direct},
        {"gate": "association_activity", "passed": association and association_valid},
        {"gate": "positive_result_nonharm", "passed": True, "basis": "enforced inside first-true branch predicates"},
    )


def _write_identical_once(path: Path, payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise FrontierError("existing atomic category differs")
        return digest
    try:
        return write_once(path, payload)
    except EvidenceLifecycleError:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            return digest
        raise


def publish_categories(frontier: AtomicFrontier, values: Mapping[str, AtomicCategoryPayload]) -> tuple[dict[str, object], ...]:
    if set(values) != set(COMPLETE_CATEGORIES):
        raise FrontierError("atomic category payload inventory differs")
    rows = []
    for category in COMPLETE_CATEGORIES:
        item = values[category]
        if item.logical_cardinality != CATEGORY_CARDINALITIES[category]:
            raise FrontierError(f"atomic category logical cardinality differs: {category}")
        payload = canonical_json_bytes({"schema": "VNFC_BPCR_R09_BLINDED_CATEGORY_PAYLOAD_V1", "category": category, "bindings": asdict(frontier.bindings), "logical_cardinality": item.logical_cardinality, "value": item.value})
        leaf = frontier.root / f"{category}.payload.json"
        leaf_sha = _write_identical_once(leaf, payload)
        index = {"schema": "VNFC_BPCR_R09_ATOMIC_CATEGORY_INDEX_V1", "category": category, "bindings": asdict(frontier.bindings), "cardinality": item.logical_cardinality, "children": [{"path": leaf.name, "sha256": leaf_sha, "cardinality": item.logical_cardinality}]}
        index_path = frontier.root / f"{category}.index.json"
        index_sha = _write_identical_once(index_path, canonical_json_bytes(index))
        rows.append({"category": category, "path": index_path.name, "sha256": index_sha, "cardinality": item.logical_cardinality})
    return tuple(rows)


def _state_dict_parameters(state: Mapping[str, torch.Tensor], direct: bool) -> dict[str, torch.Tensor]:
    from .torch_models import direct_parameter_shapes, mapr_parameter_shapes

    shapes = direct_parameter_shapes() if direct else mapr_parameter_shapes()
    expected = {"parameters_by_name." + name.replace(".", "__"): shape for name, shape in shapes.items()}
    if set(state) != set(expected):
        raise EvaluationError("checkpoint tensor inventory differs")
    parameters = {}
    for name, shape in shapes.items():
        tensor = state["parameters_by_name." + name.replace(".", "__")]
        if tensor.device.type != "cpu" or tensor.dtype != torch.float64 or tuple(tensor.shape) != shape or not bool(torch.isfinite(tensor).all()):
            raise EvaluationError("checkpoint tensor contract differs")
        parameters[name] = tensor.detach().clone()
    return parameters


def _load_torch(path: str) -> object:
    return torch.load(Path(path), map_location="cpu", weights_only=True)


def load_slots(receipts: Sequence[CheckpointReceipt], required: set[tuple[str, str]] | None = None) -> dict[tuple[str, str], LoadedSlot]:
    slots: dict[tuple[str, str], LoadedSlot] = {}
    for receipt in receipts:
        direct = receipt.arm == "DIRECT"
        initial_state = _load_torch(receipt.initial_checkpoint_path)
        final_state = _load_torch(receipt.final_checkpoint_path)
        if not isinstance(initial_state, Mapping) or not isinstance(final_state, Mapping):
            raise EvaluationError("checkpoint payload is not a state dictionary")
        initial = DirectSetAR(_state_dict_parameters(initial_state, direct)) if direct else MAPR4(_state_dict_parameters(initial_state, direct))
        final = DirectSetAR(_state_dict_parameters(final_state, direct)) if direct else MAPR4(_state_dict_parameters(final_state, direct))
        for model, optimizer_path in ((initial, receipt.initial_optimizer_path), (final, receipt.final_optimizer_path)):
            state = _load_torch(optimizer_path)
            if not isinstance(state, Mapping) or set(state) != {"state", "param_groups"}:
                raise EvaluationError("optimizer state payload differs")
            optimizer = make_optimizer(model)
            optimizer.load_state_dict(state)
        slots[(receipt.replicate_role, receipt.arm)] = LoadedSlot(receipt, initial, final)
    expected = required if required is not None else {(role, arm) for role in REPLICATE_ROLES for arm in LEARNED_ARMS}
    if set(slots) != expected:
        raise EvaluationError("loaded checkpoint slot inventory differs")
    return slots


def relabel_schedule(
    rng: EmpiricalRNG,
    fixtures: Sequence[EpisodeFixture],
    *,
    replicate_role: str,
    purpose: str,
    panel_rows: Sequence[int],
    now: object,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    from .services import _shuffle

    schedule = []
    domain = "validation/presentation" if purpose == "validation" else "conclusion/presentation"
    roster = len(fixtures[0].agents) - 1
    for epoch in range(6):
        rows = []
        for fixture, panel_row in zip(fixtures, panel_rows):
            active = len(fixture.agents) - 1
            rows.append(_shuffle(tuple(range(active)), rng, {"replicate_role": replicate_role, "domain": domain, "purpose": purpose + "/consistent-relabel", "roster_size": roster, "failed_zone": fixture.failed_zone, "update_or_panel_row": panel_row, "episode_row": panel_row, "physical_time": 20 * epoch}, now))  # type: ignore[arg-type]
        schedule.append(tuple(rows))
    return tuple(schedule)


def _frontier_predecessors(frontier: AtomicFrontier, receipts: Sequence[CheckpointReceipt]) -> dict[str, str]:
    predecessors = {}
    for receipt in receipts:
        slot = f"{receipt.replicate_role}.{receipt.arm}"
        path = frontier.root / f"{slot}.g0256.json"
        if not path.is_file():
            raise FrontierError("final training frontier predecessor is absent")
        value = json.loads(path.read_text("ascii"))
        if value.get("schema") != "VNFC_BPCR_R09_BLINDED_GENERATION_V1" or value.get("slot") != slot or value.get("generation") != 256:
            raise FrontierError("final training frontier predecessor differs")
        state_path = (frontier.root / str(value.get("state_path"))).resolve()
        try:
            state_path.relative_to(frontier.root.resolve())
        except ValueError as error:
            raise FrontierError("final training state escapes frontier") from error
        if not state_path.is_file() or hashlib.sha256(state_path.read_bytes()).hexdigest() != value.get("state_sha256"):
            raise FrontierError("final training state hash differs")
        predecessors[slot] = hashlib.sha256(path.read_bytes()).hexdigest()
    return predecessors


def build_atomic_categories(
    receipts: Sequence[CheckpointReceipt],
    validation: Sequence[Mapping[str, object]],
    conclusion: Sequence[Mapping[str, object]],
    certificate: Sequence[Mapping[str, object]],
    matrices: Mapping[str, Sequence[Sequence[float]]],
    reduction: Mapping[str, object],
    gates: Sequence[Mapping[str, object]],
    branches: Sequence[str],
) -> dict[str, AtomicCategoryPayload]:
    if len(validation) != 8192 or len(conclusion) != 4096 or len(certificate) != 64:
        raise EvaluationError("atomic evidence cannot be built from a partial panel")
    checkpoint_rows = tuple(item for receipt in receipts for item in (
        {"replicate_role": receipt.replicate_role, "arm": receipt.arm, "kind": "initial_checkpoint", "path": receipt.initial_checkpoint_path, "sha256": receipt.initial_checkpoint_sha256},
        {"replicate_role": receipt.replicate_role, "arm": receipt.arm, "kind": "final_checkpoint", "path": receipt.final_checkpoint_path, "sha256": receipt.final_checkpoint_sha256},
        {"replicate_role": receipt.replicate_role, "arm": receipt.arm, "kind": "initial_optimizer", "path": receipt.initial_optimizer_path, "sha256": receipt.initial_optimizer_sha256},
        {"replicate_role": receipt.replicate_role, "arm": receipt.arm, "kind": "final_optimizer", "path": receipt.final_optimizer_path, "sha256": receipt.final_optimizer_sha256},
    ))
    validation_map = tuple((row["replicate_role"], row["arm"], row["checkpoint"], row["roster_size"], row["failed_zone"], row["panel_row"]) for row in validation)
    conclusion_summary = tuple({key: row[key] for key in ("replicate_role", "arm", "failed_zone", "panel_row", "fail_endpoint", "total_endpoint", "intact_endpoint", "hard_valid")} for row in conclusion)
    public = tuple({"address": tuple(row[key] for key in ("replicate_role", "arm", "failed_zone", "panel_row")) + ((row["checkpoint"], row["roster_size"]) if "checkpoint" in row else ()), "traces": row["traces"]} for row in itertools.chain(validation, conclusion))
    direct = tuple({"address": (row["replicate_role"], row["failed_zone"], row["panel_row"], row.get("checkpoint"), row.get("roster_size")), "residual_active": row["residual_active"], "residual_change": row["residual_change"], "traces": tuple({key: trace.get(key) for key in ("direct_full_relative_command", "direct_zero_relative_command", "direct_residual_total_variation", "direct_residual_active", "direct_command_change")} for trace in row["traces"])} for row in itertools.chain(validation, conclusion) if row["arm"] == "DIRECT" and ("checkpoint" not in row or row["checkpoint"] == 256))
    cut = tuple({"address": (row["replicate_role"], row["failed_zone"], row["panel_row"]), "cut": row["cut"], "relabel_ok": row["relabel_ok"]} for row in conclusion if row["arm"] == "CUT")
    bcrh = tuple({"address": (row["replicate_role"], row["failed_zone"], row["panel_row"]), "decisions": row["bcrh"]} for row in conclusion if row["arm"] == "BCRH")
    matrix_payloads = {name: tuple(tuple(float(x) for x in row) for row in matrices[name]) for name in matrices}
    manifest_path = Path(__file__).with_name("empirical_source_manifest.json")
    dependency_rows = tuple(json.loads(manifest_path.read_text("ascii"))["files"])
    interval_rows = tuple(reduction["intervals"])  # type: ignore[arg-type]
    point_rows = tuple(reduction["points"])  # type: ignore[arg-type]
    values = {
        "checkpoints_optimizers": AtomicCategoryPayload(len(checkpoint_rows), checkpoint_rows),
        "training_validation_roles_coordinate_map": AtomicCategoryPayload(131072 + len(validation_map), {"training_coordinate_formula_count": 131072, "validation": validation_map}),
        "conclusion_rollouts": AtomicCategoryPayload(len(conclusion_summary), conclusion_summary),
        "public_traces_masks_commands": AtomicCategoryPayload(70 * (len(validation) + len(conclusion)), public),
        "direct_diagnostics": AtomicCategoryPayload(6 * len(direct), direct),
        "cut_association": AtomicCategoryPayload(len(cut), cut),
        "bcrh_certificates_64": AtomicCategoryPayload(len(bcrh) + len(certificate), {"held_out": bcrh, "fixtures": tuple(certificate)}),
        "replicate_matrix_efficacy": AtomicCategoryPayload(16 * 12, matrix_payloads["efficacy"]),
        "replicate_matrix_non_harm": AtomicCategoryPayload(16 * 24, matrix_payloads["non_harm"]),
        "replicate_matrix_training_gain": AtomicCategoryPayload(16 * 8, matrix_payloads["training_gain"]),
        "replicate_matrix_competence": AtomicCategoryPayload(16 * 28, matrix_payloads["competence"]),
        "replicate_matrix_mechanism": AtomicCategoryPayload(16 * 18, matrix_payloads["mechanism"]),
        "point_reductions": AtomicCategoryPayload(len(point_rows), point_rows),
        "exact_inference": AtomicCategoryPayload(len(interval_rows), interval_rows),
        "gates": AtomicCategoryPayload(len(gates), tuple(gates)),
        "branches": AtomicCategoryPayload(len(branches), tuple(branches)),
        "dependency_bytes": AtomicCategoryPayload(len(dependency_rows), dependency_rows),
    }
    if {key: value.logical_cardinality for key, value in values.items()} != CATEGORY_CARDINALITIES:
        raise EvaluationError("atomic category cardinality proof differs")
    return values


def execute_plan(
    *,
    plan: PanelPlan,
    authority: object,
    rng: EmpiricalRNG,
    frontier: AtomicFrontier,
    checkpoint_barrier: ValidatedCheckpointBarrier,
    now: object,
    construction_test_seal: object | None = None,
) -> Path:
    """Execute a plan; only the complete plan is reachable from production."""
    plan.validate()
    if not plan.full and construction_test_seal is not _CONSTRUCTION_TEST_SEAL:
        raise EvaluationError("non-full plan is construction-test-only")
    if getattr(authority, "_seal", None) is None or authority.permit.phase != "EVALUATE":
        raise EvaluationError("externally validated EVALUATE authority is required")
    authority.permit.require_active(now=now)
    rng.require_frontier_binding(frontier.bindings)
    if Path(frontier.root).resolve() != Path(authority.permit.paths["frontier_root"]).resolve():
        raise EvaluationError("EVALUATE frontier path differs from Root lease")
    if Path(checkpoint_barrier.path).resolve() != Path(authority.permit.paths["checkpoint_acceptance_path"]).resolve():
        raise EvaluationError("checkpoint barrier path differs from Root lease")
    receipts = checkpoint_barrier.validate_binding(Path(authority.permit.result_root),frontier.bindings)
    required_slots = {(role, arm) for role in REPLICATE_ROLES for arm in LEARNED_ARMS}
    if plan.full and (len(receipts) != 32 or {(r.replicate_role, r.arm) for r in receipts} != required_slots):
        raise EvaluationError("global checkpoint receipt inventory differs")
    for receipt in receipts:
        receipt.validate(Path(authority.permit.result_root), frontier.bindings)
    plan_roles = {row[0] for row in plan.validation} | {row[0] for row in plan.conclusion}
    plan_slots = {(role, arm) for role in plan_roles for arm in LEARNED_ARMS}
    slots = load_slots(receipts, plan_slots)
    from .services import bcrh_certificate, build_world

    validation: list[dict[str, object]] = []
    conclusion: list[dict[str, object]] = []
    validation_groups = sorted({(role, roster, zone) for role, _, _, roster, zone, _ in plan.validation})
    for role, roster, zone in validation_groups:
        panel_rows = sorted({row for r, _, _, n, z, row in plan.validation if (r, n, z) == (role, roster, zone)})
        fixtures = tuple(build_world(rng, replicate_role=role, purpose="validation", roster_size=roster, failed_zone=zone, panel_row=row, now=now) for row in panel_rows)  # type: ignore[arg-type]
        if len(fixtures) < 8:
            raise EvaluationError("validation plan does not route a native B>=8 batch")
        schedule = relabel_schedule(rng, fixtures, replicate_role=role, purpose="validation", panel_rows=panel_rows, now=now)
        mapr_final = slots[(role, "MAPR")].final_model
        if construction_test_seal is not _CONSTRUCTION_TEST_SEAL and not isinstance(mapr_final, MAPR4):
            raise EvaluationError("MAPR checkpoint type differs")
        for arm in LEARNED_ARMS:
            slot = slots[(role, arm)]
            for checkpoint, model in ((0, slot.initial_model), (256, slot.final_model)):
                rows = run_learned_batch(fixtures, model, direct=arm == "DIRECT", mapr_relabel_model=mapr_final, relabel_permutations=schedule)
                validation.extend({**row_data, "replicate_role": role, "arm": arm, "checkpoint": checkpoint, "roster_size": roster, "failed_zone": zone, "panel_row": panel_row} for panel_row, row_data in zip(panel_rows, rows))
    conclusion_groups = sorted({(role, zone) for role, _, zone, _ in plan.conclusion})
    for role, zone in conclusion_groups:
        panel_rows = sorted({row for r, _, z, row in plan.conclusion if (r, z) == (role, zone)})
        fixtures = tuple(build_world(rng, replicate_role=role, purpose="conclusion", roster_size=7, failed_zone=zone, panel_row=row, now=now) for row in panel_rows)  # type: ignore[arg-type]
        if len(fixtures) < 8:
            raise EvaluationError("conclusion plan does not route a native B>=8 batch")
        schedule = relabel_schedule(rng, fixtures, replicate_role=role, purpose="conclusion", panel_rows=panel_rows, now=now)
        mapr = slots[(role, "MAPR")].final_model
        direct = slots[(role, "DIRECT")].final_model
        if construction_test_seal is not _CONSTRUCTION_TEST_SEAL and (not isinstance(mapr, MAPR4) or not isinstance(direct, DirectSetAR)):
            raise EvaluationError("conclusion checkpoint type differs")
        arm_rows = {
            "MAPR": run_learned_batch(fixtures, mapr, direct=False, mapr_relabel_model=mapr, relabel_permutations=schedule, action_sensitivity=True),
            "DIRECT": run_learned_batch(fixtures, direct, direct=True, mapr_relabel_model=mapr, relabel_permutations=schedule),
            "BCRH": run_bcrh_batch(fixtures, mapr_relabel_model=mapr, relabel_permutations=schedule),
            "CUT": run_cut_batch(fixtures, mapr, rng=rng, replicate_role=role, failed_zone=zone, panel_rows=panel_rows, now=now, relabel_permutations=schedule),
        }
        for arm, rows in arm_rows.items():
            for row_index, (panel_row, row_data) in enumerate(zip(panel_rows, rows)):
                defaults = {"residual_active": (), "residual_change": (), "action_sensitive": False, "association_opportunity": 0, "association_change": 0, "cut": None, "bcrh": ()}
                association = {}
                if arm == "MAPR":
                    association = {
                        "association_opportunity": arm_rows["CUT"][row_index]["association_opportunity"],
                        "association_change": arm_rows["CUT"][row_index]["association_change"],
                    }
                conclusion.append({**defaults, **row_data, **association, "replicate_role": role, "arm": arm, "failed_zone": zone, "panel_row": panel_row})
    if len(validation) != len(plan.validation) or len(conclusion) != len(plan.conclusion):
        raise EvaluationError("evaluation execution returned a partial panel")
    certificate = bcrh_certificate()
    reducer = ExactPanelReducer(validation, conclusion)
    matrices = reducer.matrices()
    reduction = exact_reduction(matrices)
    gates = exact_gates(reduction["interval_map"], validation, conclusion, certificate)  # type: ignore[arg-type]
    association_structural = bool(gates[1]["passed"]) and all(
        (row.get("cut") or {}).get("row_multiset_preserved", False)
        for row in conclusion if row["arm"] == "CUT"
    )
    integrity = {"overall_valid": bool(gates[0]["passed"] and gates[1]["passed"]), "association_valid": association_structural}
    flags = derive_branch_flags(reduction["interval_map"], integrity)  # type: ignore[arg-type]
    branches = reduce_branches(flags)
    categories = build_atomic_categories(receipts, validation, conclusion, certificate, matrices, reduction, gates, branches)
    artifacts = publish_categories(frontier, categories)
    predecessors = _frontier_predecessors(frontier, receipts)
    manifest = frontier.seal_complete(PANEL_COUNTS, artifacts, checkpoint_barrier, predecessors)
    expected = Path(authority.permit.paths["complete_manifest_path"]).resolve()
    if manifest.resolve() != expected:
        raise FrontierError("complete manifest path differs from Root lease")
    return manifest
