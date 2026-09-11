"""Focused checks for the B01 deployment-mode evaluation entry.

Everything that needs the Linux native library (the complete check-profile invocation) is read
from an existing output root through ``VNFC_B01_DEPMODE_CHECK_ROOT``; the rest runs anywhere.
"""

import ast
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path

import pytest
import torch

from experiments.candidates.variable_n_fleet_churn_n7_direct_b01 import deployment_mode, learning

REPOSITORY = Path(__file__).resolve().parents[4]
SCRIPT = REPOSITORY / "scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py"
LOCAL_CHECKPOINTS = Path("C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn")


def _entry_module():
    spec = importlib.util.spec_from_file_location("vnfc_b01_deployment_mode_entry", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_inputs(batch=3, n=7):
    generator = torch.Generator().manual_seed(20260905)
    agents = torch.rand((batch, n, 38), generator=generator, dtype=torch.float64)
    zones = torch.rand((batch, 2, 15), generator=generator, dtype=torch.float64)
    globals_ = torch.rand((batch, 4), generator=generator, dtype=torch.float64)
    legal = torch.ones((batch, n, 4), dtype=torch.float64)
    legal[0, 0, 0] = 0.0
    legal[1, 3, 2] = 0.0
    fixed = torch.full((batch, 4), -1, dtype=torch.int64)
    fixed[2, 1] = 4
    opaque = torch.stack([torch.randperm(n, generator=generator) + 1 for _ in range(batch)]).to(torch.int64)
    return agents, zones, globals_, legal, fixed, opaque


def _synthetic_model(arm):
    generator = torch.Generator().manual_seed(7)
    parameters = {name: .1 * torch.randn(value.shape, generator=generator, dtype=torch.float64)
                  for name, value in deployment_mode.placeholder_parameters(arm).items()}
    model = (learning.MAPR if arm == "MAPR" else learning.Direct)(parameters)
    if arm == "DIRECT":
        model.residual_observation = None
    return model


def _fixtures(zones):
    from types import SimpleNamespace
    return tuple(SimpleNamespace(failed_zone=zone) for zone in zones)


def test_checkpoint_placeholder_round_trip_and_digest_contract(tmp_path):
    for arm, count in (("MAPR", 89090), ("DIRECT", 148739)):
        source = _synthetic_model(arm)
        path = tmp_path / f"{arm}_final.pt"
        torch.save(dict(arm=arm, checkpoint="final", round=64, model_state=source.state_dict(),
                        optimizer_state={"state": {}, "param_groups": []}, dtype="float64", device="cpu",
                        presentation="R02 canonical opaque rank"), path)
        import hashlib
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        model, meta = deployment_mode.load_checkpoint(path, arm, digest)
        assert meta["parameters"] == count and meta["round"] == 64 and meta["sha256"] == digest
        assert meta["optimizer_state_loaded"] is False
        restored = model.state_dict()
        assert all(torch.equal(restored[name], value) for name, value in source.state_dict().items())
        assert learning.parameter_state(model, {name: p.detach().clone() for name, p
                                                in source.named_parameters()})["displacement_norm"] == 0.0
        if arm == "DIRECT":
            assert model.residual_observation is None
        with pytest.raises(AssertionError, match="digest differs"):
            deployment_mode.load_checkpoint(path, arm, "0" * 64)
        with pytest.raises(AssertionError, match="round differs"):
            deployment_mode.load_checkpoint(path, arm, digest, expected_round=32)


@pytest.mark.skipif(not LOCAL_CHECKPOINTS.exists(), reason="frozen B01 checkpoints are not on this host")
def test_declared_digests_match_the_four_frozen_final_checkpoints():
    for (record, arm), digest in deployment_mode.CHECKPOINT_DIGESTS.items():
        model, meta = deployment_mode.load_checkpoint(
            deployment_mode.checkpoint_path(LOCAL_CHECKPOINTS, record, arm), arm, digest)
        assert meta["round"] == 64 and meta["checkpoint"] == "final" and meta["arm"] == arm
        assert meta["parameters"] == (89090 if arm == "MAPR" else 148739)
        assert meta["bytes"] == (2168441 if arm == "MAPR" else 3607517)


def test_greedy_and_sample_use_the_two_existing_forward_branches():
    inputs = _synthetic_inputs()
    for arm in ("MAPR", "DIRECT"):
        model = _synthetic_model(arm)
        with torch.no_grad():
            greedy = model(*inputs, None)
            again = model(*inputs, None)
            sampled = model(*inputs, torch.full((3, 4), .5, dtype=torch.float64))
        assert torch.equal(greedy["command"], again["command"])
        # greedy is the masked maximum: the first token has no prefix state to differ on
        assert torch.equal(greedy["command"][:, 0], greedy["token_probabilities"][:, 0].argmax(1))
        for output in (greedy, sampled):
            chosen = output["token_probabilities"].gather(2, output["command"][:, :, None]).squeeze(2)
            assert bool((chosen > 0).all())          # every decoded token is inside the masked support
            assert torch.equal(output["command"][2, 1], torch.tensor(4))   # fixed occupant override
        assert not torch.equal(greedy["command"], sampled["command"])


def test_evaluation_uniform_stream_is_addressed_dedicated_and_disjoint_from_training():
    fixtures = _fixtures((1, 2, 1))
    counter = {"draws": 0}
    supplier = deployment_mode.evaluation_uniform_supplier(
        2026090506, "VNFC-N7-B01-DEPLOYMENT-MODE-20260905", "b01_formal_20260905_02", "MAPR", fixtures, counter)
    first, second = supplier(0), supplier(1)
    assert first.shape == (3, 4) and first.dtype == torch.float64
    assert bool(((first > 0) & (first < 1)).all())
    assert counter["draws"] == 24
    assert len({float(value) for value in torch.cat((first, second)).reshape(-1)}) == 24
    assert torch.equal(supplier(0), first)                     # addressed, not sequential
    other = deployment_mode.evaluation_uniform_supplier(
        2026090506, "VNFC-N7-B01-DEPLOYMENT-MODE-20260905", "b01_formal_20260905_02", "DIRECT",
        fixtures, {"draws": 0})(0)
    assert not bool((other == first).any())
    training = learning.rng(2026090505, "VNFC-N7-B01-DEPLOYMENT-MODE-20260905", "actions/MAPR")
    scale = float(1 << 64)
    training_block = torch.tensor([[(training.word(learning.coordinate(
        "VNFC-N7-B01-DEPLOYMENT-MODE-20260905", "training/action", "MAPR", 0, index, fixture.failed_zone, 0,
        token), now=None) + .5) / scale for token in range(4)]
        for index, fixture in enumerate(fixtures)], dtype=torch.float64)
    assert not bool((training_block == first).any())
    assert deployment_mode.EVALUATION_ACTION_DOMAIN != "training/action"


def test_existing_b01_invocations_do_not_pass_the_new_optional_argument():
    signature = inspect.signature(learning.rollout)
    parameter = signature.parameters["evaluation_uniforms"]
    assert parameter.default is None and list(signature.parameters)[-1] == "evaluation_uniforms"
    tree = ast.parse((REPOSITORY / "experiments/candidates/variable_n_fleet_churn_n7_direct_b01/experiment.py")
                     .read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "rollout"]
    assert len(calls) == 2
    for call in calls:
        assert len(call.args) == 8
        assert {keyword.arg for keyword in call.keywords} <= {"check_presentation"}


def _row(record, arm, mode, world, zone, value):
    return dict(record=record, arm=arm, mode=mode, world=world, zone=zone, R_fail_60=value,
                U_total=value, U_intact=value, J_ext=value)


def test_grid_readout_pairs_every_cell_on_the_shared_panel():
    rows, offsets = [], {"GREEDY": 0.0, "SAMPLE": .25}
    for record_index, record in enumerate(deployment_mode.RECORDS):
        for arm_index, arm in enumerate(deployment_mode.ARMS):
            for mode in deployment_mode.MODES:
                for world, zone in ((0, 1), (1, 2)):
                    rows.append(_row(record, arm, mode, world, zone,
                                     .1 * record_index + .5 * arm_index + offsets[mode] + world))
    bcrh = [dict(arm="BCRH", checkpoint="fixed", world=world, zone=zone, R_fail_60=1.0, U_total=1.0,
                 U_intact=1.0, J_ext=1.0) for world, zone in ((0, 1), (1, 2))]
    readout = deployment_mode.grid_readout(rows, bcrh)
    assert len(readout["contrasts"]) == 16 and len(readout["means"]) == 9
    assert len(readout["primary_contrast_means"]) == 4
    for name, mean in readout["primary_contrast_means"].items():
        assert math.isclose(mean, .25), name
    against_bcrh = next(row for row in readout["contrasts"]
                        if row["name"] == "b01_formal_20260905_02/MAPR_GREEDY_minus_BCRH")
    assert [row["R_fail_60"] for row in against_bcrh["paired_episodes"]] == [-1.0, 0.0]
    assert against_bcrh["strata"]["1"]["R_fail_60"]["n"] == 1
    assert against_bcrh["strata"]["all"]["R_fail_60"]["n"] == 2
    assert readout["mei_absolute"] == 0.10 and readout["primary_metric"] == "R_fail_60"


def test_entry_defaults_are_the_card_values_and_the_check_needs_its_reference():
    module = _entry_module()
    formal = module.build_config("formal")
    assert formal["namespace"] == "VNFC-N7-B01-DEPLOYMENT-MODE-20260905"
    assert (formal["world_seed"], formal["action_seed"]) == (2026090505, 2026090506)
    assert formal["episodes"] == 64 and formal["wall_cap"] == 180
    check = module.build_config("engineering-check")
    assert (check["world_seed"], check["action_seed"]) == (2026090595, 2026090596)
    assert check["episodes"] == 2 and check["namespace"] != formal["namespace"]
    assert formal["reference_eval_seed"] == 2026090502 and formal["reference_episodes"] == 64
    with pytest.raises(SystemExit):
        module.main(["--profile", "engineering-check", "--out", "unused", "--launch-sha", "0" * 40,
                     "--checkpoint-root", "unused"])


@pytest.mark.skipif("VNFC_B01_DEPMODE_CHECK_ROOT" not in os.environ,
                    reason="requires the existing CM-launched engineering-check output")
def test_engineering_check_output():
    root = Path(os.environ["VNFC_B01_DEPMODE_CHECK_ROOT"])
    summary = json.loads((root / "summary.json").read_text())
    assert summary["object"] == "VNFC-N7-B01-DEPLOYMENT-MODE-EVAL"
    assert summary["config"]["profile"] == "engineering-check"
    assert summary["config"]["episodes"] == 2
    rows = json.loads((root / "evaluation_episodes.json").read_text())
    bcrh = json.loads((root / "bcrh_episodes.json").read_text())
    assert len(rows) == 16 and len(bcrh) == 2
    assert len({(row["record"], row["arm"], row["mode"]) for row in rows}) == 8
    assert {row["zone"] for row in rows} == {1, 2}
    for row in rows + bcrh:
        assert row["integrated_ticks"] == 240
        assert math.isclose(row["R_fail_60"], row["fail_endpoint"][0] / row["fail_endpoint"][1])
        assert math.isclose(row["J_ext"], .5 * row["R_fail_60"] + .5 * row["U_total"])
    exposure = summary["exposure"]
    assert exposure["training_instances"] == exposure["optimizer_steps"] == exposure["parameter_updates"] == 0
    assert exposure["evaluation_episodes"] == 16 and exposure["policy_cells"] == 8
    assert exposure["policy_joint_decisions"] == 96 and exposure["bcrh_complete_calls"] == 12
    assert exposure["evaluation_action_draws"] == 4 * 96 / 2
    assert set(exposure["parameter_displacement_norms"]) == {0.0}
    assert sorted(exposure["loaded_parameters"].values()) == [89090, 89090, 148739, 148739]
    for meta in summary["checkpoints"]:
        assert meta["round"] == 64 and meta["checkpoint"] == "final"
        assert deployment_mode.CHECKPOINT_DIGESTS[(meta["record"], meta["arm"])] == meta["sha256"]
    for cell in summary["cells"]:
        assert cell["action_draws"] == (0 if cell["mode"] == "GREEDY" else 48)
        assert cell["checks"]["physical_commands"] == 12 and cell["checks"]["zone2_commands"] == 6
    replay = summary["b01_greedy_replay"]
    assert replay["compared_rows"] == 64 and replay["episodes"] == 64
    assert replay["record"] == "b01_formal_20260905_02" and replay["arm"] == "MAPR"
    assert len(summary["readout"]["contrasts"]) == 16
    assert summary["total_native_ticks"] == 240 * 18
