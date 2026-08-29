from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding import b2
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.b2 import host as b2_host
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.b2 import rng as b2_rng
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.b3 import analysis, config, host, policies, run


def test_fixed_policy_episode_is_bit_identical_to_b2_host() -> None:
    coordinate = dict(seed=271, episode_index=3, namespace=config.DISCOVERY_NAMESPACE, schedule=config.IID_SCHEDULE)
    b2_episode = b2_host.generate_episode(**coordinate)
    b3_episode = host.generate_episode(**coordinate)
    assert np.array_equal(b3_episode.mode, b2_episode.mode)
    assert np.array_equal(b3_episode.sensors, b2_episode.sensors)
    assert np.array_equal(b3_episode.preroll, b2_episode.preroll)
    assert b3_episode.initial_bindings == b2_episode.initial_bindings
    assert b3_episode.initial_plan_ages == b2_episode.initial_plan_ages
    policy = policies.FixedPolicy("PARITY", "global_p", (0,), probability=0.27)
    expected = b2_host.run_episode(b2_episode, arm="RATE-FLEX", learner=policy)
    observed = host.run_episode(b3_episode, policy=policy)
    assert observed.normalized_return == expected.normalized_return
    assert observed.service == expected.service
    assert observed.action_cost == expected.action_cost
    assert observed.physics_ledger == expected.physics_ledger
    assert observed.routine_boundary_ticks == expected.routine_boundary_ticks
    assert observed.iid_draw_records == expected.iid_draw_records
    assert observed.iid_terminal_censored_duration == expected.iid_terminal_censored_duration


def test_b3_counter_primitive_matches_b2_and_banks_are_distinct() -> None:
    coordinates = (config.DISCOVERY_NAMESPACE, 271, 0, 16, 1)
    assert host.counter_uniform("ACTION_EVENT_UNIFORM", *coordinates) == b2_rng.counter_uniform(
        "ACTION_EVENT_UNIFORM", *coordinates,
    )
    discovery = host.counter_uniform("ACTION_EVENT_UNIFORM", config.DISCOVERY_NAMESPACE, 271, 0, 16, 1)
    confirmation = host.counter_uniform("ACTION_EVENT_UNIFORM", config.CONFIRMATION_NAMESPACE, 271, 0, 16, 1)
    assert discovery != confirmation
    first = host.generate_episode(seed=271, episode_index=0, namespace=config.DISCOVERY_NAMESPACE)
    second = host.generate_episode(seed=271, episode_index=0, namespace=config.CONFIRMATION_NAMESPACE)
    assert first.namespace != second.namespace


@pytest.mark.parametrize("value,label", [(0, "low"), (15.999, "low"), (16, "high"), (32, "high")])
def test_exposure_bin_boundaries(value: float, label: str) -> None:
    assert policies.exposure_bin(value) == label


@pytest.mark.parametrize("value", [-1, 32.0001])
def test_exposure_outside_frozen_range_is_invalid(value: float) -> None:
    with pytest.raises(ValueError):
        policies.exposure_bin(value)


def test_q_probability_grid_and_lambda_matching() -> None:
    exposures = (4.0, 8.0, 16.0, 32.0) * 10
    q0 = policies.q_from_exposures(exposures)
    grid = policies.shifted_probability_grid(q0)
    assert len(grid) == 5 and tuple(sorted(grid)) == grid
    assert grid[2] == pytest.approx(q0, abs=1e-15)
    solved = tuple(policies.solve_marginal_lambda(exposures, target) for target in grid)
    for target, rate in zip(grid, solved, strict=True):
        assert policies.q_from_exposures(exposures, rate) == pytest.approx(target, abs=2e-15)
    assert solved[2] == pytest.approx(config.LAMBDA_REF, abs=2e-15)


def test_discovery_grid_has_exact_frozen_families() -> None:
    q0, grid, members = policies.discovery_grid((4, 16, 32) * 20)
    assert 0 < q0 < 1 and len(grid) == 5 and len(members) == 35
    assert sum(member.family == "stratified" for member in members) == 25
    assert sum(member.family == "global_p" for member in members) == 5
    assert sum(member.family == "global_lambda" for member in members) == 5


def _selection_metrics(policy_rows: list[tuple[policies.FixedPolicy, float, float]]):
    return {
        policy.policy_id: {
            root: {"direct_return": direct, "activity": activity}
            for root in config.ROOTS
        } for policy, direct, activity in policy_rows
    }


def test_selection_exact_ties_follow_activity_separation_and_lexicographic_index() -> None:
    a = policies.FixedPolicy("A", "stratified", (0, 4), p_low=0.1, p_high=0.5)
    b = policies.FixedPolicy("B", "stratified", (1, 3), p_low=0.2, p_high=0.4)
    c = policies.FixedPolicy("C", "stratified", (1, 2), p_low=0.2, p_high=0.4)
    metrics = _selection_metrics([(a, 1.0, 0.1), (b, 1.0, 0.1), (c, 1.0, 0.1)])
    assert policies.select_best((a, b, c), metrics, config.ROOTS) is c
    metrics = _selection_metrics([(a, 1.0, 0.09), (b, 1.0, 0.1)])
    assert policies.select_best((a, b), metrics, config.ROOTS) is a
    metrics = _selection_metrics([(a, 1.0, 0.2), (b, 1.0000000000001, 0.9)])
    assert policies.select_best((a, b), metrics, config.ROOTS) is b


def test_post_action_iid_order_and_reward_decomposition() -> None:
    episode = host.generate_episode(seed=277, episode_index=2, namespace=config.DISCOVERY_NAMESPACE)
    result = host.run_episode(episode, policy=policies.FixedPolicy("P", "global_p", (0,), probability=0.4))
    assert tuple(row[0] for row in result.iid_draw_records) == tuple(range(len(result.iid_draw_records)))
    assert tuple(row[1] for row in result.iid_draw_records) == result.routine_boundary_ticks
    assert tuple(row[2] for row in result.iid_draw_records) == result.iid_interval_draws
    assert result.reward_service_cost_exact
    assert result.normalized_return == pytest.approx(result.service - result.action_cost, abs=1e-12)
    assert result.terminal_boundary_absent


def _synthetic_episode(legal_rows: tuple[tuple[int, int, int, bool], ...]) -> host.EpisodeResult:
    return host.EpisodeResult(
        policy_id="SYNTHETIC", namespace=config.CONFIRMATION_NAMESPACE, seed=271,
        episode_index=0, normalized_return=0.5, service=0.52, action_cost=0.02,
        physics_ticks=config.HORIZON, routine_boundary_ticks=(0, 16, 32, 48),
        iid_interval_draws=(16, 16, 16, 32),
        iid_draw_records=((0, 0, 16, False), (1, 16, 16, False), (2, 32, 16, False), (3, 48, 32, False)),
        iid_terminal_censored_duration=32, legal_action_rows=legal_rows, rate_rows=(),
        identity_rows=(), identity_unique=True, reward_service_cost_exact=True,
        segment_ownership_exact=True, terminal_boundary_absent=True,
        plan_age_sum=0, physics_ledger=(),
    )


def test_initial_anchor_is_excluded_from_legal_activity_and_event_support() -> None:
    summary = analysis.summarize_root((_synthetic_episode((
        (8, 2, 0, True),
        (16, 0, 0, False),
    )),))
    assert summary["legal_rows"] == {"low": 0, "high": 1}
    assert summary["voluntary_non_keep_events"] == 0
    assert summary["activity"] == 0.0


def test_event_free_reachability_includes_first_event_but_not_later_keep() -> None:
    summary = analysis.summarize_root((_synthetic_episode((
        (8, 0, 0, True),
        (8, 1, 0, False),   # First post-startup event is reached event-free.
        (16, 0, 0, False),  # KEEP after that event is not event-free.
        (8, 0, 1, False),   # The other role still has event-free reachability.
    )),))
    assert summary["legal_rows"] == {"low": 2, "high": 1}
    assert summary["event_free_legal_rows"] == {"low": 2, "high": 0}
    assert summary["voluntary_non_keep_events"] == 1


def test_f0_construction_excludes_initial_anchor_rows() -> None:
    episode = _synthetic_episode(((8, 0, 0, True), (16, 0, 0, False)))
    f0 = tuple(exposure for exposure, _action, _role, initial in episode.legal_action_rows if not initial)
    assert f0 == (16,)


def _root_rows(*, events_per_bin: int = 10, legal_per_bin: int = 100, event_free_per_bin: int = 90):
    rows = {}
    for root in config.ROOTS:
        actions = {
            "low": {"KEEP": legal_per_bin - events_per_bin, "REFRESH-SAME": events_per_bin // 2, "REBIND": events_per_bin - events_per_bin // 2},
            "high": {"KEEP": legal_per_bin - events_per_bin, "REFRESH-SAME": events_per_bin // 2, "REBIND": events_per_bin - events_per_bin // 2},
        }
        rows[root] = {
            "legal_rows": {"low": legal_per_bin, "high": legal_per_bin},
            "event_free_legal_rows": {"low": event_free_per_bin, "high": event_free_per_bin},
            "actions": actions,
            "voluntary_non_keep_events": 2 * events_per_bin,
            "activity": events_per_bin / legal_per_bin,
            "direct_return": 0.5,
            "service": 0.52,
            "action_cost": 0.02,
        }
    return rows


def test_support_and_shell_positive_and_negative_polarities() -> None:
    candidate = _root_rows()
    shell = _root_rows()
    supported = analysis.support_and_shell_conformance(candidate, shell)
    assert supported["pass"]
    sparse = _root_rows(legal_per_bin=20, event_free_per_bin=19, events_per_bin=1)
    assert not analysis.support_and_shell_conformance(sparse, shell)["pass"]
    mismatched_shell = _root_rows(events_per_bin=40, event_free_per_bin=60)
    result = analysis.support_and_shell_conformance(candidate, mismatched_shell)
    assert not result["shell"]["pass"] and not result["pass"]


def test_candidate_requires_strictly_more_than_one_hundred_events() -> None:
    candidate = _root_rows(events_per_bin=3)
    # Freeze exactly 100 events without changing legal support.
    remaining = 100
    for root in config.ROOTS:
        for label in ("low", "high"):
            count = min(remaining, 4)
            candidate[root]["actions"][label]["REFRESH-SAME"] = count // 2
            candidate[root]["actions"][label]["REBIND"] = count - count // 2
            candidate[root]["actions"][label]["KEEP"] = 100 - count
            remaining -= count
    assert remaining == 0
    for root in config.ROOTS:
        candidate[root]["voluntary_non_keep_events"] = sum(
            candidate[root]["actions"][label][name]
            for label in ("low", "high") for name in ("REFRESH-SAME", "REBIND")
        )
    result = analysis.support_and_shell_conformance(candidate, _root_rows())
    assert result["candidate"]["voluntary_non_keep_events"] == 100
    assert not result["candidate"]["pass"]


def _contrasts(lower: float, upper: float, global_p_lower: float | None = None):
    result = {}
    for name in ("global_lambda", "keep", "shell", "global_p"):
        lo = global_p_lower if name == "global_p" and global_p_lower is not None else lower
        result[name] = {"components": {"direct_return": {"one_sided_95_lower": lo, "one_sided_95_upper": upper}}}
    return result


def _heterogeneity(stable: int = 16, clean: bool = True):
    return {"monotone_separated_count": stable, "near_optimal_set_excludes_homogeneous_and_weak": clean}


def test_every_frozen_result_branch() -> None:
    grid = (0.1, 0.2, 0.3, 0.4, 0.5)
    interior = policies.FixedPolicy("S", "stratified", (1, 3), p_low=0.2, p_high=0.4)
    branch, facts = analysis.decide_branch(valid=False, contrasts=_contrasts(0.1, 0.2), candidate=interior, grid=grid, heterogeneity=_heterogeneity())
    assert branch == "INVALID" and sum(facts["branches"].values()) == 1
    branch, _ = analysis.decide_branch(valid=True, contrasts=_contrasts(-0.1, 0.0), candidate=interior, grid=grid, heterogeneity=_heterogeneity())
    assert branch == "BOUNDED_NO_HEADROOM"
    branch, _ = analysis.decide_branch(valid=True, contrasts=_contrasts(0.0, 0.01), candidate=interior, grid=grid, heterogeneity=_heterogeneity())
    assert branch == "HEADROOM_UNRESOLVED"
    branch, _ = analysis.decide_branch(valid=True, contrasts=_contrasts(0.01, 0.02, global_p_lower=0.0), candidate=interior, grid=grid, heterogeneity=_heterogeneity())
    assert branch == "HEADROOM_WITHOUT_IDENTIFIED_EXPOSURE_HETEROGENEITY"
    branch, _ = analysis.decide_branch(valid=True, contrasts=_contrasts(0.01, 0.02), candidate=interior, grid=grid, heterogeneity=_heterogeneity())
    assert branch == "HEADROOM_AND_EXPOSURE_HETEROGENEITY"


def test_paired_inference_uses_sixteen_roots_and_reports_decomposition() -> None:
    candidate = _root_rows()
    comparator = _root_rows()
    for index, root in enumerate(config.ROOTS):
        candidate[root]["direct_return"] += index / 1000
        candidate[root]["service"] += index / 800
        candidate[root]["action_cost"] += index / 4000
    result = analysis.contrast_summary(candidate, comparator)
    assert result["components"]["direct_return"]["n"] == 16
    assert len(result["components"]["direct_return"]["leave_one_root_out_means"]) == 16
    assert set(result["components"]) == {"direct_return", "service", "action_cost"}
    assert len(result["root_differences"]) == 16


def test_exact_registered_work_accounting() -> None:
    assert config.DISCOVERY_TEAM_TICKS == 1_179_648
    assert config.CONFIRMATION_TEAM_TICKS == 1_310_720
    assert config.TOTAL_TEAM_TICKS == 2_490_368
    assert config.registered_work()["total_team_ticks"] == 2_490_368


def test_resource_monitor_hard_limits_are_terminal_facts() -> None:
    times = iter((0.0, 2.0))
    monitor = run.ResourceMonitor(clock=lambda: next(times), rss_supplier=lambda: 1, max_seconds=1.0)
    with pytest.raises(run.ResourceLimitExceeded) as caught:
        monitor.check()
    assert caught.value.limit == "wall_seconds"
    monitor = run.ResourceMonitor(clock=lambda: 0.0, rss_supplier=lambda: 101, max_rss_bytes=100)
    with pytest.raises(run.ResourceLimitExceeded) as caught:
        monitor.check()
    assert caught.value.limit == "peak_rss_bytes"


def test_hard_limit_publishes_one_atomic_invalid_terminal_without_resume() -> None:
    samples = iter((0.0, 2.0, 2.0, 2.0))
    monitor = run.ResourceMonitor(
        clock=lambda: next(samples), rss_supplier=lambda: 1,
        max_seconds=1.0, max_rss_bytes=config.MAX_RSS_BYTES,
    )
    with tempfile.TemporaryDirectory() as directory:
        path = run.run_registered(Path(directory) / "fresh", monitor=monitor)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["terminal"] is True
        assert payload["branch"] == "INVALID"
        assert payload["resources"]["terminal_nonpass"] == "RESOURCE_LIMIT_NONPASS"
        assert payload["resources"]["actual_team_ticks"] == 0
        assert sum(payload["gates"]["branches"].values()) == 1
        before = path.read_bytes()
        with pytest.raises(run.OutputStateError):
            run.run_registered(path.parent, monitor=monitor)
        assert path.read_bytes() == before


def test_atomic_result_serialization_and_one_shot_refusal() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / config.RESULT_FILENAME
        payload = {"terminal": True, "branch": "INVALID", "branches": {name: name == "INVALID" for name in config.BRANCHES}}
        count = run.atomic_write_json(path, payload)
        assert count == len(path.read_bytes())
        assert json.loads(path.read_text(encoding="utf-8")) == payload
        assert not tuple(item for item in path.parent.iterdir() if item.name.startswith(f".{path.name}"))
        with pytest.raises(run.OutputStateError):
            run.atomic_write_json(path, payload)


def _write_launcher_scaffold(cwd: Path, head: str = "a" * 40) -> Path:
    root = (cwd / run.FROZEN_OUTPUT_RELATIVE).resolve()
    root.mkdir(parents=True)
    for name in ("artifacts", "checkpoints", "metrics"):
        (root / name).mkdir()
    (root / "stdout.log").touch()
    (root / "stderr.log").touch()
    (root / ".manifest.json.lock").touch()
    preflight = {
        "schema_version": 1, "direction_id": run._DIRECTION_ID, "run_id": run._RUN_ID,
        "workers": 1, "threads_per_worker": 1, "memory_safe": True,
    }
    execute_preflight = dict(preflight)
    (root / "preflight.json").write_text(json.dumps(preflight), encoding="utf-8")
    (root / "execute-preflight.json").write_text(json.dumps(execute_preflight), encoding="utf-8")
    command = list(run.FROZEN_CHILD_ARGV)
    command_sha = run._command_digest(command)
    preflight_sha = run._sha256(root / "preflight.json")
    runner_spec = {
        "schema_version": 1, "command": command, "command_sha256": command_sha,
        "cwd": str(cwd.resolve()), "git_branch": "codex/test",
        "output_root": str(root), "outputs": run._EXPECTED_LAUNCHER_OUTPUTS,
        "preflight_sha256": preflight_sha,
    }
    (root / "runner-spec.json").write_text(json.dumps(runner_spec), encoding="utf-8")
    manifest = {
        "schema_version": 1, "status": "RUNNING", "direction_id": run._DIRECTION_ID,
        "run_id": run._RUN_ID, "cwd": str(cwd.resolve()), "code_sha": head,
        "command": command, "command_sha256": command_sha,
        "outputs": run._EXPECTED_LAUNCHER_OUTPUTS,
        "resources": {
            "preflight_ref": "preflight.json", "preflight_sha256": preflight_sha,
            "runner_spec_sha256": run._sha256(root / "runner-spec.json"),
            "workers": 1, "threads_per_worker": 1, "memory_safe": True,
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_exact_running_launcher_scaffold_is_accepted_without_mutation(tmp_path: Path, monkeypatch) -> None:
    head = "a" * 40
    root = _write_launcher_scaffold(tmp_path, head)
    before = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run, "_current_git_head", lambda _cwd: head)
    assert run._prepare_output_root(root) == root
    assert {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()} == before


def test_unexpected_missing_and_malformed_scaffold_are_refused(tmp_path: Path) -> None:
    root = _write_launcher_scaffold(tmp_path)
    unexpected = root / "unexpected.txt"
    unexpected.write_text("not launcher evidence", encoding="utf-8")
    with pytest.raises(run.OutputStateError):
        run._validate_launcher_scaffold(root, cwd=tmp_path.resolve(), expected_argv=run.FROZEN_CHILD_ARGV, head="a" * 40)
    unexpected.unlink()
    stderr = root / "stderr.log"
    stderr.unlink()
    with pytest.raises(run.OutputStateError):
        run._validate_launcher_scaffold(root, cwd=tmp_path.resolve(), expected_argv=run.FROZEN_CHILD_ARGV, head="a" * 40)
    stderr.touch()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "PREPARED"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(run.OutputStateError):
        run._validate_launcher_scaffold(root, cwd=tmp_path.resolve(), expected_argv=run.FROZEN_CHILD_ARGV, head="a" * 40)


def test_nonempty_scaffold_directory_is_refused(tmp_path: Path) -> None:
    root = _write_launcher_scaffold(tmp_path)
    (root / "metrics" / "partial.json").write_text("{}", encoding="utf-8")
    with pytest.raises(run.OutputStateError):
        run._validate_launcher_scaffold(root, cwd=tmp_path.resolve(), expected_argv=run.FROZEN_CHILD_ARGV, head="a" * 40)


def test_existing_b3_result_in_scaffold_is_one_shot_refusal(tmp_path: Path) -> None:
    root = _write_launcher_scaffold(tmp_path)
    result = root / config.RESULT_FILENAME
    result.write_text("{}", encoding="utf-8")
    before = result.read_bytes()
    with pytest.raises(run.OutputStateError):
        run._validate_launcher_scaffold(root, cwd=tmp_path.resolve(), expected_argv=run.FROZEN_CHILD_ARGV, head="a" * 40)
    assert result.read_bytes() == before


def test_discovery_confirmation_separation_and_b3_local_production_identity() -> None:
    assert config.DISCOVERY_NAMESPACE != config.CONFIRMATION_NAMESPACE
    identity = run.source_identity()
    assert identity["b3_local_runtime_only"]
    assert identity["files"] and all("/b3/" in name for name in identity["files"])
    production = Path(run.__file__).read_text(encoding="utf-8") + Path(host.__file__).read_text(encoding="utf-8")
    assert "from .b2" not in production
    assert "from ..b2" not in production
    assert "import b2" not in production
    assert "torch" not in production.lower()


def test_matched_shell_uses_forced_keep_bin_mass_and_real_actions() -> None:
    candidate = policies.FixedPolicy("S", "stratified", (1, 3), p_low=0.2, p_high=0.6)
    shell = policies.matched_shell(candidate, 0.75, 0.25)
    assert shell.probability == pytest.approx(0.3)
    assert not shell.force_keep and shell.family == "shell"
    probabilities = shell.event_probabilities(np.asarray([4.0, 16.0, 32.0]))
    assert probabilities == pytest.approx(np.asarray([0.3, 0.3, 0.3]))
