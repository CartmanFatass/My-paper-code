from __future__ import annotations

import dataclasses
import hashlib
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import reference_oracle
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.model import ActionScorer
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.training import fixed_fp32_tree

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.contract import (
    FINAL_CHECKPOINT_SLOT_COUNT,
    K_TEST,
    K_TRAIN,
    OBJECT_REVISION,
    TRAINING_BATCHES,
    LearnedArm,
    Panel,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.s2_construction import (
    OBJECT_DIGEST,
    REQUIRED_TOP_LEVEL_FIELDS,
    S2_SCHEMA,
    SYNTHETIC_NAMESPACE,
    REPAIR1_NAMESPACE,
    BoundaryRequest,
    CheckpointSlot,
    ValidatedCheckpointSlot,
    SealedEvaluation,
    S2Code,
    S2Refusal,
    acquisition_supported,
    attribution_map,
    belief_dp_root,
    belief_dp_tail,
    build_completion_manifest,
    build_action_scorer_payload,
    build_synthetic_checkpoint_bytes,
    decomposition,
    distinct_permutations,
    evaluate_complete_private,
    evaluate_learned_slot,
    evaluate_policy,
    finite_cases,
    forced_probe_blind_dp,
    greedy_index,
    learned_greedy_index,
    learned_tail_channel,
    immediate_dp,
    one_sided_lower,
    paired_t_interval,
    population_case_count,
    publish_complete_package,
    raw_permavg_tail_action,
    read_atomic_sealed_blob,
    structural_proxy,
    synthetic_atomic_transition,
    terminal_action_class,
    validate_checkpoint_inventory,
    validate_competence,
    validate_complete_package,
    validate_headroom,
    validate_support,
    validate_support_structure,
    validate_sealed_evaluation,
    _posterior,
    _package_provenance,
    _load_action_scorer_payload,
    _tail_agreement,
    _tail_components,
)


CONSTRUCTION = BoundaryRequest(
    namespace=REPAIR1_NAMESPACE,
    registered_master_seeds=False,
    complete_registered_panel=False,
    question_relevant_output=False,
    gpu=False,
)
REGISTERED_PUBLICATION = BoundaryRequest(
    namespace="REGISTERED_UCOPE_R01_R03_S2",
    registered_master_seeds=True,
    complete_registered_panel=True,
    question_relevant_output=True,
    gpu=False,
)
SYNTHETIC_SEEDS = tuple(0xC100000000000000 + index for index in range(10))


def _support(panel: int) -> dict[str, object]:
    return {
        "root_visits": [20480, 12288, 12288, 12288, 12288, 12288],
        "tail_visits": [4096] * 5,
        "displayed_count_visits": [2926, 2926, 2926, 2926, 2926, 2926, 2924],
        "balanced_totals": [40960] * 2 if panel == int(Panel.PERSISTENT) else [20480] * 4,
    }


def _inventory(root: Path) -> list[CheckpointSlot]:
    rows: list[CheckpointSlot] = []
    for arm in LearnedArm:
        for panel in Panel:
            for seed_index, seed in enumerate(SYNTHETIC_SEEDS):
                path = root / f"slot-{int(arm)}-{int(panel)}-{seed_index}.bin"
                path.write_bytes(
                    build_synthetic_checkpoint_bytes(
                        arm=int(arm),
                        panel=int(panel),
                        master_seed=seed,
                        support=_support(int(panel)),
                        model_payload=f"synthetic-model-{int(arm)}-{int(panel)}-{seed_index}".encode(),
                        request=CONSTRUCTION,
                    )
                )
                rows.append(CheckpointSlot(path))
    return rows


class _SyntheticScorer:
    def bind(self, slot: ValidatedCheckpointSlot) -> None:
        try:
            seed_index = SYNTHETIC_SEEDS.index(slot.master_seed)
        except ValueError as exc:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH) from exc
        expected = f"synthetic-model-{slot.arm}-{slot.panel}-{seed_index}".encode()
        if slot.model_payload != expected or hashlib.sha256(expected).hexdigest() != slot.model_sha256:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)

    def root_logits(self, slot: ValidatedCheckpointSlot, periods: tuple[int, ...]) -> np.ndarray:
        values = np.full(len(periods) + 1, np.float32(-1.0), dtype=np.float32)
        if slot.panel == int(Panel.PERSISTENT):
            values[0] = np.float32(1.0)
        else:
            values[1 + len(periods) // 2] = np.float32(1.0)
        if slot.arm == int(LearnedArm.RAW):
            values = np.float32(values + np.float32(0.001))
        return values

    def tail_logits(
        self, slot: ValidatedCheckpointSlot, periods: tuple[int, ...], channel: np.ndarray
    ) -> np.ndarray:
        target = int(abs(float(np.sum(channel, dtype=np.float32)))) % len(periods)
        values = np.full(len(periods), np.float32(-1.0), dtype=np.float32)
        values[target] = np.float32(1.0)
        if slot.arm == int(LearnedArm.RAW):
            values = np.float32(values + np.float32(0.001))
        return values


def _minimal_private_package() -> dict[str, object]:
    package = {key: {} for key in REQUIRED_TOP_LEVEL_FIELDS}
    package.update(
        {
            "schema": S2_SCHEMA,
            "object_revision": OBJECT_REVISION,
            "object_digest": OBJECT_DIGEST,
            "checkpoint_inventory": [
                {
                    "sha256": hashlib.sha256(f"slot-{index}".encode()).hexdigest(),
                    "model_sha256": hashlib.sha256(f"model-{index}".encode()).hexdigest(),
                }
                for index in range(FINAL_CHECKPOINT_SLOT_COUNT)
            ],
            "decompositions": {"all_identities_hold": True},
            "normalization": {"all_within_tolerance": True},
            "required_field_inventory": list(sorted(REQUIRED_TOP_LEVEL_FIELDS)),
            "provenance": {},
        }
    )
    return package


def test_boundary_refuses_every_registered_or_gpu_flag() -> None:
    CONSTRUCTION.require_construction()
    for field in (
        "registered_master_seeds",
        "complete_registered_panel",
        "question_relevant_output",
        "gpu",
    ):
        with pytest.raises(S2Refusal, match=S2Code.REGISTERED_BOUNDARY_ATTEMPTED.value):
            dataclasses.replace(CONSTRUCTION, **{field: True}).require_construction()
    with pytest.raises(S2Refusal, match=S2Code.REGISTERED_BOUNDARY_ATTEMPTED.value):
        dataclasses.replace(CONSTRUCTION, namespace="UNAUTHORIZED").require_construction()


def test_exact_inventory_closure_and_all_refusals(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints"
    root.mkdir()
    slots = _inventory(root)
    assert len(validate_checkpoint_inventory(slots, checkpoint_root=root, construction=True)) == 90

    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_INVENTORY.value):
        validate_checkpoint_inventory(slots[:-1], checkpoint_root=root, construction=True)
    duplicate = slots[:-1] + [slots[0]]
    with pytest.raises(S2Refusal, match=S2Code.DUPLICATE_SLOT.value):
        validate_checkpoint_inventory(duplicate, checkpoint_root=root, construction=True)
    original = slots[0].path.read_bytes()
    payload = json.loads(original)
    payload["object_digest"] = "0" * 64
    slots[0].path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(S2Refusal, match=S2Code.OBJECT_MISMATCH.value):
        validate_checkpoint_inventory(slots, checkpoint_root=root, construction=True)
    slots[0].path.write_bytes(original)
    payload = json.loads(original)
    payload["model_sha256"] = "0" * 64
    slots[0].path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        validate_checkpoint_inventory(slots, checkpoint_root=root, construction=True)
    slots[0].path.write_bytes(original)
    payload = json.loads(original)
    payload["batch"] = 319
    slots[0].path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(S2Refusal, match=S2Code.MALFORMED_INPUT.value):
        validate_checkpoint_inventory(slots, checkpoint_root=root, construction=True)
    slots[0].path.write_bytes(original)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(S2Refusal, match=S2Code.PATH_REFUSED.value):
        validate_checkpoint_inventory(
            [CheckpointSlot(outside)] + slots[1:],
            checkpoint_root=root,
            construction=True,
        )


def test_action_scorer_payload_is_source_shape_dtype_and_coordinate_bound() -> None:
    scorer = ActionScorer().to(dtype=torch.float32)
    payload = build_action_scorer_payload(
        scorer, arm=0, panel=0, master_seed=SYNTHETIC_SEEDS[0]
    )
    slot = ValidatedCheckpointSlot(
        arm=0,
        panel=0,
        master_seed=SYNTHETIC_SEEDS[0],
        batch=TRAINING_BATCHES,
        object_revision=OBJECT_REVISION,
        object_digest=OBJECT_DIGEST,
        path=Path("synthetic-not-read"),
        sha256="a" * 64,
        model_sha256=hashlib.sha256(payload).hexdigest(),
        model_payload=payload,
        support=_support(0),
    )
    loaded = _load_action_scorer_payload(slot)
    for name, expected in scorer.state_dict().items():
        assert torch.equal(loaded.state_dict()[name], expected)

    wrong_coordinate = build_action_scorer_payload(
        scorer, arm=0, panel=0, master_seed=SYNTHETIC_SEEDS[1]
    )
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        _load_action_scorer_payload(
            dataclasses.replace(
                slot,
                model_payload=wrong_coordinate,
                model_sha256=hashlib.sha256(wrong_coordinate).hexdigest(),
            )
        )


def test_complete_evaluator_refuses_unbound_or_caller_injected_scorer(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkpoints"
    root.mkdir()
    slots = _inventory(root)
    first = slots[0].path
    first.write_bytes(
        build_synthetic_checkpoint_bytes(
            arm=0,
            panel=0,
            master_seed=SYNTHETIC_SEEDS[0],
            support=_support(0),
            model_payload=b"substituted-but-self-hashed",
            request=CONSTRUCTION,
        )
    )
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        evaluate_complete_private(
            slots,
            checkpoint_root=root,
            scorer=_SyntheticScorer(),
            request=CONSTRUCTION,
        )
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        evaluate_complete_private(
            slots,
            checkpoint_root=root,
            scorer=_SyntheticScorer(),
            request=REGISTERED_PUBLICATION,
        )


def test_finite_population_cardinality_normalization_and_comparators() -> None:
    assert tuple(population_case_count(int(panel)) for panel in Panel) == (128, 256, 16384)
    for panel in Panel:
        weight = np.float32(0.0)
        for case in finite_cases(int(panel)):
            weight = np.float32(weight + case.weight)
        assert abs(float(weight) - 1.0) <= 1.0e-5
        root = belief_dp_root(int(panel), K_TEST)
        assert 0 <= root <= len(K_TEST)
        for history in range(64):
            assert 0 <= belief_dp_tail(history, int(panel), K_TEST) < len(K_TEST)
    assert 0 <= immediate_dp(K_TEST)[0] < len(K_TEST)
    assert 0 <= forced_probe_blind_dp(K_TEST) < len(K_TEST)
    record = evaluate_policy(
        panel=int(Panel.PERSISTENT),
        periods=K_TEST,
        root_action=0,
        tail_action=lambda history: belief_dp_tail(history, int(Panel.PERSISTENT), K_TEST),
    )
    assert len(record.components) == 6
    assert len(record.tail_actions) == 64
    assert np.isfinite(record.total)


def test_posterior_uses_written_order_with_exactly_one_final_fp32_cast() -> None:
    for count in range(7):
        short_weight = (0.85**count) * (0.15 ** (6 - count))
        long_weight = (0.15**count) * (0.85 ** (6 - count))
        expected = np.float32(short_weight / (short_weight + long_weight))
        history = (1 << count) - 1
        observed = _posterior(history, int(Panel.PERSISTENT))
        assert observed.view(np.uint32) == expected.view(np.uint32)
        displayed = np.asarray([(history >> bit) & 1 for bit in range(6)], dtype=np.int32)
        learned_channel = learned_tail_channel(
            int(LearnedArm.BELIEF_FEATURE), int(Panel.PERSISTENT), history
        )
        assert learned_channel[0].view(np.uint32) == expected.view(np.uint32)
        native_action = reference_oracle.nonlearned_actions(
            panel=int(Panel.PERSISTENT), displayed_count=count, periods=K_TEST
        )["belief_dp_tail"]
        assert belief_dp_tail(history, int(Panel.PERSISTENT), K_TEST) == native_action
    for panel in (Panel.REDRAW, Panel.SEVERED):
        for history in range(64):
            assert _posterior(history, int(panel)).view(np.uint32) == np.float32(0.5).view(np.uint32)


def test_greedy_tie_raw_permutation_and_decomposition_interfaces() -> None:
    assert greedy_index([1.0, 1.0, 0.0]) == 0
    near = np.nextafter(np.float32(1.0), np.float32(2.0))
    assert greedy_index([np.float32(1.0), near]) == 0
    assert learned_greedy_index([np.float32(1.0), np.float32(1.0)]) == 0
    assert learned_greedy_index([np.float32(1.0), near]) == 1
    assert sorted({len(distinct_permutations(history)) for history in range(64)}) == [1, 6, 15, 20]
    action = raw_permavg_tail_action(
        lambda history: np.asarray([history.bit_count(), 0.0, -1.0, -2.0], dtype=np.float32),
        0b101010,
    )
    assert action == 0
    assert raw_permavg_tail_action(
        lambda _: np.asarray([np.float32(1.0), near, -1.0, -2.0], dtype=np.float32),
        0b101010,
    ) == 1
    values = decomposition(total=1.0, forced=0.8, blind=0.7, immediate=0.72)
    assert set(values) == {"A", "A0", "B", "I", "D", "Gamma", "G"}


def test_fp32_component_and_raw_permavg_fixed_tree_are_bit_exact() -> None:
    for regime in (0, 1):
        for period in K_TEST + K_TRAIN:
            observed = _tail_components(regime, period)
            anchor = 2 if regime == 0 else 8
            period32 = np.float32(period)
            expected = (
                np.float32(
                    np.float32(0.95)
                    - np.float32((period - anchor) ** 2) / np.float32(100.0)
                ),
                np.float32(np.float32(-0.01) * period32),
                np.float32(
                    np.float32(-0.001) * np.float32(period32 * period32)
                ),
            )
            assert [int(value.view(np.uint32)) for value in observed] == [
                int(value.view(np.uint32)) for value in expected
            ]

    history = 0b000111
    permutations = distinct_permutations(history)
    values = np.asarray(
        [
            0.12301533669233322, 0.02987455390393734, -27413.78515625,
            -0.08905918151140213, -45467.078125, -991.6465454101562,
            0.00601436011493206, 0.013402152806520462, -49.22065353393555,
            -0.006204748991876841, 0.04898420348763466, 35.68870162963867,
            105414.25, -93.04680633544922, -2925.18212890625, 695303.1875,
            -134421.453125, -457.6157531738281, -19.01222801208496,
            -128.9537811279297,
        ],
        dtype=np.float32,
    )
    by_history = dict(zip(permutations, values, strict=True))
    tree_mean = np.float32(fixed_fp32_tree(values) / np.float32(len(values)))
    later = np.nextafter(tree_mean, np.float32(np.inf))
    sequential = np.float32(0.0)
    for value in values:
        sequential = np.float32(sequential + value)
    sequential_mean = np.float32(sequential / np.float32(len(values)))
    assert tree_mean < later < sequential_mean
    assert raw_permavg_tail_action(
        lambda item: np.asarray(
            [by_history[item], later, np.float32(-1.0e6), np.float32(-1.0e6)],
            dtype=np.float32,
        ),
        history,
    ) == 1


def test_all_raw_history_encodings_match_declared_y1_through_y6_order() -> None:
    for history in range(64):
        expected = np.asarray(
            [(history >> bit) & 1 for bit in range(6)], dtype=np.float32
        )
        observed = learned_tail_channel(
            int(LearnedArm.RAW), int(Panel.PERSISTENT), history
        )
        assert np.array_equal(observed, expected)


@pytest.mark.parametrize("panel", tuple(Panel))
def test_tail_agreement_normalizes_fp32_tree_roundoff(panel: Panel) -> None:
    cases = tuple(finite_cases(int(panel)))
    weights = np.asarray([case.weight for case in cases], dtype=np.float32)
    assert fixed_fp32_tree(weights) > np.float32(1.0)

    identical = _tail_agreement(int(panel), lambda _: 0, lambda _: 0)
    disjoint = _tail_agreement(int(panel), lambda _: 0, lambda _: 1)

    assert identical.tobytes() == np.float32(1.0).tobytes()
    assert disjoint.tobytes() == np.float32(0.0).tobytes()
    assert 0.0 <= float(identical) <= 1.0
    assert 0.0 <= float(disjoint) <= 1.0


def test_learned_root_and_tail_use_exact_fp32_near_tie_rule(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints"
    root.mkdir()
    slot = validate_checkpoint_inventory(
        _inventory(root), checkpoint_root=root, construction=True
    )[0]
    near = np.nextafter(np.float32(1.0), np.float32(2.0))

    class NearTieScorer:
        def root_logits(self, _: ValidatedCheckpointSlot, periods: tuple[int, ...]) -> np.ndarray:
            return np.asarray([np.float32(1.0), near] + [-1.0] * (len(periods) - 1), dtype=np.float32)

        def tail_logits(
            self, _: ValidatedCheckpointSlot, periods: tuple[int, ...], channel: np.ndarray
        ) -> np.ndarray:
            del channel
            return np.asarray([np.float32(1.0), near] + [-1.0] * (len(periods) - 2), dtype=np.float32)

    endogenous, forced = evaluate_learned_slot(slot, NearTieScorer(), K_TEST)
    assert endogenous.root_action == 1
    assert set(endogenous.tail_actions) == {1}
    assert set(forced.tail_actions) == {1}


def test_support_competence_headroom_threshold_edges() -> None:
    assert validate_support(_support(int(Panel.PERSISTENT)), int(Panel.PERSISTENT))
    assert validate_support(_support(int(Panel.REDRAW)), int(Panel.REDRAW))
    low = copy.deepcopy(_support(int(Panel.PERSISTENT)))
    low["root_visits"][1] = 2047
    low["root_visits"][2] += 10241
    assert validate_support_structure(low, int(Panel.PERSISTENT))
    assert not validate_support(low, int(Panel.PERSISTENT))
    records = {
        int(panel): [
            {"root_match": True, "regret": 0.02, "tail_agreement": 0.95}
            for _ in range(9)
        ]
        + [{"root_match": False, "regret": 0.03, "tail_agreement": 0.94}]
        for panel in Panel
    }
    assert all(validate_competence(records).values())
    headroom = {
        "unique_prior_optimum_margin": 0.02,
        "regime_optima_differ": True,
        "persistent_information": 0.04,
        "persistent_acquisition": 0.03,
        "persistent_direct": -0.02,
        "redraw_information": 0.0,
        "severed_information": 0.0,
        "redraw_immediate_margin": 0.019,
        "severed_immediate_margin": 0.019,
        "all_action_values_finite": True,
        "all_unintended_ties_separated": True,
    }
    assert validate_headroom(headroom)
    assert not validate_headroom({**headroom, "persistent_information": 0.039})


def test_support_requires_exact_keys_and_concrete_nonnegative_integers() -> None:
    valid = _support(int(Panel.PERSISTENT))
    assert validate_support(valid, int(Panel.PERSISTENT))
    malformed: list[dict[str, object]] = []
    for replacement in ("2048", True, 2048.0, 2048.5, -1):
        row = copy.deepcopy(valid)
        row["root_visits"][0] = replacement
        malformed.append(row)
    missing = copy.deepcopy(valid)
    missing.pop("tail_visits")
    malformed.append(missing)
    extra = copy.deepcopy(valid)
    extra["unexpected"] = 1
    malformed.append(extra)
    wrong_balance = copy.deepcopy(valid)
    wrong_balance["balanced_totals"][0] -= 1
    malformed.append(wrong_balance)
    wrong_root_total = copy.deepcopy(valid)
    wrong_root_total["root_visits"][1] += 1
    malformed.append(wrong_root_total)
    wrong_probe_tail = copy.deepcopy(valid)
    wrong_probe_tail["tail_visits"][0] += 1
    malformed.append(wrong_probe_tail)
    wrong_probe_counts = copy.deepcopy(valid)
    wrong_probe_counts["displayed_count_visits"][0] += 1
    malformed.append(wrong_probe_counts)
    for row in malformed:
        assert not validate_support_structure(row, int(Panel.PERSISTENT))
        assert not validate_support(row, int(Panel.PERSISTENT))


@pytest.mark.parametrize(
    ("values", "classification"),
    [
        ([0.04] * 10, "COUNT_ADVANTAGE"),
        ([0.0] * 10, "EQUIVALENT"),
        ([-0.04] * 10, "RAW_SUPERIOR"),
        ([0.02, 0.04] * 5, "UNRESOLVED"),
    ],
)
def test_paired_interval_classifier(values: list[float], classification: str) -> None:
    assert paired_t_interval(values).classification == classification


def test_acquisition_gate_and_exhaustive_attribution_map() -> None:
    flags = [True] * 10
    assert acquisition_supported(
        [0.01] * 10,
        persistent_probe=flags,
        redraw_immediate=flags,
        severed_immediate=flags,
        support_pass=True,
        competence_pass=True,
    )
    assert not acquisition_supported(
        [0.01] * 10,
        persistent_probe=[False] + flags[1:],
        redraw_immediate=flags,
        severed_immediate=flags,
        support_pass=True,
        competence_pass=True,
    )
    cases = (
        ("EQUIVALENT", "COUNT_ADVANTAGE", "COUNT_ADVANTAGE"),
        ("UNRESOLVED", "COUNT_ADVANTAGE", "COUNT_ADVANTAGE"),
        ("COUNT_ADVANTAGE", "RAW_SUPERIOR", "COUNT_ADVANTAGE"),
        ("COUNT_ADVANTAGE", "UNRESOLVED", "COUNT_ADVANTAGE"),
        ("COUNT_ADVANTAGE", "COUNT_ADVANTAGE", "EQUIVALENT"),
        ("COUNT_ADVANTAGE", "COUNT_ADVANTAGE", "UNRESOLVED"),
        ("COUNT_ADVANTAGE", "COUNT_ADVANTAGE", "COUNT_ADVANTAGE"),
    )
    results = [attribution_map(True, *case) for case in cases]
    assert len({result["branch"] for result in results}) == 7
    assert [result["successor_eligible"] for result in results] == [False] * 6 + [True]
    multiple = attribution_map(True, "EQUIVALENT", "UNRESOLVED", "RAW_SUPERIOR")
    assert len(multiple["labels"]) == 3


def test_exact_terminal_action_map() -> None:
    assert terminal_action_class(complete=False, invariant_pass=True, support_pass=True, competence_pass=True, acquisition=True).startswith("PREACTIVITY")
    assert terminal_action_class(complete=True, invariant_pass=False, support_pass=True, competence_pass=True, acquisition=True).startswith("PREACTIVITY")
    assert "SUPPORT" in terminal_action_class(complete=True, invariant_pass=True, support_pass=False, competence_pass=True, acquisition=True)
    assert "COMPETENCE" in terminal_action_class(complete=True, invariant_pass=True, support_pass=True, competence_pass=False, acquisition=True)
    assert "ACQUISITION" in terminal_action_class(complete=True, invariant_pass=True, support_pass=True, competence_pass=True, acquisition=False)
    assert "SEVEN_BRANCH" in terminal_action_class(complete=True, invariant_pass=True, support_pass=True, competence_pass=True, acquisition=True)


def test_structurally_empty_package_can_never_validate_or_gain_a_manifest() -> None:
    package = _minimal_private_package()
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_INVENTORY.value):
        validate_complete_package(package)
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        build_completion_manifest(package, request=REGISTERED_PUBLICATION)


def test_atomic_complete_only_transition_and_publication_firewall(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    interrupted = output / "interrupted"
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        synthetic_atomic_transition(
            destination=interrupted,
            output_root=output,
            complete=True,
            interrupt_before_manifest=True,
        )
    assert not interrupted.exists()
    assert not list(output.glob(".*.pending-*"))
    complete = output / "complete"
    assert synthetic_atomic_transition(destination=complete, output_root=output, complete=True) == "ATOMIC_COMPLETE"
    assert sorted(path.name for path in complete.iterdir()) == ["completion.json", "opaque.private"]
    with pytest.raises(S2Refusal, match=S2Code.ALREADY_PUBLISHED.value):
        synthetic_atomic_transition(destination=complete, output_root=output, complete=True)
    with pytest.raises(S2Refusal, match=S2Code.REGISTERED_BOUNDARY_ATTEMPTED.value):
        publish_complete_package(
            _minimal_private_package(),
            destination=output / "forbidden",
            output_root=output,
            request=CONSTRUCTION,
        )


def test_real_atomic_publication_core_survives_abrupt_subprocess_boundaries(tmp_path: Path) -> None:
    module = "experiments.candidates.ucope.variable_k_paid_probe_r01_r03.s2_construction"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    precommit = (
        "after_open", "after_partial_write", "after_full_write", "after_flush", "after_rename"
    )
    for boundary in precommit:
        root = tmp_path / boundary
        root.mkdir()
        completed = subprocess.run(
            [
                sys.executable, "-B", "-m", module,
                "--atomic-fixture-root", str(root), "--interrupt-at", boundary,
            ],
            cwd=Path(__file__).resolve().parents[4],
            env=env,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 97
        observed_residue = tuple(root.iterdir())
        assert len(observed_residue) <= 1
        for residue in observed_residue:
            with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
                read_atomic_sealed_blob(residue)
        retry = subprocess.run(
            [sys.executable, "-B", "-m", module, "--atomic-fixture-root", str(root)],
            cwd=Path(__file__).resolve().parents[4],
            env=env,
            capture_output=True,
            check=False,
        )
        assert retry.returncode == 0
        final = root / "synthetic-sealed-object.json"
        assert json.loads(read_atomic_sealed_blob(final))["technical_complete"] is True
        for residue in root.iterdir():
            if residue != final:
                with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
                    read_atomic_sealed_blob(residue)

    committed_root = tmp_path / "after_commit"
    committed_root.mkdir()
    committed = subprocess.run(
        [
            sys.executable, "-B", "-m", module,
            "--atomic-fixture-root", str(committed_root), "--interrupt-at", "after_commit",
        ],
        cwd=Path(__file__).resolve().parents[4],
        env=env,
        capture_output=True,
        check=False,
    )
    assert committed.returncode == 97
    committed_files = tuple(committed_root.iterdir())
    assert len(committed_files) == 1
    assert json.loads(read_atomic_sealed_blob(committed_files[0]))["question_relevant_output"] is False

    success_root = tmp_path / "success"
    success_root.mkdir()
    success = subprocess.run(
        [sys.executable, "-B", "-m", module, "--atomic-fixture-root", str(success_root)],
        cwd=Path(__file__).resolve().parents[4],
        env=env,
        capture_output=True,
        check=False,
    )
    assert success.returncode == 0
    success_files = tuple(success_root.iterdir())
    assert len(success_files) == 1
    assert json.loads(read_atomic_sealed_blob(success_files[0]))["technical_complete"] is True


def test_full_90_slot_private_evaluator_is_structurally_complete(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints"
    root.mkdir()
    sealed = evaluate_complete_private(
        _inventory(root),
        checkpoint_root=root,
        scorer=_SyntheticScorer(),
        request=CONSTRUCTION,
    )
    package = sealed.package
    assert validate_sealed_evaluation(sealed, request=CONSTRUCTION) is package
    assert validate_complete_package(package) == tuple(sorted(REQUIRED_TOP_LEVEL_FIELDS))
    assert len(package["checkpoint_inventory"]) == 90
    assert len(package["k_test_values"]) == 90
    assert len(package["k_train_values"]) == 90
    assert len(package["forced_test_values"]) == 90
    assert len(package["raw_permavg_values"]) == 10
    action_values = package["belief_dp_action_values"]
    assert set(action_values["root"]) == {"0", "1", "2"}
    assert all(len(row["values"]) == 5 for row in action_values["root"].values())
    assert sum(len(histories) for histories in action_values["tail"].values()) == 3 * 64
    assert all(
        len(row["values"]) == 4
        for histories in action_values["tail"].values()
        for row in histories.values()
    )
    assert all(len(record["tail_actions"]) == 64 for record in package["k_test_values"].values())
    assert all(len(record["tail_actions"]) == 64 for record in package["forced_test_values"].values())
    with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
        build_completion_manifest(package, request=REGISTERED_PUBLICATION)

    post_evaluation_mutation = copy.deepcopy(package)
    post_evaluation_mutation["terminal_action"] = "MUTATED"
    with pytest.raises(
        S2Refusal,
        match=f"{S2Code.CHECKPOINT_MISMATCH.value}|{S2Code.DUPLICATE_SLOT.value}",
    ):
        validate_sealed_evaluation(
            dataclasses.replace(sealed, package=post_evaluation_mutation),
            request=CONSTRUCTION,
        )

    substituted_inventory = list(sealed.inventory)
    substituted_inventory[0] = dataclasses.replace(
        substituted_inventory[0], path=substituted_inventory[1].path
    )
    with pytest.raises(
        S2Refusal,
        match=f"{S2Code.CHECKPOINT_MISMATCH.value}|{S2Code.DUPLICATE_SLOT.value}",
    ):
        validate_sealed_evaluation(
            dataclasses.replace(sealed, inventory=tuple(substituted_inventory)),
            request=CONSTRUCTION,
        )

    first_checkpoint = sealed.inventory[0].path
    original_checkpoint = first_checkpoint.read_bytes()
    first_checkpoint.write_bytes(original_checkpoint + b"post-evaluation-mutation")
    try:
        with pytest.raises(S2Refusal, match=S2Code.CHECKPOINT_MISMATCH.value):
            validate_sealed_evaluation(sealed, request=CONSTRUCTION)
    finally:
        first_checkpoint.write_bytes(original_checkpoint)

    wrong_cardinality = copy.deepcopy(package)
    wrong_cardinality["k_test_values"].pop(next(iter(wrong_cardinality["k_test_values"])))
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(wrong_cardinality)

    missing_actions = copy.deepcopy(package)
    next(iter(missing_actions["forced_test_values"].values()))["tail_actions"].pop()
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(missing_actions)

    inconsistent_value = copy.deepcopy(package)
    next(iter(inconsistent_value["k_train_values"].values()))["total"] += 1.0
    with pytest.raises(S2Refusal, match=S2Code.DECOMPOSITION_FAILURE.value):
        validate_complete_package(inconsistent_value)

    inconsistent_decomposition = copy.deepcopy(package)
    first_decomposition = next(
        value
        for key, value in inconsistent_decomposition["decompositions"].items()
        if key != "all_identities_hold"
    )
    first_decomposition["Gamma"] += 1.0
    with pytest.raises(S2Refusal, match=S2Code.DECOMPOSITION_FAILURE.value):
        validate_complete_package(inconsistent_decomposition)

    inconsistent_interval = copy.deepcopy(package)
    inconsistent_interval["intervals"]["delta_test"]["classification"] = "INVALID"
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(inconsistent_interval)

    derived_contrast = copy.deepcopy(package)
    contrast_rows = derived_contrast["seed_contrasts"]["delta_test"]
    contrast_rows[next(iter(contrast_rows))] += 0.001
    recalculated = paired_t_interval(list(contrast_rows.values()))
    derived_contrast["intervals"]["delta_test"] = {
        "mean": recalculated.mean,
        "lower": recalculated.lower,
        "upper": recalculated.upper,
        "classification": recalculated.classification,
    }
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(derived_contrast)

    derived_margin = copy.deepcopy(package)
    margin_rows = derived_margin["acquisition"]["margins"]
    margin_rows[next(iter(margin_rows))] += 0.001
    derived_margin["acquisition"]["lower"] = one_sided_lower(list(margin_rows.values()))
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(derived_margin)

    derived_competence = copy.deepcopy(package)
    competence_records = derived_competence["competence"]["records"]
    first_panel_records = next(iter(competence_records.values()))
    first_competence = next(iter(first_panel_records.values()))
    first_competence["root_match"] = not first_competence["root_match"]
    recomputed_gates = validate_competence(
        {int(panel): list(records.values()) for panel, records in competence_records.items()}
    )
    derived_competence["competence"]["gates"] = {
        str(panel): passed for panel, passed in recomputed_gates.items()
    }
    derived_competence["competence"]["pass"] = all(recomputed_gates.values())
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(derived_competence)

    derived_agreement = copy.deepcopy(package)
    first_agreement = next(iter(derived_agreement["descriptive_agreements"].values()))
    first_agreement["count"] = (
        first_agreement["count"] + 0.001
        if first_agreement["count"] <= 0.999
        else first_agreement["count"] - 0.001
    )
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(derived_agreement)

    derived_headroom = copy.deepcopy(package)
    derived_headroom["headroom"]["persistent_information"] += 0.001
    assert validate_headroom(derived_headroom["headroom"])
    derived_headroom["headroom"]["pass"] = True
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(derived_headroom)

    deleted_action_vector = copy.deepcopy(package)
    deleted_action_vector["belief_dp_action_values"]["tail"]["0"].pop("0")
    deleted_action_vector["provenance"] = _package_provenance(deleted_action_vector)
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(deleted_action_vector)

    extra_action_vector = copy.deepcopy(package)
    extra_action_vector["belief_dp_action_values"]["tail"]["0"]["64"] = copy.deepcopy(
        extra_action_vector["belief_dp_action_values"]["tail"]["0"]["63"]
    )
    extra_action_vector["provenance"] = _package_provenance(extra_action_vector)
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(extra_action_vector)

    nonfinite_action_vector = copy.deepcopy(package)
    nonfinite_action_vector["belief_dp_action_values"]["tail"]["0"]["0"]["values"][0] = float("nan")
    with pytest.raises(S2Refusal, match=S2Code.NONFINITE_OUTPUT.value):
        validate_complete_package(nonfinite_action_vector)

    synchronized_action_vector = copy.deepcopy(package)
    synchronized_action_vector["belief_dp_action_values"]["tail"]["0"]["0"]["values"][0] += 5.0e-7
    synchronized_action_vector["headroom"]["all_action_values_finite"] = True
    synchronized_action_vector["headroom"]["all_unintended_ties_separated"] = True
    synchronized_action_vector["provenance"] = _package_provenance(synchronized_action_vector)
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(synchronized_action_vector)

    inconsistent_support = copy.deepcopy(package)
    first_support = next(iter(inconsistent_support["support"]["slots"].values()))
    first_support["pass"] = not first_support["pass"]
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(inconsistent_support)

    inconsistent_terminal = copy.deepcopy(package)
    inconsistent_terminal["terminal_action"] = "INVALID"
    with pytest.raises(S2Refusal, match=S2Code.INCOMPLETE_OUTPUT.value):
        validate_complete_package(inconsistent_terminal)

    nonfinite = copy.deepcopy(package)
    next(iter(nonfinite["k_test_values"].values()))["components"][0] = float("nan")
    with pytest.raises(S2Refusal, match=S2Code.NONFINITE_OUTPUT.value):
        validate_complete_package(nonfinite)


def test_structurally_valid_low_support_reaches_terminal_support_failure(
    tmp_path: Path,
) -> None:
    root = tmp_path / "low-support-checkpoints"
    root.mkdir()
    slots = _inventory(root)
    low = copy.deepcopy(_support(int(Panel.PERSISTENT)))
    low["root_visits"][1] = 2047
    low["root_visits"][2] += 10241
    assert validate_support_structure(low, int(Panel.PERSISTENT))
    assert not validate_support(low, int(Panel.PERSISTENT))
    slots[0].path.write_bytes(
        build_synthetic_checkpoint_bytes(
            arm=int(LearnedArm.COUNT),
            panel=int(Panel.PERSISTENT),
            master_seed=SYNTHETIC_SEEDS[0],
            support=low,
            model_payload=b"synthetic-model-0-0-0",
            request=CONSTRUCTION,
        )
    )
    sealed = evaluate_complete_private(
        slots,
        checkpoint_root=root,
        scorer=_SyntheticScorer(),
        request=CONSTRUCTION,
    )
    assert sealed.package["support"]["pass"] is False
    assert sealed.package["terminal_action"] == "TERMINAL_SUPPORT_FAILURE"
    assert validate_complete_package(sealed.package)


def test_counts_only_structural_proxy_firewall() -> None:
    proxy = structural_proxy(REPAIR1_NAMESPACE)
    assert proxy["fixture_namespace"] == REPAIR1_NAMESPACE
    assert proxy["registered_master_seeds"] is False
    assert proxy["complete_registered_panel"] is False
    assert proxy["question_relevant_output"] is False
    assert proxy["gpu"] is False
    assert proxy["checkpoint_slot_count"] == 90
    assert proxy["attribution_branch_count"] == 7
    forbidden = {
        "J", "A", "A0", "B", "I", "D", "Gamma", "G", "M",
        "intervals", "attribution", "successor_eligible", "complete_r03_package",
    }
    assert forbidden.isdisjoint(proxy)
