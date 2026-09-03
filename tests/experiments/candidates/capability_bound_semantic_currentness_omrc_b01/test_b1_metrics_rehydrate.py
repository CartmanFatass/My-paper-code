from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_SEEDS,
    B1_SLOT_ORDER,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_rehydrate import (
    B1MetricsRehydrateError,
    rehydrate_b1_metrics,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig,
    config_digest,
)


ATTEMPT_ID = "rehydrate-source-bound-test"
SPEC_SHA256 = "7" * 64


def _json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _tape_record(tape) -> dict[str, object]:
    return {
        "identity": asdict(tape.identity),
        "primitive_digest_observed": tape.primitive_digest,
        "draw_digest_observed": tape.generation_audit.draw_digest,
        "draw_count_observed": tape.generation_audit.draw_count,
    }


def _training_tape_digest(tapes) -> str:
    return _json_sha256(
        [
            {
                "identity": asdict(tape.identity),
                "primitive_digest": tape.primitive_digest,
            }
            for tape in tapes
        ]
    )


def _action_uniform_digest(tapes, seed: int) -> str:
    records = []
    for tape in tapes:
        for opportunity_index in range(24):
            address = addressing.action_address(
                addressing.B1_RUN,
                seed,
                tape.identity.episode_id,
                opportunity_index,
            )
            records.append(
                {
                    "episode_id": tape.identity.episode_id,
                    "opportunity_index": opportunity_index,
                    "address": list(address),
                    "u64": addressing.u64(address),
                }
            )
    return _json_sha256(records)


@pytest.fixture(scope="module")
def canonical_raw_slice_groups() -> tuple[tuple[dict[str, object], ...], ...]:
    panels: dict[int, tuple[object, ...]] = {}
    bindings: dict[int, dict[str, object]] = {}
    for seed in B1_SEEDS:
        host = DynamicHost(addressing.B1_RUN, seed)
        train = tuple(
            host.build_stochastic(addressing.TRAIN, episode_id)
            for episode_id in range(384)
        )
        evaluation = tuple(
            host.build_stochastic(addressing.EVAL_STOCHASTIC, episode_id)
            for episode_id in range(32)
        ) + tuple(host.build_motif(tape_id) for tape_id in range(32))
        panels[seed] = train + evaluation
        bindings[seed] = {
            "train_episode_ids_sha256": _json_sha256(list(range(384))),
            "full_training_tape_digest": _training_tape_digest(train),
            "full_action_uniform_digest": _action_uniform_digest(train, seed),
            "ppo_configuration_digest": config_digest(PPOConfig()),
            "implementation_commit": "1" * 40,
            "source_conformance_sha256": "2" * 64,
        }

    groups = []
    for seed, arm in B1_SLOT_ORDER:
        panel = panels[seed]
        groups.append(
            (
                {
                    "schema": B1_RAW_EVIDENCE_SCHEMA,
                    "attempt_id": ATTEMPT_ID,
                    "run_name": addressing.B1_RUN,
                    "arm": arm,
                    "seed": seed,
                    "slice": {"start_update": 0, "stop_update": 48},
                    "full_bindings": dict(bindings[seed]),
                    "train_tapes": [_tape_record(tape) for tape in panel[:384]],
                    "evaluation_tapes": [_tape_record(tape) for tape in panel[384:]],
                },
            )
        )
    return tuple(groups)


def test_rehydrate_reconstructs_unique_seed_major_inventory_and_maps_transition_once(
    canonical_raw_slice_groups,
) -> None:
    result = rehydrate_b1_metrics(
        canonical_raw_slice_groups,
        attempt_id=ATTEMPT_ID,
        literal_binding_spec_sha256=SPEC_SHA256,
    )

    assert len(result.unique_tapes) == 3 * (384 + 32 + 32)
    assert [
        (
            tape.identity.seed,
            tape.identity.split,
            tape.identity.episode_id,
        )
        for tape in result.unique_tapes[:386]
    ] == [
        *((21101, addressing.TRAIN, episode_id) for episode_id in range(384)),
        (21101, addressing.EVAL_STOCHASTIC, 0),
        (21101, addressing.EVAL_STOCHASTIC, 1),
    ]
    assert "tape_transitions" in result.canonical_shared_tables
    assert "shared_tape_transitions" not in result.canonical_shared_tables
    assert len(result.canonical_shared_tables["tape_transitions"]) == 3 * 448 * 152
    assert result.canonical_shared_tables["table_counts"]["tape_transitions"] == 3 * 448 * 152
    assert "shared_tape_transitions" not in result.canonical_shared_tables["table_counts"]
    assert "shared_tape_transitions" not in result.canonical_shared_tables["table_sha256"]


def test_rehydrate_rejects_arm_tape_digest_tampering(
    canonical_raw_slice_groups,
) -> None:
    tampered = deepcopy(canonical_raw_slice_groups)
    tampered[0][0]["train_tapes"][0]["primitive_digest_observed"] = "0" * 64

    with pytest.raises(
        B1MetricsRehydrateError,
        match="primitive/draw identity differs from canonical host",
    ):
        rehydrate_b1_metrics(
            tampered,
            attempt_id=ATTEMPT_ID,
            literal_binding_spec_sha256=SPEC_SHA256,
        )
