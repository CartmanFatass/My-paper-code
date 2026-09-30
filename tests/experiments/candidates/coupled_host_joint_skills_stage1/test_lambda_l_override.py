"""b03 SET-T-b' ``--lambda-l`` override: absent = today's config, present = only ``lambda_l`` differs.

Config construction only (no fit); worlds outside the declared dev/hold-out panels.
"""
from __future__ import annotations

from dataclasses import replace
import json

import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import macro_runner as MR
from experiments.candidates.coupled_host_joint_skills_stage1 import runner
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import make_envs, make_macro_envs
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    B02_BOUNDED_HEAD_SPEC, DEFAULT_SPEC, SEEDS, MacroFitSpec, config_dict, is_declared_fit_spec,
    is_declared_macro_spec, macro_config_dict, make_config, make_macro_config,
)

WORLD = 9111
BOUNDED = dict(continuous_action_distribution="tanh_gaussian", continuous_logstd_init=-1.0,
               continuous_logstd_min=-5.0, continuous_logstd_max=0.0)


def _bytes(values):
    return json.dumps(values, sort_keys=True, default=str).encode()


def _diff(a, b):
    return {k for k in a if a[k] != b[k]} | (set(a) ^ set(b))


@pytest.mark.parametrize("arm", ["H", "SET"])
def test_step_config_lambda_l_override(arm):
    envs = make_envs(1, [WORLD])
    seed = SEEDS[arm][0]
    for base in (DEFAULT_SPEC, B02_BOUNDED_HEAD_SPEC):
        today = config_dict(make_config(arm, envs, seed, base))
        absent = config_dict(make_config(arm, envs, seed, replace(base, lambda_l=None)))
        assert _bytes(absent) == _bytes(today) and today["lambda_l"] == 0.05
        zero = config_dict(make_config(arm, envs, seed, replace(base, lambda_l=0.0)))
        assert zero["lambda_l"] == 0.0 and _diff(today, zero) == {"lambda_l"}
    # A per-step spec with the override is technical (not declared) until the DM declares one.
    assert is_declared_fit_spec(DEFAULT_SPEC) and not is_declared_fit_spec(replace(DEFAULT_SPEC, lambda_l=0.0))


@pytest.mark.parametrize("arm", ["H", "SET"])
def test_macro_config_lambda_l_override(arm):
    contract = "target"  # the b03 contract; slot/offset share make_macro_config but need a menu provider
    envs = make_macro_envs(1, [WORLD], contract)
    seed = SEEDS[arm][0]
    base = MacroFitSpec(contract=contract, **BOUNDED)
    today = macro_config_dict(make_macro_config(arm, envs, seed, base))
    absent = macro_config_dict(make_macro_config(arm, envs, seed, replace(base, lambda_l=None)))
    assert _bytes(absent) == _bytes(today) and today["lambda_l"] == 0.05
    zero_config = make_macro_config(arm, envs, seed, replace(base, lambda_l=0.0))
    zero = macro_config_dict(zero_config)
    assert zero["lambda_l"] == 0.0 and _diff(today, zero) == {"lambda_l"}
    # The agent reads config.lambda_l directly on this route (no annealing, no entropy targets).
    assert not zero_config.use_entropy_annealing and not getattr(zero_config, "use_entropy_targets", False)


def test_override_refused_when_the_agent_would_overwrite_it():
    from experiments.candidates.coupled_host_joint_skills_stage1.configuration import apply_lambda_l

    class Cfg:
        lambda_l = 0.05
        use_entropy_annealing = True

    with pytest.raises(ValueError, match="annealing"):
        apply_lambda_l(Cfg(), replace(DEFAULT_SPEC, lambda_l=0.0))
    for bad in (-0.1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite"):
            apply_lambda_l(type("C", (), {})(), replace(DEFAULT_SPEC, lambda_l=bad))


def test_b03_macro_spec_is_declared_and_may_touch_the_panels():
    spec = MacroFitSpec(contract="target", lambda_l=0.0, **BOUNDED)
    assert is_declared_macro_spec(spec)
    MR.check_macro_spec_worlds(spec)
    assert not is_declared_macro_spec(replace(spec, area_size=6000))


def test_cli_lambda_l_flows_into_step_and_macro_specs(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "abc"})
    monkeypatch.setattr(MR, "run_macro_fit", lambda out, arm, seed, sha, admission, spec, menu_dir, probe=False:
                        seen.update(spec=spec) or 0)
    monkeypatch.setattr(runner, "run_fit", lambda out, arm, seed, sha, admission, spec, probe=False:
                        seen.update(spec=spec) or 0)
    base = ["--arm", "SET", "--seed", "932201", "--launch-sha", "abc", "--out", str(tmp_path / "x"),
            "--area-size", "5000"]
    head = ["--continuous-action-distribution", "tanh_gaussian", "--continuous-logstd-init", "-1.0",
            "--continuous-logstd-min", "-5.0", "--continuous-logstd-max", "0.0"]
    assert runner.main(base + ["--contract", "target", *head, "--lambda-l", "0"]) == 0
    assert seen["spec"] == MacroFitSpec(contract="target", lambda_l=0.0, **BOUNDED)
    assert runner.main(base + ["--contract", "target", *head]) == 0
    assert seen["spec"] == MacroFitSpec(contract="target", **BOUNDED) and seen["spec"].lambda_l is None
    assert runner.main(base + ["--lambda-l", "0"]) == 0
    assert seen["spec"] == replace(DEFAULT_SPEC, lambda_l=0.0)
    assert runner.main(base) == 0
    assert seen["spec"] == DEFAULT_SPEC
    with pytest.raises(SystemExit):
        runner.main(["--floor", "random-target", "--worlds", "9111", "--launch-sha", "abc",
                     "--out", str(tmp_path / "floor"), "--area-size", "5000", "--lambda-l", "0"])
