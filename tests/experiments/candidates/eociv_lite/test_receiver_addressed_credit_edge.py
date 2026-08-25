from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from experiments.candidates.eociv_lite import actuation_runtime as actuation
from experiments.candidates.eociv_lite import receiver_addressed_credit_edge as b9
from experiments.candidates.eociv_lite import sibling_env as sibling


CANDIDATE_REVISION = "a" * 40
OTHER_REVISION = "b" * 40


def _edge(
    *,
    receiver: int = 1,
    source: int = 2,
    event: int = 0,
    profile: str = b9.PROFILE_NAMES[0],
    root_id: int = 990_100,
) -> sibling.EdgeIdentity:
    return sibling.EdgeIdentity(
        profile_registration_id=profile,
        episode_id=root_id,
        receiver_member_key=receiver,
        receiver_active_spell_epoch=1,
        source_member_key=source,
        source_active_spell_epoch=1,
        lifecycle_event_index=event,
    )


def _ready(**overrides: object) -> dict[str, object]:
    values = {
        "candidate_revision": CANDIDATE_REVISION,
        "checkout_revision": CANDIDATE_REVISION,
        "checkout_clean": True,
    }
    values.update(overrides)
    return b9.readiness(**values)


def _robust(row: dict[str, float]) -> dict[str, object]:
    complete = {metric: 0.0 for metric in b9._METRICS}
    complete.update(row)
    return {
        "global": copy.deepcopy(complete),
        "by_anchor": {anchor: copy.deepcopy(complete) for anchor in b9.ANCHOR_IDS},
        "leave_one_profile": {
            profile: copy.deepcopy(complete) for profile in b9.PROFILE_NAMES
        },
        "leave_one_root": {
            str(index): copy.deepcopy(complete) for index in range(len(b9.HELDOUT_ROOTS))
        },
    }


def _synthetic_stored_trajectory(
    actor,
    index: int,
    *,
    profile: str | None = None,
    root_id: int | None = None,
) -> b9.StoredTrajectory:
    profile_name = b9.PROFILE_NAMES[index % len(b9.PROFILE_NAMES)] if profile is None else profile
    registered_root = 990_300 + index if root_id is None else root_id
    capacity = actor.capacity
    previous = torch.zeros((capacity, actor.hidden_dim), dtype=torch.float32)
    receiver_slot = actuation.slot_features(
        sibling._pad_slot(sibling.real_payload_body(sibling.SHOCK_A))
    )
    steps: list[b9.StoredStep] = []
    with torch.no_grad():
        for time_index in range(b9.HORIZON):
            observations = np.full(
                (capacity, 10),
                np.float64((index + 1) * (time_index + 1) / 1000.0),
                dtype=np.float64,
            )
            active_mask = np.ones(capacity, dtype=np.bool_)
            slot = np.zeros((capacity, actuation.SLOT_DIM), dtype=np.float32)
            if 12 <= time_index < 24 or 36 <= time_index < 48:
                slot[1] = receiver_slot
            noise = np.full(
                (capacity, actor.actor.out_features),
                np.float32(((time_index + index) % 5 - 2) / 10.0),
            )
            action, kernel, new_hidden, _ = actor._step_tensors(
                observations, active_mask, slot, previous, noise
            )
            steps.append(
                b9.StoredStep(
                    observations,
                    active_mask,
                    slot,
                    noise,
                    action.cpu().numpy().astype(np.float32),
                    kernel.cpu().numpy().astype(np.float32),
                    float(((time_index + 2 * index) % 7) - 3),
                )
            )
            previous = new_hidden.detach()
    edges = {
        12: _edge(event=0, profile=profile_name, root_id=registered_root),
        36: _edge(event=2, profile=profile_name, root_id=registered_root),
    }
    digest = b9._trajectory_digest(steps, edges)
    return b9.StoredTrajectory(
        "A0",
        profile_name,
        registered_root,
        index % len(b9.SHOCK_TUPLES),
        b9.SHOCK_TUPLES[index % len(b9.SHOCK_TUPLES)],
        tuple(steps),
        edges,
        digest,
        f"lifecycle-{index}",
        f"noise-{index}",
    )


def test_registered_activity_is_derived_from_the_exact_factorization() -> None:
    plan = b9.FULL_PLAN
    assert plan.collection_episodes == 2 * 3 * 4 == 24
    assert plan.evaluation_episodes == 2 * 3 * 8 * 3 * 2 == 288
    assert plan.optimizer_calls == 2 * 2 == 4
    assert plan.expected_counts["episodes"] == 312
    assert plan.expected_counts["environment_transitions"] == 312 * 48 == 14_976
    assert plan.expected_counts["policy_calls"] == 14_976
    assert plan.expected_counts["global_clip_calls"] == 0
    assert plan.expected_counts["critic_loss_calls"] == 0
    assert plan.expected_counts["value_gradient_calls"] == 0
    assert plan.expected_counts["second_updates"] == 0
    assert plan.expected_counts["k_search"] == 0


def test_addressed_loss_uses_receiver_or_authenticated_distinct_source_only() -> None:
    rows = [torch.tensor([100.0, 2.0, 3.0]) for _ in range(b9.HORIZON)]
    masks = [np.ones(3, dtype=np.bool_) for _ in range(b9.HORIZON)]
    credits = torch.ones(b9.HORIZON)
    edges = {12: _edge(event=0), 36: _edge(event=2)}
    receiver, receiver_manifest = b9.addressed_credit_loss(
        rows, masks, credits, edges, b9.RECEIVER_ADDRESSED
    )
    source, source_manifest = b9.addressed_credit_loss(
        rows, masks, credits, edges, b9.SOURCE_CONTROL
    )
    assert float(receiver) == pytest.approx(-2.0)
    assert float(source) == pytest.approx(-3.0)
    assert receiver_manifest["term_count"] == source_manifest["term_count"] == 24
    assert receiver_manifest["common_time_order"] == source_manifest["common_time_order"]
    assert [member for _, member in receiver_manifest["address_order"]] == [1] * 24
    assert [member for _, member in source_manifest["address_order"]] == [2] * 24


def test_addressed_loss_rejects_alias_inactivity_count_and_nonfinite() -> None:
    rows = [torch.ones(3) for _ in range(b9.HORIZON)]
    masks = [np.ones(3, dtype=np.bool_) for _ in range(b9.HORIZON)]
    credits = torch.ones(b9.HORIZON)
    with pytest.raises(b9.BindingFailure, match="not distinct"):
        b9.addressed_credit_loss(
            rows,
            masks,
            credits,
            {12: _edge(source=1, event=0), 36: _edge(source=1, event=2)},
            b9.RECEIVER_ADDRESSED,
        )
    inactive = [value.copy() for value in masks]
    inactive[12][2] = False
    with pytest.raises(b9.BindingFailure, match="active score row"):
        b9.addressed_credit_loss(
            rows,
            inactive,
            credits,
            {12: _edge(event=0), 36: _edge(event=2)},
            b9.SOURCE_CONTROL,
        )
    with pytest.raises(b9.BindingFailure, match="complete episode"):
        b9.addressed_credit_loss(
            rows[:-1], masks, credits, {12: _edge(), 36: _edge(event=2)}, b9.RECEIVER_ADDRESSED
        )
    credits[12] = float("nan")
    with pytest.raises(b9.BindingFailure, match="nonfinite detached scalar"):
        b9.addressed_credit_loss(
            rows, masks, credits, {12: _edge(), 36: _edge(event=2)}, b9.RECEIVER_ADDRESSED
        )


def test_common_gradients_reaches_both_finite_branches_without_inactive_parameters() -> None:
    actor = b9._new_actor("A0")
    anchor_digest = b9._state_digest(b9._clone_state(actor))
    names = tuple(name for name, _ in b9._actor_path_named_parameters(actor))
    assert names == b9.ACTIVE_ACTOR_PARAMETER_NAMES
    assert not {"slot.weight", "slot.bias", "value.weight", "value.bias"} & set(names)
    trajectories = [_synthetic_stored_trajectory(actor, index) for index in range(12)]
    gradients, common = b9._common_gradients(actor, trajectories)
    assert set(gradients) == set(b9.ADDRESSING_BRANCHES)
    assert all(torch.isfinite(value).all() for branch in gradients.values() for value in branch)
    assert common["term_count"] == 288
    assert common["branch_common_bindings_identical"] is True
    assert common["branch_common_bindings"][b9.RECEIVER_ADDRESSED] == common[
        "branch_common_bindings"
    ][b9.SOURCE_CONTROL]
    assert common["gradients_computed_before_mutation"] is True
    assert b9._state_digest(b9._clone_state(actor)) == anchor_digest


def test_normalized_gae_credit_is_finite_detached_and_normalized() -> None:
    values = [torch.tensor(float(index) / 10.0, requires_grad=True) for index in range(b9.HORIZON)]
    credits = b9._normalized_gae_credits(
        [float((index % 5) - 2) for index in range(b9.HORIZON)], values
    )
    assert credits.shape == (b9.HORIZON,)
    assert torch.isfinite(credits).all()
    assert credits.requires_grad is False
    assert float(credits.mean()) == pytest.approx(0.0, abs=2e-6)
    assert float(credits.std(unbiased=False)) == pytest.approx(1.0, abs=2e-6)


def test_collect_trajectory_validates_fake_receiver_binding_without_environment_activity() -> None:
    actor = b9._new_actor("A0")
    synthetic = _synthetic_stored_trajectory(
        actor, 0, profile=b9.PROFILE_NAMES[0], root_id=b9.COLLECTION_ROOTS[("A0", b9.PROFILE_NAMES[0])][0]
    )
    policy_steps = [
        {
            "observations": step.observations,
            "active_mask": step.active_mask,
            "effective_slot_block": step.effective_slot_block,
            "noise": step.noise,
            "sampled_action": step.sampled_action,
            "action_kernel": step.action_kernel,
            "reward": step.reward,
        }
        for step in synthetic.steps
    ]
    records = [
        SimpleNamespace(
            receipt=SimpleNamespace(
                physical_tick=start,
                opportunity_identity=synthetic.critical_edges.get(
                    start,
                    _edge(
                        event=event,
                        profile=synthetic.profile,
                        root_id=synthetic.root_id,
                    ),
                ),
            )
        )
        for start, event in ((12, 0), (24, 1), (36, 2))
    ]
    fake_runner = SimpleNamespace(
        policy=SimpleNamespace(steps=policy_steps),
        env=SimpleNamespace(reward_trace=[step.reward for step in synthetic.steps]),
        boundary_records=records,
        noise=np.zeros(
            (b9.HORIZON, actor.capacity, actor.actor.out_features), dtype=np.float32
        ),
        run_episode=lambda: 0.0,
    )
    counts = b9._empty_counts()
    guard = b9.ResourceGuard(cpu_clock=lambda: 0.0, rss_reader=lambda: 1)
    collected = b9._collect_trajectory(
        actor,
        "A0",
        b9.PROFILE_NAMES[0],
        synthetic.root_id,
        0,
        counts,
        guard,
        runner_factory=lambda *args, **kwargs: fake_runner,
        record_activity=False,
    )
    assert collected.critical_edges == synthetic.critical_edges
    assert counts == b9._empty_counts()


def test_contrast_formulas_and_exact_coordinate_coverage() -> None:
    rows = b9._synthetic_evaluation_rows()
    cells = b9.contrast_cells(rows)
    assert len(rows) == 288
    assert len(cells) == 48
    cell = cells[0]
    assert cell["phi_0"] == pytest.approx(1.0)
    assert cell["phi_R"] == pytest.approx(2.0)
    assert cell["phi_S"] == pytest.approx(0.5)
    assert cell["Delta_R"] == pytest.approx(1.0)
    assert cell["J"] == pytest.approx(1.5)
    with pytest.raises(b9.BindingFailure, match="coordinate coverage"):
        b9.contrast_cells(rows[:-1])


def test_robust_aggregates_cover_both_anchors_and_every_leave_one_coordinate() -> None:
    cells = b9.contrast_cells(b9._synthetic_evaluation_rows())
    aggregates = b9.robust_aggregates(cells)
    assert set(aggregates["by_anchor"]) == set(b9.ANCHOR_IDS)
    assert set(aggregates["leave_one_profile"]) == set(b9.PROFILE_NAMES)
    assert set(aggregates["leave_one_root"]) == {str(index) for index in range(8)}
    assert all(row["J"] == pytest.approx(1.5) for row in aggregates["by_anchor"].values())
    duplicated = copy.deepcopy(cells)
    duplicated[-1]["root_index"] = duplicated[-2]["root_index"]
    duplicated[-1]["heldout_root"] = duplicated[-2]["heldout_root"]
    with pytest.raises(b9.BindingFailure, match="coordinate coverage"):
        b9.robust_aggregates(duplicated)


def test_terminal_precedence_and_global_only_absolute_correct_grammar() -> None:
    semantic = _robust(
        {
            "J": 1.0,
            "Delta_R": 1.0,
            "receiver_correct_vs_anchor": 0.0,
            "receiver_correct_vs_source": 0.0,
            "source_correct_vs_anchor": 1.0,
            "receiver_two_arm_generic_gain": 2.0,
        }
    )
    semantic["by_anchor"]["A0"]["receiver_correct_vs_anchor"] = -10.0
    semantic["leave_one_root"]["0"]["receiver_correct_vs_source"] = -10.0
    assert b9.select_terminal_branch(semantic, binding_valid=False) == "B9_INVALID_BINDING"
    assert b9.select_terminal_branch(semantic, binding_valid=True) == "B9_RECEIVER_ADDRESSED_SEMANTIC_EDGE"

    generic = copy.deepcopy(semantic)
    generic["global"]["J"] = 0.0
    assert b9.select_terminal_branch(generic, binding_valid=True) == "B9_GENERIC_OR_SOURCE_HARM_ONLY"

    unsupported = _robust(
        {
            "J": -0.1,
            "Delta_R": 1.0,
            "receiver_correct_vs_anchor": 1.0,
            "receiver_correct_vs_source": 0.5,
            "source_correct_vs_anchor": 0.5,
            "receiver_two_arm_generic_gain": 0.0,
        }
    )
    assert b9.select_terminal_branch(unsupported, binding_valid=True) == "B9_RECEIVER_NOT_SUPPORTED"
    unsupported["by_anchor"]["A0"]["J"] = 1.0
    assert b9.select_terminal_branch(unsupported, binding_valid=True) == "B9_MIXED_UNIDENTIFIED"


def test_branch_three_uses_global_damage_and_any_robust_delta_instability() -> None:
    base = {
        "J": -1.0,
        "Delta_R": 1.0,
        "receiver_correct_vs_anchor": 0.0,
        "receiver_correct_vs_source": 0.0,
        "source_correct_vs_anchor": 0.0,
        "receiver_two_arm_generic_gain": 0.0,
    }
    unstable = _robust(base)
    unstable["leave_one_root"]["0"]["Delta_R"] = 0.0
    assert b9.select_terminal_branch(unstable, binding_valid=True) == "B9_GENERIC_OR_SOURCE_HARM_ONLY"
    for metric in (
        "receiver_correct_vs_anchor",
        "receiver_correct_vs_source",
        "source_correct_vs_anchor",
    ):
        damaged = _robust(base)
        damaged["global"][metric] = -0.1
        assert b9.select_terminal_branch(damaged, binding_valid=True) == "B9_GENERIC_OR_SOURCE_HARM_ONLY"


def test_one_step_endpoint_zero_identity_and_actor_only_empty_adam() -> None:
    actor = b9._new_actor("A0")
    state = b9._clone_state(actor)
    anchor_digest = b9._state_digest(state)
    gradients = tuple(
        torch.zeros_like(parameter) for _, parameter in b9._actor_path_named_parameters(actor)
    )
    counts = b9._empty_counts()
    endpoint, witness = b9._apply_one_actor_step(
        "A0", state, gradients, b9.RECEIVER_ADDRESSED, counts
    )
    assert b9._state_digest(state) == anchor_digest
    assert witness["anchor_state_digest"] == anchor_digest
    assert witness["empty_state_before"] is True
    assert witness["step_index_after"] == 1
    assert witness["value_head_unchanged"] is True
    assert witness["global_clip_calls"] == witness["critic_loss_calls"] == 0
    assert counts["optimizer_calls"] == counts["receiver_optimizer_calls"] == 1
    for name in state:
        if name.startswith("value."):
            assert torch.equal(state[name], endpoint[name])


def test_resource_guard_uses_windows_peak_and_fails_closed_before_activity(monkeypatch) -> None:
    counters = SimpleNamespace(PeakWorkingSetSize=9, WorkingSetSize=3)
    assert b9._windows_rss_from_counters(counters) == 9
    cpu_values = iter((0.0, float(b9.CPU_TIME_CAP_SECONDS) + 0.01))
    guard = b9.ResourceGuard(cpu_clock=lambda: next(cpu_values), rss_reader=lambda: 1)
    with pytest.raises(b9.BindingFailure, match="CPU-minute"):
        guard.check()

    class FailingGuard:
        def __init__(self):
            raise b9.BindingFailure("guard construction failed")

    monkeypatch.setattr(b9, "ResourceGuard", FailingGuard)
    result = b9.run_registered(
        candidate_revision=CANDIDATE_REVISION,
        checkout_revision=CANDIDATE_REVISION,
        checkout_clean=True,
        run_id="eociv-b9-guard-proof",
    )
    assert result["terminal_branch"] == "B9_INVALID_BINDING"
    assert result["counts"] == b9._empty_counts()

    class CheckFailingGuard:
        def check(self):
            raise b9.BindingFailure("initial guard check failed")

        def witness(self):
            return {"within_caps": False}

    monkeypatch.setattr(b9, "ResourceGuard", CheckFailingGuard)
    checked = b9.run_registered(
        candidate_revision=CANDIDATE_REVISION,
        checkout_revision=CANDIDATE_REVISION,
        checkout_clean=True,
        run_id="eociv-b9-guard-check-proof",
    )
    assert checked["terminal_branch"] == "B9_INVALID_BINDING"
    assert checked["counts"] == b9._empty_counts()


def test_candidate_readiness_requires_explicit_clean_nonbase_head_and_zero_activity(tmp_path) -> None:
    before = list(tmp_path.iterdir())
    ready = _ready()
    assert ready["ready"] is True
    assert ready["candidate_revision"] == ready["checkout_revision"] == CANDIDATE_REVISION
    assert ready["episodes"] == ready["environment_transitions"] == ready["optimizer_calls"] == 0
    assert _ready(candidate_revision=b9.BASE_REVISION, checkout_revision=b9.BASE_REVISION)["ready"] is False
    assert _ready(checkout_revision=OTHER_REVISION)["ready"] is False
    assert _ready(checkout_clean=False)["ready"] is False
    assert b9.readiness(
        candidate_revision="ABC", checkout_revision="ABC", checkout_clean=True
    )["ready"] is False
    assert list(tmp_path.iterdir()) == before


def test_readiness_rejects_derived_count_drift(monkeypatch) -> None:
    drifted = dict(b9.FULL_EXPECTED_COUNTS)
    drifted["episodes"] -= 1
    monkeypatch.setattr(b9, "FULL_EXPECTED_COUNTS", drifted)
    result = _ready()
    assert result["ready"] is False
    assert any("activity" in issue for issue in result["issues"])


def test_six_phase_temporary_lifecycle_is_ordered_zero_science_and_no_reserved_result(tmp_path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    exercise = tmp_path / "eociv-b9-readiness-exercise"
    exercise.mkdir()
    log_root = exercise / ".hmasd-readiness-logs"
    log_root.mkdir()
    (log_root / "interface_smoke.stdout.log").write_text("wrapper-owned\n", encoding="utf-8")
    artifacts = []
    for phase in b9.READINESS_PHASES:
        artifact = b9.run_readiness_phase(
            phase,
            exercise_root=exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )
        artifacts.append(artifact)
        assert artifact["counts"] == b9.ZERO_SCIENCE_COUNTS
        assert artifact["scientific_terminal_admitted"] is False
    assert [artifact["phase"] for artifact in artifacts] == list(b9.READINESS_PHASES)
    assert artifacts[-1]["payload"]["terminal_branch"] == "B9_RECEIVER_ADDRESSED_SEMANTIC_EDGE"
    assert len(list(exercise.glob("*.json"))) == 6
    assert not (repository / b9.RESULT_RELATIVE_PATH).exists()
    with pytest.raises(b9.BindingFailure, match="repeated or out of order"):
        b9.analyze_entry(
            exercise_root=exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )


def test_phase_candidate_mismatch_and_tampered_artifact_reload_fail_closed(tmp_path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    exercise = tmp_path / "exercise"
    exercise.mkdir()
    (exercise / ".hmasd-readiness-logs").mkdir()
    b9.interface_smoke(
        exercise_root=exercise,
        repository_root=repository,
        candidate_revision=CANDIDATE_REVISION,
        checkout_revision=CANDIDATE_REVISION,
        checkout_clean=True,
    )
    with pytest.raises(b9.BindingFailure, match="candidate mismatch"):
        b9.bounded_exercise(
            exercise_root=exercise,
            repository_root=repository,
            candidate_revision=OTHER_REVISION,
            checkout_revision=OTHER_REVISION,
            checkout_clean=True,
        )
    first = exercise / b9.READINESS_PHASE_FILES["interface_smoke"]
    value = json.loads(first.read_text(encoding="utf-8"))
    value["payload"]["k_search"] = 1
    first.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(b9.BindingFailure, match="digest mismatch"):
        b9.bounded_exercise(
            exercise_root=exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )

    reload_exercise = tmp_path / "reload-exercise"
    reload_exercise.mkdir()
    (reload_exercise / ".hmasd-readiness-logs").mkdir()
    for phase in b9.READINESS_PHASES[:3]:
        b9.run_readiness_phase(
            phase,
            exercise_root=reload_exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )
    validation_path = reload_exercise / b9.READINESS_PHASE_FILES["artifact_validation"]
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation["payload"]["validated_phases"] = []
    validation_path.write_text(json.dumps(validation), encoding="utf-8")
    with pytest.raises(b9.BindingFailure, match="digest mismatch"):
        b9.artifact_reload(
            exercise_root=reload_exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )


def test_interface_smoke_rejects_consumed_reserved_result_namespace(tmp_path) -> None:
    repository = tmp_path / "repository"
    reserved = repository / b9.RESULT_RELATIVE_PATH
    reserved.parent.mkdir(parents=True)
    reserved.write_text("{}\n", encoding="utf-8")
    exercise = tmp_path / "exercise"
    exercise.mkdir()
    (exercise / ".hmasd-readiness-logs").mkdir()
    with pytest.raises(b9.BindingFailure, match="already consumed"):
        b9.interface_smoke(
            exercise_root=exercise,
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
        )
    assert not (exercise / b9.READINESS_PHASE_FILES["interface_smoke"]).exists()


def test_registered_lifecycle_claims_exact_result_once_before_mocked_full(tmp_path) -> None:
    repository = tmp_path / "repository"
    result_path = repository / b9.RESULT_RELATIVE_PATH
    observed: dict[str, object] = {}

    def fake_full(**kwargs: object) -> dict[str, object]:
        claim = json.loads(result_path.read_text(encoding="utf-8"))
        observed["claim"] = claim
        assert claim["status"] == "CLAIMED_BEFORE_EPISODE_ONE"
        assert claim["candidate_revision"] == kwargs["candidate_revision"]
        assert claim["run_id"] == kwargs["run_id"]
        return {
            "artifact_kind": "EOCIV_B9_REGISTERED_RESULT_IN_MEMORY",
            "candidate_revision": kwargs["candidate_revision"],
            "run_id": kwargs["run_id"],
            "terminal_branch": "B9_INVALID_BINDING",
            "counts": dict(b9.FULL_EXPECTED_COUNTS),
        }

    with pytest.raises(b9.BindingFailure, match="readiness rejected"):
        b9.run_registered_lifecycle(
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=OTHER_REVISION,
            checkout_clean=True,
            run_id="eociv-b9-mismatched-candidate",
            full_runner=fake_full,
        )
    assert not result_path.exists()
    with pytest.raises(b9.BindingFailure, match="run id"):
        b9.run_registered_lifecycle(
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
            run_id="../unsafe",
            full_runner=fake_full,
        )
    assert not result_path.exists()

    result = b9.run_registered_lifecycle(
        repository_root=repository,
        candidate_revision=CANDIDATE_REVISION,
        checkout_revision=CANDIDATE_REVISION,
        checkout_clean=True,
        run_id="eociv-b9-mocked-full",
        full_runner=fake_full,
    )
    assert result_path == repository / Path(
        "docs/research/candidates/eociv_lite/"
        "EOCIV_B9_RECEIVER_ADDRESSED_CREDIT_EDGE_RESULT.json"
    )
    assert json.loads(result_path.read_text(encoding="utf-8"))["run_id"] == "eociv-b9-mocked-full"
    assert result["result_relative_path"] == b9.RESULT_RELATIVE_PATH.as_posix()
    with pytest.raises(FileExistsError):
        b9.run_registered_lifecycle(
            repository_root=repository,
            candidate_revision=CANDIDATE_REVISION,
            checkout_revision=CANDIDATE_REVISION,
            checkout_clean=True,
            run_id="eociv-b9-mocked-full-second",
            full_runner=fake_full,
        )


def test_fresh_namespace_rejects_predecessor_artifact_and_root_reuse() -> None:
    issues = b9.validate_namespace_binding(
        raw_output_binding="eociv_lite.b7.history.v1",
        treatment="EOCIV-B7-CHECKPOINT-RESCUE",
        collection_roots=(990_100, 990_100),
        heldout_roots=(990_100,),
        artifact_inputs=("predecessor/result.json",),
    )
    assert any("fresh B9" in issue for issue in issues)
    assert any("predecessor" in issue for issue in issues)
    assert any("artifact" in issue for issue in issues)
    assert any("not unique" in issue for issue in issues)
    assert any("overlap" in issue for issue in issues)
