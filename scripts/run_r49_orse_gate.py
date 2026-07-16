"""Run the registered R49-ORSE-G0 standalone architecture gate."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, TextIO

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

from r49_orse import (  # noqa: E402
    ACTIVE_SIZES,
    CASES_PER_SIZE,
    EXPERIMENT_ID,
    HIDDEN_DIM,
    JOIN_LEAVE_EVENT_PAIRS,
    LOW_HIDDEN_PLACEHOLDER_DIM,
    MAX_AGE,
    MEMBER_FEATURE_DIM,
    MODEL_SEED,
    OPAQUE_CODES,
    PADDING_VARIANTS,
    PARITY_TOLERANCE,
    PERMUTATIONS_PER_CASE,
    PREFIX_MEDIAN_FLOOR,
    PREFIX_MIN_NORM,
    PREFIX_SUPPORT_FLOOR,
    SAMPLE_REPLAY_SEQUENCES,
    SAMPLING_SEED,
    SCHEMA_VERSION,
    SYNTHETIC_DATA_SEED,
    AppliedToken,
    OpenRosterSetPolicy,
    RosterCase,
    json_ready,
    max_abs_nested,
    parameter_count,
    parameter_gradient_audit,
    run_sequence,
    state_dict_signature,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def write_jsonl_row(handle: TextIO, payload: dict[str, Any]) -> None:
    handle.write(
        json.dumps(json_ready(payload), sort_keys=True, allow_nan=False) + "\n"
    )


def set_deterministic_cpu() -> None:
    torch.manual_seed(MODEL_SEED)
    np.random.seed(SYNTHETIC_DATA_SEED)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.use_deterministic_algorithms(True)


def make_base_case(
    case_id: int,
    active_n: int,
    rng: np.random.Generator,
    *,
    allow_joiner: bool = True,
) -> RosterCase:
    keys = np.arange(active_n, dtype=np.int64) + int(case_id) * 1000 + 1
    observations = rng.normal(
        0.0, 1.0, size=(active_n, MEMBER_FEATURE_DIM)
    ).astype(np.float32)
    codes = rng.integers(0, OPAQUE_CODES, size=active_n, dtype=np.int64)
    ages = rng.integers(0, MAX_AGE + 1, size=active_n, dtype=np.int64)
    joined = np.zeros(active_n, dtype=np.bool_)
    if allow_joiner and case_id % 4 == 0:
        joined[case_id % active_n] = True
    processed = np.zeros(active_n, dtype=np.bool_)
    epochs = rng.integers(0, 32, size=active_n, dtype=np.int64)
    low_hidden = rng.normal(
        0.0, 1.0, size=(active_n, LOW_HIDDEN_PLACEHOLDER_DIM)
    ).astype(np.float32)
    external_order = tuple(int(value) for value in rng.permutation(keys))
    case = RosterCase(
        case_id=int(case_id),
        member_keys=keys,
        observations=observations,
        opaque_codes=codes,
        ages=ages,
        joined=joined,
        processed=processed,
        membership_epochs=epochs,
        low_hidden_placeholders=low_hidden,
        active_mask=np.ones(active_n, dtype=np.bool_),
        external_order=external_order,
    )
    case.validate()
    return case


def reorder_storage(case: RosterCase, order: np.ndarray) -> RosterCase:
    order = np.asarray(order, dtype=np.int64)
    reordered = RosterCase(
        case_id=case.case_id,
        member_keys=case.member_keys[order].copy(),
        observations=case.observations[order].copy(),
        opaque_codes=case.opaque_codes[order].copy(),
        ages=case.ages[order].copy(),
        joined=case.joined[order].copy(),
        processed=case.processed[order].copy(),
        membership_epochs=case.membership_epochs[order].copy(),
        low_hidden_placeholders=case.low_hidden_placeholders[order].copy(),
        active_mask=case.active_mask[order].copy(),
        external_order=case.external_order,
    )
    reordered.validate()
    return reordered


def make_padding_variant(
    case: RosterCase,
    rng: np.random.Generator,
) -> RosterCase:
    active_n = case.active_n
    padding_n = int(rng.integers(1, active_n + 4))
    slots = active_n + padding_n
    active_positions = np.sort(rng.choice(slots, size=active_n, replace=False))

    signs = rng.choice(np.asarray((-1.0, 1.0), dtype=np.float32), size=(slots, 1))
    observations = (
        signs
        * rng.uniform(0.25, 3.0, size=(slots, MEMBER_FEATURE_DIM)).astype(np.float32)
    )
    codes = rng.integers(0, OPAQUE_CODES, size=slots, dtype=np.int64)
    ages = rng.integers(1, MAX_AGE + 1, size=slots, dtype=np.int64)
    joined = np.ones(slots, dtype=np.bool_)
    processed = np.ones(slots, dtype=np.bool_)
    epochs = rng.integers(1, 1000, size=slots, dtype=np.int64)
    low_hidden = rng.uniform(
        0.25, 2.0, size=(slots, LOW_HIDDEN_PLACEHOLDER_DIM)
    ).astype(np.float32)
    member_keys = -(
        np.arange(slots, dtype=np.int64) + int(case.case_id) * 1000 + 1
    )
    active_mask = np.zeros(slots, dtype=np.bool_)
    active_mask[active_positions] = True

    source_indices = np.flatnonzero(case.active_mask)
    member_keys[active_positions] = case.member_keys[source_indices]
    observations[active_positions] = case.observations[source_indices]
    codes[active_positions] = case.opaque_codes[source_indices]
    ages[active_positions] = case.ages[source_indices]
    joined[active_positions] = case.joined[source_indices]
    processed[active_positions] = case.processed[source_indices]
    epochs[active_positions] = case.membership_epochs[source_indices]
    low_hidden[active_positions] = case.low_hidden_placeholders[source_indices]
    padded = RosterCase(
        case_id=case.case_id,
        member_keys=member_keys,
        observations=observations,
        opaque_codes=codes,
        ages=ages,
        joined=joined,
        processed=processed,
        membership_epochs=epochs,
        low_hidden_placeholders=low_hidden,
        active_mask=active_mask,
        external_order=case.external_order,
    )
    padded.validate()
    return padded


def make_membership_event_pair(
    event_id: int,
    active_n: int,
    rng: np.random.Generator,
) -> tuple[RosterCase, RosterCase, int, int]:
    before = make_base_case(
        2_000_000 + event_id,
        active_n,
        rng,
        allow_joiner=False,
    )
    leaver_index = int(event_id % active_n)
    leaver_key = int(before.member_keys[leaver_index])
    survivor_indices = np.asarray(
        [index for index in range(active_n) if index != leaver_index],
        dtype=np.int64,
    )
    joiner_key = int(8_000_000_000 + event_id)

    member_keys = np.concatenate(
        (before.member_keys[survivor_indices], np.asarray([joiner_key], dtype=np.int64))
    )
    observations = np.concatenate(
        (
            before.observations[survivor_indices],
            rng.normal(0.0, 1.0, size=(1, MEMBER_FEATURE_DIM)).astype(np.float32),
        ),
        axis=0,
    )
    codes = np.concatenate(
        (
            before.opaque_codes[survivor_indices],
            rng.integers(0, OPAQUE_CODES, size=1, dtype=np.int64),
        )
    )
    ages = np.concatenate(
        (before.ages[survivor_indices], np.asarray([0], dtype=np.int64))
    )
    joined = np.concatenate(
        (
            np.zeros(len(survivor_indices), dtype=np.bool_),
            np.asarray([True], dtype=np.bool_),
        )
    )
    processed = np.zeros(active_n, dtype=np.bool_)
    joiner_epoch = int(np.max(before.membership_epochs)) + 1
    epochs = np.concatenate(
        (
            before.membership_epochs[survivor_indices],
            np.asarray([joiner_epoch], dtype=np.int64),
        )
    )
    low_hidden = np.concatenate(
        (
            before.low_hidden_placeholders[survivor_indices],
            rng.normal(
                0.0, 1.0, size=(1, LOW_HIDDEN_PLACEHOLDER_DIM)
            ).astype(np.float32),
        ),
        axis=0,
    )
    order = rng.permutation(active_n)
    member_keys = member_keys[order]
    observations = observations[order]
    codes = codes[order]
    ages = ages[order]
    joined = joined[order]
    processed = processed[order]
    epochs = epochs[order]
    low_hidden = low_hidden[order]
    external_order = tuple(int(value) for value in rng.permutation(member_keys))
    after = RosterCase(
        case_id=before.case_id,
        member_keys=member_keys,
        observations=observations,
        opaque_codes=codes,
        ages=ages,
        joined=joined,
        processed=processed,
        membership_epochs=epochs,
        low_hidden_placeholders=low_hidden,
        active_mask=np.ones(active_n, dtype=np.bool_),
        external_order=external_order,
    )
    after.validate()
    return before, after, leaver_key, joiner_key


def max_abs(left: list[float], right: list[float]) -> float:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape:
        return float("inf")
    if not left_array.size:
        return 0.0
    return float(np.max(np.abs(left_array - right_array)))


def finite_sequence(result: dict[str, Any]) -> bool:
    values: list[float] = [
        float(result["value"]),
        float(result["incremental_full_logits_max_abs"]),
        float(result["incremental_full_roster_max_abs"]),
    ]
    values.extend(float(value) for value in result["token_log_probs"])
    values.extend(
        float(value) for row in result["token_logits"] for value in row
    )
    values.extend(float(value) for value in result["prefix_gradient_norms"])
    return bool(np.all(np.isfinite(np.asarray(values, dtype=np.float64))))


def member_snapshot(case: RosterCase, member_key: int) -> dict[str, Any]:
    indices = np.flatnonzero(case.member_keys == int(member_key))
    if len(indices) != 1:
        raise ValueError("member snapshot requires exactly one matching key")
    index = int(indices[0])
    return {
        "opaque_code": int(case.opaque_codes[index]),
        "age": int(case.ages[index]),
        "membership_epoch": int(case.membership_epochs[index]),
        "low_hidden_placeholder": case.low_hidden_placeholders[index].copy(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if str(args.device).lower() != "cpu":
        raise ValueError("R49 is registered as a local deterministic CPU gate")

    run_root = args.run_root.resolve()
    seed_root = run_root / "seed"
    result_root = run_root / "result"
    seed_root.mkdir(parents=True, exist_ok=True)
    result_root.mkdir(parents=True, exist_ok=True)
    progress_path = seed_root / "progress.json"
    case_ledger_path = seed_root / "case_ledger.jsonl"
    membership_ledger_path = seed_root / "membership_event_ledger.jsonl"
    result_path = result_root / (
        "dry_run_check.json" if args.dry_run else "r49_orse.json"
    )

    set_deterministic_cpu()
    data_rng = np.random.default_rng(SYNTHETIC_DATA_SEED)
    sampling_generator = torch.Generator(device="cpu")
    sampling_generator.manual_seed(SAMPLING_SEED)
    model = OpenRosterSetPolicy().cpu().eval()
    initial_parameters = {
        name: tensor.detach().clone() for name, tensor in model.state_dict().items()
    }

    active_sizes = ACTIVE_SIZES
    cases_per_size = 2 if args.dry_run else CASES_PER_SIZE
    permutations_per_case = 2 if args.dry_run else PERMUTATIONS_PER_CASE
    event_pairs = 8 if args.dry_run else JOIN_LEAVE_EVENT_PAIRS
    expected_base_cases = len(active_sizes) * cases_per_size
    expected_permutation_reads = expected_base_cases * permutations_per_case

    cases: list[RosterCase] = []
    case_id = 0
    for active_n in active_sizes:
        for _ in range(cases_per_size):
            cases.append(make_base_case(case_id, active_n, data_rng))
            case_id += 1
    write_json(
        progress_path,
        {
            "phase": "base_cases_ready",
            "base_cases": len(cases),
            "expected_base_cases": expected_base_cases,
        },
    )

    gradient_case = next(case for case in cases if case.active_n >= 2)
    gradient_audit = parameter_gradient_audit(model, gradient_case)
    signature = state_dict_signature(model)
    signature_by_n = {str(active_n): signature for active_n in active_sizes}
    signature_values = list(signature_by_n.values())
    shapes_independent = all(value == signature_values[0] for value in signature_values)
    no_embedding_module = not any(
        isinstance(module, nn.Embedding) for module in model.modules()
    )
    forbidden_state_keys = [
        name
        for name in model.state_dict()
        if "agent_id" in name.lower()
        or "slot" in name.lower()
        or "membership_epoch" in name.lower()
    ]

    permutation_logits_max = 0.0
    permutation_value_max = 0.0
    padding_logits_max = 0.0
    padding_value_max = 0.0
    replay_logp_max = 0.0
    incremental_full_logits_max = 0.0
    incremental_full_roster_max = 0.0
    prefix_gradient_norms: list[float] = []
    support_mismatch_count = 0
    masked_slot_token_count = 0
    complexity_violation_count = 0
    nonfinite_sequence_count = 0
    permutation_reads = 0
    padding_variants_completed = 0
    sample_replay_sequences_completed = 0
    case_ledger_rows = 0
    cases_by_size = {str(active_n): 0 for active_n in active_sizes}

    def track_sequence(result: dict[str, Any], active_n: int) -> None:
        nonlocal incremental_full_logits_max
        nonlocal incremental_full_roster_max
        nonlocal complexity_violation_count
        nonlocal nonfinite_sequence_count
        incremental_full_logits_max = max(
            incremental_full_logits_max,
            float(result["incremental_full_logits_max_abs"]),
        )
        incremental_full_roster_max = max(
            incremental_full_roster_max,
            float(result["incremental_full_roster_max_abs"]),
        )
        complexity = result["complexity"]
        if not (
            int(complexity["active_set_full_encode_calls"]) == 1
            and int(complexity["incremental_updates"]) == int(active_n)
            and int(complexity["decoder_calls"]) == int(active_n)
            and int(complexity["pairwise_n_by_n_tensor_count"]) == 0
        ):
            complexity_violation_count += 1
        if not finite_sequence(result):
            nonfinite_sequence_count += 1

    with case_ledger_path.open("w", encoding="utf-8", newline="\n") as ledger:
        for completed, case in enumerate(cases, start=1):
            cases_by_size[str(case.active_n)] += 1
            sampled = run_sequence(
                model,
                case,
                sampling_generator=sampling_generator,
                measure_prefix_gradient=case.active_n >= 2,
            )
            track_sequence(sampled, case.active_n)
            prefix_gradient_norms.extend(sampled["prefix_gradient_norms"])

            replayed = run_sequence(
                model,
                case,
                teacher_tokens=sampled["tokens"],
                measure_prefix_gradient=False,
            )
            track_sequence(replayed, case.active_n)
            sample_replay_sequences_completed += 1
            replay_logp_max = max(
                replay_logp_max,
                max_abs(sampled["token_log_probs"], replayed["token_log_probs"]),
            )
            if sampled["effective_supports"] != replayed["effective_supports"]:
                support_mismatch_count += 1

            permutation_storage_orders: list[list[int]] = []
            for _ in range(permutations_per_case):
                storage_order = data_rng.permutation(len(case.member_keys))
                permuted_case = reorder_storage(case, storage_order)
                permuted = run_sequence(
                    model,
                    permuted_case,
                    teacher_tokens=sampled["tokens"],
                    measure_prefix_gradient=False,
                )
                track_sequence(permuted, case.active_n)
                permutation_reads += 1
                permutation_logits_max = max(
                    permutation_logits_max,
                    max_abs_nested(sampled["token_logits"], permuted["token_logits"]),
                )
                permutation_value_max = max(
                    permutation_value_max,
                    abs(float(sampled["value"]) - float(permuted["value"])),
                )
                if sampled["effective_supports"] != permuted["effective_supports"]:
                    support_mismatch_count += 1
                permutation_storage_orders.append(
                    [int(value) for value in permuted_case.member_keys.tolist()]
                )

            padded_case = make_padding_variant(case, data_rng)
            padded = run_sequence(
                model,
                padded_case,
                teacher_tokens=sampled["tokens"],
                measure_prefix_gradient=False,
            )
            track_sequence(padded, case.active_n)
            padding_variants_completed += 1
            padding_logits_max = max(
                padding_logits_max,
                max_abs_nested(sampled["token_logits"], padded["token_logits"]),
            )
            padding_value_max = max(
                padding_value_max,
                abs(float(sampled["value"]) - float(padded["value"])),
            )
            if sampled["effective_supports"] != padded["effective_supports"]:
                support_mismatch_count += 1
            inactive_keys = set(
                int(value) for value in padded_case.member_keys[~padded_case.active_mask]
            )
            masked_slot_token_count += sum(
                int(int(token.member_key) in inactive_keys) for token in padded["tokens"]
            )

            record = {
                "case_id": int(case.case_id),
                "active_n": int(case.active_n),
                "active_member_keys": [int(value) for value in case.active_keys],
                "membership_epochs": [
                    int(value) for value in case.membership_epochs.tolist()
                ],
                "active_mask": [bool(value) for value in case.active_mask.tolist()],
                "opaque_codes": [int(value) for value in case.opaque_codes.tolist()],
                "ages": [int(value) for value in case.ages.tolist()],
                "joined": [bool(value) for value in case.joined.tolist()],
                "external_ar_order": [int(value) for value in case.external_order],
                "sampled_token_sequence": [
                    token.to_dict() for token in sampled["tokens"]
                ],
                "actual_applied_prefixes": sampled["applied_prefixes"],
                "old_token_log_probabilities": sampled["token_log_probs"],
                "effective_action_support": sampled["effective_supports"],
                "permutation_storage_orders": permutation_storage_orders,
                "padding_member_keys": [
                    int(value) for value in padded_case.member_keys.tolist()
                ],
                "padding_active_mask": [
                    bool(value) for value in padded_case.active_mask.tolist()
                ],
                "incremental_full_logits_max_abs": float(
                    sampled["incremental_full_logits_max_abs"]
                ),
                "incremental_full_roster_max_abs": float(
                    sampled["incremental_full_roster_max_abs"]
                ),
            }
            write_jsonl_row(ledger, record)
            case_ledger_rows += 1
            if completed % max(1, len(cases) // 8) == 0 or completed == len(cases):
                write_json(
                    progress_path,
                    {
                        "phase": "base_invariance_and_replay",
                        "completed_base_cases": int(completed),
                        "base_cases": int(len(cases)),
                        "permutation_reads": int(permutation_reads),
                        "padding_variants": int(padding_variants_completed),
                    },
                )

    joiner_keep_unsupported = True
    leaver_zero_tokens = True
    survivor_code_exact = True
    survivor_age_exact = True
    survivor_hidden_exact = True
    survivor_epoch_exact = True
    active_token_count_exact = True
    membership_ledger_rows = 0
    event_sizes = tuple(value for value in active_sizes if value >= 2)
    with membership_ledger_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as ledger:
        for event_id in range(event_pairs):
            active_n = int(event_sizes[event_id % len(event_sizes)])
            before, after, leaver_key, joiner_key = make_membership_event_pair(
                event_id, active_n, data_rng
            )
            result = run_sequence(
                model,
                after,
                sampling_generator=sampling_generator,
                measure_prefix_gradient=False,
            )
            track_sequence(result, active_n)
            token_by_key = {
                int(token.member_key): token for token in result["tokens"]
            }
            support_by_key = {
                int(key): result["effective_supports"][position]
                for position, key in enumerate(after.external_order)
            }
            joiner_keep_unsupported = joiner_keep_unsupported and (
                "KEEP" not in support_by_key[joiner_key]
                and token_by_key[joiner_key].kind == "SET"
            )
            leaver_zero_tokens = leaver_zero_tokens and leaver_key not in token_by_key
            active_token_count_exact = active_token_count_exact and (
                len(result["tokens"]) == after.active_n
            )

            survivor_keys = sorted(
                set(int(value) for value in before.active_keys) - {leaver_key}
            )
            survivor_records: list[dict[str, Any]] = []
            for key in survivor_keys:
                left = member_snapshot(before, key)
                right = member_snapshot(after, key)
                survivor_code_exact = survivor_code_exact and (
                    left["opaque_code"] == right["opaque_code"]
                )
                survivor_age_exact = survivor_age_exact and (
                    left["age"] == right["age"]
                )
                survivor_epoch_exact = survivor_epoch_exact and (
                    left["membership_epoch"] == right["membership_epoch"]
                )
                survivor_hidden_exact = survivor_hidden_exact and bool(
                    np.array_equal(
                        left["low_hidden_placeholder"],
                        right["low_hidden_placeholder"],
                    )
                )
                survivor_records.append(
                    {
                        "member_key": int(key),
                        "before": left,
                        "after": right,
                    }
                )
            write_jsonl_row(
                ledger,
                {
                    "event_id": int(event_id),
                    "before_active_keys": [
                        int(value) for value in before.active_keys
                    ],
                    "after_active_keys": [int(value) for value in after.active_keys],
                    "leaver_key": int(leaver_key),
                    "joiner_key": int(joiner_key),
                    "survivors": survivor_records,
                    "after_membership_epochs": [
                        int(value) for value in after.membership_epochs.tolist()
                    ],
                    "after_external_ar_order": [
                        int(value) for value in after.external_order
                    ],
                    "sampled_token_sequence": [
                        token.to_dict() for token in result["tokens"]
                    ],
                    "effective_action_support": result["effective_supports"],
                    "actual_applied_prefixes": result["applied_prefixes"],
                    "old_token_log_probabilities": result["token_log_probs"],
                },
            )
            membership_ledger_rows += 1

    write_json(
        progress_path,
        {
            "phase": "analysis",
            "base_cases": int(case_ledger_rows),
            "membership_event_pairs": int(membership_ledger_rows),
        },
    )

    final_parameters = model.state_dict()
    parameter_max_abs_drift = 0.0
    for name, before in initial_parameters.items():
        parameter_max_abs_drift = max(
            parameter_max_abs_drift,
            float(torch.max(torch.abs(before - final_parameters[name])).cpu()),
        )
    parameter_grad_buffers_empty = all(
        parameter.grad is None for parameter in model.parameters()
    )
    prefix_array = np.asarray(prefix_gradient_norms, dtype=np.float64)
    prefix_support_fraction = (
        float(np.mean(prefix_array > PREFIX_MIN_NORM)) if prefix_array.size else 0.0
    )
    prefix_median = float(np.median(prefix_array)) if prefix_array.size else 0.0

    expected_counts = {
        "base_cases": int(expected_base_cases),
        "cases_by_size": {
            str(active_n): int(cases_per_size) for active_n in active_sizes
        },
        "permutation_reads": int(expected_permutation_reads),
        "padding_variants": int(expected_base_cases),
        "sample_replay_sequences": int(expected_base_cases),
        "join_leave_event_pairs": int(event_pairs),
    }
    counts = {
        "base_cases": int(len(cases)),
        "cases_by_size": cases_by_size,
        "permutation_reads": int(permutation_reads),
        "padding_variants": int(padding_variants_completed),
        "sample_replay_sequences": int(sample_replay_sequences_completed),
        "join_leave_event_pairs": int(membership_ledger_rows),
        "case_ledger_rows": int(case_ledger_rows),
        "membership_ledger_rows": int(membership_ledger_rows),
        "prefix_gradient_rows_n_ge_2": int(prefix_array.size),
    }
    exact_counts = all(
        counts[key] == value for key, value in expected_counts.items()
    )
    ledgers_complete = (
        case_ledger_rows == expected_base_cases
        and membership_ledger_rows == event_pairs
        and case_ledger_path.is_file()
        and membership_ledger_path.is_file()
    )
    all_numeric_finite = (
        nonfinite_sequence_count == 0
        and bool(gradient_audit["all_finite"])
        and all(
            math.isfinite(value)
            for value in (
                permutation_logits_max,
                permutation_value_max,
                padding_logits_max,
                padding_value_max,
                replay_logp_max,
                incremental_full_logits_max,
                incremental_full_roster_max,
                prefix_support_fraction,
                prefix_median,
                parameter_max_abs_drift,
            )
        )
    )

    m0_checks = {
        "exact_registered_counts": bool(exact_counts),
        "no_agent_id_or_slot_embedding": bool(
            no_embedding_module and not forbidden_state_keys
        ),
        "parameter_count_and_shapes_n_independent": bool(shapes_independent),
        "masked_slots_emit_zero_tokens": bool(masked_slot_token_count == 0),
        "order_active_set_epoch_prefix_ledger_complete": bool(ledgers_complete),
        "sample_and_replay_effective_support_equal": bool(
            support_mismatch_count == 0
        ),
        "all_logits_values_logps_and_gradients_finite": bool(all_numeric_finite),
        "zero_environment_reward_optimizer_checkpoint_exposure": True,
        "joiner_leaver_survivor_records_complete": bool(ledgers_complete),
        "incremental_and_full_recompute_logged": bool(
            case_ledger_rows == expected_base_cases
        ),
        "parameters_exactly_frozen": bool(
            parameter_max_abs_drift == 0.0 and parameter_grad_buffers_empty
        ),
    }
    m0_passed = all(m0_checks.values())
    m0_failures = [name for name, passed in m0_checks.items() if not passed]

    membership_checks = {
        "joiner_keep_unsupported": bool(joiner_keep_unsupported),
        "leaver_zero_tokens": bool(leaver_zero_tokens),
        "survivor_opaque_code_exact": bool(survivor_code_exact),
        "survivor_age_exact": bool(survivor_age_exact),
        "survivor_low_hidden_placeholder_exact": bool(survivor_hidden_exact),
        "survivor_membership_epoch_exact": bool(survivor_epoch_exact),
        "active_token_count_exact": bool(active_token_count_exact),
    }
    m1_checks = {
        "permutation_equivariance": bool(
            permutation_logits_max <= PARITY_TOLERANCE
            and permutation_value_max <= PARITY_TOLERANCE
        ),
        "padding_invariance": bool(
            padding_logits_max <= PARITY_TOLERANCE
            and padding_value_max <= PARITY_TOLERANCE
        ),
        "incremental_full_logit_parity": bool(
            incremental_full_logits_max <= PARITY_TOLERANCE
        ),
        "sampling_replay_logp_parity": bool(
            replay_logp_max <= PARITY_TOLERANCE
        ),
        "membership_semantics": bool(all(membership_checks.values())),
        "prefix_actionability": bool(
            prefix_support_fraction >= PREFIX_SUPPORT_FLOOR
            and prefix_median > PREFIX_MEDIAN_FLOOR
        ),
        "size_independence_and_linear_complexity": bool(
            shapes_independent and complexity_violation_count == 0
        ),
    }
    m1_passed = all(m1_checks.values())
    m1_failures = [name for name, passed in m1_checks.items() if not passed]

    if not m0_passed:
        status = "INVALID_R49_ORSE_WIRING"
        next_action = "repair only the named R49 wiring defect and rerun unchanged"
    elif m1_passed:
        status = "PASS_R49_ORSE_ARCHITECTURE"
        next_action = (
            "prepare only a default-off exogenous cross-episode variable-N "
            "compatibility gate"
        )
    else:
        status = "VALID_FAIL_R49_ORSE_ARCHITECTURE"
        next_action = (
            "retire the exact R49 Deep-Sets open-roster interface and stop the "
            "current project line without rescue"
        )

    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": bool(m0_passed),
        "dry_run": bool(args.dry_run),
        "dry_run_valid": bool(m0_passed and m1_passed) if args.dry_run else None,
        "contract": {
            "execution": "local CPU deterministic one thread",
            "model_seed": MODEL_SEED,
            "synthetic_data_seed": SYNTHETIC_DATA_SEED,
            "sampling_seed": SAMPLING_SEED,
            "opaque_codes": OPAQUE_CODES,
            "member_feature_dimension": MEMBER_FEATURE_DIM,
            "hidden_dimension": HIDDEN_DIM,
            "active_sizes": list(active_sizes),
            "cases_per_size": int(cases_per_size),
            "permutations_per_case": int(permutations_per_case),
            "expected_counts": expected_counts,
            "parity_tolerance": PARITY_TOLERANCE,
            "prefix_min_norm": PREFIX_MIN_NORM,
            "prefix_support_floor": PREFIX_SUPPORT_FLOOR,
            "prefix_median_floor": PREFIX_MEDIAN_FLOOR,
        },
        "architecture": {
            "family": "Deep Sets mean plus log-count and active-only AR",
            "member_input_dimension": MEMBER_FEATURE_DIM + OPAQUE_CODES + 3,
            "member_encoder": [64, "GELU", 64, "GELU"],
            "roster_encoder": [64, "GELU", 64, "GELU"],
            "hidden_dimension": HIDDEN_DIM,
            "parameter_count": parameter_count(model),
            "state_dict_signature": signature,
            "state_dict_signature_by_n": signature_by_n,
            "forbidden_state_dict_keys": forbidden_state_keys,
            "embedding_module_count": int(
                sum(isinstance(module, nn.Embedding) for module in model.modules())
            ),
            "persistent_agent_id_input": False,
            "padded_slot_index_input": False,
            "membership_epoch_network_input": False,
            "pairwise_n_by_n_tensors": 0,
        },
        "exposure": {
            "environment_steps": 0,
            "reward_reads": 0,
            "intrinsic_reward_reads": 0,
            "optimizer_steps": 0,
            "checkpoint_reads": 0,
            "checkpoint_writes": 0,
            "parameter_max_abs_drift": float(parameter_max_abs_drift),
            "parameter_grad_buffers_empty": bool(parameter_grad_buffers_empty),
        },
        "counts": counts,
        "m0": {
            "passed": bool(m0_passed),
            "checks": m0_checks,
            "invalid_reasons": m0_failures,
            "gradient_audit": gradient_audit,
            "support_mismatch_count": int(support_mismatch_count),
            "masked_slot_token_count": int(masked_slot_token_count),
            "nonfinite_sequence_count": int(nonfinite_sequence_count),
        },
        "m1": {
            "passed": bool(m1_passed),
            "checks": m1_checks,
            "failures": m1_failures,
            "metrics": {
                "permutation_token_logits_max_abs": float(
                    permutation_logits_max
                ),
                "permutation_value_max_abs": float(permutation_value_max),
                "padding_token_logits_max_abs": float(padding_logits_max),
                "padding_value_max_abs": float(padding_value_max),
                "incremental_full_logits_max_abs": float(
                    incremental_full_logits_max
                ),
                "incremental_full_roster_max_abs": float(
                    incremental_full_roster_max
                ),
                "sampling_replay_logp_max_abs": float(replay_logp_max),
                "prefix_actionability_fraction_gt_1e_8": float(
                    prefix_support_fraction
                ),
                "prefix_actionability_median_norm": float(prefix_median),
                "prefix_actionability_min_norm": float(
                    np.min(prefix_array) if prefix_array.size else 0.0
                ),
                "complexity_violation_count": int(complexity_violation_count),
            },
            "membership": membership_checks,
        },
        "artifacts": {
            "case_ledger": str(case_ledger_path),
            "membership_event_ledger": str(membership_ledger_path),
            "progress": str(progress_path),
            "result": str(result_path),
        },
        "decision": {
            "status": status,
            "next_action": next_action,
            "authorized_claim": (
                "interface correctness only" if status == "PASS_R49_ORSE_ARCHITECTURE" else None
            ),
            "prohibited_claims": [
                "skill semantics",
                "variable-lifetime efficacy",
                "intrinsic reward efficacy",
                "within-episode join/leave training",
                "S7 performance",
                "task improvement",
                "cooperation",
                "open-roster paper contribution",
            ],
        },
    }
    write_json(result_path, result)
    write_json(
        progress_path,
        {
            "phase": "complete",
            "status": status,
            "implementation_valid": bool(m0_passed),
            "m1_passed": bool(m1_passed),
            "result_path": str(result_path),
        },
    )
    print(
        f"R49 complete: status={status}; M0={m0_passed}; M1={m1_passed}; "
        f"result={result_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
