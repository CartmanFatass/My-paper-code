from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.result_rule import (
    classify_three_seed_result,
)
from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.study import (
    _seed_estimands,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    b01_production_test_fixture,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_evaluator import (
    prepare_b01_application,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy,
    RecurrentRolloutState,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    ExactPolicyGraph,
    WelfordState,
)


class _Sampler:
    def normal(self, *, lane: int, tick: int, field: str) -> float:
        return 0.0

    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int:
        return int(probability >= 0.5)


def _trigger_checkpoint() -> bytes:
    model = ExactPolicyGraph()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        model.prepare.bias.fill_(8.0); model.commit.bias.fill_(8.0)
        model.service_q.bias.fill_(8.0)
    stream = BytesIO()
    torch.save({
        "model": model.state_dict(), "optimizer": {}, "update": 0,
        "welford": {
            "actor": WelfordState.empty(54), "snapshot": WelfordState.empty(18),
            "critic": WelfordState.empty(58),
        },
    }, stream)
    return stream.getvalue()


def test_ordered_trigger_no_trigger_and_result_rule() -> None:
    base = {
        "usable_trigger_support": True, "shadow_nonharm": True,
        "delta_shadow": 1.0, "delta_shadow_worst20": 1.0, "delta_copy": 0.0,
    }
    assert classify_three_seed_result([base, base, {**base, "usable_trigger_support": False}]) == "FTS-BS"
    assert classify_three_seed_result([{**base, "usable_trigger_support": False}] * 2 + [base]) == "FTS-B0"
    harm = {**base, "shadow_nonharm": False}
    assert classify_three_seed_result([harm, harm, base]) == "FTS-BH"
    no_tail = {**base, "delta_shadow_worst20": 0.0}
    assert classify_three_seed_result([no_tail, no_tail, base]) == "FTS-BR"
    generic = {**base, "delta_shadow": 0.0, "delta_shadow_worst20": 0.0, "delta_copy": 1.0}
    assert classify_three_seed_result([generic, generic, base]) == "FTS-BC"
    negative = {**base, "delta_shadow": -1.0, "delta_shadow_worst20": -1.0, "delta_copy": 0.0}
    assert classify_three_seed_result([negative, negative, base]) == "FTS-BN"
    assert classify_three_seed_result([base, negative, harm]) == "FTS-BU"
    no_trigger = _seed_estimands([{"triggered": False, "package": "TARGET_VISUAL_MASK"}])
    assert no_trigger["usable_trigger_support"] is False
    branch = {
        "recovery_return_100": 1, "worst_20_tick_service": 1,
        "recovery_delay_10": 1, "energy_change": 1.0,
        "hard_event_ticks": {name: 0 for name in (
            "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
            "command_slew_breach", "separation_breach",
        )},
    }
    triggered = [{
        "triggered": True, "package": package,
        "branches": {
            "RETAIN": {**branch, "recovery_return_100": 0},
            "TRANSFER_COPY": branch,
            "TRANSFER_SHADOW": {**branch, "recovery_return_100": 2},
        },
    } for package in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK") for _ in range(2)]
    assert _seed_estimands(triggered)["usable_trigger_support"] is True


def test_test_smoke_traverses_prepared_branch_publication_and_project_cost() -> None:
    started = time.perf_counter(); checkpoint = _trigger_checkpoint()
    native = b01_production_test_fixture(1, origin_valid=True)
    state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=checkpoint, state=state)
    sampler = _Sampler(); parent = native.snapshot_bytes()
    prepared, observation, hidden = prepare_b01_application(native=native, policy=policy)
    prepared_bytes = prepared.snapshot_bytes()
    assert prepared.origin_valid.tolist() == [True]
    assert native.snapshot_bytes() == parent
    branches, observations, metadata = native.clone_b01_prepared_batches(prepared, hidden)
    assert native.snapshot_bytes() == parent and prepared.snapshot_bytes() == prepared_bytes
    published = []
    for name in ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW"):
        branch_state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
        branch_state.hidden = torch.from_numpy(metadata["branch_hidden"][name].astype(np.float32))
        branch_policy = BatchedRecurrentPolicy(
            arm="STRUCTURED", checkpoint_bytes=checkpoint, state=branch_state,
        )
        rows = branch_policy.step_rows(
            observations[name], sampler=sampler, global_tick=int(observation["tick"][0]),
            deterministic=True, recurrent_prepared=True,
        )
        after = branches[name].complete_b01_tick(metadata["branch_prepared"][name], rows)
        published.append({"branch": name, "service": int(after["service"][0])})
    assert [row["branch"] for row in published] == [
        "RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW",
    ]
    json.dumps(published)
    runner = Path("scripts/run_dish_first_trigger_source_scout_b01.py")
    completed = subprocess.run(
        [sys.executable, str(runner), "project-cost"],
        check=True, capture_output=True, text=True,
    )
    payload = json.loads(completed.stdout)
    assert [row["seed"] for row in payload["seed_rows"]] == [11, 29, 47]
    assert all(
        row["projected_seed_seconds"] == 1_474.544745605439
        for row in payload["seed_rows"]
    )
    assert len(payload["arm_rows"]) == 3
    assert {row["arm"] for row in payload["arm_rows"]} == {
        "RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW",
    }
    assert all(
        row["within_cap"] and row["full_seed_charge_seconds"] <= 1_800
        for row in payload["arm_rows"]
    )
    assert time.perf_counter() - started < 60.0
