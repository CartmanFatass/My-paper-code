from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1CheckpointBinding,
    capture_b1_checkpoint,
    save_b1_checkpoint,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_policy_replay_worker import (
    CANONICAL_PREFLIGHT,
    CANONICAL_REPO_ROOT,
    POLICY_REPLAY_TEST_RESULT_SCHEMA,
    encode_policy_replay_request,
    main,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_policy_assembly import (
    POLICY_REPLAY_TEST_AGGREGATE_SCHEMA,
    B1MetricsPolicyAssemblyError,
    aggregate_b1_policy_replay_results,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    CommonRecurrentActorCritic,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine import (
    _ADAPTERS,
    _evaluate_heldout,
    _optimizer_digest,
    _project_panel,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig,
    PPOCounters,
    RecurrentPPOTrainer,
    config_digest,
    make_adam,
)


RUN = "CBSC-OMRC-B1-THREE-SEED-SCOUT"
SEED = 21101
ARM = "RAW-GRU"
SLOT = 1
ATTEMPT = "test-policy-replay-worker"
COMMIT = "4" * 40
SOURCE = "5" * 64


def test_worker_preflight_source_identity_is_repo_root_bound() -> None:
    assert CANONICAL_REPO_ROOT == Path("C:/Projects/HMASD")
    assert CANONICAL_PREFLIGHT == Path(
        "C:/Projects/HMASD/scripts/hmasd_resource_preflight.py"
    )
    assert CANONICAL_PREFLIGHT.is_file()
    assert hashlib.sha256(CANONICAL_PREFLIGHT.read_bytes()).hexdigest()


def _checkpoint_inventory(
    root: Path, *, seed: int = SEED, slot: int = SLOT,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    durable = root / "arm-seeds" / f"{slot:02d}-seed-{seed}-{ARM}"
    durable.mkdir(parents=True)
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    host = DynamicHost(RUN, seed)
    tapes = (
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
        host.build_motif(0),
    )
    output = []
    evaluations = []
    for update in (0, 12, 24, 48):
        trainer = RecurrentPPOTrainer(
            model, run_name=RUN, seed=seed, optimizer=make_adam(model),
            address_u64=addressing.u64,
        )
        trainer.counters = PPOCounters(
            rollout_updates=update, adam_steps=update * 16,
            train_episodes=update * 8, train_transitions=update * 8 * 152,
            train_decisions=update * 8 * 24,
        )
        binding = B1CheckpointBinding(
            object_id="CBSC-OMRC-B01", attempt_id=ATTEMPT, run_name=RUN,
            arm=ARM, seed=seed, completed_rollout_updates=update,
            train_episode_ids_sha256="1" * 64,
            full_training_tape_digest="2" * 64,
            full_action_uniform_digest="3" * 64,
            ppo_configuration_digest=config_digest(PPOConfig()),
            implementation_commit=COMMIT,
            source_conformance_sha256=SOURCE,
        )
        envelope = capture_b1_checkpoint(trainer, binding)
        path = durable / f"checkpoint-update-{update}.pt"
        save_b1_checkpoint(path, envelope)
        output.append({
            "update": update,
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
        observations, work = _project_panel(tapes, _ADAPTERS[ARM])
        optimizer_before = _optimizer_digest(trainer)
        actions, state = _evaluate_heldout(tapes, observations, trainer.model)
        optimizer_after = _optimizer_digest(trainer)
        evaluations.append({
            "update": update,
            "actions": actions,
            "heldout_state_observations": {
                **state,
                "optimizer_digest_before": optimizer_before,
                "optimizer_digest_after": optimizer_after,
            },
            "adapter_work_receipt": asdict(work),
        })
    return output, evaluations


def _admission(
    root: Path, *, attempt_id: str = ATTEMPT, passed: bool = True,
    source: str = SOURCE, seed: int = SEED,
) -> tuple[Path, str]:
    bound_path = root / "admission.json"
    raw_path = root / ".admission.json.raw-test.json"
    available = 5 * 1024**3 if passed else 1024
    receipt = {
        "passed": passed,
        "physical_floor_pass": passed,
        "effective_floor_pass": passed,
        "available_physical_bytes": available,
        "effective_available_bytes": available,
    }
    raw_path.write_bytes(canonical_json_bytes(receipt) + b"\n")
    repo = Path(__file__).resolve().parents[4]
    preflight = repo / "scripts" / "hmasd_resource_preflight.py"
    executable = Path(os.path.abspath(sys.executable))
    bound = {
        "schema": "cbsc_omrc_b01_b1_bound_admission_v1",
        "attempt_id": attempt_id,
        "run_name": RUN,
        "arm": ARM,
        "seed": seed,
        "implementation_commit": COMMIT,
        "source_conformance_sha256": source,
        "bound_receipt_path": str(bound_path.resolve()),
        "raw_output_path": str(raw_path.resolve()),
        "python_executable": str(executable),
        "python_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "preflight_script": str(preflight.resolve()),
        "preflight_script_sha256": hashlib.sha256(preflight.read_bytes()).hexdigest(),
        "exact_command": [
            str(executable), str(preflight.resolve()), "admit-memory", "--out",
            str(raw_path.resolve()),
        ],
        "raw_receipt_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "receipt": receipt,
    }
    bound_path.write_bytes(canonical_json_bytes(bound) + b"\n")
    return bound_path, hashlib.sha256(bound_path.read_bytes()).hexdigest()


def _request(
    root: Path,
    inventory: list[dict[str, object]],
    evaluations: list[dict[str, object]],
    receipt: tuple[Path, str],
    *,
    source: str = SOURCE,
    seed: int = SEED,
    slot: int = SLOT,
) -> Path:
    scratch = root / "scratch"
    scratch.mkdir()
    request = encode_policy_replay_request(
        attempt_root=root,
        attempt_id=ATTEMPT,
        seed=seed,
        arm=ARM,
        original_slot_index=slot,
        checkpoint_inventory=inventory,
        implementation_commit=COMMIT,
        source_conformance_sha256=source,
        literal_binding_spec_sha256="6" * 64,
        source_evaluations=evaluations,
        source_active_modes=[],
        admission_receipt_path=receipt[0],
        admission_receipt_sha256=receipt[1],
        scratch_root=scratch,
        output_path=root / "result.json",
        error_path=root / "error.json",
        test_only=True,
    )
    path = root / "request.json"
    path.write_bytes(canonical_json_bytes(request) + b"\n")
    return path


def test_test_only_worker_is_create_only_and_emits_exact_one_slot_counts(tmp_path: Path) -> None:
    inventory, evaluations = _checkpoint_inventory(tmp_path)
    receipt = _admission(tmp_path)
    request = _request(tmp_path, inventory, evaluations, receipt)

    assert main(["--request", str(request)]) == 0
    result_path = tmp_path / "result.json"
    before = result_path.read_bytes()
    wrapper = json.loads(before)
    assert wrapper["schema"] == POLICY_REPLAY_TEST_RESULT_SCHEMA
    assert wrapper["counts"] == {
        "policy_decisions": 192,
        "policy_curves": 2,
        "execution_mode_records": 4,
        "evaluation_join_records": 4,
    }
    assert wrapper["scientific_branch"] is None
    assert len(wrapper["evaluation_join_records"]) == 4
    assert all(
        row["joined"] is True
        and row["source_evaluation_sha256"] == row["replay_evaluation_sha256"]
        for row in wrapper["evaluation_join_records"]
    )
    assert main(["--request", str(request)]) == 2
    assert result_path.read_bytes() == before


@pytest.mark.parametrize("stale,passed", [(True, True), (False, False)])
def test_worker_refuses_stale_or_failed_admission_before_checkpoint_access(
    tmp_path: Path, stale: bool, passed: bool,
) -> None:
    missing_inventory = [
        {"update": update, "path": str(tmp_path / f"missing-{update}.pt"), "sha256": "a" * 64}
        for update in (0, 12, 24, 48)
    ]
    receipt = _admission(
        tmp_path, attempt_id="stale-attempt" if stale else ATTEMPT, passed=passed
    )
    evaluations = [{"update": update} for update in (0, 12, 24, 48)]
    request = _request(tmp_path, missing_inventory, evaluations, receipt)

    assert main(["--request", str(request)]) == 2
    assert not (tmp_path / "result.json").exists()
    error = json.loads((tmp_path / "error.json").read_text(encoding="utf-8"))
    assert "admission" in error["detail"].lower()


@pytest.mark.parametrize("drift", ["checkpoint", "source"])
def test_worker_refuses_checkpoint_sha_and_source_drift(
    tmp_path: Path, drift: str,
) -> None:
    inventory, evaluations = _checkpoint_inventory(tmp_path)
    source = SOURCE
    if drift == "checkpoint":
        inventory[2] = {**inventory[2], "sha256": "a" * 64}
    else:
        source = "7" * 64
    receipt = _admission(tmp_path, source=source)
    request = _request(tmp_path, inventory, evaluations, receipt, source=source)

    assert main(["--request", str(request)]) == 2
    assert not (tmp_path / "result.json").exists()


@pytest.mark.parametrize("divergence", ["action", "tape", "order", "adapter_work"])
def test_worker_refuses_unjoined_source_heldout_fact(
    tmp_path: Path, divergence: str,
) -> None:
    inventory, evaluations = _checkpoint_inventory(tmp_path)
    changed = deepcopy(evaluations)
    if divergence == "action":
        current = changed[0]["actions"][0]["decision_actions"][0]
        changed[0]["actions"][0]["decision_actions"][0] = (
            "SERVE" if current != "SERVE" else "REFRESH"
        )
    elif divergence == "tape":
        changed[0]["actions"][0]["identity"]["episode_id"] = 1
    elif divergence == "order":
        changed[0]["actions"] = list(reversed(changed[0]["actions"]))
    else:
        changed[0]["adapter_work_receipt"]["byte_reads"] += 1
    receipt = _admission(tmp_path)
    request = _request(tmp_path, inventory, changed, receipt)

    assert main(["--request", str(request)]) == 2
    assert not (tmp_path / "result.json").exists()
    error = json.loads((tmp_path / "error.json").read_text(encoding="utf-8"))
    assert "divergence" in error["detail"].lower()
    assert error["blocking_audit_codes"] == ["HELDOUT_SOURCE_REPLAY_DIVERGENCE"]


def test_test_only_aggregate_requires_exact_three_raw_wrappers_and_result_sha(
    tmp_path: Path,
) -> None:
    wrappers = []
    tapes = []
    for seed, slot in ((21101, 1), (21121, 5), (21143, 9)):
        root = tmp_path / f"seed-{seed}"
        root.mkdir()
        inventory, evaluations = _checkpoint_inventory(root, seed=seed, slot=slot)
        receipt = _admission(root, seed=seed)
        request = _request(
            root, inventory, evaluations, receipt, seed=seed, slot=slot
        )
        assert main(["--request", str(request)]) == 0
        wrappers.append(json.loads((root / "result.json").read_text(encoding="utf-8")))
        host = DynamicHost(RUN, seed)
        tapes.extend((
            host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
            host.build_motif(0),
        ))

    aggregate = aggregate_b1_policy_replay_results(
        wrappers,
        heldout_tapes=tapes,
        expected_attempt_id=ATTEMPT,
        expected_implementation_commit=COMMIT,
        expected_source_conformance_sha256=SOURCE,
        literal_binding_spec_sha256="6" * 64,
        test_only=True,
    )
    assert aggregate["schema"] == POLICY_REPLAY_TEST_AGGREGATE_SCHEMA
    assert aggregate["formal_policy_coverage_satisfied"] is False
    assert aggregate["counts"] == {
        "worker_results": 3,
        "heldout_tapes": 6,
        "policy_decisions": 576,
        "policy_curves": 6,
        "execution_mode_records": 12,
        "evaluation_join_records": 12,
        "policy_support_total": 576,
    }

    cases = [
        wrappers[:-1],
        [wrappers[0], wrappers[0], wrappers[2]],
        list(reversed(wrappers)),
    ]
    drifted = deepcopy(wrappers)
    drifted[0]["result_body_sha256"] = "a" * 64
    cases.append(drifted)
    for case in cases:
        with pytest.raises(B1MetricsPolicyAssemblyError):
            aggregate_b1_policy_replay_results(
                case,
                heldout_tapes=tapes,
                expected_attempt_id=ATTEMPT,
                expected_implementation_commit=COMMIT,
                expected_source_conformance_sha256=SOURCE,
                literal_binding_spec_sha256="6" * 64,
                test_only=True,
            )
