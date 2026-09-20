"""The flat-input-scale entry: plan guard, the declared difference from the completed CF_E0005
construction, binding, the recorded affine and pairing with the completed CF_E0005 and D1280 fits.

Fake learners and fake hosts only (the real stack is in `test_flat_input_scale_real_tiny.py`,
because the fake-only helper forbids real construction). The reference fits are produced by the
flat-entropy and matched-information entries themselves, so `reduce` reads three objects in one
process. One check reads the actually recorded CF_E0005 configuration from
`runs/flexible_skill_duration/b03_e0005_772803_a01/summary.json`.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_scale_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_entropy_b03 as entropy  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_flat_update_b04 as update  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(scale.BLOCKS)
ARM = scale.INPUT_SCALE_ARMS[0]
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}
RECORDED_CF_E0005 = (ROOT / "runs/flexible_skill_duration/b03_e0005_772803_a01/summary.json")
# Exact dyadic offsets from the block base, per arm and block; every panel of a fit carries them.
OFFSET = {"CF_E0005": [0., 0., 0.], "CF_S": [.0625, -.03125, .125], "D1280": [.25, .1875, .125]}
J_INIT = {"unscaled": [.2, .2, .2], "scaled": [.25, .1875, .2]}


class HostEnv(helpers.Env):
    """The fake host carries Scenario 1's bounds, so its state layout closes: 6 x 3 + 50 x 2 + 1."""

    state_dim = 119
    area_size, height_range, n_uavs, n_users = 1000., (50., 150.), 6, 50


class PanelAgent(helpers.Agent):
    """The fake learner moves the coordinator optimizer only where the arm has skills."""

    def update(self, **kwargs):
        if self.config.n_z == 1:
            saved = {name: getattr(self, name + "_optimizer").step for name in b01.FLAT_ONLY_ZERO}
            for name in saved:
                getattr(self, name + "_optimizer").step = lambda: None
            try:
                return super().update(**kwargs)
            finally:
                for name, step in saved.items():
                    getattr(self, name + "_optimizer").step = step
        losses = super().update(**kwargs)
        self.coordinator_optimizer.step()
        return losses


@pytest.fixture
def fakes(monkeypatch, fake_only):
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, entropy, update, scale):
        monkeypatch.setattr(module, "shared", r)
        monkeypatch.setattr(module, "_orig_base_summary", r.base_summary)

    def make_envs(count, seed, n_uavs, n_users, horizon):
        return [HostEnv(lane, seed + lane) for lane in range(count)]

    monkeypatch.setattr(r.e0, "_make_envs", make_envs)


def world_scores(arm, block_index):
    lanes = np.arange(r.EVAL_LANES, dtype=np.float64)
    return .25 + .015625 * block_index + .00390625 * (lanes % 4) + OFFSET[arm][block_index]


_TEMPLATES = {}


def template(tmp_path, name):
    if name not in _TEMPLATES:
        out = tmp_path / f"template_{name}"
        if name in matched.ARMS:
            assert matched.run_fit(name, SEEDS[0], 1, None, out, admission=ADMISSION) == 0
        elif name in entropy.ENTROPY_ARMS:
            assert entropy.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        else:
            assert scale.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        _TEMPLATES[name] = json.loads((out / "summary.json").read_text())
    return copy.deepcopy(_TEMPLATES[name])


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = scale.BLOCKS[seed]
    summary = copy.deepcopy(summary)
    summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                   training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                   evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
    summary["learner_config"]["seed"] = seed
    summary["evaluation_config"]["seed"] = evaluation_seed
    for panel in summary["panels"]:
        values = world_scores(arm, index)
        panel["lane_seeds"] = summary["evaluation_lane_seeds"]
        panel["native_scores_J"] = [float(v) for v in values]
        panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
    summary["evaluation"] = summary["panels"][-1]
    return summary


def probe_summary(index, fits=None):
    """A complete probe of block `index`; with `fits` = (new, flat) it is the probe of those fits."""
    seed = SEEDS[index]
    new_fit, flat_fit = fits if fits is not None else ({}, {})
    config = {"scaled": new_fit.get("learner_config", {"k": 10}),
              "unscaled": flat_fit.get("learner_config", {"k": 10})}
    return {"object_id": scale.OBJECT_ID, "command": "probe", "status": "complete",
            "block_seed": seed, "evaluation_seed": scale.BLOCKS[seed], "optimizer_steps": 0,
            "launch_sha": new_fit.get("launch_sha", "sha"), "requested_launch_sha": new_fit.get("launch_sha", "sha"),
            scale.AFFINE_FIELD: new_fit.get(scale.AFFINE_FIELD),
            "constructions": {label: {"construction": label, "J_init_mean": J_INIT[label][index],
                                      "evaluation_lanes": scale.shared.EVAL_LANES,
                                      "evaluation_episodes": scale.shared.EVAL_LANES,
                                      "horizon": scale.shared.HORIZON, "learner_config": config[label]}
                              for label in ("unscaled", "scaled")}}


def supplied(tmp_path):
    new = [placed(template(tmp_path, ARM), ARM, i) for i in range(3)]
    references = [placed(template(tmp_path, arm), arm, i)
                  for arm in ("CF_E0005", "D1280") for i in range(3)]
    return new, references


def test_plan_guard_admits_exactly_the_three_planned_fits():
    for seed in SEEDS:
        scale.plan_guard(ARM, seed)
    for arm, seed in ((ARM, 773103), (ARM, 772603), ("CF", SEEDS[0]), ("CF_E0005", SEEDS[0]),
                      ("CF_M1", SEEDS[0])):
        with pytest.raises(SystemExit):
            scale.plan_guard(arm, seed)


def test_the_configuration_is_the_recorded_cf_e0005_one_with_the_affine_as_its_only_difference():
    """Against the actually recorded learner configuration of b03_e0005_772803_a01."""
    recorded = json.loads(RECORDED_CF_E0005.read_text(encoding="utf-8"))["learner_config"]
    envs = [SimpleNamespace(state_dim=119, obs_dim=104, area_size=1000, height_range=(50, 150),
                            n_uavs=6, n_users=50) for _ in range(16)]
    snapshot = production_shared.config_snapshot
    scale.bind()
    plain = b01.make_config("CF", SEEDS[0] and envs, SEEDS[0])
    assert snapshot(plain) == recorded
    assert not hasattr(plain, scale.AFFINE_FIELD)
    assert not hasattr(plain, "sequence_batch_size")  # the learner's default minibatch
    assert getattr(plain, matched.CF_FLAG) is True
    assert plain.lambda_l == .0005
    assert plain.lr_discoverer_actor == plain.lr_discoverer_critic == pytest.approx(5e-5)

    scale.CURRENT.update(input_scale_arm=ARM)
    scaled = b01.make_config("CF", envs, SEEDS[0])
    scale.CURRENT.update(input_scale_arm=None)
    # The affine is not a configuration-snapshot field, so the recorded configuration is identical
    # and the declared difference lives on the configuration object and in the fit's own summary.
    assert snapshot(scaled) == recorded
    offset, scale_values = getattr(scaled, scale.AFFINE_FIELD)
    assert len(offset) == len(scale_values) == 119
    assert offset[:3] == [0., 0., 50.] and scale_values[:3] == [1000., 1000., 100.]
    assert offset[18:20] == [0., 0.] and scale_values[18:20] == [1000., 1000.]
    assert offset[-1] == 0. and scale_values[-1] == 1.
    assert min(scale_values) > 0.


def test_a_lane_without_bounds_or_a_layout_that_does_not_close_fails_loudly():
    scale.bind()
    scale.CURRENT.update(input_scale_arm=ARM)
    try:
        bare = [SimpleNamespace(state_dim=119, obs_dim=104) for _ in range(2)]
        with pytest.raises(ValueError, match="does not expose area_size"):
            b01.make_config("CF", bare, SEEDS[0])
        mixed = [SimpleNamespace(state_dim=119, obs_dim=104, area_size=size, height_range=(50, 150),
                                 n_uavs=6, n_users=50) for size in (1000, 900)]
        with pytest.raises(ValueError, match="do not share their environment bounds"):
            b01.make_config("CF", mixed, SEEDS[0])
        wrong = [SimpleNamespace(state_dim=119, obs_dim=104, area_size=1000, height_range=(50, 150),
                                 n_uavs=6, n_users=49) for _ in range(2)]
        with pytest.raises(ValueError, match="not the configured state_dim"):
            b01.make_config("CF", wrong, SEEDS[0])
        flat_band = [SimpleNamespace(state_dim=119, obs_dim=104, area_size=1000,
                                     height_range=(50, 50), n_uavs=6, n_users=50) for _ in range(2)]
        with pytest.raises(ValueError, match="increasing finite interval"):
            b01.make_config("CF", flat_band, SEEDS[0])
    finally:
        scale.CURRENT.update(input_scale_arm=None)


def test_the_learner_and_evaluator_phases_must_agree_on_the_affine():
    """`make_config` runs once per phase; a disagreement would silence itself otherwise."""
    summary = {}
    scale.CURRENT.update(summary=summary)
    try:
        affine = {"offset": [0.], "scale": [1.]}
        bounds = {"area_size": 1000., "height_range": [50., 150.], "n_uavs": 6, "n_users": 50}
        scale._record_affine(affine, bounds)
        scale._record_affine(dict(affine), dict(bounds))  # the second phase agrees
        assert summary[scale.AFFINE_FIELD] == affine and summary[scale.BOUNDS_FIELD] == bounds
        with pytest.raises(ValueError, match="different state affines"):
            scale._record_affine({"offset": [0.], "scale": [2.]}, bounds)
        with pytest.raises(ValueError, match="different state affines"):
            scale._record_affine(affine, dict(bounds, area_size=900.))
    finally:
        scale.CURRENT.update(summary=None)
    scale._record_affine({"offset": [0.], "scale": [1.]}, {})  # no running summary: a reader


def test_fit_runs_the_frozen_flat_loop_under_this_identity(tmp_path, fakes):
    summary = template(tmp_path, ARM)
    assert summary["status"] == "complete" and summary["object_id"] == scale.OBJECT_ID
    assert summary["flat_input_scale_object"] == scale.OBJECT_ID and summary["admission"] == ADMISSION
    assert summary["factorial_arm"] == "CF" and summary["input_scale_arm"] == ARM
    assert summary["lr_multiplier"] == .5 and summary["entropy_coefficient"] == .0005
    assert summary["learner_config"]["lambda_l"] == .0005
    assert summary["learner_config"][matched.CF_FLAG] is True
    affine, bounds = summary[scale.AFFINE_FIELD], summary[scale.BOUNDS_FIELD]
    assert len(affine["offset"]) == len(affine["scale"]) == 119
    assert bounds == {"area_size": 1000., "height_range": [50., 150.], "n_uavs": 6, "n_users": 50}
    assert scale.CURRENT == {"input_scale_arm": None, "admission": None, "summary": None}
    assert production_shared.base_summary is not scale.base_summary  # the wrapper came off again
    assert set(scale.fit_endpoint(summary)) == set(range(5, 50, 5))
    with pytest.raises(ValueError):  # the flat-entropy reader does not take this object's fits
        entropy.fit_endpoint(summary)
    with pytest.raises(ValueError):  # nor this one a completed reference fit
        scale.fit_endpoint(template(tmp_path, "CF_E0005"))


def _foreign_but_self_consistent_host(summary):
    """Bounds of another layout that still closes at 119, with the affine they do imply."""
    summary[scale.BOUNDS_FIELD].update(n_uavs=4, n_users=53)
    offset, values = scale.state_affine_from_bounds(4, 53, 1000., (50., 150.), 119)
    summary[scale.AFFINE_FIELD] = {"offset": offset, "scale": values}


def test_fit_endpoint_refuses_a_missing_or_wrong_affine(tmp_path, fakes):
    summary = template(tmp_path, ARM)
    for mutate, message in (
            (lambda s: s.update(**{scale.AFFINE_FIELD: None}), "does not record its state affine"),
            (lambda s: s.update(**{scale.BOUNDS_FIELD: None}), "does not record its state affine"),
            (lambda s: s[scale.AFFINE_FIELD]["scale"].__setitem__(0, 1.),
             "not the one the recorded bounds imply"),
            (lambda s: s[scale.BOUNDS_FIELD].update(area_size=900.),
             "not the one the recorded bounds imply"),
            (_foreign_but_self_consistent_host, "not this fit's own host"),
            (lambda s: s.update(lr_multiplier=1.), "learning-rate multiplier"),
            (lambda s: s["learner_config"].update(lambda_l=.05), "not the declared construction"),
            (lambda s: s["evaluation_config"].update(**{matched.CF_FLAG: False}),
             "not the declared construction"),
            (lambda s: s.update(input_scale_arm="CF_X"), "three planned fits")):
        broken = copy.deepcopy(summary)
        mutate(broken)
        with pytest.raises(ValueError, match=message):
            scale.fit_endpoint(broken)


def test_reduce_pairs_new_fits_with_the_completed_flat_and_d1280_fits(tmp_path, fakes):
    new, references = supplied(tmp_path)
    probes = [probe_summary(i, (new[i], references[i])) for i in range(3)]
    paths = {"new": [], "ref": [], "probe": []}
    for kind, items in (("new", new), ("ref", references), ("probe", probes)):
        for index, summary in enumerate(items):
            path = tmp_path / f"{kind}_{index}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            paths[kind].append(str(path))
    out = tmp_path / "reduce"
    assert scale.main(["reduce", "--summaries", *paths["new"], "--references", *paths["ref"],
                       "--probes", *paths["probe"], "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and not result["invalid_inputs"]
    assert not result["invalid_probes"]
    for index, block in enumerate(result["blocks"]):
        assert set(block["arms"]) == {ARM, "CF_E0005", "D1280"}
        assert block["arms"]["CF_E0005"]["object_id"] == entropy.OBJECT_ID
        assert block["arms"]["D1280"]["object_id"] == matched.OBJECT_ID
        assert block["J_init"] == {"unscaled": J_INIT["unscaled"][index],
                                   "scaled": J_INIT["scaled"][index]}
        parts = block["arms"][ARM]["actor_displacement_parts"]
        assert set(parts) == {"1", "45"}
    view = result["arms"][ARM]
    for name in ("J45", "late"):  # every panel carries the same offset, so both readings agree
        assert [p[f"new_minus_flat_{name}"] for p in view["pairs"]] == OFFSET[ARM]
        assert [p[f"D1280_minus_new_{name}"] for p in view["pairs"]] == [
            d - n for d, n in zip(OFFSET["D1280"], OFFSET[ARM])]
    assert [p["late_minus_early_window"] for p in view["pairs"]] == [0., 0., 0.]
    assert view["new_minus_flat_late"]["mean"] == pytest.approx(float(np.mean(OFFSET[ARM])))
    assert view["blocks_above_flat_in_late_window"] == 2
    assert view["blocks_above_flat_at_J45"] == 2
    rises = [p["new_minus_flat_rise_from_J_init"] for p in view["pairs"]]
    expected = [OFFSET[ARM][i] - (J_INIT["scaled"][i] - J_INIT["unscaled"][i]) for i in range(3)]
    assert rises == pytest.approx(expected)
    assert view["blocks_with_larger_rise_from_J_init"] == int(sum(v > 0 for v in expected))
    assert "exploration" in result["interpretation_limit"]
    assert "no MEI verdict" in result["interpretation_limit"]


def test_reduce_without_probes_reports_no_initial_level(tmp_path, fakes):
    new, references = supplied(tmp_path)
    result = scale.reduce_fits(new, references)
    assert result["status"] == "complete"
    assert all(block["J_init"] is None for block in result["blocks"])
    assert all("J_late_minus_J_init" not in pair for pair in result["arms"][ARM]["pairs"])
    assert result["arms"][ARM]["new_minus_flat_rise_from_J_init"] is None


def test_missing_invalid_and_duplicate_inputs(tmp_path, fakes):
    new, references = supplied(tmp_path)
    result = scale.reduce_fits(new[1:], references)  # the first block's fit is missing
    assert result["status"] == "incomplete"
    assert result["arms"][ARM]["pairs"][0]["missing_operands"] == [ARM]
    assert result["blocks"][0]["missing_or_invalid_arms"] == {ARM: "not supplied"}

    broken = copy.deepcopy(new)
    broken[1]["learner_config"]["lambda_e"] = .5  # an unplanned difference from the CF_E0005 fit
    result = scale.reduce_fits(broken, references)
    assert result["arms"][ARM]["pairs"][1]["failure"] == "unplanned difference from the CF_E0005 reference"

    other_flat = copy.deepcopy(references)
    other_flat[0]["entropy_arm"] = "CF_E005"  # not the declared flat reference
    result = scale.reduce_fits(new, other_flat)
    assert result["arms"][ARM]["pairs"][0]["missing_operands"] == ["CF_E0005"]
    assert result["invalid_inputs"]

    with pytest.raises(ValueError, match="duplicate"):
        scale.reduce_fits(new + [copy.deepcopy(new[0])], references)
    with pytest.raises(ValueError, match="duplicate probe"):
        scale.reduce_fits(new, references, [probe_summary(0), probe_summary(0)])

    broken_probe = probe_summary(1)
    broken_probe["optimizer_steps"] = 3
    result = scale.reduce_fits(new, references, [broken_probe])
    assert result["invalid_probes"] == {str(SEEDS[1]): "a probe that took an optimizer step is not a probe"}
    assert result["arms"][ARM]["pairs"][1]["J_late_minus_J_init"] is None

    # A probe of another construction, panel size or source is never differenced against a fit.
    for mutate, message in (
            (lambda p: p["constructions"]["scaled"].update(evaluation_lanes=2),
             "not the frozen evaluation panel"),
            (lambda p: p["constructions"]["unscaled"].update(horizon=20), "not the frozen evaluation panel"),
            (lambda p: p.update(evaluation_seed=1), "evaluation seed"),
            (lambda p: p.update(requested_launch_sha=None), "source it was asked to run at")):
        probe = probe_summary(0, (new[0], references[0]))
        mutate(probe)
        result = scale.reduce_fits(new, references, [probe])
        assert message in result["invalid_probes"][str(SEEDS[0])]
        assert result["arms"][ARM]["pairs"][0]["J_late_minus_J_init"] is None
    for mutate, message in (
            (lambda p: [c["learner_config"].update(lambda_l=.05) for c in p["constructions"].values()],
             "not the new fit's recorded configuration"),
            (lambda p: p.update(launch_sha="other", requested_launch_sha="other"), "different sources"),
            (lambda p: p.update(**{scale.AFFINE_FIELD: None}), "state affine")):
        probe = copy.deepcopy(probe_summary(0, (new[0], references[0])))
        mutate(probe)
        result = scale.reduce_fits(new, references, [probe])
        pair = result["arms"][ARM]["pairs"][0]
        assert pair["J_late_minus_J_init"] is None and message in pair["probe_failure"]


def test_displacement_parts_split_the_log_std_component(tmp_path, fakes):
    summary = placed(template(tmp_path, ARM), ARM, 0)
    rows = summary["training_rows"]
    summary["initial_parameter_norms"] = {"discoverer_actor": 46.}
    rows[0]["losses"] = {"action_entropy": 3 * scale.GAUSSIAN_ENTROPY_PER_DIMENSION}
    rows[0]["relative_initialization_displacement"] = {"discoverer_actor": .04}
    parts = scale.displacement_parts(summary, 1)
    assert parts["logstd_part"] == pytest.approx(0.)  # entropy at its initialisation value
    assert parts["network_part"] == pytest.approx(.04)
    rows[0]["losses"] = {"action_entropy": 3 * (scale.GAUSSIAN_ENTROPY_PER_DIMENSION + .46)}
    parts = scale.displacement_parts(summary, 1)
    assert parts["logstd_part"] == pytest.approx(3 ** .5 * .46 / 46.)
    assert parts["network_part"] == pytest.approx((.04 ** 2 - parts["logstd_part"] ** 2) ** .5)
    rows[0]["losses"] = {"action_entropy": None}
    assert scale.displacement_parts(summary, 1)["network_part"] is None
    assert "incomplete" in scale.displacement_parts(summary, 1)["failure"]
