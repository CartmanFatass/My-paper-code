from __future__ import annotations

import os
from pathlib import Path

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    C1P1,
    FLEX,
    INDEPENDENT_NEAREST,
    NONZERO_UPDATE_NORM,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    HELDOUT_CELLS,
    TRAINING_CELLS,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    TBCFVModel,
    apply_affine_fixture_uniforms,
    required_affine_fixture_uniforms,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
    MSVC_COMPILE_FLAGS,
    POSIX_COMPILE_FLAGS,
    native_toolchain_identity,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.executability import (
    MAX_EPISODES,
    MAX_WALL_SECONDS,
    refuse_over_cap,
    run_executability,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.study import (
    IDENTITY,
    OBJECT_ID,
    PREPARATION_KEY_ASCII,
    SEED,
    SEED_KEY_ASCII,
    block_digest_hex,
    execute_b01_training_update,
    flat_parameters,
    initialize_b01_models,
    make_semantic_rng,
    native_available,
    publish_paired_primary,
    publish_paired_primary_or_error,
    se_of_mean_of_independent_ses,
    seed_root_key,
    validate_control_summary,
)


ROOT_KEY_HEX = "fb5f7dce9ab4cff9cc898c91aa49721936b84a16f202e51bc705504dd1d94c34"
BLOCK_DIGEST_HEX = "a67b014451fa8d614c191e82f2e20ded2d8f77f21098dcb52d2744e64d596048"
PREPARATION_KEY_HEX = "466f5ff780041c45996fa9cd67929b754200dca60e104b0c3d8367b18b90f3ee"
PREPARATION_BLOCK_HEX = "59a32b3cc79447350db1e0f2fd785af9b41f38524c14c3f2e8c3046e17565d3d"


def test_seed_and_preparation_digests_are_reproducible_and_distinct() -> None:
    root = seed_root_key()
    prep = seed_root_key(PREPARATION_KEY_ASCII)
    assert root.hex() == ROOT_KEY_HEX
    assert prep.hex() == PREPARATION_KEY_HEX
    assert SEED_KEY_ASCII != PREPARATION_KEY_ASCII
    assert IDENTITY == "RCLE-TBCFV-B01-PERSIST-VS-FLEX"
    assert block_digest_hex(root) == BLOCK_DIGEST_HEX
    assert block_digest_hex(prep) == PREPARATION_BLOCK_HEX
    assert block_digest_hex(root) != block_digest_hex(prep)
    assert seed_root_key() == root
    assert block_digest_hex(root, IDENTITY, 0) == BLOCK_DIGEST_HEX


def test_windows_compile_flags_remain_msvc() -> None:
    if os.name == "nt":
        assert native_toolchain_identity()["compile_flags"] == list(MSVC_COMPILE_FLAGS)
    assert POSIX_COMPILE_FLAGS == (
        "-std=c++17",
        "-O2",
        "-fexceptions",
        "-shared",
        "-fPIC",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-fno-unsafe-math-optimizations",
    )


def test_both_arms_start_identical_and_flex_finals_are_zero_trainable() -> None:
    reference = TBCFVModel()
    uniforms = {
        name: torch.full(shape, 0.5, dtype=torch.float64)
        for name, shape in required_affine_fixture_uniforms(reference).items()
    }
    apply_affine_fixture_uniforms(reference, uniforms)
    models = {}
    for arm in (C1P1, FLEX):
        model = TBCFVModel()
        model.load_state_dict(reference.state_dict())
        models[arm] = model
    assert torch.equal(flat_parameters(models[C1P1]), flat_parameters(models[FLEX]))
    for name in ("common_update_final", "agent_update_final"):
        layer = getattr(models[FLEX], name)
        assert torch.count_nonzero(layer.weight) == 0
        assert torch.count_nonzero(layer.bias) == 0
        assert layer.weight.requires_grad is True
        assert layer.bias.requires_grad is True


def _row(cell: str, index: int, arm: str, tau: float, u: float, y: float) -> dict[str, object]:
    return {
        "cell": cell,
        "index": index,
        "arm": arm,
        "tau": tau,
        "U": u,
        "F": 0.0,
        "Y": y,
    }


def test_paired_aggregation_on_handwritten_tables() -> None:
    treatment = []
    flex = []
    primary = {
        "8_to_12.ACTIVE_CONTINUATION": ((10.0, 12.0), (14.0, 16.0), (0.10, 0.10), (0.12, 0.12)),
        "12_to_8.ACTIVE_CONTINUATION": ((20.0, 22.0), (24.0, 26.0), (0.20, 0.20), (0.22, 0.22)),
    }
    for cell in HELDOUT_CELLS:
        if cell in primary:
            t_tau, f_tau, t_u, f_u = primary[cell]
            for index in range(2):
                treatment.append(_row(cell, index, C1P1, t_tau[index], t_u[index], 0.8))
                flex.append(_row(cell, index, FLEX, f_tau[index], f_u[index], 0.7))
        else:
            for index in range(2):
                treatment.append(_row(cell, index, C1P1, 30.0, 0.25, 0.5))
                flex.append(_row(cell, index, FLEX, 32.0, 0.27, 0.4))
    published = publish_paired_primary(treatment, flex)
    paths = {row["path"]: row for row in published["active_paths"]}
    assert paths["8_to_12"]["c1p1_tau_mean"] == 11.0
    assert paths["8_to_12"]["flex_tau_mean"] == 15.0
    assert paths["8_to_12"]["difference_flex_minus_c1p1"] == 4.0
    assert paths["8_to_12"]["c1p1_tau40_fraction"] == 0.0
    assert paths["8_to_12"]["flex_tau40_fraction"] == 0.0
    assert paths["8_to_12"]["c1p1_U_mean"] == pytest.approx(0.10)
    assert paths["8_to_12"]["flex_U_mean"] == pytest.approx(0.12)
    assert paths["8_to_12"]["c1p1_40U_mean"] == pytest.approx(4.0)
    assert paths["8_to_12"]["flex_40U_mean"] == pytest.approx(4.8)
    assert paths["12_to_8"]["c1p1_tau_mean"] == 21.0
    assert paths["12_to_8"]["flex_tau_mean"] == 25.0
    assert paths["12_to_8"]["difference_flex_minus_c1p1"] == 4.0
    assert published["delta_tau_b01"] == 4.0
    assert paths["8_to_12"]["paired_tau_se"] == pytest.approx(0.0)
    assert paths["8_to_12"]["paired_U_se"] == pytest.approx(0.0)
    assert paths["12_to_8"]["paired_tau_se"] == pytest.approx(0.0)
    assert paths["12_to_8"]["paired_U_se"] == pytest.approx(0.0)
    assert published["delta_tau_b01_se"] == pytest.approx(0.0)
    eight = published["c1p1_eight_cell_mean"]
    expected_tau = (11.0 + 21.0 + 6 * 30.0) / 8.0
    assert eight["tau_mean"] == pytest.approx(expected_tau)
    assert eight["Y_mean"] == pytest.approx((0.8 + 0.8 + 6 * 0.5) / 8.0)


def _control_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "object": OBJECT_ID,
        "status": "COMPLETE",
        "arm": C1P1,
        "seed": SEED,
        "block_digest_hex": BLOCK_DIGEST_HEX,
        "configuration": {"eval_episodes_per_cell": 256},
        "counts": {"completed_updates": 200},
        "scenarios": [],
    }
    payload.update(overrides)
    return payload


def test_publish_paired_primary_empty_control_scenarios_records_error() -> None:
    flex = [_row("8_to_12.ACTIVE_CONTINUATION", 0, FLEX, 12.0, 0.1, 0.8)]
    paired, error = publish_paired_primary_or_error([], flex)
    assert paired is None
    assert error is not None
    assert error.startswith("ValueError:")
    assert "control scenarios are empty" in error


def test_control_summary_validator_identity_and_exposure() -> None:
    identity = validate_control_summary(
        _control_payload(),
        updates=200,
        eval_episodes=256,
        block_digest=BLOCK_DIGEST_HEX,
    )
    assert identity["control_arm"] == C1P1
    assert identity["control_completed_updates"] == 200
    assert identity["control_block_digest_hex"] == BLOCK_DIGEST_HEX

    with pytest.raises(ValueError, match="field arm mismatch"):
        validate_control_summary(
            _control_payload(arm=INDEPENDENT_NEAREST),
            updates=200,
            eval_episodes=256,
            block_digest=BLOCK_DIGEST_HEX,
        )

    mismatched_updates = _control_payload()
    mismatched_updates["counts"] = {"completed_updates": 199}
    with pytest.raises(ValueError, match="counts.completed_updates"):
        validate_control_summary(
            mismatched_updates,
            updates=200,
            eval_episodes=256,
            block_digest=BLOCK_DIGEST_HEX,
        )

    with pytest.raises(ValueError, match="block_digest_hex"):
        validate_control_summary(
            _control_payload(block_digest_hex="00" * 32),
            updates=200,
            eval_episodes=256,
            block_digest=BLOCK_DIGEST_HEX,
        )


def test_delta_tau_b01_standard_error_on_handwritten_table() -> None:
    treatment = []
    flex = []
    path_a = "8_to_12.ACTIVE_CONTINUATION"
    path_b = "12_to_8.ACTIVE_CONTINUATION"
    for index, (t_tau, f_tau, t_u, f_u) in enumerate(
        ((10.0, 12.0, 0.10, 0.20), (12.0, 16.0, 0.20, 0.30), (14.0, 20.0, 0.30, 0.40))
    ):
        treatment.append(_row(path_a, index, C1P1, t_tau, t_u, 0.8))
        flex.append(_row(path_a, index, FLEX, f_tau, f_u, 0.7))
    for index, (t_tau, f_tau, t_u, f_u) in enumerate(
        ((20.0, 20.0, 0.20, 0.22), (24.0, 26.0, 0.24, 0.28))
    ):
        treatment.append(_row(path_b, index, C1P1, t_tau, t_u, 0.8))
        flex.append(_row(path_b, index, FLEX, f_tau, f_u, 0.7))
    for cell in HELDOUT_CELLS:
        if cell in (path_a, path_b):
            continue
        for index in range(2):
            treatment.append(_row(cell, index, C1P1, 30.0, 0.25, 0.5))
            flex.append(_row(cell, index, FLEX, 32.0, 0.27, 0.4))
    published = publish_paired_primary(treatment, flex)
    paths = {row["path"]: row for row in published["active_paths"]}
    se_a = 2.0 / (3.0 ** 0.5)
    se_b = 1.0
    assert paths["8_to_12"]["difference_flex_minus_c1p1"] == pytest.approx(4.0)
    assert paths["8_to_12"]["paired_tau_se"] == pytest.approx(se_a)
    assert paths["8_to_12"]["paired_U_se"] == pytest.approx(0.0)
    assert paths["12_to_8"]["difference_flex_minus_c1p1"] == pytest.approx(1.0)
    assert paths["12_to_8"]["paired_tau_se"] == pytest.approx(se_b)
    assert paths["12_to_8"]["paired_U_se"] == pytest.approx(0.01)
    assert published["delta_tau_b01"] == pytest.approx(2.5)
    expected = se_of_mean_of_independent_ses([se_a, se_b])
    assert expected == pytest.approx(((se_a ** 2 + se_b ** 2) ** 0.5) / 2.0)
    assert published["delta_tau_b01_se"] == pytest.approx(expected)


def test_executability_refuses_more_than_64_episodes_or_300s() -> None:
    refuse_over_cap(episodes=MAX_EPISODES, wall_cap=MAX_WALL_SECONDS)
    with pytest.raises(ValueError, match="more than 64 episodes"):
        refuse_over_cap(episodes=65, wall_cap=300.0)
    with pytest.raises(ValueError, match="wall cap above 300"):
        refuse_over_cap(episodes=8, wall_cap=300.1)


def test_two_update_and_tiny_executability_if_native_builds(tmp_path: Path) -> None:
    available, reason = native_available()
    if not available:
        pytest.skip(reason)
    _, rng = make_semantic_rng()
    models = initialize_b01_models(rng)
    assert torch.equal(flat_parameters(models[C1P1]), flat_parameters(models[FLEX]))
    model = models[C1P1]
    baselines = torch.zeros(8, dtype=torch.float64)
    before = flat_parameters(model).clone()
    baselines, _counts, curve0, nonzero0 = execute_b01_training_update(
        model, C1P1, rng, 0, baselines
    )
    after_first = flat_parameters(model)
    delta0 = float(torch.linalg.vector_norm(after_first - before).item())
    if nonzero0:
        assert delta0 == pytest.approx(NONZERO_UPDATE_NORM, abs=1.0e-12)
        assert curve0["parameter_delta_norm"] == NONZERO_UPDATE_NORM
    else:
        assert delta0 == pytest.approx(0.0, abs=1.0e-12)
    assert tuple(baselines.shape) == (8,)
    assert curve0["event_order"] == ["parameter_update", "baseline_update"]
    first_baselines = baselines.detach().clone()
    baselines, _counts, curve1, nonzero1 = execute_b01_training_update(
        model, C1P1, rng, 1, baselines
    )
    delta1 = float(torch.linalg.vector_norm(flat_parameters(model) - after_first).item())
    if nonzero1:
        assert delta1 == pytest.approx(NONZERO_UPDATE_NORM, abs=1.0e-12)
        assert curve1["parameter_delta_norm"] == NONZERO_UPDATE_NORM
    else:
        assert delta1 == pytest.approx(0.0, abs=1.0e-12)
    assert curve1["event_order"] == ["parameter_update", "baseline_update"]
    assert tuple(baselines.shape) == (8,)
    assert baselines is not first_baselines
    tiny = run_executability(
        out=tmp_path / "executability",
        wall_cap=300.0,
        cells=(TRAINING_CELLS[0],),
        episodes_per_cell=8,
    )
    assert tiny["status"] == "COMPLETE"
    assert tiny["episode_count"] == 8
    assert tiny["tick_count"] == 512
    assert tiny["preparation_root_key_hex"] == PREPARATION_KEY_HEX
    assert tiny["block_digest_hex"] == PREPARATION_BLOCK_HEX
