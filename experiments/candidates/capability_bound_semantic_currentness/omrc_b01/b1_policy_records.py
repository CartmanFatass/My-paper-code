"""Lossless held-out policy records for the metrics-only B1 publication.

This module owns direct implementation observations only.  It deliberately
contains no scientific reduction, polarity, classifier, or B2 trigger.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import io
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .adapters import (
    DerangedCurrentnessAdapter,
    PredictiveIndexAdapter,
    RawHistoryAdapter,
    StructCurrentnessAdapter,
)
from .contract import Action, EPISODE_TRANSITIONS, EventKind, OPPORTUNITY_COUNT
from .model import (
    INPUT_DIM,
    CommonRecurrentActorCritic,
    greedy_action,
    model_parameter_digest,
)
from .tapes import EpisodeTape


class B1PolicyRecordError(ValueError):
    """A direct policy replay or its canonical identity is incomplete."""


POLICY_DECISION_RECORD_SCHEMA = "cbsc_omrc_b01_policy_decision_record_v1"
POLICY_CURVE_RECORD_SCHEMA = "cbsc_omrc_b01_policy_curve_record_v1"
POLICY_SUPPORT_COUNT_RECORD_SCHEMA = "cbsc_omrc_b01_policy_support_count_record_v1"

RUN_ORDER = {
    "CBSC-OMRC-B1-THREE-SEED-SCOUT": 0,
    "CBSC-OMRC-B2-TWO-SEED-STABILITY": 1,
}
ARM_ORDER = {
    "STRUCT-CURRENTNESS-GRU": 0,
    "RAW-GRU": 1,
    "PI-GRU": 2,
    "DERANGED-CURRENTNESS-GRU": 3,
}
SPLIT_ORDER = {"TRAIN": 0, "EVAL_STOCHASTIC": 1, "EVAL_MOTIF": 2}
CHECKPOINT_UPDATES = (0, 12, 24, 48)

_ADAPTERS = {
    "STRUCT-CURRENTNESS-GRU": StructCurrentnessAdapter,
    "RAW-GRU": RawHistoryAdapter,
    "PI-GRU": PredictiveIndexAdapter,
    "DERANGED-CURRENTNESS-GRU": DerangedCurrentnessAdapter,
}

POLICY_RECORD_KEY_FIELDS = (
    "run_order",
    "seed",
    "checkpoint_update",
    "split_order",
    "tape_id",
    "opportunity_id",
    "arm_order",
)
POLICY_RECORD_OBSERVATION_FIELDS = (
    "checkpoint_sha256",
    "parameter_sha256",
    "adapter_state_before_bytes",
    "adapter_state_after_bytes",
    "adapter_output_bytes",
    "legal_action_mask",
    "actor_logits_fp32_bits",
    "legal_action_probabilities_fp32_bits",
    "critic_value_fp32_bits",
    "selected_action",
    "selected_action_log_probability_fp32_bits",
    "observed_decision_reward",
    "observed_settlement_reward",
    "observed_opportunity_return",
    "hidden_state_before_sha256",
    "hidden_state_after_sha256",
)
POLICY_CURVE_KEY_FIELDS = (
    "run_order",
    "seed",
    "split_order",
    "tape_id",
    "arm_order",
)
POLICY_CURVE_VALUE_FIELDS = tuple(
    field
    for update in CHECKPOINT_UPDATES
    for field in (
        f"episode_return_update_{update}",
        f"episode_decision_reward_sum_update_{update}",
        f"episode_settlement_reward_sum_update_{update}",
    )
)


DERIVED_NULL_FIELDS = (
    "heldout_mean_return",
    "terminal_mean_return",
    "mean_oracle_regret",
    "normalized_return_auc",
    "struct_minus_raw_auc",
    "struct_minus_deranged_auc",
    "struct_minus_pi_auc",
    "oracle_action_accuracy",
    "invalid_serve_rate",
    "missed_serve_rate",
    "unnecessary_refresh_rate",
    "missed_refresh_rate",
    "inactive_fallback_accuracy",
    "owner_twin_flip_accuracy",
    "semantic_twin_flip_accuracy",
    "correct_swapped_sensitivity",
    "capability_specificity",
    "retention_gap_effect",
    "owner_event_order_effect",
    "semantic_event_order_effect",
    "clear_competent_null",
    "separation_from_deranged",
    "separation_from_pi",
    "residual_concentrated_in_gated",
    "material_instability",
    "adverse_seed",
    "catastrophic_seed",
    "promotion_eligible",
    "scientific_branch",
    "scientific_polarity",
    "b2_extension_trigger",
)

AUC_METADATA_NULL_FIELDS = (
    "return_auc_x_divisor",
    "return_auc_y_normalization",
    "return_auc_y_scale",
    "return_auc_split_scope",
    "return_auc_panel_pooling",
    "return_auc_episode_aggregation",
    "return_auc_seed_aggregation",
    "return_auc_pairing_rule",
    "return_auc_missing_rule",
    "return_auc_nonfinite_rule",
    "return_auc_scientific_interpretation",
)

DIAGNOSTIC_NAMES = (
    "oracle_action_accuracy",
    "invalid_serve_rate",
    "missed_serve_rate",
    "unnecessary_refresh_rate",
    "missed_refresh_rate",
    "inactive_fallback_accuracy",
    "owner_twin_flip_accuracy",
    "semantic_twin_flip_accuracy",
    "correct_swapped_sensitivity",
    "capability_specificity",
    "retention_gap_effect",
    "owner_event_order_effect",
    "semantic_event_order_effect",
)

DIAGNOSTIC_METADATA_NULL_FIELDS = (
    "numerator",
    "denominator",
    "eligible_support_rule",
    "panel_scope",
    "split_pooling",
    "per_seed_aggregation",
    "checkpoint_reduction",
    "paired_unit",
    "minimum_support",
    "zero_denominator_rule",
    "effect",
    "interpretation",
)


def build_literal_null_manifest_fields() -> dict[str, Any]:
    """Return the complete `.03` engineering-owned literal-null schema."""

    return {
        "derived_fields": {name: None for name in DERIVED_NULL_FIELDS},
        "auc_metadata": {name: None for name in AUC_METADATA_NULL_FIELDS},
        "diagnostic_metadata": {
            diagnostic: {
                name: None for name in DIAGNOSTIC_METADATA_NULL_FIELDS
            }
            for diagnostic in DIAGNOSTIC_NAMES
        },
    }


def _exact_fraction(value: Fraction) -> dict[str, int]:
    if not isinstance(value, Fraction):
        raise B1PolicyRecordError("native ledger value is not exact Fraction")
    return {"numerator": value.numerator, "denominator": value.denominator}


def _fp32_bits(value: torch.Tensor) -> int | list[int]:
    array = value.detach().cpu().contiguous().numpy()
    if array.dtype != np.float32 or not np.isfinite(array).all():
        raise B1PolicyRecordError("policy observation is not finite FP32")
    bits = array.view(np.uint32)
    if bits.ndim == 0:
        return int(bits)
    return [int(item) for item in bits.reshape(-1)]


def _tensor_sha256(value: torch.Tensor) -> str:
    array = value.detach().cpu().contiguous().numpy()
    if array.dtype != np.float32 or not np.isfinite(array).all():
        raise B1PolicyRecordError("hidden state is not finite FP32")
    digest = hashlib.sha256()
    digest.update(b"float32")
    digest.update(str(tuple(array.shape)).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _project_tapes_with_decision_adapter_bytes(
    tapes: tuple[EpisodeTape, ...], arm: str
) -> tuple[torch.Tensor, list[list[tuple[list[int], list[int], list[int]]]]]:
    observations = np.empty(
        (len(tapes), EPISODE_TRANSITIONS, INPUT_DIM), dtype=np.float32
    )
    adapter_records: list[list[tuple[list[int], list[int], list[int]]]] = []
    for tape_index, tape in enumerate(tapes):
        adapter = _ADAPTERS[arm]()
        primitive = tape.learner_tokens()
        if len(primitive) != EPISODE_TRANSITIONS:
            raise B1PolicyRecordError("held-out tape does not contain 152 transitions")
        decisions: list[tuple[list[int], list[int], list[int]]] = []
        for transition, (token, public) in enumerate(
            zip(tape.public_tokens, primitive, strict=True)
        ):
            before = list(adapter.state)
            emission = adapter.process(token)
            after = list(adapter.state)
            observations[tape_index, transition, :136] = public.float32_channels()
            observations[tape_index, transition, 136:] = emission.float32_channels()
            if EventKind(token.event_kind) is EventKind.DECISION:
                decisions.append((before, after, list(emission.packed)))
        if len(decisions) != OPPORTUNITY_COUNT:
            raise B1PolicyRecordError("held-out tape does not contain 24 decisions")
        adapter_records.append(decisions)
    if not np.isfinite(observations).all():
        raise B1PolicyRecordError("held-out observation contains nonfinite values")
    return torch.from_numpy(observations), adapter_records


def _validated_checkpoint_parameter_digest(
    checkpoint_bytes: bytes,
    *,
    run_name: str,
    arm: str,
    seed: int,
    checkpoint_update: int,
) -> str:
    """Decode the exact bytes and bind their canonical model state to evaluation."""

    # Local imports avoid a module cycle when the B1 engine later consumes this
    # publication helper at its checkpoint/evaluation seam.
    from .b1_engine import B1EngineError, _validate_envelope
    from .checkpoint import model_parameter_digest_from_state

    stream = io.BytesIO(checkpoint_bytes)
    try:
        try:
            envelope = torch.load(stream, map_location="cpu", weights_only=True)
        except TypeError:  # pragma: no cover - older PyTorch compatibility
            stream.seek(0)
            envelope = torch.load(stream, map_location="cpu")
        binding = _validate_envelope(envelope)
    except (B1EngineError, EOFError, RuntimeError, TypeError, ValueError) as exc:
        raise B1PolicyRecordError("checkpoint bytes are not a canonical B1 envelope") from exc
    if (
        binding.run_name != run_name
        or binding.arm != arm
        or binding.seed != seed
        or binding.completed_rollout_updates != checkpoint_update
    ):
        raise B1PolicyRecordError("checkpoint identity differs from policy evaluation")
    try:
        state = envelope["recurrent_ppo_checkpoint"]["model_state"]
        return model_parameter_digest_from_state(state)
    except (KeyError, TypeError, ValueError) as exc:
        raise B1PolicyRecordError("checkpoint model state is incomplete") from exc


def build_checkpoint_policy_records(
    *,
    run_name: str,
    arm: str,
    seed: int,
    checkpoint_update: int,
    checkpoint_bytes: bytes,
    tapes: tuple[EpisodeTape, ...],
    model: CommonRecurrentActorCritic,
) -> list[dict[str, Any]]:
    """Replay one actual checkpoint on held-out tapes into exact `.03` rows."""

    if run_name not in RUN_ORDER or arm not in ARM_ORDER:
        raise B1PolicyRecordError("run or arm has no canonical `.03` order")
    if type(seed) is not int or checkpoint_update not in CHECKPOINT_UPDATES:
        raise B1PolicyRecordError("seed or checkpoint update is not canonical")
    if not isinstance(checkpoint_bytes, bytes) or not checkpoint_bytes:
        raise B1PolicyRecordError("checkpoint bytes must be present")
    if not isinstance(tapes, tuple) or not tapes:
        raise B1PolicyRecordError("at least one actual held-out tape is required")
    if not isinstance(model, CommonRecurrentActorCritic) or model.seed != seed:
        raise B1PolicyRecordError("actual model seed differs from policy row identity")
    keyed: dict[tuple[int, int], EpisodeTape] = {}
    for tape in tapes:
        if not isinstance(tape, EpisodeTape):
            raise B1PolicyRecordError("policy replay accepts actual EpisodeTape values only")
        identity = tape.identity
        if (
            identity.run_name != run_name
            or identity.seed != seed
            or identity.split not in ("EVAL_STOCHASTIC", "EVAL_MOTIF")
        ):
            raise B1PolicyRecordError("held-out tape identity differs from checkpoint")
        key = (SPLIT_ORDER[identity.split], identity.episode_id)
        if key in keyed:
            raise B1PolicyRecordError("held-out tape key is duplicated")
        keyed[key] = tape
    ordered_tapes = tuple(keyed[key] for key in sorted(keyed))
    checkpoint_parameter_sha256 = _validated_checkpoint_parameter_digest(
        checkpoint_bytes,
        run_name=run_name,
        arm=arm,
        seed=seed,
        checkpoint_update=checkpoint_update,
    )
    parameter_sha256 = model_parameter_digest(model)
    if checkpoint_parameter_sha256 != parameter_sha256:
        raise B1PolicyRecordError(
            "checkpoint model state differs from actual evaluation model"
        )
    observations, adapter_records = _project_tapes_with_decision_adapter_bytes(
        ordered_tapes, arm
    )
    checkpoint_sha256 = hashlib.sha256(checkpoint_bytes).hexdigest()
    was_training = model.training
    logits: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    hidden_before: list[torch.Tensor] = []
    hidden_after: list[torch.Tensor] = []
    try:
        model.eval()
        with torch.no_grad():
            hidden = model.initial_hidden(len(ordered_tapes), device=observations.device)
            for transition in range(EPISODE_TRANSITIONS):
                hidden_before.append(hidden.detach().clone())
                step = model.forward_step(observations[:, transition], hidden)
                logits.append(step.logits)
                values.append(step.value)
                hidden = step.hidden
                hidden_after.append(hidden.detach().clone())
            stacked_logits = torch.stack(logits, dim=1)
            decision_mask = torch.zeros(
                (len(ordered_tapes), EPISODE_TRANSITIONS), dtype=torch.bool
            )
            decision_mask[:, 12::6] = True
            selected = greedy_action(
                stacked_logits.reshape(-1, 4), decision_mask.reshape(-1)
            )
            actions = selected.actions.reshape(len(ordered_tapes), EPISODE_TRANSITIONS)
            log_probabilities = selected.log_probabilities.reshape(
                len(ordered_tapes), EPISODE_TRANSITIONS
            )
    finally:
        model.train(was_training)
    if model_parameter_digest(model) != parameter_sha256:
        raise B1PolicyRecordError("held-out policy replay changed model parameters")

    rows: list[dict[str, Any]] = []
    for tape_index, tape in enumerate(ordered_tapes):
        evaluator = tape.evaluator()
        for opportunity in range(OPPORTUNITY_COUNT):
            transition = 12 + 6 * opportunity
            actor_logits = stacked_logits[tape_index, transition]
            legal_logits = actor_logits[1:4]
            legal_probabilities = torch.softmax(legal_logits, dim=-1)
            actor_action = int(actions[tape_index, transition].item())
            if actor_action not in (1, 2, 3):
                raise B1PolicyRecordError("held-out decision selected illegal WAIT/action")
            ledger = evaluator.ledger(opportunity, Action(actor_action))
            before, after, output = adapter_records[tape_index][opportunity]
            rows.append(
                {
                    "run_order": RUN_ORDER[run_name],
                    "seed": seed,
                    "checkpoint_update": checkpoint_update,
                    "split_order": SPLIT_ORDER[tape.identity.split],
                    "tape_id": tape.identity.episode_id,
                    "opportunity_id": opportunity,
                    "arm_order": ARM_ORDER[arm],
                    "checkpoint_sha256": checkpoint_sha256,
                    "parameter_sha256": parameter_sha256,
                    "adapter_state_before_bytes": before,
                    "adapter_state_after_bytes": after,
                    "adapter_output_bytes": output,
                    "legal_action_mask": [False, True, True, True],
                    "actor_logits_fp32_bits": _fp32_bits(actor_logits),
                    "legal_action_probabilities_fp32_bits": _fp32_bits(
                        legal_probabilities
                    ),
                    "critic_value_fp32_bits": _fp32_bits(
                        values[transition][tape_index]
                    ),
                    "selected_action": actor_action - 1,
                    "selected_action_log_probability_fp32_bits": _fp32_bits(
                        log_probabilities[tape_index, transition]
                    ),
                    "observed_decision_reward": _exact_fraction(
                        ledger.decision_reward
                    ),
                    "observed_settlement_reward": _exact_fraction(
                        ledger.settlement_reward
                    ),
                    "observed_opportunity_return": _exact_fraction(
                        ledger.undiscounted_total
                    ),
                    "hidden_state_before_sha256": _tensor_sha256(
                        hidden_before[transition][tape_index]
                    ),
                    "hidden_state_after_sha256": _tensor_sha256(
                        hidden_after[transition][tape_index]
                    ),
                }
            )
    expected_fields = set(POLICY_RECORD_KEY_FIELDS + POLICY_RECORD_OBSERVATION_FIELDS)
    if any(set(row) != expected_fields for row in rows):
        raise AssertionError("policy record schema construction differs")
    return sorted(rows, key=lambda row: tuple(row[name] for name in POLICY_RECORD_KEY_FIELDS))


def _read_exact_fraction(value: object, *, label: str) -> Fraction:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"numerator", "denominator"}
        or type(value["numerator"]) is not int
        or type(value["denominator"]) is not int
        or value["denominator"] <= 0
    ):
        raise B1PolicyRecordError(f"{label} is not an exact fraction record")
    return Fraction(value["numerator"], value["denominator"])


def build_complete_policy_curves(
    policy_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build direct four-checkpoint per-tape sums without a scientific reduction."""

    if not isinstance(policy_records, Sequence) or isinstance(
        policy_records, (str, bytes, bytearray)
    ) or not policy_records:
        raise B1PolicyRecordError("policy curves require direct policy-decision rows")
    expected_fields = set(POLICY_RECORD_KEY_FIELDS + POLICY_RECORD_OBSERVATION_FIELDS)
    indexed: dict[tuple[int, int, int, int, int, int], Mapping[str, Any]] = {}
    checkpoint_identities: dict[tuple[int, int, int, int], tuple[str, str]] = {}
    for row in policy_records:
        if not isinstance(row, Mapping) or set(row) != expected_fields:
            raise B1PolicyRecordError("policy-decision row schema differs")
        if (
            row["run_order"] not in RUN_ORDER.values()
            or row["arm_order"] not in ARM_ORDER.values()
            or row["split_order"] not in (1, 2)
            or row["checkpoint_update"] not in CHECKPOINT_UPDATES
            or type(row["seed"]) is not int
            or type(row["tape_id"]) is not int
            or type(row["opportunity_id"]) is not int
            or not 0 <= row["opportunity_id"] < OPPORTUNITY_COUNT
        ):
            raise B1PolicyRecordError("policy-decision canonical key differs")
        key = (
            row["run_order"],
            row["seed"],
            row["checkpoint_update"],
            row["split_order"],
            row["tape_id"],
            row["arm_order"],
            row["opportunity_id"],
        )
        if key in indexed:
            raise B1PolicyRecordError("policy-decision canonical key is duplicated")
        indexed[key] = row
        identity_key = (
            row["run_order"], row["seed"], row["checkpoint_update"], row["arm_order"]
        )
        identity = (row["checkpoint_sha256"], row["parameter_sha256"])
        if identity_key in checkpoint_identities and checkpoint_identities[identity_key] != identity:
            raise B1PolicyRecordError("checkpoint/parameter identity differs within one policy")
        checkpoint_identities[identity_key] = identity

    groups: dict[tuple[int, int, int, int, int], dict[int, list[Mapping[str, Any]]]] = {}
    for row in policy_records:
        curve_key = tuple(row[name] for name in POLICY_CURVE_KEY_FIELDS)
        groups.setdefault(curve_key, {}).setdefault(row["checkpoint_update"], []).append(row)

    output: list[dict[str, Any]] = []
    for curve_key in sorted(groups):
        by_update = groups[curve_key]
        if set(by_update) != set(CHECKPOINT_UPDATES):
            raise B1PolicyRecordError("per-tape curve checkpoint coverage differs")
        curve = dict(zip(POLICY_CURVE_KEY_FIELDS, curve_key, strict=True))
        for update in CHECKPOINT_UPDATES:
            rows = sorted(by_update[update], key=lambda row: row["opportunity_id"])
            if [row["opportunity_id"] for row in rows] != list(range(OPPORTUNITY_COUNT)):
                raise B1PolicyRecordError("per-tape curve opportunity coverage differs")
            decision_sum = sum(
                (
                    _read_exact_fraction(
                        row["observed_decision_reward"], label="decision reward"
                    )
                    for row in rows
                ),
                Fraction(0),
            )
            settlement_sum = sum(
                (
                    _read_exact_fraction(
                        row["observed_settlement_reward"], label="settlement reward"
                    )
                    for row in rows
                ),
                Fraction(0),
            )
            return_sum = sum(
                (
                    _read_exact_fraction(
                        row["observed_opportunity_return"], label="opportunity return"
                    )
                    for row in rows
                ),
                Fraction(0),
            )
            if return_sum != decision_sum + settlement_sum:
                raise B1PolicyRecordError("opportunity ledger does not sum exactly")
            curve[f"episode_return_update_{update}"] = _exact_fraction(return_sum)
            curve[f"episode_decision_reward_sum_update_{update}"] = _exact_fraction(
                decision_sum
            )
            curve[f"episode_settlement_reward_sum_update_{update}"] = _exact_fraction(
                settlement_sum
            )
        output.append(curve)
    expected_curve_fields = set(POLICY_CURVE_KEY_FIELDS + POLICY_CURVE_VALUE_FIELDS)
    if any(set(row) != expected_curve_fields for row in output):
        raise AssertionError("policy curve schema construction differs")
    return output


POLICY_SUPPORT_SIGNATURE_FIELDS = (
    "run_order",
    "run_name",
    "seed",
    "split_order",
    "split",
    "motif_family_or_null",
    "motif_side_or_null",
    "request_active",
    "access_gated",
    "presented_body_native_neutral",
    "address_match_truth",
    "payload_source_match_truth",
    "content_match_truth",
    "owner_match_truth",
    "epoch_match_truth",
    "capability_match_truth",
    "overall_valid_truth",
    "oracle_action",
    "presented_body_age_opportunities",
    "arm_order",
    "arm",
    "checkpoint_update",
    "selected_action",
)
_TRUTH_JOIN_FIELDS = (
    "run_order",
    "seed",
    "split_order",
    "tape_id",
    "opportunity_id",
)
_TRUTH_SUPPORT_SOURCE_FIELDS = (
    "run_name",
    "split",
    "motif_family",
    "motif_side",
    "request_active",
    "access_gated",
    "presented_body_native_neutral",
    "address_match_truth",
    "payload_source_match_truth",
    "content_match_truth",
    "owner_match_truth",
    "epoch_match_truth",
    "capability_match_truth",
    "overall_valid_truth",
    "oracle_action",
    "presented_body_age_opportunities",
)


def _support_sort_value(value: object) -> tuple[int, str]:
    if value is None:
        return (0, "")
    if type(value) is bool:
        return (1, "1" if value else "0")
    if type(value) is int:
        return (2, f"{value:020d}")
    return (3, str(value))


def build_policy_support_signature_counts(
    policy_records: Sequence[Mapping[str, Any]],
    decision_truth_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Count the `.03` action-augmented truth signature without a rate/effect."""

    if (
        not isinstance(policy_records, Sequence)
        or isinstance(policy_records, (str, bytes, bytearray))
        or not policy_records
        or not isinstance(decision_truth_records, Sequence)
        or isinstance(decision_truth_records, (str, bytes, bytearray))
        or not decision_truth_records
    ):
        raise B1PolicyRecordError("policy support counts require raw policy and truth rows")
    truth_index: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    required_truth = set(_TRUTH_JOIN_FIELDS + _TRUTH_SUPPORT_SOURCE_FIELDS)
    for truth in decision_truth_records:
        if not isinstance(truth, Mapping) or not required_truth.issubset(truth):
            raise B1PolicyRecordError("decision-truth support fields are incomplete")
        key = tuple(truth[name] for name in _TRUTH_JOIN_FIELDS)
        if key in truth_index:
            raise B1PolicyRecordError("decision-truth canonical key is duplicated")
        run_order, seed, split_order, tape_id, opportunity_id = key
        if (
            run_order not in RUN_ORDER.values()
            or type(seed) is not int
            or split_order not in (1, 2)
            or type(tape_id) is not int
            or type(opportunity_id) is not int
            or not 0 <= opportunity_id < OPPORTUNITY_COUNT
            or RUN_ORDER.get(truth["run_name"]) != run_order
            or SPLIT_ORDER.get(truth["split"]) != split_order
        ):
            raise B1PolicyRecordError("decision-truth identity differs from canonical order")
        for name in (
            "request_active",
            "access_gated",
            "presented_body_native_neutral",
            "address_match_truth",
            "payload_source_match_truth",
            "content_match_truth",
            "owner_match_truth",
            "epoch_match_truth",
            "capability_match_truth",
            "overall_valid_truth",
        ):
            if type(truth[name]) is not bool:
                raise B1PolicyRecordError(f"decision-truth {name} is not literal boolean")
        if truth["oracle_action"] not in (0, 1, 2):
            raise B1PolicyRecordError("decision-truth oracle action differs")
        if (
            type(truth["presented_body_age_opportunities"]) is not int
            or truth["presented_body_age_opportunities"] < 0
        ):
            raise B1PolicyRecordError("decision-truth body age differs")
        if truth["motif_family"] is not None and (
            type(truth["motif_family"]) is not int
            or not 0 <= truth["motif_family"] <= 7
        ):
            raise B1PolicyRecordError("decision-truth motif family differs")
        if truth["motif_side"] is not None and truth["motif_side"] not in {
            "A", "B", "SETUP", "GAP1", "FILLER", "GAP6"
        }:
            raise B1PolicyRecordError("decision-truth motif side differs")
        truth_index[key] = truth

    expected_policy_fields = set(
        POLICY_RECORD_KEY_FIELDS + POLICY_RECORD_OBSERVATION_FIELDS
    )
    seen_policy: set[tuple[Any, ...]] = set()
    counts: Counter[tuple[Any, ...]] = Counter()
    arm_names = {order: name for name, order in ARM_ORDER.items()}
    for policy in policy_records:
        if not isinstance(policy, Mapping) or set(policy) != expected_policy_fields:
            raise B1PolicyRecordError("policy-decision row schema differs")
        policy_key = tuple(policy[name] for name in POLICY_RECORD_KEY_FIELDS)
        if policy_key in seen_policy:
            raise B1PolicyRecordError("policy-decision canonical key is duplicated")
        seen_policy.add(policy_key)
        join_key = tuple(policy[name] for name in _TRUTH_JOIN_FIELDS)
        truth = truth_index.get(join_key)
        if truth is None:
            raise B1PolicyRecordError("policy decision has no exact decision-truth row")
        arm_order = policy["arm_order"]
        if arm_order not in arm_names or policy["selected_action"] not in (0, 1, 2):
            raise B1PolicyRecordError("policy action/arm differs from canonical order")
        signature = (
            truth["run_order"],
            truth["run_name"],
            truth["seed"],
            truth["split_order"],
            truth["split"],
            truth["motif_family"],
            truth["motif_side"],
            truth["request_active"],
            truth["access_gated"],
            truth["presented_body_native_neutral"],
            truth["address_match_truth"],
            truth["payload_source_match_truth"],
            truth["content_match_truth"],
            truth["owner_match_truth"],
            truth["epoch_match_truth"],
            truth["capability_match_truth"],
            truth["overall_valid_truth"],
            truth["oracle_action"],
            truth["presented_body_age_opportunities"],
            arm_order,
            arm_names[arm_order],
            policy["checkpoint_update"],
            policy["selected_action"],
        )
        counts[signature] += 1
    output = [
        {
            **dict(zip(POLICY_SUPPORT_SIGNATURE_FIELDS, signature, strict=True)),
            "support_count": count,
        }
        for signature, count in sorted(
            counts.items(), key=lambda item: tuple(_support_sort_value(v) for v in item[0])
        )
    ]
    return output


__all__ = [
    "AUC_METADATA_NULL_FIELDS",
    "DERIVED_NULL_FIELDS",
    "DIAGNOSTIC_METADATA_NULL_FIELDS",
    "DIAGNOSTIC_NAMES",
    "POLICY_RECORD_KEY_FIELDS",
    "POLICY_RECORD_OBSERVATION_FIELDS",
    "POLICY_DECISION_RECORD_SCHEMA",
    "POLICY_CURVE_RECORD_SCHEMA",
    "POLICY_CURVE_KEY_FIELDS",
    "POLICY_CURVE_VALUE_FIELDS",
    "POLICY_SUPPORT_COUNT_RECORD_SCHEMA",
    "POLICY_SUPPORT_SIGNATURE_FIELDS",
    "B1PolicyRecordError",
    "build_checkpoint_policy_records",
    "build_complete_policy_curves",
    "build_literal_null_manifest_fields",
    "build_policy_support_signature_counts",
]
