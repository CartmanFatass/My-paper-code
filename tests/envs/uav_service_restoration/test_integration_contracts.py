"""Adapter contract, legacy non-regression, import side effects and integration timing.

These are the checks that decide whether the new environment is safe to put in front of
the shared training route, and whether adding it changed anything that already worked.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap

import numpy as np
import pytest

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.uav_service_restoration import UAVServiceRestorationEnv, config_from_dict
from envs.uav_service_restoration.adapter import (
    ServiceRestorationArrayAdapter,
    make_array_env,
    make_parallel_env,
)


# --------------------------------------------------------------------------------------
# Adapter contract
# --------------------------------------------------------------------------------------


def test_shared_adapter_accepts_the_environment_unmodified(short_config):
    """The unmodified shared adapter class wraps this environment as it stands."""

    adapter = make_array_env(short_config, seed=5, wrap_metrics=False)
    assert type(adapter) is ParallelToArrayAdapter
    observations, info = adapter.reset(seed=5)
    assert observations.shape == (short_config.n_uavs, adapter.obs_dim)
    assert "state" in info


def test_adapter_dimensions_come_from_the_native_providers(short_config):
    adapter = make_array_env(short_config, seed=5, wrap_metrics=False)
    native = adapter.env
    assert adapter.obs_dim == native.get_obs_dim()
    assert adapter.state_dim == native.get_state_dim()
    assert adapter.action_dim == 3
    assert adapter.n_uavs == short_config.n_uavs
    assert adapter.observation_space.shape == (short_config.n_uavs, native.get_obs_dim())
    assert adapter.action_space.shape == (short_config.n_uavs, 3)
    assert adapter.action_space.dtype == np.float32


def test_adapter_reset_and_step_shapes(short_config):
    adapter = make_array_env(short_config, seed=5)
    observations, info = adapter.reset(seed=5)
    assert observations.shape == (short_config.n_uavs, adapter.obs_dim)
    assert observations.dtype == np.float32
    assert info["state"].shape == (adapter.state_dim,)
    assert info["state"].dtype == np.float32

    actions = np.zeros((short_config.n_uavs, 3), dtype=np.float32)
    observations, reward, terminated, truncated, info = adapter.step(actions)
    assert observations.shape == (short_config.n_uavs, adapter.obs_dim)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool) and isinstance(truncated, bool)
    assert info["next_state"].shape == (adapter.state_dim,)


def test_adapter_scalar_reward_equals_the_team_reward_without_extra_division(short_config):
    """The adapter averages agent rewards; the team reward must survive that unchanged."""

    adapter = make_array_env(short_config, seed=5)
    adapter.reset(seed=5)
    actions = np.zeros((short_config.n_uavs, 3), dtype=np.float32)
    _, reward, _, _, info = adapter.step(actions)
    per_agent = list(info["rewards_dict"].values())
    assert len(per_agent) == short_config.n_uavs
    assert all(value == per_agent[0] for value in per_agent)
    assert reward == pytest.approx(per_agent[0], abs=0.0)
    assert reward == pytest.approx(float(np.mean(per_agent)), abs=0.0)
    assert info["reward_components"]["shared_global_reward"] == pytest.approx(reward)


def test_adapter_truncation_flags_reach_the_array_interface(short_config):
    adapter = make_array_env(short_config, seed=5)
    adapter.reset(seed=5)
    actions = np.zeros((short_config.n_uavs, 3), dtype=np.float32)
    flags = []
    for _ in range(short_config.n_decision_steps):
        _, _, terminated, truncated, _ = adapter.step(actions)
        flags.append((terminated, truncated))
    assert flags[-1] == (False, True)
    assert all(flag == (False, False) for flag in flags[:-1])


def test_adapter_state_info_carries_no_privileged_field(short_config):
    adapter = make_array_env(short_config, seed=5)
    _, info = adapter.reset(seed=5)
    forbidden = {
        "episode_id",
        "dataset_hash",
        "exogenous_events",
        "alert_time_s",
        "split",
        "trace_cursor",
    }
    assert not (set(info["state_info"]) & forbidden)
    actions = np.zeros((short_config.n_uavs, 3), dtype=np.float32)
    _, _, _, _, info = adapter.step(actions)
    assert not (set(info["state_info"]) & forbidden)
    assert "reward_info" in info


def test_metric_wrapper_adds_only_read_only_passthroughs(short_config):
    adapter = make_array_env(short_config, seed=5)
    assert isinstance(adapter, ServiceRestorationArrayAdapter)
    adapter.reset(seed=5)
    adapter.step(np.zeros((short_config.n_uavs, 3), dtype=np.float32))
    assert adapter.episode_summary()["total_time_s"] > 0.0
    assert adapter.get_privileged_diagnostics()["exogenous_events"]
    assert adapter.schema()["environment_id"] == "uav_service_restoration_v0"
    # reset/step are the inherited implementations, not overrides.
    assert (
        ServiceRestorationArrayAdapter.reset is ParallelToArrayAdapter.reset
    )
    assert ServiceRestorationArrayAdapter.step is ParallelToArrayAdapter.step


def test_make_parallel_env_accepts_a_path(preset_dir):
    env = make_parallel_env(str(preset_dir / "smoke_fixture.json"))
    assert isinstance(env, UAVServiceRestorationEnv)
    env.reset(seed=1)
    assert env.agents


def test_real_data_factory_fails_without_a_dataset(preset_dir):
    from envs.uav_service_restoration.demand import DemandDataError

    outage = preset_dir / "milan_site_outage.json"
    with pytest.raises(DemandDataError):
        make_parallel_env(str(outage))


# --------------------------------------------------------------------------------------
# The legacy default route is untouched
# --------------------------------------------------------------------------------------


def test_legacy_scenario_aliases_are_unchanged():
    from ha_ctse_process.env_factory import SCENARIO_ALIASES, normalize_scenario

    assert "uav_service_restoration" not in SCENARIO_ALIASES
    assert not any("service_restoration" in key for key in SCENARIO_ALIASES)
    assert normalize_scenario("base") == "base"
    with pytest.raises(ValueError):
        normalize_scenario("uav_service_restoration_v0")


@pytest.mark.parametrize("scenario", ["base", "belief_map"])
def test_legacy_seeded_traces_are_identical(scenario, legacy_fingerprint_dir):
    """Short fixed-seed legacy traces: obs, state, reward, termination and RNG state."""

    import importlib.util

    baseline_path = legacy_fingerprint_dir / f"{scenario}_seed12345.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    spec = importlib.util.spec_from_file_location(
        "legacy_baseline_fingerprint",
        legacy_fingerprint_dir.parents[2].parent
        / "scripts"
        / "uav_service_restoration"
        / "legacy_baseline_fingerprint.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    current = module.capture(scenario, int(baseline["seed"]), int(baseline["steps"]))
    differences = module._compare(baseline, current)  # noqa: SLF001
    assert differences == [], differences


# --------------------------------------------------------------------------------------
# Import side effects
# --------------------------------------------------------------------------------------


def test_importing_the_package_has_no_side_effects():
    """A subprocess so the check is not confounded by anything already imported."""

    script = textwrap.dedent(
        """
        import json, sys
        import numpy as np

        np.random.seed(4242)
        before_global = np.random.get_state()
        modules_before = set(sys.modules)

        import envs.uav_service_restoration as package

        after_global = np.random.get_state()
        modules_after = set(sys.modules)
        newly = {name for name in modules_after - modules_before}

        result = {
            "global_rng_unchanged": bool(
                before_global[0] == after_global[0]
                and np.array_equal(before_global[1], after_global[1])
                and before_global[2:] == after_global[2:]
            ),
            "torch_imported": any(name == "torch" or name.startswith("torch.") for name in newly),
            "matplotlib_imported": any(name.split(".")[0] == "matplotlib" for name in newly),
            "preprocess_imported": "envs.uav_service_restoration.preprocess_milan" in modules_after,
            "adapter_imported": "envs.uav_service_restoration.adapter" in modules_after,
            "legacy_factory_imported": "ha_ctse_process.env_factory" in modules_after,
            "legacy_env_imported": "envs.pettingzoo.env_adapter" in modules_after,
            "has_env_class": hasattr(package, "UAVServiceRestorationEnv"),
        }
        print(json.dumps(result))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[3]),
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["has_env_class"]
    assert result["global_rng_unchanged"]
    assert not result["torch_imported"]
    assert not result["matplotlib_imported"]
    # Heavy or legacy-touching modules are imported lazily, not by the package import.
    assert not result["preprocess_imported"]
    assert not result["adapter_imported"]
    assert not result["legacy_factory_imported"]
    assert not result["legacy_env_imported"]


def test_no_native_compilation_or_download_path_is_referenced():
    import inspect

    import envs.uav_service_restoration as package

    banned = ("cpp_extension", "urlopen", "requests.get", "subprocess", "torch")
    for name in package.__all__:
        obj = getattr(package, name)
        module = inspect.getmodule(obj)
        if module is None or not (module.__name__ or "").startswith(
            "envs.uav_service_restoration"
        ):
            continue
        source = inspect.getsource(module)
        for token in banned:
            assert token not in source, f"{module.__name__} references {token}"


# --------------------------------------------------------------------------------------
# Integration timing semantics (what a future trainer must respect)
# --------------------------------------------------------------------------------------


def test_physical_gamma_conversion_is_available_to_callers(short_config):
    """The environment reports its timestep in seconds so gamma can be set in time.

    The environment does not set ``gamma``; it makes the conversion possible by exposing
    ``decision_dt_s`` in its schema.
    """

    schema = UAVServiceRestorationEnv(short_config).schema()
    assert short_config.episode.decision_dt_s == 10.0
    gamma_reference, dt_reference = 0.99, 1.0
    gamma = gamma_reference ** (short_config.episode.decision_dt_s / dt_reference)
    assert gamma == pytest.approx(0.99**10)
    assert schema["termination"]["semantics"] == "continuing"


def test_raw_cumulative_quantities_survive_a_change_of_decision_interval(config_doc):
    """Same physical trajectory, different decision interval, same raw totals.

    A static controller's trajectory is independent of the decision interval, so the
    integrated offered and delivered volumes must agree to within substep quadrature
    error.
    """

    totals = {}
    for decision_dt in (10.0, 20.0):
        config_doc["episode"]["decision_dt_s"] = decision_dt
        config_doc["episode"]["duration_s"] = 300.0
        config_doc["episode"]["physics_dt_s"] = 1.0
        config = config_from_dict(config_doc)
        env = UAVServiceRestorationEnv(config)
        env.reset(seed=21)
        while env.agents:
            env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})
        summary = env.episode_summary()
        totals[decision_dt] = (
            summary["offered_mbit_total"],
            summary["delivered_mbit_total"],
            summary["unmet_mbit_total"],
        )
    for index in range(3):
        assert totals[10.0][index] == pytest.approx(totals[20.0][index], rel=1e-9)


def test_substep_refinement_converges_for_a_moving_controller(config_doc):
    """Integration error shrinks as the substep shrinks; the rule is the midpoint rule."""

    results = {}
    for physics_dt in (5.0, 2.5, 1.25, 0.625):
        config_doc["episode"]["decision_dt_s"] = 10.0
        config_doc["episode"]["duration_s"] = 200.0
        config_doc["episode"]["physics_dt_s"] = physics_dt
        config = config_from_dict(config_doc)
        env = UAVServiceRestorationEnv(config)
        env.reset(seed=22)
        while env.agents:
            env.step(
                {
                    agent: np.array([1.0, 0.0, 0.0], dtype=np.float32)
                    for agent in env.agents
                }
            )
        results[physics_dt] = env.episode_summary()["delivered_mbit_total"]

    reference = results[0.625]
    errors = [abs(results[dt] - reference) for dt in (5.0, 2.5, 1.25)]
    assert errors[0] > 0.0
    # Monotone refinement: each halving of the substep gets closer to the fine reference.
    assert errors[1] < errors[0]
    assert errors[2] < errors[1]


def _single_interval_probe(config_doc, start_x, *, quadrature):
    """Run one 100 s decision interval at full eastward thrust and report the outcome.

    Returns the integrated delivered volume, the start and end positions, and a callable
    that reports the instantaneous delivered rate at an arbitrary position under the same
    demand and site state.  That callable is what lets the test say what a *teleporting*
    implementation would have credited.
    """

    from envs.uav_service_restoration import network as net
    from envs.uav_service_restoration import scheduler as sched

    document = json.loads(json.dumps(config_doc))
    document["episode"]["duration_s"] = 100.0
    document["episode"]["decision_dt_s"] = 100.0
    document["episode"]["physics_dt_s"] = 100.0
    document["episode"]["quadrature"] = quadrature
    document["events"]["events"][0]["start_s_range"] = [0.0, 0.0]
    document["deployment"]["positions_m"] = [
        [start_x, 1500.0, 120.0],
        [start_x, 1200.0, 120.0],
        [start_x, 1800.0, 120.0],
    ]
    config = config_from_dict(document)
    env = UAVServiceRestorationEnv(config)
    env.reset(seed=31)
    start_positions = env.uav_positions_m.copy()
    env.step({agent: np.array([1.0, 0.0, 0.0], dtype=np.float32) for agent in env.agents})
    end_positions = env.uav_positions_m.copy()
    delivered = env.episode_summary()["delivered_mbit_total"]

    layout = env.demand_layout
    demand_positions = net.demand_positions_from_xy(layout.positions_m, 0.0)
    frame = env.demand_source.read_interval(
        env.episode_descriptor, env.episode_descriptor.start_utc_ms
    )
    demand = layout.aggregate_demand(frame.demand_mbps)
    site_states = env.event_schedule.site_states(50.0)

    def rate_at(positions):
        snapshot = net.build_snapshot(
            config.network, site_states, positions, demand_positions, demand
        )
        return sched.solve_or_raise(snapshot, config.scheduler).delivered_mbps_total

    return {
        "delivered_mbit": delivered,
        "start_positions": start_positions,
        "end_positions": end_positions,
        "rate_at": rate_at,
    }


def test_a_long_interval_is_not_credited_at_the_end_position(config_doc):
    """No teleportation benefit.

    The eastern site is dead from t = 0 and the eastern demand point is reachable only by
    a UAV.  Starting at x = 150 m and flying east at 20 m/s for 100 s, the UAV is out of
    access range at both the start (2250 m away) and the interval midpoint (1250 m away,
    just beyond the 1200 m limit), and in range at the end (250 m).  A teleporting
    implementation would credit the whole interval at that end position; the actual
    integration must deliver strictly less.
    """

    probe = _single_interval_probe(config_doc, 150.0, quadrature="midpoint")
    teleported = probe["rate_at"](probe["end_positions"]) * 100.0
    frozen_at_start = probe["rate_at"](probe["start_positions"]) * 100.0
    assert frozen_at_start < teleported, "the scenario must make position decisive"
    assert probe["delivered_mbit"] < teleported - 1e-6


def test_motion_inside_an_interval_is_accounted_for(config_doc):
    """The opposite error: freezing the UAV at its start position for the whole interval.

    Starting at x = 1000 m the UAV is out of range at the start (1400 m) and in range at
    the midpoint (400 m), so the midpoint quadrature must deliver strictly more than the
    left-endpoint rule, which is exactly the frozen-start value.
    """

    left = _single_interval_probe(config_doc, 1000.0, quadrature="left")
    midpoint = _single_interval_probe(config_doc, 1000.0, quadrature="midpoint")
    frozen_at_start = left["rate_at"](left["start_positions"]) * 100.0
    assert left["delivered_mbit"] == pytest.approx(frozen_at_start, rel=1e-9)
    assert midpoint["delivered_mbit"] > left["delivered_mbit"] + 1e-6
